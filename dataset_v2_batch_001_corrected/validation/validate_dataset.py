"""Automated validation for dataset_v2_batch_001.

Everything here is an AUTOMATED check (schema, timing, evidence alignment,
lexical grounding, simple clinical-consistency rules, duplicate detection).
It is not clinical review.  No record is marked "human reviewed" anywhere.

usage:  python validate_dataset.py [--root <dataset dir>] [--write]
"""
import argparse
import os
import collections
import hashlib
import itertools
import json
import re
import sys
from pathlib import Path

ROLES = {"DOCTOR", "PATIENT", "NURSE", "CAREGIVER", "FAMILY_MEMBER", "CLINICAL_STAFF", "UNKNOWN"}
SEG_KEYS = ["segment_id", "speaker_id", "role", "start_seconds", "end_seconds", "duration_seconds", "text"]
TOP_KEYS = ["encounter_id", "extraction_status", "encounter_metadata", "chief_complaint", "symptoms", "negative_findings",
            "medical_history", "medications", "allergies", "vital_signs", "physical_examination", "review_of_systems",
            "clinical_conditions", "clinical_assessment", "procedures_and_investigations", "clinical_actions", "follow_up",
            "clinical_uncertainties", "clinical_evidence", "quality_checks"]
HIST_KEYS = ["past_medical_history", "surgical_history", "family_history", "social_history"]
EXPECT = {  # entity key sets (order-insensitive)
    "chief_complaint": {"value", "normalized_value", "reported_by", "evidence_ids"},
    "symptoms": {"name", "normalized_name", "category", "status", "severity", "duration", "frequency", "onset", "temporality",
                 "body_site", "associated_symptoms", "aggravating_factors", "relieving_factors", "reported_by", "certainty",
                 "evidence_ids", "confidence"},
    "negative_findings": {"finding", "normalized_name", "status", "assertion", "reported_by", "temporality", "evidence_ids", "confidence"},
    "medical_history.past_medical_history": {"condition", "normalized_condition", "status", "duration", "reported_by", "evidence_ids", "confidence"},
    "medical_history.surgical_history": {"procedure", "normalized_procedure", "timeframe", "reported_by", "evidence_ids", "confidence"},
    "medical_history.family_history": {"condition", "normalized_condition", "relation", "reported_by", "evidence_ids", "confidence"},
    "medical_history.social_history": {"category", "description", "status", "details", "reported_by", "evidence_ids", "confidence"},
    "medications": {"name", "normalized_name", "generic_name", "dose", "route", "frequency", "duration", "indication", "status",
                    "reported_by", "evidence_ids", "confidence"},
    "allergies": {"substance", "normalized_substance", "allergy_type", "reaction", "severity", "status", "reported_by", "evidence_ids", "confidence"},
    "vital_signs": {"name", "normalized_name", "value", "unit", "reported_by", "evidence_ids", "confidence"},
    "physical_examination": {"finding", "normalized_finding", "body_site", "status", "observed_by", "evidence_ids", "confidence"},
    "review_of_systems": {"system", "status", "details", "reported_by", "evidence_ids", "confidence"},
    "clinical_conditions": {"name", "normalized_name", "status", "duration", "reported_by", "evidence_ids", "confidence"},
    "clinical_assessment": {"assessment", "normalized_assessment", "certainty", "basis", "stated_by", "evidence_ids", "confidence"},
    "procedures_and_investigations": {"name", "normalized_name", "type", "status", "requested_by", "indication", "scheduled_datetime",
                                      "evidence_ids", "confidence"},
    "clinical_actions": {"action_type", "description", "status", "responsible_person", "time_reference", "evidence_ids", "confidence"},
    "follow_up": {"type", "time_reference", "normalized_datetime", "status", "evidence_ids"},
    "clinical_uncertainties": {"type", "description", "related_entities", "resolution_status", "evidence_ids", "confidence"},
}
LIST_PATHS = [p for p in EXPECT if p != "chief_complaint"]
NUMW = {0: "zero", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine",
        10: "ten", 11: "eleven", 12: "twelve", 14: "fourteen", 15: "fifteen", 20: "twenty", 30: "thirty"}
ALLERGY_FAMILY = {"penicillin": ["amoxicillin", "ampicillin", "penicillin", "cephalexin", "amoxicillin/clavulanic acid"],
                  "aspirin": ["ibuprofen", "diclofenac", "naproxen", "etoricoxib", "mefenamic acid", "aspirin"],
                  "ibuprofen": ["ibuprofen", "diclofenac", "naproxen", "etoricoxib", "mefenamic acid", "aspirin"],
                  "sulfa drugs": ["trimethoprim", "sulfamethoxazole"], "codeine": ["codeine", "tramadol"]}
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import blueprint as _BP  # noqa: E402  (shared reference vocabulary only)

VOCAB = set(_BP.VOCAB)
_NC = collections.defaultdict(set)
for _p in _BP.PROFILES:
    for _s in _p["syms"]:
        _NC[_s[1].lower()].add(_BP.normcat(_s[2]))
SCHEMA = json.loads((Path(__file__).resolve().parents[1] / "schema" / "final_label_schema.json").read_text(encoding="utf-8"))
ENUMS = {k: set(x) for k, x in SCHEMA["enums"].items()}   # single source of truth (documented definitions live in the same file)
ACTION_STATUS = ENUMS["clinical_actions.status"]
ALLERGY_STATUS = ENUMS["allergies.status"]
UNC_TYPES = ENUMS["clinical_uncertainties.type"]
SCHEMA_CHECKS = {"enum_value", "input_schema", "label_schema", "id_match", "segment_ids", "speaker_ids", "roles", "speaker_role_consistency", "timestamps", "text",
                 "duration", "segment_count", "evidence_schema", "category_vocab", "category_mismatch", "confidence_not_null", "speaker_match",
                 "blueprint_leak", "action_status_vocab", "allergy_status_vocab", "uncertainty_type_vocab"}
