# EXP_003_QWEN3_0.6B_OPENVINO_GPU_DIRECT

Qwen3-0.6B direct clinical extraction on the Intel UHD 620 through OpenVINO FP16 - **100-record development evaluation completed** (5 smoke-test encounters 00021, 00032, 00034, 00035, 00037 + the remaining 95). The 400 locked-test encounters were **not run**.

Same model revision (c1899de2...), fixed prompt (sha256 78c5ab95...f604, verified), dataset, split, parser, schema validator and evaluator as EXP_001; different runtime,
numerical format (FP16) and hardware. No fine-tuning, LoRA, RAG, prompt change, quantisation, hosted endpoint or Foundry use.

Start here: `final_dev100_report.md`, then `comparison_with_EXP_001_dev100.md`. The earlier smoke-stage documents (`final_smoke_test_report.md`, `comparison_with_EXP_001.md`) are preserved unchanged.
Interim (62-record) snapshot: `evaluation/INTERIM_report_20261112T093318Z.md` - not final.

## Layout
* `preflight_report.json`, `prompt_hash_verification.json`, `source_model_provenance.json`, `environment_details.json`, `inference_config.json`, `experiment_manifest.json`, `run_manifest.json`
* `raw_predictions/`, `parsed_predictions/`, `failed_predictions/` (under `exp_003_dev_smoke_5/`) - raw model text is stored exactly as produced
* `evaluation/` (existing evaluator's reports, comparison JSON, post-run frozen-dataset check), `per_encounter_results/`, `failure_report.json`
* `logs/` (inference log, stdout/stderr, performance per encounter, file-access audit, `gpu_compiler/kernel.errors.txt`)
* `scripts/` - `common.py`, `ov_client.py`, `preflight.py`, `run_inference.py`, `evaluate.py`, `compare_with_exp001.py`, `finalize.py`
* `checksums/experiment_checksums.sha256`; `ov_cache/` (compiled-model cache, regenerable, not hashed)

## Reproduce (PowerShell, from the project root; isolated EXP_002 environment, nothing installed in the root .venv)
```powershell
$e = "direct_inference_baseline\experiments"; $py = "$e\EXP_002_QWEN3_0.6B_GPU_DIRECT\env_openvino\Scripts\python.exe"
mkdir "$e\EXP_003_QWEN3_0.6B_OPENVINO_GPU_DIRECT\logs\gpu_compiler" -Force; cd "$e\EXP_003_QWEN3_0.6B_OPENVINO_GPU_DIRECT\logs\gpu_compiler"   # compiler error files land in the cwd
$env:HF_HUB_OFFLINE = "1"
& $py -B -s ..\..\scripts\preflight.py ; & $py -B -s ..\..\scripts\run_inference.py ; & $py -B -s ..\..\scripts\evaluate.py ; & $py -B -s ..\..\scripts\compare_with_exp001.py
```
Labels are read only by `evaluate.py` after inference. `python-dotenv` is not installed in the isolated environment, so `common.py` stubs `load_dotenv`.

## 100-record stage additions
* Runs: `exp_003_dev_smoke_5` (5, preserved) + `exp_003_dev_remaining_95` (95) -> copied into `exp_003_dev_100` (raw/parsed/failed predictions, `evaluation/exp_003_dev_100/`).
* `per_encounter_results_dev100/`, `failure_report_dev100.json`, `run_manifest_dev100.json`, `evaluation/dev100_performance_details.json`, `evaluation/frozen_dataset_verification_after_dev100.json`, `logs/*remaining_95*`.
* Scripts: `run_remaining_95.py`, `combine_and_evaluate_dev100.py`, `interim_evaluate.py`, `interim_report.py`, `make_dev100_report.py`.
* Checksums: `checksums/experiment_checksums.sha256` (current, whole experiment), `checksums/experiment_checksums_smoke_stage.sha256` (smoke stage, before README update).
