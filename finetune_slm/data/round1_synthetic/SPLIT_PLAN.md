# How the 4,200 encounters are split, and why

| Split | Encounters | Source | Used for |
|---|---|---|---|
| **Train** | 2,856 (3,484 lines with rare cases repeated once) | Batches 2-9 | fitting the model |
| **Validation** | 250 = 190 "seen scenarios" + 60 "unseen scenarios" | Batches 2-9 | choosing the checkpoint and when to stop, nothing else |
| **Test A: benchmark** | 500 | all of Batch 1 | final score, comparable with every earlier experiment (the 30 EXP_008 ids are flagged `exp008_eval_id`) |
| **Test B: curated** | 473 | 111 scenario groups chosen by rule from Batches 2-9 | final score on new, harder, more natural cases |
| Reserve (unused) | 121 | leftover members of held-out scenario groups | not used anywhere; kept out of training so no held-out scenario leaks into it |

## Why this split, in plain words (for external questions)
1. **No leakage by scenario.** Many encounters come from the same clinical scenario (same condition, different patient and wording). A random split would put near-twins in train and test and inflate the score. So we hold out **whole scenario groups**: no scenario in Test B or in the "unseen" validation part appears in training. Measured overlap of test with training (word 5-gram similarity): median 0.06 and maximum 0.115 for Test B; median 0.04 and maximum 0.094 for the benchmark.
2. **Test A (Batch 1) is untouched by training**, as its own README requires ("evaluation use only"). It is the benchmark every earlier model and prompt was measured on, so baseline versus fine-tuned is a fair like-for-like comparison.
3. **Test B is chosen, not random**, to be unique and non-obvious:
   * 102 encounters from 15 of the 28 Batch 9 scenarios (atypical presentations, mimics, medicine-induced problems, quiet red flags);
   * about 78 "worst case" (emergency), 95 "middle" and 38 "best case" encounters from Batches 4-8, with at least one group from each of the 12 specialties;
   * 100 from Batch 2;
   * **60 hand-written, natural-language conversations from Batch 3** (the only human-authored dialogue).
   Within each held-out group we kept up to 10 encounters, the ones with the most difficulty (more uncertainties and disputed facts, 4 or more speakers, an unidentified voice, more allergies, medicines and negatives, longer labels).
4. **Test B is harder than training on purpose.** Encounters with a documented uncertainty: 48% in Test B and 52% in Test A, against 35% in training. A good score here is not just memorising easy cases.
5. **Validation is separate from test.** The "unseen scenario" part of validation shows whether the model is overfitting to scenario templates; the "seen scenario" part tracks normal learning. Only validation is used to pick the checkpoint and settings. Test is run **once**, at the end. `test/TEST_LOCK.json` records the locked ids and file hashes, dated 2026-11-22.
6. **Honest limits.** All labels are generated and automatically validated, with no clinician review; say so when reporting. A final reality check on realistic transcripts (the 20 scripted recordings in `scenarios/`, and later approved real data) is separate from this split.

## What to report
Per split and per subset (benchmark; curated by group type: non-obvious, worst, middle, best, natural hand-written): valid-JSON rate, schema-valid rate, item-level precision, recall and F1 per section, and the failure-class checks in `TRAINING_AND_DEPLOYMENT_PLAN.md`. Report the frozen-prompt baseline (the same base model with no fine-tuning) on the identical sets.
