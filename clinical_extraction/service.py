"""Extraction service: one background worker, persisted jobs, honest stage states (no percentage during generation).

Two ways to run the model, chosen by config.backend():
  * AZURE (default when EXTRACTION_ENDPOINT_URL/KEY are set): the compact transcript is sent to the model hosted on Azure ML (remote_client.py: submit/status/result).
  * LOCAL (no endpoint configured, or EXTRACTION_BACKEND=local): Qwen3-0.6B with the frozen H1 prompt (EXP_008) in a subprocess of the separate OpenVINO environment (h1_worker.py).
(inference_worker.py, the frozen 1.7B P02 worker, is kept in the repository but is no longer started by the service.)
Either way the finished extraction is saved as JSON in the extraction container (blob_sink.py). The existing transcription pipeline is not used or modified.
"""
from __future__ import annotations

import json
import logging
import queue
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Callable

from . import blob_sink, blob_source, evidence, postprocess, remote_client
from .compact import CompactTranscriptError, validate_compact
from . import config
from .config import DRAFT_NOTICE, extraction_python
from .job_store import JobStore

log = logging.getLogger("clinical_extraction")
WORKER = Path(__file__).resolve().parent / "h1_worker.py"
EVENT_TO_STATE = {"preparing": "preparing_transcript", "reading_transcript": "reading_transcript", "loading_model": "loading_model",
                  "extracting": "extracting", "validating_output": "validating_output"}
Source = Callable[[str], "tuple[dict, dict]"]


def _repair_mojibake(node: Any) -> int:
    """In place: 'Â°' (UTF-8 degree sign read as Latin-1) -> '°' in every string. Returns the number of strings changed."""
    n = 0
    if isinstance(node, dict):
        for k, v in node.items():
            if isinstance(v, str) and "Â°" in v:
                node[k] = v.replace("Â°", "°")
                n += 1
            else:
                n += _repair_mojibake(v)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            if isinstance(v, str) and "Â°" in v:
                node[i] = v.replace("Â°", "°")
                n += 1
            else:
                n += _repair_mojibake(v)
    return n


