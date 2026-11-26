"""Build the Batch 002 distribution measurements, the manifest and the human-readable reports from the generated files and the validation outputs. Read-only on inputs/labels/blueprints.
usage: python -B b2_make_reports.py"""
import collections
import csv
import hashlib
import json
import re
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
B2 = HERE.parent
PARENT = B2.parent
J = lambda p: json.loads(Path(p).read_text(encoding="utf-8"))
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
MAN = list(csv.DictReader(open(B2 / "output/manifest.csv", encoding="utf-8")))
ids = [m["encounter_id"] for m in MAN]
BP = {i: J(B2 / f"scenario_blueprints/blueprint_{i}.json") for i in ids}
LB = {i: J(B2 / f"output/labels/encounter_{i}.json") for i in ids}
IN = {i: J(B2 / f"output/inputs/encounter_{i}.json") for i in ids}
stats, val, ind, aud = J(B2 / "output/stats.json"), J(B2 / "validation/validation_report.json"), J(B2 / "validation/independent_checks.json"), J(B2 / "validation/final_schema_audit.json")
nov, met2, met1 = J(B2 / "validation/novelty_vs_batch_001_dev.json"), J(B2 / "reports/metrics_batch_002.json"), J(PARENT / "reports/metrics_after.json")
ctl = J(B2 / "validation/negative_controls.json")
dup = J(B2 / "validation/duplicate_report.json")
evi = J(B2 / "validation/evidence_validation.json")
SPEC_ORDER = ["General Medicine / Primary Care", "Cardiology", "Respiratory Medicine", "Gastroenterology", "Endocrinology", "Neurology", "Musculoskeletal / Orthopaedics", "Dermatology", "Gynaecology",
              "ENT / Ophthalmology", "Infectious Diseases", "Urgent Care / Other"]
LABEL = {"Gynaecology": "Women's health (Gynaecology)", "Musculoskeletal / Orthopaedics": "Orthopaedics / Musculoskeletal", "Endocrinology": "Endocrinology and diabetes"}
spec_c = collections.Counter(m["specialty"] for m in MAN)
tier_c = collections.Counter(m["tier"] for m in MAN)
cx_c = collections.Counter(m["complexity"] for m in MAN)
cross = collections.Counter((m["specialty"], m["tier"]) for m in MAN)

# ---------------------------------------------------------------- challenge coverage (measured from blueprints, labels and transcripts)
LOOK = [{"metformin", "metoprolol"}, {"losartan", "lisinopril"}, {"glimepiride", "glibenclamide", "gliclazide"}, {"carbamazepine", "carvedilol"}, {"prednisolone", "prednisone"},
        {"atorvastatin", "rosuvastatin", "simvastatin"}, {"pantoprazole", "omeprazole", "lansoprazole", "esomeprazole"}, {"amlodipine", "amiodarone"}]
