"""Unit tests (no model, no Azure). Uses the synthetic development encounter 00037 as a read-only fixture.
Run from the repository root with the backend venv:  .venv\\Scripts\\python -m pytest clinical_extraction/tests -q
"""
import copy
import json
import sys
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from clinical_extraction import evidence, service as service_module                      # noqa: E402
from clinical_extraction.compact import CompactTranscriptError, validate_compact          # noqa: E402
from clinical_extraction.job_store import JobStore                                        # noqa: E402
from clinical_extraction.service import ExtractionService                                 # noqa: E402

COMPACT = ROOT / "dataset_v2_batch_001_corrected" / "output" / "inputs" / "encounter_00037.json"
REFERENCE = ROOT / "direct_inference_1_7B" / "experiments" / "EXP_002_PROMPTING_INFERENCE" / "outputs" / "parsed" / "P02" / "encounter_00037.json"
pytestmark = pytest.mark.skipif(not (COMPACT.exists() and REFERENCE.exists()), reason="fixture files missing")


@pytest.fixture()
def compact():
    return json.loads(COMPACT.read_text(encoding="utf-8"))


@pytest.fixture()
def reference():
    return json.loads(REFERENCE.read_text(encoding="utf-8"))


def test_compact_valid(compact):
    assert validate_compact(compact) == []


@pytest.mark.parametrize("mutate,msg", [
    (lambda c: c.pop("segments"), "missing key"),
    (lambda c: c["segments"].__setitem__(0, {**c["segments"][0], "segment_id": "SEG1"}), "invalid segment_id"),
    (lambda c: c["segments"].__setitem__(1, {**c["segments"][1], "segment_id": "SEG0001"}), "duplicate"),
    (lambda c: c["segments"][0].pop("role"), "missing"),
    (lambda c: c["segments"][0].__setitem__("text", "  "), "empty text"),
])
def test_compact_rejects(compact, mutate, msg):
    bad = copy.deepcopy(compact)
    mutate(bad)
    with pytest.raises(CompactTranscriptError, match=msg):
        validate_compact(bad)


def test_resolver_real_reference_flags_invalid_ids_and_never_corrects(compact, reference):
    before = json.dumps(reference, sort_keys=True)
    derived = evidence.resolve_all(reference, compact)
    assert json.dumps(reference, sort_keys=True) == before                     # raw output untouched
    bad = [s for f in derived["facts"] for s in f["segments"] if s["status"] == "invalid_format"]
    assert {s["segment_id"] for s in bad} == {"SEG007", "SEG008"}              # 3-digit ids are flagged, not turned into SEG0007 / SEG0008
    assert all("text" not in s for s in bad)                                   # nothing is guessed for them
    assert derived["totals"]["invalid_format"] == len(bad) > 0
    assert derived["label"] == "Model-cited transcript segments"
    assert any(f["path"] == "chief_complaint" for f in derived["facts"])
    assert any(f["path"].startswith("medical_history.family_history[") for f in derived["facts"])
    big = [f for f in derived["facts"] if any(x["kind"] == "unusually_large_evidence_list" for x in f["flags"])]
    assert big                                                                  # chief complaint cites 26 segments


def test_resolved_segment_uses_original_transcript_data(compact):
    seg = compact["segments"][52]                                              # SEG0053
    fact = {"evidence_ids": ["SEG0053"]}
    out = evidence.resolve_fact(fact, {s["segment_id"]: s for s in compact["segments"]})
    r = out["segments"][0]
    assert r["status"] == "resolved" and r["text"] == seg["text"] and r["role"] == seg["role"]
    assert (r["start_seconds"], r["end_seconds"], r["speaker_id"]) == (seg["start_seconds"], seg["end_seconds"], seg["speaker_id"])
    assert out["flags"] == []


@pytest.mark.parametrize("ids,kinds", [
    ([], ["empty_evidence_list"]),
    (["SEG0001", "SEG0001"], ["duplicate_reference"]),
    (["SEG9999"], ["segment_not_found"]),
    (["seg0001"], ["invalid_segment_id"]),
    (["SEG00001"], ["invalid_segment_id"]),
    ([f"SEG{i:04d}" for i in range(1, 9)], ["unusually_large_evidence_list"]),
])
def test_resolver_flags(compact, ids, kinds):
    out = evidence.resolve_fact({"evidence_ids": ids}, {s["segment_id"]: s for s in compact["segments"]})
    assert sorted({f["kind"] for f in out["flags"]}) == sorted(kinds)
    assert len(out["segments"]) == len(ids)                                    # nothing silently dropped


def test_evidence_for_path(compact, reference):
    derived = evidence.resolve_all(reference, compact)
    one = evidence.evidence_for_path(derived, "symptoms[0]")
    assert one and one["segments"] and one["label"] == "Model-cited transcript segments"
    assert evidence.evidence_for_path(derived, "symptoms[99]") is None


