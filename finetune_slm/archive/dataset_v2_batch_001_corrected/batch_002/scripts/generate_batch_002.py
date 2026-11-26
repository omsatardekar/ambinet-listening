"""Batch 002 driver: 500 NEW paired synthetic encounters, generated with the UNMODIFIED Batch 001 machinery (blueprint -> dialogue -> label -> validator).

Reuse: ../scripts/blueprint.py, dialogue.py, dialogue_pools*.py, content_core.py (imported, never edited) and ../validation/validate_dataset.py (validate_record / run).
New in Batch 002 (this folder only): new scenario profiles (b2_profiles_*.py), replaced/extended surface pools (b2_pools.py), a new plan (specialty x tier quotas,
new seed, ID range 20001-20500), batch-002 manifest/stats. Nothing is written outside batch_002/.

usage: python -B generate_batch_002.py [--n 500] [--batch 25] [--dry-run]
"""
import argparse
import csv
import json
import random
import statistics
import sys
import time
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
B2 = HERE.parent                      # .../dataset_v2_batch_001_corrected/batch_002
PARENT = B2.parent                    # .../dataset_v2_batch_001_corrected
sys.path.insert(0, str(PARENT / "scripts"))
sys.path.insert(0, str(PARENT / "validation"))
sys.path.insert(0, str(HERE))
import blueprint as BP            # noqa: E402  (unmodified Batch 001 module)
import b2_profiles_1, b2_profiles_2, b2_profiles_3  # noqa: E402,F401  (register Batch 002 profiles)
import b2_pools                   # noqa: E402
b2_pools.apply()
import dialogue as DL             # noqa: E402  (unmodified)
import validate_dataset as VD     # noqa: E402  (unmodified)
from content_core import PROFILES  # noqa: E402

MASTER_SEED = 20261114
ID_BASE = 20000                   # Batch 002 ids are 20001-20500 (Batch 001 uses 00001-00500: no overlap)
MAX_ATTEMPTS = 44
SPEC_QUOTA_B2 = [("General Medicine / Primary Care", 50), ("Cardiology", 45), ("Respiratory Medicine", 45), ("Gastroenterology", 45), ("Endocrinology", 45), ("Neurology", 45),
                 ("Musculoskeletal / Orthopaedics", 40), ("Dermatology", 40), ("Gynaecology", 40), ("ENT / Ophthalmology", 30), ("Infectious Diseases", 40), ("Urgent Care / Other", 35)]
SPEC_LABEL = {"Gynaecology": "Women's health (Gynaecology)", "ENT / Ophthalmology": "ENT / Ophthalmology", "Musculoskeletal / Orthopaedics": "Orthopaedics / Musculoskeletal"}
# planned tiers (30/45/25) -> generator complexity names: simple; medium = moderate; hard = complex (15%) + challenging (10%)
TIER_OF = {"simple": "Simple", "moderate": "Medium", "complex": "Hard", "challenging": "Hard"}
CPLX_QUOTA_B2 = [("simple", 150), ("moderate", 225), ("complex", 75), ("challenging", 50)]
assert sum(n for _, n in SPEC_QUOTA_B2) == 500 and sum(n for _, n in CPLX_QUOTA_B2) == 500


def b2_profiles(spec):
    return [p["key"] for p in PROFILES if p["spec"] == spec and p["key"].startswith("b2_")]


def make_plan(seed=MASTER_SEED):
    """[(spec, complexity, profile_key)] for ids 20001..20500. Complexity is allocated per specialty by largest remainder so every specialty
    receives the global 150/225/75/50 mix as closely as integers allow; the global totals are then forced exactly."""
    rng = random.Random(seed)
    total_c = {c: n for c, n in CPLX_QUOTA_B2}
    rows = []
    for spec, n in SPEC_QUOTA_B2:
        raw = {c: n * q / 500 for c, q in total_c.items()}
        base = {c: int(v) for c, v in raw.items()}
        rem = n - sum(base.values())
        for c in sorted(raw, key=lambda c: -(raw[c] - base[c]))[:rem]:
            base[c] += 1
        rows.append((spec, base))
    # force global totals exactly (move single slots between specialties if rounding drifted)
    for c, want in total_c.items():
        while sum(b[c] for _, b in rows) > want:
            sp = max(rows, key=lambda r: r[1][c])
            other = min((cc for cc in total_c if sum(b[cc] for _, b in rows) < total_c[cc]), key=lambda cc: sum(b[cc] for _, b in rows))
            sp[1][c] -= 1
            sp[1][other] += 1
    plan = []
    for spec, base in rows:
        cs = [c for c, k in base.items() for _ in range(k)]
        rng.shuffle(cs)
        keys = b2_profiles(spec)
        order = []
        while len(order) < len(cs):
            blk = keys[:]
            rng.shuffle(blk)
            order += blk
        for c, k in zip(cs, order):
            plan.append((spec, c, k))
    rng.shuffle(plan)
    return plan


