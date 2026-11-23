# P02 vs S1 – comparison (50 prompt-development records; development-set results only)

| Metric | P02 | S1 | Direction |
|---|---|---|---|
| Strict micro F1 | 0.1207 | 0.1192 | no change |
| Strict macro F1 | 0.1222 | 0.1160 | slightly worse |
| Precision | 0.2267 | 0.2792 | better |
| Recall | 0.0823 | 0.0758 | slightly worse |
| TP / FP / FN | 153 / 522 / 1707 | 141 / 364 / 1719 | fewer FP, FN same |
| Fuzzy micro F1 (reference) | 0.1349 | 0.1285 | no change |
| Valid JSON | 50/50 | 37/50 | **worse** (13 parse failures) |
| Fully valid in own output format | n/a | 0/37 | 492 enum violations |
| Output tokens (mean) | 1,356 | 617 | −54 % |
| Input tokens (mean) | 4,329 | 3,316 | −23 % |
| Latency mean / median | 235.5 / 232.9 s | 106.6 / 107.0 s | −55 % |
| Decode tokens/s | 6.74 | 7.34 | similar |
| Peak memory | 3,111 MB | 2,844 MB | similar |
| Fabricated date/time values | 66 | 7 | better |
| Same-item contradictions | 16 | 4 | better |
| Evaluator unsupported claims | 85 | 60 | better |
| Speaker-attribution accuracy | 0.421 (53/126) | 0.088 (9/102) | **much worse** |
| Allergy-status errors | 28 | 28 | same |

Supplementary (post-hoc, not a headline): on the 37 records where S1 parsed, S1 F1 0.154 vs P02 0.122.

## Category F1 (strict)
| Category | P02 | S1 |
|---|---|---|
| chief complaint | 0.140 | 0.000 |
| symptoms | 0.108 | 0.011 |
| negative findings | 0.000 | 0.038 |
| past medical history | 0.069 | 0.062 |
| surgical history | 0.130 | 0.045 |
| family history | 0.178 | 0.140 |
| social history | 0.000 | 0.048 |
| medications | 0.497 | 0.453 |
| allergies | 0.300 | 0.341 |
| vital signs | 0.272 | 0.296 |
| physical examination | 0.014 | 0.000 |
| review of systems | 0.107 | 0.041 |
| clinical conditions | 0.024 | 0.000 |
| clinical assessment | 0.140 | 0.124 |
| investigations/procedures | 0.155 | 0.219 |
| clinical actions | 0.007 | 0.000 |
| follow-up | 0.058 | 0.270 |
| clinical uncertainties | 0.000 | 0.000 |

Gains: negative findings, social history, allergies, vitals, investigations/procedures, follow-up. Regressions: chief complaint, symptoms, surgical/family/PMH, medications, ROS, physical exam, clinical conditions, assessment, actions. Small counts; 1–3 entity differences are noise. Source: `evaluation/S1_CATEGORY_METRICS.json`.
