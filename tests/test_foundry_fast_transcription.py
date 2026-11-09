import json

import pytest
import requests

from scripts import transcribe_foundry_fast as fast_transcription


def test_fast_transcription_sends_diarization_request(tmp_path, monkeypatch):
    audio_path = tmp_path / "01audio.wav"
    audio_path.write_bytes(b"wav-data")
    config = {
        "endpoint": "https://speech.example/",
        "speech_key": "test-key",
        "api_version": "2025-10-15",
        "locale": "en-IN",
        "max_speakers": 5,
        "timeout_seconds": 120,
    }
    response = type("Response", (), {"ok": True, "json": lambda self: {"phrases": []}})()
    request = {}

    def fake_post(url, **kwargs):
        request.update(url=url, **kwargs)
        request["audio_bytes"] = kwargs["files"]["audio"][1].read()
        return response

    monkeypatch.setattr(fast_transcription.requests, "post", fake_post)

    assert fast_transcription.transcribe_file(audio_path, config) == {"phrases": []}

    assert request["url"] == (
        "https://speech.example/speechtotext/transcriptions:transcribe"
    )
    assert request["params"] == {"api-version": "2025-10-15"}
    assert request["headers"]["Ocp-Apim-Subscription-Key"] == "test-key"
    definition = json.loads(request["data"]["definition"])
    assert definition == {
        "locales": ["en-IN"],
        "diarization": {"enabled": True, "maxSpeakers": 5},
    }
    assert request["files"]["audio"][0] == "01audio.wav"
    assert request["files"]["audio"][2] == "audio/wav"
    assert request["audio_bytes"] == b"wav-data"
    assert request["timeout"] == 120


def test_fast_transcription_reports_service_errors_without_falling_back(
    tmp_path,
    monkeypatch,
):
    audio_path = tmp_path / "recording.wav"
    audio_path.write_bytes(b"wav-data")
    response = type(
        "Response",
        (),
        {
            "ok": False,
            "status_code": 429,
            "text": '{"error":"rate limited"}',
        },
    )()
    monkeypatch.setattr(
        fast_transcription.requests,
        "post",
        lambda *_args, **_kwargs: response,
    )

    with pytest.raises(RuntimeError, match=r"HTTP 429"):
        fast_transcription.transcribe_file(audio_path, {
            "endpoint": "https://speech.example",
            "speech_key": "test-key",
            "api_version": "2025-10-15",
            "locale": "en-IN",
            "max_speakers": 4,
            "timeout_seconds": 30,
        })


def test_fast_transcription_normalizes_phrase_times_and_speaker_ids():
    result = fast_transcription.normalize_result(
        {
            "durationMilliseconds": 3400,
            "phrases": [
                {
                    "offsetMilliseconds": 400,
                    "durationMilliseconds": 1250,
                    "speaker": "Speaker2",
                    "text": "Good morning.",
                },
                {
                    "offsetMilliseconds": 2000,
                    "durationMilliseconds": 900,
                    "speaker": 1,
                    "text": "Thank you.",
                },
            ],
        },
        "01audio.wav",
    )

    assert result == {
        "schema_version": "1.1",
        "recording_id": "01",
        "source_blob": "01audio.wav",
        "speech_job_id": None,
        "duration_seconds": 3.4,
        "transcript": "Good morning. Thank you.",
        "segments": [
            {
                "speaker_id": "speaker_2",
                "start_seconds": 0.4,
                "duration_seconds": 1.25,
                "text": "Good morning.",
            },
            {
                "speaker_id": "speaker_1",
                "start_seconds": 2.0,
                "duration_seconds": 0.9,
                "text": "Thank you.",
            },
        ],
    }


def test_fast_transcription_rejects_empty_or_malformed_phrases():
    with pytest.raises(ValueError, match="no phrases array"):
        fast_transcription.normalize_result({}, "01audio.wav")
    with pytest.raises(ValueError, match="without any recognized phrases"):
        fast_transcription.normalize_result({"phrases": []}, "01audio.wav")


def test_fast_transcription_request_errors_are_explicit(tmp_path, monkeypatch):
    audio_path = tmp_path / "recording.wav"
    audio_path.write_bytes(b"wav-data")

    def fail_request(*_args, **_kwargs):
        raise requests.Timeout()

    monkeypatch.setattr(fast_transcription.requests, "post", fail_request)

    with pytest.raises(RuntimeError, match="request failed \\(Timeout\\)"):
        fast_transcription.transcribe_file(audio_path, {
            "endpoint": "https://speech.example",
            "speech_key": "test-key",
            "api_version": "2025-10-15",
            "locale": "en-IN",
            "max_speakers": 4,
            "timeout_seconds": 30,
        })
