# 02 — The models, and preparing for external evaluators

Paths: `[1.7B]` = `direct_inference_1_7B/`, `[0.6B]` = `direct_inference_baseline/`.
Labels used below: **[Verified in repo]** = I read it in a file; **[Computed]** = I calculated it from the repo's `config.json`; **[General knowledge]** = standard background not stored in the repo (check before quoting as a fact about Qwen); **[Needs verification]**.

---

## 1. The two models, verified

| Item | Qwen3-0.6B | Qwen3-1.7B | Source |
|---|---|---|---|
| Hugging Face id | `Qwen/Qwen3-0.6B` | `Qwen/Qwen3-1.7B` | `[0.6B]/README.md`; `[1.7B]/scripts/common_1_7b.py` |
| Revision (commit) | `c1899de289a04d12100db370d81485cdf75e47ca` | `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e` | `…EXP_002…/conversion_record.json`; `[1.7B]/manifests/CONVERSION_RECORD_Qwen3-1.7B.json` |
| Architecture | `Qwen3ForCausalLM` (decoder-only transformer) | same | model `config.json` |
| Layers | 28 | 28 | config |
| Hidden size | 1,024 | 2,048 | config |
| MLP (intermediate) size | 3,072 | 6,144 | config |
| Attention heads / KV heads / head dim | 16 / 8 / 128 | 16 / 8 / 128 | config (grouped-query attention) |
| Vocabulary | 151,936 | 151,936 | config |
| Max positions (context) | 40,960 | 40,960 | config `max_position_embeddings` |
| Tied input/output embeddings | yes | yes | config |
| Parameters **[Computed from config]** | ≈ 0.596 B total (0.440 B excluding embeddings) | ≈ 1.721 B total (1.409 B excluding embeddings) | my arithmetic: per layer = attention (q,k,v,o + q/k norm) + 3 × hidden × intermediate MLP + norms; + vocab × hidden embeddings (tied) |
| Source weights | BF16 | BF16 | `source_weight_dtype` in the conversion records |
| Local format used | OpenVINO IR, FP16 weights, no INT8/INT4 | same | conversion records (`--weight-format fp16`) |
| File size of converted weights | 1,192,100,233 bytes (≈ 1.11 GiB) | 3,441,150,345 bytes (≈ 3.20 GiB) | `openvino_model.bin` byte counts in the conversion records |
| Model's own default sampling (generation_config) | temperature 0.6, top-k 20, top-p 0.95, do_sample true | same | HF `generation_config.json` — **we override with greedy** |

The "1.7B" and "0.6B" names are the model family's marketing sizes; my computed totals (1.72 B and 0.60 B) agree with them. Qwen's public statement of "non-embedding" parameters and training data is **[General knowledge]** and not stored in the repo.

### What the family is **[General knowledge]**
Qwen is the large-language-model family from Alibaba's Qwen team. Qwen3 is its third generation; it comes in dense models from 0.6B upwards, and the released checkpoints we used are the **post-trained (instruction/chat) versions** with a "thinking / non-thinking" switch. Evidence in the repo that ours behave as chat models: the code applies a chat template (`tokenizer.apply_chat_template(..., enable_thinking=False)` in `[1.7B]/scripts/ov_client_1_7b.py`) — a base model would not have one. Whether the model card calls the checkpoint "post-trained" should be checked before you quote it.

---

## 2. Basics, in plain English

