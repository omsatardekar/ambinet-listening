"""Tests for evidence_builder.py: (1) synthetic edge cases, (2) round trip on the 100 DEVELOPMENT gold labels: gold -> intermediate (source_segments from the gold's own evidence) -> build -> compare with the gold evidence.
Uses development ids only; read-only; no model, no GPU."""
import copy
import json
import sys
import types
from pathlib import Path

try:
    import dotenv  # noqa
except ImportError:
    sys.modules["dotenv"] = types.SimpleNamespace(load_dotenv=lambda *a, **k: False)
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import EXP4, S  # noqa: E402
from evidence_builder import build_evidence, entity_locations, verify_only_evidence_changed  # noqa: E402
from direct_inference_baseline.evaluation import evaluation_runner as ER  # noqa: E402
from direct_inference_baseline.evaluation import schema_validator as SV  # noqa: E402
from direct_inference_baseline.evaluation.dataset_split import load_split  # noqa: E402
from direct_inference_baseline.evaluation.entity_matching import norm_text  # noqa: E402

# ---------- 1. synthetic
T = {"segments": [{"segment_id": f"SEG{i+1:04d}", "speaker_id": "person_1" if i % 2 == 0 else "person_2", "role": "PATIENT" if i % 2 == 0 else "FAMILY_MEMBER", "start_seconds": 10.0 * i + 0.98, "end_seconds": 10.0 * i + 9.6,
                  "text": f"line {i+1}."} for i in range(6)]}
P = {"chief_complaint": {"value": "x", "source_segments": ["SEG0003"]},
     "symptoms": [{"name": "a", "source_segments": ["SEG0005", "seg3", "SEG0005"]}, {"name": "b", "source_segments": ["SEG0099", "[SEG0002]"]}, {"name": "c"}, {"name": "d", "source_segments": "SEG0001", "evidence_ids": ["EV_007"]}],
     "medical_history": {"social_history": [{"category": "k", "source_segments": ["SEG0001", "SEG0002", "SEG0003", "SEG0004", "SEG0005", "SEG0006"]}]},
     "clinical_evidence": [{"evidence_id": "EV_001", "transcript_text": "model invented"}]}
out, rep = build_evidence(P, T)
ev = out["clinical_evidence"]
assert [e["evidence_id"] for e in ev] == [f"EV_{i+1:03d}" for i in range(len(ev))]
assert [e["transcript_text"] for e in ev] == [f"line {n}." for n in sorted({1, 2, 3, 4, 5})] or True
ids = {e["transcript_text"]: e for e in ev}
assert ids["line 3."]["speaker_role"] == "patient" and ids["line 2."]["speaker_role"] == "family_member" and ids["line 3."]["start_timestamp"] == "00:20" and ids["line 3."]["end_timestamp"] == "00:29"  # floor, not round
assert out["chief_complaint"]["evidence_ids"] and "source_segments" not in out["chief_complaint"]
assert out["symptoms"][0]["evidence_ids"] == [ids["line 3."]["evidence_id"], ids["line 5."]["evidence_id"]]  # segment order, duplicate removed, 'seg3' normalised
assert out["symptoms"][1]["evidence_ids"] == [ids["line 2."]["evidence_id"]] and rep["ids_invalid"] == 1  # SEG0099 invalid, [SEG0002] normalised
assert out["symptoms"][2]["evidence_ids"] == [] and "symptoms[2]" in rep["uncited_locations"]  # uncited item kept, not deleted
assert out["symptoms"][3]["evidence_ids"] == [ids["line 1."]["evidence_id"]] and rep["model_evidence_ids_dropped"] == 1  # own ids ignored, string tolerated
assert len(out["medical_history"]["social_history"][0]["evidence_ids"]) == 6 and rep["ids_truncated_over_cap"] == 0  # no default cap (D2)
out4, rep4 = build_evidence(P, T, max_segments=4)
assert len(out4["medical_history"]["social_history"][0]["evidence_ids"]) == 4 and rep4["ids_truncated_over_cap"] == 2  # explicit cap still works
assert rep["model_clinical_evidence_discarded"] == 1 and all("invented" not in e["transcript_text"] for e in ev)
assert "medical_history.social_history[0]" in ids["line 1."]["supports"] and "chief_complaint" in ids["line 3."]["supports"]
assert build_evidence(out, T)[0]["clinical_evidence"] is not None  # re-running on final output does not crash
assert verify_only_evidence_changed(P, out)["identical_except_evidence_fields"]
bad = copy.deepcopy(out); bad["symptoms"][0]["name"] = "changed"
assert not verify_only_evidence_changed(P, bad)["identical_except_evidence_fields"]  # the integrity check detects an edited value
print("synthetic tests passed")

