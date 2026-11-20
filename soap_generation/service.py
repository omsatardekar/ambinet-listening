"""SOAP job service: one background worker, persisted jobs, plain stage states.

queued -> reading_summary (extraction container) -> drafting_note (agent or model) -> checking_note (format + traceability) -> saving (soap container) -> completed

`make_note` is the whole transformation without any storage or job handling (used by the service and by scripts/generate_soap.py)."""
from __future__ import annotations

import logging
import queue
import threading
from datetime import datetime, timezone
from typing import Any, Callable

from clinical_extraction import blob_source
from clinical_extraction.blob_source import SourceError
from clinical_extraction.job_store import JobStore, now

from . import blob_io, config, guard, llm, prepare, render
from .schema import NoteFormatError, normalise, parse_json

log = logging.getLogger("soap_generation")
Generator = Callable[[dict, "str | None"], str]


def make_note(doc: dict, generate: Generator, attempts: int = 2, conversation: list | None = None) -> dict[str, Any]:
    """doc = the saved extraction document. Returns {"note", "review", "markdown", "payload", "issues"}. Raises NoteFormatError after `attempts` unusable answers."""
    payload = prepare.build_input(doc, conversation)
    hint: str | None = None
    last: NoteFormatError | None = None
    for _ in range(max(1, attempts)):
        text = generate(payload, hint)
        try:
            note, issues = normalise(parse_json(text))
            break
        except NoteFormatError as exc:
            last, hint = exc, str(exc)
    else:
        raise last or NoteFormatError("no usable answer")
    if not note["encounter"]["encounter_id"]:
        note["encounter"]["encounter_id"] = payload["encounter"]["encounter_id"]
    checks = guard.check(note, payload)
    review = {"data_quality_flags": payload["data_quality_flags"], "system_checks": checks}
    return {"note": note, "review": review, "markdown": render.render(note, review), "payload": payload, "issues": issues}


class SoapJobStore(JobStore):
    """Same persistence as the extraction jobs, with the stage names of this module."""

    def __init__(self, root=None) -> None:
        super().__init__(root or config.DATA_DIR)

    def create(self, encounter_ref: str, run_id: str | None) -> dict:
        job = super().create(encounter_ref, run_id)
        job["stage_message"] = "Waiting in the queue"
        job["events"][0]["message"] = "Queued"
        self.save(job)
        return job

    def set_state(self, job: dict, status: str, message: str, **extra: Any) -> None:
        with self._lock:
            job["status"], job["stage_message"] = status, message
            job.update(extra)
            if status == "reading_summary" and not job["started_at"]:
                job["started_at"] = now()
            if status in config.TERMINAL_STATES:
                job["finished_at"] = now()
            self._event(job, status, message)
            self.save(job)

    def mark_interrupted(self) -> int:
        count = 0
        for path in self.jobs_dir.glob("*/job.json"):
            import json
            job = json.loads(path.read_text(encoding="utf-8"))
            if job["status"] not in config.TERMINAL_STATES:
                err = {"code": "interrupted", "message": "The backend stopped while this note was being prepared. Please generate it again."}
                self.set_state(job, "failed", "Interrupted by a backend restart", error=err)
                count += 1
        return count


