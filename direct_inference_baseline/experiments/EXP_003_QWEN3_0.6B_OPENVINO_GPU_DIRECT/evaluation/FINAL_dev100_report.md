# EXP_003 final 100-record development report - Qwen3-0.6B, OpenVINO FP16, Intel UHD 620 GPU

Status: COMPLETED. All 100 development encounters (5 smoke-test + 95 remaining) were run; the 400 locked-test encounters were NOT touched. No prompt optimisation, fine-tuning, LoRA or RAG. Stopped for review.

## Run integrity
* Same model (Qwen3-0.6B rev c1899de2..., OpenVINO FP16 from EXP_002), same prompt (sha256 78c5ab95...f604, asserted), same decoding (greedy, enable_thinking=False, max_new_tokens 6144), same runner/parser/validator/evaluator, GPU only (no CPU fallback), fresh pipeline per encounter.
* The 95 ids = development split minus the 5 smoke ids, disjoint from the 400 test ids (asserted). The smoke run `exp_003_dev_smoke_5` and its artifacts are unchanged (its 46 checksums still verify). The two runs were *copied* into `exp_003_dev_100` for evaluation.
* File-access audit of the 95-encounter inference: 700 files opened, **0 label or blueprint files** (`logs/inference_remaining_95_file_access_audit.json`). Labels were opened only by the evaluator afterwards.
* Verified after the run: EXP_001 checksums 55/55 OK; EXP_002 converted model 11/11 hashes OK; frozen dataset verified (1,001 files); git status shows only the pre-existing untracked items.

## Outputs by status (recorded separately; `failure_report_dev100.json`)
| Class | Count | Encounters |
|---|---|---|
| Valid JSON | 94 | |
| Failed (all) | 6 | |
| Malformed / invalid JSON | 6 | 00096, 00201, 00203, 00240, 00264, 00455 |
| Truncated (token limit) | 0 | |
| Empty | 0 | |
| Not a JSON object | 0 | |
| Inference errors | 0 | |
| Degenerate repetition flagged | 0 | |
| Schema-compliant (of 94 valid) | 0 | all 94 violate the schema: {'missing_field': 429, 'wrong_type': 150, 'enum_violation': 219, 'unexpected_field': 10} |

All 100 generations ended with finish_reason=stop. The six malformed outputs are complete-looking JSON with a syntax error (missing comma delimiter), not token-limit cuts; they were not repaired and score as failures.


## Invalid JSON encounters (all 6; none repaired)
| Encounter | Finish | Output tokens | Parser failure reason |
|---|---|---|---|
| 00096 | stop | 2548 | invalid_json: Expecting ',' delimiter at char 3769 |
| 00201 | stop | 980 | invalid_json: removed markdown fence; Expecting ',' delimiter at char 1656 |
| 00203 | stop | 1112 | invalid_json: Expecting ',' delimiter at char 2486 |
| 00240 | stop | 1000 | invalid_json: Expecting ',' delimiter at char 1627 |
| 00264 | stop | 1104 | invalid_json: Expecting ',' delimiter at char 2666 |
| 00455 | stop | 971 | invalid_json: Expecting ',' delimiter at char 1802 |

Parse success rate: 94/100 = 94.0%; invalid 6/100 = 6.0%. Total encounters 100 (0 locked-test).


## Aggregate metrics (strict matching; end-to-end counts failures as empty predictions)
| Metric | End-to-end (100) | Valid-only (94) |
|---|---|---|
| TP | 98 | 98 |
| FP | 284 | 284 |
| FN | 3523 | 3305 |
| Micro precision | 0.257 | 0.257 |
| Micro recall | 0.027 | 0.029 |
| Micro F1 | 0.049 | 0.052 |
| Macro P / R / F1 | 0.252 / 0.036 / 0.054 | 0.252 / 0.039 / 0.056 |
| Fuzzy micro F1 (secondary) | 0.052 | 0.055 |
| Medical history combined (strict) | P 0.286 R 0.013 F1 0.026 | |

