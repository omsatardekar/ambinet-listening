"""EXP_004 Phase 3 pre-work: READ-ONLY error-pattern analysis of the finished EXP_003 100-record development run.
Uses the existing evaluator's matching functions unmodified. Reads EXP_003 parsed predictions + frozen development labels/inputs; writes only inside EXP_004/analysis.
No inference. Locked-test ids are never read."""
import difflib
import json
import re
import sys
import types
from collections import Counter, defaultdict
from pathlib import Path

try:
    import dotenv  # noqa
except ImportError:
    sys.modules["dotenv"] = types.SimpleNamespace(load_dotenv=lambda *a, **k: False)
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
EXP4 = HERE.parent
ROOT = EXP4.parents[2]
sys.path.insert(0, str(ROOT))
from direct_inference_baseline.config import settings as S  # noqa: E402
from direct_inference_baseline.evaluation import evaluation_runner as ER  # noqa: E402
from direct_inference_baseline.evaluation import evidence_evaluator as EE  # noqa: E402
from direct_inference_baseline.evaluation import schema_validator as SV  # noqa: E402
from direct_inference_baseline.evaluation.dataset_split import load_split  # noqa: E402
from direct_inference_baseline.evaluation.entity_matching import CATEGORIES, KEYS, entity_list, match_category, norm_text  # noqa: E402

EXP3 = EXP4.parent / "EXP_003_QWEN3_0.6B_OPENVINO_GPU_DIRECT"
dev = load_split("development")
assert len(dev) == 100 and not (set(dev) & set(load_split("test")))
man = json.loads((EXP3 / "run_manifest_dev100.json").read_text(encoding="utf-8"))

fp_by_cat = defaultdict(list)       # (eid, key, supported, nearest gold key, ratio)
fn_by_cat = defaultdict(list)       # (eid, gold key, found in other category?, in transcript?)
pred_n, gold_n = Counter(), Counter()
empty_sections = Counter()
valid_n = 0
ev_stats = Counter()
viol = Counter()
viol_examples = {}
role_conf = Counter()
raw_enum_vals = defaultdict(Counter)
for eid in dev:
    rec = man["records"][eid]
    gold = ER.load_gold(eid)
    tr = json.loads((S.INPUT_DIR / f"encounter_{eid}.json").read_text(encoding="utf-8"))
    full = " ".join(norm_text(s["text"]) for s in tr["segments"])
    if rec["status"] != "parsed":
        continue
    valid_n += 1
    pred = json.loads((EXP3 / "parsed_predictions" / "exp_003_dev_100" / f"encounter_{eid}.json").read_text(encoding="utf-8"))
    allpred_text = {c: " ".join(norm_text(KEYS[c](e)) for e in entity_list(pred, c) if KEYS[c](e)) for c in CATEGORIES}
    for cat in CATEGORIES:
        g, p = entity_list(gold, cat), entity_list(pred, cat)
        gold_n[cat] += len(g)
        pred_n[cat] += len(p)
        if not p:
            empty_sections[cat] += 1
        m = match_category(g, p, cat, fuzzy=True)
        gkeys = [k for k, _ in m["fn_entities"]]
        for k, e in m["fp_entities"]:
            sup = EE.lexical_support(k, full, strict=False)
            near = max(((difflib.SequenceMatcher(None, k, gk).ratio(), gk) for gk in gkeys), default=(0, None))
            fp_by_cat[cat].append((eid, k, sup, near[1], round(near[0], 2)))
        for k, e in m["fn_entities"]:
            other = [c for c in CATEGORIES if c != cat and k and k in allpred_text[c]]
            fn_by_cat[cat].append((eid, k, other, EE.lexical_support(k, full, strict=False)))
    # evidence-grounding failure reasons
    evrecs = {r.get("evidence_id"): r for r in (pred.get("clinical_evidence") or []) if isinstance(r, dict)}
    segs = EE._segments(tr)
    for r in evrecs.values():
        ev_stats["evidence_records"] += 1
        if EE.real_segment(r, segs):
            ev_stats["evidence_record_real_segment"] += 1
        else:
            t, sp = norm_text(r.get("transcript_text")), r.get("speaker_id")
            if not t:
                ev_stats["evidence_text_empty"] += 1
            elif any(t in s for _, _, s in segs):
                ev_stats["evidence_text_ok_but_speaker_id_wrong"] += 1
            else:
                ev_stats["evidence_text_not_a_transcript_segment"] += 1
    for cat in CATEGORIES:
        for e in entity_list(pred, cat):
            if not KEYS[cat](e):
                continue
            ids = e.get("evidence_ids") if isinstance(e.get("evidence_ids"), list) else []
            ev_stats["entities"] += 1
            if not ids:
                ev_stats["entity_no_evidence_ids"] += 1
            elif not any(i in evrecs for i in ids):
                ev_stats["entity_evidence_ids_not_in_clinical_evidence"] += 1
            elif not any(EE.real_segment(evrecs[i], segs) for i in ids if i in evrecs):
                ev_stats["entity_evidence_not_real_segment"] += 1
    ev_stats["encounters_with_clinical_evidence"] += bool(evrecs)
    # schema violations (existing validator), generalised message
    rep = SV.validate(pred)
    for v in getattr(rep, "violations", []) or []:
        kind, msg = (v if isinstance(v, (tuple, list)) else (v.get("kind"), v.get("message"))) if not isinstance(v, str) else ("?", v)
        g = re.sub(r"\[\d+\]", "[]", str(msg))
        g = re.sub(r"='[^']*'", "='X'", g) if kind == "enum_violation" else g
        viol[(kind, g)] += 1
    for sec in ("reported_by", "observed_by", "stated_by"):
        for cat in CATEGORIES:
            for e in entity_list(pred, cat):
                if sec in e:
                    role_conf[(sec, str(e[sec]))] += 1

