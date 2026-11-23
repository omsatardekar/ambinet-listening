"""Settings of the SOAP module. Names only here; values come from the process environment (.env), nothing is read from or written to existing settings."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMPT_VERSION = "soap-1"
PROMPT_FILE = ROOT / "prompts" / (os.getenv("SOAP_PROMPT_FILE", "").strip() or "soap_agent_instructions_v1.md")
DATA_DIR = Path(os.getenv("SOAP_DATA_DIR", str(ROOT / "soap_data")))

# new storage container for the finished notes (created automatically; the extraction container is only read)
ENV_SOAP_CONTAINER = "AZURE_STORAGE_SOAP_CONTAINER"
DEFAULT_SOAP_CONTAINER = "soap-output"
ENV_SOAP_SUFFIX = "SOAP_FILE_SUFFIX"
DEFAULT_SOAP_SUFFIX = "soap.json"
MARKDOWN_SUFFIX = "soap.md"

# how the note is written: a Foundry prompt agent (default when configured) or a direct call to a deployed model
ENV_BACKEND = "SOAP_BACKEND"                       # agent | model
ENV_AGENT_NAME = "SOAP_AGENT_NAME"                 # default clinical-soap-note
ENV_AGENT_VERSION = "SOAP_AGENT_VERSION"           # required in agent mode (a Foundry prompt agent is called by name AND version); printed by scripts/create_soap_agent.py
ENV_PROJECT_ENDPOINT = "FOUNDRY_PROJECT_ENDPOINT"  # existing setting, shared with the reconstruction agent
ENV_MODEL_URL = "SOAP_MODEL_ENDPOINT_URL"          # model mode; each of the three falls back to the JUDGE_* setting of the same role
ENV_MODEL_KEY = "SOAP_MODEL_API_KEY"
ENV_MODEL_DEPLOYMENT = "SOAP_MODEL_DEPLOYMENT"
DEFAULT_AGENT_NAME = "clinical-soap-note"
MAX_OUTPUT_TOKENS = int(os.getenv("SOAP_MAX_OUTPUT_TOKENS", "16000"))   # reasoning models spend part of this on thinking
TIMEOUT_SECONDS = float(os.getenv("SOAP_TIMEOUT_SECONDS", "300"))
INCLUDE_TRANSCRIPT = os.getenv("SOAP_INCLUDE_TRANSCRIPT", "0").strip() == "1"   # default OFF by design: the SOAP step works from the extraction stage output only, so the extraction model decides the quality; 1 = also give the writer the whole conversation (for experiments)
SEND_INSTRUCTIONS = os.getenv("SOAP_SEND_INSTRUCTIONS", "0").strip() == "1"   # default off: the agent holds the prompt (scripts/create_soap_agent.py), so requests stay short; 1 = send it with every request too

NOTICE = "Draft prepared from an ambient recording. It requires review, editing and signature by the treating clinician."
TERMINAL_STATES = {"completed", "completed_with_warnings", "failed"}
STATES = ("queued", "reading_summary", "drafting_note", "checking_note", "saving", "completed", "completed_with_warnings", "failed")


def _model_setting(own: str, judge: str) -> str:
    return os.getenv(own, "").strip() or os.getenv(judge, "").strip()


def model_settings() -> tuple[str, str, str]:
    return (_model_setting(ENV_MODEL_URL, "JUDGE_ENDPOINT_URL"), _model_setting(ENV_MODEL_KEY, "JUDGE_API_KEY"), _model_setting(ENV_MODEL_DEPLOYMENT, "JUDGE_DEPLOYMENT"))


def agent_configured() -> bool:
    return bool(os.getenv(ENV_PROJECT_ENDPOINT, "").strip())


def agent_ready() -> bool:
    return agent_configured() and bool(os.getenv(ENV_AGENT_VERSION, "").strip())


def model_configured() -> bool:
    return all(model_settings())


def backend() -> str:
    """SOAP_BACKEND wins. Otherwise "agent" when a Foundry project and an agent name are configured, else "model" when a deployed model is configured."""
    value = os.getenv(ENV_BACKEND, "").strip().lower()
    if value in ("agent", "model"):
        return value
    if agent_configured() and os.getenv(ENV_AGENT_NAME, "").strip():
        return "agent"
    return "model" if model_configured() else "agent"
