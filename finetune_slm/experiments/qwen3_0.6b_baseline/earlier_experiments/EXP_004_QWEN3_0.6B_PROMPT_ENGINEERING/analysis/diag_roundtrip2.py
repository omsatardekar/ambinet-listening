import json, sys, types, copy
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
from direct_inference_baseline.evaluation.entity_matching import norm_text
from evidence_builder import build_evidence, entity_locations
mm = lambda s: f"{int(s)//60:02d}:{int(s)%60:02d}"
n=0
for eid in load_split("development"):
    g = ER.load_gold(eid); t = json.loads((S.INPUT_DIR/f"encounter_{eid}.json").read_text(encoding="utf-8")); segs=t["segments"]
    seg_of={e["evidence_id"]:[s["segment_id"] for s in segs if norm_text(s["text"])==norm_text(e["transcript_text"]) and s["speaker_id"]==e["speaker_id"] and mm(s["start_seconds"])==e["start_timestamp"]][0] for e in g["clinical_evidence"]}
    inter=copy.deepcopy(g)
    for loc,ent in entity_locations(inter): ent["source_segments"]=[seg_of[x] for x in ent.pop("evidence_ids",[])]
    inter.pop("clinical_evidence")
    out,rep=build_evidence(inter,t)
    a,b=g["clinical_evidence"],out["clinical_evidence"]
    if len(a)!=len(b) or any(x["evidence_id"]!=y["evidence_id"] or x["transcript_text"]!=y["transcript_text"] for x,y in zip(a,b)):
        print(eid,len(a),len(b),rep["ids_invalid"],rep["ids_truncated_over_cap"],rep["ids_duplicate_removed"])
        for x,y in list(zip(a,b))[:40]:
            if x["transcript_text"]!=y["transcript_text"]: print(' gold',x["evidence_id"],x["transcript_text"][:40],'| built',y["evidence_id"],y["transcript_text"][:40]); break
        n+=1
        if n>=3: break
