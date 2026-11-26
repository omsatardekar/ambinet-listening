"""INTERIM evaluation of the completed predictions of the still-running exp_003_dev_remaining_95 (read-only with respect to the live run).
Only encounters whose manifest record is final AND whose raw (and parsed, if status=parsed) files exist and are fully valid JSON are taken. Those files are COPIED
into a timestamped snapshot folder under evaluation/ and the EXISTING evaluator is run on the snapshot (S.*_DIR redirected). The live run's folders are never written."""
import json
import shutil
import sys
import time
from datetime import datetime, timezone

from common import EXP3, S, sha256_file, write_json
from direct_inference_baseline.evaluation import evaluation_runner as ER

TS = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
SNAP = EXP3 / "evaluation" / f"interim_{TS}"
RUN = "exp_003_dev_remaining_95_interim"
LIVE = "exp_003_dev_remaining_95"


def load_json(p):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


man = None
for _ in range(5):
    man = load_json(S.REPORT_DIR / LIVE / "run_manifest.json")
    if man:
        break
    time.sleep(1)
assert man, "could not read the live manifest"
included, skipped = {}, {}
for eid, rec in man["records"].items():
    if rec.get("status") not in ("parsed", "failed"):
        skipped[eid] = f"manifest status {rec.get('status')}"
        continue
    raw = load_json(EXP3 / "raw_predictions" / LIVE / f"encounter_{eid}.json")
    if raw is None:
        skipped[eid] = "raw file missing or not yet fully written"
        continue
    if rec["status"] == "parsed" and load_json(EXP3 / "parsed_predictions" / LIVE / f"encounter_{eid}.json") is None:
        skipped[eid] = "parsed file missing or not yet fully written"
        continue
    included[eid] = rec
for sub in ("raw_predictions", "parsed_predictions", "failed_predictions"):
    (SNAP / sub / RUN).mkdir(parents=True, exist_ok=True)
    for eid in included:
        f = EXP3 / sub / LIVE / f"encounter_{eid}.json"
        if f.exists():
            shutil.copyfile(f, SNAP / sub / RUN / f.name)
            assert sha256_file(f) == sha256_file(SNAP / sub / RUN / f.name)
snap_man = dict(man)
snap_man.update(experiment_id=RUN, encounter_ids=list(included), records=included, interim=True,
                interim_note="INTERIM snapshot of a still-running experiment; NOT the final 100-record development evaluation")
(SNAP / "evaluation" / RUN).mkdir(parents=True, exist_ok=True)
write_json(SNAP / "evaluation" / RUN / "run_manifest.json", snap_man)
# redirect the existing evaluator's directories to the snapshot (in-process only)
S.RAW_DIR, S.PARSED_DIR, S.FAILED_DIR, S.REPORT_DIR = (SNAP / n for n in ("raw_predictions", "parsed_predictions", "failed_predictions", "evaluation"))
rep = ER.evaluate_experiment(RUN)
write_json(SNAP / "interim_selection.json", {"timestamp_utc": TS, "included_count": len(included), "included": sorted(included),
                                              "skipped_not_complete": skipped, "live_manifest_records_seen": len(man["records"])})
print(SNAP)
print(len(included), "included;", skipped)
