"""EXP_004 P04 deterministic evidence builder (PROTOTYPE; not run on any model output yet).

Input : the model's INTERMEDIATE JSON (the frozen schema, except that every item carries "source_segments": ["SEG0007", ...] instead of "evidence_ids", and there is no "clinical_evidence")
        + the original transcript (input file: segments with segment_id, speaker_id, role, start_seconds, end_seconds, text).
Output: a FINAL JSON that follows the frozen schema (evidence_ids on every item, a complete clinical_evidence list) + a build report.
Rules  : uses ONLY the transcript and the model's cited ids. Never opens labels. Never adds, removes, reorders or edits extracted items or their other fields.
         Evidence text, speaker, role and times are copied from the transcript segment: the model can neither invent nor corrupt them.
Conventions (measured on the 100 development labels, analysis/evidence_design_probe.py): one evidence record = one whole segment; EV_001.. numbered in segment order; speaker_role = lower-case transcript role;
         start/end = floor(seconds) as MM:SS; supports = locations like "symptoms[0]", "medical_history.surgical_history[1]", "chief_complaint"."""
from __future__ import annotations

import copy
import re

MAX_SEGMENTS_PER_ITEM = None  # no truncation by default (user decision D2); a cap can be passed explicitly. Long id lists are reported, not cut.
LIST_SECTIONS = ["symptoms", "negative_findings", "medications", "allergies", "vital_signs", "physical_examination", "review_of_systems", "clinical_conditions", "clinical_assessment",
                 "procedures_and_investigations", "clinical_actions", "follow_up", "clinical_uncertainties"]
HISTORY = ["past_medical_history", "surgical_history", "family_history", "social_history"]
SEG_RE = re.compile(r"^\s*\[?\s*SEG\s*0*(\d{1,4})\s*\]?\s*$", re.I)
KEY = "source_segments"


def mmss(seconds) -> str:
    s = int(float(seconds))  # truncation (floor for non-negative values): the dataset convention
    return f"{s // 60:02d}:{s % 60:02d}"


def entity_locations(pred: dict):
    """(location string, entity dict) in a fixed traversal order: chief_complaint, list sections in schema order, then medical_history sub-lists (placed where the schema puts them)."""
    out = []
    cc = pred.get("chief_complaint")
    if isinstance(cc, dict):
        out.append(("chief_complaint", cc))
    for sec in ["symptoms", "negative_findings"]:
        out += [(f"{sec}[{i}]", e) for i, e in enumerate(pred.get(sec) or []) if isinstance(e, dict)] if isinstance(pred.get(sec), list) else []
    mh = pred.get("medical_history")
    if isinstance(mh, dict):
        for h in HISTORY:
            v = mh.get(h)
            if isinstance(v, list):
                out += [(f"medical_history.{h}[{i}]", e) for i, e in enumerate(v) if isinstance(e, dict)]
    for sec in LIST_SECTIONS[2:]:
        v = pred.get(sec)
        if isinstance(v, list):
            out += [(f"{sec}[{i}]", e) for i, e in enumerate(v) if isinstance(e, dict)]
    return out


def normalise_segment_id(raw, valid_ids: set):
    """exact id -> ('exact', id); recoverable spelling (seg3, [SEG0003], SEG03) -> ('normalised', id) if it names an existing segment; anything else -> ('invalid', raw)."""
    if not isinstance(raw, str):
        return "invalid", raw
    if raw.strip() in valid_ids:
        return ("exact", raw.strip())
    m = SEG_RE.match(raw)
    if m:
        cand = f"SEG{int(m.group(1)):04d}"
        if cand in valid_ids:
            return "normalised", cand
    return "invalid", raw


