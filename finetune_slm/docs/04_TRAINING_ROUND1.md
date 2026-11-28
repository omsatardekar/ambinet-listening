# 04. Training round 1 (GPU run 1): the model we call "step 400"

Round 1 is the main fine-tuning run. It trained Qwen3-0.6B with LoRA on the 2,856-encounter synthetic training set and produced the checkpoint called **step 400**, which is one of the two models packaged for deployment. Everything in this document happened on the Azure GPU VM, except the scoring (done afterwards with the LLM judge).

## 1. Setup in one table

| Item | Value |
|---|---|
| Base model | Qwen3-0.6B (28 layers, hidden 1,024, 16 attention heads, 8 key-value heads, MLP 3,072), frozen |
| Method | supervised fine-tuning (SFT) with **LoRA** |
| Training data | `data/round1_synthetic/data/train_oversampled.jsonl`: 3,484 lines (2,856 encounters + 628 rare cases repeated once) |
| Validation | `validation.jsonl`: 250 = 190 seen + 60 unseen scenarios (a fixed sample of 60, 30 seen + 30 unseen, every 50 steps) |
| Hardware | Azure VM `vm-qwen3-finetune-t4` (resource group `GEN-AI-BATCH6-TRAINING-RG`), one **NVIDIA T4 (16 GB)**, size `NC4as_T4_v3`, Ubuntu 22.04; data on the OS disk (`/data/finetune`); run inside `tmux` |
| Code | `scripts/to_gpu_vm/train_lora.py` (plain PyTorch + transformers + peft; no trainer library, so no trainer-API drift) |
| Output | `runs/run1/` on the VM: 14 checkpoints, `train_log.txt`, `state.pt` (for resuming) |

## 2. What the model is trained to do (and not to do)
* Each training example is a chat. User turn = the 313-token short prompt + the transcript lines. Assistant turn = the compact JSON. The Qwen3 chat template is used with **thinking off** (an empty think block is added to the assistant turn, exactly as at inference).
* **Loss on the answer only.** Prompt and transcript tokens are masked, so the model is not rewarded for copying the input. At each answer token it predicts the next token and is penalised by how little probability it gave the correct one (cross-entropy, "teacher forcing"). The model therefore learns both **what to extract** and **how to write it** in our label style. Semantic matching ("morning stiffness" versus "stiffness in the morning") is not part of training; it is part of evaluation (the judge).
* The labels use one consistent style across all batches (validated and standardised before training), so the strictness of token-level training does not cause inconsistent wording.

## 3. Why LoRA, and why not the alternatives
LoRA freezes the base weights and next to each chosen weight matrix adds two small trainable matrices A and B of rank r; the layer output becomes `W x + (alpha / r) * B A x`. Only A and B are trained.
* **Why LoRA:** far less memory (fits one 16 GB T4), the base knowledge is not overwritten (less forgetting), and the result is a small adapter (about 160 MB) that is merged into the base model before deployment.
* **Why not full fine-tuning:** it needs gradients and optimizer states for every parameter, is slower and riskier on a T4, and can forget. **Why not QLoRA:** it quantises the base to 4 bits to save memory; the 0.6B model already fits in 16 GB, so quantisation would only add noise and slow the T4.
* **Why LoRA works well here:** with a model this small, a high rank gives quality close to full fine-tuning.

## 4. Hyper-parameters (and why each was chosen)

| Setting | Value | Reason (standard practice or hardware limit, not the result of an experiment) |
|---|---|---|
| LoRA rank r | **64** | capacity of the adapter; rank 128 was the fallback if validation stalled (not needed) |
| LoRA alpha | **128** (scale alpha / r = 2) | common choice of alpha = 2 x rank |
| LoRA dropout | 0.05 | light regularisation |
| LoRA targets | q, k, v, o, gate, up, down projections in all 28 layers (196 matrices) | attention **and** MLP, so the adapter can change both what the model attends to and how it writes |
| Trainable parameters | **40,370,176** (about 7% of the model) | per layer: 655,360 attention + 786,432 MLP |
| Optimizer | AdamW (betas 0.9 / 0.999, weight decay 0) | standard |
| Learning rate | **1e-4**, 19 warm-up steps (3%), then cosine decay to 1e-5 | typical for LoRA; warm-up avoids early instability |
| Gradient clipping | 1.0 | |
| Micro-batch size | **1 example** per forward and backward pass | memory limit of the T4 with 3,000-token sequences |
| Gradient accumulation | **16** | gradients of 16 examples are added before one update |
| **Effective batch size** | **16 examples** per optimizer step (about 51,000 tokens) | one "step" in the logs |
| Steps per epoch | 218 (3,484 / 16, rounded up) | |
| **Epochs** | **3** | 3 x 218 = **654 optimizer steps** |
| Examples processed | 654 x 16 = 10,464 (3.0 passes over 3,484), roughly 33 million tokens | |
| Maximum sequence length | 5,632 tokens | the longest example is 5,412; none skipped |
| Precision | base weights fp16, LoRA weights fp32, fp16 autocast with a gradient scaler | the T4 has no bf16 |
| Memory savers | gradient checkpointing, logits computed only at answer positions, SDPA attention | peak GPU memory 8.4 GiB of about 15 |
| Validation | every 50 steps on a fixed sample of 60 (30 seen + 30 unseen) | |
| Checkpoints | every 50 steps and at the end (14 adapters, about 160 MB each) | |
| Seed | 20261127 | |
| **Temperature / sampling** | **none in training**. Evaluation uses **greedy decoding** (no sampling, temperature effectively 0), thinking off, up to 4,096 new tokens | greedy makes the output reproducible and is what the deployed model does |

