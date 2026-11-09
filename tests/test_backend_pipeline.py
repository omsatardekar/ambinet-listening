import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from backend.app import pipeline
from backend.app.progress import ProgressManager


class FakeDownloader:
    def __init__(self, value):
        self.value = value

    def readall(self):
        return self.value


class FakeBlob:
    def __init__(self, container, name):
        self.container = container
        self.blob_name = name
        self.metadata = {}

    def exists(self):
        return self.blob_name in self.container.objects

    def upload_blob(self, data, metadata=None, progress_hook=None, **_kwargs):
        payload = data.read() if hasattr(data, "read") else data
        self.container.objects[self.blob_name] = payload
        if metadata is not None:
            self.metadata = dict(metadata)
        if progress_hook is not None:
            progress_hook(len(payload), len(payload))

    def download_blob(self):
        return FakeDownloader(self.container.objects[self.blob_name])

    def get_blob_properties(self):
        return SimpleNamespace(metadata=self.metadata)

    def set_blob_metadata(self, metadata):
        self.metadata = dict(metadata)


class FakeContainer:
    def __init__(self, name):
        self.container_name = name
        self.objects = {}
        self.blobs = {}

    def exists(self):
        return True

    def get_blob_client(self, name):
        if name not in self.blobs:
            self.blobs[name] = FakeBlob(self, name)
        return self.blobs[name]

    def list_blobs(self, **_kwargs):
        return [
            SimpleNamespace(name=name, metadata=self.get_blob_client(name).metadata)
            for name in self.objects
        ]


class FakeService:
    def close(self):
        pass


def test_same_audio_is_reused_only_for_the_same_speech_provider():
    audio_container = FakeContainer("audio")
    blob = audio_container.get_blob_client("01audio.wav")
    blob.upload_blob(
        b"audio",
        metadata={
            "source_sha256": "same-fingerprint",
            "speech_provider": "azure_speech",
        },
    )

    assert pipeline._find_matching_audio(
        audio_container,
        "same-fingerprint",
        "azure_speech",
    ).name == "01audio.wav"
    assert pipeline._find_matching_audio(
        audio_container,
        "same-fingerprint",
        "foundry_fast",
    ) is None


def test_next_recording_number_avoids_existing_slm_payloads():
    audio_container = FakeContainer("audio")
    transcript_container = FakeContainer("speech")
    output_container = FakeContainer("final")
    slm_container = FakeContainer("slm")
    slm_container.objects["01slm_input.json"] = b"{}"

    number = pipeline._next_recording_number(
        audio_container,
        transcript_container,
        output_container,
        slm_container,
        "{number:02d}reconstruction.json",
        "{number:02d}final_transcript.json",
        "{number:02d}slm_input.json",
    )

    assert number == 2


