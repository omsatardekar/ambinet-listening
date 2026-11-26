# Final label schema (Batch 001 corrected)

Generated from `schema/final_label_schema.json` by `scripts/final_schema_audit.py`. That file is the single source of truth; the validator
reads the same enums and key sets. Outer structure and category names follow `clinical_extraction_schema.json`; **no top-level field was added and no field
outside the lists below exists in any of the 500 labels.**

## Conventions

* Roles: `doctor`, `patient`, `nurse`, `caregiver`, `family_member`, `clinical_staff`, `unknown` (lowercase in labels; UPPERCASE in transcripts).
* **Confidence:** Every `confidence` and `role_confidence` field is present for schema compatibility and MUST be null. No independently assessed confidence exists; do not use these fields in accuracy calculations.
* `evidence_ids` / `supports` / `related_entities` / `ambiguous_entities` use JSON locations like `symptoms[2]`; links are symmetric.
* Empty/unstated information is `null` or `[]`; nothing is inferred (no dose, duration, severity or date that was not spoken).

## Key sets

* `chief_complaint`: `value`, `normalized_value`, `reported_by`, `evidence_ids`
* `symptoms`: `name`, `normalized_name`, `category`, `status`, `severity`, `duration`, `frequency`, `onset`, `temporality`, `body_site`, `associated_symptoms`, `aggravating_factors`, `relieving_factors`, `reported_by`, `certainty`, `evidence_ids`, `confidence`
* `negative_findings`: `finding`, `normalized_name`, `status`, `assertion`, `reported_by`, `temporality`, `evidence_ids`, `confidence`
* `medical_history.past_medical_history`: `condition`, `normalized_condition`, `status`, `duration`, `reported_by`, `evidence_ids`, `confidence`
* `medical_history.surgical_history`: `procedure`, `normalized_procedure`, `timeframe`, `reported_by`, `evidence_ids`, `confidence`
* `medical_history.family_history`: `condition`, `normalized_condition`, `relation`, `reported_by`, `evidence_ids`, `confidence`
* `medical_history.social_history`: `category`, `description`, `status`, `details`, `reported_by`, `evidence_ids`, `confidence`
* `medications`: `name`, `normalized_name`, `generic_name`, `dose`, `route`, `frequency`, `duration`, `indication`, `status`, `reported_by`, `evidence_ids`, `confidence`
* `allergies`: `substance`, `normalized_substance`, `allergy_type`, `reaction`, `severity`, `status`, `reported_by`, `evidence_ids`, `confidence`
* `vital_signs`: `name`, `normalized_name`, `value`, `unit`, `reported_by`, `evidence_ids`, `confidence`
* `physical_examination`: `finding`, `normalized_finding`, `body_site`, `status`, `observed_by`, `evidence_ids`, `confidence`
* `review_of_systems`: `system`, `status`, `details`, `reported_by`, `evidence_ids`, `confidence`
* `clinical_conditions`: `name`, `normalized_name`, `status`, `duration`, `reported_by`, `evidence_ids`, `confidence`
* `clinical_assessment`: `assessment`, `normalized_assessment`, `certainty`, `basis`, `stated_by`, `evidence_ids`, `confidence`
* `procedures_and_investigations`: `name`, `normalized_name`, `type`, `status`, `requested_by`, `indication`, `scheduled_datetime`, `evidence_ids`, `confidence`
* `clinical_actions`: `action_type`, `description`, `status`, `responsible_person`, `time_reference`, `evidence_ids`, `confidence`
* `follow_up`: `type`, `time_reference`, `normalized_datetime`, `status`, `evidence_ids`
* `clinical_uncertainties`: `type`, `description`, `related_entities`, `resolution_status`, `evidence_ids`, `confidence`

Nested: `duration` = value, unit, normalized; `time_reference` = value, normalized_date; `encounter_metadata` = encounter_date, encounter_type, language, primary_speakers; `primary_speakers` = speaker_id, role, role_confidence; `quality_checks` = negation_detected, temporality_detected, speaker_attribution_available, unsupported_clinical_claims, contradictions_detected, ambiguous_entities, requires_clinician_review; `clinical_evidence` = evidence_id, speaker_id, speaker_role, transcript_text, start_timestamp, end_timestamp, supports

## Enumerated values and definitions

### `symptoms.status`
* `present`: The speaker reports the symptom as existing now.
* `resolved`: The speaker says the symptom occurred but has gone away (current resolved symptom, or a previous episode).

