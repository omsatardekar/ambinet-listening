"""Batch 001 driver: scenario-first generation of 500 paired encounters.

blueprint (facts) -> dialogue (Module-2 transcript) -> ground truth derived
from the same turns -> automated validation per internal batch of 25.
Failed records are logged (never silently dropped) and regenerated from a new
blueprint attempt of the same specialty/complexity/profile slot.

usage: python generate_batch.py [--root <dataset dir>] [--n 500] [--batch 25]
"""
import argparse
import csv
import json
import statistics
import sys
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT_DEFAULT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT_DEFAULT / "validation"))
import blueprint as BP      # noqa: E402
import dialogue as DL       # noqa: E402
import validate_dataset as VD  # noqa: E402

MASTER_SEED = 20260101
MAX_ATTEMPTS = 44
MAX_FILLERS = 12


def build_encounter(idx, slot, attempt):
    spec, cplx, key, orig = slot
    bp = BP.make_blueprint(idx, spec, cplx, key, seed=MASTER_SEED + idx, attempt=attempt, orig_key=orig)
    enc = DL.Enc(bp, 0).build()
    inp, lab, dur, n = enc.finalize(f"{idx:05d}")
    bp["noise_level"] = enc.noise_level
    bp["doctor_style"] = enc.doc_style
    bp["documentation_pause_seconds"] = round(getattr(enc, "pause_seconds", 0), 1)
    return bp, inp, lab, dur, n, 0


def identity(bp):
    """clinical identity of a scenario (a different case, not different wording): same profile, same symptom set,
    same current medicines and same assessment would be 'the same case' -- must be unique across the batch."""
    return (bp["profile"], tuple(sorted(s["norm"] for s in bp["syms"])),
            tuple(sorted(m["name"] for m in bp["meds"])), bp["assess"]["primary"], tuple(bp["assess"]["diffs"]))


