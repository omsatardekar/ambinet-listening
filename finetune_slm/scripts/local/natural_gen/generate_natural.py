"""Generate natural (medium and hard) consultation + label pairs for the second training round.

  python -m finetune_slm.scripts.local.natural_gen.generate_natural --n 6 --first-id 30001 --out finetune_slm/data/round2_natural/raw --workers 3      (pilot)

For each spec (blueprints.py) one call to the GENERATOR model (JUDGE2 deployment by default, a different model from the verifier JUDGE) returns
the conversation (turns) and the label with evidence given as turn numbers. This script converts it to the exact training format:
  input  : short prompt + lines `[SEG0001] person_1 (DOCTOR): text`  (person ids by order of first appearance)
  label  : full structure (checked with the project's schema validator) -> compact form (compact_codec.compact)
and writes finetune_slm/data/round2_natural/raw/<id>.json (spec, turns, full label, compact label, checks). Nothing here is clinician reviewed; verify_natural.py is the next step.
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
from compact_codec import compact, expand  # noqa: E402
from finetune_slm.evaluation.judge_eval.client import Judge, JudgeError, parse_json_reply  # noqa: E402
from finetune_slm.scripts.local.natural_gen.blueprints import build_specs  # noqa: E402

FINAL = json.loads((ROOT / "finetune_slm/archive/dataset_v2_batch_001_corrected/schema/final_label_schema.json").read_text(encoding="utf-8"))
CATS = {c.lower(): c for c in ("ENT", "cardiovascular", "constitutional", "dermatological", "endocrine", "gastrointestinal", "genitourinary", "musculoskeletal", "neurological", "ophthalmological", "other", "psychiatric", "respiratory")}
ROLE_FIELDS = ("reported_by", "observed_by", "stated_by", "requested_by", "responsible_person")

SYSTEM = """You write realistic synthetic outpatient consultations and the exact ground-truth extraction record for each, to train a small clinical information extraction model.
Everything is fictional. Quality and honesty matter more than length.

## The conversation
Write it as people REALLY talk, not as a checklist: uneven, with interruptions, hesitation ("um", "well, actually"), self-corrections, trailing off, tangents with no clinical content, side remarks, patients using everyday words, doctors who do not ask about everything, answers that arrive late or sideways. Vary openings and closings; do not reuse stock phrases. Doctors state an assessment only if they really would. Spoken numbers appear the way people say them (words and digits mixed). Roles: DOCTOR, PATIENT, NURSE, CAREGIVER (paid or live-in carer), FAMILY_MEMBER (parent, spouse, adult child, sibling), CLINICAL_STAFF (receptionist, HCA, phlebotomist, pharmacy technician). A young child is the PATIENT and speaks only a little. Use ONLY the speakers named in the request. Medicines, doses, vitals and tests must be clinically plausible (SBP-DBP >= 20, HR 35-190, temp 34.5-42 C, SpO2 80-100, RR 8-40). Each turn is one person speaking, one to four sentences; no stage directions; no real people.

