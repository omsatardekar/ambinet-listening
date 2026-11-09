from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


def need(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing {name} in .env")
    return value


def get_config() -> dict[str, str | int]:
    endpoint = need("AZURE_FOUNDRY_SPEECH_ENDPOINT").rstrip("/")
    parsed = urlparse(endpoint)
    if parsed.scheme != "https" or not parsed.netloc:
        raise RuntimeError(
            "AZURE_FOUNDRY_SPEECH_ENDPOINT must be a full HTTPS resource URL."
        )

    max_speakers = int(os.getenv("SPEECH_MAX_SPEAKERS", "4"))
    if max_speakers < 1:
        raise RuntimeError("SPEECH_MAX_SPEAKERS must be at least 1.")

    return {
        "endpoint": endpoint,
        "speech_key": need("AZURE_FOUNDRY_SPEECH_KEY"),
        "api_version": os.getenv(
            "FOUNDRY_SPEECH_API_VERSION",
            "2025-10-15",
        ).strip() or "2025-10-15",
        "locale": os.getenv("SPEECH_LOCALE", "en-IN").strip() or "en-IN",
        "max_speakers": max_speakers,
        "timeout_seconds": int(
            os.getenv("FOUNDRY_SPEECH_TIMEOUT_SECONDS", "900")
        ),
    }


def transcribe_file(audio_path: Path, config: dict[str, str | int]) -> dict:
    definition = {
        "locales": [str(config["locale"])],
        "diarization": {
            "enabled": True,
            "maxSpeakers": int(config["max_speakers"]),
        },
    }
    url = (
        f"{str(config['endpoint']).rstrip('/')}"
        "/speechtotext/transcriptions:transcribe"
    )
    try:
        with audio_path.open("rb") as audio_file:
            response = requests.post(
                url,
                params={"api-version": config["api_version"]},
                headers={
                    "Ocp-Apim-Subscription-Key": str(config["speech_key"]),
                    "Accept": "application/json",
                },
                data={"definition": json.dumps(definition)},
                files={"audio": (audio_path.name, audio_file, "audio/wav")},
                timeout=int(config["timeout_seconds"]),
            )
    except requests.RequestException as exc:
        raise RuntimeError(
            f"Foundry Fast Transcription request failed ({type(exc).__name__})."
        ) from exc

    if not response.ok:
        detail = response.text.strip()[:1200]
        raise RuntimeError(
            "Foundry Fast Transcription failed "
            f"(HTTP {response.status_code}): {detail or 'No service details provided.'}"
        )
    try:
        result = response.json()
    except ValueError as exc:
        raise RuntimeError(
            "Foundry Fast Transcription returned invalid JSON."
        ) from exc
    if not isinstance(result, dict):
        raise RuntimeError(
            "Foundry Fast Transcription response must be a JSON object."
        )
    return result


def normalize_result(raw: dict, blob_name: str, max_speakers: int | None = None) -> dict:
    segments = []
    transcript_parts = []
    phrases = raw.get("phrases")
    if not isinstance(phrases, list):
        raise ValueError("Foundry Fast Transcription response has no phrases array.")

    for phrase in phrases:
        if not isinstance(phrase, dict):
            continue
        text = str(phrase.get("text") or "").strip()
        if not text:
            continue
        start_ms = _number(phrase.get("offsetMilliseconds"))
        duration_ms = _number(phrase.get("durationMilliseconds"))
        segments.append({
            "speaker_id": _speaker_name(phrase.get("speaker")),
            "start_seconds": start_ms / 1000 if start_ms is not None else None,
            "duration_seconds": duration_ms / 1000 if duration_ms is not None else None,
            "text": text,
        })
        transcript_parts.append(text)

    if not segments:
        raise ValueError(
            "Foundry Fast Transcription completed without any recognized phrases."
        )

    duration_ms = _number(raw.get("durationMilliseconds"))
    recording_id = re.sub(r"audio\.wav$", "", blob_name, flags=re.IGNORECASE)
    return {
        "schema_version": "1.1",
        "recording_id": recording_id,
        "source_blob": blob_name,
        "speech_job_id": None,
        "processed_at_utc": datetime.now(timezone.utc).isoformat(),
        "max_speakers_requested": max_speakers,
        "duration_seconds": duration_ms / 1000 if duration_ms is not None else None,
        "transcript": " ".join(transcript_parts),
        "segments": segments,
    }


def _number(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _speaker_name(value: object) -> str | None:
    if value is None or not str(value).strip():
        return None
    speaker = str(value).strip().lower()
    if re.fullmatch(r"speaker_\d+", speaker):
        return speaker
    match = re.fullmatch(r"speaker[_ ]?(\d+)", speaker)
    if match:
        return f"speaker_{match.group(1)}"
    return f"speaker_{speaker}"
