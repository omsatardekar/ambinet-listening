# LLM-judge evaluation of the Qwen extraction experiments

Written for the project owner and mentor. Status: full run complete with gpt-5.4 as primary judge; a second judge (Grok, a different model family) re-judged a deterministic 20% sample and agrees substantially (section 4e). Human calibration is NOT done (see section 2).

## 1. Why this was done
The earlier evaluation matched predicted and expected facts by strict string rules and reported F1. Correct paraphrases were scored wrong, and valid facts missing from the label were scored as false positives. The mentor asked for a frontier model to judge the outputs and for metrics computed from its verdicts.

## 2. What was expected versus what was delivered
| Planned | Status | Note |
|---|---|---|
| Inventory of every experiment | Done | `output/inventory.md`; 14 runs, all paths verified |
| Flatten labels and predictions into comparable facts | Done | `flatten.py`, 5 tests |
| Frozen judge rubrics (precision and recall passes) | Done | `prompts.py`; the SHA-256 of each is stored in every result |
| Judge client with cache and retries | Done | `client.py`; key never logged |
| Pilot on about 10 encounters | Done, informally | 10 pairs; I read the reasons myself. You did not review them |
| Full run on every experiment | Done | 478 pairs (every parsed encounter of the 11 core runs), 0 failures, about 2.70 M tokens (1.82 M in, 0.88 M out) |
| Metrics with 95% confidence intervals | Done | bootstrap over encounters, fixed seed |
| Second judge on a 20% sample | Done | Phi-4-mini failed first (below); replaced by Grok (`grok-4.7` deployment): 98 pairs, 0 failures |
| Human calibration of about 40 encounters | NOT done | needs a person; without it the judge is unvalidated |
| Old strict F1 next to the new numbers | Partly | verified only for 1.7B P01 and P02 (section 4) |
| EXP_005 repaired runs and P04 smoke | Not judged | registered as "extra"; run them if wanted |

**Second judge.** The first choice, Phi-4-mini-instruct, ignored the JSON-only instruction and wrote prose (verified on one call, 384 s, output not valid JSON; in the batch run 0 pairs succeeded and 27 failed with "reply contained no JSON" before I stopped it). It is also a 4B-class model, the same size class as what is being judged. The owner then pointed `JUDGE2_*` at a Grok deployment, which produced valid verdicts on all 98 sampled pairs.

## 3. Setup facts that affect every number
- Ground truth is `dataset_v2_batch_001_corrected`. The earlier uncorrected batch differs in every transcript and label and is never mixed in.
- P05 ran on its own 50-encounter validation split, which shares no encounter with the other runs. It is compared only with EXP_003 on those 50.
- Failed or unparsed encounters count as zero predictions (tier 1). The "parsed-only" column is shown next to it, never instead of it.
- Credit: "strict" counts only fully supported or found facts; "lenient" gives half credit to partially supported or partially found ones.
- The precision pass sees only the transcript, not the label, so label mistakes cannot leak into the faithfulness score.

## 4. Results
Judge-F1 = harmonic mean of fact-level precision and recall under the judge's verdicts. It is **not** clinical accuracy, and the project rule against calling F1 accuracy still stands.

