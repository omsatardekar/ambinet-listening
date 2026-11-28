"""Compact authoring format -> draft JSON -> compile_draft (same compiler/validator).  Pure bookkeeping: all dialogue and clinical content is authored.

Block format (one or more per .txt file):
## 00616 PATIENT=1 DOCTOR=2 NURSE=3        (roles uppercase; person ids person_N)
1: spoken text ~ cc s1                      (leading digit = speaker number; turns numbered implicitly; tags after ' ~ ' name the entities this turn supports; 'pause=12' adds silence before the turn)
2: spoken text ~ s1 pause=12
@@
{ ...label JSON... }                        (entities carry "k": "<tag>"; evidence_ids are built from tagged turns; or give "evidence_ids" explicitly)

Defaults filled in (override by giving the field): see DEFAULTS.   chief_complaint uses tag "cc".
usage: python dsl.py file.txt [--no-write]
"""
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import compile_draft as C  # noqa: E402

DEFAULTS = {
    "symptoms": {"status": "present", "temporality": "current", "certainty": "certain", "reported_by": "patient"},
    "negative_findings": {"status": "absent", "assertion": "negative", "temporality": "current", "reported_by": "patient"},
    "past_medical_history": {"status": "ongoing", "reported_by": "patient"},
    "surgical_history": {"reported_by": "patient"},
    "family_history": {"reported_by": "patient"},
    "social_history": {"status": "current", "reported_by": "patient"},
    "medications": {"status": "currently_used", "reported_by": "patient"},
    "allergies": {"allergy_type": "medication", "status": "reported", "reported_by": "patient"},
    "vital_signs": {"reported_by": "doctor"},
    "physical_examination": {"status": "present", "observed_by": "doctor"},
    "review_of_systems": {"status": "negative", "reported_by": "patient"},
    "clinical_conditions": {"status": "existing", "reported_by": "patient"},
    "clinical_assessment": {"certainty": "provisional", "stated_by": "doctor"},
    "procedures_and_investigations": {"status": "planned", "requested_by": "doctor"},
    "clinical_actions": {"status": "planned", "responsible_person": "doctor"},
    "follow_up": {"type": "consultation", "status": "planned"},
    "clinical_uncertainties": {"resolution_status": "unresolved"},
}
NORM_FROM = {"symptoms": ("name", "normalized_name"), "negative_findings": ("finding", "normalized_name"), "past_medical_history": ("condition", "normalized_condition"),
             "surgical_history": ("procedure", "normalized_procedure"), "family_history": ("condition", "normalized_condition"), "physical_examination": ("finding", "normalized_finding"),
             "clinical_conditions": ("name", "normalized_name"), "clinical_assessment": ("assessment", "normalized_assessment"),
             "procedures_and_investigations": ("name", "normalized_name"), "vital_signs": ("name", "normalized_name"), "chief_complaint": ("value", "normalized_value")}
SECTIONS = ["symptoms", "negative_findings", "medications", "allergies", "vital_signs", "physical_examination", "review_of_systems", "clinical_conditions",
            "clinical_assessment", "procedures_and_investigations", "clinical_actions", "follow_up", "clinical_uncertainties"]


def parse(text):
    blocks = []
    for chunk in re.split(r"(?m)^## ", text):
        chunk = chunk.strip("\n")
        if not chunk.strip():
            continue
        head, _, rest = chunk.partition("\n")
        parts = head.split()
        eid = parts[0]
        spk = {f"person_{p.split('=')[1]}": p.split("=")[0] for p in parts[1:]}
        dial, _, lab = rest.partition("\n@@")
        turns, tags = [], []
        for ln in dial.split("\n"):
            if not ln.strip():
                continue
            mm = re.match(r"^(\d)\s*:\s*(.*)$", ln.strip())
            if not mm:
                raise ValueError(f"{eid}: bad line {ln[:60]!r} (expected 'N: text ~ tags', N = speaker number)")
            body = mm.group(2)
            t, tg = body.rsplit(" ~ ", 1) if " ~ " in body else (body, "")
            pause = None
            tl = []
            for x in tg.split():
                if x.startswith("pause="):
                    pause = float(x[6:])
                else:
                    tl.append(x)
            sid, t = f"person_{mm.group(1)}", t
            turn = {"s": sid, "t": t.strip()}
            if pause:
                turn["pause"] = pause
            turns.append(turn)
            tags.append(tl)
        label = json.loads(lab) if lab.strip() else {}
        blocks.append((eid, spk, turns, tags, label))
    return blocks


