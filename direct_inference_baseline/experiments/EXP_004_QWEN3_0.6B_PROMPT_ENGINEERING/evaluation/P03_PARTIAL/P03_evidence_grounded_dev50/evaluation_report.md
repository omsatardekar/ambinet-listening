# Direct inference baseline report - P03_evidence_grounded_dev50

Model: `Qwen/Qwen3-0.6B` via **openvino_genai**; split **development**; dataset manifest `4403fef843fb...`; prompt `4f7ee6f763aa...`; max_new_tokens 6144.

## Coverage and failures

Requested 50, attempted 35, valid JSON 33 (66.0% of requested), failed 2 (failure rate 5.7%).
Failure types: {'invalid_json': 2}.

## JSON and schema

| Metric | Value |
|---|---|
| JSON validity | 94.3% |
| Truncated (hit token budget) | 0.0% |
| Malformed JSON (not truncated) | 5.7% |
| Schema compliance among valid JSON | 0.0% |
| Schema compliance end-to-end | 0.0% |
| Required field completeness (valid JSON) | 95.2% |
| Unexpected field rate | 0.0% |

## Entity extraction - End-to-end (failures count as all-FN)

Encounters: 35. Strict exact normalised matching.

| | Precision | Recall | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| Micro | 0.225 | 0.031 | 0.055 | 40 | 138 | 1243 |
| Macro | 0.167 | 0.042 | 0.057 | | | |

Fuzzy (reported separately): micro F1 0.057, macro F1 0.060.

| Category | P | R | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| chief_complaint | 0.061 | 0.057 | 0.059 | 2 | 31 | 33 |
| symptoms | 0.143 | 0.067 | 0.092 | 7 | 42 | 97 |
| negative_findings | 0.083 | 0.005 | 0.010 | 1 | 11 | 191 |
| medical_history.past_medical_history | 0.000 | 0.000 | 0.000 | 0 | 1 | 61 |
| medical_history.surgical_history | 0.300 | 0.158 | 0.207 | 3 | 7 | 16 |
| medical_history.family_history | n/a | 0.000 | 0.000 | 0 | 0 | 20 |
| medical_history.social_history | n/a | 0.000 | 0.000 | 0 | 0 | 107 |
| medications | 0.690 | 0.241 | 0.357 | 20 | 9 | 63 |
| allergies | 0.273 | 0.188 | 0.222 | 3 | 8 | 13 |
| vital_signs | 0.286 | 0.013 | 0.025 | 2 | 5 | 149 |
| physical_examination | 0.000 | 0.000 | 0.000 | 0 | 5 | 54 |
| review_of_systems | 0.000 | 0.000 | 0.000 | 0 | 2 | 48 |
| clinical_conditions | 0.000 | 0.000 | 0.000 | 0 | 10 | 26 |
| clinical_assessment | n/a | 0.000 | 0.000 | 0 | 0 | 58 |
| procedures_and_investigations | 0.500 | 0.033 | 0.062 | 2 | 2 | 58 |
| clinical_actions | 0.000 | 0.000 | 0.000 | 0 | 4 | 191 |
| follow_up | n/a | 0.000 | 0.000 | 0 | 0 | 30 |
| clinical_uncertainties | 0.000 | 0.000 | 0.000 | 0 | 1 | 28 |

Medical history (4 sub-categories pooled): P 0.273 R 0.014 F1 0.028.

### Clinical metrics

* Vital sign accuracy: 0.7% over 151 gold vitals (name found 1.3%).
* Speaker attribution accuracy: 36.8% over 38 matched entities (excluded: 1 records with an unknown speaker, 0 entities).
* Negation: 0.5% of gold negative findings reproduced; polarity flips: 1 (negative reported as present), 0 (present reported as negative).
* Evidence grounding (of 178 predicted entities): strict 0.0%, grounded incl. lenient 0.0%, partially supported 15.7%, unsupported 84.3%.
* Unsupported claims: 9 of 178 predicted entities (5.1%); 129 further FPs are transcript-supported.

