# 10. The LLM judge, all findings, and the final selection

This is the document to read before presenting numbers. It explains exactly how every number was produced, lists every result for every model in one place, states what the numbers do and do not mean, and gives the model selection with its evidence. Code and raw results: `evaluation/judge_eval/` (`METHODOLOGY.md`, `REPORT.md`, `output/*.md`).

## 1. How we score: the LLM judge

### 1.1 Why a judge and not string matching
The first scorer compared the model's JSON to the reference JSON by strict string rules. "Stiffness in the morning" against "morning stiffness" counted as a miss, and a correct fact the reference happened to omit counted as an error. The second method uses a stronger language model as a judge with a **frozen rubric**.

### 1.2 Method in six steps
1. **Flatten.** The model output and the reference label are converted by the same function into a list of atomic facts, one per list item (for example `aspirin (dose=75 mg, route=oral, frequency=once a day)`), over 18 clinical fields. Evidence ids, confidence values and duplicate normalised names are dropped. A label has a median of 36 facts (minimum 18, maximum 58).
2. **Precision pass (faithfulness).** The judge sees the **transcript** and the model's facts, and **not the reference label**, so a label mistake can never affect this score. Per fact the verdict is `supported`, `partially_supported` (the core is right but a detail such as dose, duration, status or person is wrong), `unsupported` (invented) or `contradicted` (the opposite is said), plus a `critical` flag only for a clinically dangerous error: an invented or wrong medicine, dose, allergy or diagnosis, or a flipped negation. Supported facts are never critical.
3. **Recall pass (completeness).** The judge sees the reference facts and the model's facts and decides per reference fact: `found`, `partially_found` or `missing`. For the 20 hand-written scenarios, which have no label file, the reference is the scenario's `design` block (what was put in on purpose, plus the partial or uncertain items, which should appear as a recorded doubt); it is a short human summary, so **recall against it is a floor**.
4. **Frozen prompts.** The judge prompts are fixed; their SHA-256 hashes are stored in every result file (precision `2246a810…`, recall `481fac47…`), so any change to a word is detectable.
5. **Metrics.** Precision = share of written facts that are supported; recall = share of reference facts found; judge-F1 = their harmonic mean. **Lenient** credit gives half credit to partially supported or partially found facts; **strict** counts only fully supported or found facts. **Hallucination rate** = share of written facts that are unsupported or contradicted. **Critical-error rate** = share of written facts the judge flagged. 95% confidence intervals are bootstrapped over encounters with a fixed seed.
6. **Failures count as zero.** A record whose output could not be parsed is judged with zero predicted facts, so all its reference facts are missed. Nothing is dropped.

