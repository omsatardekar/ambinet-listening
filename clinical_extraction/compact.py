"""Validation of the compact SLM transcript (read-only: never changes ids, order or text)."""
from __future__ import annotations

import re
from typing import Any

from .config import SEGMENT_ID_PATTERN

_ID = re.compile(SEGMENT_ID_PATTERN)
REQUIRED_SEGMENT_KEYS = ("segment_id", "speaker_id", "role", "start_seconds", "end_seconds", "duration_seconds", "text")


class CompactTranscriptError(ValueError):
    pass


def validate_compact(obj: Any) -> list[str]:
    """Raise CompactTranscriptError if the structure is unusable; return a list of non-fatal warnings."""
    if not isinstance(obj, dict):
        raise CompactTranscriptError("compact transcript root must be an object")
    for key in ("schema_version", "encounter_id", "segments"):
        if key not in obj:
            raise CompactTranscriptError(f"missing key: {key}")
    if not isinstance(obj["encounter_id"], str) or not obj["encounter_id"].strip():
        raise CompactTranscriptError("encounter_id must be a non-empty string")
    segments = obj["segments"]
    if not isinstance(segments, list) or not segments:
        raise CompactTranscriptError("segments must be a non-empty list")
    warnings: list[str] = []
    seen: set[str] = set()
    for index, segment in enumerate(segments, start=1):
        if not isinstance(segment, dict):
            raise CompactTranscriptError(f"segment {index} is not an object")
        missing = [k for k in REQUIRED_SEGMENT_KEYS if k not in segment]
        if missing:
            raise CompactTranscriptError(f"segment {index} is missing {missing}")
        sid = segment["segment_id"]
        if not isinstance(sid, str) or not _ID.match(sid):
            raise CompactTranscriptError(f"segment {index} has an invalid segment_id")
        if sid in seen:
            raise CompactTranscriptError(f"duplicate segment_id {sid}")
        seen.add(sid)
        if not isinstance(segment["text"], str) or not segment["text"].strip():
            raise CompactTranscriptError(f"segment {sid} has empty text")
        if sid != f"SEG{index:04d}":
            warnings.append(f"segment_id {sid} is not the expected sequential id at position {index}")
    return warnings
