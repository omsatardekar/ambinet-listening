# Direct inference baseline report - exp_003_dev_remaining_95_interim

Model: `Qwen/Qwen3-0.6B` via **openvino_genai**; split **development**; dataset manifest `4403fef843fb...`; prompt `78c5ab95d001...`; max_new_tokens 6144.

## Coverage and failures

Requested 62, attempted 62, valid JSON 57 (91.9% of requested), failed 5 (failure rate 8.1%).
Failure types: {'invalid_json': 5}.

## JSON and schema

| Metric | Value |
|---|---|
| JSON validity | 91.9% |
| Truncated (hit token budget) | 0.0% |
| Malformed JSON (not truncated) | 8.1% |
| Schema compliance among valid JSON | 0.0% |
| Schema compliance end-to-end | 0.0% |
| Required field completeness (valid JSON) | 94.4% |
| Unexpected field rate | 0.0% |

## Entity extraction - End-to-end (failures count as all-FN)

Encounters: 62. Strict exact normalised matching.

| | Precision | Recall | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| Micro | 0.295 | 0.030 | 0.054 | 66 | 158 | 2151 |
| Macro | 0.173 | 0.041 | 0.059 | | | |

Fuzzy (reported separately): micro F1 0.056, macro F1 0.060.

| Category | P | R | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| chief_complaint | 0.070 | 0.065 | 0.067 | 4 | 53 | 58 |
| symptoms | 0.211 | 0.076 | 0.112 | 15 | 56 | 182 |
| negative_findings | 0.000 | 0.000 | 0.000 | 0 | 5 | 340 |
| medical_history.past_medical_history | 0.000 | 0.000 | 0.000 | 0 | 4 | 109 |
| medical_history.surgical_history | 0.400 | 0.121 | 0.186 | 4 | 6 | 29 |
| medical_history.family_history | 0.000 | 0.000 | 0.000 | 0 | 1 | 34 |
| medical_history.social_history | 0.000 | 0.000 | 0.000 | 0 | 1 | 181 |
| medications | 0.868 | 0.219 | 0.349 | 33 | 5 | 118 |
| allergies | 0.500 | 0.241 | 0.326 | 7 | 7 | 22 |
| vital_signs | 0.375 | 0.011 | 0.021 | 3 | 5 | 271 |
| physical_examination | 0.000 | 0.000 | 0.000 | 0 | 7 | 87 |
| review_of_systems | n/a | 0.000 | 0.000 | 0 | 0 | 84 |
| clinical_conditions | 0.000 | 0.000 | 0.000 | 0 | 6 | 45 |
| clinical_assessment | n/a | 0.000 | 0.000 | 0 | 0 | 102 |
| procedures_and_investigations | 0.000 | 0.000 | 0.000 | 0 | 1 | 92 |
| clinical_actions | 0.000 | 0.000 | 0.000 | 0 | 1 | 299 |
| follow_up | n/a | 0.000 | 0.000 | 0 | 0 | 42 |
| clinical_uncertainties | n/a | 0.000 | 0.000 | 0 | 0 | 56 |

Medical history (4 sub-categories pooled): P 0.250 R 0.011 F1 0.021.

### Clinical metrics

* Vital sign accuracy: 0.7% over 274 gold vitals (name found 1.1%).
* Speaker attribution accuracy: 41.3% over 63 matched entities (excluded: 1 records with an unknown speaker, 0 entities).
* Negation: 0.0% of gold negative findings reproduced; polarity flips: 1 (negative reported as present), 0 (present reported as negative).
* Evidence grounding (of 224 predicted entities): strict 2.7%, grounded incl. lenient 2.7%, partially supported 6.7%, unsupported 90.6%.
* Unsupported claims: 6 of 224 predicted entities (2.7%); 152 further FPs are transcript-supported.

### Attribute accuracy (matched entities)

