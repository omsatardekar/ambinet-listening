"""Turn the saved clinical extraction into the input of the SOAP agent: a cleaned copy of the findings (every item gets a `ref`), the conversation passages
linked to each item, and rule-based flags for mistakes the upstream extraction is known to make (see docs/MODULE3_FINETUNING_FOCUS.md, failure classes F1 to F26).
Nothing here changes the stored extraction."""
from __future__ import annotations

import re
from typing import Any

Rec = dict[str, Any]

HIDDEN = {"evidence_ids", "confidence", "role_confidence", "normalized_name", "normalized_value", "normalized_condition", "normalized_procedure",
          "normalized_substance", "normalized_finding", "normalized_assessment", "normalized_datetime", "normalized_date", "related_entities"}
SKIP_SECTIONS = {"encounter_id", "extraction_status", "encounter_metadata", "quality_checks", "clinical_evidence"}
LABEL_KEYS = ("value", "name", "finding", "condition", "procedure", "substance", "assessment", "description", "system", "type")
ROLE_LABEL = {"DOCTOR": "Physician", "PATIENT": "Patient", "NURSE": "Nurse", "CAREGIVER": "Caregiver", "FAMILY_MEMBER": "Family member",
              "CLINICAL_STAFF": "Clinical staff", "UNKNOWN": "Unidentified speaker"}
MAX_PASSAGES, MAX_PASSAGE_CHARS = 3, 650
SENTENCE = re.compile(r"(?<=[.!?])\s+")
STOP_WORDS = {"that", "this", "with", "have", "from", "they", "them", "were", "been", "will", "your", "into", "present", "reported", "status"}
NEEDS_SOURCE = ("allergies", "medications", "vital_signs", "clinical_assessment", "follow_up", "clinical_actions", "procedures_and_investigations")


def _clock(s: Any) -> str:
    return f"{int(s // 60)}:{int(s % 60):02d}" if isinstance(s, (int, float)) else ""


def _flat(v: Any) -> Any:
    """{value, unit, normalized} style objects become one readable string."""
    if isinstance(v, dict):
        if isinstance(v.get("normalized"), str) and v["normalized"].strip():
            return v["normalized"].strip()
        if v.get("value") not in (None, "") and v.get("unit") not in (None, ""):
            return f"{v['value']} {v['unit']}"
        inner = {k: _flat(x) for k, x in v.items() if k not in HIDDEN}
        inner = {k: x for k, x in inner.items() if x not in (None, "", [], {})}
        return " ".join(str(x) for x in inner.values()) if inner and all(isinstance(x, (str, int, float)) for x in inner.values()) else inner
    if isinstance(v, list):
        return [x for x in (_flat(i) for i in v) if x not in (None, "", [], {})]
    return v


def _clean(item: Rec) -> Rec:
    out: Rec = {}
    for k, v in item.items():
        if k in HIDDEN:
            continue
        v = _flat(v)
        if v in (None, "", [], {}):
            continue
        out[k] = v
    return out


def label_of(item: Rec) -> str:
    for k in LABEL_KEYS:
        v = item.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


def annotate(extraction: Rec) -> dict[str, list[Rec]]:
    """{section: [item with `ref`]} in a flat, predictable shape; sections with nothing are left out."""
    sections: dict[str, list[Rec]] = {}

    def add(section: str, data: Any, path: str) -> None:
        items: list[Rec] = []
        if isinstance(data, list):
            for i, d in enumerate(data):
                if isinstance(d, dict) and _clean(d):
                    items.append({"ref": f"{path}[{i}]", **_clean(d)})
        elif isinstance(data, dict) and _clean(data):
            items.append({"ref": path, **_clean(data)})
        if items:
            sections[section] = items

    for key, value in extraction.items():
        if key in SKIP_SECTIONS:
            continue
        if key == "medical_history" and isinstance(value, dict):
            for sub, data in value.items():
                add(f"medical_history.{sub}", data, f"medical_history.{sub}")
        else:
            add(key, value, key)
    return sections


def _terms(item: Rec) -> set[str]:
    """Words of a finding that should be visible in its excerpt."""
    words: set[str] = set()
    for k, v in item.items():
        if k in ("ref", "status", "certainty", "reported_by", "stated_by", "observed_by", "requested_by", "responsible_person", "type", "category", "allergy_type"):
            continue
        words |= {w for w in re.findall(r"[a-z0-9/.]{4,}", str(v).lower()) if w not in STOP_WORDS}
    return words


