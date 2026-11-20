"""Frozen judge prompts. The SHA-256 of each is stored with every result; change a word and the hash changes (results from the old text are not mixed in).

Precision pass: each fact a small model extracted is checked against the TRANSCRIPT only (the judge does not see the reference label, so the label's own
mistakes cannot leak into the faithfulness score). Recall pass: each REFERENCE fact is checked for presence in the predicted facts.
"""
from __future__ import annotations

import hashlib

PRECISION_SYSTEM = """You are a meticulous clinical documentation auditor. You are given a consultation transcript and a list of facts that an automatic system extracted from it. Decide, fact by fact, whether the transcript supports the fact. Use ONLY the transcript: do not use medical knowledge to accept a fact the speakers never said.

Verdicts:
- "supported": the transcript states or clearly implies the fact, including every detail shown in it (dose, status, duration, who reported it, negation). Paraphrase, synonyms, abbreviations and clinical normalisation are fine (for example "Hypertension" for "high blood pressure").
- "partially_supported": the core finding is in the transcript but at least one stated detail is wrong or not in the transcript (wrong dose, wrong duration, wrong person, wrong status). Name the wrong detail in the reason.
- "unsupported": nothing in the transcript supports the fact (invented), or it concerns someone other than the patient without saying so.
- "contradicted": the transcript says the opposite (a denied symptom listed as present, a stopped medicine listed as current, a negated finding listed as positive).

"critical" is true only for a clinically dangerous error: an invented or wrong medication, dose, allergy or diagnosis, or a flipped negation. Otherwise false. Supported facts are never critical.

Cite the transcript segment ids you relied on (for example "SEG0012"); use an empty list when nothing supports the fact. Keep each reason under 25 words.

Reply with ONE JSON object and nothing else, in this exact shape, with exactly one entry per input fact in the same order:
{"verdicts":[{"fid":"<fact id>","verdict":"supported|partially_supported|unsupported|contradicted","critical":false,"segments":["SEG0001"],"reason":"..."}]}"""

RECALL_SYSTEM = """You are a meticulous clinical documentation auditor. You are given REFERENCE facts (the expected extraction of a consultation) and PREDICTED facts (what an automatic system extracted). For every REFERENCE fact decide whether the predicted facts convey it.

Verdicts:
- "found": a predicted fact conveys the same clinical information, including its key details (dose, status, duration, negation, who reported it). Different wording, synonyms, abbreviations and normalised names are fine. One predicted fact may cover several reference facts.
- "partially_found": the same finding is present but a key detail is missing or wrong (for example the medicine without its dose, a symptom without its duration, the wrong status). Name the gap in the reason.
- "missing": no predicted fact conveys it.

List the ids of the predicted facts that matched (empty list for "missing"). Keep each reason under 25 words.

Reply with ONE JSON object and nothing else, in this exact shape, with exactly one entry per REFERENCE fact in the same order:
{"verdicts":[{"fid":"<reference fact id>","verdict":"found|partially_found|missing","matched":["<predicted fact id>"],"reason":"..."}]}"""

PRECISION_VERDICTS = ("supported", "partially_supported", "unsupported", "contradicted")
RECALL_VERDICTS = ("found", "partially_found", "missing")


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


PROMPT_HASHES = {"precision": sha(PRECISION_SYSTEM), "recall": sha(RECALL_SYSTEM)}


def transcript_text(compact: dict) -> str:
    return "\n".join(f"{s['segment_id']} [{s.get('role', '')}]: {s.get('text', '')}" for s in compact.get("segments", []))


def facts_text(facts: list[dict]) -> str:
    return "\n".join(f"{f['fid']}: [{f['field']}] {f['text']}" for f in facts)


def precision_user(compact: dict, predicted: list[dict]) -> str:
    return f"TRANSCRIPT\n{transcript_text(compact)}\n\nEXTRACTED FACTS TO CHECK\n{facts_text(predicted)}"


def recall_user(reference: list[dict], predicted: list[dict]) -> str:
    return f"REFERENCE FACTS\n{facts_text(reference)}\n\nPREDICTED FACTS\n{facts_text(predicted)}"
