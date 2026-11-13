"""EXP_004 P02 variant (8 pre-registered criteria) of evaluate_run.py. Original docstring: evaluation of one finished run with the EXISTING evaluator (unmodified), plus a paired comparison with the P00 (EXP_003) outputs on the SAME ids
and the pre-registered P01 keep/reject rule. usage: evaluate_run.py <run_id> <prompt_file> <subset: prompt_dev|validation>
Labels are opened here only (after inference). No inference."""
import json
import random
import statistics as st
import sys
from collections import Counter

from common import EXP3, EXP4, SPLIT, S, sha256_file, use_run, write_json
from direct_inference_baseline.evaluation import evaluation_runner as ER
from direct_inference_baseline.evaluation.entity_matching import CATEGORIES, KEYS, entity_list, norm_text, prf

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
LOWREC = ["negative_findings", "medical_history.social_history", "review_of_systems", "physical_examination", "clinical_conditions", "clinical_assessment",
          "procedures_and_investigations", "clinical_actions", "follow_up"]
rec = lambda c, k: (prf(*c[k])["recall"] or 0.0)
rep_e2e = report["end_to_end"] if isinstance(report, dict) and "end_to_end" in report else json.loads((out / "evaluation_report.json").read_text(encoding="utf-8"))["end_to_end"]
unsup = rep_e2e["unsupported_claims"]["unsupported_claim_rate_of_predictions"]
npred = n_dup = 0
for eid in IDS:
    pf = S.PARSED_DIR / run_id / f"encounter_{eid}.json"
    if not pf.exists():
        continue
    pr = json.loads(pf.read_text(encoding="utf-8"))
    for c in CATEGORIES:
        ks = [norm_text(KEYS[c](x)) for x in entity_list(pr, c) if KEYS[c](x)]
        npred += len(ks); n_dup += len(ks) - len(set(ks))
dup_rate = n_dup / max(1, npred)
non_stop = sum(1 for e in IDS if man["records"][e].get("finish_reason") != "stop")
maxtok = max(man["records"][e]["completion_tokens"] for e in IDS)
gains = {k: round(rec(new_c, k) - rec(old_c, k), 4) for k in LOWREC}
rule = {
    "1_micro_recall": mn["recall"], "1_need": ">= 0.050",
    "2_micro_f1_diff": round(mn["f1"] - mo["f1"], 4), "2_ci95": ci, "2_need": "diff >= +0.030 and CI lower bound > 0",
    "3_micro_precision": mn["precision"], "3_need": ">= 0.187",
    "4_valid_json": nb["valid_json"], "4_non_stop_finish": non_stop, "4_need": "valid >= 46 and non_stop <= 2",
    "5_categories_losing_more_than_0.05_with_p00_f1_above_0.1": [k for k, v in cat.items() if (v["p00_f1"] or 0) > 0.1 and (v["p00_f1"] - (v["new_f1"] or 0)) > 0.05],
    "6_low_recall_category_recall_gains": gains, "6_n_gaining_ge_0.03": sum(g >= 0.03 for g in gains.values()), "6_need": ">= 3 of 9",
    "7_unsupported_rate": round(unsup, 4), "7_duplicate_rate": round(dup_rate, 4), "7_duplicates": n_dup, "7_predicted_items": npred, "7_need": "unsupported <= 0.15 and duplicates <= 0.05",
    "8_mean_output_tokens": nb["mean_output_tokens"], "8_max_output_tokens": maxtok, "8_need": "mean <= 3000 and max < 6144"}
rule["pass"] = {"1_recall": rule["1_micro_recall"] >= 0.050, "2_f1": rule["2_micro_f1_diff"] >= 0.030 and ci[0] > 0, "3_precision": rule["3_micro_precision"] >= 0.187,
                "4_valid_json_and_stop": nb["valid_json"] >= 46 and non_stop <= 2, "5_category_loss": not rule["5_categories_losing_more_than_0.05_with_p00_f1_above_0.1"],
                "6_breadth": rule["6_n_gaining_ge_0.03"] >= 3, "7_unsupported_duplicates": unsup <= 0.15 and dup_rate <= 0.05, "8_length": nb["mean_output_tokens"] <= 3000 and maxtok < 6144}
rule["decision"] = "KEEP" if all(rule["pass"].values()) else "REJECT"
write_json(out / "paired_comparison_vs_P00.json", {
    "run_id": run_id, "prompt_file": prompt_file, "prompt_sha256": sha256_file(S.PROMPT_PATH), "subset": subset, "n_ids": len(IDS), "ids": IDS,
    "model": man["model"], "evaluator": "evaluation/evaluation_runner.py (unmodified)", "p00_source": "EXP_003 run_manifest_dev100.json + per_encounter_results_dev100 (same ids, no new inference)",
    "schema_new": nb, "schema_p00": ob, "micro_new": mn, "micro_p00": mo, "macro_f1_new": macro_f1(new_c), "macro_f1_p00": macro_f1(old_c),
    "micro_f1_diff_bootstrap95_ci": ci, "category": cat, "keep_rule": rule})
print(json.dumps({"schema_new": nb, "schema_p00": ob, "micro_new": mn, "micro_p00": mo, "f1_diff_ci95": ci, "rule": rule}, indent=1))
