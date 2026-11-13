# Batch 002 validation report

Automated checks only; no clinician or human reviewed any record. Every line shows numerator/denominator.

## Levels (kept separate)

| Level | Result |
|---|---|
| File generation | 500/500 slots written (0 unresolved); 500/500 transcript files, 500/500 label files and 500/500 blueprint files present with matching ids |
| JSON validity | 500/500 transcripts, 500/500 labels and 500/500 blueprints parsed (all three loaded by the validators) |
| Schema validity (Batch 001 validator, schema group) | 500/500 records with no schema errors; errors by group none |
| Schema audit against the final schema (existing `final_schema_audit.py`) | PASS: 0 failures in 393308 check evaluations, 0 records failing the validator |
| Evidence-reference validity | evidence records matching a real segment 16638/16638; entity evidence ids resolving 17113/17113; symmetric supports links 29903/29903 |
| Evidence grounding (lexical) | 23533/23533 extracted values literally found in the cited evidence (ALL_GROUNDED) |
| Semantic evidence quality (independent checks, below) | see table; failures: 0 |
| Label consistency | allergy representation matches blueprint and schema 500/500; blueprint counts match for family 500/500, surgery 500/500, current/discontinued medicines 500/500, planned medicines 500/500 |
| Duplicates | exact duplicate conversations 0; near-duplicate pairs (5-gram Jaccard >= 0.45) 0; max pairwise 0.127; scenario-fingerprint duplicates 0 |
| Validator negative controls | 22/22 deliberate corruptions detected (run on Batch 002 records 20001-20003) |
| SHA-256 integrity | output/CHECKSUMS.sha256 lists 1001 files; manifest/batch_002_manifest.json lists 1500 file hashes |
| **Overall dataset acceptance (automated)** | ACCEPTED: all automated checks pass. This is automated acceptance only: no clinical, human or linguistic review. |

## Independent check detail (scripts/b2_independent_checks.py; own implementation, reads files only)

| Check | Passed | Checked | Failed |
|---|---:|---:|---:|
| files_inputs_500 | 1 | 1 | 0 |
| files_labels_500 | 1 | 1 | 0 |
| files_blueprints_500 | 1 | 1 | 0 |
| ids_match_across_inputs_labels_blueprints | 1 | 1 | 0 |
| ids_unique_and_in_range_20001_20500 | 1 | 1 | 0 |
| ids_disjoint_from_batch_001_00001_00500 | 1 | 1 | 0 |
| encounter_id_inside_files_equals_filename | 500 | 500 | 0 |
| evidence_record_matches_real_transcript_segment | 16638 | 16638 | 0 |
| entity_evidence_ids_resolve | 17113 | 17113 | 0 |
| evidence_supports_symmetric | 29903 | 29903 | 0 |
| patient_origin_fact_has_non_question_evidence | 6551 | 6551 | 0 |
| reported_by_equals_role_of_a_cited_non_question_segment | 6551 | 6551 | 0 |
| evidence_not_greeting_only | 6551 | 6551 | 0 |
| negative_finding_evidence_contains_negation_cue | 2767 | 2767 | 0 |
| present_symptom_supported_by_statement_or_affirmed_question | 1156 | 1156 | 0 |
| medication_dose_number_in_cited_evidence | 808 | 808 | 0 |
| medication_dose_within_two_segments_after_drug_name | 808 | 808 | 0 |
| no_duplicate_medication_entries | 500 | 500 | 0 |
| no_drug_both_currently_used_and_planned_or_discontinued | 500 | 500 | 0 |
| allergy_not_placeholder | 230 | 230 | 0 |
| allergy_substance_in_cited_evidence | 230 | 230 | 0 |
| allergy_substance_not_a_current_medication_name | 230 | 230 | 0 |
| allergy_representation_matches_blueprint_and_schema | 500 | 500 | 0 |
| allergy_status_values_valid | 500 | 500 | 0 |
| no_iso_date_or_datetime_in_label | 500 | 500 | 0 |
| follow_up_normalized_datetime_null | 500 | 500 | 0 |
| symptom_count_and_temporality_match_blueprint_allowing_one_disputed_symptom_per_dispute | 500 | 500 | 0 |
| family_history_count_matches_blueprint | 500 | 500 | 0 |
| surgical_history_count_matches_blueprint | 500 | 500 | 0 |
| current_and_discontinued_medication_count_matches_blueprint | 500 | 500 | 0 |
| planned_medication_count_matches_blueprint_rx | 500 | 500 | 0 |
| no_negative_finding_contradicting_an_undisputed_current_present_symptom | 500 | 500 | 0 |
| no_duplicate_entities_within_section_symptoms_keyed_with_temporality | 5000 | 5000 | 0 |
| no_duplicate_family_history | 500 | 500 | 0 |
| scheduled_datetime_null_or_literally_spoken | 715 | 715 | 0 |

## Failures found while building the checks and how each was resolved (disclosure)

The independent checks were run during development; their first versions reported failures that I investigated one by one before the final run:
- Checker artifacts (corrected in the checker, not in the data): a long doctor turn ending in a question treated as a pure question; symptom names that contain 'not'/'no' ('not opening my bowels') treated as negated; a negation cue from a previous sentence; a disputed symptom (patient denies, caregiver reports) counted as a contradiction; a previous episode of the same symptom counted as a duplicate.
- Real content defects (corrected in the profiles, then regenerated): items listed as symptoms that were history or events (past sunburn, analgesic use, an old fracture, an insect bite last week).
- One planned-action wording rule of the existing final audit fired 4 times in an earlier run (planned referral sharing a transcript turn with a declined test). I confirmed by reading the evidence that the labels were correct (false positives of the sentence-splitting heuristic), renamed colliding plural test names and referral descriptions, and added the same rule as a generation-time gate; the final audit then reports 0 failures.

Because the checker was adjusted after seeing results, a pass is evidence of consistency between transcripts, labels and blueprints, not of clinical correctness.