EVIDENCE_CHECKS = {"evidence_unique", "evidence_alignment", "evidence_support", "supports_resolve", "supports_symmetry", "evidence_missing",
                   "evidence_resolve", "speaker_attribution", "evidence_lexical", "uncertainty_refs"}
RESOLVED_RX = re.compile(r"(that's gone now|went away|has settled|that's settled|gone away|it's gone|settled by itself|gone now)")
SOFT_SEG = (35, 70)
HARD_SEG = (30, 80)
HARD_DUR = (300.0, 540.0)


def N(t):
    return re.sub(r"\s+", " ", str(t).lower().replace("’", "'")).strip()


def ts(x):
    s = int(x)
    return f"{s // 60:02d}:{s % 60:02d}"


def yours(p):
    p = re.sub(r"\bmy\b", "your", p, flags=re.I)
    p = re.sub(r"\bI'm\b", "you're", p)
    p = re.sub(r"\bI\b", "you", p)
    return re.sub(r"\bme\b", "you", p)


def resolve(label, loc):
    """'symptoms[2]' / 'medical_history.family_history[0]' / 'chief_complaint' -> entity dict or None"""
    if loc == "chief_complaint":
        return label.get("chief_complaint")
    m = re.match(r"^([a-z_.]+)\[(\d+)\]$", loc)
    if not m:
        return None
    path, i = m.group(1), int(m.group(2))
    obj = label
    for part in path.split("."):
        if not isinstance(obj, dict) or part not in obj:
            return None
        obj = obj[part]
    if not isinstance(obj, list) or i >= len(obj):
        return None
    return obj[i]


def entities(label):
    out = []
    if "chief_complaint" in label:
        out.append(("chief_complaint", "chief_complaint", label["chief_complaint"]))
    for p in LIST_PATHS:
        obj = label
        try:
            for part in p.split("."):
                obj = obj[part]
        except Exception:
            continue
        for i, e in enumerate(obj):
            out.append((p, f"{p}[{i}]", e))
    return out


def numvars(n):
    n = int(n)
    v = {str(n)}
    if n in NUMW:
        v.add(NUMW[n])
    if n == 1:
        v |= {"a", "an", "one", "single"}
    return v


def has_dur(text, d):
    if not d:
        return True
    if d.get("value") is None:
        m = re.match(r"approximately (\d+) to (\d+) (\w+)", d.get("normalized") or "")
        if m:
            return all(any(re.search(rf"\b{x}\b", text) for x in numvars(int(n))) for n in m.groups()[:2])
        return True
    unit = d["unit"].rstrip("s")
    vs = "|".join(re.escape(x) for x in numvars(d["value"]))
    return re.search(rf"\b({vs})\s+{unit}s?\b", text) is not None


def has_dose(text, dose):
    m = re.match(r"^([\d.]+)\s*(\w+)", dose)
    if not m:
        return N(dose) in text
    num, unit = m.group(1), m.group(2)
    units = {"mg": ["mg", "milligram"], "g": ["g ", "gram"], "micrograms": ["microgram", "mcg"], "ml": ["ml"], "units": ["unit"], "sachet": ["sachet"]}
    ok_unit = any(u in text for u in units.get(unit, [unit]))
    ok_num = re.search(rf"(?<![\d.]){re.escape(num)}(?![\d])", text) is not None
    if not ok_num and "." not in num and num.isdigit() and int(num) in NUMW:
        ok_num = NUMW[int(num)] in text
    return ok_num and ok_unit


class Result:
    def __init__(self):
        self.errors = []       # hard failures
        self.warnings = []     # soft issues
        self.lex = collections.Counter()      # (category, "checked"/"passed")
        self.lex_fail = []

    def err(self, check, msg):
        self.errors.append({"check": check, "message": msg})

    def warn(self, check, msg):
        self.warnings.append({"check": check, "message": msg})

    def lexcheck(self, cat, ok, msg):
        self.lex[(cat, "checked")] += 1
        if ok:
            self.lex[(cat, "passed")] += 1
        else:
            self.lex_fail.append({"category": cat, "message": msg})
            self.err("evidence_lexical", f"{cat}: {msg}")


def validate_input(inp, R):
    if list(inp.keys()) != ["schema_version", "encounter_id", "segments"]:
        R.err("input_schema", f"unexpected top-level keys {list(inp.keys())}")
        return
    if inp["schema_version"] != "1.0":
        R.err("input_schema", "schema_version != 1.0")
    if not re.fullmatch(r"\d{5}", str(inp["encounter_id"])):
        R.err("input_schema", "encounter_id not 5 digits")
    segs = inp["segments"]
    if not isinstance(segs, list) or not segs:
        R.err("input_schema", "no segments")
        return
    seen, spk_role, prev_end, starts = set(), {}, 0.0, set()
    for i, s in enumerate(segs):
        if list(s.keys()) != SEG_KEYS:
            R.err("input_schema", f"segment {i} keys {list(s.keys())}")
            continue
        if s["segment_id"] != f"SEG{i + 1:04d}" or s["segment_id"] in seen:
            R.err("segment_ids", f"{s['segment_id']} not sequential/unique")
        seen.add(s["segment_id"])
        if not re.fullmatch(r"person_\d+", s["speaker_id"]):
            R.err("speaker_ids", f"bad speaker id {s['speaker_id']}")
        if s["role"] not in ROLES:
            R.err("roles", f"bad role {s['role']}")
        if spk_role.setdefault(s["speaker_id"], s["role"]) != s["role"]:
            R.err("speaker_role_consistency", f"{s['speaker_id']} has two roles")
        if s["start_seconds"] < 0 or s["end_seconds"] <= s["start_seconds"]:
            R.err("timestamps", f"{s['segment_id']} invalid times")
        if abs((s["end_seconds"] - s["start_seconds"]) - s["duration_seconds"]) > .011:
            R.err("timestamps", f"{s['segment_id']} duration mismatch")
        if s["start_seconds"] < prev_end - 1e-9:
            R.err("timestamps", f"{s['segment_id']} overlaps/precedes previous segment")
        if s["start_seconds"] in starts:
            R.err("timestamps", f"{s['segment_id']} identical start time")
        starts.add(s["start_seconds"])
        prev_end = s["end_seconds"]
        if not isinstance(s["text"], str) or len(s["text"].split()) < 1:
            R.err("text", f"{s['segment_id']} empty text")
        if len(s["text"].split()) > 90:
            R.warn("dialogue_length", f"{s['segment_id']} very long ({len(s['text'].split())} words)")
    n, dur = len(segs), segs[-1]["end_seconds"]
    if not (HARD_DUR[0] <= dur <= HARD_DUR[1]):
        R.err("duration", f"duration {dur}s outside {HARD_DUR}")
    if not (HARD_SEG[0] <= n <= HARD_SEG[1]):
        R.err("segment_count", f"{n} segments outside hard range {HARD_SEG}")
    elif not (SOFT_SEG[0] <= n <= SOFT_SEG[1]):
        R.warn("segment_count_soft", f"{n} segments outside target {SOFT_SEG}")
    roles = {s["role"] for s in segs}
    if "DOCTOR" not in roles or "PATIENT" not in roles:
        R.err("roles", "encounter lacks DOCTOR or PATIENT")


