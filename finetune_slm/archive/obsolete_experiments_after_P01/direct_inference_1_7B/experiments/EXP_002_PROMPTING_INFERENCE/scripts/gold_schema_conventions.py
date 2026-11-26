"""Empirical conventions of the frozen GOLD labels (types, nullability, empty strings, enum values actually used, evidence/supports conventions) over the 50 authorised
prompt-development ids, read through the dataset guard.  Read-only analysis; writes evaluations/p02_review/GOLD_CONVENTIONS.json.  DEVELOPMENT-ONLY.
usage: python -B -s gold_schema_conventions.py"""
import collections
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
TRACK = HERE.parents[3]
sys.path.insert(0, str(TRACK / "scripts"))
import common_1_7b as C  # noqa: E402

sys.path.insert(0, str(C.EXP6 / "s1"))
import evaluate_s1 as E  # noqa: E402
from direct_inference_baseline.evaluation import evaluation_runner as ER  # noqa: E402

OUT = TRACK / "experiments" / "EXP_002_PROMPTING_INFERENCE" / "evaluations" / "p02_review"
OUT.mkdir(parents=True, exist_ok=True)
IDS = list(E.IDS)
assert len(IDS) == 50
SCH = json.loads((C.FINAL_SCHEMA if hasattr(C, "FINAL_SCHEMA") else C.S.FINAL_SCHEMA).read_text(encoding="utf-8"))


