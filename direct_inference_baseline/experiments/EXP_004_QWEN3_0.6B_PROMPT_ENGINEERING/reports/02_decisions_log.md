# EXP_004 decisions log (user approvals)

## Decision 1 - P01 design approved (user)
1. 50/50 reproducible split approved; validation is an INTERNAL validation set (earlier aggregate error analysis covered all 94 valid EXP_003 outputs).
2. The 50 prompt_dev records are used for prompt iteration; individual validation outputs/errors must not be inspected during prompt development.
3. P00 reproducibility on 3 prompt_dev records (00035, 00037, 00040 = first three sorted ids) with exactly the EXP_003 model, prompt and settings.
4. Original P00 outputs preserved; new outputs written to separate directories; nothing overwritten.
5. P01 keep/reject thresholds approved: total schema violations -30% or more; wrong_type -80% or more; valid JSON not worse by more than 2; micro F1 drop at most 0.005; no category with P00 F1 > 0.1 loses more than 0.05; no substantial output-length collapse.
6. Additionally report: fully schema-compliant records, missing-field, wrong-type and invalid-enum violations, precision and recall separately.
7. Show the complete exact P01 text and its SHA-256 before any P01 inference; P01 inference only after the user approves the frozen text.

## Status
* P00 reproducibility run started (run id P00_repro3). P01 inference NOT started.

## Decision 2 - P01 text approved and frozen (user)
* P01 text sha256 9095b50196c4313a316127235eeb9937e6b047e9e116a5f057822eaf4d2f7a99 approved; `prompts/P00_original_baseline.txt`, `P01_schema_focused.txt` and `.diff` set read-only.
* Order: finish the P00 3-record reproducibility check and report it, then run P01 on the 50 prompt_dev ids, apply the approved keep/reject thresholds, stop. P02 only after the user reviews P01.
* Operationalisation fixed BEFORE seeing any P01 output: "substantial output-length collapse" = mean output tokens < 0.70 x P00 or predicted entities < 0.70 x P00 on the same ids. Total schema violations are counted over valid-JSON records (invalid JSON has no schema result); violations per valid record are reported as well. P00 reference = EXP_003 outputs for the same 50 ids (or, if the reproducibility check shows differences, reported with that caveat).

## P00 reproducibility result (3 prompt_dev records: 00035, 00037, 00040)
All 3 raw outputs are byte-identical to the original EXP_003 outputs (same chars, same token counts 656/1948/623, same SHA-256). File-access audit: 516 files opened, 0 label/blueprint. Evidence: `evaluation/P00_repro3_comparison.json`, `outputs/P00_repro3/`. Conclusion: GPU greedy generation is reproducible across sessions, so EXP_003 outputs are a valid P00 reference for the paired comparison.
P01 inference on the 50 prompt_dev ids started after this check (run id P01_schema_focused_dev50).

## 2026-11-12 P01 inference and evaluation
P01 run finished (50/50 parsed, 0 label accesses). Evaluated with the unmodified evaluator; keep rule applied as pre-registered: REJECT (fails total-violation >=30% reduction and wrong_type >=80% reduction). No P01b, P02 or validation run started; awaiting user review.


## 2026-11-12 P02 design prepared (no inference)
User formally accepted the P01 REJECT, chose P02 (comprehensive extraction, built from P00 only, no P01 rules). Analysis on prompt_dev only: analysis/underextraction_dev50.*, analysis/key_vocab_concentration_dev50.json. P02 text saved as prompts/P02_comprehensive_extraction.txt (sha256 cf50ce8e...d5, not frozen), design in reports/04_P02_experiment_design.md. First draft contained label-overlapping vocabulary (detected by leak check) and was rewritten; final leak check 0 hits. Awaiting approval; no P02 inference, no P01b/P03.

## 2026-11-12 P02 approved and frozen
User approved P02 text and sha256 cf50ce8e...d5 (no label-derived vocabulary), the settings and all 8 criteria. Prompt file set read-only; manifest updated. Inference on the 50 prompt_dev ids started. No P01b/P03/vocabulary/LoRA/1.7B.

## 2026-11-12 P02 inference and evaluation complete
50/50 parsed, 0 label accesses. Criteria applied as pre-registered: KEEP (8/8). Validation not run. Awaiting user review; nothing further started.

## 2026-11-12 P02 validation postponed; P03 design prepared
User decision: P02 validation is postponed; P02 is KEEP at development stage only (not validated, not final). P03 (evidence-grounded) chosen as an independent experiment from P00. Design: reports/06_P03_experiment_design.md; prompt prompts/P03_evidence_grounded.txt sha256 da91bc71...8d (not frozen); leakage check 0 hits. No inference started; P04, fine-tuning, validation not started.

## 2026-11-12 P03 approved; timestamp rule clarified; frozen
User approved P03 design and criteria and asked for the timestamp conversion rule. Measured on the 100 development labels (analysis/timestamp_convention_dev.py): label MM:SS equals floor(seconds) for 7012/7032 timestamp fields; where the fractional part is >= 0.5 floor matches 3516/3526 and rounding 0/3526 -> convention is truncation (drop decimals). The 20 mismatches differ by more than a rounding error (e.g. 104.27 s labelled 01:54), most likely label noise or duplicate segment text. Draft wording ('whole seconds', example 75.30) was ambiguous, so the bullet was changed to 'drop the decimals, never round up (75.80 -> 01:15, 125.40 -> 02:05)'. New sha256 4f7ee6f7...c9f (old draft da91bc71... was never run). Leakage re-check 0 hits. Prompt frozen (read-only); P03 inference started. E4 stays +-1 s as approved; the exact-floor match rate is also reported.