**No hyper-parameter search was done.** The values come from standard LoRA practice and the T4's limits; rank, learning rate and epochs were not tuned by comparing alternatives, so we cannot say they are optimal. This is stated as a limitation.

"654 steps" and "batch size": the total is 654 weight updates; each update uses a batch of 16 examples, fed one at a time and accumulated.

## 5. Time, speed and cost
* **1,102 minutes (18.4 hours)**, about **503 tokens per second**, no skipped example and no non-finite loss. A short pilot run was done first to check memory, speed, valid JSON and `expand()`; it measured about 455 tokens per second.
* Compute cost at about Rs 58 per hour: roughly **Rs 1,070** for this run. (The project approved a budget of Rs 4,000; the total used across all rounds is an estimate of about Rs 2,300 to 2,600, and the exact figure is only visible in the Azure Cost Management portal.)
* The T4 is compute-bound and power-capped (66 W against a 70 W limit, 71 degrees C, no thermal slowdown); software tweaks gave no gain, so we reduced tokens instead (removing timestamps).

## 6. What happened during training
Training loss: 1.02 at step 1, 0.24 at step 20, 0.15 at step 30, and about 0.003 to 0.01 near the end. The early drop is mostly the model learning the output format.

| Step | Seen validation loss | Unseen validation loss |
|---|---|---|
| 50 | 0.0883 | 0.0872 |
| 100 | 0.0491 | 0.0492 |
| 150 | 0.0380 | 0.0389 |
| 200 | 0.0310 | 0.0353 |
| 250 | 0.0269 | 0.0339 |
| 300 | 0.0252 | 0.0342 |
| 350 | 0.0222 | 0.0326 |
| **400** | 0.0208 | **0.0322 (lowest)** |
| 450 | 0.0214 | 0.0358 |
| 500 | 0.0206 | 0.0353 |
| 550 | 0.0210 | 0.0353 |
| 600 | 0.0208 | 0.0351 |
| 650 | 0.0211 | 0.0361 |
| 654 (final) | 0.0211 | 0.0360 |

How to read it. Both curves fall together until about step 250, so the model generalises to scenarios it did not see. After step 400 the unseen loss no longer improves while training loss keeps falling: **mild overfitting**. The last third of the run added nothing for new scenarios. The differences are small and are measured on only 30 unseen examples, so loss alone does not choose the checkpoint.

## 7. Choosing the checkpoint (validation only, never the test set)
The rule was written down before the comparison: compare step 400 (lowest unseen loss) and step 654 (last) by generating all 60 unseen-scenario validation encounters (greedy, thinking off) and scoring them with the same rough item-level F1; if they are close, prefer the one with lower unseen loss and less overfitting risk.

| Checkpoint | Valid JSON | Ended normally | Mean item F1 |
|---|---|---|---|
| Step 400 | 60 / 60 | 60 / 60 | 0.903 |
| Step 654 | 60 / 60 | 60 / 60 | 0.908 |

Step 654 was better on 20 encounters, step 400 on 14, equal on 26: not a meaningful difference with 60 examples. **Decision: step 400.** This item F1 is a rough exact-match score on validation data; it must not be compared with judge-F1.

## 8. Generation speed on the T4 (a finding, not a failure)
Generating is slow on this GPU: about **50 tokens per second in total, about 40 seconds per encounter** (an answer is about 1,900 tokens). Hugging Face generate (batch 6 to 12) and vLLM with LoRA gave the same 50 tokens per second, and more concurrent sequences made it slower, so the GPU is working at full speed. Our best explanation (not proven) is that with transcripts of about 3,000 tokens the cost is dominated by the attention cache. Consequence: one pass of the locked test set (973 encounters) takes about **11 hours** per model. Operational lessons: stopping a vLLM script with `pkill` left its engine holding 13.4 GB of GPU memory (the next job failed with out-of-memory until the process id was killed), and long jobs must be started inside `tmux`.

## 9. Results of round 1 (step 400)

### 9.1 Locked test set, 973 encounters, scored once with the LLM judge (gpt-5.4)
| Subset | Encounters | Precision | Recall | Judge-F1 (lenient) | Judge-F1 (strict) | Hallucination | Critical | Valid JSON as generated |
|---|---|---|---|---|---|---|---|---|
| Test A (Batch 1 benchmark) | 500 | 0.949 | 0.917 | 0.933 | 0.898 | 0.022 | 0.007 | 495 / 500 |
| Test B (curated) | 473 | 0.939 | 0.925 | 0.932 | 0.896 | 0.026 | 0.009 | 472 / 473 |
| **All** | **973** | **0.945** | **0.921** | **0.933** | **0.897** | **0.024** | **0.008** | **967 / 973 (99.4%)** |