class SoapService:
    def __init__(self, store: SoapJobStore | None = None, source: Callable[[str], "tuple[dict, dict]"] | None = None, generate: Generator | None = None,
                 saver: Callable[[str, dict, str], dict] | None = None, run_lookup: Callable[[str], dict | None] | None = None) -> None:
        self.store = store or SoapJobStore()
        self.source = source or blob_io.fetch_extraction
        self.generate = generate or llm.generate
        self.saver = saver or blob_io.save_note
        self.run_lookup = run_lookup
        self._queue: "queue.Queue[str]" = queue.Queue()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._interrupted = self.store.mark_interrupted()

    # ---- public -----------------------------------------------------------------------------------------------------------
    def start_thread(self) -> None:
        with self._lock:
            if self._thread is None or not self._thread.is_alive():
                self._thread = threading.Thread(target=self._loop, name="soap-generation", daemon=True)
                self._thread.start()

    def submit(self, encounter_ref: str | None = None, run_id: str | None = None) -> dict:
        ref = encounter_ref
        if not ref and run_id:
            result = self.run_lookup(run_id) if self.run_lookup else None
            ref = (result or {}).get("encounter_id") if isinstance(result, dict) else None
            if not ref:
                raise SourceError("run_not_ready", "That transcription run is unknown or its transcript is not ready.")
        if not ref:
            raise SourceError("missing_reference", "Provide encounter_id or run_id.")
        job = self.store.create(str(ref), run_id)
        self._queue.put(job["job_id"])
        self.start_thread()
        return job

    def health(self) -> dict[str, Any]:
        mode = config.backend()
        ready = config.agent_ready() if mode == "agent" else config.model_configured()
        return {"backend": mode, "ready": bool(ready), "result_container": blob_io.container_name(), "jobs_interrupted_by_restart": self._interrupted,
                "prompt_version": config.PROMPT_VERSION}

    # ---- worker -----------------------------------------------------------------------------------------------------------
    def _loop(self) -> None:
        while True:
            job_id = self._queue.get()
            try:
                self.run_job(job_id)
            except Exception as exc:                                                                    # noqa: BLE001  never let the worker die
                log.error("SOAP job %s crashed (%s)", job_id, type(exc).__name__)
                job = self.store.load(job_id)
                if job and job["status"] not in config.TERMINAL_STATES:
                    self.store.set_state(job, "failed", "The note could not be completed.", error={"code": "internal_error", "message": "The note could not be completed. Please try again."})

    def run_job(self, job_id: str) -> None:
        job = self.store.load(job_id)
        fail = lambda code, msg: self.store.set_state(job, "failed", msg, error={"code": code, "message": msg})        # noqa: E731
        self.store.set_state(job, "reading_summary", "Reading the clinical summary")
        try:
            doc, source_info = self.source(job["encounter_ref"])
        except SourceError as exc:
            return fail(exc.code, exc.message)
        job["encounter_id"] = str(doc.get("encounter_id") or job["encounter_ref"])
        job["source"] = source_info
        self.store.save(job)

        conversation = None
        if config.INCLUDE_TRANSCRIPT:
            try:
                conversation = blob_source.fetch_compact(job["encounter_ref"])[0].get("segments")
            except SourceError:
                conversation = None                                                          # the note is still written from the clinical summary alone
                job.setdefault("warnings", []).append("the full conversation could not be read: statements about what was not discussed may be incomplete")
        self.store.set_state(job, "drafting_note", "Drafting the SOAP note")
        try:
            result = make_note(doc, self.generate, conversation=conversation)
        except llm.LlmError as exc:
            return fail(exc.code, exc.message)
        except NoteFormatError:
            return fail("note_format", "The note could not be put into the expected format. Please try again.")
        except ValueError:
            return fail("no_findings", "The clinical summary has no findings to write a note from.")

        self.store.set_state(job, "checking_note", "Checking the note against the conversation")
        warnings: list[str] = list(job.get("warnings") or [])
        if result["review"]["system_checks"]:
            warnings.append(f"{len(result['review']['system_checks'])} value(s) could not be traced to the conversation")
        job["warnings"] = warnings
        self.store.write(job_id, "input_payload.json", result["payload"])
        self.store.write(job_id, "note.json", result["note"])
        self.store.write(job_id, "review.json", result["review"])
        self.store.write_text(job_id, "note.md", result["markdown"])

        self.store.set_state(job, "saving", "Saving the note")
        document = {"document_type": "soap_note", "version": 1, "saved_at": datetime.now(timezone.utc).isoformat(), "notice": config.NOTICE,
                    "encounter_id": job["encounter_id"], "encounter_ref": job["encounter_ref"], "job_id": job_id,
                    "source": {"extraction": source_info}, "note": result["note"], "review": result["review"], "markdown": result["markdown"],
                    "generation": {"backend": config.backend(), "prompt_version": config.PROMPT_VERSION}}
        try:
            job["saved_to"] = self.saver(job["encounter_ref"], document, result["markdown"])
        except SourceError as exc:
            job["saved_to"] = None
            warnings.append("the note could not be saved to the soap container (" + exc.code + ")")
        job["warnings"] = warnings
        final = "completed_with_warnings" if warnings else "completed"
        self.store.set_state(job, final, "SOAP note ready. Draft for clinician review.")
