"""EXP_004 evidence diagnostics (read-only, no inference). For existing parsed predictions of P00/P01/P02 on the 50 prompt_dev ids (or any run via argv):
 (a) evaluator-based numbers via the UNMODIFIED evaluator (ER.score_encounter + ER.aggregate): grounding strict/lenient/partial/unsupported, speaker attribution, unsupported claims, micro P/R/F1;
 (b) SUPPLEMENTARY evidence checks the evaluator does not make (defined here, evaluator untouched): evidence_ids presence/resolution, evidence-record validity decomposition, role match,
     timestamp match (+-1 s) to the segment that contains the text, `supports` locations (exist + reciprocal), evidence records per encounter vs distinct cited segments.
usage: evidence_diagnostics.py <label> <parsed_dir> [<label> <parsed_dir> ...]   (written to evaluation/evidence_diagnostics_<labels>.json)"""
import json
import re
import sys
from collections import Counter

from common import EXP3, EXP4, SPLIT, S, write_json
from direct_inference_baseline.evaluation import evaluation_runner as ER
from direct_inference_baseline.evaluation.entity_matching import CATEGORIES, entity_list, norm_text

import os
IDS = json.loads(os.environ["EXP4_IDS_JSON"]) if os.environ.get("EXP4_IDS_JSON") else SPLIT["prompt_dev_ids"]  # optional override (partial-run evaluation); default = the 50 prompt_dev ids
assert set(IDS) <= set(SPLIT["prompt_dev_ids"])
SEC = ["symptoms", "negative_findings", "medications", "allergies", "vital_signs", "physical_examination", "review_of_systems", "clinical_conditions", "clinical_assessment",
       "procedures_and_investigations", "clinical_actions", "follow_up", "clinical_uncertainties"]
MH = ["past_medical_history", "surgical_history", "family_history", "social_history"]


def ts_to_s(x):
    m = re.fullmatch(r"\s*(\d{1,3}):(\d{2})\s*", str(x or ""))
    return int(m.group(1)) * 60 + int(m.group(2)) if m else None


def locations(pred):
    """All entity locations as 'section[i]' / 'medical_history.sub[i]' / 'chief_complaint' -> entity dict (dict entities only)."""
    loc = {}
    cc = pred.get("chief_complaint")
    if isinstance(cc, dict):
        loc["chief_complaint"] = cc
    for s in SEC:
        v = pred.get(s)
        if isinstance(v, list):
            for i, e in enumerate(v):
                if isinstance(e, dict):
                    loc[f"{s}[{i}]"] = e
    mh = pred.get("medical_history")
    if isinstance(mh, dict):
        for s in MH:
            v = mh.get(s)
            if isinstance(v, list):
                for i, e in enumerate(v):
                    if isinstance(e, dict):
                        loc[f"medical_history.{s}[{i}]"] = e
    return loc


