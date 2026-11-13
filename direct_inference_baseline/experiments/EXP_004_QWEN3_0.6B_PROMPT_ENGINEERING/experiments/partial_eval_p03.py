"""EXP_004 PARTIAL evaluation of the stopped P03 run (user stopped inference). Evaluates ONLY the attempted records, pairs them with P00 on the exact same ids.
Writes only to evaluation/P03_PARTIAL/. Existing evaluator used unmodified. Nothing here is a final P03 result."""
import json
import os
import random
import statistics as st
import subprocess
import sys
from collections import Counter

from common import EXP3, EXP4, SPLIT, S, sha256_file, use_run, write_json
from direct_inference_baseline.evaluation import evaluation_runner as ER
from direct_inference_baseline.evaluation.entity_matching import CATEGORIES, KEYS, entity_list, norm_text, prf

RUN = "P03_evidence_grounded_dev50"
use_run(RUN, "P03_evidence_grounded.txt")
live_manifest = EXP4 / "evaluation" / RUN / "run_manifest.json"
man = json.loads(live_manifest.read_text(encoding="utf-8"))
ALL50 = SPLIT["prompt_dev_ids"]
attempted = sorted(man["records"])
raw_ids = sorted(p.stem.replace("encounter_", "") for p in (EXP4 / "outputs" / RUN / "raw_predictions" / RUN).glob("encounter_*.json"))
parsed_ids = sorted(p.stem.replace("encounter_", "") for p in (S.PARSED_DIR / RUN).glob("encounter_*.json"))
failed_ids = sorted(p.stem.replace("encounter_", "") for p in (S.FAILED_DIR / RUN).glob("encounter_*.json"))
log_ok = [l.split()[3] for l in (EXP4 / "outputs" / RUN / "inference.log").read_text(encoding="utf-8").splitlines() if " parsed ok " in l]
log_fail = [l.split()[3] for l in (EXP4 / "outputs" / RUN / "inference.log").read_text(encoding="utf-8").splitlines() if " failed " in l]
assert attempted == raw_ids == sorted(parsed_ids + failed_ids) and sorted(log_ok) == parsed_ids and sorted(log_fail) == failed_ids, "manifest, raw files, parsed/failed dirs and log disagree"
assert set(attempted) <= set(ALL50)
unprocessed = [i for i in ALL50 if i not in attempted]
IDS = [i for i in ALL50 if i in attempted]
integrity = {"planned": 50, "attempted": len(IDS), "parsed": len(parsed_ids), "failed_invalid_json": len(failed_ids), "not_attempted": len(unprocessed), "failed_ids": failed_ids, "unprocessed_ids": unprocessed,
             "verified_against": "run_manifest.json, raw_predictions, parsed_predictions, failed_predictions, inference.log (all consistent)",
             "prompt_sha256_in_log_line": sha256_file(S.PROMPT_PATH)}

# evaluator on the attempted subset (own report folder; live run folders untouched)
PART = EXP4 / "evaluation" / "P03_PARTIAL"
(PART / RUN).mkdir(parents=True, exist_ok=True)
(PART / RUN / "run_manifest.json").write_text(live_manifest.read_text(encoding="utf-8"), encoding="utf-8")
S.REPORT_DIR = PART
report = ER.evaluate_experiment(RUN)

p00man = json.loads((EXP3 / "run_manifest_dev100.json").read_text(encoding="utf-8"))["records"]
P00_PARSED = EXP3 / "parsed_predictions" / "exp_003_dev_100"
per_new, per_old = {}, {}
for eid in IDS:
    gold = ER.load_gold(eid)
    tr = json.loads((S.INPUT_DIR / f"encounter_{eid}.json").read_text(encoding="utf-8"))
    pn = json.loads((S.PARSED_DIR / RUN / f"encounter_{eid}.json").read_text(encoding="utf-8")) if man["records"][eid]["status"] == "parsed" else None
    per_new[eid] = ER.score_encounter(gold, pn, tr)["strict"]
    per_old[eid] = json.loads((EXP3 / "per_encounter_results_dev100" / f"encounter_{eid}.json").read_text(encoding="utf-8"))["scores"]["strict"]


def totals(per, ids):
    c = {k: [0, 0, 0] for k in CATEGORIES}
    for e in ids:
        for k, v in per[e].items():
            c[k][0] += v["tp"]; c[k][1] += v["fp"]; c[k][2] += v["fn"]
    return c


micro = lambda c: prf(sum(v[0] for v in c.values()), sum(v[1] for v in c.values()), sum(v[2] for v in c.values()))
macro = lambda c: sum(x for x in (prf(*v)["f1"] for v in c.values()) if x is not None) / len(c)
nc, oc = totals(per_new, IDS), totals(per_old, IDS)
rng = random.Random(20260402); diffs = sorted(micro(totals(per_new, s))["f1"] - micro(totals(per_old, s))["f1"] for s in ([rng.choice(IDS) for _ in IDS] for _ in range(2000)))


