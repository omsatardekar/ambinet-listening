import argparse
import json
import os
import re
import sys
import time
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import (
    BlobServiceClient,
    ContainerSasPermissions,
    generate_container_sas,
)
from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parents[1] / ".env")

API_VERSION = os.getenv("SPEECH_API_VERSION", "2025-10-15")
# Batch transcription is asynchronous. Poll every 5 minutes by default.
POLL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "300"))
TIMEOUT_MINUTES = int(os.getenv("JOB_TIMEOUT_MINUTES", "360"))
SAS_HOURS = int(os.getenv("SAS_VALID_HOURS", "24"))


def need(name):
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing {name} in .env")
    return value


def get_storage_config():
    return {
        "account": need("AZURE_STORAGE_ACCOUNT_NAME"),
        "key": need("AZURE_STORAGE_ACCOUNT_KEY"),
        "input": need("AZURE_AUDIO_CONTAINER"),
        "output": need("AZURE_TRANSCRIPT_CONTAINER"),
        "locale": os.getenv("SPEECH_LOCALE", "en-IN").strip() or "en-IN",
        "max_speakers": int(os.getenv("SPEECH_MAX_SPEAKERS", "4")),
    }


def get_transcription_config():
    endpoint = need("AZURE_SPEECH_ENDPOINT").rstrip("/")
    parsed = urlparse(endpoint)

    if parsed.scheme != "https" or not parsed.netloc:
        raise RuntimeError(
            "AZURE_SPEECH_ENDPOINT must be a full HTTPS resource URL."
        )

    return {
        "endpoint": endpoint,
        "speech_key": need("AZURE_SPEECH_KEY"),
    }


def get_config():
    return {**get_storage_config(), **get_transcription_config()}


def duration_seconds(value):
    """Convert an ISO-8601 duration such as PT12M16.14S to seconds."""
    if not isinstance(value, str):
        return None

    match = re.fullmatch(
        r"PT(?:(\d+(?:\.\d+)?)H)?"
        r"(?:(\d+(?:\.\d+)?)M)?"
        r"(?:(\d+(?:\.\d+)?)S)?",
        value,
    )

    if not match:
        return None

    hours, minutes, seconds = (
        float(part or 0) for part in match.groups()
    )
    return hours * 3600 + minutes * 60 + seconds


def speaker_name(value):
    """Normalize Azure speaker numbers to speaker_1, speaker_2, etc."""
    if value is None:
        return None

    value = str(value)
    if value.lower().startswith("speaker_"):
        return value.lower()

    return f"speaker_{value}"


def normalize_result(raw, blob_name, job_id):
    """
    Convert the Azure Speech response into a compact JSON structure.

    Kept:
      - recording metadata
      - overall duration
      - full transcript text
      - phrase-level speaker ID, start, duration, and text

    Removed:
      - confidence
      - locale
      - recognition status
      - word-level details
      - complete raw Azure response
    """
    segments = []
    transcript_parts = []

    for phrase in raw.get("recognizedPhrases", []):
        candidates = phrase.get("nBest") or [{}]
        best = candidates[0] if candidates else {}

        phrase_text = (
            best.get("display")
            or best.get("lexical")
            or ""
        ).strip()

        # Ignore empty recognition entries; they do not add useful text.
        if not phrase_text:
            continue

        offset_ticks = phrase.get("offsetInTicks")
        duration_ticks = phrase.get("durationInTicks")

        start_seconds = (
            float(offset_ticks) / 10_000_000
            if offset_ticks is not None
            else duration_seconds(phrase.get("offset"))
        )

        segment_duration = (
            float(duration_ticks) / 10_000_000
            if duration_ticks is not None
            else duration_seconds(phrase.get("duration"))
        )

        segments.append({
            "speaker_id": speaker_name(phrase.get("speaker")),
            "start_seconds": start_seconds,
            "duration_seconds": segment_duration,
            "text": phrase_text,
        })

        transcript_parts.append(phrase_text)

    raw_duration = raw.get("duration")
    total_duration = (
        float(raw["durationMilliseconds"]) / 1000
        if raw.get("durationMilliseconds") is not None
        else duration_seconds(raw_duration)
    )

    return {
        "schema_version": "1.1",
        "recording_id": blob_name.replace("audio.wav", ""),
        "source_blob": blob_name,
        "speech_job_id": job_id,
        "processed_at_utc": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": total_duration,
        "transcript": " ".join(transcript_parts),
        "segments": segments,
    }


