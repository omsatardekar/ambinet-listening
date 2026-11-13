# Direct inference baseline report - exp_003_dev_100

Model: `Qwen/Qwen3-0.6B` via **openvino_genai**; split **development**; dataset manifest `4403fef843fb...`; prompt `78c5ab95d001...`; max_new_tokens 6144.

## Coverage and failures

Requested 100, attempted 100, valid JSON 94 (94.0% of requested), failed 6 (failure rate 6.0%).
Failure types: {'invalid_json': 6}.

## JSON and schema

| Metric | Value |
|---|---|
| JSON validity | 94.0% |
| Truncated (hit token budget) | 0.0% |
| Malformed JSON (not truncated) | 6.0% |
| Schema compliance among valid JSON | 0.0% |
| Schema compliance end-to-end | 0.0% |
| Required field completeness (valid JSON) | 94.6% |
| Unexpected field rate | 0.1% |

## Entity extraction - End-to-end (failures count as all-FN)

Encounters: 100. Strict exact normalised matching.

| | Precision | Recall | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| Micro | 0.257 | 0.027 | 0.049 | 98 | 284 | 3523 |
| Macro | 0.252 | 0.036 | 0.054 | | | |

Fuzzy (reported separately): micro F1 0.052, macro F1 0.060.

| Category | P | R | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| chief_complaint | 0.043 | 0.040 | 0.041 | 4 | 90 | 96 |
| symptoms | 0.174 | 0.066 | 0.095 | 20 | 95 | 284 |
| negative_findings | 0.000 | 0.000 | 0.000 | 0 | 9 | 543 |
| medical_history.past_medical_history | 0.143 | 0.006 | 0.011 | 1 | 6 | 180 |
| medical_history.surgical_history | 0.333 | 0.093 | 0.145 | 5 | 10 | 49 |
| medical_history.family_history | 0.250 | 0.017 | 0.031 | 1 | 3 | 59 |
| medical_history.social_history | 0.500 | 0.003 | 0.007 | 1 | 1 | 297 |
| medications | 0.767 | 0.185 | 0.299 | 46 | 14 | 202 |
| allergies | 0.417 | 0.213 | 0.282 | 10 | 14 | 37 |
| vital_signs | 0.409 | 0.020 | 0.039 | 9 | 13 | 435 |
| physical_examination | 0.000 | 0.000 | 0.000 | 0 | 15 | 145 |
| review_of_systems | 0.000 | 0.000 | 0.000 | 0 | 1 | 140 |
| clinical_conditions | 0.000 | 0.000 | 0.000 | 0 | 9 | 76 |
| clinical_assessment | n/a | 0.000 | 0.000 | 0 | 0 | 170 |
| procedures_and_investigations | 0.000 | 0.000 | 0.000 | 0 | 2 | 156 |
| clinical_actions | 0.000 | 0.000 | 0.000 | 0 | 2 | 487 |
| follow_up | n/a | 0.000 | 0.000 | 0 | 0 | 75 |
| clinical_uncertainties | 1.000 | 0.011 | 0.021 | 1 | 0 | 92 |

Medical history (4 sub-categories pooled): P 0.286 R 0.013 F1 0.026.

### Clinical metrics

* Vital sign accuracy: 1.1% over 444 gold vitals (name found 2.0%).
* Speaker attribution accuracy: 51.1% over 90 matched entities (excluded: 3 records with an unknown speaker, 0 entities).
* Negation: 0.0% of gold negative findings reproduced; polarity flips: 1 (negative reported as present), 0 (present reported as negative).
* Evidence grounding (of 382 predicted entities): strict 2.4%, grounded incl. lenient 3.1%, partially supported 8.4%, unsupported 88.5%.
* Unsupported claims: 8 of 385 predicted entities (2.1%); 276 further FPs are transcript-supported.

### Attribute accuracy (matched entities)

