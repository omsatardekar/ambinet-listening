# `reported_by` semantics (proposal for approval; no frozen schema or file changed)

## Definition used
`reported_by` = the speaker who verbally supplied the information represented by the fact. It is not necessarily the patient or the person the fact describes.

Three concepts are kept separate:
1. **subject**: whose health information the fact concerns (patient, or a relative for family history).
2. **reported_by**: who said it (role of the speaker of the cited transcript segment).
3. **observed_by / measured_by**: who performed an observation or measurement, only when the transcript says so. Announcing a value does not establish who measured it.

| Example | subject | reported_by | observed_by / measured_by |
|---|---|---|---|
| Patient reports headache | patient | patient | - |
| Patient denies chest pain | patient | patient | - |
| Family member reports the patient's medicine | patient | family_member | - |
| Doctor states an examination finding | patient | doctor | observed_by = doctor (stated by the examiner) |
| Nurse announces "pulse 84" | patient | nurse | measured_by: not inferred (unknown) |
| Patient says "my brother has asthma" | the brother | patient | - |
| Doctor: "I can see COPD in your file" (confirming) | patient | doctor for that statement | - |

## Compatibility with the frozen schema (`schema/final_label_schema.json`, unchanged)
- Present: `reported_by` (symptoms, negative findings, history, medications, allergies, vital signs, review of systems, clinical conditions, chief complaint), `observed_by` (physical examination), `stated_by` (assessment), `requested_by` (investigations), `responsible_person` (actions).
- Not present: a `subject` field and a `measured_by` field. Subject is implicit (the patient) except for family history, where `relation` carries the relative. Measurement performer cannot be represented.
- Existing labels already follow the "who said the cited turn" reading (Batch 001: nurse for nurse-announced vitals; Batch 002 independent check: `reported_by` equals the role of a cited non-question segment in 6,540/6,540 patient-origin facts). So the definition needs no relabelling.
- Known gaps (not solvable without a schema change): a fact supplied by two speakers (patient and caregiver) carries one role; the conflict is kept in `clinical_uncertainties`. Confirmed history cited through the doctor's confirming turn gets `doctor` for that segment although the patient supplied it earlier.

## How S0 uses it (rule E)
S0 sets `reported_by` to the role of the single non-question cited segment, only when the evidence record reproduces a real transcript segment (speaker, role, text); questions are never a source; several speakers -> unchanged and flagged; model-written evidence (P02) -> not applied. When this would change a patient/family/caregiver attribution into `doctor`, the change is logged with human review required, because the cited statement may be a recap of what the patient said. `observed_by`, `stated_by` and `measured_by` are never derived.

## Proposed schema changes (NOT applied; need separate approval)
1. Optional `subject` on family-history-like cases is already served by `relation`; a general `subject` field is not recommended unless caregiver-reported facts about third parties appear.
2. Optional `measured_by` on `vital_signs` (enum roles or null), default null, to separate "announced by" from "measured by".
3. Allow `reported_by` to hold a list when two speakers supply the same fact, replacing part of the current use of `clinical_uncertainties` (changes the evaluator contract; not recommended now).
Any such change would apply to a new schema version and a new batch, never to the frozen Batch 001 labels or P00-P05 artifacts.

## Decision recorded (owner, 2026-11-13) and how it is applied
`reported_by` is the ACTUAL SPEAKER who made the statement. If the doctor says "I can see hypertension in your medical records", `reported_by` is `doctor`. The patient stays the subject. The underlying provenance of the information (here the medical record, elsewhere the patient's earlier statement, a relative, a measurement device) is a different thing and is not what `reported_by` records; the frozen schema has no field for it and none was added.
- S0 rule E already follows this: a single non-question cited statement by the doctor gives `doctor`; several speakers leave the value unchanged and flagged. The earlier "recap" review flag on patient-to-doctor changes remains as a review prompt only; the value follows the cited speaker.
- Batch 002 labels: for conditions the generator cites the patient's own statement AND the doctor's confirming turn; all 297 Batch 002 `clinical_conditions` carry `reported_by = patient` (the first supplier). That is consistent with "actual speaker" for the patient's statement but does not capture the doctor's confirmation as a separate attribution, because one role per fact is all the schema allows. Not changed (Batch 002 is unchanged); recorded here for the allocation and training-quality review.
