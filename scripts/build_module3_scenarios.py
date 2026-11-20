#!/usr/bin/env python3
"""Compile the hand-written Module-3 conversations (scenarios/_authoring/*.txt) into what scripts/ambient_tts.py reads.

Each authoring file = a JSON header, a line with three dashes, then the dialogue:

    {"title": "...", "specialty": "...", "accent": "GB", "speakers": {"D": ["DOCTOR","F"], "P": ["PATIENT","M"]}, ...}
    ---
    P: text
    D{p=1.2}: text            p = silent seconds before the turn (exam, typing, thinking)
    P~{ov=0.4}: Mm-hm.        '~' = starts while the previous speaker is still finishing
    P!: text                  '!' = quiet / muffled

Spoken-language enrichment (on by default, deterministic per scenario, see enrich()): about 9 short overlapping listener responses
("Mm-hm.", "Right."), about 9 "um/uh" hesitations at the start of non-doctor answers and 3 for the doctor. Turn off with --no-enrich.

Output per file: scenarios/<name>/scenario.json + dialogue.txt, plus scenarios/SCENARIO_INDEX.json.
Checks (printed, non-zero exit on a hard failure): every speaker key defined, no bracketed stage directions in spoken text,
length (estimated audio length >= MIN_EST_MINUTES, from the measured 2.53 words/s) and the header's "must_not_mention" words
(used for information that is deliberately absent, e.g. "allerg" when allergies are never discussed).
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIN_EST_MINUTES = 10.8        # required estimated length; the real Azure audio of the earlier 39 recordings ran at 2.53 words/s incl. gaps (min 2.46, max 2.60)
WORDS_PER_SEC = 2.53          # measured on the Module-2 recordings, so the estimate is realistic, not optimistic
DEFAULT_GAP_SEC = 0.65        # already inside WORDS_PER_SEC; an explicit p= pause replaces it

LINE = re.compile(r"^(?P<key>[A-Z][A-Z0-9]*)(?P<flags>[~!]*)(?:\{(?P<opts>[^}]*)\})?:\s*(?P<text>.+?)\s*$")
DISPLAY = {"DOCTOR": "Doctor", "PATIENT": "Patient", "NURSE": "Nurse", "CAREGIVER": "Caregiver", "FAMILY_MEMBER": "Family member",
           "CLINICAL_STAFF": "Other clinical staff", "UNKNOWN": "Person not identified"}
# fallback voices (all verified with `ambient_tts.py voices`); .env VOICE_<ROLE> overrides them - see .env.example
VOICES = {
    "US": {"M": ["en-US-JasonNeural", "en-US-DavisNeural", "en-US-GuyNeural", "en-US-TonyNeural", "en-US-BrandonNeural", "en-US-EricNeural", "en-US-JacobNeural", "en-US-RogerNeural"],
           "F": ["en-US-NancyNeural", "en-US-JennyNeural", "en-US-AriaNeural", "en-US-SaraNeural", "en-US-JaneNeural", "en-US-AmberNeural", "en-US-MichelleNeural", "en-US-MonicaNeural"]},
    "GB": {"M": ["en-GB-RyanNeural", "en-GB-ThomasNeural", "en-GB-AlfieNeural", "en-GB-ElliotNeural", "en-GB-OliverNeural"],
           "F": ["en-GB-SoniaNeural", "en-GB-LibbyNeural", "en-GB-AbbiNeural", "en-GB-BellaNeural", "en-GB-HollieNeural", "en-GB-OliviaNeural"]},
    "IN": {"M": ["en-IN-PrabhatNeural", "en-IN-AaravNeural", "en-IN-KunalNeural", "en-IN-RehaanNeural"],
           "F": ["en-IN-NeerjaNeural", "en-IN-AashiNeural", "en-IN-AnanyaNeural", "en-IN-KavyaNeural"]},
    "AU": {"M": ["en-AU-WilliamNeural", "en-AU-DarrenNeural", "en-AU-DuncanNeural", "en-AU-KenNeural"],
           "F": ["en-AU-NatashaNeural", "en-AU-AnnetteNeural", "en-AU-CarlyNeural", "en-AU-ElsieNeural"]},
    "CA": {"M": ["en-CA-LiamNeural"], "F": ["en-CA-ClaraNeural"]},
}


def parse(path: Path) -> tuple[dict, list[dict]]:
    head, sep, body = path.read_text(encoding="utf-8").partition("\n---\n")
    if not sep:
        raise ValueError(f"{path.name}: header and dialogue must be separated by a line with three dashes")
    meta = json.loads(head)
    turns = []
    for n, raw in enumerate(body.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = LINE.match(line)
        if not m:
            raise ValueError(f"{path.name}, dialogue line {n}: cannot parse {line[:60]!r}")
        turns.append({"line": line, "key": m["key"], "text": m["text"]})
    return meta, turns


def assign_voices(meta: dict, taken_global: list[str]) -> dict:
    accent_default = meta.get("accent", "US")
    speakers, used = {}, set()
    for key, spec in meta["speakers"].items():
        role, gender = spec[0], spec[1]
        accent = spec[2] if len(spec) > 2 else (accent_default if role in ("PATIENT", "FAMILY_MEMBER", "CAREGIVER") else meta.get("staff_accent", accent_default))
        pool = [v for v in VOICES[accent][gender] if v not in used] or [v for v in VOICES["US"][gender] if v not in used]
        start = (len(taken_global) + len(used)) % len(pool)
        voice = pool[start]
        used.add(voice)
        rate = meta.get("rates", {}).get(key, "0%")
        speakers[key] = {"speaker_id": f"spk_{key.lower()}", "role": role, "gender": gender, "accent": accent,
                         "display_name": f"{DISPLAY[role]} (fictional)", "voice": voice, "rate": rate, "pitch": "0%"}
    taken_global.append(meta["name"])
    return speakers


def estimate_minutes(turns: list[dict]) -> float:
    words = sum(len(t["text"].split()) for t in turns)
    extra = 0.0
    for t in turns:
        m = re.search(r"p=([\d.]+)", t["line"])
        if m:
            extra += float(m.group(1)) - DEFAULT_GAP_SEC
    return (words / WORDS_PER_SEC + extra) / 60


# --- spoken-language enrichment (deterministic per scenario; the authoring files themselves are never changed) --------------------------
BACKCHANNEL = {"DOCTOR": ["Mm-hm.", "Right.", "I see.", "Okay.", "Mm.", "Yes.", "Sure."],
               "PATIENT": ["Mm.", "Yeah.", "Right.", "Okay.", "Mm-hm."]}
BACKCHANNEL_OTHER = ["Mm.", "Yeah.", "Right.", "Mm-hm."]
HESITATION = ["Um, ", "Uh, ", "Well, um, ", "Hm, ", "Er, ", "Well, uh, "]
SAFE_FIRST = {"The", "This", "That", "It", "It's", "We", "My", "Yes", "No", "Well", "Not", "A", "And", "But", "So", "Just", "About", "There",
              "They", "He", "She", "You", "Some", "Most", "Only", "Maybe", "Probably", "Since", "When", "After", "Before", "Every"}
DOCTOR_LEAD = [("Okay, ", "Okay, um, "), ("Right, ", "Right, er, "), ("So ", "So, um, "), ("Well, ", "Well, uh, ")]


def enrich(turns: list[dict], speakers: dict, name: str, n_backchannel: int = 9, n_hesitation: int = 9, n_doctor: int = 3) -> list[dict]:
    rng = random.Random(name)
    roles = {k: v[0] for k, v in speakers.items()}
    parsed = []
    for t in turns:
        m = LINE.match(t["line"])
        parsed.append({"key": m["key"], "flags": m["flags"], "opts": m["opts"], "text": m["text"]})
    # 1) hesitations at the start of some answers by non-doctors (only where the first word is safe to lower-case)
    cands = [i for i, t in enumerate(parsed) if roles[t["key"]] != "DOCTOR" and len(t["text"].split()) >= 10 and t["text"].split()[0] in SAFE_FIRST
             and "?" not in t["text"][:25]]
    for i in rng.sample(cands, min(n_hesitation, len(cands))):
        w = parsed[i]["text"]
        parsed[i]["text"] = rng.choice(HESITATION) + w[0].lower() + w[1:]
    # 2) a few doctor hesitations
    dcands = [i for i, t in enumerate(parsed) if roles[t["key"]] == "DOCTOR" and any(t["text"].startswith(a) for a, _ in DOCTOR_LEAD) and len(t["text"].split()) >= 10]
    for i in rng.sample(dcands, min(n_doctor, len(dcands))):
        for a, b in DOCTOR_LEAD:
            if parsed[i]["text"].startswith(a):
                parsed[i]["text"] = b + parsed[i]["text"][len(a):]
                break
    # 3) short overlapping listener responses after long statements (spoken by whoever speaks next)
    pos = [i for i in range(len(parsed) - 1)
           if len(parsed[i]["text"].split()) >= 24 and not parsed[i]["text"].rstrip().endswith("?")
           and parsed[i + 1]["key"] != parsed[i]["key"] and "~" not in parsed[i + 1]["flags"] and len(parsed[i + 1]["text"].split()) > 3]
    chosen = sorted(rng.sample(pos, min(n_backchannel, len(pos))))
    out, last = [], ""
    for i, t in enumerate(parsed):
        out.append(t)
        if i in chosen:
            who = parsed[i + 1]["key"]
            pool = [w for w in BACKCHANNEL.get(roles[who], BACKCHANNEL_OTHER) if w != last]
            last = rng.choice(pool)
            out.append({"key": who, "flags": "~", "opts": "ov=%.2f" % rng.uniform(0.25, 0.6), "text": last})
    result = []
    for t in out:
        line = f"{t['key']}{t['flags']}" + (f"{{{t['opts']}}}" if t["opts"] else "") + f": {t['text']}"
        result.append({"line": line, "key": t["key"], "text": t["text"]})
    return result


def check(meta: dict, turns: list[dict]) -> tuple[list[str], list[str]]:
    errors, notes = [], []
    keys = set(meta["speakers"])
    spoken = "\n".join(t["text"] for t in turns)
    words = len(spoken.split())
    for t in turns:
        if t["key"] not in keys:
            errors.append(f"speaker {t['key']!r} not in header")
        if re.search(r"[\[\]<>]", t["text"]):
            errors.append(f"stage direction or bracket in spoken text: {t['text'][:50]!r}")
    for word in meta.get("must_not_mention", []):
        if word.lower() in spoken.lower():
            errors.append(f"deliberately absent information is mentioned: {word!r}")
    est = estimate_minutes(turns)
    if est < MIN_EST_MINUTES:
        errors.append(f"estimated {est:.1f} min (< {MIN_EST_MINUTES}): too short, about {int((MIN_EST_MINUTES - est) * 60 * WORDS_PER_SEC)} more words needed")
    unused = keys - {t["key"] for t in turns}
    if unused:
        errors.append(f"speakers never speak: {sorted(unused)}")
    notes.append(f"{words} words, {len(turns)} turns")
    return errors, notes


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", default=str(ROOT / "scenarios/_authoring"))
    ap.add_argument("--out", default=str(ROOT / "scenarios"))
    ap.add_argument("--no-enrich", action="store_true", help="do not add listener responses and hesitations (compile the authoring text as written)")
    ap.add_argument("--no-length-check", action="store_true", help="skip the length minimum (drafting)")
    args = ap.parse_args()
    out = Path(args.out)
    files = sorted(Path(args.src).glob("*.txt"))
    if not files:
        sys.exit(f"no authoring files in {args.src}")
    index, failed, taken = [], False, []
    for f in files:
        meta, turns = parse(f)
        meta["name"] = f"encounter_m3_{f.stem}"
        if not args.no_enrich:
            turns = enrich(turns, meta["speakers"], meta["name"])
        errors, notes = check(meta, turns)
        if args.no_length_check:
            errors = [e for e in errors if "too short" not in e]
        speakers = assign_voices(meta, taken)
        words = sum(len(t["text"].split()) for t in turns)
        est_min = estimate_minutes(turns)
        status = "OK " if not errors else "FAIL"
        print(f"{status} {meta['name']:<52} {notes[0]:<24} est {est_min:4.1f} min  " + "; ".join(errors))
        failed |= bool(errors)
        folder = out / meta["name"]
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "dialogue.txt").write_text("\n".join(t["line"] for t in turns) + "\n", encoding="utf-8")
        scenario = {
            "encounter_id": meta["name"], "title": meta["title"],
            "description": "Fictional synthetic consultation for Module 3 testing; not a real patient record or medical advice.",
            "difficulty": meta.get("difficulty", "varied"), "speakers": speakers,
            "design": meta.get("design", {}), "reference": meta.get("reference", {}),
            "conversation_features": {"specialty": meta.get("specialty"), "speaker_roles": sorted({s["role"] for s in speakers.values()}),
                                      "speaker_count": len(speakers), "turns": len(turns), "words": words, "estimated_minutes": round(est_min, 1)},
            "known_limitations": ["Fictional scripted dialogue, not a real consented clinical recording.",
                                  "Overlaps are simulated by mixing separately synthesized turns; real overlap is messier."],
        }
        (folder / "scenario.json").write_text(json.dumps(scenario, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        index.append({"folder": meta["name"], "title": meta["title"], "roles": scenario["conversation_features"]["speaker_roles"],
                      "turns": len(turns), "words": words, "estimated_minutes": round(est_min, 1), "reference": meta.get("reference", {})})
    (out / "SCENARIO_INDEX.json").write_text(json.dumps({"count": len(index), "scenarios": index}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(index)} scenarios -> {out}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