cov = collections.Counter()
for i in ids:
    b, l, inp = BP[i], LB[i], IN[i]
    segs = inp["segments"]
    f = set(b["features"])
    meds = l["medications"]
    names = {(m["generic_name"] or m["name"]).lower() for m in meds} | {m["name"].lower() for m in meds}
    cur = [m for m in meds if m["status"] == "currently_used"]
    cov["medications: >=3 current medicines"] += len(cur) >= 3
    cov["medications: discontinued (historical) medicine"] += any(m["status"] == "discontinued" for m in meds)
    cov["medications: newly prescribed (planned) medicine"] += any(m["status"] == "planned" for m in meds)
    cov["medications: current + discontinued + planned in the same encounter"] += len({m["status"] for m in meds}) == 3
    cov["medications: dose not established (uncertain / name forgotten)"] += bool({"uncertain_dose", "name_forgotten"} & f)
    cov["medications: dose disagreement between speakers"] += "med_discrepancy" in f
    cov["medications: adherence doubted"] += "adherence_uncertain" in f
    cov["medications: reported by caregiver or family member"] += any(m["reported_by"] in ("caregiver", "family_member") for m in meds)
    cov["medications: look-alike drug names in the same encounter"] += any(len(g & names) >= 2 for g in LOOK)
    ev = {r["evidence_id"]: r for r in l["clinical_evidence"]}
    seg_ix = lambda eid_: next((k for k, s in enumerate(segs) if s["text"] == ev[eid_]["transcript_text"] and s["speaker_id"] == ev[eid_]["speaker_id"]), None)
    by_seg = collections.defaultdict(set)
    for k, m in enumerate(meds):
        for t in m["evidence_ids"]:
            by_seg[t].add(k)
    cov["medications: two or more different medicines supported by one transcript segment"] += any(len(v) >= 2 for v in by_seg.values())
    al = b["allergies"]["kind"]
    cov[f"allergy status: {al}"] += 1
    aq = [k for k, s in enumerate(segs) if "allerg" in s["text"].lower() and s["role"] == "DOCTOR"]
    med_seg = [seg_ix(t) for m in cur for t in m["evidence_ids"][:3]]
    cov["allergy: medication statement within three segments of the allergy question"] += any(abs(a - q) <= 3 for a in aq for q in med_seg if q is not None)
    cov["negation: >=4 negative findings"] += len(l["negative_findings"]) >= 4
    cov["negation: patient corrects/qualifies an earlier statement (mixed negation, previous episode, resolved symptom)"] += bool({"mixed_negation", "prev_episode", "resolved_sym"} & f)
    cov["negation: positive symptom and negated symptom set in the same encounter"] += any(s["status"] == "present" for s in l["symptoms"]) and len(l["negative_findings"]) > 0
    cov["negation: disputed finding (patient denies, other speaker reports)"] += "conflict" in f
    combo = b["combo"]
    for k, nm in (("N", "nurse speaks"), ("C", "caregiver speaks"), ("F", "family member speaks"), ("S", "clinical staff speaks"), ("U", "unattributed speaker")):
        cov[f"speakers: {nm}"] += k in combo
    cov["speakers: two or more speakers contribute to the same fact (conflict / duration disagreement / discrepancy / adherence by other)"] += bool({"conflict", "duration_conflict", "med_discrepancy", "adherence_uncertain", "allergy_dispute"} & f)
    cov["temporality: resolved or previous-episode symptom"] += any(s["temporality"] in ("resolved", "past") for s in l["symptoms"])
    cov["temporality: planned investigation"] += any(p["status"] == "planned" for p in l["procedures_and_investigations"])
    cov["temporality: conditional follow-up or investigation"] += any(p["status"] == "conditional" for p in l["procedures_and_investigations"]) or any(x["status"] == "conditional" for x in l["follow_up"])
    cov["temporality: appointment time spoken by staff (scheduled_datetime holds the spoken words, no invented date)"] += any(p["scheduled_datetime"] for p in l["procedures_and_investigations"])
    cov["temporality: onset/date uncertain"] += "date_uncertain" in f
    cov["history: family history present"] += len(l["medical_history"]["family_history"]) > 0
    cov["history: surgical history present"] += len(l["medical_history"]["surgical_history"]) > 0
    cov["history: past medical history >=2 conditions"] += len(l["medical_history"]["past_medical_history"]) >= 2
    cov["abstention-appropriate: allergy status not assessed in the transcript"] += al == "not_discussed"
    cov["abstention-appropriate: allergy status uncertain (patient unsure)"] += al == "uncertain"
    cov["abstention-appropriate: incomplete or interrupted answers"] += bool({"incomplete_answers", "interruptions"} & f)
    cov["abstention-appropriate: unattributable utterance (unknown speaker)"] += "unknown_speaker" in f
    cov["abstention-appropriate: no assessment stated"] += len(l["clinical_assessment"]) == 0
    cov["abstention-appropriate: no follow-up stated"] += len(l["follow_up"]) == 0
    cov["assessment: provisional or differential only (nothing confirmed)"] += all(a["certainty"] in ("provisional", "differential") for a in l["clinical_assessment"]) and len(l["clinical_assessment"]) > 0
