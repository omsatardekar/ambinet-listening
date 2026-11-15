# EXP_006 – S1 Simplified Stage-1 Extraction

Development-set experiment (50 prompt-development records) testing a simplified, compact Stage-1 extraction against P02 with Qwen3-0.6B, OpenVINO FP16, Intel UHD 620 GPU. Not clinical validation.

**Result:** strict micro F1 0.1192 vs P02 0.1207 (no improvement; target 0.40–0.45 not reached). Precision up (0.227→0.279), output tokens and latency about halved, but 13/50 outputs were invalid JSON and speaker attribution collapsed. Recommendation: revise. See `reports/`.

Layout: `prompts/` (frozen prompt, design note), `config/`, `s1/` (adapter, tests, runner, evaluator), `outputs/{raw,parsed,failed,adapted}`, `evaluation/` (metrics, per-record metrics, diagnostics), `logs/`, `manifests/` (freeze, pre-flight, run), `reports/`, `ov_cache/` (compiled-model cache; not for version control).

Reproduce: from this directory with the project OpenVINO env: `python -B s1/test_s1_adapter.py`, `python -B s1/run_s1.py`, `python -B s1/evaluate_s1.py`, `python -B evaluation/s1_output_diagnostics.py`. Frozen files are recorded in `manifests/S1_FREEZE_MANIFEST.json`.
