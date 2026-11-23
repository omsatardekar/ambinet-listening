"""S0.2 (version S0.2.0): fill ABSENT keys of explicitly nullable fields with null. Separate layer applied on top of S0.1 output; pure library, no I/O.

"Explicitly nullable" is decided from two written sources only:
  1. the output template the model was given (prompts/P02_comprehensive_extraction.txt): the field's default there is `null` (verified against the template text by `verify_against_template`), and
  2. the frozen schema documents: unstated information is `null`; every `confidence` / `role_confidence` MUST be null (final_label_schema.json confidence_policy, FINAL_SCHEMA.md conventions).
Fields whose default is a list or an object (evidence_ids, associated_symptoms, duration objects ...) are NOT nullable and are never filled.
Rules: only add a key that is missing; never touch an existing value (including '' or any non-null value); never infer; every addition is logged; a second pass changes nothing.
This is a structural repair; it says nothing about clinical correctness."""
from __future__ import annotations

import copy
import re

S0_2_VERSION = "S0.2.0"
CONF = "confidence"
NULLABLE = {  # section -> fields whose template default is null (confidence handled separately)
    "symptoms": ["severity", "frequency", "onset", "body_site", CONF],
    "negative_findings": [CONF],
    "medical_history.past_medical_history": ["duration", CONF],
    "medical_history.surgical_history": ["timeframe", CONF],
    "medical_history.family_history": [CONF],
    "medical_history.social_history": ["details", CONF],
    "medications": ["generic_name", "dose", "route", "frequency", "duration", "indication", CONF, "normalized_name"],
    "allergies": ["reaction", CONF],
    "vital_signs": ["value", CONF],
    "physical_examination": ["body_site", CONF],
    "review_of_systems": ["details", CONF],
    "clinical_conditions": ["duration", CONF],
    "clinical_assessment": ["basis", CONF],
    "procedures_and_investigations": ["requested_by", "indication", "scheduled_datetime", CONF],
    "clinical_actions": ["time_reference", CONF],
    "follow_up": ["normalized_datetime"],
    "clinical_uncertainties": [CONF],
}
TEMPLATE_LINE_KEY = {"medical_history.past_medical_history": "past_medical_history", "medical_history.surgical_history": "surgical_history", "medical_history.family_history": "family_history",
                     "medical_history.social_history": "social_history"}


def verify_against_template(template_text):
    """Every (section, field) of NULLABLE must be `"field": null` on that section's line of the model template (confidence fields are covered by the schema policy and are checked too).
    Returns the list of problems (empty = consistent)."""
    problems = []
    lines = template_text.splitlines()
    for sec, fields in NULLABLE.items():
        key = TEMPLATE_LINE_KEY.get(sec, sec)
        ln = next((l for l in lines if re.search(r'"%s":\s*\[\{' % re.escape(key), l)), None)
        if ln is None:
            problems.append((sec, "section line not found"))
            continue
        for f in fields:
            if not re.search(r'"%s":\s*null' % re.escape(f), ln):
                problems.append((sec, f))
    return problems


def _items(pred):
    for sec in NULLABLE:
        if sec.startswith("medical_history."):
            mh = pred.get("medical_history")
            v = mh.get(sec.split(".", 1)[1]) if isinstance(mh, dict) else None
        else:
            v = pred.get(sec)
        if isinstance(v, list):
            for i, x in enumerate(v):
                if isinstance(x, dict):
                    yield f"{sec}[{i}]", sec, x


def fill(pred, enc_id):
    """returns (filled copy, log rows). `pred` is never modified."""
    out = copy.deepcopy(pred)
    rows = []

    def add(path, rule_field):
        rows.append({"encounter_id": enc_id, "kind": "change", "path": path, "original": "<key absent>", "repaired": None, "rule": "S0.2_fill_nullable_field",
                     "reason": f"'{rule_field}' is missing; its default in the model template and the schema convention is null", "deterministic": True, "human_review_required": False})
    for loc, sec, x in _items(out):
        for f in NULLABLE[sec]:
            if f not in x:
                x[f] = None
                add(f"{loc}.{f}", f)
    md = out.get("encounter_metadata")
    if isinstance(md, dict):
        if "encounter_date" not in md:
            md["encounter_date"] = None
            add("encounter_metadata.encounter_date", "encounter_date")
        for i, sp in enumerate(md.get("primary_speakers") or []):
            if isinstance(sp, dict) and "role_confidence" not in sp:
                sp["role_confidence"] = None
                add(f"encounter_metadata.primary_speakers[{i}].role_confidence", "role_confidence")
    return out, rows
