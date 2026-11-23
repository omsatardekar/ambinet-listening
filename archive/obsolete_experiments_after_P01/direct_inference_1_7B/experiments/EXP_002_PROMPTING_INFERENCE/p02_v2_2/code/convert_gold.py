"""Convert the corrected full gold labels (authorised dev ids only) into P02 v2.2 COMPACT gold.

Reads only dataset_v2_batch_001_corrected (inputs + labels of the 50 authorised ids). Writes only inside p02_v2_2/derived/. Original files are never touched.
  * evidence_ids (EV_nnn) -> transcript segment ids, by exact match of (text, speaker, MM:SS start, MM:SS end) against the transcript
  * clinical_evidence, encounter_metadata, extraction_status, quality_checks, confidence (always null) are not part of compact gold
  * null / empty / default-equal values are omitted; every omission is restored by materialiser.py (round-trip is verified for every record)
No clinical fact is dropped."""
from __future__ import annotations

import argparse
import json
import statistics as st
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidence_resolver import EvidenceResolver                          # noqa: E402
from materialiser import compact_keys, derived_default, materialise     # noqa: E402
from v22_common import (PKG, authorised_ids, categories, category_keys, compact_json_len, compact_schema, est_tokens, frozen_schema,   # noqa: E402
                        get_entities, load_gold, load_transcript, mmss)

EMPTY = (None, "", [], {})


def build_ev_map(gold: dict, transcript: dict):
    """EV id -> segment id. A mapping is accepted only when exactly ONE transcript segment matches text, speaker, start and end."""
    segs = transcript["segments"]
    m, failures = {}, []
    for e in gold["clinical_evidence"]:
        c = [s["segment_id"] for s in segs if s["text"] == e["transcript_text"] and s["speaker_id"] == e["speaker_id"]
             and mmss(s["start_seconds"]) == e["start_timestamp"] and mmss(s["end_seconds"]) == e["end_timestamp"]]
        if len(c) == 1:
            m[e["evidence_id"]] = c[0]
        else:
            failures.append({"evidence_id": e["evidence_id"], "candidates": c})
    return m, failures


def _prune(v):
    if isinstance(v, dict):
        return {k: x for k, x in v.items() if x not in EMPTY}
    return v


def derivation_class(refs_roles: list[str], value) -> str:
    uniq = set(refs_roles)
    if len(uniq) == 1:
        return "unique_role_reproduces" if next(iter(uniq)) == value else "unique_role_differs"
    return "mixed_roles" if uniq else "no_valid_refs"


def to_compact(gold: dict, transcript: dict, ev_map: dict, omit_derivable_by: bool = False):
    cs = compact_schema()
    spk = cs["speaker_field"]
    res = EvidenceResolver(transcript)
    info = {"failed_ref_mappings": 0, "nonnull_confidence": 0, "derivation": Counter(), "refs_per_fact": [], "refs_per_cat": defaultdict(list)}
    sections = {}
    for cat in categories():
        out = []
        for ent in get_entities(gold, cat):
            ce, refs = {}, []
            for x in ent.get("evidence_ids", []):
                if x in ev_map:
                    refs.append(ev_map[x])
                else:
                    refs.append(x)                                          # unmapped id stays visible (never expected)
                    info["failed_ref_mappings"] += 1
            ce_refs = refs
            for fk in category_keys(cat):
                v = ent.get(fk)
                if fk == "confidence":
                    if v is not None:
                        info["nonnull_confidence"] += 1
                    continue
                if fk == "evidence_ids":
                    continue
                if fk == spk.get(cat):
                    roles = [r.role for r in (res.resolve(s) for s in refs) if r.ok]
                    cls = derivation_class(roles, v)
                    info["derivation"][(fk, cls)] += 1
                    if v is None:
                        ce["by"] = None
                    elif not (omit_derivable_by and cls == "unique_role_reproduces"):
                        ce["by"] = v
                    continue
                ck = {"related_entities": "related", "responsible_person": "responsible"}.get(fk, fk)
                v = _prune(v)
                if v in EMPTY:
                    continue
                d, has = derived_default(cat, ck, ent)
                if has and v == d:
                    continue
                ce[ck] = v
            ce["refs"] = ce_refs
            info["refs_per_fact"].append(len(refs))
            info["refs_per_cat"][cat].append(len(refs))
            out.append(ce)
        sections[cat] = out
    compact = {}
    for key in cs["model_emits_top_level_keys_in_this_order"]:
        if key == "medical_history":
            mh = {c.split(".")[1]: sections[c] for c in categories() if c.startswith("medical_history.") and sections[c]}
            if mh:
                compact[key] = mh
        elif key == "chief_complaint":
            if sections[key]:
                compact[key] = sections[key][0]
        elif sections.get(key):
            compact[key] = sections[key]
    return compact, info


