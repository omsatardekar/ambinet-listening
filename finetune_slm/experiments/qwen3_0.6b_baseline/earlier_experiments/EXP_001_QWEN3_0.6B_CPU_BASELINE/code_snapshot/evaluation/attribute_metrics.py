"""Attribute accuracy on strictly matched entities (entity-level TP/FP/FN are unaffected by attribute errors).

For every attribute two numbers are reported, so that the many null values in the labels cannot inflate accuracy:
  accuracy_on_gold_nonnull  = correct / (matched entities whose GOLD value is not null)           (did the model get the stated value?)
  false_attribute_rate      = predicted-non-null / (matched entities whose GOLD value is null)    (did the model invent a value?)
Numeric/unit values are compared after normalisation; text values after norm_text."""
from __future__ import annotations

import re
from collections import Counter, defaultdict

from .entity_matching import norm_text


def _num_unit(v):
    """'500 mg' -> (500.0, 'mg'); '138/86' -> ('138/86', ''); returns None if not parseable."""
    if v is None:
        return None
    s = norm_text(v).replace(" / ", "/")
    m = re.match(r"^(\d+/\d+)\s*([a-z%]*)$", s)
    if m:
        return (m.group(1), m.group(2))
    m = re.match(r"^(\d+(?:\.\d+)?)\s*([a-z%]*)$", s)
    return (float(m.group(1)), m.group(2)) if m else None


def same_value(a, b) -> bool:
    if a is None or b is None:
        return a is None and b is None
    na, nb = _num_unit(a), _num_unit(b)
    if na and nb:
        return na == nb
    return norm_text(a) == norm_text(b)


def same_duration(g, p) -> bool:
    if g is None or p is None:
        return g is None and p is None
    if isinstance(g, dict) and isinstance(p, dict):
        if g.get("value") is not None and p.get("value") is not None:
            return float(g["value"]) == float(p["value"]) and norm_text(g.get("unit")) == norm_text(p.get("unit"))
        return norm_text(g.get("normalized")) == norm_text(p.get("normalized"))
    return norm_text(g) == norm_text(p)


def same_text(a, b) -> bool:
    return norm_text(a) == norm_text(b) if not (a is None or b is None) else (a is None and b is None)


# (category, attribute) -> comparator.  Names follow the requested list: severity, duration, dose, frequency, route,
# action status, temporality, negation (polarity), allergy reaction, uncertainty status.
ATTRS = {
    ("symptoms", "severity"): same_value, ("symptoms", "duration"): same_duration, ("symptoms", "frequency"): same_text,
    ("symptoms", "temporality"): same_text, ("symptoms", "status"): same_text, ("symptoms", "certainty"): same_text,
    ("negative_findings", "temporality"): same_text, ("negative_findings", "status"): same_text,
    ("negative_findings", "assertion"): same_text,
    ("medications", "dose"): same_value, ("medications", "frequency"): same_text, ("medications", "route"): same_text,
    ("medications", "status"): same_text, ("medications", "duration"): same_duration,
    ("allergies", "reaction"): same_text, ("allergies", "status"): same_text,
    ("clinical_actions", "status"): same_text, ("procedures_and_investigations", "status"): same_text,
    ("clinical_uncertainties", "resolution_status"): same_text, ("follow_up", "status"): same_text,
}
# friendly names for the requested report rows
REPORT_NAMES = {"severity": [("symptoms", "severity")], "duration": [("symptoms", "duration")], "dose": [("medications", "dose")],
                "medication_frequency": [("medications", "frequency")], "medication_route": [("medications", "route")],
                "action_status": [("clinical_actions", "status")], "investigation_status": [("procedures_and_investigations", "status")],
                "temporality": [("symptoms", "temporality"), ("negative_findings", "temporality")],
                "negation": [("negative_findings", "status"), ("negative_findings", "assertion")],
                "allergy_reaction": [("allergies", "reaction")],
                "uncertainty_status": [("symptoms", "certainty"), ("allergies", "status"), ("clinical_uncertainties", "resolution_status")]}


def score_pairs(pairs_by_cat: dict) -> dict:
    """pairs_by_cat: category -> list[(gold_entity, pred_entity)] -> raw counters per (category, attribute)."""
    out = defaultdict(lambda: Counter())
    conf = defaultdict(lambda: defaultdict(Counter))
    for cat, pairs in pairs_by_cat.items():
        for g, p in pairs:
            for (c, attr), cmp_ in ATTRS.items():
                if c != cat or attr not in g:
                    continue
                gv, pv = g.get(attr), p.get(attr)
                k = out[(c, attr)]
                if gv is not None:
                    k["gold_nonnull"] += 1
                    if cmp_(gv, pv):
                        k["correct"] += 1
                    if isinstance(gv, (str, int, float)) or attr in ("severity",):
                        conf[(c, attr)][str(gv)][str(pv)] += 1
                else:
                    k["gold_null"] += 1
                    if pv is not None:
                        k["invented"] += 1
    return {"counts": {f"{c}.{a}": dict(v) for (c, a), v in out.items()},
            "confusion": {f"{c}.{a}": {g: dict(pv) for g, pv in m.items()} for (c, a), m in conf.items()
                          if (a in ("status", "temporality", "certainty", "resolution_status", "severity"))}}


def summarize(counts: dict) -> dict:
    """counts: 'category.attr' -> summed counters. Returns accuracy rows (None = undefined, never 1.0)."""
    rows = {}
    for key, c in counts.items():
        gn, gz = c.get("gold_nonnull", 0), c.get("gold_null", 0)
        rows[key] = {"accuracy_on_gold_nonnull": c.get("correct", 0) / gn if gn else None, "n_gold_nonnull": gn,
                     "false_attribute_rate": c.get("invented", 0) / gz if gz else None, "n_gold_null": gz}
    named = {}
    for name, members in REPORT_NAMES.items():
        gn = sum(counts.get(f"{c}.{a}", {}).get("gold_nonnull", 0) for c, a in members)
        ok = sum(counts.get(f"{c}.{a}", {}).get("correct", 0) for c, a in members)
        gz = sum(counts.get(f"{c}.{a}", {}).get("gold_null", 0) for c, a in members)
        inv = sum(counts.get(f"{c}.{a}", {}).get("invented", 0) for c, a in members)
        named[name] = {"accuracy": ok / gn if gn else None, "correct": ok, "denominator_gold_nonnull_matched": gn,
                       "false_attribute_rate": inv / gz if gz else None, "denominator_gold_null_matched": gz}
    return {"by_field": rows, "requested": named}
