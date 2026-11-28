# 07. Training round 4 (GPU run 4): a targeted dataset for the live-test mistakes, and why step 400 stays

Written for: the team and reviewers. Everything here is synthetic data, model-written labels checked by a second model and by rules, and measured on 20 hand-written scenarios with an LLM judge. No clinician has reviewed any of it.

**Result in one line.** Round 4 lowered the validation loss and captured more facts (recall 0.651 against 0.562), but it made more unsupported statements (precision 0.691 against 0.730, hallucination 0.237 against 0.206, critical 0.070 against 0.050). It missed the bar we set before testing, so **round 4 is not used and step 400 stays the deployed model.**

## 1. Why we started
After the live tests in the application (document 11: encounters m3_14, m3_15, 58, 59 and 19) we knew the specific mistakes of step 400. The most visible were:

| # | Mistake seen in live runs | Example |
|---|---|---|
| 1 | Reason for visit taken from a remark, not the visit's real reason | "she wouldn't have come at all" |
| 2 | Review of systems stored although the doctor never asked | symptoms added from a list the doctor did not read |
| 3 | A doctor's explanation stored as a patient symptom | what the doctor explained about a condition recorded as the patient's own symptom |
| 4 | "If needed" attached to a test that was already booked | booked vs conditional mix-up |
| 5 | Negatives flipped or put in the wrong place | "no asthma" next to asthma in history |
| 6 | Whole sentences copied from speech into name fields | idioms and remarks as symptom names |
| 7 | Allergies: a penicillin "allergy" the patient denied, next to amoxicillin in the plan | encounter 19 |
| 8 | Vital signs: wrong or earlier value | blood pressure 100/60 written, 109/77 said |

The backend (document 11) catches several of these with plain rules, but a model that does not make them in the first place is better. We had a GPU available overnight (4 to 7 hours), the deployed step 400 as a safe fallback, and the demo on 8 December. The decision, made together: **try one more round aimed only at these classes. If it does not beat step 400, step 400 stays and we report that we tried.**

## 2. What we aimed at
Targeted examples for the eight classes above, plus the neighbouring ones: reason for visit, caregiver speaking for the patient, history hidden in a medicine list, family and social history in one turn, clinical wording inside names, and speech-to-text noise in names. The hand-written scenarios m3_01 to m3_20 and the locked 973 test are evaluation data; **nothing from them was used**, and the situations were chosen to differ from their themes.

## 3. The dataset
Location: `data/round4_targeted/` (raw files, the training and validation files in `run4/`, a README). Scripts: `scripts/local/targeted_gen/`.

| Step | What | Script |
|---|---|---|
| 1 | About 48 clinical situations, each with a seed-fixed combination of one or two target traps (12 weighted trap types), extra speakers, an allergy variant, and 30 to 54 turns | `blueprints.py` |
| 2 | The writer model (grok-4.7) writes the conversation and the label for each spec; extra rules are added to the round-2 writer prompt | `generate_targeted.py` |
| 3 | A different model (gpt-5.4) checks every fact against the transcript and lists omissions; one repair round by the writer | `natural_gen/verify_natural.py` (reused), `verify_shard.py` |
| 4 | Automatic rules reject a label: contradicted allergy, allergy against a same-family medicine, vital number not in its cited turns, a symptom or chief complaint written as a sentence, a contradicted negative, a review-of-systems entry with no doctor question | `validate_labels.py` (uses `clinical_extraction/safety_checks.py` and `postprocess.py`) |
| 5 | Length limit 18,000 characters (prompt plus answer), held-out families removed, a replay sample of round-1 training examples added | `build_round4_dataset.py` |

The 12 trap types and their weights: reason for visit 14, review of systems asked only 12, doctor explanation not symptom 12, booked vs conditional 10, negatives and flips 10, clinical wording in names 10, allergy traps 8, vitals and prior values 8, history hidden in medicines 6, family and social history in one turn 6, caregiver attribution 6, speech-to-text noise in names 4.