**Parameters.** The numbers inside the network that were set during training — mostly weights in big matrices. They are the model's "memory of how language works". "0.6B" = about 600 million of them; "1.7B" = about 1.7 billion. They are *not* a count of facts, words or layers.
**A billion parameters in practice.** Each parameter is stored as a number. In FP16 each takes 2 bytes, so 1.72 B × 2 ≈ 3.4 GB (this matches the 3.44 GB file). That is storage, not the RAM needed to run it.
**Do more parameters help?** Usually they give more capacity (nuance, longer reasoning chains, rarer vocabulary). Not automatically: training data, post-training, prompt, and task fit all matter. In *our* data, same prompt: 1.7B scored F1 0.161 vs 0.044 on the same 30 records, **but** also produced truncated, unparseable outputs 7 of 30 times where 0.6B produced 0 — bigger was better at extraction and worse at finishing within our budget.
**Transformer.** The neural-network design: text becomes token vectors; stacked layers use *attention* (each token looks at all earlier tokens) and feed-forward blocks to predict the next token. Both of our models are decoder-only: they generate one token at a time, left to right.
**Token / tokenization.** Text is chopped into pieces (words, sub-words, punctuation) by a fixed tokenizer (`tokenizer.json`, byte-pair-encoding style; vocabulary 151,936 entries). The model reads and writes tokens, not letters. About 3 characters per token for our JSON output (my estimate in the P02 analysis: chars/3.04).
**Context length.** How many tokens the model can attend to at once (prompt + output). Config allows 40,960. Our prompts were 4k–7.6k tokens in, up to 4,096 out — nowhere near the limit. What limited us was **time and RAM**, not context.
**Inference.** Using a trained model to produce output. No weights change. Two phases: *prefill* (read the prompt, parallel, ~37 tokens/s for us) and *decode* (write tokens one by one, ~2.7 tokens/s for 1.7B).
**Greedy decoding.** At every step pick the single most probable next token (`do_sample=False`). Deterministic (same input → same output on same setup), good for reproducible experiments, but cannot "explore". Temperature/top-p/top-k only matter when sampling, so **they are not applied** in our runs.
**Model size vs output-token limit.** Size = how many parameters exist. `max_new_tokens` = our own cap on how many tokens the model may write (4,096 for 1.7B). A big model still gets cut off at the cap; a small model can finish early. Our "token-cap failures" are about the cap, not the model's capability.
**Base vs instruction-tuned.** A base model only continues text; an instruction-tuned (chat) model was further trained to follow instructions and chat format. We use chat-template prompts, so we use the chat variant (see above).
**Small vs large language model.** No official line. Informally: SLMs (hundreds of millions to a few billion parameters) can run on laptops/edge; LLMs (tens to hundreds of billions) usually need servers/GPUs. Ours are both "small".

### Parameter count ≠ memory needed
- *Model file size* (3.2 GiB for 1.7B in FP16) = parameters × bytes per parameter.
- *Runtime RAM* is more: the weights are loaded (and, on an iGPU that shares system RAM, mapped/copied for the GPU), plus the **KV cache** (stored keys/values for every token so far — about 112 KiB per token for 1.7B, ≈ 0.88 GB at 8,192 tokens; preflight estimate in `[1.7B]/manifests/HARDWARE_ENV_PREFLIGHT.json`), plus activations, the compiled GPU kernels, the Python process and Windows itself.
- Measured: process RSS peaked 5.9–7.1 GB for 1.7B; system-available RAM fell to ~3 GB (P02 minimum recorded 2,015 MB; P01 54 MB). So the model "file" of 3.2 GB needed far more than 3.2 GB.
Analogy: a book's page count (parameters) vs the size of the desk you need to read it with notes, bookmarks, and a second copy open (runtime memory).

---

## 3. Why Qwen3-0.6B first, why 1.7B later

### What the repository documents
- The documented design of the product has a **"SLM"** (small language model) stage downstream of transcription (`docs/architecture.md`: "SLM input preparation", `NNslm_input.json`). That supports "a small model was the intended target".
- Hosted option was checked and rejected for this experiment: the Foundry project "has no Qwen3-0.6B deployment (only gpt-5.5)", so the model was run **locally** (`[0.6B]/README.md`).
- Local CPU run was too slow (EXP_001: ~1.5 tokens/s, ~634 s per record), which led to the OpenVINO iGPU plan (`EXP_002…/feasibility_plan.md`): GPU decode needed ≥ ~5 tok/s to proceed. Result: 5.7 tok/s, about 3.7× faster (`EXP_003…/comparison_with_EXP_001_dev100.md`).
- Hardware: i7-8665U (4 cores/8 threads), 15.8 GB RAM, Intel UHD 620 (24 EUs; "6.79 GB total memory reported" shared with system) (`EXP_002…/phase1_report.md`, `HARDWARE_ENV_PREFLIGHT.json`).
- Why the 1.7B: the 0.6B work had plateaued — S1/S1.1 were not accepted (`EXP_006`, `EXP_007` reports), and the P05 root-cause note says a larger model "is a separate capacity-versus-memory question for this iGPU" and "revisit only if S0–S4 plateau" (`EXP_004…/audit_results/P05_root_cause_investigation/RECOMMENDED_IMPROVEMENTS.md`). The 1.7B was then downloaded, converted and checked on the iGPU (`[1.7B]/manifests/…`).