def excerpt(text: str, terms: set[str], limit: int = MAX_PASSAGE_CHARS) -> str:
    """A long turn is shortened to the sentences that mention the finding (never simply the first N characters, which can cut off the very words that
    linked it), keeping their order; a question just before an answer is kept with it."""
    if len(text) <= limit:
        return text
    sents = SENTENCE.split(text)
    ranked = sorted(range(len(sents)), key=lambda i: (-sum(1 for t in terms if t in sents[i].lower()), i))
    keep: set[int] = set()
    used = 0
    for i in ranked:
        hit = any(t in sents[i].lower() for t in terms)
        if keep and not hit:
            break
        if keep and used + len(sents[i]) + 1 > limit:
            continue
        keep.add(i)
        used += len(sents[i]) + 1
        if i > 0 and sents[i - 1].rstrip().endswith("?") and used + len(sents[i - 1]) + 1 <= limit:
            keep.add(i - 1)
            used += len(sents[i - 1]) + 1
    if not keep:
        return text[:limit]
    order = sorted(keep)
    out = ""
    for n, i in enumerate(order):
        out += ("[...] " if (n == 0 and i > 0) or (n > 0 and i != order[n - 1] + 1) else (" " if n else "")) + sents[i]
    return (out + (" [...]" if order[-1] < len(sents) - 1 else ""))[: limit + 40]


def _passages(doc: Rec, refs: set[str], items: dict[str, Rec] | None = None) -> dict[str, list[Rec]]:
    out: dict[str, list[Rec]] = {}
    for fact in (doc.get("evidence") or {}).get("facts", []):
        if fact.get("path") not in refs:
            continue
        rows = []
        for s in fact.get("segments", []):
            if s.get("status") != "resolved" or not s.get("text"):
                continue
            rows.append({"speaker": ROLE_LABEL.get(s.get("role") or "", "Speaker"), "time": _clock(s.get("start_seconds")), "text": excerpt(s["text"], _terms((items or {}).get(fact["path"], {})))})
            if len(rows) == MAX_PASSAGES:
                break
        if rows:
            out[fact["path"]] = rows
    return out


# ---- rule-based flags --------------------------------------------------------------------------------------------------------------------

def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", s.lower()).strip()


