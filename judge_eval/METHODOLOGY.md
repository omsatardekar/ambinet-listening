# How the extractions were evaluated (method explanation for reviewers)

Written for an evaluator or mentor who asks "how exactly did you evaluate?". Every statement below describes what the code in `judge_eval/` does. Where something was NOT done, it says so (section 9).

## 1. The question being answered
A small language model (Qwen3-0.6B or Qwen3-1.7B) reads a consultation transcript and must produce a structured clinical JSON (symptoms, medications, allergies, history, vital signs, assessment, plan and so on). We want to know **how good that JSON is**.

The earlier method compared the model's JSON to the reference JSON by strict string rules and reported F1. Its flaw: "stiffness in the morning" vs "Morning stiffness" counts as a miss, and a correct fact that the reference happens to omit counts as an error. The new method uses a stronger model (a "judge", here **gpt-5.4 deployed in Azure AI Foundry**) to decide whether facts are right, and computes the metrics from the judge's decisions.

## 2. Strategy in one paragraph
This is **claim-level LLM-as-a-judge evaluation with a fixed rubric**. The model output and the reference label are each broken into atomic facts. The judge then answers two separate questions: (1) *Is each fact the model produced actually supported by the transcript?* (precision / faithfulness) and (2) *Is each fact in the reference label present in what the model produced?* (recall / completeness). Counts of those verdicts give precision, recall, a combined score, a hallucination rate and a critical-error rate, each with a bootstrap confidence interval. The idea is in the same family as fact-level verification metrics (FActScore-style atomic-fact checking) and RAG-evaluation metrics (faithfulness and context recall). It is **inspired by** those ideas; it is not an implementation of any named library.

## 3. Inputs: what is compared to what
| Item | Source |
|---|---|
| Transcript | `dataset_v2_batch_001_corrected/output/inputs/encounter_XXXXX.json` (segments with ids SEG0001…, speaker role and text) |
| Reference label ("ground truth") | `dataset_v2_batch_001_corrected/output/labels/encounter_XXXXX.json` |
| Model output | the parsed prediction JSON of each experiment run (paths in `judge_eval/registry.py`) |

All experiments ran on the **corrected** dataset (checked against the run manifests). The earlier uncorrected batch differs in every transcript and label and is never used.

## 4. Step 1: turn JSON into atomic facts (`flatten.py`)
Both the label and each model output are converted by the **same** function into a flat list of facts, one per list item, for 18 clinical fields (chief complaint, symptoms, negative findings, medications, allergies, vital signs, physical examination, review of systems, clinical conditions, assessment, procedures and investigations, clinical actions, follow-up, uncertainties, and past / surgical / family / social history).

What is kept and dropped:
- Dropped: evidence ids, confidence numbers, and `normalized_*` duplicates. They are bookkeeping, not clinical claims. Empty values are dropped.
- Kept: the clinically meaningful attributes (dose, frequency, status, duration, who reported it, and so on).

Example. This JSON item:
`{"name":"aspirin","normalized_name":"Aspirin","dose":"75 mg","route":"oral","frequency":"once a day","evidence_ids":["SEG0025"],"confidence":0.9}`
becomes the fact: `aspirin (dose=75 mg, route=oral, frequency=once a day)` with id `medications[0]`.

Nothing is repaired or invented. A label has a median of 36 facts per encounter (min 18, max 58).

## 5. Step 2: the two judge passes (`prompts.py`, `judge_run.py`)
Each (experiment run, encounter) pair gets **two independent judge calls**. The system prompts below are the exact, frozen text sent to the judge. Their SHA-256 hashes are stored in every result file (precision `2246a810…`, recall `481fac47…`), so any change to a word is detectable.

### 5a. Precision pass (faithfulness): "is what the model said true?"
The judge is given the **transcript** and the model's facts. It is **not shown the reference label**, so a mistake in the label can never affect this score.

