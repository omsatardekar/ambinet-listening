"""Seeded sample of Arm R (R_main) selections for qualitative reading. prompt_dev only; reads final outputs and transcripts; no labels."""
import json, random, sys, types
from pathlib import Path
try:
    import dotenv
except ImportError:
    sys.modules["dotenv"] = types.SimpleNamespace(load_dotenv=lambda *a, **k: False)
sys.dont_write_bytecode = True
EXP4 = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(EXP4/"experiments")); sys.path.insert(0, str(EXP4.parents[2]))
from common import S, SPLIT
from evidence_builder import entity_locations
rng = random.Random(20260414)
rows = []
for eid in SPLIT["prompt_dev_ids"]:
    f = json.loads((EXP4/"arm_R"/"R_main"/"final_predictions"/f"encounter_{eid}.json").read_text(encoding="utf-8"))
    ch = json.loads((EXP4/"arm_R"/"R_main"/"retrieval_choices"/f"encounter_{eid}.json").read_text(encoding="utf-8"))
    tr = json.loads((S.INPUT_DIR/f"encounter_{eid}.json").read_text(encoding="utf-8")); seg = {s["segment_id"]: s for s in tr["segments"]}
    for loc, e in entity_locations(f):
        key = next((str(e.get(k)) for k in ("normalized_name","normalized_value","normalized_condition","normalized_procedure","normalized_finding","normalized_substance","normalized_assessment","system","category","description","name","finding","value","time_reference") if e.get(k)), "")
        s = seg.get(ch[loc]["segment"]) if ch[loc]["segment"] else None
        rows.append({"id": eid, "loc": loc, "key": key[:70], "score": ch[loc]["score"], "seg": ch[loc]["segment"], "who": (f"{s['speaker_id']}/{s['role']}" if s else None), "text": (s["text"][:150] if s else None)})
by = {}
for r in rows: by.setdefault(r["loc"].split("[")[0], []).append(r)
sample = []
for c in sorted(by): sample += rng.sample(by[c], min(2, len(by[c])))
rng.shuffle(sample); sample = sample[:30]
(EXP4/"arm_R"/"R_main_qualitative_sample_30.json").write_text(json.dumps(sample, indent=1, ensure_ascii=False), encoding="utf-8")
for r in sample[:16]: print(r["id"], r["loc"], "|", r["key"], "| score", r["score"], "|", r["seg"], r["who"], "|", r["text"])
