# 05. Training round 2 (GPU run 2): natural-speech data, the loops, the guard and windowed extraction

Round 2 continued from the round-1 step-400 adapter with newly written natural-style data. It lowered the loss on natural speech and raised recall, but it also produced **repetition loops** that the loss never showed. This document explains the data mix, the exact settings, the incident (GPU out-of-memory), the loops, the two safeguards we built (the JSON guard and windowed extraction), and the results. The checkpoint called **step 156** is the second model packaged for deployment.

## 1. Why a second round
After round 1 the model was far better than the baseline but clearly worse on natural hand-written speech (precision 0.762 against 0.945 on the template test set; hallucination 0.168 against 0.024). Round-1 dialogue is template-driven (document 02). Round 2 adds 529 newly written natural consultations (hesitation, interruptions, self-corrections, spoken numbers, relatives speaking for the patient, medicines described by colour, stopped medicines, disputed numbers, and so on) to teach exactly the behaviours that failed on natural speech.

## 2. Data used in training (details in document 02)

| Part | Examples | Note |
|---|---|---|
| Natural accepted, training families | 263 written; **226 trained on** | 37 were dropped because their total length exceeded the training limit of 6,144 tokens (T4 memory) |
| Replayed round-1 training examples | 600 (random, seed fixed) | so the model does not forget the old distribution |
| **Trained on** | **826** examples | 52 steps per epoch of 16 |
| Validation | 250 round-1 examples + 41 natural examples from four held-out families (283 after the length limit; 93 of them evaluated each time) | the held-out families (heavy periods with anaemia, gout flare, memory concerns with a spouse, asthma flare) are never trained on |

The natural examples are long: median prompt 2,320 tokens and median answer 2,449 tokens (round-1 examples: 1,497 and 1,620).

## 3. Settings (what changed from round 1)

| Setting | Round 1 | Round 2 | Why |
|---|---|---|---|
| Start from | base model | **the step-400 adapter** (`--init_adapter`); optimizer and schedule start fresh | keep what round 1 learned; the extra rounds only need to add natural-speech behaviour |
| Learning rate | 1e-4 | **5e-5** (warm-up 4 steps, cosine decay to a floor of 10% of the peak) | continuing training: a smaller step avoids undoing round 1 |
| Epochs | 3 | **3** | |
| Optimizer steps | 654 | **156** (159 planned before the length limit was lowered) | 826 examples / 16 = 52 steps per epoch x 3 |
| LoRA rank / alpha / dropout / targets | 64 / 128 / 0.05 / all projections | the same | the adapter is continued |
| Batch | 1 x accumulation 16 | the same | |
| Maximum sequence length | 5,632 (first export), 6,656 default | **6,144** after the incident below | memory |
| Validation | every 50 steps | **every 25 steps**, with a separate "natural" loss on the held-out families | |
| Checkpoints | every 50 steps | every 25 steps (25, 50, 75, 100, 125, 150, 156) | |
| Precision | fp16 autocast, fp32 LoRA | the same | |
| Decoding for evaluation | greedy, thinking off | greedy, thinking off, 4,096 new tokens | the same as round 1 |

Speed: about 520 tokens per second at the start, falling to about 430 as longer examples were reached; about 2.1 minutes per step. Estimated total **about 5.4 hours** (the first 25 steps took about 51 minutes, then about 4.6 hours for the rest; the final elapsed figure was not copied from the VM). Peak GPU memory 9.8 GiB at the start and **14.2 GiB** with the longest examples.

## 4. The out-of-memory incident
The first attempt failed at **step 25**, right after the first validation pass: "CUDA out of memory. Tried to allocate 2.27 GiB; 14.05 GiB in use, of which 3.39 GiB reserved by PyTorch but unallocated". The cause is memory **fragmentation** after the validation pass, with the longest natural examples in the batch. The checkpoint of step 25 and the training state had been saved. Fix: set `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`, lower `--max_len` from 6,656 to 6,144 (19 more natural examples skipped), and **resume** from the step-25 state (`--resume`). The resumed run printed `RESUMED at step 25` and the total became 156 steps. One consequence: the example order inside the first epoch no longer lines up exactly with the saved position, so a few examples in epoch 1 may repeat or be skipped; over 3 epochs this is negligible. During the run the laptop lost its connection once (a power failure on the laptop); the VM and the `tmux` session were unaffected.

## 5. Training and validation loss

