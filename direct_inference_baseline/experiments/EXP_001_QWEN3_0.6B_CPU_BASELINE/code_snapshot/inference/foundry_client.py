"""Microsoft Foundry client, kept configurable for a FUTURE Qwen3-0.6B deployment. NOT used in the current local baseline.

Verified facts (read-only probe, see README): the configured Foundry project currently exposes one deployment (not Qwen3),
authenticates with an `api-key` header, and uses API version "v1". Structured-JSON (`response_format`) support for a Qwen
deployment is unverified, so it stays off unless explicitly enabled. Only the extraction prompt (instruction + transcript) is sent."""
from __future__ import annotations

import time

import requests

from .base_client import BaseClient, GenerationResult, PermanentInferenceError, TransientInferenceError


class FoundryClient(BaseClient):
    provider = "foundry"

    def __init__(self, endpoint: str, api_key: str, deployment: str, api_version: str = "v1", timeout: int = 300,
                 json_mode: bool = False, session: requests.Session | None = None):
        self.endpoint, self._key, self.deployment, self.api_version = endpoint.rstrip("/"), api_key, deployment, api_version
        self.timeout, self.json_mode = timeout, json_mode
        self.session = session or requests.Session()

    def describe(self) -> dict:
        return {"provider": "foundry", "model_id": None, "deployment_name": self.deployment, "api_version": self.api_version,
                "generation": {"temperature": 0, "json_mode": self.json_mode},
                "parameter_support": {"temperature": "sent as 0", "top_p": "not sent", "max_tokens": "sent", "response_format": "only if json_mode"}}

    def _generate_once(self, user_prompt: str, max_new_tokens: int) -> GenerationResult:
        url = f"{self.endpoint}/openai/v1/chat/completions"
        body = {"model": self.deployment, "messages": [{"role": "user", "content": user_prompt}], "temperature": 0, "max_tokens": max_new_tokens}
        if self.json_mode:
            body["response_format"] = {"type": "json_object"}
        t0 = time.perf_counter()
        try:
            r = self.session.post(url, headers={"api-key": self._key, "Content-Type": "application/json"}, json=body, timeout=self.timeout)
        except (requests.Timeout, requests.ConnectionError) as e:
            raise TransientInferenceError(type(e).__name__) from e
        if r.status_code in (429, 500, 502, 503, 504):
            raise TransientInferenceError(f"HTTP {r.status_code}")
        if not r.ok:
            raise PermanentInferenceError(f"HTTP {r.status_code}: {r.text[:200]}")
        j = r.json()
        ch = j["choices"][0]
        u = j.get("usage", {})
        return GenerationResult(text=ch["message"].get("content") or "", finish_reason="length" if ch.get("finish_reason") == "length" else "stop",
                                prompt_tokens=u.get("prompt_tokens"), completion_tokens=u.get("completion_tokens"),
                                latency_seconds=time.perf_counter() - t0)