def test_pipeline_migrates_legacy_final_from_slm_container(
    tmp_path: Path,
    monkeypatch,
):
    audio_container = FakeContainer("audio")
    transcript_container = FakeContainer("speech")
    output_container = FakeContainer("final")
    slm_container = FakeContainer("slm")
    upload = tmp_path / "source.wav"
    upload.write_bytes(b"existing-audio")
    fingerprint = pipeline.audio_fingerprint(upload)

    audio_blob = audio_container.get_blob_client("01audio.wav")
    audio_blob.upload_blob(
        b"existing-audio",
        metadata={
            "source_sha256": fingerprint,
            "speech_provider": "azure_speech",
            "pipeline_status": "complete",
        },
    )
    legacy_final = {
        "schema_version": "1.0",
        "encounter_id": "01",
        "processing_status": "COMPLETE",
        "review_flags": [],
        "utterances": [
            {
                "canonical_speaker_id": "person_1",
                "role": "DOCTOR",
                "start_seconds": 0.0,
                "end_seconds": 1.0,
                "duration_seconds": 1.0,
                "text": "Let us review the symptoms.",
            },
        ],
    }
    slm_container.get_blob_client("01final_transcript.json").upload_blob(
        json.dumps(legacy_final).encode("utf-8")
    )

    monkeypatch.setattr(
        pipeline.speech_pipeline,
        "get_storage_config",
        lambda: {
            "input": "audio",
            "output": "speech",
            "account": "storage",
            "key": "storage-key",
        },
    )
    monkeypatch.setattr(
        pipeline.speech_pipeline,
        "get_transcription_config",
        lambda: {"endpoint": "https://speech.example", "speech_key": "test-key"},
    )
    monkeypatch.setattr(
        pipeline.speech_pipeline,
        "build_storage_clients",
        lambda _cfg: (audio_container, transcript_container),
    )
    monkeypatch.setattr(
        pipeline.transcript_processing,
        "get_settings",
        lambda: {
            "output_container": "final",
            "slm_container": "slm",
            "reconstruction_pattern": "{number:02d}reconstruction.json",
            "output_pattern": "{number:02d}final_transcript.json",
            "slm_pattern": "{number:02d}slm_input.json",
        },
    )
    monkeypatch.setattr(
        pipeline.transcript_processing,
        "make_clients",
        lambda _cfg: (
            FakeService(),
            transcript_container,
            output_container,
            slm_container,
        ),
    )

    progress = ProgressManager()
    run_id, _ = progress.create("source.wav", fingerprint)
    pipeline.run_pipeline(
        run_id,
        "source.wav",
        fingerprint,
        upload,
        progress,
        "azure_speech",
    )

    assert json.loads(
        output_container.objects["01final_transcript.json"]
    ) == legacy_final
    slm_input = json.loads(slm_container.objects["01slm_input.json"])
    assert slm_input["segments"][0]["role"] == "DOCTOR"
    assert progress.status(run_id)["status"] == "completed"


