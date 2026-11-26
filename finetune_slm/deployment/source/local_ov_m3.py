"""Runs the REAL converted OpenVINO model through the scoring pipeline (bundle score.py, with windows) on CPU for some of the 20 hand-written scenarios.
  <openvino env python> finetune_slm/deployment/source/local_ov_m3.py --model D:\...\ov_step156_fp16 --out finetune_slm/runs/round2_natural_and_windows/ov_cpu_m3 --n 4
Output folder holds <id>_3_model_full.json, ready for judge_eval.m3_judge, and <id>_summary.json."""
import argparse, json, os, re, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]                    # repository root
ap = argparse.ArgumentParser(); ap.add_argument("--model", required=True); ap.add_argument("--out", required=True); ap.add_argument("--n", type=int, default=4); ap.add_argument("--ids", default="")
a = ap.parse_args()
sys.path.insert(0, str(ROOT / "finetune_slm" / "deployment" / "source" / os.environ.get("SCORE_BUNDLE", "code_bundle"))); os.environ["AZUREML_MODEL_DIR"] = a.model; os.environ["OV_DEVICE"] = "CPU"
import score
score._state.update(model_dir=score._find_model_dir(), device="CPU", ready=True)
assert score._sha256(score._find_model_dir() / "openvino_model.bin") == score.EXPECTED_WEIGHTS_SHA256, "weights hash"
LINE = re.compile(r"^\[(SEG\d{4})\] (person_\d+) \(([A-Z_]+)\): (.*)$")
recs = [json.loads(l) for l in open(ROOT / "finetune_slm/data/module3_eval_inputs/module3_recordings.jsonl", encoding="utf-8")]
want = a.ids.split(",") if a.ids else None
recs = [r for r in recs if (r["id"] in want)] if want else recs[: a.n]
out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
for r in recs:
    eid = r["id"]
    if (out / f"{eid}_summary.json").exists(): continue
    segs = [dict(zip(("segment_id", "speaker_id", "role", "text"), m.groups())) for l in r["messages"][0]["content"].splitlines() if (m := LINE.match(l))]
    for i, s in enumerate(segs): s["start_seconds"], s["end_seconds"] = float(i * 5), float(i * 5 + 4)
    t0 = time.time(); res = score.run_extraction({"encounter_id": eid, "segments": segs}); wall = time.time() - t0
    if res["ok"]: (out / f"{eid}_3_model_full.json").write_text(json.dumps(res["extraction"], ensure_ascii=False), encoding="utf-8")
    m = res["metadata"]
    s = {"id": eid, "ok": res["ok"], "status": m["extraction_status"], "windows": m["windows"], "failed_windows": m["failed_windows"], "needs_review": m["needs_review"],
         "in_tokens": m["input_tokens"], "out_tokens": m["output_tokens"], "seconds": round(wall, 1), "notes": m["guard_notes"][:3]}
    (out / f"{eid}_summary.json").write_text(json.dumps(s), encoding="utf-8"); print(json.dumps(s), flush=True)
