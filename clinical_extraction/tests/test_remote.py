"""Tests for the hosted-endpoint path (no network, no Azure, no model): remote_client protocol, service wiring, result saving.
Run from the repository root:  .venv\\Scripts\\python -m pytest clinical_extraction/tests -q
"""
import json
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from clinical_extraction import blob_sink, remote_client, service as service_module            # noqa: E402
from clinical_extraction.job_store import JobStore                                              # noqa: E402
from clinical_extraction.service import ExtractionService                                       # noqa: E402

COMPACT = ROOT / "finetune_slm/archive/dataset_v2_batch_001_corrected" / "output" / "inputs" / "encounter_00037.json"
REFERENCE = ROOT / "finetune_slm/experiments/qwen3_1.7b_track" / "experiments" / "EXP_002_PROMPTING_INFERENCE" / "outputs" / "parsed" / "P02" / "encounter_00037.json"
pytestmark = pytest.mark.skipif(not (COMPACT.exists() and REFERENCE.exists()), reason="fixture files missing")


@pytest.fixture()
def compact():
    return json.loads(COMPACT.read_text(encoding="utf-8"))


@pytest.fixture()
def reference():
    return json.loads(REFERENCE.read_text(encoding="utf-8"))


class FakeEndpoint:
    """Replaces remote_client._post. `script` is a list of replies (dicts, or exceptions to raise), consumed in order per call."""
    def __init__(self, script):
        self.script, self.calls = list(script), []

    def __call__(self, body):
        self.calls.append(body)
        reply = self.script.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


def no_sleep(_):
    pass


def run_extract(fake, monkeypatch, compact):
    monkeypatch.setattr(remote_client, "_post", fake)
    states = []
    result = remote_client.extract(compact, on_state=lambda s, m: states.append((s, m)), sleep=no_sleep)
    return result, states


def test_happy_path(monkeypatch, compact, reference):
    fake = FakeEndpoint([{"job_id": "J1", "state": "queued"}, {"state": "running"}, {"state": "completed"}, {"ok": True, "extraction": reference, "metadata": {"parse_status": "ok"}}])
    result, states = run_extract(fake, monkeypatch, compact)
    assert result["ok"] and result["remote_job_id"] == "J1" and result["extraction"] == reference
    assert [c["action"] for c in fake.calls] == ["submit", "status", "status", "result"]
    assert fake.calls[0]["compact_transcript"] == compact
    assert states[-1][0] == "extracting"


def test_busy_then_accepted(monkeypatch, compact, reference):
    fake = FakeEndpoint([{"error": "busy"}, {"error": "model_not_ready"}, {"job_id": "J2"}, {"state": "completed"}, {"ok": True, "extraction": reference, "metadata": {}}])
    result, states = run_extract(fake, monkeypatch, compact)
    assert result["remote_job_id"] == "J2"
    assert any("busy" in m for _, m in states) and any("starting up" in m for _, m in states)


def test_lost_job_is_resubmitted_once(monkeypatch, compact, reference):
    fake = FakeEndpoint([{"job_id": "A"}, {"error": "unknown_job"}, {"job_id": "B"}, {"state": "completed"}, {"ok": True, "extraction": reference, "metadata": {}}])
    result, _ = run_extract(fake, monkeypatch, compact)
    assert result["remote_job_id"] == "B"
    fake2 = FakeEndpoint([{"job_id": "A"}, {"error": "unknown_job"}, {"job_id": "B"}, {"error": "unknown_job"}])
    monkeypatch.setattr(remote_client, "_post", fake2)
    with pytest.raises(remote_client.RemoteError) as info:
        remote_client.extract(compact, sleep=no_sleep)
    assert info.value.code == "remote_job_lost"


def test_transient_errors_tolerated_but_auth_failure_is_immediate(monkeypatch, compact, reference):
    flaky = remote_client.RemoteError("endpoint_unreachable", "x")
    fake = FakeEndpoint([{"job_id": "J"}, flaky, flaky, {"state": "completed"}, {"ok": True, "extraction": reference, "metadata": {}}])
    result, _ = run_extract(fake, monkeypatch, compact)
    assert result["ok"]
    monkeypatch.setattr(remote_client, "_post", FakeEndpoint([{"job_id": "J"}, remote_client.RemoteError("endpoint_auth_failed", "x")]))
    with pytest.raises(remote_client.RemoteError) as info:
        remote_client.extract(compact, sleep=no_sleep)
    assert info.value.code == "endpoint_auth_failed"


