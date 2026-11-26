"""List (a) gold facts where R_cons v2 cited a segment that is NOT gold-cited (zero-inference), and (b) a few full texts from the review sample."""
import json, sys, types
from pathlib import Path
try:
    import dotenv
except ImportError:
    sys.modules["dotenv"] = types.SimpleNamespace(load_dotenv=lambda *a, **k: False)
sys.dont_write_bytecode = True
EXP4 = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(EXP4/"experiments")); sys.path.insert(0, str(EXP4.parents[2]))
from common import S, SPLIT
from direct_inference_baseline.evaluation import evaluation_runner as ER
from direct_inference_baseline.evaluation.entity_matching import CATEGORIES, entity_list, norm_text
import p05_retrieval as R
mm = lambda s: f"{int(s)//60:02d}:{int(s)%60:02d}"
n = 0; rows = []
for eid in SPLIT["prompt_dev_ids"]:
    tr = json.loads((S.INPUT_DIR/f"encounter_{eid}.json").read_text(encoding="utf-8")); segs = tr["segments"]; enc = R.Enc(segs); g = ER.load_gold(eid)
    seg_of = {}
    for r in g.get("clinical_evidence", []):
        t = norm_text(r["transcript_text"]); h = [i for i, s in enumerate(segs) if t == norm_text(s["text"]) and s["speaker_id"] == r["speaker_id"] and mm(s["start_seconds"]) == r["start_timestamp"]]
        seg_of[r["evidence_id"]] = h[0] if h else None
    for c in CATEGORIES:
        for e in entity_list(g, c):
            G = {seg_of[x] for x in (e.get("evidence_ids") or []) if seg_of.get(x) is not None}
            if not G: continue
            d = R.retrieve(c, e, enc, R.STEPS_V2)
            if d["decision"] == "cited" and not (set(d["segments"]) & G):
                key = next((str(e.get(k)) for k in ("normalized_name","normalized_value","normalized_condition","normalized_procedure","normalized_finding","normalized_substance","normalized_assessment","system","category","description","name","finding","time_reference") if e.get(k)), "")
                rows.append((eid, c, key[:40], [(segs[i]["segment_id"], enc.role[i][:3], segs[i]["text"][:80]) for i in d["segments"]], [(segs[i]["segment_id"], enc.role[i][:3], segs[i]["text"][:80]) for i in sorted(G)][:3]))
print("cited-but-not-gold-cited:", len(rows))
for r in rows: print(r[0], r[1], "|", r[2], "\n   R:", r[3], "\n   G:", r[4])
