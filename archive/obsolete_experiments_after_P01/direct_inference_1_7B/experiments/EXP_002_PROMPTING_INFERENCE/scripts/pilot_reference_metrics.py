"""Reference values for the proposed P02 pilot gates, computed from the SAVED P00 and P01 outputs only (no inference).  Development-only.
Pilot ids (proposed, not yet approved): 00168 00204 00037 00092 00152 00157 00042 00165.
usage: python -B -s pilot_reference_metrics.py   -> evaluations/p00_p01_audit/PILOT_REFERENCE_METRICS.json"""
import collections
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
TRACK = HERE.parents[3]
sys.path.insert(0, str(TRACK / "scripts"))
import common_1_7b as C  # noqa: E402

sys.path.insert(0, str(C.EXP6 / "s1"))
import evaluate_s1 as E  # noqa: E402
from direct_inference_baseline.evaluation import evaluation_runner as ER  # noqa: E402
from direct_inference_baseline.evaluation.entity_matching import CATEGORIES, entity_list, match_category, prf  # noqa: E402

PILOT = ["00168", "00204", "00037", "00092", "00152", "00157", "00042", "00165"]
assert all(i in E.IDS[:30] for i in PILOT)
E1, E2 = TRACK / "experiments" / "EXP_001_DIRECT_INFERENCE", TRACK / "experiments" / "EXP_002_PROMPTING_INFERENCE"
RUN = {"P00": (E1, "P00_direct_dev50"), "P01": (E2, "P01_schema_guided_dev50")}
AUD = E2 / "evaluations" / "p00_p01_audit"


def close_structurally(text):
    t = text.strip()
    stack, in_str, esc, snaps = [], False, False, []
    for n, ch in enumerate(t):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch in "{[":
            stack.append(ch)
        elif ch in "}]":
            if not stack:
                break
            stack.pop()
            snaps.append((n + 1, "".join(stack)))
    for end, stk in reversed(snaps):
        cand = t[:end] + "".join("}" if c == "{" else "]" for c in reversed(stk))
        try:
            return json.loads(cand)
        except Exception:  # noqa: BLE001
            continue
    return None


def parsed(k, i):
    e, r = RUN[k]
    p = e / "outputs" / "parsed" / r / f"encounter_{i}.json"
    if p.exists():
        d = json.loads(p.read_text(encoding="utf-8"))
        return d.get("parsed", d) if isinstance(d, dict) and "parsed" in d else d
    return None


def closed(k, i):
    e, r = RUN[k]
    return close_structurally(json.loads((e / "outputs" / "raw" / r / f"encounter_{i}.json").read_text(encoding="utf-8"))["response_text"])


spy = C.G.StrictAccessSpy(allow_validation=False)
out = {"pilot_ids": PILOT, "note": "development-only; reference values for the proposed gates"}
with spy:
    gold = {i: ER.load_gold(i) for i in PILOT}

    def micro(k, mode):
        t = collections.Counter()
        for i in PILOT:
            p = parsed(k, i)
            if p is None and mode == "closure":
                p = closed(k, i)
            for cat in CATEGORIES:
                m = match_category(entity_list(gold[i], cat), entity_list(p or {}, cat), cat)
                t["tp"] += m["tp"]; t["fp"] += m["fp"]; t["fn"] += m["fn"]
        return {**prf(t["tp"], t["fp"], t["fn"]), "tp": t["tp"], "fp": t["fp"], "fn": t["fn"]}

    out["micro"] = {k: {"as_scored": micro(k, "scored"), "with_structural_closure_diagnostic": micro(k, "closure")} for k in RUN}
    out["status"] = {k: {i: ("parsed" if parsed(k, i) else "FAILED") for i in PILOT} for k in RUN}
    # category key-matched counts on pilot ids
    cat = {}
    for k in RUN:
        for c in ("symptoms", "negative_findings", "clinical_actions", "medications", "allergies", "vital_signs"):
            tp = fn = 0
            for i in PILOT:
                m = match_category(entity_list(gold[i], c), entity_list(parsed(k, i) or {}, c), c)
                tp += m["tp"]; fn += m["fn"]
            cat.setdefault(c, {})[k] = {"matched_by_key": tp, "gold": tp + fn}
    out["category_matches"] = cat
    # planned medications
    pl = {"gold_planned": 0}
    for k in RUN:
        pl[k + "_matched_planned_by_key"] = 0
    for i in PILOT:
        gp = [g for g in entity_list(gold[i], "medications") if g.get("status") == "planned"]
        pl["gold_planned"] += len(gp)
        for k in RUN:
            m = match_category(gp, entity_list(parsed(k, i) or {}, "medications"), "medications")
            pl[k + "_matched_planned_by_key"] += m["tp"]
    out["planned_medications"] = pl
    out["gold_facts"] = sum(len(entity_list(gold[i], c)) for i in PILOT for c in CATEGORIES)
# audit-derived: fully correct negatives etc. on pilot ids
rows = [json.loads(l) for l in open(AUD / "AUDIT_GOLD_FACTS.jsonl", encoding="utf-8")]
fc = collections.defaultdict(lambda: collections.Counter())
for r in rows:
    if r["id"] in PILOT:
        for k in RUN:
            fc[r["cat"]][k + "_" + r[k]] += 1
out["audit_classes_pilot"] = {c: dict(v) for c, v in fc.items()}
ev = json.loads((AUD / "EVIDENCE_AUDIT.json").read_text(encoding="utf-8"))
out["evidence_pilot_ids"] = {k: {x: sum((ev[i][k] or {}).get(x, 0) for i in PILOT) for x in ("evidence_records", "ev_exact_single_segment", "ev_multi_segment_or_whole_transcript_dump", "facts_checked", "fact_evidence_ok", "fact_no_evidence_ids")} for k in RUN}
(AUD / "PILOT_REFERENCE_METRICS.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
print(json.dumps({k: out[k] for k in ("micro", "status", "category_matches", "planned_medications", "gold_facts", "evidence_pilot_ids")}, indent=1))
