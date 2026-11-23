# EXP_002 Phase 1 - isolated env and OpenVINO device detection

* Env: `env_openvino/` (Python 3.12.3, venv separate from root .venv)
* Packages: openvino 2026.4.1, openvino-genai 2026.4.1.0, openvino-tokenizers 2026.4.1.0, openvino-telemetry 2025.2.0, numpy 2.5.4
* Devices: CPU, GPU
* CPU: Intel(R) Core(TM) i7-8665U @ 1.90GHz; capabilities FP32, INT8, BIN
* GPU: **Intel(R) UHD Graphics 620 (iGPU)**, arch v9.0.0 (Gen9), 24 EUs, device id 0x3ea0, integrated;
  GOPS fp16 883 / fp32 442 / int8 1766; capabilities FP32, FP16, BIN, USM_MEMORY; total mem reported 6.79 GB, max single allocation 3.40 GB; default inference precision fp16
* Initialisation test: a tiny synthetic matmul model (no Qwen, no clinical data) compiled and ran correctly on CPU and GPU.
* No model downloaded, no inference, no dataset accessed.