### What is **not** documented (do not present as fact)
- I found **no written statement** of the owner's original reason for choosing 0.6B (e.g., a stated "must be under X parameters" requirement) nor a decision memo for moving to 1.7B. **[Needs verification with the project owner/mentor.]** If asked, say: "We started with the smallest Qwen3 so the pipeline would run locally on a laptop; once the pipeline worked and prompts plateaued, we tested the next size up."

### Reasonable technical explanation (my interpretation, labelled)
Smallest model = fastest iteration on a laptop iGPU; its failures at 0.6B (near-zero recall) suggested a capacity limit; the 1.7B is the next Qwen3 size that still fits ~16 GB RAM in FP16 (3.2 GiB weights).

### Trade-offs actually measured
| | 0.6B (direct, 100 dev) | 1.7B (direct, 50 dev) |
|---|---|---|
| Micro F1 | 0.049 | 0.153 |
| Valid JSON | 94/100 | 35/50 |
| Token-cap hits | 0 (cap 6,144) | 15 (cap 4,096) |
| Latency / record | ~154 s | ~1,134 s |
| Decode speed | ~5.7 tok/s overall | ~2.8 tok/s |
| Peak process memory | ~3.1 GB (P02 run) | 7.1 GB working set |
Different caps (6,144 vs 4,096) and record sets: not a controlled size comparison.

### Why not "1.7B is simply better"
One prompt family, one hardware setup, 30–50 dev records, generator-labels, a strict matcher, one greedy run each; the 1.7B also fails to finish many records. A 0.6B model with a larger cap, or a fine-tuned 0.6B, was never run against it. "Higher on this test" ≠ "universally better".

---

## 4. Likely external questions and answers (say it in your own words)

**Beginner**
1. **What is Qwen?** A family of open language models from Alibaba's Qwen team; we used Qwen3 0.6B and 1.7B. *(General knowledge.)*
2. **What does 0.6B / 1.7B mean?** About 0.6 / 1.7 billion learned parameters. I checked from the config: ~0.60 B and ~1.72 B.
3. **What is a parameter?** One learned number in the network; together they encode how the model predicts text.
4. **What is a token?** A text piece the tokenizer produces; the model reads and writes tokens. Our prompts were 4–7.6k tokens.
5. **What is inference?** Running the trained model to get an answer; nothing is learned.
6. **What is greedy decoding and why did you use it?** Always pick the most likely next token. We used it so results are repeatable and comparable between prompts.
7. **What is a prompt?** The instructions plus the transcript we give the model. Our prompt includes the JSON template.
8. **What is the task?** Turn a doctor–patient transcript into a structured JSON of 18 evaluated clinical categories.
9. **Why not just use accuracy?** There is no natural "correct/incorrect" per record; facts are sets with extras and misses. Precision/recall/F1 describe both kinds of error.
10. **What is F1?** The balance of precision (how many of the facts we output are right) and recall (how many of the true facts we found). Formula in `supporting/metric_definitions.md`.

