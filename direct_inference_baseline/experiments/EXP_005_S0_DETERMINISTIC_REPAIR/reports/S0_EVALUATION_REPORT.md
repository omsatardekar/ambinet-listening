# S0 deterministic repair: implementation and evaluation (version S0.1.0)

Written for: the study owner reviewing S0 before any further development stage. No model, inference, prompt change, fine-tuning or validation/locked-test access was involved. S0 repairs STRUCTURE and REPRESENTATION only; it does not correct clinical reasoning, and a better schema result is not better clinical accuracy.

## 1. What was built

`s0/s0_repair.py` (pure library, no I/O), `s0/run_s0_prompt_dev.py` (evaluation driver, runs under `StrictAccessSpy`), `s0/test_s0_repair.py` (23 unit tests, all pass). Originals are never overwritten: byte copies are in `data/original/`, repaired copies in `data/repaired/`, every change and flag in `logs/transformations_<source>.jsonl` (fields: encounter id, JSON path, original value, repaired value, rule, reason, deterministic yes/no, human review required yes/no). Frozen schema untouched: S0 adds no field; allergy status categories live in the log.

| Rule | What it does | What it refuses to do |
|---|---|---|
| A | `clinical_assessment` / `follow_up` given as a bare object -> one-item list, only when the object has that item's own scalar fields and only schema keys | empty object, object with nested lists or foreign keys: preserved and flagged |
| B | exact role-enum aliases (`DOCTOR`->`doctor`, `Family Member`->`family_member`, ...) in reported_by / observed_by / stated_by / requested_by / responsible_person | any other value (`grandma`, `family_member` as responsible_person): preserved and flagged, no semantic guessing |
| C | allergy entries that are placeholders (`none`, blank, ...) are removed from `allergies`; the transcript decides the status: explicit denial (short answer right after the allergy question) -> schema form `negative_findings: Allergies / No known allergies`; question but unclear or disputed answer -> `unknown`; no allergy question -> `not_assessed`; real allergies stay | "none" is never read as confirmed absence unless the transcript says so; a medicine listed as an allergy is flagged, never removed |
| D | `scheduled_datetime`, `normalized_datetime`, ISO/timestamp-like `time_reference` that no spoken date/time supports -> null, original kept in the log | no date is invented or inferred |
| E | `reported_by` = role of the single verified non-question cited segment (see `REPORTED_BY_SEMANTICS.md`); applies only to evidence that reproduces a real transcript segment exactly | model-written evidence ids (P02), questions, several speakers (flagged) |
| F | flags only: medicine in allergies, negative finding overlapping a positive item, dose not near the drug in the transcript, route that is not a route, prescribed drug missing, placeholder assessment/negative finding, procedural talk extracted as content, follow-up without a return-visit phrase | never changes medicine identity/dose/frequency/route, allergy identity, polarity, diagnosis or follow-up meaning |

## 2. Evaluation data and access