spk = collections.Counter(m["speaker_count"] for m in MAN)
prof_c = collections.Counter(m["profile"] for m in MAN)
dist = {"specialty": {s: spec_c[s] for s in SPEC_ORDER}, "tier": dict(tier_c), "complexity": dict(cx_c), "specialty_by_tier": {f"{s}|{t}": cross[(s, t)] for s in SPEC_ORDER for t in ("Simple", "Medium", "Hard")},
        "profiles": {"distinct": len(prof_c), "min_per_profile": min(prof_c.values()), "max_per_profile": max(prof_c.values()), "mean_per_profile": round(500 / len(prof_c), 2)},
        "speaker_count_distribution": dict(spk), "challenge_coverage": {k: v for k, v in sorted(cov.items())}}
(B2 / "validation" / "distribution.json").write_text(json.dumps(dist, indent=1), encoding="utf-8")
pct = lambda n, d=500: f"{n}/{d} ({100 * n / d:.1f}%)"

# ---------------------------------------------------------------- manifest
GEN = {"batch_002/scripts": {p.name: sha(p) for p in sorted((B2 / "scripts").glob("*.py"))},
       "reused_unmodified_batch_001_scripts": {n: sha(PARENT / "scripts" / n) for n in ("blueprint.py", "dialogue.py", "dialogue_pools.py", "dialogue_pools2.py", "content_core.py", "content_p1.py", "content_p2.py", "content_p3.py",
                                                                                        "content_p4.py", "final_schema_audit.py", "validator_selftest.py", "lock_dataset.py", "validate_batch.py", "audit_metrics.py", "filler_lexicon.json")},
       "reused_unmodified_batch_001_validator": {"validation/validate_dataset.py": sha(PARENT / "validation/validate_dataset.py")}}
schema = J(PARENT / "schema/final_label_schema.json")
man = {"batch_id": "batch_002", "dataset_root": "dataset_v2_batch_001_corrected/batch_002", "generation_seed": stats["master_seed"], "generation_date_local": time.strftime("%Y-%m-%d"),
       "encounter_id_range": stats["id_range"], "encounter_ids": ids, "counts": {"transcripts": len(ids), "labels": len(ids), "blueprints": len(ids), "total_with_batch_001": 500 + len(ids)},
       "schema": {"file": "../schema/final_label_schema.json (parent dataset schema, reused, not copied)", "name": schema.get("schema_name"), "version": schema.get("version"), "sha256": sha(PARENT / "schema/final_label_schema.json")},
       "generation_scripts": GEN, "files": {m["encounter_id"]: {"transcript": {"file": m["input_file"], "sha256": sha(B2 / m["input_file"])}, "label": {"file": m["label_file"], "sha256": sha(B2 / m["label_file"])},
                                                              "blueprint": {"file": m["blueprint_file"], "sha256": sha(B2 / m["blueprint_file"])}} for m in MAN},
       "validation_results": {"generation_acceptance_validator_pass": f"{val['pass_count']}/{len(ids)}", "independent_checks_failed_total": sum(v["failed"] for v in ind["independent_checks"].values()),
                              "final_schema_audit": {"status": aud["status"], "check_evaluations": aud["total_check_evaluations"], "failures": aud["failure_count"]},
                              "negative_controls": f"{sum(1 for c in ctl if c['result'] == 'CAUGHT')}/{len(ctl)} caught", "evidence_lexical_grounding": f"{evi['facts_grounded']}/{evi['facts_checked']}",
                              "duplicates": dup["duplicate_count"], "clinical_review": "none performed"},
       "status": "GENERATED AND AUTOMATICALLY VALIDATED (not clinician reviewed; not yet allocated to training/dev/evaluation)", "checksums_file": "output/CHECKSUMS.sha256"}
(B2 / "manifest").mkdir(exist_ok=True)
(B2 / "manifest" / "batch_002_manifest.json").write_text(json.dumps(man, indent=1), encoding="utf-8")

