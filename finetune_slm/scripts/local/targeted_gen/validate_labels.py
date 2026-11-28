"""Automatic label checks for the round-4 data, on top of the model verifier (verify_natural).

  python -m finetune_slm.scripts.local.targeted_gen.validate_labels --raw finetune_slm/data/round4_targeted/raw

Re-uses the backend rules that catch the live-test mistakes. A label is REJECTED when any of these fires on it:
  - safety_checks: allergy denied in its own cited turns, allergy vs medicine of the same family, vital number not in its cited turns
  - postprocess: contradicted negative, chief complaint or symptom name that is a sentence from speech
  - a symptom or negative-finding name of more than 6 words, a duplicated symptom (two entries that postprocess would merge)
  - the review-of-systems entry cites no turn in which the doctor asks anything
Result written into the raw file under "auto_checks" ({"ok": bool, "findings": [...]}). Nothing is changed in the label.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from clinical_extraction import evidence, postprocess, safety_checks  # noqa: E402

LINE = re.compile(r"^\[(SEG\d{4})\] (person_\d+) \(([A-Z_]+)\): (.*)$")


def compact_from_turns(turns_text: list[str]) -> dict:
    segs = []
    for i, line in enumerate(turns_text):
        m = LINE.match(line)
        if m:
            segs.append({"segment_id": m.group(1), "speaker_id": m.group(2), "role": m.group(3), "text": m.group(4), "start_seconds": float(i * 10), "end_seconds": float(i * 10 + 9)})
    return {"encounter_id": "x", "segments": segs}


def check_record(d: dict) -> dict:
    label = d["full_label"]
    compact = compact_from_turns(d["turns_text"])
    derived = evidence.resolve_all(label, compact)
    findings = [{"check": f["rule"], "detail": f["warning"]} for f in safety_checks.check(label, derived)]
    _, changes = postprocess.clean(label)
    for c in changes:
        if c["rule"] in ("contradicted_negative", "speech_wording", "chief_complaint_wording", "repeated_symptom"):
            findings.append({"check": c["rule"], "detail": json.dumps({k: v for k, v in c.items() if k != "evidence_ids"}, ensure_ascii=False)[:200]})
    for key, field in (("symptoms", "name"), ("negative_findings", "finding")):
        for i, s in enumerate(label.get(key) or []):
            if len(str(s.get(field) or "").split()) > 6:
                findings.append({"check": "long_name", "detail": f"{key}[{i}] {s.get(field)}"})
    seg_role = {s["segment_id"]: s["role"] for s in compact["segments"]}
    for i, r in enumerate(label.get("review_of_systems") or []):
        ids = r.get("evidence_ids") or []
        if ids and not any(seg_role.get(x) == "DOCTOR" for x in ids):
            findings.append({"check": "ros_without_doctor_question", "detail": f"review_of_systems[{i}] cites {ids}"})
    return {"ok": not findings, "findings": findings}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="finetune_slm/data/round4_targeted/raw")
    a = ap.parse_args()
    n = bad = 0
    for f in sorted((ROOT / a.raw).glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        d["auto_checks"] = check_record(d)
        f.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        n += 1
        if not d["auto_checks"]["ok"]:
            bad += 1
            print(f.stem, [x["check"] for x in d["auto_checks"]["findings"]])
    print(f"checked {n}; rejected by the automatic checks {bad}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
