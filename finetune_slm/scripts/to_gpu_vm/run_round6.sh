#!/usr/bin/env bash
# Round 6 (a short last try): continue the round-5 step-220 adapter for 50 steps on the data with counselling lists capped at 4.
#   bash /data/finetune/finetune_scripts/run_round6.sh train      # about 1.8 hours (start inside tmux or with nohup)
#   bash /data/finetune/finetune_scripts/run_round6.sh resume     # after an interruption
#   bash /data/finetune/finetune_scripts/run_round6.sh gen        # windows (44) for checkpoint 50, then the full text (20) only if you pass "full" as 2nd argument
set -euo pipefail
cd /data/finetune
source venv/bin/activate
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
INIT=runs/run5/checkpoint_step220
COMMON="--train round6/train_run6.jsonl --val round6/validation_run6.jsonl --max_len 6144 --lr 3e-5 --epochs 1 --init_adapter $INIT --out runs/run6 --max_steps 50 --eval_every 10 --save_every 10"
case "${1:-}" in
  train|resume)
    for f in round6/train_run6.jsonl round6/validation_run6.jsonl $INIT/adapter_model.safetensors; do [ -f "$f" ] || { echo "missing $f"; exit 1; }; done
    [ "$(wc -l < round6/train_run6.jsonl)" = "984" ] || { echo "train file should have 984 lines"; exit 1; }
    if [ "$1" = resume ]; then python finetune_scripts/train_lora.py $COMMON --resume 2>&1 | tee -a run6.log; else python finetune_scripts/train_lora.py $COMMON 2>&1 | tee run6.log; fi ;;
  gen)
    python finetune_scripts/generate_check.py --adapter runs/run6/checkpoint_step50 --data round4/module3_windows.jsonl --n 44 --batch 2 --sort --save runs/m3_win_run6_step50_outputs 2>&1 | tee runs/m3_win_run6_step50.log
    if [ "${2:-}" = full ]; then python finetune_scripts/generate_check.py --adapter runs/run6/checkpoint_step50 --data round4/module3_recordings.jsonl --n 20 --batch 2 --sort --save runs/m3_run6_step50_outputs 2>&1 | tee runs/m3_run6_step50.log; fi ;;
  *) echo "usage: run_round6.sh train|resume|gen [full]"; exit 1 ;;
esac
