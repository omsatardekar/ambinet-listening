# Round 5: cleaned mixed data, trained once from the BASE model (synthetic, model-written, not clinician reviewed)

Written before any round-5 result exists. The plan and the bar below are fixed now.

## Question
Rounds 2, 3 and 4 each continued from an earlier adapter with a few hundred model-written labels, and each time recall rose while precision fell (docs/07_TRAINING_ROUND4.md, section 9). Two suspects are tested together:
1. **Label noise** (the verifier marked some facts unsupported or partial). Round 5 removes those facts from the labels.
2. **Stacking** small rounds on step 400. Round 5 trains **once, from the base model**, on round-1 and natural data mixed.

If it does not beat step 400, step 400 stays and this is a documented experiment.

## What is in the training file (`run5/train_run5.jsonl`, 2,668 lines)
| Part | Unique | Lines | Note |
|---|---|---|---|
| Round-1 synthetic | 1,900 | 1,900 | all 628 ids that round 1 had repeated (rare scenarios) + a random fill |
| Natural encounters of round 2 | 102 | 204 | cleaned labels, each twice |
| Targeted encounters of round 4 | 282 | 564 | cleaned labels, each twice |

Natural examples are repeated twice because they are few; they make up 29% of the lines, close to round 2's share (about 27%). Validation `run5/validation_run5.jsonl` = 250 round-1 + 63 natural held-out (families of round 2 and round 4 never trained on) = 313. No id of the 20 hand-written scenarios or of the locked test is in either file. `run5/build_stats.json` holds the counts.

### Label cleaning (`scripts/local/round5_build/build_round5_dataset.py`)
For every natural encounter the verifier's list of doubtful facts (`verify.bad`: unsupported, partially supported, contradicted) is removed from the label, which is then re-compacted; nothing else is edited. 423 of 13,660 facts were removed in the training part (376 partial, 34 unsupported, 13 contradicted): **about 3%**. An encounter is used only when it has at most 1 critical omission, at most 6 doubtful facts (at most 2 contradicted, at most 2 critical), the round-4 automatic rules (`validate_labels.check_record`) find nothing in the cleaned label, and prompt + answer are at most 18,000 characters. Excluded: 197 for critical omissions, 242 by the automatic rules (most of them from round 2, which had not been checked by those rules), 108 for length, 1 for too many doubtful facts, 5 unverified.

**Limit that matters:** the verifier found only about 3% of facts doubtful, so this tests label noise only as far as that verifier sees it. If the verifier misses mistakes the writer model also makes, they stay in the labels. No clinician reviewed anything.

## Training plan
Start from the **base model** (`--init_adapter` not used). LoRA rank 64 / alpha 128 / dropout 0.05, all projections (as round 1). Learning rate 1e-4, warm-up 3%, cosine decay to 1e-5, accumulation 16, maximum length 6,144, **220 optimizer steps** (3,520 examples, about 1.3 passes over the file), validation and checkpoint every 20 steps. Round 1's loss curves fell together until about step 250 of 654, so 220 steps from the base are expected to reach the early plateau, but this is **about 55% of the compute of round 1 up to step 400 and cannot be called equal**. If round 5 is worse than step 400 it may simply be less trained; the checkpoints at steps 140, 180 and 220 show the trend.

Estimated time about 7 hours (about 13 million tokens at about 520 tokens per second); steps with natural examples are longer. Compute about Rs 400 at Rs 58 per hour (an estimate).

## The bar (set now)
On the 20 hand-written scenarios, same judge and frozen prompts as step 400:
* **Full text** (step 400: precision 0.762, recall 0.558, hallucination 0.168, critical 0.048, 20 of 20 valid): 20 of 20 ended normally without loops, and no metric worse than step 400 by more than 0.01, and precision **or** recall better by at least 0.03 (about the noise of 20 scenarios).
* **Windows** (step 400: 0.730 / 0.562 / 0.206 / 0.050): the same rule.
* **Locked test (973)**: judge-F1 not below about 0.93, and hallucination not above about 0.03.
Otherwise step 400 stays. Before any decision, the noise of the judge is measured (bootstrap over the 20 scenarios) so differences are read against it.

## Final result (2026-11-28): not used, step 400 stays
Trained 220 steps (420 min), checkpoint 220 tested. Whole conversation: 9 of 20 ended normally (11 repaired by the guard); windows: 28 of 44 ended normally (all 16 others repaired). Judge on windows: precision 0.639, recall 0.621, hallucination 0.288, critical 0.080, against step 400 0.730 / 0.562 / 0.206 / 0.050. The bar was not met. The unfinished outputs end inside the counselling list of `clinical_actions`; the natural labels have up to 13 counselling items against at most 4 in round 1 (a likely cause, not proven). Full report: `docs/08_TRAINING_ROUND5.md`.

## Run on the VM
Laptop (PowerShell):
```
cd d:\ambient_clinical_speech_transcription\ambient_clinical_speech_transcription
ssh -i $HOME\.ssh\qwen_vm azureuser@20.83.185.94 "mkdir -p /data/finetune/round5"
scp -i $HOME\.ssh\qwen_vm finetune_slm\data\round5_clean_mix\run5\train_run5.jsonl finetune_slm\data\round5_clean_mix\run5\validation_run5.jsonl azureuser@20.83.185.94:/data/finetune/round5/
scp -i $HOME\.ssh\qwen_vm finetune_slm\scripts\to_gpu_vm\run_round5.sh finetune_slm\scripts\to_gpu_vm\train_lora.py azureuser@20.83.185.94:/data/finetune/finetune_scripts/
```
VM: `bash /data/finetune/finetune_scripts/run_round5.sh pilot`, then in tmux (or nohup) `bash /data/finetune/finetune_scripts/run_round5.sh full`. After an interruption: `... resume`.
After training, generation uses `generate_check.py` as for round 4 (20 full-text scenarios and 44 windows, then the judge).
