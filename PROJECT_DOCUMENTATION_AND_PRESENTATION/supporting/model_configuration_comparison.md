# Model and run configuration comparison

All values read from repo files; see paths in the last column.

| Setting | 0.6B (EXP_001) | 0.6B (EXP_003–EXP_006) | 0.6B (EXP_007) | 1.7B (P00, P01, P02) | Source |
|---|---|---|---|---|---|
| Model id | Qwen/Qwen3-0.6B | same | same | Qwen/Qwen3-1.7B | `common_1_7b.py`, conversion records |
| Revision | c1899de289a04d12100db370d81485cdf75e47ca | same | same | 70d244cc86ccca08cf5af4e1e306ecf908b1ad5e | conversion records |
| Parameters (computed from config) | ≈0.596 B | same | same | ≈1.721 B | config arithmetic (see `02_…`) |
| Layers / hidden / MLP | 28 / 1,024 / 3,072 | same | same | 28 / 2,048 / 6,144 | `config.json` |
| Context positions | 40,960 | same | same | 40,960 | `config.json` |
| Runtime | HF Transformers (CPU) | `openvino_genai.LLMPipeline` | same | same | `huggingface_client.py`, `ov_client_1_7b.py` |
| Device | CPU i7-8665U | Intel UHD 620 iGPU | same | same (GPU asserted, no fallback) | `phase1_report.md`, `ov_client_1_7b.py` |
| Weights | BF16 loaded as FP32 | FP16 OpenVINO IR | same | FP16 OpenVINO IR (BF16 source) | conversion records |
| Quantisation | none | none | none | none | conversion records |
| Converted weight file | – | 1,192,100,233 B | same | 3,441,150,345 B | conversion records |
| Decoding | greedy, `enable_thinking=False` | same | same | same | `describe()` / run settings |
| temperature / top-p / top-k | not applied | not applied | not applied | not applied | `describe()` |
| max_new_tokens | 6,144 | 6,144 | 2,048 | 4,096 | run configs |
| Pipeline | one call per encounter | fresh pipeline per encounter | same | fresh pipeline per encounter | clients |
| Prompt | direct (78c5ab95) | P00/P01/P02/…, S1 | S1.1 P2 | P00 (78c5ab95), P01 (b51121cd), P02 (F6D5202F) | prompt files |
| Chat template | HF | manual `apply_chat_template`, thinking off | same | same | clients |
| System prompt | none (single user message) | none | none | none | clients |
| Mean latency / record | 634 s | 90–245 s | 78–90 s | ≈1,030–1,130 s | reports |
| Decode speed | ~1.5 tok/s overall | ~5.7 overall (6.7 decode) | – | ~2.7–2.8 decode, ~37–40 prefill | reports, perf logs |
| Peak process memory | not recorded here | ~2.8–3.1 GB | – | 5.9–7.1 GB (RSS/working set) | reports |
| Env | root `.venv` | `env_openvino` (Python 3.12.3) | same | same | README, phase1 report |
| OpenVINO | – | 2026.4.1 | same | 2026.4.1 (GenAI 2026.4.1.0) | preflight, conversion |
| Dataset | `dataset_v2_batch_001_corrected` | same | same | same | README |

Note: the 0.6B → 1.7B comparison is **not controlled** for the token cap (6,144 vs 4,096) or record set (see `01_…` §5).

Hardware: Intel Core i7-8665U (4C/8T, 1.9 GHz), 15.81 GB RAM, Intel UHD 620 (Gen9, 24 EUs, iGPU, device reports 6.79 GB shared memory), Windows 10 22H2 — `HARDWARE_ENV_PREFLIGHT.json`, `phase1_report.md`. Run gate: system available RAM ≥ 8.0 GiB before launch (1.7B P01/P02).
