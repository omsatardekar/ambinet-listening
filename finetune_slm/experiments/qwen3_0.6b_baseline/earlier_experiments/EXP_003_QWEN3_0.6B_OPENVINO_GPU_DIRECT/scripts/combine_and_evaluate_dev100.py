"""Builds the combined 100-encounter development run `exp_003_dev_100` from the two completed runs (5 smoke + 95 remaining) WITHOUT modifying either:
files are copied (sha256-verified) into the new run folders and the manifests are merged; then the EXISTING evaluator is run on the combined run.
Only this script (evaluation stage) reads labels."""
import json
import shutil
import statistics as st
import sys
from collections import Counter

from common import EXP3, SMOKE_IDS, S, sha256_file, write_json
from direct_inference_baseline.evaluation import evaluation_runner as ER
from direct_inference_baseline.evaluation.dataset_split import load_split

SRC = {"exp_003_dev_smoke_5": SMOKE_IDS, "exp_003_dev_remaining_95": None}
RUN = "exp_003_dev_100"
dev = load_split("development")
mans = {k: json.loads((S.REPORT_DIR / k / "run_manifest.json").read_text(encoding="utf-8")) for k in SRC}
a, b = mans["exp_003_dev_smoke_5"], mans["exp_003_dev_remaining_95"]
for k in ("prompt_sha256", "max_new_tokens", "dataset", "split", "split_seed"):
    assert a[k] == b[k], f"run manifests differ in {k}"
for k in ("provider", "model_id", "model_revision_commit", "device", "runtime", "openvino", "openvino_genai", "generation", "converted_model_dir"):
    assert a["model"].get(k) == b["model"].get(k), f"model description differs in {k}"
assert not (set(a["records"]) & set(b["records"])), "runs overlap"
assert set(a["records"]) | set(b["records"]) == set(dev) and len(dev) == 100, "the two runs must cover exactly the 100 development ids"
assert not (set(dev) & set(load_split("test")))

# ---- copy (never move) the artifacts of both runs into the combined run, verifying every hash
copied = 0
for sub in ("raw_predictions", "parsed_predictions", "failed_predictions"):
    dst = EXP3 / sub / RUN
    dst.mkdir(parents=True, exist_ok=True)
    for k in SRC:
        for f in sorted((EXP3 / sub / k).glob("*.json")):
            shutil.copyfile(f, dst / f.name)
            assert sha256_file(f) == sha256_file(dst / f.name)
            copied += 1
records = {i: (a["records"].get(i) or b["records"][i]) for i in dev}
man = dict(a)
man.update(experiment_id=RUN, encounter_ids=dev, records=records, started_utc=a["started_utc"], last_update_utc=b.get("last_update_utc"),
           stage="3 - direct inference baseline, EXP_003 combined 100-encounter development run (no fine-tuning, no prompt optimisation, no RAG)",
           components={k: {"run_manifest": f"evaluation/{k}/run_manifest.json", "run_manifest_sha256": sha256_file(S.REPORT_DIR / k / "run_manifest.json"),
                           "n_encounters": len(m["records"]), "started_utc": m["started_utc"]} for k, m in mans.items()})
rep_dir = S.REPORT_DIR / RUN
rep_dir.mkdir(parents=True, exist_ok=True)
write_json(rep_dir / "run_manifest.json", man)
write_json(EXP3 / "run_manifest_dev100.json", man)

report = ER.evaluate_experiment(RUN)

# ---- per-encounter detail (existing score_encounter) for all 100
out = EXP3 / "per_encounter_results_dev100"
out.mkdir(exist_ok=True)
for eid, rec in records.items():
    gold = ER.load_gold(eid)
    tr = json.loads((S.INPUT_DIR / f"encounter_{eid}.json").read_text(encoding="utf-8"))
    pred = json.loads((S.PARSED_DIR / RUN / f"encounter_{eid}.json").read_text(encoding="utf-8")) if rec["status"] == "parsed" else None
    write_json(out / f"encounter_{eid}.json", {"encounter_id": eid, "status": rec["status"], "failure_type": rec.get("failure_type"), "run_record": {
        k: rec.get(k) for k in ("finish_reason", "prompt_tokens", "completion_tokens", "latency_seconds", "parse_status", "schema_compliant", "schema_violation_counts")},
        "scores": ER.score_encounter(gold, pred, tr)})

# ---- failure report: failed / truncated / malformed / empty recorded separately
ft = Counter(r.get("failure_type") for r in records.values() if r["status"] != "parsed")
write_json(EXP3 / "failure_report_dev100.json", {
    "run": RUN, "attempted": len(records), "parsed_valid_json": sum(r["status"] == "parsed" for r in records.values()),
    "failed_total": sum(r["status"] != "parsed" for r in records.values()),
    "truncated_hit_token_limit": [e for e, r in records.items() if r.get("failure_type") == "truncated"],
    "malformed_invalid_json": [e for e, r in records.items() if r.get("failure_type") == "invalid_json"],
    "empty": [e for e, r in records.items() if r.get("failure_type") == "empty"],
    "not_a_json_object": [e for e, r in records.items() if r.get("failure_type") == "not_object"],
    "inference_errors": {e: r.get("error") for e, r in records.items() if r.get("failure_type") == "inference_error"},
    "failure_type_counts": dict(ft), "finish_reasons": dict(Counter(r.get("finish_reason") for r in records.values())),
    "repetition_flagged": [e for e, r in records.items() if any("repetition" in n for n in r.get("parse_notes", []))],
    "schema_non_compliant_among_valid_json": [e for e, r in records.items() if r.get("schema_compliant") is False],
    "schema_compliant": [e for e, r in records.items() if r.get("schema_compliant") is True],
    "schema_violation_totals": dict(sum((Counter(r["schema_violation_counts"]) for r in records.values() if r["status"] == "parsed"), Counter()))})

# ---- extra performance statistics from the two per-call performance logs
calls = json.loads((EXP3 / "logs" / "performance_per_encounter.json").read_text(encoding="utf-8"))["per_call_in_order"] + \
    json.loads((EXP3 / "logs" / "performance_remaining_95.json").read_text(encoding="utf-8"))["per_call_in_order"]


def stats(key):
    xs = sorted(c[key] for c in calls if c.get(key) is not None)
    return {"n": len(xs), "mean": round(st.mean(xs), 3), "median": round(st.median(xs), 3), "min": xs[0], "max": xs[-1], "p95": xs[int(0.95 * (len(xs) - 1))]}


write_json(EXP3 / "evaluation" / "dev100_performance_details.json", {
    "calls": len(calls), **{k: stats(k) for k in ("load_compile_seconds", "first_token_latency_s(prefill+1st token)", "prefill_tokens_per_second", "decode_tokens_per_second",
                                                  "generation_wall_seconds", "input_tokens", "output_tokens", "tokens_per_second_overall", "rss_mb_after")},
    "peak_working_set_mb_max_over_run": max(c["peak_working_set_mb_process_so_far"] for c in calls),
    "total_generation_hours": round(sum(c["generation_wall_seconds"] for c in calls) / 3600, 3), "total_output_tokens": sum(c["output_tokens"] for c in calls),
    "note": "peak working set is the max over the process lifetime (two processes: smoke run and remaining-95 run)"})
fz = S.verify_frozen_dataset()
write_json(EXP3 / "evaluation" / "frozen_dataset_verification_after_dev100.json", fz)
print(json.dumps(report["headline"], indent=1))
print("copied files:", copied, "| frozen verified:", fz["verified"], fz["files_checked"])
sys.exit(0 if fz["verified"] else 1)
