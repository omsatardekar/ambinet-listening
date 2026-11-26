# 06. Training round 3 (GPU run 3): cleaner labels, and why it was not used

Round 3 was a short, cheap attempt to **recover precision** after round 2 raised recall but lowered precision. It continued from the round-2 step-156 adapter with a stricter subset of the natural data at a very low learning rate. It **did not meet the bar we set in advance**, so round 3 is not used for deployment. This document records exactly what was done so the negative result is reproducible and honest.

## 1. The question and the decision rule (written before the test)
**Question.** Round 2 (step 156) gave a more complete record (recall 0.675 on windows, 52 facts per consultation) but lower precision (0.710) and more hallucination (0.213) than round 1. The natural labels were model-written and accepted with a tolerance of up to 2 or 3 unsupported facts per encounter. Would training on only the cleanest labels bring precision back without losing recall?

**Pre-set bar.** On the 20 hand-written scenarios, run on windows and judged with the same judge: **precision at least 0.74 and recall at least 0.65.** If it was not met, round 3 would not be used and the choice would stay between step 400 and step 156.

## 2. Data
From the 304 accepted natural encounters we kept only those that also pass the strict rule: **at most 1 unsupported fact and no critical omission** (the normal rule allows 2 to 3 unsupported facts).

| Part | Examples | Note |
|---|---|---|
| Strict natural, training families | **112** | out of 263 accepted for training in round 2 |
| Strict natural, held-out families | 15 | validation |
| Replayed round-1 training examples | **300** | half the replay of round 2 |
| Training file | 412 lines | after the 6,144-token length limit about 397 were trained on (about 97 natural + 300 replay) |
| Validation | 250 round-1 + 15 natural = 265 | the natural validation set is smaller than in round 2 (41), so the natural loss numbers are **not comparable** with round 2 |

Built with `scripts/local/natural_gen/build_run2_dataset.py --strict --replay 300` into `data/round2_natural/run3/`.

## 3. Settings

| Setting | Value | Note |
|---|---|---|
| Start from | the round-2 step-156 adapter | |
| Learning rate | **2e-5** | much lower than round 2 (5e-5) and round 1 (1e-4): a gentle polish |
| Epochs | **2** | |
| Optimizer steps | **50** (about 25 steps per epoch of 16) | |
| LoRA rank / alpha / dropout / targets | 64 / 128 / 0.05 / all projections | unchanged |
| Batch | 1 x accumulation 16 | |
| Maximum sequence length | 6,144 | the setting that avoided the round-2 out-of-memory |
| Validation and checkpoints | every 10 steps (10, 20, 30, 40, 50) | |
| Memory setting | `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` | |

Run time: **104.1 minutes** (finished cleanly, no incident), which is about Rs 100 of compute at the Rs 58 per hour used elsewhere (an estimate).

## 4. Validation loss

| Step | Seen | Unseen | Held-out natural (15 examples) |
|---|---|---|---|
| 10 | 0.0251 | 0.0372 | 0.3090 |
| 20 | 0.0250 | 0.0375 | 0.3076 |
| 30 | 0.0256 | 0.0386 | 0.3112 |
| 40 | 0.0261 | 0.0394 | 0.3141 |
| 50 | 0.0259 | 0.0391 | 0.3129 |

Reading it: the natural loss is lowest at step 20 and then rises slightly, while the **round-1 losses drift upward** (seen 0.0243 at the end of round 2 to 0.0259; unseen 0.0371 to 0.0391). That is a small sign of the model moving away from the old distribution, and a reason to prefer an early checkpoint. As in round 2, loss alone cannot choose, so two checkpoints were generated and judged: **step 20** (lowest natural loss) and **step 50** (final).

## 5. Results on the 20 hand-written scenarios (windows, LLM judge, same prompts)

| Model | Precision | Recall vs design | Hallucination | Critical | Windows that could not be parsed |
|---|---|---|---|---|---|
| Round 1, step 400 (windows) | 0.730 | 0.562 | 0.206 | 0.050 | 0 of 44 |
| Round 2, step 156 (windows) | 0.710 | 0.675 | 0.213 | 0.054 | 0 of 44 |
| **Round 3, step 20 (windows)** | **0.683** | **0.681** | 0.234 | 0.059 | 0 of 44 |
| **Round 3, step 50 (windows)** | **0.664** | 0.640 | 0.255 | 0.060 | **3 of 44** |

Against step 400 on full text (precision 0.762, recall 0.558, hallucination 0.168, critical 0.048): round-3 step 20 has precision **-0.069** (better in only 1 of 20 scenarios) and recall **+0.117** (better in 15 of 20); step 50 has precision **-0.088** (better in 2 of 20) and recall +0.061 (better in 12 of 20). Facts per scenario stayed at about 52.

**Bar check: not met.** Precision fell (0.683 and 0.664, against the required 0.74) and hallucination rose (0.234 and 0.255). Recall stayed about the same as round 2 (0.681 for step 20), so the stricter labels did not trade recall for precision; they only lost precision. Step 50 also produced three windows the guard could not repair.

## 6. Why it did not work (what we can and cannot say)
* **The cleaner-label idea did not help.** Training on labels with fewer unsupported facts did not reduce the model's unsupported facts.
* **Label noise was probably not the main source of hallucination.** Accepted labels contain at most 1 unsupported fact per encounter (about 2% of the facts or less), while the model's hallucination rate is about 21%. A model-level cause (the small 0.6B capacity, or the longer natural outputs that give more chances to be wrong) is more likely, but we did not test this.
* **The model kept drifting.** Both round-1 validation losses rose a little during round 3, and the longer training (step 50) was worse than step 20 on every number.
* **Small data.** 97 natural examples is little; a stricter filter made the signal weaker, not cleaner.
* **No part of this is proven**; we ran one training run with one seed.

## 7. Outcome
* Round 3 is **not packaged for deployment** and the adapters are kept only for the record (`models/adapters/round3_step20` and `round3_step50`).
* The deployable candidates remain **round 1 step 400** and **round 2 step 156** (document 07).
* Total cost of the attempt: about 104 minutes of GPU time, plus the judging of two checkpoints; the pre-set bar made the decision quick and objective.

## 8. Questions an external reviewer may ask
**Why did you try round 3 at all?** Because round 2's trade-off (recall up, precision down) is the central weakness, and a low-cost experiment (under two hours) with a bar fixed in advance was a reasonable way to test one specific idea.

**Isn't it suspicious that you only report negative results?** No: the bar was fixed before the judging, both checkpoints are reported, and the failure is stated with the numbers. A negative result at this price is information.

**Why lr 2e-5 and only 2 epochs?** To keep the change small and avoid drift from the already-adapted model. A higher learning rate or more epochs was not tested; given the upward drift of the round-1 losses we have no evidence that they would help.

**Why only 300 replayed examples?** The training set was already small; the old-distribution losses nevertheless drifted up, which suggests that more replay might help. This was not tested.

**Would more or better data help?** Possibly, but we cannot claim it. The experiment shows that tightening the acceptance filter on the same generator's output is not enough.

**What would be the next experiment?** A clinician-reviewed natural validation set, a hyper-parameter comparison on one change at a time, longer natural examples with a way to train on them (a larger GPU), or fine-tuning with a loss that penalises unsupported facts more. None of this was run.