def tname(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "bool"
    if isinstance(v, int):
        return "int"
    if isinstance(v, float):
        return "float"
    if isinstance(v, str):
        return "string(empty)" if v == "" else "string"
    if isinstance(v, list):
        return "list"
    if isinstance(v, dict):
        return "object"
    return type(v).__name__


spy = C.G.StrictAccessSpy(allow_validation=False)
types = collections.defaultdict(collections.Counter)
vals = collections.defaultdict(collections.Counter)
evid = collections.Counter()
ex = collections.defaultdict(list)
with spy:
    for i in IDS:
        g = ER.load_gold(i)
        tr = json.loads((C.S.INPUT_DIR / f"encounter_{i}.json").read_text(encoding="utf-8"))
        segs = {s["segment_id"]: s for s in tr["segments"]}
        segtext = {re.sub(r"\s+", " ", s["text"]).strip().lower(): s for s in tr["segments"]}

        def walk(obj, path):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    p = f"{path}.{k}" if path else k
                    if isinstance(v, (dict,)):
                        types[p]["object"] += 1
                        walk(v, p)
                    elif isinstance(v, list):
                        types[p]["list"] += 1
                        for x in v:
                            if isinstance(x, dict):
                                walk(x, p + "[]")
                            else:
                                types[p + "[]"][tname(x)] += 1
                    else:
                        types[p][tname(v)] += 1
                        if isinstance(v, (str, bool)) or v is None:
                            if len(vals[p]) < 60 or v in vals[p]:
                                vals[p][v if not isinstance(v, str) else v[:40]] += 1
        walk(g, "")
        # evidence conventions
        evs = {e["evidence_id"]: e for e in g["clinical_evidence"]}
        for e in g["clinical_evidence"]:
            evid["records"] += 1
            s = segtext.get(re.sub(r"\s+", " ", e["transcript_text"]).strip().lower())
            if s:
                evid["text_is_exact_single_segment"] += 1
                mm = lambda x: f"{int(x) // 60:02d}:{int(x) % 60:02d}"  # noqa: E731
                evid["start_floor_ok"] += e["start_timestamp"] == mm(s["start_seconds"])
                evid["end_floor_ok"] += e["end_timestamp"] == mm(s["end_seconds"])
                evid["speaker_id_matches_line"] += e["speaker_id"] == s["speaker_id"]
                evid["role_lowercase_matches_line"] += e["speaker_role"] == s["role"].lower()
            evid["timestamp_format_MM:SS_ok"] += bool(re.fullmatch(r"\d\d:\d\d", e["start_timestamp"])) and bool(re.fullmatch(r"\d\d:\d\d", e["end_timestamp"]))
            evid["has_empty_supports"] += not e["supports"]
        # symmetric references
        paths = {}
        for cat in ["chief_complaint", "symptoms", "negative_findings", "medications", "allergies", "vital_signs", "physical_examination", "review_of_systems", "clinical_conditions", "clinical_assessment",
                    "procedures_and_investigations", "clinical_actions", "follow_up", "clinical_uncertainties"]:
            o = g[cat]
            if cat == "chief_complaint":
                paths["chief_complaint"] = o
            else:
                for n, x in enumerate(o):
                    paths[f"{cat}[{n}]"] = x
        for sub in ("past_medical_history", "surgical_history", "family_history", "social_history"):
            for n, x in enumerate(g["medical_history"][sub]):
                paths[f"medical_history.{sub}[{n}]"] = x
        sym_ok = True
        for e in g["clinical_evidence"]:
            for sp in e["supports"]:
                ent = paths.get(sp)
                if ent is None or e["evidence_id"] not in (ent.get("evidence_ids") or []):
                    sym_ok = False
        for pth, ent in paths.items():
            for eid in ent.get("evidence_ids") or []:
                if eid not in evs or pth not in evs[eid]["supports"]:
                    sym_ok = False
        evid["records_with_symmetric_references"] += sym_ok
        evid["records"] += 0
        evid["labels"] += 1
        # examples for specific questions
        for sub in ("past_medical_history",):
            for x in g["medical_history"][sub]:
                if len(ex["pmh"]) < 12:
                    ex["pmh"].append({"id": i, "condition": x["condition"], "status": x["status"], "duration": x["duration"]})
        for m in g["medications"]:
            if m.get("route") is not None and len(ex["route"]) < 10:
                ex["route"].append({"id": i, "name": m["name"], "route": m["route"]})
        for s in g["symptoms"]:
            if s["temporality"] != "current" and len(ex["past_symptoms"]) < 10:
                ex["past_symptoms"].append({"id": i, "name": s["name"], "status": s["status"], "temporality": s["temporality"]})
        for a in g["clinical_actions"]:
            if a.get("time_reference") is not None and len(ex["action_time"]) < 5:
                ex["action_time"].append({"id": i, "tr": a["time_reference"]})

# summaries
empty = {p: dict(c) for p, c in types.items() if "string(empty)" in c}
nullable = {p: dict(c) for p, c in types.items() if "null" in c}
mixed = {p: dict(c) for p, c in types.items() if len({k for k in c if k not in ("null",)}) > 1}
enum_used = {p: dict(vals[p]) for p in vals if any(x in p for x in ("route", "status", "category", "temporality", "certainty", "assertion", "allergy_type", "severity", "type", "resolution_status", "action_type", "responsible_person", "system", "unit"))}
res = {"ids": len(IDS), "fields_with_empty_strings": empty, "nullable_fields": nullable, "fields_with_mixed_types": mixed, "enum_like_values_used": enum_used, "evidence": dict(evid), "examples": ex,
       "all_field_types": {p: dict(c) for p, c in sorted(types.items())}}
(OUT / "GOLD_CONVENTIONS.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
print("empty-string fields:", json.dumps(empty))
print("evidence:", json.dumps(dict(evid)))
print("pmh/route/past_symptoms examples:", json.dumps(ex, ensure_ascii=False)[:1800])
for k in ("medications[].route", "medical_history.past_medical_history[].status", "medical_history.social_history[].status", "review_of_systems[].status", "review_of_systems[].details", "symptoms[].temporality", "symptoms[].status",
          "medications[].status", "allergies[].status", "allergies[].reaction", "clinical_actions[].time_reference", "follow_up[].time_reference", "follow_up[].normalized_datetime", "medical_history.past_medical_history[].duration",
          "medications[].duration", "vital_signs[].value", "vital_signs[].unit", "symptoms[].severity", "symptoms[].onset", "symptoms[].frequency"):
    print(k, dict(types.get(k, {})), dict(list(vals.get(k, {}).items())[:12]))