def validate_label(inp, lab, R):
    if list(lab.keys()) != TOP_KEYS:
        R.err("label_schema", f"top-level keys/order differ: {list(lab.keys())}")
        return
    if lab["encounter_id"] != inp["encounter_id"]:
        R.err("id_match", "label encounter_id != input encounter_id")
    if lab["extraction_status"] != "completed":
        R.err("label_schema", "extraction_status not 'completed'")
    segs = inp["segments"]
    seg_index = {}
    for s in segs:
        seg_index.setdefault((s["speaker_id"], s["role"].lower(), N(s["text"]), ts(s["start_seconds"]), ts(s["end_seconds"])), s)
    # metadata
    md = lab["encounter_metadata"]
    spk = {(s["speaker_id"], s["role"].lower()) for s in segs}
    mspk = {(p["speaker_id"], p["role"]) for p in md.get("primary_speakers", [])}
    if spk != mspk:
        R.err("speaker_match", "primary_speakers differ from transcript speakers")
    # entity shape
    if list(lab["medical_history"].keys()) != HIST_KEYS:
        R.err("label_schema", "medical_history keys")
    for path, loc, e in entities(lab):
        if set(e.keys()) != EXPECT[path]:
            R.err("label_schema", f"{loc} keys differ: +{set(e) - EXPECT[path]} -{EXPECT[path] - set(e)}")
    # confidence must be null (no independently assessed confidence exists)
    def _walk(o, loc):
        if isinstance(o, dict):
            for k, x in o.items():
                if k in ("confidence", "role_confidence") and x is not None:
                    R.err("confidence_not_null", f"{loc}.{k} = {x!r}: artificial confidence value")
                else:
                    _walk(x, f"{loc}.{k}")
        elif isinstance(o, list):
            for i, x in enumerate(o):
                _walk(x, f"{loc}[{i}]")
    _walk(lab, "label")
    # every enumerated field must use a documented value
    for epath, allowed in ENUMS.items():
        if epath in ("extraction_status",):
            if lab["extraction_status"] not in allowed:
                R.err("enum_value", f"extraction_status {lab['extraction_status']!r}")
            continue
        if epath == "encounter_metadata.encounter_type":
            if lab["encounter_metadata"]["encounter_type"] not in allowed:
                R.err("enum_value", "encounter_type")
            continue
        cat = max((c for c in SCHEMA["categories"] if epath.startswith(c + ".")), key=len)
        field = epath[len(cat) + 1:]
        obj = lab
        for part in cat.split("."):
            obj = obj[part]
        for k_, e_ in enumerate(obj):
            if e_.get(field) not in allowed and not (field == "route" and e_.get(field) is None):
                R.err("enum_value", f"{cat}[{k_}].{field} = {e_.get(field)!r} is not a documented value")
    # category vocabulary and plausibility
    for i_, s_ in enumerate(lab["symptoms"]):
        c = s_["category"]
        if c not in VOCAB:
            R.err("category_vocab", f"symptoms[{i_}] category '{c}' not in controlled vocabulary")
        else:
            known = _NC.get(s_["normalized_name"].lower())
            if known and c not in known:
                R.err("category_mismatch", f"symptoms[{i_}] '{s_['normalized_name']}' has category '{c}', expected one of {sorted(known)}")
        if s_["certainty"] not in ("certain", "uncertain", "disputed"):
            R.err("category_vocab", f"symptoms[{i_}] certainty '{s_['certainty']}'")
        if s_["status"] == "present" and s_["temporality"] != "current":
            R.err("temporality", f"symptoms[{i_}] status present but temporality {s_['temporality']}")
        if s_["status"] == "resolved" and s_["temporality"] not in ("resolved", "past"):
            R.err("temporality", f"symptoms[{i_}] status resolved but temporality {s_['temporality']}")
        if s_["status"] == "present" and s_["temporality"] == "current" and s_["onset"] and re.search(r"last year|years ago|months ago|last winter", s_["onset"]):
            R.err("temporality", f"symptoms[{i_}] historical onset '{s_['onset']}' labelled as current")
    for a_ in lab["allergies"]:
        if a_["status"] not in ALLERGY_STATUS:
            R.err("allergy_status_vocab", f"allergy status {a_['status']}")
    for a_ in lab["clinical_actions"]:
        if a_["status"] not in ACTION_STATUS:
            R.err("action_status_vocab", f"action status {a_['status']}")
    for u_ in lab["clinical_uncertainties"]:
        if u_["type"] not in UNC_TYPES:
            R.err("uncertainty_type_vocab", f"uncertainty type {u_['type']}")
    # evidence records
    ev = {}
    for r in lab["clinical_evidence"]:
        if set(r.keys()) != {"evidence_id", "speaker_id", "speaker_role", "transcript_text", "start_timestamp", "end_timestamp", "supports"}:
            R.err("evidence_schema", f"evidence keys {list(r.keys())}")
            continue
        if r["evidence_id"] in ev:
            R.err("evidence_unique", f"duplicate {r['evidence_id']}")
        ev[r["evidence_id"]] = r
        key = (r["speaker_id"], r["speaker_role"], N(r["transcript_text"]), r["start_timestamp"], r["end_timestamp"])
        if key not in seg_index:
            R.err("evidence_alignment", f"{r['evidence_id']} does not match any transcript segment (speaker/role/text/timestamps)")
        if not r["supports"]:
            R.err("evidence_support", f"{r['evidence_id']} supports nothing")
        for loc in r["supports"]:
            ent = resolve(lab, loc)
            if ent is None:
                R.err("supports_resolve", f"{r['evidence_id']} supports nonexistent {loc}")
            elif r["evidence_id"] not in ent.get("evidence_ids", []):
                R.err("supports_symmetry", f"{loc} does not list {r['evidence_id']}")
    ents = entities(lab)
    ev_text = {}
    for path, loc, e in ents:
        ids = e.get("evidence_ids", [])
        if not ids:
            R.err("evidence_missing", f"{loc} has no evidence")
        for i in ids:
            if i not in ev:
                R.err("evidence_resolve", f"{loc} cites unknown {i}")
            elif loc not in ev[i]["supports"]:
                R.err("supports_symmetry", f"{i} does not list {loc}")
        text = " ".join(N(ev[i]["transcript_text"]) for i in ids if i in ev)
        ev_text[loc] = text
        roles = {ev[i]["speaker_role"] for i in ids if i in ev}
        rb = e.get("reported_by") or e.get("observed_by") or e.get("stated_by")
        if rb and path not in ("clinical_actions",) and rb not in roles:
            R.err("speaker_attribution", f"{loc} attributed to {rb} but evidence speakers are {sorted(roles)}")
    # ---- lexical grounding of every extracted value
    def chk(cat, loc, cond, what):
        R.lexcheck(cat, cond, f"{loc}: {what} not found in its evidence")
    for path, loc, e in ents:
        t = ev_text.get(loc, "")
        if path == "chief_complaint":
            chk("chief_complaint", loc, N(e["value"]) in t or N(yours(e["value"])) in t, f"'{e['value']}'")
        elif path == "symptoms":
            chk("symptom_name", loc, N(e["name"]) in t or N(yours(e["name"])) in t, f"'{e['name']}'")
            if e["duration"]:
                chk("symptom_duration", loc, has_dur(t, e["duration"]), f"duration {e['duration']}")
            if e["onset"]:
                chk("symptom_onset", loc, N(e["onset"]) in t, f"onset '{e['onset']}'")
            if e["frequency"]:
                chk("symptom_frequency", loc, N(e["frequency"]) in t, f"frequency '{e['frequency']}'")
            if e["severity"]:
                sv = e["severity"]
                if "/" in sv:
                    n = int(sv.split("/")[0])
                    chk("symptom_severity", loc, any(re.search(rf"\b{v}\b", t) for v in numvars(n)) and "ten" in t, f"severity {sv}")
                else:
                    chk("symptom_severity", loc, sv in t, f"severity {sv}")
            for a in e["aggravating_factors"] + e["relieving_factors"]:
                chk("symptom_factors", loc, N(a) in t, f"factor '{a}'")
            if e["status"] == "resolved" and e["temporality"] == "resolved":
                chk("symptom_resolved", loc, any(w in t for w in ("gone", "went away", "settled", "resolved")), "resolution wording")
            if e["certainty"] == "disputed" and e["reported_by"] not in ("caregiver", "family_member"):
                R.err("conflict_logic", f"{loc} disputed but not third-party reported")
        elif path == "negative_findings":
            chk("negative_finding", loc, N(e["finding"]) in t or N(e["finding"]).rstrip("s") in t, f"'{e['finding']}'")
            # patient must actually negate
            chk("negation_cue", loc, bool(re.search(r"\b(no|not|none|nothing|never|haven't|don't|nope)\b", t)), "negation cue")
        elif path == "medical_history.past_medical_history":
            chk("pmh", loc, N(e["condition"]) in t, f"'{e['condition']}'")
            if e["duration"]:
                chk("pmh_duration", loc, has_dur(t, e["duration"]), f"duration {e['duration']}")
        elif path == "medical_history.surgical_history":
            chk("surgery", loc, N(e["procedure"]) in t and N(e["timeframe"]) in t, f"'{e['procedure']}'/'{e['timeframe']}'")
        elif path == "medical_history.family_history":
            chk("family_history", loc, N(e["relation"]) in t and N(e["condition"]) in t, f"{e['relation']}/{e['condition']}")
        elif path == "medical_history.social_history":
            chk("social_history", loc, (e["details"] is None or N(e["details"]) in t) and (e["category"] not in ("smoking", "alcohol") or bool(re.search(r"smok|cigarette|drink|alcohol|beer", t))), f"{e['category']}")
        elif path == "medications":
            chk("medication_name", loc, N(e["name"]) in t, f"'{e['name']}'")
            if e["dose"]:
                chk("medication_dose", loc, has_dose(t, e["dose"]), f"dose {e['dose']}")
            if e["frequency"]:
                chk("medication_frequency", loc, N(e["frequency"]) in t, f"frequency '{e['frequency']}'")
            if e["indication"]:
                chk("medication_indication", loc, N(e["indication"]) in t, f"indication '{e['indication']}'")
            if e["duration"] and e["duration"].get("normalized"):
                d = e["duration"]
                chk("medication_duration", loc, has_dur(t, d) if d["value"] is not None else N(d["normalized"]) in t, f"duration {d}")
        elif path == "allergies":
            chk("allergy", loc, N(e["substance"]) in t, f"'{e['substance']}'")
            if e["reaction"]:
                chk("allergy_reaction", loc, N(e["reaction"]) in t, f"reaction '{e['reaction']}'")
        elif path == "vital_signs":
            v = str(e["value"])
            parts = v.split("/")
            ok = all(re.search(rf"(?<![\d.]){re.escape(p)}(?![\d])", t) for p in parts)
            chk("vital_sign", loc, ok, f"{e['name']} {v}")
        elif path == "physical_examination":
            chk("exam_finding", loc, N(e["finding"]) in t, f"'{e['finding']}'")
        elif path == "clinical_conditions":
            chk("condition", loc, N(e["name"]) in t, f"'{e['name']}'")
        elif path == "clinical_assessment":
            chk("assessment", loc, N(e["assessment"]) in t, f"'{e['assessment']}'")
            if e["certainty"] not in ("provisional", "differential", "uncertain"):
                R.err("confirmed_diagnosis", f"{loc} certainty '{e['certainty']}' - unconfirmed assessment must not be confirmed")
        elif path == "procedures_and_investigations":
            chk("investigation", loc, N(e["name"]) in t, f"'{e['name']}'")
            if e["scheduled_datetime"]:
                chk("investigation_schedule", loc, all(N(x) in t for x in e["scheduled_datetime"].split(" at ")), f"schedule '{e['scheduled_datetime']}'")
        elif path == "follow_up":
            chk("follow_up", loc, N(e["time_reference"]) in t, f"'{e['time_reference']}'")
        elif path == "review_of_systems":
            chk("review_of_systems", loc, bool(re.search(r"\b(no|nothing|normal|fine)\b", t)), "denial cue")
        elif path == "clinical_actions" and e["action_type"] == "medication":
            ids = set(e["evidence_ids"])
            ok = any(m["status"] == "planned" and ids & set(m["evidence_ids"]) for m in lab["medications"])
            chk("action_medication", loc, ok, "a planned medication entity sharing this action's evidence")
    # ---- clinical action / investigation support
    STOP = {"advise", "arrange", "refer", "start", "seek", "urgent", "care", "consider", "follow", "consultation", "symptoms", "persist",
            "avoid", "adequate", "regular", "daily", "performed", "before", "pending", "until", "excluded", "bring", "latest", "next", "visit", "from", "with", "that", "this"}
    PLAN_CUE = re.compile(r"arrange|order|get|book|request|send|like|want|do |think|should|plan|schedule|slot|earliest|prescrib|start|use|take|let's|refer|see you|see me|come back|review|need|next|check|catch up|back|look into|treatment|going to|again|plan|taking|you'll|be on|put you|look|for this|treatment|using|use ")
    for path, loc, e in ents:
        if path not in ("clinical_actions", "procedures_and_investigations"):
            continue
        ids = e["evidence_ids"]
        txts = [N(ev[i]["transcript_text"]) for i in ids if i in ev]
        roles = {ev[i]["speaker_role"] for i in ids if i in ev}
        t = " ".join(txts)
        if path == "clinical_actions":
            if e["action_type"] == "investigation":
                ids_ = set(e["evidence_ids"])
                R.lexcheck("action_support", any(ids_ & set(p_["evidence_ids"]) for p_ in lab["procedures_and_investigations"]),
                           f"{loc}: no investigation entity shares this action's evidence")
            if e["action_type"] == "referral":
                R.lexcheck("action_support", bool(re.search(r"refer|see|seen|letter|send", t)), f"{loc}: no referral wording in evidence")
            sents = [x for tx in txts for x in re.split(r"(?<=[.!?])\s+", tx.strip()) if x]
            if all(x.rstrip().endswith("?") and len(x.split()) <= 14 and not PLAN_CUE.search(x) for x in txts):
                R.err("action_support", f"{loc}: supported only by questions")
            if e["responsible_person"] == "doctor" and e["status"] in ("planned", "conditional") and "doctor" not in roles:
                R.err("action_support", f"{loc}: planned by doctor but no doctor evidence (patient suggestion treated as decision?)")
            if e["status"] == "completed" and not re.search(r"\b(did|already|had)\b", t):
                R.err("action_status", f"{loc}: completed without completion wording")
            if e["status"] == "planned" and not PLAN_CUE.search(t):
                R.err("action_status", f"{loc}: planned/recommended without plan wording")
        else:
            if e["status"] == "completed" and not re.search(r"\b(did|already|had)\b", t):
                R.err("action_status", f"{loc}: investigation marked completed but evidence only proposes it")
            if e["status"] == "planned" and not PLAN_CUE.search(t):
                R.err("action_status", f"{loc}: investigation planned without plan wording")
            if e["status"] == "conditional" and not re.search(r"if |hold off|might|consider|not now|revisit|not ordering", t):
                R.err("action_status", f"{loc}: conditional investigation without conditional wording")
            if e["requested_by"] == "doctor" and not (roles & {"doctor", "nurse", "clinical_staff"}):
                R.err("action_support", f"{loc}: doctor-requested but no clinician evidence")
    # ---- allergy / negative-finding consistency
    mentioned = any("allerg" in N(s["text"]) for s in segs)
    nk = [n for n in lab["negative_findings"] if n["finding"] == "Allergies"]
    al_ = lab["allergies"]
    disputed_unc = any(u["type"] == "allergy_disputed" for u in lab["clinical_uncertainties"])
    if nk and al_ and not disputed_unc:
        R.err("allergy_consistency", "explicit 'no known allergies' coexists with an allergy entry without an allergy_disputed uncertainty")
    if any(a["status"] == "disputed" for a in al_) and not disputed_unc:
        R.err("allergy_consistency", "disputed allergy without allergy_disputed uncertainty")
    if not nk and not al_ and mentioned:
        R.err("allergy_consistency", "allergies are discussed in the transcript but nothing was extracted")
    if (nk or al_) and not mentioned:
        R.err("allergy_consistency", "allergy information extracted but allergies are never discussed")
    # ---- unresolved dose disagreement must not become a confirmed dose
    for i_, m in enumerate(lab["medications"]):
        nm = N(m["name"])
        doses = set()
        other_names = [N(x["name"]) for x in lab["medications"] if x is not m]
        carry = False
        for i in sorted(m["evidence_ids"]):
            if i not in ev:
                continue
            if ev[i]["speaker_role"] not in ("patient", "caregiver", "family_member", "nurse"):
                carry = False
                continue
            for sent in re.split(r"(?<=[.!?])\s+", N(ev[i]["transcript_text"])):
                mm = None
                if nm in sent:
                    tail = sent[sent.index(nm):]
                    mm = re.search(r"(\d+(?:\.\d+)?) (?:milligram|microgram)", tail)
                    carry = True
                elif carry and not any(o in sent for o in other_names):
                    mm = re.search(r"(\d+(?:\.\d+)?) (?:milligram|microgram)", sent)   # "...it's 150 milligrams" refers to the drug just named
                else:
                    carry = False
                if mm:
                    doses.add(mm.group(1))
        if len(doses) >= 2:
            has_u = any(u["type"] in ("medication_discrepancy", "uncertain_dose") and f"medications[{i_}]" in u["related_entities"] for u in lab["clinical_uncertainties"])
            if not has_u:
                R.err("silent_correction", f"medications[{i_}] speakers state different doses {sorted(doses)} but no discrepancy uncertainty recorded")
            if m["dose"] is not None and m["status"] == "currently_used":
                R.err("silent_correction", f"medications[{i_}] has dose {m['dose']} although speakers disagree")
    # ---- clinical consistency rules
    meds = lab["medications"]
    names = [m["name"].lower() for m in meds]
    if len(names) != len(set(names)):
        R.err("medication_consistency", "duplicate medication names")
    for al in lab["allergies"]:
        sub = al["substance"].lower()
        for fam in ALLERGY_FAMILY.get(sub, []):
            for m in meds:
                if m["status"] == "planned" and (fam in (m["generic_name"] or "").lower() or fam in m["name"].lower()):
                    R.err("allergy_medication_conflict", f"planned {m['name']} conflicts with reported allergy {sub}")
    sym_norm = {s["normalized_name"] for s in lab["symptoms"] if s["certainty"] != "disputed" and s["status"] == "present" and s["temporality"] == "current"}
    for n in lab["negative_findings"]:
        if n["normalized_name"] in sym_norm:
            R.err("negation_contradiction", f"'{n['normalized_name']}' both denied and present")
    exam_present = {f["normalized_finding"].lower() for f in lab["physical_examination"] if f["status"] == "present"}
    for n in lab["negative_findings"]:
        if n["normalized_name"].lower() in exam_present:
            R.err("negation_contradiction", f"'{n['normalized_name']}' denied but examined present")
    vs = {v["name"]: v["value"] for v in lab["vital_signs"]}
    if "Blood pressure" in vs:
        s_, d_ = (int(x) for x in str(vs["Blood pressure"]).split("/"))
        if not (60 < s_ < 230 and 30 < d_ < 140 and s_ - d_ >= 20):
            R.err("vital_plausibility", f"BP {vs['Blood pressure']}")
    for nme, lo, hi in (("Heart rate", 35, 190), ("Temperature", 34.5, 42), ("Oxygen saturation", 80, 100), ("Respiratory rate", 8, 40)):
        if nme in vs and not lo <= float(vs[nme]) <= hi:
            R.err("vital_plausibility", f"{nme} {vs[nme]}")
    if all(k in vs for k in ("Weight", "Height", "BMI")):
        bmi = vs["Weight"] / (vs["Height"] / 100) ** 2
        if abs(bmi - vs["BMI"]) > .15:
            R.err("vital_consistency", f"BMI {vs['BMI']} != {bmi:.1f}")
    pmh = {p["normalized_condition"] for p in lab["medical_history"]["past_medical_history"]}
    for c in lab["clinical_conditions"]:
        if c["normalized_name"] not in pmh:
            R.err("condition_support", f"condition {c['normalized_name']} not in history")
    unc = lab["clinical_uncertainties"]
    for u in unc:
        for loc in u["related_entities"]:
            if resolve(lab, loc) is None:
                R.err("uncertainty_refs", f"related entity {loc} does not exist")
        if u["type"] == "medication_discrepancy":
            for loc in u["related_entities"]:
                ent = resolve(lab, loc)
                if ent and ent.get("dose") is not None:
                    R.err("silent_correction", f"{loc} has a dose recorded although a discrepancy is unresolved")
    q = lab["quality_checks"]
    if (unc or q["contradictions_detected"] or q["ambiguous_entities"]) and not q["requires_clinician_review"]:
        R.err("quality_checks", "uncertainty present but requires_clinician_review false")
    if any(s["certainty"] == "disputed" for s in lab["symptoms"]) and not q["contradictions_detected"]:
        R.err("quality_checks", "disputed symptom but no contradiction recorded")
    if q["negation_detected"] != bool(lab["negative_findings"]):
        R.err("quality_checks", "negation_detected inconsistent")
    if q["speaker_attribution_available"] != all(s["role"] != "UNKNOWN" for s in segs):
        R.err("quality_checks", "speaker_attribution_available inconsistent")
    # blueprint leakage guard
    blob = json.dumps(inp) + json.dumps(lab)
    for bad in ('"features"', '"blueprint"', '"profile"', '"complexity"', '"seed"'):
        if bad in blob:
            R.err("blueprint_leak", f"found {bad} in evaluation files")


