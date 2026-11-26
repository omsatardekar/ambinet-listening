"""Unit tests for the S1.1 adapter and sidecar. Synthetic data only (no project transcript, label, validation or locked-test file).
usage (project env): python -B test_s1_1_adapter.py"""
import copy
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
EXP7 = HERE.parent
ROOT = EXP7.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(EXP7 / "phase_a"))
sys.path.insert(0, str(EXP7.parent / "EXP_004_QWEN3_0.6B_PROMPT_ENGINEERING" / "experiments"))
from common import S  # noqa: E402,F401  (existing helper module; stubs the unneeded dotenv import exactly as in the S1.0 tests)
import s1_1_adapter as A  # noqa: E402
import sidecar as SC  # noqa: E402
import synth_gen as SG  # noqa: E402
from direct_inference_baseline.evaluation import schema_validator as SV  # noqa: E402
from direct_inference_baseline.evaluation.entity_matching import CATEGORIES, entity_list  # noqa: E402

fails = []


def check(n, c):
    print(("PASS " if c else "FAIL ") + n)
    if not c:
        fails.append(n)


def mk(**kw):
    d = {k: ([] if k in A.S11_LISTS else "") for k in A.S11_KEYS}
    d["allergy_status"] = "not_asked"
    d.update(kw)
    return d


SIDE = {"roles_present": ["doctor", "patient", "nurse"]}
FULL = mk(chief_complaint="heel pain", symptoms=[{"name": "heel pain", "status": "present", "duration": "two weeks", "reported_by": "patient"}, {"name": "fever", "status": "resolved", "reported_by": "patient"}],
          negative_findings=[{"finding": "chest pain", "reported_by": "patient"}], medical_history=[{"condition": "diabetes", "duration": "about ten years", "reported_by": "patient"}],
          surgical_history=[{"procedure": "appendectomy", "when": "years ago", "reported_by": "patient"}], family_history=[{"condition": "asthma", "relation": "brother", "reported_by": "patient"}],
          social_history=[{"category": "smoking", "status": "never", "reported_by": "patient"}],
          medications=[{"name": "metformin", "dose": "500 milligrams", "frequency": "twice a day", "status": "current", "reported_by": "patient"}, {"name": "metoprolol", "dose": "50 milligrams", "route": "oral", "status": "new", "reported_by": "doctor"}],
          allergy_status="reported", allergies=[{"substance": "penicillin", "reaction": "rash", "reported_by": "patient"}], vital_signs=[{"name": "blood pressure", "value": "120/80", "reported_by": "nurse"}, {"name": "pulse", "value": "84", "unit": "bpm", "reported_by": "nurse"}],
          physical_examination=[{"finding": "swelling", "body_site": "right knee", "reported_by": "doctor"}], review_of_systems=[{"system": "urinary", "reported_by": "patient"}],
          clinical_assessment=[{"assessment": "plantar fasciitis", "certainty": "provisional"}], investigations=[{"name": "foot x-ray", "type": "imaging", "status": "planned"}], procedures=[{"name": "dressing", "status": "done"}],
          clinical_actions=[{"type": "counselling", "description": "stretch the calf"}, {"type": "medication", "description": "start metoprolol"}], follow_up=[{"when": "in two weeks", "status": "planned"}])
