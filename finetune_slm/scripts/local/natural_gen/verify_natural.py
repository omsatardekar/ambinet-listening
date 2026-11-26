"""Independent check of every generated natural encounter by a DIFFERENT model than the one that wrote it (verifier = JUDGE = gpt-5.4, writer = JUDGE2 = grok-4.7).

  python -m finetune_slm.scripts.local.natural_gen.verify_natural --raw finetune_slm/data/round2_natural/raw --workers 4

Two passes, both with the frozen judge prompts or a new omission prompt:
  precision : is each label fact supported by the transcript?  (frozen PRECISION_SYSTEM, the same prompt used for the model evaluation)
  omissions : which clinically important things the speakers said are missing from the label?
Result stored in the raw file under "verify"; accepted = no contradicted fact, no critical error, at most 2 unsupported/partial facts, no critical omission and at most 3 omissions (after the repair round: at most 3 such facts, 4 omissions, 1 of them critical).
A rejected record gets ONE repair round by the writer (transcript unchanged) and is checked again; the first verdict is kept as "initial_verify".
Caveat to report: labels are model-written and model-verified, not clinician reviewed.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from finetune_slm.evaluation.judge_eval.client import Judge, parse_json_reply  # noqa: E402
from finetune_slm.evaluation.judge_eval.flatten import flatten  # noqa: E402
from finetune_slm.evaluation.judge_eval.judge_run import _ask  # noqa: E402
from finetune_slm.evaluation.judge_eval.prompts import PRECISION_SYSTEM, PRECISION_VERDICTS, facts_text, precision_user  # noqa: E402

NL = chr(10)
LINE = re.compile(r"^\[(SEG\d{4})\] (person_\d+) \(([A-Z_]+)\): (.*)$")
OMIT_SYSTEM = """You are a meticulous clinical documentation auditor. You get a consultation transcript and the facts an extraction system recorded from it. List the clinically important things the speakers actually said that are NOT recorded (or are recorded wrongly): current or planned medicines with doses, symptoms with their key details, denied findings that were asked and answered, allergies, vital signs, examination findings, history, investigations, plans, follow-up, and real doubts or disagreements between speakers. Ignore small talk, pleasantries and things nobody said. Do not suggest facts that are not in the transcript.
"critical" is true only if the omission could mislead care (a medicine, dose, allergy, flipped negation or red-flag symptom missing).
Reply with ONE JSON object and nothing else: {"omissions":[{"text":"what is missing","critical":false,"segments":["SEG0001"]}]}  (empty list if nothing important is missing)."""


def is_accepted(v: dict, revised: bool = False) -> bool:
    """Acceptance rule (applied to the stored verdict, so it can be re-evaluated without new calls).
    Precision first: no contradicted fact, no critical error, few unsupported/partial facts. Recall: no more than one CRITICAL omission (a medicine, dose, allergy, flipped
    negation or red flag); minor omissions are not a reason to reject (a clinical record is not exhaustive). Before the repair round: at most 2 bad facts and 0 critical omissions;
    after it: at most 3 bad facts and 1 critical omission."""
    crit_om = sum(1 for o in v["omissions"] if o.get("critical"))
    if v["n_contradicted"] or v["n_critical"]:
        return False
    return (v["n_bad"] <= 3 and crit_om <= 1) if revised else (v["n_bad"] <= 2 and crit_om == 0)


def check(judge: Judge, d: dict, revised: bool = False) -> dict:
    segs = [{"segment_id": m.group(1), "speaker_id": m.group(2), "role": m.group(3), "text": m.group(4)} for l in d["turns_text"] if (m := LINE.match(l))]
    compact = {"segments": segs}
    facts = flatten(d["full_label"])
    pv, _ = _ask(judge, PRECISION_SYSTEM, precision_user(compact, facts), [x["fid"] for x in facts], PRECISION_VERDICTS, 6000 + 120 * len(facts))
    tr = NL.join(f"{s['segment_id']} [{s['role']}]: {s['text']}" for s in segs)
    om = []
    for attempt in range(2):
        try:
            msg = "TRANSCRIPT" + NL + tr + NL + NL + "RECORDED FACTS" + NL + facts_text(facts)
            om = parse_json_reply(judge.call(OMIT_SYSTEM, msg, max_output_tokens=6000, use_cache=attempt == 0).text).get("omissions", [])
            break
        except Exception:                                                   # noqa: BLE001
            om = [{"text": "omission check failed", "critical": True, "segments": []}] if attempt else om
    bad = [v for v in pv if v["verdict"] in ("unsupported", "partially_supported", "contradicted")]
    contra = [v for v in pv if v["verdict"] == "contradicted"]
    crit = [v for v in pv if v.get("critical")]
    ok = None
    v = {"n_facts": len(facts), "n_bad": len(bad), "n_contradicted": len(contra), "n_critical": len(crit), "n_omissions": len(om), "accepted": ok,
            "bad": [{**v, "text": next(x["text"] for x in facts if x["fid"] == v["fid"])} for v in bad], "omissions": om, "verifier": judge.deployment}
    v["accepted"] = is_accepted(v, revised)
    return v


def revise(writer: Judge, d: dict, v: dict) -> dict:
    """One repair round: the writer model gets the transcript, its label and the verifier's findings and returns a corrected label (the transcript is not changed)."""
    from finetune_slm.scripts.local.natural_gen.generate_natural import SYSTEM, convert
    issues = [f"- Fact not fully supported ({b['verdict']}): {b['text']} -- {b.get('reason', '')}" for b in v["bad"]] + [f"- Missing from the label: {o['text']}" for o in v["omissions"]]
    head = ("Below are a consultation transcript, the current label (evidence shown as segment ids: SEG0007 = turn 7) and an auditor's findings. "
            'Return ONE JSON object {"label": {...}} with the corrected label, in the same format as before (evidence_ids as turn-number integers, 1 or 2 per item). '
            "Fix a finding only if it is right according to the transcript; if the auditor is wrong, keep the item. Add missing facts and uncertainties (follow the uncertainty recipes), "
            "remove or correct unsupported details. Keep everything else as it is.")
    user = (head + NL + NL + "TRANSCRIPT" + NL + NL.join(d["turns_text"]) + NL + NL + "CURRENT LABEL" + NL + json.dumps(d["compact_label"], ensure_ascii=False)
            + NL + NL + "AUDITOR FINDINGS" + NL + NL.join(issues))
    out = parse_json_reply(writer.call(SYSTEM, user, max_output_tokens=24000).text)
    turns = [{"s": "p" + l.split(" ")[1][7:], "t": l.split("): ", 1)[1]} for l in d["turns_text"]]
    speakers = {"p" + k[7:]: r for k, r in d["speaker_map"].items()}
    fixed = convert(d["spec"], {"speakers": speakers, "turns": turns, "label": out["label"]})
    assert fixed["turns_text"] == d["turns_text"], "transcript changed in revision"
    return fixed


