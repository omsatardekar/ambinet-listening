# Round 6: a short last try, counselling lists capped at 4 (synthetic, model-written, not clinician reviewed)

Written before any result. Follows round 5 (docs/08_TRAINING_ROUND5.md, section 5.1): every unfinished output of round 5 ends inside the `counselling` items of `clinical_actions`; natural labels have up to 13, round 1 at most 4.

## Idea (from the team)
The plan part of the note holds tests, scans, referrals, medicines and follow-up. General advice ("sleep well, eat well") is shown by the backend as a **small separate section of recommendations, at most 4**, not mixed into the plan. So the labels the model learns from carry at most 4 counselling items. Only `clinical_actions` items with `action_type` "counselling" are capped (the first 4 in the order written); the schema is unchanged and nothing else is edited. The UI/backend separation of recommendations from the plan is a separate change and is not part of this experiment.

## Data (`run6/`, script `scripts/local/round5_build/build_round6_capped.py`)
Training 984 lines = 384 natural examples (once each, from rounds 2 and 4, cleaned as in round 5; 101 of them had more than 4 counselling items, 176 items removed) + 600 round-1 examples. Validation 313 = the round-5 validation with the natural labels capped the same way. The held-out families and the 20 scenarios are not trained on. `run6/build_stats.json` has the counts.

## Training (decided now)
Continue the **round-5 step-220 adapter** (`--init_adapter runs/run5/checkpoint_step220`) for **50 optimizer steps** (800 examples, about 0.8 passes) at **lr 3e-5**, validation and checkpoint every 10 steps. About 1.8 hours. Then generation on the 44 windows for checkpoint 50 (about 1 hour); the whole-conversation run and the locked test only if the windows pass. Total about 3 hours.

**Limits stated before the run.** The extra 50 steps are also extra training, so a gain cannot be attributed to the cap alone. The cap removes real advice from the labels on purpose; the recommendations section is the place for it. One seed. Round 5's precision (0.639) is far below step 400's (0.730), and 50 steps may not close that gap; the cap is expected to help with loops, less certainly with precision.

## The bar (set now, same judge and frozen prompts, 20 scenarios on windows)
Step 400: precision 0.730, recall 0.562, hallucination 0.206, critical 0.050, 0 windows the guard cannot repair. Round 6 passes only if at least 42 of 44 windows end normally, no metric is worse than step 400 by more than 0.01, and precision or recall is better by at least 0.03. Otherwise step 400 stays and this is written up as the last experiment.

## Run on the VM
Laptop (PowerShell):
```
cd d:\ambient_clinical_speech_transcription\ambient_clinical_speech_transcription
ssh -i $HOME\.ssh\qwen_vm azureuser@20.83.185.94 "mkdir -p /data/finetune/round6"
scp -i $HOME\.ssh\qwen_vm finetune_slm\data\round6_capped_counselling\run6\train_run6.jsonl finetune_slm\data\round6_capped_counselling\run6\validation_run6.jsonl azureuser@20.83.185.94:/data/finetune/round6/
scp -i $HOME\.ssh\qwen_vm finetune_slm\scripts\to_gpu_vm\run_round6.sh azureuser@20.83.185.94:/data/finetune/finetune_scripts/
```
VM: `bash /data/finetune/finetune_scripts/run_round6.sh train` (in tmux), then `bash /data/finetune/finetune_scripts/run_round6.sh gen`.

## Final result (2026-11-28): not used, step 400 stays
128 minutes of training. Windows: 32 of 44 ended normally (bar 42); judge precision 0.621, recall 0.614, hallucination 0.303, critical 0.078 against step 400 0.730 / 0.562 / 0.206 / 0.050. The counselling cap did not fix the loops or the precision loss. See `docs/09_TRAINING_ROUND6.md`.
