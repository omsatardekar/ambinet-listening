"""EXP_004 P03 variant (E1-E6, G1-G5 pre-registered criteria) of evaluate_run.py. Original docstring: evaluation of one finished run with the EXISTING evaluator (unmodified), plus a paired comparison with the P00 (EXP_003) outputs on the SAME ids
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
import subprocess
diag_py = EXP4 / "experiments" / "evidence_diagnostics.py"
subprocess.run([sys.executable, "-B", "-s", str(diag_py), run_id, str(S.PARSED_DIR / run_id)], check=True, cwd=str(EXP4 / "logs" / "gpu_compiler"), stdout=subprocess.DEVNULL)
D = json.loads((EXP4 / "evaluation" / f"evidence_diagnostics_{run_id}.json").read_text(encoding="utf-8"))[0]
Dp = [d for d in json.loads((EXP4 / "evaluation" / "evidence_diagnostics_P00_P01_P02.json").read_text(encoding="utf-8")) if d["label"] == "P00"][0]
g, gp, sup, supp = D["evaluator"]["grounding"], Dp["evaluator"]["grounding"], D["supplementary"], Dp["supplementary"]
spk, spkp = D["evaluator"]["speaker_attribution"], Dp["evaluator"]["speaker_attribution"]
unsup = D["evaluator"]["unsupported_claims"]["unsupported_claim_rate_of_predictions"]
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
tot = lambda gg: gg["total"]
ev_valid_rate = (tot(g) - g["unsupported"]) / max(1, tot(g))
gl_rate = (g["grounded_strict"] + g["grounded_lenient"]) / max(1, tot(g))
ent_ratio = round(pred_ents(new_c) / max(1, pred_ents(old_c)), 3)
rule = {
    "E1_entities_citing_valid_evidence": round(ev_valid_rate, 4), "E1_p00": round((tot(gp) - gp["unsupported"]) / max(1, tot(gp)), 4), "E1_need": ">= 0.50",
    "E2_strict_plus_lenient_grounded": round(gl_rate, 4), "E2_strict_only": round(g["grounded_strict"] / max(1, tot(g)), 4), "E2_partial": g["partially_supported"], "E2_p00": round((gp["grounded_strict"] + gp["grounded_lenient"]) / max(1, tot(gp)), 4), "E2_need": ">= 0.10",
    "E3_valid_evidence_records": sup["ev_speaker_correct_rate"], "E3_p00": supp["ev_speaker_correct_rate"], "E3_need": ">= 0.75",
    "E4_timestamp_match_pm1s": sup["ev_timestamp_match_rate"], "E4_exact_floor_match": sup["ev_timestamp_exact_floor_rate"], "E4_p00": supp["ev_timestamp_match_rate"], "E4_need": ">= 0.70",
    "E5_supports_nonempty": sup["ev_supports_nonempty_rate"], "E5_supports_reciprocal": sup["supports_refs_reciprocal_rate"], "E5_supports_exist": sup["supports_refs_exist_rate"], "E5_need": "nonempty >= 0.80 and reciprocal >= 0.70",
    "E6_mean_evidence_records_per_encounter": sup["ev_records_mean_per_encounter"], "E6_p00": supp["ev_records_mean_per_encounter"], "E6_need": ">= 5",
    "G1_micro_f1": mn["f1"], "G1_micro_precision": mn["precision"], "G1_need": "F1 >= 0.042 and precision >= 0.187",
    "G2_predicted_entities": pred_ents(new_c), "G2_p00": pred_ents(old_c), "G2_ratio": ent_ratio, "G2_need": "ratio >= 0.70",
    "G3_valid_json": nb["valid_json"], "G3_non_stop_finish": non_stop, "G3_max_output_tokens": maxtok, "G3_mean_output_tokens": nb["mean_output_tokens"], "G3_need": "valid >= 46, non_stop <= 2, max < 6144, mean <= 3500",
    "G4_unsupported_claim_rate": round(unsup, 4), "G4_duplicate_rate": round(dup_rate, 4), "G4_need": "unsupported <= 0.10 and duplicates <= 0.05",
    "G5_speaker_attribution": spk["accuracy"], "G5_evaluated": spk["denominator_evaluated"], "G5_p00": spkp["accuracy"], "G5_p00_evaluated": spkp["denominator_evaluated"], "G5_need": ">= 0.413"}
rule["pass"] = {"E1": ev_valid_rate >= 0.50, "E2": gl_rate >= 0.10, "E3": (sup["ev_speaker_correct_rate"] or 0) >= 0.75, "E4": (sup["ev_timestamp_match_rate"] or 0) >= 0.70,
                "E5": (sup["ev_supports_nonempty_rate"] or 0) >= 0.80 and (sup["supports_refs_reciprocal_rate"] or 0) >= 0.70, "E6": (sup["ev_records_mean_per_encounter"] or 0) >= 5,
                "G1": mn["f1"] >= 0.042 and mn["precision"] >= 0.187, "G2": ent_ratio >= 0.70,
                "G3": nb["valid_json"] >= 46 and non_stop <= 2 and maxtok < 6144 and nb["mean_output_tokens"] <= 3500, "G4": unsup <= 0.10 and dup_rate <= 0.05, "G5": (spk["accuracy"] or 0) >= 0.413}
rule["decision"] = "KEEP" if all(rule["pass"].values()) else "REJECT"
write_json(out / "paired_comparison_vs_P00.json", {
    "run_id": run_id, "prompt_file": prompt_file, "prompt_sha256": sha256_file(S.PROMPT_PATH), "subset": subset, "n_ids": len(IDS), "ids": IDS,
    "model": man["model"], "evaluator": "evaluation/evaluation_runner.py (unmodified)", "p00_source": "EXP_003 run_manifest_dev100.json + per_encounter_results_dev100 (same ids, no new inference)",
    "schema_new": nb, "schema_p00": ob, "micro_new": mn, "micro_p00": mo, "macro_f1_new": macro_f1(new_c), "macro_f1_p00": macro_f1(old_c),
    "micro_f1_diff_bootstrap95_ci": ci, "category": cat, "keep_rule": rule})
print(json.dumps({"schema_new": nb, "schema_p00": ob, "micro_new": mn, "micro_p00": mo, "f1_diff_ci95": ci, "rule": rule}, indent=1))
