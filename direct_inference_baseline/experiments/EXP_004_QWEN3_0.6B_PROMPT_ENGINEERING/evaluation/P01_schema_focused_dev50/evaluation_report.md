# Direct inference baseline report - P01_schema_focused_dev50

Model: `Qwen/Qwen3-0.6B` via **openvino_genai**; split **development**; dataset manifest `4403fef843fb...`; prompt `9095b50196c4...`; max_new_tokens 6144.

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
| Required field completeness (valid JSON) | 92.1% |
| Unexpected field rate | 0.0% |

## Entity extraction - End-to-end (failures count as all-FN)

Encounters: 50. Strict exact normalised matching.

| | Precision | Recall | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| Micro | 0.242 | 0.059 | 0.095 | 110 | 345 | 1750 |
| Macro | 0.210 | 0.061 | 0.086 | | | |

Fuzzy (reported separately): micro F1 0.102, macro F1 0.103.

| Category | P | R | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| chief_complaint | 0.020 | 0.020 | 0.020 | 1 | 49 | 49 |
| symptoms | 0.134 | 0.073 | 0.095 | 11 | 71 | 139 |
| negative_findings | 0.000 | 0.000 | 0.000 | 0 | 15 | 273 |
| medical_history.past_medical_history | 0.143 | 0.011 | 0.020 | 1 | 6 | 93 |
| medical_history.surgical_history | 0.222 | 0.074 | 0.111 | 2 | 7 | 25 |
| medical_history.family_history | 0.333 | 0.034 | 0.062 | 1 | 2 | 28 |
| medical_history.social_history | 0.000 | 0.000 | 0.000 | 0 | 2 | 151 |
| medications | 0.766 | 0.281 | 0.411 | 36 | 11 | 92 |
| allergies | 0.250 | 0.250 | 0.250 | 6 | 18 | 18 |
| vital_signs | 0.597 | 0.169 | 0.263 | 37 | 25 | 182 |
| physical_examination | 0.000 | 0.000 | 0.000 | 0 | 27 | 80 |
| review_of_systems | 0.000 | 0.000 | 0.000 | 0 | 20 | 70 |
| clinical_conditions | 0.029 | 0.026 | 0.027 | 1 | 34 | 38 |
| clinical_assessment | 0.857 | 0.067 | 0.125 | 6 | 1 | 83 |
| procedures_and_investigations | 0.316 | 0.073 | 0.119 | 6 | 13 | 76 |
| clinical_actions | 0.045 | 0.004 | 0.007 | 1 | 21 | 265 |
| follow_up | 0.062 | 0.022 | 0.033 | 1 | 15 | 44 |
| clinical_uncertainties | 0.000 | 0.000 | 0.000 | 0 | 8 | 44 |

Medical history (4 sub-categories pooled): P 0.190 R 0.013 F1 0.025.

### Clinical metrics

* Vital sign accuracy: 7.8% over 219 gold vitals (name found 16.9%).
* Speaker attribution accuracy: 65.6% over 96 matched entities (excluded: 3 records with an unknown speaker, 0 entities).
* Negation: 0.0% of gold negative findings reproduced; polarity flips: 3 (negative reported as present), 1 (present reported as negative).
* Evidence grounding (of 455 predicted entities): strict 0.9%, grounded incl. lenient 0.9%, partially supported 7.7%, unsupported 91.4%.
* Unsupported claims: 40 of 455 predicted entities (8.8%); 305 further FPs are transcript-supported.

### Attribute accuracy (matched entities)

| Attribute | Accuracy (gold non-null) | n | False-attribute rate (gold null) | n |
|---|---|---|---|---|
| severity | 33.3% | 3 | 25.0% | 8 |
| duration | 0.0% | 2 | 0.0% | 9 |
| dose | 51.6% | 31 | 40.0% | 5 |
| medication_frequency | 34.3% | 35 | 100.0% | 1 |
| medication_route | n/a | 0 | 100.0% | 36 |
| action_status | 0.0% | 1 | n/a | 0 |
| investigation_status | 100.0% | 6 | n/a | 0 |
| temporality | 81.8% | 11 | n/a | 0 |
| negation | n/a | 0 | n/a | 0 |
| allergy_reaction | 0.0% | 6 | n/a | 0 |
| uncertainty_status | 35.3% | 17 | n/a | 0 |

## Entity extraction - Valid-JSON encounters only

Encounters: 50. Strict exact normalised matching.

| | Precision | Recall | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| Micro | 0.242 | 0.059 | 0.095 | 110 | 345 | 1750 |
| Macro | 0.210 | 0.061 | 0.086 | | | |

Fuzzy (reported separately): micro F1 0.102, macro F1 0.103.

| Category | P | R | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| chief_complaint | 0.020 | 0.020 | 0.020 | 1 | 49 | 49 |
| symptoms | 0.134 | 0.073 | 0.095 | 11 | 71 | 139 |
| negative_findings | 0.000 | 0.000 | 0.000 | 0 | 15 | 273 |
| medical_history.past_medical_history | 0.143 | 0.011 | 0.020 | 1 | 6 | 93 |
| medical_history.surgical_history | 0.222 | 0.074 | 0.111 | 2 | 7 | 25 |
| medical_history.family_history | 0.333 | 0.034 | 0.062 | 1 | 2 | 28 |
| medical_history.social_history | 0.000 | 0.000 | 0.000 | 0 | 2 | 151 |
| medications | 0.766 | 0.281 | 0.411 | 36 | 11 | 92 |
| allergies | 0.250 | 0.250 | 0.250 | 6 | 18 | 18 |
| vital_signs | 0.597 | 0.169 | 0.263 | 37 | 25 | 182 |
| physical_examination | 0.000 | 0.000 | 0.000 | 0 | 27 | 80 |
| review_of_systems | 0.000 | 0.000 | 0.000 | 0 | 20 | 70 |
| clinical_conditions | 0.029 | 0.026 | 0.027 | 1 | 34 | 38 |
| clinical_assessment | 0.857 | 0.067 | 0.125 | 6 | 1 | 83 |
| procedures_and_investigations | 0.316 | 0.073 | 0.119 | 6 | 13 | 76 |
| clinical_actions | 0.045 | 0.004 | 0.007 | 1 | 21 | 265 |
| follow_up | 0.062 | 0.022 | 0.033 | 1 | 15 | 44 |
| clinical_uncertainties | 0.000 | 0.000 | 0.000 | 0 | 8 | 44 |

