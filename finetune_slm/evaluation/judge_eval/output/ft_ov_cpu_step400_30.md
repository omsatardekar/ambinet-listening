# Fine-tuned model (ov_cpu_step400_30) vs frozen-prompt baseline: judge evaluation

Same judge (gpt-5.4, Foundry), same frozen prompts, same metrics as `METHODOLOGY.md`. Judge-F1 is agreement under one judge model's reading of one rubric, not clinical accuracy. Synthetic data only; labels are not clinician reviewed.

## 1. Like-for-like: the 30 encounters both models were run on (Test A, EXP_008 ids)

| model |  encounters | precision | recall | judge-F1 (lenient) | judge-F1 (strict) | hallucination | critical |
|---|---|---|---|---|---|---|---|
| frozen H1 prompt, base Qwen3-0.6B |  30 | 0.568 [0.511, 0.624] | 0.255 [0.219, 0.291] | 0.352 [0.313, 0.390] | 0.239 [0.200, 0.277] | 0.262 [0.203, 0.330] | 0.120 [0.092, 0.149] |
| fine-tuned, step 400, short prompt |  30 | 0.957 [0.949, 0.966] | 0.924 [0.906, 0.940] | 0.940 [0.928, 0.951] | 0.905 [0.887, 0.921] | 0.014 [0.008, 0.020] | 0.005 [0.000, 0.012] |

Encounters where the model output was valid JSON: baseline 30/30, fine-tuned 30/30.

## 2. Fine-tuned model on the locked test set (no baseline exists for these encounters)

| subset |  encounters | precision | recall | judge-F1 (lenient) | judge-F1 (strict) | hallucination | critical |
|---|---|---|---|---|---|---|---|
| Test A (Batch 1 benchmark) |  30 | 0.957 [0.949, 0.966] | 0.924 [0.906, 0.940] | 0.940 [0.928, 0.951] | 0.905 [0.887, 0.921] | 0.014 [0.008, 0.020] | 0.005 [0.000, 0.012] |
| All judged test encounters |  30 | 0.957 [0.949, 0.966] | 0.924 [0.906, 0.940] | 0.940 [0.928, 0.951] | 0.905 [0.887, 0.921] | 0.014 [0.008, 0.020] | 0.005 [0.000, 0.012] |

## 3. Per section (all judged test encounters, lenient)

| section | reference facts | predicted facts | recall | precision |
|---|---|---|---|---|
| allergies | 13 | 14 | 0.962 | 1.0 |
| chief_complaint | 30 | 30 | 1.0 | 1.0 |
| clinical_actions | 165 | 161 | 0.891 | 0.925 |
| clinical_assessment | 48 | 48 | 0.99 | 0.99 |
| clinical_conditions | 20 | 19 | 1.0 | 1.0 |
| clinical_uncertainties | 25 | 25 | 0.86 | 0.8 |
| follow_up | 26 | 26 | 1.0 | 1.0 |
| medical_history.family_history | 17 | 17 | 1.0 | 1.0 |
| medical_history.past_medical_history | 50 | 50 | 1.0 | 1.0 |
| medical_history.social_history | 88 | 87 | 0.892 | 0.948 |
| medical_history.surgical_history | 16 | 17 | 1.0 | 1.0 |
| medications | 72 | 71 | 0.951 | 0.944 |
| negative_findings | 168 | 150 | 0.902 | 0.977 |
| physical_examination | 46 | 53 | 0.75 | 0.887 |
| procedures_and_investigations | 49 | 49 | 0.857 | 1.0 |
| review_of_systems | 40 | 40 | 1.0 | 1.0 |
| symptoms | 91 | 90 | 0.863 | 0.883 |
| vital_signs | 129 | 129 | 1.0 | 1.0 |

Encounters not yet judged: 943. Encounters whose model output was invalid JSON are judged with zero predictions (all their reference facts count as missed).
