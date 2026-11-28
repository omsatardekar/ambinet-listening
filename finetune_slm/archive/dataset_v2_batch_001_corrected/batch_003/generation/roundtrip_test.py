"""Self-test: turn real Batch 001 records back into drafts and check the compiler reproduces the label (except timestamps, which are re-timed)."""
import json, sys, glob
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import compile_draft as C
ROOT = C.ROOT
bad = tested = 0
for f in sorted(glob.glob(str(ROOT / "output/inputs/*.json")))[:500:5]:
    inp = json.load(open(f)); lab = json.load(open(f.replace("inputs", "labels")))
    seg_of = {}
    for i, s in enumerate(inp["segments"]):
        seg_of[(s["speaker_id"], s["text"], s["start_seconds"] // 1)] = i + 1
    ev2turn = {}
    for e in lab["clinical_evidence"]:
        c = [i + 1 for i, s in enumerate(inp["segments"]) if s["speaker_id"] == e["speaker_id"] and s["text"] == e["transcript_text"] and C.VD.ts(s["start_seconds"]) == e["start_timestamp"]]
        ev2turn[e["evidence_id"]] = c[0]
    def conv(o):
        if isinstance(o, dict):
            return {k: ([ev2turn[x] for x in v] if k == "evidence_ids" else conv(v)) for k, v in o.items() if k not in ("confidence", "role_confidence")}
        if isinstance(o, list):
            return [conv(x) for x in o]
        return o
    L = {k: conv(lab[k]) for k in ["chief_complaint", "symptoms", "negative_findings", "medical_history", "medications", "allergies", "vital_signs",
                                   "physical_examination", "review_of_systems", "clinical_conditions", "clinical_assessment", "procedures_and_investigations",
                                   "clinical_actions", "follow_up", "clinical_uncertainties"]}
    L["quality_checks"] = {"contradictions_detected": lab["quality_checks"]["contradictions_detected"], "ambiguous_entities": lab["quality_checks"]["ambiguous_entities"]}
    d = {"encounter_id": inp["encounter_id"], "speakers": {s["speaker_id"]: s["role"] for s in inp["segments"]},
         "turns": [{"s": s["speaker_id"], "t": s["text"]} for s in inp["segments"]], "label": L}
    ni, nl, errs = C.compile_draft(d)
    tested += 1
    strip = lambda l: json.loads(json.dumps({k: v for k, v in l.items() if k != "clinical_evidence"}))
    ok = not errs and strip(nl) == strip(lab) and [(e["evidence_id"], e["transcript_text"], e["supports"]) for e in nl["clinical_evidence"]] == [(e["evidence_id"], e["transcript_text"], e["supports"]) for e in lab["clinical_evidence"]]
    R = C.VD.validate_record(ni, nl)
    if not ok or R.errors:
        bad += 1; print(inp["encounter_id"], "MISMATCH" if not ok else "", errs[:2], [e["message"][:80] for e in R.errors[:2]])
print(f"round-trip: tested {tested}, mismatches {bad}")
