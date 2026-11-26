"""Strict, non-repairing parsing of model output.

Allowed pre-processing (documented): remove a leading <think>...</think> block and a surrounding ``` / ```json fence.
Nothing else is repaired. Missing braces, cut-off strings, trailing text inside the JSON etc. are NOT fixed or completed:
the result is `truncated` or `invalid_json` and the record is reported as a failure."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

THINK = re.compile(r"<think>.*?</think>", re.S)
FENCE = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.S)


@dataclass
class ParseResult:
    status: str                    # ok | truncated | invalid_json | empty | not_object
    data: dict | None = None
    notes: list = field(default_factory=list)


def _repetition_loop(text: str) -> bool:
    tail = text[-1200:]
    lines = [l.strip() for l in tail.splitlines() if l.strip()]
    return len(lines) >= 8 and len(set(lines[-8:])) <= 2


def parse_response(text: str | None, finish_reason: str = "stop") -> ParseResult:
    notes = []
    if text is None or not text.strip():
        return ParseResult("empty", None, ["empty response"])
    t = text
    if THINK.search(t):
        t = THINK.sub("", t)
        notes.append("removed <think> block")
    t = t.strip()
    m = FENCE.match(t)
    if m:
        t = m.group(1)
        notes.append("removed markdown fence")
    if _repetition_loop(text):
        notes.append("degenerate repetition detected at end of output")
    try:
        data = json.loads(t)
    except json.JSONDecodeError as e:
        status = "truncated" if finish_reason == "length" else "invalid_json"
        notes.append(f"{e.msg} at char {e.pos}" + (f"; output hit the token budget (finish_reason=length)" if status == "truncated" else ""))
        return ParseResult(status, None, notes)
    if not isinstance(data, dict):
        return ParseResult("not_object", None, notes + ["top-level JSON value is not an object"])
    if finish_reason == "length":
        notes.append("parsed, but generation stopped at the token budget")
    return ParseResult("ok", data, notes)
