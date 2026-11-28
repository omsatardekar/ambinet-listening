# 08. Training round 5 (GPU run 5): cleaned mixed data, trained once from the base model, and why step 400 still stays

Written for: the team and reviewers. Synthetic data, model-written labels checked by a second model and by rules, 20 hand-written test scenarios, an LLM judge. No clinician has reviewed any of it.

**Result in one line.** Round 5 captured more facts than step 400 (recall 0.621 against 0.562) but was clearly worse on precision (0.639 against 0.730), hallucination (0.288 against 0.206) and critical errors (0.080 against 0.050), and it often failed to stop writing (16 of 44 windows hit the token limit). It missed the bar set before testing. **Step 400 stays the deployed model.**

## 1. Why we ran it
Rounds 2, 3 and 4 each continued from an earlier adapter with a few hundred model-written labels, and each time recall rose while precision fell (document 07, section 9). Two explanations were testable with the GPU available overnight:
1. **Label noise.** Some facts in the model-written labels are not supported by the conversation.
2. **Stacking.** Small rounds stacked on top of step 400 may shift the model's style instead of teaching it.

So round 5 cleaned the labels and trained **once, from the base model**, on round-1 and natural data mixed. The team accepted a run of 7 to 8 hours and agreed beforehand that a failure is still a useful experiment.

## 2. The dataset (`data/round5_clean_mix/`, script `scripts/local/round5_build/build_round5_dataset.py`)
| Part | Unique | Lines in the training file | Note |
|---|---|---|---|
| Round-1 synthetic | 1,900 | 1,900 | all 628 ids that round 1 repeated (rare scenarios) + a random fill |
| Natural, round 2 | 102 | 204 | cleaned labels, each twice |
| Targeted, round 4 | 282 | 564 | cleaned labels, each twice |
| **Training file** | | **2,668** | natural lines are 29%, close to round 2's 27% |
| Validation | | 313 | 250 round-1 + 63 natural from held-out situation families (round 2 and round 4) never trained on |

**Label cleaning.** For every natural encounter, the facts the verifier had marked unsupported, partially supported or contradicted were removed from the label (the label was then re-compacted; nothing else was edited). In the training part this removed 423 of 13,660 facts, **about 3%** (376 partial, 34 unsupported, 13 contradicted). An encounter was used only if it had at most 1 critical omission, at most 6 doubtful facts, passed the round-4 automatic rules after the removal, and fit 18,000 characters. Excluded: 197 for critical omissions, 242 by the automatic rules (mostly round-2 encounters, which had never been checked by those rules), 108 for length, 1 for too many doubtful facts, 5 unverified. No scenario id or locked-test id is in either file.

## 3. The plan and the settings (decided before the result)
| Setting | Value | Why |
|---|---|---|
| Start from | the base model (no adapter) | tests the stacking idea |
| LoRA | rank 64, alpha 128, dropout 0.05, all projections (40.4 million trainable parameters) | as round 1 |
| Learning rate | 1e-4, warm-up 3%, cosine to 1e-5 | as round 1 |
| Optimizer steps | 220 (3,520 examples, about 1.3 passes) | the budget of about 7 hours; round 1's curves flattened at about step 250 of 654 |
| Batch | 1 x accumulation 16, maximum length 6,144 | |
| Validation and checkpoints | every 20 steps | |

A 2-step pilot first: loss 1.00 then 0.81, peak GPU 8.2 GiB, about 570 tokens per second, no skipped example.

**Stated limit before the run:** 220 steps are about 55% of round 1's compute up to step 400, so a worse result could partly mean "less trained". The loss was still falling at step 220 (below).

**The bar (set before the result).** On the 20 scenarios, same judge as step 400: 20 of 20 ended normally without loops, no metric worse than step 400 by more than 0.01, precision or recall better by at least 0.03, and locked-test judge-F1 not below about 0.93.

## 4. Training
Run time **420 minutes (7 hours)**, no skipped example, 473 to 535 tokens per second, peak GPU 9.7 GiB. About Rs 410 of compute at Rs 58 per hour (an estimate). Validation loss (lower is better):

| step | 20 | 60 | 100 | 140 | 180 | 220 |
|---|---|---|---|---|---|---|
| seen | 0.1732 | 0.0865 | 0.0620 | 0.0501 | 0.0455 | **0.0434** |
| unseen | 0.1804 | 0.0837 | 0.0611 | 0.0485 | 0.0440 | **0.0431** |
| natural (63 held-out) | 0.3594 | 0.2837 | 0.2613 | 0.2497 | 0.2439 | **0.2417** |

Reading: the loss fell steadily and was still falling at the end (the training loss at step 220 was 0.092). Seen and unseen are higher than step 400's (about 0.024 and 0.035), as expected with less compute. As in round 4, the loss gave no warning about the failures below.

