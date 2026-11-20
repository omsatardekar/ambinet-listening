"""Storage for the SOAP module: read the saved extraction (extraction container, read-only) and save the finished note (its own container, created on demand)."""
from __future__ import annotations

import json
import os
from typing import Any

from clinical_extraction import blob_sink, blob_source
from clinical_extraction.blob_source import SourceError, recording_number
from clinical_extraction.config import ENV_ACCOUNT, ENV_KEY

from . import config


def container_name() -> str:
    return os.getenv(config.ENV_SOAP_CONTAINER, "").strip() or config.DEFAULT_SOAP_CONTAINER


def blob_name(encounter_ref: str, suffix: str | None = None) -> str:
    return f"{recording_number(encounter_ref):02d}{suffix or os.getenv(config.ENV_SOAP_SUFFIX, '').strip() or config.DEFAULT_SOAP_SUFFIX}"


def fetch_extraction(encounter_ref: str) -> tuple[dict, dict]:
    """The saved extraction document ({extraction, evidence, ...}) of one recording. Raises SourceError with a stable code."""
    number = recording_number(encounter_ref)
    service = blob_source._service()
    container, name = blob_sink.container_name(), blob_sink.blob_name(str(number))
    try:
        doc = blob_source._download(service, container, name)
    except SourceError:
        raise
    except Exception as exc:                                                                       # noqa: BLE001
        raise SourceError("extraction_read_failed", f"The clinical summary could not be read from storage ({type(exc).__name__}).") from None
    finally:
        service.close()
    if not isinstance(doc, dict) or not isinstance(doc.get("extraction"), dict):
        raise SourceError("extraction_not_found", "No clinical summary was found for this recording. Generate the clinical summary first.")
    return doc, {"container": container, "blob_name": name}


def save_note(encounter_ref: str, document: dict, markdown: str) -> dict[str, Any]:
    """Upload {NN}soap.json and {NN}soap.md. Returns {"container", "blob_name", "markdown_blob"}."""
    try:
        from azure.core.exceptions import ResourceExistsError
        from azure.storage.blob import BlobServiceClient, ContentSettings
    except ImportError as exc:
        raise SourceError("azure_sdk_missing", "azure-storage-blob is not installed in the backend environment.") from exc
    account, key = os.getenv(ENV_ACCOUNT, "").strip(), os.getenv(ENV_KEY, "").strip()
    if not account or not key:
        raise SourceError("storage_not_configured", "Storage account settings are missing.")
    container = container_name()
    json_name, md_name = blob_name(encounter_ref), blob_name(encounter_ref, config.MARKDOWN_SUFFIX)
    service = BlobServiceClient.from_connection_string(f"DefaultEndpointsProtocol=https;AccountName={account};AccountKey={key};EndpointSuffix=core.windows.net")
    try:
        client = service.get_container_client(container)
        try:
            client.create_container()
        except ResourceExistsError:
            pass
        client.get_blob_client(json_name).upload_blob(json.dumps(document, ensure_ascii=False, indent=2).encode("utf-8"), overwrite=True,
                                                      content_settings=ContentSettings(content_type="application/json"))
        client.get_blob_client(md_name).upload_blob(markdown.encode("utf-8"), overwrite=True, content_settings=ContentSettings(content_type="text/markdown; charset=utf-8"))
    except Exception as exc:                                                                       # noqa: BLE001
        raise SourceError("result_save_failed", f"The note could not be saved to storage ({type(exc).__name__}).") from None
    finally:
        service.close()
    return {"container": container, "blob_name": json_name, "markdown_blob": md_name}