class ExtractionService:
    def __init__(self, store: JobStore | None = None, source: Source | None = None, run_lookup: Callable[[str], dict | None] | None = None) -> None:
        self.store = store or JobStore()
        self.source = source or blob_source.fetch_compact
        self.run_lookup = run_lookup
        self._queue: "queue.Queue[str]" = queue.Queue()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._interrupted = self.store.mark_interrupted()

    # ---- public API -------------------------------------------------------------------------------------------------
    def start_thread(self) -> None:
        with self._lock:
            if self._thread is None or not self._thread.is_alive():
                self._thread = threading.Thread(target=self._loop, name="clinical-extraction", daemon=True)   # one worker: one model load at a time
                self._thread.start()

    def submit(self, encounter_ref: str | None = None, run_id: str | None = None) -> dict:
        ref = encounter_ref
        if not ref and run_id:
            result = self.run_lookup(run_id) if self.run_lookup else None
            ref = (result or {}).get("encounter_id") if isinstance(result, dict) else None
            if not ref:
                raise blob_source.SourceError("run_not_ready", "That transcription run is unknown or its final transcript is not ready.")
        if not ref:
            raise blob_source.SourceError("missing_reference", "Provide encounter_id or run_id.")
        job = self.store.create(str(ref), run_id)
        self._queue.put(job["job_id"])
        self.start_thread()
        return job

    def health(self) -> dict[str, Any]:
        py = extraction_python()
        storage = blob_source.configured()
        info: dict[str, Any] = {"backend": config.backend(), "storage_settings_present": storage, "result_container": blob_sink.container_name(),
                                "jobs_interrupted_by_restart": self._interrupted}
        storage_ok = all(storage.values())
        if config.backend() == "azure":
            remote = remote_client.configured()
            info.update(inference_location="azure_endpoint", endpoint_configured=remote, endpoint_host=remote_client.endpoint_host() if remote else None,
                        device_policy="hosted endpoint (device decided by the endpoint)", ready=bool(storage_ok and remote))
            return info
        from . import h1_worker
        required = ["openvino_model.xml", "openvino_model.bin", "openvino_tokenizer.xml", "openvino_detokenizer.xml", "config.json", "tokenizer.json"]
        missing = [n for n in required if not (h1_worker.MODEL_DIR / n).exists()]
        pointer = [n for n in ("openvino_model.bin",) if (h1_worker.MODEL_DIR / n).exists() and (h1_worker.MODEL_DIR / n).stat().st_size < 1024]
        info.update(inference_location="local_openvino", model="Qwen3-0.6B (OpenVINO FP16) with the frozen H1 prompt (EXP_008)",
                    extraction_python_configured=py is not None and py.exists(), model_files_missing=missing, model_files_are_lfs_pointers=pointer,
                    prompt_file_present=h1_worker.PROMPT_FILE.exists(), expected_prompt_sha256="dc10ba065c9f1acaa237d106bd97b451ddfe1efcd94117b727d6585511f79cd8",
                    device_setting=config.device_setting(), min_available_ram_gib=config.H1_MIN_AVAILABLE_RAM_GIB,
                    device_policy="GPU if OpenVINO sees one, otherwise CPU (EXTRACTION_DEVICE overrides)")
        info["ready"] = bool(info["extraction_python_configured"] and not missing and not pointer and info["prompt_file_present"] and storage_ok)
        if not info["extraction_python_configured"]:
            info["setup_hint"] = "Run: python -m clinical_extraction.setup_local_model"
        elif missing or pointer:
            info["setup_hint"] = "Model weights missing: run `git lfs install` and `git lfs pull`"
        return info

    # ---- worker -----------------------------------------------------------------------------------------------------
    def _loop(self) -> None:
        while True:
            job_id = self._queue.get()
            try:
                self.run_job(job_id)
            except Exception as exc:                                                              # never let the worker thread die
                log.error("extraction job %s crashed (%s)", job_id, type(exc).__name__)
                job = self.store.load(job_id)
                if job and job["status"] not in ("completed", "completed_with_warnings", "failed"):
                    self.store.set_state(job, "failed", "The extraction stopped unexpectedly.", error={"code": "internal_error", "message": type(exc).__name__})

    def run_job(self, job_id: str) -> None:
        job = self.store.load(job_id)
        self.store.set_state(job, "preparing_transcript", "Reading the final transcript from storage")
        try:
            compact, source_info = self.source(job["encounter_ref"])
            warnings = [f"compact transcript: {w}" for w in validate_compact(compact)]
        except (blob_source.SourceError, CompactTranscriptError) as exc:
            code = getattr(exc, "code", "invalid_transcript")
            return self.store.set_state(job, "failed", "The transcript could not be prepared.", error={"code": code, "message": getattr(exc, "message", str(exc))})
        manifest = source_info.get("manifest") or {}
        if manifest and manifest.get("slm_eligible") is False:
            warnings.append("source manifest marks this transcript as needing review (slm_eligible=false); extraction was still run")
        job["encounter_id"] = compact["encounter_id"]
        job["source"] = source_info
        job["warnings"] = warnings
        self.store.write(job_id, "input_compact.json", compact)

        if config.backend() == "azure":
            if not remote_client.configured():
                return self.store.set_state(job, "failed", "EXTRACTION_BACKEND=azure but the endpoint is not configured.", error={"code": "endpoint_not_configured", "message": "Set EXTRACTION_ENDPOINT_URL and EXTRACTION_ENDPOINT_KEY, or remove EXTRACTION_BACKEND to use the local model."})
            return self._run_remote(job, compact, warnings)

        py = extraction_python()
        if py is None or not py.exists():
            return self.store.set_state(job, "failed", "The extraction environment is not configured.", error={"code": "extraction_environment_missing", "message": "Run `python -m clinical_extraction.setup_local_model` (or set EXTRACTION_PYTHON to the OpenVINO environment's python executable)."})
        out = self.store.dir(job_id)
        cmd = [str(py), "-B", "-s", str(WORKER), "--input", str(out / "input_compact.json"), "--out", str(out), "--ram-gate-gib", str(config.H1_MIN_AVAILABLE_RAM_GIB), "--device", config.device_setting()]
        error: dict | None = None
        t0 = time.time()
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, encoding="utf-8")
            for line in proc.stdout:                                                              # JSON event lines only; no transcript text
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                state = EVENT_TO_STATE.get(event.get("event"))
                if state:
                    self.store.set_state(job, state, str(event.get("message") or state))
            proc.wait()
        except OSError as exc:
            return self.store.set_state(job, "failed", "The inference process could not be started.", error={"code": "worker_start_failed", "message": type(exc).__name__})

        result = self.store.read(job_id, "result.json")
        if result is None:
            return self.store.set_state(job, "failed", "The inference process ended without a result.", error={"code": "worker_no_result", "message": f"exit code {proc.returncode}"})
        if not result.get("ok") and "metadata" not in result:
            return self.store.set_state(job, "failed", result.get("message") or "Extraction failed.", error={"code": result.get("code"), "message": result.get("message"), "detail": result.get("detail")})
        metadata = result["metadata"]
        metadata.update(job_id=job_id, encounter_ref=job["encounter_ref"], source=source_info, elapsed_seconds_total=round(time.time() - t0, 1))
        self.store.write(job_id, "metadata.json", metadata)
        if not result.get("ok"):                                                                  # parse failure / truncation: never reported as a success
            code = metadata["parse_status"]
            msg = "The model output was cut off at the token limit." if code == "truncated" else "The model output could not be parsed as JSON."
            return self.store.set_state(job, "failed", msg, error={"code": code, "message": msg, "finish_reason": metadata.get("finish_reason")})

        self._finalize(job, compact, warnings, metadata)

    # ---- remote path --------------------------------------------------------------------------------------------------
    def _run_remote(self, job: dict, compact: dict, warnings: list[str]) -> None:
        job_id = job["job_id"]
        last: list[tuple[str, str]] = []

        def on_state(state: str, message: str) -> None:                                       # only record real changes (one event per message)
            if last and last[-1] == (state, message):
                return
            last.append((state, message))
            self.store.set_state(job, "extracting", message)

        t0 = time.time()
        self.store.set_state(job, "extracting", "Sending the transcript to the Azure-hosted model")
        try:
            result = remote_client.extract(compact, on_state=on_state)
        except remote_client.RemoteError as exc:
            return self.store.set_state(job, "failed", exc.message, error={"code": exc.code, "message": exc.message})
        metadata = dict(result.get("metadata") or {})
        if not result.get("ok") and not metadata:
            err = result.get("error")
            return self.store.set_state(job, "failed", "The Azure-hosted model reported an error.", error={"code": (err or {}).get("code", "remote_failed") if isinstance(err, dict) else "remote_failed",
                                                                                                           "message": "The Azure-hosted model reported an error."})
        self.store.set_state(job, "validating_output", "Checking the model output")
        metadata.update(job_id=job_id, encounter_ref=job["encounter_ref"], source=job.get("source"), inference_location="azure_endpoint", endpoint_host=remote_client.endpoint_host(),
                        remote_job_id=result.get("remote_job_id"), elapsed_seconds_total=round(time.time() - t0, 1))
        metadata.setdefault("wall_seconds", metadata.get("generation_seconds"))
        self.store.write(job_id, "metadata.json", metadata)
        if not result.get("ok"):                                                              # truncated / invalid JSON: never reported as a success
            code = metadata.get("parse_status") or "remote_failed"
            msg = "The model output was cut off at the token limit." if code == "truncated" else "The model output could not be parsed as JSON."
            return self.store.set_state(job, "failed", msg, error={"code": code, "message": msg, "finish_reason": metadata.get("finish_reason")})
        extraction = result.get("extraction")
        if not isinstance(extraction, dict):
            return self.store.set_state(job, "failed", "The endpoint returned no extraction.", error={"code": "endpoint_bad_response", "message": "No extraction in the endpoint result."})
        fixed = _repair_mojibake(extraction)                                                  # the model learned "Â°C" from ~5% of its round-1 training labels
        if fixed:
            metadata["text_encoding_repaired"] = fixed
            self.store.write(job_id, "metadata.json", metadata)
        self.store.write(job_id, "extraction_model_output.json", extraction)                    # exactly what the model returned (after the encoding repair)
        extraction, changes = postprocess.clean(extraction)
        if changes:
            metadata["postprocess"] = changes
            self.store.write(job_id, "metadata.json", metadata)
            warnings.extend(w for w in (postprocess.warning_for(c) for c in changes) if w)
        self.store.write(job_id, "extraction_raw.json", extraction)
        self._finalize(job, compact, warnings, metadata)

    # ---- shared end of both paths -------------------------------------------------------------------------------------
    def _finalize(self, job: dict, compact: dict, warnings: list[str], metadata: dict) -> None:
        job_id = job["job_id"]
        self.store.set_state(job, "resolving_evidence", "Resolving model-cited transcript segments")
        extraction = self.store.read(job_id, "extraction_raw.json")
        derived = evidence.resolve_all(extraction, compact)
        self.store.write(job_id, "evidence.json", derived)
        totals = derived["totals"]
        schema = metadata.get("schema_validation") or {}
        if schema and not schema.get("compliant"):
            warnings.append(f"schema validation reported violations: {schema.get('violation_counts')}")
        status = metadata.get("extraction_status")                                             # set by the fine-tuned scoring file: ok | repaired | partial (absent for H1 / local)
        if status == "partial":
            failed = metadata.get("failed_windows") or []
            warnings.append(f"extraction partial: {len(failed)} of {metadata.get('windows', '?')} parts of the consultation could not be read; clinician review required")
        elif status == "repaired":
            warnings.append("extraction repaired: the model output had to be corrected automatically; clinician review required")
        elif metadata.get("needs_review"):
            warnings.append("extraction flagged for clinician review")
        if metadata.get("finish_reason") == "length":
            warnings.append("generation stopped at the token limit")
        no_citations = str(metadata.get("evidence_citations") or "").startswith("not requested")       # H1 does not ask for segment ids: empty lists are expected, not a warning
        for key in ("invalid_format", "not_found", "duplicate", "empty_evidence_list", "unusually_large_evidence_list"):
            if no_citations and key == "empty_evidence_list":
                continue
            if totals.get(key):
                warnings.append(f"evidence: {totals[key]} x {key}")
        try:                                                                                   # the finished JSON goes to the extraction container (the result is kept locally either way)
            document = blob_sink.build_document({**job, "warnings": warnings}, compact, extraction, metadata, derived, DRAFT_NOTICE)
            job["saved_to"] = blob_sink.save(job["encounter_ref"], document)
        except blob_source.SourceError as exc:
            job["saved_to"] = None
            warnings.append(f"the result could not be saved to the extraction container ({exc.code})")
        job["warnings"] = warnings
        final = "completed_with_warnings" if warnings else "completed"
        self.store.set_state(job, final, "Extraction finished. Draft for clinician review." if final == "completed" else "Extraction finished with warnings. Draft for clinician review.")