Schema: required-field completeness 94.6%, unexpected-field rate 0.13%, violations {'missing_field': 429, 'wrong_type': 150, 'enum_violation': 219, 'unexpected_field': 10}. Macro F1 averages 18 categories; undefined precision stays n/a.

## Category-level strict results (end-to-end)
| Category | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| chief_complaint | 4 | 90 | 96 | 0.043 | 0.040 | 0.041 |
| symptoms | 20 | 95 | 284 | 0.174 | 0.066 | 0.095 |
| negative_findings | 0 | 9 | 543 | 0.000 | 0.000 | 0.000 |
| medical_history.past_medical_history | 1 | 6 | 180 | 0.143 | 0.006 | 0.011 |
| medical_history.surgical_history | 5 | 10 | 49 | 0.333 | 0.093 | 0.145 |
| medical_history.family_history | 1 | 3 | 59 | 0.250 | 0.017 | 0.031 |
| medical_history.social_history | 1 | 1 | 297 | 0.500 | 0.003 | 0.007 |
| medications | 46 | 14 | 202 | 0.767 | 0.185 | 0.299 |
| allergies | 10 | 14 | 37 | 0.417 | 0.213 | 0.282 |
| vital_signs | 9 | 13 | 435 | 0.409 | 0.020 | 0.039 |
| physical_examination | 0 | 15 | 145 | 0.000 | 0.000 | 0.000 |
| review_of_systems | 0 | 1 | 140 | 0.000 | 0.000 | 0.000 |
| clinical_conditions | 0 | 9 | 76 | 0.000 | 0.000 | 0.000 |
| clinical_assessment | 0 | 0 | 170 | n/a | 0.000 | 0.000 |
| procedures_and_investigations | 0 | 2 | 156 | 0.000 | 0.000 | 0.000 |
| clinical_actions | 0 | 2 | 487 | 0.000 | 0.000 | 0.000 |
| follow_up | 0 | 0 | 75 | n/a | 0.000 | 0.000 |
| clinical_uncertainties | 1 | 0 | 92 | 1.000 | 0.011 | 0.021 |

Only medications (0.299), allergies (0.282), surgical history (0.145), symptoms (0.095) and chief complaint (0.041) show meaningful signal; vital signs 0.039; clinical_uncertainties 1 TP and 0 FP. Negative findings, physical examination, review of systems, clinical conditions, assessment, procedures, actions and follow-up are 0.0 (assessment and follow-up: no predictions at all, so precision is n/a).

## Clinical quality detail
* **Vital signs:** 5 correct of 444 gold (1.13%); name found for 9.
* **Speaker attribution:** 46/90 = 51.1% (patient 39/76, doctor 7/9, nurse 0/2, family member 0/2).
* **Evidence grounding** (382 predicted entities): strict 9 (2.4%), lenient 3, partial 32, unsupported 338 (88.5%).
* **Unsupported claims:** 8 of 385 predictions (2.1%); of 284 false positives, 276 are extras the transcript does support (mostly under-extraction, not hallucination).
* **Negation:** 543 gold negative findings, 1 reproduced; 1 polarity flip.
* Attribute accuracy on matched entities is in `evaluation/exp_003_dev_100/evaluation_report.json` (e.g. medication dose 83.7%, status 82.6%, frequency 45.7%; symptom severity 7%, duration 0%).

## Breakdowns (strict micro F1, end-to-end)
| Complexity | Encounters | Valid | F1 |
|---|---|---|---|
| challenging | 14 | 14 | 0.059 |
| complex | 32 | 29 | 0.055 |
| moderate | 35 | 33 | 0.052 |
| simple | 19 | 18 | 0.014 |