def build_storage_clients(cfg):
    connection_string = (
        "DefaultEndpointsProtocol=https;"
        f"AccountName={cfg['account']};"
        f"AccountKey={cfg['key']};"
        "EndpointSuffix=core.windows.net"
    )

    service = BlobServiceClient.from_connection_string(connection_string)

    input_container = service.get_container_client(cfg["input"])
    output_container = service.get_container_client(cfg["output"])

    return input_container, output_container


def ensure_containers(input_container, output_container, output_name):
    if not input_container.exists():
        raise RuntimeError(
            f"Input container missing or inaccessible: {input_container.container_name}"
        )

    if not output_container.exists():
        try:
            output_container.create_container()
            print(f"Created output container: {output_name}")
        except ResourceExistsError:
            print(f"Output container already exists: {output_name}")


def create_input_sas(cfg):
    """Create temporary read/list SAS. The Storage Account key stays local."""
    now = datetime.now(timezone.utc)

    return generate_container_sas(
        account_name=cfg["account"],
        container_name=cfg["input"],
        account_key=cfg["key"],
        permission=ContainerSasPermissions(read=True, list=True),
        start=now - timedelta(minutes=5),
        expiry=now + timedelta(hours=SAS_HOURS),
        protocol="https",
    )


def get_job_id(job_url):
    clean_url = job_url.split("?", 1)[0].rstrip("/")
    return clean_url.split("/")[-1]


def submit_transcription(cfg, blob_name, sas, headers):
    input_base_url = (
        f"https://{cfg['account']}.blob.core.windows.net/{cfg['input']}"
    )
    audio_url = f"{input_base_url}/{blob_name}?{sas}"

    submit_url = (
        f"{cfg['endpoint']}/speechtotext/transcriptions:submit"
        f"?api-version={API_VERSION}"
    )

    payload = {
        "displayName": (
            f"ambient-{blob_name}-"
            f"{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}"
        ),
        "locale": cfg["locale"],
        "contentUrls": [audio_url],
        "properties": {
            "diarization": {
                "enabled": True,
                "maxSpeakers": cfg["max_speakers"],
            },
            # We do not request word-level timestamps because this project
            # only needs phrase-level speaker IDs and phrase timestamps.
            "wordLevelTimestampsEnabled": False,
            "timeToLiveHours": 48,
            "punctuationMode": "DictatedAndAutomatic",
            "profanityFilterMode": "None",
        },
    }

    response = requests.post(
        submit_url,
        headers={**headers, "Content-Type": "application/json"},
        json=payload,
        timeout=90,
    )

    if not response.ok:
        raise RuntimeError(
            f"Speech submit HTTP {response.status_code}: {response.text[:1500]}"
        )

    job = response.json()
    job_url = job.get("self")

    if not job_url:
        raise RuntimeError(
            f"Speech submit response did not include job URL: {job}"
        )

    return job_url


def wait_for_job(
    job_url,
    job_id,
    headers,
    on_status: Callable[[str], None] | None = None,
    poll_interval_seconds: int | None = None,
):
    deadline = time.monotonic() + TIMEOUT_MINUTES * 60
    polling_interval = POLL_SECONDS if poll_interval_seconds is None else poll_interval_seconds

    while True:
        if time.monotonic() > deadline:
            raise TimeoutError(
                f"Timed out waiting for Speech job {job_id}. "
                "Check the job in Azure before submitting it again."
            )

        status_response = requests.get(
            job_url,
            headers=headers,
            timeout=60,
        )

        if not status_response.ok:
            raise RuntimeError(
                f"Status HTTP {status_response.status_code}: "
                f"{status_response.text[:1000]}"
            )

        status_body = status_response.json()
        status = status_body.get("status", "Unknown")

        print(f"  Job {job_id}: {status}")
        if on_status is not None:
            on_status(status)

        if status.lower() == "succeeded":
            return

        if status.lower() == "failed":
            raise RuntimeError(
                f"Speech job failed: {json.dumps(status_body)[:2000]}"
            )

        time.sleep(polling_interval)


