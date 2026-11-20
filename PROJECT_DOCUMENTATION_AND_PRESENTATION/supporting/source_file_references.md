# Source file references (verify any number here)

`[1.7B]` = `direct_inference_1_7B/` · `[0.6B]` = `direct_inference_baseline/` · `[EXP2]` = `direct_inference_1_7B/experiments/EXP_002_PROMPTING_INFERENCE/`

## Prompts
- P00 direct: `[1.7B]/prompts/P00_direct_inference_prompt.txt` (byte-identical to `[0.6B]/prompts/direct_extraction_prompt.txt`)
- P01: `[1.7B]/prompts/P01_schema_guided.txt` (= `[EXP2]/prompt_versions/P01_schema_guided.txt`)
- P02 (evaluated): `[EXP2]/prompt_versions/P02_p01_schema_no_evidence.txt`
- 0.6B prompt versions and changelog: `[0.6B]/experiments/EXP_004_QWEN3_0.6B_PROMPT_ENGINEERING/prompts/`, `PROMPT_CHANGELOG.md`, `PROMPT_COMPARISON.md`

## Model, conversion, hardware
- 1.7B conversion/download/smoke: `[1.7B]/manifests/CONVERSION_RECORD_Qwen3-1.7B.json`, `DOWNLOAD_VERIFICATION_Qwen3-1.7B.json`, `HARDWARE_ENV_PREFLIGHT.json`, `SMOKE_TEST_GPU_VERIFICATION.json`
- 1.7B config: `[1.7B]/models/hf_cache/models--Qwen--Qwen3-1.7B/snapshots/70d244cc…/config.json`
- 0.6B conversion: `[0.6B]/experiments/EXP_002_QWEN3_0.6B_GPU_DIRECT/conversion_record.json`, `phase1_report.md`, `feasibility_plan.md`

## Code
- Runner: `[1.7B]/scripts/run_prompt.py`; client: `[1.7B]/scripts/ov_client_1_7b.py`; common: `common_1_7b.py`; evaluate: `evaluate_run.py`
- Inference loop & parser: `[0.6B]/inference/inference_runner.py`, `output_parser.py`
- Evaluator (frozen): `[0.6B]/evaluation/entity_matching.py`, `evaluation_runner.py`, `attribute_metrics.py`, `clinical_metrics.py`, `evidence_evaluator.py`, `schema_validator.py`
- P02 helpers: `[EXP2]/p02/code/` (`backfill_evidence.py`, `p02_evaluate.py`, `analyse_run.py`, `compare_p01_p02.py`, `verify_prompt.py`, `stop_rules.py`)

## Results
- 1.7B P00 (50): `[1.7B]/experiments/EXP_001_DIRECT_INFERENCE/reports/P00_direct_dev50_EVALUATION.md`, `STAGE1_BASELINE_REPORT.md`, `evaluations/P00_direct_dev50/METRICS.json`
- P01 vs P00 (30): `[EXP2]/reports/P01_VS_P00_30RECORD_EVALUATION_REPORT.md`; raw: `[EXP2]/evaluations/P01_schema_guided_dev50/subset30/{METRICS,CATEGORY_METRICS}.json`
- P02: `[EXP2]/reports/P02_EXPERIMENT_REPORT.md`, `P02_VS_P01_METRICS.md`; raw: `[EXP2]/p02/derived/P02_ANALYSIS.json`; run: `[EXP2]/logs/P02_STOP_RULE_RESULT.json`, `inference_P02.log`, `performance_P02.json`
- P02 design/audit: `[EXP2]/reports/P02_STAGE1_AUDIT.md`, `P02_PROMPT_DESIGN_AND_VALIDATION.md`, `P02_EXPERIMENT_PLAN.md`
- 0.6B: `EXP_001…/README.md`, `EXP_003…/final_dev100_report.md`, `comparison_with_EXP_001_dev100.md`, `EXP_004…/PROMPT_COMPARISON.md`, `reports/03_P01_results.md`, `05_P02_results.md`, `14_P05_validation_report.md`, `EXP_005…/reports/S0_2_EVALUATION_REPORT.md`, `EXP_006…/reports/S1_EXPERIMENT_REPORT.md`, `EXP_007…/reports/S1_1_PHASE_B_DECISION_REPORT.md`
- Freeze manifests: `[1.7B]/manifests/FREEZE_P00_direct_dev50.json`, `FREEZE_P01_schema_guided_dev50.json`, `FREEZE_P02.json`, `P02_30_IDS.json`, `FROZEN_50_PROMPT_DEV_IDS.json`

## Data
- Dataset: `dataset_v2_batch_001_corrected/` (Batch 001 500 encounters; `batch_002/` 500 more, unallocated)
- Schema: `clinical_extraction_schema.json`; docs: `docs/output_schema.md`, `docs/architecture.md`
