# 04 — Fine-tuning and future roadmap

**Status: fine-tuning has NOT been started. Nothing in this file is a result.** Everything under "Recommended" is a proposal to be checked and approved; hyperparameters are starting points, not facts.

Labels: **[Verified in repo]**, **[Recommendation]**, **[General knowledge]**, **[Needs verification]**.

---

## 1. Why fine-tune — based on our own findings

From `01_…` (1.7B, same 30 records, strict matching):

| Problem | Evidence | Can a prompt fix it? |
|---|---|---|
| Low recall | P02 recall 0.214; 859 of 1,093 gold facts missed | We tried three prompt stages; recall rose 0.117 → 0.156 → 0.214 but flattens |
| Negative findings | gold 168; P02 predicted 51, 1 correct | P02 has explicit negative rules and still 1 TP |
| Clinical actions / follow-up | actions gold 165, P02 0 TP; follow-up 2 of 26 | Strict key contains free text → part of the problem is the matcher/format |
| Physical exam, ROS, clinical conditions | 0 TP in P00, P01 and P02 | Convention mismatch (what counts as a "condition" vs history) is something examples teach better than rules |
| Evidence grounding | P02 ids exist 98.6%, correctness unmeasured; 123 facts without ids | Partly |
| Token-cap failures | P02 2/30, P01 5/30, P00 7/30 | Fine-tuning on compact targets can shorten outputs; not guaranteed |
| Schema compliance | 0 fully compliant records for P00/P01 (P02 not measured) | Fine-tuning on exact-format targets usually helps format a lot |

**What fine-tuning could help with:** learning the dataset's conventions (what goes in `clinical_conditions`, how to phrase `clinical_actions`, vital names), writing exact JSON shape without a 4,600-token instruction block (shorter prompts, faster prefill — prefill of ~6,700 tokens costs ~3 minutes per record today), and finding denials/instructions it currently skips.
**What it cannot guarantee:** it will not make labels better than the generator-derived gold; it can overfit to synthetic phrasing; it does not guarantee higher recall on real clinical speech; it cannot fix a matcher that penalises correct paraphrases; and a 1.7B model has limited capacity. The owner's project notes mention aspirational targets (prompting ~0.40–0.45 F1, LoRA ~0.60–0.65); **these are goals, not predictions or results**. [Needs verification: those targets come from project notes, not a repo report.]

---

## 2. Concepts from scratch

| Term | Plain explanation | Analogy |
|---|---|---|
| **Fine-tuning** | Continue training an already-trained model on our own input→output examples so its weights shift towards our task. | A trained nurse doing a month of on-the-job training in one clinic. |
| **Full fine-tuning** | Update *all* weights (1.7 B). Needs memory for weights + gradients + optimizer state (several × model size). | Rewriting the whole textbook. |
| **Parameter-efficient fine-tuning (PEFT)** | Update only a tiny added set of parameters; keep the base model. | Adding sticky-note annotations. |
| **LoRA** (Low-Rank Adaptation) | For selected weight matrices W, learn a small correction ΔW = B·A where A and B are thin matrices (rank r, e.g. 8–64). Only A and B are trained. | Instead of reprinting a 1000-page book, attach a 5-page errata sheet. |
| **Low-rank matrices** | A big matrix approximated by the product of two skinny ones (d×r and r×d with r ≪ d); far fewer numbers. | A large photo summarised by a few strong patterns. |
| **Adapter** | The small trained add-on (the LoRA A/B matrices); saved separately (tens of MB) and loaded on top of the base model, or merged into it. | A removable lens attached to a camera. |
| **Freezing the base model** | The original 1.7 B weights are not changed. | The textbook stays untouched. |
| **Which parameters are trained** | Only LoRA matrices (typically on attention projections, often MLP too); base frozen. | |
| **Why cheaper** | No gradients/optimizer state for the 1.7 B base weights, so memory and time drop sharply. | |
| **Training / validation / test sets** | Train = learn from; validation = tune and stop; test = untouched final exam. | Practice, mock exam, real exam. |
| **Data leakage** | Test information leaking into training (same encounter, near-duplicate, or tuning decisions made on test). It inflates scores. | Seeing exam questions beforehand. |
| **Overfitting** | The model memorises training examples and does worse on new ones. | Memorising answers, not understanding. |
| **Epoch** | One full pass through the training set. | |
| **Batch size** | How many examples are processed before one weight update. | |
| **Learning rate** | Size of each update step; too high = unstable, too low = slow. | |
| **Gradient accumulation** | Add up gradients over several small batches before updating — simulates a big batch with little memory. | |
| **Loss** | A number measuring how wrong the predicted tokens are vs the target; training lowers it. Lower loss ≠ higher F1 automatically. | |
| **Checkpointing** | Saving the model/adapter at intervals so training can resume or the best point can be chosen. | Saving a game. |
| **Early stopping** | Stop when validation stops improving. | |
| **Quantization** | Storing weights with fewer bits (8/4) to save memory. | |
| **QLoRA** | LoRA on top of a base model loaded in 4-bit quantised form. Saves memory further; the standard implementation depends on `bitsandbytes` (typically CUDA GPUs). [General knowledge / Needs verification for our environment] | |
| **LoRA vs QLoRA** | Same adapters; difference is whether the frozen base is held in 16-bit (LoRA) or 4-bit (QLoRA). QLoRA = less memory, slightly more complexity, sometimes small quality loss. | |