@pytest.mark.parametrize("speech_provider", ["azure_speech", "foundry_fast"])
def test_pipeline_runs_selected_speech_provider_and_uploads_each_artifact(
    tmp_path: Path,
    monkeypatch,
    speech_provider: str,
):
    audio_container = FakeContainer("audio")
    transcript_container = FakeContainer("speech")
    output_container = FakeContainer("final")
    slm_container = FakeContainer("slm")
    order = []

    monkeypatch.setenv("AZURE_AUDIO_CONTAINER", "audio")
    monkeypatch.setenv("AZURE_TRANSCRIPT_CONTAINER", "speech")
    monkeypatch.setattr(
        pipeline.speech_pipeline,
        "get_storage_config",
        lambda: {
            "account": "storage",
            "key": "storage-key",
            "input": "audio",
            "output": "speech",
            "locale": "en-IN",
            "max_speakers": 4,
        },
    )
    monkeypatch.setattr(
        pipeline.speech_pipeline,
        "get_transcription_config",
        lambda: {
            "endpoint": "https://speech.example",
            "speech_key": "test-speech-key",
        },
    )
    monkeypatch.setattr(
        pipeline.speech_pipeline,
        "get_config",
        lambda: {
            "input": "audio",
            "output": "speech",
            "speech_key": "test-speech-key",
        },
    )
    monkeypatch.setattr(
        pipeline.speech_pipeline,
        "build_storage_clients",
        lambda _cfg: (audio_container, transcript_container),
    )
    monkeypatch.setattr(
        pipeline.speech_pipeline,
        "create_input_sas",
        lambda _cfg: "sas",
    )
    monkeypatch.setattr(
        pipeline.speech_pipeline,
        "submit_transcription",
        lambda *_args: order.append("speech:submitted") or "https://speech/jobs/job-1",
    )
    monkeypatch.setattr(
        pipeline.speech_pipeline,
        "get_job_id",
        lambda _url: "job-1",
    )

    def wait_for_job(_url, _job_id, _headers, on_status=None, poll_interval_seconds=None):
        order.append("speech:polling")
        order.append(f"speech:poll-interval:{poll_interval_seconds}")
        on_status("Running")
        on_status("Succeeded")
        order.append("speech:succeeded")

    monkeypatch.setattr(pipeline.speech_pipeline, "wait_for_job", wait_for_job)
    monkeypatch.setattr(
        pipeline.speech_pipeline,
        "download_transcription_result",
        lambda *_args: {"result": "speech"},
    )
    speech_json = {
        "schema_version": "1.1",
        "recording_id": "01",
        "source_blob": "01audio.wav",
        "segments": [{"speaker_id": "speaker_1", "start_seconds": 1.0, "duration_seconds": 2.0, "text": "Hello."}],
        "transcript": "Hello.",
    }
    monkeypatch.setattr(
        pipeline.speech_pipeline,
        "normalize_result",
        lambda *_args: speech_json,
    )
    if speech_provider == "foundry_fast":
        monkeypatch.setattr(
            pipeline.fast_speech_pipeline,
            "get_config",
            lambda: {
                "endpoint": "https://foundry-speech.example",
                "speech_key": "test-fast-key",
                "api_version": "2025-10-15",
                "locale": "en-IN",
                "max_speakers": 4,
                "timeout_seconds": 900,
            },
        )
        monkeypatch.setattr(
            pipeline.fast_speech_pipeline,
            "transcribe_file",
            lambda *_args: order.append("fast:transcribed") or {"phrases": []},
        )
        monkeypatch.setattr(
            pipeline.fast_speech_pipeline,
            "normalize_result",
            lambda *_args: order.append("fast:normalized") or speech_json,
        )
    monkeypatch.setattr(
        pipeline.transcript_processing,
        "get_settings",
        lambda: {
            "audio_container": "audio",
            "input_container": "speech",
            "output_container": "final",
            "slm_container": "slm",
            "reconstruction_pattern": "{number:02d}reconstruction.json",
            "output_pattern": "{number:02d}final_transcript.json",
            "slm_pattern": "{number:02d}slm_input.json",
            "foundry_endpoint": "https://foundry.example",
            "foundry_key": "test-key",
            "model": "deployment",
            "agent_name": "agent",
            "api_version": "v1",
            "timeout": 1,
            "max_output_tokens": 24000,
            "max_retries": 0,
            "retry_base": 0,
        },
    )
    monkeypatch.setattr(
        pipeline.transcript_processing,
        "make_clients",
        lambda _cfg: (
            FakeService(),
            transcript_container,
            output_container,
            slm_container,
        ),
    )
    monkeypatch.setattr(
        pipeline.transcript_processing,
        "load_instructions",
        lambda _path: "existing instructions",
    )
    monkeypatch.setattr(
        pipeline.transcript_processing,
        "compact_encounter",
        lambda raw, blob_name: order.append("foundry:input") or {"raw": raw, "name": blob_name},
    )

    agent_json = {"speaker_registry": [], "utterances": [], "foundry_response_id": "response"}

    class FakeAgent:
        def __init__(self, **_kwargs):
            pass

        def ensure_agent(self, _instructions):
            order.append("foundry:agent")

        def reconstruct(self, _encounter, _instructions):
            order.append("foundry:request")
            return agent_json

    final_json = {
        "schema_version": "1.0",
        "encounter_id": "01",
        "processing_status": "NEEDS_REVIEW",
        "speaker_registry": [],
        "utterances": [
            {
                "canonical_speaker_id": "person_1",
                "role": "DOCTOR",
                "start_seconds": 0.0,
                "end_seconds": 1.0,
                "duration_seconds": 1.0,
                "text": "What brings you in today?",
            },
            {
                "canonical_speaker_id": "person_2",
                "role": "NURSE",
                "start_seconds": 1.1,
                "end_seconds": 2.0,
                "duration_seconds": 0.9,
                "text": "I recorded the observation.",
            },
        ],
        "review_flags": [{"type": "TEST"}],
    }
    monkeypatch.setattr(pipeline.transcript_processing, "FoundryAgent", FakeAgent)
    monkeypatch.setattr(
        pipeline.transcript_processing,
        "validate_and_finalize",
        lambda agent, raw, name: order.append("final:validated") or final_json,
    )

    upload = tmp_path / "source.wav"
    upload.write_bytes(b"RIFF-audio-bytes")
    fingerprint = pipeline.audio_fingerprint(upload)
    progress = ProgressManager()
    run_id, _ = progress.create("source.wav", fingerprint)

    pipeline.run_pipeline(
        run_id,
        "source.wav",
        fingerprint,
        upload,
        progress,
        speech_provider,
    )

    assert not upload.exists()
    assert json.loads(transcript_container.objects["01transcript.json"]) == speech_json
    assert json.loads(output_container.objects["01reconstruction.json"]) == agent_json
    assert json.loads(output_container.objects["01final_transcript.json"]) == final_json
    slm_input = json.loads(slm_container.objects["01slm_input.json"])
    assert slm_input == {
        "schema_version": "1.0",
        "encounter_id": "01",
        "segments": [
            {
                "segment_id": "SEG0001",
                "speaker_id": "person_1",
                "role": "DOCTOR",
                "start_seconds": 0.0,
                "end_seconds": 1.0,
                "duration_seconds": 1.0,
                "text": "What brings you in today?",
            },
            {
                "segment_id": "SEG0002",
                "speaker_id": "person_2",
                "role": "NURSE",
                "start_seconds": 1.1,
                "end_seconds": 2.0,
                "duration_seconds": 0.9,
                "text": "I recorded the observation.",
            },
        ],
    }
    if speech_provider == "azure_speech":
        assert order.index("speech:submitted") < order.index("speech:succeeded")
        assert f"speech:poll-interval:{pipeline.WEB_SPEECH_POLL_INTERVAL_SECONDS}" in order
        assert order.index("speech:succeeded") < order.index("foundry:request")
    else:
        assert order.index("fast:transcribed") < order.index("fast:normalized")
        assert order.index("fast:normalized") < order.index("foundry:request")
    uploaded_audio = audio_container.get_blob_client("01audio.wav")
    assert uploaded_audio.metadata["speech_provider"] == speech_provider
    assert order.index("foundry:request") < order.index("final:validated")
    assert progress.status(run_id)["status"] == "completed"
    assert progress.status(run_id)["percent"] == 100


