# Round 4 targeted dataset (synthetic, model-written, model-verified, not clinician reviewed)

Purpose: teach the 0.6B extraction model the specific mistakes seen in the live tests of step 400 (docs/11): reason for visit taken from a remark, review of systems that was never asked, a doctor's explanation stored as a patient symptom, "if needed" on booked tests, flipped or misplaced negatives, sentences copied from speech into name fields, a penicillin "allergy" the patient denied, wrong or prior vital values.

## Layout
| Path | Content |
|---|---|
| `raw/<id>.json` | one encounter: spec (situation + target traps), transcript lines, full and compact label, verifier result (`verify`), automatic checks (`auto_checks`) |
| `run4/` | the training and validation files built from the accepted encounters (created by `build_round4_dataset`) |

Scripts: `finetune_slm/scripts/local/targeted_gen/` (`blueprints.py` situations and traps, `generate_targeted.py`, `validate_labels.py`, `build_round4_dataset.py`). Verification re-uses `natural_gen/verify_natural.py`.

## Pipeline
1. `generate_targeted` - writer model (JUDGE2) writes the conversation and the label for a situation plus one or two traps (480 encounters planned, ids 40001-40480; each spec has its own seed-fixed family, traps, speakers and style).
2. `verify_natural --raw finetune_slm/data/round4_targeted/raw` - a different model (JUDGE) checks every fact against the transcript and lists omissions; one repair round by the writer.
3. `validate_labels` - the backend rules (`clinical_extraction/safety_checks.py`, `postprocess.py`) reject a label with a contradicted allergy, an allergy against a same-family medicine, a vital number not in its cited turns, a sentence-like symptom name or chief complaint, a contradicted negative, or a review-of-systems entry whose cited turns hold no doctor question.
4. `build_round4_dataset` - accepted + automatic checks passed + length limit; held-out families are never trained on; a replay sample of round-1 training examples is added.

## Not allowed to leak
The 20 hand-written scenarios (`scenarios/`) and the locked test (973) are evaluation data. The situations here were chosen to differ from the 20 scenario themes.

## Training plan (decided before the result)
Start from the step-400 adapter (`--init_adapter finetune_slm/models/adapters/round1_step400`), low learning rate (3e-5), 3 epochs (changed from 2 after the build: only 250 targeted examples survived, so each is seen three times; checkpoints every 25 steps let us also judge the epoch-1 and epoch-2 states), `--max_len 6144`, validation and checkpoints every 25 steps. Pre-set bar for deployment, on the 20 natural scenarios with the same judge as step 400 (precision 0.762, recall 0.558, hallucination 0.168, critical 0.048, 20/20 valid JSON): precision at least 0.76, hallucination at most 0.168, recall at least 0.58, 20/20 valid JSON without loops, locked-test judge-F1 not below about 0.93. Otherwise step 400 stays.

## Result of the data build (2026-11-27 01:20)
471 of 480 planned encounters were written (9 failed to convert); 470 verified (1 blocked by the verifier's content filter); the model verifier accepted 381; the automatic checks rejected a further 59 (most often a symptom or finding name of 7 or more words, then a vital number not in its cited turns, an allergy denied in its own turns, a chief complaint written as a sentence); 26 more were left out for length (limit 18,000 characters of prompt + answer).
**Training file `run4/train_run4.jsonl`: 250 targeted encounters + 350 replayed round-1 examples = 600. Validation `run4/validation_run4.jsonl`: 250 round-1 + 46 targeted held-out = 296.** The 7 held-out situation families are never trained on.
Nothing here is clinician reviewed.

## Final result (2026-11-27): not used, step 400 stays
Trained 114 steps (218 min), checkpoints 75 and 114 generated. Whole-conversation test: only 10 of 20 outputs ended normally. Windows, step 114: 42 of 44 ended normally; judged precision 0.691, recall 0.651, hallucination 0.237, critical 0.070, against step 400 0.730 / 0.562 / 0.206 / 0.050. The bar (precision at least 0.73, hallucination at most 0.206) was not met. Full report: `docs/07_TRAINING_ROUND4.md`.

## Run on the VM (after the pilot)
```
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
python /data/finetune/finetune_scripts/train_lora.py --train /data/finetune/round4/train_run4.jsonl --val /data/finetune/round4/validation_run4.jsonl \n  --init_adapter /data/finetune/runs/run1/checkpoint_step400 --out /data/finetune/runs/pilot4 --max_steps 2 --eval_every 2 --eval_n 10 --save_every 2 --max_len 6144   # PILOT FIRST (5-10 min)
python /data/finetune/finetune_scripts/train_lora.py \
  --train /data/finetune/round4/train_run4.jsonl --val /data/finetune/round4/validation_run4.jsonl \
  --init_adapter /data/finetune/runs/run1/checkpoint_step400 --out /data/finetune/runs/run4 \
  --epochs 3 --lr 3e-5 --max_len 6144 --eval_every 25 --save_every 25
```
About 113 optimizer steps (37-38 per epoch of 16), roughly 4 hours at the round-2 speed of 2.1 minutes per step.
