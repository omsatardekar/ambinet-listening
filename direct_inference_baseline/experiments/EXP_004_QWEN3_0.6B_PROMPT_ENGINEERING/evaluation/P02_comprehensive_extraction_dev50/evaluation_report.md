# Direct inference baseline report - P02_comprehensive_extraction_dev50

Model: `Qwen/Qwen3-0.6B` via **openvino_genai**; split **development**; dataset manifest `4403fef843fb...`; prompt `cf50ce8efe85...`; max_new_tokens 6144.

## Coverage and failures

Requested 50, attempted 50, valid JSON 50 (100.0% of requested), failed 0 (failure rate 0.0%).
Failure types: none.

## JSON and schema

| Metric | Value |
|---|---|
| JSON validity | 100.0% |
| Truncated (hit token budget) | 0.0% |
| Malformed JSON (not truncated) | 0.0% |
| Schema compliance among valid JSON | 0.0% |
| Schema compliance end-to-end | 0.0% |
| Required field completeness (valid JSON) | 89.5% |
| Unexpected field rate | 0.1% |

## Entity extraction - End-to-end (failures count as all-FN)

Encounters: 50. Strict exact normalised matching.

| | Precision | Recall | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| Micro | 0.227 | 0.082 | 0.121 | 153 | 522 | 1707 |
| Macro | 0.198 | 0.100 | 0.122 | | | |

Fuzzy (reported separately): micro F1 0.135, macro F1 0.145.

| Category | P | R | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| chief_complaint | 0.140 | 0.140 | 0.140 | 7 | 43 | 43 |
| symptoms | 0.204 | 0.073 | 0.108 | 11 | 43 | 139 |
| negative_findings | 0.000 | 0.000 | 0.000 | 0 | 51 | 273 |
| medical_history.past_medical_history | 0.182 | 0.043 | 0.069 | 4 | 18 | 90 |
| medical_history.surgical_history | 0.158 | 0.111 | 0.130 | 3 | 16 | 24 |
| medical_history.family_history | 0.250 | 0.138 | 0.178 | 4 | 12 | 25 |
| medical_history.social_history | 0.000 | 0.000 | 0.000 | 0 | 16 | 151 |
| medications | 0.807 | 0.359 | 0.497 | 46 | 11 | 82 |
| allergies | 0.250 | 0.375 | 0.300 | 9 | 27 | 15 |
| vital_signs | 0.500 | 0.187 | 0.272 | 41 | 41 | 178 |
| physical_examination | 0.016 | 0.013 | 0.014 | 1 | 62 | 79 |
| review_of_systems | 0.143 | 0.086 | 0.107 | 6 | 36 | 64 |
| clinical_conditions | 0.022 | 0.026 | 0.024 | 1 | 44 | 38 |
| clinical_assessment | 0.320 | 0.090 | 0.140 | 8 | 17 | 81 |
| procedures_and_investigations | 0.265 | 0.110 | 0.155 | 9 | 25 | 73 |
| clinical_actions | 0.026 | 0.004 | 0.007 | 1 | 38 | 265 |
| follow_up | 0.083 | 0.044 | 0.058 | 2 | 22 | 43 |
| clinical_uncertainties | n/a | 0.000 | 0.000 | 0 | 0 | 44 |

Medical history (4 sub-categories pooled): P 0.151 R 0.037 F1 0.059.

### Clinical metrics

* Vital sign accuracy: 10.0% over 219 gold vitals (name found 18.7%).
* Speaker attribution accuracy: 42.1% over 126 matched entities (excluded: 3 records with an unknown speaker, 0 entities).
* Negation: 0.0% of gold negative findings reproduced; polarity flips: 0 (negative reported as present), 0 (present reported as negative).
* Evidence grounding (of 675 predicted entities): strict 0.0%, grounded incl. lenient 0.0%, partially supported 0.9%, unsupported 99.1%.
* Unsupported claims: 85 of 679 predicted entities (12.5%); 437 further FPs are transcript-supported.

### Attribute accuracy (matched entities)

