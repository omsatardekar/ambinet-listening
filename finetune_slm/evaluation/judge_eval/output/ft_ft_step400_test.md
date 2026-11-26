# Fine-tuned model (ft_step400_test) vs frozen-prompt baseline: judge evaluation

Same judge (gpt-5.4, Foundry), same frozen prompts, same metrics as `METHODOLOGY.md`. Judge-F1 is agreement under one judge model's reading of one rubric, not clinical accuracy. Synthetic data only; labels are not clinician reviewed.

## 1. Like-for-like: the 30 encounters both models were run on (Test A, EXP_008 ids)

| model |  encounters | precision | recall | judge-F1 (lenient) | judge-F1 (strict) | hallucination | critical |
|---|---|---|---|---|---|---|---|
| frozen H1 prompt, base Qwen3-0.6B |  30 | 0.568 [0.511, 0.624] | 0.255 [0.219, 0.291] | 0.352 [0.313, 0.390] | 0.239 [0.200, 0.277] | 0.262 [0.203, 0.330] | 0.120 [0.092, 0.149] |
| fine-tuned, step 400, short prompt |  30 | 0.956 [0.948, 0.965] | 0.923 [0.904, 0.939] | 0.939 [0.927, 0.951] | 0.903 [0.886, 0.920] | 0.014 [0.008, 0.020] | 0.005 [0.000, 0.012] |

Encounters where the model output was valid JSON: baseline 30/30, fine-tuned 30/30.

## 2. Fine-tuned model on the locked test set (no baseline exists for these encounters)

| subset |  encounters | precision | recall | judge-F1 (lenient) | judge-F1 (strict) | hallucination | critical |
|---|---|---|---|---|---|---|---|
| Test A (Batch 1 benchmark) |  500 | 0.949 [0.947, 0.952] | 0.917 [0.907, 0.926] | 0.933 [0.927, 0.938] | 0.898 [0.892, 0.903] | 0.022 [0.020, 0.024] | 0.007 [0.005, 0.008] |
| Test B (curated) |  473 | 0.939 [0.936, 0.943] | 0.925 [0.919, 0.931] | 0.932 [0.928, 0.936] | 0.896 [0.890, 0.901] | 0.026 [0.023, 0.028] | 0.009 [0.008, 0.011] |
| All judged test encounters |  973 | 0.945 [0.943, 0.947] | 0.921 [0.914, 0.927] | 0.933 [0.929, 0.936] | 0.897 [0.893, 0.901] | 0.024 [0.022, 0.025] | 0.008 [0.007, 0.009] |

### Test B by source batch

| batch |  encounters | precision | recall | judge-F1 (lenient) | judge-F1 (strict) | hallucination | critical |
|---|---|---|---|---|---|---|---|
| batch_002 |  100 | 0.951 | 0.935 | 0.943 | 0.910 | 0.021 | 0.009 |
| batch_003 |  60 | 0.911 | 0.826 | 0.866 | 0.805 | 0.042 | 0.018 |
| batch_004 |  52 | 0.953 | 0.933 | 0.943 | 0.913 | 0.016 | 0.008 |
| batch_005 |  69 | 0.938 | 0.943 | 0.940 | 0.903 | 0.027 | 0.005 |
| batch_006 |  40 | 0.939 | 0.939 | 0.939 | 0.902 | 0.027 | 0.010 |
| batch_007 |  20 | 0.905 | 0.936 | 0.920 | 0.873 | 0.040 | 0.023 |
| batch_008 |  30 | 0.951 | 0.946 | 0.948 | 0.910 | 0.015 | 0.005 |
| batch_009 |  102 | 0.940 | 0.935 | 0.938 | 0.908 | 0.028 | 0.008 |

## 3. Per section (all judged test encounters, lenient)

| section | reference facts | predicted facts | recall | precision |
|---|---|---|---|---|
| allergies | 434 | 443 | 0.982 | 0.981 |
| chief_complaint | 973 | 967 | 0.977 | 0.999 |
| clinical_actions | 4508 | 4404 | 0.836 | 0.858 |
| clinical_assessment | 1503 | 1515 | 0.964 | 0.989 |
| clinical_conditions | 625 | 606 | 0.982 | 1.0 |
| clinical_uncertainties | 847 | 827 | 0.774 | 0.752 |
| follow_up | 753 | 747 | 0.971 | 0.983 |
| medical_history.family_history | 584 | 568 | 0.965 | 0.997 |
| medical_history.past_medical_history | 1639 | 1619 | 0.984 | 0.985 |
| medical_history.social_history | 2882 | 2850 | 0.932 | 0.965 |
| medical_history.surgical_history | 449 | 451 | 0.993 | 0.993 |
| medications | 2246 | 2203 | 0.945 | 0.928 |
| negative_findings | 4918 | 4726 | 0.952 | 0.983 |
| physical_examination | 1499 | 1620 | 0.763 | 0.892 |
| procedures_and_investigations | 1413 | 1355 | 0.914 | 0.976 |
| review_of_systems | 1380 | 1368 | 0.973 | 0.981 |
| symptoms | 2760 | 2748 | 0.841 | 0.872 |
| vital_signs | 4278 | 4226 | 0.986 | 0.997 |

Encounters not yet judged: 0. Encounters whose model output was invalid JSON are judged with zero predictions (all their reference facts count as missed).