def test_rejected_submit(monkeypatch, compact):
    monkeypatch.setattr(remote_client, "_post", FakeEndpoint([{"error": "invalid_compact_transcript", "detail": "x"}]))
    with pytest.raises(remote_client.RemoteError) as info:
        remote_client.extract(compact, sleep=no_sleep)
    assert info.value.code == "endpoint_rejected"


def test_post_decodes_double_encoded_json_and_hides_secrets(monkeypatch):
    import io
    import urllib.error
    import urllib.request
    monkeypatch.setenv("EXTRACTION_ENDPOINT_URL", "https://example.test/score")
    monkeypatch.setenv("EXTRACTION_ENDPOINT_KEY", "SECRET-KEY")
    seen = {}

    class Resp(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *a): return False

    def fake_urlopen(request, timeout):
        seen["auth"] = request.get_header("Authorization")
        return Resp(json.dumps(json.dumps({"state": "queued", "job_id": "Z"})).encode())        # Azure ML: a JSON string containing JSON

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    assert remote_client._post({"action": "status"}) == {"state": "queued", "job_id": "Z"}
    assert seen["auth"] == "Bearer SECRET-KEY"

    def failing(request, timeout):
        raise urllib.error.HTTPError("https://example.test/score", 401, "denied SECRET-KEY", {}, io.BytesIO(b"echo SECRET-KEY"))

    monkeypatch.setattr(urllib.request, "urlopen", failing)
    with pytest.raises(remote_client.RemoteError) as info:
        remote_client._post({"action": "status"})
    assert info.value.code == "endpoint_auth_failed" and "SECRET" not in info.value.message
    assert remote_client.endpoint_host() == "example.test"


def make_service(tmp_path, compact, monkeypatch, endpoint_reply, saved=None):
    monkeypatch.setenv("EXTRACTION_BACKEND", "azure")                                            # Azure is opt-in; the default backend is the local model
    monkeypatch.setenv("EXTRACTION_ENDPOINT_URL", "https://example.test/score")
    monkeypatch.setenv("EXTRACTION_ENDPOINT_KEY", "k")
    monkeypatch.setattr(remote_client, "_post", endpoint_reply)
    monkeypatch.setattr(remote_client, "POLL_SECONDS", 0)
    store = JobStore(tmp_path)
    saved_docs = [] if saved is None else saved
    monkeypatch.setattr(blob_sink, "save", lambda ref, doc: saved_docs.append((ref, doc)) or {"container": "extraction-output", "blob_name": "37extraction.json"})
    return ExtractionService(store=store, source=lambda ref: (compact, {"kind": "slm_input", "blob_name": "37slm_input.json", "container_env": "AZURE_STORAGE_SLM_CONTAINER"})), saved_docs


def test_service_remote_success_saves_json_and_never_touches_local_python(tmp_path, monkeypatch, compact, reference):
    monkeypatch.delenv("EXTRACTION_PYTHON", raising=False)                                       # local path would fail with extraction_environment_missing
    fake = FakeEndpoint([{"job_id": "J"}, {"state": "completed"}, {"ok": True, "extraction": reference, "metadata": {"parse_status": "ok", "device": "CPU", "generation_seconds": 12.5, "prompt_sha256": "f6d5"}}])
    svc, saved = make_service(tmp_path, compact, monkeypatch, fake)
    job = svc.store.create("37", None)
    svc.run_job(job["job_id"])
    done = svc.store.load(job["job_id"])
    assert done["status"] in ("completed", "completed_with_warnings"), done.get("error")
    assert done["saved_to"] == {"container": "extraction-output", "blob_name": "37extraction.json"}
    assert svc.store.read(job["job_id"], "extraction_raw.json") == reference                      # raw model output untouched
    meta = svc.store.read(job["job_id"], "metadata.json")
    assert meta["inference_location"] == "azure_endpoint" and meta["remote_job_id"] == "J"
    ref, doc = saved[0]
    assert ref == "37" and doc["extraction"] == reference and doc["evidence"]["totals"] and doc["document_type"] == "clinical_extraction"
    assert svc.health()["inference_location"] == "azure_endpoint"


@pytest.mark.parametrize("meta, expected", [
    ({"extraction_status": "ok", "needs_review": False}, None),
    ({"extraction_status": "repaired", "needs_review": True}, "extraction repaired"),
    ({"extraction_status": "partial", "needs_review": True, "failed_windows": [2], "windows": 3}, "1 of 3 parts"),
    ({"needs_review": True}, "flagged for clinician review"),
])
def test_service_remote_review_flags_become_warnings(tmp_path, monkeypatch, compact, reference, meta, expected):
    fake = FakeEndpoint([{"job_id": "J"}, {"state": "completed"}, {"ok": True, "extraction": reference, "metadata": {"parse_status": "ok", "evidence_citations": "not requested", **meta}}])
    svc, _ = make_service(tmp_path, compact, monkeypatch, fake)
    job = svc.store.create("37", None)
    svc.run_job(job["job_id"])
    done = svc.store.load(job["job_id"])
    text = " | ".join(done.get("warnings") or [])
    if expected is None:
        assert "clinician review" not in text
    else:
        assert expected in text and done["status"] == "completed_with_warnings"