50 prompt_dev encounters (ids from the frozen `split_v1.json`), two stored sources: **P02_stage1** (P02 parsed predictions, rule E not applicable because P02's own evidence ids are not trustworthy citations) and **P05_final_v4** (P05 prompt_dev final predictions with retrieved, verified evidence; rule E applicable). Access audit (`results/s0_metrics.json`): locked-test files opened 0; sealed hash file not opened; validation records opened 0; 50 prompt_dev transcripts and 50 prompt_dev labels opened (labels only for the informational scores in 4.6). Note P05_final_v4 was produced by retrieval revisions tuned on prompt_dev, so it is a development artefact.

## 3. Results (numerator/denominator)

### 3.1 Schema validity (frozen `schema_validator`)
| | P02_stage1 original | P02_stage1 repaired | P05_final_v4 original | P05_final_v4 repaired |
|---|---:|---:|---:|---:|
| Fully schema-compliant records | 0/50 | 0/50 | 0/50 | 0/50 |
| Total violations | 1,064 | 1,008 (-56) | 945 | 845 (-100) |
| wrong_type | 33 | 0 | 33 | 0 |
| enum_violation | 208 | 157 | 203 | 123 |
| missing_field | 814 | 842 (+28) | 700 | 713 (+13) |
| unexpected_field | 9 | 9 | 9 | 9 |

No record becomes fully compliant: the remaining violations are mostly missing nullable fields the model never wrote (P02, after repair: `vital_signs.confidence` 79, `physical_examination.confidence` 60, `medications.confidence` 54, `medications.duration` 47, `medications.indication` 44, ...) and invalid values (`symptoms.certainty=None` 20, `social_history.category='lifestyle'` 15, blank `reported_by` 12, `action_type='prescription'/'consultation'` 11). S0 does not fill or guess them (filling nullable fields with null would be a further structural rule, S0.2, which needs approval).
`missing_field` rises by 28 because 33 recovered `clinical_assessment`/`follow_up` objects are now visible items whose own missing fields are counted (+48), partly offset by -20 for removed placeholder allergies; this is exposure, not new error.

### 3.2 Corrections, retention and flags (P02_stage1 / P05_final_v4)
| Measure | P02_stage1 | P05_final_v4 |
|---|---:|---:|
| Structural corrections logged | 124 | 279 |
| A object->list | 33 | 33 |
| B exact enum alias | 40 | 40 |
| C placeholder allergy removed | 15 | 15 |
| C explicit "No known allergies" represented | 14 | 14 |
| D unsupported datetime nulled | 22 | 22 |
| E reported_by from cited segment | n/a (50 records) | 155 |
| Field-level value changes (B + D + E) | 62 | 217 |
| Entities in list sections before -> after | 629 -> 661 | 629 -> 661 |
| Facts retained (not removed) | 614/629 original entities | 614/629 |
| Facts dropped (placeholder allergies, not facts) | 15 | 15 |
| Recovered by object->list (previously skipped by the evaluator) | 33 | 33 |
| Facts added (explicit denial in schema form) | 14 | 14 |
| Ambiguous cases preserved and flagged (A, B unknown, E several speakers) | 7 | 9 |
| Items flagged and left unchanged by rule F (clinical issues, not corrected) | 73 | 75 (incl. 2 rule E ambiguities) |
| Changes requiring human review | 1 | 6 |

Flag types left unchanged (P02): negative finding overlapping a positive item 24, prescribed drug missing 12, placeholder assessment 11, unknown enum value 7, route not a route 6, follow-up without return-visit phrase 5, placeholder negative finding 4, dose not near drug 2, medicine listed as allergy 1, procedural talk as content 1. Allergy placeholders by record: explicit denial in the transcript 14, not assessed 1, none present 35.

### 3.3 Checks for newly introduced errors (deterministic)
- Every difference between original and repaired content is covered by a logged change: 0 uncovered (both sources, 50 records each).
- Idempotence: a second S0 pass over the 100 repaired files makes 0 changes.
- Unit tests: 23/23 pass (including "never changes dose/route/polarity", "disputed allergy answer creates no denial", "doctor question is never a speaker source", "input is never modified").
- Validator exposure: 0 new violation types; +48 missing_field inside recovered items (3.1); +1 enum value exposed (`follow_up.status='resolved'`).
- Rule E risk: 5 of 155 reported_by changes turn a patient/family attribution into `doctor` where the single cited statement may be a doctor recap; they are logged with human review required. The correctness of rule E depends on the P05 citation being the true source (the AI audit found some wrong citations), so E does not make attribution correct, it makes it consistent with the cited segment.
- Not detected by these checks: anything clinical (wrong drug, wrong dose, polarity, fabricated follow-up). They remain, flagged.

### 3.4 Informational: frozen strict evaluator on prompt_dev labels (not a clinical-accuracy claim)
| | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| Original (P02 stage 1; P05 final is identical) | 153 | 522 | 1,707 | 0.2267 | 0.0823 | 0.1207 |
| After S0 | 176 | 532 | 1,684 | 0.2486 | 0.0946 | 0.1371 |
The +23 matched facts and +10 false positives come from the 33 recovered `clinical_assessment`/`follow_up` items becoming visible to the evaluator (and 14 added denials). This is structural recovery on a development set, not better reasoning: the same facts were already produced by the model; the old pipeline discarded them for shape. It should not be quoted as an improvement of extraction quality.

## 4. Limitations and what S0 cannot do
- It cannot fix medicine identity, dose, polarity, fabricated follow-up, omitted prescriptions or allergy identity; 73 flagged items per source stay as they were.
- Rule C decides "explicit denial" from short answers right after the allergy question in this synthetic dialogue style; unusual phrasing is classified `unknown` (safe side) and not converted.
- Rule D uses token support in the spoken text; a date the patient states but the model reformats differently could be nulled (original kept in the log).
- Rule E needs verified citations; on model-written evidence (P02) it is deliberately off.
- Evaluated on 50 development records only; no held-out confirmation, no validation or locked-test records used.

## 5. Decisions needed
1. Approve a possible S0.2 rule that fills missing nullable fields with null (large reduction of `missing_field`, purely structural)?
2. Rule E definition for confirmed history ("I can see X in your file"): keep `doctor` as the supplier of that statement or require the patient's earlier statement? (see REPORTED_BY_SEMANTICS.md)
3. Whether the explicit-denial representation (rule C) should also be applied to answers that are not literally short denials.
