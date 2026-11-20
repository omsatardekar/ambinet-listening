# Experiment inventory

Status vocabulary: **Completed** · **Partially completed** · **Prompt prepared, not tested** · **Planned** · **Results unavailable**.

## Qwen3-0.6B (`direct_inference_baseline/experiments/`)

| Experiment | Purpose | Records | Status |
|---|---|---|---|
| EXP_001_QWEN3_0.6B_CPU_BASELINE | CPU direct baseline | 5 dev | Completed (smoke only) |
| EXP_002_QWEN3_0.6B_GPU_DIRECT | OpenVINO env, device check, conversion, GPU feasibility, long-context report | none (no quality study) | Completed (infrastructure) |
| EXP_003_QWEN3_0.6B_OPENVINO_GPU_DIRECT | direct prompt on GPU | 5, then 100 dev | Completed |
| EXP_004 P00 reference | direct prompt on prompt_dev/validation subsets | derived from EXP_003 | Completed (reference) |
| EXP_004 P01 schema-focused | structure rules | 50 prompt_dev | Completed, **rejected** |
| EXP_004 P02 comprehensive | coverage rules | 50 prompt_dev | Completed, dev-stage keep |
| EXP_004 P03 evidence-grounded | model-written evidence | 35 of 50 | **Partial**, rejected as designed |
| EXP_004 P04 segment-id evidence | | 5 smoke | Smoke only, rejected |
| EXP_004 P05 | P02 + external retrieval evidence | 50 validation | Completed; human evidence review **pending** |
| EXP_004 P06 | combined | – | Planned in changelog, **never run** |
| EXP_005_S0_DETERMINISTIC_REPAIR | repair stored outputs (no model) | 50 | Completed; structural only |
| EXP_006_S1_SIMPLIFIED_EXTRACTION | compact schema | 50 | Completed |
| EXP_007_S1_1_SIMPLIFIED_EXTRACTION | Phase A synthetic gates; Phase B arms B1, B2 | 10 synthetic; 50 | Completed; not accepted; B3 not run |

## Qwen3-1.7B (`direct_inference_1_7B/`)

| Experiment | Purpose | Records | Status |
|---|---|---|---|
| Setup (download, verify, convert, 7 smoke-test attempts to verify GPU use) | pipeline | – | Completed |
| EXP_001_DIRECT_INFERENCE → P00 | direct prompt | 50 prompt_dev | Completed (15 truncated) |
| EXP_002_PROMPTING_INFERENCE → P01 | schema-guided | 30 of 50 | **Partial** (stopped by owner) |
| P02 v2.1 pilot | model-written evidence, comprehensive draft | 3 | Aborted by early-stop; archived; no result |
| P02 v2.2 pilot (compact schema) | | 6 | Aborted/rejected; archived; no result |
| First P02 prompt run | | 1 | Stopped by me at owner's request; archived |
| **P02 (strengthened)** | current prompt | 30 (same as P01) | **Completed** |
| LoRA fine-tuning | | – | **Planned, not started** |

## Naming clash
"P00–P05" exist twice: 0.6B (EXP_004) and 1.7B (this track). They are different prompts after P00.
Archived material: `archive/obsolete_experiments_after_P01/`.
