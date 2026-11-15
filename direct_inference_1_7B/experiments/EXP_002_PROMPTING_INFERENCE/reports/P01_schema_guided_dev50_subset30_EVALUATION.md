# P01_schema_guided_dev50: evaluation (development-only, 30 prompt-dev ids)

prompt_dev subset: 30 of the 50 original prompt-development ids (previously used for 0.6B prompt development). DEVELOPMENT-ONLY results, not independent validation, labels are generator-derived (not human-verified, not clinical validation).

Headline = all 30 records, all 18 canonical categories, failed outputs counted as zero predictions. Unchanged canonical evaluator.

| Metric | 0.6B P00 direct | 0.6B P02 best prompt (dev) | 1.7B P01_schema_guided_dev50 | 1.7B P00_direct_dev50 |
|---|---|---|---|---|
| Strict micro P | 0.218 | 0.226 | 0.283 | 0.258 |
| Strict micro R | 0.025 | 0.083 | 0.156 | 0.117 |
| **Strict micro F1** | **0.0444** | **0.1217** | **0.2007** | **0.1610** |
| TP / FP / FN | 27/97/1066 | 91/312/1002 | 170/431/923 | 128/369/965 |
| Strict macro P / R / F1 | 0.127 / 0.030 / 0.0429 | 0.201 / 0.105 / 0.1279 | 0.234 / 0.156 / 0.1798 | 0.216 / 0.127 / 0.1535 |
| Micro F1 excl. clinical_conditions | 0.0452 | 0.1255 | 0.2067 | 0.1657 |
| Micro F1 excl. conditions+uncertainties | 0.0461 | 0.1277 | 0.2129 | 0.1718 |
| Valid JSON (of 30) | 29 | 30 | 25 | 23 |
| Invalid JSON / token-cap hits | 1 / 0 | 0 / 0 | 5 / 4 | 7 / 7 |
| Fully canonical-schema-compliant records | 0 | 0 | 0 | 0 |
| Canonical schema violations (total) | 282 | 637 | 614 | 504 |
| Evidence grounding (strict / lenient+) | 0.016 / 0.016 | 0.000 / 0.000 | 0.018 / 0.022 | 0.006 / 0.006 |
| Speaker attribution accuracy | 0.333 | 0.377 | 0.674 | 0.603 |
| Medication recall (strict) | 0.236 | 0.389 | 0.514 | 0.417 |
| Medication precision (strict) | 0.895 | 0.875 | 0.841 | 0.789 |
| Dose errors / checked on matched | 3/16 | 3/24 | 0/33 | 0/27 |
| Missing prescribed meds (of gold planned) | 15/17 | 14/17 | 14/17 | 16/17 |
| Allergy status errors (of 30) | 19 | 17 | 22 | 23 |
| Allergy category recall | 0.154 | 0.308 | 0.231 | 0.231 |
| Negation: gold negatives correct rate | 0.000 | 0.000 | 0.024 | 0.012 |
| Polarity flips (neg->pos / pos->neg) | 0/0 | 0/0 | 0/0 | 0/0 |
| Temporality accuracy (symptoms, gold non-null) | 1.000 | 1.000 | 0.750 | 0.750 |
| Unsupported claims | 4 | 49 | 79 | 77 |
| Contradictions (same item pos+neg) | 0 | 12 | 0 | 0 |
| Duplicate facts | 0 | 0 | 3 | 10 |
| Mean input / output tokens | 3767 / 864 | 4305 / 1345 | 4193 / 2709 | 3767 / 2811 |
| Mean latency per record (s) | 154.8 | 233.1 | 1094.0 | 1091.3 |
| Tokens/s overall (mean) / decode / prefill | 5.58 / - / - | 5.73 / 6.74 / 134.4 | 2.45 / 2.76 / 38.0 | 2.55 / 2.84 / 40.1 |
| Peak process working set (MB) | - | 3111 | 6960 | 7091 |

## Per-category (strict)

| Category (recall / F1) | 0.6B P00 direct | 0.6B P02 best prompt (dev) | 1.7B P01_schema_guided_dev50 | 1.7B P00_direct_dev50 |
|---|---|---|---|---|
| chief complaint | 0.033 / 0.034 | 0.200 / 0.200 | 0.067 / 0.073 | 0.100 / 0.113 |
| symptoms | 0.055 / 0.076 | 0.055 / 0.081 | 0.132 / 0.189 | 0.088 / 0.129 |
| negative findings | 0.000 / 0.000 | 0.000 / 0.000 | 0.024 / 0.038 | 0.012 / 0.021 |
| medical history (past/ongoing) | 0.000 / 0.000 | 0.020 / 0.032 | 0.120 / 0.145 | 0.100 / 0.127 |
| surgical history | 0.062 / 0.091 | 0.125 / 0.138 | 0.125 / 0.105 | 0.125 / 0.111 |
| family history | 0.000 / 0.000 | 0.235 / 0.296 | 0.353 / 0.324 | 0.294 / 0.323 |
| social history | 0.000 / 0.000 | 0.000 / 0.000 | 0.148 / 0.222 | 0.045 / 0.078 |
| medications | 0.236 / 0.374 | 0.389 / 0.538 | 0.514 / 0.638 | 0.417 / 0.545 |
| allergies | 0.154 / 0.182 | 0.308 / 0.242 | 0.231 / 0.176 | 0.231 / 0.194 |
| vital signs | 0.008 / 0.015 | 0.186 / 0.265 | 0.395 / 0.464 | 0.302 / 0.392 |
| physical examination | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| review of systems | 0.000 / 0.000 | 0.075 / 0.092 | 0.000 / 0.000 | 0.000 / 0.000 |
| clinical conditions | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| clinical assessment | 0.000 / 0.000 | 0.125 / 0.194 | 0.354 / 0.466 | 0.312 / 0.423 |
| investigations and procedures | 0.000 / 0.000 | 0.163 / 0.222 | 0.306 / 0.345 | 0.224 / 0.265 |
| clinical actions | 0.000 / 0.000 | 0.000 / 0.000 | 0.006 / 0.010 | 0.000 / 0.000 |
| follow-up | 0.000 / 0.000 | 0.000 / 0.000 | 0.038 / 0.041 | 0.038 / 0.043 |
| clinical uncertainties | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |

Category collapse vs 0.6B P02 (TP=0 where P02 TP>=3): {"0.6B P00 direct": ["medical_history.family_history", "review_of_systems", "clinical_assessment", "procedures_and_investigations"], "0.6B P02 best prompt (dev)": [], "1.7B P01_schema_guided_dev50": ["review_of_systems"], "1.7B P00_direct_dev50": ["review_of_systems"]}

File-access audit: locked-test opened 0, sealed hash file opened False, validation records opened 0.