| Attribute | Accuracy (gold non-null) | n | False-attribute rate (gold null) | n |
|---|---|---|---|---|
| severity | 0.0% | 10 | 0.0% | 5 |
| duration | 0.0% | 10 | 0.0% | 5 |
| dose | 80.6% | 31 | 100.0% | 2 |
| medication_frequency | 45.5% | 33 | n/a | 0 |
| medication_route | 100.0% | 1 | 84.4% | 32 |
| action_status | n/a | 0 | n/a | 0 |
| investigation_status | n/a | 0 | n/a | 0 |
| temporality | 100.0% | 15 | n/a | 0 |
| negation | n/a | 0 | n/a | 0 |
| allergy_reaction | 16.7% | 6 | 0.0% | 1 |
| uncertainty_status | 22.7% | 22 | n/a | 0 |

## Entity extraction - Valid-JSON encounters only

Encounters: 57. Strict exact normalised matching.

| | Precision | Recall | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| Micro | 0.295 | 0.032 | 0.058 | 66 | 158 | 1980 |
| Macro | 0.173 | 0.044 | 0.062 | | | |

Fuzzy (reported separately): micro F1 0.060, macro F1 0.063.

| Category | P | R | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| chief_complaint | 0.070 | 0.070 | 0.070 | 4 | 53 | 53 |
| symptoms | 0.211 | 0.083 | 0.119 | 15 | 56 | 166 |
| negative_findings | 0.000 | 0.000 | 0.000 | 0 | 5 | 314 |
| medical_history.past_medical_history | 0.000 | 0.000 | 0.000 | 0 | 4 | 100 |
| medical_history.surgical_history | 0.400 | 0.129 | 0.195 | 4 | 6 | 27 |
| medical_history.family_history | 0.000 | 0.000 | 0.000 | 0 | 1 | 32 |
| medical_history.social_history | 0.000 | 0.000 | 0.000 | 0 | 1 | 166 |
| medications | 0.868 | 0.241 | 0.377 | 33 | 5 | 104 |
| allergies | 0.500 | 0.250 | 0.333 | 7 | 7 | 21 |
| vital_signs | 0.375 | 0.012 | 0.023 | 3 | 5 | 248 |
| physical_examination | 0.000 | 0.000 | 0.000 | 0 | 7 | 78 |
| review_of_systems | n/a | 0.000 | 0.000 | 0 | 0 | 77 |
| clinical_conditions | 0.000 | 0.000 | 0.000 | 0 | 6 | 42 |
| clinical_assessment | n/a | 0.000 | 0.000 | 0 | 0 | 94 |
| procedures_and_investigations | 0.000 | 0.000 | 0.000 | 0 | 1 | 86 |
| clinical_actions | 0.000 | 0.000 | 0.000 | 0 | 1 | 279 |
| follow_up | n/a | 0.000 | 0.000 | 0 | 0 | 40 |
| clinical_uncertainties | n/a | 0.000 | 0.000 | 0 | 0 | 53 |

Medical history (4 sub-categories pooled): P 0.250 R 0.012 F1 0.023.

### Clinical metrics

* Vital sign accuracy: 0.8% over 251 gold vitals (name found 1.2%).
* Speaker attribution accuracy: 41.3% over 63 matched entities (excluded: 1 records with an unknown speaker, 0 entities).
* Negation: 0.0% of gold negative findings reproduced; polarity flips: 1 (negative reported as present), 0 (present reported as negative).
* Evidence grounding (of 224 predicted entities): strict 2.7%, grounded incl. lenient 2.7%, partially supported 6.7%, unsupported 90.6%.
* Unsupported claims: 6 of 224 predicted entities (2.7%); 152 further FPs are transcript-supported.

### Attribute accuracy (matched entities)