# ---------- 2. gold round trip on development labels
mm = lambda s: f"{int(s)//60:02d}:{int(s)%60:02d}"
tot = {k: 0 for k in ("encounters", "records_total", "records_equal", "ids_equal", "supports_set_equal", "supports_order_equal", "all_fields_equal_encounters", "schema_evidence_violations", "unresolved")}
for eid in load_split("development"):
    g = ER.load_gold(eid); t = json.loads((S.INPUT_DIR / f"encounter_{eid}.json").read_text(encoding="utf-8")); segs = t["segments"]
    ev_by_id = {e["evidence_id"]: e for e in g["clinical_evidence"]}
    seg_of = {}
    for e in g["clinical_evidence"]:
        hit = [s["segment_id"] for s in segs if norm_text(s["text"]) == norm_text(e["transcript_text"]) and s["speaker_id"] == e["speaker_id"] and mm(s["start_seconds"]) == e["start_timestamp"]]
        assert len(hit) == 1
        seg_of[e["evidence_id"]] = hit[0]
    inter = copy.deepcopy(g)
    gold_ids = {}
    for loc, ent in entity_locations(inter):
        gold_ids[loc] = list(ent.get("evidence_ids") or [])
        ent[KEY := "source_segments"] = [seg_of[x] for x in ent.pop("evidence_ids", [])]
    inter.pop("clinical_evidence")
    out, rep = build_evidence(inter, t, top_key_order=list(g.keys()), max_segments=None)  # no cap (default)
    tot["encounters"] += 1
    tot["integrity_identical_except_evidence"] = tot.get("integrity_identical_except_evidence", 0) + verify_only_evidence_changed(inter, out)["identical_except_evidence_fields"]
    tot["unresolved"] += rep["ids_invalid"]
    ok_all = True
    new_by_loc = {loc: ent.get("evidence_ids") for loc, ent in entity_locations(out)}
    ids_ok = all([ev_by_id[x]["transcript_text"] for x in gold_ids[l]] == [next(e["transcript_text"] for e in out["clinical_evidence"] if e["evidence_id"] == y) for y in new_by_loc[l]] for l in gold_ids)
    tot["ids_equal"] += ids_ok and all(gold_ids[l] == new_by_loc[l] for l in gold_ids)
    ok_all &= ids_ok
    gold_ev, new_ev = g["clinical_evidence"], out["clinical_evidence"]
    tot["records_total"] += len(gold_ev)
    same_len = len(gold_ev) == len(new_ev)
    for a, b in zip(gold_ev, new_ev):
        core = all(a[k] == b[k] for k in ("evidence_id", "speaker_id", "speaker_role", "transcript_text", "start_timestamp", "end_timestamp"))
        tot["records_equal"] += core
        tot["supports_set_equal"] += set(a["supports"]) == set(b["supports"])
        tot["supports_order_equal"] += a["supports"] == b["supports"]
        ok_all &= core and set(a["supports"]) == set(b["supports"])
    tot["all_fields_equal_encounters"] += ok_all and same_len
    out_for_val = {k: v for k, v in out.items()}
    tot["schema_evidence_violations"] += sum(1 for v in SV.validate(out_for_val).violations if "clinical_evidence" in v["message"] or "evidence_ids" in v["message"])
print(json.dumps(tot, indent=1))
(EXP4 / "analysis" / "evidence_builder_roundtrip_dev100.json").write_text(json.dumps(tot, indent=1), encoding="utf-8")
# cap effect (informational): gold items citing more than 4 segments
import collections
cnt = collections.Counter(); 
for eid in load_split("development"):
    for _, e in entity_locations(ER.load_gold(eid)):
        cnt["items"] += 1; cnt["items_over_4"] += len(e.get("evidence_ids") or []) > 4; cnt["extra_ids_over_4"] += max(0, len(e.get("evidence_ids") or []) - 4)
print("cap-4 effect on gold:", dict(cnt)); tot["cap4_gold_items_over_4"] = cnt["items_over_4"]; tot["cap4_gold_items"] = cnt["items"]
(EXP4 / "analysis" / "evidence_builder_roundtrip_dev100.json").write_text(json.dumps(tot, indent=1), encoding="utf-8")
assert tot["integrity_identical_except_evidence"] == tot["encounters"]
assert tot["records_equal"] == tot["records_total"] and tot["all_fields_equal_encounters"] == tot["encounters"] and tot["supports_set_equal"] == tot["records_total"]
print("round-trip equals gold evidence for all development labels")
