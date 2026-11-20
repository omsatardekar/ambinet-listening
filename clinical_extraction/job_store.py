"""Persistent extraction jobs: one folder per job, atomic JSON writes, so a restart does not erase history.

Layout (extraction_data/jobs/<job_id>/):
  job.json                 state, stage, timestamps, events, warnings, error
  input_compact.json       the exact compact transcript sent to the model (copy; the Blob original is never touched)
  extraction_raw.json      the parsed P02 output exactly as the frozen parser returned it
  model_response_raw.txt   the raw model text
  metadata.json            execution metadata (prompt hash, model, device, tokens, finish reason, parse/schema status, ...)
  evidence.json            derived evidence resolution (kept separate from the raw extraction)
Transcript and extraction text are never written to logs by this module.
"""
from __future__ import annotations

import json
import os
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import DATA_DIR, TERMINAL_STATES


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json_atomic(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".{uuid.uuid4().hex[:6]}.tmp")
    tmp.write_text(json.dumps(obj, indent=1, ensure_ascii=False), encoding="utf-8")
    # On Windows os.replace raises PermissionError while another thread/process (a status poll, the event stream, an antivirus scan) has the target
    # open. That is transient: retry briefly instead of failing the whole extraction.
    delay = 0.02
    for attempt in range(40):
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            if attempt == 39:
                try:
                    tmp.unlink()
                except OSError:
                    pass
                raise
            time.sleep(delay)
            delay = min(delay * 1.5, 0.25)


class JobStore:
    def __init__(self, root: Path | None = None) -> None:
        self.root = Path(root) if root else DATA_DIR
        self.jobs_dir = self.root / "jobs"
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        gi = self.root / ".gitignore"
        if not gi.exists():
            gi.write_text("*\n!.gitignore\n", encoding="utf-8")        # patient-related output must never be committed
        self._lock = threading.RLock()

    def dir(self, job_id: str) -> Path:
        if not job_id.isalnum():
            raise KeyError(job_id)
        return self.jobs_dir / job_id

    def create(self, encounter_ref: str, run_id: str | None) -> dict:
        job_id = uuid.uuid4().hex
        job = {"job_id": job_id, "encounter_ref": encounter_ref, "run_id": run_id, "encounter_id": None, "status": "queued", "stage_message": "Waiting in the extraction queue",
               "created_at": now(), "started_at": None, "finished_at": None, "warnings": [], "error": None, "events": []}
        self._event(job, "queued", "Extraction queued")
        self.save(job)
        return job

    def save(self, job: dict) -> None:
        with self._lock:
            write_json_atomic(self.dir(job["job_id"]) / "job.json", job)

    def load(self, job_id: str) -> dict | None:
        try:
            path = self.dir(job_id) / "job.json"
        except KeyError:
            return None
        with self._lock:                                         # readers and the writer of job.json never overlap inside this process
            if not path.exists():
                return None
            return json.loads(path.read_text(encoding="utf-8"))

    def set_state(self, job: dict, status: str, message: str, **extra: Any) -> None:
        with self._lock:
            job["status"] = status
            job["stage_message"] = message
            job.update(extra)
            if status == "preparing_transcript" and not job["started_at"]:
                job["started_at"] = now()
            if status in TERMINAL_STATES:
                job["finished_at"] = now()
            self._event(job, status, message)
            self.save(job)

    @staticmethod
    def _event(job: dict, status: str, message: str) -> None:
        job["events"].append({"sequence": len(job["events"]) + 1, "status": status, "message": message, "timestamp": now()})

    def write(self, job_id: str, name: str, obj: Any) -> None:
        with self._lock:
            write_json_atomic(self.dir(job_id) / name, obj)

    def write_text(self, job_id: str, name: str, text: str) -> None:
        d = self.dir(job_id)
        d.mkdir(parents=True, exist_ok=True)
        (d / name).write_text(text, encoding="utf-8")

    def read(self, job_id: str, name: str) -> Any | None:
        path = self.dir(job_id) / name
        with self._lock:
            return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None

    def mark_interrupted(self) -> int:
        """Jobs left running by a previous process cannot continue (the worker subprocess died with it)."""
        count = 0
        for path in self.jobs_dir.glob("*/job.json"):
            job = json.loads(path.read_text(encoding="utf-8"))
            if job["status"] not in TERMINAL_STATES:
                job["error"] = {"code": "interrupted", "message": "The backend stopped while this extraction was in progress. Start a new extraction."}
                self.set_state(job, "failed", "Interrupted by a backend restart", error=job["error"])
                count += 1
        return count