## The label (what a careful clinician would record from THIS transcript only)
Output the label with these keys (omit any key whose value would be empty/null, and any empty section): chief_complaint, symptoms, negative_findings, medical_history {past_medical_history, surgical_history, family_history, social_history}, medications, allergies, vital_signs, physical_examination, review_of_systems, clinical_conditions, clinical_assessment, procedures_and_investigations, clinical_actions, follow_up, clinical_uncertainties, quality_checks {contradictions_detected, ambiguous_entities}.
Field names and enum values are exactly those of the schema given below. Never write confidence. Do not write dates (encounter_date is null).
In every entity `evidence_ids` is a list of 1 or 2 TURN NUMBERS (1-based, integers) that support it (include the question turn when the answer only makes sense with it).
`reported_by`, `observed_by`, `stated_by`, `requested_by`, `responsible_person` are lower-case roles of someone who speaks in the cited turns.
Rules:
- Use only what is said. Never infer, never invent. A topic nobody raised produces nothing (no allergy line if allergies were never mentioned).
- A denied finding goes in negative_findings (status absent, assertion negative, with the doctor's question + answer turns), never in symptoms. If a speaker first denies and later reports it, record only the final, fuller version as a symptom and do NOT also record the denial.
- A doctor's question is not a fact. A medicine the patient takes is not an allergy. A medicine belonging to someone else is not the patient's. A stopped medicine is status discontinued; a medicine never taken is not recorded. Dose, frequency, route, indication belong only to the medicine they were said for; if a speaker corrects a value, keep only the corrected value.
- Write numbers in the label in normal form even if spoken as words ("a hundred and fifty milligrams" -> "150 mg"; "one-forty over ninety" -> "140/90"), but do not make a vague amount exact ("five-ish years" stays approximate in duration.normalized, value null).
- Doctor impressions go in clinical_assessment only if the doctor stated one (certainty provisional or differential, never a confirmed diagnosis). "Let's see what the tests say" is not an assessment.
- Plan items: status planned only when stated as arranged; conditional when hedged ("if it does not settle", "we might"); advice to the patient is a clinical_action counselling/recommended/patient. Every planned or conditional investigation is both a procedures_and_investigations entry and a clinical_actions investigation entry with the same status and evidence. A planned medication is a medications entry (status planned, reported_by doctor) plus a clinical_actions medication entry (planned, doctor). Follow-up: follow_up entry (type consultation; time_reference as spoken; status conditional iff it starts with "if ", else planned) plus a twin clinical_actions entry (action_type follow_up, description "Follow-up consultation", same status/time_reference {value, normalized_date null}, responsible doctor) with the same evidence.
- Allergies: if allergies were asked and denied: negative_findings {finding "Allergies", normalized_name "No known allergies", status absent, assertion negative}; if reported: allergies entry (severity "unknown", reaction only if said); if possible/unsure: status uncertain + an allergy_uncertain uncertainty; if one person denies and another recalls: allergy_disputed.
- Uncertainties (clinical_uncertainties; type, description (one plain sentence), related_entities like "symptoms[0]" / "medications[1]" (0-based positions in your own lists), resolution_status unresolved | partially_resolved | resolved, evidence_ids): date_uncertain (nobody can date something), uncertain_dose (dose given tentatively), adherence_uncertain (taken as prescribed? doubted by someone), incomplete_medication_name (cannot name the medicine; name = the description), allergy_uncertain, allergy_disputed, duration_disagreement (two durations), conflicting_statement (one denies, another reports; the symptom certainty disputed), medication_discrepancy (two sources give different doses; dose null), unknown_speaker. Add one line to quality_checks.contradictions_detected for each conflicting_statement, medication_discrepancy, allergy_disputed and duration_disagreement. Only add an uncertainty when the conversation really contains it; never "just in case".
- Statuses: symptom status present|resolved, temporality current|past|resolved; certainty certain|uncertain|disputed; medication status currently_used|discontinued|planned; past_medical_history status ongoing; clinical_conditions only for conditions someone states, status existing.
- symptoms.category must be EXACTLY one of: ENT, cardiovascular, constitutional, dermatological, endocrine, gastrointestinal, genitourinary, musculoskeletal, neurological, ophthalmological, other, psychiatric, respiratory (fever, tiredness, weight change, feeling cold = constitutional; sleep complaints = neurological).
- Only chief_complaint is a single object; everything else is a list.

## Output
Return ONE JSON object and nothing else: {"speakers": {"A": "PATIENT", "B": "DOCTOR", ...}, "turns": [{"s": "A", "t": "text"}, ...], "label": {...}}. Speaker keys are single capital letters.

## Schema (enums and key sets)
""" + json.dumps({"categories": FINAL["categories"], "enums": FINAL["enums"], "nested_keys": FINAL["nested_keys"]}, ensure_ascii=False)


def user_message(spec: dict) -> str:
    roles = ["PATIENT", "DOCTOR"] + spec["extra_speakers"]
    return (f"Write encounter {spec['id']}.\nSituation: {spec['situation']}\nDifficulty: {spec['difficulty']} (hard = several of the natural-speech traps below really happen, and some details stay unresolved; "
            f"medium = messy but mostly clear).\nSpeakers (exactly these roles, one person each unless the situation needs two parents): {', '.join(roles)}.\nPatient manner: {spec['patient_style']}. Doctor manner: {spec['doctor_style']}. "
            f"Language flavour: {spec['flavour']} (vocabulary and spelling; never a caricature).\nAim for about {spec['target_turns']} turns.\nNatural-speech features that must really occur in the conversation and be handled correctly in the label:\n"
            + "\n".join(f"- {f}" for f in spec["features"]) + "\nInvent your own concrete details (age, drugs, doses, names). Do not follow a fixed checklist order.")


def convert(spec: dict, out: dict) -> dict:
    """Generator output -> training example. Raises ValueError with a short reason if unusable."""
    turns = out["turns"]
    roles = out["speakers"]
    if not turns or any(t["s"] not in roles for t in turns):
        raise ValueError("turn with unknown speaker")
    order: dict[str, str] = {}
    for t in turns:
        if t["s"] not in order:
            order[t["s"]] = f"person_{len(order) + 1}"
    used = {k: v for k, v in roles.items() if k in order}
    lines = [f"[SEG{i:04d}] {order[t['s']]} ({roles[t['s']]}): {' '.join(str(t['t']).split())}" for i, t in enumerate(turns, 1)]
    n = len(turns)

    def fix(node):
        if isinstance(node, dict):
            res = {}
            for k, v in node.items():
                if k == "evidence_ids":
                    ids = []
                    for x in (v if isinstance(v, list) else [v]):
                        xi = int(x)
                        if not 1 <= xi <= n:
                            raise ValueError(f"evidence turn {xi} out of range")
                        sid = f"SEG{xi:04d}"
                        if sid not in ids:
                            ids.append(sid)
                    if not ids:
                        raise ValueError("empty evidence_ids")
                    res[k] = ids[:2]
                elif k == "category" and isinstance(v, str) and v.lower() in CATS:
                    res[k] = CATS[v.lower()]
                elif k in ROLE_FIELDS and isinstance(v, str):
                    res[k] = v.lower()
                else:
                    res[k] = fix(v)
            return res
        if isinstance(node, list):
            return [fix(x) for x in node]
        return node

    label = fix(out["label"])
    prim = sorted(used.items(), key=lambda kv: (kv[1] != "DOCTOR", kv[1] != "PATIENT", order[kv[0]]))
    label["encounter_id"] = spec["id"]
    label["extraction_status"] = "completed"
    label["encounter_metadata"] = {"encounter_date": None, "encounter_type": "outpatient_consultation", "language": "en",
                                   "primary_speakers": [{"speaker_id": order[k], "role": v.lower(), "role_confidence": None} for k, v in prim]}
    qc = label.get("quality_checks") or {}
    label["quality_checks"] = {"negation_detected": True, "temporality_detected": True, "speaker_attribution_available": "UNKNOWN" not in used.values(), "unsupported_clinical_claims": [],
                               "contradictions_detected": qc.get("contradictions_detected", []), "ambiguous_entities": qc.get("ambiguous_entities", []), "requires_clinician_review": True}
    warnings: list = []
    full = expand(label, warnings=warnings)
    if warnings:
        raise ValueError("unknown keys: " + "; ".join(warnings[:3]))
    from direct_inference_baseline.evaluation import schema_validator as SV
    rep = SV.validate(full)
    if not rep.compliant:
        raise ValueError("schema violations: " + "; ".join(v["message"] for v in rep.violations[:4]))
    return {"turns_text": lines, "speaker_map": {order[k]: v for k, v in used.items()}, "full_label": full, "compact_label": compact(full)}


def make_one(judge: Judge, spec: dict, outdir: Path) -> str:
    f = outdir / f"{spec['id']}.json"
    if f.exists():
        return "exists"
    err = "?"
    for attempt in range(2):
        try:
            reply = judge.call(SYSTEM, user_message(spec) + ("\n(Previous attempt was unusable: " + err + ". Fix it.)" if attempt else ""), max_output_tokens=24000, use_cache=attempt == 0)
            data = convert(spec, parse_json_reply(reply.text))
            data.update(spec=spec, generator=judge.deployment, usage={k: v for k, v in reply.usage.items() if isinstance(v, int)})
            f.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
            return "ok"
        except (JudgeError, ValueError, KeyError, TypeError) as exc:
            err = f"{type(exc).__name__}: {str(exc)[:200]}"
    return "FAILED " + err


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--first-id", type=int, default=30001)
    ap.add_argument("--out", default="finetune_slm/data/round2_natural/raw")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--generator", default="JUDGE2")
    ap.add_argument("--skip", type=int, default=0, help="skip the first N specs (to continue a later slice)")
    a = ap.parse_args()
    judge = Judge(a.generator)
    outdir = ROOT / a.out
    outdir.mkdir(parents=True, exist_ok=True)
    specs = build_specs(a.skip + a.n, a.first_id)[a.skip:]
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for s, r in zip(specs, ex.map(lambda s: make_one(judge, s, outdir), specs)):
            print(s["id"], s["family"], s["difficulty"], r, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
