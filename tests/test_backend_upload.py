import asyncio
import hashlib
from io import BytesIO

import pytest
from fastapi import HTTPException
from starlette.datastructures import UploadFile

from backend.app import main


def test_upload_stages_only_the_original_wav_and_returns_its_fingerprint(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "UPLOAD_DIR", tmp_path)
    recording = b"RIFF" + (4).to_bytes(4, "little") + b"WAVE" + b"audio-data"
    upload = UploadFile(filename="encounter.wav", file=BytesIO(recording))

    path, fingerprint = asyncio.run(main._save_upload(upload))

    assert path.read_bytes() == recording
    assert fingerprint == hashlib.sha256(recording).hexdigest()

    path.unlink()
    assert list(tmp_path.iterdir()) == []


def test_upload_rejects_non_wav_content_and_removes_temporary_file(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "UPLOAD_DIR", tmp_path)
    upload = UploadFile(filename="recording.wav", file=BytesIO(b"not-a-wave"))

    with pytest.raises(HTTPException) as error:
        asyncio.run(main._save_upload(upload))

    assert error.value.status_code == 415
    assert list(tmp_path.iterdir()) == []


def test_windows_client_path_is_reduced_to_a_display_filename():
    assert main._safe_filename(r"C:\private\recordings\visit.wav") == "visit.wav"


def test_health_reports_duplicate_stage_container_mapping(monkeypatch):
    for setting in main.REQUIRED_AZURE_SETTINGS:
        monkeypatch.setenv(setting, "configured")
    monkeypatch.setenv("AZURE_AUDIO_CONTAINER", "audio")
    monkeypatch.setenv("AZURE_TRANSCRIPT_CONTAINER", "transcripts")
    monkeypatch.setenv("AZURE_STORAGE_OUTPUT_CONTAINER", "transcripts")
    monkeypatch.setenv("AZURE_STORAGE_SLM_CONTAINER", "final")

    health = main.health()

    assert not health["azure_configured"]
    assert not health["container_mapping_valid"]
    assert health["configuration_issues"] == [
        "AZURE_TRANSCRIPT_CONTAINER and AZURE_STORAGE_OUTPUT_CONTAINER must refer to different Blob containers."
    ]


def test_health_reports_speech_provider_availability_independently(monkeypatch):
    for setting in main.REQUIRED_AZURE_SETTINGS:
        monkeypatch.setenv(setting, "configured")
    monkeypatch.setenv("AZURE_AUDIO_CONTAINER", "audio")
    monkeypatch.setenv("AZURE_TRANSCRIPT_CONTAINER", "transcripts")
    monkeypatch.setenv("AZURE_STORAGE_OUTPUT_CONTAINER", "reconstructions")
    monkeypatch.setenv("AZURE_STORAGE_SLM_CONTAINER", "final")
    monkeypatch.delenv("AZURE_SPEECH_ENDPOINT", raising=False)
    monkeypatch.delenv("AZURE_SPEECH_KEY", raising=False)
    monkeypatch.setenv("AZURE_FOUNDRY_SPEECH_ENDPOINT", "https://speech.example")
    monkeypatch.setenv("AZURE_FOUNDRY_SPEECH_KEY", "test-key")

    health = main.health()

    assert health["azure_configured"]
    assert not health["speech_providers"]["azure_speech"]["configured"]
    assert health["speech_providers"]["foundry_fast"]["configured"]


def test_upload_error_does_not_expose_internal_container_setting_names(monkeypatch):
    for setting in main.REQUIRED_AZURE_SETTINGS:
        monkeypatch.setenv(setting, "configured")
    monkeypatch.setenv("AZURE_AUDIO_CONTAINER", "audio")
    monkeypatch.setenv("AZURE_TRANSCRIPT_CONTAINER", "transcripts")
    monkeypatch.setenv("AZURE_STORAGE_OUTPUT_CONTAINER", "transcripts")
    monkeypatch.setenv("AZURE_STORAGE_SLM_CONTAINER", "final")
    upload = UploadFile(filename="encounter.wav", file=BytesIO(b"RIFF-audio"))

    with pytest.raises(HTTPException) as error:
        asyncio.run(main.start_pipeline(upload, "azure_speech"))

    assert error.value.status_code == 503
    assert "AZURE_STORAGE_OUTPUT_CONTAINER" not in error.value.detail
    assert "temporarily unavailable" in error.value.detail
