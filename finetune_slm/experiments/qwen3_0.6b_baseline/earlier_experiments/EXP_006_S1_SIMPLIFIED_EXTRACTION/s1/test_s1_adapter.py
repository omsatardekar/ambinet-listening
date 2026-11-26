"""Unit tests for the S1 adapter (synthetic data only; no project transcript, label or validation file is opened except the frozen schema validator module).
usage (project env): python -B test_s1_adapter.py"""
import copy
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
EXP6 = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(EXP6.parent / "EXP_004_QWEN3_0.6B_PROMPT_ENGINEERING" / "experiments"))
import s1_adapter as A  # noqa: E402
from common import S  # noqa: E402,F401
from direct_inference_baseline.evaluation import schema_validator as SV  # noqa: E402
from direct_inference_baseline.evaluation.entity_matching import CATEGORIES, entity_list  # noqa: E402

EMPTY = {k: ([] if k in A.S1_LISTS else "") for k in A.S1_KEYS}
EMPTY["encounter_id"] = "T1"
EMPTY["allergy_status"] = "not_asked"
fails = []


def check(n, c):
    print(("PASS " if c else "FAIL ") + n)
    if not c:
        fails.append(n)


def mk(**kw):
    d = copy.deepcopy(EMPTY)
    d.update(kw)
    return d


FULL = mk(chief_complaint="heel pain", symptoms=[{"name": "heel pain", "status": "present", "duration": "two weeks", "reported_by": "patient"}, {"name": "fever", "status": "resolved", "duration": "", "reported_by": "patient"}],
          negative_findings=[{"finding": "chest pain", "reported_by": "patient"}], medical_history=[{"condition": "diabetes", "duration": "about ten years", "reported_by": "patient"}], current_conditions=[{"condition": "hypertension", "reported_by": "doctor"}],
          surgical_history=[{"procedure": "appendectomy", "when": "years ago", "reported_by": "patient"}], family_history=[{"condition": "asthma", "relation": "brother", "reported_by": "patient"}],
          social_history=[{"category": "smoking", "status": "never", "detail": "", "reported_by": "patient"}],
          medications=[{"name": "metformin", "dose": "500 milligrams", "route": "", "frequency": "twice a day", "status": "current", "reported_by": "patient"}, {"name": "metoprolol", "dose": "50 milligrams", "route": "oral", "frequency": "", "status": "new", "reported_by": "doctor"}],
          allergy_status="reported", allergies=[{"substance": "penicillin", "reaction": "rash", "reported_by": "patient"}], vital_signs=[{"name": "blood pressure", "value": "120/80", "unit": "", "reported_by": "nurse"}, {"name": "pulse", "value": "84", "unit": "bpm", "reported_by": "nurse"}],
          physical_examination=[{"finding": "swelling", "body_site": "right knee", "reported_by": "doctor"}], review_of_systems=[{"system": "urinary", "details": "", "reported_by": "patient"}],
          clinical_assessment=[{"assessment": "plantar fasciitis", "certainty": "provisional"}], investigations=[{"name": "foot x-ray", "type": "imaging", "status": "planned"}], procedures=[{"name": "dressing", "status": "done"}],
          clinical_actions=[{"type": "counselling", "description": "stretch the calf"}, {"type": "medication", "description": "start metoprolol"}], follow_up=[{"when": "in two weeks", "status": "planned"}])