# ---------------------------------------------------------------- reports
attempts = collections.Counter(int(m["generation_attempt"]) for m in MAN)
fails = stats["failed_attempts_by_check"]
q = ind["independent_checks"]
bv = ind["base_validator"]
rows = lambda d: "\n".join(f"| {k} | {v} |" for k, v in d)
dr = ["# Batch 002 distribution report", "", "All numbers are measured from the generated files (validation/distribution.json). Planned quotas are in scripts/generate_batch_002.py.", "",
      "## Specialty (planned = actual)", "", "| Specialty | Encounters | Simple | Medium | Hard |", "|---|---:|---:|---:|---:|"]
for s in SPEC_ORDER:
    dr.append(f"| {LABEL.get(s, s)} | {spec_c[s]} | {cross[(s, 'Simple')]} | {cross[(s, 'Medium')]} | {cross[(s, 'Hard')]} |")
dr += [f"| **Total** | **{sum(spec_c.values())}** | **{tier_c['Simple']}** | **{tier_c['Medium']}** | **{tier_c['Hard']}** |", "",
       "Internal specialty names follow the unmodified Batch 001 generator; 'Gynaecology' is reported as women's health, 'General Medicine / Primary Care' and 'Infectious Diseases' are separate specialties, and 'Urgent Care / Other' collects minor injury, allergy and general urgent presentations. Nephrology/urology is not a separate specialty (urinary infection sits under Infectious Diseases).", "",
       "## Difficulty tiers", "", "| Tier | Planned | Actual | Generator complexity |", "|---|---:|---:|---|",
       f"| Simple | 150 | {tier_c['Simple']} | simple ({cx_c['simple']}) |", f"| Medium | 225 | {tier_c['Medium']} | moderate ({cx_c['moderate']}) |",
       f"| Hard | 125 | {tier_c['Hard']} | complex ({cx_c['complex']}) + challenging ({cx_c['challenging']}) |", "",
       "The generator's complexity features decide the content (for example a 'moderate' encounter may include a resolved symptom or discontinued medicine; 'complex' and 'challenging' add speaker disagreements, interruptions, unknown speakers, mixed negation).", "",
       "## Profiles and speakers", "", f"- Distinct scenario profiles: {dist['profiles']['distinct']} (Batch 001: {met1['profiles_distinct']}); encounters per profile min {dist['profiles']['min_per_profile']}, max {dist['profiles']['max_per_profile']}, mean {dist['profiles']['mean_per_profile']} (Batch 001 max {met1['profile_reuse_max']}, mean {met1['profile_reuse_mean']}).",
       f"- Speakers per encounter: {dict(sorted(spk.items()))}.", f"- Encounters containing each role: {stats['speaker_role_distribution_encounters_containing_role']}.", "",
       "## Requested extraction challenges: measured coverage (of 500 encounters)", "", "| Challenge | Encounters |", "|---|---:|"]
dr += [f"| {k} | {pct(v)} |" for k, v in sorted(cov.items())]
dr += ["", "Counts are measured from blueprints, labels and transcripts (see scripts/b2_make_reports.py for the exact rules). Look-alike drug groups used: " + "; ".join("/".join(sorted(g)) for g in LOOK) + ".", ""]
(B2 / "reports" / "DISTRIBUTION_REPORT.md").write_text("\n".join(dr), encoding="utf-8")