### What survived
| Stage | Number |
|---|---|
| Planned | 480 (ids 40001 to 40480) |
| Written and converted | 471 (9 failed schema conversion) |
| Verified | 470 (1 blocked by the verifier's content filter) |
| Accepted by the model verifier | 381 |
| Rejected by the automatic rules | 59 (most often: a name of 7 or more words, a vital number not in its cited turns, an allergy denied in its own turns, a chief complaint written as a sentence) |
| Left out for length | 26 |
| **Targeted examples in training** | **250** |

Final files: **training 600 lines = 250 targeted + 350 replayed round-1 examples**; **validation 296 lines = 250 round-1 + 46 targeted examples from 7 held-out situation families** that are never trained on. The training file covers every class: reason for visit 54, review of systems 58, doctor explanation 45, booked vs conditional 52, negatives 43, clinical wording 43, allergies 31, vitals 25, and others.

The target was about 500, but 250 survived: a strict two-model and rule check removed about half. We kept the strictness rather than lower it.

## 4. The plan and the settings (decided before the result)
| Setting | Value | Why |
|---|---|---|
| Start from | step-400 adapter (`runs/run1/checkpoint_step400`) | the deployed model, so improvement is measurable |
| Learning rate | 3e-5 | low, a gentle polish (round 1 used 1e-4, round 2 5e-5, round 3 2e-5) |
| Epochs | 3 (changed from 2 after the build) | only 250 targeted examples survived, so each is seen three times |
| Optimizer steps | 114 (about 38 per epoch of 16) | |
| Batch | 1 x accumulation 16 | |
| LoRA rank / alpha / dropout | 64 / 128 / 0.05, all projections | unchanged |
| Maximum sequence length | 6,144 | the setting that avoided the round-2 out-of-memory |
| Validation and checkpoints | every 25 steps | to be able to judge the epoch-1 and epoch-2 states |
| GPU | Azure T4 VM, `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` | |

A 2-step pilot first: loss 0.267 then 0.165, peak GPU 8.6 GiB, 549 tokens per second, 0 examples skipped. (The pilot used the default learning rate 1e-4; the full run used 3e-5.) One training script on the VM was out of date and had no `--init_adapter` option; it was replaced with the laptop copy before the run.

## 5. The bar we set before testing
On the 20 hand-written scenarios, same judge and frozen prompts as step 400 (full text: precision 0.762, recall 0.558, hallucination 0.168, critical 0.048, 20 of 20 valid JSON):

* precision at least 0.76, hallucination at most 0.168, recall at least 0.58;
* 20 of 20 valid JSON without loops;
* locked-test judge-F1 not below about 0.93.

Otherwise step 400 stays. After the first test, we added a second, windowed bar (the deployed system cuts a conversation into windows of 14,000 characters). **We state plainly that this second bar was written after seeing the full-text result.** It was set before the windowed runs were generated, and it is the setting round 2 and round 3 were judged on: precision at least 0.73, recall at least 0.562, hallucination at most 0.206, and 0 windows the guard cannot repair (step 400 on windows: 0.730, 0.562, 0.206, 0.050, 0 of 44).

## 6. Training
Run time **218 minutes** (about 3.6 hours), finished cleanly with no skipped examples. About Rs 210 of compute at the Rs 58 per hour used elsewhere (an estimate, as in documents 04 to 06).

Validation loss (lower is better; the pilot's second step is in the first column):

| | step 2 | step 25 | step 50 | step 75 | step 100 | step 114 |
|---|---|---|---|---|---|---|
| seen (round-1 style) | 0.0299 | 0.0303 | 0.0272 | 0.0262 | 0.0267 | 0.0264 |
| unseen | 0.0561 | 0.0378 | 0.0364 | **0.0355** | 0.0368 | 0.0365 |
| natural | 0.3442 | 0.2857 | 0.2678 | 0.2601 | 0.2580 | **0.2578** |

Reading: all three fell and flattened after about step 75, so the model learned without forgetting round 1. By loss alone round 4 looked successful. We took step 75 (best unseen) and step 114 (best natural) to generation.

## 7. Results
### 7.1 Whole conversation (20 hand-written scenarios, 4,096 new tokens at most)
| | ended normally | valid as written | repaired by the guard | cannot be repaired |
|---|---|---|---|---|
| Round 1, step 400 | 20 | 20 | 0 | 0 |
| Round 4, step 75 | 10 | 9 | 10 | 1 |
| Round 4, step 114 | 10 | 10 | 9 | 1 |

Half of the outputs ran to the token limit. Five or six per checkpoint were repetition loops (guard rule R6); the others were a key written as the value of the previous key (rule R7), a mistake step 400 did not make on these scenarios. The guard saves most outputs, but a loop loses everything the model would have written afterwards (some repaired outputs had only 5 to 15 items). **Bar 1 failed**: 20 of 20 was required.

### 7.2 Windows (44 windows, the deployed setting)
| | windows ended normally | after the guard |
|---|---|---|
| Round 4, step 114 | 42 / 44 | 44 / 44 usable (2 repaired) |
| Round 4, step 75 | 32 / 44 | not judged |

### 7.3 Judge on windows (20 scenarios, same judge and prompts)
| | precision | recall | hallucination | critical |
|---|---|---|---|---|
| **Round 1, step 400 (deployed)** | **0.730** | 0.562 | **0.206** | **0.050** |
| Round 2, step 156 | 0.710 | 0.675 | 0.213 | 0.054 |
| Round 3, step 20 | 0.683 | 0.681 | 0.234 | 0.059 |
| **Round 4, step 114** | 0.691 | **0.651** | 0.237 | 0.070 |

**Bar 2 failed**: precision 0.691 (needed at least 0.73), hallucination 0.237 (needed at most 0.206). Recall passed (0.651 against 0.562). Critical errors rose from 0.050 to 0.070. Step 75 was not judged because 12 of its 44 windows did not finish. The locked 973 test was not run, because the bar had already failed.

## 8. Decision
**Round 4 is not used. Step 400 stays the deployed model**, with the H1 deployment kept for rollback. The reason: round 4 gave a more complete record but more unsupported statements, including more critical ones, and on full text half of the outputs did not finish. In a clinical setting a wrong fact written down is worse than a missing one, so we did not trade precision for recall.

## 9. What we learned
* **Validation loss is not enough.** In rounds 2 and 4 the loss improved while generation got worse; only generating and judging shows it (see also document 05, section 6).
* **Three rounds in a row show the same pattern**: continuing from step 400 on longer, natural-style, model-written labels raises recall and lowers precision. A capacity limit of the 0.6B model is possible but untested; a larger base model (the 1.7B track) is a different experiment.
* **The strict data filter is expensive**: about half of the model-verified encounters were rejected by the rules. That is also a sign that the writer model makes the same kinds of mistake we wanted to remove.
* **One seed, 20 scenarios.** A paired bootstrap over the 20 scenarios, done after round 5 (document 08, section 5.2), shows that round 4's precision loss (-0.039, interval -0.067 to -0.013) and recall gain (+0.088) were larger than the scenario-resampling noise; hallucination (+0.031, interval -0.002 to +0.062) was not. The bootstrap does not cover the judge's own variation or the training seed. (An earlier version of this sentence called these differences 'within noise'; that was too loose.) A fifth round followed with a different cause tested: document 08.

## 10. Honest limits
Synthetic data, model-written and model-verified labels, no clinician review. A single training seed. The judge is one model with one rubric. Recall is measured against the short `design` block of each scenario, a floor-style check. The second (windowed) bar was written after seeing the full-text result, although before the windowed outputs existed.

## 11. What to say at the demo
"We ran three more fine-tuning rounds, the last one built from the mistakes we saw in live tests. Each round found more facts but also wrote more unsupported ones, so we kept the first model and rely on the backend checks and the 'Before you sign' list for the remaining mistakes." Not: "we improved the model", and not an accuracy percentage.

## 12. Where the files are
| What | Where |
|---|---|
| Dataset, README and result | `data/round4_targeted/` |
| Scripts | `scripts/local/targeted_gen/` |
| Adapters (steps 75 and 114) | `models/adapters/round4/` |
| Generation outputs, logs, merged windows | `runs/round4_targeted/` |
| Judge output | `evaluation/judge_eval/output/m3_win_run4_step114.md` |
