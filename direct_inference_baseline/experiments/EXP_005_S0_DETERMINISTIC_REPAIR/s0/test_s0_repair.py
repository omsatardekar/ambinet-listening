"""Unit tests for S0 (synthetic data only; no project data opened).  usage: python -B test_s0_repair.py   (exit code 1 on any failure)"""
import copy
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import s0_repair as R  # noqa: E402

SEGS = [{"segment_id": "SEG0001", "speaker_id": "person_2", "role": "DOCTOR", "text": "Any allergies I should know about?"},
        {"segment_id": "SEG0002", "speaker_id": "person_1", "role": "PATIENT", "text": "No, none that I know of."},
        {"segment_id": "SEG0003", "speaker_id": "person_2", "role": "DOCTOR", "text": "Let's book a thyroid test, come back in two weeks."},
        {"segment_id": "SEG0004", "speaker_id": "person_3", "role": "NURSE", "text": "Here are the numbers, doctor. Pulse is 84."},
        {"segment_id": "SEG0005", "speaker_id": "person_1", "role": "PATIENT", "text": "I've had a headache for three days."}]
BASE = {"clinical_assessment": [], "follow_up": [], "allergies": [], "negative_findings": [], "medications": [], "symptoms": [], "vital_signs": [], "procedures_and_investigations": [], "clinical_actions": [],
        "clinical_evidence": [], "medical_history": {"past_medical_history": [], "surgical_history": [], "family_history": [], "social_history": []}, "chief_complaint": {"value": "x", "reported_by": "patient", "evidence_ids": []}}
fails = []


def check(name, cond):
    if not cond:
        fails.append(name)
    print(("PASS " if cond else "FAIL ") + name)


def rep(pred, segs=SEGS, trusted=False):
    p = copy.deepcopy(BASE)
    p.update(pred)
    return R.repair(p, segs, "T1", trusted) + (p,)


# A
out, log, st, orig = rep({"follow_up": {"type": "consultation", "time_reference": "in two weeks", "normalized_datetime": None, "status": "planned", "evidence_ids": []}})
check("A object wrapped into a one-item list", isinstance(out["follow_up"], list) and out["follow_up"][0]["time_reference"] == "in two weeks")
out, log, st, orig = rep({"clinical_assessment": {}})
check("A empty object preserved and flagged", out["clinical_assessment"] == {} and any(r["rule"] == "A_ambiguous_object" for r in log))
out, log, st, orig = rep({"clinical_assessment": {"assessment": "x", "basis": ["a", "b"]}})
check("A object with a nested list preserved and flagged", isinstance(out["clinical_assessment"], dict) and any(r["rule"] == "A_ambiguous_object" for r in log))
# B
out, log, st, orig = rep({"symptoms": [{"name": "h", "reported_by": "PATIENT"}], "clinical_actions": [{"description": "d", "responsible_person": "DOCTOR"}, {"description": "e", "responsible_person": "family_member"}],
                          "negative_findings": [{"finding": "f", "reported_by": "Family Member"}, {"finding": "g", "reported_by": "grandma"}]})