# latent-age plausibility (the age is never spoken; it conditions history, medicines and surgery). Blueprints whose age falls outside the range are regenerated like any failed attempt.
AGE_RULES = {"b2_early_pregnancy_bleeding": (19, 42), "b2_pcos_irregular_cycles": (19, 40), "b2_acne_scarring_isotretinoin_review": (19, 40), "b2_perimenopause_hot_flushes": (44, 58),
             "b2_heavy_periods_iron_deficiency": (19, 50), "b2_exertional_wheeze_young_asthma": (19, 45), "b2_hip_osteoarthritis_groin": (50, 90), "b2_osteoporosis_fracture_risk": (55, 90),
             "b2_memory_difficulty_older": (60, 90), "b2_coronary_disease_antiplatelet_review": (50, 90), "b2_stable_angina_exertional": (45, 90), "b2_leg_oedema_heart_failure": (55, 90),
             "b2_covid_like_illness_older": (60, 90), "b2_sleep_apnoea_snoring": (30, 80), "b2_vaginal_discharge_thrush": (19, 65), "b2_ankle_sprain_ottawa": (19, 65),
             "b2_tonsillitis_recurrent": (19, 45), "b2_scabies_household": (19, 80)}


def planned_action_text_conflict(lab):
    """Same rule as Batch 001 final_schema_audit.py 'planned_not_conditional_text' (re-implemented here because that script is not importable): a PLANNED action whose evidence text also
    contains conditional/declined wording about the same words. Used as an extra generation-time acceptance gate so the existing final audit has nothing to flag."""
    import re as _re
    ev = {r["evidence_id"]: r for r in lab["clinical_evidence"]}
    out = []
    for a in lab["clinical_actions"]:
        if a["status"] != "planned":
            continue
        toks = [w[:5] for w in _re.findall(r"[a-z]{5,}", a["description"].lower()) if w not in ("arrange", "refer", "start", "follow", "consultation", "advise", "avoid")]
        txt = " ".join(ev[i]["transcript_text"].lower() for i in a["evidence_ids"])
        if [x for x in _re.split(r"(?<=[.!?])\s+", txt) if _re.search(r"hold off|not ordering|if it hasn't settled|we might do if|not now", x) and any(t in x for t in toks)]:
            out.append(a["description"])
    return out


def duplicate_generic_medicine(lab):
    """Two medication entries with the same normalized (generic) name, e.g. 'paracetamol' (knee pain) and the brand 'Dolo' (fever): found by the Batch 002 independent checks; the unmodified
    Batch 001 blueprint only de-duplicates on the spoken name. Used as an extra acceptance gate."""
    names = [(m["normalized_name"] or m["name"]).lower() for m in lab["medications"]]
    return sorted(n for n, c in __import__("collections").Counter(names).items() if c > 1)


def identity(bp):
    return (bp["profile"], tuple(sorted(s["norm"] for s in bp["syms"])), tuple(sorted(m["name"] for m in bp["meds"])), bp["assess"]["primary"], tuple(bp["assess"]["diffs"]))


