# P02 v2.2 Stage 1 validation report

Scope: preparation pipeline only. **No model was loaded, no OpenVINO or transformers import exists in any new file, no inference was run.** Development-only (the 50 authorised prompt-dev ids; labels are generator-derived).
Written for: the project owner, to decide whether to approve a Stage 2 pilot.

Configuration verified, not changed: Qwen3-1.7B, revision `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e` (from `run_settings_P02_v2_1_pilot8.json`), OpenVINO FP16, explicit GPU (Intel UHD 620), greedy, thinking off, token cap 4,096. Nothing in Stage 1 touches these.

All new files live under `direct_inference_1_7B/experiments/EXP_002_PROMPTING_INFERENCE/` in `p02_v2_2/`, plus `prompt_versions/P02_comprehensive_v2_2.txt` and this report. Everything below was run with plain `python -B -I` (standard library only).

---

## 1. Files created

| File | Purpose |
|---|---|
| `p02_v2_2/schema/compact_output_schema_v2_2.json` | A. compact model-output schema: emission order, `refs`/`by`/`responsible`/`related` renames, defaults, required keys, nested objects, reference policy, what the backend derives, what it does not (`quality_checks`) |
| `p02_v2_2/code/v22_common.py` | paths, read-only access guard (the 50 dev ids only), frozen-schema loader, frozen `entity_matching.py` loaded by file path |
| `p02_v2_2/code/convert_gold.py` | B. gold converter (corrected dataset → compact gold, round-trip check, reference distribution, size statistics) |
| `p02_v2_2/code/evidence_resolver.py` | C. resolver: segment lookup, exact original text/speaker/role/times, invalid/excessive/duplicate/missing flags, front-end evidence lookup |
| `p02_v2_2/code/materialiser.py` | D. compact → full record, validation flags, EV allocation, `supports`, speaker rules |
| `p02_v2_2/code/evaluate_v22.py` | E. independent evaluator (compact or full format) |
| `p02_v2_2/code/reproduce_documented_measurements.py` | checks the evaluator against the numbers already documented from P00/P01/P02 v2.1 |
| `p02_v2_2/code/verify_prompt_v22.py` | static checks of the v2.2 prompt |
| `p02_v2_2/code/integrity_check_stage1.py` | hash and modification check of everything frozen |
| `p02_v2_2/tests/test_v22.py` | F. 30 unit tests |
| `p02_v2_2/derived/gold_compact/` (50) and `gold_compact_omit_derivable_by/` (50) | compact gold, two variants |
| `p02_v2_2/derived/*.json`, `UNIT_TEST_OUTPUT.txt` | conversion report, reference distribution, gold self-check, reproduction, prompt verification, integrity check |
| `prompt_versions/P02_comprehensive_v2_2.txt` | G. prompt draft |

Re-run: `python -B -I code/convert_gold.py`, `code/evaluate_v22.py --gold-selfcheck --out derived/gold_selfcheck_evaluation.json`, `code/reproduce_documented_measurements.py`, `code/verify_prompt_v22.py`, `tests/test_v22.py`.

## 2. Files inspected (read-only)
`dataset_v2_batch_001_corrected/schema/final_label_schema.json`; the corrected `inputs/` and `labels/` of the 50 frozen dev ids and their `CHECKSUMS.sha256` lines; `manifests/FROZEN_50_PROMPT_DEV_IDS.json`, `PILOT8_P02_IDS.json`, `FREEZE_P02_v2_1_pilot8.json`; `direct_inference_baseline/evaluation/entity_matching.py` (read in full, loaded as a module), `schema_validator.py`/`evidence_evaluator.py`/`clinical_metrics.py` (grep), `inference/inference_runner.py` and `output_parser.py` (the parts that decide parsed/failed); `scripts/common_1_7b.py`; `prompt_versions/P02_comprehensive_v2_1.txt`; the P00 (EXP_001), P01 and P02 v2.1 parsed/failed/raw folders; `evaluations/p00_p01_audit/PILOT_REFERENCE_METRICS.json`; `reports/P02_v2_2_PROPOSAL.md`.

---

## 3. Design as implemented (the corrections you asked for)