## 2026-11-13 P03 stopped by user; partial evaluation
User stopped P03 inference after seeing evidence problems (e.g. 00215, 00248). Processes force-stopped 01:48 IST (one in-flight record lost, nothing deleted). Verified 35 attempted / 33 valid / 2 invalid (00127, 00264) / 15 not attempted. Partial evaluation on the 35 ids with paired P00 on the same ids: reports/P03_PARTIAL_EVALUATION_REPORT.md. Recommendation: reject P03 as designed; redesign needs user approval. No P04, validation, fine-tuning or further inference.

## 2026-11-13 P03 rejected as designed; P04 design prepared
User agreed with the partial P03 evaluation: P03 REJECTED AS DESIGNED. New direction: P04 integrated experiment (not P02+P03 concatenation). Offline investigation (no inference): anchoring evidence (181/181 outputs have exactly one evidence record across P00-P03); transcript structure verified on 100 dev inputs; gold evidence conventions measured; evaluator lexical grounding ceiling on gold 66% and lexical retrieval 86.7% (metric is gameable); builder prototype reproduces gold evidence for all 100 dev labels (3516/3516). P04 prompt sha256 a4c17897...68 (not frozen). Awaiting approval; no inference, no smoke test, no arm R run yet.

## 2026-11-13 P04 design review (D1-D5) and revisions
User approved the P04 architecture with revisions: question/answer wording, greeting wording, no fixed id maximum (also removed from the builder), smoke S4 report-only and S6 clarified (integrity check; invalid references reported separately; full intermediate and final JSON for all five records), arm R approved and run offline (no inference), D5 gates kept as provisional development gates; the 50 prompt_dev records are not an independent validation set; the 50-record validation subset is preserved for later; locked test untouched. New prompt sha256 e05c8beaf82380bdd9581acd07fc77940a363346eb003d44295364683c5aaf55 (not frozen). Smoke ids verified (prompt_dev, not validation, not test). Arm R results: extraction identical to P02 (153/522/1707); gold-segment hit-any R_main 81.1%, R_simple 88.9%; evaluator lexical grounding 80-87% (circular, above gold's 66%). No model inference run; smoke test not started; waiting for approval.

## 2026-11-13 P04 approved; smoke test authorised and started
User approved the revised P04 prompt (sha256 e05c8beaf82380bdd9581acd07fc77940a363346eb003d44295364683c5aaf55), smoke gates S1-S6 (+ per-encounter reporting of facts/valid refs/no refs/invalid refs/records/questionable refs), V3 relaxed to reporting only (no minimum record count), V5 provisional 73.9% with denominator and matched-item coverage always reported (not overall clinical evidence accuracy). Smoke test authorised for 00035, 00037, 00040, 00215, 00248 only. Pre-flight passed (prompt hash, ids in prompt_dev and not in validation/test, OpenVINO FP16 model files vs EXP_002 conversion record, settings identical to P02/P03 manifests, 6144 cap). Started 2026-11-13 02:16 local. No 50-record run, no P02 validation.

## 2026-11-13 P04 smoke test completed
Run P04_smoke_5 (02:16-02:49 local, 2016 s): 4/5 parsed; 00037 invalid JSON (runaway id lists). Gates S1 FAIL, S2 FAIL (82.5% facts with valid ref), S3 FAIL (3/5 with >=5 records; counts inflated by long runs), S5 FAIL (items 40 vs 82), S6 PASS (4/4; 0 label files; 0 test transcripts used). Manual reading: 11 appropriate / 7 questionable / 15 wrong of 33 referenced facts; 7 facts without reference. Disclosure recorded: the existing runner hashes all 500 input transcripts (400 locked-test) at the start of every run (evaluation/frozen_dataset_hash_access_audit.json); no labels. Stopped for user review; no 50-record run started.

## 2026-11-13 P04 rejected as designed; P05 design and diagnostics (no inference)
User rejected P04 as designed (smoke test), asked for P02 + conservative retrieval-based evidence and a documented locked-test access audit. Done offline: audit (reports/08), dev-only guard + test (0 locked-test files opened by the guarded check), Arm R ladder (R_simple/R_main vs conservative steps), retrieval rule validity on gold, abstention and conflict analysis, builder integration on copies of P02 outputs (extraction identical), qualitative read (30 ok / 3 questionable / 3 wrong of 36; mine, not independent), sensitivity. Rules were revised four times after seeing prompt_dev results (v1->v4, disclosed); results are development-only. P02 prompt and outputs not modified. No model inference, no GPU, no validation, no locked-test labels. Awaiting review.

## 2026-11-13 P05 approved; freeze and integration (no inference)
D1-D5 approved: P05 architecture/provisional gates; conservative abstention for unreachable categories (no semantic matcher); 45-fact human audit as a feasibility check; freeze before validation; guard integration. Done: R_cons v4 source/config/builder/evaluator/schema/P02 prompt hashed in P05_FREEZE_MANIFEST.json (sha256 e383d3a352a6e431bc74c49c8c409d15a6e02831b05ee73e47aec472fd56fae0); four post-hoc revisions and limitations recorded; StrictAccessSpy + authorisation gate integrated in run_p05_validation.py; dry-run spy reports (0 locked-test files, 0 sealed-file opens, 0 labels in inference/post-processing, 0 validation records); disclosed and fixed a label-regex defect in the new spy before the final freeze; validation protocol, gates and audit plan written. No inference, no GPU, no validation record read. Awaiting user review and explicit authorisation.

## 2026-11-13 P05 validation executed
Run under the recorded authorisation with frozen files; no locked-test access; evaluator and builder unchanged. Report: reports/14_P05_validation_report.md. No further experiment started; awaiting user review.
