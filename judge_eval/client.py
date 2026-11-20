"""Client for the judge models deployed in Azure AI Foundry (standard library only).

Two endpoint styles are detected from the URL: ".../responses" (OpenAI Responses API) and ".../chat/completions". Settings come from the environment:
    JUDGE_ENDPOINT_URL / JUDGE_API_KEY / JUDGE_DEPLOYMENT      primary judge
    JUDGE2_ENDPOINT_URL / JUDGE2_API_KEY / JUDGE2_DEPLOYMENT   second judge (agreement sample)
The key is read from the environment, sent only in the `api-key` header, and never logged or put in an error message. Every successful call is cached on
disk keyed by (judge, deployment, prompts), so re-running an evaluation costs nothing and is reproducible. Use synthetic data only.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CACHE_DIR = Path(__file__).resolve().parent / "cache"
TIMEOUT_SECONDS = float(os.getenv("JUDGE_TIMEOUT_SECONDS", "180"))
MAX_ATTEMPTS = 4


class JudgeError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code, self.message = code, message


@dataclass
class Reply:
    text: str
    usage: dict[str, Any]
    cached: bool
    judge: str
    deployment: str


def _load_dotenv_if_needed() -> None:
    """Make `python -m judge_eval...` work from a fresh shell: read the repository .env for names not already set (never overrides)."""
    env_file = Path(__file__).resolve().parents[1] / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, _, value = line.partition("=")
        name, value = name.strip(), value.strip().strip('"').strip("'")
        if name and value and name not in os.environ:
            os.environ[name] = value


class Judge:
    def __init__(self, prefix: str = "JUDGE") -> None:
        _load_dotenv_if_needed()
        self.prefix = prefix
        self.url = os.getenv(f"{prefix}_ENDPOINT_URL", "").strip()
        self._key = os.getenv(f"{prefix}_API_KEY", "").strip()
        self.deployment = os.getenv(f"{prefix}_DEPLOYMENT", "").strip()

    def configured(self) -> bool:
        return bool(self.url and self._key and self.deployment)

    @property
    def style(self) -> str:
        return "responses" if self.url.rstrip("/").endswith("/responses") else "chat"

    def describe(self) -> dict[str, str]:
        return {"judge": self.prefix, "deployment": self.deployment, "style": self.style, "path": "/" + self.url.split("//", 1)[-1].split("/", 1)[-1] if self.url else ""}

    def _body(self, system: str, user: str, max_output_tokens: int) -> dict[str, Any]:
        if self.style == "responses":
            return {"model": self.deployment, "input": [{"role": "system", "content": system}, {"role": "user", "content": user}], "max_output_tokens": max_output_tokens}
        return {"model": self.deployment, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}], "temperature": 0, "max_tokens": max_output_tokens}

    def _cache_path(self, system: str, user: str, max_output_tokens: int) -> Path:
        digest = hashlib.sha256(json.dumps([self.prefix, self.deployment, self.style, system, user, max_output_tokens], ensure_ascii=False).encode("utf-8")).hexdigest()
        return CACHE_DIR / self.prefix / f"{digest}.json"

    def call(self, system: str, user: str, max_output_tokens: int = 4000, use_cache: bool = True) -> Reply:
        if not self.configured():
            raise JudgeError("judge_not_configured", f"{self.prefix}_ENDPOINT_URL / {self.prefix}_API_KEY / {self.prefix}_DEPLOYMENT must all be set.")
        path = self._cache_path(system, user, max_output_tokens)
        if use_cache and path.exists():
            hit = json.loads(path.read_text(encoding="utf-8"))
            return Reply(hit["text"], hit.get("usage", {}), True, self.prefix, self.deployment)
        payload = json.dumps(self._body(system, user, max_output_tokens), ensure_ascii=False).encode("utf-8")
        data = self._post_with_retry(payload)
        text, usage = self._extract(data)
        if not text.strip():
            raise JudgeError("judge_empty_reply", "The judge returned no text (the output budget may have been consumed by reasoning).")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"text": text, "usage": usage, "deployment": self.deployment}, ensure_ascii=False), encoding="utf-8")
        return Reply(text, usage, False, self.prefix, self.deployment)

    def _post_with_retry(self, payload: bytes) -> dict[str, Any]:
        last = "unknown"
        for attempt in range(1, MAX_ATTEMPTS + 1):
            request = urllib.request.Request(self.url, data=payload, method="POST", headers={"api-key": self._key, "Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                    data = json.loads(response.read().decode("utf-8"))
                if not isinstance(data, dict):
                    raise JudgeError("judge_bad_response", "The judge endpoint returned an unexpected JSON shape.")
                return data
            except urllib.error.HTTPError as exc:
                last = f"HTTP {exc.code}"
                if exc.code in (401, 403):
                    raise JudgeError("judge_auth_failed", f"The judge endpoint rejected the key (HTTP {exc.code}).") from None
                if exc.code in (400, 404):                                       # request or deployment problem: retrying will not help
                    detail = _error_hint(exc)
                    raise JudgeError("judge_request_rejected", f"The judge endpoint answered HTTP {exc.code}{detail}.") from None
                if exc.code not in (408, 409, 429, 500, 502, 503, 504):
                    raise JudgeError("judge_http_error", f"The judge endpoint answered HTTP {exc.code}.") from None
                retry_after = exc.headers.get("retry-after") if exc.headers else None
                wait = float(retry_after) if retry_after and retry_after.replace(".", "", 1).isdigit() else 2.0 * 2 ** (attempt - 1)
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                last, wait = type(exc).__name__, 2.0 * 2 ** (attempt - 1)
            except ValueError:
                raise JudgeError("judge_bad_response", "The judge endpoint returned something that is not JSON.") from None
            if attempt < MAX_ATTEMPTS:
                time.sleep(min(wait, 60))
        raise JudgeError("judge_unavailable", f"The judge endpoint failed after {MAX_ATTEMPTS} attempts ({last}).")

    @staticmethod
    def _extract(data: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
        if isinstance(data.get("output_text"), str) and data["output_text"]:
            return data["output_text"], usage
        parts: list[str] = []
        for item in data.get("output") or []:                                      # Responses API
            if isinstance(item, dict) and item.get("type") == "message":
                for block in item.get("content") or []:
                    if isinstance(block, dict) and isinstance(block.get("text"), str):
                        parts.append(block["text"])
        if parts:
            return "".join(parts), usage
        for choice in data.get("choices") or []:                                   # Chat Completions
            message = choice.get("message") if isinstance(choice, dict) else None
            if isinstance(message, dict) and isinstance(message.get("content"), str):
                parts.append(message["content"])
        return "".join(parts), usage


def _error_hint(exc: urllib.error.HTTPError) -> str:
    """Short, safe part of an Azure error (its `code` only; never the message, which can echo request content)."""
    try:
        body = json.loads(exc.read().decode("utf-8"))
        code = (body.get("error") or {}).get("code") if isinstance(body, dict) else None
        return f" (code: {code})" if isinstance(code, str) and len(code) < 60 else ""
    except Exception:                                                              # noqa: BLE001
        return ""


def parse_json_reply(text: str) -> Any:
    """Parse a judge reply that should be one JSON value; tolerates a Markdown fence around it. Raises JudgeError if it is not JSON."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1]
        cleaned = cleaned.rsplit("```", 1)[0]
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or end <= start:
        raise JudgeError("judge_not_json", "The judge reply contained no JSON object.")
    try:
        return json.loads(cleaned[start:end + 1])
    except ValueError:
        raise JudgeError("judge_not_json", "The judge reply was not valid JSON.") from None
