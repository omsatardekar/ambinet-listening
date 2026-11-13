import json, sys, types, collections
from pathlib import Path
try:
    import dotenv
except ImportError:
    sys.modules["dotenv"] = types.SimpleNamespace(load_dotenv=lambda *a, **k: False)
sys.dont_write_bytecode = True
EXP4 = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(EXP4/"experiments")); sys.path.insert(0, str(EXP4.parents[2]))
from direct_inference_baseline.evaluation import evaluation_runner as ER
from direct_inference_baseline.evaluation.dataset_split import load_split
from evidence_builder import entity_locations
c = collections.Counter(); ex = []
for eid in load_split("development"):
    g = ER.load_gold(eid)
    cited = {x for _, e in entity_locations(g) for x in (e.get("evidence_ids") or [])}
    for r in g["clinical_evidence"]:
        c["records"] += 1
        if r["evidence_id"] not in cited:
            c["record_not_cited_by_any_entity"] += 1
            if len(ex) < 3: ex.append((eid, r["evidence_id"], r["supports"], r["transcript_text"][:50]))
        if not r["supports"]: c["supports_empty"] += 1
    # entities listed by locations vs all items in gold
    n_all = sum(len(g.get(s) or []) for s in ["symptoms","negative_findings","medications","allergies","vital_signs","physical_examination","review_of_systems","clinical_conditions","clinical_assessment","procedures_and_investigations","clinical_actions","follow_up","clinical_uncertainties"]) + sum(len(v) for v in g["medical_history"].values()) + 1
    c["items_all"] += n_all; c["items_walked"] += len(entity_locations(g))
print(dict(c), ex)
