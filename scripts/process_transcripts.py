from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from azure.storage.blob import BlobServiceClient, ContentSettings
from dotenv import load_dotenv

import prepare_slm_input as slm_preparation
from foundry_agent import FoundryAgent, FoundryAPIError, load_instructions

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
ALLOWED_ROLES = {
    "DOCTOR", "PATIENT", "NURSE", "CAREGIVER", "FAMILY_MEMBER", "PHARMACIST",
    "INTERPRETER", "OTHER_CLINICAL_STAFF", "ADMINISTRATIVE_STAFF", "OTHER", "UNKNOWN",
}
ALLOWED_STATUSES = {"CONFIDENT", "PROVISIONAL", "NEEDS_REVIEW"}


def required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required .env setting: {name}")
    return value


def get_settings() -> dict[str, Any]:
    slm_suffix = os.getenv("SLM_FILE_SUFFIX", "slm_input.json").strip()
    if not slm_suffix:
        slm_suffix = "slm_input.json"
    settings = {
        "storage_account": required("AZURE_STORAGE_ACCOUNT_NAME"),
        "storage_key": required("AZURE_STORAGE_ACCOUNT_KEY"),
        "audio_container": required("AZURE_AUDIO_CONTAINER"),
        "input_container": required("AZURE_TRANSCRIPT_CONTAINER"),
        "output_container": required("AZURE_STORAGE_OUTPUT_CONTAINER"),
        "slm_container": required("AZURE_STORAGE_SLM_CONTAINER"),
        "foundry_endpoint": required("FOUNDRY_PROJECT_ENDPOINT").rstrip("/"),
        "foundry_key": required("FOUNDRY_API_KEY"),
        "model": required("FOUNDRY_MODEL_DEPLOYMENT_NAME"),
        "agent_name": os.getenv("FOUNDRY_AGENT_NAME", "clinical-conversation-reconstruction").strip(),
        "api_version": os.getenv("FOUNDRY_API_VERSION", "v1").strip(),
        "reconstruction_pattern": os.getenv(
            "RECONSTRUCTION_FILE_PATTERN",
            "{number:02d}reconstruction.json",
        ),
        "output_pattern": os.getenv("OUTPUT_FILE_PATTERN", "{number:02d}final_transcript.json"),
        "slm_pattern": f"{{number:02d}}{slm_suffix}",
        "max_output_tokens": int(os.getenv("MAX_OUTPUT_TOKENS", "12000")),
        "timeout": int(os.getenv("REQUEST_TIMEOUT_SECONDS", "300")),
        "max_retries": int(os.getenv("MAX_RETRIES", "4")),
        "retry_base": float(os.getenv("RETRY_BASE_SECONDS", "3")),
    }
    containers = (
        settings["audio_container"],
        settings["input_container"],
        settings["output_container"],
        settings["slm_container"],
    )
    if len({name.casefold() for name in containers}) != len(containers):
        raise RuntimeError(
            "Audio, transcript, final transcript, and SLM containers must be distinct."
        )
    return settings


def make_clients(cfg: dict[str, Any]):
    conn = (
        "DefaultEndpointsProtocol=https;"
        f"AccountName={cfg['storage_account']};"
        f"AccountKey={cfg['storage_key']};"
        "EndpointSuffix=core.windows.net"
    )
    service = BlobServiceClient.from_connection_string(conn)
    input_client = service.get_container_client(cfg["input_container"])
    output_client = service.get_container_client(cfg["output_container"])
    slm_client = service.get_container_client(cfg["slm_container"])
    return service, input_client, output_client, slm_client


def ensure_containers(input_client, output_client, slm_client) -> None:
    try:
        input_client.get_container_properties()
    except ResourceNotFoundError as exc:
        raise RuntimeError(
            f"Input container '{input_client.container_name}' does not exist or is inaccessible."
        ) from exc
    for container in (output_client, slm_client):
        try:
            container.create_container()
            print(f"Created output container: {container.container_name}")
        except ResourceExistsError:
            print(f"Output container already exists: {container.container_name}")


def discover_inputs(input_client, start: int | None, end: int | None) -> list[tuple[int, str]]:
    found = []
    for item in input_client.list_blobs():
        match = re.fullmatch(r"(\d{2})transcript\.json", item.name, flags=re.IGNORECASE)
        if not match:
            continue
        number = int(match.group(1))
        if start is not None and number < start:
            continue
        if end is not None and number > end:
            continue
        found.append((number, item.name))
    return sorted(found)


