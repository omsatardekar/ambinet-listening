# EXP_001_QWEN3_0.6B_CPU_BASELINE

**Status: COMPLETED - DEVELOPMENT SMOKE TEST ONLY. This is a five-encounter CPU smoke test, not the full 400-encounter baseline.**
**The locked 400-encounter test was NOT executed.** No fine-tuning, LoRA, prompt optimisation or RAG was used.

This directory is an immutable archive. Do not edit it; create a new experiment directory (e.g. EXP_002) for any later run.
All prediction/report files were copied byte-for-byte from `outputs/` (nothing regenerated); see `checksums/experiment_checksums.sha256`.

| Item | Value |
|---|---|
| Model | `Qwen/Qwen3-0.6B`, snapshot `c1899de289a04d12100db370d81485cdf75e47ca` |
| Provider / hardware | Hugging Face Transformers, CPU, float32 |
| Decoding | greedy, `enable_thinking=False`, max_new_tokens 6144 |
| Prompt | `prompt/direct_extraction_prompt.txt`, sha256 `78c5ab95d0019d0b3c6801ae17f7fa29477dde37d123ecd4fda946e3dd14f604` |
| Dataset | `dataset_v2_batch_001_corrected` (500 encounters; 100 development / 400 locked test, seed 20260301) |
| Encounters inferred | 00021, 00032, 00034, 00035, 00037 (all from the development split) |
| Original runs | `exp_dev_smoke_5` (5 encounters, primary) and `exp_dev_probe_1` (1-encounter probe, supplementary) |

## Results (preliminary; 5 encounters, not statistically conclusive)
Micro precision 0.111, micro recall 0.018, micro F1 0.030, macro F1 0.019. JSON validity 5/5, schema compliance 0/5.
About 1.5 tokens/s, mean latency 634 s per encounter (range 386-1320 s). Outputs were 597-1,948 tokens; the model stopped on its own (no truncation) and omitted most schema sections.
No inference errors; `failed_predictions` directories were empty. See `reports/failure_report.json`.

## Layout
* `experiment_manifest.json` - full manifest incl. sha256 and original source path of every archived file
* `model_details.json`, `inference_config.json`, `environment/` (pip freeze, Python/OS/CPU)
* `prompt/`, `split/` (development_ids, test_ids, split_metadata), `inference_config_source/`
* `predictions/raw_predictions/`, `predictions/parsed_predictions/` (the 5 encounters)
* `reports/` - evaluation_report.json/.md, per_encounter_results.jsonl, confusion_matrices.json, run_manifest.json (original); inference_summary.json, failure_report.json (derived from run_manifest at archive time)
* `logs/inference.log` - the shared module log (covers both the probe and smoke runs; contains HTTP model-hub lookups and per-encounter lines, no secrets)
* `supplementary_probe_exp_dev_probe_1/` - earlier one-encounter probe (00021)
* `code_snapshot/` - the exact inference/evaluation/config source used (the module is untracked in git)
* `checksums/experiment_checksums.sha256`

Files created at archive time (not copies): `README.md`, `experiment_manifest.json`, `model_details.json`, `inference_config.json`, `environment/*`, `reports/inference_summary.json`, `reports/failure_report.json`.
