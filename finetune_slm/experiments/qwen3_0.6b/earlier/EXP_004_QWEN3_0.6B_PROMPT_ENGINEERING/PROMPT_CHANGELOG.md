# Prompt changelog (append-only)

| Version | Status | Change vs parent | Reason (observed error pattern) | sha256 |
|---|---|---|---|---|
| P00_original_baseline | FROZEN, evaluated in EXP_003 (100 dev encounters) | none; byte-identical copy of `direct_inference_baseline/prompts/direct_extraction_prompt.txt` | baseline | 78c5ab95d0019d0b3c6801ae17f7fa29477dde37d123ecd4fda946e3dd14f604 |
| P01_schema_focused | TEXT WRITTEN, AWAITING USER APPROVAL, not run | parent P00; inserts one 'Structure rules' block (7 rules, 1,646 chars, +352 tokens) before 'Output format'; nothing else changed (`prompts/P01_schema_focused.diff`) | 0/94 schema-compliant; clinical_assessment object in 94/94; roles DOCTOR/person_N | 9095b50196c4313a316127235eeb9937e6b047e9e116a5f057822eaf4d2f7a99 |
| P02_comprehensive | PLANNED | recall + standard clinical terms in normalized fields | recall 2.7%; terminology mismatches among the 276 supported FPs | - |
| P03_evidence_grounded | PLANNED | evidence record per cited line, correct speaker_id | 1 evidence record per encounter; 88.5% unsupported | - |
| P04_negation_temporality | PLANNED | explicit negation/temporality/uncertainty handling | 0/543 gold negatives reproduced | - |
| P05_speaker_attribution | PLANNED | role from the speaker's transcript role, no invention | 51% attribution accuracy | - |
| P06_combined | PLANNED | only strategies with measured gains | decided by results | - |

Rules: a version is never edited after its first run; a fix is a new version (e.g. P01b). Every entry records the parent, the diff file and the reason.

## P01 result (2026-11-12)
Run P01_schema_focused_dev50 on 50 prompt_dev ids: REJECT under the pre-registered rule (total violations 444 -> 658, wrong_type 80 -> 51); micro F1 0.047 -> 0.095, valid JSON 48 -> 50. See reports/03_P01_results.md. Prompt file unchanged.


## P02 proposal (2026-11-12, not run)
prompts/P02_comprehensive_extraction.txt, sha256 cf50ce8efe850cda76fe6eadebf45391fa0461a657e52de5783edb31ccdde5d1. P00 + one "Coverage rules" block (diff: prompts/P02_comprehensive_extraction.diff). Awaiting user approval.

## P02 result (2026-11-12)
Approved and frozen (sha256 cf50ce8e...d5). Run P02_comprehensive_extraction_dev50 on 50 prompt_dev ids: KEEP, 8/8 pre-registered criteria pass. Micro F1 0.047 -> 0.121, recall 0.026 -> 0.082, precision 0.237 -> 0.227; schema violations 444 -> 1064. See reports/05_P02_results.md.

## Status note (2026-11-12)
P02 is KEEP at the development stage only. Its validation run is postponed by user decision; P02 is not validated and not final.

## P03 proposal (2026-11-12, not run)
prompts/P03_evidence_grounded.txt, sha256 da91bc71cdc40f0fcfac8ed4e0f3f4b7bc651fc6244dbc30a1cc50f757d0188d. P00 + one 'Evidence rules' block (diff: prompts/P03_evidence_grounded.diff). Independent of P01 and P02. Awaiting approval.

## P03 frozen (2026-11-12)
Timestamp bullet clarified (truncate decimals). Final sha256 4f7ee6f763aa886ec8090f7bb680f40eaa2f7f89e37175dfd6b8ce29daad5c9f (draft da91bc71... superseded before any run). Frozen and run as P03_evidence_grounded_dev50.

## P03 partial result (2026-11-13)
Inference stopped by the user at 35/50 records (33 valid, 2 invalid JSON, 15 not attempted). PARTIAL evaluation on the 35 attempted ids vs P00 on the same ids: no change in extraction (F1 0.055 vs 0.053), evidence unchanged in kind (one record per encounter, only chief_complaint cites it, 0% strict grounding, 0% timestamp match). Indicative REJECT; not a final result. See reports/P03_PARTIAL_EVALUATION_REPORT.md.

