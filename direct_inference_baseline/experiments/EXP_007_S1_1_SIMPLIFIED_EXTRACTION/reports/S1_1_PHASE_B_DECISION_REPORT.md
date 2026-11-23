# EXP_007 S1.1 – Phase B decision report (B1 and B2)

**Scope: development-set results only** (the same 50 prompt-development records used for P02/S1.0; these records were used for earlier tuning, so nothing here is independent validation). No validation-50, locked-test-400, sealed-hash or Batch 002 data were opened (per-arm audits: 0 locked-test files, sealed file not opened, 0 validation records, labels read for the 50 dev ids only after inference). Labels are generator-derived, not human-verified.

Prompt P2 was selected by **Amendment 001, a post-hoc design amendment** (thresholds chosen after Phase A results were seen). The original Phase A gates are not represented as passed: original Gate C failed, so B3 (constrained decoding) was not run.

Both arms: P2 prompt, Qwen3-0.6B FP16 OpenVINO on GPU, greedy, thinking off, `max_new_tokens` 2048, same 50 ids, no tuning between arms, frozen files unchanged (hash checks pass). B1 = original rendering (`[SEG] person_N (ROLE)`); B2 = role-label rendering (`role: text`) with sidecar. Failed outputs contribute zero predictions (headline = all 18 categories). Raw numbers: `evaluation/B1/`, `evaluation/B2/`.

## 1. Headline comparison

| | P02 (primary) | S1.0 | B1 | B2 | Threshold |
|---|---|---|---|---|---|
| Strict micro P / R / F1 | 0.227 / 0.082 / **0.1207** | 0.279 / 0.076 / 0.1192 | 0.268 / 0.115 / **0.1610** | 0.272 / 0.097 / **0.1427** | F1 ≥ 0.1507 |
| Strict macro P / R / F1 | 0.198 / 0.100 / 0.1222 | 0.234 / 0.086 / 0.1160 | 0.259 / 0.148 / 0.1625 | 0.250 / 0.119 / 0.1454 | – |
| Micro F1 excl. clinical_conditions | – | – | 0.1634 | see JSON | disclosed separately |
| Valid JSON (of 50) | 50 output records | 37 | **45** | **31** | ≥ 48 |
| Canonical fully schema-compliant records | 0 | 0 | 0 | 0 (1 record fully valid S1.1 format) | – |
| Speaker attribution accuracy | 0.421 | 0.088 | **0.211** | **0.953** (128 entities in 31 parsed records) | ≥ 0.42 |
| Category collapse vs P02 | – | – | review_of_systems | review_of_systems | none allowed |
| Token-cap hits | – | – | 0 | 0 | recorded |
| Repetition-loop records / empty collapse | – | – | 0 / 0 | 1 / 0 | recorded |
| Mean output tokens | 1356 | 617 | 506 | 531 | – |
| Mean latency / encounter (s) | 235.5 | 106.6 | 90.1 | 78.1 | – |

**Acceptance (earlier approved thresholds):** B1 passes micro F1 only (fails 48/50 valid JSON, speaker ≥ 0.42, no category collapse). B2 passes speaker accuracy only (fails F1 0.1427 < 0.1507, valid JSON 31/50, category collapse). **Neither arm is accepted.**

## 2. Clinical metrics

| | P02 | S1.0 | B1 | B2 |
|---|---|---|---|---|
| Medication recall (strict) | 0.359 | 0.320 | 0.297 | 0.344 |
| Medication dose accuracy on matched (gold non-null) | 0.875 | 0.917 | 0.939 | 0.972 |
| Missing prescribed medications (of 29 planned) | 25 | 25 | 24 | 25 |
| Allergy-status errors (of 50) | 28 | 28 | 19 | 21 |
| Negative-finding recall | 0.000 | 0.022 | 0.048 | 0.040 |
| Investigations/procedures recall | 0.110 | 0.183 | 0.256 | 0.195 |
| Follow-up recall | 0.044 | 0.222 | 0.622 | 0.533 |
| Contradictions (same item pos. and neg.) | 16 | 4 | 1 | 0 |
| Unsupported facts (evaluator) | 85 | 60 | 55 | 41 |

Allergy-status errors count records with no parsed output as errors, so B2's 21 includes 19 failed records' effect and is not a clean comparison.

## 3. Per-category recall (strict)

