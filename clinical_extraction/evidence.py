"""Backend resolution of the evidence ids written by P02 against the exact compact transcript used for inference.

Principles (see the integration task):
* The raw model output is never modified; this module only builds a separate, derived response.
* Only ids of the exact form SEG + four digits are accepted. Nothing is auto-corrected (SEG007 is NOT turned into SEG0007).
* Invalid, missing, duplicate, empty and unusually large reference lists are flagged and kept visible, never dropped.
* A resolved segment is "model-cited", not "verified evidence": existing id does not mean clinically relevant.
Ported in spirit from the experiment-side EvidenceResolver; the original frozen files are untouched.
"""
from __future__ import annotations

import math
import re
from typing import Any

from .config import MAX_REFS_WARNING, SEGMENT_ID_PATTERN

_ID = re.compile(SEGMENT_ID_PATTERN)
LABEL = "Model-cited transcript segments"
NOTICE = ("These are the transcript segments the model cited for this fact. An existing segment id does not mean the segment "
          "supports the fact; clinician review is required.")


MATCH_LABEL = "Transcript segments matched by the backend (not cited by the model)"
MATCH_NOTICE = ("The model did not cite segments for this fact. The backend compared the words of the fact with the transcript and "
                "lists the most similar segments. This is a text-similarity match, not proof that the segment supports the fact; "
                "clinician review is required.")
MATCH_MIN_SCORE = 0.5      # share of the fact's content words that must occur in the segment
MATCH_MAX_SEGMENTS = 3
# keys whose values are labels/enums or bookkeeping, not words that would be spoken in the consultation
_NOT_CONTENT = {"evidence_ids", "confidence", "role_confidence", "status", "certainty", "assertion", "temporality", "reported_by",
                "stated_by", "category", "type", "action_type", "extraction_status", "system", "severity_scale",
                "normalized_name", "normalized_value", "normalized_condition", "normalized_procedure", "normalized_substance",
                "normalized_finding", "normalized_assessment", "normalized_datetime", "time_reference",
                "allergy_type", "route", "unit", "generic_name"}
_PLACEHOLDER = {"unknown", "none", "null", "n/a", "not stated", "unspecified"}
_STOP = frozenset("""a an and are as at be been but by can could did do does for from had has have he her his i if in into is it its
me my no not of on or our she so some that the their them then there they this to was we were what when which who will with would you
your yes okay ok well just also about any more very than too up out""".split())
_WORD = re.compile(r"[a-z0-9]+(?:[./][0-9]+)?")


def _stem(word: str) -> str:
    for suffix in ("ing", "ed", "es", "s"):
        if len(word) > len(suffix) + 3 and word.endswith(suffix):
            return word[: -len(suffix)]
    return word


def _tokens(text: str) -> set[str]:
    return {_stem(w) for w in _WORD.findall(text.lower()) if w not in _STOP and (len(w) > 2 or w.isdigit())}


def _fact_text(node: Any) -> str:
    """All free-text/number values of one fact (nested lists such as associated_symptoms included), enum-like keys left out."""
    if isinstance(node, dict):
        return " ".join(_fact_text(v) for k, v in node.items() if k not in _NOT_CONTENT)
    if isinstance(node, list):
        return " ".join(_fact_text(v) for v in node)
    if isinstance(node, (str, int, float)) and not isinstance(node, bool):
        return "" if str(node).strip().lower() in _PLACEHOLDER else str(node)
    return ""


# ---- spoken numbers -----------------------------------------------------------------------------------------------------------------
# The transcript says "one twenty-four over seventy-nine" and "thirty-eight point three"; the extraction writes 124/79 and 38.3.
_UNITS = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen "
                                      "sixteen seventeen eighteen nineteen".split())}