| Point | What was done |
|---|---|
| Evidence refs | `refs` = original segment ids. The model never writes transcript text, timestamps, speaker ids or `clinical_evidence`. The resolver matches by **exact** id only: no case folding, padding or nearest-id repair. |
| Invalid / excessive refs | flagged (`invalid_reference`, `non_string_reference`, `excessive_references`, `duplicate_reference`, `no_references`, `refs_not_a_list`); **every reference stays in the output**, including invalid ones (kept as the original string in `evidence_ids`, with no evidence record created). Nothing is truncated or dropped. |
| Reference limit | **configurable, no universal two-reference limit.** Default 4, chosen from the distribution in section 5; it only flags. The prompt states 1–2 as a soft target. |
| Categories | all 18 clinical categories kept (chief complaint, symptoms incl. resolved, negative findings, the four medical-history lists, medications incl. planned, allergies, vitals, examination, ROS, conditions, assessments, procedures, actions, follow-up, uncertainties). Only the **emission order** changes (high-risk sections first). |
| Negation / planned / resolved / contradictions | negation = explicit `negative_findings`; `status: planned`; `status: resolved` (+ `temporality`); a conflicting dose is represented by **leaving the dose out and writing a `medication_discrepancy` uncertainty whose description names both values**, with `related` pointing at the medication. The evaluator checks exactly this (section 7.3). |
| Speaker fields | `by` is an explicit model field. The backend derives it **only if every valid cited segment has the same role**; mixed roles stay null and are flagged `speaker_unresolved`. An explicit `by` is never changed; it is flagged if it is a speaker id, not a role, or is not among the cited segments' roles. `responsible_person` is **never derived** (explicit `responsible`). |
| `quality_checks` | **not produced and not invented.** Materialised records carry no such key; the evaluator reports it as "not assessed". Decision listed in section 9. |
| Existing code | untouched. The only reuse is `entity_matching.py`, loaded read-only from its file as a pure-function module so that v2.2 entity scores are comparable with all earlier runs. |

---

## 4. Tests executed

| Test | Result |
|---|---|
| Unit tests `tests/test_v22.py` | **30 of 30 pass** (`derived/UNIT_TEST_OUTPUT.txt`): resolver (5), materialiser (10), gold conversion (7), evaluator (8) |
| Prompt verification `verify_prompt_v22.py` | **54 of 54 pass** (`derived/PROMPT_V2_2_VERIFICATION.json`) |
| Gold self-check `evaluate_v22.py --gold-selfcheck` | pass (section 7.1) |
| Reproduction of documented measurements | **28 of 28 reproduced** (section 7.2) |
| Integrity check | pass (section 8) |

The unit tests include negative tests (damaged round trip is detected, invalid ids stay invalid, wrong enum values are flagged and kept, unknown keys end up in `unmapped`, the access guard refuses non-dev ids). Two assertions of my first draft were tautologies; I replaced them with real checks before the final run.

---

## 5. Gold conversion statistics (50 dev records, corrected dataset)

| Quantity | Value |
|---|---:|
| Records converted | **50** |
| Gold evidence records | 1,772 |
| Evidence records mapped to exactly one transcript segment (text, speaker, MM:SS start and end) | **1,772** |
| Failed or ambiguous mappings | **0** |
| Fact references mapped / unmapped | 3,258 / 0 |
| Non-null `confidence` fields (always null by policy) | 0 |
| Gold `primary_speakers` equal to the transcript speaker table | 50 of 50 |
| Round trip `materialise(compact(gold)) == gold` (every field except `quality_checks`, evidence block and metadata included) | **50 of 50 exact**, in both compact variants |

### Reference-count distribution (all facts, n = 1,860)
| refs per fact | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 13 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| facts | 867 | 808 | 75 | 61 | 26 | 3 | 13 | 3 | 1 | 1 | 1 | 1 |
| cumulative | 46.6% | 90.1% | 94.1% | 97.4% | 98.8% | 98.9% | 99.6% | 99.8% | 99.8% | 99.9% | 100% | 100% |

Median 2, mean 1.75, maximum 13. **A two-reference limit would flag 9.9% of gold facts; a limit of 4 flags 2.6% (49 facts).** The default stays 4 and only flags. The excess is concentrated:

