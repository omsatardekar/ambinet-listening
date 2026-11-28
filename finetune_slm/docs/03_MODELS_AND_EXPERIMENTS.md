# 03. The two models (Qwen3-0.6B and Qwen3-1.7B) and every experiment before fine-tuning

This document explains the two base models, the common setup of the experiments, each experiment (what was tried, what was frozen, what changed, what came out), and why the project moved from prompting to fine-tuning. The folders are `experiments/qwen3_0.6b/` and `experiments/qwen3_1.7b_track/`.

## 1. The two models

| | Qwen3-0.6B | Qwen3-1.7B |
|---|---|---|
| Family | Qwen3 (dense decoder-only transformer, Alibaba) | same family |
| Layers / hidden size / MLP size | 28 / 1,024 / 3,072 | 28 / 2,048 / 6,144 |
| Attention heads / key-value heads | 16 / 8 | 16 / 8 |
| Vocabulary, maximum positions | 151,936 tokens, 40,960 positions | the same |
| Weights file used by us | 1.5 GB (Hugging Face base model) | OpenVINO FP16 conversion (the 3.4 GB `.bin` is not in Git) |
| Peak memory seen in our runs | about 3.1 GB | needed an 8 GiB free-memory gate before loading |
| Speed on the laptop (Intel UHD 620 GPU) | a few minutes per encounter | about 17 to 19 minutes per record (a 30-record run took 8 to 9 hours) |
| Role in the project | **the final track** (chosen by the project mentor); the one we fine-tuned | the "bigger model by prompting only" comparison; **never fine-tuned** |

Both models run with **thinking off** (the Qwen3 chat template is used with `enable_thinking=False`), greedy decoding, and a fresh pipeline per encounter.

## 2. Common setup of the experiments (before fine-tuning)
* **Hardware.** An Intel Core i7-8665U laptop with an Intel UHD Graphics 620 integrated GPU (24 execution units), running **OpenVINO 2026.4.1 FP16**. This is not the T4 GPU used later for training.
* **Data.** `dataset_v2_batch_001_corrected` (Batch 1, 500 synthetic encounters): 100 development and 400 locked-test encounters (seed 20260301). The 100 development encounters were split into 50 `prompt_dev` (used to tune prompts) and 50 `validation` (selection only), stratified by specialty and complexity (seed 20260401). The locked 400 were never opened by these experiments.
* **The 30 shared encounters.** The later experiments (EXP_008 and the 1.7B P01 and P02 runs) use the same 30 encounters, so they can be compared directly with the same judge.
* **Frozen things.** Every prompt version is stored with its SHA-256; model revisions are recorded (0.6B revision `c1899de2…`, 1.7B revision `70d244cc…`); the schema, the dataset and the evaluator were not modified; every run records the exact settings and a file-access audit that shows labels were opened only by the evaluator, after inference.
* **Two scorers.** First a strict string matcher (micro F1), later an **LLM judge** (document 10). They give different numbers (the judge scores about twice as high because it credits paraphrases), so numbers from the two must never be compared with each other.

## 3. The 0.6B experiments, in order

