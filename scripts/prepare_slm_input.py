
"""
Stage 2: Prepare compact, validated transcripts for the fine-tuned SLM.

Input:
    Azure Blob container: AZURE_STORAGE_OUTPUT_CONTAINER
    Files: 01final_transcript.json, 02final_transcript.json, ...

Output:
    Azure Blob container: AZURE_STORAGE_SLM_CONTAINER
    Files: 01slm_input.json, 02slm_input.json, ...
    Review sidecars: 01slm_input.manifest.json, ...

The detailed Stage 1 files are never modified.
"""

import argparse
import json
import logging
import os
import re
import sys
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from azure.storage.blob import BlobServiceClient, ContentSettings
from dotenv import load_dotenv


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

STORAGE_ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT_NAME", "").strip()
STORAGE_ACCOUNT_KEY = os.getenv("AZURE_STORAGE_ACCOUNT_KEY", "").strip()

INPUT_CONTAINER = os.getenv("AZURE_STORAGE_OUTPUT_CONTAINER", "").strip()
OUTPUT_CONTAINER = os.getenv("AZURE_STORAGE_SLM_CONTAINER", "").strip()

INPUT_SUFFIX = os.getenv(
    "RECONSTRUCTED_FILE_SUFFIX",
    "final_transcript.json"
).strip()

OUTPUT_SUFFIX = os.getenv(
    "SLM_FILE_SUFFIX",
    "slm_input.json"
).strip() or "slm_input.json"

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

ALLOWED_ROLES = {
    "DOCTOR",
    "PATIENT",
    "NURSE",
    "CAREGIVER",
    "FAMILY_MEMBER",
    "PHARMACIST",
    "INTERPRETER",
    "OTHER_CLINICAL_STAFF",
    "ADMINISTRATIVE_STAFF",
    "OTHER",
    "UNKNOWN",
}

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("slm_input_preparation")


# ---------------------------------------------------------------------
# Azure Blob Storage
# ---------------------------------------------------------------------

def create_blob_service() -> BlobServiceClient:
    if not STORAGE_ACCOUNT_NAME or not STORAGE_ACCOUNT_KEY:
        raise RuntimeError(
            "Missing AZURE_STORAGE_ACCOUNT_NAME or "
            "AZURE_STORAGE_ACCOUNT_KEY in .env"
        )

    account_url = (
        f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net"
    )

    return BlobServiceClient(
        account_url=account_url,
        credential=STORAGE_ACCOUNT_KEY,
    )


def ensure_container(container_client) -> None:
    try:
        container_client.create_container()
        logger.info("Created output container: %s", OUTPUT_CONTAINER)
    except ResourceExistsError:
        logger.info("Output container already exists: %s", OUTPUT_CONTAINER)


# ---------------------------------------------------------------------
# Naming and selection
# ---------------------------------------------------------------------

def extract_recording_number(blob_name: str) -> int | None:
    """
    Extract the recording number from names such as:
        02final_transcript.json
        folder/02final_transcript.json
    """
    filename = blob_name.rsplit("/", 1)[-1]

    match = re.match(r"^(\d+)", filename)
    if not match:
        return None

    return int(match.group(1))


def make_output_filename(recording_number: int) -> str:
    return f"{recording_number:02d}{OUTPUT_SUFFIX}"


def make_manifest_filename(recording_number: int) -> str:
    return f"{recording_number:02d}slm_input.manifest.json"


# ---------------------------------------------------------------------
# JSON and data validation
# ---------------------------------------------------------------------

def require_non_empty_string(
    value: Any,
    field_name: str,
    segment_number: int,
) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"Segment {segment_number}: {field_name} must be "
            "a non-empty string."
        )

    return value.strip()


def require_number(
    value: Any,
    field_name: str,
    segment_number: int,
) -> float:
    if isinstance(value, bool) or value is None:
        raise ValueError(
            f"Segment {segment_number}: {field_name} must be numeric."
        )

    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(
            f"Segment {segment_number}: invalid {field_name} value."
        )

    if not number.is_finite():
        raise ValueError(
            f"Segment {segment_number}: {field_name} must be finite."
        )

    return float(number)


def round_seconds(value: float) -> float:
    return round(value, 3)