* By source batch (Test B, judge-F1 lenient / recall): batch 2 0.943 (0.935); **batch 3 (hand-written natural dialogue) 0.866 (0.826), the lowest**; batch 4 0.943; batch 5 0.940; batch 6 0.939; batch 7 0.920; batch 8 0.948; batch 9 (non-obvious cases) 0.938.
* By section (recall / precision): vital signs 0.986 / 0.997; allergies 0.982 / 0.981; past history 0.984 / 0.985; conditions 0.982 / 1.0; follow-up 0.971 / 0.983; review of systems 0.973 / 0.981; assessment 0.964 / 0.989; negative findings 0.952 / 0.983; medications 0.945 / 0.928; social history 0.932 / 0.965; procedures and investigations 0.914 / 0.976; symptoms 0.841 / 0.872. **Weakest: clinical actions 0.836 / 0.858; physical examination 0.763 / 0.892; clinical uncertainties 0.774 / 0.752.**
* **Six invalid outputs of 973 (0.6%)**, all stopped normally. Three broke in the same place after a `clinical_uncertainties` item (the model started a new key and closed the object without the three remaining required fields); one wrote the next object's fields inside a list. All involve a conflict or doubt between speakers. The later JSON guard repairs all six (document 10).

### 9.2 Before and after on the same 30 encounters
| | Before: H1 prompt, base model | After: fine-tuned, step 400, short prompt |
|---|---|---|
| Judge-F1 (lenient) | 0.352 [0.313, 0.390] | **0.939 [0.927, 0.951]** |
| Judge-F1 (strict) | 0.239 [0.200, 0.277] | **0.903 [0.886, 0.920]** |
| Precision / recall | 0.568 / 0.255 | 0.956 / 0.923 |
| Hallucination | 0.262 | **0.014** |
| Critical-error rate | 0.120 | **0.005** |
| Valid JSON | 30 / 30 | 30 / 30 |
| Prompt length | 2,359 tokens | 313 tokens |

### 9.3 Natural hand-written speech (20 scenarios)
| | Precision | Recall vs design | Hallucination | Critical | Valid JSON |
|---|---|---|---|---|---|
| Before (base model, H1 prompt) | 0.515 | 0.272 | 0.325 | 0.159 | 19 / 20 |
| **After (step 400)** | **0.762** | **0.558** | **0.168** | **0.048** | **20 / 20** |

The fine-tuned model is far better than the baseline here, but clearly below its level on the template test set (precision 0.762 against 0.945, hallucination 0.168 against 0.024). The remaining errors are mostly spoken corrections (a stopped or swapped medicine recorded as current), denials recorded as findings, a relative's medicine attributed to the patient, spoken-number and unit slips, and sections invented from nothing said. This is what round 2 tried to fix.

### 9.4 Conversion to the deployment format
The merged step-400 model was converted to OpenVINO FP16 (no quantisation). On the 30 baseline encounters through the real scoring pipeline on CPU: 30 of 30 valid JSON, 22 of 30 outputs identical to the PyTorch text and the other 8 differing after some point in a long greedy generation (floating-point differences between runtimes, same number of facts), and **judge-F1 0.940 against 0.939** for the PyTorch outputs. The conversion does not change accuracy at this level of measurement. Speed on the laptop CPU (not the Azure VM): median 351 s per encounter.

## 10. Questions an external reviewer may ask
**Why 3 epochs?** The plan was "up to 3 epochs, stop early when the unseen validation loss stops improving". The unseen loss was lowest at about 1.8 epochs (step 400 of 654), so we selected that checkpoint and did not use the remainder.

**Why was step 400 chosen and not the last one?** Lowest unseen validation loss and equal generated quality at the last step (item F1 0.903 against 0.908, not meaningfully different), so we took the earlier, less overfit checkpoint. The test set played no part.

**Is it overfitting?** Mildly after step 400 (unseen loss rises slightly while training loss keeps falling); the chosen checkpoint is before that point. The gap between seen and unseen loss at step 400 is small (0.0208 against 0.0322).

**Why batch size 1 with accumulation 16?** Sequences are about 3,000 tokens; one example fills the T4's memory comfortably, so we accumulate 16 examples to get a stable update.

**Why compact output and a short prompt?** Fewer tokens means faster training and inference; the round trip to the full format is lossless (document 02).

**Is the 0.933 real accuracy?** No. It is judge-F1 on synthetic, template-style test data, under one judge and one rubric. The realistic number is the natural-speech result (0.762 precision, 0.558 recall against the design list). Do not quote 0.933 without that qualification.

**Why is validation loss so low (0.02 to 0.03)?** It is the loss per answer token with the correct answer given at every step; most tokens of a structured JSON are predictable. It is not an accuracy.

**What would you do differently?** Add natural-style data earlier (round 2), run a small hyper-parameter comparison, and keep a clinician-reviewed validation set.
