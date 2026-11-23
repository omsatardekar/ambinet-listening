"""Command line helper for controlled single-encounter tests (no web server, no Blob access).

  python -m clinical_extraction.cli run --compact <compact.json>     run ONE extraction through the same service code (needs EXTRACTION_PYTHON)
  python -m clinical_extraction.cli check                            verify prompt hash, model files, weights hash and imports; loads no model
It never starts a batch.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from .config import ROOT, extraction_python
from .job_store import JobStore
from .service import WORKER, ExtractionService


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--compact", required=True)
    sub.add_parser("check")
    a = ap.parse_args()
    py = extraction_python()
    if py is None or not py.exists():
        print("No OpenVINO environment found. Run: python -m clinical_extraction.setup_local_model   (or set EXTRACTION_PYTHON)")
        return 2
    if a.cmd == "check":
        out = JobStore().root / "check"
        out.mkdir(parents=True, exist_ok=True)
        dummy = out / "dummy_input.json"
        dummy.write_text("{}", encoding="utf-8")
        code = subprocess.call([str(py), "-B", "-s", str(WORKER), "--input", str(dummy), "--out", str(out / "jobs" / "x"), "--check"])
        print((out / "jobs" / "x" / "result.json").read_text(encoding="utf-8") if (out / "jobs" / "x" / "result.json").exists() else "no result")
        return code
    compact = json.loads(Path(a.compact).read_text(encoding="utf-8"))
    service = ExtractionService(source=lambda _ref: (compact, {"kind": "local_file", "blob_name": None}))
    job = service.store.create(str(compact.get("encounter_id", "local")), None)
    service.run_job(job["job_id"])
    final = service.store.load(job["job_id"])
    print(json.dumps({k: final.get(k) for k in ("job_id", "status", "stage_message", "warnings", "error")}, indent=1))
    print("job folder:", service.store.dir(job["job_id"]))
    return 0 if final["status"] in ("completed", "completed_with_warnings") else 1


if __name__ == "__main__":
    sys.exit(main())
