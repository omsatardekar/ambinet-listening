"""Deterministic clean-up of a model extraction, applied by the backend before evidence resolution. No model is involved and nothing is invented.

Two rules, both written against mistakes the fine-tuned 0.6B model really makes (seen in the m3_14 test, see finetune_slm/docs/07):

1. contradicted_negative: a "No X" finding (negative_findings) where X is a condition the extraction also records in the patient's medical history
   ("No asthma" next to "asthma, ongoing"). The negative finding is removed and the removal is reported as a warning for the clinician.
2. merged_duplicate_test: a test the model wrote twice, once in procedures_and_investigations ("Rapid blood test for malaria", requested by the doctor)
   and once in clinical_actions as an investigation ("Arrange Malaria rapid test"). The action is removed; its evidence segments are added to the test.
   This is reported in the metadata only (nothing clinical is lost).

3. repeated_symptom: the same symptom written more than once, often only with a leading article ("flushes" and "the flushes"). The items are merged into the first one
   (evidence segments united, empty fields filled from the later copy, a conflicting value keeps the first and is listed); a leading "the/my/a" is removed from symptom names.
   Reported in the metadata only.

4. speech_wording (flag only, nothing is removed): a symptom whose name is a sentence copied from speech ("I'm not a snappy person", "I've overdone it")
   instead of a symptom name. The clinician is warned; the item stays.

Only these four patterns are touched, every change is listed, and an extraction without them is returned unchanged. The model's own output is kept by the caller.
"""
from __future__ import annotations

import copy
import re
from typing import Any

_STOP = {"a", "an", "the", "of", "for", "to", "and", "or", "in", "on", "at", "no", "not", "any", "with", "without",
         "arrange", "order", "book", "do", "test", "tests", "blood", "check", "investigation", "planned", "scheduled"}


def _tokens(text: Any) -> frozenset[str]:
    words = re.findall(r"[a-z0-9]+", str(text or "").lower())
    return frozenset(w for w in words if w not in _STOP and len(w) > 1)


def _same(a: frozenset[str], b: frozenset[str]) -> bool:
    return bool(a) and a == b


def _condition_names(item: dict) -> list[frozenset[str]]:
    return [t for t in (_tokens(item.get("condition")), _tokens(item.get("normalized_condition"))) if t]


def _drop_contradicted_negatives(out: dict, changes: list[dict]) -> None:
    history = (out.get("medical_history") or {}).get("past_medical_history") or []
    known = [t for h in history if isinstance(h, dict) and str(h.get("status") or "").lower() not in ("absent", "negated", "denied")
             for t in _condition_names(h)]
    if not known or not isinstance(out.get("negative_findings"), list):
        return
    kept = []
    for n in out["negative_findings"]:
        names = [t for t in (_tokens(n.get("finding")),) if t] if isinstance(n, dict) else []     # the wording the model chose, not its normalised label (which can name something else)
        if any(_same(a, b) for a in names for b in known):
            changes.append({"rule": "contradicted_negative", "removed": f"No {n.get('finding')}", "evidence_ids": n.get("evidence_ids") or [],
                            "reason": "the same condition is recorded in the patient's medical history"})
        else:
            kept.append(n)
    out["negative_findings"] = kept


def _merge_duplicate_tests(out: dict, changes: list[dict]) -> None:
    tests = out.get("procedures_and_investigations")
    actions = out.get("clinical_actions")
    if not isinstance(tests, list) or not isinstance(actions, list):
        return
    keep = []
    for a in actions:
        if isinstance(a, dict) and str(a.get("action_type") or "").lower() == "investigation":
            want = _tokens(a.get("description"))
            match = next((t for t in tests if isinstance(t, dict) and (_same(want, _tokens(t.get("normalized_name"))) or _same(want, _tokens(t.get("name"))))), None)
            if match is not None:
                ids = list(match.get("evidence_ids") or [])
                for e in a.get("evidence_ids") or []:
                    if e not in ids:
                        ids.append(e)
                match["evidence_ids"] = ids
                changes.append({"rule": "merged_duplicate_test", "removed": a.get("description"), "kept": match.get("name"), "evidence_ids": ids})
                continue
        keep.append(a)
    out["clinical_actions"] = keep


_DET = {"the", "a", "an", "my", "her", "his", "their", "our", "some", "this", "that"}


def _name_tokens(text: Any) -> frozenset[str]:
    return frozenset(w for w in re.findall(r"[a-z0-9']+", str(text or "").lower()) if w not in _DET)


