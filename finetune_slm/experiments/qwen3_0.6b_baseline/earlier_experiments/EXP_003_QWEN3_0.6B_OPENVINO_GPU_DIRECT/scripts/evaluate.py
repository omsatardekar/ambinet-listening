"""EXP_003 evaluation: the EXISTING evaluator (evaluation_runner.evaluate_experiment / score_encounter), unmodified, run after inference is complete.
Only here are labels read."""
import json
import sys
from collections import Counter

from common import EXP3, EXPERIMENT_ID, S, sha256_file, write_json
from direct_inference_baseline.evaluation import evaluation_runner as ER

report = ER.evaluate_experiment(EXPERIMENT_ID)              # writes evaluation/<exp>/{evaluation_report.json,.md, per_encounter_results.jsonl, confusion_matrices.json}
rep_dir = S.REPORT_DIR / EXPERIMENT_ID
man = json.loads((rep_dir / "run_manifest.json").read_text(encoding="utf-8"))
(EXP3 / "run_manifest.json").write_text((rep_dir / "run_manifest.json").read_text(encoding="utf-8"), encoding="utf-8")   # top-level copy

# full per-encounter scoring detail from the same evaluator functions
(EXP3 / "per_encounter_results").mkdir(exist_ok=True)
for eid, rec in man["records"].items():
    gold = ER.load_gold(eid)
    tr = json.loads((S.INPUT_DIR / f"encounter_{eid}.json").read_text(encoding="utf-8"))
    pred = json.loads((S.PARSED_DIR / EXPERIMENT_ID / f"encounter_{eid}.json").read_text(encoding="utf-8")) if rec["status"] == "parsed" else None
    detail = ER.score_encounter(gold, pred, tr)
    write_json(EXP3 / "per_encounter_results" / f"encounter_{eid}.json", {"encounter_id": eid, "status": rec["status"], "run_record": {
        k: rec.get(k) for k in ("finish_reason", "prompt_tokens", "completion_tokens", "latency_seconds", "parse_status", "schema_compliant", "schema_violation_counts")},
        "scores": detail})

recs = man["records"]
write_json(EXP3 / "failure_report.json", {
    "experiment_id": EXPERIMENT_ID, "attempted": len(recs), "failed": [e for e, r in recs.items() if r["status"] != "parsed"],
    "failure_types": dict(Counter(r.get("failure_type") for r in recs.values() if r["status"] != "parsed")),
    "finish_reasons": dict(Counter(r.get("finish_reason") for r in recs.values())), "json_valid": sum(r.get("parse_status") == "ok" for r in recs.values()),
    "truncated": sum(r.get("parse_status") == "truncated" for r in recs.values()),
    "malformed_or_empty": sum(r.get("parse_status") in ("invalid_json", "empty", "not_object") for r in recs.values()),
    "inference_errors": {e: r.get("error") for e, r in recs.items() if r.get("failure_type") == "inference_error"},
    "schema_non_compliant": [e for e, r in recs.items() if r.get("schema_compliant") is False],
    "schema_violation_counts": {e: r.get("schema_violation_counts") for e, r in recs.items()}})

fz = S.verify_frozen_dataset()                              # full integrity check incl. labels, AFTER inference
write_json(EXP3 / "evaluation" / "frozen_dataset_verification_after_run.json", fz)
print(json.dumps(report["headline"], indent=1))
print("frozen dataset verified after run:", fz["verified"], fz["files_checked"])
sys.exit(0 if fz["verified"] else 1)