def test_job_store_persists_and_marks_interrupted(tmp_path):
    store = JobStore(tmp_path)
    job = store.create("37", None)
    store.set_state(job, "extracting", "working")
    assert (tmp_path / ".gitignore").read_text().startswith("*")
    again = JobStore(tmp_path)                                                 # simulated backend restart
    assert again.load(job["job_id"])["status"] == "extracting"
    assert again.mark_interrupted() == 1
    reloaded = again.load(job["job_id"])
    assert reloaded["status"] == "failed" and reloaded["error"]["code"] == "interrupted"
    assert again.load("../../etc") is None


STUB = textwrap.dedent('''
    import json, sys
    from pathlib import Path
    a = sys.argv
    out = Path(a[a.index("--out") + 1])
    ref = json.loads(Path(sys.argv[0]).with_name("reference.json").read_text(encoding="utf-8"))
    for e in ("preparing", "reading_transcript", "loading_model", "extracting", "validating_output"):
        print(json.dumps({"event": e, "message": e}), flush=True)
    (out / "extraction_raw.json").write_text(json.dumps(ref), encoding="utf-8")
    (out / "result.json").write_text(json.dumps({"ok": True, "metadata": {"parse_status": "ok", "finish_reason": "stop", "schema_validation": {"compliant": False, "violation_counts": {"missing_field": 1}}}}), encoding="utf-8")
''')


def _service(tmp_path, monkeypatch, compact, reference, stub=True):
    if stub:
        (tmp_path / "reference.json").write_text(json.dumps(reference), encoding="utf-8")
        (tmp_path / "stub_worker.py").write_text(STUB, encoding="utf-8")
        monkeypatch.setattr(service_module, "WORKER", tmp_path / "stub_worker.py")
        monkeypatch.setenv("EXTRACTION_PYTHON", sys.executable)
    return ExtractionService(store=JobStore(tmp_path / "data"), source=lambda ref: (compact, {"kind": "local"}))


def test_job_state_machine_and_separate_outputs(tmp_path, monkeypatch, compact, reference):
    svc = _service(tmp_path, monkeypatch, compact, reference)
    job = svc.store.create("37", None)
    svc.run_job(job["job_id"])
    final = svc.store.load(job["job_id"])
    states = [e["status"] for e in final["events"]]
    assert states[:2] == ["queued", "preparing_transcript"]
    assert [s for s in states if s in ("loading_model", "extracting", "validating_output", "resolving_evidence")] == ["loading_model", "extracting", "validating_output", "resolving_evidence"]
    assert final["status"] == "completed_with_warnings"                         # invalid ids + schema violations => warnings, never a plain success
    assert any("invalid_format" in w for w in final["warnings"]) and any("schema validation" in w for w in final["warnings"])
    d = svc.store.dir(job["job_id"])
    assert json.loads((d / "extraction_raw.json").read_text(encoding="utf-8")) == reference       # raw output kept exactly
    assert (d / "evidence.json").exists() and (d / "metadata.json").exists() and (d / "input_compact.json").exists()
    assert json.loads((d / "input_compact.json").read_text(encoding="utf-8")) == compact           # same segments, same order, same text


def test_failure_is_not_reported_as_success(tmp_path, monkeypatch, compact, reference):
    svc = _service(tmp_path, monkeypatch, compact, reference, stub=False)
    monkeypatch.delenv("EXTRACTION_PYTHON", raising=False)
    monkeypatch.setattr(service_module, "extraction_python", lambda: None)                  # no environment on this machine (auto-discovery would find one here)
    job = svc.store.create("37", None)
    svc.run_job(job["job_id"])
    final = svc.store.load(job["job_id"])
    assert final["status"] == "failed" and final["error"]["code"] == "extraction_environment_missing"
    assert not (svc.store.dir(job["job_id"]) / "extraction_raw.json").exists()


def test_bad_source_fails_cleanly(tmp_path, monkeypatch, compact, reference):
    def bad_source(_ref):
        raise service_module.blob_source.SourceError("transcript_not_found", "none")
    svc = ExtractionService(store=JobStore(tmp_path / "data"), source=bad_source)
    job = svc.store.create("99", None)
    svc.run_job(job["job_id"])
    assert svc.store.load(job["job_id"])["error"]["code"] == "transcript_not_found"


def test_api_routes(tmp_path, monkeypatch, compact, reference):
    pytest.importorskip("fastapi")
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from clinical_extraction.api import build_router
    svc = _service(tmp_path, monkeypatch, compact, reference)
    app = FastAPI()
    app.include_router(build_router(svc))
    client = TestClient(app)
    job = svc.store.create("37", None)
    svc.run_job(job["job_id"])
    jid = job["job_id"]
    assert client.get(f"/api/extraction/{jid}/status").json()["status"] == "completed_with_warnings"
    res = client.get(f"/api/extraction/{jid}/result").json()
    assert res["extraction"] == reference and "metadata" in res and "clinician review" in res["notice"]
    ev = client.get(f"/api/extraction/{jid}/evidence", params={"path": "symptoms[0]"}).json()
    assert ev["label"] == "Model-cited transcript segments"
    assert client.get(f"/api/extraction/{jid}/evidence", params={"path": "nope[0]"}).status_code == 404
    assert client.get("/api/extraction/doesnotexist/status").status_code == 404
    assert client.get("/api/extraction/health").status_code == 200
    assert client.post("/api/extraction/start", json={}).status_code == 422