| Attribute | Accuracy (gold non-null) | n | False-attribute rate (gold null) | n |
|---|---|---|---|---|
| severity | 0.0% | 10 | 0.0% | 5 |
| duration | 0.0% | 10 | 0.0% | 5 |
| dose | 80.6% | 31 | 100.0% | 2 |
| medication_frequency | 45.5% | 33 | n/a | 0 |
| medication_route | 100.0% | 1 | 84.4% | 32 |
| action_status | n/a | 0 | n/a | 0 |
| investigation_status | n/a | 0 | n/a | 0 |
| temporality | 100.0% | 15 | n/a | 0 |
| negation | n/a | 0 | n/a | 0 |
| allergy_reaction | 16.7% | 6 | 0.0% | 1 |
| uncertainty_status | 22.7% | 22 | n/a | 0 |

## Performance

* Latency per encounter (s): {'mean': 155.66, 'median': 143.476, 'p95': 209.258, 'min': 102.568, 'max': 443.842, 'n': 62}
* Completion tokens: {'mean': 881.355, 'median': 794.0, 'p95': 1261, 'min': 592, 'max': 2548, 'n': 62}
* Prompt tokens: {'mean': 3759.21, 'median': 3718.0, 'p95': 4348, 'min': 3276, 'max': 4639, 'n': 62}
* Tokens/second: {'mean': 5.642, 'median': 5.664, 'p95': 6.188, 'min': 4.386, 'max': 6.287, 'n': 62}
* Total generation time: 2.681 h; finish reasons {'stop': 62}; repetition flagged in 0 outputs.

## By complexity (end-to-end, strict micro)

| Complexity | Encounters | Valid JSON | P | R | F1 |
|---|---|---|---|---|---|
| challenging | 7 | 7 | 0.333 | 0.046 | 0.080 |
| complex | 22 | 20 | 0.333 | 0.028 | 0.052 |
| moderate | 20 | 18 | 0.309 | 0.036 | 0.064 |
| simple | 13 | 12 | 0.103 | 0.008 | 0.016 |

## By specialty (end-to-end, strict micro)

| Specialty | Encounters | Valid JSON | P | R | F1 |
|---|---|---|---|---|---|
| Cardiology | 7 | 7 | 0.370 | 0.043 | 0.076 |
| Dermatology | 3 | 3 | 0.333 | 0.033 | 0.060 |
| ENT / Ophthalmology | 2 | 1 | 0.000 | 0.000 | 0.000 |
| Endocrinology | 5 | 5 | 0.355 | 0.055 | 0.096 |
| Gastroenterology | 5 | 4 | 0.389 | 0.035 | 0.065 |
| General Medicine / Infectious Diseases | 9 | 8 | 0.400 | 0.038 | 0.069 |
| Gynaecology | 4 | 3 | 0.300 | 0.021 | 0.040 |
| Mental Health / Other | 5 | 5 | 0.231 | 0.036 | 0.062 |
| Musculoskeletal / Orthopaedics | 3 | 2 | 0.000 | 0.000 | 0.000 |
| Nephrology / Urology | 4 | 4 | 0.083 | 0.007 | 0.013 |
| Neurology | 8 | 8 | 0.364 | 0.026 | 0.048 |
| Respiratory Medicine | 7 | 7 | 0.152 | 0.019 | 0.034 |

## Definitions

* **entity_matching**: Strict: normalised primary key per category, multiset TP/FP/FN (see entity_matching.py). Fuzzy reported separately.
* **undefined_values**: Precision/recall/F1 are null (undefined) when their denominator is zero; they are never set to 0 or 1. Macro averages only categories with a defined value.
* **end_to_end vs valid_only**: end_to_end counts an encounter without a usable prediction as all-FN; valid_only excludes such encounters.
* **attribute_accuracy**: On strictly matched entities only: accuracy over gold-non-null values, and a separate false-attribute rate where gold is null.
* **grounding**: grounded_strict / grounded_lenient / partially_supported / unsupported, see evidence_evaluator.py (lexical, not clinical correctness).
* **unsupported_claims**: Strict FPs whose key is not lexically supported anywhere in the transcript; denominator reported.

Automated evaluation only; scores reflect lexical/normalised matching to the frozen labels and are not a clinical-quality judgement.