def test_service_remote_truncated_is_failure_and_not_saved(tmp_path, monkeypatch, compact):
    fake = FakeEndpoint([{"job_id": "J"}, {"state": "completed"}, {"ok": False, "metadata": {"parse_status": "truncated", "finish_reason": "length"}}])
    svc, saved = make_service(tmp_path, compact, monkeypatch, fake)
    job = svc.store.create("37", None)
    svc.run_job(job["job_id"])
    done = svc.store.load(job["job_id"])
    assert done["status"] == "failed" and done["error"]["code"] == "truncated" and saved == []


def test_service_remote_endpoint_error_is_reported(tmp_path, monkeypatch, compact):
    fake = FakeEndpoint([remote_client.RemoteError("endpoint_unreachable", "The extraction endpoint could not be reached (URLError).")])
    svc, _ = make_service(tmp_path, compact, monkeypatch, fake)
    job = svc.store.create("37", None)
    svc.run_job(job["job_id"])
    done = svc.store.load(job["job_id"])
    assert done["status"] == "failed" and done["error"]["code"] == "endpoint_unreachable"


def test_save_failure_keeps_result_with_warning(tmp_path, monkeypatch, compact, reference):
    from clinical_extraction.blob_source import SourceError
    fake = FakeEndpoint([{"job_id": "J"}, {"state": "completed"}, {"ok": True, "extraction": reference, "metadata": {"parse_status": "ok"}}])
    svc, _ = make_service(tmp_path, compact, monkeypatch, fake)

    def boom(ref, doc):
        raise SourceError("result_save_failed", "x")

    monkeypatch.setattr(blob_sink, "save", boom)
    job = svc.store.create("37", None)
    svc.run_job(job["job_id"])
    done = svc.store.load(job["job_id"])
    assert done["status"] == "completed_with_warnings" and done["saved_to"] is None
    assert any("could not be saved" in w for w in done["warnings"])
    assert svc.store.read(job["job_id"], "extraction_raw.json") == reference


def test_blob_names(monkeypatch):
    monkeypatch.delenv("AZURE_STORAGE_EXTRACTION_CONTAINER", raising=False)
    monkeypatch.delenv("EXTRACTION_FILE_SUFFIX", raising=False)
    assert blob_sink.container_name() == "extraction-output" and blob_sink.blob_name("3") == "03extraction.json" and blob_sink.blob_name("12") == "12extraction.json"
    monkeypatch.setenv("AZURE_STORAGE_EXTRACTION_CONTAINER", "my-out")
    assert blob_sink.container_name() == "my-out"


def test_atomic_write_survives_transient_permission_errors_and_concurrent_readers(tmp_path, monkeypatch):
    """Windows regression: os.replace raised PermissionError while the UI polled job.json, which failed the whole extraction."""
    import os
    import threading

    from clinical_extraction import job_store

    real_replace, calls = os.replace, {"n": 0}

    def flaky(src, dst):
        calls["n"] += 1
        if calls["n"] <= 3:
            raise PermissionError("file in use")
        return real_replace(src, dst)

    monkeypatch.setattr(job_store.os, "replace", flaky)
    store = JobStore(tmp_path)
    job = store.create("37", None)
    assert calls["n"] >= 4 and store.load(job["job_id"])["status"] == "queued"           # the first writes failed 3 times, then succeeded

    monkeypatch.setattr(job_store.os, "replace", real_replace)
    stop, errors = threading.Event(), []

    def poll():
        while not stop.is_set():
            try:
                assert store.load(job["job_id"]) is not None
            except Exception as exc:                                                       # noqa: BLE001
                errors.append(type(exc).__name__)

    readers = [threading.Thread(target=poll) for _ in range(4)]
    [t.start() for t in readers]
    for i in range(150):
        store.set_state(job, "extracting", f"step {i}")
    stop.set()
    [t.join() for t in readers]
    assert errors == [] and store.load(job["job_id"])["stage_message"] == "step 149"
    assert not list((tmp_path / "jobs" / job["job_id"]).glob("*.tmp"))                    # no temp files left behind
