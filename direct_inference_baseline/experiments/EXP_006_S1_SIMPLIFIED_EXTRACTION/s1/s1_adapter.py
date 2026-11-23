"""S1 deterministic adapter: S1 intermediate JSON -> canonical evaluation schema (frozen final_label_schema key sets). Pure library, no I/O.

It only (1) renames/relocates fields, (2) applies the schema's own constants and definitional mappings (listed in MAPPING_NOTES), (3) parses an unambiguous "N unit(s)" duration, and
(4) represents an explicitly stated "no known allergies" in the schema's own form. It never invents facts, evidence ids, dates or speakers, never corrects names or doses, never turns an unknown
allergy status into a denial, never changes polarity, never removes duplicates, and never adds anything the model did not extract.
Structural problems it cannot map unambiguously (wrong container type, non-object item, ...) are NOT repaired: the section is skipped and an adapter problem is recorded."""
from __future__ import annotations

import re

ADAPTER_VERSION = "S1-adapter-1.0.0"
ROLES = {"doctor", "patient", "nurse", "caregiver", "family_member", "clinical_staff", "unknown"}
ROLE_ALIAS = {r: r for r in ROLES}
ROLE_ALIAS.update({"family member": "family_member", "clinical staff": "clinical_staff", "family-member": "family_member", "clinical-staff": "clinical_staff"})
NUMW = {"a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12}
S1_LISTS = ["symptoms", "negative_findings", "medical_history", "current_conditions", "surgical_history", "family_history", "social_history", "medications", "allergies", "vital_signs",
            "physical_examination", "review_of_systems", "clinical_assessment", "investigations", "procedures", "clinical_actions", "follow_up"]
S1_KEYS = ["encounter_id", "chief_complaint", "symptoms", "negative_findings", "medical_history", "current_conditions", "surgical_history", "family_history", "social_history", "medications",
           "allergy_status", "allergies", "vital_signs", "physical_examination", "review_of_systems", "clinical_assessment", "investigations", "procedures", "clinical_actions", "follow_up"]
S1_ITEM_KEYS = {"symptoms": {"name", "status", "duration", "reported_by"}, "negative_findings": {"finding", "reported_by"}, "medical_history": {"condition", "duration", "reported_by"},
                "current_conditions": {"condition", "reported_by"}, "surgical_history": {"procedure", "when", "reported_by"}, "family_history": {"condition", "relation", "reported_by"},
                "social_history": {"category", "status", "detail", "reported_by"}, "medications": {"name", "dose", "route", "frequency", "status", "reported_by"}, "allergies": {"substance", "reaction", "reported_by"},
                "vital_signs": {"name", "value", "unit", "reported_by"}, "physical_examination": {"finding", "body_site", "reported_by"}, "review_of_systems": {"system", "details", "reported_by"},
                "clinical_assessment": {"assessment", "certainty"}, "investigations": {"name", "type", "status"}, "procedures": {"name", "status"}, "clinical_actions": {"type", "description"}, "follow_up": {"when", "status"}}
S1_ENUMS = {("symptoms", "status"): {"present", "resolved"}, ("social_history", "category"): {"smoking", "alcohol", "occupation", "exercise", "diet", "living"},
            ("social_history", "status"): {"current", "former", "never", "none", "retired"}, ("medications", "status"): {"current", "stopped", "new"},
            ("clinical_assessment", "certainty"): {"provisional", "differential"}, ("investigations", "type"): {"laboratory", "imaging", "cardiac", "other"},
            ("investigations", "status"): {"planned", "done", "conditional"}, ("procedures", "status"): {"planned", "done", "conditional"},
            ("clinical_actions", "type"): {"medication", "investigation", "counselling", "referral", "follow_up", "other"}, ("follow_up", "status"): {"planned", "conditional"}}
ALLERGY_STATUS = {"reported", "none_stated", "unknown", "not_asked"}
MAPPING_NOTES = [
    "encounter_id copied; extraction_status 'completed', encounter_metadata (date null, type outpatient_consultation, language en, primary_speakers []), clinical_evidence [], clinical_uncertainties [], quality_checks defaults: schema constants, not model output",
    "chief_complaint: string -> {value, normalized_value null, reported_by null, evidence_ids []}; empty string -> value null",
    "symptoms: status present -> status present + temporality current; resolved -> resolved + resolved (the schema also has 'past', which S1 cannot distinguish: not guessed); duration 'N unit(s)' parsed, other text kept in duration.normalized",
    "negative_findings: status absent, assertion negative, temporality current (schema constants; S1 does not distinguish current from past denials)",
    "medical_history -> medical_history.past_medical_history (status ongoing, schema constant); current_conditions -> clinical_conditions (status existing); surgical/family/social copied by name",
    "medications: current -> currently_used, stopped -> discontinued, new -> planned; name/dose/route/frequency copied; generic_name, normalized_name, duration, indication null",
    "allergy_status none_stated -> negative_findings entry {Allergies / No known allergies / absent / negative / patient / current} (schema form of an explicit denial); reported -> allergies entries; unknown / not_asked -> nothing; allergy_type null (not given), severity 'unknown' (schema constant), status reported",
    "vital_signs: purely numeric value -> number, otherwise string; unit copied; reported_by copied (who said it, not who measured it)",
    "physical_examination: status present, observed_by null; review_of_systems: status negative (the schema's only value; S1 lists denied systems)",
    "clinical_assessment: stated_by doctor (schema default)",
    "investigations + procedures -> procedures_and_investigations (procedures type other); done -> completed; requested_by, indication, scheduled_datetime null",
    "clinical_actions: status/responsible_person by the schema's definitions: medication, investigation, referral, follow_up -> planned/doctor; counselling, other -> recommended/patient",
    "follow_up: type consultation (schema's only value), time_reference = S1 'when' as spoken, normalized_datetime null",
]


def validate_s1(s1):
    """Validity of the S1-format JSON itself (independent of the canonical schema). Returns a list of issue dicts."""
    issues = []
    if not isinstance(s1, dict):
        return [{"kind": "wrong_type", "where": "root", "msg": "not an object"}]
    for k in S1_KEYS:
        if k not in s1:
            issues.append({"kind": "missing_key", "where": k, "msg": "missing"})
    for k in s1:
        if k not in S1_KEYS:
            issues.append({"kind": "unexpected_key", "where": k, "msg": "not part of the S1 format"})
    if "chief_complaint" in s1 and not isinstance(s1["chief_complaint"], str):
        issues.append({"kind": "wrong_type", "where": "chief_complaint", "msg": "expected a string"})
    if "allergy_status" in s1 and s1["allergy_status"] not in ALLERGY_STATUS:
        issues.append({"kind": "enum_violation", "where": "allergy_status", "msg": repr(s1["allergy_status"])})
    for lst in S1_LISTS:
        v = s1.get(lst)
        if lst not in s1:
            continue
        if not isinstance(v, list):
            issues.append({"kind": "wrong_type", "where": lst, "msg": "expected a list"})
            continue
        for i, x in enumerate(v):
            if not isinstance(x, dict):
                issues.append({"kind": "wrong_type", "where": f"{lst}[{i}]", "msg": "item is not an object"})
                continue
            for f in S1_ITEM_KEYS[lst] - set(x):
                issues.append({"kind": "missing_field", "where": f"{lst}[{i}].{f}", "msg": "missing"})
            for f in set(x) - S1_ITEM_KEYS[lst]:
                issues.append({"kind": "unexpected_field", "where": f"{lst}[{i}].{f}", "msg": "not part of the S1 format"})
            for (sec, f), allowed in S1_ENUMS.items():
                if sec == lst and f in x and x[f] not in allowed:
                    issues.append({"kind": "enum_violation", "where": f"{lst}[{i}].{f}", "msg": repr(x[f])})
            if "reported_by" in x and x["reported_by"] not in ROLES and ROLE_ALIAS.get(str(x["reported_by"]).strip().lower()) is None:
                issues.append({"kind": "enum_violation", "where": f"{lst}[{i}].reported_by", "msg": repr(x["reported_by"])})
    return issues


def _s(x):
    """string value or None for empty / non-string"""
    return x.strip() if isinstance(x, str) and x.strip() else None


def _role(x):
    if not isinstance(x, str):
        return None
    return ROLE_ALIAS.get(x.strip().lower(), x.strip() or None)


def parse_duration(text):
    t = _s(text)
    if t is None:
        return None
    m = re.fullmatch(r"(about |nearly |around |almost |roughly )?(\d+|a|an|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve) (day|week|month|year)s?", t.lower())
    if not m:
        return {"value": None, "unit": None, "normalized": t}
    n = int(m.group(2)) if m.group(2).isdigit() else NUMW[m.group(2)]
    unit = m.group(3) + "s"
    return {"value": n, "unit": unit, "normalized": f"{(m.group(1) or '').replace('around', 'about').replace('almost', 'nearly').replace('roughly', 'about')}{n} {unit}"}


def adapt(s1):
    """returns (canonical dict, problems list). `s1` is never modified."""
    problems = []
    if not isinstance(s1, dict):
        return None, [{"kind": "adapter_failure", "where": "root", "msg": "S1 output is not an object"}]
    out = {"encounter_id": s1.get("encounter_id") if isinstance(s1.get("encounter_id"), str) else None, "extraction_status": "completed",
           "encounter_metadata": {"encounter_date": None, "encounter_type": "outpatient_consultation", "language": "en", "primary_speakers": []},
           "chief_complaint": {"value": None, "normalized_value": None, "reported_by": None, "evidence_ids": []},
           "symptoms": [], "negative_findings": [], "medical_history": {"past_medical_history": [], "surgical_history": [], "family_history": [], "social_history": []}, "medications": [], "allergies": [],
           "vital_signs": [], "physical_examination": [], "review_of_systems": [], "clinical_conditions": [], "clinical_assessment": [], "procedures_and_investigations": [], "clinical_actions": [], "follow_up": [],
           "clinical_uncertainties": [], "clinical_evidence": [],
           "quality_checks": {"negation_detected": False, "temporality_detected": False, "speaker_attribution_available": False, "unsupported_clinical_claims": [], "contradictions_detected": [], "ambiguous_entities": [], "requires_clinician_review": False}}
    cc = s1.get("chief_complaint")
    if isinstance(cc, str):
        out["chief_complaint"]["value"] = _s(cc)
    elif cc is not None:
        problems.append({"kind": "adapter_failure", "where": "chief_complaint", "msg": "not a string; skipped"})

    def items(name):
        v = s1.get(name)
        if v is None:
            return []
        if not isinstance(v, list):
            problems.append({"kind": "adapter_failure", "where": name, "msg": "not a list; section skipped"})
            return []
        good = []
        for i, x in enumerate(v):
            if isinstance(x, dict):
                good.append(x)
            else:
                problems.append({"kind": "adapter_failure", "where": f"{name}[{i}]", "msg": "item is not an object; skipped"})
        return good

    for x in items("symptoms"):
        st = _s(x.get("status"))
        out["symptoms"].append({"name": _s(x.get("name")), "normalized_name": None, "category": None, "status": st, "severity": None, "duration": parse_duration(x.get("duration")), "frequency": None, "onset": None,
                                "temporality": {"present": "current", "resolved": "resolved"}.get(st), "body_site": None, "associated_symptoms": [], "aggravating_factors": [], "relieving_factors": [],
                                "reported_by": _role(x.get("reported_by")), "certainty": None, "evidence_ids": [], "confidence": None})
    for x in items("negative_findings"):
        out["negative_findings"].append({"finding": _s(x.get("finding")), "normalized_name": None, "status": "absent", "assertion": "negative", "reported_by": _role(x.get("reported_by")), "temporality": "current",
                                         "evidence_ids": [], "confidence": None})
    mh = out["medical_history"]
    for x in items("medical_history"):
        mh["past_medical_history"].append({"condition": _s(x.get("condition")), "normalized_condition": None, "status": "ongoing", "duration": parse_duration(x.get("duration")), "reported_by": _role(x.get("reported_by")),
                                           "evidence_ids": [], "confidence": None})
    for x in items("current_conditions"):
        out["clinical_conditions"].append({"name": _s(x.get("condition")), "normalized_name": None, "status": "existing", "duration": None, "reported_by": _role(x.get("reported_by")), "evidence_ids": [], "confidence": None})
    for x in items("surgical_history"):
        mh["surgical_history"].append({"procedure": _s(x.get("procedure")), "normalized_procedure": None, "timeframe": _s(x.get("when")), "reported_by": _role(x.get("reported_by")), "evidence_ids": [], "confidence": None})
    for x in items("family_history"):
        mh["family_history"].append({"condition": _s(x.get("condition")), "normalized_condition": None, "relation": _s(x.get("relation")), "reported_by": _role(x.get("reported_by")), "evidence_ids": [], "confidence": None})
    for x in items("social_history"):
        mh["social_history"].append({"category": _s(x.get("category")), "description": _s(x.get("detail")), "status": _s(x.get("status")), "details": _s(x.get("detail")), "reported_by": _role(x.get("reported_by")),
                                     "evidence_ids": [], "confidence": None})
    for x in items("medications"):
        out["medications"].append({"name": _s(x.get("name")), "normalized_name": None, "generic_name": None, "dose": _s(x.get("dose")), "route": _s(x.get("route")), "frequency": _s(x.get("frequency")), "duration": None,
                                   "indication": None, "status": {"current": "currently_used", "stopped": "discontinued", "new": "planned"}.get(_s(x.get("status"))), "reported_by": _role(x.get("reported_by")),
                                   "evidence_ids": [], "confidence": None})
    ast = s1.get("allergy_status")
    for x in items("allergies"):
        out["allergies"].append({"substance": _s(x.get("substance")), "normalized_substance": None, "allergy_type": None, "reaction": _s(x.get("reaction")), "severity": "unknown", "status": "reported",
                                 "reported_by": _role(x.get("reported_by")), "evidence_ids": [], "confidence": None})
    if ast == "none_stated" and not any(isinstance(n, dict) and str(n.get("finding")).lower() == "allergies" for n in out["negative_findings"]):
        out["negative_findings"].append({"finding": "Allergies", "normalized_name": "No known allergies", "status": "absent", "assertion": "negative", "reported_by": "patient", "temporality": "current", "evidence_ids": [], "confidence": None})
    for x in items("vital_signs"):
        v = _s(x.get("value")) if isinstance(x.get("value"), str) else x.get("value")
        if isinstance(v, str) and re.fullmatch(r"\d+", v):
            v = int(v)
        elif isinstance(v, str) and re.fullmatch(r"\d+\.\d+", v):
            v = float(v)
        out["vital_signs"].append({"name": _s(x.get("name")), "normalized_name": None, "value": v, "unit": _s(x.get("unit")), "reported_by": _role(x.get("reported_by")), "evidence_ids": [], "confidence": None})
    for x in items("physical_examination"):
        out["physical_examination"].append({"finding": _s(x.get("finding")), "normalized_finding": None, "body_site": _s(x.get("body_site")), "status": "present", "observed_by": None, "evidence_ids": [], "confidence": None})
    for x in items("review_of_systems"):
        out["review_of_systems"].append({"system": _s(x.get("system")), "status": "negative", "details": _s(x.get("details")), "reported_by": _role(x.get("reported_by")), "evidence_ids": [], "confidence": None})
    for x in items("clinical_assessment"):
        out["clinical_assessment"].append({"assessment": _s(x.get("assessment")), "normalized_assessment": None, "certainty": _s(x.get("certainty")), "basis": None, "stated_by": "doctor", "evidence_ids": [], "confidence": None})
    for x in items("investigations"):
        out["procedures_and_investigations"].append({"name": _s(x.get("name")), "normalized_name": None, "type": _s(x.get("type")), "status": {"planned": "planned", "done": "completed", "conditional": "conditional"}.get(_s(x.get("status"))),
                                                     "requested_by": None, "indication": None, "scheduled_datetime": None, "evidence_ids": [], "confidence": None})
    for x in items("procedures"):
        out["procedures_and_investigations"].append({"name": _s(x.get("name")), "normalized_name": None, "type": "other", "status": {"planned": "planned", "done": "completed", "conditional": "conditional"}.get(_s(x.get("status"))),
                                                     "requested_by": None, "indication": None, "scheduled_datetime": None, "evidence_ids": [], "confidence": None})
    for x in items("clinical_actions"):
        t = _s(x.get("type"))
        order = t in ("medication", "investigation", "referral", "follow_up")
        out["clinical_actions"].append({"action_type": t, "description": _s(x.get("description")), "status": "planned" if order else ("recommended" if t in ("counselling", "other") else None),
                                        "responsible_person": "doctor" if order else ("patient" if t in ("counselling", "other") else None), "time_reference": None, "evidence_ids": [], "confidence": None})
    for x in items("follow_up"):
        out["follow_up"].append({"type": "consultation", "time_reference": _s(x.get("when")), "normalized_datetime": None, "status": _s(x.get("status")), "evidence_ids": []})
    return out, problems
