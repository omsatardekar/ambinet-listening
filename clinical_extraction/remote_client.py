"""Client for the Azure-hosted extraction endpoint (Azure ML managed online endpoint today; any endpoint with the same contract later).

Contract (POST <EXTRACTION_ENDPOINT_URL>, header "Authorization: Bearer <EXTRACTION_ENDPOINT_KEY>", JSON body):
    {"action": "submit", "compact_transcript": {...}}  -> {"job_id", "state": "queued", "warnings": [...]}   or {"error": "busy" | ...}
    {"action": "status", "job_id": "..."}              -> {"state": queued|running|completed|failed, "error", "elapsed_seconds"}   or {"error": "unknown_job"}
    {"action": "result", "job_id": "..."}              -> {"ok": true, "extraction": {...}, "metadata": {...}, "evidence": {...}}  or {"ok": false, "metadata": {...}}
Azure ML returns the JSON returned by score.py as a JSON *string*; this client decodes that second layer. Replacing the model (for example by a fine-tuned
model on a GPU endpoint) only needs a new URL and key if the new endpoint keeps this contract. The key is read from the environment and never logged.
Standard library only (urllib), so the backend venv needs no new package.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Callable

ENV_URL = "EXTRACTION_ENDPOINT_URL"
ENV_KEY = "EXTRACTION_ENDPOINT_KEY"
REQUEST_TIMEOUT_SECONDS = float(os.getenv("EXTRACTION_ENDPOINT_REQUEST_TIMEOUT_SECONDS", "120"))    # per HTTP call (Azure ML cuts requests at 180 s)
POLL_SECONDS = float(os.getenv("EXTRACTION_ENDPOINT_POLL_SECONDS", "10"))
JOB_TIMEOUT_SECONDS = float(os.getenv("EXTRACTION_ENDPOINT_JOB_TIMEOUT_MINUTES", "60")) * 60
BUSY_RETRY_SECONDS = float(os.getenv("EXTRACTION_ENDPOINT_BUSY_RETRY_SECONDS", "15"))
MAX_TRANSIENT_ERRORS = 6                                                                         # consecutive network/5xx errors tolerated while polling


class RemoteError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def configured() -> bool:
    return bool(os.getenv(ENV_URL, "").strip() and os.getenv(ENV_KEY, "").strip())


def endpoint_host() -> str | None:
    url = os.getenv(ENV_URL, "").strip()
    return url.split("//", 1)[-1].split("/", 1)[0] if url else None


def _post(body: dict[str, Any]) -> dict[str, Any]:
    url, key = os.getenv(ENV_URL, "").strip(), os.getenv(ENV_KEY, "").strip()
    request = urllib.request.Request(url, data=json.dumps(body, ensure_ascii=False).encode("utf-8"), method="POST",
                                     headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            payload = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        # never include the response body or the key in the message (the body can echo request content)
        code = "endpoint_auth_failed" if exc.code in (401, 403) else "endpoint_http_error"
        raise RemoteError(code, f"The extraction endpoint answered HTTP {exc.code}.") from None
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise RemoteError("endpoint_unreachable", f"The extraction endpoint could not be reached ({type(exc).__name__}).") from None
    try:
        data = json.loads(payload)
        if isinstance(data, str):                                                                # Azure ML double-encodes score.py's return value
            data = json.loads(data)
    except ValueError:
        raise RemoteError("endpoint_bad_response", "The extraction endpoint returned something that is not JSON.") from None
    if not isinstance(data, dict):
        raise RemoteError("endpoint_bad_response", "The extraction endpoint returned an unexpected JSON shape.")
    return data


def extract(compact: dict, on_state: Callable[[str, str], None] | None = None, sleep: Callable[[float], None] = time.sleep,
            clock: Callable[[], float] = time.monotonic) -> dict[str, Any]:
    """Submit, poll, fetch. Returns the endpoint's result dict ({"ok": ..., "extraction"?, "metadata", "evidence"?}) and adds "remote_job_id".

    Raises RemoteError with a stable code. A job that the endpoint lost (container restart) is resubmitted once.
    """
    notify = on_state or (lambda state, message: None)
    deadline = clock() + JOB_TIMEOUT_SECONDS
    resubmitted = False
    while True:
        notify("queued", "Sent to the Azure-hosted model; waiting for a free slot")
        job_id = _submit_with_retry(compact, deadline, notify, sleep, clock)
        errors = 0
        while True:
            if clock() > deadline:
                raise RemoteError("endpoint_timeout", "The extraction did not finish within the allowed time.")
            sleep(POLL_SECONDS)
            try:
                status = _post({"action": "status", "job_id": job_id})
                errors = 0
            except RemoteError as exc:
                if exc.code == "endpoint_auth_failed":
                    raise
                errors += 1
                if errors >= MAX_TRANSIENT_ERRORS:
                    raise
                continue
            if status.get("error") == "unknown_job":                                             # container restarted: jobs are in memory there
                if resubmitted:
                    raise RemoteError("remote_job_lost", "The endpoint lost the job twice (it restarted).")
                resubmitted = True
                break
            state = status.get("state")
            if state in ("queued", "running"):
                notify("extracting", "The Azure-hosted model is extracting clinical facts")
                continue
            if state in ("completed", "failed"):
                result = _post({"action": "result", "job_id": job_id})
                result["remote_job_id"] = job_id
                return result
            raise RemoteError("endpoint_bad_response", f"Unexpected job state from the endpoint: {state!r}.")


def _submit_with_retry(compact: dict, deadline: float, notify: Callable[[str, str], None], sleep: Callable[[float], None], clock: Callable[[], float]) -> str:
    while True:
        reply = _post({"action": "submit", "compact_transcript": compact})
        if reply.get("job_id"):
            return str(reply["job_id"])
        error = reply.get("error")
        if error == "busy":                                                                      # one extraction at a time on the endpoint: wait our turn
            if clock() > deadline:
                raise RemoteError("endpoint_timeout", "The endpoint stayed busy for too long.")
            notify("queued", "The Azure-hosted model is busy with another extraction; waiting")
            sleep(BUSY_RETRY_SECONDS)
            continue
        if error == "model_not_ready":                                                           # still hashing the weights after a (re)start
            if clock() > deadline:
                raise RemoteError("endpoint_timeout", "The endpoint model did not become ready in time.")
            notify("queued", "The Azure-hosted model is starting up; waiting")
            sleep(BUSY_RETRY_SECONDS)
            continue
        raise RemoteError("endpoint_rejected", f"The endpoint rejected the request: {error or 'unknown'}.")
