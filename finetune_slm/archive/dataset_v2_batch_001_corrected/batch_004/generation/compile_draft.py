"""Compile an annotated draft (dialogue + compact annotation) into the exact Batch 001 input/label files and validate it.

The draft is authored by hand (dialogue and annotation).  This script only does the mechanical, error-prone part:
  * assigns segment timestamps (seeded by encounter id) and writes the input JSON in the Batch 001 format,
  * maps turn numbers in `evidence_ids` to EV_xxx ids, writes clinical_evidence (speaker, role, text, timestamps, supports),
  * keeps evidence/supports links symmetric, fills schema defaults (null / []), computes quality_checks flags,
  * runs the UNMODIFIED Batch 001 validator (validation/validate_dataset.py) on the result.
It never changes clinical content.  usage:
  python compile_draft.py draft_00501.json [--out-root DIR] [--no-write] [--quiet]
Exit status 0 only when the validator reports no errors.
"""
import argparse
import json
import random
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "validation"))
import validate_dataset as VD  # noqa: E402  (unmodified Batch 001 validator)

KEYS = {k: list(v["keys"]) for k, v in json.loads((ROOT / "schema/final_label_schema.json").read_text(encoding="utf-8"))["categories"].items()}
ARRAY_FIELDS = {"associated_symptoms", "aggravating_factors", "relieving_factors"}
LISTS = [p for p in KEYS if p != "chief_complaint" and not p.startswith("medical_history.")]
HIST = ["past_medical_history", "surgical_history", "family_history", "social_history"]
ROLES_UP = VD.ROLES


def ts_fix(x):
    return round(x, 2)


def build_input(d, errs):
    enc = d["encounter_id"]
    spk = d["speakers"]
    turns = d["turns"]
    rng = random.Random(int(enc) * 7919 + 13)
    if not re.fullmatch(r"\d{5}", enc):
        errs.append("encounter_id must be 5 digits")
    for sid, role in spk.items():
        if role not in ROLES_UP:
            errs.append(f"speaker {sid} role {role} not in {sorted(ROLES_UP)}")
    gaps, dur = [], []
    for i, t in enumerate(turns):
        if t["s"] not in spk:
            errs.append(f"turn {i + 1}: unknown speaker {t['s']}")
        w = len(t["t"].split())
        dur.append(max(0.9, w / rng.uniform(1.7, 2.3) + rng.uniform(0.4, 1.0)))
        g = rng.uniform(0.7, 3.0) if i else rng.uniform(0.3, 1.3)
        g += float(t.get("pause") or 0)
        gaps.append(g)
    total = sum(dur) + sum(gaps)
    if total > 525 and turns:   # long dialogue: speak/pause proportionally faster (never below ~0.75x of the base pace)
        f = 525 / total
        if f < 0.75:
            errs.append(f"dialogue too long: ~{total:.0f}s at base pace; cut words/turns")
        else:
            dur = [d * f for d in dur]
            gaps = [g * f for g in gaps]
            total = sum(dur) + sum(gaps)
    if total < 306 and turns:  # stretch natural gaps (never text) to reach the dataset's 300 s floor
        need = 306 - total
        cap = [max(0.0, 7.0 - g) for g in gaps]
        capsum = sum(cap)
        if capsum < need:
            errs.append(f"dialogue too short: ~{total:.0f}s even with maximal pauses; add turns / longer turns (need >= 300 s)")
        else:
            f = need / capsum
            gaps = [g + c * f for g, c in zip(gaps, cap)]
    segs, t_now = [], 0.0
    for i, t in enumerate(turns):
        t_now += gaps[i]
        st, en = ts_fix(t_now), ts_fix(t_now + dur[i])
        segs.append({"segment_id": f"SEG{i + 1:04d}", "speaker_id": t["s"], "role": spk.get(t["s"], "UNKNOWN"),
                     "start_seconds": st, "end_seconds": en, "duration_seconds": ts_fix(en - st), "text": t["t"].strip()})
        t_now = en
    return {"schema_version": "1.0", "encounter_id": enc, "segments": segs}


def fill(path, e):
    out = {}
    for k in KEYS[path]:
        if k == "confidence":
            out[k] = None
        elif k in e:
            out[k] = e[k]
        elif path == "allergies" and k == "severity":
            out[k] = "unknown"          # schema: severity is never graded in this version
        else:
            out[k] = [] if k in ARRAY_FIELDS else None
    extra = set(e) - set(KEYS[path])
    return out, extra


