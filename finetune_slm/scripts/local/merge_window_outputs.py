"""Merge the per-window model outputs of the chunking experiment into one output folder per encounter, ready for judge_eval.m3_judge.

  python finetune_slm/scripts/local/merge_window_outputs.py --windows finetune_slm/runs/round2_natural_and_windows/m3_win_step156 --index finetune_slm/data/module3_eval_inputs/module3_windows_index.json --out finetune_slm/runs/round2_natural_and_windows/m3_win_step156_merged
"""
import argparse, glob, json, os, shutil, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "finetune_slm", "scripts", "shared")); sys.path.insert(0, os.path.join(ROOT, "finetune_slm/data/round1_synthetic", "codec"))
from json_guard import parse_with_repair
from compact_codec import expand
from finetune_slm.scripts.shared.chunking import merge
ap = argparse.ArgumentParser()
ap.add_argument("--windows", required=True); ap.add_argument("--index", required=True); ap.add_argument("--out", required=True)
a = ap.parse_args()
index = json.load(open(a.index))
shutil.rmtree(a.out, ignore_errors=True); os.makedirs(a.out)
stat = {"windows": 0, "failed_windows": 0, "repaired_windows": 0}
for eid, ws in index.items():
    parts = []
    for k, w in enumerate(ws, 1):
        f = os.path.join(a.windows, f"{eid}__w{k}_2_model_raw.json")
        stat["windows"] += 1
        obj, notes = parse_with_repair(open(f, encoding="utf-8").read()) if os.path.exists(f) else (None, ["missing"])
        if obj is None:
            stat["failed_windows"] += 1; print("FAILED window", eid, k, notes[-1:]); continue
        stat["repaired_windows"] += bool(notes)
        parts.append(({"to_global": w["to_global"]}, expand(obj)))
    if not parts:
        continue
    merged = merge(parts)
    merged["encounter_id"] = eid
    json.dump(merged, open(os.path.join(a.out, f"{eid}_3_model_full.json"), "w", encoding="utf-8"), ensure_ascii=False)
print(stat)
