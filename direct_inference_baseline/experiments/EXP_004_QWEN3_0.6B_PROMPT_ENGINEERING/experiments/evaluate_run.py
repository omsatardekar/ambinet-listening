"""EXP_004 evaluation of one finished run with the EXISTING evaluator (unmodified), plus a paired comparison with the P00 (EXP_003) outputs on the SAME ids
and the pre-registered P01 keep/reject rule. usage: evaluate_run.py <run_id> <prompt_file> <subset: prompt_dev|validation>
Labels are opened here only (after inference). No inference."""
import json
import random
import statistics as st
import sys
from collections import Counter

from common import EXP3, EXP4, SPLIT, S, sha256_file, use_run, write_json
from direct_inference_baseline.evaluation import evaluation_runner as ER
from direct_inference_baseline.evaluation.entity_matching import CATEGORIES, prf

run_id, prompt_file, subset = sys.argv[1:4]
IDS = {"prompt_dev": SPLIT["prompt_dev_ids"], "validation": SPLIT["validation_ids"]}[subset]
use_run(run_id, prompt_file)
man = json.loads((S.REPORT_DIR / run_id / "run_manifest.json").read_text(encoding="utf-8"))
assert set(man["records"]) == set(IDS), "run must cover exactly the subset ids"
report = ER.evaluate_experiment(run_id)
p00 = json.loads((EXP3 / "run_manifest_dev100.json").read_text(encoding="utf-8"))["records"]
out = EXP4 / "evaluation" / run_id
per_new, per_old = {}, {}
for eid in IDS:
    rec = man["records"][eid]
    gold = ER.load_gold(eid)
    tr = json.loads((S.INPUT_DIR / f"encounter_{eid}.json").read_text(encoding="utf-8"))
    pred = json.loads((S.PARSED_DIR / run_id / f"encounter_{eid}.json").read_text(encoding="utf-8")) if rec["status"] == "parsed" else None
    per_new[eid] = ER.score_encounter(gold, pred, tr)["strict"]
    write_json(out / "per_encounter" / f"encounter_{eid}.json", {"encounter_id": eid, "status": rec["status"], "failure_type": rec.get("failure_type"), "scores_strict": per_new[eid],
               "schema_violation_counts": rec.get("schema_violation_counts"), "completion_tokens": rec.get("completion_tokens"), "latency_seconds": rec.get("latency_seconds")})
    per_old[eid] = json.loads((EXP3 / "per_encounter_results_dev100" / f"encounter_{eid}.json").read_text(encoding="utf-8"))["scores"]["strict"]


def totals(per, ids):
    c = {k: [0, 0, 0] for k in CATEGORIES}
    for e in ids:
        for k, v in per[e].items():
            c[k][0] += v["tp"]; c[k][1] += v["fp"]; c[k][2] += v["fn"]
    return c


def micro(c):
    return prf(sum(v[0] for v in c.values()), sum(v[1] for v in c.values()), sum(v[2] for v in c.values()))


def macro_f1(c):
    xs = [prf(*v)["f1"] for v in c.values() if prf(*v)["f1"] is not None]
    return sum(xs) / len(xs)


def schema_block(recs, ids):
    parsed = [e for e in ids if recs[e]["status"] == "parsed"]
    kinds = Counter()
    for e in parsed:
        kinds.update(recs[e].get("schema_violation_counts") or {})
    return {"valid_json": len(parsed), "invalid_json": len(ids) - len(parsed), "fully_schema_compliant_records": sum(bool(recs[e].get("schema_compliant")) for e in parsed),
            "violations_total": sum(kinds.values()), "missing_field": kinds.get("missing_field", 0), "wrong_type": kinds.get("wrong_type", 0), "invalid_enum": kinds.get("enum_violation", 0),
            "unexpected_field": kinds.get("unexpected_field", 0), "violations_per_valid_record": round(sum(kinds.values()) / len(parsed), 2) if parsed else None,
            "mean_output_tokens": round(st.mean(recs[e]["completion_tokens"] for e in ids), 1), "mean_latency_s": round(st.mean(recs[e]["latency_seconds"] for e in ids), 1)}


