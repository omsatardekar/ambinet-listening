# Changelog: Batch 001 -> Batch 001 corrected

Per-record detail: `reports/record_changes.csv` (500 rows: original vs new profile, segments, duration, original non-compliant categories,
confidence fields, allergy representation, noise level, plan/assessment mode, age band) and `reports/comparison.json`.

## Counts (original vs corrected, 500 records)

| Item | Count |
|---|---|
| Transcript records modified | 500 (all regenerated) |
| Label records modified | 500 |
| Semantic category corrections (original symptoms with category outside the vocabulary: 92 "reported" + 53 gynaecological/nephrological/general) | 145 |
| `confirmed_by` fields removed | 361 |
| Confidence fields set to null | 17,977 |
| Records using an allergy representation the original could not express (not discussed / historical / disputed / reaction stated as unknown) | 130 |
| Encounters whose allergy scenario differs from the original | 352 |
| Conversations revised for naturalness (new engine, no filler, persona wording subsets) | 500 |
| Conversations with restrained transcript imperfections | 235 |
| Encounters moved to a different clinical profile (same specialty/complexity) | 87 |
| Distinct profiles | 83 -> 108 |
| Specialty / complexity quotas | unchanged (exact) |

## Changes by area

* **Schema/semantics:** controlled symptom-category vocabulary; `category` no longer encodes attribution/uncertainty; `confirmed_by`
  removed everywhere (generator, validator, docs); all `confidence`/`role_confidence` fields kept but `null`; action status vocabulary
  `planned | completed | recommended | conditional`; allergy status `reported | uncertain | historical | disputed`; new uncertainty types
  `duration_disagreement`, `adherence_uncertain`, `allergy_disputed`.
* **Allergy/negatives:** "no known allergies" is an explicit negative finding only when said; if allergies are never discussed nothing is
  extracted; reported-with-unknown-reaction, historical and patient-vs-caregiver disputes are separate cases.
* **Dialogue engine:** filler mechanisms removed (chart-loading talk, transport chat, "give me a second", explanatory monologues,
  repeated-dose checks); per-encounter random subsets of widened phrase pools; five macro structures (standard, history-first,
  vitals-first, early examination, medication-first); combined lifestyle questions; self-corrections, partial drug names
  ("something called amlo... amlodipine, maybe 5 milligrams"), patient/caregiver duration disagreement, adherence uncertainty.
* **Scenarios:** 25 added profiles (e.g. headache with uncertain onset, possible seizure history, Bell's palsy, ectopic beats without chest
  pain, drug-induced ankle swelling, multifactorial breathlessness, biliary colic, shingles, scabies, diabetic foot, stress incontinence,
  PCOS); age band conditions history/medicines/surgery; chief complaint can be a non-classic symptom of the profile; diagnoses that an
  assessment presupposes (e.g. COPD flare-up) are now present in the history; acute presentations are never given an empty plan.
* **Clinical actions:** plan modes none/single/standard/rich; follow-up and safety-net advice optional; conditional (considered but not
  ordered) investigations; a patient-requested test that the doctor declines produces no entity; counselling is `recommended`.
* **Transcript realism:** optional restrained imperfections applied after merging, with clinical literals and all numbers masked.
* **Validator:** new checks for categories, null confidence, absent `confirmed_by`, allergy consistency, temporality, planned/completed/
  conditional wording, action support, unresolved-dose-disagreement; reports split into schema / evidence / clinical consistency /
  dialogue realism; 22 negative controls.
* **Driver:** same slot plan as the original (ids, specialty, complexity), clinical-identity uniqueness gate, regeneration of failed attempts
  logged in `validation/quality_log.txt`.

## Not changed

Module-2 transcript schema, label top-level structure and category names, evidence conventions (`supports` as JSON locations, `person_N`
speaker IDs, `MM:SS` timestamps), roles, `scenario_blueprints/` as internal-only data.
