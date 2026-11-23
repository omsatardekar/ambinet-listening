# EXP_003 INTERIM evaluation - snapshot 20261112T093318Z

**INTERIM RESULT ONLY. This is not the final 100-record development evaluation.** The inference run `exp_003_dev_remaining_95` was still running (not touched); the final evaluation will be produced later by `combine_and_evaluate_dev100.py` and will not overwrite this file.

## Scope and safety
* Completed predictions evaluated: **62** of the 95 remaining development encounters (the 5 smoke-test encounters are NOT in this number). Skipped as incomplete/partial: 0.
* Selection: only manifest records with final status whose raw (and parsed) JSON files were fully readable were taken; these files were **copied** into this timestamped snapshot (sha256-verified) and the existing evaluator ran on the copy. The live run's folders were only read, never written. Currently running or unanswered encounters are excluded.
* The existing evaluator (`evaluation/evaluation_runner.py`, unmodified) was run in a separate process; labels were opened only there. The inference process never receives labels (its audit is written on completion).
* No prompt, model, decoding, schema, dataset or evaluator change; no new inference.

## Headline comparison
| Metric | Interim EXP_003 (62, excl. smoke 5) | EXP_003 smoke (5) | EXP_001 CPU (5) |
|---|---|---|---|
| Predictions evaluated | 62 | 5 | 5 |
| Valid JSON | 57 | 5 | 5 |
| Invalid JSON | 5 | 0 | 0 |
| Truncated rate | 0.000 | 0.000 | 0.000 |
| Schema-compliant (of valid) | 0.000 | 0.000 | 0.000 |
| Required-field completeness | 0.944 | 0.944 | 0.944 |
| TP | 66 | 3 | 3 |
| FP | 158 | 24 | 24 |
| FN | 2151 | 168 | 168 |
| Micro precision | 0.295 | 0.111 | 0.111 |
| Micro recall | 0.030 | 0.018 | 0.018 |
| Micro F1 | 0.054 | 0.030 | 0.030 |
| Macro F1 | 0.059 | 0.019 | 0.019 |
| Vital-sign accuracy | 0.007 | 0.000 | 0.000 |
| Speaker attribution accuracy | 0.413 | 0.333 | 0.333 |
| Unsupported-evidence rate | 0.906 | 0.926 | 0.778 |
| Unsupported-claim rate (of predictions) | 0.027 | 0.037 | 0.037 |
| Mean latency / encounter (s) | 155.660 | 172.581 | 633.940 |
| Mean tokens/s | 5.642 | 5.664 | 1.495 |
| Mean output tokens | 881.355 | 956.600 | 942.800 |

## Category-level strict F1 (interim 62 | smoke 5 | EXP_001 5) with TP/FP/FN for the interim run
| Category | Interim F1 | TP | FP | FN | P | R | Smoke F1 | EXP_001 F1 |
|---|---|---|---|---|---|---|---|---|
| chief_complaint | 0.067 | 4 | 53 | 58 | 0.070 | 0.065 | 0.000 | 0.000 |
| symptoms | 0.112 | 15 | 56 | 182 | 0.211 | 0.076 | 0.074 | 0.074 |
| negative_findings | 0.000 | 0 | 5 | 340 | 0.000 | 0.000 | 0.000 | 0.000 |
| medical_history.past_medical_history | 0.000 | 0 | 4 | 109 | 0.000 | 0.000 | 0.000 | 0.000 |
| medical_history.surgical_history | 0.186 | 4 | 6 | 29 | 0.400 | 0.121 | 0.000 | 0.000 |
| medical_history.family_history | 0.000 | 0 | 1 | 34 | 0.000 | 0.000 | 0.000 | 0.000 |
| medical_history.social_history | 0.000 | 0 | 1 | 181 | 0.000 | 0.000 | 0.000 | 0.000 |
| medications | 0.349 | 33 | 5 | 118 | 0.868 | 0.219 | 0.267 | 0.267 |
| allergies | 0.326 | 7 | 7 | 22 | 0.500 | 0.241 | 0.000 | 0.000 |
| vital_signs | 0.021 | 3 | 5 | 271 | 0.375 | 0.011 | 0.000 | 0.000 |
| physical_examination | 0.000 | 0 | 7 | 87 | 0.000 | 0.000 | 0.000 | 0.000 |
| review_of_systems | 0.000 | 0 | 0 | 84 | n/a | 0.000 | 0.000 | 0.000 |
| clinical_conditions | 0.000 | 0 | 6 | 45 | 0.000 | 0.000 | 0.000 | 0.000 |
| clinical_assessment | 0.000 | 0 | 0 | 102 | n/a | 0.000 | 0.000 | 0.000 |
| procedures_and_investigations | 0.000 | 0 | 1 | 92 | 0.000 | 0.000 | 0.000 | 0.000 |
| clinical_actions | 0.000 | 0 | 1 | 299 | 0.000 | 0.000 | 0.000 | 0.000 |
| follow_up | 0.000 | 0 | 0 | 42 | n/a | 0.000 | 0.000 | 0.000 |
| clinical_uncertainties | 0.000 | 0 | 0 | 56 | n/a | 0.000 | 0.000 | 0.000 |

## Other interim detail
* Vital signs: 2 correct of 274 gold (0.0073); name found 3.
* Speaker attribution: 26/63 correct.
* Evidence grounding of 224 predicted entities: strict 6, lenient 0, partial 15, unsupported 203.
* Unsupported claims: 6 of 224; extra-but-transcript-supported false positives: 152.
* Negation: gold negatives 340, reproduced 0 correctly, polarity flips 1.
* Schema violations (valid JSON only): {'missing_field': 266, 'enum_violation': 131, 'wrong_type': 91, 'unexpected_field': 1}. Failures by type: {'invalid_json': 5} (no truncations, no empty outputs, no inference errors; all finish_reason=stop).
* The 5 invalid outputs are complete-looking JSON ending normally (not token-limit truncation) but with a syntax error (`Expecting ',' delimiter`) - encounters 00096, 00201, 00203, 00240, 00264. They are scored as failures; nothing was repaired.

## Performance (interim)
Mean latency 155.7 s (median 143.5, max 443.8); mean 5.64 tok/s; mean output 881 tokens; total 2.68 h of generation so far.

## Interpretation and caveats
* Interim sample of 62 (valid JSON 57); all numbers will change as the run completes. 'End-to-end' scoring counts the 5 invalid outputs as zero-prediction failures; valid-only scores are in the snapshot's `evaluation_report.json`.
* Compared with the 5-record baseline, the larger sample shows low-but-nonzero micro F1 and notably better medication/allergy extraction; the 5-record figures were not representative. The 5-record sets are different encounters, so the comparison is indicative, not like-for-like.
* The model still omits most schema sections (recall ~3%), so schema compliance is 0%.
* Runtime/format/hardware differ from EXP_001 (Transformers FP32 CPU vs OpenVINO FP16 GPU); on the shared 5 encounters entity metrics were identical.
