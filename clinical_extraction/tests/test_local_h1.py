"""Tests for the local-model backend (Qwen3-0.6B + H1 prompt). No model and no Azure: the worker is replaced by a stub."""
import json
import sys
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from clinical_extraction import blob_sink, config, remote_client, service as service_module     # noqa: E402
from clinical_extraction.job_store import JobStore                                              # noqa: E402
from clinical_extraction.service import ExtractionService                                       # noqa: E402

COMPACT = ROOT / "finetune_slm/archive/dataset_v2_batch_001_corrected" / "output" / "inputs" / "encounter_00037.json"
pytestmark = pytest.mark.skipif(not COMPACT.exists(), reason="fixture file missing")

H1_STUB = textwrap.dedent('''
    import json, sys
    from pathlib import Path
    a = sys.argv
    out = Path(a[a.index("--out") + 1])
    (out / "args.json").write_text(json.dumps(a[1:]), encoding="utf-8")
    for e in ("preparing", "reading_transcript", "loading_model", "extracting", "validating_output"):
        print(json.dumps({"event": e, "message": e}), flush=True)
    extraction = {"encounter_id": "00037", "symptoms": [{"name": "fever", "evidence_ids": []}], "negative_findings": []}
    (out / "extraction_raw.json").write_text(json.dumps(extraction), encoding="utf-8")
    meta = {"parse_status": "ok", "finish_reason": "stop", "inference_location": "local_openvino", "device": "CPU",
            "evidence_citations": "not requested by the H1 prompt (evidence_ids are expected to be empty)", "schema_validation": {"compliant": True, "violation_counts": {}}}
    (out / "result.json").write_text(json.dumps({"ok": True, "metadata": meta}), encoding="utf-8")
''')


def _service(tmp_path, monkeypatch, saved):
    (tmp_path / "h1_stub.py").write_text(H1_STUB, encoding="utf-8")
    monkeypatch.setattr(service_module, "WORKER", tmp_path / "h1_stub.py")
    monkeypatch.setenv("EXTRACTION_PYTHON", sys.executable)
    monkeypatch.setattr(blob_sink, "save", lambda ref, doc: saved.append((ref, doc)) or {"container": "extraction-output", "blob_name": "37extraction.json"})
    compact = json.loads(COMPACT.read_text(encoding="utf-8"))
    return ExtractionService(store=JobStore(tmp_path / "data"), source=lambda ref: (compact, {"kind": "local"}))


def test_local_backend_can_be_forced_even_when_the_azure_endpoint_is_configured(tmp_path, monkeypatch):
    monkeypatch.setenv("EXTRACTION_BACKEND", "local")
    monkeypatch.setenv("EXTRACTION_ENDPOINT_URL", "https://example.test/score")
    monkeypatch.setenv("EXTRACTION_ENDPOINT_KEY", "k")
    monkeypatch.setattr(remote_client, "_post", lambda *a, **k: pytest.fail("the Azure endpoint must not be called when the backend is local"))
    saved = []
    svc = _service(tmp_path, monkeypatch, saved)
    job = svc.store.create("37", None)
    svc.run_job(job["job_id"])
    done = svc.store.load(job["job_id"])
    assert done["status"] == "completed", (done.get("error"), done.get("warnings"))         # empty evidence_ids are expected for H1: no warning
    assert saved and saved[0][1]["extraction"]["symptoms"][0]["name"] == "fever"            # result goes to the extraction container
    args = json.loads((svc.store.dir(job["job_id"]) / "args.json").read_text(encoding="utf-8"))
    assert "--device" in args and args[args.index("--ram-gate-gib") + 1] == str(config.H1_MIN_AVAILABLE_RAM_GIB)


def test_azure_backend_without_endpoint_fails_clearly(tmp_path, monkeypatch):
    monkeypatch.setenv("EXTRACTION_BACKEND", "azure")
    monkeypatch.delenv("EXTRACTION_ENDPOINT_URL", raising=False)
    monkeypatch.delenv("EXTRACTION_ENDPOINT_KEY", raising=False)
    svc = _service(tmp_path, monkeypatch, [])
    job = svc.store.create("37", None)
    svc.run_job(job["job_id"])
    assert svc.store.load(job["job_id"])["error"]["code"] == "endpoint_not_configured"


def test_health_reports_local_model_and_setup_hint(tmp_path, monkeypatch):
    monkeypatch.delenv("EXTRACTION_BACKEND", raising=False)
    monkeypatch.setattr(service_module, "extraction_python", lambda: None)
    info = ExtractionService(store=JobStore(tmp_path)).health()
    assert info["backend"] == "local" and info["inference_location"] == "local_openvino"
    assert info["ready"] is False and "setup_local_model" in info["setup_hint"]


def test_azure_is_the_default_when_the_endpoint_is_configured_else_local(monkeypatch):
    monkeypatch.delenv("EXTRACTION_BACKEND", raising=False)
    monkeypatch.setenv("EXTRACTION_ENDPOINT_URL", "https://example.test/score")
    monkeypatch.setenv("EXTRACTION_ENDPOINT_KEY", "k")
    assert config.backend() == "azure"
    monkeypatch.delenv("EXTRACTION_ENDPOINT_KEY")
    assert config.backend() == "local"


def test_device_and_backend_settings(monkeypatch):
    monkeypatch.setenv("EXTRACTION_DEVICE", "cpu")
    assert config.device_setting() == "CPU"
    monkeypatch.setenv("EXTRACTION_DEVICE", "whatever")
    assert config.device_setting() == "AUTO"
    monkeypatch.setenv("EXTRACTION_BACKEND", "Azure")
    assert config.backend() == "azure"
    monkeypatch.setenv("EXTRACTION_BACKEND", "local")
    assert config.backend() == "local"