def deep_diff(a, b, path="", out=None, limit=40):
    out = [] if out is None else out
    if len(out) >= limit:
        return out
    if type(a) != type(b):
        out.append(f"{path}: type {type(a).__name__} vs {type(b).__name__}")
    elif isinstance(a, dict):
        for k in list(a) + [k for k in b if k not in a]:
            if k not in a or k not in b:
                out.append(f"{path}/{k}: missing in {'materialised' if k not in b else 'gold'}")
            else:
                deep_diff(a[k], b[k], f"{path}/{k}", out, limit)
    elif isinstance(a, list):
        if len(a) != len(b):
            out.append(f"{path}: length {len(a)} vs {len(b)}")
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                deep_diff(x, y, f"{path}[{i}]", out, limit)
    elif a != b:
        out.append(f"{path}: {a!r} vs {b!r}")
    return out


def roundtrip(gold: dict, compact: dict, transcript: dict, derive_by_where_omitted=True):
    """materialise(compact) must equal gold in every field except quality_checks (not derived). Returns (differences, MaterialiseResult)."""
    r = materialise(compact, transcript, max_refs=10 ** 6)
    g = {k: v for k, v in gold.items() if k != "quality_checks"}
    return deep_diff(g, r.full), r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(PKG / "derived"))
    ap.add_argument("--ids", nargs="*", default=None, help="subset of the 50 authorised ids (default: all 50)")
    A = ap.parse_args()
    out = Path(A.out).resolve()
    if PKG.resolve() not in out.parents and out != PKG.resolve():
        sys.exit("refusing to write outside p02_v2_2/")
    ids = A.ids or authorised_ids()
    (out / "gold_compact").mkdir(parents=True, exist_ok=True)
    (out / "gold_compact_omit_derivable_by").mkdir(parents=True, exist_ok=True)
    rep = {"dataset": "dataset_v2_batch_001_corrected (read-only)", "ids": ids, "records_converted": 0, "evidence_records": 0, "evidence_mapped": 0, "evidence_failed": [],
           "fact_refs_mapped": 0, "fact_refs_unmapped": 0, "nonnull_confidence_fields": 0, "roundtrip_records_exact": 0, "roundtrip_differences": {},
           "metadata_derivation_mismatch": [], "gold_primary_speakers_equal_transcript_table": 0, "quality_checks_dropped": 0}
    refs_all, refs_cat = [], defaultdict(list)
    deriv = Counter()
    sizes = {"full_gold": [], "gold_without_evidence_metadata_checks_all_keys": [], "compact_explicit_by": [], "compact_omit_derivable_by": []}
    for eid in ids:
        gold, tr = load_gold(eid), load_transcript(eid)
        m, fails = build_ev_map(gold, tr)
        rep["evidence_records"] += len(gold["clinical_evidence"])
        rep["evidence_mapped"] += len(m)
        rep["evidence_failed"] += [{"id": eid, **f} for f in fails]
        compact, info = to_compact(gold, tr, m)
        compact2, _ = to_compact(gold, tr, m, omit_derivable_by=True)
        (out / "gold_compact" / f"encounter_{eid}.json").write_text(json.dumps(compact, ensure_ascii=False, indent=1), encoding="utf-8")
        (out / "gold_compact_omit_derivable_by" / f"encounter_{eid}.json").write_text(json.dumps(compact2, ensure_ascii=False, indent=1), encoding="utf-8")
        rep["records_converted"] += 1
        rep["fact_refs_unmapped"] += info["failed_ref_mappings"]
        rep["fact_refs_mapped"] += sum(info["refs_per_fact"]) - info["failed_ref_mappings"]
        rep["nonnull_confidence_fields"] += info["nonnull_confidence"]
        refs_all += info["refs_per_fact"]
        for c, v in info["refs_per_cat"].items():
            refs_cat[c] += v
        deriv.update(info["derivation"])
        diffs, r1 = roundtrip(gold, compact, tr)
        diffs2, _ = roundtrip(gold, compact2, tr)
        if not diffs:
            rep["roundtrip_records_exact"] += 1
        else:
            rep["roundtrip_differences"][eid] = diffs[:10]
        if diffs2:
            rep["roundtrip_differences"][eid + "_omit_by_variant"] = diffs2[:10]
        res = EvidenceResolver(tr)
        derived_meta = {"encounter_date": None, "encounter_type": "outpatient_consultation", "language": "en",
                        "primary_speakers": [{"speaker_id": s["speaker_id"], "role": s["role"], "role_confidence": None} for s in res.speaker_table()]}
        if gold["encounter_metadata"] != derived_meta:
            rep["metadata_derivation_mismatch"].append(eid)
        rep["gold_primary_speakers_equal_transcript_table"] += (gold["encounter_metadata"]["primary_speakers"] == derived_meta["primary_speakers"])
        rep["quality_checks_dropped"] += ("quality_checks" in gold)
        sizes["full_gold"].append(compact_json_len(gold))
        sizes["gold_without_evidence_metadata_checks_all_keys"].append(compact_json_len({k: v for k, v in gold.items() if k not in ("clinical_evidence", "quality_checks", "encounter_metadata")}))
        sizes["compact_explicit_by"].append(compact_json_len(compact))
        sizes["compact_omit_derivable_by"].append(compact_json_len(compact2))
    # reference-count distribution
    dist = Counter(refs_all)
    n = len(refs_all)
    cum, run = {}, 0
    for k in sorted(dist):
        run += dist[k]
        cum[k] = round(run / n, 4)
    ref_report = {"facts": n, "distribution": {str(k): dist[k] for k in sorted(dist)}, "cumulative_share": {str(k): v for k, v in cum.items()},
                  "min": min(refs_all), "median": st.median(refs_all), "mean": round(st.mean(refs_all), 3), "max": max(refs_all),
                  "share_le_2": round(sum(v for k, v in dist.items() if k <= 2) / n, 4), "share_le_3": round(sum(v for k, v in dist.items() if k <= 3) / n, 4),
                  "share_le_4": round(sum(v for k, v in dist.items() if k <= 4) / n, 4), "share_le_5": round(sum(v for k, v in dist.items() if k <= 5) / n, 4),
                  "per_category": {c: {"facts": len(v), "median": st.median(v), "max": max(v), "share_gt_2": round(sum(x > 2 for x in v) / len(v), 3), "share_gt_4": round(sum(x > 4 for x in v) / len(v), 3)} for c, v in refs_cat.items() if v},
                  "chosen_default_max_refs": compact_schema()["reference_policy"]["max_refs_default"],
                  "note": "The limit only flags (excessive_references); no reference is dropped. Gold facts above the limit are reported, not truncated."}
    (out / "ref_count_distribution.json").write_text(json.dumps(ref_report, indent=1), encoding="utf-8")
    sp = defaultdict(Counter)
    for (fk, cls), c in deriv.items():
        sp[fk][cls] += c
    tot = Counter()
    for fk in sp:
        tot.update(sp[fk])
    rep["speaker_derivation"] = {"by_field": {k: dict(v) for k, v in sp.items()}, "total": dict(tot),
                                 "rule": "strict: derive only if every valid cited segment has the same role; mixed roles are NOT derived",
                                 "note": "gold null speaker values are written as explicit by:null"}
    rep["sizes_chars_compact_json"] = {k: {"median": st.median(v), "max": max(v), "est_tokens_median": est_tokens(st.median(v)), "est_tokens_max": est_tokens(max(v))} for k, v in sizes.items()}
    rep["not_derivable_or_not_in_compact"] = {
        "responsible_person": "who must act; kept as explicit `responsible` (speaker of the cited line is often not the responsible person)",
        "reported_by_in_mixed_role_refs": f"{tot.get('mixed_roles', 0)} facts cite lines of more than one role; kept explicit",
        "quality_checks": "owner decision pending; dropped from compact gold, not materialised",
        "normalized_* fields": "model-produced canonical terms; not derivable",
        "confidence": "always null in gold (checked: %d non-null)" % rep["nonnull_confidence_fields"]}
    (out / "gold_conversion_report.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: rep[k] for k in ("records_converted", "evidence_records", "evidence_mapped", "fact_refs_mapped", "fact_refs_unmapped", "roundtrip_records_exact", "metadata_derivation_mismatch", "gold_primary_speakers_equal_transcript_table")}, indent=1))
    print("evidence_failed", len(rep["evidence_failed"]), "roundtrip differences", len(rep["roundtrip_differences"]))
    print("ref distribution", ref_report["distribution"], "le2", ref_report["share_le_2"], "le4", ref_report["share_le_4"])
    print("speaker derivation", rep["speaker_derivation"]["total"])
    print("sizes", {k: (v["median"], v["max"]) for k, v in rep["sizes_chars_compact_json"].items()})


if __name__ == "__main__":
    main()