| Step | Seen | Unseen | Held-out natural |
|---|---|---|---|
| 25 | 0.0254 | 0.0350 | 0.3661 |
| 50 | 0.0247 | 0.0351 | 0.3421 |
| 100 | 0.0236 | 0.0354 | 0.3275 |
| 125 | 0.0248 | 0.0379 | 0.3297 |
| 150 | 0.0242 | 0.0370 | 0.3270 |
| **156 (final)** | 0.0243 | 0.0371 | **0.3266** |

The natural loss is about ten times the round-1 loss because these are four families the model never trains on, written in a messier style. Reading it: the loss fell on natural speech (0.366 to 0.327) and the old-distribution losses stayed flat (seen 0.024; unseen 0.035 to 0.037), so by loss alone round 2 looked successful. Most of the gain came in the first 100 steps; after that the curves are flat. The training-step losses are noisy (0.06 to 0.29 from step to step) because a step averages only 16 examples and natural examples have a higher loss than replayed ones.

## 6. What the loss did not show: repetition loops
When the checkpoints were run on the 20 hand-written scenarios, many outputs **never finished**: the model repeated one list item (for example a troponin test, or "Sits in the crossword") until it hit the 4,096-token limit.

| Model | Valid JSON as generated (20 scenarios) |
|---|---|
| Round 1, step 400 | **20 / 20** |
| Round 2, step 100 | 6 / 20 |
| Round 2, step 156 | 11 / 20 |

Step 400 never looped on these scenarios (959 to 2,260 new tokens each; it always stopped by itself). Possible contributors (a **hypothesis, not proven**): the natural labels are longer (mean 9.9 thousand characters against 6.2 thousand), the 20 scenarios are longer than the natural training examples (3,700 to 4,450 input tokens against a median of about 2,300) and the longest training examples were skipped, and greedy decoding. We checked the natural labels for exact repeated list items and the cause is not simple duplication in the data. The lesson: **validation loss measures one token at a time with the correct answer given, so it cannot detect a model that fails to stop.** Always generate and judge.

## 7. Safeguard 1: the JSON guard (`scripts/shared/json_guard.py`)
A deterministic repair of malformed output, with no model involved. It acts only where the JSON parser reports an error, lists every repair, and marks the record for clinician review.

| Rule | Repairs |
|---|---|
| R1, R1b | a key started but never written: `"description":"text","}` becomes `"description":"text"}`; the same at the very end of the text (brackets closed) |
| R2 | a list not closed before the next key |
| R3 | a quote mix-up inside a string |
| R5 | one extra closing brace left by R1 |
| **R6 (added in round 2)** | a **repetition loop**: exact copies of an earlier flat item are removed, the unfinished tail is cut, the open brackets are closed; then the other rules are applied again |
| **R7 (added in round 2)** | a key written as the value of the previous key (`"duration":"reported_by":"patient"`): the empty field stays absent |

Checks: all 6 invalid outputs of the 973-encounter test now parse; **987 outputs that were already valid are returned unchanged (0 altered)**; all 20 round-2 outputs of both checkpoints now parse (step 100: 6 valid + 14 repaired; step 156: 11 valid + 9 repaired). If still unparseable: one regeneration with light sampling (temperature 0.3, top-p 0.9, because greedy decoding would repeat the same text), then `extraction_status: failed` with clinician review required. Limits: R6 removes identical items anywhere in the output, so a genuine repeat in another section would also be dropped, and content after the loop point is lost; repaired records are flagged. Content accuracy of repaired outputs is judged like any other.

## 8. Safeguard 2: windowed extraction (`scripts/shared/chunking.py`)
**Why.** The 20 scenarios have 3,700 to 4,450 input tokens, natural training examples are about 2,300, and real consultations can be longer still; the T4 could not train on more than 6,144 tokens in total, so the model has seen few examples as long as real ones.

**How.** A long transcript is cut into windows of at most **7,000 characters (about 1,800 tokens)** with **4 shared segments** between neighbours. Each window is sent to the model on its own with local segment ids `SEG0001…` (the format the model was trained on). The results are merged deterministically: list items identical apart from evidence ids are united (this also removes duplicates caused by the overlap), `related_entities` pointers like `medications[0]` are renumbered, evidence ids are mapped back to the original segment ids, the first chief complaint found is kept, speakers are united, and a quality check that is true in any window stays true. A transcript that fits in one window is processed unchanged. Merging an output with a copy of itself returns it unchanged (unit-tested). The 20 scenarios give 44 windows.

**Update (2026-11-26).** Windows lose context (document 07, section 5.2) and step 400 did not need them at the lengths tested, so its scoring file now uses windows of 14,000 characters with 10 shared segments; the 7,000 / 4 setting described here is the one step 156 keeps.

