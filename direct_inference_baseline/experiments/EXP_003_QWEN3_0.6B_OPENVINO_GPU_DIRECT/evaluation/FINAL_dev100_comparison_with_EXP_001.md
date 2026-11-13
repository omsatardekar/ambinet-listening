# EXP_003 (100 development encounters) vs EXP_001 (5 encounters)

**This is not a like-for-like comparison.** EXP_001 ran only the same five development encounters (00021, 00032, 00034, 00035, 00037) as the EXP_003 smoke test; it was never run on the other 95. The 100-record EXP_003 numbers therefore have no EXP_001 counterpart. Two valid comparisons exist: (A) the same 5 encounters, EXP_001 vs EXP_003 (identical entity metrics), and (B) EXP_003 on 5 vs 100 encounters (sample effect).

## What differs between EXP_001 and EXP_003
| Factor | EXP_001 | EXP_003 | Differs? |
|---|---|---|---|
| Model | Qwen3-0.6B rev c1899de2... | same | No |
| Numerical format | BF16 weights loaded as FP32 | FP16-converted OpenVINO IR | **Yes** |
| Runtime | HF Transformers | openvino_genai.LLMPipeline | **Yes** |
| Hardware | i7-8665U CPU | Intel UHD 620 iGPU | **Yes** |
| Prompt / decoding / schema / parser / evaluator | fixed (sha256 78c5ab95...), greedy, 6144 | identical (verified) | No |
| Dataset / split | frozen v2 batch 001, development | same | No |
| Encounters | 5 | 5 (smoke), then 100 | Sample size |

Latency and any small output differences are the combined effect of format, runtime and hardware; none can be attributed to the GPU alone.

## A. Same five encounters
| Metric | EXP_001 | EXP_003 (5) |
|---|---|---|
| Micro P/R/F1 | 0.111/0.018/0.030 | 0.111/0.018/0.030 |
| TP/FP/FN | 3/24/168 | 3/24/168 |
| Macro F1 | 0.019 | 0.019 |
| Mean latency (s) | 633.940 | 172.581 |
| Mean tok/s | 1.495 | 5.664 |

Two of five outputs were byte-identical and three diverged slightly (details in `comparison_with_EXP_001.md`). Latency fell about 3.7x.

## B. EXP_003, 5 encounters vs 100 encounters
| Metric | EXP_003 (5) | EXP_003 (100) |
|---|---|---|
| Valid JSON | 5/5 | 94/100 |
| Micro P/R/F1 | 0.111/0.018/0.030 | 0.257/0.027/0.049 |
| TP/FP/FN | 3/24/168 | 98/284/3523 |
| Macro F1 | 0.019 | 0.054 |
| Medications F1 | 0.267 | 0.299 |
| Allergies F1 | 0.000 | 0.282 |
| Symptoms F1 | 0.074 | 0.095 |
| Speaker attribution | 0.333 | 0.511 |
| Unsupported-evidence rate | 0.926 | 0.885 |
| Mean latency (s) | 172.581 | 153.996 |
| Mean tok/s | 5.664 | 5.678 |

The 5-record sample understated the model: with 100 encounters micro F1 rises 0.030 -> 0.049 and macro F1 0.019 -> 0.054, allergies and surgical history become non-zero, and 6 of 100 outputs are malformed JSON (none among the 5). Speed (about 154 s per encounter, 5.7 tok/s) is stable across the sample.

## Conclusion
On the shared five encounters the OpenVINO FP16 GPU backend reproduces EXP_001's extraction quality and is about 3.7x faster. The 100-record development baseline for this model and prompt is micro F1 0.049 (valid-only 0.052), so the poor quality is a property of the model plus the fixed prompt, not of the backend. Because EXP_001 never covered the other 95 encounters, a 100-record CPU baseline does not exist; obtaining one would take roughly 100 x 634 s = 17.6 h of CPU generation and has not been run.