orig = copy.deepcopy(FULL)
out, probs = A.adapt(FULL)
check("input never modified", FULL == orig)
check("full example: no adapter problems and S1 format valid", not probs and not A.validate_s1(FULL))
check("names and values copied unchanged", out["medications"][0]["name"] == "metformin" and out["medications"][0]["dose"] == "500 milligrams" and out["medications"][1]["dose"] == "50 milligrams" and out["symptoms"][0]["name"] == "heel pain")
check("doses stay with their own medicine (no merging)", out["medications"][0]["route"] is None and out["medications"][1]["route"] == "oral" and out["medications"][1]["frequency"] is None)
check("medication status mapping", [m["status"] for m in out["medications"]] == ["currently_used", "planned"])
check("symptom temporality mapping and duration parse", out["symptoms"][0]["temporality"] == "current" and out["symptoms"][1]["temporality"] == "resolved" and out["symptoms"][0]["duration"] == {"value": 2, "unit": "weeks", "normalized": "2 weeks"} and out["symptoms"][1]["duration"] is None)
check("vital values: number parsed, blood pressure kept as text, speaker kept", out["vital_signs"][0]["value"] == "120/80" and out["vital_signs"][1]["value"] == 84 and out["vital_signs"][0]["reported_by"] == "nurse")
check("negative finding keeps its name; positives not converted", out["negative_findings"][0]["finding"] == "chest pain" and all(n["normalized_name"] is None for n in out["negative_findings"]))
check("allergy reported -> allergies entry, no negative finding", len(out["allergies"]) == 1 and out["allergies"][0]["allergy_type"] is None and not any(n["finding"] == "Allergies" for n in out["negative_findings"]))
check("no evidence ids, no dates and no uncertainties invented", all(not e.get("evidence_ids") for c in CATEGORIES for e in entity_list(out, c)) and out["clinical_evidence"] == [] and out["clinical_uncertainties"] == [] and out["follow_up"][0]["normalized_datetime"] is None)
check("follow-up time is the spoken words", out["follow_up"][0]["time_reference"] == "in two weeks" and out["follow_up"][0]["type"] == "consultation")
check("investigations and procedures merged, done -> completed", [p["status"] for p in out["procedures_and_investigations"]] == ["planned", "completed"])
check("action mapping by schema definitions", out["clinical_actions"][0]["status"] == "recommended" and out["clinical_actions"][1]["status"] == "planned" and out["clinical_actions"][1]["responsible_person"] == "doctor")
r = SV.validate(out)
check("canonical structure: no missing/unexpected/wrong_type violations", not any(k in r.counts for k in ("missing_field", "unexpected_field", "wrong_type", "missing_top_level", "unexpected_top_level")))
# allergy statuses
for st, expect in (("none_stated", 1), ("unknown", 0), ("not_asked", 0), ("reported", 0)):
    o, _ = A.adapt(mk(allergy_status=st))
    n = sum(1 for x in o["negative_findings"] if x["normalized_name"] == "No known allergies")
    check(f"allergy_status {st}: denial entries = {expect}", n == expect and o["allergies"] == [])
o, _ = A.adapt(mk(allergy_status="none_stated", negative_findings=[{"finding": "Allergies", "reported_by": "patient"}]))
check("explicit denial not duplicated when the model already listed it", sum(1 for x in o["negative_findings"] if str(x["finding"]).lower() == "allergies") == 1)
# problems are recorded, not repaired
o, p = A.adapt(mk(symptoms={"name": "x"}, medications=["metformin", {"name": "a", "dose": "", "route": "", "frequency": "", "status": "current", "reported_by": "patient"}], chief_complaint=["x"]))
check("wrong container/item types: section skipped, problem recorded, nothing invented", o["symptoms"] == [] and len(o["medications"]) == 1 and {q["where"] for q in p} == {"symptoms", "medications[0]", "chief_complaint"})
o, p = A.adapt(["not an object"])
check("non-object S1 output -> adapter failure", o is None and p[0]["kind"] == "adapter_failure")
# validation of the S1 format
bad = mk(symptoms=[{"name": "x", "status": "current", "reported_by": "doc"}], medications=[{"name": "a"}], allergy_status="maybe", extra=1)
kinds = {i["kind"] for i in A.validate_s1(bad)}
check("S1 validator detects enum, missing field, unexpected key", {"enum_violation", "missing_field", "unexpected_key"} <= kinds)
check("exact role-case aliases accepted by the S1 validator and adapter", not any(i["where"].endswith("reported_by") for i in A.validate_s1(mk(symptoms=[{"name": "x", "status": "present", "duration": "", "reported_by": "PATIENT"}]))) and A.adapt(mk(symptoms=[{"name": "x", "status": "present", "duration": "", "reported_by": "PATIENT"}]))[0]["symptoms"][0]["reported_by"] == "patient")
check("empty values become null (absent), not guessed", A.adapt(mk(medications=[{"name": "m", "dose": "", "route": "", "frequency": "", "status": "", "reported_by": ""}]))[0]["medications"][0]["dose"] is None)
check("duplicates are preserved (not removed)", len(A.adapt(mk(symptoms=[{"name": "cough", "status": "present", "duration": "", "reported_by": "patient"}] * 2))[0]["symptoms"]) == 2)
print(f"{len(fails)} failed" if fails else "all passed")
sys.exit(1 if fails else 0)
