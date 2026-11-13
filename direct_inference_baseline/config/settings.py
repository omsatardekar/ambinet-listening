"""Paths, environment and frozen-dataset guard.  Loads the EXISTING root .env (never a module-local one) by an absolute,
root-relative path, so commands work from any working directory.  Secrets are never printed."""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

MODULE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = MODULE_DIR.parent
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(ENV_PATH)

DATASET_DIR = PROJECT_ROOT / "dataset_v2_batch_001_corrected"
INPUT_DIR = DATASET_DIR / "output" / "inputs"
LABEL_DIR = DATASET_DIR / "output" / "labels"          # read ONLY by evaluation/, never by inference/
MANIFEST_CSV = DATASET_DIR / "output" / "manifest.csv"
FINAL_MANIFEST = DATASET_DIR / "output" / "FINAL_MANIFEST.json"
CHECKSUMS = DATASET_DIR / "output" / "CHECKSUMS.sha256"
ROOT_SCHEMA = PROJECT_ROOT / "clinical_extraction_schema.json"      # authoritative output format (never modified)
FINAL_SCHEMA = DATASET_DIR / "schema" / "final_label_schema.json"   # enums/key sets of the frozen labels

SPLIT_DIR = MODULE_DIR / "data" / "splits"
OUTPUT_DIR = MODULE_DIR / "outputs"
RAW_DIR, PARSED_DIR, FAILED_DIR, REPORT_DIR = (OUTPUT_DIR / n for n in ("raw_predictions", "parsed_predictions", "failed_predictions", "reports"))
LOG_DIR = MODULE_DIR / "logs"
PROMPT_PATH = MODULE_DIR / "prompts" / "direct_extraction_prompt.txt"

SECRET_NAMES = ("FOUNDRY_API_KEY", "AZURE_AI_API_KEY", "AZURE_STORAGE_ACCOUNT_KEY", "AZURE_SPEECH_KEY", "AZURE_FOUNDRY_SPEECH_KEY")


@dataclass(frozen=True)
class Settings:
    provider: str
    hf_model_id: str
    hf_device: str
    foundry_endpoint: str
    foundry_deployment: str
    foundry_api_version: str
    foundry_model_name: str
    request_timeout: int
    max_retries: int
    retry_base_seconds: float

    def __repr__(self) -> str:       # never leaks the endpoint/key
        return (f"Settings(provider={self.provider!r}, hf_model_id={self.hf_model_id!r}, hf_device={self.hf_device!r}, "
                f"foundry_deployment={self.foundry_deployment!r})")


def _get(*names: str, default: str = "") -> str:
    for n in names:
        v = os.getenv(n, "").strip().strip("\"'")
        if v:
            return v
    return default


def load_settings() -> Settings:
    return Settings(
        provider=_get("INFERENCE_PROVIDER", default="huggingface").lower(),
        hf_model_id=_get("HF_MODEL_ID", default="Qwen/Qwen3-0.6B"),
        hf_device=_get("HF_DEVICE", default="cpu"),
        foundry_endpoint=_get("AZURE_AI_PROJECT_ENDPOINT", "FOUNDRY_PROJECT_ENDPOINT"),
        foundry_deployment=_get("MODEL_DEPLOYMENT_NAME", "FOUNDRY_MODEL_DEPLOYMENT_NAME"),
        foundry_api_version=_get("AZURE_AI_API_VERSION", "FOUNDRY_API_VERSION", default="v1"),
        foundry_model_name=_get("MODEL_NAME", default="Qwen3-0.6B"),
        request_timeout=int(_get("REQUEST_TIMEOUT_SECONDS", default="300")),
        max_retries=int(_get("MAX_RETRIES", default="4")),
        retry_base_seconds=float(_get("RETRY_BASE_SECONDS", default="3")),
    )


def foundry_key() -> str:
    return _get("AZURE_AI_API_KEY", "FOUNDRY_API_KEY")


def check_config() -> dict:
    """Report which variables are present WITHOUT printing values."""
    s = load_settings()
    present = {n: bool(os.getenv(n, "").strip()) for n in ("INFERENCE_PROVIDER", "HF_MODEL_ID", "HF_DEVICE", "FOUNDRY_PROJECT_ENDPOINT",
                                                          "FOUNDRY_API_KEY", "FOUNDRY_MODEL_DEPLOYMENT_NAME", "FOUNDRY_API_VERSION")}
    return {"env_file": str(ENV_PATH), "env_file_exists": ENV_PATH.exists(), "provider": s.provider, "hf_model_id": s.hf_model_id,
            "hf_device": s.hf_device, "variables_present": present,
            "foundry_note": "Foundry deployment currently configured is NOT Qwen3-0.6B; the Foundry client is kept for a future Qwen deployment.",
            "dataset_dir_exists": DATASET_DIR.exists(), "schema_exists": ROOT_SCHEMA.exists()}


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def verify_frozen_dataset(inputs_only: bool = False) -> dict:
    """Read-only: re-hash frozen files against the dataset's own CHECKSUMS.sha256.
    inputs_only=True (used by the inference runner) hashes ONLY transcripts and the manifest, so inference code never opens a label file."""
    expected = {}
    for line in CHECKSUMS.read_text(encoding="utf-8").splitlines():
        if line.strip():
            h, rel = line.split("  ", 1)
            if inputs_only and "/labels/" in rel:
                continue
            expected[rel.strip()] = h
    bad = [rel for rel, h in expected.items() if not (DATASET_DIR / rel).exists() or sha256_file(DATASET_DIR / rel) != h]
    return {"files_checked": len(expected), "mismatches": bad, "verified": not bad,
            "dataset_manifest_sha256": sha256_file(FINAL_MANIFEST)}
