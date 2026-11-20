"""Read the existing compact SLM input (preferred) or final transcript from Azure Blob Storage. Read-only: nothing is uploaded or changed.

Names are taken from the existing pipeline (verified in scripts/process_transcripts.py::get_settings and scripts/prepare_slm_input.py):
  SLM container   (env AZURE_STORAGE_SLM_CONTAINER):    {number:02d}slm_input.json , {number:02d}slm_input.manifest.json   (suffix from env SLM_FILE_SUFFIX)
  final container (env AZURE_STORAGE_OUTPUT_CONTAINER): {number:02d}final_transcript.json                                  (pattern from env OUTPUT_FILE_PATTERN)
The existing pipeline already writes the SLM input with prepare_compact_transcript(); the final transcript is only a fallback and is converted with that same function.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
from typing import Any

from .config import ENV_ACCOUNT, ENV_FINAL_PATTERN, ENV_KEY, ENV_OUTPUT_CONTAINER, ENV_SLM_CONTAINER, ENV_SLM_SUFFIX, SCRIPTS


class SourceError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def recording_number(encounter_ref: str) -> int:
    match = re.match(r"^\s*0*(\d+)\s*$", str(encounter_ref))
    if not match:
        raise SourceError("bad_encounter_reference", "The encounter reference must be a recording number such as 2 or 02.")
    return int(match.group(1))


def configured() -> dict[str, bool]:
    return {name: bool(os.getenv(name, "").strip()) for name in (ENV_ACCOUNT, ENV_KEY, ENV_SLM_CONTAINER, ENV_OUTPUT_CONTAINER)}


def _service():
    try:
        from azure.storage.blob import BlobServiceClient
    except ImportError as exc:                                                    # backend venv has it; the OpenVINO env does not need it
        raise SourceError("azure_sdk_missing", "azure-storage-blob is not installed in the backend environment.") from exc
    missing = [n for n, ok in configured().items() if not ok]
    if missing:
        raise SourceError("storage_not_configured", f"Missing storage settings: {', '.join(missing)}")
    connection = ("DefaultEndpointsProtocol=https;" f"AccountName={os.environ[ENV_ACCOUNT].strip()};" f"AccountKey={os.environ[ENV_KEY].strip()};" "EndpointSuffix=core.windows.net")
    return BlobServiceClient.from_connection_string(connection)


def _download(service, container: str, name: str) -> Any | None:
    from azure.core.exceptions import ResourceNotFoundError
    blob = service.get_container_client(container).get_blob_client(name)
    try:
        data = blob.download_blob().readall()
    except ResourceNotFoundError:
        return None
    return json.loads(data.decode("utf-8"))


def _prepare_module():
    spec = importlib.util.spec_from_file_location("existing_prepare_slm_input", SCRIPTS.parent.parent / "scripts" / "prepare_slm_input.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)                                               # module-level code only reads env and defines functions
    return module


def fetch_compact(encounter_ref: str) -> tuple[dict, dict]:
    """Return (compact_transcript, source_info). Raises SourceError with a stable code."""
    number = recording_number(encounter_ref)
    service = _service()
    slm_name = f"{number:02d}{os.getenv(ENV_SLM_SUFFIX, 'slm_input.json').strip() or 'slm_input.json'}"
    slm_container = os.environ[ENV_SLM_CONTAINER].strip()
    info: dict[str, Any] = {"container_env": ENV_SLM_CONTAINER, "blob_name": slm_name, "kind": "slm_input"}
    try:
        compact = _download(service, slm_container, slm_name)
        if compact is not None:
            manifest = _download(service, slm_container, f"{number:02d}slm_input.manifest.json")
            if isinstance(manifest, dict):
                info["manifest"] = {k: manifest.get(k) for k in ("review_status", "slm_eligible", "segment_count", "source_processing_status")}
            return compact, info
        final_name = os.getenv(ENV_FINAL_PATTERN, "{number:02d}final_transcript.json").strip().format(number=number)
        final = _download(service, os.environ[ENV_OUTPUT_CONTAINER].strip(), final_name)
        if final is None:
            raise SourceError("transcript_not_found", f"No compact SLM input or final transcript was found for recording {number:02d}.")
        compact, _manifest = _prepare_module().prepare_compact_transcript(final)  # the existing, verified conversion; transcription code is not touched
        return compact, {"container_env": ENV_OUTPUT_CONTAINER, "blob_name": final_name, "kind": "final_transcript_converted"}
    finally:
        service.close()