## 5. Results (checkpoint 220, the last; step 180 was not tested)
### 5.1 Ending normally
| | whole conversation (20) | windows (44) |
|---|---|---|
| Round 1, step 400 | 20 ended normally | 0 windows the guard could not repair |
| Round 4, step 114 | 10 | 42 |
| **Round 5, step 220** | **9** | **28** |

The guard repaired every unfinished output (11 of 20 whole conversations, all 16 windows; none failed), but a repair cuts off what the model would have written after the loop. **Bar not met** (20 of 20 required).

**What the unfinished outputs have in common.** Almost all stop inside the `clinical_actions` list while writing another `counselling` item ("Do not stop the inhaler", "Advise avoiding the cream", "Hold on to something until dizziness passes"); the rest are other endless lists (a repeated negative finding, repeated medicines). In the training file the natural labels have a mean of 2.7 counselling items and a maximum of 13, against 1.6 and a maximum of 4 in round 1; step 400 learned from lists of at most 4 and never looped. This is a **likely cause, not a proven one**: we have not trained the same recipe with the counselling lists capped.

### 5.2 Judge on windows (20 scenarios, same judge and frozen prompts as step 400)
| | precision | recall | hallucination | critical |
|---|---|---|---|---|
| **Round 1, step 400 (deployed)** | **0.730** | 0.562 | **0.206** | **0.050** |
| Round 4, step 114 | 0.691 | **0.651** | 0.237 | 0.070 |
| **Round 5, step 220** | 0.639 | 0.621 | 0.288 | 0.080 |

**Reading the differences.** A bootstrap over the 20 scenarios (2,000 resamples, paired with step 400) gives these differences with 95% intervals:

| difference to step 400 | precision | recall | hallucination | critical |
|---|---|---|---|---|
| Round 4, step 114 | -0.039 [-0.067, -0.013] | +0.088 [+0.042, +0.134] | +0.031 [-0.002, +0.062] | +0.020 [+0.005, +0.035] |
| Round 5, step 220 | -0.092 [-0.123, -0.062] | +0.058 [+0.018, +0.098] | +0.082 [+0.053, +0.111] | +0.030 [+0.013, +0.045] |

Across these 20 scenarios the precision loss and the recall gain are both larger than the resampling noise, for both rounds; round 5's hallucination and critical increases also exclude zero. **This corrects a sentence in document 07 (section 9)**, which called differences of a few hundredths "within noise": for round 4 that was too loose. The bootstrap covers only the choice of scenarios; it does not cover the judge's own variation or the training seed (one seed per round), so the intervals are narrower than the true uncertainty.

Not run: the locked 973 test (the bar had already failed) and the judge on the whole-conversation outputs.

## 6. Decision
**Round 5 is not used. Step 400 stays the deployed model** (H1 deployment kept for rollback). Round 5 repeated the pattern of rounds 2 to 4: more facts found, more unsupported facts written, and in addition it often does not stop. It was also the worst of the four on precision and hallucination.

## 7. What it tells us about the two explanations
* **Stacking is not the main cause.** Training once from the base model on mixed data did not avoid the precision loss; it was larger than in round 4. (The reduced compute is a confound: round 5 was less trained than step 400.)
* **Label noise as the verifier sees it is not the main cause either**, but the test was weak: the verifier marked only 3% of facts and we removed only those. Mistakes the verifier does not catch remain in the labels.
* **The natural-style labels themselves are the common factor** of rounds 2 to 5: longer outputs (about 52 facts per consultation against 30), long open-ended lists (counselling), model-written. Every run that included them lost precision. A capacity limit of the 0.6B model is also still possible and untested.
* **Untested idea (not done):** cap the counselling and other open lists in the natural labels and see whether the loops and the precision loss shrink. Another independent test is the 1.7B model.

## 8. Honest limits
Synthetic data, model-written and model-verified labels, no clinician review. One training seed per round. One judge with one rubric. Recall is against the short `design` block of each scenario. Round 5 had about 55% of round 1's compute. Only the last checkpoint was tested. The bootstrap resamples scenarios only.

## 9. What to say at the demo
"We ran five further training rounds, including one built from the mistakes seen in live tests and one trained from scratch on cleaned data. Each found more facts but also wrote more unsupported ones, so we kept the first model. The remaining mistakes are caught by the backend checks and the 'Before you sign' list." Not: "we improved the model", and not an accuracy percentage.

## 10. Where the files are
| What | Where |
|---|---|
| Dataset, README | `data/round5_clean_mix/` |
| Build script | `scripts/local/round5_build/build_round5_dataset.py` |
| VM run script | `scripts/to_gpu_vm/run_round5.sh` |
| Adapter (step 220) and training log | `models/adapters/round5/` |
| Generation outputs, logs, merged windows, judge log | `runs/round5_clean_mix/` |
| Judge output | `evaluation/judge_eval/output/m3_win_run5_step220.md` |

## 11. What came next
The untested idea from section 7 (capping the counselling lists) was run as round 6 and also failed its bar: see `09_TRAINING_ROUND6.md`.
