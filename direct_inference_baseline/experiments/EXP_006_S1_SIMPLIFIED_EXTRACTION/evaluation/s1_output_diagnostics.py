"""Post-hoc diagnostics of the S1 parsed outputs (reads only EXP_006/outputs/parsed; no transcript, label or validation file).
usage: python -B s1_output_diagnostics.py  -> evaluation/S1_OUTPUT_DIAGNOSTICS.json"""
import json
from collections import Counter
from pathlib import Path

E6 = Path(__file__).resolve().parent.parent
P = E6 / "outputs" / "parsed" / "S1_dev50"
LISTS = ["symptoms", "negative_findings", "medical_history", "current_conditions", "surgical_history", "family_history", "social_history", "medications", "allergies",
         "vital_signs", "physical_examination", "review_of_systems", "clinical_assessment", "investigations", "procedures", "clinical_actions", "follow_up"]
CORE = {"symptoms": "name", "negative_findings": "finding", "medical_history": "condition", "current_conditions": "condition", "surgical_history": "procedure",
        "family_history": "condition", "social_history": "category", "medications": "name", "allergies": "substance", "vital_signs": "name",
        "physical_examination": "finding", "review_of_systems": "system", "clinical_assessment": "assessment", "investigations": "name", "procedures": "name",
        "clinical_actions": "description", "follow_up": "when"}
recs = [json.loads(f.read_text(encoding="utf-8")) for f in sorted(P.glob("encounter_*.json"))]
items = Counter(); blank_core = Counter(); rb_total = 0; rb_blank = 0; rb_vals = Counter()
cc_present = 0; allergy_status = Counter(); keys_missing = Counter()
for r in recs:
    if str(r.get("chief_complaint", "")).strip():
        cc_present += 1
    if "chief_complaint" not in r:
        keys_missing["chief_complaint"] += 1
    allergy_status[str(r.get("allergy_status", "<missing>"))] += 1
    for k in LISTS:
        v = r.get(k)
        if not isinstance(v, list):
            continue
        for it in v:
            if not isinstance(it, dict):
                continue
            items[k] += 1
            if not str(it.get(CORE[k], "")).strip():
                blank_core[k] += 1
            if "reported_by" in it:
                rb_total += 1
                x = str(it["reported_by"]).strip()
                rb_vals[x or "<blank>"] += 1
                rb_blank += (x == "")
out = {"records_parsed": len(recs), "records_with_non_empty_chief_complaint": cc_present, "records_missing_chief_complaint_key": keys_missing["chief_complaint"],
       "allergy_status_values": dict(allergy_status), "items_by_section": dict(items), "items_with_blank_primary_field_by_section": dict(blank_core),
       "items_total": sum(items.values()), "items_blank_primary_total": sum(blank_core.values()),
       "reported_by_fields": rb_total, "reported_by_blank": rb_blank, "reported_by_values": dict(rb_vals)}
(E6 / "evaluation" / "S1_OUTPUT_DIAGNOSTICS.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
print(json.dumps(out, indent=1))
