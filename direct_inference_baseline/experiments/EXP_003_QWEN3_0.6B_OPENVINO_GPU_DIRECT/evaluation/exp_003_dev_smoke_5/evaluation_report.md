# Direct inference baseline report - exp_003_dev_smoke_5

Model: `Qwen/Qwen3-0.6B` via **openvino_genai**; split **development**; dataset manifest `4403fef843fb...`; prompt `78c5ab95d001...`; max_new_tokens 6144.

## Coverage and failures

Requested 5, attempted 5, valid JSON 5 (100.0% of requested), failed 0 (failure rate 0.0%).
Failure types: none.

## JSON and schema

| Metric | Value |
|---|---|
| JSON validity | 100.0% |
| Truncated (hit token budget) | 0.0% |
| Malformed JSON (not truncated) | 0.0% |
| Schema compliance among valid JSON | 0.0% |
| Schema compliance end-to-end | 0.0% |
| Required field completeness (valid JSON) | 94.4% |
| Unexpected field rate | 0.0% |

## Entity extraction - End-to-end (failures count as all-FN)

Encounters: 5. Strict exact normalised matching.

| | Precision | Recall | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| Micro | 0.111 | 0.018 | 0.030 | 3 | 24 | 168 |
| Macro | 0.107 | 0.013 | 0.019 | | | |

Fuzzy (reported separately): micro F1 0.030, macro F1 0.019.

| Category | P | R | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| chief_complaint | 0.000 | 0.000 | 0.000 | 0 | 5 | 5 |
| symptoms | 0.083 | 0.067 | 0.074 | 1 | 11 | 14 |
| negative_findings | 0.000 | 0.000 | 0.000 | 0 | 3 | 27 |
| medical_history.past_medical_history | n/a | 0.000 | 0.000 | 0 | 0 | 7 |
| medical_history.surgical_history | 0.000 | 0.000 | 0.000 | 0 | 2 | 4 |
| medical_history.family_history | n/a | 0.000 | 0.000 | 0 | 0 | 3 |
| medical_history.social_history | n/a | 0.000 | 0.000 | 0 | 0 | 13 |
| medications | 0.667 | 0.167 | 0.267 | 2 | 1 | 10 |
| allergies | 0.000 | 0.000 | 0.000 | 0 | 1 | 2 |
| vital_signs | n/a | 0.000 | 0.000 | 0 | 0 | 16 |
| physical_examination | 0.000 | 0.000 | 0.000 | 0 | 1 | 7 |
| review_of_systems | n/a | 0.000 | 0.000 | 0 | 0 | 6 |
| clinical_conditions | n/a | 0.000 | 0.000 | 0 | 0 | 2 |
| clinical_assessment | n/a | 0.000 | 0.000 | 0 | 0 | 9 |
| procedures_and_investigations | n/a | 0.000 | 0.000 | 0 | 0 | 10 |
| clinical_actions | n/a | 0.000 | 0.000 | 0 | 0 | 26 |
| follow_up | n/a | 0.000 | 0.000 | 0 | 0 | 2 |
| clinical_uncertainties | n/a | 0.000 | 0.000 | 0 | 0 | 5 |

Medical history (4 sub-categories pooled): P 0.000 R 0.000 F1 0.000.

### Clinical metrics

* Vital sign accuracy: 0.0% over 16 gold vitals (name found 0.0%).
* Speaker attribution accuracy: 33.3% over 3 matched entities (excluded: 0 records with an unknown speaker, 0 entities).
* Negation: 0.0% of gold negative findings reproduced; polarity flips: 0 (negative reported as present), 0 (present reported as negative).
* Evidence grounding (of 27 predicted entities): strict 0.0%, grounded incl. lenient 0.0%, partially supported 7.4%, unsupported 92.6%.
* Unsupported claims: 1 of 27 predicted entities (3.7%); 23 further FPs are transcript-supported.

### Attribute accuracy (matched entities)

| Attribute | Accuracy (gold non-null) | n | False-attribute rate (gold null) | n |
|---|---|---|---|---|
| severity | 0.0% | 1 | n/a | 0 |
| duration | 0.0% | 1 | n/a | 0 |
| dose | 0.0% | 1 | 100.0% | 1 |
| medication_frequency | 0.0% | 2 | n/a | 0 |
| medication_route | n/a | 0 | 50.0% | 2 |
| action_status | n/a | 0 | n/a | 0 |
| investigation_status | n/a | 0 | n/a | 0 |
| temporality | 100.0% | 1 | n/a | 0 |
| negation | n/a | 0 | n/a | 0 |
| allergy_reaction | n/a | 0 | n/a | 0 |
| uncertainty_status | 0.0% | 1 | n/a | 0 |

## Entity extraction - Valid-JSON encounters only

Encounters: 5. Strict exact normalised matching.

| | Precision | Recall | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| Micro | 0.111 | 0.018 | 0.030 | 3 | 24 | 168 |
| Macro | 0.107 | 0.013 | 0.019 | | | |

Fuzzy (reported separately): micro F1 0.030, macro F1 0.019.

