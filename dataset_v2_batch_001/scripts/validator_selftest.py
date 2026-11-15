"""Negative controls: deliberately corrupt valid records and confirm the validator rejects them.
Run:  python scripts/validator_selftest.py"""
import copy, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "validation"))
import validate_dataset as VD

def load(i):
    return (json.loads((ROOT / f"output/inputs/encounter_{i}.json").read_text(encoding="utf-8")),
            json.loads((ROOT / f"output/labels/encounter_{i}.json").read_text(encoding="utf-8")))

def first(lab, path):
    o = lab
    for p in path.split("."): o = o[p]
    return o

def mutations():
    def m_dose(i, l):  # change a dose that was spoken
        for m in l["medications"]:
            if m["dose"]: m["dose"] = "999 mg"; return True
    def m_ts(i, l): i["segments"][5]["end_seconds"] = i["segments"][5]["start_seconds"] - 1; return True
    def m_overlap(i, l): i["segments"][6]["start_seconds"] = i["segments"][5]["start_seconds"]; return True
    def m_evtext(i, l): l["clinical_evidence"][2]["transcript_text"] += " extra"; return True
    def m_evspk(i, l): l["clinical_evidence"][1]["speaker_id"] = "person_9"; return True
    def m_support(i, l): l["clinical_evidence"][0]["supports"].append("symptoms[99]"); return True
    def m_noev(i, l): l["symptoms"][0]["evidence_ids"] = []; return True
    def m_name(i, l): l["symptoms"][0]["name"] = "Totally invented symptom"; return True
    def m_sev(i, l):
        for s in l["symptoms"]:
            if s["severity"] is None: s["severity"] = "severe"; return True
    def m_role(i, l): i["segments"][1]["role"] = "ROBOT"; return True
    def m_confirmed(i, l):
        if l["clinical_assessment"]: l["clinical_assessment"][0]["certainty"] = "confirmed"; return True
    def m_neg(i, l):
        if l["negative_findings"] and l["symptoms"]:
            l["negative_findings"][0]["normalized_name"] = l["symptoms"][0]["normalized_name"]; return True
    def m_leak(i, l): i["complexity"] = "challenging"; return True
    def m_dur(i, l):
        for s in l["symptoms"]:
            if s["duration"]: s["duration"]["value"] = 41; return True
    def m_vital(i, l):
        for v in l["vital_signs"]:
            if v["name"] == "Heart rate": v["value"] = 250; return True
    return dict(dose=m_dose, negative_time=m_ts, overlap=m_overlap, evidence_text=m_evtext, evidence_speaker=m_evspk,
                dangling_support=m_support, missing_evidence=m_noev, invented_symptom=m_name, invented_severity=m_sev,
                bad_role=m_role, confirmed_dx=m_confirmed, negation_contradiction=m_neg, blueprint_leak=m_leak,
                wrong_duration=m_dur, implausible_vital=m_vital)

caught = missed = n_na = 0
rows = []
for name, fn in mutations().items():
    hit = False
    for eid in ["%05d" % k for k in range(1, 120)]:
        i, l = load(eid); i, l = copy.deepcopy(i), copy.deepcopy(l)
        if fn(i, l):
            R = VD.validate_record(i, l)
            hit = True
            ok = bool(R.errors)
            rows.append((name, eid, "CAUGHT" if ok else "MISSED"))
            caught += ok; missed += (not ok)
            break
    if not hit: n_na += 1; rows.append((name, "-", "not applicable"))
for r in rows: print(*r)
print(f"caught {caught}, missed {missed}, not applicable {n_na}")
sys.exit(1 if missed else 0)