### 1.3 The judges
* **Primary judge: gpt-5.4** in Azure AI Foundry (the `JUDGE` deployment). It judged every number in this document.
* **Second judge: grok-4.7** (a different model family, `JUDGE2`) re-judged a deterministic every-fifth sample of 98 encounter pairs. **Agreement:** precision verdicts 83.0% (Cohen's kappa 0.739), recall verdicts 90.2% (kappa 0.812). A first attempt with Phi-4-mini-instruct failed because it could not produce valid JSON verdicts. Two judges agreeing shows consistency, not correctness. The second judge was **not** run on the fine-tuning results.
* The same two model deployments were used elsewhere: grok-4.7 **wrote** the natural round-2 data and gpt-5.4 **verified** its labels (document 02).

### 1.4 Limits of the judge (state these)
1. **One judge, not calibrated against a human.** No clinician has checked the verdicts; call every figure "gpt-5.4's assessment". Human calibration on about 40 encounters (Cohen's kappa against a human) was **not done**.
2. **Run-to-run variance is unmeasured.** The judge model accepts no temperature setting, so a re-run could shift numbers slightly; our own re-runs read a cache and are identical.
3. **The `critical` flag is noisy** (seen set on a fact whose only problem was an unstated route); treat the critical rate as an upper estimate.
4. **The judge is strict about attributes** (route, indication, who reported it), which lowers precision for runs that add plausible but unstated details.
5. **Possible shared bias.** gpt-5.4 verified the natural training labels and also judges the evaluation. The test set, the 20 scenarios and the 30 baseline encounters were never part of that verification, but a style preference cannot be ruled out. The second judge was not run on fine-tuned outputs.
6. **Judge-F1 is not clinical accuracy** and is never called accuracy in our documents.
7. Synthetic data only; nothing real was sent to any judge.

## 2. Every result in one place

### 2.1 Prompted baselines (same 30 encounters, document 03 for details)
Best 0.6B prompt (S1.1 B1) judge-F1 0.395; **H1 (the model that was deployed) 0.352**; best 1.7B (P02) 0.536; hallucination 16 to 28% in every prompted run.

### 2.2 Round 1: the locked test set (973 encounters, once)
| Subset | Precision | Recall | Judge-F1 (lenient / strict) | Hallucination | Critical | Valid as generated |
|---|---|---|---|---|---|---|
| Test A (500) | 0.949 | 0.917 | 0.933 / 0.898 | 0.022 | 0.007 | 495 / 500 |
| Test B (473) | 0.939 | 0.925 | 0.932 / 0.896 | 0.026 | 0.009 | 472 / 473 |
| **All (973)** | **0.945** | **0.921** | **0.933 / 0.897** | **0.024** | **0.008** | **967 / 973** |

The six invalid outputs are all repaired by the guard (100% valid after the guard, six flagged for review). Weakest content: clinical uncertainties (recall 0.774, precision 0.752), physical examination (0.763 recall), clinical actions (0.836), symptoms (0.841); the hand-written Batch 3 is the lowest source batch (judge-F1 0.866, recall 0.826). **Step 156 (round 2) has not been run on this test set** (about 11 hours of GPU).

### 2.3 Before and after on the 30 baseline encounters
| | H1 baseline | Round 1, step 400 | Round 1 after OpenVINO FP16 conversion |
|---|---|---|---|
| Judge-F1 (lenient) | 0.352 | 0.939 | 0.940 |
| Judge-F1 (strict) | 0.239 | 0.903 | |
| Precision / recall | 0.568 / 0.255 | 0.956 / 0.923 | 0.957 / 0.924 |
| Hallucination | 0.262 | 0.014 | 0.014 |
| Critical | 0.120 | 0.005 | 0.005 |

### 2.4 The 20 hand-written natural scenarios (the realistic check)

| Model and input | Valid | Precision | Recall vs design | Hallucination | Critical | Facts per scenario |
|---|---|---|---|---|---|---|
| H1 baseline (base model, long prompt) | 19 / 20 | 0.515 | 0.272 | 0.325 | 0.159 | |
| **Round 1, step 400, full text** | 20 / 20 | **0.762** | 0.558 | **0.168** | **0.048** | 30 |
| Round 1, step 400, windows | 20 / 20 | 0.730 | 0.562 | 0.206 | 0.050 | |
| Round 2, step 100 + guard, full text | 20 / 20 (14 repaired) | 0.703 | 0.524 | 0.206 | 0.079 | |
| Round 2, step 156 + guard, full text | 20 / 20 (9 repaired) | 0.717 | 0.580 | 0.205 | 0.071 | |
| **Round 2, step 156, windows** | 20 / 20 | 0.710 | **0.675** | 0.213 | 0.054 | **52** |
| Round 3, step 20, windows | 20 / 20 | 0.683 | 0.681 | 0.234 | 0.059 | 52 |
| Round 3, step 50, windows | 17 of 20 complete* | 0.664 | 0.640 | 0.255 | 0.060 | 51 |

*Step 50: 3 of 44 windows could not be parsed even by the guard.

**Without the guard** the round-2 outputs that looped count as empty (step 100: valid 6 / 20, precision 0.722, recall 0.207; step 156: valid 11 / 20, precision 0.729, recall 0.345).

**Per scenario (precision / recall)**

| scenario | H1 baseline | step 400 full text | step 400 windows | step 156 windows |
|---|---|---|---|---|
| 01 foot sore, bus driver | 0.821 / 0.393 | 0.842 / 0.536 | 0.810 / 0.571 | 0.843 / 0.643 |
| 02 low mood, wife answers | 0.467 / 0.179 | 0.729 / 0.536 | 0.582 / 0.500 | 0.581 / 0.571 |
| 03 heart tablets, bruising, carer | 0.478 / 0.286 | 0.776 / 0.321 | 0.765 / 0.393 | 0.614 / 0.643 |
| 04 hair thinning (absence test) | 0.625 / 0.125 | 0.735 / 0.750 | 0.700 / 0.750 | 0.750 / 0.750 |
| 05 swollen ankles, ED | 0.346 / 0.231 | 0.734 / 0.615 | 0.698 / 0.538 | 0.783 / 0.769 |
| 06 hip and groin pain | 0.385 / 0.179 | 0.730 / 0.571 | 0.775 / 0.536 | 0.774 / 0.643 |
| 07 hearing a voice at night | 0.615 / 0.300 | 0.696 / 0.300 | 0.750 / 0.400 | 0.778 / 0.650 |
| 08 toddler vaccination | 0.429 / 0.333 | 0.705 / 0.278 | 0.726 / 0.222 | 0.596 / 0.278 |
| 09 dizzy on standing, plumber | 0.421 / 0.409 | 0.756 / 0.636 | 0.769 / 0.727 | 0.678 / 0.727 |
| 10 high calcium found by chance | 0.545 / 0.318 | 0.722 / 0.455 | 0.605 / 0.545 | 0.555 / 0.636 |
| 11 rectal bleeding, embarrassed | n/a / 0.000 | 0.700 / 0.500 | 0.662 / 0.500 | 0.805 / 0.545 |
| 12 cracked hands, carer and pharmacy tech | 0.639 / 0.286 | 0.661 / 0.571 | 0.757 / 0.679 | 0.746 / 0.750 |
| 13 forgetting and getting lost | 0.575 / 0.367 | 0.847 / 0.633 | 0.724 / 0.633 | 0.754 / 0.800 |
| 14 fever after travel | 0.538 / 0.208 | 0.826 / 0.792 | 0.805 / 0.625 | 0.716 / 0.750 |
| 15 irregular periods, night sweats | 0.472 / 0.333 | 0.885 / 0.750 | 0.798 / 0.667 | 0.848 / 0.833 |
| 16 kitchen knife cut | 0.600 / 0.423 | 0.717 / 0.654 | 0.800 / 0.538 | 0.690 / 0.577 |
| 17 burning upper stomach | 0.444 / 0.346 | 0.781 / 0.423 | 0.707 / 0.462 | 0.780 / 0.654 |
| 18 hoarse voice, teacher | 0.167 / 0.167 | 0.738 / 0.667 | 0.729 / 0.833 | 0.625 / 0.611 |
| 19 prediabetes, what happens now | 0.200 / 0.000 | 0.775 / 0.562 | 0.708 / 0.500 | 0.739 / 0.875 |
| 20 diabetes screening, symptom diary | 0.593 / 0.318 | 0.764 / 0.682 | 0.728 / 0.727 | 0.712 / 0.773 |

(The H1 baseline's precision for scenario 11 is n/a because its output was invalid and counts as zero facts.)

### 2.5 Paired comparisons (same 20 scenarios, per-scenario differences)
| Comparison | Precision | Recall |
|---|---|---|
| Step 156 windows against step 400 **full text** | -0.038 (better in 7, worse in 13; about 2 standard errors) | **+0.112** (better in 15, worse in 3; about 4 standard errors) |
| Step 156 windows against step 400 **windows** (the like-for-like deployed configuration) | **-0.012** (better in 9, worse in 11; about 0.7 standard errors, **not distinguishable from zero**) | **+0.107** (better in 17, worse in 1; about 3.8 standard errors) |

### 2.6 Real model in the deployment format
The OpenVINO FP16 conversion of step 400 reproduces the PyTorch accuracy (judge-F1 0.940 against 0.939 on 30 encounters, 30 of 30 valid). The OpenVINO FP16 model of step 156 ran on the laptop CPU through the full scoring pipeline on four long scenarios: 4 of 4 valid, 2 or 3 windows each, 413 to 631 seconds per consultation (laptop CPU, not the Azure VM). Azure speed is not yet measured.

## 3. What the numbers support, and what they do not
**They support:**
* Fine-tuning works: on the same 30 encounters judge-F1 rises from 0.352 to 0.939, hallucination falls from 0.262 to 0.014 and critical errors from 0.120 to 0.005; on natural hand-written speech precision rises from 0.515 to 0.762 and hallucination falls from 0.325 to 0.168 (step 400).
* Natural-style training (round 2) raises recall on natural speech by about 0.11 (clear and consistent across scenarios).
* Windowing plus the guard make every model usable on any consultation length with 100% parseable output.
* Round 3 did not help.

**They do not support:**
* A claim of "93% accuracy" in real use. The 0.933 is judge-F1 on synthetic template-style data.
* A claim that step 156 is better than step 400 on the template test set, because it was not run there.
* A claim about performance on real speech, accents, background noise or speech-recognition errors.
* Any clinical-safety claim; no clinician reviewed anything.

## 4. Final selection

**Status: both models are packaged and ready** (`deployment/step400_round1/` and `deployment/step156_round2/`, each with the 11 OpenVINO files and its own scoring file that pins the SHA-256 of its weights). The project team makes the final choice; the evidence and our recommendation are below.

| | Step 400 (round 1) | Step 156 (round 2) |
|---|---|---|
| Strengths | highest precision on full text (0.762), lowest hallucination (0.168), lowest critical rate (0.048); proven on the 973-encounter test set; OpenVINO parity checked on 30 encounters | **recall +0.11** (0.675 against 0.562 like for like), a more complete record (52 against 30 facts), a clear win on 17 of 20 scenarios for recall |
| Weaknesses | lower recall (about 0.56); writes fewer facts | slightly lower precision (-0.04 against full text; about -0.01 and not significant against windows), higher hallucination than step 400 on full text (0.213 against 0.168; 0.213 against 0.206 on windows); loops on long outputs without the guard; **not run on the 973-encounter test set** |
| Needs | the guard; windows only for very long inputs: its scoring file uses 14,000 characters per window with 10 segments of overlap, so all 20 scenarios (10,835 to 12,654 characters) run in one pass | windows of 7,000 characters and the guard (built into its scoring file); it must always use them, and even so both windows of the m3_14 test looped (section 5) |

**Our recommendation (revised after the live tests in section 5): deploy step 400, with the existing H1 deployment kept as the rollback.** The project's priority is a low rate of invented facts, because the extraction feeds the SOAP note. Evidence:
* Step 400 has the lowest hallucination (0.168 on full text) and the lowest critical-error rate (0.048) on the 20 natural scenarios, and it is the only model proven on the 973-encounter test (hallucination 0.024).
* Step 400 never looped on the 20 scenarios (20 of 20 valid without repair) and its single pass is valid at every length tested. Windows are therefore not needed for it at these lengths; on step 400, windowing cost precision (0.762 on full text against 0.730 on windows) and caused a real error in the live test (a conflicting smoking entry created because the second window lacked the context of the first). Its scoring file now uses 14,000 characters per window, so every tested consultation is one pass.
* Step 156 is better on recall when both models are windowed (+0.107, 17 of 20 scenarios; precision -0.012, not distinguishable from zero), and that comparison stands. But on the one live consultation we ran through it (m3_14) both windows hit the token limit, the repair left only 26 facts against 43 for step 400, and it invented two plan items.
* An earlier version of this document recommended step 156 on the windowed comparison alone. That was before the live test and before we found that step 400 does not need windows; the windowed comparison is not the deployed configuration of step 400 any more.

If the team's priority is a more complete record over the lowest rate of unsupported facts, step 156 remains packaged (`deployment/step156_round2/`), but it has not been run on the 973-encounter test and loops without the guard.

**Before a final release (not yet done):**
1. Run step 156 (windowed) on a stratified subset of the locked test set to check there is no regression on template-style data.
2. Measure speed more widely on the Azure CPU endpoint. Done so far for step 400 only, on three live consultations (section 5.1: 193 to 272 seconds); step 156 was only run on the laptop (413 to 631 seconds for four scenarios; about 30 minutes on m3_14 because both windows looped).
3. Run the second judge on the fine-tuned results, and calibrate the judge against a clinician on about 40 encounters.
4. Have a clinician review a sample of outputs from the 20 scenarios, in particular the allergy, negation and medication fields.
5. Test with real, approved, speech-recognised transcripts when available.

## 5. Live tests through the application (2026-11-26), what they showed, and the backend safeguards

After deployment, two of the 20 scenarios were run through the whole application (recording, transcription, extraction on the Azure endpoint, SOAP note) and read against the dialogue: m3_14 (fever after travel, three runs) and m3_15 (irregular periods, two runs). These are **single examples, not measurements**; the rates in section 2 remain the measured ones.

### 5.1 Azure speed (step 400, endpoint `qwen3-p02-extraction`, deployment `qwen3-0-6b-step400`)
| Test | Windows | Seconds (extraction job) |
|---|---|---|
| 4-turn sample request | 1 | 24.6 |
| m3_14, first run (7,000-character windows) | 2 | 193 |
| m3_14, second run (14,000-character windows) | 1 | 272 |
| m3_15 (two runs) | 1 | 213 to 215 |
The application's "Prepared in" figure for the whole extraction step was 3 min 18 s to 4 min 38 s. Laptop CPU for comparison: 413 to 631 seconds for step 156 on four scenarios.

### 5.2 What the first m3_14 run showed (step 400, two windows)
* **Missed:** the allergy answer ("None. I don't have any."); the fact that no antimalarial tablets were taken; nausea and constipation.
* **Window damage:** a "Former smoker" entry next to "Current smoker", because the second window saw "I've been trying to stop" without the earlier "Do you smoke? Yes". The merge keeps both entries; an overlap of 4 segments cannot carry that context. This led to the window change below.
* **Training-data bug found:** the unit "Â°C" in a duplicate temperature entry. The model wrote it itself; 150 of the lines in `data/round1_synthetic/data/train.jsonl` contain the garbled "Â°". Fixed in the backend (below); the training data have **not** been cleaned and a future training run should do that first.
* **Other model errors:** the inhaler's puff instruction attached to the Dolo dose uncertainty; the follow-up advice given to the husband attached to the patient; a gastrointestinal review of systems linked to a segment about family illness; every test listed twice (laboratory and investigation).

### 5.3 The window change (step 400 only)
Reason: windows lose context, and step 400 did not need them on the 20 scenarios (section 4). The scoring file of step 400 now pins **14,000 characters per window and 10 segments of overlap** (the builder takes `--window-chars` and `--window-overlap`; step 156 keeps 7,000 and 4). All 20 scenarios and the m3_14 job (92 segments) are now **one window**. Each model has its own bundle folder. The offline self-test (6 checks) passes. What is not tested: a consultation much longer than the 20 scenarios (the longest has 12,654 characters) through the real OpenVINO model in one pass.

### 5.4 What the second m3_14 run and the m3_15 runs showed (step 400, one window)
* **Better:** the allergy answer reached the SOAP note ("no known allergies reported"); dengue was recorded as the doctor's alternative; one smoking entry and one temperature entry; the m3_15 vital signs, medicine, history and plan were mostly right and the SOAP notes were good.
* **Still wrong (the model, not the windows):** "No asthma" listed as absent although the patient has asthma (a flipped negation); smoking marked "former" for a current smoker; a genitourinary review of systems "negative" linked to a segment about family illness (the same kind of error as the gastrointestinal one); three plan items invented or misplaced ("Arrange urgent admission" stated as certain, "Seek urgent care for severe malaria" cited to a segment about cigarettes, "Stay away from mosquitoes" never said); "snores" attributed to the patient when it was her husband; the body site "anus" given to the underarm glands; alendronate marked "planned" for a medicine she already takes; a neurological review "negative" next to her memory trouble; two plan items that contradict each other about hormone therapy.

### 5.5 Step 156 on the same m3_14 transcript (real OpenVINO model, laptop CPU, windows of 7,000 characters)
Both windows reached the token limit and were repaired by the guard (status "repaired"); 1,821 seconds on the laptop (generation 1,811 seconds). Result: 26 facts against 43 for step 400; no medications, no reported-absent findings, no smoking or alcohol; "Attends the wedding" as a social-history item; two invented plan items ("Do not share the malaria inhaler", "Do not give antimalarial tablets"); the allergy answer also missed. One example, but it is the case that moved our recommendation to step 400.

### 5.6 How the SOAP note catches errors (Module 4)
The SOAP writer is a large language model in Foundry. It does **not** receive the transcript by default. Its input (`soap_data/jobs/*/input_payload.json`) is: the extraction (each finding with a reference such as `negative_findings[4]`), the **transcript passages each finding cites** (`source_passages`), and rule-based `data_quality_flags` (for example a vital sign that does not look like a measurement). It compares each finding with the passage it cites and lists mismatches under "Before you sign"; a code check also traces numbers, medicines and allergies to the conversation. In the live tests it flagged almost every extraction error listed above (blood pressure "1 or 8 over 78" from a speech-recognition error, "No asthma", smoking status, wrong review-of-systems links, invented plan items, the follow-up attributed to the wrong person, the snoring, the body site "anus"). It depends on honest citations: a wrong fact cited to a plausible segment could pass; and it cannot flag what the extraction never recorded and no finding cites. It also produced one false alarm (it said the instruction to tell the nurse was not found, but the doctor did say it).

### 5.7 Backend safeguards added after these tests (no retraining, no change to the model)
All in `clinical_extraction/` (the model's exact output is kept as `extraction_model_output.json` in the job folder; every change is listed in `metadata.postprocess`; 76 backend and SOAP tests pass):
| Safeguard | What it does | Measured on 1,343 stored model outputs |
|---|---|---|
| Review flag from the scoring file | `extraction_status` repaired or partial, or `needs_review`, becomes a visible warning and the job status "completed with warnings" | |
| Encoding repair | "Â°" becomes "°" in every string | caused by the training-data bug above |
| Contradicted negative | removes "No X" when X is in the medical history, with a warning | 6 removals, 4 distinct cases (for example "No asthma", "No diabetes") |
| Duplicate tests | merges an "Arrange X" investigation into the matching laboratory item, keeping all evidence segments | 1,670 merges; the model duplicates tests in about three quarters of its outputs |
| Repeated symptoms | removes a leading "the/my/a"; merges the same symptom written twice (same status, category, time and compatible body site; a name contained in another name merges only with the same stated frequency); a merge with conflicting details keeps the first and warns | 104 merges (84 symptoms, 20 reported-absent findings), 26 with a conflicting value, shown as a warning; on the real m3_15 job "sweats" was merged into "night sweats" |
| Speech wording flag | warns when a symptom name is a sentence copied from speech ("I'm not a snappy person"); nothing is removed | 7 flags, 3 distinct phrases |
Limits: these rules catch narrow, recurring patterns. They do not fix wrong speaker attribution, wrong labels, invented plan items or missed facts; the contradicted-negative rule removes the negative even when the negative was right and the history entry wrong (the warning asks for review); one rule first matched on the model's normalised label and wrongly removed 10 items before it was restricted to the model's own wording.

### 5.8 What to say, and not to say
Say: on natural conversations about 76% of what the model writes is supported by the transcript and about 17% is unsupported, it captures about 56% of the facts designed into each conversation (against 52% supported, 33% unsupported for the untuned model); on the large synthetic test the unsupported rate is 2.4%; the output is a draft, the SOAP "Before you sign" section catches most of the remaining errors, a clinician signs every note. Do **not** say "70% accurate" or "93% accurate": neither is a measured figure, and the 93% is judge-F1 on synthetic, template-style data.

## 6. Questions an external reviewer may ask
**What is judge-F1 and is it accuracy?** The harmonic mean of the judge's precision and recall. It is agreement with one judge model under one rubric; it is not clinical accuracy.

**Why a language model as judge?** String matching penalises correct paraphrases and rewards copying; a frozen-rubric judge checks each fact against the transcript. The old strict F1 numbers are about half the judge numbers for the same outputs and must not be mixed with them.

**How do you know the judge is right?** We do not know. We know it agrees with a second, different-family judge on 83% (precision verdicts, kappa 0.74) and 90% (recall verdicts, kappa 0.81) of a 98-pair sample; we have not compared it with a human.

**Is the 0.933 inflated?** For real speech, yes: it is on synthetic, template-style test data from scenario groups that are held out of training but share the template style. The natural-speech number (precision 0.762) is the better guide.

**What is the hallucination rate?** The share of facts the model wrote that the transcript does not support or contradicts, as read by the judge. The frozen precision prompt tells the judge to use only the transcript, not medical knowledge.

**What is a critical error?** An invented or wrong medicine, dose, allergy or diagnosis, or a flipped negation. The rate was 0.5% on the 30 baseline encounters, 0.8% on the 973 test encounters and 4.8% on the natural scenarios (step 400). The flag is noisy; a clinician should review all flagged facts before any safety claim.

**Why did you pick windows?** Because round-2 outputs looped on long inputs and the T4 could not train on long sequences; windows of about 1,800 tokens match the training length, bound the output length and make any consultation length work.

**Are the repaired outputs reliable?** They are valid JSON and flagged for review. For the six repaired test outputs only validity is claimed; the repaired content has not been judged for accuracy. The guard never alters an output that already parses.

**How reproducible is this?** Prompts are frozen with hashes; judge replies are cached; every raw model output is saved (`runs/`); training scripts, seeds and settings are in the repository. The judge itself accepts no temperature, so a fresh judge run could differ slightly.

**Why not report only the best number?** The documents report every model we ran, including the failed round 3, and state the limits next to each result.

**What happens when the model is wrong?** The scoring file marks repaired, partial or schema-invalid results `needs_review` and returns `extraction_status` (ok, repaired, partial, failed) in the metadata; a failed extraction asks for clinician review. The Module 4 SOAP note is built from the extraction only, so errors propagate; a clinician always reviews the final note.

**Why step 400 and not step 156?** Priority is the fewest invented facts, because the extraction feeds the SOAP note. Step 400 has the lowest hallucination and critical rates, is proven on 973 test encounters and never looped; step 156 has higher recall when both are windowed but looped on every window of the one live consultation we ran (section 5.5) and has not been run on the large test.

**Why windows, and do they lose context?** Windows exist because long outputs made the round-2 model loop and the T4 could not train on long sequences. They do lose context (section 5.2), so step 400, which does not loop at the tested lengths, now runs consultations of up to about 14,000 characters in one pass; windows are the fallback for longer ones.

**What did you change after seeing the live tests?** The window size of step 400, a review warning for repaired results, an encoding repair, and four deterministic rules in the backend (section 5.7). The model and its weights did not change.

**Why can the backend rules be trusted not to hide errors?** They only warn or merge exact repeats; the model's raw output is kept next to the cleaned one, every change is listed in the job metadata, and the one rule that removes a statement (a "No X" that contradicts the history) always shows a warning to the clinician.

**Is this ready for patients?** No. It is a draft-generating pipeline tested on synthetic conversations. No clinician has reviewed the labels, the judge or the outputs, and real speech has not been tested.