| Category | P | R | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| chief_complaint | 0.000 | 0.000 | 0.000 | 0 | 5 | 5 |
| symptoms | 0.083 | 0.067 | 0.074 | 1 | 11 | 14 |
| negative_findings | 0.000 | 0.000 | 0.000 | 0 | 3 | 27 |
| medical_history.past_medical_history | n/a | 0.000 | 0.000 | 0 | 0 | 7 |
| medical_history.surgical_history | 0.000 | 0.000 | 0.000 | 0 | 2 | 4 |
| medical_history.family_history | n/a | 0.000 | 0.000 | 0 | 0 | 3 |
| medical_history.social_history | n/a | 0.000 | 0.000 | 0 | 0 | 13 |
| medications | 0.667 | 0.167 | 0.267 | 2 | 1 | 10 |
| allergies | 0.000 | 0.000 | 0.000 | 0 | 1 | 2 |
| vital_signs | n/a | 0.000 | 0.000 | 0 | 0 | 16 |
| physical_examination | 0.000 | 0.000 | 0.000 | 0 | 1 | 7 |
| review_of_systems | n/a | 0.000 | 0.000 | 0 | 0 | 6 |
| clinical_conditions | n/a | 0.000 | 0.000 | 0 | 0 | 2 |
| clinical_assessment | n/a | 0.000 | 0.000 | 0 | 0 | 9 |
| procedures_and_investigations | n/a | 0.000 | 0.000 | 0 | 0 | 10 |
| clinical_actions | n/a | 0.000 | 0.000 | 0 | 0 | 26 |
| follow_up | n/a | 0.000 | 0.000 | 0 | 0 | 2 |
| clinical_uncertainties | n/a | 0.000 | 0.000 | 0 | 0 | 5 |

Medical history (4 sub-categories pooled): P 0.000 R 0.000 F1 0.000.

### Clinical metrics

* Vital sign accuracy: 0.0% over 16 gold vitals (name found 0.0%).
* Speaker attribution accuracy: 33.3% over 3 matched entities (excluded: 0 records with an unknown speaker, 0 entities).
* Negation: 0.0% of gold negative findings reproduced; polarity flips: 0 (negative reported as present), 0 (present reported as negative).
* Evidence grounding (of 27 predicted entities): strict 0.0%, grounded incl. lenient 0.0%, partially supported 7.4%, unsupported 92.6%.
* Unsupported claims: 1 of 27 predicted entities (3.7%); 23 further FPs are transcript-supported.

### Attribute accuracy (matched entities)

| Attribute | Accuracy (gold non-null) | n | False-attribute rate (gold null) | n |
|---|---|---|---|---|
| severity | 0.0% | 1 | n/a | 0 |
| duration | 0.0% | 1 | n/a | 0 |
| dose | 0.0% | 1 | 100.0% | 1 |
| medication_frequency | 0.0% | 2 | n/a | 0 |
| medication_route | n/a | 0 | 50.0% | 2 |
| action_status | n/a | 0 | n/a | 0 |
| investigation_status | n/a | 0 | n/a | 0 |
| temporality | 100.0% | 1 | n/a | 0 |
| negation | n/a | 0 | n/a | 0 |
| allergy_reaction | n/a | 0 | n/a | 0 |
| uncertainty_status | 0.0% | 1 | n/a | 0 |

## Performance

* Latency per encounter (s): {'mean': 172.581, 'median': 134.034, 'p95': 140.183, 'min': 101.037, 'max': 368.28, 'n': 5}
* Completion tokens: {'mean': 956.6, 'median': 775, 'p95': 775, 'min': 629, 'max': 1948, 'n': 5}
* Prompt tokens: {'mean': 3784.8, 'median': 3987, 'p95': 4079, 'min': 3368, 'max': 4108, 'n': 5}
* Tokens/second: {'mean': 5.664, 'median': 5.528, 'p95': 5.782, 'min': 5.289, 'max': 6.225, 'n': 5}
* Total generation time: 0.24 h; finish reasons {'stop': 5}; repetition flagged in 0 outputs.

## By complexity (end-to-end, strict micro)

| Complexity | Encounters | Valid JSON | P | R | F1 |
|---|---|---|---|---|---|
| challenging | 1 | 1 | 0.250 | 0.023 | 0.043 |
| complex | 2 | 2 | 0.105 | 0.026 | 0.042 |
| moderate | 1 | 1 | 0.000 | 0.000 | 0.000 |
| simple | 1 | 1 | 0.000 | 0.000 | 0.000 |

## By specialty (end-to-end, strict micro)

| Specialty | Encounters | Valid JSON | P | R | F1 |
|---|---|---|---|---|---|
| ENT / Ophthalmology | 1 | 1 | 0.000 | 0.000 | 0.000 |
| Gastroenterology | 1 | 1 | 0.333 | 0.028 | 0.051 |
| General Medicine / Infectious Diseases | 2 | 2 | 0.100 | 0.024 | 0.039 |
| Neurology | 1 | 1 | 0.000 | 0.000 | 0.000 |

## Definitions

* **entity_matching**: Strict: normalised primary key per category, multiset TP/FP/FN (see entity_matching.py). Fuzzy reported separately.
* **undefined_values**: Precision/recall/F1 are null (undefined) when their denominator is zero; they are never set to 0 or 1. Macro averages only categories with a defined value.
* **end_to_end vs valid_only**: end_to_end counts an encounter without a usable prediction as all-FN; valid_only excludes such encounters.
* **attribute_accuracy**: On strictly matched entities only: accuracy over gold-non-null values, and a separate false-attribute rate where gold is null.
* **grounding**: grounded_strict / grounded_lenient / partially_supported / unsupported, see evidence_evaluator.py (lexical, not clinical correctness).
* **unsupported_claims**: Strict FPs whose key is not lexically supported anywhere in the transcript; denominator reported.

Automated evaluation only; scores reflect lexical/normalised matching to the frozen labels and are not a clinical-quality judgement.