| Category | facts | median | max | share > 2 | share > 4 |
|---|---:|---:|---:|---:|---:|
| symptoms | 150 | 2 | 13 | 43.3% | 28.7% |
| clinical_uncertainties | 44 | 2 | 4 | 47.7% | 0% |
| past_medical_history | 94 | 2 | 3 | 41.5% | 0% |
| medications | 128 | 2 | 6 | 25.8% | 4.7% |
| allergies | 24 | 2 | 3 | 8.3% | 0% |
| negative_findings | 273 | 2 | 4 | 6.6% | 0% |
| clinical_actions | 266 | 1 | 4 | 2.6% | 0% |
| all other categories | – | ≤ 2 | ≤ 2 | 0% | 0% |

Symptoms are the exception (gold cites every later mention). A per-category limit (for example symptoms 8, others 4) is possible without code change in the evaluator; it is listed as a decision.

### Speaker-field derivation (strict rule, 1,505 speaker values = 1,504 non-null + 1 null)
| Field | Same role in all cited lines and equal to gold | Mixed roles (not derived) | Same role but differs from gold |
|---|---:|---:|---:|
| reported_by | 341 | 913 | 0 |
| stated_by | 89 | 0 | 0 |
| observed_by | 80 | 0 | 0 |
| requested_by | 75 | 5 | 2 |
| **total** | **585 (38.9%)** | **918 (61.0%)** | **2** |

So **derivation alone covers only 39% of speaker values; 61% cite lines of more than one role (typically the doctor's question plus the patient's answer) and cannot be derived unambiguously.** For that reason `by` stays an explicit model field and the backend uses derivation only as a fallback and an audit. (A looser rule, "the non-doctor role among the cited lines", matched 1,494 of 1,504 in my earlier measurement, but it is a heuristic and is **not** implemented.) `responsible_person` (266 facts) is explicit.

### Size of the compact gold (estimated tokens, chars / 3.04)
| Form | median chars | max chars | est. tokens median | est. tokens max |
|---|---:|---:|---:|---:|
| full gold | 17,933 | 25,328 | 5,899 | 8,332 |
| full gold without evidence, metadata and checks | 8,321 | 11,860 | 2,737 | 3,901 |
| **compact gold, explicit `by`** | **5,545** | **8,003** | **1,824** | **2,633** |
| compact gold, `by` omitted where derivable | 5,383 | 7,823 | 1,771 | 2,573 |

The largest perfect compact answer is about 2.6k estimated tokens (64% of the 4,096 cap). That is a property of the target, not a prediction for the model, which may be more verbose.

### Fields that cannot be derived safely
`responsible_person` (who must act); `reported_by` etc. for 918 facts with mixed-role references; all `normalized_*` terms; `quality_checks` (owner decision); free-text values such as descriptions. Derived without ambiguity: `encounter_id`, `extraction_status`, `encounter_metadata` (50 of 50 equal to gold), `confidence` (null), `clinical_evidence` (regenerated exactly).

---

## 6. Materialisation validation

* Every one of the 50 gold records round-trips exactly (section 5), including the regenerated `clinical_evidence` (ids `EV_001…` in transcript order, `MM:SS` rounded down, `supports` in category order) and `encounter_metadata`.
* **Expected differences caused by the compact schema** (all intended, none lose a clinical fact): `quality_checks` absent; `encounter_id`, `extraction_status`, `encounter_metadata`, `clinical_evidence` and every `confidence` are produced by the backend rather than the model; null/empty/default values are omitted and restored; `evidence_ids` become segment ids and are renumbered to `EV_nnn`; an **invalid reference stays visible** and gets no evidence record, so a full record built from a faulty output intentionally fails the frozen reference rule.
* 49 gold facts are flagged `excessive_references` at the default limit of 4 and 2 are flagged `by_not_in_refs_roles` (the two `requested_by` values that differ from the cited speaker). These flags on gold are the expected baseline, not errors.
* A hand-written example (the one inside the prompt) materialises with zero flags.

## 7. Evaluator validation