def compact_encounter(raw: dict[str, Any], blob_name: str) -> dict[str, Any]:
    segments = raw.get("segments")
    if not isinstance(segments, list) or not segments:
        raise ValueError(f"{blob_name} has no non-empty 'segments' array.")
    normalized = []
    for index, segment in enumerate(segments):
        if not isinstance(segment, dict):
            raise ValueError(f"{blob_name}: segment {index} is not an object.")
        normalized.append({
            "index": index,
            "speaker_id": segment.get("speaker_id"),
            "start_seconds": segment.get("start_seconds"),
            "duration_seconds": segment.get("duration_seconds"),
            "text": str(segment.get("text", "")),
        })

    # Determine how many distinct speaker IDs the ASR produced.
    # Speaker IDs are fallible hints. A low count is not evidence that extra
    # participants exist, so the model must preserve uncertain turns for review.
    distinct_ids = sorted({
        seg.get("speaker_id") for seg in segments if seg.get("speaker_id")
    })
    is_foundry_fast = raw.get("speech_job_id") is None
    if is_foundry_fast and len(distinct_ids) <= 2:
        diarization_notice = (
            "The source produced only "
            f"{len(distinct_ids)} speaker ID(s) ({', '.join(distinct_ids)}). "
            "This count may under-represent participants, but do not assume that "
            "additional participants exist. Do not invent speakers or roles to match "
            "expected clinic staffing. Preserve each source segment and conversational "
            "turn; do not merge a question, response, handoff, or correction into one "
            "utterance. If speaker identity or role is not supported by explicit or "
            "repeated evidence, use UNKNOWN or PROVISIONAL and require review."
        )
    elif len(distinct_ids) <= 2:
        diarization_notice = (
            f"The ASR source produced {len(distinct_ids)} distinct speaker ID(s) "
            f"({', '.join(distinct_ids)}). Treat these IDs as fallible clues, not "
            "proof of identity or role. Do not assume additional participants."
        )
    else:
        diarization_notice = (
            f"The ASR source produced {len(distinct_ids)} distinct speaker ID(s): "
            f"{', '.join(distinct_ids)}. Treat these IDs as fallible clues, not "
            "proof of identity or role."
        )

    return {
        "encounter_id": str(raw.get("recording_id") or blob_name[:2]),
        "source_blob": blob_name,
        "duration_seconds": raw.get("duration_seconds"),
        "raw_transcript_text": raw.get("transcript", ""),
        "segments": normalized,
        "source_schema_version": raw.get("schema_version"),
        "speech_job_id": raw.get("speech_job_id"),
        "diarization_metadata": {
            "source_type": "foundry_fast" if is_foundry_fast else "azure_speech_batch",
            "distinct_speaker_ids_in_source": distinct_ids,
            "distinct_speaker_id_count": len(distinct_ids),
            "diarization_may_be_coarse": is_foundry_fast and len(distinct_ids) <= 2,
        },
        "important_instruction": (
            "Preserve source segment order and conversational turn boundaries. "
            "Never merge different speaker IDs into one utterance. Do not merge "
            "separate complete turns, questions and answers, handoffs, or corrections. "
            "Use speaker IDs as fallible clues; assign uncertain speakers or roles "
            "as UNKNOWN/PROVISIONAL and require review. "
            + diarization_notice
        ),
    }