def build_evidence(intermediate: dict, transcript: dict, top_key_order: list | None = None, max_segments: int | None = MAX_SEGMENTS_PER_ITEM):
    pred = copy.deepcopy(intermediate)
    segs = transcript["segments"]
    by_id = {s["segment_id"]: (i, s) for i, s in enumerate(segs)}
    valid = set(by_id)
    rep = {"entities": 0, "entities_with_valid_citation": 0, "entities_uncited": 0, "ids_exact": 0, "ids_normalised": 0, "ids_invalid": 0, "ids_duplicate_removed": 0, "ids_truncated_over_cap": 0,
           "ids_per_item_distribution": {}, "items_with_more_than_6_ids": 0, "key_missing": 0, "key_wrong_type": 0, "model_evidence_ids_dropped": 0, "model_clinical_evidence_discarded": 0, "invalid_examples": [], "uncited_locations": []}
    if pred.get("clinical_evidence"):
        rep["model_clinical_evidence_discarded"] = len(pred["clinical_evidence"]) if isinstance(pred["clinical_evidence"], list) else 1
    locs = entity_locations(pred)
    cited_by_entity = {}
    used = set()
    for loc, ent in locs:
        rep["entities"] += 1
        if "evidence_ids" in ent and ent["evidence_ids"]:
            rep["model_evidence_ids_dropped"] += 1  # the model wrote its own ids: they are ignored, only source_segments is used
        raw = ent.get(KEY)
        if KEY not in ent:
            rep["key_missing"] += 1
            raw = []
        elif not isinstance(raw, list):
            rep["key_wrong_type"] += 1
            raw = [raw] if isinstance(raw, str) else []
        seen, keep = set(), []
        for r in raw:
            kind, sid = normalise_segment_id(r, valid)
            if kind == "invalid":
                rep["ids_invalid"] += 1
                if len(rep["invalid_examples"]) < 10:
                    rep["invalid_examples"].append(str(r)[:40])
                continue
            rep["ids_exact" if kind == "exact" else "ids_normalised"] += 1
            if sid in seen:
                rep["ids_duplicate_removed"] += 1
                continue
            seen.add(sid); keep.append(sid)
        if max_segments is not None and len(keep) > max_segments:
            rep["ids_truncated_over_cap"] += len(keep) - max_segments
            keep = keep[:max_segments]
        cited_by_entity[loc] = keep
        rep["ids_per_item_distribution"][str(len(keep))] = rep["ids_per_item_distribution"].get(str(len(keep)), 0) + 1
        rep["items_with_more_than_6_ids"] += len(keep) > 6
        used.update(keep)
        if keep:
            rep["entities_with_valid_citation"] += 1
        else:
            rep["entities_uncited"] += 1
            rep["uncited_locations"].append(loc)
    order = sorted(used, key=lambda sid: by_id[sid][0])
    ev_id = {sid: f"EV_{n + 1:03d}" for n, sid in enumerate(order)}
    records = []
    for sid in order:
        s = by_id[sid][1]
        records.append({"evidence_id": ev_id[sid], "speaker_id": s["speaker_id"], "speaker_role": str(s["role"]).lower(), "transcript_text": s["text"],
                        "start_timestamp": mmss(s["start_seconds"]), "end_timestamp": mmss(s["end_seconds"]),
                        "supports": [loc for loc, _ in locs if sid in cited_by_entity.get(loc, [])]})
    for loc, ent in locs:
        ent.pop(KEY, None)
        ent["evidence_ids"] = [ev_id[sid] for sid in sorted(cited_by_entity.get(loc, []), key=lambda x: by_id[x][0])]
    pred["clinical_evidence"] = records
    if top_key_order:
        pred = {**{k: pred[k] for k in top_key_order if k in pred}, **{k: v for k, v in pred.items() if k not in top_key_order}}
    rep["evidence_records"] = len(records)
    return pred, rep


def verify_only_evidence_changed(intermediate: dict, final: dict) -> dict:
    """Integrity check for the builder: after removing the evidence-related keys (item-level source_segments / evidence_ids and the top-level clinical_evidence) from BOTH objects,
    the intermediate and the final output must be identical (same items, same order, same values, same key order of the remaining fields)."""
    def strip(o, top=True):
        if isinstance(o, dict):
            return {k: strip(v, False) for k, v in o.items() if k not in (KEY, "evidence_ids") and not (top and k == "clinical_evidence")}
        if isinstance(o, list):
            return [strip(x, False) for x in o]
        return o
    a, b = strip(intermediate), strip(final)
    import json as _j
    return {"identical_except_evidence_fields": _j.dumps(a, sort_keys=False, ensure_ascii=False) == _j.dumps(b, sort_keys=False, ensure_ascii=False), "n_items_before": len(entity_locations(intermediate)), "n_items_after": len(entity_locations(final))}
