import json, sys, types, collections
from pathlib import Path
try:
    import dotenv
except ImportError:
    sys.modules["dotenv"] = types.SimpleNamespace(load_dotenv=lambda *a, **k: False)
sys.dont_write_bytecode = True
EXP4 = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(EXP4/"experiments")); sys.path.insert(0, str(EXP4.parents[2]))
from common import S
from direct_inference_baseline.evaluation import evaluation_runner as ER
from direct_inference_baseline.evaluation.dataset_split import load_split
from evidence_builder import entity_locations
c = collections.Counter()
for eid in load_split("development"):
    g = ER.load_gold(eid); segs = json.loads((S.INPUT_DIR/f"encounter_{eid}.json").read_text(encoding="utf-8"))["segments"]
    pos = {s["segment_id"]: i for i, s in enumerate(segs)}
    evseg = {}
    for r in g["clinical_evidence"]:
        for i, s in enumerate(segs):
            if s["text"] == r["transcript_text"] and s["speaker_id"] == r["speaker_id"] and f"{int(s['start_seconds'])//60:02d}:{int(s['start_seconds'])%60:02d}" == r["start_timestamp"]:
                evseg[r["evidence_id"]] = i
    for loc, e in entity_locations(g):
        for x in e.get("evidence_ids") or []:
            c["cited_ids"] += 1; c["cites_seg1"] += evseg[x] == 0; c["cites_first2"] += evseg[x] <= 1
            if loc == "chief_complaint": c["cc_ids"] += 1; c["cc_cites_first2"] += evseg[x] <= 1; c["cc_pos_sum"] += evseg[x]
print(dict(c)); print("gold share of cited ids in first 2 segments:", round(c["cites_first2"]/c["cited_ids"],3), "chief complaint:", round(c["cc_cites_first2"]/c["cc_ids"],3), "mean cc segment index", round(c["cc_pos_sum"]/c["cc_ids"],1))