**Limits.** A fact stated across a window border may be split (the overlap reduces this); a window that does not see the start of the visit may not know the chief complaint; windowing costs step 400 about 0.03 precision on the 20 scenarios (below), because a window does not see the rest of the visit.

## 9. Results of round 2 on the 20 hand-written scenarios (LLM judge, same prompts as always)

| Model | Input | Valid | Precision | Recall vs design | Hallucination | Critical | Facts per scenario |
|---|---|---|---|---|---|---|---|
| Base model + H1 prompt | full | 19 / 20 | 0.515 | 0.272 | 0.325 | 0.159 | |
| Round 1, step 400 | full | 20 / 20 | **0.762** | 0.558 | **0.168** | **0.048** | 30 |
| Round 1, step 400 | windows | 20 / 20 | 0.730 | 0.562 | 0.206 | 0.050 | |
| Round 2, step 100 + guard | full | 20 / 20 (14 repaired) | 0.703 | 0.524 | 0.206 | 0.079 | |
| Round 2, step 156 + guard | full | 20 / 20 (9 repaired) | 0.717 | 0.580 | 0.205 | 0.071 | |
| **Round 2, step 156** | **windows** | 20 / 20 | 0.710 | **0.675** | 0.213 | 0.054 | **52** |

Without the guard, loop outputs count as empty (step 100: precision 0.722, recall 0.207; step 156: 0.729 and 0.345), which is why recall looks low there.

**Paired comparison, step 156 on windows against step 400 on full text, per scenario:** recall **+0.112** (better in 15 of 20 scenarios, worse in 3, about 4 standard errors, so not noise); precision **-0.038** (better in 7, worse in 13, about 2 standard errors). Of the precision gap, about 0.03 comes from windowing itself (step 400 loses 0.032 when windowed), so the model change alone costs only about 0.02.

**Deployment-format check.** The real OpenVINO FP16 model of step 156 was run on the laptop CPU through the full scoring pipeline (windows, guard, schema validator, evidence resolver) on four long scenarios: **4 of 4 valid** (status ok; one flagged for review by the schema validation), 2 or 3 windows each, 413 to 631 seconds per consultation (laptop CPU, not the Azure VM).

## 10. Reading the result
* **Round 2 gives a more complete record**: recall on natural speech rises from 0.56 to 0.68 and the model writes 52 facts per consultation instead of 30.
* **It costs precision**: 0.762 (step 400, full text) to 0.710 (step 156, windows) and hallucination 0.168 to 0.213; critical-error rates are similar (0.048 against 0.054).
* A combined precision/recall figure (harmonic mean) is 0.644 for step 400 on full text and 0.692 for step 156 on windows.
* It is a **trade-off, not a clean win**. The choice between the two models depends on whether the team values completeness or precision more (document 07).
* Caveats: 20 scenarios, one judge, recall measured against a short design list (a floor), natural-data labels are model-written, one training run.

## 11. Questions an external reviewer may ask
**Why continue from step 400 and not train from the base model?** Training from the base on a mix of round-1 and natural data would cost another 18 hours; continuing at a lower learning rate keeps what was learned and costs about 5 hours. We did not test the alternative.

**Why replay 600 round-1 examples?** To avoid forgetting the old distribution. The old-distribution validation loss stayed flat, which suggests it worked; we did not test other replay sizes.

**Why lr 5e-5?** Half of round 1, to make smaller changes on a continued adapter. It was not tuned.

**Why did the model loop?** Not proven (section 6). It appeared only after training on long natural outputs; step 400 never looped on the same inputs.

**Why is the guard allowed to change the output?** Only invalid JSON is touched, only at the position the parser flags, every change is logged and the record is marked for review; 987 valid outputs are never altered.

**Why windows of 7,000 characters?** About 1,800 tokens, close to the natural training prompts (a median of about 2,300 tokens including the instructions). We did not tune the size; larger windows were not tested.

**Does windowing lose information?** It can: facts across a border, and context from the rest of the visit (the 0.03 precision cost for step 400). The overlap and the merge reduce this; it is the price of bounded length, and any consultation length now works.

**Is the loss on natural speech good?** It fell (0.366 to 0.327), but it is measured on 41 examples from four families and it did not predict looping. The generated, judged output is the evidence we use.

**What is the temperature?** Training has none. Evaluation is greedy. Only the single regeneration inside the guard uses temperature 0.3, top-p 0.9.
