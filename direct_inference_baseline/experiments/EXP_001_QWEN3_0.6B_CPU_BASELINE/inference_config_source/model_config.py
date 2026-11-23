"""Fixed generation configuration for the direct baseline (recorded verbatim in every run manifest)."""
from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class GenerationConfig:
    # Deterministic decoding: greedy search. temperature/top_p/top_k are therefore NOT applied (recorded as None).
    # Qwen's published recommendation for non-thinking mode is sampling (T=0.7, top_p=0.8, top_k=20); greedy is used here
    # instead so that the baseline is reproducible. Qwen warns greedy can loop - repetition is detected and reported, not hidden.
    do_sample: bool = False
    temperature: float | None = None
    top_p: float | None = None
    top_k: int | None = None
    repetition_penalty: float = 1.0
    max_new_tokens: int = 6144
    enable_thinking: bool = False         # Qwen3 chat template switch: non-thinking mode (no <think> block)
    torch_dtype: str = "float32"
    seed: int = 20260101

    def as_dict(self) -> dict:
        return asdict(self)
