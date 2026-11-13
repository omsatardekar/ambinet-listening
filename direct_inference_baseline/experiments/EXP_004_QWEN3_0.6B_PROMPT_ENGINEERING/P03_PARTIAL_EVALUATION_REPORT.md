# P03 PARTIAL EVALUATION REPORT - PARTIAL P03 DEVELOPMENT RESULTS

**These are partial development results. Inference was stopped by the user before the 50-record run finished. This is not the final P03 experiment result and must not be quoted as one.**
Prompt: `prompts/P03_evidence_grounded.txt`, sha256 `4f7ee6f763aa886ec8090f7bb680f40eaa2f7f89e37175dfd6b8ce29daad5c9f` (frozen, unchanged). Evaluator, schema, dataset, labels, P00-P02 and EXP_001-003 untouched. Validation and locked test records not used.

## 1. Execution summary
Run `P03_evidence_grounded_dev50` started 2026-11-12 23:56. At 2026-11-13 01:48 IST I stopped the two processes (the launcher and the Python child) with a forced stop; Windows has no graceful signal for this runner, so it was a hard kill. The record in flight at that moment (after 00393, which finished at 01:46:39) was not saved; it is among the unprocessed ids. Nothing was deleted, overwritten or rerun. All raw outputs, parsed/failed outputs, `inference.log`, `performance.json` and the run manifest are preserved.

Verified counts (manifest, raw files, parsed/failed folders and the log all agree; script `experiments/partial_eval_p03.py` asserts this):

| | Count | Your expectation |
|---|---|---|
| Planned | 50 | 50 |
| Attempted | **35** | 32 |
| Valid JSON | **33** (94.3% of attempted) | 30 |
| Invalid JSON | 2 (00127, 00264; both "Expecting ',' delimiter") | 2 |
| Not attempted | **15** | 18 |
The difference is timing: three more records (00288-00393 range) finished after the log you read. All 35 had finish_reason `stop`; max 2,221 output tokens.
Failed ids: **00127, 00264**. Unprocessed ids (15): 00397, 00402, 00403, 00409, 00416, 00426, 00429, 00454, 00455, 00460, 00462, 00469, 00471, 00475, 00497.
For the pairing, P00 failed on 00264 among these 35 ids (P00 invalid: 1; P03 invalid: 2).

## 2. Evaluation integrity
The existing evaluator evaluates the records listed in the run manifest, so a partial subset is handled safely. I ran it unmodified on a copy of the manifest under `evaluation/P03_PARTIAL/` (live run folders untouched). P00 is compared on **the exact same 35 ids** (P00 outputs from EXP_003, no new inference). All figures below use these 35 ids (33 valid for P03, 34 valid for P00) unless stated. The 15 unprocessed records are not scored as zeros for P03. Sample sizes are therefore equal for both prompts but small (35), so differences are noisy. The pre-registered criteria were defined for all 50 records; their partial values are indicative only (section 7).

## 3. Extraction, schema and cost (same 35 ids)
| | P00 | P03 (partial) |
|---|---|---|
| TP / FP / FN | 38 / 123 / 1245 | 40 / 138 / 1243 |
| Micro precision | 0.236 | 0.225 |
| Micro recall | 0.030 | 0.031 |
| Micro F1 | 0.053 | 0.055 |
| Macro F1 | 0.056 | 0.057 |
| Micro-F1 difference, paired bootstrap 95% | | -0.014 to +0.020 (includes 0) |
| Valid JSON | 34/35 (97.1%) | 33/35 (94.3%) |
| Fully schema-compliant records | 0 | 0 |
| Violations total (missing / wrong-type / enum / unexpected) | 338 (194 / 57 / 83 / 4) | 313 (159 / 57 / 97 / 0) |
| Required-field completeness (keys present / expected, valid records) | 93.7% | 95.2% |
| Predicted items / duplicates | 161 / 0 | 178 / 0 (duplicate rate 0%) |
| Mean output tokens | 892 | 977 |
| Mean latency, tokens/s | 158.7 s, 5.61 | 184.4 s, 5.27 |
Extraction did not change measurably: the evidence rules neither helped nor hurt accuracy. Category F1 differences are all within 1-3 true positives (medications 0.389 -> 0.357, surgical history 0.148 -> 0.207, procedures 0 -> 0.062, clinical_uncertainties 0.069 -> 0; full table in `partial_evaluation.json`).

