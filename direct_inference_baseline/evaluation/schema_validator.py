"""Structural validation of a parsed prediction against the finalized schema.

Authority: root `clinical_extraction_schema.json` (top-level structure, category names, and the field sets of the categories
that its example populates) reconciled with the frozen dataset's `final_label_schema.json` (field sets for the categories the
example leaves empty, plus enum values). Reconciliation is checked at import time; neither file is modified.

Definitions
- valid_json is decided elsewhere (output_parser). Here: schema_compliant = no structural violation of any kind.
- violations: missing_top_level, unexpected_top_level, wrong_type, missing_field, unexpected_field, enum_violation.
- required_field_completeness = present_required_keys / expected_required_keys, where expected keys are the 20 top-level keys
  plus every field of every entity the model emitted plus the fields of the nested objects that must exist.
- unexpected_field_rate = unexpected keys / all keys emitted."""
from __future__ import annotations

import json
from dataclasses import dataclass, field

from ..config import settings as S

ROOT = json.loads(S.ROOT_SCHEMA.read_text(encoding="utf-8"))
FINAL = json.loads(S.FINAL_SCHEMA.read_text(encoding="utf-8"))
TOP_KEYS = list(ROOT.keys())
assert TOP_KEYS == FINAL["top_level_keys"], "root schema and frozen schema disagree on top-level keys"
CATS = FINAL["categories"]
ENUMS = FINAL["enums"]
NESTED = FINAL["nested_keys"]
# reconciliation: wherever the root example populates a category, its key set must equal the frozen key set
_ROOT_LISTS = {"symptoms": ROOT["symptoms"], "negative_findings": ROOT["negative_findings"], "medications": ROOT["medications"],
               "allergies": ROOT["allergies"], "procedures_and_investigations": ROOT["procedures_and_investigations"],
               "clinical_actions": ROOT["clinical_actions"], "follow_up": ROOT["follow_up"]}
for _c, _v in _ROOT_LISTS.items():
    assert set(_v[0]) == set(CATS[_c]["keys"]), f"root example and frozen schema differ for {_c}"
assert set(ROOT["chief_complaint"]) == set(CATS["chief_complaint"]["keys"])
assert set(ROOT["quality_checks"]) == set(NESTED["quality_checks"])
assert set(ROOT["clinical_evidence"][0]) == set(NESTED["clinical_evidence"])

LIST_CATS = [c for c in CATS if c not in ("chief_complaint",) and not c.startswith("medical_history.")]
HIST = ["past_medical_history", "surgical_history", "family_history", "social_history"]
ROLES = set(FINAL["roles"])
ROLE_FIELDS = ("reported_by", "observed_by", "stated_by")


@dataclass
class SchemaReport:
    compliant: bool = False
    violations: list = field(default_factory=list)
    keys_expected: int = 0
    keys_present: int = 0
    keys_emitted: int = 0
    keys_unexpected: int = 0
    counts: dict = field(default_factory=dict)

    def add(self, kind: str, msg: str):
        self.violations.append({"kind": kind, "message": msg})
        self.counts[kind] = self.counts.get(kind, 0) + 1


def _check_entity(rep: SchemaReport, where: str, e, keys: list):
    if not isinstance(e, dict):
        rep.add("wrong_type", f"{where} is not an object")
        rep.keys_expected += len(keys)
        return
    rep.keys_expected += len(keys)
    for k in keys:
        if k in e:
            rep.keys_present += 1
        else:
            rep.add("missing_field", f"{where}.{k}")
    for k in e:
        rep.keys_emitted += 1
        if k not in keys:
            rep.keys_unexpected += 1
            rep.add("unexpected_field", f"{where}.{k}")
    for rk in ROLE_FIELDS:
        if rk in e and e[rk] is not None and e[rk] not in ROLES:
            rep.add("enum_violation", f"{where}.{rk}={e[rk]!r}")
    for k in ("evidence_ids",):
        if k in e and not isinstance(e[k], list):
            rep.add("wrong_type", f"{where}.{k} should be a list")