def validate_record(inp, lab):
    R = Result()
    validate_input(inp, R)
    if not R.errors or all(e["check"] not in ("input_schema",) for e in R.errors):
        validate_label(inp, lab, R)
    return R


# ------------------------------------------------------------------ dataset level
def shingles(text, n=5):
    w = re.findall(r"[a-z0-9']+", text.lower())
    return {" ".join(w[i:i + n]) for i in range(max(0, len(w) - n + 1))}


def dataset_checks(root: Path, inputs, labels, bps, report):
    ids = sorted(inputs)
    # --- duplicates
    sh = {i: shingles(" ".join(s["text"] for s in inputs[i]["segments"])) for i in ids}
    inv = collections.defaultdict(list)
    for i, S in sh.items():
        for g in S:
            inv[g].append(i)
    pair_common = collections.Counter()
    for g, lst in inv.items():
        if 1 < len(lst) <= 40:
            for a, b in itertools.combinations(lst, 2):
                pair_common[(a, b)] += 1
    near = []
    maxj = 0.0
    for (a, b), c in pair_common.items():
        j = c / (len(sh[a]) + len(sh[b]) - c)
        maxj = max(maxj, j)
        if j >= 0.45:
            near.append({"a": a, "b": b, "jaccard_5gram": round(j, 3)})
    full = collections.Counter(hashlib.md5(" ".join(s["text"] for s in inputs[i]["segments"]).encode()).hexdigest() for i in ids)
    exact = sum(c - 1 for c in full.values() if c > 1)
    first = collections.Counter(N(inputs[i]["segments"][0]["text"]) for i in ids)
    first_two = collections.Counter(tuple(N(s["text"]) for s in inputs[i]["segments"][:2]) for i in ids)
    seg_text = collections.Counter()
    for i in ids:
        for t in {N(s["text"]) for s in inputs[i]["segments"] if len(s["text"].split()) >= 5}:
            seg_text[t] += 1
    heavy = [(t, c) for t, c in seg_text.most_common(15)]
    sym_combo = collections.Counter(tuple(sorted(s["normalized_name"] for s in labels[i]["symptoms"] if s["temporality"] == "current")) for i in ids)
    fp = collections.Counter()
    for i in ids:
        L = labels[i]
        fp[(bps[i]["profile"] if i in bps else "", tuple(sorted(s["normalized_name"] for s in L["symptoms"])),
            tuple(sorted((m["name"], m["status"]) for m in L["medications"])), tuple(sorted(a["assessment"] for a in L["clinical_assessment"])))] += 1
    role_pat = collections.Counter(tuple(s["role"][:2] for s in inputs[i]["segments"][:14]) for i in ids)
    timeline = collections.Counter(tuple(round(s["start_seconds"], 1) for s in inputs[i]["segments"][:10]) for i in ids)
    dup_scn = sum(c - 1 for c in fp.values() if c > 1)
    report["duplicate_report"] = {
        "encounters": len(ids), "exact_duplicate_conversations": exact,
        "near_duplicate_pairs_jaccard_ge_0.45": near, "max_pairwise_5gram_jaccard": round(maxj, 3),
        "opening_sentence_unique": len(first), "opening_sentence_max_share": round(first.most_common(1)[0][1] / len(ids), 4),
        "top_openings": [[t, c] for t, c in first.most_common(5)],
        "first_two_turn_pairs_unique": len(first_two), "first_two_turn_pair_max_share": round(first_two.most_common(1)[0][1] / len(ids), 4),
        "most_repeated_full_segments(text,#encounters)": [[t, c] for t, c in heavy],
        "symptom_combinations_unique": len(sym_combo), "symptom_combination_max_repeat": sym_combo.most_common(1)[0][1],
        "scenario_fingerprint_duplicates(profile+symptoms+meds+assessment)": dup_scn,
        "role_pattern_first14_unique": len(role_pat), "role_pattern_max_share": round(role_pat.most_common(1)[0][1] / len(ids), 4),
        "identical_first10_timeline_vectors": sum(c - 1 for c in timeline.values() if c > 1),
        "duplicate_count": exact + len(near) + dup_scn,
    }
    return report