def download_transcription_result(job_url, headers):
    """
    Azure's returned job URL may already contain an api-version query string.
    Remove it before appending /files to avoid the previous 404 URL issue.
    """
    clean_job_url = job_url.split("?", 1)[0].rstrip("/")
    files_url = f"{clean_job_url}/files?api-version={API_VERSION}"

    print("  Fetching transcription result files...")

    files_response = requests.get(
        files_url,
        headers=headers,
        timeout=60,
    )

    if not files_response.ok:
        raise RuntimeError(
            f"List files HTTP {files_response.status_code}: "
            f"{files_response.text[:1000]}"
        )

    result_files = [
        item
        for item in files_response.json().get("values", [])
        if item.get("kind") == "Transcription"
    ]

    if not result_files:
        raise RuntimeError(
            "Speech job succeeded but Azure returned no transcription result file."
        )

    content_url = result_files[0].get("links", {}).get("contentUrl")

    if not content_url:
        raise RuntimeError(
            "Azure transcription result file did not contain contentUrl."
        )

    result_response = requests.get(content_url, timeout=120)

    if not result_response.ok:
        raise RuntimeError(
            f"Download result HTTP {result_response.status_code}: "
            f"{result_response.text[:1000]}"
        )

    return result_response.json()


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Transcribe numbered WAV blobs with Azure AI Speech "
            "and save compact phrase-level diarization JSON."
        )
    )
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=50)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if args.start < 1 or args.end < args.start:
        parser.error("Use a valid positive --start and --end range.")

    cfg = get_config()
    input_container, output_container = build_storage_clients(cfg)

    ensure_containers(
        input_container,
        output_container,
        cfg["output"],
    )

    print(f"Input container : {cfg['input']}")
    print(f"Output container: {cfg['output']}")
    print(f"Speech endpoint : {cfg['endpoint']}")
    print(f"Locale          : {cfg['locale']}")
    print(f"Max speakers    : {cfg['max_speakers']}")
    print(f"Polling interval: {POLL_SECONDS} seconds")

    selected = []

    for number in range(args.start, args.end + 1):
        blob_name = f"{number:02d}audio.wav"

        if input_container.get_blob_client(blob_name).exists():
            selected.append((number, blob_name))
            print(f"FOUND {blob_name}")
        else:
            print(f"MISSING {blob_name}")

    print(f"\nFound {len(selected)} WAV file(s).")

    if args.check:
        return

    if not selected:
        raise RuntimeError(
            "No matching WAV files were found in the input container."
        )

    sas = create_input_sas(cfg)
    headers = {
        "Ocp-Apim-Subscription-Key": cfg["speech_key"]
    }

    uploaded = 0
    skipped = 0
    failures = []

    for index, (number, blob_name) in enumerate(selected, start=1):
        output_name = f"{number:02d}transcript.json"
        output_blob = output_container.get_blob_client(output_name)

        if output_blob.exists() and not args.overwrite:
            print(
                f"\n[{index}/{len(selected)}] "
                f"SKIP {output_name} (already exists)"
            )
            skipped += 1
            continue

        print(f"\n[{index}/{len(selected)}] Submit {blob_name}")

        try:
            job_url = submit_transcription(
                cfg,
                blob_name,
                sas,
                headers,
            )
            job_id = get_job_id(job_url)

            wait_for_job(
                job_url,
                job_id,
                headers,
            )

            raw_result = download_transcription_result(
                job_url,
                headers,
            )

            final_json = normalize_result(
                raw_result,
                blob_name,
                job_id,
            )

            output_blob.upload_blob(
                json.dumps(
                    final_json,
                    ensure_ascii=False,
                    indent=2,
                ).encode("utf-8"),
                overwrite=True,
                content_type="application/json",
            )

            print(
                f"  UPLOADED {output_name} "
                f"({len(final_json['segments'])} phrase segments)"
            )
            uploaded += 1

        except Exception as exc:
            print(f"  FAILED {blob_name}: {exc}")
            failures.append((blob_name, str(exc)))

    print("\n========== RUN SUMMARY ==========")
    print(f"Uploaded : {uploaded}")
    print(f"Skipped  : {skipped}")
    print(f"Failed   : {len(failures)}")

    if failures:
        print("\nFailures:")
        for name, error in failures:
            print(f"- {name}: {error}")

        sys.exit(1)

    print("\nTranscription batch completed successfully.")


if __name__ == "__main__":
    main()