### Attribute accuracy (matched entities)

| Attribute | Accuracy (gold non-null) | n | False-attribute rate (gold null) | n |
|---|---|---|---|---|
| severity | 33.3% | 3 | 25.0% | 4 |
| duration | 0.0% | 3 | 0.0% | 4 |
| dose | 88.2% | 17 | 100.0% | 3 |
| medication_frequency | 26.3% | 19 | 100.0% | 1 |
| medication_route | n/a | 0 | 90.0% | 20 |
| action_status | n/a | 0 | n/a | 0 |
| investigation_status | 100.0% | 2 | n/a | 0 |
| temporality | 87.5% | 8 | n/a | 0 |
| negation | 100.0% | 2 | n/a | 0 |
| allergy_reaction | 0.0% | 3 | n/a | 0 |
| uncertainty_status | 30.0% | 10 | n/a | 0 |

## Entity extraction - Valid-JSON encounters only

Encounters: 33. Strict exact normalised matching.

| | Precision | Recall | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| Micro | 0.225 | 0.033 | 0.058 | 40 | 138 | 1168 |
| Macro | 0.167 | 0.046 | 0.061 | | | |

Fuzzy (reported separately): micro F1 0.061, macro F1 0.063.

| Category | P | R | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| chief_complaint | 0.061 | 0.061 | 0.061 | 2 | 31 | 31 |
| symptoms | 0.143 | 0.073 | 0.097 | 7 | 42 | 89 |
| negative_findings | 0.083 | 0.005 | 0.010 | 1 | 11 | 181 |
| medical_history.past_medical_history | 0.000 | 0.000 | 0.000 | 0 | 1 | 57 |
| medical_history.surgical_history | 0.300 | 0.176 | 0.222 | 3 | 7 | 14 |
| medical_history.family_history | n/a | 0.000 | 0.000 | 0 | 0 | 19 |
| medical_history.social_history | n/a | 0.000 | 0.000 | 0 | 0 | 103 |
| medications | 0.690 | 0.263 | 0.381 | 20 | 9 | 56 |
| allergies | 0.273 | 0.200 | 0.231 | 3 | 8 | 12 |
| vital_signs | 0.286 | 0.014 | 0.027 | 2 | 5 | 140 |
| physical_examination | 0.000 | 0.000 | 0.000 | 0 | 5 | 52 |
| review_of_systems | 0.000 | 0.000 | 0.000 | 0 | 2 | 46 |
| clinical_conditions | 0.000 | 0.000 | 0.000 | 0 | 10 | 25 |
| clinical_assessment | n/a | 0.000 | 0.000 | 0 | 0 | 54 |
| procedures_and_investigations | 0.500 | 0.035 | 0.066 | 2 | 2 | 55 |
| clinical_actions | 0.000 | 0.000 | 0.000 | 0 | 4 | 181 |
| follow_up | n/a | 0.000 | 0.000 | 0 | 0 | 28 |
| clinical_uncertainties | 0.000 | 0.000 | 0.000 | 0 | 1 | 25 |

Medical history (4 sub-categories pooled): P 0.273 R 0.015 F1 0.029.

### Clinical metrics

* Vital sign accuracy: 0.7% over 142 gold vitals (name found 1.4%).
* Speaker attribution accuracy: 36.8% over 38 matched entities (excluded: 0 records with an unknown speaker, 0 entities).
* Negation: 0.5% of gold negative findings reproduced; polarity flips: 1 (negative reported as present), 0 (present reported as negative).
* Evidence grounding (of 178 predicted entities): strict 0.0%, grounded incl. lenient 0.0%, partially supported 15.7%, unsupported 84.3%.
* Unsupported claims: 9 of 178 predicted entities (5.1%); 129 further FPs are transcript-supported.

### Attribute accuracy (matched entities)