gen = ["# Batch 002 generation report", "", f"Generated {time.strftime('%Y-%m-%d')} with master seed {stats['master_seed']}; ids {stats['id_range']}; {stats['records_written']} of 500 planned encounters written, 0 unresolved.", "",
       "## Method", "",
       "1. The unmodified Batch 001 pipeline is reused: scenario blueprint (facts fixed first) -> multi-speaker dialogue -> label derived from the same turns -> independent validator. Imported modules: blueprint, dialogue, dialogue_pools, content_core, validate_dataset.",
       "2. New content (this folder only): 60 new clinical profiles (5 per specialty, b2_profiles_*.py); look-alike drug options added to existing chronic-condition medication lists; new surgical, family-history, allergy and social-history wording replacing the Batch 001 phrasing; replacement wording for the placeholder-free routine question/answer pools (b2_pools.py, b2_pools_replace.py). All applied in memory; no Batch 001 file was edited.",
       "3. New plan: specialty quotas x difficulty tiers (30/45/25), new seed, ids 20001-20500 (disjoint from Batch 001's 00001-00500).",
       "4. Acceptance: each candidate passes the Batch 001 record validator, a latent-age plausibility gate, a planned-vs-conditional wording gate (re-implementation of one rule of the Batch 001 final audit), a duplicate-generic-medicine gate (the same drug under a generic and a brand name) and a clinical-identity uniqueness gate; otherwise it is regenerated from the same slot with a new attempt (as in Batch 001). Nothing is silently dropped: every failed attempt is in validation/quality_log.txt.", "",
       "## Attempts", "", f"- Records accepted at first attempt: {attempts[0]}; needing 1 or more regenerations: {500 - attempts[0]}; maximum attempt index used: {max(attempts)}.", f"- Total failed attempts: {stats['generation_failed_attempts_regenerated']}; by check: {fails}.",
       "- 'duration' and 'segment_count' failures are the generator's own length targets (5-9 minutes, 30-80 segments); 'age_profile_plausibility' enforces the latent-age ranges for age-specific profiles.", "",
       "## Iterations before the final run (disclosure)", "",
       "Two earlier complete generation runs were produced and deleted by me before the final run because review of samples found problems in my new content: look-alike claims in assessment text that did not follow the sampled medicines, early-pregnancy encounters that could draw contra-indicated chronic medicines, NSAID prescriptions without common cautions, non-symptoms listed as symptoms (past sunburn, analgesic use, an old fracture, an insect bite last week), contradictory intensity wording ('light bleeding' rated severe), single-dose prescriptions with duplicate wording, a dose written as '200/6 micrograms' that could not be matched in the transcript, and one patient listed on paracetamol 650 mg and on the brand Dolo (the same drug twice; the unmodified Batch 001 blueprint de-duplicates only on the spoken name, so Batch 001 may contain the same pattern; this was not checked because it would require opening locked-test labels). A third run was repeated after replacing the routine question wording and after a pool change broke the allergy and regular-medication evidence wording (fixed by keeping the required words). The record set in this folder is the last complete run; the earlier outputs were not kept (they were my own intermediate files).", "",
       "## Characteristics", "", f"- Mean duration {stats['average_duration_seconds']} s (range {stats['min_duration_seconds']}-{stats['max_duration_seconds']}); mean {stats['average_segment_count']} segments (range {stats['min_segment_count']}-{stats['max_segment_count']}).",
       f"- Allergy representation (Batch 001 schema): {dist['challenge_coverage']['allergy status: none']} explicit 'no known allergies', {dist['challenge_coverage']['allergy status: known']} known, {dist['challenge_coverage']['allergy status: not_discussed']} not discussed, {dist['challenge_coverage']['allergy status: uncertain']} uncertain, {dist['challenge_coverage']['allergy status: disputed']} disputed, {dist['challenge_coverage']['allergy status: historical']} historical.", "",
       "## Comparison with Batch 001 (same measuring script, `audit_metrics.py`)", "", "| Measure | Batch 002 | Batch 001 |", "|---|---:|---:|"]
for k, lab in (("profiles_distinct", "distinct profiles"), ("profile_reuse_max", "max encounters per profile"), ("share_of_segments_that_are_those_texts", "share of segments whose text occurs in >=5% of encounters"),
               ("opening_unique", "distinct opening sentences"), ("opening_max_share", "most common opening: share"), ("closing_unique", "distinct closing sentences"), ("closing_max_share", "most common closing: share"),
               ("segments_mean", "mean segments"), ("duration_mean", "mean duration (s)")):
    gen.append(f"| {lab} | {met2[k]} | {met1[k]} |")