---

## 3. Data situation (what we really have) [Verified in repo]

| Set | Size | Status |
|---|---|---|
| Batch 001 corrected | 500 synthetic encounters | frozen |
| — locked test | 400 | **never used**; sealed; must stay the final test (or become a "locked test" only once) |
| — development | 100 → 50 `prompt_dev` (used to design prompts, all 0.6B and 1.7B experiments) + 50 `validation` (consumed by the 0.6B P05 validation run) | **cannot be a clean test for a fine-tuned model** because prompts were tuned on prompt_dev and validation was already consumed |
| Batch 002 | 500 synthetic encounters (ids 20001–20500), automated validation only | **not allocated** to train/dev/test; no inference |
| Planned corpus | 8 batches × 500 = 4,000 (owner's plan, per project notes) | Only 2 batches exist **[Needs verification]** |

Important consequences **[Recommendation]**: do not train on the 400 locked records; do not evaluate on the 50 prompt_dev records without saying they were used for prompt design; Batch 002 can't serve as both training and evaluation without a written allocation. 500 examples is small for LoRA but not unusual for a narrow, format-heavy task; more batches would reduce risk.

---

## 4. Proposed workflow (steps 1–15)

1. **Audit and freeze data and labels.** Hash every file; record the allocation of each id to train/validation/test in a manifest (never changed afterwards). *(Existing practice: `FROZEN_50_PROMPT_DEV_IDS.json`, `P02_30_IDS.json`.)*
2. **Review annotation consistency.** The gold is generator-derived; check conventions (e.g. is "no known allergies" in `negative_findings`? gold says yes). Compare 20–30 records by hand with a clinician if possible. Known items from our analysis: strict keys for actions/follow-up are free text; conditions vs history split is unclear.
3. **Split without leakage.** Split by *encounter*, stratified by specialty × complexity (as the existing `dataset_split.py` does, seeds recorded). Keep all segments of one encounter in one split. Suggested: new Batch 002 → train/validation; Batch 001 locked 400 → final test. **[Recommendation]**
4. **Reproducible baseline.** On the *same final test ids*, run the existing frozen prompts (P00, P01, P02) before any training, so the comparison is fair. This is one 9–16 h run per prompt on our laptop — **plan the time** (or use a faster machine for baselines; any change of machine must be recorded and the settings reproduced).
5. **Select model revision.** Qwen3-1.7B at `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e` (already pinned and verified).
6. **Training framework and LoRA config.** Common choices: Hugging Face Transformers + PEFT (+ TRL). Starting point **[Recommendation, not verified for our data]**: rank 16, alpha 32, dropout 0.05, target attention (q,k,v,o) and MLP projections, learning rate ~2e-4 (cosine), 2–3 epochs, effective batch size 16 via gradient accumulation, sequence length covering input + target (our inputs are ~4–7.6k tokens with the long P02 prompt; a **short** instruction prompt would cut that to ~2.1k + transcript).
7. **QLoRA or not.** On a cloud GPU with ≥ 24 GB, plain LoRA in bf16 should be feasible for a 1.7B model; QLoRA is only needed for smaller GPUs. **[Needs verification by a dry run on the chosen machine.]**
8. **Prepare structured target outputs.** Convert gold labels into exactly the output format the evaluator expects (the repo already has `p02/code/convert_gold.py`, a gold→evidence-segment map, and the P02 output shape with `evidence_ids` as segment ids). Train with the **short** instruction (schema + minimal rules), not the 4.6k-token guide, so prefill is cheap. Keep `clinical_evidence` empty (backend backfills).
9. **Train with LoRA.** Log loss, learning rate, seed, library versions, data hash.
10. **Validate during training.** Compute validation loss each N steps **and** a fast task metric (parse rate + micro F1 on a small validation subset) — loss alone does not track F1.
11. **Save checkpoints and configuration.** Adapter weights, tokenizer, training args, data manifest hash, git commit, hardware; keep the best-by-validation-F1 checkpoint.
12. **Evaluate on the same held-out test set** with the frozen evaluator, same settings (greedy, thinking off, same cap).
13. **Compare** against direct inference (P00), P01, P02 and, for reference, 0.6B — same ids, same tiers.
14. **Category-wise error analysis:** negatives, actions, follow-up, exam, ROS, conditions; FP examples; speaker; evidence.
15. **Decide** whether it is genuinely better: all of — higher micro F1 on the untouched test; no category collapse; JSON validity and truncation no worse; improvement larger than run-to-run noise (repeat with ≥ 2–3 seeds); and a human spot-check. State limits (synthetic data).

---

## 5. Hardware and deployment

**Local training is probably not realistic [Recommendation, not measured].** The laptop has 15.8 GB RAM, a 4-core CPU and an Intel UHD 620 with no CUDA. Inference of the 1.7B already needs ~6–7 GB, runs at 2.7 tokens/s, and our long runs take 9–16 h; training needs gradients/activations on top. PyTorch training on an Intel iGPU is not a standard path; CPU training of a 1.7B model would be extremely slow. Plan a **cloud/remote GPU** (single 24 GB-class GPU) for training. The cost/time estimate is **Not available** — do a short dry run first.

**Using OpenVINO after fine-tuning [Needs verification before promising].** The general route is: train the LoRA adapter → merge it into the base weights (a standard PEFT operation) → export the merged HF model with `optimum-cli export openvino` (same command we already used, `--weight-format fp16`) → run with OpenVINO GenAI. The existing export pipeline (`[1.7B]/scripts/convert_model.py`, `CONVERSION_RECORD_Qwen3-1.7B.json`) shows this works for the base model; I have **not** verified a merged-LoRA model through it, nor whether OpenVINO GenAI can load adapters unmerged. A short test (convert the merged model, compare outputs to the PyTorch merged model on 3 records) would confirm it. Merged weights remain a normal 1.7B model, so inference cost on our laptop would be the same as today (~3.2 GiB weights, ~2.7 tok/s), but a much shorter prompt would reduce prefill time.

---

## 6. Success metrics and the "accuracy" question

### Metrics to report for every model
- Overall **micro** precision, recall, F1 (tier 1: failures = zero) and the parsed-only view.
- **Macro** F1 (mean of the 18 category F1s); category-wise P/R/F1 with TP/FP/FN.
- JSON validity; schema compliance; evidence-ID validity (exists) **and** evidence correctness if a check is built.
- Unsupported-fact rate (evaluator's lexical `unsupported_claims`, labelled as such).
- Record completion rate; token-cap failure rate.
- Latency per record, peak process memory, lowest available RAM.
The goal is **better extraction quality**, not longer outputs: more predicted facts raise recall only if precision holds; always read P and R together.

### What the current evaluator can and cannot say
| Measure | Supported? | Comment |
|---|---|---|
| Fact-level P/R/F1 (strict) | yes | headline |
| Category-wise P/R/F1 | yes, 18 categories | per category |
| Record-level success (parsed/attempted) | yes | completion, not correctness |
| JSON validity, schema validity | yes | |
| Attribute accuracy on matched facts (dose, temporality, status…) | yes, in `attributes` | conditional on a match |
| Field-level exact match over all fields | not computed | would need a field-by-field comparison of aligned facts |
| Record-level accuracy ("all facts correct") | not computed | would be ≈ 0 for every run; uninformative |
| Semantic correctness | no | needs fuzzy/semantic matching or human review; fuzzy mode is a non-official diagnostic |

**Do not average category F1 values and call it overall accuracy** — that is macro-F1, a different thing. Do not call F1 "accuracy".

### Defensible future "overall" figures (without touching past results) **[Recommendation]**
1. **Fact-level micro F1 (strict)** — keep as the primary headline.
2. **Fact-level micro F1 (semantic/adjudicated)** — a second headline from a *fixed*, pre-registered matcher (e.g. a synonym table frozen before testing, or blinded human adjudication of a sample of FP/FN), reported next to the strict one.
3. **Record-level "fully captured critical facts" rate** — define a small set of critical categories (medications with dose, allergies, vitals, assessments) and report the share of records where *all* gold facts in those categories are recovered; clearly named, not "accuracy".
4. **Field accuracy on matched facts** (existing attributes) — as a conditional accuracy.
Historical numbers must not be recomputed under the new matcher without labelling.

---

## 7. What I must remember tomorrow
- **Fine-tuning has not started.** LoRA = train small add-on matrices; base frozen.
- Data: 400 locked test (never used), 50 prompt_dev and 50 validation already consumed, Batch 002 (500) unallocated.
- Local laptop cannot comfortably train; plan cloud GPU; OpenVINO after fine-tuning (merge → export) is expected to work but **not yet verified**.
- Success = better micro/macro F1 on untouched test, no collapse in categories, same or better validity/truncation, repeated runs.
- We do not have an "accuracy" number; do not invent one.
