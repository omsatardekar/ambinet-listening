"""Validate a P02 v2.2 COMPACT model output against the transcript and materialise the FULL project record.

Nothing is repaired silently: unknown keys, invalid references, enum violations, missing required values, inconsistent speaker fields and so on are returned
as `flags` and the offending content is kept as given (unknown keys are returned in `unmapped`, never discarded). The frozen schema, the frozen evaluator and
all other baseline modules are only read (the frozen key sets/enums come from final_label_schema.json at run time)."""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field

from evidence_resolver import DEFAULT_MAX_REFS, EvidenceResolver
from p02_common import categories, category_keys, compact_schema, frozen_schema, get_entities, location, mmss

LOC_RE = re.compile(r"^([a-z_]+(?:\.[a-z_]+)?)\[(\d+)\]$")
EMPTY = (None, "", [], {})


@dataclass
class Flag:
    kind: str
    location: str
    detail: str

    def as_dict(self):
        return {"kind": self.kind, "location": self.location, "detail": self.detail}


@dataclass
class MaterialiseResult:
    full: dict
    flags: list
    stats: dict
    unmapped: list = field(default_factory=list)        # [{location, key, value}] compact keys that have no place in the full schema (kept here, not dropped)
    evidence_by_ref: dict = field(default_factory=dict)  # segment id -> EV id

    def flag_counts(self) -> dict:
        return dict(Counter(f.kind for f in self.flags))


# ------------------------------------------------------------------------------------------------------------------------------------
def _spec():
    cs, fs = compact_schema(), frozen_schema()
    renames = {"refs": "evidence_ids", "related": "related_entities", "responsible": "responsible_person"}
    inv = {v: k for k, v in renames.items()}
    speaker = cs["speaker_field"]
    allowed, full_of = {}, {}
    for cat in categories():
        keys = category_keys(cat)
        a = {}
        for k in keys:
            if k == "confidence":
                continue
            ck = inv.get(k, k)
            if k == speaker.get(cat):
                ck = "by"
            a[ck] = k
        allowed[cat] = a                 # compact key -> full key
    return cs, fs, renames, allowed


def compact_keys(cat: str) -> list[str]:
    """Keys a model may write for one fact of a category."""
    return list(_spec()[3][cat])


def enum_for(cat: str, full_key: str):
    fs, cs = frozen_schema(), compact_schema()
    if cat == "symptoms" and full_key == "category":
        return cs["symptoms_category_enum"]["values"]
    e = fs["enums"].get(f"{cat}.{full_key}")
    return list(e) if isinstance(e, dict) else None


def _default_for(cat: str, ckey: str, ent: dict, defaults: dict):
    d = defaults.get(cat, {})
    if ckey not in d:
        return None, False
    v = d[ckey]
    if v == "@by_status":
        st = ent.get("status", defaults.get(cat, {}).get("status"))
        return {"present": "current", "resolved": "resolved"}.get(st), True
    return v, True


def derived_default(cat: str, ckey: str, ent: dict):
    """Public: the value the materialiser restores when `ckey` is omitted (used by the gold converter so that omitted == restored by construction)."""
    cs = compact_schema()
    v, has = _default_for(cat, ckey, ent, cs["defaults_when_key_omitted"])
    return v, has


