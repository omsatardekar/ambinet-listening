"""Safety checks that compare the extraction with the transcript segments it cites. They run after evidence resolution (`evidence.resolve_all`),
change nothing and only produce warnings for the clinician. No model is involved.

1. allergy_denied_in_source: an allergy whose cited conversation says the opposite ("No. Never. I have taken penicillin and everything.").
2. allergy_vs_medicine: a recorded allergy and a current or planned medicine of the same drug family (penicillin allergy next to amoxicillin).
3. vital_not_in_source: a vital sign whose number does not appear in the segments cited for it (spoken numbers such as "one oh nine over seventy-seven" are read as digits).

All three are written against mistakes seen in real runs (finetune_slm/docs/11). They can raise a false alarm; they never remove or change an item.
"""
from __future__ import annotations

import re
from typing import Any

from .evidence import spoken_numbers

# stems, matched at the start of a word of the medicine / allergy name
_FAMILIES: dict[str, tuple[str, ...]] = {
    "penicillin": ("penicillin", "amoxi", "amoxy", "ampicillin", "flucloxacillin", "cloxacillin", "piperacillin", "clavulan", "co-amoxiclav", "coamoxiclav", "augmentin"),
    "cephalosporin": ("cef", "ceph", "ceftriaxone", "cefuroxime"),
    "sulfonamide": ("sulfa", "sulpha", "sulfamethoxazole", "cotrimoxazole", "co-trimoxazole", "bactrim"),
    "NSAID": ("ibuprofen", "diclofenac", "naproxen", "ketorolac", "indomethacin", "aspirin", "nsaid", "mefenamic", "etoricoxib", "celecoxib"),
    "macrolide": ("erythromycin", "azithromycin", "clarithromycin", "macrolide"),
    "fluoroquinolone": ("ciprofloxacin", "levofloxacin", "ofloxacin", "norfloxacin", "moxifloxacin", "quinolone"),
    "tetracycline": ("tetracycline", "doxycycline", "minocycline"),
    "opioid": ("codeine", "morphine", "tramadol", "oxycodone", "opioid", "fentanyl"),
}
_INACTIVE = ("stopped", "discontinued", "past", "historical", "completed", "never", "not_taking", "not taking")
_REFUTED = ("negated", "denied", "refuted", "none", "absent")

_DENIAL = re.compile(
    r"(?:^\W*no\b[.,!]?\s*(?:never|nothing|not)\b)|\bnever (?:had|have|a reaction|any)\b|\bno (?:reaction|allerg\w*|problem\w*)\b|\bnot allergic\b|\bno known (?:drug )?allerg\w*\b", re.I)
_TOOK_IT = re.compile(r"\b(?:have|had|has|i've|ive) (?:taken|been given|used)\b|\btake (?:it|them) fine\b", re.I)
_REACTION_WORDS = re.compile(r"\b(?:rash|hives|swell\w*|itch\w*|breath\w*|anaphyla\w*|vomit\w*|reaction (?:to|was|came))\b", re.I)


def _denies(text: str) -> bool:
    return bool(_DENIAL.search(text) or (_TOOK_IT.search(text) and not _REACTION_WORDS.search(text)))


def _family(text: Any) -> str | None:
    for word in re.findall(r"[a-z][a-z\-]+", str(text or "").lower()):
        for fam, stems in _FAMILIES.items():
            if any(word.startswith(s) for s in stems):
                return fam
    return None


def _segments(derived: dict) -> dict[str, list[dict]]:
    return {f["path"]: [s for s in f.get("segments", []) if s.get("status") == "resolved" and s.get("text")] for f in derived.get("facts", [])}


def _allergy_denied(extraction: dict, segs: dict[str, list[dict]]) -> list[dict]:
    out = []
    for i, a in enumerate(extraction.get("allergies") or []):
        if not isinstance(a, dict) or str(a.get("status") or "").lower() in _REFUTED:
            continue
        path = f"allergies[{i}]"
        for s in segs.get(path, []):
            if str(s.get("role") or "").upper() == "DOCTOR":
                continue
            if _denies(s["text"]):
                out.append({"rule": "allergy_denied_in_source", "path": path, "substance": a.get("substance"), "quote": s["text"][:160],
                            "warning": f"allergy '{a.get('substance')}' is recorded, but the conversation cited for it reads like a denial ('{s['text'][:80]}'); confirm with the patient; clinician review required"})
                break
    return out


def _allergy_vs_medicine(extraction: dict) -> list[dict]:
    meds: list[tuple[str, str]] = []
    for m in extraction.get("medications") or []:
        if isinstance(m, dict) and str(m.get("status") or "").lower() not in _INACTIVE:
            meds.append((str(m.get("name") or m.get("generic_name") or ""), str(m.get("name") or "") + " " + str(m.get("generic_name") or "")))
    for c in extraction.get("clinical_actions") or []:
        if isinstance(c, dict) and str(c.get("action_type") or "").lower() == "medication":
            meds.append((str(c.get("description") or ""), str(c.get("description") or "")))
    out, seen = [], set()
    for a in extraction.get("allergies") or []:
        if not isinstance(a, dict) or str(a.get("status") or "").lower() in _REFUTED:
            continue
        fam = _family(a.get("substance"))
        if not fam:
            continue
        for label, text in meds:
            if _family(text) == fam and (a.get("substance"), label) not in seen:
                seen.add((a.get("substance"), label))
                out.append({"rule": "allergy_vs_medicine", "substance": a.get("substance"), "medicine": label, "family": fam,
                            "warning": f"allergy '{a.get('substance')}' and medicine '{label}' are in the same drug family ({fam}); confirm the allergy history before prescribing; clinician review required"})
    return out


def _numbers_in(text: str) -> set[str]:
    full = text.lower() + " " + spoken_numbers(text)
    nums = set(re.findall(r"\d+(?:\.\d+)?", full))
    nums |= {n.rstrip("0").rstrip(".") for n in nums if "." in n}
    return nums | set(re.findall(r"\d+/\d+", full))


def _vital_not_in_source(extraction: dict, segs: dict[str, list[dict]]) -> list[dict]:
    out = []
    for i, v in enumerate(extraction.get("vital_signs") or []):
        if not isinstance(v, dict) or v.get("value") in (None, ""):
            continue
        path = f"vital_signs[{i}]"
        texts = [s["text"] for s in segs.get(path, [])]
        if not texts:
            continue                                    # nothing cited: the evidence warnings already cover this
        have = set().union(*(_numbers_in(t) for t in texts))
        want = [p for p in re.findall(r"\d+(?:\.\d+)?", str(v["value"]))]
        want = [w.rstrip("0").rstrip(".") if "." in w else w for w in want]
        if want and not all(w in have for w in want):
            out.append({"rule": "vital_not_in_source", "path": path, "name": v.get("name"), "value": v["value"],
                        "warning": f"{v.get('name') or 'vital sign'} {v['value']}{v.get('unit') or ''} does not appear in the conversation cited for it; check the value; clinician review required"})
    return out


def check(extraction: dict, derived: dict) -> list[dict]:
    """The findings; each has a `rule` and a ready-to-show `warning`. Empty when nothing is suspicious."""
    if not isinstance(extraction, dict) or not isinstance(derived, dict):
        return []
    segs = _segments(derived)
    return _allergy_denied(extraction, segs) + _allergy_vs_medicine(extraction) + _vital_not_in_source(extraction, segs)
