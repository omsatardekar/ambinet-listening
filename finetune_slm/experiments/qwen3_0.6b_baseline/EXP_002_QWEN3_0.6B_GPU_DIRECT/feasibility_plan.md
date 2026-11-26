# EXP_002 - OpenVINO iGPU feasibility plan (PLAN ONLY - nothing installed or run)

Status: awaiting approval. EXP_001 is untouched. No locked-test encounter is processed at any step.

## Hardware (read-only check on this PC)
Intel UHD Graphics 620 (Gen9.5, ~24 EUs, shares system RAM; driver 31.0.101.2135; Windows reports 1 GB dedicated "AdapterRAM", which is only a legacy display value),
i7-8665U (4C/8T), 15.8 GB RAM, Windows 10 22H2, Python 3.12 available at C:\Program Files\Python312.

## Phase 0 - already done (read-only)
Hardware/driver inventory above; documentation search (see report). No packages installed, no downloads.

## Phase 1 - isolated env + device detection (needs approval)
* New venv, separate from root .venv: `direct_inference_baseline/experiments/EXP_002_QWEN3_0.6B_GPU_DIRECT/env_openvino/` (Python 3.12). ~1-2 GB disk.
* Install only `openvino` (and `openvino-genai`). No torch, no root .venv changes.
* Run `ov.Core().available_devices` and print `FULL_DEVICE_NAME` / `GPU_DEVICE_TOTAL_MEM_SIZE` / `OPTIMIZATION_CAPABILITIES` for CPU and GPU.
* GO/NO-GO: GPU listed? If not -> stop, report (fallback: OpenVINO on the CPU only).

## Phase 2 - model acquisition (needs approval; explained before doing)
Preferred: download pre-converted `OpenVINO/Qwen3-0.6B-{fp16,int8,int4}-ov` from Hugging Face (about 1.2 / 0.7 / 0.5 GB). No conversion on this laptop.
Alternative: convert the exact EXP_001 snapshot (c1899de2...) with `optimum-cli export openvino` (needs torch+optimum in the isolated env, several GB). This is the only way to prove "same weights".
Either way the weights are numerically NOT identical to EXP_001 (fp32 -> fp16/int8/int4); EXP_002 must be labelled as a different precision, not a pure hardware change.

## Phase 3 - load test, no dataset (needs approval)
Load each precision on GPU; record load time, peak RAM, and generate ~64 tokens from a short generic prompt (not clinical data).

## Phase 4 - speed measurement on ONE development encounter (needs separate approval)
Same fixed prompt, one dev encounter (00021, the same as EXP_001), greedy. Measure prefill s, decode tok/s, completion tokens, peak memory; compare with EXP_001 (1.5 tok/s, ~540 s). Also measure OpenVINO on CPU, to separate "OpenVINO helps" from "GPU helps".

## Decision rule
Proceed to a 5-encounter dev smoke test only if GPU decode >= ~5 tok/s and the output is valid JSON. Locked test stays blocked until you approve separately.
