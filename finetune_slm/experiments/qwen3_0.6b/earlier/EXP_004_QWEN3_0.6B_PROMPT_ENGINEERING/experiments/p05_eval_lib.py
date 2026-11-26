"""EXP_004 P05 evaluation library (metrics for facts, citations and abstentions). Reads gold labels ONLY for the ids it is given (the caller guarantees the scope); used after generation. No model, no inference.
Metrics are deliberately kept separate: coverage (cited / extracted), agreement with gold-cited segments WHEN CITED, agreement counting abstentions as misses, behaviour counters; none of them is clinical accuracy."""
from __future__ import annotations

import json
from collections import Counter, defaultdict

from common import S
import p05_retrieval as R
from direct_inference_baseline.evaluation import evaluation_runner as ER
from direct_inference_baseline.evaluation.entity_matching import CATEGORIES, entity_list, match_category, norm_text

mm = lambda s: f"{int(s)//60:02d}:{int(s)%60:02d}"
GROUPS = {"positive findings (chief complaint, symptoms, conditions)": ["chief_complaint", "symptoms", "clinical_conditions"], "negative findings": ["negative_findings"], "medications": ["medications"], "allergies": ["allergies"],
          "vital signs": ["vital_signs"], "family history": ["medical_history.family_history"], "surgical history": ["medical_history.surgical_history"],
          "assessment, procedures and clinical actions": ["clinical_assessment", "procedures_and_investigations", "clinical_actions"],
          "other (past history, social history, exam, review of systems, follow-up, uncertainties)": ["medical_history.past_medical_history", "medical_history.social_history", "physical_examination", "review_of_systems", "follow_up", "clinical_uncertainties"],
          "speaker-sensitive facts (categories with a hard speaker-class rule)": list(R.EXPECT_CLASS)}


def load_transcript(eid):
    return json.loads((S.INPUT_DIR / f"encounter_{eid}.json").read_text(encoding="utf-8"))


def gold_segment_map(eid, segs):
    g = ER.load_gold(eid)
    seg_of = {}
    for r in g.get("clinical_evidence", []):
        t = norm_text(r["transcript_text"])
        hit = [i for i, s in enumerate(segs) if t == norm_text(s["text"]) and s["speaker_id"] == r["speaker_id"] and mm(s["start_seconds"]) == r["start_timestamp"]]
        seg_of[r["evidence_id"]] = hit[0] if hit else None
    return g, seg_of


def gold_set(seg_of, ge):
    return {seg_of[x] for x in (ge.get("evidence_ids") or []) if seg_of.get(x) is not None}


def post_flags(cat, item, enc, sel):
    f = Counter()
    if not sel:
        return f
    nonq = [i for i in sel if not enc.q[i]] or list(sel)
    f["question_only"] += all(enc.q[i] for i in sel)
    f["greeting_like"] += any(i <= 1 and (set(enc.raw[i]) & R.SMALLTALK) and len(enc.words[i]) <= 12 for i in sel)
    f["position0"] += 0 in sel
    fields = R.query_fields(cat, item)
    matched = list({s for st in fields.values() for s in st if any(R.sm(s, w) for i in nonq for w in enc.words[i])})
    if cat == "negative_findings":
        f["polarity_conflict"] += not any(R.has_neg(enc.raw[i]) for i in nonq)
    elif not R.item_negative(cat, item):
        f["polarity_conflict"] += any(R.anchor_negated(enc, i, matched) for i in nonq)
    if cat == "medical_history.family_history":
        f["kin_conflict"] += not any(R.has_kin(enc.raw[i]) for i in nonq)
    elif cat in R.OWN_HISTORY:
        f["kin_conflict"] += any(R.kin_conflict(enc, i, matched) for i in nonq)
    exp = R.EXPECT_CLASS.get(cat)
    if exp:
        f["speaker_class_conflict"] += any(R.role_class(enc.role[i]) != exp for i in nonq)
    return f


def accumulate(tot, cat, item, enc, selection, G):
    """selection: dict(decision, reason, segments). G = gold-cited set (may be empty = no reference)."""
    sel = set(selection["segments"])
    for key in (cat, "ALL"):
        k = tot[key]; k["n"] += 1; k["gold"] += len(G)
        if selection["decision"] == "cited":
            k["cited"] += 1; k["hit"] += bool(sel & G); k["inter"] += len(sel & G); k["sel"] += len(sel)
            for fl, v in post_flags(cat, item, enc, sel).items():
                k[fl] += v
        else:
            k["abstain_" + selection["reason"]] += 1


def row(k):
    n, c = k["n"], k["cited"]
    return {"n": n, "cited": c, "coverage_cited_over_n": round(c / n, 4) if n else None, "hit_when_cited": round(k["hit"] / c, 4) if c else None, "hit_abstentions_as_misses": round(k["hit"] / n, 4) if n else None,
            "set_precision": round(k["inter"] / k["sel"], 4) if k["sel"] else None, "set_recall": round(k["inter"] / k["gold"], 4) if k["gold"] else None,
            **{f"{fl}_of_cited": (round(k[fl] / c, 4) if c else None) for fl in ("question_only", "greeting_like", "position0", "polarity_conflict", "kin_conflict", "speaker_class_conflict")},
            "counts": {fl: k[fl] for fl in ("question_only", "greeting_like", "position0", "polarity_conflict", "kin_conflict", "speaker_class_conflict")}, "abstain_reasons": {x[8:]: v for x, v in k.items() if x.startswith("abstain_")}}


def group_rows(tot):
    out = {}
    for g, cats in GROUPS.items():
        k = Counter()
        for c in cats:
            k.update(tot.get(c, Counter()))
        out[g] = row(k) if k["n"] else None
    return out


def matched_facts(eid, final, gold, seg_of):
    """strict-TP (gold, predicted) pairs of one record -> list of (category, predicted entity dict, gold-cited set)"""
    out = []
    for c in CATEGORIES:
        m = match_category(entity_list(gold, c), entity_list(final, c), c)
        for ge, pe in m["pairs"]:
            G = gold_set(seg_of, ge)
            if G:
                out.append((c, pe, G))
    return out
