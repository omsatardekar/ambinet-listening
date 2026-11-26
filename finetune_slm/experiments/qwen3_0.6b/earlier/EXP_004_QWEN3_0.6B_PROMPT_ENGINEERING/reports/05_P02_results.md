# P02 (comprehensive extraction) - results on the 50 prompt-development records

Run `P02_comprehensive_extraction_dev50`, prompt sha256 `cf50ce8e...d5` (approved and frozen, read-only, hash printed in the run log matches). Built from P00 only; no P01 rules, no evidence/speaker/negation strategy.
Same model (Qwen3-0.6B rev c1899de2), OpenVINO FP16, Intel UHD 620 GPU, greedy, thinking off, max_new_tokens 6144, same 50 ids, unmodified evaluator and schema.
Inference: 50/50 parsed, 0 failed, all finish_reason=stop, 0 label/blueprint files opened (610 files audited). Validation and locked test records not used.

## Decision under the pre-registered rule: KEEP (all 8 criteria pass)

| # | Criterion | P02 | Result |
|---|---|---|---|
| 1 | Micro recall >= 0.050 | 0.082 (P00 0.026) | pass |
| 2 | Micro F1 >= +0.030 over P00, bootstrap lower bound > 0 | +0.073 (0.047 -> 0.121); 95% CI [+0.054, +0.094] | pass |
| 3 | Micro precision >= 0.187 | 0.227 (P00 0.237) | pass |
| 4 | Valid JSON >= 46/50 and <= 2 non-stop finishes | 50/50, 0 non-stop | pass |
| 5 | No category with P00 F1 > 0.1 loses > 0.05 | none | pass |
| 6 | >= 3 of 9 low-recall categories gain >= +0.03 recall | 4 of 9 | pass (margin: see below) |
| 7 | Unsupported <= 15% and duplicates <= 5% | 12.5% and 0.15% (1 of 675) | pass |
| 8 | Mean tokens <= 3000, none at 6144 | mean 1,356, max 2,674 | pass |

Margins to note: criterion 6 passes with 4 gains (review_of_systems +0.086, assessment +0.090, procedures +0.110, follow_up +0.044) against a threshold of 3; criterion 7's unsupported rate is 12.5% against the 15% limit (P01 8.8%). Criteria were applied exactly as pre-registered.

## Accuracy, paired with P00 on the same 50 ids (strict evaluator)

| | P00 | P01 (reference only) | P02 |
|---|---|---|---|
| TP / FP / FN | 49 / 158 / 1811 | 110 / 345 / 1750 | 153 / 522 / 1707 |
| Precision | 0.237 | 0.242 | 0.227 |
| Recall | 0.026 | 0.059 | 0.082 |
| Micro F1 | 0.047 | 0.095 | 0.121 |
| Macro F1 | 0.048 | 0.086 | 0.122 |
| Fuzzy micro F1 | - | 0.102 | 0.135 |
| Items per valid record | 4.4 | 9.1 | 13.6 (36 in the gold) |

Precision is essentially unchanged; the gain is recall (about 3x P00). Absolute performance is still low: 92% of gold items are missed.

## Category metrics (strict; P00 -> P02, precision/recall/F1)
| Category | P00 F1 | P02 P | P02 R | P02 F1 | TP |
|---|---|---|---|---|---|
| chief_complaint | 0.020 | 0.14 | 0.14 | 0.140 | 7 |
| symptoms | 0.086 | 0.20 | 0.07 | 0.108 | 11 |
| negative_findings | 0 | 0 | 0 | 0 | 0 (51 predicted, 273 gold) |
| past_medical_history | 0.020 | 0.18 | 0.04 | 0.069 | 4 |
| surgical_history | 0.111 | 0.16 | 0.11 | 0.130 | 3 |
| family_history | 0 | 0.25 | 0.14 | 0.178 | 4 |
| social_history | 0.013 | 0 | 0 | 0 | 0 (16 predicted, 151 gold) |
| medications | 0.302 | 0.81 | 0.36 | 0.497 | 46 |
| allergies | 0.211 | 0.25 | 0.38 | 0.300 | 9 |
| vital_signs | 0.052 | 0.50 | 0.19 | 0.272 | 41 |
| physical_examination | 0 | 0.02 | 0.01 | 0.014 | 1 (63 predicted) |
| review_of_systems | 0 | 0.14 | 0.09 | 0.107 | 6 |
| clinical_conditions | 0 | 0.02 | 0.03 | 0.024 | 1 |
| clinical_assessment | 0 | 0.32 | 0.09 | 0.140 | 8 |
| procedures_and_investigations | 0 | 0.26 | 0.11 | 0.155 | 9 |
| clinical_actions | 0 | 0.03 | 0.004 | 0.007 | 1 |
| follow_up | 0 | 0.08 | 0.04 | 0.058 | 2 |
| clinical_uncertainties | 0.044 | - | 0 | 0 | 0 (none emitted) |

