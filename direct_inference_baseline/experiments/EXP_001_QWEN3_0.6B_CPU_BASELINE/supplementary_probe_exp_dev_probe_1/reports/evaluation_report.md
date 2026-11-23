# Direct inference baseline report - exp_dev_probe_1

Model: `Qwen/Qwen3-0.6B` via **huggingface**; split **development**; dataset manifest `4403fef843fb...`; prompt `78c5ab95d001...`; max_new_tokens 6144.

## Coverage and failures

Requested 1, attempted 1, valid JSON 1 (100.0% of requested), failed 0 (failure rate 0.0%).
Failure types: none.

## JSON and schema

| Metric | Value |
|---|---|
| JSON validity | 100.0% |
| Truncated (hit token budget) | 0.0% |
| Malformed JSON (not truncated) | 0.0% |
| Schema compliance among valid JSON | 0.0% |
| Schema compliance end-to-end | 0.0% |
| Required field completeness (valid JSON) | 94.2% |
| Unexpected field rate | 0.0% |

## Entity extraction - End-to-end (failures count as all-FN)

Encounters: 1. Strict exact normalised matching.

| | Precision | Recall | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| Micro | 0.250 | 0.023 | 0.043 | 1 | 3 | 42 |
| Macro | 0.167 | 0.015 | 0.020 | | | |

Fuzzy (reported separately): micro F1 0.043, macro F1 0.020.

| Category | P | R | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| chief_complaint | 0.000 | 0.000 | 0.000 | 0 | 1 | 1 |
| symptoms | 0.500 | 0.250 | 0.333 | 1 | 1 | 3 |
| negative_findings | n/a | 0.000 | 0.000 | 0 | 0 | 5 |
| medical_history.past_medical_history | n/a | 0.000 | 0.000 | 0 | 0 | 1 |
| medical_history.surgical_history | 0.000 | 0.000 | 0.000 | 0 | 1 | 1 |
| medical_history.family_history | n/a | n/a | n/a | 0 | 0 | 0 |
| medical_history.social_history | n/a | 0.000 | 0.000 | 0 | 0 | 3 |
| medications | n/a | 0.000 | 0.000 | 0 | 0 | 3 |
| allergies | n/a | 0.000 | 0.000 | 0 | 0 | 1 |
| vital_signs | n/a | 0.000 | 0.000 | 0 | 0 | 5 |
| physical_examination | n/a | 0.000 | 0.000 | 0 | 0 | 2 |
| review_of_systems | n/a | 0.000 | 0.000 | 0 | 0 | 1 |
| clinical_conditions | n/a | 0.000 | 0.000 | 0 | 0 | 1 |
| clinical_assessment | n/a | 0.000 | 0.000 | 0 | 0 | 2 |
| procedures_and_investigations | n/a | 0.000 | 0.000 | 0 | 0 | 3 |
| clinical_actions | n/a | 0.000 | 0.000 | 0 | 0 | 8 |
| follow_up | n/a | 0.000 | 0.000 | 0 | 0 | 1 |
| clinical_uncertainties | n/a | 0.000 | 0.000 | 0 | 0 | 1 |

Medical history (4 sub-categories pooled): P 0.000 R 0.000 F1 0.000.

### Clinical metrics

* Vital sign accuracy: 0.0% over 5 gold vitals (name found 0.0%).
* Speaker attribution accuracy: 0.0% over 1 matched entities (excluded: 0 records with an unknown speaker, 0 entities).
* Negation: 0.0% of gold negative findings reproduced; polarity flips: 0 (negative reported as present), 0 (present reported as negative).
* Evidence grounding (of 4 predicted entities): strict 0.0%, grounded incl. lenient 0.0%, partially supported 0.0%, unsupported 100.0%.
* Unsupported claims: 0 of 4 predicted entities (0.0%); 3 further FPs are transcript-supported.

### Attribute accuracy (matched entities)

| Attribute | Accuracy (gold non-null) | n | False-attribute rate (gold null) | n |
|---|---|---|---|---|
| severity | 0.0% | 1 | n/a | 0 |
| duration | 0.0% | 1 | n/a | 0 |
| dose | n/a | 0 | n/a | 0 |
| medication_frequency | n/a | 0 | n/a | 0 |
| medication_route | n/a | 0 | n/a | 0 |
| action_status | n/a | 0 | n/a | 0 |
| investigation_status | n/a | 0 | n/a | 0 |
| temporality | 100.0% | 1 | n/a | 0 |
| negation | n/a | 0 | n/a | 0 |
| allergy_reaction | n/a | 0 | n/a | 0 |
| uncertainty_status | 0.0% | 1 | n/a | 0 |

## Entity extraction - Valid-JSON encounters only

Encounters: 1. Strict exact normalised matching.

| | Precision | Recall | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| Micro | 0.250 | 0.023 | 0.043 | 1 | 3 | 42 |
| Macro | 0.167 | 0.015 | 0.020 | | | |

Fuzzy (reported separately): micro F1 0.043, macro F1 0.020.

