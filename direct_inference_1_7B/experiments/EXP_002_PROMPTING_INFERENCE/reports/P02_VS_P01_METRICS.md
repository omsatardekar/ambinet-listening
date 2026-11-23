# P02 vs P01 — same 30 records, strict matcher (development-only)

F1 is precision/recall over matched facts, not accuracy. Failed records score zero predictions in the headline (tier 1).

## Overall (tier 1: all records)

| Metric | P01 | P02 | change |
|---|---|---|---|
| micro precision | 0.283 | 0.323 | +0.040 |
| micro recall | 0.156 | 0.214 | +0.059 |
| micro f1 | 0.201 | 0.258 | +0.057 |
| TP | 170 | 234 | +64 |
| FP | 431 | 490 | +59 |
| FN | 923 | 859 | -64 |
| macro precision (categories) | 0.234 | 0.253 | +0.019 |
| macro recall (categories) | 0.156 | 0.198 | +0.041 |
| macro f1 (categories) | 0.180 | 0.209 | +0.030 |

## Parsed records only (tier 2, shown next to tier 1, never instead)

| Metric | P01 | P02 |
|---|---|---|
| micro precision | 0.283 (25 rec) | 0.323 (28 rec) |
| micro recall | 0.189 (25 rec) | 0.234 (28 rec) |
| micro f1 | 0.226 (25 rec) | 0.271 (28 rec) |

## Validity and size

| | P01 | P02 |
|---|---|---|
| records / parsed / failed | 30 / 25 / 5 | 30 / 28 / 2 |
| truncated at 4,096 | 4 | 2 |
| failure types | {'truncated': 4, 'invalid_json': 1} | {'truncated': 2} |
| output tokens median / max | 2590.0 / 4096 | 2284.0 / 4096 |
| generation seconds median / max / total | 1047 / 1638 / 32819 | 1028 / 1850 / 33052 |
| input_tokens_median | 4126.5 | 6684.5 |
| prefill_tokens_per_second_median | 38.5 | 36.650000000000006 |
| decode_tokens_per_second_median | 2.7845 | 2.7135 |
| peak_process_rss_mb_max | 6957 | 5857 |
| min_system_available_mb_lowest | 54 | 2015 |

## Per category (tier 1)

| Category | gold | P01 pred | P02 pred | P01 TP | P02 TP | P01 P / R / F1 | P02 P / R / F1 |
|---|---|---|---|---|---|---|---|
| chief_complaint | 30 | 25 | 28 | 2 | 4 | 0.080 / 0.067 / 0.073 | 0.143 / 0.133 / 0.138 |
| symptoms | 91 | 36 | 40 | 12 | 10 | 0.333 / 0.132 / 0.189 | 0.250 / 0.110 / 0.153 |
| negative_findings | 168 | 40 | 51 | 4 | 1 | 0.100 / 0.024 / 0.038 | 0.020 / 0.006 / 0.009 |
| medical_history.past_medical_history | 50 | 33 | 39 | 6 | 6 | 0.182 / 0.120 / 0.145 | 0.154 / 0.120 / 0.135 |
| medical_history.surgical_history | 16 | 22 | 20 | 2 | 2 | 0.091 / 0.125 / 0.105 | 0.100 / 0.125 / 0.111 |
| medical_history.family_history | 17 | 20 | 27 | 6 | 5 | 0.300 / 0.353 / 0.324 | 0.185 / 0.294 / 0.227 |
| medical_history.social_history | 88 | 29 | 26 | 13 | 24 | 0.448 / 0.148 / 0.222 | 0.923 / 0.273 / 0.421 |
| medications | 72 | 44 | 51 | 37 | 42 | 0.841 / 0.514 / 0.638 | 0.824 / 0.583 / 0.683 |
| allergies | 13 | 21 | 29 | 3 | 4 | 0.143 / 0.231 / 0.176 | 0.138 / 0.308 / 0.190 |
| vital_signs | 129 | 91 | 119 | 51 | 99 | 0.560 / 0.395 / 0.464 | 0.832 / 0.767 / 0.798 |
| physical_examination | 46 | 39 | 36 | 0 | 0 | 0.000 / 0.000 / 0.000 | 0.000 / 0.000 / 0.000 |
| review_of_systems | 40 | 21 | 27 | 0 | 0 | 0.000 / 0.000 / 0.000 | 0.000 / 0.000 / 0.000 |
| clinical_conditions | 20 | 29 | 29 | 0 | 0 | 0.000 / 0.000 / 0.000 | 0.000 / 0.000 / 0.000 |
| clinical_assessment | 48 | 25 | 39 | 17 | 20 | 0.680 / 0.354 / 0.466 | 0.513 / 0.417 / 0.460 |
| procedures_and_investigations | 49 | 38 | 39 | 15 | 13 | 0.395 / 0.306 / 0.345 | 0.333 / 0.265 / 0.295 |
| clinical_actions | 165 | 42 | 68 | 1 | 0 | 0.024 / 0.006 / 0.010 | 0.000 / 0.000 / 0.000 |
| follow_up | 26 | 23 | 28 | 1 | 2 | 0.043 / 0.038 / 0.041 | 0.071 / 0.077 / 0.074 |
| clinical_uncertainties | 25 | 23 | 28 | 0 | 2 | 0.000 / 0.000 / 0.000 | 0.071 / 0.080 / 0.075 |

