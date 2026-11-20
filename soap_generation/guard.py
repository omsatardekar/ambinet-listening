"""Traceability check: every number, medicine and allergy in the finished note must be findable in what the agent was given (the extraction and the linked
conversation passages, with spoken numbers such as "seventy-five" read as digits). Anything else is listed for the clinician; the note is not changed."""
from __future__ import annotations

import difflib
import json
import re
from typing import Any

from clinical_extraction.evidence import spoken_numbers

NUM = re.compile(r"\d+(?:[./]\d+)?")


def _haystack(payload: dict) -> tuple[str, set[str]]:
    text = json.dumps(payload.get("extraction", {}), ensure_ascii=False).lower()
    rows_all = [r for rows in (payload.get("source_passages") or {}).values() for r in rows] + list(payload.get("conversation") or [])
    for r in rows_all:
        t = str(r.get("text", ""))
        text += " " + t.lower() + " " + spoken_numbers(t)
    return text, set(NUM.findall(text))


def _found(name: str, text: str, words: set[str]) -> bool:
    """A drug or allergen counts as found when its name occurs, or a word of the conversation is a close spelling of it (speech-to-text often misspells drug names)."""
    name = name.lower().strip()
    if not name:
        return True
    if name in text or name.split()[0] in text:
        return True
    first = name.split()[0]
    return bool(difflib.get_close_matches(first, words, n=1, cutoff=0.8))


def _walk(note: dict) -> list[tuple[str, str]]:
    """(where, text) for every free-text value of the note that may contain numbers."""
    out: list[tuple[str, str]] = []

    def go(node: Any, where: str) -> None:
        if isinstance(node, str):
            out.append((where, node))
        elif isinstance(node, list):
            for i in node:
                go(i, where)
        elif isinstance(node, dict):
            for k, v in node.items():
                if k in ("icd10_suggestion", "number", "problem_number", "encounter_id", "attestation"):
                    continue
                go(v, f"{where}.{k}" if where else k)
    go({k: v for k, v in note.items() if k in ("subjective", "objective", "assessment", "plan")}, "")
    return out


def check(note: dict, payload: dict) -> list[dict]:
    text, numbers = _haystack(payload)
    words = set(re.findall(r"[a-z]{4,}", text))
    found: list[dict] = []
    seen: set[str] = set()
    for where, value in _walk(note):
        for tok in NUM.findall(value):
            if tok in numbers or tok in seen:
                continue
            if tok in {"1", "2", "3", "4", "5"} and re.search(rf"\b{tok}\b", value) and where.startswith("plan.by_problem"):
                continue
            seen.add(tok)
            found.append({"ref": where, "topic": f"Value '{tok}'", "reason": "This number could not be found in the conversation or the extracted findings. Please verify it."})
    for m in note["subjective"]["medications"]:
        if not _found(m["name"], text, words):
            found.append({"ref": "subjective.medications", "topic": f"Medication '{m['name']}'", "reason": "This medicine could not be found in the conversation. Please verify it."})
    for a in note["subjective"]["allergies"]["items"]:
        if not _found(a["substance"], text, words):
            found.append({"ref": "subjective.allergies", "topic": f"Allergy '{a['substance']}'", "reason": "This allergy could not be found in the conversation. Please verify it."})
    return found