### `symptoms.certainty`
* `certain`: Stated without hedging by the attributed speaker and not contradicted.
* `uncertain`: Stated with hedging or the speaker cannot give key detail (for example onset); the gap is also recorded in clinical_uncertainties.
* `disputed`: Two speakers give contradictory information about the symptom (for example patient denies it, caregiver reports it); both reports are kept and a conflicting_statement uncertainty exists.

### `symptoms.temporality`
* `current`: Present now.
* `resolved`: Occurred in this illness and has since gone.
* `past`: A previous, separate episode.

### `negative_findings.status`
* `absent`: The speaker explicitly denies the finding.

### `negative_findings.assertion`
* `negative`: Explicit negation in the transcript.

### `negative_findings.temporality`
* `current`: Denied for the present illness.
* `past`: Denied for the past (for example no previous surgery).

### `medications.status`
* `currently_used`: The speaker says the medicine is taken now.
* `discontinued`: The speaker says the medicine was stopped.
* `planned`: The doctor prescribes or proposes starting it in this encounter.

### `medications.route`
* `oral`: Spoken as by mouth; null when no route is spoken.

### `allergies.allergy_type`
* `medication`: Drug allergy.
* `food`: Food allergy.
* `environmental`: Environmental or contact allergen.

### `allergies.severity`
* `unknown`: Severity is not graded in this schema version; always 'unknown'.

### `allergies.status`
* `reported`: A speaker states the allergy as fact (the reaction may be given, or stated as not remembered, or not mentioned: reaction null).
* `uncertain`: The speaker believes there may be an allergy but cannot name the substance and/or reaction.
* `historical`: The speaker describes a past reaction (for example in childhood) and says the substance has been avoided since.
* `disputed`: Patient and caregiver/family member disagree; entity carries the third party's report, the patient's denial is a separate negative_findings entry, and an allergy_disputed uncertainty links both.

### `physical_examination.status`
* `present`: Finding observed by the doctor.
* `absent`: Doctor states the finding is not present.

### `review_of_systems.status`
* `negative`: Patient denies abnormality for the system when asked at system level.

### `clinical_conditions.status`
* `existing`: A condition already on record that the patient reported and the doctor acknowledged.

### `clinical_assessment.certainty`
* `provisional`: The doctor's working impression, not confirmed.
* `differential`: A possibility the doctor says cannot be ruled out, or an uncommitted either/or impression.

### `procedures_and_investigations.type`
* `laboratory`: Specimen test.
* `imaging`: Imaging study.
* `cardiac`: ECG, Holter, stress test.
* `other`: Any other test or procedure.

### `procedures_and_investigations.status`
* `planned`: Ordered or booked by the doctor in this encounter; will happen.
* `completed`: Already performed (before the consultation by staff, or previously per the patient); not merely proposed.
* `conditional`: Discussed as something that may be done only if a stated condition arises (for example if it has not settled in two weeks). Not ordered now, no scheduled time.

### `clinical_actions.action_type`
* `investigation`: A test or imaging.
* `medication`: A prescription.
* `counselling`: Advice or instruction to the patient.
* `referral`: Referral to a service.
* `follow_up`: A return visit.
* `other`: Other instruction (for example bring the prescription).

### `clinical_actions.status`
* `planned`: A committed future task for the clinic or doctor (order a test, start a drug, refer, book a visit).
* `completed`: Done already (for example a test performed by the nurse before the doctor saw the patient).
* `recommended`: Advice the patient is asked to follow (lifestyle, safety-net, bring documents). Not an order.
* `conditional`: Will happen only if a stated condition occurs (a considered test, or a follow-up phrased 'if it is not better in N days'). Never used for something already ordered or already done.

### `clinical_actions.responsible_person`
* `doctor`: Doctor owns the task.
* `patient`: Patient is asked to do it.
* `nurse`: Nurse performed it.
* `clinical_staff`: Reception/other staff will arrange or book it.

### `follow_up.type`
* `consultation`: A return consultation.