def safe_number(value):
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def validate_and_finalize(agent_result: dict[str, Any], raw: dict[str, Any], blob_name: str) -> dict[str, Any]:
    source_segments = raw.get("segments", [])
    source_ids = {i: seg.get("speaker_id") for i, seg in enumerate(source_segments)}
    source_times = {i: seg for i, seg in enumerate(source_segments)}
    flags = list(agent_result.get("review_flags") or [])
    registry = agent_result.get("speaker_registry") or []
    utterances = agent_result.get("utterances") or []
    if not isinstance(registry, list) or not isinstance(utterances, list):
        raise ValueError("Agent JSON must contain speaker_registry and utterances arrays.")

    registry_map = {}
    for person in registry:
        if not isinstance(person, dict):
            continue
        pid = person.get("canonical_speaker_id")
        role = person.get("role", "UNKNOWN")
        if not pid:
            flags.append({"type": "INVALID_SPEAKER_REGISTRY_ENTRY", "detail": "Missing canonical_speaker_id"})
            continue
        if role not in ALLOWED_ROLES:
            person["role"] = "UNKNOWN"
            person["review_required"] = True
            flags.append({"type": "INVALID_ROLE", "speaker_id": pid, "detail": f"Unsupported role {role!r}"})
        person["role_confidence"] = min(1.0, max(0.0, safe_number(person.get("role_confidence")) or 0.0))
        person["attribution_status"] = person.get("attribution_status") if person.get("attribution_status") in ALLOWED_STATUSES else "NEEDS_REVIEW"
        person["evidence"] = person.get("evidence") if isinstance(person.get("evidence"), list) else []
        person["conflicting_evidence"] = person.get("conflicting_evidence") if isinstance(person.get("conflicting_evidence"), list) else []
        person["original_azure_speaker_ids"] = person.get("original_azure_speaker_ids") if isinstance(person.get("original_azure_speaker_ids"), list) else []
        person["review_required"] = bool(person.get("review_required", person["attribution_status"] == "NEEDS_REVIEW"))
        registry_map[pid] = person

    normalized_utterances = []
    covered = set()
    coverage_counts = {}
    for n, utterance in enumerate(utterances, start=1):
        if not isinstance(utterance, dict):
            flags.append({"type": "INVALID_UTTERANCE", "detail": f"Utterance {n} was not an object"})
            continue
        indices = utterance.get("source_segment_indices") or []
        valid_indices = []
        for index in indices:
            if isinstance(index, int) and 0 <= index < len(source_segments):
                valid_indices.append(index)
                covered.add(index)
                coverage_counts[index] = coverage_counts.get(index, 0) + 1
            else:
                flags.append({"type": "INVALID_SOURCE_INDEX", "utterance_id": utterance.get("utterance_id"), "value": index})
        if not valid_indices:
            flags.append({"type": "UTTERANCE_WITHOUT_SOURCE", "utterance_id": utterance.get("utterance_id", f"U{n:04d}")})
            continue
        if len(set(valid_indices)) > 1:
            flags.append({
                "type": "MERGED_SOURCE_TURNS_REVIEW",
                "utterance_id": utterance.get("utterance_id", f"U{n:04d}"),
                "segment_indices": sorted(set(valid_indices)),
                "detail": (
                    "The reconstruction combined multiple source segments. They are "
                    "preserved separately with UNKNOWN attribution for clinician review."
                ),
            })
            for index in sorted(set(valid_indices)):
                segment = source_segments[index]
                start = safe_number(segment.get("start_seconds"))
                duration = safe_number(segment.get("duration_seconds"))
                normalized_utterances.append({
                    "utterance_id": f"U{len(normalized_utterances)+1:04d}",
                    "start_seconds": start,
                    "end_seconds": start + duration if start is not None and duration is not None else None,
                    "duration_seconds": duration,
                    "canonical_speaker_id": "UNKNOWN",
                    "role": "UNKNOWN",
                    "text": str(segment.get("text", "")),
                    "source_segment_indices": [index],
                    "original_azure_speaker_ids": (
                        [str(source_ids[index])] if source_ids[index] is not None else []
                    ),
                    "attribution_confidence": 0.0,
                    "attribution_status": "NEEDS_REVIEW",
                    "reconstruction_type": "UNCHANGED",
                    "notes": [
                        "A model merged source segments; this segment was preserved without inheriting the merged speaker attribution."
                    ],
                })
            continue
        pid = utterance.get("canonical_speaker_id") or "UNKNOWN"
        if pid not in registry_map and pid != "UNKNOWN":
            flags.append({"type": "UNREGISTERED_CANONICAL_SPEAKER", "speaker_id": pid})
            pid = "UNKNOWN"
        role = utterance.get("role", registry_map.get(pid, {}).get("role", "UNKNOWN"))
        if role not in ALLOWED_ROLES:
            role = "UNKNOWN"
        if pid == "UNKNOWN":
            role = "UNKNOWN"
        elif pid in registry_map:
            registry_role = registry_map[pid].get("role", "UNKNOWN")
            if role != registry_role:
                flags.append({"type": "SPEAKER_ROLE_INCONSISTENCY", "speaker_id": pid, "utterance_role": role, "registry_role": registry_role})
            role = registry_role
        text = str(utterance.get("text") or "").strip()
        if not text:
            flags.append({"type": "EMPTY_UTTERANCE_TEXT", "utterance_id": utterance.get("utterance_id", f"U{n:04d}")})
            text = "[UNRECOGNIZED OR MISSING TEXT — REVIEW REQUIRED]"
        # Source-derived IDs are authoritative for traceability, not attribution.
        azure_ids = sorted({str(source_ids[i]) for i in valid_indices if source_ids[i] is not None})
        # Use the min/max source times as a safety envelope. Do not trust invented timing.
        starts = [safe_number(source_times[i].get("start_seconds")) for i in valid_indices]
        ends = []
        for i in valid_indices:
            st = safe_number(source_times[i].get("start_seconds"))
            dur = safe_number(source_times[i].get("duration_seconds"))
            if st is not None and dur is not None:
                ends.append(st + dur)
        start = min((x for x in starts if x is not None), default=None)
        end = max(ends, default=None)
        status = utterance.get("attribution_status") if utterance.get("attribution_status") in ALLOWED_STATUSES else "NEEDS_REVIEW"
        confidence = safe_number(utterance.get("attribution_confidence"))
        confidence = min(1.0, max(0.0, confidence if confidence is not None else 0.0))
        normalized_utterances.append({
            "utterance_id": f"U{len(normalized_utterances)+1:04d}",
            "start_seconds": start,
            "end_seconds": end,
            "duration_seconds": (end - start) if start is not None and end is not None else None,
            "canonical_speaker_id": pid,
            "role": role,
            "text": text,
            "source_segment_indices": sorted(set(valid_indices)),
            "original_azure_speaker_ids": azure_ids,
            "attribution_confidence": confidence,
            "attribution_status": status,
            "reconstruction_type": utterance.get("reconstruction_type", "UNCHANGED"),
            "notes": utterance.get("notes") if isinstance(utterance.get("notes"), list) else [],
        })

    duplicated = sorted(index for index, count in coverage_counts.items() if count > 1)
    if duplicated:
        flags.append({"type": "SOURCE_SEGMENT_REFERENCED_MULTIPLE_TIMES", "segment_indices": duplicated, "detail": "Review whether a source segment was legitimately split between speakers or duplicated by the model."})
    missing = sorted(set(range(len(source_segments))) - covered)
    if missing:
        flags.append({
            "type": "SOURCE_SEGMENTS_NOT_REPRESENTED",
            "segment_indices": missing,
            "detail": "The agent omitted one or more raw segments. They are preserved below as explicit UNKNOWN review utterances.",
        })
        for i in missing:
            seg = source_segments[i]
            st = safe_number(seg.get("start_seconds"))
            dur = safe_number(seg.get("duration_seconds"))
            normalized_utterances.append({
                "utterance_id": f"U{len(normalized_utterances)+1:04d}",
                "start_seconds": st,
                "end_seconds": st + dur if st is not None and dur is not None else None,
                "duration_seconds": dur,
                "canonical_speaker_id": "UNKNOWN",
                "role": "UNKNOWN",
                "text": str(seg.get("text", "")),
                "source_segment_indices": [i],
                "original_azure_speaker_ids": [str(seg.get("speaker_id"))] if seg.get("speaker_id") is not None else [],
                "attribution_confidence": 0.0,
                "attribution_status": "NEEDS_REVIEW",
                "reconstruction_type": "UNCHANGED",
                "notes": ["Preserved from raw ASR because the agent did not include this source segment."],
            })

    normalized_utterances.sort(key=lambda x: (x["start_seconds"] is None, x["start_seconds"] or 0.0, x["utterance_id"]))
    # Re-number after chronological sorting.
    for n, item in enumerate(normalized_utterances, start=1):
        item["utterance_id"] = f"U{n:04d}"

    # Ensure every canonical participant referenced by an utterance is registered.
    for item in normalized_utterances:
        pid = item["canonical_speaker_id"]
        if pid != "UNKNOWN" and pid not in registry_map:
            registry_map[pid] = {
                "canonical_speaker_id": pid, "role": "UNKNOWN", "role_confidence": 0.0,
                "attribution_status": "NEEDS_REVIEW", "original_azure_speaker_ids": item["original_azure_speaker_ids"],
                "evidence": [], "conflicting_evidence": ["Speaker was referenced by an utterance but missing from registry."],
                "review_required": True,
            }
            item["role"] = "UNKNOWN"
            item["attribution_status"] = "NEEDS_REVIEW"
            flags.append({"type": "MISSING_SPEAKER_REGISTRY_ENTRY", "speaker_id": pid})

    used_speakers = {
        item["canonical_speaker_id"]
        for item in normalized_utterances
        if item["canonical_speaker_id"] != "UNKNOWN"
    }
    registry_map = {
        speaker_id: person
        for speaker_id, person in registry_map.items()
        if speaker_id in used_speakers
    }

    review_required = bool(flags) or any(
        item["attribution_status"] == "NEEDS_REVIEW" or item["canonical_speaker_id"] == "UNKNOWN"
        for item in normalized_utterances
    ) or any(p.get("review_required") or p.get("attribution_status") == "NEEDS_REVIEW" for p in registry_map.values())

    final = {
        "schema_version": "1.0",
        "encounter_id": str(raw.get("recording_id") or blob_name[:2]),
        "source_blob": blob_name,
        "source_speech_job_id": raw.get("speech_job_id"),
        "processed_at_utc": datetime.now(timezone.utc).isoformat(),
        "processing_status": "NEEDS_REVIEW" if review_required or agent_result.get("processing_status") == "NEEDS_REVIEW" else "COMPLETE",
        "processing_notice": "LLM text/context reconstruction only; not acoustic speaker verification or clinician approval.",
        "speaker_registry": sorted(registry_map.values(), key=lambda p: p.get("canonical_speaker_id", "")),
        "utterances": normalized_utterances,
        "review_flags": flags,
        "reconstruction_notes": agent_result.get("reconstruction_notes") if isinstance(agent_result.get("reconstruction_notes"), list) else [],
        "foundry_response_id": agent_result.get("foundry_response_id"),
        "model_deployment": agent_result.get("model_deployment"),
    }
    return final


