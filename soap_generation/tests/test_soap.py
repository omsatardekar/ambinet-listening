import json
import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from clinical_extraction.blob_source import SourceError
from soap_generation import api, config, guard, llm, prepare, render
from soap_generation.schema import NoteFormatError, normalise, parse_json
from soap_generation.service import SoapJobStore, SoapService, make_note

from .fixtures import BAD_DOC, good_note


@pytest.fixture(autouse=True)
def no_real_storage_reads(monkeypatch):
    """Tests never read the conversation from storage unless a test switches it on and supplies a fake reader."""
    monkeypatch.setattr(config, "INCLUDE_TRANSCRIPT", False)


def flags_by_ref():
    out = {}
    for f in prepare.build_input(BAD_DOC)["data_quality_flags"]:
        out.setdefault(f["ref"], []).append(f["issue"])
    return out


# ---- input preparation and rule flags ------------------------------------------------------------------------------------------------------
def test_input_has_refs_passages_and_no_bookkeeping():
    payload = prepare.build_input(BAD_DOC)
    assert payload["encounter"]["encounter_id"] == "03"
    sym = payload["extraction"]["symptoms"][0]
    assert sym["ref"] == "symptoms[0]" and sym["duration"] == "3 weeks" and "evidence_ids" not in sym
    assert payload["extraction"]["follow_up"][0]["ref"] == "follow_up"
    assert payload["source_passages"]["vital_signs[0]"][0]["speaker"] == "Physician"
    assert "quality_checks" not in payload["extraction"]


def test_known_extraction_mistakes_are_flagged():
    f = flags_by_ref()
    assert any("same phrase is also listed as a symptom" in i for i in f["negative_findings[0]"])           # polarity (F1)
    assert any("same name as a listed medicine" in i for i in f["allergies[0]"])                            # allergy = a medicine (F3)
    assert any("oxygen saturation" in i for i in f["vital_signs[1]"])                                       # unit (F18)
    assert any("does not look like a measurement" in i for i in f["vital_signs[2]"])                        # price as a vital (F24)
    assert any("same dose and frequency" in i for i in f["medications[0]"]) and "medications[3]" not in f   # copied values (F16)
    assert any("timestamp" in i for i in f["follow_up"])                                                    # 52.48s (F17)
    assert any("repeats a symptom" in i for i in f["clinical_assessment[0]"])                                  # assessment = symptom (F5)
    assert any("generic date uncertainty" in i for i in f["clinical_uncertainties[0]"])                     # (F11)
    assert any("no supporting passage" in i for i in f["medications[0]"])                                   # (F23)
    assert "medications[3]" not in f and "vital_signs[0]" not in f                                          # supported items are not flagged


# ---- parsing and normalising -----------------------------------------------------------------------------------------------------------------
def test_parse_accepts_fences_and_prose_but_not_garbage():
    note = json.dumps(good_note())
    assert parse_json("```json\n" + note + "\n```")["note_type"].startswith("Outpatient")
    assert parse_json("Here is the note:\n" + note + "\nDone.")["subjective"]
    for bad in ("", "no json here", "[1, 2]", "{not json}"):
        with pytest.raises(NoteFormatError):
            parse_json(bad)


def test_normalise_fills_defaults_and_fixes_allergy_status():
    raw = good_note()
    del raw["objective"]["diagnostics"]
    raw["subjective"]["allergies"] = {"status": "reported", "items": [], "comment": ""}
    raw["subjective"]["past_medical_history"] = "Heart disease"
    raw["assessment"]["problems"][0]["icd10_suggestion"] = {"code": "", "description": ""}
    note, issues = normalise(raw)
    assert note["objective"]["diagnostics"] == [] and note["subjective"]["past_medical_history"] == ["Heart disease"]
    assert note["subjective"]["allergies"]["status"] == "not_documented" and any("reset" in i for i in issues)
    assert note["assessment"]["problems"][0]["icd10_suggestion"] is None
    assert note["clinician_review"]["attestation"].startswith("Draft prepared")


def test_an_answer_that_is_not_a_note_is_rejected():
    with pytest.raises(NoteFormatError):
        normalise({"hello": "world"})


# ---- traceability guard and rendering --------------------------------------------------------------------------------------------------------
def test_guard_flags_only_untraceable_values():
    payload = prepare.build_input(BAD_DOC)
    note, _ = normalise(good_note())
    assert guard.check(note, payload) == []                                   # 119/74, 20 mg, 3 weeks all come from the input; "One nineteen over seventy-four" is read as 119/74
    note["objective"]["vital_signs"].append({"name": "Pulse", "value": "134", "unit": "bpm", "comment": ""})
    note["subjective"]["medications"].append({"name": "Warfarin", "dose": "", "route": "", "frequency": "", "status": "taking", "comment": ""})
    topics = [c["topic"] for c in guard.check(note, payload)]
    assert "Value '134'" in topics and "Medication 'Warfarin'" in topics