### 7.1 Gold against itself (50 records)
| Check | Result |
|---|---|
| Entity micro P/R/F1, compact gold materialised vs gold | 1,860 TP, 0 FP, 0 FN, **1.0 / 1.0 / 1.0**; every category with gold facts 1.0 |
| Same for full gold (the `--format full` path) | 1.0 |
| Negative findings (273), medications (128) | 1.0 / 1.0 / 1.0 |
| Planned medication recall (29 planned) | 1.0 by name, 1.0 by name and status |
| Medication discrepancy (4 gold cases) | 4 detected, 4 linked to the right medicine, 4 name both values, 4 dose null, **4 fully handled** |
| Reference validity | 3,258 of 3,258 refs resolve |
| Reference overlap with gold | precision 1.0, recall 1.0, 100% identical segment sets |
| Parsed / truncated | 50 / 0 |
| **Floor of the lexical unsupported-claim indicators on gold** | `no_lexical_overlap_with_cited_text` 171 of 1,771 (**9.7%**, paraphrases such as "Lives with spouse" or `musculoskeletal` ROS); `number_not_in_cited_text` 14 of 542 (**2.6%**); invented dates 0 of 3; route without an oral cue 0 of 10; habit not in transcript 0 of 32; negative finding without a negation cue 0 of 273; fact without valid reference 0 |

These self-checks show that the pipeline and metrics are consistent, not that any model is good. The indicators are **lexical, not clinical**; read a model's rate against the gold floor above.

### 7.2 Reproduction of already documented measurements (28 of 28)
| Documented | New evaluator |
|---|---|
| P00 on the 8 pilot ids, failed = zero predictions: TP/FP/FN 20/92/260, P 0.179, R 0.071, F1 0.102; status 6 parsed, 2 failed | identical |
| P01, same 8 ids: 17/46/263, P 0.270, R 0.061, F1 0.099; 4 parsed, 4 failed | identical |
| P02 v2.1, 00168, gold/actual fact counts: symptoms 3/1, negatives 7/0, ROS 1/0, conditions 1/0, assessments 2/1, actions 6/1, uncertainties 1/0 | identical |
| P02 v2.1, 00168 evidence block: 36 records; 48 fact references, 18 distinct, all real segment ids; **0 resolve to the model's own evidence records**; text mismatch 2; speaker mismatch 0; start timestamps wrong 36, end 35; only SEG0006 without a record; evidence = 66% of output | identical |
| P02 v2.1, three records: parsed/failed/failed; finish stop/length/length; 3,789 / 4,096 / 4,096 tokens; 1,597 / 1,803 / 1,759 s | identical |

Limits of this comparison: the entity counts use the **same frozen matching function** as the old evaluation, so their agreement shows that loading, failed-as-zero handling and aggregation are correct, not that the matcher is independently verified. P02 v2.1 entity precision/recall for the three records was never documented (the frozen evaluation was not run), so there was nothing to compare; the new evaluator's value is stored for the record in `derived/p02_v2_1_3records_new_evaluator.json` and is not a gate result. The v2.1 outputs have no compact format, so their evidence reference checks run through the `--format full` path.

### 7.3 Where the evaluator can be fooled
Medication discrepancy "handled" needs: a `medication_discrepancy` uncertainty linked (by `related` or by name in the description) to the right medicine, both gold doses named in the description (numbers with units, after unit normalisation), and the medicine's dose null. A model that writes the discrepancy but also keeps one dose scores as detected but not handled; a model that silently chooses one dose scores as not detected. Both are tested.

---

## 8. Integrity (`derived/INTEGRITY_CHECK.json`)
* The 100 dev input and label files match the dataset's own `CHECKSUMS.sha256` (only those 100 files were hashed; no other label was opened).
* All 21 hashes recorded in `FREEZE_P02_v2_1_pilot8.json` still match: prompt v2.1, `run_prompt.py`, client, common, integrity, evaluator scripts, ids, conversion record, pilot ids, the baseline evaluator and inference modules (including `entity_matching.py`, `schema_validator.py`, `evidence_evaluator.py`) and the pilot config.
* `git status` shows no modified tracked file.
* Files created or changed since Stage 1 began are only those inside `p02_v2_2/`, the v2.2 prompt and this report.