check("B case alias fixed", out["symptoms"][0]["reported_by"] == "patient" and out["clinical_actions"][0]["responsible_person"] == "doctor")
check("B defined spelling alias fixed", out["negative_findings"][0]["reported_by"] == "family_member")
check("B unknown value preserved and flagged", out["negative_findings"][1]["reported_by"] == "grandma" and any(r["rule"] == "B_unknown_enum_value" and r["original"] == "grandma" for r in log))
check("B value outside the allowed set for the field preserved and flagged", out["clinical_actions"][1]["responsible_person"] == "family_member")
# C
ph = {"substance": "none", "normalized_substance": "none", "allergy_type": "none", "reaction": "none", "severity": "unknown", "status": "reported", "reported_by": "doctor", "evidence_ids": []}
out, log, st, orig = rep({"allergies": [ph]})
check("C placeholder removed and explicit denial represented in the schema form", out["allergies"] == [] and out["negative_findings"][-1]["normalized_name"] == "No known allergies" and out["negative_findings"][-1]["reported_by"] == "patient" and st == "explicit_no_known_allergies")
segs2 = [dict(SEGS[0]), {"segment_id": "SEG0002", "speaker_id": "person_1", "role": "PATIENT", "text": "No, none that I know of."}, {"segment_id": "SEG0003", "speaker_id": "person_4", "role": "CAREGIVER", "text": "Actually I think she reacted to ibuprofen once."}]
out, log, st, orig = rep({"allergies": [ph]}, segs2)
check("C disputed answer: placeholder removed, NO denial created, status unknown", out["allergies"] == [] and out["negative_findings"] == [] and st == "unknown")
out, log, st, orig = rep({"allergies": [ph]}, [SEGS[2], SEGS[4]])
check("C no allergy question: removed, no denial created, status not_assessed", out["allergies"] == [] and out["negative_findings"] == [] and st == "not_assessed")
real = dict(ph, substance="penicillin", normalized_substance="Penicillin", allergy_type="medication", reaction="rash")
out, log, st, orig = rep({"allergies": [real]})
check("C a real allergy is untouched", out["allergies"] == [real] and st is None)
out, log, st, orig = rep({"allergies": [dict(real, substance="amlodipine", normalized_substance="Amlodipine")], "medications": [{"name": "amlodipine", "normalized_name": "amlodipine", "generic_name": "amlodipine"}]})
check("C medicine listed as allergy is only flagged", len(out["allergies"]) == 1 and any(r["rule"] == "F_medication_listed_as_allergy" for r in log))
# D
out, log, st, orig = rep({"procedures_and_investigations": [{"name": "x", "scheduled_datetime": "2023-04-10T10:00:00Z"}, {"name": "y", "scheduled_datetime": "two weeks"}], "follow_up": [{"type": "consultation", "normalized_datetime": "388.63s", "time_reference": "", "status": "planned"}]})
check("D unsupported ISO datetime nulled, original kept in the log", out["procedures_and_investigations"][0]["scheduled_datetime"] is None and any(r["original"] == "2023-04-10T10:00:00Z" for r in log))
check("D supported wording kept", out["procedures_and_investigations"][1]["scheduled_datetime"] == "two weeks")
check("D timestamp-like value nulled", out["follow_up"][0]["normalized_datetime"] is None)
# E
ev = [{"evidence_id": "EV_001", "speaker_id": "person_3", "speaker_role": "nurse", "transcript_text": "Here are the numbers, doctor. Pulse is 84.", "supports": ["vital_signs[0]"]}]
vit = {"name": "pulse", "value": 84, "unit": "bpm", "reported_by": "doctor", "evidence_ids": ["EV_001"]}
out, log, st, orig = rep({"vital_signs": [vit], "clinical_evidence": ev}, trusted=True)
check("E reported_by derived from a verified cited segment", out["vital_signs"][0]["reported_by"] == "nurse")
out, log, st, orig = rep({"vital_signs": [vit], "clinical_evidence": ev}, trusted=False)
check("E not applied to untrusted evidence", out["vital_signs"][0]["reported_by"] == "doctor")
bad = [dict(ev[0], transcript_text="Here are the numbers. Pulse is 90.")]
out, log, st, orig = rep({"vital_signs": [vit], "clinical_evidence": bad}, trusted=True)
check("E evidence record that does not reproduce a real segment is ignored", out["vital_signs"][0]["reported_by"] == "doctor")
q = [{"evidence_id": "EV_001", "speaker_id": "person_2", "speaker_role": "doctor", "transcript_text": "Any allergies I should know about?", "supports": []}]
out, log, st, orig = rep({"symptoms": [{"name": "h", "reported_by": "patient", "evidence_ids": ["EV_001"]}], "clinical_evidence": q}, trusted=True)
check("E a doctor question is never a speaker source", out["symptoms"][0]["reported_by"] == "patient")
# F / no clinical correction
med = {"name": "thyronorm", "normalized_name": "Thyronorm", "dose": "500 milligrams", "route": "every morning", "frequency": "daily", "status": "currently_used", "reported_by": "doctor"}
neg = {"finding": "headache", "normalized_name": "headache", "status": "absent", "reported_by": "doctor"}
out, log, st, orig = rep({"medications": [med], "negative_findings": [neg], "symptoms": [{"name": "headache", "normalized_name": "headache", "reported_by": "patient"}]})
check("F dose/route/polarity never changed (flags only)", out["medications"][0]["dose"] == "500 milligrams" and out["medications"][0]["route"] == "every morning" and out["negative_findings"] == [dict(neg, reported_by="doctor")]
      and {"F_route_is_not_a_route", "F_negative_finding_overlaps_positive_item"} <= {r["rule"] for r in log})
# general
out, log, st, orig = rep({"allergies": [ph], "follow_up": {"type": "consultation", "time_reference": "x", "status": "planned"}, "vital_signs": [dict(vit, reported_by="DOCTOR")]})
check("input is never modified", json.dumps(orig, sort_keys=True) == json.dumps(rep({"allergies": [ph], "follow_up": {"type": "consultation", "time_reference": "x", "status": "planned"}, "vital_signs": [dict(vit, reported_by="DOCTOR")]})[3], sort_keys=True))
out2, log2, _ = R.repair(out, SEGS, "T1", False)
check("idempotent: a second pass changes nothing", out2 == out and not [r for r in log2 if r["kind"] == "change"])
check("every log row has the required fields", all({"encounter_id", "path", "original", "repaired", "rule", "reason", "deterministic", "human_review_required"} <= set(r) for r in log))
print(f"\n{len(fails)} failed" if fails else "\nall passed")
sys.exit(1 if fails else 0)
