# dataset_v2_batch_001 — locked evaluation benchmark (500 paired encounters)

Synthetic, role-labelled, timestamped clinical encounters in the **Module 2 transcript format**, each paired with a
**ground-truth clinical extraction JSON** that follows the project's `clinical_extraction_schema.json`.

> **Evaluation only.** Do not add these records, their labels, or near-duplicates to any SLM training set.
> Verify the lock with `python scripts/lock_dataset.py --verify` (SHA-256 of all 1,001 evaluation files).

> **What "validated" means here.** Every check in this directory is *automated*. **No clinician has reviewed any
> record**, and no record is marked human-reviewed anywhere. The dialogue is *synthetic, template-composed* text
> (see Limitations); it is not recorded speech and not LLM-free of artefacts.

The previous bulk dataset was not present in this repository (`git ls-files` shows no dataset or generator), so nothing was
reused and nothing needs deleting. This directory is new and self-contained.

## Layout

```
output/inputs/encounter_00001.json … 00500.json   Module-2 transcripts (schema_version 1.0, segments[])
output/labels/encounter_00001.json … 00500.json   ground-truth extraction (same encounter_id)
output/manifest.csv      encounter_id, specialty, complexity, duration_seconds, speaker_count, speaker_roles, input_file, label_file, validation_status
output/stats.json        measured statistics (see below)
output/CHECKSUMS.sha256  lock file
scenario_blueprints/     INTERNAL generation blueprints (facts fixed before any dialogue). NOT evaluation data.
validation/              validate_dataset.py + validation_report.json, evidence_validation.json, duplicate_report.json, quality_log.txt
scripts/                 generate_batch.py, validate_batch.py, validator_selftest.py, lock_dataset.py + content/dialogue modules
```

## Method (scenario-first)

1. **Blueprint** (`blueprint.py`): one of 83 hand-authored clinical profiles in 12 specialties is sampled with its symptoms,
   durations, severities, negatives, history, medicines, allergies, vitals, exam findings, assessment, plan, follow-up,
   participants and complexity "features" (medication discrepancy, conflicting caregiver statement, uncertain dates/doses/
   allergy, forgotten drug name, interruptions, incomplete answers, mixed negation, unattributable speaker …).
   Quotas (12 specialties × 4 complexities) are exact by construction. Coherence rules: no allergy-conflicting or duplicate-class
   prescriptions, no history that contradicts the assessment, sex/surgery sanity, plausible vitals, BMI computed from weight/height.
2. **Dialogue** (`dialogue.py`): the blueprint is realised turn by turn in varied order and style with hesitations,
   repetitions, approximate dates, interruptions, corrections and recaps. Question order, phrasing and speaker combinations vary.
3. **Transcript**: Module-2 JSON. Consecutive same-speaker turns are merged into one segment (as a diariser would output);
   timing comes from word counts, silent gaps for examination/vitals, and per-speaker speech rates. No overlapping speech.
4. **Ground truth**: each fact is created *at the moment the turn that states it is written*, and that turn is attached as its
   evidence. A field the dialogue never states stays `null`/empty (no inferred doses, durations, severities or dates).
5. **Validation per internal batch of 25** (`validate_dataset.validate_record`). A failing record is logged in
   `validation/quality_log.txt` and regenerated from a new blueprint attempt for the same slot; nothing is silently dropped.

## Schema decisions you should confirm

`clinical_extraction_schema.json` is a single worked example whose `vital_signs`, `physical_examination`, `review_of_systems`,
`clinical_conditions`, `clinical_assessment` and `clinical_uncertainties` are empty arrays, and whose evidence `supports` use IDs
(`SYM_001`) that do not exist as fields. Outer structure, category names and all populated nested fields are unchanged. I had to decide:

