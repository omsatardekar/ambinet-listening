# Stage 1 – Qwen3-1.7B direct inference (P00), 50 prompt-dev records

DEVELOPMENT-ONLY. The 50 records were used earlier for 0.6B prompt development; labels are generator-derived. No independent or clinical validation is claimed.

## Setup (all frozen before inference)
- Model `Qwen/Qwen3-1.7B` @ `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`, download verified against Hub LFS hashes (`manifests/DOWNLOAD_VERIFICATION_Qwen3-1.7B.json`).
- OpenVINO FP16 export (`manifests/CONVERSION_RECORD_Qwen3-1.7B.json`), explicit GPU device (Intel UHD 620), GPU execution verified from Windows GPU-engine counters in the smoke test; no CPU fallback.
- Prompt P00 = unchanged 0.6B direct prompt (sha256 78c5ab95…f604). Greedy, thinking disabled, `max_new_tokens`=4096 (0.6B runs used 6144 – disclosed difference).
- 50 frozen ids (`manifests/FROZEN_50_PROMPT_DEV_IDS.json`), fresh pipeline per record.
- Audit: 0 locked-test files, sealed hash file not opened, 0 labels during inference, 0 validation records; frozen 0.6B hashes unchanged.

## Result (full table: `P00_direct_dev50_EVALUATION.md`, metrics: `evaluations/P00_direct_dev50/METRICS.json`)
| | 0.6B P00 | 0.6B P02 | 1.7B P00 |
|---|---|---|---|
| Strict micro F1 | 0.0474 | 0.1207 | **0.1528** |
| Strict macro F1 | 0.0478 | 0.1222 | 0.1444 |
| Valid JSON / 50 | 48 | 50 | **35** |
| Token-cap hits | 0 | 0 | **15** |
| Unsupported claims | 4 | 85 | 104 |
| Mean latency / record | 153 s | 236 s | **1134 s** |
| Decode tok/s | – | 6.7 | 2.8 |

## Findings
- Same prompt: 1.7B is much better than 0.6B (F1 0.047 → 0.153) and slightly above the best 0.6B prompt, even though 30% of records produced no scorable output (failed records count as zero predictions, so 0.153 is a floor for what the model can do on parsed records).
- **15/50 outputs hit the 4096-token cap** and are unparseable: this is the dominant failure mode, a cost of the user-specified cap, not a conversion problem.
- Worse than 0.6B P02 in: allergies (recall 0.208 vs 0.375), review of systems, follow-up, valid-JSON rate, unsupported claims (104 vs 85), duplicates (11 vs 1). Better in vitals, assessment, investigations, family history, speaker attribution, dose accuracy (0 errors).
- Evidence grounding ~0.005 and canonical-schema compliance 0/50 for every system: P00 does not ask for them.
- Parsed-only metrics are not headline figures.

## Evaluator note
The frozen evaluator raised ValueError on a non-numeric duration value ("10 days"). `scripts/evaluate_run.py` wraps `same_duration` at runtime (no frozen file edited) to score such values as mismatches; non-crashing cases are scored identically.

## Schedule consequence
Wall time was 15.9 h (57,118 s), about 2x the earlier estimate. Each further 50-record run is expected to cost roughly 12–16 h.
