"""EXP_004 read-only inspection of the completed (partial) P03 outputs: where does the single evidence record come from, what does it support, examples of wrong associations.
Uses prompt_dev ids only; reads inputs and parsed predictions; no labels needed."""
import json
import re
import sys
from collections import Counter

from common import EXP4, S, SPLIT, write_json
from direct_inference_baseline.evaluation.entity_matching import CATEGORIES, KEYS, entity_list, norm_text
from direct_inference_baseline.evaluation.evidence_evaluator import lexical_support

RUN = "P03_evidence_grounded_dev50"
pdir = EXP4 / "outputs" / RUN / "parsed_predictions" / RUN
ids = sorted(p.stem.replace("encounter_", "") for p in pdir.glob("encounter_*.json"))
assert set(ids) <= set(SPLIT["prompt_dev_ids"])
stat = Counter(); detail = {}
mm = lambda s: f"{int(s)//60:02d}:{int(s)%60:02d}"
for eid in ids:
    tr = json.loads((S.INPUT_DIR / f"encounter_{eid}.json").read_text(encoding="utf-8")); segs = tr["segments"]
    pred = json.loads((pdir / f"encounter_{eid}.json").read_text(encoding="utf-8"))
    evl = [e for e in (pred.get("clinical_evidence") or []) if isinstance(e, dict)]
    stat["records"] += 1; stat["evidence_records"] += len(evl)
    stat["records_with_exactly_one_evidence"] += len(evl) == 1
    ents = []
    for c in CATEGORIES:
        for i, e in enumerate(entity_list(pred, c)):
            ents.append((c, i, e))
    n_with = sum(bool(e.get("evidence_ids")) for _, _, e in ents)
    stat["entities"] += len(ents); stat["entities_with_ids"] += n_with
    stat["records_where_no_entity_has_ids"] += n_with == 0
    for ev in evl:
        t = norm_text(ev.get("transcript_text"))
        idx = [k for k, s in enumerate(segs) if t and (t == norm_text(s["text"]) or t in norm_text(s["text"]))]
        k0 = idx[0] if idx else None
        stat["ev_is_first_segment"] += k0 == 0
        stat["ev_in_first_3_segments"] += k0 is not None and k0 < 3
        stat["ev_found"] += k0 is not None
        # does the cited line actually state the items that cite it?
        for c, i, e in ents:
            if ev.get("evidence_id") in (e.get("evidence_ids") or []):
                key = KEYS[c](e)
                stat["cited_items"] += 1
                if key and lexical_support(norm_text(key) if "|" not in str(key) else key, ev.get("transcript_text") or "", strict=False):
                    stat["cited_items_lexically_supported_lenient"] += 1
        ts_a, ts_b = ev.get("start_timestamp"), ev.get("end_timestamp")
        stat["ts_placeholder_or_unparsable"] += not (re.fullmatch(r"\d{1,3}:\d{2}", str(ts_a)) and re.fullmatch(r"\d{1,3}:\d{2}", str(ts_b)))
        stat["ts_zero_zero"] += str(ts_a) == "00:00"
    detail[eid] = {"n_segments": len(segs), "n_evidence_records": len(evl), "entities": len(ents), "entities_with_evidence_ids": n_with,
                   "evidence": [{"evidence_id": e.get("evidence_id"), "speaker_id": e.get("speaker_id"), "speaker_role": e.get("speaker_role"), "text": (e.get("transcript_text") or "")[:140], "start": e.get("start_timestamp"),
                                 "end": e.get("end_timestamp"), "supports": e.get("supports")} for e in evl],
                   "matching_segment": None}
    if evl:
        t = norm_text(evl[0].get("transcript_text")); hit = [s for s in segs if t and t in norm_text(s["text"])]
        if hit:
            s = hit[0]; detail[eid]["matching_segment"] = {"segment_id": s["segment_id"], "speaker_id": s["speaker_id"], "role": s["role"], "start_mmss_floor": mm(s["start_seconds"]), "end_mmss_floor": mm(s["end_seconds"])}
    detail[eid]["items_with_ids"] = [{"loc": f"{c}[{i}]", "key": str(KEYS[c](e))[:60], "evidence_ids": e.get("evidence_ids")} for c, i, e in ents if e.get("evidence_ids")][:6]
    detail[eid]["first_segments"] = [f"{s['segment_id']} {s['speaker_id']} {s['role']} {s['start_seconds']:.2f}-{s['end_seconds']:.2f}: {s['text'][:90]}" for s in segs[:3]]
write_json(EXP4 / "evaluation" / "P03_PARTIAL" / "evidence_inspection.json", {"stats": dict(stat), "per_encounter": detail})
print(json.dumps(dict(stat)))
for eid in ("00215", "00248"):
    if eid in detail:
        print(eid, json.dumps(detail[eid], indent=1, ensure_ascii=False))
        print("   items with evidence: all items listed above;  total items", detail[eid]["entities"])
    else:
        print(eid, "no parsed P03 output (failed or not attempted)")
