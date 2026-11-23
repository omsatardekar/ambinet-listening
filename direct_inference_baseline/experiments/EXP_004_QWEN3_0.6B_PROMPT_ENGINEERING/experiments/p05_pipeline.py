"""EXP_004 P05 stage 2-4: frozen R_cons v4 retrieval -> existing evidence builder -> final frozen-schema JSON. Pure functions of (stage-1 P02 JSON, transcript). No labels, no model, no file access of its own.
The extracted facts, their order and all non-evidence fields are never changed (asserted per record with verify_only_evidence_changed)."""
from __future__ import annotations

import copy

import p05_retrieval as R
from evidence_builder import build_evidence, entity_locations, verify_only_evidence_changed

STEPS = R.STEPS_V4


def postprocess(pred: dict, transcript: dict, top_key_order=None):
    """pred = parsed P02 output. Returns (final JSON, report) where report holds per-fact decisions with reason codes and the builder report."""
    enc = R.Enc(transcript["segments"])
    inter = copy.deepcopy(pred)
    decisions = []
    for loc, ent in entity_locations(inter):
        cat = loc.split("[")[0]
        d = R.retrieve(cat, ent, enc, STEPS)
        ent["source_segments"] = [enc.segs[i]["segment_id"] for i in d["segments"]]
        decisions.append({"location": loc, "category": cat, "decision": d["decision"], "reason": d["reason"], "score": round(float(d.get("score", 0.0)), 3), "segments": ent["source_segments"],
                          "context_question_added": bool(d.get("context_question"))})
    final, rep = build_evidence(inter, transcript, top_key_order=top_key_order)
    integ = verify_only_evidence_changed(pred, final)
    assert integ["identical_except_evidence_fields"] and integ["n_items_before"] == integ["n_items_after"], "builder changed something other than evidence fields"
    rep["integrity_identical_except_evidence_fields"] = True
    return final, {"builder": rep, "decisions": decisions, "cited": sum(d["decision"] == "cited" for d in decisions), "abstained": sum(d["decision"] != "cited" for d in decisions)}
