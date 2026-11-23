"""EXP_004 P03: determine the dataset's seconds -> MM:SS convention (development labels + inputs only, read-only; format convention only, no content is used)."""
import json, math, re, sys, types
from collections import Counter
from pathlib import Path
try:
    import dotenv
except ImportError:
    sys.modules["dotenv"] = types.SimpleNamespace(load_dotenv=lambda *a, **k: False)
sys.dont_write_bytecode = True
EXP4 = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(EXP4.parents[2]))
from direct_inference_baseline.config import settings as S
from direct_inference_baseline.evaluation import evaluation_runner as ER
from direct_inference_baseline.evaluation.dataset_split import load_split
from direct_inference_baseline.evaluation.entity_matching import norm_text
def mmss(x): return f"{int(x)//60:02d}:{int(x)%60:02d}"
c = Counter(); frac = Counter(); examples = []
for eid in load_split("development"):
    tr = json.loads((S.INPUT_DIR / f"encounter_{eid}.json").read_text(encoding="utf-8"))
    for r in ER.load_gold(eid).get("clinical_evidence", []):
        t = norm_text(r.get("transcript_text"))
        seg = [s for s in tr["segments"] if t and t == norm_text(s["text"]) and s["speaker_id"] == r.get("speaker_id")]
        if not seg: c["no_exact_segment_match"] += 1; continue
        s = seg[0]; c["records_matched"] += 1
        for kind, sec, ts in (("start", s["start_seconds"], r["start_timestamp"]), ("end", s["end_seconds"], r["end_timestamp"])):
            c["fields"] += 1
            for nm, fn in (("floor", math.floor), ("round_half_up", lambda v: math.floor(v + 0.5)), ("ceil", math.ceil), ("python_round", round)):
                c[nm] += ts == mmss(fn(sec))
            f = round(sec - math.floor(sec), 2)
            if mmss(math.floor(sec)) != ts and len(examples) < 5: examples.append((sec, ts))
            # fractional-part discrimination: records where floor and round differ
            if f >= 0.5:
                c["frac_ge_0.5_fields"] += 1
                c["frac_ge_0.5_match_floor"] += ts == mmss(math.floor(sec))
                c["frac_ge_0.5_match_round"] += ts == mmss(math.floor(sec + 0.5))
print(dict(c)); print("floor mismatches (seconds, label):", examples)
json.dump({"counts": dict(c), "floor_mismatch_examples": examples}, open(EXP4/"analysis"/"timestamp_convention_dev.json", "w"), indent=1)