## 9. Prompt draft (`prompt_versions/P02_comprehensive_v2_2.txt`)
12,288 characters; about **2,600 tokens by estimate** (the tokenizer was not loaded; v2.1 was 4,170 measured). Sections in emission order, keys with `*` = required, defaults stated, allowed values copied from the frozen enums. One invented worked example (shoulder ache, sertraline discrepancy, hiccups resolved, planned meloxicam) that shows a discrepancy with the dose left out, a resolved symptom, a planned medicine without invented route/reason, explicit negations, and references.
Verification: every key list and every starred key equals the compact schema, all 20 allowed-value lists equal the frozen enums, the example output is valid JSON and materialises with **zero flags**, no `clinical_evidence`/timestamp/transcript-text instructions, the old leaked phrase is absent, no dev id appears. **Leak check:** no 5-word sequence of the example transcript occurs in any of the 50 dev transcripts, none of its distinctive terms (shoulder, hiccup, sertraline, meloxicam, rotator, tendinitis, bursitis, tinnitus, hoarse, ringing) occurs in any dev transcript or gold label, and no example fact key equals a dev gold key except the standard vital names and the smoking category. My first example failed this check (shared phrases and drug names); it was replaced and re-verified. The check cannot cover validation or locked-test data, which were not opened.

---

## 10. Unresolved design decisions (need your answer)
1. **`quality_checks`.** Options: (a) leave it out of v2.2 and of the evaluation; (b) derive it from the facts with deterministic rules; (c) let the model write it. Fields such as `contradictions_detected` follow rules stated in the frozen schema, but I did not turn them into a scoring system. Not assessed until you decide.
2. **`by`: always written by the model (implemented in the prompt and the explicit gold variant) or omitted where derivable (`gold_compact_omit_derivable_by`).** The difference is small (about 150 characters per record, about 50 tokens).
3. **Reference limit.** Default 4 for every category, or per category (symptoms higher)?
4. **Sparse defaults.** The materialiser restores omitted keys with the defaults in the schema (for example `negative_findings.temporality = current`, `procedures.status = planned`, `follow_up.status = planned`, symptom `status = present`). Every default applied is counted by the materialiser; accept, or require some of these keys to be written?
5. **`responsible_person` stays explicit** (not derivable). Confirm.
6. **Token counting.** Counting the prompt's tokens needs the tokenizer files only (not the model); I did not do it because of the "do not load Qwen" instruction. Approve if you want the exact count before any run.
7. **How v2.2 scores are compared with earlier runs.** Entity metrics are comparable (same matcher). Evidence metrics are not (the evidence contract changed). Confirm that the entity tiers and the new reference metrics are the pilot's gates.

## 11. Limitations and blockers
* **No blocker for Stage 2.** The existing runner (`run_prompt.py` / `inference_runner.py`) needs **no change** to run the v2.2 prompt: it substitutes `{ENCOUNTER_ID}` and `{TRANSCRIPT}`, applies no key check (`output_parser.py` only requires a JSON object), saves compact JSON as `parsed`, and merely records `schema_compliant: false` against the frozen schema, which is expected and informational. Scoring must use `evaluate_v22.py`; the frozen `evaluate_run.py` expects the full schema (evidence block, full key names), so its numbers on compact output would not be meaningful and it must not be used for v2.2. (I did not run it on compact output.)
* Dev-only. The 50 ids are the only ones these tools can open. Gold is generator-derived. Nothing here estimates performance on unseen data.
* The compact-gold token sizes and the prompt token count are estimates (3.04 and 4.72 characters per token).
* The unsupported-claim indicators are lexical; their gold floor (9.7% and 2.6%) is not zero.
* `by_not_in_refs_roles` and the reference limit are review signals, not correctness checks. A valid but wrong reference is not detectable here.
* Whether a 1.7B model will follow the sparse-writing and `by` rules is untested; that is the purpose of a pilot. The shorter prompt (about 2.6k against 4.2k tokens) and a target of about 1.8k tokens per record (median) should cut the 25–30 minute generation time, but this is an estimate, not a measurement.
* The evaluator imports the frozen `entity_matching.py` by path: a read-only dependency on a frozen file (hash recorded in the v2.1 freeze).

---

## 12. Confirmations
* **No model was loaded** (no Qwen, no OpenVINO, no tokenizer, no `transformers`; a text search of all new Python files finds none of these imports).
* **No inference was run.** No six-record pilot, no 500-record run, no remaining v2.1 pilot records.
* **No frozen or existing file was modified**: all 21 frozen hashes match, `git status` shows no modified tracked file, and only new files exist inside `p02_v2_2/`, plus the v2.2 prompt and this report.
* **No original dataset or label was changed**: the 100 dev files match the dataset checksums; no label outside the 50 dev ids was opened.
* No model setting or token limit was changed (4,096 as before).

Stage 1 is complete. I am waiting for your approval and answers to section 10 before any inference.