## 4. Evidence metrics (P03 33 valid records vs P00 34 valid records, same ids)
| Metric | P00 | P03 |
|---|---|---|
| Grounding (evaluator), items evaluated | 161 | 178 |
| Strict / lenient / partial / unsupported | 2 / 0 / 8 / 151 (93.8%) | **0 / 0 / 28 / 150 (84.3%)** |
| Strict+lenient grounded | 1.2% | **0%** |
| Items with any evidence_ids | 29.6% | **18.5%** (33 of 178) |
| evidence_ids that resolve to a record | 91.7% | 100% (33 of 33) |
| Evidence records per encounter | 1.0 | **1.0 (33 records for 33 encounters)** |
| Records whose text is in the transcript / whole segment | 76.5% / 61.8% | 97.0% / 90.9% |
| Records with correct speaker_id for their text | 26.5% | 84.8% (28/33) |
| Role field correct (when speaker correct) | 100% | 100% (but see below: 18 of 33 in capitals) |
| Timestamps within +-1 s of the cited segment | 0% | **0% (0 of 33)**; exact truncation match 0% |
| Timestamps in MM:SS form at all | 2 of 34 | 16 of 33 (17 are decimal seconds or other) |
| `supports` non-empty | 0% | 51.5% (17 of 33) |
| `supports` entries that exist / point to an entity that lists the record | n/a | 94.1% / 82.3% (of 17 entries) |
| Speaker attribution (evaluator) | 44.1% (34 evaluated) | **36.8% (38 evaluated)** |
| Unsupported claims (evaluator) | 2.5% | 5.1% |
Evidence-ID "validity" and the speaker/text improvements are **not real progress**: they are a consequence of the model writing exactly one record and copying a real line verbatim (section 5). Strict/lenient grounding went to 0.

## 5. Evidence-specific inspection (prompt_dev ids only)
Aggregate over the 33 valid P03 outputs (`evaluation/P03_PARTIAL/evidence_inspection.json`):
* **Every output has exactly one evidence record** (33/33), exactly as P00. The "one record per transcript line that states an item" rule had no effect.
* **That single record is the opening of the conversation:** it is the first segment in 25/33 records and within the first three segments in 30/33. So your observation about 00215 and 00248 is general: EV_001 is copied from the greeting/first lines.
* **Only the chief complaint cites evidence.** All 33 entities with `evidence_ids` are `chief_complaint`; the other 145 items (symptoms, medications, vitals, and so on) have empty `evidence_ids` in every record.
* **The cited line does not state the cited item:** of the 33 cited chief complaints, only 3 are lexically supported (lenient) by the cited text.
* `supports`: `["chief_complaint"]` 14, `[]` 16, `["symptoms[0]"]` 2, `["vital_signs"]` 1 (not a valid location format).
* Timestamps: 17 of 33 are not MM:SS (decimal seconds or ranges); of the 16 MM:SS values, none matches the cited segment (e.g. 00037 "09:00" vs 00:00; 00042 "03:24" vs 00:03; 00069 "01:15" vs 00:07).
* Roles: 18 of 33 `speaker_role` values are upper case (PATIENT/DOCTOR/NURSE) despite the instruction to lower-case them.

Representative examples:
* **00215** (46 segments, 4 items in total): EV_001 = `person_1`, role "PATIENT" (upper case), text "Hello, doctor. Where would you like me?" (SEG0001, the greeting), start "0.62-3.93", end "3.93" (raw seconds, a range in the start field, no MM:SS), supports `["chief_complaint"]`. The only item with evidence is the chief complaint, whose value is "severe"; the actual complaint (headaches in the mornings) is stated in SEG0003. The other three items have no evidence_ids.
* **00248** (39 segments, 3 items): EV_001 = `person_1`, "PATIENT", text "Morning. Nice to finally see you, doctor." (SEG0001, which spans 00:00-00:04), start/end "06:03" (invented; no segment is there), `supports: []`. The chief complaint value is a long fragment ("Mild, I'd say. Yes, deadlines. That That makes it worse. Wee...") that this line does not state; the complaint ("feeling overwhelmed at work") is in SEG0003. Two other items have no evidence_ids.
* Speaker ids of the evidence records are correct more often (84.8%) only because the greeting really is said by `person_1` and the record copies it; this does not show that the model matches speakers to facts.

Likely cause (hypothesis, consistent with the data but not tested): the unchanged output template pre-fills exactly one evidence record (EV_001) and gives `evidence_ids: ["EV_001"]` only for `chief_complaint`, with `[]` for every other section. The model reproduces exactly that: one EV_001 and a chief complaint pointing to it. The added instructions asked for a multi-step bookkeeping procedure (number records in first-citation order while writing earlier sections) that a 0.6B model does not follow. I did not test this explanation.