## P03 status (2026-11-13)
REJECTED AS DESIGNED by the user after the partial evaluation; partial results and all artifacts preserved.

## P04 proposal (2026-11-13, not run)
prompts/P04_integrated_segment_evidence.txt sha256 a4c17897b89e90ff4eaea119ea5f4a995b2459652cdf24152b4f174fe217ab68 = P02 + Source rules (segment ids) + template with source_segments and no clinical_evidence; a deterministic evidence builder creates the frozen-schema evidence. Diffs vs P00 and P02 saved. Design: reports/07_P04_architecture_and_design.md. Awaiting approval.

## P04 revised (2026-11-13, not run)
Per user review D1-D5: Source rules reworded (directly states or confirms; question lines only when needed to interpret the response; select by meaning not position; do not cite greetings or small talk unless clinically relevant; minimum number of segments, no absolute maximum). New sha256 e05c8beaf82380bdd9581acd07fc77940a363346eb003d44295364683c5aaf55. Superseded draft a4c17897...ab68 kept in prompts/superseded_drafts/. Builder default cap removed. Design v2: reports/07_P04_architecture_and_design_v2.md. Arm R run offline.

## P04 smoke test result (2026-11-13)
Prompt e05c8bea...f55 unchanged. 5 records: 4 parsed, 00037 invalid JSON after runaway id lists (5365 tokens, 1081 s). Gates S1, S2, S3, S5 FAIL; S6 PASS (4/4). Extraction 40 items vs P02 82 on the same ids (F1 0.089 vs 0.163). Chief complaint cited the doctor's question or the greeting in all four parsed records; long consecutive id runs; spurious fill-in items. See reports/P04_smoke_test_report.md.

## P04 status and P05 proposal (2026-11-13)
P04 REJECTED AS DESIGNED by the user (smoke test: extraction decline vs P02, frequent wrong evidence selection, over-citation, one invalid JSON, latency increase); everything preserved. P05 proposed (design only): P02 extraction (prompt cf50ce8e...d5, outputs untouched) + conservative retrieval-based evidence (p05_retrieval.py, 4 post-hoc revisions v1->v4 disclosed) + existing builder. Locked-test checksum-read audit documented in reports/08_locked_test_access_audit.md; development-only guard built and tested (experiments/dev_guard.py).

## P05 approved and frozen (2026-11-13)
User approved P05 (P02 extraction + R_cons v4 conservative retrieval evidence) with conditions. Freeze manifest sha256 e383d3a352a6e431bc74c49c8c409d15a6e02831b05ee73e47aec472fd56fae0. Integrated dev_guard runner built; dry-run access audits pass; validation not authorised or started. See reports/10-13.

## P05 validation run (2026-11-13)
Authorised by the user against freeze manifest e383d3a3…; 50 validation records; all 15 frozen gates passed; coverage 74.5%, hit-when-cited 99.3%, abstentions-as-misses 89.3%; stage-1 strict F1 0.121 (P02, development stage). Human audit pending. See reports/14_P05_validation_report.md.

### Reporting correction (2026-11-13) to reports/14_P05_validation_report.md
Clarified that hit-when-cited 99.3% = 133/134 and 89.3% = 133/149; 134/149 = 89.9% is matched-fact coverage; 134/530 is the share of cited facts that strictly match gold (not citation precision). Added the 711 vs 702 (empty-key) note. No numbers, outputs or evaluator changed.

### AI independent technical audit (2026-11-13)
Added audit_results/P05_AI_independent_audit/ (report, item scores CSV, summary JSON): AI-assisted, same-session reviewer, not a human or clinical review. 30 cited and 15 abstained items scored; no labels, evaluator outputs for scoring, or locked-test data used; original packets and outputs unchanged.

### P05 root-cause investigation (2026-11-13)
Added audit_results/P05_root_cause_investigation/ (analysis, matrix, recommendations, analysis_scripts). Diagnostic only: no frozen artifact, dataset, validation output or label was modified; no model run; no locked-test access. Nothing implemented pending approval.
