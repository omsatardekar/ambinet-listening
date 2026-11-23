# P00_direct_dev50: evaluation (development-only, 50 prompt-dev ids)

prompt_dev: the 50 original prompt-development ids (previously used for 0.6B prompt development). DEVELOPMENT-ONLY results, not independent validation, labels are generator-derived (not human-verified, not clinical validation).

Headline = all 50 records, all 18 canonical categories, failed outputs counted as zero predictions. Unchanged canonical evaluator.

| Metric | 0.6B P00 direct | 0.6B P02 best prompt (dev) | 1.7B P00_direct_dev50 |
|---|---|---|---|
| Strict micro P | 0.237 | 0.227 | 0.271 |
| Strict micro R | 0.026 | 0.082 | 0.106 |
| **Strict micro F1** | **0.0474** | **0.1207** | **0.1528** |
| TP / FP / FN | 49/158/1811 | 153/522/1707 | 198/533/1662 |
| Strict macro P / R / F1 | 0.231 / 0.032 / 0.0478 | 0.198 / 0.100 / 0.1222 | 0.226 / 0.114 / 0.1444 |
| Micro F1 excl. clinical_conditions | 0.0484 | 0.1240 | 0.1567 |
| Micro F1 excl. conditions+uncertainties | 0.0485 | 0.1263 | 0.1608 |
| Valid JSON (of 50) | 48 | 50 | 35 |
| Invalid JSON / token-cap hits | 2 / 0 | 0 / 0 | 15 / 15 |
| Fully canonical-schema-compliant records | 0 | 0 | 0 |
| Canonical schema violations (total) | 444 | 1064 | 696 |
| Evidence grounding (strict / lenient+) | 0.014 / 0.024 | 0.000 / 0.000 | 0.005 / 0.005 |
| Speaker attribution accuracy | 0.463 | 0.421 | 0.540 |
| Medication recall (strict) | 0.188 | 0.359 | 0.336 |
| Medication precision (strict) | 0.774 | 0.807 | 0.782 |
| Dose errors / checked on matched | 4/22 | 5/40 | 0/37 |
| Missing prescribed meds (of gold planned) | 27/29 | 25/29 | 26/29 |
| Allergy status errors (of 50) | 34 | 28 | 39 |
| Allergy category recall | 0.167 | 0.375 | 0.208 |
| Negation: gold negatives correct rate | 0.000 | 0.000 | 0.007 |
| Polarity flips (neg->pos / pos->neg) | 0/0 | 0/0 | 0/0 |
| Temporality accuracy (symptoms, gold non-null) | 1.000 | 0.909 | 0.769 |
| Unsupported claims | 4 | 85 | 104 |
| Contradictions (same item pos+neg) | 0 | 16 | 0 |
| Duplicate facts | 0 | 1 | 11 |
| Mean input / output tokens | 3791 / 863 | 4329 / 1356 | 3791 / 2927 |
| Mean latency per record (s) | 152.9 | 235.5 | 1133.5 |
| Tokens/s overall (mean) / decode / prefill | 5.65 / - / - | 5.73 / 6.74 / 134.4 | 2.56 / 2.84 / 40.1 |
| Peak process working set (MB) | - | 3111 | 7091 |

## Per-category (strict)

| Category (recall / F1) | 0.6B P00 direct | 0.6B P02 best prompt (dev) | 1.7B P00_direct_dev50 |
|---|---|---|---|
| chief complaint | 0.020 / 0.020 | 0.140 / 0.140 | 0.100 / 0.118 |
| symptoms | 0.060 / 0.086 | 0.073 / 0.108 | 0.087 / 0.133 |
| negative findings | 0.000 / 0.000 | 0.000 / 0.000 | 0.007 / 0.013 |
| medical history (past/ongoing) | 0.011 / 0.020 | 0.043 / 0.069 | 0.064 / 0.088 |
| surgical history | 0.074 / 0.111 | 0.111 / 0.130 | 0.111 / 0.107 |
| family history | 0.000 / 0.000 | 0.138 / 0.178 | 0.207 / 0.235 |
| social history | 0.007 / 0.013 | 0.000 / 0.000 | 0.046 / 0.081 |
| medications | 0.188 / 0.302 | 0.359 / 0.497 | 0.336 / 0.470 |
| allergies | 0.167 / 0.211 | 0.375 / 0.300 | 0.208 / 0.192 |
| vital signs | 0.027 / 0.052 | 0.187 / 0.272 | 0.274 / 0.373 |
| physical examination | 0.000 / 0.000 | 0.013 / 0.014 | 0.000 / 0.000 |
| review of systems | 0.000 / 0.000 | 0.086 / 0.107 | 0.029 / 0.042 |
| clinical conditions | 0.000 / 0.000 | 0.026 / 0.024 | 0.026 / 0.026 |
| clinical assessment | 0.000 / 0.000 | 0.090 / 0.140 | 0.258 / 0.368 |
| investigations and procedures | 0.000 / 0.000 | 0.110 / 0.155 | 0.232 / 0.281 |
| clinical actions | 0.000 / 0.000 | 0.004 / 0.007 | 0.000 / 0.000 |
| follow-up | 0.000 / 0.000 | 0.044 / 0.058 | 0.022 / 0.026 |
| clinical uncertainties | 0.023 / 0.044 | 0.000 / 0.000 | 0.045 / 0.045 |

Category collapse vs 0.6B P02 (TP=0 where P02 TP>=3): {"0.6B P00 direct": ["medical_history.family_history", "review_of_systems", "clinical_assessment", "procedures_and_investigations"], "0.6B P02 best prompt (dev)": [], "1.7B P00_direct_dev50": []}

File-access audit: locked-test opened 0, sealed hash file opened False, validation records opened 0.