def load_dir(root: Path):
    inputs, labels = {}, {}
    for p in sorted((root / "output" / "inputs").glob("encounter_*.json")):
        inputs[p.stem.split("_")[1]] = json.loads(p.read_text(encoding="utf-8"))
    for p in sorted((root / "output" / "labels").glob("encounter_*.json")):
        labels[p.stem.split("_")[1]] = json.loads(p.read_text(encoding="utf-8"))
    bps = {}
    for p in sorted((root / "scenario_blueprints").glob("blueprint_*.json")):
        bps[p.stem.split("_")[1]] = json.loads(p.read_text(encoding="utf-8"))
    return inputs, labels, bps


def run(root: Path, write=False, expected=500):
    from collections import Counter
    inputs, labels, bps = load_dir(root)
    rep = {"total_input_files": len(inputs), "total_label_files": len(labels), "expected": expected}
    ids_ok = set(inputs) == set(labels)
    rep["input_label_ids_match"] = ids_ok
    per, lexc, lexfail = {}, collections.Counter(), []
    spec_c, cpl_c = Counter(), Counter()
    err_by_check, warn_by_check = Counter(), Counter()
    for i in sorted(inputs):
        if i not in labels:
            per[i] = {"status": "FAIL", "errors": [{"check": "missing_label", "message": "no label file"}]}
            continue
        R = validate_record(inputs[i], labels[i])
        status = "PASS" if not R.errors else "FAIL"
        per[i] = {"status": status, "errors": R.errors[:20], "warnings": R.warnings[:10]}
        lexc.update(R.lex)
        lexfail += [dict(f, encounter_id=i) for f in R.lex_fail]
        for e in R.errors:
            err_by_check[e["check"]] += 1
        for w in R.warnings:
            warn_by_check[w["check"]] += 1
        if i in bps:
            spec_c[bps[i]["spec"]] += 1
            cpl_c[bps[i]["complexity"]] += 1
    rep["per_record"] = per
    rep["pass_count"] = sum(1 for v in per.values() if v["status"] == "PASS")
    rep["fail_count"] = sum(1 for v in per.values() if v["status"] != "PASS")
    rep["errors_by_check"] = dict(err_by_check)
    groups = {"schema_validation": SCHEMA_CHECKS, "evidence_validation_errors": EVIDENCE_CHECKS}
    rep["error_groups"] = {"schema": {k: n for k, n in err_by_check.items() if k in SCHEMA_CHECKS},
                           "evidence": {k: n for k, n in err_by_check.items() if k in EVIDENCE_CHECKS},
                           "clinical_consistency": {k: n for k, n in err_by_check.items() if k not in SCHEMA_CHECKS and k not in EVIDENCE_CHECKS}}
    rep["warnings_by_check"] = dict(warn_by_check)
    rep["specialty_distribution"] = dict(spec_c)
    rep["complexity_distribution"] = dict(cpl_c)
    cats = sorted({c for c, _ in lexc})
    ev = {c: {"checked": lexc[(c, "checked")], "passed": lexc[(c, "passed")]} for c in cats}
    tot_c, tot_p = sum(v["checked"] for v in ev.values()), sum(v["passed"] for v in ev.values())
    evidence_report = {"method": "every extracted value is looked up (case-insensitive, number-word aware) in the transcript text of the evidence records that support it",
                       "caveat": "lexical grounding proves the value is literally stated in cited evidence; it does not prove clinical correctness",
                       "by_category": ev, "facts_checked": tot_c, "facts_grounded": tot_p,
                       "alignment_status": "ALL_GROUNDED" if tot_c == tot_p and tot_c > 0 else "FAILURES_PRESENT",
                       "failures": lexfail[:200], "failure_count": len(lexfail)}
    rep["evidence_alignment_status"] = evidence_report["alignment_status"]
    dataset_checks(root, inputs, labels, bps, rep)
    dup = rep.pop("duplicate_report")
    # profile / scenario diversity
    if bps:
        pc = collections.Counter(b["profile"] for b in bps.values())
        ic = collections.Counter((b["profile"], tuple(sorted(s["norm"] for s in b["syms"])), tuple(sorted(m["name"] for m in b["meds"])),
                                  b["assess"]["primary"]) for b in bps.values())
        div = {"distinct_profiles": len(pc), "max_encounters_per_profile": max(pc.values()), "mean_encounters_per_profile": round(len(bps) / len(pc), 2),
               "profiles_used_more_than_6_times": sorted(k for k, n in pc.items() if n > 6),
               "age_band_distribution": dict(collections.Counter(b.get("age_band") for b in bps.values())),
               "plan_mode_distribution": dict(collections.Counter(b.get("plan_mode") for b in bps.values())),
               "assessment_mode_distribution": dict(collections.Counter(b.get("assess_mode") for b in bps.values())),
               "allergy_representation": dict(collections.Counter(b["allergies"]["kind"] for b in bps.values())),
               "repeated_clinical_identity": sum(c - 1 for c in ic.values() if c > 1),
               "encounters_with_profile_changed_from_original": sum(1 for b in bps.values() if b.get("profile_original") != b["profile"])}
        dup["profile_diversity"] = div
    if write:
        v = root / "validation"
        (v / "validation_report.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False), encoding="utf-8")
        (v / "duplicate_report.json").write_text(json.dumps(dup, indent=1, ensure_ascii=False), encoding="utf-8")
        (v / "evidence_validation.json").write_text(json.dumps(evidence_report, indent=1, ensure_ascii=False), encoding="utf-8")
        (v / "schema_validation.json").write_text(json.dumps({"scope": "JSON schema, key sets, controlled category vocabulary, null-confidence rule, "
                                                              "no confirmed_by, ids/timestamps/speakers", "records_checked": len(per),
                                                              "errors": rep["error_groups"]["schema"], "records_with_schema_errors": sum(
            1 for r_ in per.values() if any(e["check"] in SCHEMA_CHECKS for e in r_["errors"]))}, indent=1), encoding="utf-8")
        (v / "clinical_consistency_report.json").write_text(json.dumps({
            "disclaimer": "AUTOMATED rule checks only. This is NOT clinical review; no clinician has validated these records.",
            "records_checked": len(per), "errors": rep["error_groups"]["clinical_consistency"],
            "records_with_consistency_errors": sum(1 for r_ in per.values() if any(e["check"] not in SCHEMA_CHECKS and e["check"] not in EVIDENCE_CHECKS for e in r_["errors"])),
            "rules": ["negation vs present contradictions", "allergy vs planned prescription conflicts", "allergy represented distinctly (explicit none / not discussed / reported / unknown reaction / historical / disputed)",
                      "unresolved dose disagreement not converted to a dose", "planned vs completed investigation wording", "conditional investigations", "temporality vs status",
                      "unconfirmed diagnoses not marked confirmed", "vital plausibility/BMI", "conditions need history support", "action support (not only questions; clinician evidence)"]},
            indent=1), encoding="utf-8")
    return rep, dup, evidence_report


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    rep, dup, ev = run(Path(a.root), a.write)
    print(json.dumps({k: v for k, v in rep.items() if k != "per_record"}, indent=1)[:3500])
    print("evidence:", ev["alignment_status"], ev["facts_checked"], ev["facts_grounded"])
    print("duplicates:", dup["duplicate_count"], "max jaccard", dup["max_pairwise_5gram_jaccard"])
    sys.exit(0 if rep["fail_count"] == 0 else 1)