orig = copy.deepcopy(FULL)
out, probs, flags = A.adapt(FULL, "T1", SIDE)
check("input never modified", FULL == orig)
check("full example: no problems, no flags, S1.1 format valid", not probs and not flags and not A.validate_s11(FULL))
check("encounter id comes from the harness, not the model", out["encounter_id"] == "T1")
check("chief complaint copied verbatim; reported_by null (never inferred)", out["chief_complaint"]["value"] == "heel pain" and out["chief_complaint"]["reported_by"] is None)
check("clinical_conditions is the schema's empty list (not requested from the model)", out["clinical_conditions"] == [] and "current_conditions" not in A.S11_KEYS)
check("names and values copied unchanged", out["medications"][0]["name"] == "metformin" and out["medications"][0]["dose"] == "500 milligrams" and out["symptoms"][0]["name"] == "heel pain")
check("doses stay with their own medicine; absent optional fields become null", out["medications"][0]["route"] is None and out["medications"][1]["route"] == "oral" and out["medications"][1]["frequency"] is None)
check("medication status mapping", [m["status"] for m in out["medications"]] == ["currently_used", "planned"])
check("symptom temporality and duration", out["symptoms"][0]["temporality"] == "current" and out["symptoms"][1]["temporality"] == "resolved" and out["symptoms"][0]["duration"]["value"] == 2 and out["symptoms"][1]["duration"] is None)
check("vital values: number parsed, blood pressure text kept, speaker kept", out["vital_signs"][0]["value"] == "120/80" and out["vital_signs"][1]["value"] == 84 and out["vital_signs"][0]["reported_by"] == "nurse")
check("no evidence ids, dates or uncertainties invented", all(not e.get("evidence_ids") for c in CATEGORIES for e in entity_list(out, c)) and out["clinical_uncertainties"] == [] and out["follow_up"][0]["normalized_datetime"] is None)
check("follow-up words copied", out["follow_up"][0]["time_reference"] == "in two weeks")
check("investigations+procedures merged; done->completed", [p["status"] for p in out["procedures_and_investigations"]] == ["planned", "completed"])
r = SV.validate(out)
check("canonical structure: no missing/unexpected/wrong_type violations", not any(k in r.counts for k in ("missing_field", "unexpected_field", "wrong_type", "missing_top_level", "unexpected_top_level")))
check("empty adapted record is canonically valid too", not any(k in SV.validate(A.adapt(mk(), "T2", SIDE)[0]).counts for k in ("missing_field", "unexpected_field", "wrong_type", "missing_top_level", "unexpected_top_level")))
for st, expect in (("none_stated", 1), ("unknown", 0), ("not_asked", 0), ("reported", 0)):
    o, _, _ = A.adapt(mk(allergy_status=st), "T", SIDE)
    n = sum(1 for x in o["negative_findings"] if x["normalized_name"] == "No known allergies")
    check(f"allergy_status {st}: denial entries = {expect}", n == expect and o["allergies"] == [])