| Attribute | Accuracy (gold non-null) | n | False-attribute rate (gold null) | n |
|---|---|---|---|---|
| severity | 16.7% | 6 | 20.0% | 5 |
| duration | 0.0% | 5 | 0.0% | 6 |
| dose | 87.5% | 40 | 83.3% | 6 |
| medication_frequency | 71.1% | 45 | 100.0% | 1 |
| medication_route | 50.0% | 2 | 90.9% | 44 |
| action_status | 0.0% | 1 | n/a | 0 |
| investigation_status | 100.0% | 9 | n/a | 0 |
| temporality | 90.9% | 11 | n/a | 0 |
| negation | n/a | 0 | n/a | 0 |
| allergy_reaction | 42.9% | 7 | 100.0% | 2 |
| uncertainty_status | 35.0% | 20 | n/a | 0 |

## Entity extraction - Valid-JSON encounters only

Encounters: 50. Strict exact normalised matching.

| | Precision | Recall | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| Micro | 0.227 | 0.082 | 0.121 | 153 | 522 | 1707 |
| Macro | 0.198 | 0.100 | 0.122 | | | |

Fuzzy (reported separately): micro F1 0.135, macro F1 0.145.

| Category | P | R | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| chief_complaint | 0.140 | 0.140 | 0.140 | 7 | 43 | 43 |
| symptoms | 0.204 | 0.073 | 0.108 | 11 | 43 | 139 |
| negative_findings | 0.000 | 0.000 | 0.000 | 0 | 51 | 273 |
| medical_history.past_medical_history | 0.182 | 0.043 | 0.069 | 4 | 18 | 90 |
| medical_history.surgical_history | 0.158 | 0.111 | 0.130 | 3 | 16 | 24 |
| medical_history.family_history | 0.250 | 0.138 | 0.178 | 4 | 12 | 25 |
| medical_history.social_history | 0.000 | 0.000 | 0.000 | 0 | 16 | 151 |
| medications | 0.807 | 0.359 | 0.497 | 46 | 11 | 82 |
| allergies | 0.250 | 0.375 | 0.300 | 9 | 27 | 15 |
| vital_signs | 0.500 | 0.187 | 0.272 | 41 | 41 | 178 |
| physical_examination | 0.016 | 0.013 | 0.014 | 1 | 62 | 79 |
| review_of_systems | 0.143 | 0.086 | 0.107 | 6 | 36 | 64 |
| clinical_conditions | 0.022 | 0.026 | 0.024 | 1 | 44 | 38 |
| clinical_assessment | 0.320 | 0.090 | 0.140 | 8 | 17 | 81 |
| procedures_and_investigations | 0.265 | 0.110 | 0.155 | 9 | 25 | 73 |
| clinical_actions | 0.026 | 0.004 | 0.007 | 1 | 38 | 265 |
| follow_up | 0.083 | 0.044 | 0.058 | 2 | 22 | 43 |
| clinical_uncertainties | n/a | 0.000 | 0.000 | 0 | 0 | 44 |

Medical history (4 sub-categories pooled): P 0.151 R 0.037 F1 0.059.

### Clinical metrics

* Vital sign accuracy: 10.0% over 219 gold vitals (name found 18.7%).
* Speaker attribution accuracy: 42.1% over 126 matched entities (excluded: 3 records with an unknown speaker, 0 entities).
* Negation: 0.0% of gold negative findings reproduced; polarity flips: 0 (negative reported as present), 0 (present reported as negative).
* Evidence grounding (of 675 predicted entities): strict 0.0%, grounded incl. lenient 0.0%, partially supported 0.9%, unsupported 99.1%.
* Unsupported claims: 85 of 679 predicted entities (12.5%); 437 further FPs are transcript-supported.

### Attribute accuracy (matched entities)

