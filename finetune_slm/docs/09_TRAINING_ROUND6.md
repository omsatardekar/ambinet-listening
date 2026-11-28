# 09. Training round 6 (GPU run 6): counselling lists capped at 4, and why step 400 still stays

Written for: the team and reviewers. Synthetic data, model-written labels checked by a second model and by rules, 20 hand-written test scenarios, an LLM judge. No clinician has reviewed any of it.

**Result in one line.** Capping the counselling lists did not fix the loops (32 of 44 windows ended normally against 28 in round 5, bar 42) and did not recover precision (0.621 against step 400's 0.730). It missed the bar set before testing. **Step 400 stays the deployed model.**

## 1. Why we ran it
Round 5 (document 08) ended with an untested explanation: its unfinished outputs stopped inside the `counselling` list of `clinical_actions`, and its natural labels have up to 13 counselling items (mean 2.7) against at most 4 in round 1. The team proposed a last, cheap test: cap those lists at 4 (general advice such as "sleep well, eat well" is meant to become a small separate recommendations section in the application, at most 4 items, not part of the plan) and see whether the loops and the precision loss shrink. The team allowed about three hours.

## 2. The dataset (`data/round6_capped_counselling/`, script `scripts/local/round5_build/build_round6_capped.py`)
| Part | Lines | Note |
|---|---|---|
| Natural encounters (the cleaned labels of round 5, each once) | 384 | in each label the first 4 `counselling` items are kept, the rest removed: 101 examples changed, 176 items removed |
| Round-1 synthetic (random) | 600 | |
| **Training file** | **984** | |
| Validation | 313 | same encounters as round 5, natural labels capped |

All labels still expand; no scenario or locked-test id is used. Items of other types (tests, scans, follow-up) were not touched.

## 3. The plan and the bar (set before the result)
Start from round-5 step 220 (`--init_adapter`), 50 optimizer steps, lr 3e-5, batch 1 x accumulation 16, maximum length 6,144, validation and checkpoint every 10 steps. **Bar:** at least 42 of 44 windows end normally; no metric worse than step 400 by more than 0.01; precision or recall better by at least 0.03. The full-text and locked tests only if the windows pass. **Stated limits before the run:** the extra 50 steps are also extra training, so a gain could not be credited to the cap alone; round 5's precision (0.639) was far below step 400's, and 50 steps were not expected to close it.

## 4. Training
128 minutes, no skipped example, about 360 to 400 tokens per second, peak GPU 9.7 GiB. Validation loss (lower is better):

| | seen | unseen | natural |
|---|---|---|---|
| Round 5, step 220 | 0.0434 | 0.0431 | 0.2417 |
| step 10 | 0.0461 | 0.0459 | 0.2423 |
| step 30 | 0.0446 | 0.0439 | 0.2372 |
| **step 50** | 0.0431 | 0.0425 | 0.2365 |

Reading: small, steady improvements; as in rounds 4 and 5, the loss said nothing about the generation problems.

## 5. Results (checkpoint 50, windows only)
32 of 44 windows ended normally; the guard repaired 11 of the other 12 and one window (m3_02) could not be repaired. Judge, 20 scenarios, same judge and frozen prompts as step 400:

| | ended normally | precision | recall | hallucination | critical |
|---|---|---|---|---|---|
| **Round 1, step 400 (deployed)** | 44 repairable | **0.730** | 0.562 | **0.206** | **0.050** |
| Round 5, step 220 | 28 | 0.639 | 0.621 | 0.288 | 0.080 |
| **Round 6, step 50** | 32 | 0.621 | 0.614 | 0.303 | 0.078 |

The bar was not met (42 of 44 required; precision and hallucination far from step 400). Round 6 against round 5 differs by a few hundredths; the judge was run once and no bootstrap was done, so that small difference is not interpreted. Not run: the whole-conversation test, the locked 973 test (the bar had already failed).

## 6. Decision
**Round 6 is not used. Step 400 stays the deployed model** (H1 deployment kept for rollback).

## 7. What it tells us
* **Long counselling lists are not the main cause** of the loops or of the precision loss: the cap raised normal endings only from 28 to 32 of 44 and moved no quality metric toward step 400.
* Still untested: a capacity limit of the 0.6B model (our suspicion, not shown), other open lists, and the 1.7B model.
* Six rounds on this 0.6B model now (rounds 1 to 6): only round 1 produced a model we trust more than the others on precision. The measured pattern across rounds 2 to 6 is the same: more facts found, more unsupported facts written.

## 8. Honest limits
Synthetic data, model-written and model-verified labels, no clinician review. One seed per round, one judge run. Round 6 had 50 more steps than round 5, so even a gain could not be attributed to the cap alone. Windows only.

## 9. What to say at the demo
"We ran five further training rounds, including one trained from scratch on cleaned data and one that capped the long advice lists. Each found more facts but also wrote more unsupported ones, so we kept the first model. The remaining mistakes are caught by the backend checks and the 'Before you sign' list." Not: "we improved the model", and not an accuracy percentage.

## 10. Where the files are
| What | Where |
|---|---|
| Dataset, README | `data/round6_capped_counselling/` |
| Build script | `scripts/local/round5_build/build_round6_capped.py` |
| VM run script | `scripts/to_gpu_vm/run_round6.sh` |
| Adapter (step 50) and training log | `models/adapters/round6/` |
| Window outputs, logs, merged windows, judge log | `runs/round6_capped/` |
| Judge output | `evaluation/judge_eval/output/m3_win_run6_step50.md` |