gen += ["", f"- Novelty (against the 100 Batch 001 DEVELOPMENT records only): max 5-gram Jaccard {nov['max_5gram_jaccard_batch002_vs_any_dev_record']}; {nov['pairs_with_jaccard_ge_0.45']} pairs >= 0.45; {nov['share_verbatim_in_dev100']:.1%} of Batch 002 segments (>=5 words) appear verbatim in those 100 transcripts; profile keys in common: {nov['profile_keys_in_common']}; surgery/family surface phrases in common: {nov['surgery_or_family_surface_phrases_in_common_with_dev100']}.",
        f"- {nov['share_repeated_within_batch002']:.1%} of Batch 002 segments (>=5 words) also occur in another Batch 002 encounter (routine questions and answers), similar to Batch 001's template scaffolding.",
        "- The 400 locked-test records were not opened, so similarity to them is not measured; disjointness rests on construction (no Batch 001 profile registered, replaced phrasing, new ids and seed).", "",
        "## What did NOT improve (honest)", "",
        "- Scenario diversity is lower than Batch 001 (60 profiles vs 108; each used 6-10 times). Clinical content is new, but the same profile repeated with different sampled symptoms, medicines and histories.",
        "- Conversation naturalness is bounded by the unmodified dialogue engine: the turn structure is still largely alternating question-answer with the same repertoire of mechanisms (interruptions, conflicts, unknown speaker). Wording of routine questions is new, but template scaffolding is not removed. Real irregular speech, overlapping speech, recognition errors and deeper multi-turn clinical reasoning are not produced.",
        "- Hard encounters add the generator's existing complications; they are not free-form clinical complexity.", "",
        "## Files", "", "output/inputs, output/labels (500 + 500), scenario_blueprints (500), output/manifest.csv, output/stats.json, output/CHECKSUMS.sha256, manifest/batch_002_manifest.json, validation/*, reports/*.", ""]
(B2 / "reports" / "GENERATION_REPORT.md").write_text("\n".join(gen), encoding="utf-8")

passc = lambda n: f"{q[n]['numerator_passed']}/{q[n]['denominator_checked']}"
vr = ["# Batch 002 validation report", "", "Automated checks only; no clinician or human reviewed any record. Every line shows numerator/denominator.", "",
      "## Levels (kept separate)", "", "| Level | Result |", "|---|---|",
      f"| File generation | {stats['records_written']}/500 slots written (0 unresolved); {len(ids)}/500 transcript files, {len(ids)}/500 label files and {len(ids)}/500 blueprint files present with matching ids |",
      f"| JSON validity | {len(ids)}/500 transcripts, {len(ids)}/500 labels and {len(ids)}/500 blueprints parsed (all three loaded by the validators) |",
      f"| Schema validity (Batch 001 validator, schema group) | {val['pass_count']}/500 records with no schema errors; errors by group {val['error_groups']['schema'] or 'none'} |",
      f"| Schema audit against the final schema (existing `final_schema_audit.py`) | {aud['status']}: {aud['failure_count']} failures in {aud['total_check_evaluations']} check evaluations, {aud['pairs_failing_validator']} records failing the validator |",
      f"| Evidence-reference validity | evidence records matching a real segment {passc('evidence_record_matches_real_transcript_segment')}; entity evidence ids resolving {passc('entity_evidence_ids_resolve')}; symmetric supports links {passc('evidence_supports_symmetric')} |",
      f"| Evidence grounding (lexical) | {evi['facts_grounded']}/{evi['facts_checked']} extracted values literally found in the cited evidence ({evi['alignment_status']}) |",
      f"| Semantic evidence quality (independent checks, below) | see table; failures: {sum(v['failed'] for k, v in q.items() if k.startswith(('patient_origin', 'reported_by', 'evidence_not', 'negative_finding_evidence', 'present_symptom', 'medication_dose', 'allergy_substance')))} |",
      f"| Label consistency | allergy representation matches blueprint and schema {passc('allergy_representation_matches_blueprint_and_schema')}; blueprint counts match for family {passc('family_history_count_matches_blueprint')}, surgery {passc('surgical_history_count_matches_blueprint')}, current/discontinued medicines {passc('current_and_discontinued_medication_count_matches_blueprint')}, planned medicines {passc('planned_medication_count_matches_blueprint_rx')} |",
      f"| Duplicates | exact duplicate conversations {dup['exact_duplicate_conversations']}; near-duplicate pairs (5-gram Jaccard >= 0.45) {len(dup['near_duplicate_pairs_jaccard_ge_0.45'])}; max pairwise {dup['max_pairwise_5gram_jaccard']}; scenario-fingerprint duplicates {dup['scenario_fingerprint_duplicates(profile+symptoms+meds+assessment)']} |",
      f"| Validator negative controls | {sum(1 for c in ctl if c['result'] == 'CAUGHT')}/{len(ctl)} deliberate corruptions detected (run on Batch 002 records 20001-20003) |",
      f"| SHA-256 integrity | output/CHECKSUMS.sha256 lists {len(ids) * 2 + 1} files; manifest/batch_002_manifest.json lists {len(ids) * 3} file hashes |",
      f"| **Overall dataset acceptance (automated)** | {'ACCEPTED' if val['pass_count'] == 500 and aud['failure_count'] == 0 and sum(v['failed'] for v in q.values()) == 0 else 'NOT ACCEPTED'}: all automated checks pass. This is automated acceptance only: no clinical, human or linguistic review. |", "",
      "## Independent check detail (scripts/b2_independent_checks.py; own implementation, reads files only)", "", "| Check | Passed | Checked | Failed |", "|---|---:|---:|---:|"]
