"""Configuration for the clinical-extraction module (additive; reads, never writes, the existing environment).

Nothing here changes the backend .env, the existing Azure settings or the frozen P02 experiment files.
"""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]                      # repository root (portable: derived from this file)
TRACK = ROOT / "direct_inference_1_7B"
SCRIPTS = TRACK / "scripts"

# ---- frozen P02 experiment (never edited by this module) -------------------------------------------------------------
PROMPT_FILE = TRACK / "experiments" / "EXP_002_PROMPTING_INFERENCE" / "prompt_versions" / "P02_p01_schema_no_evidence.txt"
PROMPT_RELATIVE = "experiments/EXP_002_PROMPTING_INFERENCE/prompt_versions/P02_p01_schema_no_evidence.txt"
FREEZE_MANIFEST = TRACK / "manifests" / "FREEZE_P02.json"
CONVERSION_RECORD = TRACK / "manifests" / "CONVERSION_RECORD_Qwen3-1.7B.json"
MODEL_DIR = TRACK / "models" / "Qwen3-1.7B-ov-fp16"
# Verified against FREEZE_P02.json, P02_CONFIG.json, run_settings_P02.json, the P02 run manifest and the prompt file itself.
EXPECTED_PROMPT_SHA256 = "f6d5202f26d97c2d73c9d00adbca050bc7114ad8b0272749eeff8d0757de09b0"
MODEL_ID = "Qwen/Qwen3-1.7B"
MODEL_REVISION = "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e"
FROZEN_MAX_NEW_TOKENS = 4096                                    # value used by the frozen P02 run; the worker takes it from common_1_7b

# ---- existing application settings (names only; values come from the process environment) ----------------------------
ENV_SLM_CONTAINER = "AZURE_STORAGE_SLM_CONTAINER"
ENV_OUTPUT_CONTAINER = "AZURE_STORAGE_OUTPUT_CONTAINER"
ENV_ACCOUNT = "AZURE_STORAGE_ACCOUNT_NAME"
ENV_KEY = "AZURE_STORAGE_ACCOUNT_KEY"
ENV_SLM_SUFFIX = "SLM_FILE_SUFFIX"                              # default "slm_input.json" (as in the existing pipeline)
ENV_FINAL_PATTERN = "OUTPUT_FILE_PATTERN"                       # default "{number:02d}final_transcript.json"

# ---- new settings for the Azure-hosted model and the result container (additive; see remote_client.py and blob_sink.py) --------
ENV_EXTRACTION_CONTAINER = "AZURE_STORAGE_EXTRACTION_CONTAINER"   # NEW container for the saved extraction JSON (default "extraction-output")
ENV_EXTRACTION_SUFFIX = "EXTRACTION_FILE_SUFFIX"                  # optional, default "extraction.json"
# EXTRACTION_ENDPOINT_URL / EXTRACTION_ENDPOINT_KEY: the hosted model endpoint. When both are set the model runs there; otherwise the local OpenVINO path is used.

# ---- new, extraction-only settings -----------------------------------------------------------------------------------
DATA_DIR = Path(os.getenv("EXTRACTION_DATA_DIR", str(ROOT / "extraction_data")))
# Python interpreter of the SEPARATE OpenVINO environment (never the backend venv). No default: it must be configured.
ENV_EXTRACTION_PYTHON = "EXTRACTION_PYTHON"
MIN_AVAILABLE_RAM_GIB = float(os.getenv("EXTRACTION_MIN_AVAILABLE_RAM_GIB", "8.0"))   # gate of the frozen 1.7B P02 worker (inference_worker.py); never lowered silently
H1_MIN_AVAILABLE_RAM_GIB = float(os.getenv("EXTRACTION_H1_MIN_AVAILABLE_RAM_GIB", "3.5"))   # Qwen3-0.6B peaks at about 3.1 GB (EXP_004/EXP_008 performance logs)
ENV_BACKEND = "EXTRACTION_BACKEND"                              # optional: "azure" (hosted endpoint; the default when the endpoint is configured) or "local" (Qwen3-0.6B + H1 on this computer)
ENV_DEVICE = "EXTRACTION_DEVICE"                                # AUTO (default: GPU if OpenVINO sees one, else CPU) | GPU | CPU
MAX_REFS_WARNING = int(os.getenv("EXTRACTION_MAX_EVIDENCE_REFS", "6"))                # "unusually large" evidence list
SEGMENT_ID_PATTERN = r"^SEG\d{4}$"

DRAFT_NOTICE = "Unvalidated clinical draft produced by a small language model. It can miss or misstate facts and requires clinician review."
TERMINAL_STATES = {"completed", "completed_with_warnings", "failed"}
STATES = ("queued", "preparing_transcript", "loading_model", "reading_transcript", "extracting",
          "validating_output", "resolving_evidence", "completed", "completed_with_warnings", "failed")


def backend() -> str:
    """"azure" (default whenever EXTRACTION_ENDPOINT_URL and EXTRACTION_ENDPOINT_KEY are set) or "local". EXTRACTION_BACKEND=local|azure forces one of them."""
    value = os.getenv(ENV_BACKEND, "").strip().lower()
    if value in ("azure", "local"):
        return value
    return "azure" if os.getenv("EXTRACTION_ENDPOINT_URL", "").strip() and os.getenv("EXTRACTION_ENDPOINT_KEY", "").strip() else "local"


def device_setting() -> str:
    value = os.getenv(ENV_DEVICE, "").strip().upper()
    return value if value in ("GPU", "CPU") else "AUTO"


def _venv_python(venv: Path) -> Path:
    return venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def extraction_python() -> Path | None:
    """EXTRACTION_PYTHON if set; otherwise the first existing environment among the ones the setup script and the experiments create (no configuration needed
    on a machine that ran `python -m clinical_extraction.setup_local_model`)."""
    value = os.getenv(ENV_EXTRACTION_PYTHON, "").strip()
    if value:
        return Path(value)
    for venv in (ROOT / ".venv-extraction", ROOT / "direct_inference_baseline" / "experiments" / "EXP_002_QWEN3_0.6B_GPU_DIRECT" / "env_openvino"):
        py = _venv_python(venv)
        if py.exists():
            return py
    return None
