# EXP_003 final smoke-test report - Qwen3-0.6B, OpenVINO FP16, Intel UHD 620 GPU, five development encounters

Status: COMPLETED. Five development encounters only (00021, 00032, 00034, 00035, 00037). The other 95 development encounters and the 400 locked-test
encounters were NOT run. Results are indicative only (5 encounters, 27 predicted entities, 171 gold entities).

## Verification before execution (`preflight_report.json`, all passed)
OpenVINO model files = EXP_002 conversion record (11 files); source snapshot c1899de2... files = recorded hashes; GPU = Intel UHD Graphics 620; prompt sha256
78c5ab95...f604 = EXP_001 archive = EXP_001 manifest; inference/evaluation code byte-identical to the EXP_001 code snapshot; live split files identical to the EXP_001
archive; the five ids are in the development split; input token counts equal EXP_001 for all five; frozen inputs verified (501 files); no label/blueprint file opened
while building prompts. During inference a file-access audit recorded 510 opened files and **0 label or blueprint files** (`logs/inference_file_access_audit.json`).
After the run the full frozen dataset verified again (1,001 files).

## Runtime settings
openvino_genai.LLMPipeline, device GPU (no CPU fallback used), FP16-converted model, compiled-model cache `ov_cache/` (inside EXP_003), greedy (do_sample=False),
enable_thinking=False via the Qwen3 chat template, max_new_tokens 6144, model-native EOS/stop ids (151645, 151643), a fresh pipeline per encounter.
Full detail: `inference_config.json`, `run_manifest.json`, `environment_details.json`.

## Results (existing evaluator, strict matching)
| | Value |
|---|---|
| Valid JSON | 5/5 (no truncation, no malformed, no empty; all finish_reason=stop) |
| Complete schema compliance | 0/5 (missing_field 29, wrong_type 8, enum_violation 10) |
| Required-field completeness | 94.4% |
| Unexpected-field rate | 0.0% |
| Micro P / R / F1 | 0.111 / 0.018 / 0.030 (TP 3, FP 24, FN 168) |
| Macro P / R / F1 | 0.107 / 0.013 / 0.019 (18 categories averaged) |
| Symptoms | P 0.083 R 0.067 F1 0.074 (TP 1, FP 11, FN 14) |
| Medications | P 0.667 R 0.167 F1 0.267 (TP 2, FP 1, FN 10) |
| Allergies | F1 0.0 (TP 0, FP 1, FN 2) |
| Negative findings, medical history (4 sub-categories), vital signs, physical examination, clinical conditions, clinical assessment, procedures/investigations, clinical actions, follow-up | all TP 0; recall 0.0 (precision undefined where nothing was predicted) |
| Vital-sign accuracy | 0 of 16 |
| Speaker attribution | 1 of 3 matched entities (33.3%) |
| Evidence grounding (27 predicted entities) | strict 0, lenient 0, partially supported 2, unsupported 25 (92.6%) |
| Unsupported claims | 1 of 27 (3.7%); 23 further false positives are transcript-supported extras |
| Negation | 0% of gold negative findings reproduced; 0 polarity flips |

Per-category and per-attribute tables, specialty/complexity breakdowns: `evaluation/exp_003_dev_smoke_5/evaluation_report.md`. Per-encounter detail: `per_encounter_results/`.
The model again produced short, early-stopping JSON that omits most schema sections; it is the same behaviour as EXP_001.

## Performance (`logs/performance_per_encounter.json`)
| | Per encounter (5) |
|---|---|
| Input tokens | 3,368-4,108 (mean 3,785) |
| Output tokens | 629-1,948 (mean 957) |
| Model load (warm cache) | 3.1-4.3 s |
| First-token latency (prefill + first token) | 21.7-31.4 s (prefill 131-156 tok/s) |
| Decode speed | 5.8-7.9 tok/s |
| Generation time | 101-368 s (mean 172.6 s); overall 5.66 tok/s |
| Peak working set (process, cumulative) | about 2.8 GB |
Total generation time 0.24 h (EXP_001: 0.88 h). If output lengths resemble these five, the remaining 95 development encounters would take roughly 4.7 h and the 400 locked-test encounters roughly 20 h; output length varies, so treat that as an estimate.

## GPU errors and warnings
The same two Intel graphics-compiler kernel-header messages seen in EXP_002 ("Input V38 intersects with V37"; "Explicit input 2 must not follow an implicit input 0") were logged
(`logs/gpu_compiler/kernel.errors.txt`). No crashes, no failed inference, no OpenVINO runtime warnings in `logs/run_stdout_stderr.log`. Outputs were valid and two were
byte-identical to the FP32 CPU run, so there is no sign the messages affect results.

## Comparison with EXP_001 (`comparison_with_EXP_001.md`)
Entity-extraction, attribute, clinical, schema-compliance and breakdown metrics are identical to EXP_001. Differences: evidence-grounding (strict 2 -> 0, unsupported
21 -> 25), enum violations 9 -> 10, completeness 94.36% -> 94.42%. Two outputs are byte-identical, three diverge slightly. Latency fell 3.7x; that reflects runtime,
numerical format and hardware together and cannot be credited to the GPU alone.

## Notes and deviations
* `python-dotenv` is not installed in env_openvino; `scripts/common.py` stubs `dotenv.load_dotenv` (the root `.env` is not needed for local inference and was not read).
* The existing module code was imported unmodified; its output directories were redirected into EXP_003 at run time. A new pipeline is created per encounter (see `scripts/ov_client.py`).
* Raw outputs are stored exactly as produced under `raw_predictions/`.

## Recommendation
The backend is functionally equivalent to EXP_001 on this sample and about 3.7x faster. The extraction quality remains very low, which is unchanged by the backend. Running the
remaining 95 development encounters (about 4.7 h) would give a statistically useful baseline, but I have not started it and will wait for your approval.
