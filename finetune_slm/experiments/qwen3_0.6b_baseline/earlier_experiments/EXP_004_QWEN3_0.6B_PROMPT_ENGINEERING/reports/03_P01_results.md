# P01 (schema-focused) - results on the 50 prompt-development records

Run `P01_schema_focused_dev50`, prompt sha256 `9095b501...7a99` (approved, unchanged). Same model, GPU, settings and ids as the P00 reference (EXP_003 outputs for the same 50 ids; P00 reproducibility 3/3 byte-identical).
Inference: 50/50 parsed, 0 failed, all `finish_reason=stop`, 0 label/blueprint files opened (audit: 610 files). Evaluator unmodified. Locked test set and validation set not touched.

## Decision under the pre-registered rule: REJECT

| Criterion | Need | P01 vs P00 | Result |
|---|---|---|---|
| Total schema violations | down >= 30% | 444 -> 658 (**+48%**) | FAIL |
| wrong_type violations | down >= 80% | 80 -> 51 (-36%) | FAIL |
| Valid JSON | not worse by > 2 | 48 -> 50 (+2) | pass |
| Micro F1 | drop <= 0.005 | 0.047 -> 0.095 (+0.048) | pass |
| Category with P00 F1 > 0.1 loses > 0.05 | none | none | pass |
| Output collapse (<0.70x tokens or entities) | none | tokens 1.39x, entities 2.20x | pass |

The first two conditions fail, so P01 is rejected as specified. "Keep with changes" would need a targeted wording fix run as P01b; I have not started it.

## Schema (same 50 ids)

| | P00 | P01 |
|---|---|---|
| Valid / invalid JSON | 48 / 2 | 50 / 0 |
| Fully schema-compliant records | 0 | 0 |
| Violations total | 444 | 658 |
| missing_field | 245 | 520 |
| wrong_type | 80 | 51 |
| invalid_enum | 112 | 86 |
| unexpected_field | 7 | 1 |
| Violations per valid record | 9.25 | 13.16 |
| Items extracted per valid record | 4.4 (209 total) | 9.1 (455 total) |
| Violations per extracted item | 2.1 | 1.45 |

## Accuracy (strict evaluator, same 50 ids)

| | P00 | P01 |
|---|---|---|
| TP / FP / FN | 49 / 158 / 1811 | 110 / 345 / 1750 |
| Precision | 0.237 | 0.242 |
| Recall | 0.026 | 0.059 |
| Micro F1 | 0.047 | 0.095 |
| Macro F1 | 0.048 | 0.086 |

Paired bootstrap 95% interval for the micro-F1 difference: [+0.027, +0.070] (excludes 0, but n=50 and absolute F1 is still very low). Precision is essentially unchanged; the gain is recall.
Category F1 (P00 -> P01): medications 0.30 -> 0.41, vital_signs 0.05 -> 0.26, clinical_assessment 0 -> 0.125, procedures 0 -> 0.12, allergies 0.21 -> 0.25, symptoms 0.09 -> 0.10, family_history 0 -> 0.06, clinical_conditions 0 -> 0.03, follow_up 0 -> 0.03, clinical_actions 0 -> 0.007; social_history 0.013 -> 0 and clinical_uncertainties 0.044 -> 0 (both from a P00 F1 below 0.1, so outside the loss rule). chief_complaint (0.02), negative_findings, physical_examination and review_of_systems stay at or near 0.

## What the schema numbers actually show
* **Fixed or largely fixed:** `primary_speakers` missing 30 records -> 0 (not in the top patterns); `physical_examination` as object 13 -> 0; `symptoms.certainty` null 15 -> none in the top patterns; evidence records missing `supports` 25 -> 6; invalid JSON 2 -> 0.
* **Not fixed:** `clinical_assessment` is still emitted as an object in **43/50** records (48/48 for P00). Despite an explicit rule, this single pattern accounts for 43 of the 51 wrong_type violations. `follow_up` as object 9 -> 5.
* **Missing `confidence` fields persist** despite the rule (vital_signs 62, symptoms 52, medications 47, conditions 34, ...), and unprompted optional keys (`medications.generic_name`, `indication`, `dose`, `follow_up.evidence_ids`) are omitted. The count rose because the model now writes about twice as many items, each with the same omission habit. So raw violation totals are partly a volume effect; per item the rate fell (2.1 -> 1.45), but the pre-registered rule uses totals and I applied it as written.
* Remaining enums: `symptoms.status='current'` (11), `allergies.allergy_type='none'` (8), `symptoms.category='skin'` (8).
* Not a compliance-by-emptiness result: P01 outputs are larger, not emptier. Still empty in most records: past_medical_history 47/50, family_history 48, social_history 48, surgical_history 41, clinical_uncertainties 42, negative_findings 38 (15 items in 50 records vs 543 gold negatives overall in the earlier analysis).

## Other required metrics (P01, 50 ids)
* Speaker attribution 65.6% (63/96 evaluated); patient 34/50, doctor 29/33, nurse 0/9, family_member 0/3, caregiver 0/1. EXP_003's 51% was on 94 records, so this is not a paired figure; I did not rescore P00 on these 50 ids.
* Evidence grounding: 4/455 entities strictly grounded, 35 partially, 416 (91%) unsupported; still one evidence record per encounter (mean 1.0).
* Unsupported claims: 40/455 predictions (8.8%); 305 of the 345 false positives are transcript-supported extras (terminology/granularity), consistent with the EXP_003 finding.
* Vital signs: name found 37/219, value correct 17 (7.8%).
* Latency 210 s mean (P00 153 s; +37%), 5.6 tokens/s, mean output 1,195 tokens (P00 863), total 2.9 h. Prompt tokens mean 4,143.

## Interpretation (hypotheses, not established)
* The structure rules fixed the surface problems they named for roles, certainty, primary_speakers and supports, but did not fix the dominant one (assessment as object) and did not remove the omission of optional/confidence keys.
* P01 was expected not to change recall. It nearly doubled it. I do not know why; plausible mechanisms are that a longer, more explicit template-restating prompt changes how much the model writes, or that the rules about empty lists and per-section arrays encourage filling sections. This was not tested, so treat it as an observation only. The effect is a confound for any later version built on P01.
* Absolute performance is still very low (micro F1 0.095, recall 0.059, 0 fully compliant records).

## Remaining error types
Chief complaint wrong (~49/50), negatives and history sections nearly empty, clinical_actions recall about 0.4%, evidence grounding, nurse/family speaker roles, assessment-as-object, confidence/optional-key omission.

## Caveats
n=50 single run of a deterministic greedy decode; bootstrap resamples encounters only. The P00 reference is the earlier EXP_003 run (reproducibility verified on 3 records only). Keep/reject was decided by the rules approved before the run, with no post-hoc change.

## Artifacts
`evaluation/P01_schema_focused_dev50/` (`paired_comparison_vs_P00.json`, `pattern_analysis.json`, `evaluation_report.json/.md`, per_encounter/), `outputs/P01_schema_focused_dev50/`, `experiments/analyze_run_patterns.py`, `experiments/evaluate_run.py`.
