"""Step 2: turn a label or a model output into a flat list of atomic facts that a judge (or a human) can read one by one.

A fact is {"fid", "field", "text", "attributes"}. `text` is a short human sentence; `attributes` keeps the clinically meaningful key/values
(dose, status, duration ...). Evidence ids, confidence numbers, and fields that only repeat another field (normalized_*) are dropped: they are not
clinical claims. Nothing is repaired or invented; empty values are omitted. The same function is used for labels and predictions so both sides are
described identically.
"""
from __future__ import annotations

from typing import Any

# Skipped as keys inside a fact: provenance and bookkeeping, not clinical content.
DROP_KEYS = {"evidence_ids", "confidence", "confirmed_by", "related_entities_ids"}
# Primary text key per field (first non-empty wins); remaining keys become attributes.
HEADLINE = {
    "chief_complaint": ("value", "normalized_value"), "symptoms": ("name", "normalized_name"), "negative_findings": ("finding", "normalized_name"),
    "medications": ("name", "normalized_name", "generic_name"), "allergies": ("substance", "normalized_substance"),
    "vital_signs": ("name", "type", "measurement", "vital_sign"), "physical_examination": ("finding", "normalized_finding"),
    "review_of_systems": ("system",), "clinical_conditions": ("condition", "name", "normalized_condition"),
    "clinical_assessment": ("assessment", "normalized_assessment"), "procedures_and_investigations": ("name", "normalized_name"),
    "clinical_actions": ("description", "action_type"), "follow_up": ("description", "instruction", "action", "type"),
    "clinical_uncertainties": ("description", "type"),
    "medical_history.past_medical_history": ("condition", "normalized_condition"), "medical_history.surgical_history": ("procedure", "name", "normalized_procedure"),
    "medical_history.family_history": ("condition", "relation", "normalized_condition"), "medical_history.social_history": ("factor", "category", "description", "type"),
}
LIST_FIELDS = ["symptoms", "negative_findings", "medications", "allergies", "vital_signs", "physical_examination", "review_of_systems",
               "clinical_conditions", "clinical_assessment", "procedures_and_investigations", "clinical_actions", "follow_up", "clinical_uncertainties"]
HISTORY_FIELDS = ["past_medical_history", "surgical_history", "family_history", "social_history"]
FIELDS = ["chief_complaint"] + [f"medical_history.{h}" for h in HISTORY_FIELDS] + LIST_FIELDS


def _empty(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}


def _clean(value: Any) -> Any:
    """Drop empties recursively; keep scalars as they are."""
    if isinstance(value, dict):
        out = {k: _clean(v) for k, v in value.items() if k not in DROP_KEYS}
        return {k: v for k, v in out.items() if not _empty(v)}
    if isinstance(value, list):
        return [v for v in (_clean(x) for x in value) if not _empty(v)]
    return value


def _render(value: Any) -> str:
    if isinstance(value, dict):
        if "normalized" in value and value["normalized"]:
            return str(value["normalized"])
        return ", ".join(f"{k}: {_render(v)}" for k, v in value.items())
    if isinstance(value, list):
        return "; ".join(_render(v) for v in value)
    return str(value)


def _fact(fid: str, field: str, item: Any) -> dict[str, Any] | None:
    if isinstance(item, str):                                   # some small-model outputs put plain strings in a list field
        return {"fid": fid, "field": field, "text": item.strip(), "attributes": {}} if item.strip() else None
    if not isinstance(item, dict):
        return None
    attrs = _clean(item)
    if not attrs:
        return None
    head = next((attrs[k] for k in HEADLINE.get(field, ()) if k in attrs), None)
    if head is None:
        head = next(iter(attrs.values()))
    rest = {k: v for k, v in attrs.items() if k not in HEADLINE.get(field, ()) or attrs.get(k) != head}
    rest = {k: v for k, v in rest.items() if not k.startswith("normalized_") and k != "normalized"}
    detail = ", ".join(f"{k}={_render(v)}" for k, v in rest.items())
    return {"fid": fid, "field": field, "text": _render(head) + (f" ({detail})" if detail else ""), "attributes": rest}


def flatten(doc: Any) -> list[dict[str, Any]]:
    """Atomic facts of one extraction document. Tolerates the shape differences between runs (dict vs list assessment, missing fields)."""
    if not isinstance(doc, dict):
        return []
    facts: list[dict[str, Any]] = []

    def add(field: str, item: Any) -> None:
        fid = f"{field}[{sum(1 for f in facts if f['field'] == field)}]"
        fact = _fact(fid, field, item)
        if fact:
            facts.append(fact)

    cc = doc.get("chief_complaint")
    if isinstance(cc, dict):
        add("chief_complaint", cc)
    history = doc.get("medical_history")
    if isinstance(history, dict):
        for h in HISTORY_FIELDS:
            for item in history.get(h) or []:
                add(f"medical_history.{h}", item)
    for field in LIST_FIELDS:
        value = doc.get(field)
        if isinstance(value, (dict, str)):                       # e.g. a run that returned clinical_assessment as one object, or a bare string
            value = [value]
        if not isinstance(value, list):
            continue
        for item in value or []:
            add(field, item)
    return facts