def prepare_compact_transcript(
    source: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Convert the detailed Stage 1 reconstruction into the compact
    Stage 2 schema.

    Original utterance text and boundaries are preserved.
    """

    if not isinstance(source, dict):
        raise ValueError("Input JSON root must be an object.")

    encounter_id = require_non_empty_string(
        source.get("encounter_id"),
        "encounter_id",
        0,
    )

    utterances = source.get("utterances")

    if not isinstance(utterances, list) or not utterances:
        raise ValueError(
            "Input must contain a non-empty 'utterances' array."
        )

    compact_segments = []
    previous_start = -1.0

    for index, utterance in enumerate(utterances, start=1):
        if not isinstance(utterance, dict):
            raise ValueError(
                f"Utterance {index} must be a JSON object."
            )

        speaker_id = require_non_empty_string(
            utterance.get("canonical_speaker_id"),
            "canonical_speaker_id",
            index,
        )

        role = require_non_empty_string(
            utterance.get("role"),
            "role",
            index,
        ).upper()

        if role not in ALLOWED_ROLES:
            raise ValueError(
                f"Utterance {index}: unsupported role '{role}'."
            )

        start = require_number(
            utterance.get("start_seconds"),
            "start_seconds",
            index,
        )

        end = require_number(
            utterance.get("end_seconds"),
            "end_seconds",
            index,
        )

        duration = require_number(
            utterance.get("duration_seconds"),
            "duration_seconds",
            index,
        )

        text = require_non_empty_string(
            utterance.get("text"),
            "text",
            index,
        )

        if start < 0:
            raise ValueError(
                f"Utterance {index}: start_seconds cannot be negative."
            )

        if end < start:
            raise ValueError(
                f"Utterance {index}: end_seconds is before start_seconds."
            )

        if duration <= 0:
            raise ValueError(
                f"Utterance {index}: duration_seconds must be positive."
            )

        # Preserve chronological order. Overlapping utterances are
        # permitted; only a backwards start-time sequence is rejected.
        if start < previous_start:
            raise ValueError(
                f"Utterance {index}: start time is earlier than the "
                "previous utterance. Check source ordering."
            )

        calculated_duration = end - start

        if abs(calculated_duration - duration) > 0.05:
            raise ValueError(
                f"Utterance {index}: duration does not match "
                "end_seconds - start_seconds."
            )

        previous_start = start

        compact_segments.append({
            "segment_id": f"SEG{index:04d}",
            "speaker_id": speaker_id,
            "role": role,
            "start_seconds": round_seconds(start),
            "end_seconds": round_seconds(end),
            "duration_seconds": round_seconds(calculated_duration),
            "text": text,
        })

    compact_json = {
        "schema_version": "1.0",
        "encounter_id": encounter_id,
        "segments": compact_segments,
    }

    # Keep review and traceability information out of the SLM payload.
    # It is stored in a separate manifest file.
    stage1_status = str(
        source.get("processing_status", "UNKNOWN")
    ).upper()

    review_flags = source.get("review_flags", [])
    if not isinstance(review_flags, list):
        review_flags = []

    review_required = (
        stage1_status not in {"APPROVED", "COMPLETED", "COMPLETE"}
        or bool(review_flags)
    )

    manifest = {
        "manifest_schema_version": "1.0",
        "encounter_id": encounter_id,
        "source_blob": source.get("source_blob"),
        "prepared_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_processing_status": stage1_status,
        "review_status": "NEEDS_REVIEW" if review_required else "NOT_REQUIRED",
        "slm_eligible": not review_required,
        "segment_count": len(compact_segments),
        "review_flags": review_flags,
        "reconstruction_notes": source.get("reconstruction_notes", []),
        "notice": (
            "This manifest contains workflow and review metadata. "
            "It is not part of the SLM transcript payload."
        ),
    }

    return compact_json, manifest


# ---------------------------------------------------------------------
# Blob processing
# ---------------------------------------------------------------------

def download_json(blob_client) -> dict[str, Any]:
    raw_bytes = blob_client.download_blob().readall()

    try:
        return json.loads(raw_bytes.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Source blob is not valid UTF-8 JSON: {exc}")


def upload_json(
    container_client,
    blob_name: str,
    payload: dict[str, Any],
    overwrite: bool,
) -> None:
    blob_client = container_client.get_blob_client(blob_name)

    serialized = json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
        allow_nan=False,
    )

    blob_client.upload_blob(
        serialized.encode("utf-8"),
        overwrite=overwrite,
        content_settings=ContentSettings(
            content_type="application/json; charset=utf-8"
        ),
    )


def process_one(
    input_container_client,
    output_container_client,
    source_blob_name: str,
    recording_number: int,
    overwrite: bool,
    dry_run: bool,
) -> bool:
    output_filename = make_output_filename(recording_number)
    manifest_filename = make_manifest_filename(recording_number)

    logger.info("Processing recording %02d", recording_number)
    logger.info("Source: %s", source_blob_name)

    source_blob_client = input_container_client.get_blob_client(
        source_blob_name
    )

    source = download_json(source_blob_client)

    compact_json, manifest = prepare_compact_transcript(source)

    logger.info(
        "Validated %d reconstructed segments",
        len(compact_json["segments"]),
    )

    logger.info(
        "Review status: %s | SLM eligible: %s",
        manifest["review_status"],
        manifest["slm_eligible"],
    )

    if dry_run:
        logger.info(
            "DRY RUN: validated successfully; no files uploaded."
        )
        return True

    upload_json(
        output_container_client,
        output_filename,
        compact_json,
        overwrite=overwrite,
    )

    upload_json(
        output_container_client,
        manifest_filename,
        manifest,
        overwrite=overwrite,
    )

    logger.info("Uploaded compact transcript: %s", output_filename)
    logger.info("Uploaded review manifest: %s", manifest_filename)

    return True


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Prepare compact SLM input JSON from detailed "
            "clinical transcript reconstruction files."
        )
    )

    parser.add_argument(
        "--start",
        type=int,
        default=1,
        help="First recording number to process.",
    )

    parser.add_argument(
        "--end",
        type=int,
        default=50,
        help="Last recording number to process.",
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing compact JSON and manifest files.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate files without uploading outputs.",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    if args.start < 1 or args.end < args.start:
        raise ValueError("Invalid recording range.")
    if not INPUT_CONTAINER:
        raise RuntimeError(
            "Missing required .env setting: AZURE_STORAGE_OUTPUT_CONTAINER"
        )
    if not OUTPUT_CONTAINER:
        raise RuntimeError(
            "Missing required .env setting: AZURE_STORAGE_SLM_CONTAINER"
        )
    if INPUT_CONTAINER.casefold() == OUTPUT_CONTAINER.casefold():
        raise RuntimeError(
            "AZURE_STORAGE_OUTPUT_CONTAINER and AZURE_STORAGE_SLM_CONTAINER "
            "must be distinct."
        )

    logger.info("Starting Stage 2: SLM input preparation")
    logger.info("Input container: %s", INPUT_CONTAINER)
    logger.info("Output container: %s", OUTPUT_CONTAINER)
    logger.info("Recording range: %02d to %02d", args.start, args.end)

    service = create_blob_service()

    input_container_client = service.get_container_client(
        INPUT_CONTAINER
    )

    output_container_client = service.get_container_client(
        OUTPUT_CONTAINER
    )

    if not input_container_client.exists():
        raise RuntimeError(
            f"Input container does not exist: {INPUT_CONTAINER}"
        )

    if not args.dry_run:
        ensure_container(output_container_client)

    matching_blobs = []

    for blob in input_container_client.list_blobs():
        filename = blob.name.rsplit("/", 1)[-1]

        if not filename.endswith(INPUT_SUFFIX):
            continue

        recording_number = extract_recording_number(blob.name)

        if recording_number is None:
            continue

        if args.start <= recording_number <= args.end:
            matching_blobs.append((recording_number, blob.name))

    matching_blobs.sort(key=lambda item: item[0])

    if not matching_blobs:
        logger.warning(
            "No matching reconstructed transcript files were found."
        )
        logger.warning(
            "Expected names ending with: %s",
            INPUT_SUFFIX,
        )
        return

    logger.info("Found %d matching transcript files.", len(matching_blobs))

    succeeded = 0
    failed = 0

    for recording_number, source_blob_name in matching_blobs:
        try:
            process_one(
                input_container_client=input_container_client,
                output_container_client=output_container_client,
                source_blob_name=source_blob_name,
                recording_number=recording_number,
                overwrite=args.overwrite,
                dry_run=args.dry_run,
            )
            succeeded += 1

        except Exception as exc:
            failed += 1
            logger.exception(
                "FAILED recording %02d: %s",
                recording_number,
                exc,
            )

    logger.info("=" * 60)
    logger.info("STAGE 2 SUMMARY")
    logger.info("Successful: %d", succeeded)
    logger.info("Failed: %d", failed)
    logger.info("Total: %d", succeeded + failed)
    logger.info("=" * 60)

    service.close()

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