def _strip_determiner(name: Any) -> Any:
    if isinstance(name, str):
        m = re.match(r"^(?:the|a|an|my|her|his|their|our|some)\s+(\S.*)$", name.strip(), flags=re.I)
        if m:
            return m.group(1)
    return name


def _merge_repeated(items: Any, key: str, section: str, changes: list[dict]) -> list | None:
    if not isinstance(items, list):
        return None
    out: list = []
    seen: dict[tuple, list[dict]] = {}
    for it in items:
        if not isinstance(it, dict):
            out.append(it)
            continue
        it[key] = _strip_determiner(it.get(key))
        toks = _name_tokens(it.get(key))
        sig = (str(it.get("status") or "").lower(), str(it.get("category") or "").lower(), str(it.get("temporality") or "").lower())
        site = str(it.get("body_site") or "").strip().lower()
        freq = str(it.get("frequency") or "").strip().lower()

        def _matches(f: dict) -> bool:
            if not toks:
                return False
            fsite, ftoks = str(f.get("body_site") or "").strip().lower(), _name_tokens(f.get(key))
            if site and fsite and site != fsite:
                return False
            if ftoks == toks:
                return True
            ffreq = str(f.get("frequency") or "").strip().lower()                       # "sweats" / "night sweats": one name contains the other AND the same stated frequency
            return bool(freq) and freq == ffreq and (ftoks < toks or toks < ftoks)

        first = next((f for f in seen.get(sig, []) if _matches(f)), None)
        if first is None:
            seen.setdefault(sig, []).append(it)
            out.append(it)
            continue
        if len(toks) > len(_name_tokens(first.get(key))):                               # keep the more specific wording
            first[key], first["normalized_name"] = it.get(key), it.get("normalized_name") or first.get("normalized_name")
        conflicts = {}
        for k, v in it.items():
            if k == "evidence_ids":
                first["evidence_ids"] = list(first.get("evidence_ids") or []) + [e for e in (v or []) if e not in (first.get("evidence_ids") or [])]
            elif isinstance(v, list) and isinstance(first.get(k), list):
                first[k] = first[k] + [e for e in v if e not in first[k]]
            elif first.get(k) in (None, "", []) and v not in (None, "", []):
                first[k] = v
            elif v not in (None, "", []) and first.get(k) != v and k not in ("normalized_name", key):
                conflicts[k] = v
        changes.append({"rule": "repeated_symptom", "section": section, "kept": first.get(key), "removed": it.get(key),
                        "evidence_ids": first.get("evidence_ids") or [], "ignored_conflicting_values": conflicts})
    return out


_FIRST_PERSON = re.compile(r"^\s*(?:i|we)(?:'m|'ve|'d|'ll| am| have| had| was| were| can't| cannot| don't| do not| didn't| couldn't| won't| feel| think| keep| get)\b", re.I)


def _flag_speech_wording(out: dict, changes: list[dict]) -> None:
    for i, s in enumerate(out.get("symptoms") or []):
        if isinstance(s, dict) and isinstance(s.get("name"), str) and _FIRST_PERSON.match(s["name"]):
            changes.append({"rule": "speech_wording", "path": f"symptoms[{i}]", "name": s["name"], "evidence_ids": s.get("evidence_ids") or []})


def clean(extraction: dict) -> tuple[dict, list[dict]]:
    """Returns (cleaned copy, list of changes). The input is not modified."""
    out = copy.deepcopy(extraction)
    changes: list[dict] = []
    _drop_contradicted_negatives(out, changes)
    _merge_duplicate_tests(out, changes)
    for section, key in (("symptoms", "name"), ("negative_findings", "finding")):
        merged = _merge_repeated(out.get(section), key, section, changes)
        if merged is not None:
            out[section] = merged
    _flag_speech_wording(out, changes)
    return (out if (changes or out != extraction) else extraction), changes             # a stripped article alone is also a (silent) change


def warning_for(change: dict) -> str | None:
    """Only clinically meaningful changes become a visible warning."""
    if change["rule"] == "contradicted_negative":
        return f"removed '{change['removed']}': it contradicts the medical history; clinician review required"
    if change["rule"] == "repeated_symptom" and change.get("ignored_conflicting_values"):
        details = ", ".join(f"{k}: {v.get('normalized') if isinstance(v, dict) and v.get('normalized') else v}" for k, v in change["ignored_conflicting_values"].items())
        return f"'{change['kept']}' was recorded twice with different details ({details}); the first was kept; clinician review required"
    if change["rule"] == "speech_wording":
        return f"symptom '{change['name']}' looks like a sentence copied from speech, not a symptom name; clinician review required"
    return None