# ------------------------------------------------------------------------------------------------------------------------------------
def materialise(compact, transcript: dict, max_refs: int = DEFAULT_MAX_REFS) -> MaterialiseResult:
    cs, fs, renames, allowed = _spec()
    res = EvidenceResolver(transcript, max_refs)
    flags: list[Flag] = []
    unmapped: list[dict] = []
    stats = {"entities": Counter(), "defaults_applied": Counter(), "speaker_derived": 0, "speaker_explicit": 0, "speaker_unresolved": 0,
             "refs_total": 0, "refs_valid": 0, "refs_invalid": 0, "facts_without_refs": 0, "facts_over_limit": 0}
    full = {"encounter_id": transcript.get("encounter_id"), "extraction_status": "completed",
            "encounter_metadata": {"encounter_date": None, "encounter_type": "outpatient_consultation", "language": "en",
                                   "primary_speakers": [{"speaker_id": s["speaker_id"], "role": s["role"], "role_confidence": None} for s in res.speaker_table()]}}
    for cat in categories():
        if cat == "chief_complaint":
            full["chief_complaint"] = {k: (None if k != "evidence_ids" else []) for k in category_keys(cat)}
        elif "." in cat:
            full.setdefault("medical_history", {})[cat.split(".")[1]] = []
        else:
            full[cat] = []
    if not isinstance(compact, dict):
        flags.append(Flag("compact_not_an_object", "", f"top level is {type(compact).__name__}"))
        return MaterialiseResult(full, flags, stats, unmapped)
    emitted = set(cs["model_emits_top_level_keys_in_this_order"])
    for k in compact:
        if k not in emitted:
            flags.append(Flag("unknown_top_level_key", k, "not a v2.2 section (kept in unmapped)"))
            unmapped.append({"location": "", "key": k, "value": compact[k]})
    # ---- facts ----------------------------------------------------------------------------------------------------------------
    pending_refs = []         # (entity dict in full, [ResolvedRef], location, original refs)
    for cat in categories():
        if "." in cat:
            sect = compact.get("medical_history")
            if sect is not None and not isinstance(sect, dict):
                if cat == categories()[3]:
                    flags.append(Flag("section_wrong_type", "medical_history", "expected an object with four lists"))
                continue
            items = (sect or {}).get(cat.split(".")[1])
        else:
            items = compact.get(cat)
        if items in (None, [], {}):
            continue
        if cat == "chief_complaint":
            if not isinstance(items, dict):
                flags.append(Flag("section_wrong_type", cat, "chief_complaint must be one object"))
                continue
            items_list = [items]
        else:
            if not isinstance(items, list):
                flags.append(Flag("section_wrong_type", cat, "expected a list of fact objects"))
                continue
            items_list = items
        out_list = []
        for i, ent in enumerate(items_list):
            loc = location(cat, i)
            if not isinstance(ent, dict):
                flags.append(Flag("entity_not_object", loc, f"item is {type(ent).__name__}"))
                continue
            stats["entities"][cat] += 1
            fe = {}
            for ck in ent:
                if ck not in allowed[cat]:
                    flags.append(Flag("unknown_key", loc, f"{ck!r} is not a v2.2 key for {cat}"))
                    unmapped.append({"location": loc, "key": ck, "value": ent[ck]})
            spk_full = cs["speaker_field"].get(cat)
            refs, rflags = res.resolve_fact(ent.get("refs"), loc)
            for f in rflags:
                flags.append(Flag(f.kind, f.location, f.detail))
            raw_refs = ent.get("refs") if isinstance(ent.get("refs"), list) else []
            stats["refs_total"] += len(raw_refs)
            stats["refs_valid"] += sum(r.ok for r in refs)
            stats["refs_invalid"] += sum(not r.ok for r in refs)
            stats["facts_without_refs"] += (not raw_refs)
            stats["facts_over_limit"] += (len(raw_refs) > max_refs)
            valid_roles = {r.role for r in refs if r.ok}
            for fk in category_keys(cat):
                ck = next((c for c, f in allowed[cat].items() if f == fk), None)
                if fk == "confidence":
                    fe[fk] = None
                elif fk == "evidence_ids":
                    fe[fk] = []                                           # filled once EV ids are allocated
                elif fk == spk_full:
                    if "by" in ent:
                        v = ent["by"]
                        stats["speaker_explicit"] += 1
                        fe[fk] = v
                        if isinstance(v, str):
                            sid_roles = {s["speaker_id"]: s["role"] for s in res.speaker_table()}
                            if v in sid_roles:
                                flags.append(Flag("by_is_speaker_id", loc, f"by={v!r} is a speaker id (its role in this transcript is {sid_roles[v]!r}); kept as given"))
                            elif v not in fs["roles"]:
                                flags.append(Flag("by_not_a_role", loc, f"by={v!r} is not one of {fs['roles']}"))
                            elif valid_roles and v not in valid_roles:
                                flags.append(Flag("by_not_in_refs_roles", loc, f"by={v!r} but the cited segments are spoken by {sorted(valid_roles)}"))
                        elif v is not None:
                            flags.append(Flag("bad_value_type", loc, f"by must be a role string or null, got {type(v).__name__}"))
                    elif len(valid_roles) == 1:
                        fe[fk] = next(iter(valid_roles))
                        stats["speaker_derived"] += 1
                    else:
                        fe[fk] = None
                        stats["speaker_unresolved"] += 1
                        flags.append(Flag("speaker_unresolved", loc, f"`by` omitted and the valid cited segments have roles {sorted(valid_roles)}: not derivable, left null"))
                else:
                    if ck in ent and ent[ck] not in (None,):
                        v = ent[ck]
                        fe[fk] = v
                    else:
                        v, has = _default_for(cat, ck, ent, cs["defaults_when_key_omitted"])
                        if has and ck not in ent:
                            fe[fk] = v
                            stats["defaults_applied"][f"{cat}.{fk}"] += 1
                        else:
                            fe[fk] = [] if fk in cs["list_valued_keys"] else None
                    # nested objects restore their own subkeys with null
                    nk = cs["nested_objects"].get(f"{cat}.{fk}")
                    if nk and isinstance(fe[fk], dict):
                        extra = [k2 for k2 in fe[fk] if k2 not in nk]
                        for k2 in extra:
                            flags.append(Flag("unknown_key", loc, f"{fk}.{k2} is not a key of {fk}"))
                            unmapped.append({"location": f"{loc}.{fk}", "key": k2, "value": fe[fk][k2]})
                        fe[fk] = {k2: fe[fk].get(k2) for k2 in nk}
                    elif nk and fe[fk] not in (None,):
                        flags.append(Flag("bad_value_type", loc, f"{fk} must be an object with keys {nk} or be omitted, got {type(fe[fk]).__name__}"))
                    # enums
                    en = enum_for(cat, fk)
                    if en is not None and isinstance(fe[fk], str) and fe[fk] not in en:
                        flags.append(Flag("enum_violation", loc, f"{fk}={fe[fk]!r} not in {en}"))
                    if fk in cs["list_valued_keys"] and fe[fk] is not None and not isinstance(fe[fk], list):
                        flags.append(Flag("bad_value_type", loc, f"{fk} must be a list"))
            # required
            for rk in cs["required_nonempty"].get(cat, []):
                if rk == "refs":
                    continue                                            # reported as no_references / invalid_reference by the resolver
                if ent.get(rk) in EMPTY:
                    flags.append(Flag("missing_required", loc, f"{rk} is missing or empty"))
            for ck, v in ent.items():
                if v == "" and ck in allowed[cat]:
                    flags.append(Flag("empty_string_value", loc, f"{ck} is an empty string (kept)"))
            if cat == "vital_signs" and isinstance(ent.get("value"), bool):
                flags.append(Flag("bad_value_type", loc, "value must be a number or a string"))
            if cat == "symptoms":
                st, tp = fe.get("status"), fe.get("temporality")
                if (st == "present" and tp != "current") or (st == "resolved" and tp == "current"):
                    flags.append(Flag("status_temporality_inconsistent", loc, f"status={st!r} with temporality={tp!r}"))
            pending_refs.append((fe, refs, loc, raw_refs))
            out_list.append(fe)
        if cat == "chief_complaint":
            if out_list:
                full["chief_complaint"] = out_list[0]
        elif "." in cat:
            full["medical_history"][cat.split(".")[1]] = out_list
        else:
            full[cat] = out_list
    # ---- related_entities must point at facts that exist ----------------------------------------------------------------------
    for i, u in enumerate(full.get("clinical_uncertainties", [])):
        rel = u.get("related_entities")
        for r in (rel if isinstance(rel, list) else []):
            m = LOC_RE.match(r) if isinstance(r, str) else None
            ok = False
            if m:
                cat, idx = m.group(1), int(m.group(2))
                ok = cat in categories() and idx < len(get_entities(full, cat))
            if not ok:
                flags.append(Flag("related_unresolved", f"clinical_uncertainties[{i}]", f"related entity {r!r} does not point at a materialised fact"))
    # ---- clinical_evidence: one record per distinct cited valid segment, transcript order -----------------------------------
    cited = {}
    for fe, refs, loc, raw in pending_refs:
        for r in refs:
            if r.ok:
                cited.setdefault(r.segment_id, []).append(loc)
    ev_ids = {}
    evidence = []
    for n, sid in enumerate(sorted(cited, key=lambda s: res.position[s]), start=1):
        seg = res.by_id[sid]
        ev_ids[sid] = f"EV_{n:03d}"
        sup = []
        evidence.append({"evidence_id": ev_ids[sid], "speaker_id": seg["speaker_id"], "speaker_role": str(seg["role"]).lower(), "transcript_text": seg["text"],
                         "start_timestamp": mmss(seg["start_seconds"]), "end_timestamp": mmss(seg["end_seconds"]), "supports": sup})
    # supports in category order, entity index order
    by_loc = {}
    for fe, refs, loc, raw in pending_refs:
        by_loc[loc] = (fe, refs, raw)
    for cat in categories():
        for i, _ in enumerate(get_entities(full, cat)):
            loc = location(cat, i)
            if loc in by_loc:
                for sid in dict.fromkeys(r.segment_id for r in by_loc[loc][1] if r.ok):
                    evidence[int(ev_ids[sid][3:]) - 1]["supports"].append(loc)
    for fe, refs, loc, raw in pending_refs:
        fe["evidence_ids"] = [ev_ids[r.segment_id] if r.ok else r.ref for r in refs]
    full["clinical_evidence"] = evidence
    # quality_checks: deliberately not derived (owner decision pending); the key is absent
    return MaterialiseResult(full, flags, stats, unmapped, ev_ids)