def _enum_checks(rep: SchemaReport, pred: dict):
    for path, allowed in ENUMS.items():
        if path == "extraction_status":
            vals = [("extraction_status", pred.get("extraction_status"))]
        elif path == "encounter_metadata.encounter_type":
            md = pred.get("encounter_metadata")
            vals = [("encounter_type", md.get("encounter_type"))] if isinstance(md, dict) else []
        else:
            cat = max((c for c in CATS if path.startswith(c + ".")), key=len)
            field_ = path[len(cat) + 1:]
            obj = pred
            try:
                for part in cat.split("."):
                    obj = obj[part]
            except (KeyError, TypeError):
                continue
            if not isinstance(obj, list):
                continue
            vals = [(f"{cat}[{i}].{field_}", e.get(field_)) for i, e in enumerate(obj) if isinstance(e, dict) and field_ in e]
        for where, v in vals:
            if v not in allowed and not (path == "medications.route" and v is None):
                rep.add("enum_violation", f"{where}={v!r}")
    for i, s in enumerate(pred.get("symptoms") or []):
        if isinstance(s, dict) and "category" in s and s["category"] not in _VOCAB:
            rep.add("enum_violation", f"symptoms[{i}].category={s['category']!r}")


_VOCAB = {"constitutional", "neurological", "cardiovascular", "respiratory", "gastrointestinal", "musculoskeletal", "dermatological",
          "endocrine", "genitourinary", "ENT", "ophthalmological", "psychiatric", "other"}


def validate(pred: dict) -> SchemaReport:
    rep = SchemaReport()
    if not isinstance(pred, dict):
        rep.add("wrong_type", "prediction is not an object")
        return rep
    rep.keys_expected += len(TOP_KEYS)
    for k in TOP_KEYS:
        if k in pred:
            rep.keys_present += 1
        else:
            rep.add("missing_top_level", k)
    for k in pred:
        rep.keys_emitted += 1
        if k not in TOP_KEYS:
            rep.keys_unexpected += 1
            rep.add("unexpected_top_level", k)
    for scalar in ("encounter_id", "extraction_status"):
        if scalar in pred and not isinstance(pred[scalar], str):
            rep.add("wrong_type", f"{scalar} should be a string")
    md = pred.get("encounter_metadata")
    if "encounter_metadata" in pred:
        if isinstance(md, dict):
            _check_entity(rep, "encounter_metadata", md, NESTED["encounter_metadata"])
            sp = md.get("primary_speakers")
            if isinstance(sp, list):
                for i, s in enumerate(sp):
                    _check_entity(rep, f"encounter_metadata.primary_speakers[{i}]", s, NESTED["primary_speakers"])
            elif "primary_speakers" in md:
                rep.add("wrong_type", "primary_speakers should be a list")
        else:
            rep.add("wrong_type", "encounter_metadata should be an object")
    if "chief_complaint" in pred:
        _check_entity(rep, "chief_complaint", pred["chief_complaint"], CATS["chief_complaint"]["keys"])
    mh = pred.get("medical_history")
    if "medical_history" in pred:
        if isinstance(mh, dict):
            _check_entity(rep, "medical_history", {k: 1 for k in mh}, HIST)
            for h in HIST:
                lst = mh.get(h)
                if lst is None:
                    continue
                if not isinstance(lst, list):
                    rep.add("wrong_type", f"medical_history.{h} should be a list")
                    continue
                for i, e in enumerate(lst):
                    _check_entity(rep, f"medical_history.{h}[{i}]", e, CATS[f"medical_history.{h}"]["keys"])
        else:
            rep.add("wrong_type", "medical_history should be an object")
    for c in LIST_CATS:
        if c not in pred:
            continue
        lst = pred[c]
        if not isinstance(lst, list):
            rep.add("wrong_type", f"{c} should be a list")
            continue
        for i, e in enumerate(lst):
            _check_entity(rep, f"{c}[{i}]", e, CATS[c]["keys"])
    if "clinical_evidence" in pred and isinstance(pred["clinical_evidence"], list):
        for i, e in enumerate(pred["clinical_evidence"]):
            if isinstance(e, dict):
                _check_entity(rep, f"clinical_evidence[{i}]", e, NESTED["clinical_evidence"])
                if "supports" in e and not isinstance(e["supports"], list):
                    rep.add("wrong_type", f"clinical_evidence[{i}].supports should be a list")
                if e.get("speaker_role") not in ROLES:
                    rep.add("enum_violation", f"clinical_evidence[{i}].speaker_role={e.get('speaker_role')!r}")
    if "quality_checks" in pred:
        _check_entity(rep, "quality_checks", pred["quality_checks"], NESTED["quality_checks"])
    _enum_checks(rep, pred)
    rep.compliant = not rep.violations
    return rep


def completeness(rep: SchemaReport) -> float:
    return rep.keys_present / rep.keys_expected if rep.keys_expected else 0.0