| Attribute | Accuracy (gold non-null) | n | False-attribute rate (gold null) | n |
|---|---|---|---|---|
| severity | 7.1% | 14 | 0.0% | 6 |
| duration | 0.0% | 12 | 0.0% | 8 |
| dose | 83.7% | 43 | 100.0% | 3 |
| medication_frequency | 45.7% | 46 | n/a | 0 |
| medication_route | 100.0% | 1 | 86.7% | 45 |
| action_status | n/a | 0 | n/a | 0 |
| investigation_status | n/a | 0 | n/a | 0 |
| temporality | 100.0% | 20 | n/a | 0 |
| negation | n/a | 0 | n/a | 0 |
| allergy_reaction | 12.5% | 8 | 0.0% | 2 |
| uncertainty_status | 32.3% | 31 | n/a | 0 |

## Entity extraction - Valid-JSON encounters only

Encounters: 94. Strict exact normalised matching.

| | Precision | Recall | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| Micro | 0.257 | 0.029 | 0.052 | 98 | 284 | 3305 |
| Macro | 0.252 | 0.039 | 0.056 | | | |

Fuzzy (reported separately): micro F1 0.055, macro F1 0.063.

| Category | P | R | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| chief_complaint | 0.043 | 0.043 | 0.043 | 4 | 90 | 90 |
| symptoms | 0.174 | 0.070 | 0.100 | 20 | 95 | 264 |
| negative_findings | 0.000 | 0.000 | 0.000 | 0 | 9 | 512 |
| medical_history.past_medical_history | 0.143 | 0.006 | 0.011 | 1 | 6 | 169 |
| medical_history.surgical_history | 0.333 | 0.098 | 0.152 | 5 | 10 | 46 |
| medical_history.family_history | 0.250 | 0.018 | 0.033 | 1 | 3 | 56 |
| medical_history.social_history | 0.500 | 0.004 | 0.007 | 1 | 1 | 277 |
| medications | 0.767 | 0.200 | 0.317 | 46 | 14 | 184 |
| allergies | 0.417 | 0.222 | 0.290 | 10 | 14 | 35 |
| vital_signs | 0.409 | 0.022 | 0.041 | 9 | 13 | 407 |
| physical_examination | 0.000 | 0.000 | 0.000 | 0 | 15 | 134 |
| review_of_systems | 0.000 | 0.000 | 0.000 | 0 | 1 | 131 |
| clinical_conditions | 0.000 | 0.000 | 0.000 | 0 | 9 | 71 |
| clinical_assessment | n/a | 0.000 | 0.000 | 0 | 0 | 160 |
| procedures_and_investigations | 0.000 | 0.000 | 0.000 | 0 | 2 | 149 |
| clinical_actions | 0.000 | 0.000 | 0.000 | 0 | 2 | 461 |
| follow_up | n/a | 0.000 | 0.000 | 0 | 0 | 72 |
| clinical_uncertainties | 1.000 | 0.011 | 0.022 | 1 | 0 | 87 |

Medical history (4 sub-categories pooled): P 0.286 R 0.014 F1 0.027.

### Clinical metrics

* Vital sign accuracy: 1.2% over 416 gold vitals (name found 2.2%).
* Speaker attribution accuracy: 51.1% over 90 matched entities (excluded: 3 records with an unknown speaker, 0 entities).
* Negation: 0.0% of gold negative findings reproduced; polarity flips: 1 (negative reported as present), 0 (present reported as negative).
* Evidence grounding (of 382 predicted entities): strict 2.4%, grounded incl. lenient 3.1%, partially supported 8.4%, unsupported 88.5%.
* Unsupported claims: 8 of 385 predicted entities (2.1%); 276 further FPs are transcript-supported.

### Attribute accuracy (matched entities)