def test_a_long_turn_keeps_the_sentence_that_mentions_the_finding():
    long = "It's what I was afraid of. " + "Let me explain how the heart pumps and why the blood backs up into the lungs and the legs. " * 9 + "Then a chest x-ray, and some blood tests. And then we will see."
    assert len(long) > 650
    out = prepare.excerpt(long, {"chest", "x-ray"})
    assert "chest x-ray" in out and len(out) < 720 and out.startswith("[...]")
    assert prepare.excerpt("Short answer.", {"x"}) == "Short answer."


def test_guard_accepts_a_misspelt_drug_name():
    payload = {"extraction": {}, "source_passages": {"m": [{"speaker": "Patient", "time": "0:10", "text": "I take, uhh, the lysinopril. 10."}]}}
    note, _ = normalise(good_note())
    note["subjective"]["medications"] = [{"name": "Lisinopril", "dose": "10", "route": "", "frequency": "", "status": "taking", "comment": ""}]
    assert [c for c in guard.check(note, payload) if "Lisinopril" in c["topic"]] == []
    note["subjective"]["medications"][0]["name"] = "Warfarin"
    assert [c for c in guard.check(note, payload) if "Warfarin" in c["topic"]]


def test_render_prints_not_documented_for_empty_parts():
    note, _ = normalise(good_note())
    md = render.render(note, {"system_checks": [{"topic": "Value '9'", "reason": "check"}]})
    for part in ("## S: SUBJECTIVE", "## O: OBJECTIVE", "## A: ASSESSMENT", "## P: PLAN", "## CLINICIAN REVIEW"):
        assert part in md
    assert "Not documented" in md and "Value '9': check" in md and "119/74" in md and "R23.8" in md


# ---- whole transformation ---------------------------------------------------------------------------------------------------------------------
def test_make_note_repairs_one_bad_answer():
    answers = iter(["I cannot do that", json.dumps(good_note())])
    seen = []
    result = make_note(BAD_DOC, lambda payload, hint: (seen.append(hint), next(answers))[1])
    assert seen[0] is None and "no JSON" in seen[1]                           # the second request carries the reason
    assert result["note"]["encounter"]["encounter_id"] == "03" and "SOAP NOTE" in result["markdown"]


def test_make_note_gives_up_after_two_bad_answers():
    with pytest.raises(NoteFormatError):
        make_note(BAD_DOC, lambda payload, hint: "still not json")


def test_request_is_short_by_default_and_can_carry_the_instructions(monkeypatch):
    body = json.loads(llm.build_request({"extraction": {}}, "the answer is not valid JSON"))
    assert "soap_instructions" not in body and body["input"] == {"extraction": {}} and "could not be used" in body["correction"]        # the agent holds the prompt
    monkeypatch.setattr(config, "SEND_INSTRUCTIONS", True)
    assert "SOAP progress note" in json.loads(llm.build_request({}))["soap_instructions"]


# ---- service and API -------------------------------------------------------------------------------------------------------------------------
def make_service(tmp_path, source=None, generate=None, saver=None):
    saved = []
    service = SoapService(store=SoapJobStore(tmp_path), source=source or (lambda ref: (BAD_DOC, {"container": "c", "blob_name": "03extraction.json"})),
                          generate=generate or (lambda p, h: json.dumps(good_note())), saver=saver or (lambda ref, doc, md: saved.append((ref, doc, md)) or {"container": "soap-output", "blob_name": "03soap.json"}))
    service.saved = saved
    return service


def wait(service, job_id, timeout=20):
    end = time.time() + timeout
    while time.time() < end:
        job = service.store.load(job_id)
        if job["status"] in config.TERMINAL_STATES:
            return job
        time.sleep(0.05)
    raise AssertionError("job did not finish")


def test_service_runs_a_job_end_to_end(tmp_path):
    service = make_service(tmp_path)
    job = wait(service, service.submit(encounter_ref="03")["job_id"])
    assert job["status"] == "completed" and job["saved_to"]["blob_name"] == "03soap.json"
    ref, doc, md = service.saved[0]
    assert doc["document_type"] == "soap_note" and doc["note"]["subjective"]["chief_complaint"] and "## P: PLAN" in md
    assert [e["status"] for e in job["events"]] == ["queued", "reading_summary", "drafting_note", "checking_note", "saving", "completed"]


def test_missing_extraction_is_a_clear_failure(tmp_path):
    def source(ref):
        raise SourceError("extraction_not_found", "No clinical summary was found for this recording. Generate the clinical summary first.")
    service = make_service(tmp_path, source=source)
    job = wait(service, service.submit(encounter_ref="9")["job_id"])
    assert job["status"] == "failed" and job["error"]["code"] == "extraction_not_found" and "Generate the clinical summary" in job["error"]["message"]


