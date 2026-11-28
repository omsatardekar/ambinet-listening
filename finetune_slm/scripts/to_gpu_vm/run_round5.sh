#!/usr/bin/env bash
# Round 5 on the T4 VM: train from the BASE model on the cleaned mixed set (no --init_adapter).
#   bash /data/finetune/finetune_scripts/run_round5.sh pilot     # 2 steps, about 6 minutes: checks memory, speed, loss
#   bash /data/finetune/finetune_scripts/run_round5.sh full      # 220 steps, about 7 hours (start inside tmux or with nohup)
#   bash /data/finetune/finetune_scripts/run_round5.sh resume    # after an interruption: same run, continues from its last checkpoint
set -euo pipefail
cd /data/finetune
source venv/bin/activate
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
for f in round5/train_run5.jsonl round5/validation_run5.jsonl finetune_scripts/train_lora.py; do [ -f "$f" ] || { echo "missing $f"; exit 1; }; done
[ "$(wc -l < round5/train_run5.jsonl)" = "2668" ] || { echo "train file should have 2668 lines"; exit 1; }
COMMON="--train round5/train_run5.jsonl --val round5/validation_run5.jsonl --max_len 6144 --lr 1e-4 --epochs 2"
case "${1:-}" in
  pilot)  python finetune_scripts/train_lora.py $COMMON --out runs/pilot5 --max_steps 2 --eval_every 2 --eval_n 10 --save_every 2 2>&1 | tee pilot5.log ;;
  full)   python finetune_scripts/train_lora.py $COMMON --out runs/run5 --max_steps 220 --eval_every 20 --save_every 20 2>&1 | tee run5.log ;;
  resume) python finetune_scripts/train_lora.py $COMMON --out runs/run5 --max_steps 220 --eval_every 20 --save_every 20 --resume 2>&1 | tee -a run5.log ;;
  *) echo "usage: run_round5.sh pilot|full|resume"; exit 1 ;;
esac