## Speaker attribution (on facts the matcher paired with a gold fact)

| | P01 | P02 |
|---|---|---|
| pairs | 168 | 230 |
| correct_role | 101 | 207 |
| wrong_role | 13 | 15 |
| not_a_role_value | 45 | 0 |
| missing | 9 | 8 |

## Evidence (separate from entity metrics)

- P01 (model-written evidence block): {'refs_total': 424, 'refs_valid': 424, 'refs_invalid': 0, 'valid_share': 1.0}
- P02 raw model output (segment ids): {'refs_total': 1240, 'refs_valid': 1223, 'refs_invalid': 17, 'valid_share': 0.9863}
- P02 backend backfill: {'counts': {'facts': 724, 'refs_total': 1240, 'refs_valid': 1223, 'refs_invalid': 17, 'facts_without_refs': 123, 'evidence_records_built': 487, 'flag_excessive_references': 39, 'flag_invalid_reference': 17}, 'flag_kinds': {'no_references': 123, 'excessive_references': 39, 'invalid_reference': 17}, 'valid_ref_share': 0.9863}

## Additional completeness diagnostic (matcher's fuzzy mode; NOT the official metric)

| Category | P01 fuzzy recall | P02 fuzzy recall | P01 pred/gold | P02 pred/gold |
|---|---|---|---|---|
| chief_complaint | 0.067 | 0.133 | 0.833 | 0.933 |
| symptoms | 0.143 | 0.121 | 0.396 | 0.44 |
| negative_findings | 0.048 | 0.054 | 0.238 | 0.304 |
| medical_history.past_medical_history | 0.160 | 0.160 | 0.66 | 0.78 |
| medical_history.surgical_history | 0.188 | 0.250 | 1.375 | 1.25 |
| medical_history.family_history | 0.412 | 0.412 | 1.176 | 1.588 |
| medical_history.social_history | 0.148 | 0.273 | 0.33 | 0.295 |
| medications | 0.514 | 0.583 | 0.611 | 0.708 |
| allergies | 0.231 | 0.308 | 1.615 | 2.231 |
| vital_signs | 0.395 | 0.767 | 0.705 | 0.922 |
| physical_examination | 0.022 | 0.022 | 0.848 | 0.783 |
| review_of_systems | 0.000 | 0.000 | 0.525 | 0.675 |
| clinical_conditions | 0.000 | 0.050 | 1.45 | 1.45 |
| clinical_assessment | 0.375 | 0.479 | 0.521 | 0.812 |
| procedures_and_investigations | 0.367 | 0.327 | 0.776 | 0.796 |
| clinical_actions | 0.042 | 0.018 | 0.255 | 0.412 |
| follow_up | 0.269 | 0.077 | 0.885 | 1.077 |
| clinical_uncertainties | 0.000 | 0.080 | 0.92 | 1.12 |