### 4a. Same 30 encounters for every run except P05 (the fair comparison)
| run | judged / attempted | precision (lenient) | recall (lenient) | judge-F1 lenient [95% CI] | judge-F1 strict | hallucination rate | critical-flag rate |
|---|---|---|---|---|---|---|---|
| 0.6B EXP_003 direct | 29 / 30 | 0.589 | 0.115 | 0.193 [0.152, 0.230] | 0.111 | 0.167 | 0.107 |
| 0.6B P01 | 30 / 30 | 0.557 | 0.197 | 0.291 [0.234, 0.341] | 0.192 | 0.249 | 0.114 |
| 0.6B P02 | 30 / 30 | 0.577 | 0.220 | 0.318 [0.263, 0.364] | 0.198 | 0.241 | 0.136 |
| 0.6B P03 | 28 / 30 | 0.537 | 0.135 | 0.216 [0.173, 0.254] | 0.122 | 0.194 | 0.152 |
| 0.6B S1 | 24 / 30 | 0.625 | 0.196 | 0.299 [0.237, 0.359] | 0.225 | 0.260 | 0.157 |
| 0.6B S1.1 B1 | 27 / 30 | 0.650 | 0.284 | 0.395 [0.343, 0.444] | 0.314 | 0.280 | 0.119 |
| 0.6B S1.1 B2 | 17 / 30 | 0.724 | 0.219 | 0.336 [0.239, 0.421] | 0.275 | 0.220 | 0.070 |
| 1.7B P00 direct | 23 / 30 | 0.749 | 0.335 | 0.463 [0.378, 0.537] | 0.386 | 0.161 | 0.074 |
| 1.7B P01 | 25 / 30 | 0.725 | 0.409 | 0.523 [0.455, 0.580] | 0.446 | 0.178 | 0.082 |
| 1.7B P02 (frozen) | 28 / 30 | 0.666 | 0.448 | 0.536 [0.484, 0.573] | 0.446 | 0.231 | 0.101 |

### 4b. P05 versus EXP_003 on P05's own 50 encounters
| run | judged / attempted | precision | recall | judge-F1 lenient [95% CI] | strict |
|---|---|---|---|---|---|
| 0.6B EXP_003 direct | 46 / 50 | 0.549 | 0.094 | 0.161 [0.130, 0.190] | 0.088 |
| 0.6B P05 | 50 / 50 | 0.541 | 0.239 | 0.331 [0.302, 0.359] | 0.208 |

### 4c. Each run on all of its own encounters (sizes differ, so rows are NOT directly comparable)
EXP_003 on all 100: F1 0.177 [0.155, 0.200] (94 parsed, 6 failed). 0.6B P01 0.272 (50), P02 0.330 (50), P03 0.220 (35 attempted), P05 0.331 (50), S1 0.296, S1.1 B1 0.402, S1.1 B2 0.357 (all 50). 1.7B P00 0.421 (50), P01 0.523 (30), P02 0.536 (30). Full table: `output/metrics_JUDGE_own.md`.

### 4d. What the numbers support
- **1.7B is clearly better than 0.6B** on the shared 30: the best 1.7B run (P02, 0.536 [0.484, 0.573]) is above the best 0.6B run (S1.1 B1, 0.395 [0.343, 0.444]) and the intervals do not overlap. Caveat: the 0.6B S1 and S1.1 runs have many failed records scored as zero, and 1.7B P00 has 7 failures; the parsed-only column is higher for those (for example 1.7B P00 0.563).
- **0.6B direct (EXP_003) extracts too little**: recall about 0.10, precision about 0.59. It writes about 5 facts per encounter against a median of 36 in the label.
- **Among 0.6B prompts**, P02 and P05 are the best of the plain prompts (about 0.32–0.33), P03 is clearly worse (0.216), and S1.1 B1 is the best of all 0.6B runs.
- **1.7B P00, P01 and P02 cannot be ranked with confidence.** P02 is highest, but the intervals overlap heavily and this comparison is unpaired. P02 has the highest recall (0.448) and also the highest hallucination rate (0.231 vs 0.178 for P01).
- **Old strict F1 vs judge-F1 for 1.7B on the same 30** (old numbers from `P02_VS_P01_METRICS.md`): P01 0.201, P02 0.258 under strict matching; 0.523 and 0.536 under the judge. The judge scores roughly twice as high, as expected from paraphrase credit, and shows a much smaller P01→P02 gap.
- **Hallucination** (unsupported plus contradicted facts) is 16–28% in every run, so no run is clean. Examples seen for 1.7B P02: "no fever" when the transcript has fever, invented vital signs, and an allergy attributed to the wrong drug.
- **Label gaps are small.** For 1.7B P02, 19 of 407 supported predicted facts (4.7%) matched no reference fact; for 0.6B P02, 26 of 287 (9.1%).
- **Weak fields (1.7B P02)**: review of systems recall 0.0, clinical uncertainties 0.06, clinical actions 0.29, symptoms 0.25. Strong: chief complaint 0.87, vital signs 0.81, assessment 0.69. Per-field numbers for every run are in `output/metrics_JUDGE_*.json`.