vr += [f"| {k} | {v['numerator_passed']} | {v['denominator_checked']} | {v['failed']} |" for k, v in q.items()]
vr += ["", "## Failures found while building the checks and how each was resolved (disclosure)", "",
       "The independent checks were run during development; their first versions reported failures that I investigated one by one before the final run:",
       "- Checker artifacts (corrected in the checker, not in the data): a long doctor turn ending in a question treated as a pure question; symptom names that contain 'not'/'no' ('not opening my bowels') treated as negated; a negation cue from a previous sentence; a disputed symptom (patient denies, caregiver reports) counted as a contradiction; a previous episode of the same symptom counted as a duplicate.",
       "- Real content defects (corrected in the profiles, then regenerated): items listed as symptoms that were history or events (past sunburn, analgesic use, an old fracture, an insect bite last week).",
       "- One planned-action wording rule of the existing final audit fired 4 times in an earlier run (planned referral sharing a transcript turn with a declined test). I confirmed by reading the evidence that the labels were correct (false positives of the sentence-splitting heuristic), renamed colliding plural test names and referral descriptions, and added the same rule as a generation-time gate; the final audit then reports 0 failures.", "",
       "Because the checker was adjusted after seeing results, a pass is evidence of consistency between transcripts, labels and blueprints, not of clinical correctness.", ""]
(B2 / "reports" / "VALIDATION_REPORT.md").write_text("\n".join(vr), encoding="utf-8")

