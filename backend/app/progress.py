from __future__ import annotations

import copy
import threading
import uuid
from datetime import datetime, timezone
from typing import Any


PIPELINE_STAGES = (
    ("audio_upload", "Recording received"),
    ("speech_transcription", "Speech transcription"),
    ("llm_reconstruction", "Conversation structure"),
    ("final_transcript", "Review-ready draft"),
)


class ProgressManager:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._runs: dict[str, dict[str, Any]] = {}
        self._fingerprints: dict[str, str] = {}

    def create(self, filename: str, fingerprint: str) -> tuple[str, bool]:
        with self._lock:
            existing_id = self._fingerprints.get(fingerprint)
            if existing_id in self._runs:
                return existing_id, True

            run_id = uuid.uuid4().hex
            state: dict[str, Any] = {
                "run_id": run_id,
                "filename": filename,
                "status": "queued",
                "current_stage": None,
                "operation": "Waiting to start",
                "message": "Recording received. Preparing the pipeline.",
                "percent": 0,
                "stages": {
                    key: {"label": label, "status": "waiting", "message": "Waiting"}
                    for key, label in PIPELINE_STAGES
                },
                "events": [],
                "result": None,
                "error": None,
                "started_at": datetime.now(timezone.utc).isoformat(),
            }
            self._runs[run_id] = state
            self._fingerprints[fingerprint] = run_id
            self._append_event(state, None, "queued", state["message"], 0, state["operation"])
            return run_id, False

    def update(
        self,
        run_id: str,
        stage: str,
        status: str,
        message: str,
        percent: int,
        operation: str | None = None,
        stage_status: str | None = None,
    ) -> None:
        with self._lock:
            state = self._require_run(run_id)
            if stage not in state["stages"]:
                raise ValueError(f"Unknown pipeline stage: {stage}")
            state["status"] = "running"
            state["current_stage"] = stage
            state["operation"] = operation or message
            state["message"] = message
            # The bar only ever moves forward within a run.
            state["percent"] = max(state["percent"], max(0, min(100, percent)))
            state["stages"][stage]["status"] = stage_status or status
            state["stages"][stage]["message"] = message
            self._append_event(state, stage, status, message, state["percent"], state["operation"])

    def complete(self, run_id: str, result: dict[str, Any]) -> None:
        with self._lock:
            state = self._require_run(run_id)
            state["status"] = "completed"
            state["current_stage"] = "final_transcript"
            state["operation"] = "Pipeline completed"
            state["message"] = "Final transcript uploaded successfully. Pipeline completed."
            state["percent"] = 100
            state["result"] = copy.deepcopy(result)
            self._append_event(
                state,
                "final_transcript",
                "completed",
                state["message"],
                100,
                state["operation"],
            )

    def fail(self, run_id: str, stage: str, message: str) -> None:
        with self._lock:
            state = self._require_run(run_id)
            state["status"] = "failed"
            state["current_stage"] = stage
            state["operation"] = "Pipeline stopped"
            state["message"] = message
            state["error"] = message
            if stage in state["stages"]:
                state["stages"][stage]["status"] = "failed"
                state["stages"][stage]["message"] = message
            self._append_event(
                state,
                stage,
                "failed",
                message,
                state["percent"],
                state["operation"],
            )

    def status(self, run_id: str) -> dict[str, Any] | None:
        with self._lock:
            state = self._runs.get(run_id)
            return self._public_state(state) if state else None

    def events_after(self, run_id: str, sequence: int) -> tuple[list[dict[str, Any]], bool]:
        with self._lock:
            state = self._runs.get(run_id)
            if state is None:
                raise KeyError(run_id)
            events = [copy.deepcopy(event) for event in state["events"] if event["sequence"] > sequence]
            return events, state["status"] in {"completed", "failed"}

    def result(self, run_id: str) -> dict[str, Any] | None:
        with self._lock:
            state = self._runs.get(run_id)
            if state is None or state["status"] != "completed":
                return None
            return copy.deepcopy(state["result"])

    def _append_event(
        self,
        state: dict[str, Any],
        stage: str | None,
        status: str,
        message: str,
        percent: int,
        operation: str,
    ) -> None:
        state["events"].append({
            "sequence": len(state["events"]) + 1,
            "run_id": state["run_id"],
            "filename": state["filename"],
            "stage": stage,
            "status": status,
            "run_status": state["status"],
            "message": message,
            "operation": operation,
            "percent": percent,
            "stages": copy.deepcopy(state["stages"]),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    @staticmethod
    def _public_state(state: dict[str, Any]) -> dict[str, Any]:
        return {
            key: copy.deepcopy(value)
            for key, value in state.items()
            if key not in {"events", "result"}
        }

    def _require_run(self, run_id: str) -> dict[str, Any]:
        try:
            return self._runs[run_id]
        except KeyError as exc:
            raise KeyError(run_id) from exc
