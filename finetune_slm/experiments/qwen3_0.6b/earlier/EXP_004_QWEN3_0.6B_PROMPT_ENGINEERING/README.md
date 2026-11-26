# EXP_004_QWEN3_0.6B_PROMPT_ENGINEERING

Systematic, version-controlled prompt engineering study for Qwen3-0.6B direct clinical extraction (OpenVINO FP16, Intel UHD 620 GPU, runtime and settings of EXP_003).
**Status: SETUP ONLY. No inference has been run.** Awaiting approval of the P01 design (`reports/01_P01_experiment_design.md`).

## Immutable (never modified by this experiment)
EXP_001, EXP_002, EXP_003 (including its prompt), the frozen dataset and labels, the frozen schema, the existing evaluator and module code, the locked 400-record test set (not used at all).

## Layout
* `prompts/` - every prompt version (`P00_original_baseline.txt` = byte-identical copy of the EXP_003 prompt, sha256 78c5ab95d0019d0b3c6801ae17f7fa29477dde37d123ecd4fda946e3dd14f604, verified). Never overwritten.
* `experiments/` - split definition (`split_v1.json`, `make_split.py`) and per-version runner/config scripts.
* `outputs/<prompt_version>/` - raw, parsed and failed predictions per version (separate directories).
* `evaluation/<prompt_version>/` - evaluator outputs per version; `P00_baseline_subset_metrics.json` (P00 reference on the two subsets, derived from EXP_003).
* `reports/` - `00_error_analysis_and_split.md`, `01_P01_experiment_design.md`, later one short report per experiment.
* `analysis/` - read-only error analysis of EXP_003 (`error_analysis_exp003.py/.json`).
* `PROMPT_CHANGELOG.md`, `PROMPT_COMPARISON.md`, `EXPERIMENT_MANIFEST.json`.

## Method summary
Split of the 100 EXP_003 development encounters into 50 `prompt_dev` (tuning) and 50 `validation` (selection only), stratified by specialty x complexity, seed 20260401.
Same encounter ids for every prompt version; each version: exact text + sha256, model revision, inference settings, ids, date, evaluator version, raw outputs, evaluation. The final prompt (`FINAL_PROMPT.md`) is chosen on validation results, not development results.
Out of scope: LoRA/fine-tuning, Qwen3-1.7B, locked-test evaluation, RAG, quantisation, hosted endpoints.