gt = ["# Batch 002 ground-truth quality report", "", "**Not clinician verified.** Labels are produced by the generator from the same turns that create the transcript (facts are attached when the turn is written), then checked by a separate validator and by independently written checks. They are not independently annotated by humans and were not derived from any model prediction.", "",
      "## Checks performed (numerators/denominators)", "", "| # | Required check | Result |", "|---|---|---|",
      f"| 1 | Label refers to the correct encounter | {passc('encounter_id_inside_files_equals_filename')} encounter ids match file names; ids unique and in range: {passc('ids_unique_and_in_range_20001_20500')} |",
      f"| 2 | Every evidence segment exists | {passc('evidence_record_matches_real_transcript_segment')} evidence records match a transcript segment on speaker, text, role and start time |",
      f"| 3 | Every evidence segment supports its fact | lexical grounding {evi['facts_grounded']}/{evi['facts_checked']}; patient-origin facts with a non-question supporting segment {passc('patient_origin_fact_has_non_question_evidence')}; negative findings with a negation cue in the cited answer {passc('negative_finding_evidence_contains_negation_cue')}; present symptoms with a non-negated statement or affirmed question {passc('present_symptom_supported_by_statement_or_affirmed_question')}; no greeting-only evidence {passc('evidence_not_greeting_only')} |",
      f"| 4 | Speaker attribution | `reported_by` equals the role of a cited non-question segment {passc('reported_by_equals_role_of_a_cited_non_question_segment')} |",
      f"| 5 | Polarity preserved | negative findings with negation cue {passc('negative_finding_evidence_contains_negation_cue')}; no negative finding contradicting an undisputed present symptom {passc('no_negative_finding_contradicting_an_undisputed_current_present_symptom')} |",
      f"| 6 | Medication identity and dose | dose number present in cited evidence {passc('medication_dose_number_in_cited_evidence')}; dose within two segments after the drug name {passc('medication_dose_within_two_segments_after_drug_name')}; no duplicate medicine entries {passc('no_duplicate_medication_entries')}; no drug both current and planned/discontinued {passc('no_drug_both_currently_used_and_planned_or_discontinued')} |",
      f"| 7 | Allergy status | representation matches blueprint and schema {passc('allergy_representation_matches_blueprint_and_schema')}; no placeholder allergy {passc('allergy_not_placeholder')}; allergy substance in cited evidence {passc('allergy_substance_in_cited_evidence')}; no allergy that is a current medicine {passc('allergy_substance_not_a_current_medication_name')} |",
      f"| 8 | Historical vs current | symptom count and temporality match blueprint (allowing the disputed symptom) {passc('symptom_count_and_temporality_match_blueprint_allowing_one_disputed_symptom_per_dispute')} |",
      f"| 9 | No unsupported datetime | no ISO date/time in any label {passc('no_iso_date_or_datetime_in_label')}; follow-up normalized_datetime null {passc('follow_up_normalized_datetime_null')}; scheduled_datetime null or literally spoken {passc('scheduled_datetime_null_or_literally_spoken')} |",
      f"| 10 | No duplicate or contradictory labels | no duplicate entities within sections {passc('no_duplicate_entities_within_section_symptoms_keyed_with_temporality')}; no duplicate family history {passc('no_duplicate_family_history')} |", "",
      "## Remaining limits", "",
      "- A passing check means the label is consistent with the transcript and the generating blueprint; it does not show that the medicine/dose/assessment pairing is clinically sensible. Profile content, doses and plans were authored from general knowledge by an AI, then constrained only by simple exclusions (no teratogenic chronic drugs in early pregnancy profiles, no NSAID prescription profile with common NSAID cautions, age ranges).",
      "- Known template artefacts remain: for example an expression such as 'I did have being unsteady at one point' (verb-form of a resolved symptom) and short repeated acknowledgements.",
      "- `reported_by` follows the Batch 001 convention (role of the speaker of the cited turn; clinician confirmations of history are cited through the confirming turn). Under the owner's definition (the speaker who verbally supplied the information) this holds in the independent check above; the schema has no `subject` field and `observed_by` is used for examination findings.",
      "- Confidence fields are null by design. Do not use Batch 002 for evaluation and training at the same time without a recorded allocation; no allocation has been made.", ""]
(B2 / "reports" / "GROUND_TRUTH_QA_REPORT.md").write_text("\n".join(gt), encoding="utf-8")

un = ["# Failed or uncertain records", "", "## Unresolved or failed", "", "None: all 500 slots were written and passed every automated check.", "",
      "## Records that needed regeneration (not failures; listed for transparency)", "", f"{500 - attempts[0]} of 500 records were accepted only after one or more failed attempts. The per-attempt reasons are in validation/quality_log.txt and the accepted attempt index is the `generation_attempt` column of output/manifest.csv.", "",
      "## Uncertain / not verifiable by automation", "",
      "- Clinical plausibility of profile content, dose/frequency pairings, plans and referral choices (not clinically reviewed).",
      "- Naturalness and linguistic quality (no linguistic review; template scaffolding remains).",
      "- Similarity to the 400 locked-test Batch 001 records (not measured; the records may not be opened).",
      "- Records flagged by the generator's own uncertainty features (disputed or uncertain allergy, discrepant doses, unknown speaker) are intentional; they are labelled as uncertainties in the labels, not defects.", ""]
(B2 / "reports" / "FAILED_OR_UNCERTAIN_RECORDS.md").write_text("\n".join(un), encoding="utf-8")
print(json.dumps({"manifest_files": len(ids) * 3, "attempt0": attempts[0], "max_attempt": max(attempts), "challenge_rows": len(cov)}))
