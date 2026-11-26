"""Runs the REAL converted OpenVINO model through the scoring pipeline (bundle score.py) on CPU, for the baseline encounters, and compares with the PyTorch step-400 raw outputs.
  <openvino env python> finetune_slm/deployment/source/local_ov_test.py --model D:\...\ov_step400_fp16 --out finetune_slm/runs/round1_step400/ov_cpu --n 30"""
import argparse, json, os, re, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]                    # repository root
ap = argparse.ArgumentParser(); ap.add_argument("--model", required=True); ap.add_argument("--out", required=True); ap.add_argument("--n", type=int, default=30); ap.add_argument("--device", default="CPU")
a = ap.parse_args()
sys.path.insert(0, str(ROOT / "finetune_slm" / "deployment" / "source" / os.environ.get("SCORE_BUNDLE", "code_bundle"))); os.environ["AZUREML_MODEL_DIR"] = a.model; os.environ["OV_DEVICE"] = a.device
import score
score._state.update(model_dir=score._find_model_dir(), device=a.device, ready=True)
assert score._sha256(score._find_model_dir() / "openvino_model.bin") == score.EXPECTED_WEIGHTS_SHA256, "weights hash"
ids = sorted(p.stem.replace("encounter_", "") for p in (ROOT / "finetune_slm/experiments/qwen3_0.6b/EXP_008_QWEN3_0.6B_HYBRID_P02_S1/outputs/H1_main30/parsed_predictions/H1_main30").glob("encounter_*.json"))[: a.n]
out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
for eid in ids:
    if (out / f"{eid}_summary.json").exists(): continue
    compact = json.loads((ROOT / "finetune_slm/data/round1_synthetic/test/raw_inputs" / f"encounter_{eid}.json").read_text(encoding="utf-8")) if (ROOT / "finetune_slm/data/round1_synthetic/test/raw_inputs" / f"encounter_{eid}.json").exists() else json.loads((ROOT / "finetune_slm/archive/dataset_v2_batch_001_corrected/output/inputs" / f"encounter_{eid}.json").read_text(encoding="utf-8"))
    cap = {}
    def gen(prompt, sample=False):
        g = score._generate(prompt, sample); cap["raw"] = g["text"]; return g
    t0 = time.time(); res = score.run_extraction(compact, generate=gen); wall = time.time() - t0
    (out / f"{eid}_2_model_raw.json").write_text(cap["raw"], encoding="utf-8")
    if res["ok"]: (out / f"{eid}_3_model_full.json").write_text(json.dumps(res["extraction"], indent=1, ensure_ascii=False), encoding="utf-8")
    ref = ROOT / "finetune_slm/runs/round1_step400/test_step400_outputs" / f"{eid}_2_model_raw.json"
    same = ref.exists() and ref.read_text(encoding="utf-8") == cap["raw"]
    s = {"id": eid, "ok": res["ok"], "status": res["metadata"]["extraction_status"] if res["ok"] else "failed", "same_text_as_pytorch": same, "in_tokens": res["metadata"]["input_tokens"], "out_tokens": res["metadata"]["output_tokens"], "seconds": round(wall, 1)}
    (out / f"{eid}_summary.json").write_text(json.dumps(s), encoding="utf-8"); print(json.dumps(s), flush=True)
