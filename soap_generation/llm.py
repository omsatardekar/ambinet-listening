"""The writer of the note: a Foundry prompt agent (default) or a deployed model, behind one function `generate(payload)` that returns the raw answer text.

* agent mode: the same mechanism as the reconstruction stage (agent_framework FoundryAgent, signed in with the Azure CLI). The agent holds the prompt: it is created
  once with scripts/create_soap_agent.py (re-run it after editing prompts/soap_agent_instructions_v1.md, then restart the backend). Requests carry only the findings.
* model mode: a direct call to a deployed model (Responses or Chat Completions style, detected from the URL), key in the `api-key` header.
Patient-related text is sent to the service you configure and is never written to a log or an error message here. Use synthetic data until real data is approved."""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import urllib.error
import urllib.request
from typing import Any

from . import config

log = logging.getLogger("soap_generation")
TASK = "Write the SOAP progress note for this encounter. Return only the JSON object described in the instructions."


class LlmError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code, self.message = code, message


def instructions_text() -> str:
    try:
        return config.PROMPT_FILE.read_text(encoding="utf-8")
    except OSError as exc:
        raise LlmError("instructions_missing", f"The SOAP instructions file is missing: {config.PROMPT_FILE.name}") from exc


def build_request(payload: dict, repair_hint: str | None = None) -> str:
    body: dict[str, Any] = {"task": TASK}
    if config.SEND_INSTRUCTIONS:
        body["soap_instructions"] = instructions_text()
    body["input"] = payload
    if repair_hint:
        body["correction"] = (f"Your previous answer could not be used: {repair_hint}. Answer again with ONE valid JSON object that follows the output format exactly, "
                              "and nothing else.")
    return json.dumps(body, ensure_ascii=False, separators=(",", ":"))


# ---- agent -------------------------------------------------------------------------------------------------------------------------------

def call_agent(request_text: str) -> str:
    endpoint = os.getenv(config.ENV_PROJECT_ENDPOINT, "").strip().rstrip("/")
    if not endpoint:
        raise LlmError("agent_not_configured", "FOUNDRY_PROJECT_ENDPOINT is not set.")
    name = os.getenv(config.ENV_AGENT_NAME, "").strip() or config.DEFAULT_AGENT_NAME
    version = os.getenv(config.ENV_AGENT_VERSION, "").strip()
    if not version:
        raise LlmError("agent_version_missing", "SOAP_AGENT_VERSION is not set. Run scripts/create_soap_agent.py --update-env once, or set the version of the agent in .env.")
    try:
        from agent_framework.foundry import FoundryAgent
        from azure.identity import AzureCliCredential
    except ImportError as exc:
        raise LlmError("agent_sdk_missing", "The Foundry agent packages are not installed in the backend environment.") from exc
    credential = AzureCliCredential()
    try:
        agent = FoundryAgent(project_endpoint=endpoint, agent_name=name, agent_version=version, credential=credential, timeout=config.TIMEOUT_SECONDS)
        text = asyncio.run(agent.run(request_text)).text
    except LlmError:
        raise
    except Exception as exc:                                                                        # noqa: BLE001  (type only: messages can hold endpoint details)
        log.error("SOAP agent call failed (%s)", type(exc).__name__)
        raise LlmError("agent_call_failed", "The note writer did not answer. Check the agent name and that you are signed in to Azure.") from None
    finally:
        credential.close()
    if not isinstance(text, str) or not text.strip():
        raise LlmError("empty_answer", "The note writer returned an empty answer.")
    return text.strip()


# ---- direct model call ---------------------------------------------------------------------------------------------------------------------

def _extract(data: dict) -> str:
    if isinstance(data.get("output_text"), str) and data["output_text"].strip():
        return data["output_text"]
    parts: list[str] = []
    for item in data.get("output") or []:
        for c in (item.get("content") or []) if isinstance(item, dict) else []:
            if isinstance(c, dict) and isinstance(c.get("text"), str):
                parts.append(c["text"])
    if parts:
        return "".join(parts)
    for ch in data.get("choices") or []:
        msg = (ch or {}).get("message") or {}
        if isinstance(msg.get("content"), str):
            return msg["content"]
    return ""


def call_model(system: str, user: str) -> str:
    url, key, deployment = config.model_settings()
    if not (url and key and deployment):
        raise LlmError("model_not_configured", "SOAP_MODEL_ENDPOINT_URL, SOAP_MODEL_API_KEY and SOAP_MODEL_DEPLOYMENT (or the JUDGE_* settings) must all be set.")
    responses = url.rstrip("/").endswith("/responses")
    if responses:
        body: dict[str, Any] = {"model": deployment, "input": [{"role": "system", "content": system}, {"role": "user", "content": user}], "max_output_tokens": config.MAX_OUTPUT_TOKENS}
    else:
        body = {"model": deployment, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}], "max_completion_tokens": config.MAX_OUTPUT_TOKENS}
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    last = "unknown"
    for attempt in range(1, 5):
        req = urllib.request.Request(url, data=data, method="POST", headers={"api-key": key, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=config.TIMEOUT_SECONDS) as resp:
                parsed = json.loads(resp.read().decode("utf-8"))
            text = _extract(parsed) if isinstance(parsed, dict) else ""
            if not text.strip():
                raise LlmError("empty_answer", "The model returned no text (its output budget may have been used up).")
            return text.strip()
        except urllib.error.HTTPError as exc:
            last = f"HTTP {exc.code}"
            if exc.code in (401, 403):
                raise LlmError("model_auth_failed", "The model endpoint rejected the credentials.") from None
            if exc.code not in (408, 409, 429, 500, 502, 503, 504):
                raise LlmError("model_call_failed", f"The model endpoint returned {last}.") from None
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last = type(exc).__name__
        if attempt < 4:
            time.sleep(min(30, 2 ** attempt))
    raise LlmError("model_call_failed", f"The model endpoint did not answer ({last}).")


def generate(payload: dict, repair_hint: str | None = None) -> str:
    request = build_request(payload, repair_hint)
    if config.backend() == "model":
        system = instructions_text()
        return call_model(system, json.dumps({"task": TASK, "input": payload, **({"correction": json.loads(request).get("correction")} if repair_hint else {})},
                                            ensure_ascii=False, separators=(",", ":")))
    return call_agent(request)