| ID | What was tried | Result | Decision |
|---|---|---|---|
| **EXP_001** | CPU baseline: Hugging Face Transformers, float32, the original long direct-extraction prompt (sha `78c5ab95…`), 5 development encounters | micro F1 0.030, JSON valid 5/5, schema compliant 0/5; about 1.5 tokens per second, 634 s per encounter | only a smoke test; CPU is too slow |
| **EXP_002** | environment and conversion: an isolated Python 3.12 OpenVINO environment, device detection (CPU and Intel GPU), conversion of Qwen3-0.6B to OpenVINO FP16 | the 11 model files and the environment that **the application still uses for local inference** | kept (`EXP_002_QWEN3_0.6B_GPU_DIRECT`) |
| **EXP_003** | the same direct prompt on the Intel GPU through OpenVINO FP16, 100 development encounters | judge-F1 0.177 on all 100 (94 parsed, 6 failed); 0.193 on the shared 30; it writes about 5 facts per encounter against a median of 36 in the label | baseline "P00" for all later prompts |
| **EXP_004** | **prompt engineering** on the 50 `prompt_dev` encounters. P01 schema-focused, P02 comprehensive extraction, P03 evidence-grounded, P04 segment-id evidence (smoke test only), P05 P02 + retrieved evidence | P01 rejected (more schema violations); **P02 kept at development stage** (strict micro F1 0.121 against 0.047 for P00); P03 and P04 rejected as designed (the model could not cite evidence reliably); P05 added retrieved evidence to P02 outputs (judge-F1 0.331 on its own 50) | P02 and P05 are the best plain prompts (judge-F1 about 0.32 to 0.33) |
| **EXP_005** | **S0 deterministic repair** (no model): rules A to F that fix structure only (a bare object becomes a one-item list, role-name aliases, placeholder allergies, unsupported dates removed, flags) | it repairs structure and representation only; it does not correct clinical content, and a better schema result is not better clinical accuracy (`reports/S0_EVALUATION_REPORT.md`) | helper, not a model improvement |
| **EXP_006** | **S1 simplified extraction**: a compact stage-1 output adapted to the full schema by a deterministic adapter | strict micro F1 0.1192 against 0.1207 for P02; 13 of 50 outputs invalid JSON; speaker attribution collapsed | revise, no gain |
| **EXP_007** | **S1.1**: a refined simplified format, two arms (B1 = original line rendering `[SEG] person_N (ROLE)`; B2 = role-label rendering `role: text`) | B1: strict micro F1 0.161, 45 of 50 valid JSON, judge-F1 0.395 on the shared 30 (best 0.6B prompt run); B2: F1 0.143 with only 31 valid but speaker attribution 0.953 | B1 is the best plain 0.6B prompt result; prompt selection was a post-hoc amendment |
| **EXP_008 (H1)** | **hybrid prompt**: the full normal P02 JSON schema + the discipline of S1.1 (write only what is said, a doctor's question is not a fact, one item per fact) + **no worked examples with literal values**, + "an empty list is correct" | 30 of 30 parsed on the first attempt, 0 token-cap hits (maximum 2,577 tokens); judge-F1 **0.352** (precision 0.568, recall 0.255, hallucination 0.262, critical 0.120) | **the model deployed in the application and the baseline for all fine-tuning comparisons**. Frozen prompt sha `dc10ba06…` |

How H1 was built: all prompt work used 3 spare development ids that are not among the 30 evaluated ids. Five early drafts failed (truncated at 6,144 tokens with 20+ segment ids per item; invalid JSON; echoed the blank skeleton and extracted nothing; filled the head but left every list blank). The sixth family started from the proven EXP_004 P02 prompt, removed its literal examples, added faithfulness rules and switched to segment-id evidence. A sanity check showed the EXP_004 P02 prompt run through the EXP_008 runner reproduced the stored output exactly, so the collapses were caused by the prompts, not the setup.

## 4. The 1.7B experiments (prompting only)

| ID | What was tried | Result |
|---|---|---|
| **EXP_001 (P00)** | the direct prompt on Qwen3-1.7B, 50 development encounters | 15 outputs truncated at the 4,096-token cap; run time 15.9 hours; judge-F1 0.463 on the shared 30 (23 of 30 judged), 0.421 on its own 50 |
| **EXP_002 P01** | schema-guided prompt (stopped by the project owner after exactly 30 records) | strict F1 0.201 (precision 0.283, recall 0.156); judge-F1 0.523 (25 of 30 judged); P01's gain over P00 is mostly completion (more outputs finish) |
| **EXP_002 P02 (frozen)** | P01 schema and structure unchanged, no model-written evidence, a strengthened extraction guide (4,645 template tokens) | 28 of 30 parsed (00060 and 00206 truncated), no out-of-memory, 9.25 hours; strict F1 0.258 (precision 0.323, recall 0.214); judge-F1 **0.536** (precision 0.666, recall 0.448, hallucination 0.231, critical 0.101) |

Intermediate P02 attempts (a compact-schema "v2.2" and a "v3") were rejected or archived: the owner required that the P01 prompt, schema, field names and order stay unchanged and only the model-written evidence be removed (`finetune_slm/archive/obsolete_experiments_after_P01/`).

**Rules kept for the 1.7B track** (project owner): a free-memory gate of 8.0 GiB before the first model load (never lowered), no retries and stop on out-of-memory, only the 50 development ids ever read, and no fine-tuning of the 1.7B model.

## 5. All prompted models on the same 30 encounters (LLM judge, lenient)

| Model and prompt | Judged / attempted | Precision | Recall | Judge-F1 [95% CI] | Hallucination | Critical |
|---|---|---|---|---|---|---|
| 0.6B EXP_003 direct | 29 / 30 | 0.589 | 0.115 | 0.193 [0.152, 0.230] | 0.167 | 0.107 |
| 0.6B P01 | 30 / 30 | 0.557 | 0.197 | 0.291 [0.234, 0.341] | 0.249 | 0.114 |
| 0.6B P02 | 30 / 30 | 0.577 | 0.220 | 0.318 [0.263, 0.364] | 0.241 | 0.136 |
| 0.6B P03 | 28 / 30 | 0.537 | 0.135 | 0.216 [0.173, 0.254] | 0.194 | 0.152 |
| 0.6B S1 | 24 / 30 | 0.625 | 0.196 | 0.299 [0.237, 0.359] | 0.260 | 0.157 |
| 0.6B S1.1 B1 | 27 / 30 | 0.650 | 0.284 | 0.395 [0.343, 0.444] | 0.280 | 0.119 |
| 0.6B S1.1 B2 | 17 / 30 | 0.724 | 0.219 | 0.336 [0.239, 0.421] | 0.220 | 0.070 |
| **0.6B H1 (EXP_008)** | 30 / 30 | 0.568 | 0.255 | **0.352 [0.313, 0.390]** | 0.262 | 0.120 |
| 1.7B P00 direct | 23 / 30 | 0.749 | 0.335 | 0.463 [0.378, 0.537] | 0.161 | 0.074 |
| 1.7B P01 | 25 / 30 | 0.725 | 0.409 | 0.523 [0.455, 0.580] | 0.178 | 0.082 |
| 1.7B P02 (frozen) | 28 / 30 | 0.666 | 0.448 | 0.536 [0.484, 0.573] | 0.231 | 0.101 |
| **0.6B fine-tuned, step 400** (for comparison, same 30) | 30 / 30 | 0.956 | 0.923 | **0.939 [0.927, 0.951]** | 0.014 | 0.005 |

Notes: failed or unparsed encounters count as zero predictions; the 0.6B S1 and S1.1 runs have many failed records scored as zero. The 1.7B results come from Intel-GPU runs scored as recorded. The fine-tuned row is the same 30 encounters, the same judge and the same prompts (document 10), but a different model, prompt, runtime (T4 versus Intel GPU) and decoding length.

## 6. What the prompting experiments taught us (why we moved to fine-tuning)
1. **1.7B is clearly better than 0.6B by prompting** (the best 1.7B run, 0.536, is above the best 0.6B run, 0.395, and the intervals do not overlap), but it is slow and memory-hungry, and its outputs often hit the 4,096-token cap.
2. **0.6B by prompting is unreliable**: no 0.6B prompt exceeded judge-F1 0.40. The direct prompt extracts about 5 facts per encounter against a median of 36; hallucination is 16 to 28% in every run.
3. **Prompt engineering saturated.** Five further prompt designs for H1 collapsed in different ways, and the prompt gets longer (2,359 tokens for H1, 4,645 for the 1.7B P02), which costs time and memory at inference.
4. **Worked examples leak.** The frozen 1.7B P02 prompt contained 14 invented worked examples; their content appears in 28 of 28 of its outputs (106 occurrences, for example "rest the shoulder" in 16 encounters). The judge counts those copied facts as unsupported, so the 1.7B P02 precision and hallucination figures understate its true ability. H1 therefore has no worked examples, and the runner refuses to start if any of the example words appear.
5. **The 0.6B model cannot cite evidence in a prompt.** Evidence collapsed into one blob record, or caused truncation; the backend therefore rebuilds source links by text similarity. Fine-tuning teaches the model to write real segment ids.
6. **Structural problems that a prompt could not fix**: history sections left empty although the history was spoken (19 to 23 of 30 outputs), `clinical_assessment` and `follow_up` written as one object instead of a list (7 of 30), `person_1` assumed to be the patient although the doctor in 9 of 30 records, and about 30% of output tokens spent on whitespace.
7. **The 32 failure classes** found in six live runs (document 01) are behaviours (inventing an allergy, filing a denial as a finding) that fine-tuning can teach directly.

Conclusion at that time (2026-11-15): stop prompt tuning, fine-tune Qwen3-0.6B on synthetic data with a short prompt, and measure on the same frozen 30 encounters with the same judge.

## 7. Questions an external reviewer may ask
**Why Qwen3?** It is a current open-weight small-model family with 0.6B and 1.7B sizes, a chat template with an explicit thinking switch, and OpenVINO support for CPU hosting. We did not compare other model families; that is a limitation.

**Why 0.6B and not 1.7B?** The mentor chose the 0.6B model for the final track. In our measurements it is much cheaper to host (about 3.1 GB of memory against an 8 GiB gate, and minutes against about 17 to 19 minutes per record on the same laptop). Prompted 1.7B is better than prompted 0.6B, but the fine-tuned 0.6B (judge-F1 0.939 on the shared 30) is far above the prompted 1.7B (0.536). We did not fine-tune the 1.7B model, so we cannot say how much more it would gain.

**Why not quantise?** The deployed model is OpenVINO FP16 with no quantisation; we did not test INT8 or INT4 and do not claim anything about them.

**Can the earlier experiments be compared with the fine-tuned model?** Only through the LLM judge on the same 30 encounters (that is the table above). The strict-matcher numbers (about 0.12 to 0.26) must never be compared with judge numbers.

**Is the H1 baseline fair?** It is the best of our own prompt work with the frozen schema, run through the same judge; it is also what the application used. The baseline on the 20 hand-written scenarios was re-run on a T4 (PyTorch fp16) and not on the Intel GPU (document 10).

**Where are the details?** Each experiment folder has its own README, manifests and checksums; the judge description is `evaluation/judge_eval/METHODOLOGY.md` and `REPORT.md`.