| Specialty | Encounters | Valid | F1 |
|---|---|---|---|
| Cardiology | 11 | 11 | 0.053 |
| Dermatology | 7 | 7 | 0.043 |
| ENT / Ophthalmology | 4 | 3 | 0.051 |
| Endocrinology | 7 | 7 | 0.081 |
| Gastroenterology | 9 | 8 | 0.048 |
| General Medicine / Infectious Diseases | 15 | 14 | 0.057 |
| Gynaecology | 4 | 3 | 0.040 |
| Mental Health / Other | 8 | 8 | 0.053 |
| Musculoskeletal / Orthopaedics | 8 | 6 | 0.036 |
| Nephrology / Urology | 6 | 6 | 0.053 |
| Neurology | 11 | 11 | 0.042 |
| Respiratory Medicine | 10 | 10 | 0.029 |

Specialty groups have 4-15 encounters; differences are within noise and should not be over-read.

## Performance (100 encounters, `evaluation/dev100_performance_details.json`)
| | Mean | Median | Min | Max | p95 |
|---|---|---|---|---|---|
| Input tokens | 3771.65 | 3718.0 | 3237 | 4639 | 4348 |
| Output tokens | 874.99 | 782.0 | 592 | 2548 | 1273 |
| Model load (warm cache), s | 4.0 | 3.381 | 3.029 | 8.514 | 7.325 |
| First-token latency (prefill+1st), s | 26.825 | 26.059 | 21.031 | 42.296 | 35.847 |
| Prefill tok/s | 142.322 | 145.4 | 109.1 | 161.5 | 156.6 |
| Decode tok/s | 6.962 | 7.017 | 5.511 | 7.915 | 7.555 |
| Generation time, s | 153.996 | 140.899 | 100.523 | 443.842 | 225.106 |
| Overall tok/s | 5.678 | 5.721 | 4.241 | 6.287 | 6.225 |
| RSS after call, MB | 2608.23 | 2592.5 | 2491 | 2793 | 2731 |

Total generation 4.278 h for 87,499 output tokens; peak process working set 2942 MB (maximum over the two processes). The 95-encounter run took 4.16 h wall (14,974 s).
Extrapolation (estimate): the 400 locked-test encounters would take about 400 x 154 s = 17 h of generation.

## GPU errors and warnings
The same two Intel graphics-compiler kernel-header messages as in EXP_002 ("Input V38 intersects with V37"; "Explicit input 2 must not follow an implicit input 0") were logged on pipeline creation (`logs/gpu_compiler/kernel.errors.txt`). No crashes, 0 inference errors, no out-of-memory, no OpenVINO runtime warnings; every encounter succeeded. The messages had no visible effect on outputs. (The `NativeCommandError` line at the top of the stdout log is PowerShell wrapping the compiler stderr text.)

## Findings and limits
* The baseline is weak: strict micro recall 2.7%, F1 0.049, 0% schema compliance. The model emits short JSON (mean 875 tokens) that omits most schema sections, regardless of backend.
* Precision on what it does emit is moderate (25.7%), with medications at 76.7%.
* 6% malformed JSON is a real reliability problem for a pipeline that needs parseable output.
* Strict matching is conservative, but fuzzy micro F1 is only slightly higher (0.052), so the gap is genuine under-extraction rather than wording differences.
* These are development-split results for one fixed prompt; they are not a locked-test estimate.

## Not done (per instruction)
No locked-test (400) evaluation, prompt optimisation, fine-tuning, LoRA, RAG or quantisation. Awaiting your approval before anything further.


## Final integrity check
* Inference outputs: 200 files in `exp_003_dev_100` are byte-identical to their source-run files (0 mismatches); smoke-stage prediction/evaluation files vs their recorded checksums: 0 changed of 46 entries checked.
* EXP_001 archive: 55/55 checksums match. Frozen dataset: verified (1,001 files, `evaluation/frozen_dataset_verification_after_dev100.json`). EXP_002 model: 11/11 hashes match. Locked test: not used.
* The whole-experiment checksum file `checksums/experiment_checksums.sha256` (690 files) was generated after the final report; the smoke-stage list is kept as `checksums/experiment_checksums_smoke_stage.sha256`.