"""Builds the DRAFT S1.1 output JSON schema (design stage; not frozen). Writes design/S1_1_output_schema.json.
usage: python -B make_schema.py"""
import json
from pathlib import Path

ROLE = ["doctor", "patient", "nurse", "caregiver", "family_member", "clinical_staff", "unknown"]


def s(min1=False):
    return {"type": "string", "minLength": 1} if min1 else {"type": "string"}


def enum(v):
    return {"type": "string", "enum": v}


def item(props, required):
    return {"type": "object", "properties": props, "required": required, "additionalProperties": False}


def lst(it):
    return {"type": "array", "items": it}


rb = enum(ROLE)
schema = {"type": "object", "properties": {
    "chief_complaint": s(True),
    "symptoms": lst(item({"name": s(True), "status": enum(["present", "resolved"]), "duration": s(), "reported_by": rb}, ["name", "status", "reported_by"])),
    "negative_findings": lst(item({"finding": s(True), "reported_by": rb}, ["finding", "reported_by"])),
    "medical_history": lst(item({"condition": s(True), "duration": s(), "reported_by": rb}, ["condition", "reported_by"])),
    "surgical_history": lst(item({"procedure": s(True), "when": s(), "reported_by": rb}, ["procedure", "reported_by"])),
    "family_history": lst(item({"condition": s(True), "relation": s(True), "reported_by": rb}, ["condition", "relation", "reported_by"])),
    "social_history": lst(item({"category": enum(["smoking", "alcohol", "occupation", "exercise", "diet", "living"]), "status": enum(["current", "former", "never", "none", "retired"]),
                                "detail": s(), "reported_by": rb}, ["category", "reported_by"])),
    "medications": lst(item({"name": s(True), "dose": s(), "route": s(), "frequency": s(), "status": enum(["current", "stopped", "new"]), "reported_by": rb},
                            ["name", "status", "reported_by"])),
    "allergy_status": enum(["reported", "none_stated", "unknown", "not_asked"]),
    "allergies": lst(item({"substance": s(True), "reaction": s(), "reported_by": rb}, ["substance", "reported_by"])),
    "vital_signs": lst(item({"name": enum(["blood pressure", "pulse", "temperature", "respiratory rate", "oxygen saturation", "weight", "height", "BMI"]),
                             "value": s(True), "unit": s(), "reported_by": rb}, ["name", "value", "reported_by"])),
    "physical_examination": lst(item({"finding": s(True), "body_site": s(), "reported_by": rb}, ["finding", "reported_by"])),
    "review_of_systems": lst(item({"system": s(True), "details": s(), "reported_by": rb}, ["system", "reported_by"])),
    "clinical_assessment": lst(item({"assessment": s(True), "certainty": enum(["provisional", "differential"])}, ["assessment", "certainty"])),
    "investigations": lst(item({"name": s(True), "type": enum(["laboratory", "imaging", "cardiac", "other"]), "status": enum(["planned", "done", "conditional"])}, ["name", "status"])),
    "procedures": lst(item({"name": s(True), "status": enum(["planned", "done", "conditional"])}, ["name", "status"])),
    "clinical_actions": lst(item({"type": enum(["medication", "investigation", "counselling", "referral", "follow_up", "other"]), "description": s(True)}, ["type", "description"])),
    "follow_up": lst(item({"when": s(True), "status": enum(["planned", "conditional"])}, ["when", "status"])),
}, "required": ["chief_complaint", "symptoms", "negative_findings", "medical_history", "surgical_history", "family_history", "social_history", "medications", "allergy_status",
                "allergies", "vital_signs", "physical_examination", "review_of_systems", "clinical_assessment", "investigations", "procedures", "clinical_actions", "follow_up"],
    "additionalProperties": False}
out = Path(__file__).with_name("S1_1_output_schema.json")
out.write_text(json.dumps(schema, indent=1), encoding="utf-8")
print("written", out.name, len(out.read_text(encoding="utf-8")), "bytes;", len(schema["properties"]), "keys")