def main() -> None:
    parser = argparse.ArgumentParser(description="Reconstruct Speech transcripts and save validated SLM-ready output.")
    parser.add_argument("--start", type=int, default=None, help="First recording number, e.g. 1")
    parser.add_argument("--end", type=int, default=None, help="Last recording number, e.g. 5")
    parser.add_argument("--overwrite", action="store_true", help="Reprocess and replace existing reconstruction and final JSON files")
    parser.add_argument("--check", action="store_true", help="Check configuration/containers and list inputs; no LLM calls")
    parser.add_argument("--create-agent-only", action="store_true", help="Create/reuse the Foundry agent without processing transcripts")
    parser.add_argument("--force-agent-update", action="store_true", help="Create a new version of the agent even if it already exists")
    args = parser.parse_args()

    cfg = get_settings()
    if args.start is not None and args.start < 1:
        parser.error("--start must be >= 1")
    if args.end is not None and args.end < 1:
        parser.error("--end must be >= 1")
    if args.start is not None and args.end is not None and args.end < args.start:
        parser.error("--end must be >= --start")

    if cfg["output_pattern"].format(number=1) == cfg["output_pattern"].format(number=2):
        raise RuntimeError("OUTPUT_FILE_PATTERN must include a unique {number} value.")
    if cfg["reconstruction_pattern"].format(number=1) == cfg["reconstruction_pattern"].format(number=2):
        raise RuntimeError("RECONSTRUCTION_FILE_PATTERN must include a unique {number} value.")
    service, input_container, output_container, slm_container = make_clients(cfg)
    ensure_containers(input_container, output_container, slm_container)
    inputs = discover_inputs(input_container, args.start, args.end)
    print(f"Audio container       : {cfg['audio_container']}")
    print(f"Speech transcript     : {cfg['input_container']}")
    print(f"Reconstruction/final  : {cfg['output_container']}")
    print(f"Final transcript      : {cfg['output_container']}")
    print(f"Validated SLM input   : {cfg['slm_container']}")
    print(f"Foundry agent       : {cfg['agent_name']}")
    print(f"Model deployment    : {cfg['model']}")
    print(f"Matching transcripts: {len(inputs)}")
    for number, name in inputs:
        print(f"  FOUND {name}")

    if args.check:
        print("CHECK completed. No Foundry agent or model calls were made.")
        service.close()
        return

    agent = FoundryAgent(
        endpoint=cfg["foundry_endpoint"], api_key=cfg["foundry_key"], model=cfg["model"],
        agent_name=cfg["agent_name"], api_version=cfg["api_version"], timeout=cfg["timeout"],
        max_output_tokens=cfg["max_output_tokens"], max_retries=cfg["max_retries"],
        retry_base_seconds=cfg["retry_base"],
    )
    instructions = load_instructions(ROOT / "prompts" / "agent_instructions.md")
    agent.ensure_agent(instructions, force_update=args.force_agent_update)
    if args.create_agent_only:
        print("Agent setup completed. No transcripts were processed.")
        service.close()
        return
    if not inputs:
        raise RuntimeError("No raw transcript files matched NNtranscript.json in the input container.")

    processed = skipped = failed = 0
    for index, (number, input_name) in enumerate(inputs, start=1):
        reconstruction_name = cfg["reconstruction_pattern"].format(number=number)
        final_name = cfg["output_pattern"].format(number=number)
        slm_name = cfg["slm_pattern"].format(number=number)
        reconstruction_blob = output_container.get_blob_client(reconstruction_name)
        final_blob = output_container.get_blob_client(final_name)
        if final_blob.exists() and not args.overwrite:
            final = json.loads(
                final_blob.download_blob().readall().decode("utf-8-sig")
            )
            compact, manifest = slm_preparation.prepare_compact_transcript(final)
            slm_preparation.upload_json(
                slm_container, slm_name, compact, overwrite=True
            )
            slm_preparation.upload_json(
                slm_container,
                slm_preparation.make_manifest_filename(number),
                manifest,
                overwrite=True,
            )
            print(
                f"[{index}/{len(inputs)}] REUSED {final_name} and refreshed "
                f"{slm_name}"
            )
            skipped += 1
            continue
        print(
            f"[{index}/{len(inputs)}] Processing {input_name} -> "
            f"{reconstruction_name} -> {final_name} -> {slm_name}"
        )
        try:
            raw_bytes = input_container.get_blob_client(input_name).download_blob().readall()
            raw = json.loads(raw_bytes.decode("utf-8-sig"))
            if reconstruction_blob.exists() and not args.overwrite:
                agent_result = json.loads(
                    reconstruction_blob.download_blob().readall().decode("utf-8-sig")
                )
            else:
                encounter = compact_encounter(raw, input_name)
                agent_result = agent.reconstruct(encounter, instructions)
                reconstruction_payload = json.dumps(
                    agent_result,
                    ensure_ascii=False,
                    indent=2,
                ).encode("utf-8")
                reconstruction_blob.upload_blob(
                    reconstruction_payload,
                    overwrite=args.overwrite,
                    content_settings=ContentSettings(content_type="application/json; charset=utf-8"),
                )
            final = validate_and_finalize(agent_result, raw, input_name)
            payload = json.dumps(final, ensure_ascii=False, indent=2).encode("utf-8")
            final_blob.upload_blob(
                payload, overwrite=args.overwrite,
                content_settings=ContentSettings(content_type="application/json; charset=utf-8"),
            )
            compact, manifest = slm_preparation.prepare_compact_transcript(final)
            slm_preparation.upload_json(
                slm_container, slm_name, compact, overwrite=True
            )
            slm_preparation.upload_json(
                slm_container,
                slm_preparation.make_manifest_filename(number),
                manifest,
                overwrite=True,
            )
            print(
                f"  SAVED {reconstruction_name}, {final_name}, and {slm_name} "
                f"| utterances={len(final['utterances'])} "
                f"| status={final['processing_status']}"
            )
            processed += 1
        except Exception as exc:
            print(f"  FAILED {input_name}: {exc}")
            failed += 1

    print("\n========== RUN SUMMARY ==========")
    print(f"Processed: {processed}")
    print(f"Skipped  : {skipped}")
    print(f"Failed   : {failed}")
    service.close()
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
