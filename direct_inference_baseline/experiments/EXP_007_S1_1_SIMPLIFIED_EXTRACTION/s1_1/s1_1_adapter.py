"""S1.1 deterministic adapter: S1.1 intermediate JSON -> canonical evaluation schema (frozen final_label_schema key sets). Pure library, no I/O.
Same principles as the S1.0 adapter (EXP_006, unchanged; its helpers are imported): renames/relocates fields, applies the schema's own constants and definitional mappings, parses an unambiguous
'N unit(s)' duration, represents an explicit 'no known allergies' in the schema's own form. It never invents facts, evidence ids, dates or speakers, never corrects names/doses, never turns an
unknown allergy status into a denial, never changes polarity, never removes duplicates.
Differences from S1.0:
 - the model no longer produces current_conditions or encounter_id; the canonical `clinical_conditions` is the schema's empty list [] (the schema's defined empty-value representation) and the
   encounter id comes from the harness;
 - optional item fields may be absent (-> null); a blank primary field is kept as null and counted;
 - reported_by is copied unchanged. It is CHECKED against the encounter's sidecar: invalid role, role not present in that encounter, 'unknown' and missing roles are FLAGGED (never mapped, never repaired)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "EXP_006_S1_SIMPLIFIED_EXTRACTION" / "s1"))
import s1_adapter as A0  # noqa: E402  (frozen S1.0 adapter; read-only import for _s, parse_duration, ROLES)

ADAPTER_VERSION = "S1.1-adapter-1.0.0"
ROLES = A0.ROLES
S11_LISTS = ["symptoms", "negative_findings", "medical_history", "surgical_history", "family_history", "social_history", "medications", "allergies", "vital_signs", "physical_examination",
             "review_of_systems", "clinical_assessment", "investigations", "procedures", "clinical_actions", "follow_up"]
S11_KEYS = ["chief_complaint", "symptoms", "negative_findings", "medical_history", "surgical_history", "family_history", "social_history", "medications", "allergy_status", "allergies",
            "vital_signs", "physical_examination", "review_of_systems", "clinical_assessment", "investigations", "procedures", "clinical_actions", "follow_up"]
PRIMARY = {"symptoms": "name", "negative_findings": "finding", "medical_history": "condition", "surgical_history": "procedure", "family_history": "condition", "social_history": "category",
           "medications": "name", "allergies": "substance", "vital_signs": "name", "physical_examination": "finding", "review_of_systems": "system", "clinical_assessment": "assessment",
           "investigations": "name", "procedures": "name", "clinical_actions": "description", "follow_up": "when"}
REQUIRED = {"symptoms": {"name", "status", "reported_by"}, "negative_findings": {"finding", "reported_by"}, "medical_history": {"condition", "reported_by"}, "surgical_history": {"procedure", "reported_by"},
            "family_history": {"condition", "relation", "reported_by"}, "social_history": {"category", "reported_by"}, "medications": {"name", "status", "reported_by"}, "allergies": {"substance", "reported_by"},
            "vital_signs": {"name", "value", "reported_by"}, "physical_examination": {"finding", "reported_by"}, "review_of_systems": {"system", "reported_by"}, "clinical_assessment": {"assessment", "certainty"},
            "investigations": {"name", "status"}, "procedures": {"name", "status"}, "clinical_actions": {"type", "description"}, "follow_up": {"when", "status"}}
ALLOWED = {"symptoms": REQUIRED["symptoms"] | {"duration"}, "negative_findings": REQUIRED["negative_findings"], "medical_history": REQUIRED["medical_history"] | {"duration"},
           "surgical_history": REQUIRED["surgical_history"] | {"when"}, "family_history": REQUIRED["family_history"], "social_history": REQUIRED["social_history"] | {"status", "detail"},
           "medications": REQUIRED["medications"] | {"dose", "route", "frequency"}, "allergies": REQUIRED["allergies"] | {"reaction"}, "vital_signs": REQUIRED["vital_signs"] | {"unit"},
           "physical_examination": REQUIRED["physical_examination"] | {"body_site"}, "review_of_systems": REQUIRED["review_of_systems"] | {"details"}, "clinical_assessment": REQUIRED["clinical_assessment"],
           "investigations": REQUIRED["investigations"] | {"type"}, "procedures": REQUIRED["procedures"], "clinical_actions": REQUIRED["clinical_actions"], "follow_up": REQUIRED["follow_up"]}
ENUMS = {k: v for k, v in A0.S1_ENUMS.items()}
ALLERGY_STATUS = A0.ALLERGY_STATUS
MAPPING_NOTES = A0.MAPPING_NOTES + [
    "S1.1: current_conditions is not requested from the model; canonical clinical_conditions = [] (the schema's empty-list representation). encounter_id is supplied by the harness (file name).",
    "S1.1: absent optional fields -> null; blank primary field -> null (counted as an empty field, not repaired); chief_complaint copied verbatim, reported_by null (never inferred).",
    "S1.1: reported_by copied unchanged; flags: invalid_role, role_not_in_encounter, role_unavailable (value 'unknown'), role_missing; no mapping from speaker id to role, no correction.",
]


def _s(x):
    return A0._s(x)


def _role_raw(x):
    """the value as given (case-folded only for the exact role vocabulary and its documented spelling aliases); anything else is returned unchanged"""
    if not isinstance(x, str):
        return None
    a = A0.ROLE_ALIAS.get(x.strip().lower())
    return a if a is not None else (x.strip() or None)


def validate_s11(s):
    """validity of the S1.1-format JSON itself (independent of the canonical schema)."""
    issues = []
    if not isinstance(s, dict):
        return [{"kind": "wrong_type", "where": "root", "msg": "not an object"}]
    for k in S11_KEYS:
        if k not in s:
            issues.append({"kind": "missing_key", "where": k, "msg": "missing"})
    for k in s:
        if k not in S11_KEYS:
            issues.append({"kind": "unexpected_key", "where": k, "msg": "not part of the S1.1 format"})
    if "chief_complaint" in s:
        if not isinstance(s["chief_complaint"], str):
            issues.append({"kind": "wrong_type", "where": "chief_complaint", "msg": "expected a string"})
        elif not s["chief_complaint"].strip():
            issues.append({"kind": "empty_field", "where": "chief_complaint", "msg": "blank"})
    if "allergy_status" in s and s["allergy_status"] not in ALLERGY_STATUS:
        issues.append({"kind": "enum_violation", "where": "allergy_status", "msg": repr(s["allergy_status"])})
    for lst in S11_LISTS:
        if lst not in s:
            continue
        v = s[lst]
        if not isinstance(v, list):
            issues.append({"kind": "wrong_type", "where": lst, "msg": "expected a list"})
            continue
        for i, x in enumerate(v):
            if not isinstance(x, dict):
                issues.append({"kind": "wrong_type", "where": f"{lst}[{i}]", "msg": "item is not an object"})
                continue
            for f in REQUIRED[lst] - set(x):
                issues.append({"kind": "missing_field", "where": f"{lst}[{i}].{f}", "msg": "missing"})
            for f in set(x) - ALLOWED[lst]:
                issues.append({"kind": "unexpected_field", "where": f"{lst}[{i}].{f}", "msg": "not part of the S1.1 format"})
            if PRIMARY[lst] in x and not _s(x[PRIMARY[lst]]):
                issues.append({"kind": "empty_field", "where": f"{lst}[{i}].{PRIMARY[lst]}", "msg": "blank primary field"})
            for (sec, f), allowed in ENUMS.items():
                if sec == lst and f in x and x[f] not in allowed:
                    issues.append({"kind": "enum_violation", "where": f"{lst}[{i}].{f}", "msg": repr(x[f])})
            if "reported_by" in x and x["reported_by"] not in ROLES and A0.ROLE_ALIAS.get(str(x["reported_by"]).strip().lower()) is None:
                issues.append({"kind": "enum_violation", "where": f"{lst}[{i}].reported_by", "msg": repr(x["reported_by"])})
    return issues


def adapt(s, encounter_id, sidecar=None):
    """returns (canonical dict or None, problems list, speaker_flags list). `s` is never modified. `sidecar` (optional) is the encounter's sidecar dict (roles_present is used)."""
    problems, flags = [], []
    if not isinstance(s, dict):
        return None, [{"kind": "adapter_failure", "where": "root", "msg": "S1.1 output is not an object"}], flags
    present = set(sidecar["roles_present"]) if sidecar else None
    out = {"encounter_id": encounter_id, "extraction_status": "completed", "encounter_metadata": {"encounter_date": None, "encounter_type": "outpatient_consultation", "language": "en", "primary_speakers": []},
           "chief_complaint": {"value": None, "normalized_value": None, "reported_by": None, "evidence_ids": []},
           "symptoms": [], "negative_findings": [], "medical_history": {"past_medical_history": [], "surgical_history": [], "family_history": [], "social_history": []}, "medications": [], "allergies": [],
           "vital_signs": [], "physical_examination": [], "review_of_systems": [], "clinical_conditions": [], "clinical_assessment": [], "procedures_and_investigations": [], "clinical_actions": [], "follow_up": [],
           "clinical_uncertainties": [], "clinical_evidence": [],
           "quality_checks": {"negation_detected": False, "temporality_detected": False, "speaker_attribution_available": False, "unsupported_clinical_claims": [], "contradictions_detected": [], "ambiguous_entities": [], "requires_clinician_review": False}}
    cc = s.get("chief_complaint")
    if isinstance(cc, str):
        out["chief_complaint"]["value"] = _s(cc)
    elif cc is not None:
        problems.append({"kind": "adapter_failure", "where": "chief_complaint", "msg": "not a string; skipped"})

    def role(x, where):
        if "reported_by" not in x:
            flags.append({"kind": "role_missing", "where": where})
            return None
        raw = x.get("reported_by")
        r = _role_raw(raw)
        if r is None:
            flags.append({"kind": "role_missing", "where": where})
        elif r not in ROLES:
            flags.append({"kind": "invalid_role", "where": where, "value": r})
        elif r == "unknown":
            flags.append({"kind": "role_unavailable", "where": where})
        elif present is not None and r not in present:
            flags.append({"kind": "role_not_in_encounter", "where": where, "value": r})
        return r

    def items(name):
        v = s.get(name)
        if v is None:
            return []
        if not isinstance(v, list):
            problems.append({"kind": "adapter_failure", "where": name, "msg": "not a list; section skipped"})
            return []
        good = []
        for i, x in enumerate(v):
            if isinstance(x, dict):
                good.append((i, x))
            else:
                problems.append({"kind": "adapter_failure", "where": f"{name}[{i}]", "msg": "item is not an object; skipped"})
        return good

    for i, x in items("symptoms"):
        st = _s(x.get("status"))
        out["symptoms"].append({"name": _s(x.get("name")), "normalized_name": None, "category": None, "status": st, "severity": None, "duration": A0.parse_duration(x.get("duration")), "frequency": None, "onset": None,
                                "temporality": {"present": "current", "resolved": "resolved"}.get(st), "body_site": None, "associated_symptoms": [], "aggravating_factors": [], "relieving_factors": [],
                                "reported_by": role(x, f"symptoms[{i}]"), "certainty": None, "evidence_ids": [], "confidence": None})
    for i, x in items("negative_findings"):
        out["negative_findings"].append({"finding": _s(x.get("finding")), "normalized_name": None, "status": "absent", "assertion": "negative", "reported_by": role(x, f"negative_findings[{i}]"), "temporality": "current",
                                         "evidence_ids": [], "confidence": None})
    mh = out["medical_history"]
    for i, x in items("medical_history"):
        mh["past_medical_history"].append({"condition": _s(x.get("condition")), "normalized_condition": None, "status": "ongoing", "duration": A0.parse_duration(x.get("duration")),
                                           "reported_by": role(x, f"medical_history[{i}]"), "evidence_ids": [], "confidence": None})
    for i, x in items("surgical_history"):
        mh["surgical_history"].append({"procedure": _s(x.get("procedure")), "normalized_procedure": None, "timeframe": _s(x.get("when")), "reported_by": role(x, f"surgical_history[{i}]"), "evidence_ids": [], "confidence": None})
    for i, x in items("family_history"):
        mh["family_history"].append({"condition": _s(x.get("condition")), "normalized_condition": None, "relation": _s(x.get("relation")), "reported_by": role(x, f"family_history[{i}]"), "evidence_ids": [], "confidence": None})
    for i, x in items("social_history"):
        mh["social_history"].append({"category": _s(x.get("category")), "description": _s(x.get("detail")), "status": _s(x.get("status")), "details": _s(x.get("detail")), "reported_by": role(x, f"social_history[{i}]"),
                                     "evidence_ids": [], "confidence": None})
    for i, x in items("medications"):
        out["medications"].append({"name": _s(x.get("name")), "normalized_name": None, "generic_name": None, "dose": _s(x.get("dose")), "route": _s(x.get("route")), "frequency": _s(x.get("frequency")), "duration": None,
                                   "indication": None, "status": {"current": "currently_used", "stopped": "discontinued", "new": "planned"}.get(_s(x.get("status"))), "reported_by": role(x, f"medications[{i}]"),
                                   "evidence_ids": [], "confidence": None})
    ast = s.get("allergy_status")
    for i, x in items("allergies"):
        out["allergies"].append({"substance": _s(x.get("substance")), "normalized_substance": None, "allergy_type": None, "reaction": _s(x.get("reaction")), "severity": "unknown", "status": "reported",
                                 "reported_by": role(x, f"allergies[{i}]"), "evidence_ids": [], "confidence": None})
    if ast == "none_stated" and not any(isinstance(n, dict) and str(n.get("finding")).lower() == "allergies" for n in out["negative_findings"]):
        out["negative_findings"].append({"finding": "Allergies", "normalized_name": "No known allergies", "status": "absent", "assertion": "negative", "reported_by": "patient", "temporality": "current", "evidence_ids": [], "confidence": None})
    for i, x in items("vital_signs"):
        v = _s(x.get("value")) if isinstance(x.get("value"), str) else x.get("value")
        if isinstance(v, str) and re.fullmatch(r"\d+", v):
            v = int(v)
        elif isinstance(v, str) and re.fullmatch(r"\d+\.\d+", v):
            v = float(v)
        out["vital_signs"].append({"name": _s(x.get("name")), "normalized_name": None, "value": v, "unit": _s(x.get("unit")), "reported_by": role(x, f"vital_signs[{i}]"), "evidence_ids": [], "confidence": None})
    for i, x in items("physical_examination"):
        out["physical_examination"].append({"finding": _s(x.get("finding")), "normalized_finding": None, "body_site": _s(x.get("body_site")), "status": "present", "observed_by": None, "evidence_ids": [], "confidence": None})
    for i, x in items("review_of_systems"):
        out["review_of_systems"].append({"system": _s(x.get("system")), "status": "negative", "details": _s(x.get("details")), "reported_by": role(x, f"review_of_systems[{i}]"), "evidence_ids": [], "confidence": None})
    for i, x in items("clinical_assessment"):
        out["clinical_assessment"].append({"assessment": _s(x.get("assessment")), "normalized_assessment": None, "certainty": _s(x.get("certainty")), "basis": None, "stated_by": "doctor", "evidence_ids": [], "confidence": None})
    st_map = {"planned": "planned", "done": "completed", "conditional": "conditional"}
    for i, x in items("investigations"):
        out["procedures_and_investigations"].append({"name": _s(x.get("name")), "normalized_name": None, "type": _s(x.get("type")), "status": st_map.get(_s(x.get("status"))), "requested_by": None, "indication": None,
                                                     "scheduled_datetime": None, "evidence_ids": [], "confidence": None})
    for i, x in items("procedures"):
        out["procedures_and_investigations"].append({"name": _s(x.get("name")), "normalized_name": None, "type": "other", "status": st_map.get(_s(x.get("status"))), "requested_by": None, "indication": None,
                                                     "scheduled_datetime": None, "evidence_ids": [], "confidence": None})
    for i, x in items("clinical_actions"):
        t = _s(x.get("type"))
        order = t in ("medication", "investigation", "referral", "follow_up")
        out["clinical_actions"].append({"action_type": t, "description": _s(x.get("description")), "status": "planned" if order else ("recommended" if t in ("counselling", "other") else None),
                                        "responsible_person": "doctor" if order else ("patient" if t in ("counselling", "other") else None), "time_reference": None, "evidence_ids": [], "confidence": None})
    for i, x in items("follow_up"):
        out["follow_up"].append({"type": "consultation", "time_reference": _s(x.get("when")), "normalized_datetime": None, "status": _s(x.get("status")), "evidence_ids": []})
    return out, problems, flags