| Attribute | Accuracy (gold non-null) | n | False-attribute rate (gold null) | n |
|---|---|---|---|---|
| severity | 7.1% | 14 | 0.0% | 6 |
| duration | 0.0% | 12 | 0.0% | 8 |
| dose | 83.7% | 43 | 100.0% | 3 |
| medication_frequency | 45.7% | 46 | n/a | 0 |
| medication_route | 100.0% | 1 | 86.7% | 45 |
| action_status | n/a | 0 | n/a | 0 |
| investigation_status | n/a | 0 | n/a | 0 |
| temporality | 100.0% | 20 | n/a | 0 |
| negation | n/a | 0 | n/a | 0 |
| allergy_reaction | 12.5% | 8 | 0.0% | 2 |
| uncertainty_status | 32.3% | 31 | n/a | 0 |

## Performance

* Latency per encounter (s): {'mean': 153.996, 'median': 140.899, 'p95': 225.106, 'min': 100.523, 'max': 443.842, 'n': 100}
* Completion tokens: {'mean': 874.99, 'median': 782.0, 'p95': 1273, 'min': 592, 'max': 2548, 'n': 100}
* Prompt tokens: {'mean': 3771.65, 'median': 3718.0, 'p95': 4348, 'min': 3237, 'max': 4639, 'n': 100}
* Tokens/second: {'mean': 5.678, 'median': 5.721, 'p95': 6.225, 'min': 4.241, 'max': 6.287, 'n': 100}
* Total generation time: 4.278 h; finish reasons {'stop': 100}; repetition flagged in 0 outputs.

## By complexity (end-to-end, strict micro)

| Complexity | Encounters | Valid JSON | P | R | F1 |
|---|---|---|---|---|---|
| challenging | 14 | 14 | 0.300 | 0.033 | 0.059 |
| complex | 32 | 29 | 0.297 | 0.030 | 0.055 |
| moderate | 35 | 33 | 0.248 | 0.029 | 0.052 |
| simple | 19 | 18 | 0.093 | 0.008 | 0.014 |

## By specialty (end-to-end, strict micro)

| Specialty | Encounters | Valid JSON | P | R | F1 |
|---|---|---|---|---|---|
| Cardiology | 11 | 11 | 0.297 | 0.029 | 0.053 |
| Dermatology | 7 | 7 | 0.240 | 0.024 | 0.043 |
| ENT / Ophthalmology | 4 | 3 | 0.308 | 0.028 | 0.051 |
| Endocrinology | 7 | 7 | 0.333 | 0.046 | 0.081 |
| Gastroenterology | 9 | 8 | 0.281 | 0.026 | 0.048 |
| General Medicine / Infectious Diseases | 15 | 14 | 0.279 | 0.032 | 0.057 |
| Gynaecology | 4 | 3 | 0.300 | 0.021 | 0.040 |
| Mental Health / Other | 8 | 8 | 0.235 | 0.030 | 0.053 |
| Musculoskeletal / Orthopaedics | 8 | 6 | 0.240 | 0.020 | 0.036 |
| Nephrology / Urology | 6 | 6 | 0.184 | 0.031 | 0.053 |
| Neurology | 11 | 11 | 0.310 | 0.023 | 0.042 |
| Respiratory Medicine | 10 | 10 | 0.143 | 0.016 | 0.029 |

## Definitions

* **entity_matching**: Strict: normalised primary key per category, multiset TP/FP/FN (see entity_matching.py). Fuzzy reported separately.
* **undefined_values**: Precision/recall/F1 are null (undefined) when their denominator is zero; they are never set to 0 or 1. Macro averages only categories with a defined value.
* **end_to_end vs valid_only**: end_to_end counts an encounter without a usable prediction as all-FN; valid_only excludes such encounters.
* **attribute_accuracy**: On strictly matched entities only: accuracy over gold-non-null values, and a separate false-attribute rate where gold is null.
* **grounding**: grounded_strict / grounded_lenient / partially_supported / unsupported, see evidence_evaluator.py (lexical, not clinical correctness).
* **unsupported_claims**: Strict FPs whose key is not lexically supported anywhere in the transcript; denominator reported.

Automated evaluation only; scores reflect lexical/normalised matching to the frozen labels and are not a clinical-quality judgement.
