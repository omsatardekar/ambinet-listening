# Module 3 fine-tuning: documentation index

Eleven short reports, written to be read in order by someone new to the project. Each one ends with the questions an external reviewer is likely to ask about that part, with answers based only on what we did and measured.

| # | File | Read it to learn |
|---|---|---|
| 01 | [01_PROJECT_AND_MODULE3.md](01_PROJECT_AND_MODULE3.md) | what the project is, what Module 3 does, why a small model, what was wrong before, a glossary |
| 02 | [02_DATASETS.md](02_DATASETS.md) | every dataset (round 1, natural round 2, round 3, the 20 scenarios), how each was made, the split, the weaknesses (template-driven dialogue, model-written labels) |
| 03 | [03_MODELS_AND_EXPERIMENTS.md](03_MODELS_AND_EXPERIMENTS.md) | Qwen3-0.6B and 1.7B, all earlier experiments (EXP_001 to EXP_008, the 1.7B track), what was frozen, why we moved to fine-tuning |
| 04 | [04_TRAINING_ROUND1.md](04_TRAINING_ROUND1.md) | GPU run 1: epochs, data, every hyper-parameter, loss curve, checkpoint choice, the locked-test results |
| 05 | [05_TRAINING_ROUND2.md](05_TRAINING_ROUND2.md) | GPU run 2: natural-speech data, the out-of-memory incident, the repetition loops, the JSON guard, windowed extraction, results |
| 06 | [06_TRAINING_ROUND3.md](06_TRAINING_ROUND3.md) | GPU run 3: cleaner labels, the pre-set bar, why it was not used |
| 07 | [07_TRAINING_ROUND4.md](07_TRAINING_ROUND4.md) | GPU run 4: a targeted dataset built from the live-test mistakes, plan and settings, the bar set before testing, results, why it was not used and step 400 stays |
| 08 | [08_TRAINING_ROUND5.md](08_TRAINING_ROUND5.md) | GPU run 5: cleaned mixed data trained once from the base model, the bar, results with a bootstrap of the judge noise, why step 400 still stays |
| 09 | [09_TRAINING_ROUND6.md](09_TRAINING_ROUND6.md) | GPU run 6: counselling lists capped at 4, 50 steps from round-5 step 220, the bar, results, why step 400 still stays |
| 10 | [10_LLM_JUDGE_AND_FINAL_SELECTION.md](10_LLM_JUDGE_AND_FINAL_SELECTION.md) | how every number was produced, all results of all models, limits, the final selection and what is still to do |
| 11 | [11_LIVE_TESTS_AND_DEPO_WORDING.md](11_LIVE_TESTS_AND_DEPO_WORDING.md) | three live runs, the six backend safeguards, what to say and not say at the depo |

Older working documents (kept as they are):
* [FINETUNING_TRAINING_REPORT.md](FINETUNING_TRAINING_REPORT.md): the chronological report, sections 1 to 42, written while the work happened.
* [MODULE3_FINETUNING_FOCUS.md](MODULE3_FINETUNING_FOCUS.md): the 32 failure classes (F1 to F32) found in six live runs and the checks derived from them.
* [FOLDER_MOVES.md](FOLDER_MOVES.md): where every file was before the folder reorganisation of 2026-11-25.

## Where to find an answer fast
| Question | Go to |
|---|---|
| What is Module 3 and why a 0.6B model? | 01 sections 1 to 3 |
| What did the model do wrong before fine-tuning? | 01 section 4, `MODULE3_FINETUNING_FOCUS.md` |
| How was the data made, and is it template-driven? | 02 sections 2 and 3, 02 section 6 |
| How is the test set kept clean? | 02 section 2.2 |
| Which models and prompts did you try first? | 03 sections 3 to 5 |
| What are the training settings and why? | 04 section 4 |
| How long and how much did it cost? | 04 section 5 |
| Why step 400? | 04 section 7 |
| Why did round 2 loop, and what is the guard? | 05 sections 6 and 7 |
| Why windows? | 05 section 8 |
| Why did round 3 fail? | 06 |
| Why did round 4 (targeted data) not replace step 400? | 07 |
| Why did round 5 (cleaned labels, from the base model) not replace step 400? How big is the judge noise? | 08 section 5 |
| What is the temperature? | 04 section 4 (table) and 05 section 11 |
| Did capping the counselling lists fix the loops (round 6)? | 09 |
| What is judge-F1, how reliable is it? | 10 section 1 |
| Which model is the final choice? | 10 section 4 (step 400; confirmed after rounds 4 and 5, see 07 to 09) |
| What did the live tests in the application show, and what did the backend add? | 10 section 5 |
| What is still not done? | 10 section 4 (before a final release) |

## Headline numbers (all with the caveats in document 10)
| | Value |
|---|---|
| H1 baseline on 30 encounters: judge-F1 / hallucination | 0.352 / 0.262 |
| Round 1 (step 400) on the same 30: judge-F1 / hallucination | 0.939 / 0.014 |
| Round 1 on the 973-encounter locked test: judge-F1 / precision / recall / hallucination | 0.933 / 0.945 / 0.921 / 0.024 |
| Natural scenarios, baseline: precision / recall / hallucination | 0.515 / 0.272 / 0.325 |
| Natural scenarios, step 400: precision / recall / hallucination | 0.762 / 0.558 / 0.168 |
| Natural scenarios, step 156 with windows: precision / recall / hallucination | 0.710 / 0.675 / 0.213 |
| Live Azure speed, step 400, one consultation of about 12,000 characters | 193 to 272 seconds (extraction job) |
| Training cost across all rounds | about Rs 2,300 to 2,600 (an estimate; the portal holds the exact figure) |