```
You are a meticulous clinical documentation auditor. You are given a consultation transcript and a list of facts that an automatic system extracted from it. Decide, fact by fact, whether the transcript supports the fact. Use ONLY the transcript: do not use medical knowledge to accept a fact the speakers never said.

Verdicts:
- "supported": the transcript states or clearly implies the fact, including every detail shown in it (dose, status, duration, who reported it, negation). Paraphrase, synonyms, abbreviations and clinical normalisation are fine (for example "Hypertension" for "high blood pressure").
- "partially_supported": the core finding is in the transcript but at least one stated detail is wrong or not in the transcript (wrong dose, wrong duration, wrong person, wrong status). Name the wrong detail in the reason.
- "unsupported": nothing in the transcript supports the fact (invented), or it concerns someone other than the patient without saying so.
- "contradicted": the transcript says the opposite (a denied symptom listed as present, a stopped medicine listed as current, a negated finding listed as positive).

"critical" is true only for a clinically dangerous error: an invented or wrong medication, dose, allergy or diagnosis, or a flipped negation. Otherwise false. Supported facts are never critical.

Cite the transcript segment ids you relied on (for example "SEG0012"); use an empty list when nothing supports the fact. Keep each reason under 25 words.

Reply with ONE JSON object and nothing else, in this exact shape, with exactly one entry per input fact in the same order:
{"verdicts":[{"fid":"<fact id>","verdict":"supported|partially_supported|unsupported|contradicted","critical":false,"segments":["SEG0001"],"reason":"..."}]}
```
User message: `TRANSCRIPT` (one line per segment: `SEG0005 [PATIENT]: text`) followed by `EXTRACTED FACTS TO CHECK` (one line per fact).

### 5b. Recall pass (completeness): "did the model capture what it should have?"
The judge is given the **reference facts** and the **model's facts** (no transcript; the reference is treated as the expected content).

```
You are a meticulous clinical documentation auditor. You are given REFERENCE facts (the expected extraction of a consultation) and PREDICTED facts (what an automatic system extracted). For every REFERENCE fact decide whether the predicted facts convey it.

Verdicts:
- "found": a predicted fact conveys the same clinical information, including its key details (dose, status, duration, negation, who reported it). Different wording, synonyms, abbreviations and normalised names are fine. One predicted fact may cover several reference facts.
- "partially_found": the same finding is present but a key detail is missing or wrong (for example the medicine without its dose, a symptom without its duration, the wrong status). Name the gap in the reason.
- "missing": no predicted fact conveys it.

List the ids of the predicted facts that matched (empty list for "missing"). Keep each reason under 25 words.

Reply with ONE JSON object and nothing else, in this exact shape, with exactly one entry per REFERENCE fact in the same order:
{"verdicts":[{"fid":"<reference fact id>","verdict":"found|partially_found|missing","matched":["<predicted fact id>"],"reason":"..."}]}
```

### 5c. Safeguards in the code
- The reply must be valid JSON with **exactly one verdict per input fact** and only allowed verdict words. Otherwise the call is retried once (bypassing the cache); a second failure is recorded as an error, never silently accepted.
- If a model produced no facts at all, no judge call is made: every reference fact is "missing".
- Every successful reply is cached on disk (keyed by judge, deployment and prompt text), so re-running costs nothing and is reproducible.
- The API key is read from `.env`, sent only in the request header, and never printed or logged.

## 6. Step 3: from verdicts to metrics (`aggregate.py`)
Counts are summed over encounters (micro-average), then:

| Metric | Formula |
|---|---|
| Precision (strict) | supported facts ÷ all predicted facts |
| Precision (lenient) | (supported + 0.5 × partially supported) ÷ all predicted facts |
| Recall (strict) | found reference facts ÷ all reference facts |
| Recall (lenient) | (found + 0.5 × partially found) ÷ all reference facts |
| Judge-F1 | 2 × precision × recall ÷ (precision + recall), computed in the strict and the lenient variant |
| Hallucination rate | (unsupported + contradicted) ÷ predicted facts |
| Critical rate | facts the judge flagged critical ÷ predicted facts |
| Per-field scores | the same counts split by clinical field |
| 95% confidence interval | bootstrap: resample the encounters with replacement 2,000 times (fixed seed), recompute, take the 2.5th and 97.5th percentiles |

**Failed outputs.** If the model's output could not be parsed, that encounter counts as zero predictions and all its reference facts as missing (so recall is penalised). "Tier 2" shows parsed encounters only, next to tier 1, never instead of it.

**Naming.** "Judge-F1" is agreement under one judge model's reading of one rubric. It is **not clinical accuracy** and should never be called accuracy.