def quality_flags(sections: dict[str, list[Rec]], passages: dict[str, list[Rec]], have_evidence: bool) -> list[Rec]:
    flags: list[Rec] = []

    def flag(ref: str, issue: str) -> None:
        if not any(f["ref"] == ref and f["issue"] == issue for f in flags):
            flags.append({"ref": ref, "issue": issue})

    symptoms = {_norm(label_of(i)): i["ref"] for i in sections.get("symptoms", [])}
    for n in sections.get("negative_findings", []):
        if _norm(label_of(n)) in symptoms:
            flag(n["ref"], "listed as not present, but the same phrase is also listed as a symptom")

    seen: dict[str, set[str]] = {}
    for sec in ("chief_complaint", "symptoms", "negative_findings", "medical_history.past_medical_history", "physical_examination", "review_of_systems", "clinical_conditions", "clinical_assessment"):
        for i in sections.get(sec, []):
            seen.setdefault(_norm(label_of(i)), set()).add(sec)
    for phrase, secs in seen.items():
        if phrase and len(secs) >= 3:
            for sec in secs:
                for i in sections.get(sec, []):
                    if _norm(label_of(i)) == phrase:
                        flag(i["ref"], f"the same phrase appears in {len(secs)} different sections")

    med_names = {_norm(label_of(m)) for m in sections.get("medications", [])}
    for a in sections.get("allergies", []):
        subst = _norm(str(a.get("substance", "")) or label_of(a))
        if subst and subst in med_names:
            flag(a["ref"], "the allergy has the same name as a listed medicine: possibly a medicine the patient takes, not an allergy")
        if not a.get("reaction") and a.get("status") == "reported":
            flag(a["ref"], "allergy without a stated reaction: verify it was presented as an allergy")

    if have_evidence:
        for sec in NEEDS_SOURCE:
            for i in sections.get(sec, []):
                if i["ref"] not in passages:
                    flag(i["ref"], "no supporting passage was found in the conversation")

    for v in sections.get("vital_signs", []):
        name, value, unit = str(v.get("name", "")).lower(), str(v.get("value", "")), str(v.get("unit", "")).lower()
        if re.search(r"oxygen|spo2|saturation", name) and unit and "%" not in unit and "percent" not in unit:
            flag(v["ref"], f"oxygen saturation with unit '{unit}' (expected %)")
        if re.search(r"[a-z]{3,}", value.lower()) or re.search(r"pound|dollar|month|week|day|year|£|\$", value.lower() + " " + unit):
            flag(v["ref"], "the value or unit does not look like a measurement (a price, a duration or a count?)")

    pair: dict[tuple[str, str], list[str]] = {}
    for m in sections.get("medications", []):
        if m.get("dose") and m.get("frequency"):
            pair.setdefault((str(m["dose"]).lower(), str(m["frequency"]).lower()), []).append(m["ref"])
    for refs in pair.values():
        if len(refs) >= 3:
            for r in refs:
                flag(r, "the same dose and frequency are listed for three or more medicines (values may have been copied between them)")

    seconds = re.compile(r"^\s*\d+(\.\d+)?\s*s(ec(onds?)?)?\s*$", re.I)
    for sec in ("follow_up", "clinical_actions"):
        for i in sections.get(sec, []):
            t = i.get("time_reference") or ""
            if isinstance(t, str) and seconds.match(t):
                flag(i["ref"], f"the time '{t}' looks like a recording timestamp, not an appointment interval")

    complaint = [label_of(i) for i in sections.get("chief_complaint", [])]
    if complaint and complaint[0]:
        words = lambda t: {w for w in re.findall(r"[a-z]{4,}", t.lower())}  # noqa: E731
        pool = set().union(*(words(label_of(i)) for sec in ("symptoms", "clinical_conditions", "clinical_assessment", "medical_history.past_medical_history") for i in sections.get(sec, [])), set())
        if pool and not (words(complaint[0]) & pool):
            flag(sections["chief_complaint"][0]["ref"], "the chief complaint shares no wording with any listed symptom or condition: it may be a remark, not a complaint")
    for a in sections.get("clinical_assessment", []):
        la = _norm(label_of(a))
        if la and (la in symptoms or la in {_norm(c) for c in complaint}):
            flag(a["ref"], "the assessment repeats a symptom or the complaint: the clinician may not have stated a diagnosis")
        if str(a.get("stated_by", "")).lower() == "patient":
            flag(a["ref"], "assessment attributed to the patient")
    for e in sections.get("physical_examination", []):
        if str(e.get("observed_by", "")).lower() == "patient":
            flag(e["ref"], "examination finding attributed to the patient")
    for u in sections.get("clinical_uncertainties", []):
        if re.search(r"date of (the )?(consultation|visit|last|encounter)", str(u.get("description", "")).lower()):
            flag(u["ref"], "generic date uncertainty that does not describe a real doubt in the conversation")
    return flags


def build_input(doc: Rec, conversation: list[Rec] | None = None) -> Rec:
    """`doc` is the saved extraction document ({extraction, evidence, encounter_id, ...}); `conversation` the optional compact transcript segments. Returns the agent input."""
    extraction = doc.get("extraction")
    if not isinstance(extraction, dict):
        raise ValueError("the saved document has no extraction")
    sections = annotate(extraction)
    refs = {i["ref"] for items in sections.values() for i in items}
    passages = _passages(doc, refs, {i["ref"]: i for items in sections.values() for i in items})
    have_evidence = bool((doc.get("evidence") or {}).get("facts"))
    out = {
        "encounter": {"encounter_id": str(doc.get("encounter_id") or doc.get("encounter_ref") or ""), "date_of_service": None, "patient_age_sex": None,
                      "note": "Date of service, age and sex are not provided."},
        "extraction": sections,
        "source_passages": passages,
        "data_quality_flags": quality_flags(sections, passages, have_evidence),
    }
    if conversation:
        out["conversation"] = [{"speaker": ROLE_LABEL.get(s.get("role") or "", "Speaker"), "time": _clock(s.get("start_seconds")), "text": s.get("text", "")} for s in conversation]
    return out
