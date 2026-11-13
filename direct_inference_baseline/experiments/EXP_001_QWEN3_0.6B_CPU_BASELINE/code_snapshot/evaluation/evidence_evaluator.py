"""Evidence grounding and unsupported-claim analysis (lexical, transcript-based).

For each PREDICTED entity (every category except the evidence list itself) the cited evidence_ids are resolved to the model's own
clinical_evidence records, which are then checked against the real transcript:

  unsupported         : no evidence_ids, an id that does not resolve, or no cited record whose text/speaker matches a real
                        transcript segment (a segment's normalised text must equal, or contain, the record's normalised text,
                        and speaker_id must be that segment's speaker).
  partially_supported : at least one cited record is a real segment, but the entity's primary key is NOT lexically supported by
                        the cited text (a related sentence is not supporting evidence).
  grounded            : real segment AND the primary key is lexically supported by the cited text.

Lexical support has two thresholds, both reported: STRICT = every content token of the primary key occurs in the cited text;
LENIENT = at least half of them do (token = norm_text word, >2 chars, not a stop word; 5-character prefix match so simple plurals
and suffixes count). Normalised dataset names such as "bilateral knee pain" are not always spoken verbatim, so STRICT understates
and LENIENT overstates; neither measures clinical correctness.

UNSUPPORTED CLAIM = a predicted entity that is not a strict TP (extra relative to the labels) AND whose primary key is not
lexically supported (LENIENT) anywhere in the whole transcript. Denominator: all predicted entities (also reported per FP).
Missing information (FN) is never counted as a hallucination, and an extra but transcript-supported entity is reported as
'extra_supported', not as a claim without support."""
from __future__ import annotations

import math

from .entity_matching import CATEGORIES, KEYS, content_tokens, entity_list, norm_text


def _stem(t: str) -> str:
    return t[:5]


def lexical_support(key: str, text: str, strict: bool) -> bool:
    toks = [_stem(t) for t in content_tokens(key.split("|")[-1] if "|" in key else key)]
    if not toks:
        return False
    hay = " ".join(_stem(t) for t in norm_text(text).split())
    present = sum(1 for t in toks if re.search(rf"(?<![a-z0-9]){re.escape(t)}", hay) is not None)
    return present == len(toks) if strict else present >= math.ceil(len(toks) / 2)


import re  # noqa: E402


def _segments(transcript: dict):
    return [(s["segment_id"], s["speaker_id"], norm_text(s["text"])) for s in transcript["segments"]]


def real_segment(rec: dict, segs) -> bool:
    if not isinstance(rec, dict):
        return False
    t, spk = norm_text(rec.get("transcript_text")), rec.get("speaker_id")
    return bool(t) and any(spk == sp and (t == st or t in st) for _, sp, st in segs)


def evaluate_grounding(pred: dict, transcript: dict) -> dict:
    segs = _segments(transcript)
    ev = {}
    for r in pred.get("clinical_evidence") or []:
        if isinstance(r, dict) and r.get("evidence_id") is not None:
            ev[r["evidence_id"]] = r
    full = " ".join(s for _, _, s in segs)
    out = {"grounded_strict": 0, "grounded_lenient": 0, "partially_supported": 0, "unsupported": 0, "total": 0, "by_category": {}}
    for cat in CATEGORIES:
        for e in entity_list(pred, cat):
            key = KEYS[cat](e)
            if key in (None, ""):
                continue
            nk = norm_text(key) if "|" not in str(key) else key
            ids = e.get("evidence_ids") if isinstance(e.get("evidence_ids"), list) else []
            recs = [ev[i] for i in ids if i in ev]
            real = [r for r in recs if real_segment(r, segs)]
            if not real:
                status = "unsupported"
            else:
                text = " ".join(str(r.get("transcript_text")) for r in real)
                if lexical_support(nk, text, True):
                    status = "grounded_strict"
                elif lexical_support(nk, text, False):
                    status = "grounded_lenient"
                else:
                    status = "partially_supported"
            out["total"] += 1
            out[status] += 1
            c = out["by_category"].setdefault(cat, {"grounded_strict": 0, "grounded_lenient": 0, "partially_supported": 0, "unsupported": 0, "total": 0})
            c[status] += 1
            c["total"] += 1
    return out


def unsupported_claims(pred: dict, transcript: dict, fp_entities_by_cat: dict) -> dict:
    """fp_entities_by_cat: category -> [(normalised key, entity)] that are strict false positives."""
    full = " ".join(norm_text(s["text"]) for s in transcript["segments"])
    n_pred = sum(len(entity_list(pred, c)) for c in CATEGORIES)
    unsup = supported_extra = 0
    items = []
    for cat, fps in fp_entities_by_cat.items():
        for key, e in fps:
            if lexical_support(key, full, strict=False):
                supported_extra += 1
            else:
                unsup += 1
                items.append({"category": cat, "key": key})
    return {"predicted_entities": n_pred, "false_positives": sum(len(v) for v in fp_entities_by_cat.values()),
            "unsupported_claims": unsup, "extra_but_transcript_supported": supported_extra, "items": items[:50]}