# --- speaker handling: never mapped, always flagged
o, p, f = A.adapt(mk(symptoms=[{"name": "x", "status": "present", "reported_by": "person_1"}]), "T", SIDE)
check("person_N is kept as given and flagged invalid_role (no silent mapping)", o["symptoms"][0]["reported_by"] == "person_1" and [x["kind"] for x in f] == ["invalid_role"])
o, p, f = A.adapt(mk(symptoms=[{"name": "x", "status": "present", "reported_by": "caregiver"}]), "T", SIDE)
check("valid role absent from this encounter is kept and flagged role_not_in_encounter", o["symptoms"][0]["reported_by"] == "caregiver" and [x["kind"] for x in f] == ["role_not_in_encounter"])
o, p, f = A.adapt(mk(symptoms=[{"name": "x", "status": "present", "reported_by": "unknown"}]), "T", SIDE)
check("'unknown' kept as the schema's 'unknown' and flagged role_unavailable", o["symptoms"][0]["reported_by"] == "unknown" and [x["kind"] for x in f] == ["role_unavailable"])
o, p, f = A.adapt(mk(symptoms=[{"name": "x", "status": "present"}]), "T", SIDE)
check("missing reported_by -> null and flagged role_missing", o["symptoms"][0]["reported_by"] is None and [x["kind"] for x in f] == ["role_missing"])
o, p, f = A.adapt(mk(symptoms=[{"name": "x", "status": "present", "reported_by": "PATIENT"}]), "T", SIDE)
check("role spelling alias (case only) accepted without flag", o["symptoms"][0]["reported_by"] == "patient" and not f)
# --- no repair
o, p, f = A.adapt(mk(symptoms={"name": "x"}, medications=["metformin", {"name": "a", "status": "current", "reported_by": "patient"}], chief_complaint=["x"]), "T", SIDE)
check("wrong container/item types: skipped, recorded, nothing invented", o["symptoms"] == [] and len(o["medications"]) == 1 and {q["where"] for q in p} == {"symptoms", "medications[0]", "chief_complaint"})
o, p, f = A.adapt(["not an object"], "T", SIDE)
check("non-object output -> adapter failure", o is None and p[0]["kind"] == "adapter_failure")
o, p, f = A.adapt(mk(medications=[{"name": "", "status": "", "reported_by": ""}]), "T", SIDE)
check("blank values become null (empty field, not repaired or guessed)", o["medications"][0]["name"] is None and o["medications"][0]["status"] is None)
check("duplicates preserved", len(A.adapt(mk(symptoms=[{"name": "cough", "status": "present", "reported_by": "patient"}] * 2), "T", SIDE)[0]["symptoms"]) == 2)
bad = mk(symptoms=[{"name": "", "status": "bad", "reported_by": "doc"}], medications=[{"name": "a"}], allergy_status="maybe", extra=1)
kinds = {i["kind"] for i in A.validate_s11(bad)}
check("validator detects enum, missing field, unexpected key, empty field", {"enum_violation", "missing_field", "unexpected_key", "empty_field"} <= kinds)
check("validator reports a missing chief_complaint key", any(i["kind"] == "missing_key" and i["where"] == "chief_complaint" for i in A.validate_s11({k: v for k, v in mk().items() if k != "chief_complaint"})))
# --- sidecar
L, exp = SG.CASES["synA01"]
inp = {"encounter_id": "synA01", "segments": [{"segment_id": f"SEG{i + 1:04d}", "speaker_id": sp, "role": role, "start_seconds": t, "end_seconds": t + 3, "text": txt} for i, (sp, role, t, txt) in enumerate(L)]}
sc = SC.build_sidecar(inp)
check("sidecar keeps segment ids, speaker ids, roles and times for every line", sc["n_lines"] == len(L) and sc["lines"][0]["segment_id"] == "SEG0001" and sc["lines"][0]["speaker_id"] == "person_1" and sc["lines"][0]["role"] == "PATIENT" and sc["lines"][0]["start_seconds"] == L[0][2])
check("sidecar speaker->role map and roles present", sc["speaker_to_role"]["person_2"] == "DOCTOR" and set(sc["roles_present"]) == {"doctor", "patient", "nurse"} or set(sc["roles_present"]) <= {"doctor", "patient", "nurse"})
r1 = SC.render_r1(inp)
check("R1 rendering has no segment ids, speaker ids or times; one 'role: text' per line", "SEG" not in r1 and "person_" not in r1 and "s:" not in r1.split(":")[0] and len(r1.splitlines()) == len(L) and r1.splitlines()[0].startswith("patient: "))
check("original input dict unchanged by rendering", inp["segments"][0]["speaker_id"] == "person_1")
amb = {"encounter_id": "a", "segments": [{"segment_id": "SEG0001", "speaker_id": "person_1", "role": "FAMILY_MEMBER", "start_seconds": 0, "end_seconds": 1, "text": "a"}, {"segment_id": "SEG0002", "speaker_id": "person_3", "role": "FAMILY_MEMBER", "start_seconds": 1, "end_seconds": 2, "text": "b"},
                                   {"segment_id": "SEG0003", "speaker_id": "person_2", "role": "UNKNOWN", "start_seconds": 2, "end_seconds": 3, "text": "c"}]}
kk = {f["kind"] for f in SC.build_sidecar(amb)["flags"]}
check("ambiguous roles and unavailable roles are flagged in the sidecar", {"ambiguous_role", "role_unavailable"} <= kk)
try:
    SC.render_r1({"segments": [{"segment_id": "S", "speaker_id": "p", "role": "MYSTERY", "start_seconds": 0, "end_seconds": 1, "text": "x"}]})
    check("unmapped role refuses to render (never guessed)", False)
except ValueError:
    check("unmapped role refuses to render (never guessed)", True)
print(f"{len(fails)} failed" if fails else "all passed")
sys.exit(1 if fails else 0)
