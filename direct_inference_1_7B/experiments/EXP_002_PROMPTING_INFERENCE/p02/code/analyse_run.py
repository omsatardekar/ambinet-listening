"""Category-level, partial-extraction and speaker-attribution analysis of one run (full P01 schema) against gold, using the FROZEN strict matcher unchanged.
Read-only. Usage: python -B -I analyse_run.py --label P01 --parsed D --failed D --raw D --ids-file F --out derived/NAME.json
Official metric = tier 1 (all records; a failed record scores zero predictions). Parsed-only is reported next to it, never instead of it.
Speaker attribution is analysed only on facts the strict matcher paired with a gold fact (otherwise there is nothing to compare)."""
from __future__ import annotations

import argparse
import json
import statistics as st
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from p02_evaluate import evaluate, load_run                   # noqa: E402
from p02_common import categories, compact_schema, entity_matching, get_entities, load_gold   # noqa: E402

EM = entity_matching()
SPK = compact_schema()["speaker_field"]
ROLES = {"doctor", "patient", "nurse", "caregiver", "family_member", "clinical_staff", "unknown"}


def speaker_analysis(recs):
    c = defaultdict(Counter)
    wrong = []
    for eid, r in recs.items():
        if r["status"] != "parsed":
            continue
        g = load_gold(eid)
        for cat in categories():
            f = SPK.get(cat)
            if not f:
                continue
            m = EM.match_category(EM.entity_list(g, cat), EM.entity_list(r["obj"], cat), cat)
            for ge, pe in m["pairs"]:
                gv, pv = ge.get(f), pe.get(f)
                k = c[cat]
                k["pairs"] += 1
                if pv in (None, ""):
                    k["missing"] += 1
                elif isinstance(pv, str) and pv.lower() == str(gv).lower():
                    k["correct_role"] += 1
                elif isinstance(pv, str) and pv not in ROLES:
                    k["not_a_role_value"] += 1
                    wrong.append({"id": eid, "cat": cat, "gold": gv, "pred": pv})
                else:
                    k["wrong_role"] += 1
                    wrong.append({"id": eid, "cat": cat, "gold": gv, "pred": pv})
    tot = Counter()
    for v in c.values():
        tot.update(v)
    return {"per_category": {k: dict(v) for k, v in c.items()}, "total": dict(tot), "examples_wrong": wrong[:12]}


def partial_examples(recs, n=6):
    out = []
    for eid, r in recs.items():
        if r["status"] != "parsed":
            continue
        g = load_gold(eid)
        for cat in categories():
            ge = EM.entity_list(g, cat)
            pe = EM.entity_list(r["obj"], cat)
            m = EM.match_category(ge, pe, cat)
            if m["tp"] and m["fn"]:
                gk = [EM.norm_text(EM.KEYS[cat](e) or "") for e in ge]
                pk = [EM.norm_text(EM.KEYS[cat](e) or "") for e in pe]
                out.append({"id": eid, "category": cat, "gold": len(EM.keyed(ge, cat)), "matched": m["tp"], "missing": m["fn"], "extra": m["fp"],
                            "gold_keys": [k for k in gk if k][:8], "pred_keys": [k for k in pk if k][:8]})
    out.sort(key=lambda x: -x["gold"])
    return out[:n]


def fp_examples(recs, n=3):
    c = defaultdict(list)
    for eid, r in recs.items():
        if r["status"] != "parsed":
            continue
        g = load_gold(eid)
        for cat in categories():
            ge, pe = EM.entity_list(g, cat), EM.entity_list(r["obj"], cat)
            m = EM.match_category(ge, pe, cat)
            if m["fp"]:
                gset = {EM.norm_text(EM.KEYS[cat](e) or "") for e in ge}
                extras = [EM.KEYS[cat](e) for e in pe if EM.KEYS[cat](e) and EM.norm_text(EM.KEYS[cat](e)) not in gset]
                c[cat] += [(eid, x) for x in extras[:2]]
    return {k: v[:n] for k, v in c.items()}


def fuzzy_diagnostic(recs):
    """ADDITIONAL diagnostic, not the official metric: the frozen matcher's own fuzzy mode (token Jaccard >= 0.75 or difflib ratio >= 0.85) credits paraphrases that the strict key rejects.
    Per category over ALL records (failed records contribute their gold as misses): strict tp, extra fuzzy-paired, resulting recall."""
    out = {}
    for cat in categories():
        g_n = s_tp = f_tp = p_n = 0
        for eid, r in recs.items():
            ge = EM.entity_list(load_gold(eid), cat)
            pe = EM.entity_list(r["obj"], cat) if r["status"] == "parsed" else []
            m = EM.match_category(ge, pe, cat, fuzzy=True)
            g_n += len(EM.keyed(ge, cat))
            p_n += len(EM.keyed(pe, cat))
            s_tp += m["tp"]
            f_tp += len(m["fuzzy_pairs"])
        out[cat] = {"gold": g_n, "pred": p_n, "strict_tp": s_tp, "fuzzy_extra_tp": f_tp, "fuzzy_recall": round((s_tp + f_tp) / g_n, 4) if g_n else None,
                    "fuzzy_precision": round((s_tp + f_tp) / p_n, 4) if p_n else None, "count_ratio_pred_over_gold": round(p_n / g_n, 3) if g_n else None}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--parsed", required=True)
    ap.add_argument("--failed", required=True)
    ap.add_argument("--raw", required=True)
    ap.add_argument("--ids-file", required=True)
    ap.add_argument("--out", required=True)
    A = ap.parse_args()
    ids = json.loads(Path(A.ids_file).read_text(encoding="utf-8-sig"))["ids"]
    recs = load_run(A.parsed, A.failed, A.raw, ids)
    E = evaluate(recs, "full", label=A.label)
    res = {k: v for k, v in E.items() if k != "_scored"}
    res["speaker_attribution_on_matched_facts"] = speaker_analysis(recs)
    res["fuzzy_completeness_diagnostic_not_official"] = fuzzy_diagnostic(recs)
    res["partial_extraction_examples"] = partial_examples(recs)
    res["false_positive_examples"] = fp_examples(recs)
    res["failure_types"] = dict(Counter(r["failure"] for r in recs.values() if r["status"] == "failed"))
    res["records_scored"] = len(recs)
    Path(A.out).write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    t1 = res["entities_tier1_all_records_failed_as_zero"]
    print(A.label, "records", len(recs), "parsed", res["validity"]["parsed"], "| tier1 micro", {k: t1["micro"][k] for k in ("precision", "recall", "f1", "tp", "fp", "fn")})
    for c, v in t1["per_category"].items():
        print(f"  {c:38} gold {v['gold']:4} pred {v['pred']:4} tp {v['tp']:3} fp {v['fp']:3} fn {v['fn']:3}  P {v['precision']} R {v['recall']} F1 {v['f1']}")
    print("speaker", res["speaker_attribution_on_matched_facts"]["total"])


if __name__ == "__main__":
    main()
