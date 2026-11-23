# S0.2 (S0.2.0): fill absent nullable fields with null

Approved by the owner on 2026-11-13. Separate versioned layer on top of the S0.1 repaired copies; originals (`data/original/`) and S0.1 copies (`data/repaired/`) are untouched; S0.2 copies are in `data/repaired_s0_2/`; every addition is in `logs/transformations_s0_2_<source>.jsonl`. No model, inference, P00-P05 or frozen-schema change; prompt_dev ids only (0 locked-test, sealed-file or validation accesses, `results/s0_2_metrics.json`).
S0.2 is a structural repair. It does not improve clinical extraction accuracy and nothing here should be read as such.

## What counts as "explicitly nullable"
The frozen schema file lists key sets but does not declare types, so nullability is decided from the two written sources: (1) the field's default in the output template given to the model (`P02_comprehensive_extraction.txt`) is `null`, checked automatically by `verify_against_template` (0 problems), and (2) the schema documents: unstated information is `null`, and every `confidence` / `role_confidence` must be null. Fields whose default is a list or an object (`evidence_ids`, `associated_symptoms`, `duration` objects, ...) are not nullable and are never filled. Fillable fields: `confidence` (all categories), medication `normalized_name/generic_name/dose/route/frequency/duration/indication`, symptom `severity/frequency/onset/body_site`, history `duration/timeframe/details`, allergy `reaction`, vital `value`, exam `body_site`, ROS `details`, assessment `basis`, procedure `requested_by/indication/scheduled_datetime`, action `time_reference`, follow-up `normalized_datetime`, `encounter_date`, `role_confidence`.
Rules: add a key only when it is absent; never change an existing value (including empty strings and enum errors); never infer; never create a negative finding.

## Results (50 prompt_dev records per source)
| | P02_stage1 | P05_final_v4 |
|---|---:|---:|
| Fully schema-compliant records: original / after S0.1 / after S0.2 | 0 / 0 / 0 of 50 | 0 / 0 / 2 of 50 |
| Total violations: original / S0.1 / S0.2 | 1,064 / 1,008 / **346** | 945 / 845 / **183** |
| missing_field | 814 / 842 / **180** | 700 / 713 / **51** |
| enum_violation | 208 / 157 / 157 | 203 / 123 / 123 |
| wrong_type | 33 / 0 / 0 | 33 / 0 / 0 |
| unexpected_field | 9 / 9 / 9 | 9 / 9 / 9 |
| Null fields added | 662 | 662 |
| Existing values changed or removed (all leaves compared) | 0 | 0 |
| Second S0.2 pass changes | 0 | 0 |
| Second full pass (S0.1 on the S0.2 output) changes | 0 | 0 |
| Strict evaluator TP/FP/FN, S0.1 vs S0.2 | 176/532/1,684 both | identical |

Added by field: `confidence` 505, `duration` 50, `indication` 48, `generic_name` 32, `frequency` 8, `dose` 7, `route` 7, `scheduled_datetime` 4, `basis` 1.
Remaining violations after S0.2 (not nullable, so not touched): missing list/enum-type fields (`follow_up.evidence_ids` 35, `medications.evidence_ids` 24, `medications.reported_by` 23, `allergies.evidence_ids` 11, ...) and invalid values (`symptoms.certainty=None` 24, `clinical_actions.action_type` 23, `social_history.category/status` 16 each, blank `vital_signs.reported_by` 13). These need model or review-based correction, not S0.
Validators run: the frozen `schema_validator` (all three states, both sources) and the frozen strict evaluator `score_encounter` (S0.1 vs S0.2: identical scores, so the layer did not alter matching). Tests: `test_s0_2.py` 9/9 pass, `test_s0_repair.py` 23/23 still pass.

## Reading the numbers
- The fall in violations (P02 1,008 -> 346; P05 845 -> 183) is mostly 505 absent `confidence` keys the model omitted. It shows the output is easier to validate, not that it is more correct: enum errors (157 / 123), omitted evidence ids and every clinical issue flagged by S0.1 remain.
- Not done by design: filling `evidence_ids` with `[]`, defaulting enum values, creating "no" findings for unknown information.