### 4f. EXP_008: Qwen3-0.6B hybrid prompt H1 (added after the main report)
Full normal P02 JSON, no example facts, frozen prompt (sha256 dc10ba06...), same 30 encounters. 30/30 parsed on the first attempt, 0 token-cap hits. Judge-F1 (lenient) **0.352 [0.313, 0.390]**, precision 0.568, recall 0.255, hallucination 0.262, critical-flag rate 0.120. Paired with the other 0.6B runs on the same encounters: tie with S1.1 B1 (-0.043 [-0.096, +0.020]) and with EXP_004 P02 (+0.034 [-0.015, +0.083]); better than EXP_003 direct (+0.159 [+0.110, +0.207]); worse than 1.7B P02 (-0.184 [-0.232, -0.126]). So H1 is the most reliable 0.6B prompt (100% parse) but not the most accurate, and it did not lower hallucination. Full details, failed prompt designs and weak sections: `direct_inference_baseline/experiments/EXP_008_QWEN3_0.6B_HYBRID_P02_S1/README.md`.
**Side finding about the 1.7B P02 results above:** the frozen 1.7B P02 prompt contained 14 invented worked examples, and their content appears in 28 of 28 of its outputs (106 occurrences, for example "rest the shoulder" in 16 encounters, "hip pain" in 9). Those copied facts are counted as unsupported by the judge, so the 1.7B P02 precision and hallucination figures above are understated for the model's true ability. The prompt itself is frozen, so this is recorded, not corrected.

## 5. Limits — read before quoting any number
1. **One judge, not calibrated.** No human has checked the verdicts. Until the roughly 40-encounter calibration is done, state these as "gpt-5.4's assessment".
2. **Run-to-run variance is unmeasured.** The reasoning model accepts no temperature setting, so a re-run could shift the numbers slightly (the cache makes our own reruns identical).
3. **The "critical" flag is noisy.** In the review I saw it set on a fact whose only problem was an unstated route (aspirin "oral"). Treat the critical rate as an upper estimate and review the flagged facts by hand before any claim about patient safety.
4. **The judge is strict about attributes** such as route, indication and who reported the fact. That lowers precision for runs that add plausible but unstated details.
5. **Intervals are unpaired bootstraps over encounters.** A paired comparison (same encounters, run against run) would be sharper for P00/P01/P02 and has not been done.
6. **Small samples.** The 1.7B runs have 23–28 judged encounters, so intervals are wide.
7. **S1 and S1.1 outputs were adapted to the full schema by a deterministic adapter**; the judge scored the adapted form.
8. **1.7B outputs came from the Intel-GPU runs** and are scored as recorded, not re-generated on Azure CPU.
9. Synthetic data only; nothing real was sent to the judge.

## 6. Next steps (in order of value)
1. Human calibration on about 40 stratified encounters (judge vs human agreement, Cohen's kappa).
2. Deploy a stronger different-family second judge, run the 20% sample (`--judge JUDGE2 --every 5`), then `python -m judge_eval.aggregate --judge JUDGE --scope prompt_dev_set --agreement JUDGE2`.
3. Paired bootstrap for 1.7B P00/P01/P02.
4. Human review of all flagged critical facts.
5. Optionally judge the "extra" runs (EXP_005 repaired, P04 smoke).
6. After fine-tuning, score the new model with the same frozen rubrics on the same 30 encounters so the comparison is direct.

## 7. Reproduce
```
python -m judge_eval.inventory
python -m judge_eval.judge_run --judge JUDGE --runs all-core --scope own --workers 24     # resumable; results cached
python -m judge_eval.aggregate --judge JUDGE --scope prompt_dev_set                         # or validation_set / own
python -m pytest judge_eval/tests -q
```
Judge replies are cached in `judge_eval/cache/`, verdicts in `judge_eval/results/`, tables in `judge_eval/output/`. Settings come from `JUDGE_*` and `JUDGE2_*` in `.env`.
