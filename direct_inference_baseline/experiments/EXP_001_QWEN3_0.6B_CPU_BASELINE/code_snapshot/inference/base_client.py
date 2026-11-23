"""Provider-neutral client interface, result type and bounded retry helper."""
from __future__ import annotations

import random
import time
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Callable


class TransientInferenceError(RuntimeError):
    """Retryable failure (rate limit, 5xx, timeout, connection reset)."""


class PermanentInferenceError(RuntimeError):
    """Non-retryable failure (bad request, auth, missing model)."""


@dataclass
class GenerationResult:
    text: str
    finish_reason: str                 # "stop" = model emitted end-of-turn; "length" = token budget exhausted (truncated)
    prompt_tokens: int | None
    completion_tokens: int | None
    latency_seconds: float
    attempts: int = 1
    notes: list = field(default_factory=list)

    def as_dict(self) -> dict:
        return asdict(self)


class BaseClient(ABC):
    provider: str = "base"

    @abstractmethod
    def describe(self) -> dict:
        """Model identifier, deployment, version and parameter support - recorded in every run manifest."""

    @abstractmethod
    def _generate_once(self, user_prompt: str, max_new_tokens: int) -> GenerationResult: ...

    def generate(self, user_prompt: str, max_new_tokens: int, retries: int = 3, base_seconds: float = 2.0,
                 sleep: Callable[[float], None] = time.sleep) -> GenerationResult:
        """Bounded retries with exponential backoff + jitter for TRANSIENT errors only. A truncated output is NOT retried
        (greedy decoding would reproduce it); it is reported as truncation."""
        last = None
        for attempt in range(1, retries + 2):
            try:
                res = self._generate_once(user_prompt, max_new_tokens)
                res.attempts = attempt
                return res
            except TransientInferenceError as e:
                last = e
                if attempt > retries:
                    break
                sleep(base_seconds * (2 ** (attempt - 1)) + random.uniform(0, 0.25))
        raise TransientInferenceError(f"gave up after {retries + 1} attempts: {last}")
