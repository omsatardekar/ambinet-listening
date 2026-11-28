"""Generate the round-4 targeted consultations (conversation + label) with the same writer model and converter as round 2.

  python -m finetune_slm.scripts.local.targeted_gen.generate_targeted --n 12 --first-id 40001 --workers 3     (pilot)

The only differences from natural_gen.generate_natural: the specs come from targeted_gen.blueprints (a situation plus one or two TARGET TRAPS taken from the live-test mistakes),
and the system prompt gets extra labelling rules (reason for visit, review of systems, speaker attribution, status words, negatives, clinical wording, allergies, vitals).
Output: finetune_slm/data/round4_targeted/raw/<id>.json (same format as round 2, so verify_natural can check it).
"""
from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "finetune_slm"))                     # direct_inference_baseline now lives in finetune_slm/
sys.path.insert(0, str(ROOT / "finetune_slm/data/round1_synthetic" / "codec"))
from finetune_slm.evaluation.judge_eval.client import Judge, JudgeError, parse_json_reply  # noqa: E402
from finetune_slm.scripts.local.natural_gen import generate_natural as G  # noqa: E402
from finetune_slm.scripts.local.targeted_gen.blueprints import build_specs  # noqa: E402

EXTRA_RULES = """
## Extra labelling rules for this batch (these override anything looser above)
- The transcript must read like SPEECH-TO-TEXT output of a real clinic: lower-case fillers ("err", "umm", "uh"), short fragments ("Mm.", "Of.", "Right."), numbers sometimes as words and sometimes as digits, an occasional misspelled drug name. No stage directions, no brackets.
- chief_complaint is the reason the patient came, as the patient states it (a short phrase). An opening remark, joke, apology, small talk or the trigger event (a relative's diagnosis) is NEVER the chief complaint.
- Review of systems / negative findings exist ONLY for things the doctor actually asked and the patient answered; cite exactly that question and answer. No entry for a system nobody asked about.
- Symptom and finding names are short clinical noun phrases (1 to 5 words), never sentences, never starting with I / we / my, never an idiom. Words of the speaker stay in the turn.
- A doctor's or nurse's explanation of what is happening in the body is not a symptom, history or social fact of the patient. A nurse's or caregiver's own life is not the patient's.
- Vital signs: only the CURRENT measurement, written normally. A previous value ("last time...") is not a vital sign. Never invent a number.
- Booked or arranged tests and visits are planned; only hedged ones are conditional. Never mark a booked item conditional.
- A medicine that someone has taken without a reaction is not an allergy. Never prescribe a drug of the same family as a recorded allergy.
- Keep every list entry unique: one entry per fact, no near-duplicates ("flushes" and "the flushes").
- The conversation must really contain every TARGET TRAP listed, and the label must follow its rule exactly.
"""
SYSTEM = G.SYSTEM.replace("## Output", EXTRA_RULES + "\n## Output", 1)
ALLERGY_TEXT = {"a": "the patient says no reaction ever and mentions having taken a penicillin-type antibiotic fine (no allergy)", "b": "the patient is unsure which drug caused a past reaction",
                "c": "the patient has a real allergy and describes the reaction", "d": "allergies are never discussed"}


def user_message(spec: dict) -> str:
    roles = ["PATIENT", "DOCTOR"] + spec["extra_speakers"]
    traps = "\n".join(f"- TRAP {i}: {t['happens']}\n  LABEL RULE: {t['label_rule']}" for i, t in enumerate(spec["traps"], 1))
    allergy = f"\nAllergy variant for this encounter: {ALLERGY_TEXT[spec['allergy_variant']]}." if spec.get("allergy_variant") else ""
    return (f"Write encounter {spec['id']}.\nSituation: {spec['situation']}\nSpeakers (exactly these roles, one person each unless the situation needs two parents): {', '.join(roles)}.\n"
            f"Patient manner: {spec['patient_style']}. Doctor manner: {spec['doctor_style']}. Language flavour: {spec['flavour']} (vocabulary and spelling; never a caricature).\n"
            f"Aim for about {spec['target_turns']} turns.\nTARGET TRAPS that must really occur in the conversation and be labelled exactly by the rule:\n{traps}{allergy}\n"
            "Also include these natural-speech features:\n" + "\n".join(f"- {f}" for f in spec["features"]) +
            "\nInvent your own concrete details (age, drugs, doses, names). Do not follow a fixed checklist order. Do not reuse an obvious template.")


def make_one(judge: Judge, spec: dict, outdir: Path) -> str:
    f = outdir / f"{spec['id']}.json"
    if f.exists():
        return "exists"
    err = "?"
    for attempt in range(2):
        try:
            reply = judge.call(SYSTEM, user_message(spec) + ("\n(Previous attempt was unusable: " + err + ". Fix it.)" if attempt else ""), max_output_tokens=24000, use_cache=attempt == 0)
            data = G.convert(spec, parse_json_reply(reply.text))
            data.update(spec=spec, generator=judge.deployment, usage={k: v for k, v in reply.usage.items() if isinstance(v, int)})
            f.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
            return "ok"
        except (JudgeError, ValueError, KeyError, TypeError) as exc:
            err = f"{type(exc).__name__}: {str(exc)[:200]}"
    return "FAILED " + err


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--first-id", type=int, default=40001)
    ap.add_argument("--out", default="finetune_slm/data/round4_targeted/raw")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--generator", default="JUDGE2")
    ap.add_argument("--skip", type=int, default=0)
    a = ap.parse_args()
    judge = Judge(a.generator)
    outdir = ROOT / a.out
    outdir.mkdir(parents=True, exist_ok=True)
    specs = build_specs(a.skip + a.n, a.first_id)[a.skip:]
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for s, r in zip(specs, ex.map(lambda s: make_one(judge, s, outdir), specs)):
            print(s["id"], s["family"], "+".join(t["key"] for t in s["traps"]), r, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
