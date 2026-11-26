"""Split a long consultation into windows the model handles well, extract each window, merge the results (no dependencies, standard library only).

  windows = make_windows(segments, max_chars=7000, overlap=4)       segments: [{"segment_id","speaker_id","role","text"}]
  each window is sent to the model with LOCAL ids SEG0001.. (the model was trained on transcripts that start at SEG0001);
  window.to_global maps a local id back to the original id.
  merged = merge([(window, full_structure_of_that_window), ...])    full structure = output of expand()

Merge rules (all deterministic):
  * list sections: items of all windows in order; an item identical to an earlier one except for evidence_ids/confidence (case-insensitive text) is dropped and its
    evidence ids are added to the earlier item (this also removes the repeats caused by the overlap between windows);
  * `related_entities` pointers like "medications[0]" are renumbered to the merged lists;
  * chief_complaint: first window that has one; encounter_metadata: first window, speakers united; quality_checks: any window that says true stays true.
Limits: a fact stated across a window border may be split (the overlap reduces this), and the window that does not see the start of the visit may not know the chief complaint.
"""
from __future__ import annotations

import copy
import json
import re

LIST_SECTIONS = ["symptoms", "negative_findings", "medications", "vital_signs", "physical_examination", "clinical_assessment", "procedures_and_investigations",
                 "clinical_actions", "follow_up", "clinical_uncertainties"]
HISTORY_SECTIONS = ["past_medical_history", "surgical_history", "family_history", "social_history"]
SEG = re.compile(r"SEG(\d{4})")
PTR = re.compile(r"^([A-Za-z_.]+)\[(\d+)\]$")


def make_windows(segments: list[dict], max_chars: int = 7000, overlap: int = 4) -> list[dict]:
    """Greedy windows of at most max_chars of transcript text; consecutive windows share `overlap` segments. One window if everything fits."""
    sizes = [len(s["text"]) + 40 for s in segments]
    if sum(sizes) <= max_chars:
        return [_window(segments, 0)]
    out, start = [], 0
    while start < len(segments):
        end, total = start, 0
        while end < len(segments) and (total + sizes[end] <= max_chars or end == start):
            total += sizes[end]
            end += 1
        out.append(_window(segments[start:end], start))
        if end >= len(segments):
            break
        start = max(end - overlap, start + 1)
    return out


def _window(segs: list[dict], first_index: int) -> dict:
    local = []
    to_global = {}
    for i, s in enumerate(segs, 1):
        lid = f"SEG{i:04d}"
        to_global[lid] = s["segment_id"]
        local.append({**s, "segment_id": lid})
    return {"segments": local, "to_global": to_global, "first_index": first_index}


def _globalise(full: dict, to_global: dict) -> dict:
    """Replace local segment ids by the original ones everywhere in the structure (including free text, which only holds ids in evidence_ids)."""
    def fix(o):
        if isinstance(o, dict):
            return {k: ([to_global.get(x, x) for x in v] if k == "evidence_ids" and isinstance(v, list) else fix(v)) for k, v in o.items()}
        if isinstance(o, list):
            return [fix(x) for x in o]
        return o
    return fix(full)


def _key(item: dict) -> str:
    d = {k: (v.lower().strip() if isinstance(v, str) else v) for k, v in item.items() if k not in ("evidence_ids", "confidence", "related_entities")}
    return json.dumps(d, sort_keys=True, ensure_ascii=False)


def _merge_list(paths: str, per_window: list[list[dict]]):
    """returns merged list and, per window, a map old index -> merged index"""
    merged, index, maps = [], {}, []
    for items in per_window:
        m = {}
        for i, it in enumerate(items):
            k = _key(it)
            if k in index:
                tgt = merged[index[k]]
                tgt["evidence_ids"] = sorted(set(tgt.get("evidence_ids", [])) | set(it.get("evidence_ids", [])))
                m[i] = index[k]
            else:
                index[k] = len(merged)
                merged.append(copy.deepcopy(it))
                m[i] = len(merged) - 1
        maps.append(m)
    return merged, maps


def merge(parts: list[tuple[dict, dict]]) -> dict:
    """parts: [(window, full_structure)] in window order. Returns one full structure."""
    fulls = [_globalise(f, w["to_global"]) for w, f in parts]
    if len(fulls) == 1:
        return fulls[0]
    out = copy.deepcopy(fulls[0])
    index_maps: dict[str, list[dict]] = {}
    for sec in LIST_SECTIONS:
        out[sec], index_maps[sec] = _merge_list(sec, [f.get(sec) or [] for f in fulls])
    out["medical_history"] = out.get("medical_history") or {}
    out["encounter_metadata"] = out.get("encounter_metadata") or {}
    for sec in HISTORY_SECTIONS:
        out["medical_history"][sec], index_maps["medical_history." + sec] = _merge_list(sec, [(f.get("medical_history") or {}).get(sec) or [] for f in fulls])
    # related_entities pointers
    # renumber pointers: rebuild per window using the per-window maps (items keep the pointers of the window that first produced them)
    seen_owner = {}
    for sec in LIST_SECTIONS:
        for w, f in enumerate(fulls):
            for i, it in enumerate(f.get(sec) or []):
                tgt = index_maps[sec][w][i]
                if (sec, tgt) in seen_owner:
                    continue
                seen_owner[(sec, tgt)] = w
                if "related_entities" in it and it["related_entities"]:
                    new = []
                    for p in it["related_entities"]:
                        m = PTR.match(p) if isinstance(p, str) else None
                        if m and m.group(1) in index_maps and int(m.group(2)) in index_maps[m.group(1)][w]:
                            new.append(f"{m.group(1)}[{index_maps[m.group(1)][w][int(m.group(2))]}]")
                        else:
                            new.append(p)
                    out[sec][tgt]["related_entities"] = new
    cc = next((f["chief_complaint"] for f in fulls if (f.get("chief_complaint") or {}).get("value")), out.get("chief_complaint"))
    out["chief_complaint"] = cc
    speakers, seen = [], set()
    for f in fulls:
        for sp in (f.get("encounter_metadata") or {}).get("primary_speakers") or []:
            if sp.get("speaker_id") not in seen:
                seen.add(sp.get("speaker_id"))
                speakers.append(sp)
    out["encounter_metadata"]["primary_speakers"] = speakers
    qc = {}
    for f in fulls:
        for k, v in (f.get("quality_checks") or {}).items():
            qc[k] = bool(qc.get(k)) or bool(v) if isinstance(v, bool) else v
    out["quality_checks"] = qc
    return out
