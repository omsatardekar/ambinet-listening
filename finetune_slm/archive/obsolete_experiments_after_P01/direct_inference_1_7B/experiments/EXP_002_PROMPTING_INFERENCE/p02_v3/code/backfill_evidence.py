"""Backend evidence backfill for P02 v3 (P01 schema without model-written evidence).

Input : the model's parsed output in the ORIGINAL full P01 schema, with evidence_ids holding transcript segment ids (SEG0007) and clinical_evidence [].
Output: the same record with clinical_evidence built from the original transcript (EV_001... in transcript order, exact text/speaker/role/MM:SS times, `supports` locations)
        and every valid segment id in evidence_ids replaced by its EV id.
Never repaired silently: an id that is not a segment id of THIS transcript is kept as given and reported; model-written evidence records (if any) are reported and replaced by
the backend ones; other fields (including quality_checks) are untouched. Reuses the Stage-1 EvidenceResolver (no second resolver)."""
from __future__ import annotations

import copy
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "p02_v2_2" / "code"))
from evidence_resolver import DEFAULT_MAX_REFS, EvidenceResolver      # noqa: E402
from v22_common import categories, get_entities, location, mmss        # noqa: E402


def backfill(pred, transcript: dict, max_refs: int = DEFAULT_MAX_REFS):
    """returns (full_record, flags[list of dict], stats[dict])"""
    res = EvidenceResolver(transcript, max_refs)
    flags, stats = [], Counter()
    full = copy.deepcopy(pred)
    if not isinstance(full, dict):
        return full, [{"kind": "record_not_an_object", "location": "", "detail": type(pred).__name__}], dict(stats)
    ce = full.get("clinical_evidence")
    if ce not in (None, []):
        flags.append({"kind": "model_wrote_evidence_records", "location": "clinical_evidence", "detail": f"{len(ce) if isinstance(ce, list) else type(ce).__name__} model-written item(s) replaced by backend records"})
        stats["model_wrote_evidence_records"] += 1
    pending = []                                   # (entity, resolved list, loc)
    for cat in categories():
        for i, ent in enumerate(get_entities(full, cat)):
            if not isinstance(ent, dict):
                flags.append({"kind": "entity_not_object", "location": location(cat, i), "detail": type(ent).__name__})
                continue
            loc = location(cat, i)
            stats["facts"] += 1
            refs = ent.get("evidence_ids")
            if refs is None or refs == []:
                flags.append({"kind": "no_references", "location": loc, "detail": "the fact cites no transcript segment"})
                stats["facts_without_refs"] += 1
                pending.append((ent, [], loc))
                continue
            if not isinstance(refs, list):
                flags.append({"kind": "refs_not_a_list", "location": loc, "detail": type(refs).__name__})
                pending.append((ent, [], loc))
                continue
            rr, rf = res.resolve_fact(refs, loc)
            for f in rf:
                flags.append(f.as_dict())
                stats["flag_" + f.kind] += 1
            stats["refs_total"] += len(refs)
            stats["refs_valid"] += sum(r.ok for r in rr)
            stats["refs_invalid"] += sum(not r.ok for r in rr)
            pending.append((ent, rr, loc))
    cited = {}
    for ent, rr, loc in pending:
        for r in rr:
            if r.ok:
                cited.setdefault(r.segment_id, None)
    ev_of, evidence = {}, []
    for n, sid in enumerate(sorted(cited, key=lambda s: res.position[s]), start=1):
        seg = res.by_id[sid]
        ev_of[sid] = f"EV_{n:03d}"
        evidence.append({"evidence_id": ev_of[sid], "speaker_id": seg["speaker_id"], "speaker_role": str(seg["role"]).lower(), "transcript_text": seg["text"],
                         "start_timestamp": mmss(seg["start_seconds"]), "end_timestamp": mmss(seg["end_seconds"]), "supports": []})
    by_loc = {loc: (ent, rr) for ent, rr, loc in pending}
    for cat in categories():
        for i, _ in enumerate(get_entities(full, cat)):
            loc = location(cat, i)
            if loc in by_loc:
                for sid in dict.fromkeys(r.segment_id for r in by_loc[loc][1] if r.ok):
                    evidence[int(ev_of[sid][3:]) - 1]["supports"].append(loc)
    for ent, rr, loc in pending:
        if rr:
            ent["evidence_ids"] = [ev_of[r.segment_id] if r.ok else r.ref for r in rr]
    full["clinical_evidence"] = evidence
    stats["evidence_records_built"] = len(evidence)
    return full, flags, dict(stats)
