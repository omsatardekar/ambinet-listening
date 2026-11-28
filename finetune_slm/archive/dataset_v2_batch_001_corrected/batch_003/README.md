# Batch 003 (500 synthetic encounters, ids 00501-01000)

Hand-written dialogue + label per encounter, compiled by `generation/compile_draft.py` / `generation/dsl.py` and checked with the unmodified Batch 001 validator (`../validation/validate_dataset.py`) and the schema `../schema/final_label_schema.json`.

- `output/inputs`, `output/labels`: 500 pairs (encounter_00501 .. encounter_01000). Source drafts: `generation/drafts/` (393 started by a colleague, 107 completed here, in `generation/dsl/q*.txt`).
- `reports/dataset_checks.json`: validator 500/500 pass, evidence grounding 12267/12267, 0 exact duplicates, 0 near duplicates (max 5-gram Jaccard 0.03 within the batch, 0.01 vs Batch 001).
- `reports/schema_audit.json`: project schema audit, 2 remaining failures (see limitations).
- `reports/manifest_batch_003.json`: SHA-256 of every file. `reports/distribution.json`: speaker and entity counts.

Speakers: 2 roles in 274 encounters, 3 in 174, 4 in 51, 5 in 1. Nurse 84, caregiver 69, family member 83, clinical staff 37, unidentified voice 6.

Limitations (not clinician reviewed): audit check `duration_disagreement_shape` fails for 00873 and 00931 (the disagreement is about frequency, not duration); a few encounters follow the plan's hard zeros by omitting topics a real visit would cover; some records mention a result (e.g. a previous blood test) that is not labelled because the plan fixed investigations at 0. Batch 001 and Batch 002 files are untouched.