Gains over P02 (B1 / B2): follow_up 0.044→0.622 / 0.533; clinical_assessment 0.090→0.213 / 0.124; investigations 0.110→0.256 / 0.195; negative findings 0→0.048 / 0.040; social history 0→0.106 / 0.053; family history 0.138→0.241 / 0.172.
Losses: chief_complaint 0.140→0.020 / 0.020; review_of_systems 0.086→**0.000 / 0.000** (collapse); clinical_actions ~0 for all; physical_examination 0.013→0.013 / **0.000**; clinical_conditions 0.026→0 (by design, removed from generation; adapter emits the schema's empty list); vital_signs 0.187→0.183 / 0.146. Greater than 50% recall drop vs P02: B1 {chief_complaint, review_of_systems, clinical_conditions, clinical_actions}; B2 adds physical_examination.

## 4. Did role-label rendering improve speaker attribution without reducing recall?

- **Speaker attribution: yes, clearly.** B1 reproduces the S1.0 failure mode (444 `invalid_role` flags: the model copies `person_N` instead of the bracketed role; accuracy 0.211). B2 gives 0.953 (patient 80/81, doctor 36/37) with 0 invalid-role flags (7 role_missing, 3 role_unavailable from the sidecar).
- **Recall: not cleanly answerable, but B2 did not obviously reduce it.** On the 28 records both arms parsed, B2 recall is 0.151 vs B1 0.126 (micro F1 0.193 vs 0.172; P02 0.132 on the same records). B2's lower overall recall (0.097 vs 0.115) is driven by 19 failed records vs 5, not by lower extraction on parsed records. Per category B2 is lower than B1 in many categories (e.g., clinical_assessment, follow-up, social history), so this should be read as unproven.
- **But B2 is structurally worse:** 19/50 invalid JSON (all "Expecting ',' delimiter" errors, no token-cap hits) vs 5/50 for B1. The speaker accuracy is measured on the 31 parsed records only (3 further records excluded as UNKNOWN speaker).

## 5. Parsed-only diagnostics (labelled diagnostics, not headline results)

| Subset | System | Micro P / R / F1 |
|---|---|---|
| 45 records B1 parsed | B1 | 0.268 / 0.127 / 0.173 |
| same 45 | P02 | 0.236 / 0.086 / 0.126 |
| 31 records B2 parsed | B2 | 0.272 / 0.154 / 0.197 |
| same 31 | P02 | 0.246 / 0.087 / 0.129 |

These exclude failures and therefore flatter the arms. Only the all-50 numbers in Section 1 are results. The parsed-only 0.154 S1.0 figure from EXP_006 remains a diagnostic and not S1.0's overall score.

## 6. Interpretation and caveats

- B1's F1 of 0.161 clears 0.1507 by 0.010. The prompt-dev set is 50 records with ~1,860 gold items; the confidence interval around a ~0.04 F1 difference was not computed here and is probably wide. The improvement comes mainly from categories where short, explicit statements exist (follow-up, assessment, investigations, social history) and is partly offset by collapse in review_of_systems and chief_complaint. A 0.6B model is also writing short fixed-format output, so more of the gain may reflect output-format effects than better extraction.
- Format compliance is poor in both arms: 621 (B1) and 62 (B2) enum violations, mostly `reported_by` (B1: person_N copies), so 0/50 canonical-compliant records for every system, P02 included.
- Compared with P02, both arms are 2.6–3x faster and produce ~60% fewer output tokens, a real efficiency gain.
- Phase A synthetic results are not comparable with real-data results and are context only.

## 7. Recommendation

1. **Reject B1 and B2 as the final extraction configuration** (neither meets the approved acceptance set). B1 is the only arm with a measured micro-F1 gain, but it fails valid JSON, speaker attribution and category-collapse criteria.
2. **Retain two findings:** (a) role-label rendering fixes speaker attribution (0.21→0.95) and cuts input tokens ~40% (3,404→2,062 mean); (b) the shorter S1.1 output structure improves speed. Both are worth carrying forward in any later design.
3. **Meaningful extraction improvement was not demonstrated.** The best arm gains +0.04 F1 over P02 on the dev set, with no independent validation. Per your stated rule, I recommend **stopping further S1 prompt experimentation on these 50 records** rather than tuning further against them. If you want to proceed anyway, the justified next step is a decision on the structural problem (invalid JSON in B2 and category collapses) via a different mechanism, e.g. a new, separately approved design, not another round of prompt edits.
4. B3 (constrained decoding) was not run because Gate C failed and it was not authorised. S2–S4 and fine-tuning have not been started.

## 8. Limitations and disclosures

Post-hoc Amendment 001 (thresholds chosen after Phase A results were seen); dev-set only and previously used for tuning; generator-derived labels; clinical_conditions removed from generation (reported separately, adapter emits empty list); failed outputs count as zero predictions; speaker accuracy denominators differ between systems (152 / 128 / 126 / 102 entities); allergy-status and speaker comparisons are not on identical record sets; no confidence intervals computed.

## 9. Integrity

Frozen hashes unchanged after each run; `git status` shows no modified tracked files (only untracked EXP_006/EXP_007 etc.); nothing pushed to GitHub; P00–P05, EXP_001–006, schemas and datasets untouched. Supporting files: `evaluation/PARSED_ONLY_DIAGNOSTIC_B1_B2.json`, `evaluation/B1_VS_B2_SAME_PARSED_RECORDS.json`, `logs/phase_b_exit_codes.txt`, `logs/file_access_audit_B1.json`, `_B2.json`, `manifests/S1_1_B*_RUN_SETTINGS.json`.
