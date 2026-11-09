from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import re
import sys
import threading
import time
import wave
from pathlib import Path
from typing import Any

from azure.storage.blob import ContentSettings
from dotenv import load_dotenv

from .progress import PIPELINE_STAGES, ProgressManager


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
load_dotenv(PROJECT_ROOT / ".env")

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import process_transcripts as transcript_processing  # noqa: E402
import transcribe_blob_recordings as speech_pipeline  # noqa: E402
import transcribe_foundry_fast as fast_speech_pipeline  # noqa: E402
import prepare_slm_input as slm_preparation  # noqa: E402


logger = logging.getLogger("ambient_demo.pipeline")
_blob_allocation_lock = threading.Lock()
_JSON_CONTENT = ContentSettings(content_type="application/json; charset=utf-8")
_AUDIO_CONTENT = ContentSettings(content_type="audio/wav")
WEB_SPEECH_POLL_INTERVAL_SECONDS = 10


def _audio_seconds(path: Path) -> float:
    """Length of the recording, used to size the progress estimate for external waits."""
    try:
        with wave.open(str(path), "rb") as reader:
            return reader.getnframes() / float(reader.getframerate() or 16000)
    except (OSError, EOFError, wave.Error):
        try:
            return path.stat().st_size / 32000.0
        except OSError:
            return 60.0


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, "").strip() or default)
    except ValueError:
        return default


class _EstimatedProgress:
    """Keeps the progress bar moving while a slow external service works.

    The speech service and the model do not report a percentage, so while we wait the
    bar advances smoothly from ``start`` towards ``end`` along an easing curve sized by
    ``expected_seconds``. It never reaches ``end`` on its own (the real completion of the
    step moves it on), so it cannot claim more progress than has actually happened.
    """

    def __init__(
        self,
        progress: ProgressManager,
        run_id: str,
        stage: str,
        message: str,
        operation: str,
        start: int,
        end: int,
        expected_seconds: float,
        interval: float = 1.0,
    ) -> None:
        self._progress = progress
        self._run_id = run_id
        self._stage = stage
        self.message = message
        self._operation = operation
        self._start = start
        self._end = end
        self._expected = max(5.0, expected_seconds)
        self._interval = interval
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._last = start

    def __enter__(self) -> "_EstimatedProgress":
        self._began = time.monotonic()
        self._thread = threading.Thread(target=self._run, name="progress-estimate", daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *_exc: Any) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5)

    def _run(self) -> None:
        span = self._end - self._start
        while not self._stop.wait(self._interval):
            elapsed = time.monotonic() - self._began
            percent = self._start + int(span * (1 - math.exp(-elapsed / self._expected)))
            percent = min(self._end - 1, percent)
            if percent <= self._last:
                continue
            self._last = percent
            try:
                self._progress.update(
                    self._run_id,
                    self._stage,
                    "in_progress",
                    self.message,
                    percent,
                    operation=self._operation,
                    stage_status="in_progress",
                )
            except Exception:  # progress is cosmetic; never break the pipeline
                logger.debug("Could not publish estimated progress", exc_info=True)