## 6. Comparison with P01 and P02
P03 neither helps evidence (0% strict grounding) nor extraction (F1 0.055 on these ids vs P02 0.121 on all 50, and not comparable sample sizes). P01 and P02 also left evidence unchanged (4/455 and 0/675 grounded on 50 ids). No prompt so far changed the one-record behaviour.

## 7. Pre-registered criteria, partial and indicative (defined for 50 records; NOT a final verdict)
| Criterion | Partial value (35 ids) | Status | Can the 15 missing records change it? |
|---|---|---|---|
| E1 >= 50% items cite a valid record | 15.7% (28/178) | FAIL | No: even if every one of about 80 further items were valid, 108/258 = 42% |
| E2 >= 10% strict+lenient grounded | 0% | FAIL | No (0 of 178; would need 18+ more with about 80 items left, and the pattern shows none) |
| E3 >= 75% valid evidence records | 84.8% | PASS (vacuous: single copied greeting record) | Possibly |
| E4 >= 70% timestamps within +-1 s | 0% (0/33) | FAIL | No: 15 more records could give at most 15/48 = 31% |
| E5 supports >= 80% non-empty and >= 70% reciprocal | 51.5% / 82.3% | FAIL | Not realistically |
| E6 >= 5 evidence records per encounter | 1.0 | FAIL | No (every record has 1) |
| G1 F1 >= 0.042 and precision >= 0.187 | 0.055 / 0.225 | PASS | Possibly |
| G2 predicted items >= 70% of P00 | 110% (178/161) | PASS | Possibly |
| G3 valid JSON, non-stop, tokens | 33/35 (94.3%), 0 non-stop, mean 977 | PASS on partial (the 46/50 threshold is not directly comparable) | Unknown |
| G4 unsupported <= 10%, duplicates <= 5% | 5.1%, 0% | PASS | Possibly |
| G5 speaker attribution >= 41.3% | 36.8% (38 evaluated) | FAIL (small denominator) | Possible but unlikely |
Five evidence criteria (E1, E2, E4, E5, E6) fail in a way the remaining 15 records cannot repair arithmetically. Under the pre-registered rule (all criteria must pass), P03 would be REJECT. This is stated as a strong indication from partial data, not as a completed experiment.

## 8. Limitations of the partial evaluation
35 of 50 records (the 15 unprocessed are the largest ids in the sorted list and were not chosen by difficulty, but I did not check they are representative); small samples and wide intervals; P00 paired only on the same ids; evidence metrics are structural and lexical, not clinical; the E3/G-criteria partial values are not final; the hard kill lost one in-flight record; the heuristic that the model's behavior is template anchoring is untested. Speaker-attribution denominators differ (38 vs 34).

## 9. Recommendation
**Reject P03 as designed.** Instruction-only evidence rules did not change the model's behavior: one greeting record, only the chief complaint cites it, timestamps invented or unconverted, 0% grounded. I recommend redesigning rather than re-running or finishing the remaining 15 records (about 3 more GPU hours that cannot change the verdict). A redesign (P04, not created, needs your approval) should address the likely causes: the template's single pre-filled evidence example and `["EV_001"]` anchor, and the need for the model to track numbering across sections. Options to discuss: (a) change the template so that every section shows a non-empty evidence_ids example and several evidence records (a template change beyond "instructions only"); (b) give one worked example of a segment -> record mapping with generic content; (c) a two-step prompt (extract first, then cite) which needs a second inference pass and code outside the current runner; (d) have evidence assembled by code from the segment ids (the model cites segment ids only), which would test grounding without relying on the 0.6B model copying text, but changes the task definition. I have not started any of these.

## 10. Artifacts
`evaluation/P03_PARTIAL/partial_evaluation.json` (all numbers), `evaluation/P03_PARTIAL/evidence_inspection.json` (per-encounter evidence details and statistics), `evaluation/P03_PARTIAL/P03_evidence_grounded_dev50/` (evaluator report on the partial manifest), `evaluation/evidence_diagnostics_P03_PARTIAL35.json` and `..._P00_PARTIAL35.json`, `experiments/partial_eval_p03.py`, `experiments/inspect_p03_evidence.py`, `outputs/P03_evidence_grounded_dev50/` (raw, parsed, failed, logs).