| Category | P | R | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| chief_complaint | 0.000 | 0.000 | 0.000 | 0 | 1 | 1 |
| symptoms | 0.500 | 0.250 | 0.333 | 1 | 1 | 3 |
| negative_findings | n/a | 0.000 | 0.000 | 0 | 0 | 5 |
| medical_history.past_medical_history | n/a | 0.000 | 0.000 | 0 | 0 | 1 |
| medical_history.surgical_history | 0.000 | 0.000 | 0.000 | 0 | 1 | 1 |
| medical_history.family_history | n/a | n/a | n/a | 0 | 0 | 0 |
| medical_history.social_history | n/a | 0.000 | 0.000 | 0 | 0 | 3 |
| medications | n/a | 0.000 | 0.000 | 0 | 0 | 3 |
| allergies | n/a | 0.000 | 0.000 | 0 | 0 | 1 |
| vital_signs | n/a | 0.000 | 0.000 | 0 | 0 | 5 |
| physical_examination | n/a | 0.000 | 0.000 | 0 | 0 | 2 |
| review_of_systems | n/a | 0.000 | 0.000 | 0 | 0 | 1 |
| clinical_conditions | n/a | 0.000 | 0.000 | 0 | 0 | 1 |
| clinical_assessment | n/a | 0.000 | 0.000 | 0 | 0 | 2 |
| procedures_and_investigations | n/a | 0.000 | 0.000 | 0 | 0 | 3 |
| clinical_actions | n/a | 0.000 | 0.000 | 0 | 0 | 8 |
| follow_up | n/a | 0.000 | 0.000 | 0 | 0 | 1 |
| clinical_uncertainties | n/a | 0.000 | 0.000 | 0 | 0 | 1 |

Medical history (4 sub-categories pooled): P 0.000 R 0.000 F1 0.000.

### Clinical metrics

* Vital sign accuracy: 0.0% over 5 gold vitals (name found 0.0%).
* Speaker attribution accuracy: 0.0% over 1 matched entities (excluded: 0 records with an unknown speaker, 0 entities).
* Negation: 0.0% of gold negative findings reproduced; polarity flips: 0 (negative reported as present), 0 (present reported as negative).
* Evidence grounding (of 4 predicted entities): strict 0.0%, grounded incl. lenient 0.0%, partially supported 0.0%, unsupported 100.0%.
* Unsupported claims: 0 of 4 predicted entities (0.0%); 3 further FPs are transcript-supported.

### Attribute accuracy (matched entities)

| Attribute | Accuracy (gold non-null) | n | False-attribute rate (gold null) | n |
|---|---|---|---|---|
| severity | 0.0% | 1 | n/a | 0 |
| duration | 0.0% | 1 | n/a | 0 |
| dose | n/a | 0 | n/a | 0 |
| medication_frequency | n/a | 0 | n/a | 0 |
| medication_route | n/a | 0 | n/a | 0 |
| action_status | n/a | 0 | n/a | 0 |
| investigation_status | n/a | 0 | n/a | 0 |
| temporality | 100.0% | 1 | n/a | 0 |
| negation | n/a | 0 | n/a | 0 |
| allergy_reaction | n/a | 0 | n/a | 0 |
| uncertainty_status | 0.0% | 1 | n/a | 0 |

## Performance

* Latency per encounter (s): {'mean': 540.246, 'median': 540.246, 'p95': 540.246, 'min': 540.246, 'max': 540.246, 'n': 1}
* Completion tokens: {'mean': 775, 'median': 775, 'p95': 775, 'min': 775, 'max': 775, 'n': 1}
* Prompt tokens: {'mean': 3987, 'median': 3987, 'p95': 3987, 'min': 3987, 'max': 3987, 'n': 1}
* Tokens/second: {'mean': 1.435, 'median': 1.435, 'p95': 1.435, 'min': 1.435, 'max': 1.435, 'n': 1}
* Total generation time: 0.15 h; finish reasons {'stop': 1}; repetition flagged in 0 outputs.

## By complexity (end-to-end, strict micro)

| Complexity | Encounters | Valid JSON | P | R | F1 |
|---|---|---|---|---|---|
| challenging | 1 | 1 | 0.250 | 0.023 | 0.043 |

## By specialty (end-to-end, strict micro)

| Specialty | Encounters | Valid JSON | P | R | F1 |
|---|---|---|---|---|---|
| General Medicine / Infectious Diseases | 1 | 1 | 0.250 | 0.023 | 0.043 |

## Definitions

* **entity_matching**: Strict: normalised primary key per category, multiset TP/FP/FN (see entity_matching.py). Fuzzy reported separately.
* **undefined_values**: Precision/recall/F1 are null (undefined) when their denominator is zero; they are never set to 0 or 1. Macro averages only categories with a defined value.
* **end_to_end vs valid_only**: end_to_end counts an encounter without a usable prediction as all-FN; valid_only excludes such encounters.
* **attribute_accuracy**: On strictly matched entities only: accuracy over gold-non-null values, and a separate false-attribute rate where gold is null.
* **grounding**: grounded_strict / grounded_lenient / partially_supported / unsupported, see evidence_evaluator.py (lexical, not clinical correctness).
* **unsupported_claims**: Strict FPs whose key is not lexically supported anywhere in the transcript; denominator reported.

Automated evaluation only; scores reflect lexical/normalised matching to the frozen labels and are not a clinical-quality judgement.