## 7. Worked example (real result: Qwen3-1.7B, prompt P02, encounter 00037)
The model produced 35 facts; the reference has 40.

Precision pass verdicts: 18 supported, 7 partially supported, 8 unsupported, 2 contradicted (2 flagged critical).
- `no fever (status=absent …)` → **contradicted, critical**: "Transcript reports fever present, not absent" (cited SEG0005).
- `telmisartan (dose=40 milligrams, route=oral, frequency=once a day, indication=hypertension)` → **partially supported**: "40 mg once daily by caregiver is supported; route and indication not stated."
- `joint pain (… duration=4 days …)` → **partially supported**: transcript says three weeks, constant.

Recall pass verdicts: 15 found, 10 partially found, 15 missing. For example "family history: migraines (relation=mother)" → found (matched predicted `medical_history.family_history[1]`).

Arithmetic for this encounter:
- precision strict = 18 / 35 = 0.514; lenient = (18 + 3.5) / 35 = 0.614
- recall strict = 15 / 40 = 0.375; lenient = (15 + 5) / 40 = 0.500
- judge-F1 lenient = 2 × 0.614 × 0.500 / (0.614 + 0.500) = 0.551

The reported numbers are these counts summed over all encounters of a run.

## 8. Which experiments and which encounters
- 14 runs are registered; the 11 "core" runs were judged: Qwen3-0.6B EXP_003 (direct, 100 encounters), EXP_004 P01, P02, P03, P05, EXP_006 S1, EXP_007 S1.1 B1 and B2, and Qwen3-1.7B P00, P01, P02. Total 478 encounter results, 0 judge failures.
- **Same-records comparison:** 30 encounters shared by every core run except P05 (so differences are the model or prompt, not easier encounters). P05 ran on a different 50-encounter validation split and is compared only with EXP_003 on those 50.
- Only development encounters were used; the locked test set was not touched.
- Synthetic data only; nothing real was sent to the judge.

## 9. What was NOT done (be upfront with the evaluator)
1. **No human check of the judge.** A person has not yet verified a sample of verdicts. Until the planned roughly 40-encounter calibration is done, results are "gpt-5.4's assessment", not validated ground truth.
2. **Second judge covers a sample only.** gpt-5.4 judged everything. A different-family model (Grok) re-judged a deterministic every-5th sample (98 encounter pairs). Agreement: precision verdicts 83.0% (Cohen's kappa 0.739), recall verdicts 90.2% (kappa 0.812). The first attempt with Phi-4-mini-instruct failed because it could not produce valid JSON verdicts. Two LLM judges agreeing shows consistency, not correctness.
3. **No repeat-run variance measurement.** The judge model accepts no temperature setting, so a re-run could differ slightly. Our own re-runs read the cache.
4. **The "critical" flag is noisy.** One reviewed case flagged a correct drug whose only problem was an unstated route. Treat it as an upper estimate; flagged cases need manual review.
5. **Precision credit is strict about attributes** (route, indication, who reported). That lowers precision for outputs that add plausible but unstated details. The strict and lenient variants are both reported for this reason.
6. **The recall pass trusts the reference label.** Label mistakes affect recall (they do not affect precision). The share of correct model facts that match no reference fact was small (about 5% for 1.7B P02, about 9% for 0.6B P02), which suggests the labels are largely complete.
7. **Confidence intervals are unpaired.** A paired comparison between runs on the same encounters has not been run.
8. S1 and S1.1 outputs were adapted to the full schema by a deterministic adapter before judging.

## 10. How to reproduce and inspect
```
python -m judge_eval.inventory                                   # which runs and encounters exist
python -m judge_eval.judge_run --judge JUDGE --runs all-core --scope own --workers 24
python -m judge_eval.aggregate --judge JUDGE --scope prompt_dev_set     # or validation_set / own
python -m pytest judge_eval/tests -q
```
- Every individual verdict, with its reason and cited segments, is in `judge_eval/results/JUDGE/<run>/<encounter>.json` (open any file to audit a decision).
- Summary tables and per-field numbers: `judge_eval/output/metrics_JUDGE_*.md/json`. Results and conclusions: `judge_eval/REPORT.md`.
- The settings (endpoint, deployment) come from `JUDGE_*` in `.env`; the keys are never stored in these files.