def test_writer_failure_and_save_failure(tmp_path):
    def boom(p, h):
        raise llm.LlmError("model_call_failed", "The model endpoint did not answer.")
    s1 = make_service(tmp_path / "a", generate=boom)
    assert wait(s1, s1.submit(encounter_ref="03")["job_id"])["error"]["code"] == "model_call_failed"

    def cannot_save(ref, doc, md):
        raise SourceError("result_save_failed", "The note could not be saved to storage (X).")
    s2 = make_service(tmp_path / "b", saver=cannot_save)
    job = wait(s2, s2.submit(encounter_ref="03")["job_id"])
    assert job["status"] == "completed_with_warnings" and job["saved_to"] is None                     # the note is still available on screen


def test_the_whole_conversation_reaches_the_writer_and_a_read_failure_is_reported(tmp_path, monkeypatch):
    from clinical_extraction import blob_source
    monkeypatch.setattr(config, "INCLUDE_TRANSCRIPT", True)
    seen = []
    monkeypatch.setattr(blob_source, "fetch_compact", lambda ref: ({"segments": [{"role": "DOCTOR", "start_seconds": 5, "text": "We will do an X-ray."}]}, {}))
    service = make_service(tmp_path / "a", generate=lambda p, h: (seen.append(p), json.dumps(good_note()))[1])
    job = wait(service, service.submit(encounter_ref="03")["job_id"])
    assert seen[0]["conversation"] == [{"speaker": "Physician", "time": "0:05", "text": "We will do an X-ray."}] and job["status"] == "completed"

    def unreadable(ref):
        raise SourceError("transcript_not_found", "missing")
    monkeypatch.setattr(blob_source, "fetch_compact", unreadable)
    s2 = make_service(tmp_path / "b")
    job = wait(s2, s2.submit(encounter_ref="03")["job_id"])
    assert job["status"] == "completed_with_warnings" and any("conversation could not be read" in w for w in job["warnings"])


def test_api_flow(tmp_path):
    service = make_service(tmp_path)
    app = FastAPI()
    app.include_router(api.build_router(service))
    client = TestClient(app)
    r = client.post("/api/soap/start", json={"encounter_id": "03"})
    assert r.status_code == 202
    job_id = r.json()["job_id"]
    wait(service, job_id)
    assert client.get(f"/api/soap/{job_id}/status").json()["status"] == "completed"
    body = client.get(f"/api/soap/{job_id}/result").json()
    assert body["note"]["assessment"]["problems"][0]["problem"] == "Easy bruising" and "## A: ASSESSMENT" in body["markdown"] and "generation" not in json.dumps(body)
    assert client.get("/api/soap/health").json()["prompt_version"] == config.PROMPT_VERSION
    assert client.post("/api/soap/start", json={}).status_code == 422
    assert client.get("/api/soap/doesnotexist/status").status_code == 404


def test_agent_mode_needs_a_version_and_says_so(monkeypatch):
    monkeypatch.setenv("FOUNDRY_PROJECT_ENDPOINT", "https://example.invalid/api/projects/x")
    monkeypatch.setenv("SOAP_AGENT_NAME", "clinical-soap-note")
    monkeypatch.delenv("SOAP_AGENT_VERSION", raising=False)
    assert config.agent_configured() and not config.agent_ready()
    with pytest.raises(llm.LlmError) as err:
        llm.call_agent("{}")
    assert err.value.code == "agent_version_missing" and "create_soap_agent.py" in err.value.message
    monkeypatch.setenv("SOAP_AGENT_VERSION", "1")
    assert config.agent_ready()


def test_env_update_changes_only_its_own_lines(tmp_path, monkeypatch):
    import importlib.util
    import dotenv
    monkeypatch.setattr(dotenv, "load_dotenv", lambda *args, **kwargs: False)       # the script loads .env when imported: never the real one in a test
    spec = importlib.util.spec_from_file_location("create_soap_agent", config.ROOT / "scripts" / "create_soap_agent.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    env = tmp_path / ".env"
    env.write_text("A=1\n# SOAP_AGENT_VERSION=old comment\nSOAP_AGENT_NAME=x\nSECRET=keep\n", encoding="utf-8")
    mod._set_env(env, {"SOAP_AGENT_NAME": "clinical-soap-note", "SOAP_AGENT_VERSION": "3"})
    assert env.read_text(encoding="utf-8").splitlines() == ["A=1", "# SOAP_AGENT_VERSION=old comment", "SOAP_AGENT_NAME=clinical-soap-note", "SECRET=keep", "SOAP_AGENT_VERSION=3"]