Largest gains: medications 0.30 -> 0.50, vital signs 0.05 -> 0.27, chief complaint 0.02 -> 0.14. Two P00-nonzero categories fell to 0 (social_history 0.013 -> 0; clinical_uncertainties 0.044 -> 0); both had P00 F1 below 0.1, so criterion 5 does not cover them, but they are regressions.
Where the strategy did NOT work: **negative_findings** (51 items emitted, 0 matched, strict or fuzzy; 0 of 273 gold negatives found, the same as P00), **social_history** (16 emitted, 0 matched), **physical_examination** (63 emitted, 1 matched), **clinical_actions** (39 emitted, 1 matched strict, 5 fuzzy). The model now writes content in these sections but not content that the evaluator matches. I did not inspect why for individual outputs; the earlier aggregate analysis (closed vocabularies for social_history, free-text keys for the others) suggests a naming-convention mismatch, but that is a hypothesis.

## Schema (reported, not gating)
| | P00 | P01 | P02 |
|---|---|---|---|
| Valid / invalid JSON | 48 / 2 | 50 / 0 | 50 / 0 |
| Fully schema-compliant records | 0 | 0 | 0 |
| Violations total | 444 | 658 | 1,064 |
| missing_field | 245 | 520 | 814 |
| wrong_type | 80 | 51 | 33 |
| invalid_enum | 112 | 86 | 208 |
| unexpected_field | 7 | 1 | 9 |
| Violations per valid record | 9.25 | 13.2 | 21.3 |
| Violations per extracted item | 2.1 | 1.45 | 1.57 |

Schema got worse in absolute terms, which was expected: structure is untouched and output volume rose. Missing `confidence` keys dominate (vital_signs 79, physical_examination 60, medications 54, ...) plus optional medication keys. Invalid enums roughly doubled (208 vs 112). The assessment-as-object problem is lower than P00 (20/50 records vs 48/50) even though P02 has no structure rules; follow_up as object 13/50. The primary_speakers key is not among the top patterns here (only checked via the top-violations list, not a dedicated count).
Empty sections (of 50 records): clinical_uncertainties 50, family_history 35, social_history 34, surgical_history 31, past_medical_history 28, procedures 23, clinical_actions 17.

## Other required metrics (P02, 50 ids)
* Unsupported claims: 85/679 predictions (12.5%); 437 of 522 false positives are extras that the transcript does support (terminology/granularity); P01 had 8.8%. This rose by 3.7 points as volume rose.
* Duplicates: 1 of 675 predicted items (0.15%) (P00 0, P01 0.2%).
* Evidence grounding: 0 strictly grounded, 6 partially, 669/675 (99%) unsupported (P01 91%); about one evidence record per encounter, 11 records missing `supports`. The prompt did not address evidence, so this is unchanged in kind; the figure got worse because more items sit on one evidence record.
* Speaker attribution: 42.1% (53/126); patient 20/71, doctor 33/46, family_member 0/4, caregiver 0/3, nurse 0/2. P01 was 65.6% on 96 evaluated, EXP_003 51% on a different set; the evaluated denominators differ, so compare with care. This is a regression relative to P01 and likely to P00 (not rescored on these ids).
* Vital signs: names found 41/219, value correct 22 (10.0%) (P01 7.8%).
* Negation polarity: 0/273 gold negatives found.
* Latency: 235 s mean (P00 153, P01 210), 5.7 tokens/s, 1,356 mean output tokens (P00 863), total 3.27 h; mean prompt 4,329 tokens.

## What changed, what improved, what got worse, what remains
* **Changed:** one 12-bullet coverage block added to P00; nothing else.
* **Improved:** recall about 3x (0.026 -> 0.082), micro F1 0.047 -> 0.121 (CI excludes 0), items per record 4.4 -> 13.6, 0 invalid JSON, medications, vital signs, chief complaint, allergies, assessment, procedures, review of systems.
* **Worse:** schema violation totals (+140% vs P00), speaker attribution, evidence-grounding rate, unsupported-claim rate (12.5%), latency (+54%), and two small categories to 0 (social_history, clinical_uncertainties).
* **Remaining:** negatives never matched, social history, physical examination, clinical actions (free-text keys), chief complaint (14% correct), uncertainties never emitted, schema compliance 0/50, speaker roles, evidence records.

## Comparison with P01 (informational, not a gate)
P02 beats P01 on recall (0.082 vs 0.059) and micro F1 (0.121 vs 0.095), has more items, but worse schema totals (wrong_type is lower, invalid_enum and missing_field higher), speaker attribution and evidence grounding. P01 and P02 are not additive claims: they were run independently and no combined prompt has been tested. The P01 recall effect remains unexplained; P02's larger recall gain suggests volume of extraction may be part of the mechanism, but that is not tested.

## Caveats
n=50, one deterministic greedy run; bootstrap resamples encounters only; prompt_dev was inspected in aggregate for design, so these are development results, not an unbiased estimate (validation has not been used). P00 speaker/evidence/unsupported values were not rescored on these 50 ids. Terminology gains are not separately measured. KEEP means the strategy passed its development criteria; it is not a final prompt selection.

## Artifacts
`outputs/P02_comprehensive_extraction_dev50/` (raw/parsed predictions, performance.json, file_access_audit.json, inference.log), `evaluation/P02_comprehensive_extraction_dev50/` (`paired_comparison_vs_P00.json`, `pattern_analysis.json`, evaluation_report.json/.md, per_encounter/), `experiments/evaluate_p02.py`.