def audio_fingerprint(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as audio_file:
        for chunk in iter(lambda: audio_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_pipeline(
    run_id: str,
    filename: str,
    fingerprint: str,
    upload_path: Path,
    progress: ProgressManager,
    speech_provider: str = "azure_speech",
) -> None:
    current_stage = "audio_upload"
    audio_blob = None
    process_service = None

    try:
        progress.update(
            run_id,
            "audio_upload",
            "in_progress",
            f"Preparing {filename}.",
            1,
            operation="Preparing your recording",
            stage_status="in_progress",
        )
        storage_config = speech_pipeline.get_storage_config()
        speech_config = (
            speech_pipeline.get_transcription_config()
            if speech_provider == "azure_speech"
            else fast_speech_pipeline.get_config()
        )
        speech_config.update(storage_config)

        process_config = transcript_processing.get_settings()
        required_containers = {
            "Audio recording": speech_config["input"],
            "Speech transcript": speech_config["output"],
            "Final transcript": process_config["output_container"],
            "SLM input": process_config["slm_container"],
        }
        if len({name.casefold() for name in required_containers.values()}) != len(required_containers):
            raise RuntimeError("Audio, transcript, final transcript, and SLM containers must be distinct.")

        audio_container, transcript_container = speech_pipeline.build_storage_clients(
            speech_config
        )
        process_service, _, output_container, slm_container = (
            transcript_processing.make_clients(process_config)
        )

        progress.update(
            run_id,
            "audio_upload",
            "in_progress",
            "Connecting to secure storage.",
            2,
            operation="Connecting to secure storage",
            stage_status="in_progress",
        )
        _require_container(audio_container, required_containers["Audio recording"])
        _require_container(transcript_container, required_containers["Speech transcript"])
        _require_container(output_container, required_containers["Final transcript"])
        _require_container(slm_container, required_containers["SLM input"])

        progress.update(
            run_id,
            "audio_upload",
            "in_progress",
            f"Checking {filename} before upload.",
            4,
            operation="Checking for earlier copies",
            stage_status="in_progress",
        )

        with _blob_allocation_lock:
            prior_audio = _find_matching_audio(
                audio_container,
                fingerprint,
                speech_provider,
            )
            if prior_audio is not None:
                audio_blob = audio_container.get_blob_client(prior_audio.name)
                _remove_upload(upload_path)
                existing_status = (prior_audio.metadata or {}).get("pipeline_status", "")
                number = _recording_number(prior_audio.name)
                if number is None:
                    raise RuntimeError("A matching uploaded recording has an invalid blob name.")
                final_name = process_config["output_pattern"].format(number=number)
                existing_final = output_container.get_blob_client(final_name)
                if existing_final.exists():
                    final_result = _read_json(existing_final)
                    _upload_slm_outputs(
                        slm_container,
                        number,
                        process_config["slm_pattern"],
                        final_result,
                    )
                    for stage, label in PIPELINE_STAGES:
                        progress.update(
                            run_id,
                            stage,
                            "completed",
                            f"Existing completed output found. {label} was not re-submitted.",
                            _stage_completion_percent(stage),
                            operation="Reusing existing Blob output",
                            stage_status="completed",
                        )
                    progress.complete(run_id, final_result)
                    return
                legacy_final = slm_container.get_blob_client(final_name)
                if legacy_final.exists():
                    final_result = _read_json(legacy_final)
                    compact, manifest = slm_preparation.prepare_compact_transcript(
                        final_result
                    )
                    slm_preparation.upload_json(
                        output_container,
                        final_name,
                        final_result,
                        overwrite=False,
                    )
                    slm_preparation.upload_json(
                        slm_container,
                        process_config["slm_pattern"].format(number=number),
                        compact,
                        overwrite=True,
                    )
                    slm_preparation.upload_json(
                        slm_container,
                        slm_preparation.make_manifest_filename(number),
                        manifest,
                        overwrite=True,
                    )
                    for stage, label in PIPELINE_STAGES:
                        progress.update(
                            run_id,
                            stage,
                            "completed",
                            f"Existing completed output found. {label} was not re-submitted.",
                            _stage_completion_percent(stage),
                            operation="Migrating and reusing existing Blob output",
                            stage_status="completed",
                        )
                    progress.complete(run_id, final_result)
                    return
                raise RuntimeError(
                    "This recording already has a prior pipeline run without a final "
                    f"transcript (status: {existing_status or 'unknown'}). Automatic "
                    "resubmission is disabled to prevent duplicate processing requests."
                )

            number = _next_recording_number(
                audio_container,
                transcript_container,
                output_container,
                slm_container,
                process_config["reconstruction_pattern"],
                process_config["output_pattern"],
                process_config["slm_pattern"],
            )
            audio_name = f"{number:02d}audio.wav"
            audio_blob = audio_container.get_blob_client(audio_name)
            metadata = {
                "source_sha256": fingerprint,
                "pipeline_run_id": run_id,
                "pipeline_status": "processing",
                "speech_provider": speech_provider,
            }
            audio_size = upload_path.stat().st_size
            progress.update(
                run_id,
                "audio_upload",
                "in_progress",
                f"Uploading {filename}.",
                6,
                operation="Uploading audio",
                stage_status="in_progress",
            )

            def audio_upload_progress(current: int, total: int | None) -> None:
                effective_total = total or audio_size
                fraction = min(1.0, current / effective_total) if effective_total else 1.0
                percent = min(15, 6 + int(fraction * 9))
                progress.update(
                    run_id,
                    "audio_upload",
                    "in_progress",
                    f"Uploading {filename}.",
                    percent,
                    operation=f"Uploading audio ({current:,} of {total:,} bytes)",
                    stage_status="in_progress",
                )

            with upload_path.open("rb") as audio_file:
                audio_blob.upload_blob(
                    audio_file,
                    overwrite=False,
                    metadata=metadata,
                    content_settings=_AUDIO_CONTENT,
                    progress_hook=audio_upload_progress,
                    max_concurrency=2,
                    timeout=120,
                )

        progress.update(
            run_id,
            "audio_upload",
            "completed",
            f"{filename} successfully uploaded as {audio_name}.",
            15,
            operation="Recording uploaded",
            stage_status="completed",
        )

        transcript_name = f"{number:02d}transcript.json"
        transcript_blob = transcript_container.get_blob_client(transcript_name)
        current_stage = "speech_transcription"

        if transcript_blob.exists():
            transcript = _read_json(transcript_blob)
            progress.update(
                run_id,
                current_stage,
                "completed",
                "Existing transcript reused.",
                55,
                operation="Reusing existing speech transcript",
                stage_status="completed",
            )
        else:
            progress.update(
                run_id,
                current_stage,
                "in_progress",
                "Recording received. Starting transcription.",
                17,
                operation="Starting transcription",
                stage_status="in_progress",
            )
            audio_seconds = _audio_seconds(upload_path)

            if speech_provider == "foundry_fast":
                progress.update(
                    run_id,
                    current_stage,
                    "in_progress",
                    "Sending the recording to Foundry Fast Transcription.",
                    20,
                    operation="Transcribing with Foundry Fast Transcription",
                    stage_status="in_progress",
                )
                with _EstimatedProgress(
                    progress,
                    run_id,
                    current_stage,
                    "Transcribing the conversation.",
                    "Transcribing with Foundry Fast Transcription",
                    start=20,
                    end=40,
                    expected_seconds=max(15.0, audio_seconds * _env_float("PROGRESS_FAST_SPEECH_FACTOR", 0.25)),
                ):
                    raw_speech_result = fast_speech_pipeline.transcribe_file(
                        upload_path,
                        speech_config,
                    )
                transcript = fast_speech_pipeline.normalize_result(
                    raw_speech_result,
                    audio_name,
                    max_speakers=int(speech_config.get("max_speakers", 4)),
                )
            else:
                progress.update(
                    run_id,
                    current_stage,
                    "in_progress",
                    "Securing access to the recording.",
                    18,
                    operation="Preparing transcription",
                    stage_status="in_progress",
                )
                sas = speech_pipeline.create_input_sas(speech_config)
                headers = {"Ocp-Apim-Subscription-Key": speech_config["speech_key"]}
                job_url = speech_pipeline.submit_transcription(
                    speech_config,
                    audio_name,
                    sas,
                    headers,
                )
                job_id = speech_pipeline.get_job_id(job_url)
                progress.update(
                    run_id,
                    current_stage,
                    "in_progress",
                    "Transcription started. Waiting for the service to finish.",
                    20,
                    operation="Transcribing with Azure Speech",
                    stage_status="in_progress",
                )

                with _EstimatedProgress(
                    progress,
                    run_id,
                    current_stage,
                    "Transcribing the conversation.",
                    "Transcribing with Azure Speech",
                    start=20,
                    end=38,
                    expected_seconds=max(45.0, audio_seconds * _env_float("PROGRESS_BATCH_SPEECH_FACTOR", 0.5)),
                ) as estimate:

                    def speech_status(status: str) -> None:
                        estimate.message = f"Transcribing the conversation (service status: {status})."

                    speech_pipeline.wait_for_job(
                        job_url,
                        job_id,
                        headers,
                        on_status=speech_status,
                        poll_interval_seconds=WEB_SPEECH_POLL_INTERVAL_SECONDS,
                    )
                progress.update(
                    run_id,
                    current_stage,
                    "in_progress",
                    "Transcription complete. Preparing the conversation text.",
                    40,
                    operation="Retrieving transcription result",
                    stage_status="in_progress",
                )
                raw_speech_result = speech_pipeline.download_transcription_result(
                    job_url,
                    headers,
                )
                transcript = speech_pipeline.normalize_result(
                    raw_speech_result,
                    audio_name,
                    job_id,
                )
            progress.update(
                run_id,
                current_stage,
                "in_progress",
                "Transcription complete. Preparing the conversation text.",
                40,
                operation="Preparing transcription output",
                stage_status="in_progress",
            )
            transcript_payload = json.dumps(
                transcript,
                ensure_ascii=False,
                indent=2,
            ).encode("utf-8")

            def transcript_upload_progress(current: int, total: int | None) -> None:
                effective_total = total or len(transcript_payload)
                fraction = min(1.0, current / effective_total) if effective_total else 1.0
                percent = 42 + int(fraction * 13)
                progress.update(
                    run_id,
                    current_stage,
                    "in_progress",
                    "Saving the transcript.",
                    percent,
                    operation=f"Uploading transcript ({current:,} of {total:,} bytes)",
                    stage_status="in_progress",
                )

            transcript_blob.upload_blob(
                transcript_payload,
                overwrite=False,
                content_settings=_JSON_CONTENT,
                progress_hook=transcript_upload_progress,
            )
            progress.update(
                run_id,
                current_stage,
                "completed",
                "Transcript JSON uploaded successfully.",
                55,
                operation="Transcript JSON uploaded successfully",
                stage_status="completed",
            )

        _set_pipeline_status(audio_blob, "speech_completed")
        current_stage = "llm_reconstruction"
        progress.update(
            run_id,
            current_stage,
            "in_progress",
            "Reading the transcript.",
            55,
            operation="Reading the transcript",
            stage_status="in_progress",
        )
        transcript = _read_json(transcript_blob)
        reconstruction_name = process_config["reconstruction_pattern"].format(number=number)
        reconstruction_blob = output_container.get_blob_client(reconstruction_name)

        if reconstruction_blob.exists():
            agent_result = _read_json(reconstruction_blob)
            progress.update(
                run_id,
                current_stage,
                "completed",
                "Existing conversation draft reused.",
                80,
                operation="Reusing existing reconstruction",
                stage_status="completed",
            )
        else:
            progress.update(
                run_id,
                current_stage,
                "in_progress",
                "Preparing conversation analysis.",
                57,
                operation="Preparing conversation analysis",
                stage_status="in_progress",
            )
            agent = transcript_processing.FoundryAgent(
                endpoint=process_config["foundry_endpoint"],
                api_key=process_config["foundry_key"],
                model=process_config["model"],
                agent_name=process_config["agent_name"],
                api_version=process_config["api_version"],
                timeout=process_config["timeout"],
                max_output_tokens=process_config["max_output_tokens"],
                max_retries=process_config["max_retries"],
                retry_base_seconds=process_config["retry_base"],
            )
            instructions = transcript_processing.load_instructions(
                transcript_processing.AGENT_PROMPT_PATH
            )
            agent.ensure_agent(instructions)
            progress.update(
                run_id,
                current_stage,
                "in_progress",
                "Organizing speakers and conversation context.",
                60,
                operation="Reconstructing clinical conversation",
                stage_status="in_progress",
            )
            encounter = transcript_processing.compact_encounter(
                transcript,
                transcript_name,
            )
            segment_count = len(transcript.get("segments") or [])
            with _EstimatedProgress(
                progress,
                run_id,
                current_stage,
                "Organizing speakers and conversation context.",
                "Reconstructing clinical conversation",
                start=60,
                end=70,
                expected_seconds=_env_float("PROGRESS_LLM_BASE_SECONDS", 30.0)
                + segment_count * _env_float("PROGRESS_LLM_SECONDS_PER_SEGMENT", 1.0),
            ):
                agent_result = agent.reconstruct(encounter, instructions)
            progress.update(
                run_id,
                current_stage,
                "in_progress",
                "Conversation structure complete. Saving the draft.",
                70,
                operation="Saving the conversation draft",
                stage_status="in_progress",
            )
            reconstruction_payload = json.dumps(
                agent_result,
                ensure_ascii=False,
                indent=2,
            ).encode("utf-8")

            def reconstruction_upload_progress(current: int, total: int | None) -> None:
                effective_total = total or len(reconstruction_payload)
                fraction = min(1.0, current / effective_total) if effective_total else 1.0
                percent = 70 + int(fraction * 10)
                progress.update(
                    run_id,
                    current_stage,
                    "in_progress",
                    "Saving the conversation draft.",
                    percent,
                    operation=f"Uploading reconstruction ({current:,} of {total:,} bytes)",
                    stage_status="in_progress",
                )

            reconstruction_blob.upload_blob(
                reconstruction_payload,
                overwrite=False,
                content_settings=_JSON_CONTENT,
                progress_hook=reconstruction_upload_progress,
            )
            progress.update(
                run_id,
                current_stage,
                "completed",
                "Structured JSON uploaded successfully.",
                80,
                operation="Structured JSON uploaded successfully",
                stage_status="completed",
            )

        _set_pipeline_status(audio_blob, "reconstruction_completed")
        current_stage = "final_transcript"
        progress.update(
            run_id,
            current_stage,
            "in_progress",
            "Checking the conversation draft.",
            80,
            operation="Validating reconstructed transcript",
            stage_status="in_progress",
        )
        agent_result = _read_json(reconstruction_blob)
        final_result = transcript_processing.validate_and_finalize(
            agent_result,
            transcript,
            transcript_name,
        )
        final_name = process_config["output_pattern"].format(number=number)
        final_blob = output_container.get_blob_client(final_name)

        if final_blob.exists():
            final_result = _read_json(final_blob)
            progress.update(
                run_id,
                current_stage,
                "completed",
                "Existing review-ready draft reused.",
                94,
                operation="Reusing existing final transcript",
                stage_status="completed",
            )
        else:
            progress.update(
                run_id,
                current_stage,
                "in_progress",
                "Draft checked. Saving the review-ready transcript.",
                88,
                operation="Uploading final transcript",
                stage_status="in_progress",
            )
            final_payload = json.dumps(
                final_result,
                ensure_ascii=False,
                indent=2,
            ).encode("utf-8")

            def final_upload_progress(current: int, total: int | None) -> None:
                effective_total = total or len(final_payload)
                fraction = min(1.0, current / effective_total) if effective_total else 1.0
                percent = min(99, 88 + int(fraction * 12))
                progress.update(
                    run_id,
                    current_stage,
                    "in_progress",
                    "Saving the review-ready transcript.",
                    min(percent, 95),
                    operation=f"Uploading final transcript ({current:,} of {total:,} bytes)",
                    stage_status="in_progress",
                )

            final_blob.upload_blob(
                final_payload,
                overwrite=False,
                content_settings=_JSON_CONTENT,
                progress_hook=final_upload_progress,
            )

        _upload_slm_outputs(
            slm_container,
            number,
            process_config["slm_pattern"],
            final_result,
        )
        progress.update(
            run_id,
            current_stage,
            "completed",
            "Final transcript and compact SLM input uploaded successfully.",
            100,
            operation="Final transcript and SLM input uploaded successfully",
            stage_status="completed",
        )

        try:
            _set_pipeline_status(audio_blob, "complete")
        except Exception as exc:
            logger.warning(
                "Could not record completed status metadata for run %s (%s)",
                run_id,
                type(exc).__name__,
            )
        progress.complete(run_id, final_result)
    except Exception as exc:
        safe_detail = _safe_exception_detail(exc)
        logger.error(
            "Pipeline run %s failed during %s (%s): %s",
            run_id,
            current_stage,
            type(exc).__name__,
            safe_detail,
        )
        if audio_blob is not None and current_stage != "audio_upload":
            try:
                _set_pipeline_status(audio_blob, "failed")
            except Exception as metadata_error:
                logger.error(
                    "Could not record failure metadata for run %s (%s)",
                    run_id,
                    type(metadata_error).__name__,
                )
        progress.fail(
            run_id,
            current_stage,
            f"{_stage_label(current_stage)} could not be completed. Check the service logs or contact your administrator.",
        )
    finally:
        _remove_upload(upload_path)
        if process_service is not None:
            try:
                process_service.close()
            except Exception as exc:
                logger.warning(
                    "Could not close the Blob client after run %s (%s)",
                    run_id,
                    type(exc).__name__,
                )


def _required_setting(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required .env setting: {name}")
    return value


def _upload_slm_outputs(
    container: Any,
    number: int,
    slm_pattern: str,
    final_result: dict[str, Any],
) -> None:
    compact, manifest = slm_preparation.prepare_compact_transcript(final_result)
    slm_preparation.upload_json(
        container,
        slm_pattern.format(number=number),
        compact,
        overwrite=True,
    )
    slm_preparation.upload_json(
        container,
        slm_preparation.make_manifest_filename(number),
        manifest,
        overwrite=True,
    )


def _get_speech_config() -> dict[str, Any]:
    return speech_pipeline.get_config()


def _require_container(container: Any, label: str) -> None:
    if not container.exists():
        raise RuntimeError(f"Required Azure Blob container is unavailable: {label}.")


def _find_matching_audio(
    container: Any,
    fingerprint: str,
    speech_provider: str,
) -> Any | None:
    for blob in container.list_blobs(include=["metadata"]):
        metadata = blob.metadata or {}
        existing_provider = metadata.get("speech_provider", "azure_speech")
        if (
            metadata.get("source_sha256") == fingerprint
            and existing_provider == speech_provider
        ):
            return blob
    return None


def _next_recording_number(
    audio_container: Any,
    transcript_container: Any,
    output_container: Any,
    slm_container: Any,
    reconstruction_pattern: str,
    output_pattern: str,
    slm_pattern: str,
) -> int:
    first_reconstruction = reconstruction_pattern.format(number=1)
    second_reconstruction = reconstruction_pattern.format(number=2)
    if first_reconstruction == second_reconstruction:
        raise RuntimeError("RECONSTRUCTION_FILE_PATTERN must include a unique {number} value.")

    first_final = output_pattern.format(number=1)
    second_final = output_pattern.format(number=2)
    if first_final == second_final:
        raise RuntimeError("OUTPUT_FILE_PATTERN must include a unique {number} value.")

    first_slm = slm_pattern.format(number=1)
    second_slm = slm_pattern.format(number=2)
    if first_slm == second_slm:
        raise RuntimeError("SLM_FILE_SUFFIX must produce a unique filename per encounter.")
    if first_slm == slm_preparation.make_manifest_filename(1):
        raise RuntimeError("SLM input and manifest file patterns must differ.")

    existing_audio = {blob.name for blob in audio_container.list_blobs()}
    existing_transcripts = {blob.name for blob in transcript_container.list_blobs()}
    existing_output = {blob.name for blob in output_container.list_blobs()}
    existing_slm = {blob.name for blob in slm_container.list_blobs()}
    if reconstruction_pattern.format(number=1) == output_pattern.format(number=1):
        raise RuntimeError("Reconstruction and final transcript file patterns must differ.")

    for number in range(1, 1_000_000):
        if (
            f"{number:02d}audio.wav" not in existing_audio
            and f"{number:02d}transcript.json" not in existing_transcripts
            and reconstruction_pattern.format(number=number) not in existing_output
            and output_pattern.format(number=number) not in existing_output
            and output_pattern.format(number=number) not in existing_slm
            and slm_pattern.format(number=number) not in existing_slm
            and slm_preparation.make_manifest_filename(number) not in existing_slm
        ):
            return number
    raise RuntimeError("No unused encounter number is available in the configured containers.")


def _recording_number(blob_name: str) -> int | None:
    match = re.fullmatch(r"(\d+)audio\.wav", blob_name, flags=re.IGNORECASE)
    return int(match.group(1)) if match else None


def _read_json(blob: Any) -> dict[str, Any]:
    value = json.loads(blob.download_blob().readall().decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Blob {blob.blob_name!r} must contain a JSON object.")
    return value


def _set_pipeline_status(audio_blob: Any, status: str) -> None:
    properties = audio_blob.get_blob_properties()
    metadata = dict(properties.metadata or {})
    metadata["pipeline_status"] = status
    audio_blob.set_blob_metadata(metadata=metadata)


def _remove_upload(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError as exc:
        logger.warning("Could not remove uploaded audio temporary file (%s)", type(exc).__name__)


def _stage_completion_percent(stage: str) -> int:
    return {
        "audio_upload": 15,
        "speech_transcription": 55,
        "llm_reconstruction": 80,
        "final_transcript": 100,
    }[stage]


def _stage_label(stage: str) -> str:
    return dict((key, label) for key, label in PIPELINE_STAGES).get(stage, "Pipeline")


def _safe_exception_detail(exc: Exception) -> str:
    detail = str(exc).split("; response=", 1)[0].strip()
    for setting in (
        "AZURE_STORAGE_ACCOUNT_KEY",
        "AZURE_SPEECH_KEY",
        "FOUNDRY_API_KEY",
    ):
        secret = os.getenv(setting, "")
        if secret:
            detail = detail.replace(secret, "[redacted]")
    detail = re.sub(r"(?i)([?&](?:sig|se|sp|sv|sr)=)[^&\s]+", r"\1[redacted]", detail)
    detail = re.sub(r"https?://\S+\?[^\s]+", "[signed URL redacted]", detail)
    return detail[:500] or "Check backend logs for details."