def test_process_settings_map_each_pipeline_stage_to_the_requested_container(monkeypatch):
    settings = {
        "AZURE_STORAGE_ACCOUNT_NAME": "storage",
        "AZURE_STORAGE_ACCOUNT_KEY": "test-key",
        "AZURE_AUDIO_CONTAINER": "audio",
        "AZURE_TRANSCRIPT_CONTAINER": "speech",
        "AZURE_STORAGE_OUTPUT_CONTAINER": "clinical-final-transcripts",
        "AZURE_STORAGE_SLM_CONTAINER": "slm",
        "FOUNDRY_PROJECT_ENDPOINT": "https://foundry.example",
        "FOUNDRY_API_KEY": "test-key",
        "FOUNDRY_MODEL_DEPLOYMENT_NAME": "deployment",
    }
    for name, value in settings.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setenv("SLM_FILE_SUFFIX", "slm_input.json")

    config = pipeline.transcript_processing.get_settings()

    assert config["audio_container"] == "audio"
    assert config["input_container"] == "speech"
    assert config["output_container"] == "clinical-final-transcripts"
    assert config["slm_container"] == "slm"
    assert config["slm_pattern"] == "{number:02d}slm_input.json"


def test_process_settings_reject_duplicate_pipeline_containers(monkeypatch):
    settings = {
        "AZURE_STORAGE_ACCOUNT_NAME": "storage",
        "AZURE_STORAGE_ACCOUNT_KEY": "test-key",
        "AZURE_AUDIO_CONTAINER": "audio",
        "AZURE_TRANSCRIPT_CONTAINER": "speech",
        "AZURE_STORAGE_OUTPUT_CONTAINER": "speech",
        "AZURE_STORAGE_SLM_CONTAINER": "slm",
        "FOUNDRY_PROJECT_ENDPOINT": "https://foundry.example",
        "FOUNDRY_API_KEY": "test-key",
        "FOUNDRY_MODEL_DEPLOYMENT_NAME": "deployment",
    }
    for name, value in settings.items():
        monkeypatch.setenv(name, value)

    try:
        pipeline.transcript_processing.get_settings()
    except RuntimeError as error:
        assert "must be distinct" in str(error)
    else:
        raise AssertionError("Duplicate pipeline containers should be rejected.")