**Intermediate**
11. **Why a small model for clinical extraction?** Privacy (runs locally, no transcript leaves the machine), cost, and the product design has a small-model stage. The trade-off is lower quality, which our results show.
12. **Why Qwen and not another model?** *I did not find a documented model-comparison.* Honest answer: Qwen3 offers small sizes with a chat template, permissive availability on Hugging Face, and OpenVINO export support; we did not benchmark other families. **[Needs verification]**
13. **Why not GPT-4 / a large hosted model?** Not tested here. A hosted model was available in the project (`gpt-5.5` on Foundry per the README), but this study specifically asks how far a *small local* model can go. Privacy/cost/latency are the usual reasons; I would not claim we measured it.
14. **What is the difference between 0.6B and 1.7B on your data?** Same direct prompt: F1 0.044 vs 0.161 on 30 records; but the 1.7B hit the token cap on 7 of 30, the 0.6B on 0. Slower (~7×) and needs ~2× more memory.
15. **Does more parameters always mean better?** No; capacity helps, but data, tuning, and task matter; plus our larger model failed more often to finish.
16. **Model size vs output-token limit?** Size is parameters; the limit is our own cap on generated tokens. P02's two failures were cap hits.
17. **Model storage vs RAM?** File 3.2 GiB; running needed 6–7 GB process memory plus OS because of KV cache, activations, GPU buffers and the shared-memory iGPU.
18. **What is the difference between prompt engineering and fine-tuning?** Prompting changes the instructions at run time; weights stay fixed. Fine-tuning updates (some) weights on example input→output pairs. We have done only prompting.
19. **What is the difference between inference and fine-tuning?** Inference reads weights; fine-tuning changes them.
20. **How do you evaluate a clinical extraction model?** Compare extracted facts with gold facts by strict normalised keys, report TP/FP/FN, precision/recall/F1 micro and per category, plus validity and failure rates; evidence and speaker separately.
21. **Why strict matching?** It is reproducible and cannot be gamed, but it penalises paraphrases. We report a fuzzy view separately, labelled non-official.
22. **Why does P02 look better than P01?** Mostly vitals, social history and medicines, plus fewer failed records. Some of that comes from naming conventions we learned from dev gold.
23. **Is 0.258 F1 good?** No. It means we still miss about 79% of the gold facts. It is better than P01 (0.201) and P00 (0.161); it is not production quality.
24. **Why do negatives and actions score ~0?** The model rarely writes them, and for actions the strict key contains free text. Fix needs training, not more rules, in our view (hypothesis).
25. **What are your biggest limitations?** Synthetic, generator-labelled data; dev-only; one run; strict matcher; no clinician review; 30 records; length/time limits.

**Advanced**
26. **How did you make sure results are reproducible?** Fixed revision hash, frozen prompt/config SHA-256, frozen evaluator hashes, fixed id manifest, greedy decoding, fresh pipeline per record, RAM gate, manifest check that stops the run if a frozen file changes (exit code 4).
27. **What is OpenVINO and why?** Intel's toolkit for running models on Intel hardware; we used it to run on the laptop's integrated GPU (see `03_…`).
28. **Is your GPU result valid?** We verified GPU use in smoke tests with Windows GPU-engine counters, and the client refuses to run on any device but GPU (no CPU fallback) (`ov_client_1_7b.py`, `[1.7B]/manifests/SMOKE_TEST_GPU_VERIFICATION.json`).
29. **How do you avoid data leakage?** Locked-test ids never opened (audit logs state 0 locked-test files opened by the 1.7B runs); labels only read by the evaluator; the 50 dev ids were used for prompt tuning so results are labelled development-only. For fine-tuning we must not train on those or the locked 400.
30. **Why were some outputs invalid JSON?** Mostly truncation at the 4,096-token cap; also a few malformed JSON (missing commas). We do not repair them; failed records count as zero.
31. **Evidence handling?** The model outputs segment ids; the backend validates and builds evidence records. 98.6% of P02's ids exist; correctness of which segment was chosen is not measured.
32. **Did you fine-tune?** No. It is the next planned phase.
33. **Could 0.6B beat 1.7B after fine-tuning?** Unknown; not tested.
34. **Is the prompt overfit to your data?** Possibly for naming conventions (vitals/social). Examples in the prompt were checked absent from dev transcripts, but conventions came from dev gold. A fresh, unseen set is needed.
35. **What does "development-only" mean?** The labels are synthetic and the records were used while designing prompts; results cannot be generalised.

---

## What I must remember tomorrow
- 0.6B ≈ 0.60 B params, 1.7B ≈ 1.72 B (computed from config); both 28 layers; context limit 40,960 tokens.
- 1.7B FP16 file = 3.2 GiB; runtime process memory 6–7 GB.
- Same direct prompt, same 30 records: 0.6B F1 0.044 → 1.7B 0.161 (P00) → 0.201 (P01) → 0.258 (P02).
- Be honest that the reason for choosing 0.6B first and moving to 1.7B is not written in a decision document.
- F1 ≠ accuracy.