summary = {"valid_predictions_analysed": valid_n, "gold_entities_by_category": dict(gold_n), "predicted_entities_by_category": dict(pred_n),
           "valid_encounters_with_empty_section": dict(empty_sections)}
fp_summary = {}
for cat, rows in fp_by_cat.items():
    sup = sum(1 for r in rows if r[2])
    near = sum(1 for r in rows if r[3] and r[4] >= 0.5)
    fp_summary[cat] = {"fp": len(rows), "transcript_supported": sup, "unsupported": len(rows) - sup, "has_similar_unmatched_gold_key_ratio>=0.5": near,
                       "examples": [{"enc": r[0], "pred_key": r[1], "nearest_gold_unmatched": r[3], "ratio": r[4]} for r in rows[:12]]}
fn_summary = {}
for cat, rows in fn_by_cat.items():
    fn_summary[cat] = {"fn": len(rows), "gold_key_lexically_in_transcript": sum(1 for r in rows if r[3]),
                       "predicted_under_another_category": sum(1 for r in rows if r[2]), "examples": [{"enc": r[0], "gold_key": r[1]} for r in rows[:10]]}
tot_fp = sum(len(v) for v in fp_by_cat.values())
tot_sup = sum(1 for v in fp_by_cat.values() for r in v if r[2])
tot_near = sum(1 for v in fp_by_cat.values() for r in v if r[3] and r[4] >= 0.5)
out = {"note": "valid predictions only (94); all numbers computed with the unmodified evaluator functions", "summary": summary, "fp_total": tot_fp, "fp_transcript_supported": tot_sup,
       "fp_with_similar_unmatched_gold_key": tot_near, "false_positives_by_category": fp_summary, "false_negatives_by_category": fn_summary,
       "evidence": dict(ev_stats), "schema_violation_patterns_top40": [{"kind": k[0], "pattern": k[1], "count": c} for k, c in viol.most_common(40)],
       "schema_violation_kind_totals": dict(Counter({k[0]: 0 for k in viol}) + Counter()) if False else dict(sum((Counter({k[0]: c}) for k, c in viol.items()), Counter())),
       "speaker_role_values_emitted_top": [{"field": k[0], "value": k[1], "count": c} for k, c in role_conf.most_common(15)]}
(HERE / "error_analysis_exp003.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
print(json.dumps({k: out[k] for k in ("fp_total", "fp_transcript_supported", "fp_with_similar_unmatched_gold_key", "evidence", "schema_violation_kind_totals")}, indent=1))
