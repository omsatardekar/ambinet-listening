# EXP_002 - long-context (4,004-token synthetic prompt) comparison: OpenVINO CPU vs UHD 620 GPU

Model: converted FP16 Qwen3-0.6B (snapshot c1899de2...), greedy, enable_thinking=False, max_new_tokens=128, synthetic non-clinical prompt
(150 fake inventory records + a retrieval question; `results/longctx_prompt.json`). Each timed run uses a freshly built LLMPipeline
(a reused pipeline skips prefill for an identical prompt - see `results/superseded_*`). Caches: `ov_cache/gpu_long`, `ov_cache/cpu_long`.
"cold" = empty compiled-model cache; "warm" = cache populated. Two timed runs per set, run sequentially on a thermally limited laptop.

| set | load s | prefill+1st token s | prefill tok/s | decode tok/s | total s | peak MB |
|---|---|---|---|---|---|---|
| GPU cold r1 / r2 | 19.8 / 5.5 | 35.4 / 35.8 | 113 / 112 | 3.96 / 5.01 | 61.2 / 56.2 | 2786 |
| GPU warm r1 / r2 | 3.5 / 4.6 | 31.5 / 31.6 | 127 / 127 | 5.77 / 5.86 | 49.1 / 49.0 | 2390 |
| CPU cold r1 / r2 | 8.0 / 6.9 | 46.6 / 47.7 | 86 / 84 | 6.29 / 6.42 | 62.9 / 63.6 | 3263 |
| CPU warm r1 / r2 | 5.8 / 7.1 | 48.6 / 56.0 | 83 / 72 | 4.46 / 4.92 | 71.4 / 76.7 | 3262 |

Pooled (4 runs each): GPU TTFT 33.6 s (31.5-35.8), decode 5.15 tok/s (3.96-5.86), total 53.9 s; CPU TTFT 49.7 s (46.6-56.0), decode 5.52 tok/s (4.46-6.42), total 68.6 s.
Output: 103 tokens in every run (stopped on EOS). All 8 OpenVINO outputs are byte-identical to each other and to the float32 transformers reference
(137 s on this CPU). Output is coherent: the first five records are reproduced exactly (5/5); the "last record" item is wrong
(model says plastic funnel, truth leather belt) - identical in fp32, so a model limitation, not a device/precision effect.
GPU compiler messages: the same two kernel-header errors ("Input V38 intersects with V37"; "Explicit input 2 must not follow an implicit input 0") appear in every
GPU pipeline creation (cold and warm cache), are non-fatal, and have no observable effect (identical output, no crash). Logs: `logs/*kernel_errors*`.
No warnings/errors were logged on CPU.
