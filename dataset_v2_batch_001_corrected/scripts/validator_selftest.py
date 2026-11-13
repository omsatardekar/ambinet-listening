"""Negative controls: deliberately corrupt valid records and confirm the validator rejects every corruption.
Run:  python scripts/validator_selftest.py   (exit code 1 if any corruption goes undetected)"""
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "validation"))
import validate_dataset as VD  # noqa: E402


def load(i):
    return (json.loads((ROOT / f"output/inputs/encounter_{i}.json").read_text(encoding="utf-8")),
            json.loads((ROOT / f"output/labels/encounter_{i}.json").read_text(encoding="utf-8")))


def M():
    def fever_present_when_only_negative(i, l):
        if l["negative_findings"]:
            n = l["negative_findings"][0]
            l["symptoms"].append({"name": n["finding"], "normalized_name": n["normalized_name"], "category": "constitutional", "status": "present",
                                  "severity": None, "duration": None, "frequency": None, "onset": None, "temporality": "current", "body_site": None,
                                  "associated_symptoms": [], "aggravating_factors": [], "relieving_factors": [], "reported_by": "patient",
                                  "certainty": "certain", "evidence_ids": list(n["evidence_ids"]), "confidence": None})
            return True

    def dose_invented(i, l):
        for m in l["medications"]:
            if m["dose"] is None and m["status"] == "currently_used":
                m["dose"] = "20 mg"
                return True

    def allergy_reaction_invented(i, l):
        for a in l["allergies"]:
            if a["reaction"] is None and a["status"] == "reported":
                a["reaction"] = "anaphylaxis"
                return True

    def caregiver_attributed_to_patient(i, l):
        ev = {r["evidence_id"]: r["speaker_role"] for r in l["clinical_evidence"]}
        for p in ("medications", "symptoms", "allergies"):
            for e in l[p]:
                if e["reported_by"] in ("caregiver", "family_member") and "patient" not in {ev[x] for x in e["evidence_ids"]}:
                    e["reported_by"] = "patient"
                    return True

    def historical_symptom_labelled_current(i, l):
        for s in l["symptoms"]:
            if s["temporality"] == "past":
                s["temporality"] = "current"
                s["status"] = "present"
                return True

    def investigation_completed_when_only_planned(i, l):
        for p in l["procedures_and_investigations"]:
            if p["status"] == "planned":
                p["status"] = "completed"
                return True

    def unsupported_diagnosis(i, l):
        if l["clinical_assessment"]:
            e = copy.deepcopy(l["clinical_assessment"][0])
            e["assessment"] = "myocardial infarction"
            e["normalized_assessment"] = "Myocardial infarction"
            l["clinical_assessment"].append(e)
            return True

    def disagreement_converted_to_certainty(i, l):
        for k, u in enumerate(l["clinical_uncertainties"]):
            if u["type"] == "medication_discrepancy":
                ref = u["related_entities"][0]
                idx = int(ref.split("[")[1].rstrip("]"))
                m = l["medications"][idx]
                import re
                m["dose"] = re.search(r"patient states ([\d.]+ \w+)", u["description"]).group(1)   # silently pick the patient's version
                u["type"] = "date_uncertain"
                return True

    def disputed_symptom_made_certain(i, l):
        for s in l["symptoms"]:
            if s["certainty"] == "disputed":
                s["certainty"] = "certain"
                return True

    def invalid_evidence_reference(i, l):
        l["symptoms"][0]["evidence_ids"] = ["EV_999"]
        return True

    def incorrect_category(i, l):
        for s in l["symptoms"]:
            if s["normalized_name"].lower() in VD._NC and "cardiovascular" not in VD._NC[s["normalized_name"].lower()]:
                s["category"] = "cardiovascular"
                return True

    def category_misused_for_attribution(i, l):
        l["symptoms"][0]["category"] = "reported"
        return True

    def arbitrary_confidence(i, l):
        l["symptoms"][0]["confidence"] = 0.97
        return True

    def role_confidence_invented(i, l):
        l["encounter_metadata"]["primary_speakers"][0]["role_confidence"] = 0.98
        return True

    def confirmed_by_field_present(i, l):
        if l["clinical_conditions"]:
            l["clinical_conditions"][0]["confirmed_by"] = "doctor"
            return True

    def negative_allergy_when_never_discussed(i, l):
        if not l["allergies"] and not any(n["finding"] == "Allergies" for n in l["negative_findings"]) \
                and not any("allerg" in s["text"].lower() for s in i["segments"]):
            e = l["clinical_evidence"][1]
            l["negative_findings"].append({"finding": "Allergies", "normalized_name": "No known allergies", "status": "absent", "assertion": "negative",
                                           "reported_by": e["speaker_role"], "temporality": "current", "evidence_ids": [e["evidence_id"]], "confidence": None})
            e["supports"].append(f"negative_findings[{len(l['negative_findings']) - 1}]")
            return True

    def allergy_discussed_but_dropped(i, l):
        k = [n for n in l["negative_findings"] if n["finding"] == "Allergies"]
        if k:
            for r in l["clinical_evidence"]:
                r["supports"] = [x for x in r["supports"] if not x.startswith("negative_findings[%d]" % l["negative_findings"].index(k[0]))] or r["supports"][:0]
            l["negative_findings"].remove(k[0])
            return True

    def evidence_text_altered(i, l):
        l["clinical_evidence"][2]["transcript_text"] += " extra"
        return True

    def speaker_misattributed_in_evidence(i, l):
        l["clinical_evidence"][1]["speaker_id"] = "person_9"
        return True

    def overlapping_segments(i, l):
        i["segments"][6]["start_seconds"] = i["segments"][5]["start_seconds"]
        return True

    def blueprint_leak(i, l):
        i["complexity"] = "challenging"
        return True

    def duration_invented(i, l):
        for s in l["symptoms"]:
            if s["duration"] and s["duration"].get("value") is not None:
                s["duration"]["value"] = 41
                return True

    return dict(locals())


caught = missed = na = 0
rows = []
for name, fn in M().items():
    if not callable(fn):
        continue
    hit = False
    for k in range(1, 501):
        eid = f"{k:05d}"
        i, l = load(eid)
        i, l = copy.deepcopy(i), copy.deepcopy(l)
        if fn(i, l):
            R = VD.validate_record(i, l)
            ok = bool(R.errors)
            rows.append((name, eid, "CAUGHT" if ok else "MISSED", sorted({e["check"] for e in R.errors})[:3]))
            caught += ok
            missed += (not ok)
            hit = True
            break
    if not hit:
        na += 1
        rows.append((name, "-", "not applicable (no suitable record)", []))
for r in rows:
    print(*r)
print(f"caught {caught}, missed {missed}, not applicable {na}")
Path(ROOT / "validation" / "negative_controls.json").write_text(json.dumps([{"control": r[0], "record": r[1], "result": r[2], "checks_triggered": r[3]} for r in rows], indent=1), encoding="utf-8")
sys.exit(1 if missed else 0)