def build(eid, spk, turns, tags, L):
    errs = []
    tm = {}
    for i, tl in enumerate(tags, 1):
        for k in tl:
            tm.setdefault(k, []).append(i)

    def fin(sec, e, loc):
        e = dict(e)
        for k, v in DEFAULTS.get(sec.split(".")[-1], {}).items():
            e.setdefault(k, v)
        if sec in NORM_FROM:
            a, b = NORM_FROM[sec]
            if a in e and b not in e:
                e[b] = e[a][:1].upper() + e[a][1:]
        if sec.split(".")[-1] == "medications" and "name" in e:
            e.setdefault("normalized_name", e["name"].title() if "cream" not in e["name"] else e["name"])
            e.setdefault("generic_name", e["normalized_name"])
        if sec == "allergies" and "substance" in e:
            e.setdefault("normalized_substance", e["substance"][:1].upper() + e["substance"][1:])
        if sec == "social_history":
            pass
        if sec == "negative_findings" and str(e.get("finding", "")).lower() == "allergies":
            e["finding"], e["normalized_name"] = "Allergies", "No known allergies"
        k = e.pop("k", None)
        if "evidence_ids" not in e:
            if k is None:
                errs.append(f"{loc}: needs \"k\" tag or evidence_ids")
            elif k not in tm:
                errs.append(f"{loc}: tag {k!r} is on no turn")
            else:
                e["evidence_ids"] = tm[k]
        return e

    L = dict(L)
    if "vitals" in L:     # shortcut: {"k":"v","by":"doctor","bp":"128/80","hr":68,"temp":36.6,"spo2":98,"rr":16,"wt":84,"ht":170,"bmi":29.1}
        v = L.pop("vitals")
        spec = [("bp", "Blood pressure", "Blood pressure", "mmHg"), ("hr", "Heart rate", "Heart rate", "bpm"), ("temp", "Temperature", "Body temperature", "°C"),
                ("spo2", "Oxygen saturation", "Oxygen saturation", "%"), ("rr", "Respiratory rate", "Respiratory rate", "breaths/min"),
                ("wt", "Weight", "Weight", "kg"), ("ht", "Height", "Height", "cm"), ("bmi", "BMI", "Body mass index", "kg/m²")]
        L["vital_signs"] = [{"k": v.get("k", "v"), "name": n, "normalized_name": nn, "value": v[key], "unit": u, "reported_by": v.get("by", "doctor")} for key, n, nn, u in spec if key in v] + L.get("vital_signs", [])
    if "allergy_none" in L:   # shortcut: explicit 'no known allergies' negative finding, tag given
        L["negative_findings"] = L.get("negative_findings", []) + [{"k": L.pop("allergy_none"), "finding": "Allergies", "normalized_name": "No known allergies"}]
    out = {}
    if "chief_complaint" in L:
        cc = dict(L["chief_complaint"])
        cc.setdefault("k", "cc")
        cc.setdefault("reported_by", "patient")
        out["chief_complaint"] = fin("chief_complaint", cc, "chief_complaint")
    for sec in SECTIONS:
        if sec in L:
            out[sec] = [fin(sec, e, f"{sec}[{i}]") for i, e in enumerate(L[sec])]
    # auto twin actions (only when no action with the same tag and type was written by hand)
    acts = out.setdefault("clinical_actions", [])
    have = {(a.get("k"), a["action_type"]) for a in L.get("clinical_actions", [])}
    for i, e in enumerate(L.get("procedures_and_investigations", [])):
        if e.get("status", "planned") in ("planned", "conditional") and (e.get("k"), "investigation") not in have and not e.get("noact"):
            acts.append(fin("clinical_actions", {"k": e["k"], "action_type": "investigation", "description": "Arrange " + e.get("normalized_name", e["name"]), "status": e.get("status", "planned")}, f"auto-action[{i}]"))
    for e in L.get("follow_up", []):
        if (e.get("k"), "follow_up") not in have:
            acts.append(fin("clinical_actions", {"k": e["k"], "action_type": "follow_up", "description": "Follow-up consultation", "status": e.get("status", "planned"),
                                                 "time_reference": {"value": e["time_reference"], "normalized_date": None}}, "auto-action[follow_up]"))
    for e in L.get("medications", []):
        if e.get("status") == "planned" and (e.get("k"), "medication") not in have:
            acts.append(fin("clinical_actions", {"k": e["k"], "action_type": "medication", "description": " ".join(x for x in ["Start", e.get("normalized_name") or e["name"].title(), e.get("dose"), e.get("frequency")] if x)}, "auto-action[med]"))
    for k, d in L.get("counsel", []):
        acts.append(fin("clinical_actions", {"k": k, "action_type": "counselling", "description": d, "status": "recommended", "responsible_person": "patient"}, "counsel"))
    if not acts:
        out.pop("clinical_actions")
    if "medical_history" in L:
        out["medical_history"] = {h: [fin(h, e, f"medical_history.{h}[{i}]") for i, e in enumerate(L["medical_history"][h])] for h in L["medical_history"]}
    if "quality_checks" in L:
        out["quality_checks"] = L["quality_checks"]
    return {"encounter_id": eid, "speakers": spk, "turns": turns, "label": out}, errs


def main():
    path = Path(sys.argv[1])
    write = "--no-write" not in sys.argv
    bad = 0
    for eid, spk, turns, tags, label in parse(path.read_text(encoding="utf-8")):
        d, errs = build(eid, spk, turns, tags, label)
        if errs:
            print(f"{eid}: FAIL (dsl)")
            for e in errs[:15]:
                print("  -", e)
            bad += 1
            continue
        dp = HERE / "drafts" / f"draft_{eid}.json"
        tmp = HERE / "drafts" / f".tmp_{eid}.json"
        tmp.write_text(json.dumps(d, indent=1, ensure_ascii=False), encoding="utf-8")
        inp, lab, cerrs = C.compile_draft(d)
        R = C.VD.validate_record(inp, lab)
        msgs = cerrs + [f"[{e['check']}] {e['message']}" for e in R.errors]
        n, dur = len(inp["segments"]), inp["segments"][-1]["end_seconds"] if inp["segments"] else 0
        if msgs:
            print(f"{eid}: FAIL turns={n} dur={dur}s")
            for m in msgs[:12]:
                print("  -", m)
            tmp.unlink()
            bad += 1
        else:
            tmp.replace(dp)
            if write:
                out = HERE / "staging" / "output"
                (out / "inputs").mkdir(parents=True, exist_ok=True)
                (out / "labels").mkdir(parents=True, exist_ok=True)
                (out / "inputs" / f"encounter_{eid}.json").write_text(json.dumps(inp, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                (out / "labels" / f"encounter_{eid}.json").write_text(json.dumps(lab, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print(f"{eid}: PASS turns={n} dur={dur}s")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
