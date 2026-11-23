# P02 — experiment plan (current)

**P01** = original schema-guided baseline (completed, 30 records, unchanged). **P02** = the current improved prompt: the P01 prompt and 20-key output schema, without model-written evidence, plus a concise extraction guide. P02 is the only active post-P01 experiment; earlier intermediate attempts are archived in `archive/obsolete_experiments_after_P01/` (see `P02_WORKSPACE_CLEANUP_REPORT.md`).

## Question
Does P02 extract more of the information that is in the transcript (recall) without a large loss of precision, and does it keep the output valid? Compared with P01 on exactly the same 30 records. F1 here is precision/recall over matched facts, not accuracy.

## Fixed inputs
| Item | Value |
|---|---|
| Prompt | `prompt_versions/P02_p01_schema_no_evidence.txt` (strengthened; see `P02_PROMPT_DESIGN_AND_VALIDATION.md`), sha256 `F6D5202F26D97C2D73C9D00ADBCA050BC7114AD8B0272749EEFF8D0757DE09B0` |
| Records | `manifests/P02_30_IDS.json` (the 30 P01 records, frozen order) |
| Dataset | `dataset_v2_batch_001_corrected` (development-only, generator-derived labels) |
| Model | Qwen3-1.7B, revision `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`, OpenVINO FP16, GPU, greedy, thinking off, 4,096-token cap, fresh pipeline per record |
| Run controls | status: **completed 2026-11-15 (30 records, 28 parsed); results in `P02_EXPERIMENT_REPORT.md`**; RAM gate 8.0 GiB (six readings, final >= 8.0), no retries, stop on OOM; run id `P02`; freeze and config are created by the pre-flight at launch |
| Early stop (`p02/code/stop_rules.py`, unchanged) | (1) record 1 does not parse; (2) two of the first three records do not parse; (3) two of the first three parsed records have 16 or more of 18 sections empty. After record 3 all 30 run |

## Evidence handling
The model leaves `clinical_evidence` empty and writes segment ids in `evidence_ids`. `p02/code/backfill_evidence.py` (reusing `evidence_resolver.py`) validates the ids against the transcript, builds `clinical_evidence` and `EV_nnn` ids, and flags invalid ids without repairing them. Evidence metrics are reported separately from entity metrics.

## Evaluation
- Official: the frozen strict matcher (`direct_inference_baseline/evaluation/entity_matching.py`, unchanged) through `p02/code/p02_evaluate.py`; all 30 records, failed = zero predictions; parsed-only shown separately.
- Additional, labelled as diagnostics only: the matcher's fuzzy mode and predicted/gold count ratios (`p02/code/analyse_run.py`).
- Reported: P/R/F1 with TP/FP/FN, per category, JSON validity, truncations, evidence validity, speaker attribution, runtime, memory.

## Why earlier P02 attempts were archived (findings kept here; documents are in the archive)
- Draft v2.1 (model-written evidence, 4,164-token template): in a three-record pilot, 2 of 3 outputs hit the 4,096-token cap; stopped by its early-stop rule.
- v2.2 (compact schema: renamed fields, sparse keys, reordered sections, worked example): in a six-record pilot, 3 of 6 outputs were invalid JSON, two parsed outputs had 16–17 of 18 sections empty, and the worked example leaked into answers. Rejected because it changed the output contract; the contract is now fixed to P01's.

## Limits
Development-only. The three naming vocabularies in the prompt (vital-sign names, social-history categories, review-of-systems systems) were read from the dev gold conventions. Strict keys for actions and follow-up contain free text and cap what any prompt can score there.