Medical history (4 sub-categories pooled): P 0.190 R 0.013 F1 0.025.

### Clinical metrics

* Vital sign accuracy: 7.8% over 219 gold vitals (name found 16.9%).
* Speaker attribution accuracy: 65.6% over 96 matched entities (excluded: 3 records with an unknown speaker, 0 entities).
* Negation: 0.0% of gold negative findings reproduced; polarity flips: 3 (negative reported as present), 1 (present reported as negative).
* Evidence grounding (of 455 predicted entities): strict 0.9%, grounded incl. lenient 0.9%, partially supported 7.7%, unsupported 91.4%.
* Unsupported claims: 40 of 455 predicted entities (8.8%); 305 further FPs are transcript-supported.

### Attribute accuracy (matched entities)

| Attribute | Accuracy (gold non-null) | n | False-attribute rate (gold null) | n |
|---|---|---|---|---|
| severity | 33.3% | 3 | 25.0% | 8 |
| duration | 0.0% | 2 | 0.0% | 9 |
| dose | 51.6% | 31 | 40.0% | 5 |
| medication_frequency | 34.3% | 35 | 100.0% | 1 |
| medication_route | n/a | 0 | 100.0% | 36 |
| action_status | 0.0% | 1 | n/a | 0 |
| investigation_status | 100.0% | 6 | n/a | 0 |
| temporality | 81.8% | 11 | n/a | 0 |
| negation | n/a | 0 | n/a | 0 |
| allergy_reaction | 0.0% | 6 | n/a | 0 |
| uncertainty_status | 35.3% | 17 | n/a | 0 |

## Performance

* Latency per encounter (s): {'mean': 210.184, 'median': 157.13, 'p95': 377.001, 'min': 115.828, 'max': 446.576, 'n': 50}
* Completion tokens: {'mean': 1195.3, 'median': 886.5, 'p95': 2297, 'min': 662, 'max': 2595, 'n': 50}
* Prompt tokens: {'mean': 4143.08, 'median': 4070.0, 'p95': 4700, 'min': 3589, 'max': 4991, 'n': 50}
* Tokens/second: {'mean': 5.618, 'median': 5.628, 'p95': 6.099, 'min': 4.697, 'max': 6.279, 'n': 50}
* Total generation time: 2.919 h; finish reasons {'stop': 50}; repetition flagged in 0 outputs.

## By complexity (end-to-end, strict micro)

| Complexity | Encounters | Valid JSON | P | R | F1 |
|---|---|---|---|---|---|
| challenging | 6 | 6 | 0.258 | 0.059 | 0.096 |
| complex | 17 | 17 | 0.241 | 0.075 | 0.115 |
| moderate | 18 | 18 | 0.231 | 0.051 | 0.084 |
| simple | 9 | 9 | 0.265 | 0.035 | 0.062 |

## By specialty (end-to-end, strict micro)

| Specialty | Encounters | Valid JSON | P | R | F1 |
|---|---|---|---|---|---|
| Cardiology | 6 | 6 | 0.222 | 0.036 | 0.062 |
| Dermatology | 3 | 3 | 0.231 | 0.061 | 0.097 |
| ENT / Ophthalmology | 2 | 2 | 0.258 | 0.103 | 0.147 |
| Endocrinology | 4 | 4 | 0.314 | 0.106 | 0.158 |
| Gastroenterology | 4 | 4 | 0.200 | 0.060 | 0.092 |
| General Medicine / Infectious Diseases | 8 | 8 | 0.216 | 0.070 | 0.106 |
| Gynaecology | 2 | 2 | 0.200 | 0.014 | 0.026 |
| Mental Health / Other | 4 | 4 | 0.357 | 0.037 | 0.068 |
| Musculoskeletal / Orthopaedics | 4 | 4 | 0.280 | 0.044 | 0.076 |
| Nephrology / Urology | 3 | 3 | 0.167 | 0.035 | 0.058 |
| Neurology | 5 | 5 | 0.211 | 0.043 | 0.071 |
| Respiratory Medicine | 5 | 5 | 0.270 | 0.087 | 0.131 |

## Definitions

* **entity_matching**: Strict: normalised primary key per category, multiset TP/FP/FN (see entity_matching.py). Fuzzy reported separately.
* **undefined_values**: Precision/recall/F1 are null (undefined) when their denominator is zero; they are never set to 0 or 1. Macro averages only categories with a defined value.
* **end_to_end vs valid_only**: end_to_end counts an encounter without a usable prediction as all-FN; valid_only excludes such encounters.
* **attribute_accuracy**: On strictly matched entities only: accuracy over gold-non-null values, and a separate false-attribute rate where gold is null.
* **grounding**: grounded_strict / grounded_lenient / partially_supported / unsupported, see evidence_evaluator.py (lexical, not clinical correctness).
* **unsupported_claims**: Strict FPs whose key is not lexically supported anywhere in the transcript; denominator reported.

Automated evaluation only; scores reflect lexical/normalised matching to the frozen labels and are not a clinical-quality judgement.