_TENS = {w: 10 * i for i, w in enumerate("_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()) if w != "_"}
_NUMWORDS = set(_UNITS) | set(_TENS) | {"hundred", "thousand"}
_TOKEN = re.compile(r"[a-z']+|\d+(?:\.\d+)?|[^\sa-z\d]")


def _phrase_value(words: list[str], implied_hundreds: bool = False) -> str | None:
    """Value of one run of number words as a digit string ("seventy five" -> "75", "thirty eight point three" -> "38.3")."""
    if not words:
        return None
    if "point" in words:
        k = words.index("point")
        whole, frac = _phrase_value(words[:k]), [str(_UNITS[w]) for w in words[k + 1:] if w in _UNITS and _UNITS[w] < 10]
        return f"{whole}.{''.join(frac)}" if whole is not None and frac else whole
    if "oh" in words or "zero" in words:                       # "one oh nine" -> 109
        digits = ["0" if w in ("oh", "zero") else str(_UNITS[w]) for w in words if w in _UNITS or w == "oh"]
        return "".join(digits) if digits and all(len(d) == 1 for d in digits) else None
    parts = [w for w in words if w in _NUMWORDS]
    if (implied_hundreds and len(parts) >= 2 and parts[0] in _UNITS and 1 <= _UNITS[parts[0]] <= 9
            and "hundred" not in parts and "thousand" not in parts):                 # "one twenty-four" -> 124 (blood pressure)
        rest = _phrase_value(parts[1:])
        if rest is not None and rest.isdigit() and 10 <= int(rest) <= 99:
            return str(_UNITS[parts[0]] * 100 + int(rest))
    total = current = 0
    for w in parts:
        if w in _UNITS:
            current += _UNITS[w]
        elif w in _TENS:
            current += _TENS[w]
        elif w == "hundred":
            current = max(current, 1) * 100
        elif w == "thousand":
            total += max(current, 1) * 1000
            current = 0
    return str(total + current)


def spoken_numbers(text: str) -> str:
    """The numbers said in `text` as digits, e.g. "One oh nine over seventy-seven" -> "109/77 109 77". Appended to the segment text
    for matching only; the original wording is kept."""
    toks = _TOKEN.findall(text.lower())
    out: list[str] = []
    runs: list[tuple[int, int]] = []                              # (start, end) of runs of number words, hyphens and "and" skipped
    i = 0
    while i < len(toks):
        if toks[i] in _NUMWORDS:
            j = i
            while j + 1 < len(toks) and (toks[j + 1] in _NUMWORDS or toks[j + 1] in ("-", "and", "point", "oh")):
                j += 1
            runs.append((i, j))
            i = j + 1
        else:
            i += 1
    consumed: set[int] = set()
    for n, (a, b) in enumerate(runs):
        if n in consumed:
            continue
        words = [t for t in toks[a:b + 1] if t not in ("-", "and")]
        while words and words[-1] in ("and", "point", "oh"):
            words.pop()
        nxt = runs[n + 1] if n + 1 < len(runs) else None
        if nxt and toks[b + 1:nxt[0]] == ["over"]:               # blood pressure "X over Y"
            left = _phrase_value(words, implied_hundreds=True)
            right = _phrase_value([t for t in toks[nxt[0]:nxt[1] + 1] if t not in ("-", "and")])
            if left and right:
                out += [f"{left}/{right}", left, right]
                consumed.add(n + 1)
                continue
        v = _phrase_value(words)
        if v is not None:
            out.append(v)
    return " ".join(out)


def _walk(extraction: dict) -> list[tuple[str, dict]]:
    """Every extracted fact (an object that carries an evidence_ids key) with a stable path such as symptoms[0]."""
    found: list[tuple[str, dict]] = []

    def visit(node: Any, path: str) -> None:
        if isinstance(node, dict):
            if "evidence_ids" in node:
                found.append((path, node))
                return
            for key, value in node.items():
                if key == "clinical_evidence":
                    continue
                visit(value, f"{path}.{key}" if path else key)
        elif isinstance(node, list):
            for i, value in enumerate(node):
                visit(value, f"{path}[{i}]")

    visit(extraction, "")
    return found


def _fact_label(fact: dict) -> str:
    for key in ("value", "name", "finding", "condition", "procedure", "substance", "assessment", "description", "system",
                "category", "action_type", "type", "time_reference"):
        value = fact.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def match_segments(fact: dict, segments: list[dict]) -> list[dict]:
    """Backend text-similarity match: segments that contain most of the fact's content words (rarer words weigh more)."""
    value = str(fact.get("value", ""))
    if re.search(r"\d", value) and ("unit" in fact or "name" in fact):   # a measurement (blood pressure 124/79): the number is what is said
        wanted = _tokens(value)
    else:
        wanted = _tokens(_fact_text(fact))
    if not wanted:
        return []
    seg_tokens = [_tokens(seg["text"] + " " + spoken_numbers(seg["text"])) for seg in segments]
    n = len(segments)
    weight = {w: math.log(1 + n / (1 + sum(1 for t in seg_tokens if w in t))) for w in wanted}
    total = sum(weight.values())
    scored = []
    for seg, tokens in zip(segments, seg_tokens):
        score = sum(weight[w] for w in wanted if w in tokens) / total
        if score >= MATCH_MIN_SCORE:
            scored.append((score, seg))
    scored.sort(key=lambda pair: (-pair[0], pair[1]["segment_id"]))
    return [{"segment_id": seg["segment_id"], "status": "resolved", "text": seg["text"], "speaker_id": seg["speaker_id"],
             "role": seg["role"], "start_seconds": seg["start_seconds"], "end_seconds": seg["end_seconds"],
             "match_score": round(score, 2)} for score, seg in scored[:MATCH_MAX_SEGMENTS]]


def resolve_fact(fact: dict, index: dict[str, dict]) -> dict:
    refs = fact.get("evidence_ids")
    flags: list[dict] = []
    resolved: list[dict] = []
    if not isinstance(refs, list):
        flags.append({"kind": "evidence_ids_not_a_list", "value": repr(refs)[:80]})
        refs = []
    if not refs:
        flags.append({"kind": "empty_evidence_list"})
    seen: set[str] = set()
    for ref in refs:
        item: dict[str, Any] = {"segment_id": ref}
        if not isinstance(ref, str) or not _ID.match(ref):
            item["status"] = "invalid_format"
            flags.append({"kind": "invalid_segment_id", "segment_id": ref})
            resolved.append(item)
            continue
        if ref in seen:
            item["status"] = "duplicate"
            flags.append({"kind": "duplicate_reference", "segment_id": ref})
            resolved.append(item)
            continue
        seen.add(ref)
        segment = index.get(ref)
        if segment is None:
            item["status"] = "not_found"
            flags.append({"kind": "segment_not_found", "segment_id": ref})
        else:
            item.update(status="resolved", text=segment["text"], speaker_id=segment["speaker_id"], role=segment["role"],
                        start_seconds=segment["start_seconds"], end_seconds=segment["end_seconds"])
        resolved.append(item)
    if len([r for r in refs if isinstance(r, str)]) > MAX_REFS_WARNING:
        flags.append({"kind": "unusually_large_evidence_list", "count": len(refs), "threshold": MAX_REFS_WARNING})
    source = "model_cited" if resolved else "none"
    if not resolved:                      # the model cited nothing: offer backend matches, clearly labelled as such
        resolved = match_segments(fact, list(index.values()))
        if resolved:
            source = "backend_matched"
            flags.append({"kind": "backend_matched_segments", "count": len(resolved)})
    return {"segments": resolved, "flags": flags, "source": source}


def resolve_all(extraction: dict, compact: dict) -> dict:
    """Derived response for the whole extraction. `compact` is the exact transcript that was sent to the model."""
    index = {s["segment_id"]: s for s in compact["segments"]}
    facts = []
    totals = {"facts": 0, "references": 0, "resolved": 0, "invalid_format": 0, "not_found": 0, "duplicate": 0,
              "empty_evidence_list": 0, "unusually_large_evidence_list": 0, "model_cited_facts": 0,
              "backend_matched_facts": 0, "unmatched_facts": 0}
    for path, fact in _walk(extraction):
        r = resolve_fact(fact, index)
        facts.append({"path": path, "fact_label": _fact_label(fact), **r})
        totals["facts"] += 1
        totals["references"] += len(r["segments"]) if r["source"] == "model_cited" else 0
        totals[{"model_cited": "model_cited_facts", "backend_matched": "backend_matched_facts", "none": "unmatched_facts"}[r["source"]]] += 1
        for seg in r["segments"]:
            if r["source"] == "model_cited" and seg["status"] in totals:
                totals[seg["status"]] += 1
        for flag in r["flags"]:
            if flag["kind"] in totals:
                totals[flag["kind"]] += 1
    return {"label": LABEL, "notice": NOTICE, "encounter_id": compact["encounter_id"], "totals": totals, "facts": facts}


def evidence_for_path(derived: dict, path: str) -> dict | None:
    for fact in derived["facts"]:
        if fact["path"] == path:
            matched = fact.get("source") == "backend_matched"
            return {"label": MATCH_LABEL if matched else LABEL, "notice": MATCH_NOTICE if matched else NOTICE, **fact}
    return None