def schema(recs, ids):
    pr = [e for e in ids if recs[e]["status"] == "parsed"]
    k = Counter()
    for e in pr:
        k.update(recs[e].get("schema_violation_counts") or {})
    ke = sum(recs[e].get("keys_expected", 0) for e in pr); kp = sum(recs[e].get("keys_present", 0) for e in pr)
    return {"valid_json": len(pr), "invalid_json": len(ids) - len(pr), "valid_json_pct": round(100 * len(pr) / len(ids), 1), "fully_schema_compliant_records": sum(bool(recs[e].get("schema_compliant")) for e in pr),
            "violations_total": sum(k.values()), "missing_field": k.get("missing_field", 0), "wrong_type": k.get("wrong_type", 0), "invalid_enum": k.get("enum_violation", 0), "unexpected_field": k.get("unexpected_field", 0),
            "required_field_completeness_pct": round(100 * kp / ke, 1) if ke else None,
            "mean_output_tokens": round(st.mean(recs[e]["completion_tokens"] for e in ids), 1), "mean_latency_s": round(st.mean(recs[e]["latency_seconds"] for e in ids), 1),
            "tokens_per_second_mean": round(st.mean(recs[e]["completion_tokens"] / recs[e]["latency_seconds"] for e in ids), 2)}


def run_diag(label, pdir):
    env = dict(os.environ, EXP4_IDS_JSON=json.dumps(IDS), PYTHONIOENCODING="utf-8")
    subprocess.run([sys.executable, "-B", "-s", str(EXP4 / "experiments" / "evidence_diagnostics.py"), label, str(pdir)], check=True, env=env, cwd=str(EXP4 / "logs" / "gpu_compiler"), stdout=subprocess.DEVNULL)
    return json.loads((EXP4 / "evaluation" / f"evidence_diagnostics_{label}.json").read_text(encoding="utf-8"))[0]


Dn, Do = run_diag("P03_PARTIAL35", S.PARSED_DIR / RUN), run_diag("P00_PARTIAL35", P00_PARSED)


def dups(pdir, ids):
    n = d = 0
    for e in ids:
        f = pdir / f"encounter_{e}.json"
        if not f.exists():
            continue
        pr = json.loads(f.read_text(encoding="utf-8"))
        for c in CATEGORIES:
            ks = [norm_text(KEYS[c](x)) for x in entity_list(pr, c) if KEYS[c](x)]
            n += len(ks); d += len(ks) - len(set(ks))
    return {"predicted_items": n, "duplicate_items": d, "duplicate_rate": round(d / max(1, n), 4)}


cat = {k: {"p00": prf(*oc[k]), "p03": prf(*nc[k])} for k in CATEGORIES}
out = {"label": "PARTIAL P03 DEVELOPMENT RESULTS - NOT THE FINAL P03 EXPERIMENT (inference stopped by user)", "integrity": integrity, "prompt_sha256": sha256_file(S.PROMPT_PATH),
       "evaluated_ids": IDS, "extraction_p03": micro(nc), "extraction_p00": micro(oc), "macro_f1_p03": macro(nc), "macro_f1_p00": macro(oc), "micro_f1_diff_bootstrap95": [round(diffs[49], 4), round(diffs[1949], 4)],
       "schema_p03": schema(man["records"], IDS), "schema_p00": schema(p00man, IDS), "category": cat, "diagnostics_p03": Dn, "diagnostics_p00": Do,
       "duplicates_p03": dups(S.PARSED_DIR / RUN, IDS), "duplicates_p00": dups(P00_PARSED, IDS),
       "tp_fp_fn_p03": [sum(v[i] for v in nc.values()) for i in range(3)], "tp_fp_fn_p00": [sum(v[i] for v in oc.values()) for i in range(3)]}
write_json(PART / "partial_evaluation.json", out)
brief = {k: out[k] for k in ("integrity", "extraction_p03", "extraction_p00", "macro_f1_p03", "macro_f1_p00", "micro_f1_diff_bootstrap95", "schema_p03", "schema_p00", "duplicates_p03", "duplicates_p00", "tp_fp_fn_p03", "tp_fp_fn_p00")}
print(json.dumps(brief, indent=1))
for lab, D in (("P03", Dn), ("P00", Do)):
    print(lab, json.dumps({"grounding": D["evaluator"]["grounding"], "speaker": {k: D["evaluator"]["speaker_attribution"][k] for k in ("accuracy", "denominator_evaluated")},
                           "unsupported": D["evaluator"]["unsupported_claims"]["unsupported_claim_rate_of_predictions"], "supp": D["supplementary"]}))