def build(idx, slot, attempt):
    spec, cplx, key = slot
    bp = BP.make_blueprint(idx, spec, cplx, key, seed=MASTER_SEED + idx, attempt=attempt, orig_key=key)
    enc = DL.Enc(bp, 0).build()
    inp, lab, dur, n = enc.finalize(f"{idx:05d}")
    bp["noise_level"] = enc.noise_level
    bp["doctor_style"] = enc.doc_style
    bp["documentation_pause_seconds"] = round(getattr(enc, "pause_seconds", 0), 1)
    bp["batch"] = "002"
    bp["tier"] = TIER_OF[cplx]
    bp["master_seed_batch_002"] = MASTER_SEED
    return bp, inp, lab, dur, n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=500)
    ap.add_argument("--batch", type=int, default=25)
    ap.add_argument("--dry-run", action="store_true", help="print the plan and stop")
    a = ap.parse_args()
    plan = make_plan()[:a.n]
    if a.dry_run:
        print(Counter(p[0] for p in plan), Counter(p[1] for p in plan), len({p[2] for p in plan}), "profiles")
        return
    for d in ("output/inputs", "output/labels", "scenario_blueprints", "validation", "reports", "manifest"):
        (B2 / d).mkdir(parents=True, exist_ok=True)
    existing = list((B2 / "output" / "inputs").glob("*.json"))
    if existing:
        print(f"REFUSING: {len(existing)} Batch 002 inputs already exist in {B2 / 'output' / 'inputs'}; move them away first (this driver never overwrites).")
        sys.exit(2)
    log = [f"Batch 002 generation log ({time.strftime('%Y-%m-%d %H:%M:%S')}), master seed {MASTER_SEED}, ids {ID_BASE + 1}-{ID_BASE + len(plan)}",
           "All checks below are AUTOMATED. No clinician has reviewed any record.", ""]
    manifest, durs, segs_n, role_c, failed_attempts = [], [], [], Counter(), 0
    fail_checks = Counter()
    seen = set()
    for b0 in range(0, len(plan), a.batch):
        ids = list(range(b0 + 1, min(b0 + a.batch, len(plan)) + 1))
        log.append(f"== internal batch {b0 // a.batch + 1}: encounters {ID_BASE + ids[0]}-{ID_BASE + ids[-1]}")
        passed = 0
        for n in ids:
            idx = ID_BASE + n
            slot = plan[n - 1]
            for attempt in range(MAX_ATTEMPTS):
                use = slot
                if attempt >= 22:
                    alts = [k for k in b2_profiles(slot[0]) if k != slot[2]]
                    use = (slot[0], slot[1], alts[(attempt - 22) % len(alts)])
                    if attempt == 22:
                        log.append(f"   {idx} profile '{slot[2]}' could not satisfy validation in 22 attempts; trying sibling Batch 002 profiles")
                bp, inp, lab, dur, nseg = build(idx, use, attempt)
                R = VD.validate_record(inp, lab)
                lo, hi = AGE_RULES.get(bp["profile"], (0, 200))
                if not R.errors and not lo <= bp["age"] <= hi:
                    R.err("age_profile_plausibility", f"latent age {bp['age']} outside {lo}-{hi} for profile {bp['profile']}")
                if not R.errors and planned_action_text_conflict(lab):
                    R.err("planned_not_conditional_text", f"planned action shares evidence with conditional wording: {planned_action_text_conflict(lab)}")
                if not R.errors and duplicate_generic_medicine(lab):
                    R.err("duplicate_generic_medicine", f"same medicine listed twice under different names: {duplicate_generic_medicine(lab)}")
                if not R.errors and identity(bp) in seen:
                    R.err("duplicate_clinical_identity", "same profile/symptoms/medications/assessment as an earlier Batch 002 encounter")
                if not R.errors:
                    seen.add(identity(bp))
                    eid = f"{idx:05d}"
                    (B2 / "output/inputs" / f"encounter_{eid}.json").write_text(json.dumps(inp, indent=2, ensure_ascii=False), encoding="utf-8")
                    (B2 / "output/labels" / f"encounter_{eid}.json").write_text(json.dumps(lab, indent=2, ensure_ascii=False), encoding="utf-8")
                    (B2 / "scenario_blueprints" / f"blueprint_{eid}.json").write_text(json.dumps(bp, indent=1, ensure_ascii=False, default=list), encoding="utf-8")
                    passed += 1
                    roles = sorted({s["role"] for s in inp["segments"]})
                    manifest.append(dict(encounter_id=eid, specialty=bp["spec"], specialty_label=SPEC_LABEL.get(bp["spec"], bp["spec"]), tier=bp["tier"], complexity=bp["complexity"],
                                         profile=bp["profile"], planned_profile=slot[2], generation_attempt=attempt, duration_seconds=dur, segment_count=nseg,
                                         speaker_count=len({s["speaker_id"] for s in inp["segments"]}), speaker_roles="|".join(roles),
                                         input_file=f"output/inputs/encounter_{eid}.json", label_file=f"output/labels/encounter_{eid}.json",
                                         blueprint_file=f"scenario_blueprints/blueprint_{eid}.json", validation_status="PASS_AUTOMATED"))
                    durs.append(dur)
                    segs_n.append(nseg)
                    for r in roles:
                        role_c[r] += 1
                    if attempt:
                        log.append(f"   {idx} regenerated as attempt {attempt} after {attempt} failed attempt(s)")
                    break
                failed_attempts += 1
                for e in R.errors:
                    fail_checks[e["check"]] += 1
                log.append(f"   {idx} attempt {attempt} FAILED ({len(R.errors)} errors; {dict(Counter(e['check'] for e in R.errors).most_common(4))}) e.g. {R.errors[0]['message'][:140]}")
            else:
                log.append(f"   {idx} UNRESOLVED after {MAX_ATTEMPTS} attempts - not written")
                manifest.append(dict(encounter_id=f"{idx:05d}", specialty=slot[0], specialty_label=SPEC_LABEL.get(slot[0], slot[0]), tier=TIER_OF[slot[1]], complexity=slot[1],
                                     profile="", planned_profile=slot[2], generation_attempt="", duration_seconds="", segment_count="", speaker_count="", speaker_roles="",
                                     input_file="", label_file="", blueprint_file="", validation_status="FAILED_UNRESOLVED"))
        log.append(f"   batch result: {passed}/{len(ids)} passed automated validation")
        print(f"batch {b0 // a.batch + 1}: {passed}/{len(ids)}", flush=True)
    manifest.sort(key=lambda r: r["encounter_id"])
    cols = ["encounter_id", "specialty", "specialty_label", "tier", "complexity", "profile", "planned_profile", "generation_attempt", "duration_seconds", "segment_count",
            "speaker_count", "speaker_roles", "input_file", "label_file", "blueprint_file", "validation_status"]
    with open(B2 / "output" / "manifest.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(manifest)
    log += ["", f"total failed attempts (all regenerated or reported): {failed_attempts}", f"failed attempts by check: {dict(fail_checks.most_common())}"]
    (B2 / "validation" / "quality_log.txt").write_text("\n".join(log) + "\n", encoding="utf-8")
    rep, dup, evid = VD.run(B2, write=True, expected=len(plan))
    ok = [m for m in manifest if m["validation_status"] == "PASS_AUTOMATED"]
    stats = {"batch": "002", "master_seed": MASTER_SEED, "id_range": f"{ID_BASE + 1}-{ID_BASE + len(plan)}", "total_slots": len(manifest), "records_written": len(durs),
             "specialty_distribution": dict(Counter(m["specialty"] for m in ok)), "tier_distribution": dict(Counter(m["tier"] for m in ok)),
             "complexity_distribution": dict(Counter(m["complexity"] for m in ok)), "profiles_used": len({m["profile"] for m in ok}),
             "speaker_role_distribution_encounters_containing_role": dict(role_c), "average_duration_seconds": round(statistics.mean(durs), 2),
             "min_duration_seconds": min(durs), "max_duration_seconds": max(durs), "average_segment_count": round(statistics.mean(segs_n), 2),
             "min_segment_count": min(segs_n), "max_segment_count": max(segs_n), "validation_pass_count": rep["pass_count"], "validation_failure_count": rep["fail_count"],
             "generation_failed_attempts_regenerated": failed_attempts, "failed_attempts_by_check": dict(fail_checks), "duplicate_count": dup["duplicate_count"],
             "near_duplicate_pairs": len(dup["near_duplicate_pairs_jaccard_ge_0.45"]), "evidence_alignment_status": evid["alignment_status"],
             "evidence_facts_checked": evid["facts_checked"], "evidence_facts_grounded": evid["facts_grounded"], "validation_type": "automated only; no clinical or human review performed"}
    (B2 / "output" / "stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
    print(json.dumps(stats, indent=1))


if __name__ == "__main__":
    main()