def build_label(d, inp, errs):
    enc, segs, L = d["encounter_id"], inp["segments"], d["label"]
    nseg = len(segs)
    ents = []   # (loc, entity dict) in schema order
    lab = {"encounter_id": enc, "extraction_status": "completed"}
    order, seen = [], set()
    for s in segs:
        if s["speaker_id"] not in seen:
            seen.add(s["speaker_id"])
            order.append(s)
    lab["encounter_metadata"] = {"encounter_date": None, "encounter_type": "outpatient_consultation", "language": "en",
                                 "primary_speakers": [{"speaker_id": s["speaker_id"], "role": s["role"].lower(), "role_confidence": None} for s in order]}
    cc_in = L.get("chief_complaint")
    if cc_in is None:
        errs.append("chief_complaint is required")
        cc_in = {}
    cc, extra = fill("chief_complaint", cc_in)
    if extra:
        errs.append(f"chief_complaint: unknown keys {sorted(extra)}")
    lab["chief_complaint"] = cc
    ents.append(("chief_complaint", cc))
    unknown_top = set(L) - {"chief_complaint", "medical_history", "quality_checks"} - set(LISTS)
    if unknown_top:
        errs.append(f"unknown label sections {sorted(unknown_top)}")
    for p in ["symptoms", "negative_findings"]:
        lab[p] = []
    mh = L.get("medical_history", {}) or {}
    bad = set(mh) - set(HIST)
    if bad:
        errs.append(f"unknown medical_history keys {sorted(bad)}")
    order_top = ["symptoms", "negative_findings", "medical_history", "medications", "allergies", "vital_signs", "physical_examination",
                 "review_of_systems", "clinical_conditions", "clinical_assessment", "procedures_and_investigations", "clinical_actions",
                 "follow_up", "clinical_uncertainties"]
    for p in order_top:
        if p == "medical_history":
            lab[p] = {}
            for h in HIST:
                lab[p][h] = []
                for i, e in enumerate(mh.get(h, []) or []):
                    f, extra = fill(f"medical_history.{h}", e)
                    if extra:
                        errs.append(f"medical_history.{h}[{i}]: unknown keys {sorted(extra)}")
                    lab[p][h].append(f)
                    ents.append((f"medical_history.{h}[{i}]", f))
            continue
        lab[p] = []
        for i, e in enumerate(L.get(p, []) or []):
            f, extra = fill(p, e)
            if extra:
                errs.append(f"{p}[{i}]: unknown keys {sorted(extra)}")
            lab[p].append(f)
            ents.append((f"{p}[{i}]", f))
    # evidence ids: turn numbers -> EV ids in turn order
    cited = set()
    for loc, e in ents:
        ids = e.get("evidence_ids") or []
        if not ids:
            errs.append(f"{loc}: evidence_ids empty (list the turn numbers that support it)")
        for n in ids:
            if not isinstance(n, int) or not 1 <= n <= nseg:
                errs.append(f"{loc}: evidence turn {n!r} is not a turn number 1..{nseg}")
            else:
                cited.add(n)
    evid = {n: f"EV_{i + 1:03d}" for i, n in enumerate(sorted(cited))}
    supports = {n: [] for n in cited}
    for loc, e in ents:
        raw = [n for n in (e.get("evidence_ids") or []) if isinstance(n, int) and n in evid]
        e["evidence_ids"] = [evid[n] for n in sorted(set(raw))]
        for n in set(raw):
            supports[n].append(loc)
    evidence = []
    for n in sorted(cited):
        s = segs[n - 1]
        evidence.append({"evidence_id": evid[n], "speaker_id": s["speaker_id"], "speaker_role": s["role"].lower(), "transcript_text": s["text"],
                         "start_timestamp": VD.ts(s["start_seconds"]), "end_timestamp": VD.ts(s["end_seconds"]), "supports": supports[n]})
    lab["clinical_evidence"] = evidence
    qin = L.get("quality_checks", {}) or {}
    syms = lab["symptoms"]
    temporal = any(s["duration"] or s["onset"] or s["temporality"] != "current" for s in syms) or bool(lab["medical_history"]["past_medical_history"])
    contra = list(qin.get("contradictions_detected", []))
    amb = list(qin.get("ambiguous_entities", []))
    lab["quality_checks"] = {"negation_detected": bool(lab["negative_findings"]), "temporality_detected": temporal,
                             "speaker_attribution_available": all(s["role"] != "UNKNOWN" for s in segs), "unsupported_clinical_claims": [],
                             "contradictions_detected": contra, "ambiguous_entities": amb,
                             "requires_clinician_review": bool(lab["clinical_uncertainties"] or contra or amb)}
    return lab


def compile_draft(d):
    errs = []
    inp = build_input(d, errs)
    lab = build_label(d, inp, errs)
    return inp, lab, errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("draft")
    ap.add_argument("--out-root", default=str(HERE / "staging"), help="directory that receives output/inputs and output/labels")
    ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    d = json.loads(Path(a.draft).read_text(encoding="utf-8"))
    inp, lab, errs = compile_draft(d)
    R = VD.validate_record(inp, lab)
    msgs = errs + [f"[{e['check']}] {e['message']}" for e in R.errors]
    if not a.no_write and not msgs:
        out = Path(a.out_root) / "output"
        (out / "inputs").mkdir(parents=True, exist_ok=True)
        (out / "labels").mkdir(parents=True, exist_ok=True)
        (out / "inputs" / f"encounter_{d['encounter_id']}.json").write_text(json.dumps(inp, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (out / "labels" / f"encounter_{d['encounter_id']}.json").write_text(json.dumps(lab, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    n, dur = len(inp["segments"]), inp["segments"][-1]["end_seconds"] if inp["segments"] else 0
    if msgs:
        print(f"{d['encounter_id']}: FAIL ({len(msgs)} problems) turns={n} duration={dur}s")
        for m in msgs[:40]:
            print("  -", m)
    elif not a.quiet:
        print(f"{d['encounter_id']}: PASS turns={n} duration={dur}s warnings={len(R.warnings)}")
        for w in R.warnings:
            print("  ~", w["check"], w["message"])
    sys.exit(1 if msgs else 0)


if __name__ == "__main__":
    main()