| Attribute | Accuracy (gold non-null) | n | False-attribute rate (gold null) | n |
|---|---|---|---|---|
| severity | 16.7% | 6 | 20.0% | 5 |
| duration | 0.0% | 5 | 0.0% | 6 |
| dose | 87.5% | 40 | 83.3% | 6 |
| medication_frequency | 71.1% | 45 | 100.0% | 1 |
| medication_route | 50.0% | 2 | 90.9% | 44 |
| action_status | 0.0% | 1 | n/a | 0 |
| investigation_status | 100.0% | 9 | n/a | 0 |
| temporality | 90.9% | 11 | n/a | 0 |
| negation | n/a | 0 | n/a | 0 |
| allergy_reaction | 42.9% | 7 | 100.0% | 2 |
| uncertainty_status | 35.0% | 20 | n/a | 0 |

## Performance

* Latency per encounter (s): {'mean': 235.464, 'median': 232.935, 'p95': 331.416, 'min': 118.317, 'max': 464.119, 'n': 50}
* Completion tokens: {'mean': 1356.34, 'median': 1327.5, 'p95': 1913, 'min': 640, 'max': 2674, 'n': 50}
* Prompt tokens: {'mean': 4329.08, 'median': 4256.0, 'p95': 4886, 'min': 3775, 'max': 5177, 'n': 50}
* Tokens/second: {'mean': 5.734, 'median': 5.767, 'p95': 6.069, 'min': 4.803, 'max': 6.123, 'n': 50}
* Total generation time: 3.27 h; finish reasons {'stop': 50}; repetition flagged in 0 outputs.

## By complexity (end-to-end, strict micro)

| Complexity | Encounters | Valid JSON | P | R | F1 |
|---|---|---|---|---|---|
| challenging | 6 | 6 | 0.257 | 0.096 | 0.139 |
| complex | 17 | 17 | 0.239 | 0.084 | 0.124 |
| moderate | 18 | 18 | 0.217 | 0.087 | 0.124 |
| simple | 9 | 9 | 0.178 | 0.051 | 0.080 |

## By specialty (end-to-end, strict micro)

| Specialty | Encounters | Valid JSON | P | R | F1 |
|---|---|---|---|---|---|
| Cardiology | 6 | 6 | 0.145 | 0.041 | 0.064 |
| Dermatology | 3 | 3 | 0.237 | 0.092 | 0.132 |
| ENT / Ophthalmology | 2 | 2 | 0.294 | 0.064 | 0.105 |
| Endocrinology | 4 | 4 | 0.159 | 0.073 | 0.100 |
| Gastroenterology | 4 | 4 | 0.243 | 0.113 | 0.154 |
| General Medicine / Infectious Diseases | 8 | 8 | 0.253 | 0.077 | 0.118 |
| Gynaecology | 2 | 2 | 0.273 | 0.083 | 0.128 |
| Mental Health / Other | 4 | 4 | 0.228 | 0.097 | 0.136 |
| Musculoskeletal / Orthopaedics | 4 | 4 | 0.200 | 0.069 | 0.103 |
| Nephrology / Urology | 3 | 3 | 0.261 | 0.106 | 0.151 |
| Neurology | 5 | 5 | 0.256 | 0.106 | 0.150 |
| Respiratory Medicine | 5 | 5 | 0.243 | 0.087 | 0.128 |

## Definitions

* **entity_matching**: Strict: normalised primary key per category, multiset TP/FP/FN (see entity_matching.py). Fuzzy reported separately.
* **undefined_values**: Precision/recall/F1 are null (undefined) when their denominator is zero; they are never set to 0 or 1. Macro averages only categories with a defined value.
* **end_to_end vs valid_only**: end_to_end counts an encounter without a usable prediction as all-FN; valid_only excludes such encounters.
* **attribute_accuracy**: On strictly matched entities only: accuracy over gold-non-null values, and a separate false-attribute rate where gold is null.
* **grounding**: grounded_strict / grounded_lenient / partially_supported / unsupported, see evidence_evaluator.py (lexical, not clinical correctness).
* **unsupported_claims**: Strict FPs whose key is not lexically supported anywhere in the transcript; denominator reported.

Automated evaluation only; scores reflect lexical/normalised matching to the frozen labels and are not a clinical-quality judgement.