### `follow_up.status`
* `planned`: A time is stated unconditionally.
* `conditional`: Return only if a stated condition occurs ('if it's not better in three days').

### `clinical_uncertainties.type`
* `date_uncertain`: A speaker cannot say when a symptom began.
* `duration_disagreement`: Two speakers give different durations for the same symptom (for example patient 'two weeks', caregiver 'three weeks'). The symptom duration is recorded only as an approximate range (value null, normalized 'approximately A to B unit') because the range was only summarised, not confirmed by both.
* `uncertain_dose`: A single speaker gives a dose tentatively ('maybe'); the dose is recorded as stated and flagged, never verified.
* `medication_discrepancy`: Two sources give different doses for the same current medicine; the medication dose is null.
* `adherence_uncertain`: Prescribed frequency is stated but a speaker says doses are missed or is not sure the medicine is taken as prescribed; actual adherence is unknown.
* `incomplete_medication_name`: The speaker cannot name the medicine (described by appearance); name is the description, generic/normalized names are null.
* `allergy_uncertain`: A possible allergy is reported without a nameable substance or reaction.
* `allergy_disputed`: Patient denies allergies while a caregiver/family member recalls a possible allergic reaction; both are preserved (negative finding plus allergy entry with status 'disputed').
* `conflicting_statement`: Patient and another speaker contradict each other about a symptom (patient denial vs third-party report).
* `unknown_speaker`: An utterance could not be attributed to an identified speaker (role UNKNOWN).

### `clinical_uncertainties.resolution_status`
* `unresolved`: Not settled in the encounter.
* `partially_resolved`: Summarised or narrowed in the encounter (for example a range) but not confirmed by all parties.
* `resolved`: Settled in the encounter (defined for completeness; not used in this batch).

### `medical_history.past_medical_history.status`
* `ongoing`: Reported as present now.

### `medical_history.social_history.category`
* `smoking`: Tobacco use.
* `alcohol`: Alcohol use.
* `occupation`: Work or retirement.
* `exercise`: Physical activity.
* `diet`: Eating pattern.
* `living`: Living arrangement.

### `medical_history.social_history.status`
* `current`: Ongoing.
* `former`: Stopped.
* `never`: Never did.
* `none`: Does not do it.
* `retired`: Occupation: retired.

### `extraction_status`
* `completed`: Extraction finished.

### `encounter_metadata.encounter_type`
* `outpatient_consultation`: All encounters in this batch.

## Allergy representation (distinguishable cases)

* **explicit_no_known_allergies**: negative_findings entry {finding: 'Allergies', normalized_name: 'No known allergies', status: absent}; allergies empty; the transcript contains an allergy question answered in the negative.
* **not_discussed**: allergies empty AND no negative_findings 'Allergies' entry AND the word 'allerg' occurs nowhere in the transcript. An empty allergies array alone never means 'no allergies'.
* **reported**: allergies entry status 'reported'.
* **reported_reaction_unknown**: allergies entry status 'reported', reaction null; the patient may have said the reaction is not remembered.
* **uncertain**: allergies entry status 'uncertain' + allergy_uncertain uncertainty.
* **historical**: allergies entry status 'historical'.
* **disputed**: negative_findings 'Allergies' (patient) + allergies entry status 'disputed' (caregiver/family) + allergy_disputed uncertainty relating to both + contradictions_detected line.

## Reference rules (all enforced by the audit)

* Every evidence_ids entry resolves to a clinical_evidence record; every clinical_evidence.supports location resolves to an existing entity that lists that evidence_id (symmetric).
* clinical_uncertainties.related_entities and quality_checks.ambiguous_entities are JSON locations such as 'allergies[0]' that resolve inside the same label.
* allergy_uncertain relates to allergies[*]; allergy_disputed relates to one negative_findings 'Allergies' entry and one allergies entry with status disputed; medication_* and adherence_uncertain and incomplete_medication_name relate to medications[*]; date_uncertain, duration_disagreement, unknown_speaker relate to symptoms[*]; conflicting_statement relates to a negative_findings entry and a symptoms entry with certainty disputed.
* Each of conflicting_statement, medication_discrepancy, allergy_disputed, duration_disagreement has exactly one matching line in quality_checks.contradictions_detected.
* clinical_actions status 'conditional' only for investigation or follow_up actions; each conditional investigation action shares evidence with a procedures_and_investigations entry of status 'conditional', and each conditional follow_up action matches a follow_up entry of status 'conditional'.

## Conditional vs planned vs completed vs recommended

| Status | Meaning | Allowed on | Evidence wording |
|---|---|---|---|
| planned | committed future task for the clinic/doctor | investigation, medication, referral, follow_up | doctor orders/prescribes/books it |
| completed | already done | investigation (nurse-performed or previously done) | 'I did', 'already', 'had ... done' |
| recommended | advice for the patient to follow, not an order | counselling, other | imperative advice |
| conditional | only if a stated condition arises; not ordered, no time slot | investigation, follow_up | 'if it hasn't settled', 'hold off', 'if it's not better' |

