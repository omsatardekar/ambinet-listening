# Running the fine-tuning on the VM

Files: `train_lora.py` (training), `generate_check.py` (generate and check outputs). Both use only transformers, peft and torch (no TRL). Tested on this laptop with a tiny random model on CPU (training step, validation, checkpoint save, resume, generation, `expand()`); the GPU parts (fp16, gradient checkpointing, memory) are verified by the pilot on the T4.

Always run inside the virtual environment: `source /data/finetune/venv/bin/activate`

## 1. Pilot (about 5-10 minutes)
```
python /data/finetune/finetune_scripts/train_lora.py --out /data/finetune/runs/pilot --max_steps 2 --eval_every 2 --eval_n 10 --save_every 2
```
Look at: `peak GPU` (must stay well under 15 GiB), `tok/s` (this gives the time of the full run: about 11.1 million tokens per pass divided by tok/s), `loss` (about 1 to 3 at the start, not `nan`), and `skipped 0`.

Then check generation speed and the output pipeline on 3 validation examples (an untrained 2-step adapter will probably not write valid JSON yet; we are measuring speed and that nothing crashes):
```
python /data/finetune/finetune_scripts/generate_check.py --adapter /data/finetune/runs/pilot/checkpoint_step2 --n 3
python /data/finetune/finetune_scripts/generate_check.py --adapter none --n 3
```

## 2. Full run (after the pilot looks healthy), inside tmux
```
tmux new -s train
source /data/finetune/venv/bin/activate
python /data/finetune/finetune_scripts/train_lora.py --out /data/finetune/runs/run1 --epochs 3
```
Detach with Ctrl+B then D; re-enter with `tmux attach -t train`. If it is interrupted, run the same command with `--resume` added. Checkpoints are saved every 100 optimizer steps in `/data/finetune/runs/run1/`, and `train_log.txt` has the full log. Validation loss (seen and unseen scenarios) is printed every 100 steps.

## 3. After training
Pick the checkpoint with the lowest **unseen** validation loss, then run `generate_check.py` on 60 validation examples. The locked test file is not used until the final evaluation.