def write_record(root, idx, bp, inp, lab):
    eid = f"{idx:05d}"
    (root / "output" / "inputs" / f"encounter_{eid}.json").write_text(json.dumps(inp, indent=2, ensure_ascii=False), encoding="utf-8")
    (root / "output" / "labels" / f"encounter_{eid}.json").write_text(json.dumps(lab, indent=2, ensure_ascii=False), encoding="utf-8")
    (root / "scenario_blueprints" / f"blueprint_{eid}.json").write_text(json.dumps(bp, indent=1, ensure_ascii=False, default=list), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(ROOT_DEFAULT))
    ap.add_argument("--n", type=int, default=500)
    ap.add_argument("--batch", type=int, default=25)
    a = ap.parse_args()
    root = Path(a.root)
    for d in ("output/inputs", "output/labels", "scenario_blueprints", "validation"):
        (root / d).mkdir(parents=True, exist_ok=True)
    for sub in ("output/inputs", "output/labels", "scenario_blueprints"):  # fresh batch: never mix with an earlier run
        for f in (root / sub).glob("*.json"):
            f.unlink()
    plan = BP.rebalanced_plan(MASTER_SEED)[:a.n]
    log = [f"Batch 001 generation log  ({time.strftime('%Y-%m-%d %H:%M:%S')})",
           "All checks below are AUTOMATED. No clinician has reviewed any record.", ""]
    manifest, durs, segs_n, role_c, fail_attempts = [], [], [], Counter(), 0
    seen_identity = set()
    for b0 in range(0, len(plan), a.batch):
        batch_ids = list(range(b0 + 1, min(b0 + a.batch, len(plan)) + 1))
        log.append(f"== internal batch {b0 // a.batch + 1}: encounters {batch_ids[0]:05d}-{batch_ids[-1]:05d}")
        passed = 0
        for idx in batch_ids:
            slot = plan[idx - 1]
            for attempt in range(MAX_ATTEMPTS):
                use = slot
                if attempt >= 22:  # this profile cannot reach 5 minutes of genuine content at this complexity: try a sibling profile
                    alts = [p["key"] for p in BP.PROFILES if p["spec"] == slot[0] and p["key"] != slot[2]]
                    use = (slot[0], slot[1], alts[(attempt - 22) % len(alts)], slot[3])
                    if attempt == 22:
                        log.append(f"   {idx:05d} profile '{slot[2]}' could not reach the duration range in 22 attempts; trying sibling profiles")
                bp, inp, lab, dur, n, F = build_encounter(idx, use, attempt)
                R = VD.validate_record(inp, lab)
                if not R.errors and identity(bp) in seen_identity:
                    R.err("duplicate_clinical_identity", "same profile/symptoms/history/medications/assessment/plan as an earlier encounter")
                if not R.errors:
                    seen_identity.add(identity(bp))
                    write_record(root, idx, bp, inp, lab)
                    passed += 1
                    spk = sorted({s["role"] for s in inp["segments"]})
                    spk_n = len({s["speaker_id"] for s in inp["segments"]})
                    manifest.append(dict(encounter_id=f"{idx:05d}", specialty=bp["spec"], complexity=bp["complexity"],
                                         duration_seconds=dur, speaker_count=spk_n, speaker_roles="|".join(spk),
                                         input_file=f"output/inputs/encounter_{idx:05d}.json",
                                         label_file=f"output/labels/encounter_{idx:05d}.json", validation_status="PASS_AUTOMATED"))
                    durs.append(dur)
                    segs_n.append(n)
                    for r in {s["role"] for s in inp["segments"]}:
                        role_c[r] += 1
                    if attempt:
                        log.append(f"   {idx:05d} corrected: regenerated as attempt {attempt} after {attempt} failed attempt(s)")
                    break
                fail_attempts += 1
                top = Counter(e["check"] for e in R.errors)
                log.append(f"   {idx:05d} attempt {attempt} FAILED ({len(R.errors)} errors; {dict(top.most_common(4))}) e.g. {R.errors[0]['message'][:150]}")
            else:
                log.append(f"   {idx:05d} UNRESOLVED after {MAX_ATTEMPTS} attempts - not written")
                manifest.append(dict(encounter_id=f"{idx:05d}", specialty=slot[0], complexity=slot[1], duration_seconds="",
                                     speaker_count="", speaker_roles="", input_file="", label_file="", validation_status="FAILED_UNRESOLVED"))
        log.append(f"   batch result: {passed}/{len(batch_ids)} passed automated validation")
        print(f"batch {b0 // a.batch + 1}: {passed}/{len(batch_ids)}", flush=True)
    manifest.sort(key=lambda r: r["encounter_id"])
    with open(root / "output" / "manifest.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["encounter_id", "specialty", "complexity", "duration_seconds", "speaker_count", "speaker_roles",
                                          "input_file", "label_file", "validation_status"])
        w.writeheader()
        w.writerows(manifest)
    log.append("")
    log.append(f"total failed attempts (all regenerated or reported): {fail_attempts}")
    (root / "validation" / "quality_log.txt").write_text("\n".join(log) + "\n", encoding="utf-8")
    # dataset-level validation (also writes the three validation reports)
    rep, dup, evid = VD.run(root, write=True)
    spec_c = Counter(m["specialty"] for m in manifest if m["validation_status"] == "PASS_AUTOMATED")
    cpl_c = Counter(m["complexity"] for m in manifest if m["validation_status"] == "PASS_AUTOMATED")
    segcount_soft = sum(1 for n in segs_n if VD.SOFT_SEG[0] <= n <= VD.SOFT_SEG[1])
    stats = {
        "total_records": len(manifest), "records_written": len(durs),
        "specialty_distribution": dict(spec_c), "complexity_distribution": dict(cpl_c),
        "speaker_role_distribution_encounters_containing_role": dict(role_c),
        "speaker_count_distribution": dict(Counter(m["speaker_count"] for m in manifest)),
        "average_duration_seconds": round(statistics.mean(durs), 2), "min_duration_seconds": min(durs), "max_duration_seconds": max(durs),
        "average_segment_count": round(statistics.mean(segs_n), 2), "min_segment_count": min(segs_n), "max_segment_count": max(segs_n),
        "segment_count_within_35_70": segcount_soft, "segment_count_outside_35_70": len(segs_n) - segcount_soft,
        "validation_pass_count": rep["pass_count"], "validation_failure_count": rep["fail_count"],
        "generation_failed_attempts_regenerated": fail_attempts,
        "duplicate_count": dup["duplicate_count"], "near_duplicate_pairs": len(dup["near_duplicate_pairs_jaccard_ge_0.45"]),
        "evidence_alignment_status": evid["alignment_status"], "evidence_facts_checked": evid["facts_checked"],
        "evidence_facts_grounded": evid["facts_grounded"],
        "validation_type": "automated only; no clinical or human review performed",
    }
    (root / "output" / "stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
    print(json.dumps(stats, indent=1))


if __name__ == "__main__":
    main()