def verify_one(judge: Judge, writer: Judge, f: Path) -> str:
    try:
        return _verify_one(judge, writer, f)
    except Exception as exc:                                                   # noqa: BLE001  (e.g. file still being written; picked up on the next pass)
        return f"ERROR {type(exc).__name__}: {str(exc)[:120]}"


def _verify_one(judge: Judge, writer: Judge, f: Path) -> str:
    d = json.loads(f.read_text(encoding="utf-8"))
    if "verify" in d:
        return "done"
    v = check(judge, d)
    if not v["accepted"]:
        try:
            fixed = revise(writer, d, v)
            d["initial_verify"], d["initial_compact_label"], d["initial_full_label"] = v, d["compact_label"], d["full_label"]
            d["compact_label"], d["full_label"] = fixed["compact_label"], fixed["full_label"]
            v = check(judge, d, revised=True)
            v["revised"] = True
        except Exception as exc:                                              # noqa: BLE001
            v["revision_failed"] = f"{type(exc).__name__}: {str(exc)[:150]}"
    d["verify"] = v
    f.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    return ("accepted" if v["accepted"] else "rejected") + (" (after revision)" if v.get("revised") else "")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="finetune_slm/data/round2_natural/raw")
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    judge, writer = Judge("JUDGE"), Judge("JUDGE2")
    files = sorted((ROOT / a.raw).glob("*.json"))
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for f, r in zip(files, ex.map(lambda f: verify_one(judge, writer, f), files)):
            print(f.stem, r, flush=True)
    tot = []
    for f in files:
        try:
            tot.append(json.loads(f.read_text(encoding="utf-8")).get("verify"))
        except Exception:                                                     # noqa: BLE001
            pass
    tot = [t for t in tot if t]
    print(f"verified {len(tot)}; accepted {sum(t['accepted'] for t in tot)}; mean facts {sum(t['n_facts'] for t in tot) / max(1, len(tot)):.1f}; "
          f"bad facts {sum(t['n_bad'] for t in tot)}; contradicted {sum(t['n_contradicted'] for t in tot)}; omissions {sum(t['n_omissions'] for t in tot)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