| Attribute | Accuracy (gold non-null) | n | False-attribute rate (gold null) | n |
|---|---|---|---|---|
| severity | 33.3% | 3 | 25.0% | 4 |
| duration | 0.0% | 3 | 0.0% | 4 |
| dose | 88.2% | 17 | 100.0% | 3 |
| medication_frequency | 26.3% | 19 | 100.0% | 1 |
| medication_route | n/a | 0 | 90.0% | 20 |
| action_status | n/a | 0 | n/a | 0 |
| investigation_status | 100.0% | 2 | n/a | 0 |
| temporality | 87.5% | 8 | n/a | 0 |
| negation | 100.0% | 2 | n/a | 0 |
| allergy_reaction | 0.0% | 3 | n/a | 0 |
| uncertainty_status | 30.0% | 10 | n/a | 0 |

## Performance

* Latency per encounter (s): {'mean': 184.376, 'median': 161.837, 'p95': 281.549, 'min': 115.665, 'max': 414.484, 'n': 35}
* Completion tokens: {'mean': 976.714, 'median': 818, 'p95': 1670, 'min': 626, 'max': 2221, 'n': 35}
* Prompt tokens: {'mean': 4186.743, 'median': 4129, 'p95': 4761, 'min': 3711, 'max': 5052, 'n': 35}
* Tokens/second: {'mean': 5.269, 'median': 5.357, 'p95': 5.742, 'min': 4.291, 'max': 5.931, 'n': 35}
* Total generation time: 1.793 h; finish reasons {'stop': 35}; repetition flagged in 0 outputs.

## By complexity (end-to-end, strict micro)

| Complexity | Encounters | Valid JSON | P | R | F1 |
|---|---|---|---|---|---|
| challenging | 3 | 2 | 0.333 | 0.038 | 0.068 |
| complex | 12 | 12 | 0.239 | 0.035 | 0.061 |
| moderate | 12 | 11 | 0.186 | 0.029 | 0.051 |
| simple | 8 | 8 | 0.227 | 0.022 | 0.040 |

## By specialty (end-to-end, strict micro)

| Specialty | Encounters | Valid JSON | P | R | F1 |
|---|---|---|---|---|---|
| Cardiology | 3 | 3 | 0.111 | 0.010 | 0.018 |
| Dermatology | 2 | 2 | 0.429 | 0.046 | 0.083 |
| ENT / Ophthalmology | 1 | 1 | 0.167 | 0.028 | 0.048 |
| Endocrinology | 3 | 3 | 0.278 | 0.040 | 0.070 |
| Gastroenterology | 2 | 1 | 0.500 | 0.028 | 0.053 |
| General Medicine / Infectious Diseases | 6 | 6 | 0.205 | 0.041 | 0.068 |
| Gynaecology | 2 | 2 | 0.250 | 0.014 | 0.026 |
| Mental Health / Other | 2 | 1 | 0.333 | 0.015 | 0.029 |
| Musculoskeletal / Orthopaedics | 2 | 2 | 0.167 | 0.015 | 0.028 |
| Nephrology / Urology | 3 | 3 | 0.172 | 0.044 | 0.070 |
| Neurology | 5 | 5 | 0.211 | 0.021 | 0.039 |
| Respiratory Medicine | 4 | 4 | 0.241 | 0.045 | 0.075 |

## Definitions

* **entity_matching**: Strict: normalised primary key per category, multiset TP/FP/FN (see entity_matching.py). Fuzzy reported separately.
* **undefined_values**: Precision/recall/F1 are null (undefined) when their denominator is zero; they are never set to 0 or 1. Macro averages only categories with a defined value.
* **end_to_end vs valid_only**: end_to_end counts an encounter without a usable prediction as all-FN; valid_only excludes such encounters.
* **attribute_accuracy**: On strictly matched entities only: accuracy over gold-non-null values, and a separate false-attribute rate where gold is null.
* **grounding**: grounded_strict / grounded_lenient / partially_supported / unsupported, see evidence_evaluator.py (lexical, not clinical correctness).
* **unsupported_claims**: Strict FPs whose key is not lexically supported anywhere in the transcript; denominator reported.

Automated evaluation only; scores reflect lexical/normalised matching to the frozen labels and are not a clinical-quality judgement.
