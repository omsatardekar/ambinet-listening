"""EXP_004 read-only pattern analysis of one run vs P00 on the same ids (violation patterns, empty sections, entity counts, speaker/evidence).
usage: analyze_run_patterns.py <run_id> <subset>.  Uses the existing schema validator on already-parsed predictions; no labels, no inference."""
import json
import re
import sys
from collections import Counter

from common import EXP3, EXP4, SPLIT, S, use_run, write_json
from direct_inference_baseline.evaluation import schema_validator as SV

run_id, subset = sys.argv[1:3]
IDS = {"prompt_dev": SPLIT["prompt_dev_ids"], "validation": SPLIT["validation_ids"]}[subset]
SECTIONS = ["symptoms", "negative_findings", "medications", "allergies", "vital_signs", "physical_examination", "review_of_systems", "clinical_conditions", "clinical_assessment",
            "procedures_and_investigations", "clinical_actions", "follow_up", "clinical_uncertainties", "clinical_clinical_evidence"]
SECTIONS[-1] = "clinical_evidence"
MH = ["past_medical_history", "surgical_history", "family_history", "social_history"]


def load(d, eid):
    p = d / f"encounter_{eid}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def pattern(msg):
    return re.sub(r"\[\d+\]", "[]", msg)


def analyse(parsed_dir):
    pats, kinds, empty, n_items, nvalid, tot_items = Counter(), Counter(), Counter(), Counter(), 0, 0
    obj_sections, roles_bad, ev_per_enc, ev_missing_supports = Counter(), 0, [], 0
    for eid in IDS:
        pred = load(parsed_dir, eid)
        if pred is None:
            continue
        nvalid += 1
        rep = SV.validate(pred)
        for v in getattr(rep, "violations", []):
            k, m = (v["kind"], v["message"]) if isinstance(v, dict) else (v[0], v[1])
            kinds[k] += 1
            pats[(k, pattern(m))] += 1
        for sec in SECTIONS:
            val = pred.get(sec)
            if isinstance(val, list):
                n_items[sec] += len(val)
                tot_items += len(val)
                if not val:
                    empty[sec] += 1
            elif isinstance(val, dict):
                obj_sections[sec] += 1
            elif val is None:
                empty[sec] += 1
        mh = pred.get("medical_history") or {}
        for sec in MH:
            val = mh.get(sec) if isinstance(mh, dict) else None
            if isinstance(val, list):
                n_items[sec] += len(val)
                tot_items += len(val)
                if not val:
                    empty[sec] += 1
            else:
                empty[sec] += 1
        ev = pred.get("clinical_evidence")
        if isinstance(ev, list):
            ev_per_enc.append(len(ev))
            ev_missing_supports += sum(1 for e in ev if isinstance(e, dict) and "supports" not in e)
        meta = pred.get("encounter_metadata") or {}
        if not (isinstance(meta, dict) and meta.get("primary_speakers")):
            obj_sections["primary_speakers_missing"] += 1
    return {"valid_records": nvalid, "violation_kinds": dict(kinds), "top_patterns": [[list(k), c] for k, c in pats.most_common(25)], "empty_sections_count_of_records": dict(empty),
            "total_items": tot_items, "items_per_valid_record": round(tot_items / max(1, nvalid), 1), "items_by_section": dict(n_items), "sections_emitted_as_object": dict(obj_sections),
            "evidence_records_mean": round(sum(ev_per_enc) / max(1, len(ev_per_enc)), 2), "evidence_without_supports": ev_missing_supports}


new = analyse(EXP4 / "outputs" / run_id / "parsed_predictions" / run_id)
old = analyse(EXP3 / "parsed_predictions" / "exp_003_dev_100") if (EXP3 / "parsed_predictions" / "exp_003_dev_100").exists() else None
write_json(EXP4 / "evaluation" / run_id / "pattern_analysis.json", {"run": new, "p00_same_ids": old})
print(json.dumps({"run": new, "p00": old}, indent=1))