| Topic | Decision |
|---|---|
| Entity shapes for the six empty categories | Instantiated (key sets enforced by the validator; see `EXPECT` in `validate_dataset.py`). `clinical_conditions` has one extra key, `confirmed_by`. |
| `supports` | JSON locations that resolve inside the label, e.g. `symptoms[2]`, `medical_history.family_history[0]`, `chief_complaint`. Links are bidirectional with each entity's `evidence_ids`. |
| Speaker IDs | `person_N` (matches the transcript), not the example's `Speaker_N`. Roles are lowercase in labels, uppercase in transcripts. |
| Timestamps | `MM:SS`, floor of the segment's start/end seconds. |
| Evidence text | The full supporting segment text, so it always matches the transcript. |
| `confidence` | Fixed by rule (1.0 explicit, 0.6 uncertain/disputed); it is *not* a model estimate. `role_confidence` 1.0, or 0.5 for UNKNOWN. |
| Negated "no allergies / surgeries / medicines / conditions" | `negative_findings` (e.g. `Allergies` → "No known allergies"). |
| New prescriptions | `medications` with `status: "planned"` plus a `clinical_actions` entry; patient's own medicines are `currently_used` / `discontinued`. |
| Unresolved conflicts | Recorded as `clinical_uncertainties` + `quality_checks.contradictions_detected`; conflicting dose is left `null`, never "corrected". |
| `encounter_date` | Always `null` (never spoken). |
| The supplied schema file | It already parses as valid JSON on disk (no trailing comma present in the file). |

## Measured results (from `output/stats.json`)

500/500 inputs, 500/500 labels, all IDs match. Specialty and complexity quotas met exactly. Duration 302.5–539.8 s
(mean 412.2 s ≈ 6.9 min); segments 37–80 (mean 60.0; 437 of 500 within 35–70). All 500 pass automated validation after
32 failed generation attempts were regenerated. Evidence alignment: 22,184/22,184 extracted values found in their cited evidence.
Duplicates: 0 exact, 0 near-duplicate pairs (max 5-gram Jaccard 0.071), 0 repeated clinical identities.

## What the automated checks do and do not prove

Checked: JSON/schema, key sets, ID/segment/speaker/role consistency, chronology and overlap, duration/segment ranges, evidence
record ↔ transcript alignment (speaker, role, text, timestamps), `supports` resolution and symmetry, attribution of each fact to a
speaker who actually said it, **lexical grounding of every value** (names, doses, durations, severities, frequencies, factors,
vitals, findings, assessments, follow-ups…), negation cues, allergy-vs-prescription conflicts, negated-vs-present contradictions,
vital plausibility/BMI, unconfirmed diagnoses not marked confirmed, silent-correction guard, blueprint leakage, duplicates.
`scripts/validator_selftest.py` corrupts valid records 15 ways and confirms each is rejected (15/15).

Not checked (needs a clinician): whether the clinical content is *medically* correct or the doses sensible, whether
dialogue sounds like real clinic speech, and subtle ambiguity (e.g. two people could be read as answering).

## Limitations

* **Language is template-composed**, from hand-written phrase pools with randomised structure and disfluency. It is varied
  (152 distinct opening lines, no opening > 3.0%, max pairwise 5-gram Jaccard 0.071) but has recognisable recurring
  stock phrases (most common structural doctor lines appear in ≲ 20% of encounters) and clean punctuation that real ASR would not give.
* 83 clinical profiles: specialties are broad but each profile recurs ~6 times with different facts; unusual presentations and rare diseases are absent.
* 63 encounters (all complex/challenging) exceed 70 segments (max 80); none are under 35.
* Neutral small talk is deliberately not extracted; a few conversational statements ("I took the morning off") are therefore unlabelled by design.
* 26 blueprints request an unattributable speaker; 24 realise it (2 had no symptom to attach it to).
* Clinical content was written from general knowledge, not reviewed by a clinician.
* Hedged speech is labelled as given; frequency/severity wording uses a fixed lexicon, so lexical matching is easier than for real speech.

## Reproduce

```
python scripts/generate_batch.py          # regenerates everything (deterministic; identical bytes across PYTHONHASHSEED values)
python scripts/validate_batch.py --dataset-checks
python scripts/validator_selftest.py
python scripts/lock_dataset.py --verify
```