def analyse(label, pdir):
    results, c, ev_per_enc, distinct_cited = [], Counter(), [], []
    for eid in IDS:
        f = pdir / f"encounter_{eid}.json"
        tr = json.loads((S.INPUT_DIR / f"encounter_{eid}.json").read_text(encoding="utf-8"))
        pred = json.loads(f.read_text(encoding="utf-8")) if f.exists() else None
        results.append(ER.score_encounter(ER.load_gold(eid), pred, tr))
        if pred is None:
            continue
        c["records"] += 1
        segs = tr["segments"]
        nsegs = {s["segment_id"]: s for s in segs}
        evl = [e for e in (pred.get("clinical_evidence") or []) if isinstance(e, dict)]
        evmap = {e.get("evidence_id"): e for e in evl}
        ev_per_enc.append(len(evl))
        loc = locations(pred)
        cited_ids = set()
        for l, e in loc.items():
            c["entities"] += 1
            ids = e.get("evidence_ids") if isinstance(e.get("evidence_ids"), list) else []
            if ids:
                c["entities_with_evidence_ids"] += 1
            for i in ids:
                cited_ids.add(i)
                c["evidence_id_refs"] += 1
                c["evidence_id_refs_resolving"] += i in evmap
        for e in evl:
            c["evidence_records"] += 1
            t, spk = norm_text(e.get("transcript_text")), e.get("speaker_id")
            host = [s for s in segs if t and (t == norm_text(s["text"]) or t in norm_text(s["text"]))]
            if not t:
                c["ev_text_empty"] += 1
            elif not host:
                c["ev_text_not_in_transcript"] += 1
            else:
                c["ev_text_in_transcript"] += 1
                c["ev_text_exact_whole_segment"] += any(t == norm_text(s["text"]) for s in host)
                ok = [s for s in host if s["speaker_id"] == spk]
                if ok:
                    c["ev_speaker_correct"] += 1
                    s0 = ok[0]
                    role = norm_text(e.get("speaker_role"))
                    c["ev_role_correct"] += role == norm_text(s0["role"])
                    a, b = ts_to_s(e.get("start_timestamp")), ts_to_s(e.get("end_timestamp"))
                    if a is not None and b is not None:
                        c["ev_timestamp_parsable"] += 1
                        c["ev_timestamp_match_pm1s"] += abs(a - s0["start_seconds"]) <= 1.0 and abs(b - s0["end_seconds"]) <= 1.0
                        c["ev_timestamp_match_exact_floor"] += a == int(s0["start_seconds"]) and b == int(s0["end_seconds"])
                else:
                    c["ev_speaker_wrong"] += 1
            sup = e.get("supports")
            if not isinstance(sup, list) or not sup:
                c["ev_supports_empty_or_missing"] += 1
            else:
                for s_ in sup:
                    c["supports_refs"] += 1
                    tgt = loc.get(s_)
                    if tgt is not None:
                        c["supports_refs_exist"] += 1
                        if e.get("evidence_id") in (tgt.get("evidence_ids") or []):
                            c["supports_refs_reciprocal"] += 1
        distinct_cited.append(len(cited_ids))
    agg = ER.aggregate(results)
    st = agg["strict"]["micro"]
    r = lambda a, b: round(a / b, 4) if b else None
    return {"label": label, "parsed_records": c["records"],
            "evaluator": {"micro_precision": st["precision"], "micro_recall": st["recall"], "micro_f1": st["f1"], "grounding": agg["evidence_grounding"], "speaker_attribution": agg["speaker_attribution"],
                          "unsupported_claims": agg["unsupported_claims"]},
            "supplementary": {"counts": dict(c), "entities_with_evidence_ids_rate": r(c["entities_with_evidence_ids"], c["entities"]), "evidence_id_resolves_rate": r(c["evidence_id_refs_resolving"], c["evidence_id_refs"]),
                              "ev_records_mean_per_encounter": round(sum(ev_per_enc) / max(1, len(ev_per_enc)), 2), "distinct_cited_evidence_mean_per_encounter": round(sum(distinct_cited) / max(1, len(distinct_cited)), 2),
                              "ev_text_in_transcript_rate": r(c["ev_text_in_transcript"], c["evidence_records"]), "ev_text_exact_whole_segment_rate": r(c["ev_text_exact_whole_segment"], c["evidence_records"]),
                              "ev_speaker_correct_rate": r(c["ev_speaker_correct"], c["evidence_records"]), "ev_role_correct_rate": r(c["ev_role_correct"], c["ev_speaker_correct"]),
                              "ev_timestamp_match_rate": r(c["ev_timestamp_match_pm1s"], c["evidence_records"]), "ev_timestamp_exact_floor_rate": r(c["ev_timestamp_match_exact_floor"], c["evidence_records"]), "ev_supports_nonempty_rate": r(c["evidence_records"] - c["ev_supports_empty_or_missing"], c["evidence_records"]),
                              "supports_refs_exist_rate": r(c["supports_refs_exist"], c["supports_refs"]), "supports_refs_reciprocal_rate": r(c["supports_refs_reciprocal"], c["supports_refs"])}}


args = sys.argv[1:]
out = [analyse(args[i], (EXP4.parents[0] / args[i + 1]) if not re.match(r"^[A-Za-z]:", args[i + 1]) else __import__("pathlib").Path(args[i + 1])) for i in range(0, len(args), 2)]
name = "_".join(o["label"] for o in out)
write_json(EXP4 / "evaluation" / f"evidence_diagnostics_{name}.json", out)
for o in out:
    e, s_ = o["evaluator"], o["supplementary"]
    g = e["grounding"]
    print(o["label"], "| P/R/F1 %.3f/%.3f/%.3f" % (e["micro_precision"], e["micro_recall"], e["micro_f1"]), "| grounding", {k: g[k] for k in ("grounded_strict", "grounded_lenient", "partially_supported", "unsupported", "total")},
          "| speaker", round(e["speaker_attribution"]["accuracy"] or 0, 3), e["speaker_attribution"]["denominator_evaluated"], "| unsupp", round(e["unsupported_claims"]["unsupported_claim_rate_of_predictions"], 3))
    print("   ", {k: v for k, v in s_.items() if k != "counts"})
