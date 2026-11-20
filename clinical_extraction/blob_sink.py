"""Save the finished extraction as JSON in its own Blob container (new container; the existing containers are only read, never written here).

Blob name: {number:02d}{EXTRACTION_FILE_SUFFIX or "extraction.json"}   e.g. 03extraction.json, container env AZURE_STORAGE_EXTRACTION_CONTAINER
(default name "extraction-output"; created if it does not exist). The document keeps the model's raw JSON separate from metadata and derived evidence.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

from .blob_source import SourceError, recording_number
from .config import ENV_ACCOUNT, ENV_EXTRACTION_CONTAINER, ENV_EXTRACTION_SUFFIX, ENV_KEY

DEFAULT_CONTAINER = "extraction-output"
DEFAULT_SUFFIX = "extraction.json"


def container_name() -> str:
    return os.getenv(ENV_EXTRACTION_CONTAINER, "").strip() or DEFAULT_CONTAINER


def blob_name(encounter_ref: str) -> str:
    return f"{recording_number(encounter_ref):02d}{os.getenv(ENV_EXTRACTION_SUFFIX, '').strip() or DEFAULT_SUFFIX}"


def build_document(job: dict, compact: dict, extraction: dict, metadata: dict, derived: dict, notice: str) -> dict[str, Any]:
    return {"document_type": "clinical_extraction", "version": 1, "saved_at": datetime.now(timezone.utc).isoformat(), "notice": notice,
            "encounter_id": compact.get("encounter_id"), "encounter_ref": job.get("encounter_ref"), "job_id": job.get("job_id"),
            "source": job.get("source"), "warnings": job.get("warnings") or [], "extraction": extraction, "metadata": metadata, "evidence": derived}


def save(encounter_ref: str, document: dict) -> dict[str, str]:
    """Upload the document; returns {"container", "blob_name"}. Raises SourceError (stable code) on any storage problem."""
    try:
        from azure.core.exceptions import ResourceExistsError
        from azure.storage.blob import BlobServiceClient, ContentSettings
    except ImportError as exc:
        raise SourceError("azure_sdk_missing", "azure-storage-blob is not installed in the backend environment.") from exc
    account, key = os.getenv(ENV_ACCOUNT, "").strip(), os.getenv(ENV_KEY, "").strip()
    if not account or not key:
        raise SourceError("storage_not_configured", "Storage account settings are missing.")
    name, container = blob_name(encounter_ref), container_name()
    service = BlobServiceClient.from_connection_string(f"DefaultEndpointsProtocol=https;AccountName={account};AccountKey={key};EndpointSuffix=core.windows.net")
    try:
        client = service.get_container_client(container)
        try:
            client.create_container()
        except ResourceExistsError:
            pass
        client.get_blob_client(name).upload_blob(json.dumps(document, ensure_ascii=False, indent=2).encode("utf-8"), overwrite=True,
                                                 content_settings=ContentSettings(content_type="application/json"))
    except SourceError:
        raise
    except Exception as exc:                                                                  # noqa: BLE001  (type only: messages can contain account details)
        raise SourceError("result_save_failed", f"The extraction could not be saved to storage ({type(exc).__name__}).") from None
    finally:
        service.close()
    return {"container": container, "blob_name": name}
