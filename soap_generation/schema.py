"""Parse and normalise the note returned by the agent. The frontend and the renderer can then rely on one exact shape; missing keys become empty values,
nothing is invented, and an answer that is not a note at all is rejected so the caller can ask once more."""
from __future__ import annotations

import json
import re
from typing import Any


class NoteFormatError(ValueError):
    pass


T_ROS_ITEM = {"system": "", "finding": ""}
TEMPLATE: dict[str, Any] = {
    "note_type": "",
    "encounter": {"encounter_id": "", "date_of_service": "", "patient_age_sex": "", "visit_type": "", "participants": [""], "informants": [""]},
    "subjective": {
        "chief_complaint": "", "hpi": "",
        "hpi_elements": {"onset": "", "location": "", "duration": "", "character": "", "aggravating": "", "alleviating": "", "timing": "", "severity": "", "associated": ""},
        "review_of_systems": {"positive": [T_ROS_ITEM], "negative": [T_ROS_ITEM], "not_reviewed": ""},
        "past_medical_history": [""], "past_surgical_history": [""], "family_history": [""], "social_history": [""],
        "medications": [{"name": "", "dose": "", "route": "", "frequency": "", "status": "", "comment": ""}],
        "allergies": {"status": "", "items": [{"substance": "", "reaction": "", "comment": ""}], "comment": ""},
    },
    "objective": {
        "vital_signs": [{"name": "", "value": "", "unit": "", "comment": ""}],
        "physical_exam": [{"system": "", "finding": ""}],
        "diagnostics": [{"item": "", "result": "", "comment": ""}],
        "comment": "",
    },
    "assessment": {
        "summary": "",
        "problems": [{"number": 0, "problem": "", "status": "", "clinician_impression": "", "reasoning": "", "icd10_suggestion": None}],
        "differential": [""],
    },
    "plan": {
        "by_problem": [{"problem_number": 0, "diagnostics": [""], "treatment": [""], "patient_education": [""], "referrals": [""], "follow_up": ""}],
        "return_precautions": [""], "follow_up": "", "care_coordination": [""],
    },
    "clinician_review": {"items_to_verify": [{"ref": "", "topic": "", "reason": ""}], "documentation_gaps": [""], "attestation": ""},
}
ALLERGY_STATUS = {"reported", "none_reported", "not_documented"}
ATTESTATION = ("Draft prepared from an ambient recording of the encounter. Requires review, editing and signature by the treating clinician before it becomes "
               "part of the medical record.")


def parse_json(text: str) -> dict:
    s = (text or "").strip()
    s = re.sub(r"^```(?:json)?\s*|\s*```$", "", s, flags=re.I).strip()
    if not s.startswith("{"):
        a, b = s.find("{"), s.rfind("}")
        if a < 0 or b <= a:
            raise NoteFormatError("the answer contains no JSON object")
        s = s[a:b + 1]
    try:
        data = json.loads(s)
    except json.JSONDecodeError as exc:
        raise NoteFormatError(f"the answer is not valid JSON ({exc.msg} at position {exc.pos})") from None
    if not isinstance(data, dict):
        raise NoteFormatError("the answer is not a JSON object")
    return data


def _text(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, str):
        return v.strip()
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return str(v)
    if isinstance(v, list):
        return "; ".join(x for x in (_text(i) for i in v) if x)
    if isinstance(v, dict):
        return "; ".join(x for x in (_text(i) for i in v.values()) if x)
    return ""


def _empty(v: Any) -> bool:
    if isinstance(v, str):
        return not v.strip()
    if isinstance(v, list):
        return not v
    if isinstance(v, dict):
        return all(_empty(x) for k, x in v.items() if k not in ("number", "problem_number"))
    return v is None


def _fit(value: Any, template: Any) -> Any:
    if isinstance(template, str):
        return _text(value)
    if isinstance(template, int):
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0
    if template is None:                                              # optional ICD-10 suggestion
        if isinstance(value, dict) and _text(value.get("code")):
            return {"code": _text(value.get("code")), "description": _text(value.get("description"))}
        return None
    if isinstance(template, list):
        item = template[0]
        if value is None or value == "":
            return []
        seq = value if isinstance(value, list) else [value]
        fitted = [_fit(v, item) for v in seq]
        return [f for f in fitted if not _empty(f)]
    if isinstance(template, dict):
        src = value if isinstance(value, dict) else {}
        return {k: _fit(src.get(k), t) for k, t in template.items()}
    return value


def normalise(raw: dict) -> tuple[dict, list[str]]:
    """(note in the exact shape, issues). Raises NoteFormatError when the answer is not a note."""
    present = [k for k in ("subjective", "objective", "assessment", "plan") if isinstance(raw.get(k), dict)]
    if len(present) < 3:
        raise NoteFormatError("the answer is missing the SOAP sections")
    note = _fit(raw, TEMPLATE)
    issues = [f"section '{k}' was missing" for k in ("subjective", "objective", "assessment", "plan") if k not in present]

    note["note_type"] = note["note_type"] or "Outpatient progress note (SOAP)"
    allergies = note["subjective"]["allergies"]
    if allergies["status"] not in ALLERGY_STATUS:
        allergies["status"] = "reported" if allergies["items"] else "not_documented"
    if allergies["status"] == "reported" and not allergies["items"]:
        allergies["status"] = "not_documented"
        issues.append("allergy status 'reported' without any allergy item was reset to 'not_documented'")
    if allergies["status"] != "reported":
        allergies["items"] = [] if allergies["status"] == "not_documented" else allergies["items"]

    problems = note["assessment"]["problems"]
    for i, p in enumerate(problems, 1):
        p["number"] = i
    count = len(problems)
    for i, plan in enumerate(note["plan"]["by_problem"], 1):
        if not 1 <= plan["problem_number"] <= max(count, 1):
            plan["problem_number"] = min(i, max(count, 1))
    note["clinician_review"]["attestation"] = note["clinician_review"]["attestation"] or ATTESTATION
    return note, issues