new_c, old_c = totals(per_new, IDS), totals(per_old, IDS)
nb, ob = schema_block(man["records"], IDS), schema_block(p00, IDS)
mn, mo = micro(new_c), micro(old_c)
pred_ents = lambda c: sum(v[0] + v[1] for v in c.values())
cat = {k: {"new_f1": prf(*new_c[k])["f1"], "p00_f1": prf(*old_c[k])["f1"], "new": prf(*new_c[k]), "p00": prf(*old_c[k])} for k in CATEGORIES}
# paired bootstrap of micro-F1 difference over encounters
rng = random.Random(20260402)
diffs = []
for _ in range(2000):
    s = [rng.choice(IDS) for _ in IDS]
    diffs.append(micro(totals(per_new, s))["f1"] - micro(totals(per_old, s))["f1"])
diffs.sort()
ci = [round(diffs[49], 4), round(diffs[1949], 4)]
red = lambda a, b: None if not b else round(1 - a / b, 3)
rule = {
    "total_violations_reduction": red(nb["violations_total"], ob["violations_total"]), "need": ">= 0.30",
    "wrong_type_reduction": red(nb["wrong_type"], ob["wrong_type"]), "wrong_type_need": ">= 0.80",
    "valid_json_new_minus_p00": nb["valid_json"] - ob["valid_json"], "valid_json_need": ">= -2",
    "micro_f1_new_minus_p00": round(mn["f1"] - mo["f1"], 4), "micro_f1_need": ">= -0.005",
    "categories_losing_more_than_0.05_with_p00_f1_above_0.1": [k for k, v in cat.items() if (v["p00_f1"] or 0) > 0.1 and (v["p00_f1"] - (v["new_f1"] or 0)) > 0.05],
    "output_tokens_ratio_new_over_p00": round(nb["mean_output_tokens"] / ob["mean_output_tokens"], 3), "predicted_entities_ratio": round(pred_ents(new_c) / max(1, pred_ents(old_c)), 3),
    "collapse_definition": "pre-registered: collapse if mean output tokens < 0.70 x P00 or predicted entities < 0.70 x P00"}
rule["pass"] = {"total_violations": (rule["total_violations_reduction"] or 0) >= 0.30, "wrong_type": (rule["wrong_type_reduction"] or 0) >= 0.80, "valid_json": rule["valid_json_new_minus_p00"] >= -2,
                "micro_f1": rule["micro_f1_new_minus_p00"] >= -0.005, "category_loss": not rule["categories_losing_more_than_0.05_with_p00_f1_above_0.1"],
                "no_collapse": rule["output_tokens_ratio_new_over_p00"] >= 0.70 and rule["predicted_entities_ratio"] >= 0.70}
rule["decision"] = "KEEP" if all(rule["pass"].values()) else "REJECT"
write_json(out / "paired_comparison_vs_P00.json", {
    "run_id": run_id, "prompt_file": prompt_file, "prompt_sha256": sha256_file(S.PROMPT_PATH), "subset": subset, "n_ids": len(IDS), "ids": IDS,
    "model": man["model"], "evaluator": "evaluation/evaluation_runner.py (unmodified)", "p00_source": "EXP_003 run_manifest_dev100.json + per_encounter_results_dev100 (same ids, no new inference)",
    "schema_new": nb, "schema_p00": ob, "micro_new": mn, "micro_p00": mo, "macro_f1_new": macro_f1(new_c), "macro_f1_p00": macro_f1(old_c),
    "micro_f1_diff_bootstrap95_ci": ci, "category": cat, "keep_rule": rule})
print(json.dumps({"schema_new": nb, "schema_p00": ob, "micro_new": mn, "micro_p00": mo, "f1_diff_ci95": ci, "rule": rule}, indent=1))
