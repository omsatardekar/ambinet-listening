# P00 / P01 record-by-record clinical extraction gap analysis (Qwen3-1.7B, 30 development records)

**DEVELOPMENT-ONLY.** Labels are generator-derived; the 50 prompt-development records were used earlier for 0.6B prompt development. Not independent or clinical validation.

Source of every row: transcript (`dataset_v2_batch_001_corrected/output/inputs`) -> gold label (`.../output/labels`) -> P00 raw/parsed output -> P01 raw/parsed output. Data tables behind this report: `evaluations/p00_p01_audit/{RECONCILIATION.json, AUDIT_GOLD_FACTS.jsonl, AUDIT_EXTRA_PREDICTIONS.jsonl, SPEAKER_AUDIT.json, EVIDENCE_AUDIT.json, AUDIT_SUMMARY.json}`.

Class legend: CORRECT / PARTIAL (matched, a detail differs) / MISSED / INCORRECT / UNSUPPORTED / WRONG_ATTRIB / WRONG_STATUS / WRONG_NORM (same fact, different surface form: the strict matcher scores it a miss + a false positive) / EVIDENCE_ERROR (section 'Evidence') / N/A (category absent in gold and prediction). `NO OUTPUT` = the record's JSON was truncated/invalid, so nothing was extracted.

## 1. Reconciliation (Phase 1)

Frozen ids = first 30 of `FROZEN_50_PROMPT_DEV_IDS.json` (`00035` .. `00266`, not sequential). Duplicate ids: none. Unexpected extra P01 files: none. Every file's inner `encounter_id` was checked against the id (not just the filename). P00 files for the other 20 frozen ids exist but were not used.

| ID | Segs | Transcript id | Gold id | P00 raw/parsed id | P00 status | P01 raw/parsed id | P01 status | Matched |
|---|---:|---|---|---|---|---|---|---|
| 00035 | 39 | 00035 | 00035 | 00035/00035 | parsed | 00035/00035 | parsed | YES |
| 00037 | 56 | 00037 | 00037 | 00037/00037 | parsed | 00037/failed-file | failed (length, 4096 tok) | YES |
| 00040 | 58 | 00040 | 00040 | 00040/failed-file | failed (length, 4096 tok) | 00040/00040 | parsed | YES |
| 00042 | 43 | 00042 | 00042 | 00042/00042 | parsed | 00042/00042 | parsed | YES |
| 00060 | 49 | 00060 | 00060 | 00060/failed-file | failed (length, 4096 tok) | 00060/00060 | parsed | YES |
| 00069 | 42 | 00069 | 00069 | 00069/00069 | parsed | 00069/00069 | parsed | YES |
| 00077 | 50 | 00077 | 00077 | 00077/00077 | parsed | 00077/00077 | parsed | YES |
| 00092 | 51 | 00092 | 00092 | 00092/00092 | parsed | 00092/failed-file | failed (length, 4096 tok) | YES |
| 00120 | 46 | 00120 | 00120 | 00120/00120 | parsed | 00120/00120 | parsed | YES |
| 00127 | 51 | 00127 | 00127 | 00127/failed-file | failed (length, 4096 tok) | 00127/00127 | parsed | YES |
| 00141 | 59 | 00141 | 00141 | 00141/00141 | parsed | 00141/00141 | parsed | YES |
| 00152 | 38 | 00152 | 00152 | 00152/00152 | parsed | 00152/00152 | parsed | YES |
| 00155 | 56 | 00155 | 00155 | 00155/failed-file | failed (length, 4096 tok) | 00155/00155 | parsed | YES |
| 00157 | 38 | 00157 | 00157 | 00157/00157 | parsed | 00157/00157 | parsed | YES |
| 00162 | 37 | 00162 | 00162 | 00162/00162 | parsed | 00162/00162 | parsed | YES |
| 00165 | 40 | 00165 | 00165 | 00165/00165 | parsed | 00165/00165 | parsed | YES |
| 00168 | 37 | 00168 | 00168 | 00168/failed-file | failed (length, 4096 tok) | 00168/failed-file | failed (length, 4096 tok) | YES |
| 00182 | 47 | 00182 | 00182 | 00182/00182 | parsed | 00182/00182 | parsed | YES |
| 00187 | 59 | 00187 | 00187 | 00187/00187 | parsed | 00187/00187 | parsed | YES |
| 00189 | 42 | 00189 | 00189 | 00189/00189 | parsed | 00189/00189 | parsed | YES |
| 00202 | 45 | 00202 | 00202 | 00202/00202 | parsed | 00202/00202 | parsed | YES |
| 00204 | 40 | 00204 | 00204 | 00204/failed-file | failed (length, 4096 tok) | 00204/failed-file | failed (length, 4096 tok) | YES |
| 00206 | 66 | 00206 | 00206 | 00206/00206 | parsed | 00206/failed-file | failed (stop, 3620 tok) | YES |
| 00210 | 61 | 00210 | 00210 | 00210/failed-file | failed (length, 4096 tok) | 00210/00210 | parsed | YES |
| 00215 | 46 | 00215 | 00215 | 00215/00215 | parsed | 00215/00215 | parsed | YES |
| 00221 | 50 | 00221 | 00221 | 00221/00221 | parsed | 00221/00221 | parsed | YES |
| 00238 | 43 | 00238 | 00238 | 00238/00238 | parsed | 00238/00238 | parsed | YES |
| 00248 | 39 | 00248 | 00248 | 00248/00248 | parsed | 00248/00248 | parsed | YES |
| 00264 | 45 | 00264 | 00264 | 00264/00264 | parsed | 00264/00264 | parsed | YES |
| 00266 | 46 | 00266 | 00266 | 00266/00266 | parsed | 00266/00266 | parsed | YES |

All 30 records: transcript, label, P00 output and P01 output are present, correctly matched by inner encounter id, and exactly one of parsed/failed exists per output. Missing: none. Mismatched: none. Inaccessible: none.

Both-parsed (20): 00035, 00042, 00069, 00077, 00120, 00141, 00152, 00157, 00162, 00165, 00182, 00187, 00189, 00202, 00215, 00221, 00238, 00248, 00264, 00266.  Recovered by P01 (P00 failed): 00040, 00060, 00127, 00155, 00210.  Lost by P01: 00037, 00092, 00206.  Failed in both: 00168, 00204.

## 1b. Method, definitions and limits of this audit

- **Unit of audit:** every gold fact (1,093 across the 30 records, the same total the strict evaluator uses: TP+FN) and every extra predicted fact, per category, per prompt. Row-level data: `AUDIT_GOLD_FACTS.jsonl`, `AUDIT_EXTRA_PREDICTIONS.jsonl`.
- **Classification** (priority for a matched fact with several issues: WRONG_STATUS > WRONG_ATTRIB > PARTIAL > UNSUPPORTED):
  - CORRECT = the strict matcher links the gold and predicted fact and every checked attribute agrees (status, temporality, certainty, severity, duration, frequency, dose, route, value/unit, reported_by/observed_by/stated_by, relation ...).
  - PARTIAL = matched, but a detail (dose, route, frequency, duration, severity, reaction, value, unit, time, type) differs. WRONG_STATUS / WRONG_ATTRIB = matched, but a status-like or speaker-like attribute is wrong (including a speaker id such as `person_1` written instead of a role). UNSUPPORTED (on a matched fact) = a detail was added that gold does not have (here: an invented `route`).
  - WRONG_NORM = the fact is present in the output but in a form the strict matcher cannot link. Two sub-cases: (a) the evaluator's own fuzzy matcher links it; (b) **audit heuristic, not part of the evaluator**: an unmatched prediction in the same category whose words lie inside the transcript segment that best expresses the gold fact and that shares a word with the gold fact's own wording (for example gold 'Polydipsia' vs predicted 'constant thirst'). Heuristic (b) can over- or under-link; it is used only for this audit and never for the headline metrics.
  - MISSED = no usable prediction for the fact. Records whose JSON failed are shown as NO OUTPUT and counted as MISSED.
  - Extras (no gold counterpart): INCORRECT = recognisably wrong (a placeholder or a medication written as an allergy, or the fact exists in gold under another category); UNSUPPORTED = its content words do not appear in the transcript; 'supported by transcript' = present in the transcript but not in gold (extra but true, or a paraphrase the matcher cannot link).
  - EVIDENCE_ERROR is reported in the per-record Evidence lines and in the evidence table below, not per fact.
- **Not asserted:** the audit judges only against the gold label and the transcript text; gold labels are generator-derived, not human-verified.

## 1c. Aggregate class counts

### Records completed by BOTH prompts (20 records): extraction on identical, parsed outputs

| Category | Gold facts | P00: OK / PART / NORM / STAT / ATTR / UNSUP / MISS | P01: OK / PART / NORM / STAT / ATTR / UNSUP / MISS |
|---|---:|---|---|
| chief complaint | 20 | 2 / 0 / 17 / 0 / 0 / 0 / 1 | 1 / 0 / 16 / 0 / 0 / 0 / 3 |
| symptoms | 53 | 1 / 2 / 15 / 3 / 1 / 0 / 31 | 2 / 4 / 13 / 2 / 0 / 0 / 32 |
| negative findings | 111 | 0 / 0 / 8 / 2 / 0 / 0 / 101 | 0 / 0 / 14 / 3 / 0 / 0 / 94 |
| past medical history | 29 | 1 / 0 / 15 / 0 / 3 / 0 / 10 | 4 / 0 / 15 / 0 / 1 / 0 / 9 |
| surgical history | 10 | 2 / 0 / 8 / 0 / 0 / 0 / 0 | 2 / 0 / 8 / 0 / 0 / 0 / 0 |
| family history | 10 | 4 / 0 / 5 / 0 / 1 / 0 / 0 | 4 / 0 / 5 / 0 / 1 / 0 / 0 |
| social history | 56 | 0 / 0 / 0 / 4 / 0 / 0 / 52 | 0 / 0 / 0 / 10 / 0 / 0 / 46 |
| medications | 47 | 2 / 1 / 6 / 1 / 10 / 13 / 14 | 0 / 2 / 6 / 2 / 6 / 17 / 14 |
| allergies | 4 | 0 / 1 / 1 / 1 / 1 / 0 / 0 | 0 / 2 / 1 / 1 / 0 / 0 / 0 |
| vital signs | 86 | 11 / 2 / 14 / 0 / 23 / 0 / 36 | 20 / 2 / 14 / 0 / 16 / 0 / 34 |
| physical examination | 30 | 0 / 0 / 18 / 0 / 0 / 0 / 12 | 0 / 0 / 17 / 0 / 0 / 0 / 13 |
| review of systems | 25 | 0 / 0 / 0 / 0 / 0 / 0 / 25 | 0 / 0 / 0 / 0 / 0 / 0 / 25 |
| clinical conditions | 12 | 0 / 0 / 1 / 0 / 0 / 0 / 11 | 0 / 0 / 2 / 0 / 0 / 0 / 10 |
| clinical assessment | 28 | 11 / 0 / 6 / 2 / 0 / 0 / 9 | 11 / 0 / 6 / 2 / 0 / 0 / 9 |
| investigations/procedures | 30 | 4 / 5 / 15 / 0 / 0 / 0 / 6 | 4 / 5 / 15 / 0 / 0 / 0 / 6 |
| clinical actions | 109 | 0 / 0 / 7 / 0 / 0 / 0 / 102 | 0 / 0 / 6 / 1 / 0 / 0 / 102 |
| follow up | 18 | 1 / 0 / 3 / 0 / 0 / 0 / 14 | 1 / 0 / 5 / 0 / 0 / 0 / 12 |
| clinical uncertainties | 10 | 0 / 0 / 0 / 0 / 0 / 0 / 10 | 0 / 0 / 0 / 0 / 0 / 0 / 10 |
| **TOTAL** | 688 | 39 / 11 / 139 / 13 / 39 / 13 / 434 | 49 / 15 / 143 / 21 / 24 / 17 / 419 |

(OK correct, PART partial, NORM wrong normalisation / surface form, STAT wrong status, ATTR wrong attribution, UNSUP matched fact with an unsupported added detail, MISS missed.)

### All 30 records (failed outputs count as MISSED, as in the headline scoring)

| Category | Gold facts | P00: OK / PART / NORM / STAT / ATTR / UNSUP / MISS | P01: OK / PART / NORM / STAT / ATTR / UNSUP / MISS |
|---|---:|---|---|
| chief complaint | 30 | 3 / 0 / 18 / 0 / 0 / 0 / 9 | 1 / 0 / 19 / 0 / 1 / 0 / 9 |
| symptoms | 91 | 1 / 2 / 19 / 4 / 1 / 0 / 64 | 2 / 4 / 19 / 4 / 2 / 0 / 60 |
| negative findings | 168 | 0 / 0 / 9 / 2 / 0 / 0 / 157 | 0 / 0 / 17 / 4 / 0 / 0 / 147 |
| past medical history | 50 | 1 / 0 / 20 / 0 / 4 / 0 / 25 | 4 / 0 / 23 / 0 / 2 / 0 / 21 |
| surgical history | 16 | 2 / 0 / 10 / 0 / 0 / 0 / 4 | 2 / 0 / 11 / 0 / 0 / 0 / 3 |
| family history | 17 | 4 / 0 / 9 / 0 / 1 / 0 / 3 | 5 / 0 / 7 / 0 / 1 / 0 / 4 |
| social history | 88 | 0 / 0 / 0 / 4 / 0 / 0 / 84 | 0 / 0 / 0 / 13 / 0 / 0 / 75 |
| medications | 72 | 2 / 1 / 8 / 1 / 11 / 15 / 34 | 1 / 3 / 7 / 3 / 13 / 17 / 28 |
| allergies | 13 | 0 / 1 / 4 / 1 / 1 / 0 / 6 | 0 / 2 / 5 / 1 / 0 / 0 / 5 |
| vital signs | 129 | 13 / 3 / 14 / 0 / 23 / 0 / 76 | 23 / 2 / 20 / 0 / 26 / 0 / 58 |
| physical examination | 46 | 0 / 0 / 20 / 0 / 0 / 0 / 26 | 0 / 0 / 22 / 0 / 0 / 0 / 24 |
| review of systems | 40 | 0 / 0 / 0 / 0 / 0 / 0 / 40 | 0 / 0 / 0 / 0 / 0 / 0 / 40 |
| clinical conditions | 20 | 0 / 0 / 1 / 0 / 0 / 0 / 19 | 0 / 0 / 2 / 0 / 0 / 0 / 18 |
| clinical assessment | 48 | 13 / 0 / 7 / 2 / 0 / 0 / 26 | 15 / 0 / 6 / 2 / 0 / 0 / 25 |
| investigations/procedures | 49 | 4 / 7 / 19 / 0 / 0 / 0 / 19 | 9 / 6 / 18 / 0 / 0 / 0 / 16 |
| clinical actions | 165 | 0 / 0 / 7 / 0 / 0 / 0 / 158 | 0 / 0 / 8 / 1 / 0 / 0 / 156 |
| follow up | 26 | 1 / 0 / 3 / 0 / 0 / 0 / 22 | 1 / 0 / 6 / 0 / 0 / 0 / 19 |
| clinical uncertainties | 25 | 0 / 0 / 0 / 0 / 0 / 0 / 25 | 0 / 0 / 0 / 0 / 0 / 0 / 25 |
| **TOTAL** | 1093 | 44 / 14 / 168 / 14 / 41 / 15 / 797 | 63 / 17 / 190 / 28 / 45 / 17 / 733 |

### Extra predictions with no gold counterpart (all 30 records)

| Category | P00 extra: supported-by-transcript / UNSUPPORTED / INCORRECT | P01 extra: supported / UNSUPPORTED / INCORRECT |
|---|---|---|
| chief complaint | 1 / 1 / 0 | 1 / 3 / 0 |
| symptoms | 4 / 1 / 1 | 3 / 0 / 2 |
| negative findings | 4 / 9 / 0 | 6 / 13 / 0 |
| past medical history | 4 / 0 / 0 | 3 / 0 / 1 |
| surgical history | 8 / 0 / 0 | 9 / 0 / 0 |
| family history | 0 / 0 / 0 | 3 / 3 / 1 |
| social history | 4 / 7 / 0 | 9 / 7 / 0 |
| allergies | 1 / 0 / 10 | 2 / 0 / 11 |
| vital signs | 8 / 9 / 0 | 10 / 10 / 0 |
| physical examination | 7 / 1 / 0 | 15 / 2 / 0 |
| review of systems | 4 / 12 / 0 | 4 / 17 / 0 |
| clinical conditions | 13 / 0 / 11 | 13 / 0 / 14 |
| clinical assessment | 1 / 0 / 0 | 2 / 0 / 0 |
| investigations/procedures | 2 / 2 / 0 | 2 / 2 / 1 |
| clinical actions | 4 / 26 / 0 | 6 / 27 / 0 |
| follow up | 0 / 16 / 0 | 0 / 16 / 0 |
| clinical uncertainties | 0 / 30 / 0 | 0 / 23 / 0 |
| **TOTAL** | 65 / 114 / 22 | 88 / 123 / 30 |

### Facts that differ between P00 and P01 on the 20 records both completed (CORRECT in one prompt only)

Counts: both correct 34, P01 only 15, P00 only 5, neither 634.

P01 only:
- 00042 procedures_and_investigations: HbA1c (P00 PARTIAL, P01 CORRECT)
- 00069 vital_signs: Oxygen saturation (P00 WRONG_ATTRIBUTION, P01 CORRECT)
- 00069 vital_signs: Blood pressure (P00 WRONG_ATTRIBUTION, P01 CORRECT)
- 00069 vital_signs: Heart rate (P00 WRONG_ATTRIBUTION, P01 CORRECT)
- 00141 medical_history.past_medical_history: Eczema (P00 MISSED, P01 CORRECT)
- 00165 symptoms: Fever (P00 WRONG_ATTRIBUTION, P01 CORRECT)
- 00165 medical_history.past_medical_history: Asthma (P00 WRONG_ATTRIBUTION, P01 CORRECT)
- 00165 vital_signs: Heart rate (P00 WRONG_ATTRIBUTION, P01 CORRECT)
- 00165 vital_signs: Oxygen saturation (P00 WRONG_ATTRIBUTION, P01 CORRECT)
- 00165 vital_signs: Blood pressure (P00 WRONG_ATTRIBUTION, P01 CORRECT)
- 00202 medical_history.past_medical_history: Epilepsy (P00 WRONG_ATTRIBUTION, P01 CORRECT)
- 00264 vital_signs: Heart rate (P00 WRONG_ATTRIBUTION, P01 CORRECT)
- 00264 vital_signs: Oxygen saturation (P00 WRONG_ATTRIBUTION, P01 CORRECT)
- 00264 vital_signs: Blood pressure (P00 WRONG_ATTRIBUTION, P01 CORRECT)
- 00266 clinical_assessment: Breakthrough seizure on known epilepsy (P00 WRONG_NORMALIZATION, P01 CORRECT)

P00 only:
- 00035 chief_complaint: Slurred speech (P00 CORRECT, P01 MISSED)
- 00069 procedures_and_investigations: Pelvic ultrasound (P00 CORRECT, P01 PARTIAL)
- 00157 medications: Cetirizine (P00 CORRECT, P01 PARTIAL)
- 00182 clinical_assessment: Irritable bowel syndrome as a working diagnosis (P00 CORRECT, P01 WRONG_NORMALIZATION)
- 00264 medications: Apixaban (P00 CORRECT, P01 UNSUPPORTED)

### Speakers (A), 30 records

| | P00 | P01 |
|---|---:|---:|
| Records with usable output | 23 | 25 |
| All transcript speakers listed with the correct role | 10 | 17 |
| Records with at least one speaker missing | 13 | 8 |
| Records with a wrong role / an invented speaker | 1 / 0 | 0 / 0 |

Matched-fact issue tags: P00 {'PARTIAL': 24, 'UNSUPPORTED': 19, 'WRONG_ATTRIBUTION': 46, 'person_id_instead_of_role': 37, 'WRONG_STATUS': 14}; P01 {'PARTIAL': 27, 'UNSUPPORTED': 31, 'WRONG_ATTRIBUTION': 56, 'WRONG_STATUS': 28, 'person_id_instead_of_role': 42}.

### Evidence (L), parsed outputs

| | P00 | P01 |
|---|---:|---:|
| Parsed outputs | 23 | 25 |
| Outputs whose `clinical_evidence` holds exactly ONE record (every fact cites it) | 22 | 23 |
| Evidence records in total | 25 | 29 |
| ...that are an exact single transcript segment | 4 | 9 |
| ...that are multi-segment / whole-transcript dumps | 12 | 9 |
| ...with empty `supports` | 24 | 29 |
| Facts checked | 497 | 601 |
| Facts with NO evidence id at all | 78 | 177 |
| Facts whose cited text does not mention the fact | 250 | 307 |
| ...of which cite the greeting / intro segment (first two segments) | 31 | 25 |
| Facts whose path is missing from the cited record's `supports` | 417 | 424 |
| Facts with usable evidence (text mentions the fact AND path in `supports`) | 0 | 0 |

## 2. Record-by-record audit

### Record 00035   (P00: parsed, P01: parsed)

**Speakers (A).** Transcript: person_1 patient, person_2 doctor. Gold primary speakers: person_1 patient, person_2 doctor.
- P00: predicted [('person_1', 'patient'), ('person_2', 'doctor')]; all speakers+roles correct: True; missing none; wrong role none; invented ids none.
- P01: predicted [('person_1', 'patient'), ('person_2', 'doctor')]; all speakers+roles correct: True; missing none; wrong role none; invented ids none.

**Chief complaint (B).** Gold: 'slight slur in my speech' / normalized 'Slurred speech' (reported by patient).
- P00: 'slurred speech' / normalized 'slurred speech' (reported_by patient) -> CORRECT
- P01: 'slurred speech for ten days' / normalized 'slurred speech for ten days' (reported_by patient) -> MISSED

**symptoms**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Slurred speech (status="present", temporality="current", certainty="certain") | SEG0003 person_1 patient: "Yeah, it's a slight slur in my speech. I don't know what's causing it. I didn't want to ma" | PARTIAL: severity: gold="severe" pred=null; duration: gold={"value": 10, "unit": "days", "normalize pred={"value": "10 days", "unit": "days", "no | PARTIAL: severity: gold="severe" pred=null; duration: gold={"value": 10, "unit": "days", "normalize pred={"value": "10 days", "unit": "days", "no |

**negative findings**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Palpitations (temporality="current", reported_by="patient") | SEG0008 person_2 doctor: "Any palpitations, chest pain or confusion at all?" | MISSED | MISSED |
| Chest pain (temporality="current", reported_by="patient") | SEG0008 person_2 doctor: "Any palpitations, chest pain or confusion at all?" | MISSED | MISSED |
| Confusion (temporality="current", reported_by="patient") | SEG0008 person_2 doctor: "Any palpitations, chest pain or confusion at all?" | MISSED | MISSED |
| No known chronic conditions (temporality="current", reported_by="patient") | SEG0012 person_2 doctor: "Okay, any medical conditions, anything you've been treated for?" | MISSED | MISSED |
| No known allergies (temporality="current", reported_by="patient") | SEG0015 person_1 patient: "No, no allergies to anything." | MISSED | MISSED |

**surgical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Excision of back lump (reported_by="patient") | SEG0017 person_1 patient: "Just a lump removed from my back, years ago." | WRONG_NORM ('lump removed from back') | WRONG_NORM ('lump removed from back') |

**family history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Myocardial infarction (relation="father", reported_by="patient") | SEG0023 person_1 patient: "Uh, you know, my father had a heart attack." | WRONG_NORM ('heart attack') | WRONG_NORM ('heart attack') |

**social history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| living (status="current", reported_by="patient") | SEG0018 person_2 doctor: "Who's at home with you?" | MISSED | MISSED |
| occupation (status="current", reported_by="patient") | SEG0021 person_1 patient: "I'm a software engineer, so I'm at a screen all day." | MISSED | MISSED |

**medications**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Aspirin (dose="75 mg", frequency="once a day", status="currently_used") | SEG0025 person_1 patient: "It's aspirin, 75 milligrams, once a day." | UNSUPPORTED: route: not in gold, pred="oral" | UNSUPPORTED: route: not in gold, pred="oral" |

**vital signs**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Heart rate (value=79, unit="bpm", reported_by="doctor") | SEG0028 person_2 doctor: "Okay: heart rate 79, temp 36.7 degrees, pressure 167 over 90. And oxygen saturation is 96 " | WRONG_ATTRIB: reported_by: gold="doctor" pred="patient" | WRONG_ATTRIB: reported_by: gold="doctor" pred="patient" |
| Body temperature (value=36.7, unit="°C", reported_by="doctor") | SEG0028 person_2 doctor: "Okay: heart rate 79, temp 36.7 degrees, pressure 167 over 90. And oxygen saturation is 96 " | MISSED | MISSED |
| Blood pressure (value="167/90", unit="mmHg", reported_by="doctor") | SEG0028 person_2 doctor: "Okay: heart rate 79, temp 36.7 degrees, pressure 167 over 90. And oxygen saturation is 96 " | WRONG_ATTRIB: reported_by: gold="doctor" pred="patient" | WRONG_ATTRIB: reported_by: gold="doctor" pred="patient" |
| Oxygen saturation (value=96, unit="%", reported_by="doctor") | SEG0028 person_2 doctor: "Okay: heart rate 79, temp 36.7 degrees, pressure 167 over 90. And oxygen saturation is 96 " | WRONG_ATTRIB: reported_by: gold="doctor" pred="patient" | WRONG_ATTRIB: reported_by: gold="doctor" pred="patient" |
| *(extra P00)* | temperature [UNSUPPORTED] | | |
| *(extra P01)* | temperature [UNSUPPORTED] | | |

**review of systems**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| musculoskeletal (status="negative", reported_by="patient") | SEG0011 person_1 patient: "I move fine otherwise." | MISSED | MISSED |

**clinical conditions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | possible mini stroke [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |
| *(extra P01)* | possible mini stroke [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**clinical assessment**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Possible mini-stroke, which we need to investigate urgently (certainty="provisional", stated_by="doctor") | SEG0031 person_2 doctor: "Let me tell you where I've got to. It points towards a possible mini-stroke, which we need" | WRONG_NORM ('possible mini stroke') | WRONG_NORM ('possible mini stroke') |

**investigations/procedures**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Electrocardiogram (status="planned", type="cardiac") | SEG0035 person_2 doctor: "I'd like to arrange an ECG for possible stroke. I'd rather check than guess, and this is t" | PARTIAL: type: gold="cardiac" pred="laboratory" | PARTIAL: type: gold="cardiac" pred="laboratory" |

**clinical actions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| investigation/arrange electrocardiogram (status="planned", responsible_person="doctor") | SEG0035 person_2 doctor: "I'd like to arrange an ECG for possible stroke. I'd rather check than guess, and this is t" | MISSED | MISSED |
| counselling/advise no driving and accompanied visits (status="recommended", responsible_person="patient") | SEG0035 person_2 doctor: "I'd like to arrange an ECG for possible stroke. I'd rather check than guess, and this is t" | MISSED | MISSED |
| counselling/seek urgent care if the numbness weakness or speech problem returns (status="recommended", responsible_person="patient") | SEG0035 person_2 doctor: "I'd like to arrange an ECG for possible stroke. I'd rather check than guess, and this is t" | MISSED | MISSED |
| follow up/follow up consultation (status="planned", responsible_person="doctor") | SEG0035 person_2 doctor: "I'd like to arrange an ECG for possible stroke. I'd rather check than guess, and this is t" | MISSED | MISSED |
| *(extra P00)* | referral/arrange an electrocardiogram for possible stroke [UNSUPPORTED] | | |
| *(extra P01)* | investigation/electrocardiogram for possible stroke [UNSUPPORTED] | | |

**follow up**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| consultation/after the results are back (status="planned", time_reference="after the results are ba) | SEG0035 person_2 doctor: "I'd like to arrange an ECG for possible stroke. I'd rather check than guess, and this is t" | WRONG_NORM ('consultation/after results are back') | MISSED |
| *(extra P01)* | consultation/310.19 310.89s [UNSUPPORTED] | | |

**clinical uncertainties**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | conflicting statement [UNSUPPORTED] | | |

**Not applicable (no gold fact and no prediction):** past medical history, allergies, physical examination.

**Evidence (L).**
- P00: 1 evidence records; 0 are an exact single transcript segment; 15 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_multi_segment_or_whole_transcript_dump': 1, 'ev_empty_supports': 1, 'fact_path_missing_from_supports': 15, 'fact_not_mentioned_in_cited_text': 2}.
- P01: 1 evidence records; 0 are an exact single transcript segment; 14 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_multi_segment_or_whole_transcript_dump': 1, 'ev_empty_supports': 1, 'fact_path_missing_from_supports': 14, 'fact_not_mentioned_in_cited_text': 1}.

### Record 00037   (P00: parsed, P01: FAILED)

**Speakers (A).** Transcript: person_1 doctor, person_2 patient, person_3 caregiver. Gold primary speakers: person_1 doctor, person_2 patient, person_3 caregiver.
- P00: predicted [('person_1', 'doctor')]; all speakers+roles correct: False; missing [('person_2', 'patient'), ('person_3', 'caregiver')]; wrong role none; invented ids none.
- P01: no usable output.

**Chief complaint (B).** Gold: 'fever and joint pains' / normalized 'Fever with arthralgia' (reported by caregiver).
- P00: 'fever and joint pains' / normalized 'fever and joint pains' (reported_by person_3) -> WRONG_NORM ('fever and joint pains')
- P01: no usable output.

**symptoms**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Fever with arthralgia (status="present", temporality="current", certainty="certain") | SEG0005 person_3 caregiver: "Hmm, he's been having fever and joint pains, doctor." | WRONG_NORM ('fever') | NO OUTPUT (record failed) |
| Rash (status="present", temporality="current", certainty="certain") | SEG0009 person_2 patient: "it, It happens every other day. I've also had a blotchy rash on the trunk, for four weeks." | WRONG_NORM ('blotchy rash on the trunk') | NO OUTPUT (record failed) |
| Wrist and ankle swelling (status="present", temporality="current", certainty="certain") | SEG0010 person_1 doctor: "What about swollen painful wrists and ankles, have you noticed that?" | WRONG_NORM ('swollen and painful wrists and ankles') | NO OUTPUT (record failed) |
| Diarrhoea (status="present", temporality="current", certainty="disputed") | SEG0038 person_3 caregiver: "actually, doctor, I did notice diarrhoea he doesn't always say" | MISSED | NO OUTPUT (record failed) |
| *(extra P00)* | joint pains [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**negative findings**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Bleeding (temporality="current", reported_by="patient") | SEG0034 person_1 doctor: "have you noticed bleeding, vomiting or neck stiffness?" | MISSED | NO OUTPUT (record failed) |
| Vomiting (temporality="current", reported_by="patient") | SEG0034 person_1 doctor: "have you noticed bleeding, vomiting or neck stiffness?" | MISSED | NO OUTPUT (record failed) |
| Neck stiffness (temporality="current", reported_by="patient") | SEG0034 person_1 doctor: "have you noticed bleeding, vomiting or neck stiffness?" | MISSED | NO OUTPUT (record failed) |
| Diarrhoea (temporality="current", reported_by="patient") | SEG0037 person_2 patient: "No, no diarrhoea." | MISSED | NO OUTPUT (record failed) |
| Red eyes (temporality="current", reported_by="patient") | SEG0041 person_2 patient: "No red eyes or cough, none of it." | MISSED | NO OUTPUT (record failed) |
| Cough (temporality="current", reported_by="patient") | SEG0041 person_2 patient: "No red eyes or cough, none of it." | MISSED | NO OUTPUT (record failed) |
| *(extra P00)* | no allergies [EXTRA_SUPPORTED_BY_TRANSCRIPT]; no previous surgery [UNSUPPORTED]; no fever [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**past medical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Hypertension (status="ongoing", reported_by="patient") | SEG0013 person_2 patient: "High blood pressure, for about ten years. I've had eczema for five years now. I've got hea" | WRONG_NORM ('high blood pressure') | NO OUTPUT (record failed) |
| Eczema (status="ongoing", reported_by="patient") | SEG0013 person_2 patient: "High blood pressure, for about ten years. I've had eczema for five years now. I've got hea" | WRONG_ATTRIB: reported_by: gold="patient" pred="" | NO OUTPUT (record failed) |
| Ischaemic heart disease (status="ongoing", reported_by="patient") | SEG0013 person_2 patient: "High blood pressure, for about ten years. I've had eczema for five years now. I've got hea" | WRONG_NORM ('heart disease') | NO OUTPUT (record failed) |

**surgical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Coronary stenting (reported_by="patient") | SEG0017 person_2 patient: "I had a stent put in my heart two years ago." | WRONG_NORM ('stent') | NO OUTPUT (record failed) |

**family history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Thyroid disorder (relation="sister", reported_by="patient") | SEG0015 person_2 patient: "My sister has thyroid problems. Well, my mother has migraines." | WRONG_NORM ('thyroid problems') | NO OUTPUT (record failed) |
| Migraine (relation="mother", reported_by="patient") | SEG0015 person_2 patient: "My sister has thyroid problems. Well, my mother has migraines." | WRONG_NORM ('migraines') | NO OUTPUT (record failed) |

**social history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| smoking (status="current", reported_by="patient") | SEG0027 person_2 patient: "I smoke about ten cigarettes a day" | MISSED | NO OUTPUT (record failed) |
| alcohol (status="never", reported_by="patient") | SEG0029 person_2 patient: "I don't drink at all." | MISSED | NO OUTPUT (record failed) |
| exercise (status="none", reported_by="patient") | SEG0030 person_1 doctor: "how about exercise?" | MISSED | NO OUTPUT (record failed) |
| living (status="current", reported_by="patient") | SEG0032 person_1 doctor: "Do you live alone?" | MISSED | NO OUTPUT (record failed) |
| *(extra P00)* | lifestyle [UNSUPPORTED]; lifestyle [UNSUPPORTED] | | |

**medications**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Telmisartan (dose="40 mg", frequency="once a day", status="currently_used") | SEG0019 person_3 caregiver: "It's telmisartan, 40 milligrams, once a day, doctor." | WRONG_ATTRIB: frequency: gold="once a day" pred=null; reported_by: gold="caregiver" pred="person_3" (speaker id written instead of role) | NO OUTPUT (record failed) |
| Hydrocortisone (frequency="when needed", status="currently_used", reported_by="caregiver") | SEG0023 person_3 caregiver: "He takes hydrocortisone cream, when needed." | WRONG_NORM ('hydrocortisone cream') | NO OUTPUT (record failed) |
| Paracetamol (dose="650 mg", route="oral", frequency="three times a day") | SEG0055 person_1 doctor: "You'll be taking paracetamol, 650 milligrams, three times a day, for five days. You take i" | MISSED | NO OUTPUT (record failed) |

**allergies**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Antibiotic (unspecified) (status="uncertain", reported_by="patient") | SEG0025 person_2 patient: "I think I reacted to to some antibiotic once, years ago. I don't remember which one, or wh" | WRONG_NORM ('antibiotic') | NO OUTPUT (record failed) |

**physical examination**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Wrist and finger joint swelling (status="present", observed_by="doctor") | SEG0046 person_1 doctor: "Both wrists and several finger joints are puffy and tender." | MISSED | NO OUTPUT (record failed) |
| Truncal rash (status="present", observed_by="doctor") | SEG0048 person_1 doctor: "A fine rash over the chest and back, not itchy to touch." | WRONG_NORM ('fine rash over the chest and back') | NO OUTPUT (record failed) |
| *(extra P00)* | swollen and tender wrists and ankles [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**review of systems**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| genitourinary (status="negative", reported_by="patient") | SEG0043 person_2 patient: "no changes there" | MISSED | NO OUTPUT (record failed) |

**clinical conditions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | early inflammatory arthritis [INCORRECT - gold has this fact in category 'clinical assessment']; chikungunya [EXTRA_SUPPORTED_BY_TRANSCRIPT]; viral fever with joint involvement [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**clinical assessment**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Viral fever with joint involvement, possibly chikungunya (certainty="provisional", stated_by="doctor") | SEG0052 person_1 doctor: "I can't promise yet, but most people with a viral fever with joint involvement, possibly c" | WRONG_NORM ('probably a viral fever with joint involvement, possibly chikungunya') | NO OUTPUT (record failed) |
| Early inflammatory arthritis (certainty="differential", stated_by="doctor") | SEG0050 person_1 doctor: "Right, here's what I'm thinking. This is probably a viral fever with joint involvement, po" | MISSED | NO OUTPUT (record failed) |

**investigations/procedures**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Complete blood count (status="planned", type="laboratory") | SEG0053 person_1 doctor: "I'll request a full blood count, it'll help with fever. I want a dengue test done, that's " | WRONG_NORM ('full blood count') | NO OUTPUT (record failed) |
| Dengue NS1 antigen (status="planned", type="laboratory") | SEG0053 person_1 doctor: "I'll request a full blood count, it'll help with fever. I want a dengue test done, that's " | WRONG_NORM ('dengue test') | NO OUTPUT (record failed) |
| Chikungunya serology (status="planned", type="laboratory") | SEG0053 person_1 doctor: "I'll request a full blood count, it'll help with fever. I want a dengue test done, that's " | WRONG_NORM ('chikungunya test') | NO OUTPUT (record failed) |

**clinical actions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| investigation/arrange complete blood count (status="planned", responsible_person="doctor") | SEG0053 person_1 doctor: "I'll request a full blood count, it'll help with fever. I want a dengue test done, that's " | MISSED | NO OUTPUT (record failed) |
| investigation/arrange dengue ns1 antigen (status="planned", responsible_person="doctor") | SEG0053 person_1 doctor: "I'll request a full blood count, it'll help with fever. I want a dengue test done, that's " | MISSED | NO OUTPUT (record failed) |
| investigation/arrange chikungunya serology (status="planned", responsible_person="doctor") | SEG0053 person_1 doctor: "I'll request a full blood count, it'll help with fever. I want a dengue test done, that's " | MISSED | NO OUTPUT (record failed) |
| medication/start paracetamol 650 mg three times a day (status="planned", responsible_person="doctor") | SEG0055 person_1 doctor: "You'll be taking paracetamol, 650 milligrams, three times a day, for five days. You take i" | MISSED | NO OUTPUT (record failed) |
| counselling/avoid nsaids until dengue excluded (status="recommended", responsible_person="patient") | SEG0055 person_1 doctor: "You'll be taking paracetamol, 650 milligrams, three times a day, for five days. You take i" | MISSED | NO OUTPUT (record failed) |
| *(extra P00)* | medication/paracetamol 650 mg three times a day for five days [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**clinical uncertainties**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| allergy_uncertain (resolution_status="unresolved") | SEG0025 person_2 patient: "I think I reacted to to some antibiotic once, years ago. I don't remember which one, or wh" | MISSED | NO OUTPUT (record failed) |
| conflicting_statement (resolution_status="unresolved") | SEG0037 person_2 patient: "No, no diarrhoea." | MISSED | NO OUTPUT (record failed) |
| *(extra P00)* | date uncertain [UNSUPPORTED]; date uncertain [UNSUPPORTED]; date uncertain [UNSUPPORTED]; date uncertain [UNSUPPORTED]; date uncertain [UNSUPPORTED]; date uncertain [UNSUPPORTED]; date uncertain [UNSUPPORTED]; date uncertain [UNSUPPORTED] | | |

**Not applicable (no gold fact and no prediction):** vital signs, follow up.

**Evidence (L).**
- P00: 1 evidence records; 0 are an exact single transcript segment; 37 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_text_not_in_transcript': 1, 'ev_empty_supports': 1, 'fact_not_mentioned_in_cited_text': 15, 'fact_path_missing_from_supports': 15, 'fact_no_evidence_ids': 22}.
- P01: no usable output.

### Record 00040   (P00: FAILED, P01: parsed)

**Speakers (A).** Transcript: person_1 patient, person_2 doctor. Gold primary speakers: person_1 patient, person_2 doctor.
- P00: no usable output.
- P01: predicted [('person_1', 'patient'), ('person_2', 'doctor')]; all speakers+roles correct: True; missing none; wrong role none; invented ids none.

**Chief complaint (B).** Gold: 'tingling in my fingers' / normalized 'Paraesthesia' (reported by patient).
- P00: no usable output.
- P01: 'Tingling in fingers' / normalized 'Tingling in fingers' (reported_by patient) -> WRONG_NORM ('tingling in fingers')

**symptoms**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Paraesthesia (status="present", temporality="current", certainty="certain") | SEG0003 person_1 patient: "So the thing is, I've got tingling in my fingers." | NO OUTPUT (record failed) | WRONG_NORM ('tingling in fingers') |
| Wrist pain (status="present", temporality="current", certainty="certain") | SEG0006 person_2 doctor: "What about an ache in the wrist, have you noticed that?" | NO OUTPUT (record failed) | MISSED |
| Hand numbness (status="present", temporality="current", certainty="certain") | SEG0007 person_1 patient: "Yes, about the same, six months. With ache in the wrist, I'd say moderate. It's a couple o" | NO OUTPUT (record failed) | MISSED |
| Nocturnal paraesthesia (status="present", temporality="current", certainty="certain") | SEG0009 person_1 patient: "Honestly, once or twice a day. I've been waking up at night with pins and needles too, you" | NO OUTPUT (record failed) | MISSED |

**negative findings**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Headache (temporality="current", reported_by="patient") | SEG0035 person_1 patient: "No headache or weakness in the legs, none of it." | NO OUTPUT (record failed) | MISSED |
| Leg weakness (temporality="current", reported_by="patient") | SEG0035 person_1 patient: "No headache or weakness in the legs, none of it." | NO OUTPUT (record failed) | MISSED |
| Neck pain (temporality="current", reported_by="patient") | SEG0037 person_1 patient: "No neck pain, trouble walking or bladder problems, none of it." | NO OUTPUT (record failed) | MISSED |
| Gait difficulty (temporality="current", reported_by="patient") | SEG0037 person_1 patient: "No neck pain, trouble walking or bladder problems, none of it." | NO OUTPUT (record failed) | MISSED |
| Bladder dysfunction (temporality="current", reported_by="patient") | SEG0037 person_1 patient: "No neck pain, trouble walking or bladder problems, none of it." | NO OUTPUT (record failed) | MISSED |
| Joint swelling (temporality="current", reported_by="patient") | SEG0038 person_2 doctor: "Any swelling in the joints?" | NO OUTPUT (record failed) | MISSED |

**past medical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Hypothyroidism (status="ongoing", reported_by="patient") | SEG0029 person_1 patient: "I have an underactive thyroid, for about ten years." | NO OUTPUT (record failed) | MISSED |
| Type 2 diabetes mellitus (status="ongoing", reported_by="patient") | SEG0031 person_1 patient: "I've got diabetes." | NO OUTPUT (record failed) | WRONG_NORM ('diabetes') |
| Hypercholesterolaemia (status="ongoing", reported_by="patient") | SEG0033 person_1 patient: "I've got high cholesterol." | NO OUTPUT (record failed) | WRONG_NORM ('high cholesterol') |

**surgical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Appendicectomy (reported_by="patient") | SEG0027 person_1 patient: "I had my appendix out about eight years ago." | NO OUTPUT (record failed) | WRONG_NORM ('Appendectomy') |

**family history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Colon cancer (relation="uncle", reported_by="patient") | SEG0025 person_1 patient: "My uncle had colon cancer. Okay, you know, so my mother has migraines." | NO OUTPUT (record failed) | CORRECT |
| Migraine (relation="mother", reported_by="patient") | SEG0025 person_1 patient: "My uncle had colon cancer. Okay, you know, so my mother has migraines." | NO OUTPUT (record failed) | WRONG_NORM ('Migraines') |

**social history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| exercise (status="current", reported_by="patient") | SEG0018 person_2 doctor: "Do you get any exercise?" | NO OUTPUT (record failed) | WRONG_STATUS: status: gold="current" pred="ongoing" |
| diet (status="current", reported_by="patient") | SEG0020 person_2 doctor: "What's your diet like?" | NO OUTPUT (record failed) | WRONG_STATUS: status: gold="current" pred="ongoing" |

**medications**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Levothyroxine (dose="75 micrograms", frequency="every morning", status="currently_used") | SEG0011 person_1 patient: "I'm on thyroxine, every morning." | NO OUTPUT (record failed) | WRONG_NORM ('thyroxine') |
| Metformin (dose="500 mg", frequency="twice a day", status="currently_used") | SEG0015 person_1 patient: "For two months. Metformin, twice a day." | NO OUTPUT (record failed) | CORRECT |
| Atorvastatin (dose="20 mg", frequency="at night", status="currently_used") | SEG0017 person_1 patient: "500 milligrams, I think that's what's on the box. Atorvastatin. I take it 20 milligrams, a" | NO OUTPUT (record failed) | PARTIAL: frequency: gold="at night" pred="night" |
| Rosuvastatin (status="discontinued", reported_by="patient") | SEG0017 person_1 patient: "500 milligrams, I think that's what's on the box. Atorvastatin. I take it 20 milligrams, a" | NO OUTPUT (record failed) | MISSED |

**allergies**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Antibiotic (unspecified) (status="uncertain", reported_by="patient") | SEG0023 person_1 patient: "Right, I think I reacted to some antibiotic once, years ago. I don't remember which one, o" | NO OUTPUT (record failed) | WRONG_NORM ('antibiotic') |

**vital signs**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Body temperature (value=36.7, unit="°C", reported_by="doctor") | SEG0046 person_2 doctor: "Okay: temperature 36.7, BP is 123 over 70. And heart rate 64, SpO2 97 percent on room air." | NO OUTPUT (record failed) | WRONG_NORM ('temperature') |
| Blood pressure (value="123/70", unit="mmHg", reported_by="doctor") | SEG0046 person_2 doctor: "Okay: temperature 36.7, BP is 123 over 70. And heart rate 64, SpO2 97 percent on room air." | NO OUTPUT (record failed) | CORRECT |
| Heart rate (value=64, unit="bpm", reported_by="doctor") | SEG0046 person_2 doctor: "Okay: temperature 36.7, BP is 123 over 70. And heart rate 64, SpO2 97 percent on room air." | NO OUTPUT (record failed) | CORRECT |
| Oxygen saturation (value=97, unit="%", reported_by="doctor") | SEG0046 person_2 doctor: "Okay: temperature 36.7, BP is 123 over 70. And heart rate 64, SpO2 97 percent on room air." | NO OUTPUT (record failed) | CORRECT |

**physical examination**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Positive Phalen's test (status="present", observed_by="doctor") | SEG0050 person_2 doctor: "Bending the wrist for a minute brings on the numbness." | NO OUTPUT (record failed) | MISSED |
| Positive Tinel's sign (status="present", observed_by="doctor") | SEG0052 person_2 doctor: "Tapping over the wrist reproduces the tingling." | NO OUTPUT (record failed) | MISSED |
| *(extra P01)* | numbness in the thumb and first two fingers [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**review of systems**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| cardiovascular (status="negative", reported_by="patient") | SEG0041 person_1 patient: "Nothing like that." | NO OUTPUT (record failed) | MISSED |
| respiratory (status="negative", reported_by="patient") | SEG0043 person_1 patient: "Okay, so no problems with breathing." | NO OUTPUT (record failed) | MISSED |
| *(extra P01)* | neurological [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**clinical conditions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Type 2 diabetes mellitus (status="existing", reported_by="patient") | SEG0031 person_1 patient: "I've got diabetes." | NO OUTPUT (record failed) | MISSED |
| Hypercholesterolaemia (status="existing", reported_by="patient") | SEG0033 person_1 patient: "I've got high cholesterol." | NO OUTPUT (record failed) | MISSED |
| *(extra P01)* | underactive thyroid [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**clinical assessment**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Carpal tunnel syndrome (certainty="provisional", stated_by="doctor") | SEG0053 person_2 doctor: "That's all I need, thank you. Right, here's what I'm thinking. The most likely explanation" | NO OUTPUT (record failed) | CORRECT |
| Pinched nerve in the neck (certainty="differential", stated_by="doctor") | SEG0053 person_2 doctor: "That's all I need, thank you. Right, here's what I'm thinking. The most likely explanation" | NO OUTPUT (record failed) | MISSED |

**investigations/procedures**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| HbA1c (status="planned", type="laboratory") | SEG0053 person_2 doctor: "That's all I need, thank you. Right, here's what I'm thinking. The most likely explanation" | NO OUTPUT (record failed) | MISSED |
| Nerve conduction study (status="planned", type="other") | SEG0053 person_2 doctor: "That's all I need, thank you. Right, here's what I'm thinking. The most likely explanation" | NO OUTPUT (record failed) | PARTIAL: type: gold="other" pred="laboratory" |
| *(extra P01)* | neuropathy screen [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**clinical actions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| investigation/arrange hba1c (status="planned", responsible_person="doctor") | SEG0053 person_2 doctor: "That's all I need, thank you. Right, here's what I'm thinking. The most likely explanation" | NO OUTPUT (record failed) | MISSED |
| investigation/arrange nerve conduction study (status="planned", responsible_person="doctor") | SEG0053 person_2 doctor: "That's all I need, thank you. Right, here's what I'm thinking. The most likely explanation" | NO OUTPUT (record failed) | MISSED |
| counselling/advise typing breaks (status="recommended", responsible_person="patient") | SEG0053 person_2 doctor: "That's all I need, thank you. Right, here's what I'm thinking. The most likely explanation" | NO OUTPUT (record failed) | MISSED |
| counselling/seek urgent care if the symptoms get worse (status="recommended", responsible_person="patient") | SEG0053 person_2 doctor: "That's all I need, thank you. Right, here's what I'm thinking. The most likely explanation" | NO OUTPUT (record failed) | MISSED |
| follow up/follow up consultation (status="planned", responsible_person="doctor") | SEG0054 person_2 doctor: "See me again after the results are back." | NO OUTPUT (record failed) | MISSED |
| *(extra P01)* | follow up/see me again after the results are back [UNSUPPORTED] | | |

**follow up**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| consultation/after the results are back (status="planned", time_reference="after the results are ba) | SEG0054 person_2 doctor: "See me again after the results are back." | NO OUTPUT (record failed) | MISSED |
| *(extra P01)* | consultation/ [UNSUPPORTED] | | |

**clinical uncertainties**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| adherence_uncertain (resolution_status="unresolved") | SEG0017 person_1 patient: "500 milligrams, I think that's what's on the box. Atorvastatin. I take it 20 milligrams, a" | NO OUTPUT (record failed) | MISSED |
| allergy_uncertain (resolution_status="unresolved") | SEG0023 person_1 patient: "Right, I think I reacted to some antibiotic once, years ago. I don't remember which one, o" | NO OUTPUT (record failed) | MISSED |
| *(extra P01)* | date uncertain [UNSUPPORTED]; date uncertain [UNSUPPORTED] | | |

**Not applicable (no gold fact and no prediction):** none.

**Evidence (L).**
- P00: no usable output.
- P01: 1 evidence records; 0 are an exact single transcript segment; 27 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_text_not_in_transcript': 1, 'ev_empty_supports': 1, 'fact_path_missing_from_supports': 19, 'fact_no_evidence_ids': 8, 'fact_not_mentioned_in_cited_text': 17}.

### Record 00042   (P00: parsed, P01: parsed)

**Speakers (A).** Transcript: person_1 patient, person_2 doctor. Gold primary speakers: person_1 patient, person_2 doctor.
- P00: predicted [('person_1', 'patient'), ('person_2', 'doctor')]; all speakers+roles correct: True; missing none; wrong role none; invented ids none.
- P01: predicted [('person_1', 'patient'), ('person_2', 'doctor')]; all speakers+roles correct: True; missing none; wrong role none; invented ids none.

**Chief complaint (B).** Gold: 'constant thirst' / normalized 'Polydipsia' (reported by patient).
- P00: 'constant thirst' / normalized 'constant thirst' (reported_by patient) -> WRONG_NORM ('constant thirst')
- P01: 'constant thirst' / normalized 'constant thirst' (reported_by patient) -> WRONG_NORM ('constant thirst')

**symptoms**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Polydipsia (status="present", temporality="current", certainty="certain") | SEG0003 person_1 patient: "I wanted to get constant thirst looked at. I'd rather know what's going on than keep guess" | WRONG_NORM ('constant thirst') | WRONG_NORM ('constant thirst') |
| Fatigue (status="present", temporality="current", certainty="certain") | SEG0009 person_1 patient: "Tiredness goes along with it, most of the time. Oh, the Tiredness? That's been for about t" | MISSED | MISSED |
| Polydipsia (status="resolved", temporality="past", certainty="certain") | SEG0010 person_2 doctor: "Have you had constant thirst before, or is this the first time?" | MISSED | MISSED |

**negative findings**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Chest pain (temporality="current", reported_by="patient") | SEG0012 person_2 doctor: "Did you get chest pain, vomiting or weight loss?" | MISSED | MISSED |
| Vomiting (temporality="current", reported_by="patient") | SEG0012 person_2 doctor: "Did you get chest pain, vomiting or weight loss?" | MISSED | MISSED |
| Weight loss (temporality="current", reported_by="patient") | SEG0012 person_2 doctor: "Did you get chest pain, vomiting or weight loss?" | MISSED | MISSED |
| Foot ulcers (temporality="current", reported_by="patient") | SEG0014 person_2 doctor: "Any sign of foot sores?" | MISSED | MISSED |

**past medical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Type 2 diabetes mellitus (status="ongoing", reported_by="patient") | SEG0021 person_1 patient: "Yes, diabetes." | WRONG_NORM ('diabetes') | WRONG_NORM ('diabetes') |
| Hypertension (status="ongoing", reported_by="patient") | SEG0023 person_1 patient: "I have high blood pressure." | MISSED | MISSED |

**surgical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Cholecystectomy (reported_by="patient") | SEG0028 person_1 patient: "I had my gallbladder removed in 2016." | WRONG_NORM ('gallbladder removal') | WRONG_NORM ('gallbladder removal') |

**social history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| smoking (status="current", reported_by="patient") | SEG0026 person_1 patient: "I smoke about ten cigarettes a day. I don't drink at all. I drive a delivery van all day. " | MISSED | MISSED |
| alcohol (status="never", reported_by="patient") | SEG0026 person_1 patient: "I smoke about ten cigarettes a day. I don't drink at all. I drive a delivery van all day. " | MISSED | MISSED |
| occupation (status="current", reported_by="patient") | SEG0026 person_1 patient: "I smoke about ten cigarettes a day. I don't drink at all. I drive a delivery van all day. " | MISSED | MISSED |
| diet (status="current", reported_by="patient") | SEG0026 person_1 patient: "I smoke about ten cigarettes a day. I don't drink at all. I drive a delivery van all day. " | MISSED | MISSED |
| exercise (status="current", reported_by="patient") | SEG0025 person_2 doctor: "Yes, diabetes is known to us, good to have that clear. So, tell me about your routine, wor" | MISSED | MISSED |
| *(extra P00)* | lifestyle [UNSUPPORTED] | | |
| *(extra P01)* | lifestyle [UNSUPPORTED] | | |

**medications**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Metformin (dose="500 mg", frequency="twice a day", status="currently_used") | SEG0005 person_1 patient: "Okay, so I'm on metformin, 500 milligrams, twice a day. It's telmisartan, 40 milligrams, o" | UNSUPPORTED: route: not in gold, pred="oral" | UNSUPPORTED: route: not in gold, pred="oral" |
| Telmisartan (dose="40 mg", frequency="once a day", status="currently_used") | SEG0005 person_1 patient: "Okay, so I'm on metformin, 500 milligrams, twice a day. It's telmisartan, 40 milligrams, o" | UNSUPPORTED: route: not in gold, pred="oral" | UNSUPPORTED: route: not in gold, pred="oral" |
| Glimepiride (dose="1 mg", frequency="before breakfast", status="planned") | SEG0040 person_2 doctor: "Let's get an HbA1c, for diabetes control. For this, glimepiride, 1 milligrams, before brea" | MISSED | WRONG_STATUS: route: not in gold, pred="oral"; status: gold="planned" pred="currently_used"; reported_by: gold="doctor" pred="patient" |

**allergies**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | unknown [INCORRECT - placeholder written as an allergy entry (gold has no allergy)] | | |
| *(extra P01)* | glimepiride [INCORRECT - a medication from the medication list written as an allergy] | | |

**vital signs**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Blood pressure (value="167/90", unit="mmHg", reported_by="doctor") | SEG0031 person_2 doctor: "Okay: pressure 167 over 90, pulse 78, SpO2 97 percent on room air, height 164 centimetres," | CORRECT | CORRECT |
| Heart rate (value=78, unit="bpm", reported_by="doctor") | SEG0031 person_2 doctor: "Okay: pressure 167 over 90, pulse 78, SpO2 97 percent on room air, height 164 centimetres," | MISSED | MISSED |
| Oxygen saturation (value=97, unit="%", reported_by="doctor") | SEG0031 person_2 doctor: "Okay: pressure 167 over 90, pulse 78, SpO2 97 percent on room air, height 164 centimetres," | CORRECT | CORRECT |
| Body height (value=164, unit="cm", reported_by="doctor") | SEG0031 person_2 doctor: "Okay: pressure 167 over 90, pulse 78, SpO2 97 percent on room air, height 164 centimetres," | WRONG_NORM ('height') | WRONG_NORM ('height') |
| Body temperature (value=36.8, unit="°C", reported_by="doctor") | SEG0031 person_2 doctor: "Okay: pressure 167 over 90, pulse 78, SpO2 97 percent on room air, height 164 centimetres," | WRONG_NORM ('temperature') | MISSED |
| Body weight (value=54, unit="kg", reported_by="doctor") | SEG0031 person_2 doctor: "Okay: pressure 167 over 90, pulse 78, SpO2 97 percent on room air, height 164 centimetres," | WRONG_NORM ('weight') | WRONG_NORM ('weight') |
| *(extra P00)* | pulse [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |
| *(extra P01)* | pulse [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**physical examination**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| No foot ulcers (status="absent", observed_by="doctor") | SEG0034 person_2 doctor: "your feet look fine, no ulcers or sores, and the pulses are palpable" | WRONG_NORM ('feet look fine no ulcers or sores and the pulses are palpable') | WRONG_NORM ('feet look fine no ulcers or sores and the pulses are palpable') |

**review of systems**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| neurological (status="negative", reported_by="patient") | SEG0016 person_2 doctor: "Neurologically, anything strange?" | MISSED | MISSED |
| skin (status="negative", reported_by="patient") | SEG0019 person_1 patient: "Nothing on the skin, no." | MISSED | MISSED |
| *(extra P00)* | diabetes [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |
| *(extra P01)* | diabetes [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**clinical conditions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Type 2 diabetes mellitus (status="existing", reported_by="patient") | SEG0021 person_1 patient: "Yes, diabetes." | WRONG_NORM ('diabetes') | WRONG_NORM ('diabetes') |

**clinical assessment**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Diabetes that isn't well controlled (certainty="provisional", stated_by="doctor") | SEG0037 person_2 doctor: "It's reasonable to be concerned, but right now diabetes that isn't well controlled is my l" | WRONG_NORM ('this is probably diabetes that isn t well controlled') | WRONG_NORM ('this is probably diabetes that isn t well controlled') |

**investigations/procedures**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Renal function test (status="planned", type="laboratory") | SEG0038 person_2 doctor: "I want kidney function tests done, that's for diabetes." | WRONG_NORM ('kidney function tests') | WRONG_NORM ('kidney function tests') |
| HbA1c (status="planned", type="laboratory") | SEG0040 person_2 doctor: "Let's get an HbA1c, for diabetes control. For this, glimepiride, 1 milligrams, before brea" | PARTIAL: type: gold="laboratory" pred="other" | CORRECT |

**clinical actions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| investigation/arrange renal function test (status="planned", responsible_person="doctor") | SEG0038 person_2 doctor: "I want kidney function tests done, that's for diabetes." | MISSED | MISSED |
| investigation/arrange hba1c (status="planned", responsible_person="doctor") | SEG0040 person_2 doctor: "Let's get an HbA1c, for diabetes control. For this, glimepiride, 1 milligrams, before brea" | MISSED | MISSED |
| medication/start glimepiride 1 mg before breakfast (status="planned", responsible_person="doctor") | SEG0040 person_2 doctor: "Let's get an HbA1c, for diabetes control. For this, glimepiride, 1 milligrams, before brea" | MISSED | MISSED |
| counselling/advise dietary sugar reduction (status="recommended", responsible_person="patient") | SEG0040 person_2 doctor: "Let's get an HbA1c, for diabetes control. For this, glimepiride, 1 milligrams, before brea" | MISSED | MISSED |
| referral/refer to dietitian (status="planned", responsible_person="doctor") | SEG0040 person_2 doctor: "Let's get an HbA1c, for diabetes control. For this, glimepiride, 1 milligrams, before brea" | MISSED | MISSED |
| follow up/follow up consultation (status="planned", responsible_person="doctor") | SEG0042 person_2 doctor: "I'd like you back after the results are back. So, take care, and call us if anything chang" | MISSED | MISSED |
| *(extra P00)* | counselling/for blood sugar control glimepiride 1 mg before breakfast until we review [UNSUPPORTED]; investigation/kidney function tests [UNSUPPORTED]; investigation/hba1c [UNSUPPORTED] | | |
| *(extra P01)* | counselling/dietitian referral [UNSUPPORTED]; investigation/kidney function tests [UNSUPPORTED]; investigation/hba1c [UNSUPPORTED] | | |

**follow up**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| consultation/after the results are back (status="planned", time_reference="after the results are ba) | SEG0042 person_2 doctor: "I'd like you back after the results are back. So, take care, and call us if anything chang" | MISSED | MISSED |
| *(extra P00)* | consultation/ [UNSUPPORTED] | | |
| *(extra P01)* | consultation/ [UNSUPPORTED] | | |

**clinical uncertainties**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | date uncertain [UNSUPPORTED]; conflicting statement [UNSUPPORTED] | | |
| *(extra P01)* | date uncertain [UNSUPPORTED] | | |

**Not applicable (no gold fact and no prediction):** family history.

**Evidence (L).**
- P00: 1 evidence records; 0 are an exact single transcript segment; 26 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_multi_segment_or_whole_transcript_dump': 1, 'ev_empty_supports': 1, 'fact_path_missing_from_supports': 26, 'fact_not_mentioned_in_cited_text': 16}.
- P01: 1 evidence records; 0 are an exact single transcript segment; 25 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_multi_segment_or_whole_transcript_dump': 1, 'ev_empty_supports': 1, 'fact_path_missing_from_supports': 24, 'fact_not_mentioned_in_cited_text': 20, 'fact_no_evidence_ids': 1}.

### Record 00060   (P00: FAILED, P01: parsed)

**Speakers (A).** Transcript: person_1 patient, person_2 doctor, person_3 family_member. Gold primary speakers: person_1 patient, person_2 doctor, person_3 family_member.
- P00: no usable output.
- P01: predicted [('person_1', 'patient'), ('person_2', 'doctor'), ('person_3', 'family_member')]; all speakers+roles correct: True; missing none; wrong role none; invented ids none.

**Chief complaint (B).** Gold: 'fever and chills' / normalized 'Fever and chills' (reported by patient).
- P00: no usable output.
- P01: 'fever and chills' / normalized 'fever and chills' (reported_by person_1) -> WRONG_ATTRIB: reported_by: gold="patient" pred="person_1" (speaker id written instead of role)

**symptoms**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Fever and chills (status="present", temporality="current", certainty="certain") | SEG0004 person_1 patient: "Well, um, I've been having fever and chills." | NO OUTPUT (record failed) | WRONG_NORM ('fever') |
| Shortness of breath (status="present", temporality="current", certainty="certain") | SEG0008 person_1 patient: "Honestly, a couple of times a week. Severe, I'd say. I've also had shortness of breath, fo" | NO OUTPUT (record failed) | WRONG_ATTRIB: duration: gold={"value": 5, "unit": "days", "normalized pred={"value": null, "unit": null, "normalize; reported_by: gold="patient" pred="person_1" (sp |
| Weakness (status="present", temporality="current", certainty="certain") | SEG0009 person_2 doctor: "Have you been feeling very weak?" | NO OUTPUT (record failed) | MISSED |
| Pleuritic chest pain (status="present", temporality="current", certainty="certain") | SEG0011 person_2 doctor: "What about sharp pain on the right side when you breathe in, have you noticed that?" | NO OUTPUT (record failed) | WRONG_NORM ('sharp pain on the right side when breathing in') |
| *(extra P01)* | chills [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**negative findings**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Haemoptysis (temporality="current", reported_by="patient") | SEG0013 person_2 doctor: "Any coughing up blood, palpitations or recent travel?" | NO OUTPUT (record failed) | MISSED |
| Palpitations (temporality="current", reported_by="patient") | SEG0013 person_2 doctor: "Any coughing up blood, palpitations or recent travel?" | NO OUTPUT (record failed) | MISSED |
| Recent travel (temporality="current", reported_by="patient") | SEG0013 person_2 doctor: "Any coughing up blood, palpitations or recent travel?" | NO OUTPUT (record failed) | MISSED |
| Leg swelling (temporality="current", reported_by="patient") | SEG0016 person_1 patient: "No. No leg swelling." | NO OUTPUT (record failed) | WRONG_NORM ('no leg swelling') |

**past medical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Type 2 diabetes mellitus (status="ongoing", reported_by="patient") | SEG0024 person_1 patient: "I have diabetes, for about a year. I have high blood pressure, for two years." | NO OUTPUT (record failed) | WRONG_NORM ('diabetes') |
| Hypertension (status="ongoing", reported_by="patient") | SEG0024 person_1 patient: "I have diabetes, for about a year. I have high blood pressure, for two years." | NO OUTPUT (record failed) | WRONG_NORM ('high blood pressure') |

**surgical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Thyroid surgery (reported_by="patient") | SEG0022 person_1 patient: "I had my thyroid operated on a long time ago." | NO OUTPUT (record failed) | WRONG_NORM ('thyroid operation') |

**family history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P01)* | diabetes [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**social history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| smoking (status="current", reported_by="patient") | SEG0031 person_1 patient: "I smoke, yes, around five a day. A beer or two most evenings, to be honest. I try to avoid" | NO OUTPUT (record failed) | MISSED |
| alcohol (status="current", reported_by="patient") | SEG0030 person_2 doctor: "A few questions about your lifestyle now." | NO OUTPUT (record failed) | MISSED |
| diet (status="current", reported_by="patient") | SEG0031 person_1 patient: "I smoke, yes, around five a day. A beer or two most evenings, to be honest. I try to avoid" | NO OUTPUT (record failed) | MISSED |
| exercise (status="current", reported_by="patient") | SEG0030 person_2 doctor: "A few questions about your lifestyle now." | NO OUTPUT (record failed) | MISSED |
| *(extra P01)* | lifestyle [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**medications**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Ramipril (dose="5 mg", frequency="every morning", status="currently_used") | SEG0026 person_3 family_member: "She takes ramipril, 5 milligrams, every morning for my blood pressure." | NO OUTPUT (record failed) | WRONG_ATTRIB: route: not in gold, pred="oral"; reported_by: gold="family_member" pred="person_3" (speaker id written instead of role) |
| Telmisartan (status="discontinued", reported_by="patient") | SEG0027 person_1 patient: "I used to take telmisartan, but I stopped it." | NO OUTPUT (record failed) | WRONG_ATTRIB: reported_by: gold="patient" pred="person_1" (speaker id written instead of role) |
| Paracetamol (dose="500 mg", frequency="every six hours if neede, status="planned") | SEG0045 person_2 doctor: "We'll begin with paracetamol, 500 milligrams, every six hours if needed, for three days. I" | NO OUTPUT (record failed) | MISSED |

**allergies**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Antibiotic (unspecified) (status="uncertain", reported_by="patient") | SEG0029 person_1 patient: "Hmm, there was some antibiotic, I was told I was allergic. But I couldn't tell you what it" | NO OUTPUT (record failed) | WRONG_NORM ('antibiotic') |

**vital signs**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Blood pressure (value="139/75", unit="mmHg", reported_by="doctor") | SEG0034 person_2 doctor: "Okay: BP is 139 over 75, heart rate 90. And respiratory rate 22, BMI works out to 17.3, he" | NO OUTPUT (record failed) | WRONG_ATTRIB: reported_by: gold="doctor" pred="person_2" (speaker id written instead of role) |
| Heart rate (value=90, unit="bpm", reported_by="doctor") | SEG0034 person_2 doctor: "Okay: BP is 139 over 75, heart rate 90. And respiratory rate 22, BMI works out to 17.3, he" | NO OUTPUT (record failed) | WRONG_ATTRIB: reported_by: gold="doctor" pred="person_2" (speaker id written instead of role) |
| Respiratory rate (value=22, unit="breaths/min", reported_by="doctor") | SEG0034 person_2 doctor: "Okay: BP is 139 over 75, heart rate 90. And respiratory rate 22, BMI works out to 17.3, he" | NO OUTPUT (record failed) | WRONG_ATTRIB: unit: gold="breaths/min" pred="breaths per minute"; reported_by: gold="doctor" pred="person_2" (speaker id written instead of role) |
| Body mass index (value=17.3, unit="kg/m²", reported_by="doctor") | SEG0034 person_2 doctor: "Okay: BP is 139 over 75, heart rate 90. And respiratory rate 22, BMI works out to 17.3, he" | NO OUTPUT (record failed) | MISSED |
| Body height (value=180, unit="cm", reported_by="doctor") | SEG0034 person_2 doctor: "Okay: BP is 139 over 75, heart rate 90. And respiratory rate 22, BMI works out to 17.3, he" | NO OUTPUT (record failed) | WRONG_NORM ('height') |
| Oxygen saturation (value=91, unit="%", reported_by="doctor") | SEG0034 person_2 doctor: "Okay: BP is 139 over 75, heart rate 90. And respiratory rate 22, BMI works out to 17.3, he" | NO OUTPUT (record failed) | WRONG_ATTRIB: reported_by: gold="doctor" pred="person_2" (speaker id written instead of role) |
| Body weight (value=56, unit="kg", reported_by="doctor") | SEG0034 person_2 doctor: "Okay: BP is 139 over 75, heart rate 90. And respiratory rate 22, BMI works out to 17.3, he" | NO OUTPUT (record failed) | WRONG_NORM ('weight') |
| Body temperature (value=37.2, unit="°C", reported_by="doctor") | SEG0034 person_2 doctor: "Okay: BP is 139 over 75, heart rate 90. And respiratory rate 22, BMI works out to 17.3, he" | NO OUTPUT (record failed) | MISSED |
| *(extra P01)* | bmi [UNSUPPORTED]; temperature [UNSUPPORTED] | | |

**physical examination**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Tachypnoea (status="present", observed_by="doctor") | SEG0037 person_2 doctor: "Breathing rate is a bit fast." | NO OUTPUT (record failed) | MISSED |
| Right lower zone crackles (status="present", observed_by="doctor") | SEG0039 person_2 doctor: "There's bronchial breathing and crackles at the right lower zone." | NO OUTPUT (record failed) | WRONG_NORM ('bronchial breathing and crackles at the right lower zone') |

**review of systems**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| cardiovascular (status="negative", reported_by="patient") | SEG0017 person_2 doctor: "On the cardiac side, anything I should know?" | NO OUTPUT (record failed) | MISSED |
| neurological (status="negative", reported_by="patient") | SEG0020 person_1 patient: "Yeah, no, that's all normal." | NO OUTPUT (record failed) | MISSED |
| *(extra P01)* | respiratory [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**clinical conditions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Hypertension (status="existing", reported_by="patient") | SEG0024 person_1 patient: "I have diabetes, for about a year. I have high blood pressure, for two years." | NO OUTPUT (record failed) | MISSED |
| *(extra P01)* | pneumonia [EXTRA_SUPPORTED_BY_TRANSCRIPT]; pulmonary embolism [INCORRECT - gold has this fact in category 'clinical assessment'] | | |

**clinical assessment**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Possible pneumonia on the right side (certainty="provisional", stated_by="doctor") | SEG0041 person_2 doctor: "Okay, so my impression is this: This looks most like a possible pneumonia on the right sid" | NO OUTPUT (record failed) | MISSED |
| Pulmonary embolism (certainty="differential", stated_by="doctor") | SEG0041 person_2 doctor: "Okay, so my impression is this: This looks most like a possible pneumonia on the right sid" | NO OUTPUT (record failed) | MISSED |
| *(extra P01)* | this looks most like a possible pneumonia on the right side a pulmonary embolism is still possible [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**investigations/procedures**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Sputum culture (status="planned", type="laboratory") | SEG0041 person_2 doctor: "Okay, so my impression is this: This looks most like a possible pneumonia on the right sid" | NO OUTPUT (record failed) | CORRECT |
| Complete blood count and CRP (status="planned", type="laboratory") | SEG0043 person_2 doctor: "We should do blood tests for infection. Let's get a chest X-ray, for suspected pneumonia." | NO OUTPUT (record failed) | MISSED |
| Chest X-ray (status="planned", type="imaging") | SEG0043 person_2 doctor: "We should do blood tests for infection. Let's get a chest X-ray, for suspected pneumonia." | NO OUTPUT (record failed) | CORRECT |

**clinical actions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| investigation/arrange sputum culture (status="planned", responsible_person="doctor") | SEG0041 person_2 doctor: "Okay, so my impression is this: This looks most like a possible pneumonia on the right sid" | NO OUTPUT (record failed) | MISSED |
| investigation/arrange complete blood count and crp (status="planned", responsible_person="doctor") | SEG0043 person_2 doctor: "We should do blood tests for infection. Let's get a chest X-ray, for suspected pneumonia." | NO OUTPUT (record failed) | MISSED |
| investigation/arrange chest x ray (status="planned", responsible_person="doctor") | SEG0043 person_2 doctor: "We should do blood tests for infection. Let's get a chest X-ray, for suspected pneumonia." | NO OUTPUT (record failed) | MISSED |
| medication/start paracetamol 500 mg every six hours if needed (status="planned", responsible_person="doctor") | SEG0045 person_2 doctor: "We'll begin with paracetamol, 500 milligrams, every six hours if needed, for three days. I" | NO OUTPUT (record failed) | MISSED |
| counselling/advise rest fluids and completing antibiotics (status="recommended", responsible_person="patient") | SEG0045 person_2 doctor: "We'll begin with paracetamol, 500 milligrams, every six hours if needed, for three days. I" | NO OUTPUT (record failed) | MISSED |
| counselling/advise smoking cessation (status="recommended", responsible_person="patient") | SEG0045 person_2 doctor: "We'll begin with paracetamol, 500 milligrams, every six hours if needed, for three days. I" | NO OUTPUT (record failed) | MISSED |
| counselling/seek urgent care if the breathlessness worsens or you become drowsy (status="recommended", responsible_person="patient") | SEG0045 person_2 doctor: "We'll begin with paracetamol, 500 milligrams, every six hours if needed, for three days. I" | NO OUTPUT (record failed) | MISSED |
| follow up/follow up consultation (status="planned", responsible_person="doctor") | SEG0047 person_2 doctor: "Book a review in three days. That's everything from me. Any other questions?" | NO OUTPUT (record failed) | MISSED |
| *(extra P01)* | medication/paracetamol 500 mg every six hours if needed for three days [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**follow up**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| consultation/in three days (status="planned", time_reference="in three days") | SEG0047 person_2 doctor: "Book a review in three days. That's everything from me. Any other questions?" | NO OUTPUT (record failed) | WRONG_NORM ('consultation/three days') |

**clinical uncertainties**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| allergy_uncertain (resolution_status="unresolved") | SEG0029 person_1 patient: "Hmm, there was some antibiotic, I was told I was allergic. But I couldn't tell you what it" | NO OUTPUT (record failed) | MISSED |
| *(extra P01)* | date uncertain [UNSUPPORTED] | | |

**Not applicable (no gold fact and no prediction):** none.

**Evidence (L).**
- P00: no usable output.
- P01: 1 evidence records; 0 are an exact single transcript segment; 32 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_multi_segment_or_whole_transcript_dump': 1, 'ev_empty_supports': 1, 'fact_not_mentioned_in_cited_text': 26, 'fact_path_missing_from_supports': 31, 'fact_no_evidence_ids': 1}.

### Record 00069   (P00: parsed, P01: parsed)

**Speakers (A).** Transcript: person_1 patient, person_2 doctor. Gold primary speakers: person_1 patient, person_2 doctor.
- P00: predicted [('person_1', 'patient'), ('person_2', 'doctor')]; all speakers+roles correct: True; missing none; wrong role none; invented ids none.
- P01: predicted [('person_1', 'patient'), ('person_2', 'doctor')]; all speakers+roles correct: True; missing none; wrong role none; invented ids none.

**Chief complaint (B).** Gold: 'pain low in the pelvis' / normalized 'Pelvic pain' (reported by patient).
- P00: 'pain low in the pelvis' / normalized 'pain low in the pelvis' (reported_by person_1) -> WRONG_NORM ('pain low in the pelvis')
- P01: 'pain low in the pelvis' / normalized 'pain low in the pelvis' (reported_by patient) -> WRONG_NORM ('pain low in the pelvis')

**symptoms**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Pelvic pain (status="present", temporality="current", certainty="certain") | SEG0003 person_1 patient: "well, I've been having pain low in the pelvis" | WRONG_NORM ('pain') | WRONG_NORM ('pain') |
| Bloating (status="present", temporality="current", certainty="certain") | SEG0009 person_1 patient: "it usually comes with bloating the, The bloating? That's been for two days as for bloating" | MISSED | MISSED |

**negative findings**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Dysuria (temporality="current", reported_by="patient") | SEG0010 person_2 doctor: "and what about burning when passing urine, missed period or vaginal discharge?" | MISSED | MISSED |
| Missed period (temporality="current", reported_by="patient") | SEG0010 person_2 doctor: "and what about burning when passing urine, missed period or vaginal discharge?" | MISSED | MISSED |
| Vaginal discharge (temporality="current", reported_by="patient") | SEG0010 person_2 doctor: "and what about burning when passing urine, missed period or vaginal discharge?" | MISSED | MISSED |
| Fever (temporality="current", reported_by="patient") | SEG0012 person_2 doctor: "Nothing like fever?" | MISSED | MISSED |
| No known allergies (temporality="current", reported_by="patient") | SEG0017 person_1 patient: "Okay, so no, no allergies to anything." | MISSED | MISSED |
| No regular medication (temporality="current", reported_by="patient") | SEG0018 person_2 doctor: "any regular medication?" | MISSED | MISSED |
| No known chronic conditions (temporality="current", reported_by="patient") | SEG0020 person_2 doctor: "Do you have any medical conditions I should know about?" | MISSED | MISSED |

**social history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| living (status="current", reported_by="patient") | SEG0022 person_2 doctor: "So, do you live alone?" | MISSED | MISSED |
| exercise (status="none", reported_by="patient") | SEG0024 person_2 doctor: "How about exercise?" | MISSED | MISSED |

**medications**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Mefenamic acid (dose="500 mg", route="oral", frequency="three times a day with f) | SEG0036 person_2 doctor: "I think a pelvic ultrasound makes sense here, for pelvic pain. Let's use mefenamic acid, 5" | MISSED | MISSED |

**vital signs**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Body weight (value=59, unit="kg", reported_by="doctor") | SEG0028 person_2 doctor: "okay: weight 59 kilos, SpO2 98 percent on room air, temperature 36.7. And pressure 124 ove" | WRONG_NORM ('weight') | WRONG_NORM ('weight') |
| Oxygen saturation (value=98, unit="%", reported_by="doctor") | SEG0028 person_2 doctor: "okay: weight 59 kilos, SpO2 98 percent on room air, temperature 36.7. And pressure 124 ove" | WRONG_ATTRIB: reported_by: gold="doctor" pred="person_2" (speaker id written instead of role) | CORRECT |
| Body temperature (value=36.7, unit="°C", reported_by="doctor") | SEG0028 person_2 doctor: "okay: weight 59 kilos, SpO2 98 percent on room air, temperature 36.7. And pressure 124 ove" | WRONG_NORM ('temperature') | WRONG_NORM ('temperature') |
| Blood pressure (value="124/76", unit="mmHg", reported_by="doctor") | SEG0028 person_2 doctor: "okay: weight 59 kilos, SpO2 98 percent on room air, temperature 36.7. And pressure 124 ove" | WRONG_ATTRIB: reported_by: gold="doctor" pred="person_2" (speaker id written instead of role) | CORRECT |
| Body height (value=170, unit="cm", reported_by="doctor") | SEG0028 person_2 doctor: "okay: weight 59 kilos, SpO2 98 percent on room air, temperature 36.7. And pressure 124 ove" | WRONG_NORM ('height') | WRONG_NORM ('height') |
| Body mass index (value=20.4, unit="kg/m²", reported_by="doctor") | SEG0028 person_2 doctor: "okay: weight 59 kilos, SpO2 98 percent on room air, temperature 36.7. And pressure 124 ove" | MISSED | MISSED |
| Heart rate (value=73, unit="bpm", reported_by="doctor") | SEG0028 person_2 doctor: "okay: weight 59 kilos, SpO2 98 percent on room air, temperature 36.7. And pressure 124 ove" | WRONG_ATTRIB: reported_by: gold="doctor" pred="person_2" (speaker id written instead of role) | CORRECT |
| *(extra P00)* | bmi [UNSUPPORTED] | | |
| *(extra P01)* | bmi [UNSUPPORTED] | | |

**physical examination**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Left lower abdominal tenderness (status="present", observed_by="doctor") | SEG0031 person_2 doctor: "There's tenderness in the lower tummy on the left, and no guarding." | WRONG_NORM ('tenderness in the lower tummy on the left') | WRONG_NORM ('tenderness in the lower tummy on the left') |
| No guarding (status="absent", observed_by="doctor") | SEG0031 person_2 doctor: "There's tenderness in the lower tummy on the left, and no guarding." | MISSED | MISSED |

**review of systems**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| neurological (status="negative", reported_by="patient") | SEG0014 person_2 doctor: "Okay, so. Neurologically, anything strange?" | MISSED | MISSED |

**clinical conditions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | endometriosis [EXTRA_SUPPORTED_BY_TRANSCRIPT]; chronic pelvic pain [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |
| *(extra P01)* | endometriosis [EXTRA_SUPPORTED_BY_TRANSCRIPT]; chronic pelvic pain [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**clinical assessment**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Chronic pelvic pain, possibly endometriosis (certainty="provisional", stated_by="doctor") | SEG0035 person_2 doctor: "I can't promise yet, but most people with chronic pelvic pain, possibly endometriosis do w" | CORRECT | CORRECT |

**investigations/procedures**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Pelvic ultrasound (status="planned", type="imaging") | SEG0036 person_2 doctor: "I think a pelvic ultrasound makes sense here, for pelvic pain. Let's use mefenamic acid, 5" | CORRECT | PARTIAL: type: gold="imaging" pred="other" |

**clinical actions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| investigation/arrange pelvic ultrasound (status="planned", responsible_person="doctor") | SEG0036 person_2 doctor: "I think a pelvic ultrasound makes sense here, for pelvic pain. Let's use mefenamic acid, 5" | MISSED | MISSED |
| medication/start mefenamic acid 500 mg three times a day with food (status="planned", responsible_person="doctor") | SEG0036 person_2 doctor: "I think a pelvic ultrasound makes sense here, for pelvic pain. Let's use mefenamic acid, 5" | WRONG_NORM ('medication/take mefenamic acid 500 mg three times a day with food') | WRONG_NORM ('medication/mefenamic acid 500 mg three times a day with food') |
| counselling/advise heat pad and pain diary (status="recommended", responsible_person="patient") | SEG0038 person_2 doctor: "A heat pad and and some gentle movement help many people, and a pain diary helps me see a " | MISSED | MISSED |
| counselling/advise reducing caffeine intake (status="recommended", responsible_person="patient") | SEG0038 person_2 doctor: "A heat pad and and some gentle movement help many people, and a pain diary helps me see a " | MISSED | MISSED |
| referral/refer to gynaecology (status="planned", responsible_person="doctor") | SEG0039 person_2 doctor: "Mm-hm. I'd like you to see a gynaecologist as well, and I'll write the referral." | WRONG_NORM ('referral/see a gynaecologist') | WRONG_NORM ('referral/see a gynaecologist') |
| follow up/follow up consultation (status="planned", responsible_person="doctor") | SEG0041 person_2 doctor: "We'll catch up after the scan. Do you have any questions?" | MISSED | MISSED |
| *(extra P00)* | follow up/catch up after the scan [UNSUPPORTED]; counselling/use a heat pad and gentle movement [UNSUPPORTED] | | |
| *(extra P01)* | counselling/heat pad and gentle movement pain diary cut back on tea coffee and fizzy drinks [UNSUPPORTED] | | |

**follow up**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| consultation/after the scan (status="planned", time_reference="after the scan") | SEG0041 person_2 doctor: "We'll catch up after the scan. Do you have any questions?" | MISSED | MISSED |
| *(extra P00)* | consultation/ [UNSUPPORTED] | | |

**clinical uncertainties**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | conflicting statement [UNSUPPORTED] | | |

**Not applicable (no gold fact and no prediction):** past medical history, surgical history, family history, allergies.

**Evidence (L).**
- P00: 1 evidence records; 0 are an exact single transcript segment; 20 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_multi_segment_or_whole_transcript_dump': 1, 'ev_empty_supports': 1, 'fact_path_missing_from_supports': 20, 'fact_not_mentioned_in_cited_text': 2}.
- P01: 1 evidence records; 1 are an exact single transcript segment; 17 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_empty_supports': 1, 'fact_not_mentioned_in_cited_text': 13, 'fact_path_missing_from_supports': 13, 'fact_no_evidence_ids': 4}.

### Record 00077   (P00: parsed, P01: parsed)

**Speakers (A).** Transcript: person_1 patient, person_2 doctor, person_3 family_member, person_4 nurse. Gold primary speakers: person_1 patient, person_2 doctor, person_3 family_member, person_4 nurse.
- P00: predicted [('person_1', 'patient'), ('person_2', 'doctor'), ('person_3', 'family_member')]; all speakers+roles correct: False; missing [('person_4', 'nurse')]; wrong role none; invented ids none.
- P01: predicted [('person_1', 'patient'), ('person_2', 'doctor'), ('person_3', 'family_member'), ('person_4', 'nurse')]; all speakers+roles correct: True; missing none; wrong role none; invented ids none.

**Chief complaint (B).** Gold: 'acne along the jaw' / normalized 'Acne' (reported by family_member).
- P00: 'acne along the jaw' / normalized 'acne along the jaw' (reported_by person_3) -> WRONG_NORM ('acne along the jaw')
- P01: 'Acne along the jaw and thinning hair on the scalp' / normalized 'Acne along the jaw and thinning hair on the scalp' (reported_by person_3) -> MISSED

**symptoms**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Acne (status="present", temporality="current", certainty="uncertain") | SEG0003 person_3 family_member: "Hello, doctor. I hope it's alright if I stay in for this. Doctor, it's acne along the jaw." | WRONG_STATUS: certainty: gold="uncertain" pred="certain"; severity: gold="moderate" pred=null; duration: gold={"value": null, "unit": "weeks", "normal pred={"value" | WRONG_STATUS: certainty: gold="uncertain" pred="certain"; duration: gold={"value": null, "unit": "weeks", "normal pred={"value": "3-4 weeks", "unit": "weeks", ; rep |
| Scalp hair thinning (status="present", temporality="current", certainty="certain") | SEG0010 person_1 patient: "Moderate, really. Hmm, and there's thinning hair on the scalp as well, about four days now" | WRONG_NORM ('thinning hair') | WRONG_NORM ('thinning hair on the scalp') |
| Irregular menses (status="present", temporality="current", certainty="certain") | SEG0010 person_1 patient: "Moderate, really. Hmm, and there's thinning hair on the scalp as well, about four days now" | WRONG_NORM ('irregular periods') | WRONG_NORM ('irregular periods') |
| *(extra P00)* | moderate acne [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**negative findings**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Trying to conceive (temporality="current", reported_by="patient") | SEG0013 person_2 doctor: "Any trying for a baby, headaches with vision changes or pelvic pain at all?" | MISSED | MISSED |
| Visual symptoms with headache (temporality="current", reported_by="patient") | SEG0013 person_2 doctor: "Any trying for a baby, headaches with vision changes or pelvic pain at all?" | MISSED | MISSED |
| Pelvic pain (temporality="current", reported_by="patient") | SEG0013 person_2 doctor: "Any trying for a baby, headaches with vision changes or pelvic pain at all?" | MISSED | MISSED |
| Heavy bleeding (temporality="current", reported_by="patient") | SEG0015 person_2 doctor: "How about heavy bleeding?" | WRONG_NORM ('no heavy bleeding') | WRONG_NORM ('No heavy bleeding') |
| No previous surgery (temporality="past", reported_by="patient") | SEG0027 person_2 doctor: "So, have you had any previous surgeries?" | MISSED | MISSED |
| No known allergies (temporality="current", reported_by="patient") | SEG0032 person_2 doctor: "Any allergies I should know about?" | MISSED | MISSED |

**past medical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Anaemia (status="ongoing", reported_by="patient") | SEG0021 person_2 doctor: "Right, so low haemoglobin and high blood pressure are already on your record. We'll keep t" | MISSED | MISSED |
| Hypertension (status="ongoing", reported_by="patient") | SEG0021 person_2 doctor: "Right, so low haemoglobin and high blood pressure are already on your record. We'll keep t" | WRONG_NORM ('high blood pressure') | WRONG_NORM ('high blood pressure') |
| *(extra P00)* | low hemoglobin [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |
| *(extra P01)* | low hemoglobin [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**surgical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | no previous surgeries [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |
| *(extra P01)* | no previous surgeries [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**family history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Kidney stones (relation="father", reported_by="patient") | SEG0037 person_1 patient: "My father had kidney stones. So, you know, my mother had high blood pressure." | WRONG_ATTRIB: reported_by: gold="patient" pred="person_1" (speaker id written instead of role) | WRONG_ATTRIB: reported_by: gold="patient" pred="person_1" (speaker id written instead of role) |
| Hypertension (relation="mother", reported_by="patient") | SEG0037 person_1 patient: "My father had kidney stones. So, you know, my mother had high blood pressure." | WRONG_NORM ('high blood pressure') | WRONG_NORM ('high blood pressure') |

**social history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| occupation (status="current", reported_by="patient") | SEG0022 person_1 patient: "I drive a delivery van all day." | MISSED | MISSED |
| living (status="current", reported_by="patient") | SEG0024 person_1 patient: "I live with my family, my husband and two kids." | MISSED | MISSED |
| diet (status="current", reported_by="patient") | SEG0026 person_1 patient: "Mostly home-cooked food, rice and vegetables." | MISSED | MISSED |
| *(extra P00)* | work [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |
| *(extra P01)* | work [EXTRA_SUPPORTED_BY_TRANSCRIPT]; eating [UNSUPPORTED] | | |

**medications**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Iron tablets (frequency="once a day", status="currently_used", reported_by="family_member") | SEG0030 person_3 family_member: "It's iron tablets, once a day, doctor. Right, um, she takes ramipril, 5 milligrams, every " | WRONG_ATTRIB: frequency: gold="once a day" pred=null; reported_by: gold="family_member" pred="person_3" (speaker id written instead of role) | WRONG_ATTRIB: dose: not in gold, pred="once a day"; route: not in gold, pred="oral"; reported_by: gold="family_member" pred="person_3" (speaker id written instead o |
| Ramipril (dose="5 mg", frequency="every morning", status="currently_used") | SEG0030 person_3 family_member: "It's iron tablets, once a day, doctor. Right, um, she takes ramipril, 5 milligrams, every " | WRONG_ATTRIB: reported_by: gold="family_member" pred="person_3" (speaker id written instead of role) | WRONG_ATTRIB: route: not in gold, pred="oral"; reported_by: gold="family_member" pred="person_3" (speaker id written instead of role) |
| Amlodipine (status="discontinued", reported_by="patient") | SEG0031 person_1 patient: "Before this I was on amlodipine; that's been stopped." | WRONG_ATTRIB: reported_by: gold="patient" pred="person_1" (speaker id written instead of role) | WRONG_ATTRIB: dose: not in gold, pred="unknown"; route: not in gold, pred="oral"; frequency: not in gold, pred="unknown"; reported_by: gold="patient" pred="person_1 |

**allergies**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Aspirin (status="disputed", reported_by="family_member") | SEG0034 person_3 family_member: "Okay, so actually, I remember she had some kind of reaction to aspirin before. I couldn't " | WRONG_STATUS: status: gold="disputed" pred="historical"; reported_by: gold="family_member" pred="person_1" (speaker id written instead of role) | WRONG_STATUS: status: gold="disputed" pred="historical"; reported_by: gold="family_member" pred="person_3" (speaker id written instead of role) |

**vital signs**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Oxygen saturation (value=97, unit="%", reported_by="nurse") | SEG0038 person_4 nurse: "Here are the numbers, doctor. Oxygen saturation is 97 percent, temp 36.5 degrees, pulse 80" | WRONG_ATTRIB: reported_by: gold="nurse" pred="person_4" (speaker id written instead of role) | WRONG_ATTRIB: reported_by: gold="nurse" pred="person_4" (speaker id written instead of role) |
| Body temperature (value=36.5, unit="°C", reported_by="nurse") | SEG0038 person_4 nurse: "Here are the numbers, doctor. Oxygen saturation is 97 percent, temp 36.5 degrees, pulse 80" | MISSED | MISSED |
| Heart rate (value=80, unit="bpm", reported_by="nurse") | SEG0038 person_4 nurse: "Here are the numbers, doctor. Oxygen saturation is 97 percent, temp 36.5 degrees, pulse 80" | MISSED | MISSED |
| Blood pressure (value="127/80", unit="mmHg", reported_by="nurse") | SEG0038 person_4 nurse: "Here are the numbers, doctor. Oxygen saturation is 97 percent, temp 36.5 degrees, pulse 80" | WRONG_ATTRIB: reported_by: gold="nurse" pred="person_4" (speaker id written instead of role) | WRONG_ATTRIB: reported_by: gold="nurse" pred="person_4" (speaker id written instead of role) |
| *(extra P00)* | pulse [EXTRA_SUPPORTED_BY_TRANSCRIPT]; temperature [UNSUPPORTED] | | |
| *(extra P01)* | pulse [EXTRA_SUPPORTED_BY_TRANSCRIPT]; temperature [UNSUPPORTED] | | |

**physical examination**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Facial hirsutism (status="present", observed_by="doctor") | SEG0042 person_2 doctor: "Facial acne along the jaw and some dark coarse hair on the chin." | WRONG_NORM ('dark coarse hair on the chin') | WRONG_NORM ('facial acne along the jaw and some dark coarse hair on the chin') |
| *(extra P00)* | facial acne along the jaw [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**review of systems**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| respiratory (status="negative", reported_by="patient") | SEG0018 person_1 patient: "No, my breathing's been fine." | MISSED | MISSED |
| *(extra P00)* | gynecological [UNSUPPORTED] | | |
| *(extra P01)* | gynecological [UNSUPPORTED] | | |

**clinical conditions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Anaemia (status="existing", reported_by="patient") | SEG0021 person_2 doctor: "Right, so low haemoglobin and high blood pressure are already on your record. We'll keep t" | MISSED | MISSED |
| Hypertension (status="existing", reported_by="patient") | SEG0021 person_2 doctor: "Right, so low haemoglobin and high blood pressure are already on your record. We'll keep t" | MISSED | MISSED |
| *(extra P00)* | polycystic ovary syndrome [EXTRA_SUPPORTED_BY_TRANSCRIPT]; thyroid problem [INCORRECT - gold has this fact in category 'clinical assessment'] | | |
| *(extra P01)* | polycystic ovary syndrome [EXTRA_SUPPORTED_BY_TRANSCRIPT]; thyroid problem [INCORRECT - gold has this fact in category 'clinical assessment'] | | |

**clinical assessment**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Possible polycystic ovary syndrome (certainty="differential", stated_by="doctor") | SEG0044 person_2 doctor: "Right, here's what I'm thinking. I'm honestly not certain yet. It could be possible polycy" | WRONG_NORM ('possible polycystic ovary syndrome or thyroid problem') | WRONG_NORM ('possible polycystic ovary syndrome or thyroid problem') |
| Thyroid problem (certainty="differential", stated_by="doctor") | SEG0044 person_2 doctor: "Right, here's what I'm thinking. I'm honestly not certain yet. It could be possible polycy" | MISSED | MISSED |

**investigations/procedures**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Pelvic ultrasound (status="planned", type="imaging") | SEG0046 person_2 doctor: "I'll request a pelvic ultrasound, it'll help with irregular periods. I'm going to order a " | CORRECT | CORRECT |
| Thyroid function test (status="planned", type="laboratory") | SEG0046 person_2 doctor: "I'll request a pelvic ultrasound, it'll help with irregular periods. I'm going to order a " | WRONG_NORM ('thyroid test') | WRONG_NORM ('thyroid test') |

**clinical actions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| investigation/arrange pelvic ultrasound (status="planned", responsible_person="doctor") | SEG0046 person_2 doctor: "I'll request a pelvic ultrasound, it'll help with irregular periods. I'm going to order a " | MISSED | MISSED |
| investigation/arrange thyroid function test (status="planned", responsible_person="doctor") | SEG0046 person_2 doctor: "I'll request a pelvic ultrasound, it'll help with irregular periods. I'm going to order a " | MISSED | MISSED |
| counselling/lifestyle advice for pcos (status="recommended", responsible_person="patient") | SEG0046 person_2 doctor: "I'll request a pelvic ultrasound, it'll help with irregular periods. I'm going to order a " | MISSED | MISSED |
| follow up/follow up consultation (status="planned", responsible_person="doctor") | SEG0046 person_2 doctor: "I'll request a pelvic ultrasound, it'll help with irregular periods. I'm going to order a " | MISSED | MISSED |
| *(extra P00)* | follow up/see you again after the results are back [UNSUPPORTED] | | |
| *(extra P01)* | follow up/call the clinic if you need us [UNSUPPORTED] | | |

**follow up**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| consultation/after the results are back (status="planned", time_reference="after the results are ba) | SEG0046 person_2 doctor: "I'll request a pelvic ultrasound, it'll help with irregular periods. I'm going to order a " | MISSED | MISSED |
| *(extra P00)* | consultation/ [UNSUPPORTED] | | |
| *(extra P01)* | consultation/ [UNSUPPORTED] | | |

**clinical uncertainties**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| duration_disagreement (resolution_status="partially_resolved") | SEG0007 person_2 doctor: "Okay, so roughly three to four weeks. Is that right?" | MISSED | MISSED |
| allergy_disputed (resolution_status="unresolved") | SEG0034 person_3 family_member: "Okay, so actually, I remember she had some kind of reaction to aspirin before. I couldn't " | MISSED | MISSED |
| *(extra P00)* | conflicting statement [UNSUPPORTED]; conflicting statement [UNSUPPORTED]; conflicting statement [UNSUPPORTED] | | |
| *(extra P01)* | conflicting statement [UNSUPPORTED] | | |

**Not applicable (no gold fact and no prediction):** none.

**Evidence (L).**
- P00: 1 evidence records; 0 are an exact single transcript segment; 33 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_multi_segment_or_whole_transcript_dump': 1, 'ev_empty_supports': 1, 'fact_not_mentioned_in_cited_text': 20, 'fact_path_missing_from_supports': 33}.
- P01: 1 evidence records; 1 are an exact single transcript segment; 30 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_empty_supports': 1, 'fact_not_mentioned_in_cited_text': 24, 'fact_path_missing_from_supports': 29, 'fact_no_evidence_ids': 1}.

### Record 00092   (P00: parsed, P01: FAILED)

**Speakers (A).** Transcript: person_1 doctor, person_2 patient. Gold primary speakers: person_1 doctor, person_2 patient.
- P00: predicted [('person_1', 'doctor')]; all speakers+roles correct: False; missing [('person_2', 'patient')]; wrong role none; invented ids none.
- P01: no usable output.

**Chief complaint (B).** Gold: 'sweating' / normalized 'Sweating' (reported by patient).
- P00: 'Sweating' / normalized 'Sweating' (reported_by patient) -> CORRECT
- P01: no usable output.

**symptoms**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Sweating (status="present", temporality="current", certainty="certain") | SEG0004 person_2 patient: "I've been sweating, and I wanted to get it checked. It's a relief to finally sit down and " | MISSED | NO OUTPUT (record failed) |
| Headache (status="resolved", temporality="resolved", certainty="certain") | SEG0004 person_2 patient: "I've been sweating, and I wanted to get it checked. It's a relief to finally sit down and " | MISSED | NO OUTPUT (record failed) |
| Sweating (status="resolved", temporality="past", certainty="certain") | SEG0005 person_1 doctor: "Right, have you been sweating at any time before this?" | MISSED | NO OUTPUT (record failed) |

**negative findings**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Vomiting (temporality="current", reported_by="patient") | SEG0008 person_2 patient: "Um, uh, no vomiting, confusion or seizure, none of it." | MISSED | NO OUTPUT (record failed) |
| Confusion (temporality="current", reported_by="patient") | SEG0008 person_2 patient: "Um, uh, no vomiting, confusion or seizure, none of it." | MISSED | NO OUTPUT (record failed) |
| Seizure (temporality="current", reported_by="patient") | SEG0008 person_2 patient: "Um, uh, no vomiting, confusion or seizure, none of it." | MISSED | NO OUTPUT (record failed) |
| Weight loss (temporality="current", reported_by="patient") | SEG0009 person_1 doctor: "A few quick ones: weight loss or chest pain?" | MISSED | NO OUTPUT (record failed) |
| Chest pain (temporality="current", reported_by="patient") | SEG0009 person_1 doctor: "A few quick ones: weight loss or chest pain?" | MISSED | NO OUTPUT (record failed) |
| No previous surgery (temporality="past", reported_by="patient") | SEG0022 person_1 doctor: "Have you had any previous surgeries?" | MISSED | NO OUTPUT (record failed) |
| No known allergies (temporality="current", reported_by="patient") | SEG0032 person_1 doctor: "Any allergies I should know about?" | MISSED | NO OUTPUT (record failed) |

**past medical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Type 2 diabetes mellitus (status="ongoing", reported_by="patient") | SEG0020 person_2 patient: "I've, I've had diabetes, yes." | WRONG_NORM ('diabetes') | NO OUTPUT (record failed) |

**surgical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | no operations [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**social history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| alcohol (status="current", reported_by="patient") | SEG0024 person_1 doctor: "Do you drink alcohol?" | MISSED | NO OUTPUT (record failed) |
| smoking (status="never", reported_by="patient") | SEG0027 person_2 patient: "I've never smoked." | MISSED | NO OUTPUT (record failed) |
| exercise (status="current", reported_by="patient") | SEG0028 person_1 doctor: "Do you get any exercise?" | MISSED | NO OUTPUT (record failed) |
| diet (status="current", reported_by="patient") | SEG0031 person_2 patient: "I skip breakfast most days." | MISSED | NO OUTPUT (record failed) |

**medications**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Metformin (dose="500 mg", frequency="twice a day", status="currently_used") | SEG0016 person_2 patient: "I take something called glyc... Glycomet, 500 milligrams, maybe, twice a day." | WRONG_NORM ('glycomet') | NO OUTPUT (record failed) |

**vital signs**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Oxygen saturation (value=99, unit="%", reported_by="doctor") | SEG0036 person_1 doctor: "Okay: oxygen saturation is 99 percent, pulse is 82 beats a minute, height 150 centimetres," | MISSED | NO OUTPUT (record failed) |
| Heart rate (value=82, unit="bpm", reported_by="doctor") | SEG0036 person_1 doctor: "Okay: oxygen saturation is 99 percent, pulse is 82 beats a minute, height 150 centimetres," | MISSED | NO OUTPUT (record failed) |
| Body height (value=150, unit="cm", reported_by="doctor") | SEG0036 person_1 doctor: "Okay: oxygen saturation is 99 percent, pulse is 82 beats a minute, height 150 centimetres," | MISSED | NO OUTPUT (record failed) |
| Blood pressure (value="122/73", unit="mmHg", reported_by="doctor") | SEG0036 person_1 doctor: "Okay: oxygen saturation is 99 percent, pulse is 82 beats a minute, height 150 centimetres," | MISSED | NO OUTPUT (record failed) |
| Body temperature (value=36.9, unit="°C", reported_by="doctor") | SEG0036 person_1 doctor: "Okay: oxygen saturation is 99 percent, pulse is 82 beats a minute, height 150 centimetres," | MISSED | NO OUTPUT (record failed) |
| Body mass index (value=32.9, unit="kg/m²", reported_by="doctor") | SEG0036 person_1 doctor: "Okay: oxygen saturation is 99 percent, pulse is 82 beats a minute, height 150 centimetres," | MISSED | NO OUTPUT (record failed) |
| Body weight (value=74, unit="kg", reported_by="doctor") | SEG0036 person_1 doctor: "Okay: oxygen saturation is 99 percent, pulse is 82 beats a minute, height 150 centimetres," | MISSED | NO OUTPUT (record failed) |

**physical examination**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| No tremor (status="absent", observed_by="doctor") | SEG0041 person_1 doctor: "Pulse is normal and there's no tremor right now." | MISSED | NO OUTPUT (record failed) |

**review of systems**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| musculoskeletal (status="negative", reported_by="patient") | SEG0012 person_2 patient: "No, joints are fine." | MISSED | NO OUTPUT (record failed) |
| gastrointestinal (status="negative", reported_by="patient") | SEG0014 person_2 patient: "No, that side's been fine." | MISSED | NO OUTPUT (record failed) |

**clinical conditions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Type 2 diabetes mellitus (status="existing", reported_by="patient") | SEG0020 person_2 patient: "I've, I've had diabetes, yes." | MISSED | NO OUTPUT (record failed) |
| *(extra P00)* | low sugar episodes [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**clinical assessment**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Low sugar episodes related to diabetes medication (certainty="provisional", stated_by="doctor") | SEG0043 person_1 doctor: "So, thanks for that. Right, here's what I'm thinking. The most likely explanation is low s" | CORRECT | NO OUTPUT (record failed) |

**investigations/procedures**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Fasting blood glucose (status="planned", type="laboratory") | SEG0045 person_1 doctor: "Nothing I've seen today points to an emergency. It looks like low sugar episodes related t" | WRONG_NORM ('hba1c test') | NO OUTPUT (record failed) |
| HbA1c (status="planned", type="laboratory") | SEG0045 person_1 doctor: "Nothing I've seen today points to an emergency. It looks like low sugar episodes related t" | MISSED | NO OUTPUT (record failed) |
| *(extra P00)* | blood sugar test [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**clinical actions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| investigation/arrange fasting blood glucose (status="planned", responsible_person="doctor") | SEG0045 person_1 doctor: "Nothing I've seen today points to an emergency. It looks like low sugar episodes related t" | MISSED | NO OUTPUT (record failed) |
| investigation/arrange hba1c (status="planned", responsible_person="doctor") | SEG0045 person_1 doctor: "Nothing I've seen today points to an emergency. It looks like low sugar episodes related t" | MISSED | NO OUTPUT (record failed) |
| counselling/advise carrying fast acting sugar and regular meals (status="recommended", responsible_person="patient") | SEG0045 person_1 doctor: "Nothing I've seen today points to an emergency. It looks like low sugar episodes related t" | MISSED | NO OUTPUT (record failed) |
| other/bring latest prescription or medication box to next visit (status="recommended", responsible_person="patient") | SEG0046 person_1 doctor: "And please bring the latest prescription or the medicine boxes to the next visit, so we ca" | MISSED | NO OUTPUT (record failed) |
| counselling/seek urgent care if you black out or can t wake up properly after an episode (status="recommended", responsible_person="patient") | SEG0048 person_1 doctor: "One warning sign to remember: you black out or can't wake up properly after an episode. In" | MISSED | NO OUTPUT (record failed) |
| follow up/follow up consultation (status="planned", responsible_person="doctor") | SEG0050 person_1 doctor: "Let's review you after the results are back. Alright, take care, and call us if anything c" | MISSED | NO OUTPUT (record failed) |
| *(extra P00)* | investigation/request blood sugar test [UNSUPPORTED]; investigation/request hba1c test [UNSUPPORTED] | | |

**follow up**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| consultation/after the results are back (status="planned", time_reference="after the results are ba) | SEG0050 person_1 doctor: "Let's review you after the results are back. Alright, take care, and call us if anything c" | MISSED | NO OUTPUT (record failed) |
| *(extra P00)* | consultation/ [UNSUPPORTED] | | |

**clinical uncertainties**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| uncertain_dose (resolution_status="unresolved") | SEG0016 person_2 patient: "I take something called glyc... Glycomet, 500 milligrams, maybe, twice a day." | MISSED | NO OUTPUT (record failed) |
| *(extra P00)* | conflicting statement [UNSUPPORTED] | | |

**Not applicable (no gold fact and no prediction):** family history, allergies.

**Evidence (L).**
- P00: 1 evidence records; 0 are an exact single transcript segment; 12 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_near_copy_not_exact': 1, 'ev_empty_supports': 1, 'fact_not_mentioned_in_cited_text': 11, 'fact_path_missing_from_supports': 12}.
- P01: no usable output.

### Record 00120   (P00: parsed, P01: parsed)

**Speakers (A).** Transcript: person_1 doctor, person_2 patient. Gold primary speakers: person_1 doctor, person_2 patient.
- P00: predicted [('person_1', 'doctor')]; all speakers+roles correct: False; missing [('person_2', 'patient')]; wrong role none; invented ids none.
- P01: predicted [('person_1', 'doctor')]; all speakers+roles correct: False; missing [('person_2', 'patient')]; wrong role none; invented ids none.

**Chief complaint (B).** Gold: 'gritty tired eyes' / normalized 'Gritty eyes' (reported by patient).
- P00: 'gritty tired eyes' / normalized 'gritty tired eyes' (reported_by patient) -> WRONG_NORM ('gritty tired eyes')
- P01: 'gritty tired eyes' / normalized 'gritty tired eyes' (reported_by patient) -> WRONG_NORM ('gritty tired eyes')

**symptoms**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Gritty eyes (status="present", temporality="current", certainty="certain") | SEG0004 person_2 patient: "I wanted to get gritty tired eyes looked at." | MISSED | MISSED |
| Eye burning (status="present", temporality="current", certainty="certain") | SEG0010 person_2 patient: "Burning at the end of the day goes along with it, most of the time. The Burning at the end" | WRONG_NORM ('burning at the end of the day') | MISSED |
| Reflex tearing (status="present", temporality="current", certainty="certain") | SEG0010 person_2 patient: "Burning at the end of the day goes along with it, most of the time. The Burning at the end" | WRONG_NORM ('watery eyes in the wind') | MISSED |
| *(extra P01)* | dry eye [INCORRECT - gold has this fact in category 'clinical assessment'] | | |

**negative findings**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Eye pain (temporality="current", reported_by="patient") | SEG0015 person_1 doctor: "Any eye pain, loss of vision or sensitivity to light at all?" | WRONG_NORM ('no eye pain loss of vision or sensitivity to light') | WRONG_NORM ('no eye pain loss of vision or sensitivity to light') |
| Visual loss (temporality="current", reported_by="patient") | SEG0015 person_1 doctor: "Any eye pain, loss of vision or sensitivity to light at all?" | MISSED | MISSED |
| Photophobia (temporality="current", reported_by="patient") | SEG0015 person_1 doctor: "Any eye pain, loss of vision or sensitivity to light at all?" | MISSED | MISSED |
| Eye discharge (temporality="current", reported_by="patient") | SEG0017 person_1 doctor: "Have you noticed discharge, double vision or dry mouth?" | MISSED | MISSED |
| Diplopia (temporality="current", reported_by="patient") | SEG0017 person_1 doctor: "Have you noticed discharge, double vision or dry mouth?" | MISSED | MISSED |
| Dry mouth (temporality="current", reported_by="patient") | SEG0017 person_1 doctor: "Have you noticed discharge, double vision or dry mouth?" | MISSED | MISSED |
| No known allergies (temporality="current", reported_by="patient") | SEG0038 person_2 patient: "I don't have any known medication allergies." | MISSED | MISSED |

**past medical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Migraine (status="ongoing", reported_by="patient") | SEG0030 person_2 patient: "I've had migraines, yes. I've had heart disease, yes." | WRONG_NORM ('migraines') | WRONG_NORM ('migraines') |
| Ischaemic heart disease (status="ongoing", reported_by="patient") | SEG0030 person_2 patient: "I've had migraines, yes. I've had heart disease, yes." | WRONG_NORM ('heart disease') | WRONG_NORM ('heart disease') |
| Atrial fibrillation (status="ongoing", reported_by="patient") | SEG0032 person_2 patient: "Yes, an irregular heartbeat." | MISSED | MISSED |

**surgical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Thyroid surgery (reported_by="patient") | SEG0028 person_2 patient: "just my thyroid operated on, a long time ago" | WRONG_NORM ('thyroid operation') | WRONG_NORM ('thyroid operation') |

**family history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P01)* | unknown [UNSUPPORTED] | | |

**social history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| occupation (status="current", reported_by="patient") | SEG0024 person_2 patient: "I teach at a primary school" | MISSED | WRONG_STATUS: status: gold="current" pred="unknown" |
| living (status="current", reported_by="patient") | SEG0026 person_2 patient: "I live with my family, my husband and two kids." | MISSED | MISSED |

**medications**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Sumatriptan (dose="50 mg", frequency="when needed", status="currently_used") | SEG0034 person_2 patient: "It's sumatriptan, 50 milligrams, maybe, when needed for my migraines." | PARTIAL: frequency: gold="when needed" pred=null | UNSUPPORTED: route: not in gold, pred="oral" |
| Clopidogrel (dose="75 mg", frequency="once a day", status="currently_used") | SEG0036 person_2 patient: "No, it's at home. I'm on clopidogrel, 75 milligrams, once a day for the stent. Apixaban. I" | UNSUPPORTED: route: not in gold, pred="oral" | UNSUPPORTED: route: not in gold, pred="oral" |
| Apixaban (dose="5 mg", frequency="twice a day", status="currently_used") | SEG0036 person_2 patient: "No, it's at home. I'm on clopidogrel, 75 milligrams, once a day for the stent. Apixaban. I" | UNSUPPORTED: route: not in gold, pred="oral" | UNSUPPORTED: route: not in gold, pred="oral" |
| Carboxymethylcellulose (frequency="four times a day", status="planned", reported_by="doctor") | SEG0042 person_1 doctor: "An eye check is what I'd like next, for gritty eyes what I'm giving you is lubricating eye" | MISSED | MISSED |

**allergies**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | unknown [INCORRECT - placeholder written as an allergy entry (gold has no allergy)] | | |
| *(extra P01)* | unknown [INCORRECT - placeholder written as an allergy entry (gold has no allergy)] | | |

**physical examination**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Clear corneas (status="present", observed_by="doctor") | SEG0013 person_1 doctor: "the eyes look a a little pink but the corneas are clear" | MISSED | MISSED |
| *(extra P00)* | little pressure here [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |
| *(extra P01)* | little pressure here [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**review of systems**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| musculoskeletal (status="negative", reported_by="patient") | SEG0020 person_2 patient: "No, nothing there." | MISSED | MISSED |
| skin (status="negative", reported_by="patient") | SEG0022 person_2 patient: "Skin's normal." | MISSED | MISSED |
| *(extra P00)* | eyes [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |
| *(extra P01)* | ocular [UNSUPPORTED] | | |

**clinical conditions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Atrial fibrillation (status="existing", reported_by="patient") | SEG0032 person_2 patient: "Yes, an irregular heartbeat." | MISSED | MISSED |
| *(extra P00)* | dry eye [INCORRECT - gold has this fact in category 'clinical assessment'] | | |
| *(extra P01)* | dry eye [INCORRECT - gold has this fact in category 'clinical assessment'] | | |

**clinical assessment**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Dry eye (certainty="differential", stated_by="doctor") | SEG0041 person_1 doctor: "Nothing I've seen today points to an emergency. It looks like dry eye, but I'd like to con" | MISSED | MISSED |
| Digital eye strain (certainty="differential", stated_by="doctor") | SEG0039 person_1 doctor: "Okay, so my impression is this: I'm honestly not certain yet. It could be dry eye, or it m" | WRONG_NORM ('i m honestly not certain yet it could be dry eye or it might be digital eye strain') | WRONG_NORM ('i m honestly not certain yet it could be dry eye or it might be digital eye strain') |

**investigations/procedures**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Eye examination (status="planned", type="other") | SEG0042 person_1 doctor: "An eye check is what I'd like next, for gritty eyes what I'm giving you is lubricating eye" | MISSED | MISSED |
| *(extra P00)* | lubricating eye drops [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |
| *(extra P01)* | lubricating eye drops [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**clinical actions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| investigation/arrange eye examination (status="planned", responsible_person="doctor") | SEG0042 person_1 doctor: "An eye check is what I'd like next, for gritty eyes what I'm giving you is lubricating eye" | MISSED | MISSED |
| medication/start carboxymethylcellulose four times a day (status="planned", responsible_person="doctor") | SEG0042 person_1 doctor: "An eye check is what I'd like next, for gritty eyes what I'm giving you is lubricating eye" | MISSED | MISSED |
| counselling/20 20 20 screen break rule (status="recommended", responsible_person="patient") | SEG0044 person_1 doctor: "Look away from the screen every twenty minutes and blink fully. And please bring the lates" | MISSED | MISSED |
| other/bring latest prescription or medication box to next visit (status="recommended", responsible_person="patient") | SEG0044 person_1 doctor: "Look away from the screen every twenty minutes and blink fully. And please bring the lates" | MISSED | MISSED |
| follow up/follow up consultation (status="planned", responsible_person="doctor") | SEG0044 person_1 doctor: "Look away from the screen every twenty minutes and blink fully. And please bring the lates" | MISSED | MISSED |
| *(extra P00)* | follow up/see me again in four weeks [UNSUPPORTED] | | |
| *(extra P01)* | follow up/see me again in four weeks [UNSUPPORTED] | | |

**follow up**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| consultation/in four weeks (status="planned", time_reference="in four weeks") | SEG0044 person_1 doctor: "Look away from the screen every twenty minutes and blink fully. And please bring the lates" | WRONG_NORM ('consultation/four weeks') | WRONG_NORM ('consultation/four weeks') |

**clinical uncertainties**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| uncertain_dose (resolution_status="unresolved") | SEG0034 person_2 patient: "It's sumatriptan, 50 milligrams, maybe, when needed for my migraines." | MISSED | MISSED |
| adherence_uncertain (resolution_status="unresolved") | SEG0036 person_2 patient: "No, it's at home. I'm on clopidogrel, 75 milligrams, once a day for the stent. Apixaban. I" | MISSED | MISSED |
| *(extra P00)* | date uncertain [UNSUPPORTED] | | |
| *(extra P01)* | date uncertain [UNSUPPORTED] | | |

**Not applicable (no gold fact and no prediction):** vital signs.

**Evidence (L).**
- P00: 1 evidence records; 0 are an exact single transcript segment; 19 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_multi_segment_or_whole_transcript_dump': 1, 'ev_empty_supports': 1, 'fact_path_missing_from_supports': 19, 'fact_not_mentioned_in_cited_text': 13}.
- P01: 1 evidence records; 0 are an exact single transcript segment; 20 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_multi_segment_or_whole_transcript_dump': 1, 'ev_empty_supports': 1, 'fact_path_missing_from_supports': 19, 'fact_not_mentioned_in_cited_text': 5, 'fact_no_evidence_ids': 1}.

### Record 00127   (P00: FAILED, P01: parsed)

**Speakers (A).** Transcript: person_1 patient, person_2 doctor, person_3 caregiver, person_4 unknown. Gold primary speakers: person_1 patient, person_2 doctor, person_3 caregiver, person_4 unknown.
- P00: no usable output.
- P01: predicted [('person_1', 'patient'), ('person_2', 'doctor'), ('person_3', 'caregiver')]; all speakers+roles correct: False; missing [('person_4', 'unknown')]; wrong role none; invented ids none.

**Chief complaint (B).** Gold: 'trouble sleeping' / normalized 'Insomnia' (reported by caregiver).
- P00: no usable output.
- P01: 'Trouble sleeping' / normalized 'Trouble sleeping' (reported_by person_1) -> WRONG_NORM ('trouble sleeping')

**symptoms**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Insomnia (status="present", temporality="current", certainty="certain") | SEG0047 person_2 doctor: "I understand the worry. At the moment I'd say it's insomnia, probably stress-related, and " | NO OUTPUT (record failed) | WRONG_ATTRIB: severity: gold="severe" pred=null; duration: gold={"value": 2, "unit": "months", "normaliz pred={"value": null, "unit": null, "normalize; reported_by: |
| Daytime fatigue (status="present", temporality="current", certainty="certain") | SEG0013 person_2 doctor: "Have you been feeling exhausted in the day?" | NO OUTPUT (record failed) | MISSED |
| Poor concentration (status="present", temporality="current", certainty="certain") | SEG0016 person_1 patient: "I've also had trouble concentrating. As for trouble concentrating, it feels severe to me." | NO OUTPUT (record failed) | MISSED |
| Early morning waking (status="resolved", temporality="resolved", certainty="certain") | SEG0019 person_1 patient: "No, no low mood, no chest pain. I was waking up at three in the morning at one point, but " | NO OUTPUT (record failed) | MISSED |

**negative findings**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Low mood (temporality="current", reported_by="patient") | SEG0018 person_2 doctor: "Any low mood or chest pain at all?" | NO OUTPUT (record failed) | MISSED |
| Chest pain (temporality="current", reported_by="patient") | SEG0018 person_2 doctor: "Any low mood or chest pain at all?" | NO OUTPUT (record failed) | MISSED |
| Restless legs (temporality="current", reported_by="patient") | SEG0020 person_2 doctor: "And what about restless legs, snoring or heavy caffeine?" | NO OUTPUT (record failed) | MISSED |
| Snoring (temporality="current", reported_by="patient") | SEG0020 person_2 doctor: "And what about restless legs, snoring or heavy caffeine?" | NO OUTPUT (record failed) | MISSED |
| High caffeine intake (temporality="current", reported_by="patient") | SEG0020 person_2 doctor: "And what about restless legs, snoring or heavy caffeine?" | NO OUTPUT (record failed) | MISSED |
| *(extra P01)* | no fever [UNSUPPORTED]; no allergies [EXTRA_SUPPORTED_BY_TRANSCRIPT]; no previous surgery [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**past medical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Anxiety disorder (status="ongoing", reported_by="patient") | SEG0033 person_1 patient: "I've had anxiety for five years now." | NO OUTPUT (record failed) | WRONG_NORM ('anxiety') |
| Hypertension (status="ongoing", reported_by="patient") | SEG0035 person_1 patient: "I have high blood pressure, for two years. I thought it would sort itself out, but it hasn" | NO OUTPUT (record failed) | WRONG_NORM ('high blood pressure') |

**surgical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Thyroid surgery (reported_by="patient") | SEG0031 person_1 patient: "I had my thyroid operated on a long time ago." | NO OUTPUT (record failed) | WRONG_NORM ('thyroid operation') |

**family history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Diabetes mellitus (relation="father", reported_by="patient") | SEG0029 person_1 patient: "My father was diabetic." | NO OUTPUT (record failed) | WRONG_NORM ('diabetes') |

**social history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| diet (status="current", reported_by="patient") | SEG0037 person_2 doctor: "What's your diet like?" | NO OUTPUT (record failed) | WRONG_STATUS: status: gold="current" pred=""; reported_by: gold="patient" pred="person_1" (speaker id written instead of role) |

**medications**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Escitalopram (dose="10 mg", frequency="once a day", status="currently_used") | SEG0025 person_1 patient: "I'm on escitalopram, 10 milligrams, once a day. Telmisartan, 40 milligrams, once a day. I " | NO OUTPUT (record failed) | WRONG_ATTRIB: route: not in gold, pred="oral"; reported_by: gold="patient" pred="person_1" (speaker id written instead of role) |
| Telmisartan (dose="40 mg", frequency="once a day", status="currently_used") | SEG0025 person_1 patient: "I'm on escitalopram, 10 milligrams, once a day. Telmisartan, 40 milligrams, once a day. I " | NO OUTPUT (record failed) | WRONG_ATTRIB: route: not in gold, pred="oral"; reported_by: gold="patient" pred="person_1" (speaker id written instead of role) |
| Melatonin (dose="3 mg", frequency="at night", status="currently_used") | SEG0025 person_1 patient: "I'm on escitalopram, 10 milligrams, once a day. Telmisartan, 40 milligrams, once a day. I " | NO OUTPUT (record failed) | WRONG_ATTRIB: route: not in gold, pred="oral"; reported_by: gold="patient" pred="person_1" (speaker id written instead of role) |

**allergies**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Antibiotic (unspecified) (status="uncertain", reported_by="patient") | SEG0040 person_1 patient: "I think I reacted to some antibiotic once, years ago. I don't remember which one, or what " | NO OUTPUT (record failed) | WRONG_NORM ('antibiotic') |

**vital signs**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Respiratory rate (value=17, unit="breaths/min", reported_by="doctor") | SEG0043 person_2 doctor: "Okay: respiratory rate 17, BP is 114 over 69, oxygen saturation is 97 percent, pulse is 82" | NO OUTPUT (record failed) | MISSED |
| Blood pressure (value="114/69", unit="mmHg", reported_by="doctor") | SEG0043 person_2 doctor: "Okay: respiratory rate 17, BP is 114 over 69, oxygen saturation is 97 percent, pulse is 82" | NO OUTPUT (record failed) | WRONG_ATTRIB: reported_by: gold="doctor" pred="person_1" (speaker id written instead of role) |
| Oxygen saturation (value=97, unit="%", reported_by="doctor") | SEG0043 person_2 doctor: "Okay: respiratory rate 17, BP is 114 over 69, oxygen saturation is 97 percent, pulse is 82" | NO OUTPUT (record failed) | WRONG_ATTRIB: reported_by: gold="doctor" pred="person_1" (speaker id written instead of role) |
| Heart rate (value=82, unit="bpm", reported_by="doctor") | SEG0043 person_2 doctor: "Okay: respiratory rate 17, BP is 114 over 69, oxygen saturation is 97 percent, pulse is 82" | NO OUTPUT (record failed) | WRONG_ATTRIB: reported_by: gold="doctor" pred="person_1" (speaker id written instead of role) |
| Body temperature (value=36.8, unit="°C", reported_by="doctor") | SEG0043 person_2 doctor: "Okay: respiratory rate 17, BP is 114 over 69, oxygen saturation is 97 percent, pulse is 82" | NO OUTPUT (record failed) | WRONG_NORM ('temperature') |

**physical examination**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P01)* | no abnormal findings [UNSUPPORTED] | | |

**review of systems**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| cardiovascular (status="negative", reported_by="patient") | SEG0022 person_2 doctor: "Has your heart given you any trouble?" | NO OUTPUT (record failed) | MISSED |
| *(extra P01)* | neurological [UNSUPPORTED] | | |

**clinical conditions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Anxiety disorder (status="existing", reported_by="patient") | SEG0033 person_1 patient: "I've had anxiety for five years now." | NO OUTPUT (record failed) | MISSED |
| *(extra P01)* | insomnia [INCORRECT - gold has this fact in category 'chief complaint'] | | |

**clinical assessment**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Insomnia, probably stress-related (certainty="provisional", stated_by="doctor") | SEG0045 person_2 doctor: "Don't worry, I'll go through it in a moment. So, based on your history, this looks most li" | NO OUTPUT (record failed) | CORRECT |
| Thyroid problem (certainty="differential", stated_by="doctor") | SEG0045 person_2 doctor: "Don't worry, I'll go through it in a moment. So, based on your history, this looks most li" | NO OUTPUT (record failed) | MISSED |

**investigations/procedures**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Sleep study (status="planned", type="other") | SEG0049 person_2 doctor: "Let's get a sleep study, for insomnia. Let's book a thyroid test to look into insomnia. Sa" | NO OUTPUT (record failed) | CORRECT |
| Thyroid function test (status="planned", type="laboratory") | SEG0049 person_2 doctor: "Let's get a sleep study, for insomnia. Let's book a thyroid test to look into insomnia. Sa" | NO OUTPUT (record failed) | WRONG_NORM ('thyroid test') |

**clinical actions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| investigation/arrange sleep study (status="planned", responsible_person="doctor") | SEG0049 person_2 doctor: "Let's get a sleep study, for insomnia. Let's book a thyroid test to look into insomnia. Sa" | NO OUTPUT (record failed) | MISSED |
| investigation/arrange thyroid function test (status="planned", responsible_person="doctor") | SEG0049 person_2 doctor: "Let's get a sleep study, for insomnia. Let's book a thyroid test to look into insomnia. Sa" | NO OUTPUT (record failed) | MISSED |
| counselling/advise sleep hygiene measures (status="recommended", responsible_person="patient") | SEG0049 person_2 doctor: "Let's get a sleep study, for insomnia. Let's book a thyroid test to look into insomnia. Sa" | NO OUTPUT (record failed) | MISSED |
| other/bring latest prescription or medication box to next visit (status="recommended", responsible_person="patient") | SEG0049 person_2 doctor: "Let's get a sleep study, for insomnia. Let's book a thyroid test to look into insomnia. Sa" | NO OUTPUT (record failed) | MISSED |
| follow up/follow up consultation (status="planned", responsible_person="doctor") | SEG0049 person_2 doctor: "Let's get a sleep study, for insomnia. Let's book a thyroid test to look into insomnia. Sa" | NO OUTPUT (record failed) | MISSED |
| *(extra P01)* | follow up/book a sleep study and thyroid test [UNSUPPORTED] | | |

**follow up**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| consultation/in four weeks (status="planned", time_reference="in four weeks") | SEG0049 person_2 doctor: "Let's get a sleep study, for insomnia. Let's book a thyroid test to look into insomnia. Sa" | NO OUTPUT (record failed) | MISSED |
| *(extra P01)* | consultation/4 weeks [UNSUPPORTED] | | |

**clinical uncertainties**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| unknown_speaker (resolution_status="unresolved") | SEG0017 person_4 unknown: "Yes, that's right, that's how it was." | NO OUTPUT (record failed) | MISSED |
| uncertain_dose (resolution_status="unresolved") | SEG0025 person_1 patient: "I'm on escitalopram, 10 milligrams, once a day. Telmisartan, 40 milligrams, once a day. I " | NO OUTPUT (record failed) | MISSED |
| allergy_uncertain (resolution_status="unresolved") | SEG0040 person_1 patient: "I think I reacted to some antibiotic once, years ago. I don't remember which one, or what " | NO OUTPUT (record failed) | MISSED |
| *(extra P01)* | date uncertain [UNSUPPORTED] | | |

**Not applicable (no gold fact and no prediction):** none.

**Evidence (L).**
- P00: no usable output.
- P01: 3 evidence records; 0 are an exact single transcript segment; 27 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_text_not_in_transcript': 3, 'ev_empty_supports': 3, 'fact_path_missing_from_supports': 14, 'fact_no_evidence_ids': 13, 'fact_not_mentioned_in_cited_text': 11}.

### Record 00141   (P00: parsed, P01: parsed)

**Speakers (A).** Transcript: person_1 doctor, person_2 patient, person_3 family_member, person_4 nurse. Gold primary speakers: person_1 doctor, person_2 patient, person_3 family_member, person_4 nurse.
- P00: predicted [('person_1', 'doctor')]; all speakers+roles correct: False; missing [('person_2', 'patient'), ('person_3', 'family_member'), ('person_4', 'nurse')]; wrong role none; invented ids none.
- P01: predicted [('person_1', 'doctor'), ('person_2', 'patient'), ('person_3', 'family_member')]; all speakers+roles correct: False; missing [('person_4', 'nurse')]; wrong role none; invented ids none.

**Chief complaint (B).** Gold: 'fever' / normalized 'Fever' (reported by patient).
- P00: 'fever' / normalized 'fever' (reported_by patient) -> CORRECT
- P01: 'fever' / normalized 'fever' (reported_by patient) -> CORRECT

**symptoms**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Fever (status="present", temporality="current", certainty="certain") | SEG0007 person_2 patient: "um, so... a fever. That's why I came" | WRONG_STATUS: temporality: gold="current" pred="past"; severity: gold="moderate" pred=null; frequency: gold="a few times a day" pred=null | WRONG_STATUS: temporality: gold="current" pred="past"; severity: gold="moderate" pred=null; frequency: gold="a few times a day" pred=null |
| Non-healing wound (status="present", temporality="current", certainty="certain") | SEG0013 person_2 patient: "A small cut that wasn't healing goes along with it, most of the time" | MISSED | MISSED |
| Leg redness and swelling (status="present", temporality="current", certainty="certain") | SEG0017 person_1 doctor: "what about a red swollen area on your leg, have you noticed that?" | MISSED | MISSED |
| Vomiting (status="present", temporality="current", certainty="disputed") | SEG0021 person_3 family_member: "Well, actually, doctor, I did notice vomiting. She doesn't always say." | MISSED | MISSED |
| Local pain (status="resolved", temporality="resolved", certainty="certain") | SEG0024 person_2 patient: "no, um, no red streaks going up the leg, no calf pain, no numbness around it i did have pa" | MISSED | MISSED |

**negative findings**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Vomiting (temporality="current", reported_by="patient") | SEG0019 person_1 doctor: "How about vomiting?" | MISSED | MISSED |
| Red streaks (temporality="current", reported_by="patient") | SEG0024 person_2 patient: "no, um, no red streaks going up the leg, no calf pain, no numbness around it i did have pa" | MISSED | MISSED |
| Calf pain (temporality="current", reported_by="patient") | SEG0024 person_2 patient: "no, um, no red streaks going up the leg, no calf pain, no numbness around it i did have pa" | MISSED | MISSED |
| Numbness (temporality="current", reported_by="patient") | SEG0024 person_2 patient: "no, um, no red streaks going up the leg, no calf pain, no numbness around it i did have pa" | MISSED | MISSED |
| Shortness of breath (temporality="current", reported_by="patient") | SEG0026 person_2 patient: "Um, no, no shortness of breath or pus." | MISSED | MISSED |
| Pus (temporality="current", reported_by="patient") | SEG0026 person_2 patient: "Um, no, no shortness of breath or pus." | MISSED | MISSED |
| *(extra P00)* | no fever [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |
| *(extra P01)* | no fever [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**past medical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Type 2 diabetes mellitus (status="ongoing", reported_by="patient") | SEG0032 person_2 patient: "uh, I've had diabetes for nearly five years now" | WRONG_NORM ('diabetes') | WRONG_NORM ('diabetes') |
| Eczema (status="ongoing", reported_by="patient") | SEG0034 person_2 patient: "I have eczema." | MISSED | CORRECT |

**surgical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Hernia repair (reported_by="patient") | SEG0044 person_2 patient: "Yes, I had a hernia repair, about five years back." | CORRECT | CORRECT |

**family history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Breast cancer (relation="grandmother", reported_by="patient") | SEG0036 person_2 patient: "My grandmother had breast cancer." | CORRECT | CORRECT |

**social history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| exercise (status="current", reported_by="patient") | SEG0045 person_1 doctor: "Do you exercise at all?" | MISSED | MISSED |
| occupation (status="current", reported_by="patient") | SEG0048 person_2 patient: "I run a small shop, so I'm on my feet a lot." | MISSED | MISSED |
| *(extra P00)* | physical activity [UNSUPPORTED] | | |
| *(extra P01)* | physical activity [UNSUPPORTED] | | |

**medications**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| small white one (status="currently_used", reported_by="patient") | SEG0040 person_2 patient: "It's a... um, I can't remember what it's called. It's a small white one." | MISSED | MISSED |
| Hydrocortisone (frequency="when needed", status="currently_used", reported_by="patient") | SEG0042 person_2 patient: "For my sugar, I believe. My husband sets them out for me, I just take what I'm given. It's" | WRONG_NORM ('hydrocortisone cream') | WRONG_NORM ('hydrocortisone cream') |
| Glimepiride (status="discontinued", reported_by="patient") | SEG0042 person_2 patient: "For my sugar, I believe. My husband sets them out for me, I just take what I'm given. It's" | MISSED | MISSED |
| Clindamycin (dose="300 mg", frequency="three times a day", status="planned") | SEG0056 person_1 doctor: "so, good, that's the examination. Let's book blood tests to look into infection. Let's boo" | MISSED | MISSED |

**allergies**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Antibiotic (unspecified) (status="uncertain", reported_by="patient") | SEG0038 person_2 patient: "yeah, I think I reacted to some antibiotic once, years ago i don't remember which one, or " | WRONG_NORM ('antibiotic') | WRONG_NORM ('antibiotic') |

**vital signs**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Body temperature (value=38.1, unit="°C", reported_by="nurse") | SEG0049 person_4 nurse: "Here are the numbers, doctor. Temp 38.1 degrees, BMI works out to 27.0, height 154 centime" | MISSED | MISSED |
| Body mass index (value=27.0, unit="kg/m²", reported_by="nurse") | SEG0049 person_4 nurse: "Here are the numbers, doctor. Temp 38.1 degrees, BMI works out to 27.0, height 154 centime" | MISSED | MISSED |
| Body height (value=154, unit="cm", reported_by="nurse") | SEG0049 person_4 nurse: "Here are the numbers, doctor. Temp 38.1 degrees, BMI works out to 27.0, height 154 centime" | MISSED | MISSED |
| Blood pressure (value="110/69", unit="mmHg", reported_by="nurse") | SEG0049 person_4 nurse: "Here are the numbers, doctor. Temp 38.1 degrees, BMI works out to 27.0, height 154 centime" | CORRECT | CORRECT |
| Heart rate (value=98, unit="bpm", reported_by="nurse") | SEG0049 person_4 nurse: "Here are the numbers, doctor. Temp 38.1 degrees, BMI works out to 27.0, height 154 centime" | CORRECT | CORRECT |
| Oxygen saturation (value=97, unit="%", reported_by="nurse") | SEG0049 person_4 nurse: "Here are the numbers, doctor. Temp 38.1 degrees, BMI works out to 27.0, height 154 centime" | CORRECT | CORRECT |
| Body weight (value=64, unit="kg", reported_by="nurse") | SEG0049 person_4 nurse: "Here are the numbers, doctor. Temp 38.1 degrees, BMI works out to 27.0, height 154 centime" | WRONG_NORM ('weight') | WRONG_NORM ('weight') |
| *(extra P00)* | temperature [UNSUPPORTED] | | |
| *(extra P01)* | temperature [UNSUPPORTED] | | |

**physical examination**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| No purulent discharge (status="absent", observed_by="doctor") | SEG0053 person_1 doctor: "There's a small scab where the cut was, no pus coming out." | MISSED | MISSED |
| Erythema, warmth and swelling (status="present", observed_by="doctor") | SEG0055 person_1 doctor: "The skin on the lower leg is red, warm and swollen, about the size of my palm." | WRONG_NORM ('red warm and swollen skin on the lower leg') | WRONG_NORM ('red warm and swollen skin on the lower leg') |

**review of systems**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| gastrointestinal (status="negative", reported_by="patient") | SEG0028 person_2 patient: "no, that side's been fine" | MISSED | MISSED |
| genitourinary (status="negative", reported_by="patient") | SEG0030 person_2 patient: "That's normal as far as I know." | MISSED | MISSED |
| *(extra P00)* | respiratory [UNSUPPORTED] | | |
| *(extra P01)* | respiratory [UNSUPPORTED] | | |

**clinical conditions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Type 2 diabetes mellitus (status="existing", reported_by="patient") | SEG0032 person_2 patient: "uh, I've had diabetes for nearly five years now" | MISSED | MISSED |
| *(extra P00)* | skin infection [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |
| *(extra P01)* | skin infection [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**clinical assessment**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | skin infection [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |
| *(extra P01)* | skin infection [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**investigations/procedures**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Complete blood count and CRP (status="planned", type="laboratory") | SEG0056 person_1 doctor: "so, good, that's the examination. Let's book blood tests to look into infection. Let's boo" | WRONG_NORM ('blood tests') | WRONG_NORM ('blood tests') |
| Wound swab (status="planned", type="laboratory") | SEG0056 person_1 doctor: "so, good, that's the examination. Let's book blood tests to look into infection. Let's boo" | CORRECT | CORRECT |

**clinical actions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| investigation/arrange complete blood count and crp (status="planned", responsible_person="doctor") | SEG0056 person_1 doctor: "so, good, that's the examination. Let's book blood tests to look into infection. Let's boo" | MISSED | MISSED |
| investigation/arrange wound swab (status="planned", responsible_person="doctor") | SEG0056 person_1 doctor: "so, good, that's the examination. Let's book blood tests to look into infection. Let's boo" | MISSED | MISSED |
| medication/start clindamycin 300 mg three times a day (status="planned", responsible_person="doctor") | SEG0056 person_1 doctor: "so, good, that's the examination. Let's book blood tests to look into infection. Let's boo" | MISSED | MISSED |
| counselling/advise marking edge of redness (status="recommended", responsible_person="patient") | SEG0056 person_1 doctor: "so, good, that's the examination. Let's book blood tests to look into infection. Let's boo" | MISSED | MISSED |
| counselling/advise leg elevation (status="recommended", responsible_person="patient") | SEG0056 person_1 doctor: "so, good, that's the examination. Let's book blood tests to look into infection. Let's boo" | MISSED | MISSED |
| counselling/seek urgent care if the redness spreads or the fever gets higher (status="recommended", responsible_person="patient") | SEG0057 person_1 doctor: "Come back or go to emergency straight away if the redness spreads or the fever gets higher" | MISSED | MISSED |
| follow up/follow up consultation (status="planned", responsible_person="doctor") | SEG0057 person_1 doctor: "Come back or go to emergency straight away if the redness spreads or the fever gets higher" | MISSED | MISSED |
| *(extra P00)* | medication/take clindamycin 300 mg three times a day for seven days [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |
| *(extra P01)* | medication/take clindamycin 300 mg three times a day for seven days [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**follow up**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| consultation/in a week (status="planned", time_reference="in a week") | SEG0057 person_1 doctor: "Come back or go to emergency straight away if the redness spreads or the fever gets higher" | CORRECT | CORRECT |

**clinical uncertainties**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| conflicting_statement (resolution_status="unresolved") | SEG0020 person_2 patient: "No, none, no vomiting." | MISSED | MISSED |
| allergy_uncertain (resolution_status="unresolved") | SEG0038 person_2 patient: "yeah, I think I reacted to some antibiotic once, years ago i don't remember which one, or " | MISSED | MISSED |
| incomplete_medication_name (resolution_status="unresolved") | SEG0040 person_2 patient: "It's a... um, I can't remember what it's called. It's a small white one." | MISSED | MISSED |
| *(extra P00)* | date uncertain [UNSUPPORTED] | | |
| *(extra P01)* | date uncertain [UNSUPPORTED] | | |

**Not applicable (no gold fact and no prediction):** none.

**Evidence (L).**
- P00: 1 evidence records; 0 are an exact single transcript segment; 23 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_multi_segment_or_whole_transcript_dump': 1, 'ev_empty_supports': 1, 'fact_not_mentioned_in_cited_text': 7, 'fact_path_missing_from_supports': 12, 'fact_no_evidence_ids': 11}.
- P01: 1 evidence records; 0 are an exact single transcript segment; 24 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_text_not_in_transcript': 1, 'ev_empty_supports': 1, 'fact_not_mentioned_in_cited_text': 12, 'fact_path_missing_from_supports': 12, 'fact_no_evidence_ids': 12}.

### Record 00152   (P00: parsed, P01: parsed)

**Speakers (A).** Transcript: person_1 doctor, person_2 patient. Gold primary speakers: person_1 doctor, person_2 patient.
- P00: predicted [('person_1', 'doctor')]; all speakers+roles correct: False; missing [('person_2', 'patient')]; wrong role none; invented ids none.
- P01: predicted [('person_1', 'doctor'), ('person_2', 'patient')]; all speakers+roles correct: True; missing none; wrong role none; invented ids none.

**Chief complaint (B).** Gold: 'leaking urine when I cough or sneeze' / normalized 'Stress urinary leakage' (reported by patient).
- P00: 'leaking urine when I cough or sneeze' / normalized 'leaking urine when I cough or sneeze' (reported_by patient) -> WRONG_NORM ('leaking urine when i cough or sneeze')
- P01: 'leaking urine when I cough or sneeze' / normalized 'leaking urine when I cough or sneeze' (reported_by patient) -> WRONG_NORM ('leaking urine when i cough or sneeze')

**symptoms**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Stress urinary leakage (status="present", temporality="current", certainty="certain") | SEG0004 person_2 patient: "Um, so... leaking urine when I cough or sneeze. That's why I came." | MISSED | MISSED |
| Nocturia (status="present", temporality="current", certainty="certain") | SEG0010 person_2 patient: "Mostly mild. Yes, laughing. That makes it worse. So, I've also been getting up once at nig" | MISSED | MISSED |

**negative findings**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Haematuria (temporality="current", reported_by="patient") | SEG0011 person_1 doctor: "And what about blood in the urine or burning when passing urine?" | MISSED | MISSED |
| Dysuria (temporality="current", reported_by="patient") | SEG0011 person_1 doctor: "And what about blood in the urine or burning when passing urine?" | MISSED | MISSED |
| Back pain (temporality="current", reported_by="patient") | SEG0014 person_2 patient: "No, no back pain or difficulty emptying." | MISSED | MISSED |
| Voiding difficulty (temporality="current", reported_by="patient") | SEG0014 person_2 patient: "No, no back pain or difficulty emptying." | MISSED | MISSED |
| No known allergies (temporality="current", reported_by="patient") | SEG0017 person_1 doctor: "Any drug or food allergies?" | MISSED | MISSED |
| No regular medication (temporality="current", reported_by="patient") | SEG0023 person_1 doctor: "Are you on any regular medication?" | MISSED | MISSED |
| No previous surgery (temporality="past", reported_by="patient") | SEG0025 person_1 doctor: "Any previous surgeries?" | MISSED | MISSED |
| No known chronic conditions (temporality="current", reported_by="patient") | SEG0027 person_1 doctor: "Do you have any medical conditions I should know about?" | MISSED | MISSED |

**social history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| occupation (status="current", reported_by="patient") | SEG0020 person_2 patient: "I'm a self-employed electrician." | MISSED | MISSED |
| living (status="current", reported_by="patient") | SEG0022 person_2 patient: "I share a flat with two friends." | MISSED | MISSED |

**vital signs**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Blood pressure (value="114/80", unit="mmHg", reported_by="doctor") | SEG0007 person_1 doctor: "Okay: blood pressure 114 over 80, height 159 centimetres, temperature is 36.9 degrees, BMI" | MISSED | MISSED |
| Body height (value=159, unit="cm", reported_by="doctor") | SEG0007 person_1 doctor: "Okay: blood pressure 114 over 80, height 159 centimetres, temperature is 36.9 degrees, BMI" | MISSED | MISSED |
| Body temperature (value=36.9, unit="°C", reported_by="doctor") | SEG0007 person_1 doctor: "Okay: blood pressure 114 over 80, height 159 centimetres, temperature is 36.9 degrees, BMI" | MISSED | MISSED |
| Body mass index (value=36.8, unit="kg/m²", reported_by="doctor") | SEG0007 person_1 doctor: "Okay: blood pressure 114 over 80, height 159 centimetres, temperature is 36.9 degrees, BMI" | MISSED | MISSED |
| Respiratory rate (value=15, unit="breaths/min", reported_by="doctor") | SEG0007 person_1 doctor: "Okay: blood pressure 114 over 80, height 159 centimetres, temperature is 36.9 degrees, BMI" | MISSED | MISSED |
| Body weight (value=93, unit="kg", reported_by="doctor") | SEG0007 person_1 doctor: "Okay: blood pressure 114 over 80, height 159 centimetres, temperature is 36.9 degrees, BMI" | MISSED | MISSED |
| Heart rate (value=68, unit="bpm", reported_by="doctor") | SEG0007 person_1 doctor: "Okay: blood pressure 114 over 80, height 159 centimetres, temperature is 36.9 degrees, BMI" | MISSED | MISSED |
| Oxygen saturation (value=99, unit="%", reported_by="doctor") | SEG0007 person_1 doctor: "Okay: blood pressure 114 over 80, height 159 centimetres, temperature is 36.9 degrees, BMI" | MISSED | MISSED |

**physical examination**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| No visible prolapse (status="absent", observed_by="doctor") | SEG0031 person_1 doctor: "No bulge is visible when you cough, and the tummy is soft." | MISSED | MISSED |

**review of systems**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| respiratory (status="negative", reported_by="patient") | SEG0016 person_2 patient: "Breathing's normal." | MISSED | MISSED |

**clinical assessment**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Stress urinary incontinence (certainty="differential", stated_by="doctor") | SEG0033 person_1 doctor: "Let me tell you where I've got to. I can't pin this down yet. We're looking at stress urin" | WRONG_STATUS: certainty: gold="differential" pred="provisional" | WRONG_STATUS: certainty: gold="differential" pred="provisional" |
| Overactive bladder (certainty="differential", stated_by="doctor") | SEG0033 person_1 doctor: "Let me tell you where I've got to. I can't pin this down yet. We're looking at stress urin" | MISSED | MISSED |

**investigations/procedures**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Bladder diary (status="planned", type="other") | SEG0035 person_1 doctor: "Nothing I've seen today points to an emergency. It looks like stress urinary incontinence," | MISSED | MISSED |

**clinical actions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| investigation/arrange bladder diary (status="planned", responsible_person="doctor") | SEG0035 person_1 doctor: "Nothing I've seen today points to an emergency. It looks like stress urinary incontinence," | MISSED | MISSED |
| counselling/pelvic floor exercises (status="recommended", responsible_person="patient") | SEG0035 person_1 doctor: "Nothing I've seen today points to an emergency. It looks like stress urinary incontinence," | MISSED | MISSED |
| follow up/follow up consultation (status="planned", responsible_person="doctor") | SEG0035 person_1 doctor: "Nothing I've seen today points to an emergency. It looks like stress urinary incontinence," | MISSED | MISSED |

**follow up**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| consultation/in six weeks (status="planned", time_reference="in six weeks") | SEG0035 person_1 doctor: "Nothing I've seen today points to an emergency. It looks like stress urinary incontinence," | MISSED | MISSED |

**Not applicable (no gold fact and no prediction):** past medical history, surgical history, family history, medications, allergies, clinical conditions, clinical uncertainties.

**Evidence (L).**
- P00: 1 evidence records; 0 are an exact single transcript segment; 2 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_near_copy_not_exact': 1, 'ev_empty_supports': 1, 'fact_path_missing_from_supports': 2, 'fact_not_mentioned_in_cited_text': 1}.
- P01: 1 evidence records; 0 are an exact single transcript segment; 2 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_text_not_in_transcript': 1, 'ev_empty_supports': 1, 'fact_path_missing_from_supports': 2, 'fact_not_mentioned_in_cited_text': 1}.

### Record 00155   (P00: FAILED, P01: parsed)

**Speakers (A).** Transcript: person_1 patient, person_2 doctor, person_3 family_member. Gold primary speakers: person_1 patient, person_2 doctor, person_3 family_member.
- P00: no usable output.
- P01: predicted [('person_1', 'patient'), ('person_2', 'doctor')]; all speakers+roles correct: False; missing [('person_3', 'family_member')]; wrong role none; invented ids none.

**Chief complaint (B).** Gold: 'throbbing headache on one side' / normalized 'Headache' (reported by patient).
- P00: no usable output.
- P01: 'I wanted to get a throbbing headache on one side looked at.' / normalized 'I wanted to get a throbbing headache on one side looked at.' (reported_by person_1) -> WRONG_NORM ('i wanted to get a throbbing headache on one side looked at')

**symptoms**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Headache (status="present", temporality="current", certainty="certain") | SEG0004 person_1 patient: "I wanted to get a throbbing headache on one side looked at." | NO OUTPUT (record failed) | WRONG_STATUS: temporality: gold="current" pred="past"; certainty: gold="certain" pred="uncertain"; severity: gold="4/10" pred=null; duration: gold={"value": 1, "uni |
| Vomiting (status="present", temporality="current", certainty="certain") | SEG0010 person_1 patient: "It usually comes with vomiting. And nausea as well, since last Tuesday." | NO OUTPUT (record failed) | WRONG_STATUS: temporality: gold="current" pred="present"; certainty: gold="certain" pred="uncertain"; duration: gold={"value": 10, "unit": "days", "normalize pred={ |
| Nausea (status="present", temporality="current", certainty="certain") | SEG0010 person_1 patient: "It usually comes with vomiting. And nausea as well, since last Tuesday." | NO OUTPUT (record failed) | MISSED |

**negative findings**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Diplopia (temporality="current", reported_by="patient") | SEG0024 person_2 doctor: "Good, that's the examination. And what about double vision or loss of consciousness?" | NO OUTPUT (record failed) | MISSED |
| Loss of consciousness (temporality="current", reported_by="patient") | SEG0024 person_2 doctor: "Good, that's the examination. And what about double vision or loss of consciousness?" | NO OUTPUT (record failed) | MISSED |
| Neck stiffness (temporality="current", reported_by="patient") | SEG0026 person_2 doctor: "and what about neck stiffness or fever?" | NO OUTPUT (record failed) | MISSED |
| Fever (temporality="current", reported_by="patient") | SEG0026 person_2 doctor: "and what about neck stiffness or fever?" | NO OUTPUT (record failed) | WRONG_NORM ('no fever') |
| No known allergies (temporality="current", reported_by="patient") | SEG0030 person_2 doctor: "okay, are there any allergies on your record that I should check?" | NO OUTPUT (record failed) | MISSED |

**past medical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Migraine (status="ongoing", reported_by="patient") | SEG0033 person_1 patient: "I have migraines, for about ten years yes, anxiety" | NO OUTPUT (record failed) | WRONG_NORM ('Migraines') |
| Anxiety disorder (status="ongoing", reported_by="patient") | SEG0033 person_1 patient: "I have migraines, for about ten years yes, anxiety" | NO OUTPUT (record failed) | WRONG_NORM ('anxiety') |

**surgical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P01)* | migraines [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**family history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P01)* | migraines [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**social history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| alcohol (status="current", reported_by="patient") | SEG0039 person_2 doctor: "So, and alcohol, how much?" | NO OUTPUT (record failed) | MISSED |
| occupation (status="current", reported_by="patient") | SEG0042 person_1 patient: "I work in an office, mostly sitting at a desk." | NO OUTPUT (record failed) | MISSED |
| living (status="current", reported_by="patient") | SEG0044 person_1 patient: "I share a flat with two friends" | NO OUTPUT (record failed) | MISSED |
| *(extra P01)* | work [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**medications**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Sumatriptan (dose="50 mg", frequency="when needed", status="currently_used") | SEG0036 person_1 patient: "I'm on something called suma... sumatriptan, 50 milligrams, maybe, when needed for my migr" | NO OUTPUT (record failed) | WRONG_ATTRIB: route: not in gold, pred="oral"; reported_by: gold="patient" pred="person_1" (speaker id written instead of role) |
| Propranolol (dose="20 mg", route="oral", frequency="twice a day") | SEG0053 person_1 patient: "So, I take the propranolol, 20 milligrams, twice a day and take the domperidone, 10 millig" | NO OUTPUT (record failed) | MISSED |
| Domperidone (dose="10 mg", route="oral", frequency="when nauseous") | SEG0053 person_1 patient: "So, I take the propranolol, 20 milligrams, twice a day and take the domperidone, 10 millig" | NO OUTPUT (record failed) | WRONG_STATUS: frequency: gold="when nauseous" pred="as needed"; status: gold="planned" pred="currently_used"; reported_by: gold="doctor" pred="person_1" (speaker id |

**allergies**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P01)* | sumatriptan [INCORRECT - a medication from the medication list written as an allergy] | | |

**vital signs**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Heart rate (value=67, unit="bpm", reported_by="doctor") | SEG0015 person_2 doctor: "okay: pulse is 67 beats a minute, temperature 37.0, oxygen saturation is 97 percent, blood" | NO OUTPUT (record failed) | MISSED |
| Body temperature (value=37.0, unit="°C", reported_by="doctor") | SEG0015 person_2 doctor: "okay: pulse is 67 beats a minute, temperature 37.0, oxygen saturation is 97 percent, blood" | NO OUTPUT (record failed) | WRONG_NORM ('temperature') |
| Oxygen saturation (value=97, unit="%", reported_by="doctor") | SEG0015 person_2 doctor: "okay: pulse is 67 beats a minute, temperature 37.0, oxygen saturation is 97 percent, blood" | NO OUTPUT (record failed) | WRONG_ATTRIB: reported_by: gold="doctor" pred="person_1" (speaker id written instead of role) |
| Blood pressure (value="120/73", unit="mmHg", reported_by="doctor") | SEG0015 person_2 doctor: "okay: pulse is 67 beats a minute, temperature 37.0, oxygen saturation is 97 percent, blood" | NO OUTPUT (record failed) | WRONG_ATTRIB: reported_by: gold="doctor" pred="person_1" (speaker id written instead of role) |
| *(extra P01)* | pulse [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**physical examination**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Supple neck (status="present", observed_by="doctor") | SEG0021 person_2 doctor: "Neck is supple, no stiffness at all." | NO OUTPUT (record failed) | WRONG_NORM ('neck is supple no stiffness at all') |
| Normal cranial nerve examination (status="present", observed_by="doctor") | SEG0023 person_2 doctor: "Cranial nerves look normal, eye movements are full." | NO OUTPUT (record failed) | WRONG_NORM ('cranial nerves look normal eye movements are full') |

**review of systems**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| genitourinary (status="negative", reported_by="patient") | SEG0029 person_1 patient: "That's normal as far as I know." | NO OUTPUT (record failed) | MISSED |
| *(extra P01)* | neurological [UNSUPPORTED] | | |

**clinical conditions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Migraine (status="existing", reported_by="patient") | SEG0033 person_1 patient: "I have migraines, for about ten years yes, anxiety" | NO OUTPUT (record failed) | MISSED |
| Anxiety disorder (status="existing", reported_by="patient") | SEG0033 person_1 patient: "I have migraines, for about ten years yes, anxiety" | NO OUTPUT (record failed) | MISSED |
| *(extra P01)* | migraine with aura [INCORRECT - gold has this fact in category 'clinical assessment'] | | |

**clinical assessment**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Migraine with aura (certainty="provisional", stated_by="doctor") | SEG0045 person_2 doctor: "Okay, thinking it through, I think we're dealing with migraine with aura at this stage. Te" | NO OUTPUT (record failed) | CORRECT |
| Tension-type headache (certainty="differential", stated_by="doctor") | SEG0045 person_2 doctor: "Okay, thinking it through, I think we're dealing with migraine with aura at this stage. Te" | NO OUTPUT (record failed) | MISSED |

**investigations/procedures**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| MRI brain (status="planned", type="imaging") | SEG0047 person_2 doctor: "I understand the worry. At the moment I'd say it's migraine with aura, and we'll know more" | NO OUTPUT (record failed) | WRONG_NORM ('MRI of the brain') |

**clinical actions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| investigation/arrange magnetic resonance imaging brain (status="planned", responsible_person="doctor") | SEG0047 person_2 doctor: "I understand the worry. At the moment I'd say it's migraine with aura, and we'll know more" | NO OUTPUT (record failed) | MISSED |
| medication/start propranolol 20 mg twice a day (status="planned", responsible_person="doctor") | SEG0053 person_1 patient: "So, I take the propranolol, 20 milligrams, twice a day and take the domperidone, 10 millig" | NO OUTPUT (record failed) | WRONG_NORM ('medication/propranolol 20 mg twice a day') |
| medication/start domperidone 10 mg when nauseous (status="planned", responsible_person="doctor") | SEG0053 person_1 patient: "So, I take the propranolol, 20 milligrams, twice a day and take the domperidone, 10 millig" | NO OUTPUT (record failed) | WRONG_NORM ('medication/domperidone 10 mg when nauseous') |
| counselling/advise regular meals and sleep (status="recommended", responsible_person="patient") | SEG0049 person_2 doctor: "The treatment will be propranolol, 20 milligrams, twice a day, for three months. You take " | NO OUTPUT (record failed) | MISSED |
| counselling/advise headache diary (status="recommended", responsible_person="patient") | SEG0049 person_2 doctor: "The treatment will be propranolol, 20 milligrams, twice a day, for three months. You take " | NO OUTPUT (record failed) | MISSED |
| other/bring latest prescription or medication box to next visit (status="recommended", responsible_person="patient") | SEG0050 person_2 doctor: "and please bring the latest prescription or the medicine boxes to the next visit, so we ca" | NO OUTPUT (record failed) | MISSED |
| counselling/seek urgent care if you have the worst headache of your life or any weakness (status="recommended", responsible_person="patient") | SEG0050 person_2 doctor: "and please bring the latest prescription or the medicine boxes to the next visit, so we ca" | NO OUTPUT (record failed) | MISSED |
| follow up/follow up consultation (status="planned", responsible_person="doctor") | SEG0052 person_2 doctor: "book a review in six weeks. Let me check I've been clear. What will you do once you get ho" | NO OUTPUT (record failed) | MISSED |
| *(extra P01)* | follow up/book a review in six weeks [UNSUPPORTED] | | |

**follow up**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| consultation/in six weeks (status="planned", time_reference="in six weeks") | SEG0052 person_2 doctor: "book a review in six weeks. Let me check I've been clear. What will you do once you get ho" | NO OUTPUT (record failed) | MISSED |
| *(extra P01)* | follow up/six weeks [UNSUPPORTED] | | |

**clinical uncertainties**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| uncertain_dose (resolution_status="unresolved") | SEG0036 person_1 patient: "I'm on something called suma... sumatriptan, 50 milligrams, maybe, when needed for my migr" | NO OUTPUT (record failed) | MISSED |
| *(extra P01)* | conflicting statement [UNSUPPORTED] | | |

**Not applicable (no gold fact and no prediction):** none.

**Evidence (L).**
- P00: no usable output.
- P01: 1 evidence records; 0 are an exact single transcript segment; 27 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_multi_segment_or_whole_transcript_dump': 1, 'ev_empty_supports': 1, 'fact_path_missing_from_supports': 27, 'fact_not_mentioned_in_cited_text': 24}.

### Record 00157   (P00: parsed, P01: parsed)

**Speakers (A).** Transcript: person_1 doctor, person_2 patient. Gold primary speakers: person_1 doctor, person_2 patient.
- P00: predicted [('person_1', 'doctor')]; all speakers+roles correct: False; missing [('person_2', 'patient')]; wrong role none; invented ids none.
- P01: predicted [('person_1', 'doctor')]; all speakers+roles correct: False; missing [('person_2', 'patient')]; wrong role none; invented ids none.

**Chief complaint (B).** Gold: 'sneezing fits' / normalized 'Sneezing' (reported by patient).
- P00: 'sneezing fits' / normalized 'sneezing fits' (reported_by patient) -> WRONG_NORM ('sneezing fits')
- P01: 'sneezing fits' / normalized 'sneezing fits' (reported_by patient) -> WRONG_NORM ('sneezing fits')

**symptoms**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Sneezing (status="present", temporality="current", certainty="certain") | SEG0002 person_2 patient: "Doctor, it's sneezing fits. It's getting on my nerves now." | CORRECT | CORRECT |
| Nasal congestion (status="present", temporality="current", certainty="certain") | SEG0008 person_2 patient: "I notice it more with early mornings. There's a blocked nose at night as well." | MISSED | MISSED |

**negative findings**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Anosmia (temporality="current", reported_by="patient") | SEG0009 person_1 doctor: "Did you get loss of smell, facial pain, fever or shortness of breath?" | MISSED | MISSED |
| Facial pain (temporality="current", reported_by="patient") | SEG0009 person_1 doctor: "Did you get loss of smell, facial pain, fever or shortness of breath?" | MISSED | MISSED |
| Fever (temporality="current", reported_by="patient") | SEG0009 person_1 doctor: "Did you get loss of smell, facial pain, fever or shortness of breath?" | MISSED | MISSED |
| Shortness of breath (temporality="current", reported_by="patient") | SEG0009 person_1 doctor: "Did you get loss of smell, facial pain, fever or shortness of breath?" | MISSED | MISSED |
| No known allergies (temporality="current", reported_by="patient") | SEG0013 person_1 doctor: "Any drug or food allergies?" | MISSED | MISSED |
| No known chronic conditions (temporality="current", reported_by="patient") | SEG0019 person_1 doctor: "Any medical conditions, anything you've been treated for?" | MISSED | MISSED |

**social history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| exercise (status="current", reported_by="patient") | SEG0015 person_1 doctor: "Do you exercise at all?" | MISSED | MISSED |
| living (status="current", reported_by="patient") | SEG0018 person_2 patient: "I stay with my daughter and her family." | MISSED | MISSED |

**medications**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Cetirizine (dose="10 mg", frequency="when it flares", status="currently_used") | SEG0004 person_2 patient: "I take cetirizine, 10 milligrams, when it flares." | CORRECT | PARTIAL: frequency: gold="when it flares" pred="day to day" |
| Fluticasone (dose="50 micrograms", frequency="one spray each side dail, status="planned") | SEG0033 person_1 doctor: "I want an allergy test done, that's for allergic rhinitis. What I'm giving you is fluticas" | MISSED | MISSED |

**allergies**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | none [INCORRECT - placeholder written as an allergy entry (gold has no allergy)] | | |
| *(extra P01)* | none [INCORRECT - placeholder written as an allergy entry (gold has no allergy)] | | |

**vital signs**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Respiratory rate (value=16, unit="breaths/min", reported_by="doctor") | SEG0023 person_1 doctor: "Okay: respiratory rate 16, pressure 123 over 68, SpO2 98 percent on room air, temperature " | MISSED | MISSED |
| Blood pressure (value="123/68", unit="mmHg", reported_by="doctor") | SEG0023 person_1 doctor: "Okay: respiratory rate 16, pressure 123 over 68, SpO2 98 percent on room air, temperature " | MISSED | MISSED |
| Oxygen saturation (value=98, unit="%", reported_by="doctor") | SEG0023 person_1 doctor: "Okay: respiratory rate 16, pressure 123 over 68, SpO2 98 percent on room air, temperature " | MISSED | MISSED |
| Body temperature (value=36.5, unit="°C", reported_by="doctor") | SEG0023 person_1 doctor: "Okay: respiratory rate 16, pressure 123 over 68, SpO2 98 percent on room air, temperature " | MISSED | MISSED |
| Heart rate (value=83, unit="bpm", reported_by="doctor") | SEG0023 person_1 doctor: "Okay: respiratory rate 16, pressure 123 over 68, SpO2 98 percent on room air, temperature " | MISSED | MISSED |

**physical examination**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| No wheeze (status="absent", observed_by="doctor") | SEG0026 person_1 doctor: "Chest is clear, no wheeze." | MISSED | MISSED |
| Pale swollen nasal mucosa (status="present", observed_by="doctor") | SEG0028 person_1 doctor: "The inside of your nose is pale and swollen." | WRONG_NORM ('pale and swollen inside of the nose') | WRONG_NORM ('pale and swollen inside of the nose') |

**review of systems**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| skin (status="negative", reported_by="patient") | SEG0012 person_2 patient: "Skin's normal." | MISSED | MISSED |

**clinical conditions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | allergic rhinitis [INCORRECT - gold has this fact in category 'clinical assessment'] | | |
| *(extra P01)* | allergic rhinitis [INCORRECT - gold has this fact in category 'clinical assessment'] | | |

**clinical assessment**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Allergic rhinitis (certainty="provisional", stated_by="doctor") | SEG0030 person_1 doctor: "Let me tell you where I've got to. The most likely explanation is allergic rhinitis." | CORRECT | CORRECT |

**investigations/procedures**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Allergen skin prick test (status="planned", type="other") | SEG0033 person_1 doctor: "I want an allergy test done, that's for allergic rhinitis. What I'm giving you is fluticas" | WRONG_NORM ('allergy test') | WRONG_NORM ('allergy test') |

**clinical actions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| investigation/arrange allergen skin prick test (status="planned", responsible_person="doctor") | SEG0033 person_1 doctor: "I want an allergy test done, that's for allergic rhinitis. What I'm giving you is fluticas" | MISSED | MISSED |
| medication/start fluticasone 50 mcg one spray each side daily (status="planned", responsible_person="doctor") | SEG0033 person_1 doctor: "I want an allergy test done, that's for allergic rhinitis. What I'm giving you is fluticas" | MISSED | MISSED |
| counselling/advise allergen avoidance measures (status="recommended", responsible_person="patient") | SEG0033 person_1 doctor: "I want an allergy test done, that's for allergic rhinitis. What I'm giving you is fluticas" | MISSED | MISSED |
| counselling/seek urgent care if the symptoms get worse (status="recommended", responsible_person="patient") | SEG0033 person_1 doctor: "I want an allergy test done, that's for allergic rhinitis. What I'm giving you is fluticas" | MISSED | MISSED |
| follow up/follow up consultation (status="planned", responsible_person="doctor") | SEG0035 person_1 doctor: "Book a review in four weeks." | MISSED | MISSED |
| *(extra P00)* | follow up/book a review in four weeks [UNSUPPORTED] | | |
| *(extra P01)* | follow up/book a review in four weeks [UNSUPPORTED]; medication/fluticasone nasal spray 50 mcg one spray each side daily for four weeks [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**follow up**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| consultation/in four weeks (status="planned", time_reference="in four weeks") | SEG0035 person_1 doctor: "Book a review in four weeks." | MISSED | MISSED |
| *(extra P00)* | consultation/302.47 304.83s [UNSUPPORTED] | | |
| *(extra P01)* | follow up/4 weeks [UNSUPPORTED] | | |

**Not applicable (no gold fact and no prediction):** past medical history, surgical history, family history, clinical uncertainties.

**Evidence (L).**
- P00: 1 evidence records; 0 are an exact single transcript segment; 10 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_text_not_in_transcript': 1, 'ev_empty_supports': 1, 'fact_not_mentioned_in_cited_text': 10, 'fact_path_missing_from_supports': 10}.
- P01: 1 evidence records; 0 are an exact single transcript segment; 11 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_text_not_in_transcript': 1, 'ev_empty_supports': 1, 'fact_not_mentioned_in_cited_text': 11, 'fact_path_missing_from_supports': 11}.

### Record 00162   (P00: parsed, P01: parsed)

**Speakers (A).** Transcript: person_1 patient, person_2 doctor, person_3 nurse. Gold primary speakers: person_1 patient, person_2 doctor, person_3 nurse.
- P00: predicted [('person_1', 'patient'), ('person_2', 'doctor'), ('person_3', 'nurse')]; all speakers+roles correct: True; missing none; wrong role none; invented ids none.
- P01: predicted [('person_1', 'patient'), ('person_2', 'doctor'), ('person_3', 'nurse')]; all speakers+roles correct: True; missing none; wrong role none; invented ids none.

**Chief complaint (B).** Gold: 'neck pain going down my right arm' / normalized 'Neck pain with right arm radiation' (reported by patient).
- P00: 'neck pain going down my right arm' / normalized 'neck pain going down my right arm' (reported_by patient) -> WRONG_NORM ('neck pain going down my right arm')
- P01: 'neck pain going down my right arm' / normalized 'neck pain going down my right arm' (reported_by patient) -> WRONG_NORM ('neck pain going down my right arm')

**symptoms**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Neck pain with right arm radiation (status="present", temporality="current", certainty="certain") | SEG0003 person_1 patient: "It's neck pain going down my right arm. I thought I'd wait, but it hasn't gone." | WRONG_NORM ('neck pain') | WRONG_NORM ('neck pain') |
| Nocturnal arm ache (status="present", temporality="current", certainty="certain") | SEG0007 person_1 patient: "It settles a little with resting my arm on my head. I'd call it severe. I've been waking w" | WRONG_NORM ('waking with arm ache') | WRONG_NORM ('waking with an ache in the arm') |
| *(extra P00)* | arm pain [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |
| *(extra P01)* | right arm pain [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**negative findings**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Fever (temporality="current", reported_by="patient") | SEG0008 person_2 doctor: "Any fever balance problems or weakness in the legs?" | WRONG_NORM ('no fever') | WRONG_NORM ('no fever') |
| Balance problems (temporality="current", reported_by="patient") | SEG0008 person_2 doctor: "Any fever balance problems or weakness in the legs?" | MISSED | MISSED |
| Leg weakness (temporality="current", reported_by="patient") | SEG0008 person_2 doctor: "Any fever balance problems or weakness in the legs?" | MISSED | MISSED |
| No known chronic conditions (temporality="current", reported_by="patient") | SEG0016 person_2 doctor: "do you have any medical conditions I should know about?" | MISSED | MISSED |
| *(extra P00)* | no allergies [UNSUPPORTED]; no previous surgery [UNSUPPORTED] | | |
| *(extra P01)* | no allergies [UNSUPPORTED]; no previous surgery [UNSUPPORTED] | | |

**past medical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | neck pain [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |
| *(extra P01)* | neck pain [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**surgical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | x ray of the neck [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |
| *(extra P01)* | x ray of the neck [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**social history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| living (status="current", reported_by="patient") | SEG0012 person_2 doctor: "Do you live alone?" | MISSED | MISSED |
| occupation (status="current", reported_by="patient") | SEG0015 person_1 patient: "I work night shifts at a warehouse" | WRONG_STATUS: status: gold="current" pred="" | MISSED |
| *(extra P01)* | living alone [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**medications**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Paracetamol (dose="500 mg", frequency="when needed", status="currently_used") | SEG0019 person_1 patient: "I take paracetamol, 500 milligrams, when needed. I took the morning off to come in today. " | UNSUPPORTED: route: not in gold, pred="oral" | PARTIAL: route: not in gold, pred="oral"; frequency: gold="when needed" pred=null |
| Naproxen (dose="250 mg", frequency="twice a day after food", status="planned") | SEG0031 person_2 doctor: "For this, naproxen, 250 milligrams, twice a day after food, for five days. That's for nerv" | MISSED | MISSED |

**allergies**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | paracetamol [INCORRECT - a medication from the medication list written as an allergy] | | |
| *(extra P01)* | paracetamol [INCORRECT - a medication from the medication list written as an allergy] | | |

**vital signs**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Body temperature (value=36.7, unit="°C", reported_by="nurse") | SEG0020 person_3 nurse: "here are the numbers, doctor. Temp 36.7 degrees, SpO2 99 percent on room air, BP is 111 ov" | MISSED | MISSED |
| Oxygen saturation (value=99, unit="%", reported_by="nurse") | SEG0020 person_3 nurse: "here are the numbers, doctor. Temp 36.7 degrees, SpO2 99 percent on room air, BP is 111 ov" | CORRECT | CORRECT |
| Blood pressure (value="111/70", unit="mmHg", reported_by="nurse") | SEG0020 person_3 nurse: "here are the numbers, doctor. Temp 36.7 degrees, SpO2 99 percent on room air, BP is 111 ov" | CORRECT | CORRECT |
| Heart rate (value=66, unit="bpm", reported_by="nurse") | SEG0020 person_3 nurse: "here are the numbers, doctor. Temp 36.7 degrees, SpO2 99 percent on room air, BP is 111 ov" | MISSED | MISSED |
| *(extra P00)* | pulse [EXTRA_SUPPORTED_BY_TRANSCRIPT]; temperature [UNSUPPORTED] | | |
| *(extra P01)* | pulse [EXTRA_SUPPORTED_BY_TRANSCRIPT]; temperature [UNSUPPORTED] | | |

**physical examination**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Reduced right biceps power (status="present", observed_by="doctor") | SEG0024 person_2 doctor: "Biceps power is a little reduced on the right." | WRONG_NORM ('reduced biceps power on the right') | WRONG_NORM ('reduced biceps power on the right') |
| Positive Spurling test (status="present", observed_by="doctor") | SEG0026 person_2 doctor: "Tilting the head to the right brings on the arm tingling" | WRONG_NORM ('arm tingling on tilting the head to the right') | WRONG_NORM ('arm tingling on tilting the head to the right') |

**review of systems**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| respiratory (status="negative", reported_by="patient") | SEG0011 person_1 patient: "breathing's normal" | MISSED | MISSED |
| *(extra P00)* | neurological [UNSUPPORTED] | | |
| *(extra P01)* | neurological [UNSUPPORTED] | | |

**clinical conditions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | neck pain [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |
| *(extra P01)* | neck pain [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**clinical assessment**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Pinched nerve in the neck (certainty="provisional", stated_by="doctor") | SEG0028 person_2 doctor: "okay, thinking it through, it points towards a pinched nerve in the neck" | CORRECT | CORRECT |

**investigations/procedures**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Cervical spine X-ray (status="planned", type="imaging") | SEG0029 person_2 doctor: "I'll request an X-ray of the neck, it'll help with neck and arm pain" | WRONG_NORM ('x ray of the neck') | WRONG_NORM ('x ray of the neck') |

**clinical actions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| investigation/arrange cervical spine x ray (status="planned", responsible_person="doctor") | SEG0029 person_2 doctor: "I'll request an X-ray of the neck, it'll help with neck and arm pain" | MISSED | MISSED |
| medication/start naproxen 250 mg twice a day after food (status="planned", responsible_person="doctor") | SEG0031 person_2 doctor: "For this, naproxen, 250 milligrams, twice a day after food, for five days. That's for nerv" | MISSED | MISSED |
| counselling/neck mobility and posture advice (status="recommended", responsible_person="patient") | SEG0031 person_2 doctor: "For this, naproxen, 250 milligrams, twice a day after food, for five days. That's for nerv" | MISSED | MISSED |
| counselling/advise adequate fluid intake and rest (status="recommended", responsible_person="patient") | SEG0031 person_2 doctor: "For this, naproxen, 250 milligrams, twice a day after food, for five days. That's for nerv" | MISSED | MISSED |
| referral/refer to physiotherapy (status="planned", responsible_person="doctor") | SEG0031 person_2 doctor: "For this, naproxen, 250 milligrams, twice a day after food, for five days. That's for nerv" | WRONG_NORM ('referral/physiotherapy') | MISSED |
| counselling/seek urgent care if the symptoms get worse (status="recommended", responsible_person="patient") | SEG0033 person_2 doctor: "Keep an eye out, and if the symptoms get worse, call us the same day or go to emergency. P" | MISSED | MISSED |
| follow up/follow up consultation (status="planned", responsible_person="doctor") | SEG0033 person_2 doctor: "Keep an eye out, and if the symptoms get worse, call us the same day or go to emergency. P" | MISSED | MISSED |
| *(extra P00)* | follow up/see me in three weeks [UNSUPPORTED] | | |
| *(extra P01)* | medication/naproxen 250 mg twice a day after food for five days [EXTRA_SUPPORTED_BY_TRANSCRIPT]; counselling/keep the neck moving gently and avoid long periods looking down at a phone [UNSUPPORTED]; follow up/please come and see me in three weeks [UNSUPPORTED] | | |

**follow up**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| consultation/in three weeks (status="planned", time_reference="in three weeks") | SEG0033 person_2 doctor: "Keep an eye out, and if the symptoms get worse, call us the same day or go to emergency. P" | MISSED | WRONG_NORM ('consultation/three weeks') |
| *(extra P00)* | follow up/three weeks [UNSUPPORTED] | | |

**clinical uncertainties**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | date uncertain [UNSUPPORTED] | | |
| *(extra P01)* | date uncertain [UNSUPPORTED] | | |

**Not applicable (no gold fact and no prediction):** family history.

**Evidence (L).**
- P00: 1 evidence records; 0 are an exact single transcript segment; 26 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_near_copy_not_exact': 1, 'ev_empty_supports': 1, 'fact_not_mentioned_in_cited_text': 23, 'fact_path_missing_from_supports': 26}.
- P01: 1 evidence records; 1 are an exact single transcript segment; 27 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_empty_supports': 1, 'fact_not_mentioned_in_cited_text': 24, 'fact_path_missing_from_supports': 27}.

### Record 00165   (P00: parsed, P01: parsed)

**Speakers (A).** Transcript: person_1 nurse, person_2 doctor, person_3 patient. Gold primary speakers: person_1 nurse, person_2 doctor, person_3 patient.
- P00: predicted [('person_1', 'NURSE'), ('person_2', 'DOCTOR'), ('person_3', 'PATIENT')]; all speakers+roles correct: False; missing [('person_1', 'nurse'), ('person_2', 'doctor'), ('person_3', 'patient')]; wrong role [('person_1', 'NURSE'), ('person_2', 'DOCTOR'), ('person_3', 'PATIENT')]; invented ids none.
- P01: predicted [('person_1', 'nurse'), ('person_2', 'doctor'), ('person_3', 'patient')]; all speakers+roles correct: True; missing none; wrong role none; invented ids none.

**Chief complaint (B).** Gold: 'fever' / normalized 'Fever' (reported by patient).
- P00: 'I've been having a fever' / normalized 'I've been having a fever' (reported_by person_3) -> WRONG_NORM ('i ve been having a fever')
- P01: 'I've been having a fever' / normalized 'I've been having a fever' (reported_by patient) -> WRONG_NORM ('i ve been having a fever')

**symptoms**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Fever (status="present", temporality="current", certainty="certain") | SEG0003 person_3 patient: "Well, I've been having a fever." | WRONG_ATTRIB: reported_by: gold="patient" pred="person_3" (speaker id written instead of role) | CORRECT |
| Odynophagia (status="present", temporality="current", certainty="certain") | SEG0007 person_2 doctor: "Any pain on swallowing as well?" | MISSED | MISSED |

**negative findings**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Ear pain (temporality="current", reported_by="patient") | SEG0009 person_2 doctor: "And what about ear pain or cough?" | MISSED | MISSED |
| Cough (temporality="current", reported_by="patient") | SEG0009 person_2 doctor: "And what about ear pain or cough?" | MISSED | MISSED |
| Rash (temporality="current", reported_by="patient") | SEG0011 person_2 doctor: "Any rash, difficulty breathing or runny nose at all?" | MISSED | MISSED |
| Difficulty breathing (temporality="current", reported_by="patient") | SEG0011 person_2 doctor: "Any rash, difficulty breathing or runny nose at all?" | MISSED | MISSED |
| Rhinorrhoea (temporality="current", reported_by="patient") | SEG0011 person_2 doctor: "Any rash, difficulty breathing or runny nose at all?" | MISSED | MISSED |
| No previous surgery (temporality="past", reported_by="patient") | SEG0015 person_2 doctor: "Any previous surgeries?" | MISSED | MISSED |
| No known allergies (temporality="current", reported_by="patient") | SEG0022 person_3 patient: "No allergies." | WRONG_NORM ('no allergies') | WRONG_NORM ('no allergies') |

**past medical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Asthma (status="ongoing", reported_by="patient") | SEG0020 person_3 patient: "Asthma, for nearly five years." | WRONG_ATTRIB: reported_by: gold="patient" pred="person_3" (speaker id written instead of role) | CORRECT |

**surgical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | no operations [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |
| *(extra P01)* | no operations [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**family history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Diabetes mellitus (relation="mother", reported_by="patient") | SEG0018 person_3 patient: "My mother has diabetes." | WRONG_NORM ('diabetes') | WRONG_NORM ('diabetes') |

**social history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| occupation (status="current", reported_by="patient") | SEG0026 person_3 patient: "I drive a delivery van all day. I play badminton on Sundays. I stay with my daughter and h" | MISSED | MISSED |
| exercise (status="current", reported_by="patient") | SEG0026 person_3 patient: "I drive a delivery van all day. I play badminton on Sundays. I stay with my daughter and h" | MISSED | MISSED |
| living (status="current", reported_by="patient") | SEG0026 person_3 patient: "I drive a delivery van all day. I play badminton on Sundays. I stay with my daughter and h" | MISSED | MISSED |
| *(extra P00)* | lifestyle [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |
| *(extra P01)* | lifestyle [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**medications**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Salmeterol/fluticasone (frequency="twice a day", status="currently_used", reported_by="patient") | SEG0024 person_3 patient: "It's Seretide inhaler, twice a day for my asthma. Paracetamol, 500 milligrams, when needed" | WRONG_NORM ('seretide inhaler') | WRONG_NORM ('seretide inhaler') |
| Paracetamol (dose="500 mg", frequency="when needed", status="currently_used") | SEG0024 person_3 patient: "It's Seretide inhaler, twice a day for my asthma. Paracetamol, 500 milligrams, when needed" | WRONG_ATTRIB: route: not in gold, pred="oral"; reported_by: gold="patient" pred="person_3" (speaker id written instead of role) | UNSUPPORTED: route: not in gold, pred="oral" |
| Azithromycin (dose="500 mg", frequency="once a day", status="planned") | SEG0035 person_2 doctor: "I can't promise yet, but most people with tonsillitis, probably bacterial do well once it'" | MISSED | MISSED |

**allergies**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | no allergies [INCORRECT - placeholder written as an allergy entry (gold has no allergy)] | | |
| *(extra P01)* | no allergies [INCORRECT - placeholder written as an allergy entry (gold has no allergy)] | | |

**vital signs**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Heart rate (value=107, unit="bpm", reported_by="nurse") | SEG0004 person_1 nurse: "Here are the numbers, doctor. Heart rate 107, SpO2 97 percent on room air, blood pressure " | WRONG_ATTRIB: reported_by: gold="nurse" pred="person_1" (speaker id written instead of role) | CORRECT |
| Oxygen saturation (value=97, unit="%", reported_by="nurse") | SEG0004 person_1 nurse: "Here are the numbers, doctor. Heart rate 107, SpO2 97 percent on room air, blood pressure " | WRONG_ATTRIB: reported_by: gold="nurse" pred="person_1" (speaker id written instead of role) | CORRECT |
| Blood pressure (value="119/66", unit="mmHg", reported_by="nurse") | SEG0004 person_1 nurse: "Here are the numbers, doctor. Heart rate 107, SpO2 97 percent on room air, blood pressure " | WRONG_ATTRIB: reported_by: gold="nurse" pred="person_1" (speaker id written instead of role) | CORRECT |

**physical examination**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Tender submandibular lymph nodes (status="present", observed_by="doctor") | SEG0029 person_2 doctor: "The glands under the jaw are tender." | WRONG_NORM ('glands under the jaw are tender') | WRONG_NORM ('tender glands under the jaw') |
| Tonsillar enlargement and erythema (status="present", observed_by="doctor") | SEG0031 person_2 doctor: "Both tonsils are red and swollen, and there are white patches on the left one." | WRONG_NORM ('both tonsils are red and swollen and there are white patches on the left one') | WRONG_NORM ('red and swollen tonsils') |
| Tonsillar exudate (status="present", observed_by="doctor") | SEG0031 person_2 doctor: "Both tonsils are red and swollen, and there are white patches on the left one." | MISSED | WRONG_NORM ('white patches on the left tonsil') |

**review of systems**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| musculoskeletal (status="negative", reported_by="patient") | SEG0014 person_3 patient: "No, nothing there." | MISSED | MISSED |
| *(extra P00)* | respiratory [UNSUPPORTED] | | |
| *(extra P01)* | respiratory [UNSUPPORTED] | | |

**clinical conditions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | tonsillitis [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |
| *(extra P01)* | tonsillitis [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**clinical assessment**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Tonsillitis, probably bacterial (certainty="provisional", stated_by="doctor") | SEG0033 person_2 doctor: "Right, you can sit back down. So where does that leave us? My working impression is tonsil" | CORRECT | CORRECT |
| Viral throat infection (certainty="differential", stated_by="doctor") | SEG0033 person_2 doctor: "Right, you can sit back down. So where does that leave us? My working impression is tonsil" | MISSED | MISSED |

**investigations/procedures**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Throat swab culture (status="planned", type="laboratory") | SEG0035 person_2 doctor: "I can't promise yet, but most people with tonsillitis, probably bacterial do well once it'" | WRONG_NORM ('throat swab') | WRONG_NORM ('throat swab') |

**clinical actions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| investigation/arrange throat swab culture (status="planned", responsible_person="doctor") | SEG0035 person_2 doctor: "I can't promise yet, but most people with tonsillitis, probably bacterial do well once it'" | MISSED | MISSED |
| medication/start azithromycin 500 mg once a day (status="planned", responsible_person="doctor") | SEG0035 person_2 doctor: "I can't promise yet, but most people with tonsillitis, probably bacterial do well once it'" | MISSED | MISSED |
| counselling/advise completing antibiotic course (status="recommended", responsible_person="patient") | SEG0037 person_2 doctor: "Finish the whole course of antibiotics even if you feel better after two days." | MISSED | MISSED |
| counselling/advise reducing salt and fried food (status="recommended", responsible_person="patient") | SEG0038 person_2 doctor: "Right, right. Cut down on salt and fried food for now, it really does make a difference. D" | MISSED | MISSED |
| counselling/seek urgent care if you can t swallow your saliva or you have trouble breathing (status="recommended", responsible_person="patient") | SEG0038 person_2 doctor: "Right, right. Cut down on salt and fried food for now, it really does make a difference. D" | MISSED | MISSED |
| follow up/follow up consultation (status="planned", responsible_person="doctor") | SEG0038 person_2 doctor: "Right, right. Cut down on salt and fried food for now, it really does make a difference. D" | MISSED | MISSED |
| *(extra P00)* | follow up/see you again in a week [UNSUPPORTED]; counselling/cut down on salt and fried food for now it really does make a difference [UNSUPPORTED]; medication/azithromycin 500 mg once a day for three days [UNSUPPORTED]; investigation/throat swab [UNSUPPORTED] | | |
| *(extra P01)* | follow up/see you again in a week [UNSUPPORTED]; medication/azithromycin 500 mg once a day for three days [UNSUPPORTED]; investigation/throat swab [UNSUPPORTED] | | |

**follow up**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| consultation/in a week (status="planned", time_reference="in a week") | SEG0038 person_2 doctor: "Right, right. Cut down on salt and fried food for now, it really does make a difference. D" | MISSED | MISSED |
| *(extra P00)* | consultation/ [UNSUPPORTED] | | |
| *(extra P01)* | consultation/ [UNSUPPORTED] | | |

**clinical uncertainties**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | conflicting statement [UNSUPPORTED] | | |
| *(extra P01)* | conflicting statement [UNSUPPORTED] | | |

**Not applicable (no gold fact and no prediction):** none.

**Evidence (L).**
- P00: 1 evidence records; 0 are an exact single transcript segment; 25 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_multi_segment_or_whole_transcript_dump': 1, 'ev_empty_supports': 1, 'fact_path_missing_from_supports': 25, 'fact_not_mentioned_in_cited_text': 7}.
- P01: 1 evidence records; 1 are an exact single transcript segment; 25 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_empty_supports': 1, 'fact_not_mentioned_in_cited_text': 25, 'fact_cites_intro_segment_unrelated': 25, 'fact_path_missing_from_supports': 25}.

### Record 00168   (P00: FAILED, P01: FAILED)

**Speakers (A).** Transcript: person_1 nurse, person_2 doctor, person_3 patient. Gold primary speakers: person_1 nurse, person_2 doctor, person_3 patient.
- P00: no usable output.
- P01: no usable output.

**Chief complaint (B).** Gold: 'feeling faint' / normalized 'Presyncope' (reported by patient).
- P00: no usable output.
- P01: no usable output.

**symptoms**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Presyncope (status="present", temporality="current", certainty="certain") | SEG0003 person_3 patient: "Right, uh, I've been feeling faint, and I wanted to get it checked." | NO OUTPUT (record failed) | NO OUTPUT (record failed) |
| Headache (status="present", temporality="current", certainty="certain") | SEG0008 person_2 doctor: "Any a pounding headache as well?" | NO OUTPUT (record failed) | NO OUTPUT (record failed) |
| Nausea (status="resolved", temporality="resolved", certainty="certain") | SEG0009 person_3 patient: "Oh, um, yes, about the same, about two weeks. There was nausea, yes, but that went away." | NO OUTPUT (record failed) | NO OUTPUT (record failed) |

**negative findings**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Syncope (temporality="current", reported_by="patient") | SEG0010 person_2 doctor: "Have you noticed fainting or chest pain?" | NO OUTPUT (record failed) | NO OUTPUT (record failed) |
| Chest pain (temporality="current", reported_by="patient") | SEG0010 person_2 doctor: "Have you noticed fainting or chest pain?" | NO OUTPUT (record failed) | NO OUTPUT (record failed) |
| Anuria (temporality="current", reported_by="patient") | SEG0013 person_3 patient: "Hmm, I haven't had passing no urine, vomiting, confusion or fever, no." | NO OUTPUT (record failed) | NO OUTPUT (record failed) |
| Vomiting (temporality="current", reported_by="patient") | SEG0013 person_3 patient: "Hmm, I haven't had passing no urine, vomiting, confusion or fever, no." | NO OUTPUT (record failed) | NO OUTPUT (record failed) |
| Confusion (temporality="current", reported_by="patient") | SEG0013 person_3 patient: "Hmm, I haven't had passing no urine, vomiting, confusion or fever, no." | NO OUTPUT (record failed) | NO OUTPUT (record failed) |
| Fever (temporality="current", reported_by="patient") | SEG0013 person_3 patient: "Hmm, I haven't had passing no urine, vomiting, confusion or fever, no." | NO OUTPUT (record failed) | NO OUTPUT (record failed) |
| No known allergies (temporality="current", reported_by="patient") | SEG0016 person_2 doctor: "Do you have any known allergies at all?" | NO OUTPUT (record failed) | NO OUTPUT (record failed) |

**past medical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Hypertension (status="ongoing", reported_by="patient") | SEG0021 person_3 patient: "I've had high blood pressure, yes. Okay, so I've had arthritis in my knees for five years " | NO OUTPUT (record failed) | NO OUTPUT (record failed) |
| Osteoarthritis of the knee (status="ongoing", reported_by="patient") | SEG0021 person_3 patient: "I've had high blood pressure, yes. Okay, so I've had arthritis in my knees for five years " | NO OUTPUT (record failed) | NO OUTPUT (record failed) |

**surgical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Cholecystectomy (reported_by="patient") | SEG0024 person_3 patient: "hmm, yes, I had my gallbladder removed, in 2016" | NO OUTPUT (record failed) | NO OUTPUT (record failed) |

**social history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| alcohol (status="never", reported_by="patient") | SEG0019 person_3 patient: "I don't drink at all. Yes, I live on my own. I work night shifts at a warehouse" | NO OUTPUT (record failed) | NO OUTPUT (record failed) |
| living (status="current", reported_by="patient") | SEG0018 person_2 doctor: "now some background about your lifestyle" | NO OUTPUT (record failed) | NO OUTPUT (record failed) |
| occupation (status="current", reported_by="patient") | SEG0019 person_3 patient: "I don't drink at all. Yes, I live on my own. I work night shifts at a warehouse" | NO OUTPUT (record failed) | NO OUTPUT (record failed) |

**medications**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Ramipril (frequency="every morning", status="currently_used", reported_by="patient") | SEG0026 person_3 patient: "Ramipril. I take it 5 milligrams, every morning." | NO OUTPUT (record failed) | NO OUTPUT (record failed) |
| Paracetamol (dose="650 mg", frequency="when needed", status="currently_used") | SEG0029 person_3 patient: "so, I don't think I have it with me. Paracetamol. I take it 650 milligrams, when needed fo" | NO OUTPUT (record failed) | NO OUTPUT (record failed) |
| ORS (dose="1 sachet", route="oral", frequency="three times a day") | SEG0031 person_2 doctor: "Good, thank you. Listening to the whole story, I'd lean towards heat exhaustion with some " | NO OUTPUT (record failed) | NO OUTPUT (record failed) |

**vital signs**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Blood pressure (value="100/62", unit="mmHg", reported_by="nurse") | SEG0030 person_1 nurse: "Okay, so the vitals from earlier. Pressure 100 over 62, pulse 93, respiratory rate 19." | NO OUTPUT (record failed) | NO OUTPUT (record failed) |
| Heart rate (value=93, unit="bpm", reported_by="nurse") | SEG0030 person_1 nurse: "Okay, so the vitals from earlier. Pressure 100 over 62, pulse 93, respiratory rate 19." | NO OUTPUT (record failed) | NO OUTPUT (record failed) |
| Respiratory rate (value=19, unit="breaths/min", reported_by="nurse") | SEG0030 person_1 nurse: "Okay, so the vitals from earlier. Pressure 100 over 62, pulse 93, respiratory rate 19." | NO OUTPUT (record failed) | NO OUTPUT (record failed) |

**review of systems**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| respiratory (status="negative", reported_by="patient") | SEG0015 person_3 patient: "breathing's normal" | NO OUTPUT (record failed) | NO OUTPUT (record failed) |

**clinical conditions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Osteoarthritis of the knee (status="existing", reported_by="patient") | SEG0021 person_3 patient: "I've had high blood pressure, yes. Okay, so I've had arthritis in my knees for five years " | NO OUTPUT (record failed) | NO OUTPUT (record failed) |

**clinical assessment**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Heat exhaustion with some dehydration (certainty="provisional", stated_by="doctor") | SEG0031 person_2 doctor: "Good, thank you. Listening to the whole story, I'd lean towards heat exhaustion with some " | NO OUTPUT (record failed) | NO OUTPUT (record failed) |
| Electrolyte imbalance (certainty="differential", stated_by="doctor") | SEG0031 person_2 doctor: "Good, thank you. Listening to the whole story, I'd lean towards heat exhaustion with some " | NO OUTPUT (record failed) | NO OUTPUT (record failed) |

**investigations/procedures**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Serum electrolytes (status="planned", type="laboratory") | SEG0031 person_2 doctor: "Good, thank you. Listening to the whole story, I'd lean towards heat exhaustion with some " | NO OUTPUT (record failed) | NO OUTPUT (record failed) |

**clinical actions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| investigation/arrange serum electrolytes (status="planned", responsible_person="doctor") | SEG0031 person_2 doctor: "Good, thank you. Listening to the whole story, I'd lean towards heat exhaustion with some " | NO OUTPUT (record failed) | NO OUTPUT (record failed) |
| medication/start oral rehydration salts 1 sachet three times a day (status="planned", responsible_person="doctor") | SEG0031 person_2 doctor: "Good, thank you. Listening to the whole story, I'd lean towards heat exhaustion with some " | NO OUTPUT (record failed) | NO OUTPUT (record failed) |
| counselling/advise avoiding midday sun (status="recommended", responsible_person="patient") | SEG0031 person_2 doctor: "Good, thank you. Listening to the whole story, I'd lean towards heat exhaustion with some " | NO OUTPUT (record failed) | NO OUTPUT (record failed) |
| other/bring latest prescription or medication box to next visit (status="recommended", responsible_person="patient") | SEG0032 person_2 doctor: "understood and please bring the latest prescription or the medicine boxes to the next visi" | NO OUTPUT (record failed) | NO OUTPUT (record failed) |
| counselling/seek urgent care if you become confused or stop sweating (status="recommended", responsible_person="patient") | SEG0034 person_2 doctor: "Keep an eye out, and if you become confused or stop sweating, call us the same day or go t" | NO OUTPUT (record failed) | NO OUTPUT (record failed) |
| follow up/follow up consultation (status="planned", responsible_person="doctor") | SEG0034 person_2 doctor: "Keep an eye out, and if you become confused or stop sweating, call us the same day or go t" | NO OUTPUT (record failed) | NO OUTPUT (record failed) |

**follow up**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| consultation/in three days (status="planned", time_reference="in three days") | SEG0034 person_2 doctor: "Keep an eye out, and if you become confused or stop sweating, call us the same day or go t" | NO OUTPUT (record failed) | NO OUTPUT (record failed) |

**clinical uncertainties**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| medication_discrepancy (resolution_status="unresolved") | SEG0026 person_3 patient: "Ramipril. I take it 5 milligrams, every morning." | NO OUTPUT (record failed) | NO OUTPUT (record failed) |

**Not applicable (no gold fact and no prediction):** family history, allergies, physical examination.

**Evidence (L).**
- P00: no usable output.
- P01: no usable output.

### Record 00182   (P00: parsed, P01: parsed)

**Speakers (A).** Transcript: person_1 doctor, person_2 patient. Gold primary speakers: person_1 doctor, person_2 patient.
- P00: predicted [('person_1', 'doctor')]; all speakers+roles correct: False; missing [('person_2', 'patient')]; wrong role none; invented ids none.
- P01: predicted [('person_1', 'doctor')]; all speakers+roles correct: False; missing [('person_2', 'patient')]; wrong role none; invented ids none.

**Chief complaint (B).** Gold: 'cramping pain in the lower tummy' / normalized 'Lower abdominal cramping' (reported by patient).
- P00: 'It's cramping pain in the lower tummy. I thought I'd wait, but it hasn't gone.' / normalized 'It's cramping pain in the lower tummy. I thought I'd wait, but it hasn't gone.' (reported_by patient) -> WRONG_NORM ('it s cramping pain in the lower tummy i thought i d wait but it hasn t gone')
- P01: 'It's cramping pain in the lower tummy. I thought I'd wait, but it hasn't gone.' / normalized 'It's cramping pain in the lower tummy. I thought I'd wait, but it hasn't gone.' (reported_by patient) -> WRONG_NORM ('it s cramping pain in the lower tummy i thought i d wait but it hasn t gone')

**symptoms**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Lower abdominal cramping (status="present", temporality="current", certainty="certain") | SEG0004 person_2 patient: "It's cramping pain in the lower tummy. I thought I'd wait, but it hasn't gone." | WRONG_NORM ('Abdominal cramping') | WRONG_NORM ('Abdominal cramping') |
| Altered bowel habit (status="present", temporality="current", certainty="certain") | SEG0006 person_2 patient: "It's worse with stress and certain foods. I've had alternating constipation and loose stoo" | WRONG_NORM ('alternating constipation and loose stools') | WRONG_NORM ('alternating constipation and loose stools') |
| Bloating (status="present", temporality="current", certainty="certain") | SEG0006 person_2 patient: "It's worse with stress and certain foods. I've had alternating constipation and loose stoo" | WRONG_STATUS: temporality: gold="current" pred="resolved"; duration: gold={"value": 6, "unit": "months", "normaliz pred={"value": null, "unit": null, "normalize | PARTIAL: duration: gold={"value": 6, "unit": "months", "normaliz pred={"value": null, "unit": null, "normalize |

**negative findings**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Nocturnal diarrhoea (temporality="current", reported_by="patient") | SEG0015 person_2 patient: "No night-time diarrhoea, anaemia, fever or blood in the stool, none of it." | MISSED | MISSED |
| Anaemia (temporality="current", reported_by="patient") | SEG0015 person_2 patient: "No night-time diarrhoea, anaemia, fever or blood in the stool, none of it." | MISSED | MISSED |
| Fever (temporality="current", reported_by="patient") | SEG0015 person_2 patient: "No night-time diarrhoea, anaemia, fever or blood in the stool, none of it." | WRONG_NORM ('no fever') | WRONG_NORM ('no fever') |
| Blood in stool (temporality="current", reported_by="patient") | SEG0015 person_2 patient: "No night-time diarrhoea, anaemia, fever or blood in the stool, none of it." | MISSED | MISSED |
| No known allergies (temporality="current", reported_by="patient") | SEG0021 person_2 patient: "No allergies." | WRONG_NORM ('no allergies') | WRONG_NORM ('no allergies') |
| *(extra P01)* | no previous surgery [UNSUPPORTED] | | |

**past medical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Anxiety disorder (status="ongoing", reported_by="patient") | SEG0037 person_2 patient: "I have anxiety, for nearly five years." | MISSED | MISSED |
| *(extra P00)* | irritable bowel syndrome [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |
| *(extra P01)* | knee arthroscopy [INCORRECT - gold has this fact in category 'surgical history'] | | |

**surgical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Knee arthroscopy (reported_by="patient") | SEG0019 person_2 patient: "I had a knee arthroscopy three years ago. I did try to ignore it for a while." | CORRECT | CORRECT |

**family history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Kidney stones (relation="father", reported_by="patient") | SEG0023 person_2 patient: "My father had kidney stones." | CORRECT | CORRECT |

**social history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| alcohol (status="never", reported_by="patient") | SEG0029 person_2 patient: "I don't drink at all." | MISSED | MISSED |
| occupation (status="current", reported_by="patient") | SEG0031 person_2 patient: "I run a small shop, so I'm on my feet a lot." | WRONG_STATUS: status: gold="current" pred="" | WRONG_STATUS: status: gold="current" pred="" |
| diet (status="current", reported_by="patient") | SEG0033 person_2 patient: "Mostly home-cooked food, rice and vegetables." | MISSED | WRONG_STATUS: status: gold="current" pred="" |
| exercise (status="none", reported_by="patient") | SEG0035 person_2 patient: "Barely, I'm mostly sedentary these days." | MISSED | MISSED |
| *(extra P01)* | lifestyle [UNSUPPORTED] | | |

**medications**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Escitalopram (dose="10 mg", frequency="once a day", status="currently_used") | SEG0025 person_2 patient: "Right, it's escitalopram, 10 milligrams, once a day." | UNSUPPORTED: route: not in gold, pred="oral" | UNSUPPORTED: route: not in gold, pred="oral" |
| Mebeverine (dose="135 mg", route="oral", frequency="three times a day") | SEG0042 person_1 doctor: "Let's use mebeverine, 135 milligrams, three times a day, for four weeks. You take it by mo" | MISSED | MISSED |

**allergies**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | no allergies [INCORRECT - placeholder written as an allergy entry (gold has no allergy)] | | |
| *(extra P01)* | escitalopram [INCORRECT - a medication from the medication list written as an allergy] | | |

**vital signs**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Heart rate (value=84, unit="bpm", reported_by="doctor") | SEG0009 person_1 doctor: "Okay: heart rate 84, oxygen saturation is 98 percent, BP is 118 over 81, respiratory rate " | CORRECT | CORRECT |
| Oxygen saturation (value=98, unit="%", reported_by="doctor") | SEG0009 person_1 doctor: "Okay: heart rate 84, oxygen saturation is 98 percent, BP is 118 over 81, respiratory rate " | CORRECT | CORRECT |
| Blood pressure (value="118/81", unit="mmHg", reported_by="doctor") | SEG0009 person_1 doctor: "Okay: heart rate 84, oxygen saturation is 98 percent, BP is 118 over 81, respiratory rate " | CORRECT | CORRECT |
| Respiratory rate (value=18, unit="breaths/min", reported_by="doctor") | SEG0009 person_1 doctor: "Okay: heart rate 84, oxygen saturation is 98 percent, BP is 118 over 81, respiratory rate " | PARTIAL: unit: gold="breaths/min" pred="breaths per minute" | PARTIAL: unit: gold="breaths/min" pred="breaths per minute" |

**physical examination**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Left iliac fossa tenderness (status="present", observed_by="doctor") | SEG0012 person_1 doctor: "Soft tummy, a bit tender on the left lower side, no masses." | WRONG_NORM ('tender on the left lower side') | WRONG_NORM ('tender on the left lower side') |
| No abdominal mass (status="absent", observed_by="doctor") | SEG0012 person_1 doctor: "Soft tummy, a bit tender on the left lower side, no masses." | MISSED | MISSED |
| *(extra P00)* | soft tummy [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |
| *(extra P01)* | soft tummy [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**review of systems**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| genitourinary (status="negative", reported_by="patient") | SEG0017 person_2 patient: "Hmm, no, that's all fine." | MISSED | MISSED |
| *(extra P00)* | gastrointestinal [UNSUPPORTED] | | |
| *(extra P01)* | gastrointestinal [UNSUPPORTED] | | |

**clinical conditions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | irritable bowel syndrome [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |
| *(extra P01)* | coeliac disease [INCORRECT - gold has this fact in category 'clinical assessment']; irritable bowel syndrome [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**clinical assessment**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Irritable bowel syndrome as a working diagnosis (certainty="provisional", stated_by="doctor") | SEG0039 person_1 doctor: "Having listened and examined, this is probably irritable bowel syndrome as a working diagn" | CORRECT | WRONG_NORM ('Probably irritable bowel syndrome as a working diagnosis.') |
| Coeliac disease (certainty="differential", stated_by="doctor") | SEG0039 person_1 doctor: "Having listened and examined, this is probably irritable bowel syndrome as a working diagn" | MISSED | MISSED |

**investigations/procedures**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Tissue transglutaminase antibody (status="planned", type="laboratory") | SEG0041 person_1 doctor: "Nothing I've seen today points to an emergency. It looks like irritable bowel syndrome as " | MISSED | MISSED |
| Faecal calprotectin (status="planned", type="laboratory") | SEG0041 person_1 doctor: "Nothing I've seen today points to an emergency. It looks like irritable bowel syndrome as " | WRONG_NORM ('stool calprotectin') | WRONG_NORM ('stool calprotectin') |
| *(extra P01)* | mebeverine [INCORRECT - gold has this fact in category 'medications'] | | |

**clinical actions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| investigation/arrange tissue transglutaminase antibody (status="planned", responsible_person="doctor") | SEG0041 person_1 doctor: "Nothing I've seen today points to an emergency. It looks like irritable bowel syndrome as " | MISSED | MISSED |
| investigation/arrange faecal calprotectin (status="planned", responsible_person="doctor") | SEG0041 person_1 doctor: "Nothing I've seen today points to an emergency. It looks like irritable bowel syndrome as " | MISSED | MISSED |
| medication/start mebeverine 135 mg three times a day (status="planned", responsible_person="doctor") | SEG0042 person_1 doctor: "Let's use mebeverine, 135 milligrams, three times a day, for four weeks. You take it by mo" | WRONG_NORM ('medication/take mebeverine 135 mg three times a day for four weeks') | WRONG_NORM ('medication/take mebeverine 135 mg three times a day') |
| counselling/advise regular meals and fibre (status="recommended", responsible_person="patient") | SEG0044 person_1 doctor: "Regular meals and a bit more fibre, and don't rush your toilet time. Note down what you at" | MISSED | MISSED |
| counselling/advise food diary (status="recommended", responsible_person="patient") | SEG0044 person_1 doctor: "Regular meals and a bit more fibre, and don't rush your toilet time. Note down what you at" | MISSED | MISSED |
| counselling/seek urgent care if the symptoms get worse (status="recommended", responsible_person="patient") | SEG0044 person_1 doctor: "Regular meals and a bit more fibre, and don't rush your toilet time. Note down what you at" | MISSED | MISSED |
| *(extra P00)* | counselling/note down what you ate before the bad days it often reveals a pattern [UNSUPPORTED] | | |
| *(extra P01)* | counselling/note down what you ate before the bad days it often reveals a pattern [UNSUPPORTED]; follow up/call us if anything changes [UNSUPPORTED] | | |

**follow up**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | consultation/ [UNSUPPORTED] | | |
| *(extra P01)* | follow up/ [UNSUPPORTED] | | |

**clinical uncertainties**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | conflicting statement [UNSUPPORTED] | | |
| *(extra P01)* | date uncertain [UNSUPPORTED] | | |

**Not applicable (no gold fact and no prediction):** none.

**Evidence (L).**
- P00: 1 evidence records; 0 are an exact single transcript segment; 26 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_multi_segment_or_whole_transcript_dump': 1, 'ev_empty_supports': 1, 'fact_path_missing_from_supports': 26, 'fact_not_mentioned_in_cited_text': 6}.
- P01: 1 evidence records; 1 are an exact single transcript segment; 32 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_wrong_speaker_id': 1, 'ev_wrong_or_empty_speaker_role': 1, 'ev_empty_supports': 1, 'fact_path_missing_from_supports': 6, 'fact_not_mentioned_in_cited_text': 4, 'fact_no_evidence_ids': 26}.

### Record 00187   (P00: parsed, P01: parsed)

**Speakers (A).** Transcript: person_1 doctor, person_2 patient, person_3 nurse. Gold primary speakers: person_1 doctor, person_2 patient, person_3 nurse.
- P00: predicted [('person_1', 'doctor')]; all speakers+roles correct: False; missing [('person_2', 'patient'), ('person_3', 'nurse')]; wrong role none; invented ids none.
- P01: predicted [('person_1', 'doctor'), ('person_2', 'patient')]; all speakers+roles correct: False; missing [('person_3', 'nurse')]; wrong role none; invented ids none.

**Chief complaint (B).** Gold: 'thump in the chest at night' / normalized 'Nocturnal palpitations' (reported by patient).
- P00: 'I wanted to get a thump in the chest at night looked at.' / normalized 'I wanted to get a thump in the chest at night looked at.' (reported_by patient) -> WRONG_NORM ('i wanted to get a thump in the chest at night looked at')
- P01: 'I wanted to get a thump in the chest at night looked at.' / normalized 'I wanted to get a thump in the chest at night looked at.' (reported_by patient) -> WRONG_NORM ('i wanted to get a thump in the chest at night looked at')

**symptoms**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Nocturnal palpitations (status="present", temporality="current", certainty="certain") | SEG0004 person_2 patient: "I wanted to get a thump in the chest at night looked at. My family kept telling me to get " | WRONG_NORM ('chest thump') | WRONG_NORM ('chest thump') |
| Anxiety (status="present", temporality="current", certainty="certain") | SEG0008 person_2 patient: "Okay, so it feels mild to me. It happens all the time. I looked a few things up online, an" | MISSED | MISSED |
| Insomnia (status="present", temporality="current", certainty="certain") | SEG0009 person_1 doctor: "Has there been poor sleep too?" | MISSED | MISSED |
| Palpitations (skipped beats) (status="resolved", temporality="resolved", certainty="certain") | SEG0014 person_2 patient: "I did have skipped beats at one point, but that's gone now." | MISSED | MISSED |

**negative findings**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| No known allergies (temporality="current", reported_by="patient") | SEG0015 person_1 doctor: "Do you have any known allergies at all?" | WRONG_NORM ('no allergies') | WRONG_NORM ('no allergies') |
| No previous surgery (temporality="past", reported_by="patient") | SEG0022 person_1 doctor: "Have you had any previous surgeries?" | WRONG_STATUS: temporality: gold="past" pred="current" | WRONG_STATUS: temporality: gold="past" pred="current" |
| Family history of sudden death (temporality="current", reported_by="patient") | SEG0035 person_2 patient: "I haven't noticed any family history of sudden death." | MISSED | MISSED |
| Energy drink use (temporality="current", reported_by="patient") | SEG0036 person_1 doctor: "Have you noticed energy drinks, fainting or chest pain?" | MISSED | MISSED |
| Syncope (temporality="current", reported_by="patient") | SEG0036 person_1 doctor: "Have you noticed energy drinks, fainting or chest pain?" | MISSED | MISSED |
| Chest pain (temporality="current", reported_by="patient") | SEG0036 person_1 doctor: "Have you noticed energy drinks, fainting or chest pain?" | MISSED | MISSED |
| *(extra P00)* | no fever [UNSUPPORTED] | | |
| *(extra P01)* | no fever [UNSUPPORTED] | | |

**past medical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Anxiety disorder (status="ongoing", reported_by="patient") | SEG0029 person_2 patient: "I have anxiety." | WRONG_NORM ('anxiety') | WRONG_NORM ('anxiety') |
| Hypothyroidism (status="ongoing", reported_by="patient") | SEG0031 person_2 patient: "I've got an underactive thyroid." | MISSED | MISSED |
| Atrial fibrillation (status="ongoing", reported_by="patient") | SEG0033 person_2 patient: "I've had an irregular heartbeat for nearly five years now." | MISSED | MISSED |

**surgical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | no operations [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |
| *(extra P01)* | irregular heartbeat [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**family history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Asthma (relation="brother", reported_by="patient") | SEG0025 person_2 patient: "My brother has asthma." | CORRECT | CORRECT |

**social history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| alcohol (status="current", reported_by="patient") | SEG0026 person_1 doctor: "Let's talk a little about your daily life and habits." | MISSED | MISSED |
| exercise (status="current", reported_by="patient") | SEG0026 person_1 doctor: "Let's talk a little about your daily life and habits." | MISSED | WRONG_STATUS: status: gold="current" pred="ongoing" |
| occupation (status="current", reported_by="patient") | SEG0027 person_2 patient: "I have a couple of drinks on the weekend. I cycle to work most mornings. I teach at a prim" | MISSED | MISSED |
| living (status="current", reported_by="patient") | SEG0026 person_1 doctor: "Let's talk a little about your daily life and habits." | MISSED | WRONG_STATUS: status: gold="current" pred="ongoing" |
| *(extra P00)* | lifestyle [UNSUPPORTED] | | |
| *(extra P01)* | work [EXTRA_SUPPORTED_BY_TRANSCRIPT]; drinking [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**medications**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Escitalopram (dose="10 mg", frequency="once a day", status="currently_used") | SEG0018 person_2 patient: "Hmm, it's escitalopram, 10 milligrams, once a day for the anxiety. Thyroxine, 75 microgram" | UNSUPPORTED: route: not in gold, pred="oral" | UNSUPPORTED: route: not in gold, pred="oral" |
| Levothyroxine (frequency="every morning", status="currently_used", reported_by="patient") | SEG0018 person_2 patient: "Hmm, it's escitalopram, 10 milligrams, once a day for the anxiety. Thyroxine, 75 microgram" | WRONG_NORM ('thyroxine') | WRONG_NORM ('thyroxine') |
| Apixaban (dose="5 mg", frequency="twice a day", status="currently_used") | SEG0021 person_2 patient: "Not with me. I'll bring it next time. Well, I'm on apixaban, 5 milligrams, twice a day." | UNSUPPORTED: route: not in gold, pred="oral" | UNSUPPORTED: route: not in gold, pred="oral" |

**allergies**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | no known medication allergies [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |
| *(extra P01)* | medication [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**vital signs**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Body temperature (value=37.0, unit="°C", reported_by="nurse") | SEG0040 person_3 nurse: "Okay, so the vitals from earlier. Temp 37.0 degrees, pressure 110 over 74, saturation 98 p" | MISSED | MISSED |
| Blood pressure (value="110/74", unit="mmHg", reported_by="nurse") | SEG0040 person_3 nurse: "Okay, so the vitals from earlier. Temp 37.0 degrees, pressure 110 over 74, saturation 98 p" | WRONG_ATTRIB: reported_by: gold="nurse" pred="doctor" | WRONG_ATTRIB: reported_by: gold="nurse" pred="doctor" |
| Oxygen saturation (value=98, unit="%", reported_by="nurse") | SEG0040 person_3 nurse: "Okay, so the vitals from earlier. Temp 37.0 degrees, pressure 110 over 74, saturation 98 p" | WRONG_NORM ('saturation') | WRONG_NORM ('saturation') |
| Heart rate (value=82, unit="bpm", reported_by="nurse") | SEG0040 person_3 nurse: "Okay, so the vitals from earlier. Temp 37.0 degrees, pressure 110 over 74, saturation 98 p" | MISSED | MISSED |
| *(extra P00)* | pulse [EXTRA_SUPPORTED_BY_TRANSCRIPT]; temperature [UNSUPPORTED] | | |
| *(extra P01)* | pulse [EXTRA_SUPPORTED_BY_TRANSCRIPT]; temperature [UNSUPPORTED] | | |

**physical examination**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| No cardiac murmur (status="absent", observed_by="doctor") | SEG0044 person_1 doctor: "Heart sounds are normal with no murmur." | WRONG_NORM ('heart sounds are normal with no murmur') | MISSED |
| Occasional ectopic beats (status="present", observed_by="doctor") | SEG0046 person_1 doctor: "Pulse is regular at the moment, with a couple of early beats while I listened." | MISSED | MISSED |
| *(extra P01)* | normal heart sounds [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**review of systems**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| musculoskeletal (status="negative", reported_by="patient") | SEG0039 person_2 patient: "Nothing else aches." | MISSED | MISSED |
| *(extra P00)* | cardiovascular [UNSUPPORTED] | | |
| *(extra P01)* | cardiovascular [UNSUPPORTED] | | |

**clinical conditions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Anxiety disorder (status="existing", reported_by="patient") | SEG0029 person_2 patient: "I have anxiety." | MISSED | MISSED |
| *(extra P00)* | benign extra heartbeats [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |
| *(extra P01)* | benign extra heartbeats [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**clinical assessment**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Benign extra heartbeats, though we should confirm (certainty="provisional", stated_by="doctor") | SEG0047 person_1 doctor: "That's fine, sit up. Okay, so my impression is this: I'd lean towards benign extra heartbe" | WRONG_NORM ('i d lean towards benign extra heartbeats though we should confirm') | WRONG_NORM ('i d lean towards benign extra heartbeats though we should confirm') |
| Rhythm problem (certainty="differential", stated_by="doctor") | SEG0047 person_1 doctor: "That's fine, sit up. Okay, so my impression is this: I'd lean towards benign extra heartbe" | MISSED | MISSED |

**investigations/procedures**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Thyroid function test (status="completed", type="laboratory") | SEG0052 person_2 patient: "I had a thyroid test done at another clinic last year. I don't have the report with me." | WRONG_NORM ('thyroid test') | WRONG_NORM ('thyroid test') |

**clinical actions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| counselling/caffeine reduction trial (status="recommended", responsible_person="patient") | SEG0053 person_1 doctor: "Try cutting out caffeine for two weeks and see if the beats settle. And please bring the l" | MISSED | MISSED |
| other/bring latest prescription or medication box to next visit (status="recommended", responsible_person="patient") | SEG0053 person_1 doctor: "Try cutting out caffeine for two weeks and see if the beats settle. And please bring the l" | MISSED | MISSED |
| follow up/follow up consultation (status="planned", responsible_person="doctor") | SEG0055 person_1 doctor: "I'll want another look in four weeks." | MISSED | MISSED |
| *(extra P00)* | follow up/i ll want another look in four weeks [UNSUPPORTED] | | |
| *(extra P01)* | follow up/i ll want another look in four weeks [UNSUPPORTED] | | |

**follow up**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| consultation/in four weeks (status="planned", time_reference="in four weeks") | SEG0055 person_1 doctor: "I'll want another look in four weeks." | WRONG_NORM ('consultation/four weeks') | WRONG_NORM ('consultation/four weeks') |

**clinical uncertainties**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| medication_discrepancy (resolution_status="unresolved") | SEG0018 person_2 patient: "Hmm, it's escitalopram, 10 milligrams, once a day for the anxiety. Thyroxine, 75 microgram" | MISSED | MISSED |
| *(extra P00)* | date uncertain [UNSUPPORTED] | | |
| *(extra P01)* | date uncertain [UNSUPPORTED] | | |

**Not applicable (no gold fact and no prediction):** none.

**Evidence (L).**
- P00: 3 evidence records; 2 are an exact single transcript segment; 25 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_empty_supports': 3, 'ev_text_not_in_transcript': 1, 'fact_path_missing_from_supports': 9, 'fact_no_evidence_ids': 15, 'fact_not_mentioned_in_cited_text': 3, 'fact_dangling_evidence_id': 1}.
- P01: 1 evidence records; 1 are an exact single transcript segment; 28 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_empty_supports': 1, 'fact_path_missing_from_supports': 4, 'fact_no_evidence_ids': 24, 'fact_not_mentioned_in_cited_text': 2}.

### Record 00189   (P00: parsed, P01: parsed)

**Speakers (A).** Transcript: person_1 patient, person_2 doctor, person_3 clinical_staff. Gold primary speakers: person_1 patient, person_2 doctor, person_3 clinical_staff.
- P00: predicted [('person_1', 'patient'), ('person_2', 'doctor')]; all speakers+roles correct: False; missing [('person_3', 'clinical_staff')]; wrong role none; invented ids none.
- P01: predicted [('person_1', 'patient'), ('person_2', 'doctor')]; all speakers+roles correct: False; missing [('person_3', 'clinical_staff')]; wrong role none; invented ids none.

**Chief complaint (B).** Gold: 'dry cough that won't go away' / normalized 'Chronic cough' (reported by patient).
- P00: 'dry cough that won't go away' / normalized 'dry cough that won't go away' (reported_by person_1) -> WRONG_NORM ('dry cough that won t go away')
- P01: 'dry cough that won't go away' / normalized 'dry cough that won't go away' (reported_by person_1) -> WRONG_NORM ('dry cough that won t go away')

**symptoms**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Chronic cough (status="present", temporality="current", certainty="certain") | SEG0003 person_1 patient: "Yeah, it's a dry cough that won't go away. I thought I'd wait, but it hasn't gone. I took " | WRONG_NORM ('cough') | WRONG_NORM ('cough') |
| Throat clearing (status="present", temporality="current", certainty="certain") | SEG0008 person_2 doctor: "Have you been clearing your throat all the time?" | MISSED | MISSED |

**negative findings**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Night sweats (temporality="current", reported_by="patient") | SEG0010 person_2 doctor: "Any night sweats?" | MISSED | MISSED |
| Weight loss (temporality="current", reported_by="patient") | SEG0012 person_2 doctor: "And what about weight loss, wheezing or shortness of breath?" | MISSED | MISSED |
| Wheeze (temporality="current", reported_by="patient") | SEG0012 person_2 doctor: "And what about weight loss, wheezing or shortness of breath?" | MISSED | MISSED |
| Shortness of breath (temporality="current", reported_by="patient") | SEG0012 person_2 doctor: "And what about weight loss, wheezing or shortness of breath?" | MISSED | MISSED |
| No known allergies (temporality="current", reported_by="patient") | SEG0019 person_1 patient: "No allergies that I know of, no." | MISSED | MISSED |

**past medical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Gastro-oesophageal reflux disease (status="ongoing", reported_by="patient") | SEG0021 person_1 patient: "Yes, acid reflux. I have high blood pressure. I have heart disease." | WRONG_NORM ('acid reflux') | WRONG_NORM ('acid reflux') |
| Hypertension (status="ongoing", reported_by="patient") | SEG0021 person_1 patient: "Yes, acid reflux. I have high blood pressure. I have heart disease." | WRONG_NORM ('high blood pressure') | WRONG_NORM ('high blood pressure') |
| Ischaemic heart disease (status="ongoing", reported_by="patient") | SEG0021 person_1 patient: "Yes, acid reflux. I have high blood pressure. I have heart disease." | MISSED | MISSED |

**surgical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Coronary stenting (reported_by="patient") | SEG0017 person_1 patient: "yeah, just a stent put in my heart, two years ago" | WRONG_NORM ('stent put in my heart') | WRONG_NORM ('stent put in my heart') |

**family history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Hypertension (relation="mother", reported_by="patient") | SEG0024 person_1 patient: "My mother had high blood pressure." | WRONG_NORM ('high blood pressure') | WRONG_NORM ('high blood pressure') |

**social history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| exercise (status="current", reported_by="patient") | SEG0026 person_1 patient: "I play badminton on Sundays. Yes, I live on my own. I try to avoid too much sugar." | MISSED | MISSED |
| living (status="current", reported_by="patient") | SEG0025 person_2 doctor: "Tell me about your routine, work, habits, that sort of thing." | MISSED | MISSED |
| diet (status="current", reported_by="patient") | SEG0026 person_1 patient: "I play badminton on Sundays. Yes, I live on my own. I try to avoid too much sugar." | MISSED | MISSED |
| *(extra P00)* | lifestyle [UNSUPPORTED] | | |
| *(extra P01)* | lifestyle [UNSUPPORTED] | | |

**medications**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Ramipril (dose="5 mg", frequency="every morning", status="currently_used") | SEG0005 person_1 patient: "Ramipril. I take it 5 milligrams, every morning for my blood pressure. A neighbour of mine" | WRONG_ATTRIB: reported_by: gold="patient" pred="person_1" (speaker id written instead of role) | WRONG_ATTRIB: route: not in gold, pred="oral"; reported_by: gold="patient" pred="person_1" (speaker id written instead of role) |
| Aspirin (dose="75 mg", frequency="once a day", status="currently_used") | SEG0005 person_1 patient: "Ramipril. I take it 5 milligrams, every morning for my blood pressure. A neighbour of mine" | WRONG_ATTRIB: reported_by: gold="patient" pred="person_1" (speaker id written instead of role) | WRONG_ATTRIB: route: not in gold, pred="oral"; reported_by: gold="patient" pred="person_1" (speaker id written instead of role) |
| Pantoprazole (dose="40 mg", frequency="before breakfast", status="planned") | SEG0040 person_2 doctor: "What I'm giving you is pantoprazole, 40 milligrams, before breakfast, for four weeks. That" | WRONG_STATUS: status: gold="planned" pred="currently_used"; reported_by: gold="doctor" pred="person_1" (speaker id written instead of role) | MISSED |

**vital signs**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Body temperature (value=36.7, unit="°C", reported_by="doctor") | SEG0029 person_2 doctor: "Okay: temperature is 36.7 degrees, oxygen saturation is 98 percent, heart rate 85. And blo" | WRONG_NORM ('temperature') | WRONG_NORM ('temperature') |
| Oxygen saturation (value=98, unit="%", reported_by="doctor") | SEG0029 person_2 doctor: "Okay: temperature is 36.7 degrees, oxygen saturation is 98 percent, heart rate 85. And blo" | WRONG_ATTRIB: reported_by: gold="doctor" pred="person_2" (speaker id written instead of role) | WRONG_ATTRIB: reported_by: gold="doctor" pred="person_1" (speaker id written instead of role) |
| Heart rate (value=85, unit="bpm", reported_by="doctor") | SEG0029 person_2 doctor: "Okay: temperature is 36.7 degrees, oxygen saturation is 98 percent, heart rate 85. And blo" | MISSED | MISSED |
| Blood pressure (value="111/76", unit="mmHg", reported_by="doctor") | SEG0029 person_2 doctor: "Okay: temperature is 36.7 degrees, oxygen saturation is 98 percent, heart rate 85. And blo" | WRONG_ATTRIB: reported_by: gold="doctor" pred="person_2" (speaker id written instead of role) | WRONG_ATTRIB: reported_by: gold="doctor" pred="person_1" (speaker id written instead of role) |
| Respiratory rate (value=18, unit="breaths/min", reported_by="doctor") | SEG0029 person_2 doctor: "Okay: temperature is 36.7 degrees, oxygen saturation is 98 percent, heart rate 85. And blo" | WRONG_ATTRIB: unit: gold="breaths/min" pred="per minute"; reported_by: gold="doctor" pred="person_2" (speaker id written instead of role) | WRONG_ATTRIB: unit: gold="breaths/min" pred="per minute"; reported_by: gold="doctor" pred="person_1" (speaker id written instead of role) |

**physical examination**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Clear chest on auscultation (status="present", observed_by="doctor") | SEG0034 person_2 doctor: "Chest is clear and the throat looks a little red at the back." | MISSED | MISSED |
| *(extra P00)* | throat looks a little red at the back [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |
| *(extra P01)* | throat looks a little red at the back [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**review of systems**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| genitourinary (status="negative", reported_by="patient") | SEG0015 person_1 patient: "That's normal as far as I know." | MISSED | MISSED |

**clinical conditions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Gastro-oesophageal reflux disease (status="existing", reported_by="patient") | SEG0021 person_1 patient: "Yes, acid reflux. I have high blood pressure. I have heart disease." | MISSED | WRONG_NORM ('acid reflux') |
| Hypertension (status="existing", reported_by="patient") | SEG0021 person_1 patient: "Yes, acid reflux. I have high blood pressure. I have heart disease." | MISSED | MISSED |

**clinical assessment**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Cough driven by acid reflux (certainty="provisional", stated_by="doctor") | SEG0036 person_2 doctor: "Right, here's what I'm thinking. The most likely explanation is a cough driven by acid ref" | CORRECT | CORRECT |

**investigations/procedures**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Chest X-ray (status="planned", type="imaging") | SEG0038 person_2 doctor: "I can't promise yet, but most people with a cough driven by acid reflux do well once it's " | CORRECT | CORRECT |

**clinical actions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| investigation/arrange chest x ray (status="planned", responsible_person="clinical_staff") | SEG0038 person_2 doctor: "I can't promise yet, but most people with a cough driven by acid reflux do well once it's " | MISSED | MISSED |
| medication/start pantoprazole 40 mg before breakfast (status="planned", responsible_person="doctor") | SEG0040 person_2 doctor: "What I'm giving you is pantoprazole, 40 milligrams, before breakfast, for four weeks. That" | MISSED | MISSED |
| counselling/advise avoiding late meals and elevating bed head (status="recommended", responsible_person="patient") | SEG0040 person_2 doctor: "What I'm giving you is pantoprazole, 40 milligrams, before breakfast, for four weeks. That" | MISSED | MISSED |
| follow up/follow up consultation (status="planned", responsible_person="doctor") | SEG0040 person_2 doctor: "What I'm giving you is pantoprazole, 40 milligrams, before breakfast, for four weeks. That" | MISSED | MISSED |
| *(extra P00)* | medication/pantoprazole 40 mg before breakfast for four weeks [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |
| *(extra P01)* | medication/pantoprazole 40 mg before breakfast for four weeks [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**follow up**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| consultation/in a month (status="planned", time_reference="in a month") | SEG0040 person_2 doctor: "What I'm giving you is pantoprazole, 40 milligrams, before breakfast, for four weeks. That" | MISSED | MISSED |
| *(extra P01)* | follow up/ [UNSUPPORTED] | | |

**Not applicable (no gold fact and no prediction):** allergies, clinical uncertainties.

**Evidence (L).**
- P00: 1 evidence records; 0 are an exact single transcript segment; 18 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_near_copy_not_exact': 1, 'ev_empty_supports': 1, 'fact_not_mentioned_in_cited_text': 13, 'fact_path_missing_from_supports': 18}.
- P01: 1 evidence records; 0 are an exact single transcript segment; 19 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_multi_segment_or_whole_transcript_dump': 1, 'ev_empty_supports': 1, 'fact_path_missing_from_supports': 18, 'fact_not_mentioned_in_cited_text': 1, 'fact_no_evidence_ids': 1}.

### Record 00202   (P00: parsed, P01: parsed)

**Speakers (A).** Transcript: person_1 patient, person_2 doctor. Gold primary speakers: person_1 patient, person_2 doctor.
- P00: predicted [('person_1', 'patient'), ('person_2', 'doctor')]; all speakers+roles correct: True; missing none; wrong role none; invented ids none.
- P01: predicted [('person_1', 'patient'), ('person_2', 'doctor')]; all speakers+roles correct: True; missing none; wrong role none; invented ids none.

**Chief complaint (B).** Gold: 'fit last month' / normalized 'Seizure' (reported by patient).
- P00: 'fit' / normalized 'fit' (reported_by person_2) -> MISSED
- P01: 'fit' / normalized 'fit' (reported_by patient) -> MISSED

**symptoms**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Seizure (status="present", temporality="current", certainty="certain") | SEG0003 person_1 patient: "it's a fit last month i thought I'd wait, but it hasn't gone i told myself I'd wait and se" | MISSED | PARTIAL: duration: gold={"value": 4, "unit": "days", "normalized pred={"value": null, "unit": null, "normalize |
| Tongue biting (status="present", temporality="current", certainty="uncertain") | SEG0009 person_1 patient: "So, it's worse with missing tablets. As for biting my tongue, I honestly can't say when th" | MISSED | MISSED |
| Seizure (status="resolved", temporality="past", certainty="certain") | SEG0010 person_2 doctor: "have you had a fit last month before, or is this the first time?" | MISSED | MISSED |
| *(extra P00)* | fit [UNSUPPORTED] | | |

**negative findings**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Head injury (temporality="current", reported_by="patient") | SEG0012 person_2 doctor: "Any head injury or headache?" | MISSED | MISSED |
| Headache (temporality="current", reported_by="patient") | SEG0012 person_2 doctor: "Any head injury or headache?" | MISSED | MISSED |
| Unilateral weakness (temporality="current", reported_by="patient") | SEG0014 person_2 doctor: "Did you get weakness on one side or loss of bladder control?" | MISSED | MISSED |
| Urinary incontinence (temporality="current", reported_by="patient") | SEG0014 person_2 doctor: "Did you get weakness on one side or loss of bladder control?" | MISSED | MISSED |
| No known allergies (temporality="current", reported_by="patient") | SEG0027 person_1 patient: "I don't have any known medication allergies." | MISSED | WRONG_NORM ('no allergies') |
| *(extra P00)* | no fever [UNSUPPORTED] | | |
| *(extra P01)* | no fever [UNSUPPORTED]; no previous surgery [UNSUPPORTED] | | |

**past medical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Epilepsy (status="ongoing", reported_by="patient") | SEG0021 person_1 patient: "I've had epilepsy, yes" | WRONG_ATTRIB: reported_by: gold="patient" pred="person_1" (speaker id written instead of role) | CORRECT |

**surgical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Excision of back lump (reported_by="patient") | SEG0025 person_1 patient: "So, I had a lump removed from my back years ago." | WRONG_NORM ('lump removed from back') | WRONG_NORM ('lump removed from back') |

**social history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| occupation (status="current", reported_by="patient") | SEG0023 person_1 patient: "I run a small shop, so I'm on my feet a lot. I eat out quite a lot, to be honest. It's jus" | MISSED | MISSED |
| diet (status="current", reported_by="patient") | SEG0022 person_2 doctor: "Tell me about your routine, work, habits, that sort of thing." | MISSED | MISSED |
| living (status="current", reported_by="patient") | SEG0022 person_2 doctor: "Tell me about your routine, work, habits, that sort of thing." | MISSED | MISSED |
| *(extra P01)* | work [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**medications**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Sodium valproate (dose="500 mg", frequency="twice a day", status="currently_used") | SEG0005 person_1 patient: "Right, I'm on sodium valproate, 500 milligrams, twice a day." | WRONG_ATTRIB: route: not in gold, pred="oral"; reported_by: gold="patient" pred="person_1" (speaker id written instead of role) | UNSUPPORTED: route: not in gold, pred="oral" |

**allergies**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | unknown [INCORRECT - placeholder written as an allergy entry (gold has no allergy)] | | |
| *(extra P01)* | no known medication allergies [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**vital signs**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Heart rate (value=80, unit="bpm", reported_by="doctor") | SEG0030 person_2 doctor: "Okay: heart rate 80, respiratory rate 18, BP is 113 over 73, temperature is 36.8 degrees." | WRONG_ATTRIB: reported_by: gold="doctor" pred="person_2" (speaker id written instead of role) | WRONG_ATTRIB: reported_by: gold="doctor" pred="patient" |
| Respiratory rate (value=18, unit="breaths/min", reported_by="doctor") | SEG0030 person_2 doctor: "Okay: heart rate 80, respiratory rate 18, BP is 113 over 73, temperature is 36.8 degrees." | WRONG_ATTRIB: unit: gold="breaths/min" pred="breaths per minute"; reported_by: gold="doctor" pred="person_2" (speaker id written instead of role) | WRONG_ATTRIB: unit: gold="breaths/min" pred="beats per minute"; reported_by: gold="doctor" pred="patient" |
| Blood pressure (value="113/73", unit="mmHg", reported_by="doctor") | SEG0030 person_2 doctor: "Okay: heart rate 80, respiratory rate 18, BP is 113 over 73, temperature is 36.8 degrees." | WRONG_ATTRIB: reported_by: gold="doctor" pred="person_2" (speaker id written instead of role) | WRONG_ATTRIB: reported_by: gold="doctor" pred="patient" |
| Body temperature (value=36.8, unit="°C", reported_by="doctor") | SEG0030 person_2 doctor: "Okay: heart rate 80, respiratory rate 18, BP is 113 over 73, temperature is 36.8 degrees." | WRONG_NORM ('temperature') | WRONG_NORM ('temperature') |

**physical examination**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Alert and oriented (status="present", observed_by="doctor") | SEG0035 person_2 doctor: "You're alert and orientated, speech is clear." | MISSED | MISSED |
| Symmetrical reflexes and power (status="present", observed_by="doctor") | SEG0037 person_2 doctor: "Reflexes and power are symmetrical on both sides." | MISSED | MISSED |
| *(extra P00)* | no signs of seizure [UNSUPPORTED] | | |
| *(extra P01)* | no weakness [EXTRA_SUPPORTED_BY_TRANSCRIPT]; no joint pain [UNSUPPORTED]; no loss of bladder control [EXTRA_SUPPORTED_BY_TRANSCRIPT]; no head injury [EXTRA_SUPPORTED_BY_TRANSCRIPT]; no aches elsewhere [EXTRA_SUPPORTED_BY_TRANSCRIPT]; no headache [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**review of systems**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| musculoskeletal (status="negative", reported_by="patient") | SEG0017 person_1 patient: "Hmm, no, joints are fine." | MISSED | MISSED |
| respiratory (status="negative", reported_by="patient") | SEG0019 person_1 patient: "Breathing's normal." | MISSED | MISSED |
| *(extra P00)* | neurological [UNSUPPORTED] | | |
| *(extra P01)* | neurological [UNSUPPORTED] | | |

**clinical conditions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | breakthrough seizure on known epilepsy [INCORRECT - gold has this fact in category 'clinical assessment'] | | |
| *(extra P01)* | breakthrough seizure [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**clinical assessment**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Breakthrough seizure on known epilepsy (certainty="provisional", stated_by="doctor") | SEG0039 person_2 doctor: "Putting it all together, this looks most like breakthrough seizure on known epilepsy." | CORRECT | CORRECT |

**investigations/procedures**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| MRI brain (status="planned", type="imaging") | SEG0041 person_2 doctor: "it's reasonable to to be concerned, but right now breakthrough seizure on known epilepsy i" | WRONG_NORM ('MRI of the brain') | WRONG_NORM ('MRI of the brain') |
| Electroencephalogram (status="planned", type="other") | SEG0041 person_2 doctor: "it's reasonable to to be concerned, but right now breakthrough seizure on known epilepsy i" | MISSED | MISSED |
| Antiepileptic drug level (status="planned", type="laboratory") | SEG0041 person_2 doctor: "it's reasonable to to be concerned, but right now breakthrough seizure on known epilepsy i" | WRONG_NORM ('blood level of the tablet') | WRONG_NORM ('blood level of the tablet') |
| *(extra P00)* | eeg [UNSUPPORTED] | | |
| *(extra P01)* | eeg [UNSUPPORTED] | | |

**clinical actions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| investigation/arrange magnetic resonance imaging brain (status="planned", responsible_person="doctor") | SEG0041 person_2 doctor: "it's reasonable to to be concerned, but right now breakthrough seizure on known epilepsy i" | WRONG_NORM ('investigation/magnetic resonance imaging of the brain') | MISSED |
| investigation/arrange electroencephalogram (status="planned", responsible_person="doctor") | SEG0041 person_2 doctor: "it's reasonable to to be concerned, but right now breakthrough seizure on known epilepsy i" | MISSED | MISSED |
| investigation/arrange antiepileptic drug level (status="planned", responsible_person="doctor") | SEG0041 person_2 doctor: "it's reasonable to to be concerned, but right now breakthrough seizure on known epilepsy i" | MISSED | MISSED |
| counselling/advise no driving (status="recommended", responsible_person="patient") | SEG0043 person_2 doctor: "No driving until we've reviewed you again, I'm sorry, but that's the rule. Never skip the " | MISSED | MISSED |
| counselling/advise medication adherence (status="recommended", responsible_person="patient") | SEG0043 person_2 doctor: "No driving until we've reviewed you again, I'm sorry, but that's the rule. Never skip the " | MISSED | MISSED |
| counselling/seek urgent care if you have another seizure lasting more than five minutes (status="recommended", responsible_person="patient") | SEG0043 person_2 doctor: "No driving until we've reviewed you again, I'm sorry, but that's the rule. Never skip the " | MISSED | MISSED |
| follow up/follow up consultation (status="planned", responsible_person="doctor") | SEG0043 person_2 doctor: "No driving until we've reviewed you again, I'm sorry, but that's the rule. Never skip the " | MISSED | MISSED |
| *(extra P00)* | investigation/eeg [UNSUPPORTED]; investigation/blood level of the tablet [UNSUPPORTED] | | |
| *(extra P01)* | follow up/i d like you back in four weeks [UNSUPPORTED] | | |

**follow up**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| consultation/in four weeks (status="planned", time_reference="in four weeks") | SEG0043 person_2 doctor: "No driving until we've reviewed you again, I'm sorry, but that's the rule. Never skip the " | MISSED | WRONG_NORM ('consultation/four weeks') |
| *(extra P00)* | follow up/4 weeks [UNSUPPORTED] | | |

**clinical uncertainties**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| date_uncertain (resolution_status="unresolved") | SEG0009 person_1 patient: "So, it's worse with missing tablets. As for biting my tongue, I honestly can't say when th" | MISSED | MISSED |
| *(extra P00)* | conflicting statement [UNSUPPORTED] | | |
| *(extra P01)* | conflicting statement [UNSUPPORTED] | | |

**Not applicable (no gold fact and no prediction):** family history.

**Evidence (L).**
- P00: 1 evidence records; 0 are an exact single transcript segment; 23 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_multi_segment_or_whole_transcript_dump': 1, 'ev_empty_supports': 1, 'fact_path_missing_from_supports': 23, 'fact_not_mentioned_in_cited_text': 4}.
- P01: 1 evidence records; 1 are an exact single transcript segment; 29 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_empty_supports': 1, 'fact_path_missing_from_supports': 16, 'fact_not_mentioned_in_cited_text': 15, 'fact_no_evidence_ids': 13}.

### Record 00204   (P00: FAILED, P01: FAILED)

**Speakers (A).** Transcript: person_1 patient, person_2 doctor, person_3 caregiver. Gold primary speakers: person_1 patient, person_2 doctor, person_3 caregiver.
- P00: no usable output.
- P01: no usable output.

**Chief complaint (B).** Gold: 'itching' / normalized 'Itching' (reported by patient).
- P00: no usable output.
- P01: no usable output.

**symptoms**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Itching (status="present", temporality="current", certainty="certain") | SEG0005 person_1 patient: "So, So the thing is, I've got itching." | NO OUTPUT (record failed) | NO OUTPUT (record failed) |
| Scalp scaling (status="present", temporality="current", certainty="certain") | SEG0009 person_1 patient: "It's mild, honestly. I've had scaling on the scalp too, for about three months. Hmm, uh, a" | NO OUTPUT (record failed) | NO OUTPUT (record failed) |
| Scaly plaques (status="present", temporality="current", certainty="uncertain") | SEG0009 person_1 patient: "It's mild, honestly. I've had scaling on the scalp too, for about three months. Hmm, uh, a" | NO OUTPUT (record failed) | NO OUTPUT (record failed) |
| Morning finger stiffness (status="resolved", temporality="resolved", certainty="certain") | SEG0010 person_1 patient: "Stiff fingers in the morning was there, you know, but it's gone away on its own." | NO OUTPUT (record failed) | NO OUTPUT (record failed) |

**negative findings**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Fever (temporality="current", reported_by="patient") | SEG0012 person_1 patient: "No, no fever, eye redness or weeping." | NO OUTPUT (record failed) | NO OUTPUT (record failed) |
| Eye redness (temporality="current", reported_by="patient") | SEG0012 person_1 patient: "No, no fever, eye redness or weeping." | NO OUTPUT (record failed) | NO OUTPUT (record failed) |
| Skin weeping (temporality="current", reported_by="patient") | SEG0012 person_1 patient: "No, no fever, eye redness or weeping." | NO OUTPUT (record failed) | NO OUTPUT (record failed) |
| Joint swelling (temporality="current", reported_by="patient") | SEG0013 person_2 doctor: "Did you get joint swelling or sore throat before it started?" | NO OUTPUT (record failed) | NO OUTPUT (record failed) |
| Preceding sore throat (temporality="current", reported_by="patient") | SEG0013 person_2 doctor: "Did you get joint swelling or sore throat before it started?" | NO OUTPUT (record failed) | NO OUTPUT (record failed) |
| No previous surgery (temporality="past", reported_by="patient") | SEG0017 person_2 doctor: "Any previous surgeries?" | NO OUTPUT (record failed) | NO OUTPUT (record failed) |

**past medical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Type 2 diabetes mellitus (status="ongoing", reported_by="patient") | SEG0024 person_1 patient: "So, I have diabetes. Sorry, I know I'm rambling a bit. I have high blood pressure, for abo" | NO OUTPUT (record failed) | NO OUTPUT (record failed) |
| Hypertension (status="ongoing", reported_by="patient") | SEG0024 person_1 patient: "So, I have diabetes. Sorry, I know I'm rambling a bit. I have high blood pressure, for abo" | NO OUTPUT (record failed) | NO OUTPUT (record failed) |

**social history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| diet (status="current", reported_by="patient") | SEG0020 person_1 patient: "I try to avoid too much sugar." | NO OUTPUT (record failed) | NO OUTPUT (record failed) |
| exercise (status="current", reported_by="patient") | SEG0021 person_2 doctor: "Okay, do you exercise at all?" | NO OUTPUT (record failed) | NO OUTPUT (record failed) |

**medications**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Amlodipine (dose="5 mg", frequency="once a day", status="currently_used") | SEG0028 person_1 patient: "It's amlodipine, 5 milligrams, once a day." | NO OUTPUT (record failed) | NO OUTPUT (record failed) |

**allergies**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Aspirin (reaction="a rash", status="reported", reported_by="patient") | SEG0026 person_1 patient: "Yes, aspirin, it gives me a rash. Yes, I'm allergic to sulfa drugs." | NO OUTPUT (record failed) | NO OUTPUT (record failed) |
| Sulfonamide (status="reported", reported_by="patient") | SEG0026 person_1 patient: "Yes, aspirin, it gives me a rash. Yes, I'm allergic to sulfa drugs." | NO OUTPUT (record failed) | NO OUTPUT (record failed) |

**vital signs**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Body temperature (value=36.4, unit="°C", reported_by="doctor") | SEG0032 person_2 doctor: "Okay: temp 36.4 degrees, pulse is 70 beats a minute, pressure 122 over 72, oxygen saturati" | NO OUTPUT (record failed) | NO OUTPUT (record failed) |
| Heart rate (value=70, unit="bpm", reported_by="doctor") | SEG0032 person_2 doctor: "Okay: temp 36.4 degrees, pulse is 70 beats a minute, pressure 122 over 72, oxygen saturati" | NO OUTPUT (record failed) | NO OUTPUT (record failed) |
| Blood pressure (value="122/72", unit="mmHg", reported_by="doctor") | SEG0032 person_2 doctor: "Okay: temp 36.4 degrees, pulse is 70 beats a minute, pressure 122 over 72, oxygen saturati" | NO OUTPUT (record failed) | NO OUTPUT (record failed) |
| Oxygen saturation (value=98, unit="%", reported_by="doctor") | SEG0032 person_2 doctor: "Okay: temp 36.4 degrees, pulse is 70 beats a minute, pressure 122 over 72, oxygen saturati" | NO OUTPUT (record failed) | NO OUTPUT (record failed) |

**physical examination**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Nail pitting (status="present", observed_by="doctor") | SEG0035 person_2 doctor: "A few small pits in the fingernails." | NO OUTPUT (record failed) | NO OUTPUT (record failed) |
| Silvery scaly plaques (status="present", observed_by="doctor") | SEG0037 person_2 doctor: "Well-defined thick silvery plaques over both elbows and knees." | NO OUTPUT (record failed) | NO OUTPUT (record failed) |

**review of systems**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| neurological (status="negative", reported_by="patient") | SEG0016 person_1 patient: "No, that's all normal." | NO OUTPUT (record failed) | NO OUTPUT (record failed) |

**clinical assessment**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Plaque psoriasis (certainty="provisional", stated_by="doctor") | SEG0038 person_2 doctor: "That's fine, sit up. Taking everything into account, this looks most like plaque psoriasis" | NO OUTPUT (record failed) | NO OUTPUT (record failed) |
| Eczema (certainty="differential", stated_by="doctor") | SEG0038 person_2 doctor: "That's fine, sit up. Taking everything into account, this looks most like plaque psoriasis" | NO OUTPUT (record failed) | NO OUTPUT (record failed) |

**clinical actions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| counselling/advise moderate sun exposure and moisturising (status="recommended", responsible_person="patient") | SEG0038 person_2 doctor: "That's fine, sit up. Taking everything into account, this looks most like plaque psoriasis" | NO OUTPUT (record failed) | NO OUTPUT (record failed) |
| follow up/follow up consultation (status="planned", responsible_person="doctor") | SEG0039 person_2 doctor: "Right. We'll catch up in six weeks. Right, ask me anything before you go." | NO OUTPUT (record failed) | NO OUTPUT (record failed) |

**follow up**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| consultation/in six weeks (status="planned", time_reference="in six weeks") | SEG0039 person_2 doctor: "Right. We'll catch up in six weeks. Right, ask me anything before you go." | NO OUTPUT (record failed) | NO OUTPUT (record failed) |

**clinical uncertainties**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| date_uncertain (resolution_status="unresolved") | SEG0009 person_1 patient: "It's mild, honestly. I've had scaling on the scalp too, for about three months. Hmm, uh, a" | NO OUTPUT (record failed) | NO OUTPUT (record failed) |
| adherence_uncertain (resolution_status="unresolved") | SEG0028 person_1 patient: "It's amlodipine, 5 milligrams, once a day." | NO OUTPUT (record failed) | NO OUTPUT (record failed) |

**Not applicable (no gold fact and no prediction):** surgical history, family history, clinical conditions, investigations/procedures.

**Evidence (L).**
- P00: no usable output.
- P01: no usable output.

### Record 00206   (P00: parsed, P01: FAILED)

**Speakers (A).** Transcript: person_1 doctor, person_2 patient, person_3 caregiver, person_4 nurse. Gold primary speakers: person_1 doctor, person_2 patient, person_3 caregiver, person_4 nurse.
- P00: predicted [('person_1', 'doctor')]; all speakers+roles correct: False; missing [('person_2', 'patient'), ('person_3', 'caregiver'), ('person_4', 'nurse')]; wrong role none; invented ids none.
- P01: no usable output.

**Chief complaint (B).** Gold: 'low fever a few days ago' / normalized 'Fever' (reported by caregiver).
- P00: 'low fever and sore throat' / normalized 'low fever and sore throat' (reported_by patient) -> MISSED
- P01: no usable output.

**symptoms**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Fever (status="present", temporality="current", certainty="certain") | SEG0005 person_3 caregiver: "He's been having a low fever a few days ago doctor." | WRONG_NORM ('low fever') | NO OUTPUT (record failed) |
| Sore throat (status="present", temporality="current", certainty="certain") | SEG0013 person_2 patient: "a five out of ten I suppose i've I've had a sore throat earlier too for two days" | WRONG_STATUS: certainty: gold="certain" pred="uncertain"; severity: gold="severe" pred=null; duration: gold={"value": 2, "unit": "days", "normalized pred={"value":  | NO OUTPUT (record failed) |
| Cough (status="present", temporality="current", certainty="certain") | SEG0018 person_1 doctor: "Have you had a dry cough?" | MISSED | NO OUTPUT (record failed) |
| Pleuritic chest pain (status="resolved", temporality="resolved", certainty="certain") | SEG0021 person_2 patient: "Honestly, a few times a day. Oh, I did have sharp pain in the left chest when I breathe in" | MISSED | NO OUTPUT (record failed) |
| Fever (status="resolved", temporality="past", certainty="certain") | SEG0022 person_1 doctor: "Have you had a low fever a few days ago before, or is this the first time?" | MISSED | NO OUTPUT (record failed) |

**negative findings**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Leg swelling (temporality="current", reported_by="patient") | SEG0024 person_1 doctor: "So did you get leg swelling or coughing up blood?" | WRONG_NORM ('no leg swelling') | NO OUTPUT (record failed) |
| Haemoptysis (temporality="current", reported_by="patient") | SEG0024 person_1 doctor: "So did you get leg swelling or coughing up blood?" | MISSED | NO OUTPUT (record failed) |
| Recent long travel (temporality="current", reported_by="patient") | SEG0026 person_1 doctor: "have you noticed recent long travel injury to the chest or breathlessness at rest?" | MISSED | NO OUTPUT (record failed) |
| Chest injury (temporality="current", reported_by="patient") | SEG0026 person_1 doctor: "have you noticed recent long travel injury to the chest or breathlessness at rest?" | MISSED | NO OUTPUT (record failed) |
| Dyspnoea at rest (temporality="current", reported_by="patient") | SEG0026 person_1 doctor: "have you noticed recent long travel injury to the chest or breathlessness at rest?" | MISSED | NO OUTPUT (record failed) |

**past medical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Type 2 diabetes mellitus (status="ongoing", reported_by="patient") | SEG0035 person_2 patient: "I've had diabetes for nearly five years now." | WRONG_NORM ('diabetes') | NO OUTPUT (record failed) |
| Atrial fibrillation (status="ongoing", reported_by="patient") | SEG0037 person_2 patient: "I've had an irregular heartbeat for about a year now" | WRONG_NORM ('irregular heartbeat') | NO OUTPUT (record failed) |
| Hypertension (status="ongoing", reported_by="patient") | SEG0039 person_2 patient: "High blood pressure, for about ten years." | MISSED | NO OUTPUT (record failed) |

**surgical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Excision of back lump (reported_by="patient") | SEG0045 person_2 patient: "yes I had a lump removed from my back years ago. A neighbour of mine said I should see som" | WRONG_NORM ('lump removed from back') | NO OUTPUT (record failed) |

**family history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Thyroid disorder (relation="sister", reported_by="patient") | SEG0033 person_2 patient: "my sister has thyroid problems okay so my mother has migraines" | WRONG_NORM ('thyroid problems') | NO OUTPUT (record failed) |
| Migraine (relation="mother", reported_by="patient") | SEG0033 person_2 patient: "my sister has thyroid problems okay so my mother has migraines" | WRONG_NORM ('migraines') | NO OUTPUT (record failed) |

**social history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| smoking (status="former", reported_by="patient") | SEG0048 person_1 doctor: "A few questions about your lifestyle now." | MISSED | NO OUTPUT (record failed) |
| alcohol (status="former", reported_by="patient") | SEG0048 person_1 doctor: "A few questions about your lifestyle now." | MISSED | NO OUTPUT (record failed) |
| exercise (status="current", reported_by="patient") | SEG0049 person_2 patient: "I stopped smoking about two years back. I gave up drinking about three years ago. I play b" | MISSED | NO OUTPUT (record failed) |
| living (status="current", reported_by="patient") | SEG0048 person_1 doctor: "A few questions about your lifestyle now." | MISSED | NO OUTPUT (record failed) |
| *(extra P00)* | lifestyle [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**medications**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| small white one (status="currently_used", reported_by="patient") | SEG0041 person_2 patient: "it's, It's a... um, I can't remember what it's called. It's a small white one" | MISSED | NO OUTPUT (record failed) |
| Telmisartan (dose="40 mg", frequency="once a day", status="currently_used") | SEG0043 person_2 patient: "yeah, for my sugar, I believe. My wife sets them out for me, I just take what I'm given. O" | UNSUPPORTED: route: not in gold, pred="oral" | NO OUTPUT (record failed) |
| Ibuprofen (dose="400 mg", frequency="when it hurts", status="currently_used") | SEG0043 person_2 patient: "yeah, for my sugar, I believe. My wife sets them out for me, I just take what I'm given. O" | UNSUPPORTED: route: not in gold, pred="oral" | NO OUTPUT (record failed) |

**allergies**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| House dust (reaction="itchy eyes", status="reported", reported_by="patient") | SEG0047 person_2 patient: "yes, dust i get itchy eyes. Sulfa drugs i come out in... well, itching all over" | WRONG_NORM ('dust') | NO OUTPUT (record failed) |
| Sulfonamide (reaction="itching all over", status="reported", reported_by="patient") | SEG0047 person_2 patient: "yes, dust i get itchy eyes. Sulfa drugs i come out in... well, itching all over" | WRONG_NORM ('sulfa drugs') | NO OUTPUT (record failed) |

**vital signs**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Heart rate (value=69, unit="bpm", reported_by="nurse") | SEG0050 person_4 nurse: "Okay, so the vitals from earlier. Pulse is 69 beats a minute, temp 37.0 degrees, respirato" | MISSED | NO OUTPUT (record failed) |
| Body temperature (value=37.0, unit="°C", reported_by="nurse") | SEG0050 person_4 nurse: "Okay, so the vitals from earlier. Pulse is 69 beats a minute, temp 37.0 degrees, respirato" | MISSED | NO OUTPUT (record failed) |
| Respiratory rate (value=15, unit="breaths/min", reported_by="nurse") | SEG0050 person_4 nurse: "Okay, so the vitals from earlier. Pulse is 69 beats a minute, temp 37.0 degrees, respirato" | PARTIAL: unit: gold="breaths/min" pred="breaths per minute" | NO OUTPUT (record failed) |
| Blood pressure (value="119/81", unit="mmHg", reported_by="nurse") | SEG0050 person_4 nurse: "Okay, so the vitals from earlier. Pulse is 69 beats a minute, temp 37.0 degrees, respirato" | CORRECT | NO OUTPUT (record failed) |
| Oxygen saturation (value=97, unit="%", reported_by="nurse") | SEG0050 person_4 nurse: "Okay, so the vitals from earlier. Pulse is 69 beats a minute, temp 37.0 degrees, respirato" | CORRECT | NO OUTPUT (record failed) |
| *(extra P00)* | pulse [EXTRA_SUPPORTED_BY_TRANSCRIPT]; temperature [UNSUPPORTED] | | |

**physical examination**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Equal air entry (status="present", observed_by="doctor") | SEG0055 person_1 doctor: "air entry is equal on both sides" | MISSED | NO OUTPUT (record failed) |
| Pleural rub (status="present", observed_by="doctor") | SEG0058 person_1 doctor: "I can hear a faint rub on the left side" | WRONG_NORM ('faint rub on the left side') | NO OUTPUT (record failed) |

**review of systems**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| skin (status="negative", reported_by="patient") | SEG0029 person_2 patient: "Nothing on the skin no." | MISSED | NO OUTPUT (record failed) |
| genitourinary (status="negative", reported_by="patient") | SEG0031 person_2 patient: "no changes there" | MISSED | NO OUTPUT (record failed) |
| *(extra P00)* | respiratory [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**clinical conditions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | viral pleurisy [INCORRECT - gold has this fact in category 'clinical assessment'] | | |

**clinical assessment**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Viral pleurisy (certainty="provisional", stated_by="doctor") | SEG0061 person_1 doctor: "I can't promise yet, but most people with viral pleurisy do well once it's treated properl" | CORRECT | NO OUTPUT (record failed) |
| Chest infection (certainty="differential", stated_by="doctor") | SEG0059 person_1 doctor: "right good that's the examination. Taking everything into account this is probably viral p" | MISSED | NO OUTPUT (record failed) |
| Clot in the lung that we should rule out (certainty="differential", stated_by="doctor") | SEG0059 person_1 doctor: "right good that's the examination. Taking everything into account this is probably viral p" | MISSED | NO OUTPUT (record failed) |

**investigations/procedures**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Electrocardiogram (status="planned", type="cardiac") | SEG0063 person_1 doctor: "I want an ECG done, that's for chest pain. It's a routine test and it'll give us a much cl" | PARTIAL: type: gold="cardiac" pred="laboratory" | NO OUTPUT (record failed) |
| Chest X-ray (status="planned", type="imaging") | SEG0063 person_1 doctor: "I want an ECG done, that's for chest pain. It's a routine test and it'll give us a much cl" | PARTIAL: type: gold="imaging" pred="laboratory" | NO OUTPUT (record failed) |

**clinical actions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| investigation/arrange electrocardiogram (status="planned", responsible_person="doctor") | SEG0063 person_1 doctor: "I want an ECG done, that's for chest pain. It's a routine test and it'll give us a much cl" | MISSED | NO OUTPUT (record failed) |
| investigation/arrange chest x ray (status="planned", responsible_person="doctor") | SEG0063 person_1 doctor: "I want an ECG done, that's for chest pain. It's a routine test and it'll give us a much cl" | MISSED | NO OUTPUT (record failed) |
| counselling/regular analgesia to allow deep breathing (status="recommended", responsible_person="patient") | SEG0065 person_1 doctor: "Regular pain relief makes it easier to take deep breaths, which protects the lung. If you " | MISSED | NO OUTPUT (record failed) |
| counselling/seek urgent care if you become breathless or the pain changes (status="recommended", responsible_person="patient") | SEG0065 person_1 doctor: "Regular pain relief makes it easier to take deep breaths, which protects the lung. If you " | MISSED | NO OUTPUT (record failed) |
| *(extra P00)* | investigation/electrocardiogram and chest x ray [UNSUPPORTED] | | |

**follow up**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | consultation/ [UNSUPPORTED] | | |

**clinical uncertainties**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| incomplete_medication_name (resolution_status="unresolved") | SEG0041 person_2 patient: "it's, It's a... um, I can't remember what it's called. It's a small white one" | MISSED | NO OUTPUT (record failed) |
| *(extra P00)* | conflicting statement [UNSUPPORTED] | | |

**Not applicable (no gold fact and no prediction):** none.

**Evidence (L).**
- P00: 1 evidence records; 0 are an exact single transcript segment; 28 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_multi_segment_or_whole_transcript_dump': 1, 'ev_empty_supports': 1, 'fact_path_missing_from_supports': 27, 'fact_not_mentioned_in_cited_text': 11, 'fact_no_evidence_ids': 1}.
- P01: no usable output.

### Record 00210   (P00: FAILED, P01: parsed)

**Speakers (A).** Transcript: person_1 patient, person_2 doctor, person_3 family_member. Gold primary speakers: person_1 patient, person_2 doctor, person_3 family_member.
- P00: no usable output.
- P01: predicted [('person_1', 'patient'), ('person_2', 'doctor'), ('person_3', 'family_member')]; all speakers+roles correct: True; missing none; wrong role none; invented ids none.

**Chief complaint (B).** Gold: 'breathlessness when I lie flat' / normalized 'Orthopnoea' (reported by family_member).
- P00: no usable output.
- P01: 'Breathlessness when lying flat' / normalized 'Breathlessness when lying flat' (reported_by person_3) -> MISSED

**symptoms**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Orthopnoea (status="present", temporality="current", certainty="certain") | SEG0005 person_3 family_member: "He's been having breathlessness when I lie flat, doctor." | NO OUTPUT (record failed) | WRONG_NORM ('breathlessness') |
| Fatigue (status="present", temporality="current", certainty="certain") | SEG0015 person_1 patient: "Tiredness goes along with it, most of the time. The tiredness? That's been for six months." | NO OUTPUT (record failed) | WRONG_NORM ('tiredness') |
| Bilateral ankle swelling (status="present", temporality="current", certainty="certain") | SEG0015 person_1 patient: "Tiredness goes along with it, most of the time. The tiredness? That's been for six months." | NO OUTPUT (record failed) | WRONG_NORM ('swelling in ankles') |
| Paroxysmal nocturnal dyspnoea (status="present", temporality="current", certainty="certain") | SEG0017 person_1 patient: "Honestly, every other day. Maybe a four out of ten on a bad day. And I've been waking up a" | NO OUTPUT (record failed) | MISSED |

**negative findings**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Syncope (temporality="current", reported_by="patient") | SEG0033 person_1 patient: "No fainting, thankfully." | NO OUTPUT (record failed) | MISSED |
| Calf pain (temporality="current", reported_by="patient") | SEG0034 person_2 doctor: "Any calf pain, coughing up blood, fever or chest pain at all?" | NO OUTPUT (record failed) | MISSED |
| Haemoptysis (temporality="current", reported_by="patient") | SEG0034 person_2 doctor: "Any calf pain, coughing up blood, fever or chest pain at all?" | NO OUTPUT (record failed) | MISSED |
| Fever (temporality="current", reported_by="patient") | SEG0034 person_2 doctor: "Any calf pain, coughing up blood, fever or chest pain at all?" | NO OUTPUT (record failed) | WRONG_NORM ('no fever') |
| Chest pain (temporality="current", reported_by="patient") | SEG0034 person_2 doctor: "Any calf pain, coughing up blood, fever or chest pain at all?" | NO OUTPUT (record failed) | MISSED |
| No previous surgery (temporality="past", reported_by="patient") | SEG0048 person_2 doctor: "Have you had any previous surgeries?" | NO OUTPUT (record failed) | WRONG_STATUS: temporality: gold="past" pred="current"; reported_by: gold="patient" pred="person_1" (speaker id written instead of role) |
| *(extra P01)* | no allergies [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**past medical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Heart failure (status="ongoing", reported_by="patient") | SEG0045 person_1 patient: "I've got heart failure." | NO OUTPUT (record failed) | WRONG_ATTRIB: reported_by: gold="patient" pred="person_1" (speaker id written instead of role) |

**surgical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P01)* | no operations [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**family history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P01)* | heart failure [INCORRECT - gold has this fact in category 'past medical history'] | | |

**social history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| smoking (status="never", reported_by="patient") | SEG0047 person_1 patient: "I've never smoked. I have a couple of drinks on the weekend. I run a small shop, so I'm on" | NO OUTPUT (record failed) | MISSED |
| alcohol (status="current", reported_by="patient") | SEG0046 person_2 doctor: "Tell me about your routine, work, habits, that sort of thing." | NO OUTPUT (record failed) | MISSED |
| occupation (status="current", reported_by="patient") | SEG0047 person_1 patient: "I've never smoked. I have a couple of drinks on the weekend. I run a small shop, so I'm on" | NO OUTPUT (record failed) | MISSED |
| diet (status="current", reported_by="patient") | SEG0046 person_2 doctor: "Tell me about your routine, work, habits, that sort of thing." | NO OUTPUT (record failed) | MISSED |
| exercise (status="current", reported_by="patient") | SEG0047 person_1 patient: "I've never smoked. I have a couple of drinks on the weekend. I run a small shop, so I'm on" | NO OUTPUT (record failed) | MISSED |
| *(extra P01)* | lifestyle [UNSUPPORTED] | | |

**medications**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Spironolactone (dose="25 mg", frequency="once a day", status="currently_used") | SEG0041 person_3 family_member: "He is on spironolactone, 25 milligrams, once a day for my heart, I give it to him." | NO OUTPUT (record failed) | WRONG_ATTRIB: route: not in gold, pred="oral"; reported_by: gold="family_member" pred="person_1" (speaker id written instead of role) |

**allergies**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Antibiotic (unspecified) (status="uncertain", reported_by="patient") | SEG0043 person_1 patient: "Hmm, there was some antibiotic, I was told I was allergic. But I couldn't tell you what it" | NO OUTPUT (record failed) | WRONG_NORM ('antibiotic') |

**vital signs**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Blood pressure (value="129/77", unit="mmHg", reported_by="doctor") | SEG0020 person_2 doctor: "Okay: blood pressure 129 over 77, pulse is 85 beats a minute, saturation 92 percent." | NO OUTPUT (record failed) | WRONG_ATTRIB: reported_by: gold="doctor" pred="person_1" (speaker id written instead of role) |
| Heart rate (value=85, unit="bpm", reported_by="doctor") | SEG0020 person_2 doctor: "Okay: blood pressure 129 over 77, pulse is 85 beats a minute, saturation 92 percent." | NO OUTPUT (record failed) | MISSED |
| Oxygen saturation (value=92, unit="%", reported_by="doctor") | SEG0020 person_2 doctor: "Okay: blood pressure 129 over 77, pulse is 85 beats a minute, saturation 92 percent." | NO OUTPUT (record failed) | WRONG_NORM ('saturation') |
| *(extra P01)* | pulse [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**physical examination**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Raised jugular venous pressure (status="present", observed_by="doctor") | SEG0025 person_2 doctor: "Neck veins are raised." | NO OUTPUT (record failed) | WRONG_NORM ('neck veins are raised') |
| Bibasal crackles (status="present", observed_by="doctor") | SEG0028 person_2 doctor: "I can hear crackles at the bases of both lungs." | NO OUTPUT (record failed) | MISSED |
| Bilateral pitting leg oedema (status="present", observed_by="doctor") | SEG0030 person_2 doctor: "There's pitting oedema up to the shins on both legs." | NO OUTPUT (record failed) | WRONG_NORM ('pitting edema up to the shins on both legs') |
| *(extra P01)* | little pressure here tell me if it s tender [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**review of systems**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| musculoskeletal (status="negative", reported_by="patient") | SEG0037 person_1 patient: "No, nothing there." | NO OUTPUT (record failed) | MISSED |
| gastrointestinal (status="negative", reported_by="patient") | SEG0039 person_1 patient: "No, all normal there." | NO OUTPUT (record failed) | MISSED |
| *(extra P01)* | respiratory [UNSUPPORTED] | | |

**clinical conditions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P01)* | heart failure [INCORRECT - gold has this fact in category 'past medical history'] | | |

**clinical assessment**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Fluid overload related to the heart (certainty="provisional", stated_by="doctor") | SEG0050 person_2 doctor: "Taking everything into account, this is probably fluid overload related to the heart. It c" | NO OUTPUT (record failed) | CORRECT |
| Kidney problem (certainty="differential", stated_by="doctor") | SEG0050 person_2 doctor: "Taking everything into account, this is probably fluid overload related to the heart. It c" | NO OUTPUT (record failed) | MISSED |

**investigations/procedures**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Echocardiogram (status="planned", type="imaging") | SEG0054 person_2 doctor: "Let's book an echocardiogram to look into breathlessness and swelling." | NO OUTPUT (record failed) | CORRECT |
| Renal function and BNP (status="planned", type="laboratory") | SEG0056 person_2 doctor: "I'm sending you for blood tests because of heart failure review. Let's book a chest X-ray " | NO OUTPUT (record failed) | WRONG_NORM ('blood tests') |
| Chest X-ray (status="planned", type="imaging") | SEG0056 person_2 doctor: "I'm sending you for blood tests because of heart failure review. Let's book a chest X-ray " | NO OUTPUT (record failed) | CORRECT |

**clinical actions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| investigation/arrange echocardiogram (status="planned", responsible_person="doctor") | SEG0054 person_2 doctor: "Let's book an echocardiogram to look into breathlessness and swelling." | NO OUTPUT (record failed) | MISSED |
| investigation/arrange renal function and bnp (status="planned", responsible_person="doctor") | SEG0056 person_2 doctor: "I'm sending you for blood tests because of heart failure review. Let's book a chest X-ray " | NO OUTPUT (record failed) | MISSED |
| investigation/arrange chest x ray (status="planned", responsible_person="doctor") | SEG0056 person_2 doctor: "I'm sending you for blood tests because of heart failure review. Let's book a chest X-ray " | NO OUTPUT (record failed) | MISSED |
| counselling/advise daily weights (status="recommended", responsible_person="patient") | SEG0056 person_2 doctor: "I'm sending you for blood tests because of heart failure review. Let's book a chest X-ray " | NO OUTPUT (record failed) | MISSED |
| counselling/advise fluid and salt restriction (status="recommended", responsible_person="patient") | SEG0056 person_2 doctor: "I'm sending you for blood tests because of heart failure review. Let's book a chest X-ray " | NO OUTPUT (record failed) | MISSED |
| counselling/seek urgent care if the breathlessness gets worse or you can t lie down at all (status="recommended", responsible_person="patient") | SEG0057 person_2 doctor: "The thing that would worry me is if the breathlessness gets worse or you can't lie down at" | NO OUTPUT (record failed) | MISSED |
| follow up/follow up consultation (status="planned", responsible_person="doctor") | SEG0059 person_2 doctor: "I'd like you back in one week. Good. Let us know how you get on." | NO OUTPUT (record failed) | MISSED |
| *(extra P01)* | follow up/book an echocardiogram to look into breathlessness and swelling [UNSUPPORTED] | | |

**follow up**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| consultation/in one week (status="planned", time_reference="in one week") | SEG0059 person_2 doctor: "I'd like you back in one week. Good. Let us know how you get on." | NO OUTPUT (record failed) | MISSED |
| *(extra P01)* | consultation/1 week [UNSUPPORTED] | | |

**clinical uncertainties**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| allergy_uncertain (resolution_status="unresolved") | SEG0043 person_1 patient: "Hmm, there was some antibiotic, I was told I was allergic. But I couldn't tell you what it" | NO OUTPUT (record failed) | MISSED |
| *(extra P01)* | date uncertain [UNSUPPORTED]; date uncertain [UNSUPPORTED]; date uncertain [UNSUPPORTED] | | |

**Not applicable (no gold fact and no prediction):** none.

**Evidence (L).**
- P00: no usable output.
- P01: 1 evidence records; 0 are an exact single transcript segment; 30 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_text_not_in_transcript': 1, 'ev_empty_supports': 1, 'fact_path_missing_from_supports': 30, 'fact_not_mentioned_in_cited_text': 28}.

### Record 00215   (P00: parsed, P01: parsed)

**Speakers (A).** Transcript: person_1 patient, person_2 doctor. Gold primary speakers: person_1 patient, person_2 doctor.
- P00: predicted [('person_1', 'patient'), ('person_2', 'doctor')]; all speakers+roles correct: True; missing none; wrong role none; invented ids none.
- P01: predicted [('person_1', 'patient'), ('person_2', 'doctor')]; all speakers+roles correct: True; missing none; wrong role none; invented ids none.

**Chief complaint (B).** Gold: 'headaches in the mornings' / normalized 'Morning headache' (reported by patient).
- P00: 'headaches in the mornings' / normalized 'headaches in the mornings' (reported_by person_1) -> WRONG_NORM ('headaches in the mornings')
- P01: 'headaches in the mornings' / normalized 'headaches in the mornings' (reported_by patient) -> WRONG_NORM ('headaches in the mornings')

**symptoms**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Morning headache (status="present", temporality="current", certainty="certain") | SEG0003 person_1 patient: "Well, you know, honestly, it's headaches in the mornings, and my family pushed me to come." | WRONG_NORM ('headaches') | WRONG_NORM ('headaches') |

**negative findings**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| No previous surgery (temporality="past", reported_by="patient") | SEG0010 person_2 doctor: "Have you had any previous surgeries?" | WRONG_STATUS: temporality: gold="past" pred="current"; reported_by: gold="patient" pred="person_1" (speaker id written instead of role) | WRONG_STATUS: temporality: gold="past" pred="current" |
| Epistaxis (temporality="current", reported_by="patient") | SEG0022 person_2 doctor: "Okay, and what about nosebleeds, chest pain or palpitations?" | MISSED | MISSED |
| Chest pain (temporality="current", reported_by="patient") | SEG0022 person_2 doctor: "Okay, and what about nosebleeds, chest pain or palpitations?" | MISSED | MISSED |
| Palpitations (temporality="current", reported_by="patient") | SEG0022 person_2 doctor: "Okay, and what about nosebleeds, chest pain or palpitations?" | MISSED | MISSED |
| Weakness (temporality="current", reported_by="patient") | SEG0024 person_2 doctor: "Any weakness?" | MISSED | MISSED |
| *(extra P00)* | no fever [UNSUPPORTED]; no allergies [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |
| *(extra P01)* | no fever [UNSUPPORTED]; no allergies [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**past medical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Hypertension (status="ongoing", reported_by="patient") | SEG0013 person_1 patient: "Um, I have high blood pressure, for nearly five years." | WRONG_NORM ('high blood pressure') | WRONG_NORM ('high blood pressure') |

**surgical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | no surgery [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |
| *(extra P01)* | no surgery [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**family history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P01)* | unknown [UNSUPPORTED] | | |

**social history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| smoking (status="never", reported_by="patient") | SEG0015 person_1 patient: "I've never smoked." | MISSED | MISSED |
| living (status="current", reported_by="patient") | SEG0017 person_1 patient: "I share a flat with two friends." | MISSED | MISSED |
| diet (status="current", reported_by="patient") | SEG0019 person_1 patient: "I skip breakfast most days." | MISSED | WRONG_STATUS: status: gold="current" pred="" |

**medications**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Amlodipine (dose="5 mg", frequency="once a day", status="currently_used") | SEG0009 person_1 patient: "Amlodipine, 5 milligrams, once a day." | WRONG_ATTRIB: route: not in gold, pred="oral"; reported_by: gold="patient" pred="person_1" (speaker id written instead of role) | MISSED |
| Telmisartan (dose="40 mg", route="oral", frequency="once a day") | SEG0044 person_1 patient: "So, I take the telmisartan, 40 milligrams, once a day. Is that right?" | MISSED | WRONG_STATUS: status: gold="planned" pred="currently_used"; reported_by: gold="doctor" pred="patient" |

**allergies**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Ibuprofen (reaction="a rash", status="reported", reported_by="patient") | SEG0021 person_1 patient: "Um, yes, ibuprofen, it gives me a rash." | WRONG_ATTRIB: reaction: gold="a rash" pred=null; reported_by: gold="patient" pred="person_1" (speaker id written instead of role) | PARTIAL: reaction: gold="a rash" pred=null |

**vital signs**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Heart rate (value=89, unit="bpm", reported_by="doctor") | SEG0030 person_2 doctor: "Okay: pulse 89, temperature 36.8, BP is 152 over 97." | MISSED | MISSED |
| Body temperature (value=36.8, unit="°C", reported_by="doctor") | SEG0030 person_2 doctor: "Okay: pulse 89, temperature 36.8, BP is 152 over 97." | WRONG_NORM ('temperature') | WRONG_NORM ('temperature') |
| Blood pressure (value="152/97", unit="mmHg", reported_by="doctor") | SEG0030 person_2 doctor: "Okay: pulse 89, temperature 36.8, BP is 152 over 97." | WRONG_ATTRIB: reported_by: gold="doctor" pred="person_2" (speaker id written instead of role) | WRONG_ATTRIB: reported_by: gold="doctor" pred="patient" |
| *(extra P00)* | pulse [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |
| *(extra P01)* | pulse [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**physical examination**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Bilateral ankle oedema (status="present", observed_by="doctor") | SEG0036 person_2 doctor: "There's mild pitting swelling at both ankles." | WRONG_NORM ('mild pitting swelling at both ankles') | WRONG_NORM ('mild pitting swelling at both ankles') |

**review of systems**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| musculoskeletal (status="negative", reported_by="patient") | SEG0027 person_1 patient: "No, joints are fine." | MISSED | MISSED |
| *(extra P00)* | cardiovascular [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |
| *(extra P01)* | cardiovascular [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**clinical conditions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | hypertension [INCORRECT - gold has this fact in category 'past medical history'] | | |
| *(extra P01)* | hypertension [INCORRECT - gold has this fact in category 'past medical history'] | | |

**clinical assessment**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Hypertension that isn't well controlled (certainty="provisional", stated_by="doctor") | SEG0039 person_2 doctor: "From what you've told me and what I found, I'd lean towards hypertension that isn't well c" | CORRECT | CORRECT |

**investigations/procedures**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Lipid profile (status="planned", type="laboratory") | SEG0039 person_2 doctor: "From what you've told me and what I found, I'd lean towards hypertension that isn't well c" | PARTIAL: type: gold="laboratory" pred="other" | PARTIAL: type: gold="laboratory" pred="other" |

**clinical actions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| investigation/arrange lipid profile (status="planned", responsible_person="doctor") | SEG0039 person_2 doctor: "From what you've told me and what I found, I'd lean towards hypertension that isn't well c" | MISSED | MISSED |
| medication/start telmisartan 40 mg once a day (status="planned", responsible_person="doctor") | SEG0044 person_1 patient: "So, I take the telmisartan, 40 milligrams, once a day. Is that right?" | MISSED | MISSED |
| counselling/advise salt reduction (status="recommended", responsible_person="patient") | SEG0043 person_2 doctor: "Salt is the big one, try to keep it low even though it's hard. Cut down on salt and fried " | MISSED | MISSED |
| counselling/advise reducing salt and fried food (status="recommended", responsible_person="patient") | SEG0043 person_2 doctor: "Salt is the big one, try to keep it low even though it's hard. Cut down on salt and fried " | MISSED | MISSED |
| counselling/seek urgent care if the symptoms get worse (status="recommended", responsible_person="patient") | SEG0043 person_2 doctor: "Salt is the big one, try to keep it low even though it's hard. Cut down on salt and fried " | MISSED | MISSED |
| *(extra P00)* | medication/telmisartan 40 mg once a day long term [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |
| *(extra P01)* | medication/telmisartan 40 mg once a day long term [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**follow up**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | consultation/ [UNSUPPORTED] | | |
| *(extra P01)* | consultation/ [UNSUPPORTED] | | |

**clinical uncertainties**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | unknown speaker [UNSUPPORTED] | | |
| *(extra P01)* | unknown speaker [UNSUPPORTED] | | |

**Not applicable (no gold fact and no prediction):** none.

**Evidence (L).**
- P00: 1 evidence records; 1 are an exact single transcript segment; 20 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_empty_supports': 1, 'fact_not_mentioned_in_cited_text': 2, 'fact_cites_intro_segment_unrelated': 2, 'fact_path_missing_from_supports': 2, 'fact_no_evidence_ids': 18}.
- P01: 1 evidence records; 0 are an exact single transcript segment; 22 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_multi_segment_or_whole_transcript_dump': 1, 'ev_empty_supports': 1, 'fact_path_missing_from_supports': 13, 'fact_no_evidence_ids': 9}.

### Record 00221   (P00: parsed, P01: parsed)

**Speakers (A).** Transcript: person_1 patient, person_2 doctor, person_3 caregiver. Gold primary speakers: person_1 patient, person_2 doctor, person_3 caregiver.
- P00: predicted [('person_1', 'patient'), ('person_2', 'doctor'), ('person_3', 'caregiver')]; all speakers+roles correct: True; missing none; wrong role none; invented ids none.
- P01: predicted [('person_1', 'patient'), ('person_2', 'doctor'), ('person_3', 'caregiver')]; all speakers+roles correct: True; missing none; wrong role none; invented ids none.

**Chief complaint (B).** Gold: 'leaking urine when I cough or sneeze' / normalized 'Stress urinary leakage' (reported by patient).
- P00: 'leaking urine when I cough or sneeze' / normalized 'leaking urine when coughing or sneezing' (reported_by person_1) -> WRONG_NORM ('leaking urine when coughing or sneezing')
- P01: 'leaking urine when I cough or sneeze' / normalized 'leaking urine when coughing or sneezing' (reported_by patient) -> WRONG_NORM ('leaking urine when coughing or sneezing')

**symptoms**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Stress urinary leakage (status="present", temporality="current", certainty="certain") | SEG0005 person_1 patient: "yeah it's leaking urine when I cough or sneeze i thought I'd wait but it hasn't gone" | MISSED | MISSED |
| Pelvic heaviness (status="present", temporality="current", certainty="certain") | SEG0013 person_1 patient: "About a three out of ten. Laughing definitely sets it off. I did try to ignore it for a wh" | MISSED | MISSED |
| Urinary urgency (status="present", temporality="current", certainty="uncertain") | SEG0014 person_1 patient: "as for urgent need to go sometimes, I honestly can't say when that began it might have bee" | MISSED | MISSED |
| Pad use (status="present", temporality="current", certainty="certain") | SEG0017 person_2 doctor: "have you been needing to wear a pad?" | MISSED | MISSED |
| Stress urinary leakage (status="resolved", temporality="past", certainty="certain") | SEG0021 person_2 doctor: "Have you had leaking urine when you cough or sneeze before, or is this the first time?" | MISSED | MISSED |
| *(extra P00)* | urinary leakage [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |
| *(extra P01)* | urinary leakage [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**negative findings**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Haematuria (temporality="current", reported_by="patient") | SEG0023 person_2 doctor: "A few quick ones: blood in the urine difficulty emptying back pain or fever?" | MISSED | MISSED |
| Voiding difficulty (temporality="current", reported_by="patient") | SEG0023 person_2 doctor: "A few quick ones: blood in the urine difficulty emptying back pain or fever?" | MISSED | MISSED |
| Back pain (temporality="current", reported_by="patient") | SEG0023 person_2 doctor: "A few quick ones: blood in the urine difficulty emptying back pain or fever?" | MISSED | MISSED |
| Fever (temporality="current", reported_by="patient") | SEG0023 person_2 doctor: "A few quick ones: blood in the urine difficulty emptying back pain or fever?" | MISSED | WRONG_NORM ('no fever') |
| *(extra P01)* | no allergies [UNSUPPORTED]; no previous surgery [UNSUPPORTED] | | |

**past medical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Type 2 diabetes mellitus (status="ongoing", reported_by="patient") | SEG0041 person_2 doctor: "alright, diabetes and high blood pressure, that matches what I have here" | WRONG_NORM ('diabetes') | WRONG_NORM ('diabetes') |
| Hypertension (status="ongoing", reported_by="patient") | SEG0041 person_2 doctor: "alright, diabetes and high blood pressure, that matches what I have here" | WRONG_NORM ('high blood pressure') | WRONG_NORM ('high blood pressure') |
| Ischaemic heart disease (status="ongoing", reported_by="patient") | SEG0040 person_1 patient: "Diabetes for five years i have high blood pressure for two years i told myself I'd wait an" | WRONG_NORM ('heart disease') | WRONG_NORM ('heart disease') |

**surgical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Coronary artery bypass grafting (reported_by="patient") | SEG0030 person_1 patient: "yes I had a a bypass operation six years ago" | WRONG_NORM ('bypass operation') | WRONG_NORM ('bypass operation') |

**family history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P01)* | unknown [UNSUPPORTED] | | |

**social history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| occupation (status="current", reported_by="patient") | SEG0032 person_1 patient: "I teach at a primary school." | MISSED | MISSED |
| diet (status="current", reported_by="patient") | SEG0033 person_2 doctor: "okay, what's your diet like?" | MISSED | WRONG_STATUS: status: gold="current" pred="unknown" |

**medications**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Metformin (dose="500 mg", frequency="twice a day", status="currently_used") | SEG0036 person_1 patient: "I take Glycomet, 500 milligrams, twice a day" | WRONG_NORM ('glycomet') | WRONG_NORM ('glycomet') |
| Losartan (dose="50 mg", frequency="once a day", status="currently_used") | SEG0038 person_1 patient: "about about a month it's losartan, 50 milligrams, once a day for my blood pressure it's cl" | MISSED | MISSED |
| Clopidogrel (dose="75 mg", frequency="once a day", status="currently_used") | SEG0038 person_1 patient: "about about a month it's losartan, 50 milligrams, once a day for my blood pressure it's cl" | WRONG_ATTRIB: route: not in gold, pred="oral"; reported_by: gold="patient" pred="person_1" (speaker id written instead of role) | UNSUPPORTED: route: not in gold, pred="oral" |

**allergies**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P01)* | unknown [INCORRECT - placeholder written as an allergy entry (gold has no allergy)] | | |

**vital signs**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Body temperature (value=36.4, unit="°C", reported_by="doctor") | SEG0008 person_2 doctor: "Okay: temperature 36.4, BP is 125 over 80, pulse is 80 beats a minute. And SpO2 98 percent" | MISSED | WRONG_NORM ('temperature') |
| Blood pressure (value="125/80", unit="mmHg", reported_by="doctor") | SEG0008 person_2 doctor: "Okay: temperature 36.4, BP is 125 over 80, pulse is 80 beats a minute. And SpO2 98 percent" | MISSED | WRONG_ATTRIB: reported_by: gold="doctor" pred="patient" |
| Heart rate (value=80, unit="bpm", reported_by="doctor") | SEG0008 person_2 doctor: "Okay: temperature 36.4, BP is 125 over 80, pulse is 80 beats a minute. And SpO2 98 percent" | MISSED | MISSED |
| Oxygen saturation (value=98, unit="%", reported_by="doctor") | SEG0008 person_2 doctor: "Okay: temperature 36.4, BP is 125 over 80, pulse is 80 beats a minute. And SpO2 98 percent" | MISSED | WRONG_ATTRIB: reported_by: gold="doctor" pred="patient" |
| *(extra P01)* | pulse [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**physical examination**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| No visible prolapse (status="absent", observed_by="doctor") | SEG0044 person_2 doctor: "No bulge is visible when you cough, and the tummy is soft." | WRONG_NORM ('no bulge is visible when coughing') | WRONG_NORM ('no bulge is visible when coughing') |
| *(extra P01)* | tummy is soft [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**review of systems**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| gastrointestinal (status="negative", reported_by="patient") | SEG0026 person_1 patient: "bowels are regular, nothing odd" | MISSED | MISSED |
| respiratory (status="negative", reported_by="patient") | SEG0028 person_1 patient: "no problems with breathing" | MISSED | MISSED |
| *(extra P01)* | urological [UNSUPPORTED] | | |

**clinical conditions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Type 2 diabetes mellitus (status="existing", reported_by="patient") | SEG0041 person_2 doctor: "alright, diabetes and high blood pressure, that matches what I have here" | MISSED | MISSED |
| Hypertension (status="existing", reported_by="patient") | SEG0041 person_2 doctor: "alright, diabetes and high blood pressure, that matches what I have here" | MISSED | MISSED |
| *(extra P00)* | stress urinary incontinence [INCORRECT - gold has this fact in category 'clinical assessment'] | | |
| *(extra P01)* | stress urinary incontinence [INCORRECT - gold has this fact in category 'clinical assessment']; overactive bladder [INCORRECT - gold has this fact in category 'clinical assessment'] | | |

**clinical assessment**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Stress urinary incontinence (certainty="differential", stated_by="doctor") | SEG0048 person_2 doctor: "I understand the worry. At the moment I'd say it's stress urinary incontinence and we'll k" | WRONG_STATUS: certainty: gold="differential" pred="provisional" | WRONG_STATUS: certainty: gold="differential" pred="provisional" |
| Overactive bladder (certainty="differential", stated_by="doctor") | SEG0046 person_2 doctor: "okay finished. Putting it all together I'm honestly not certain yet. It could be stress ur" | MISSED | MISSED |

**investigations/procedures**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Urinalysis (status="planned", type="laboratory") | SEG0049 person_2 doctor: "I want a urine test done, that's for urinary leakage. I want a bladder diary done, that's " | WRONG_NORM ('urine test') | WRONG_NORM ('urine test') |
| Bladder diary (status="planned", type="other") | SEG0049 person_2 doctor: "I want a urine test done, that's for urinary leakage. I want a bladder diary done, that's " | PARTIAL: type: gold="other" pred="laboratory" | PARTIAL: type: gold="other" pred="laboratory" |

**clinical actions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| investigation/arrange urinalysis (status="planned", responsible_person="doctor") | SEG0049 person_2 doctor: "I want a urine test done, that's for urinary leakage. I want a bladder diary done, that's " | MISSED | MISSED |
| investigation/arrange bladder diary (status="planned", responsible_person="doctor") | SEG0049 person_2 doctor: "I want a urine test done, that's for urinary leakage. I want a bladder diary done, that's " | MISSED | WRONG_NORM ('investigation/bladder diary') |
| counselling/pelvic floor exercises (status="recommended", responsible_person="patient") | SEG0049 person_2 doctor: "I want a urine test done, that's for urinary leakage. I want a bladder diary done, that's " | MISSED | WRONG_STATUS: status: gold="recommended" pred="planned"; responsible_person: gold="patient" pred="doctor" |
| counselling/advise avoiding additional painkillers (status="recommended", responsible_person="patient") | SEG0049 person_2 doctor: "I want a urine test done, that's for urinary leakage. I want a bladder diary done, that's " | MISSED | MISSED |
| follow up/follow up consultation (status="planned", responsible_person="doctor") | SEG0049 person_2 doctor: "I want a urine test done, that's for urinary leakage. I want a bladder diary done, that's " | MISSED | MISSED |
| *(extra P00)* | follow up/review you in eight weeks [UNSUPPORTED] | | |
| *(extra P01)* | investigation/urine test [UNSUPPORTED]; follow up/review in eight weeks [UNSUPPORTED] | | |

**follow up**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| consultation/in eight weeks (status="planned", time_reference="in eight weeks") | SEG0049 person_2 doctor: "I want a urine test done, that's for urinary leakage. I want a bladder diary done, that's " | MISSED | WRONG_NORM ('consultation/eight weeks') |
| *(extra P00)* | consultation/8 weeks [UNSUPPORTED] | | |

**clinical uncertainties**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| date_uncertain (resolution_status="unresolved") | SEG0014 person_1 patient: "as for urgent need to go sometimes, I honestly can't say when that began it might have bee" | MISSED | MISSED |
| *(extra P00)* | conflicting statement [UNSUPPORTED] | | |
| *(extra P01)* | conflicting statement [UNSUPPORTED] | | |

**Not applicable (no gold fact and no prediction):** none.

**Evidence (L).**
- P00: 1 evidence records; 0 are an exact single transcript segment; 16 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_near_copy_not_exact': 1, 'fact_path_missing_from_supports': 5, 'fact_not_mentioned_in_cited_text': 4, 'fact_no_evidence_ids': 10}.
- P01: 1 evidence records; 0 are an exact single transcript segment; 32 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_text_not_in_transcript': 1, 'ev_empty_supports': 1, 'fact_path_missing_from_supports': 22, 'fact_not_mentioned_in_cited_text': 18, 'fact_no_evidence_ids': 10}.

### Record 00238   (P00: parsed, P01: parsed)

**Speakers (A).** Transcript: person_1 patient, person_2 doctor. Gold primary speakers: person_1 patient, person_2 doctor.
- P00: predicted [('person_1', 'patient'), ('person_2', 'doctor')]; all speakers+roles correct: True; missing none; wrong role none; invented ids none.
- P01: predicted [('person_1', 'patient'), ('person_2', 'doctor')]; all speakers+roles correct: True; missing none; wrong role none; invented ids none.

**Chief complaint (B).** Gold: 'breathlessness on the stairs' / normalized 'Exertional dyspnoea' (reported by patient).
- P00: 'Mainly breathlessness on the stairs' / normalized 'Mainly breathlessness on the stairs' (reported_by person_1) -> WRONG_NORM ('mainly breathlessness on the stairs')
- P01: 'Mainly breathlessness on the stairs' / normalized 'Mainly breathlessness on the stairs' (reported_by person_1) -> WRONG_NORM ('mainly breathlessness on the stairs')

**symptoms**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Exertional dyspnoea (status="present", temporality="current", certainty="certain") | SEG0003 person_1 patient: "Mainly breathlessness on the stairs. There's a couple of other things, but that's the main" | WRONG_NORM ('breathlessness') | WRONG_NORM ('breathlessness') |

**negative findings**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Weight loss (temporality="current", reported_by="patient") | SEG0009 person_1 patient: "no weight loss, chest pain or fainting, none of it" | MISSED | WRONG_NORM ('No weight loss') |
| Chest pain (temporality="current", reported_by="patient") | SEG0009 person_1 patient: "no weight loss, chest pain or fainting, none of it" | MISSED | WRONG_NORM ('No chest pain') |
| Syncope (temporality="current", reported_by="patient") | SEG0009 person_1 patient: "no weight loss, chest pain or fainting, none of it" | MISSED | WRONG_NORM ('no fainting') |
| Melaena (temporality="current", reported_by="patient") | SEG0010 person_2 doctor: "Have you had any black stools?" | MISSED | MISSED |
| No previous surgery (temporality="past", reported_by="patient") | SEG0020 person_2 doctor: "have you had any previous surgeries?" | MISSED | MISSED |
| No known allergies (temporality="current", reported_by="patient") | SEG0022 person_2 doctor: "Any drug or food allergies?" | MISSED | MISSED |

**past medical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Gastro-oesophageal reflux disease (status="ongoing", reported_by="patient") | SEG0029 person_1 patient: "Acid reflux, for five years. I have eczema." | WRONG_NORM ('acid reflux') | WRONG_NORM ('acid reflux') |
| Eczema (status="ongoing", reported_by="patient") | SEG0029 person_1 patient: "Acid reflux, for five years. I have eczema." | WRONG_ATTRIB: reported_by: gold="patient" pred="person_1" (speaker id written instead of role) | WRONG_ATTRIB: reported_by: gold="patient" pred="person_1" (speaker id written instead of role) |

**surgical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | no operations [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |
| *(extra P01)* | no operations [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**family history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Hypertension (relation="mother", reported_by="patient") | SEG0027 person_1 patient: "My mother had high blood pressure." | WRONG_NORM ('high blood pressure') | WRONG_NORM ('high blood pressure') |

**social history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| occupation (status="current", reported_by="patient") | SEG0015 person_1 patient: "Yes, I'm a nurse on a busy ward" | MISSED | MISSED |
| diet (status="current", reported_by="patient") | SEG0017 person_1 patient: "I'm mostly vegetarian" | WRONG_STATUS: status: gold="current" pred=""; reported_by: gold="patient" pred="person_1" (speaker id written instead of role) | WRONG_STATUS: status: gold="current" pred=""; reported_by: gold="patient" pred="person_1" (speaker id written instead of role) |
| living (status="current", reported_by="patient") | SEG0018 person_2 doctor: "do you live alone?" | MISSED | MISSED |
| *(extra P00)* | living situation [UNSUPPORTED] | | |
| *(extra P01)* | living alone [UNSUPPORTED] | | |

**medications**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Pantoprazole (dose="40 mg", frequency="before breakfast", status="currently_used") | SEG0025 person_1 patient: "Pantoprazole. I take it 40 milligrams, before breakfast. I take hydrocortisone cream, when" | WRONG_ATTRIB: frequency: gold="before breakfast" pred=null; reported_by: gold="patient" pred="person_1" (speaker id written instead of role) | WRONG_ATTRIB: route: not in gold, pred="oral"; reported_by: gold="patient" pred="person_1" (speaker id written instead of role) |
| Hydrocortisone (frequency="when needed", status="currently_used", reported_by="patient") | SEG0025 person_1 patient: "Pantoprazole. I take it 40 milligrams, before breakfast. I take hydrocortisone cream, when" | WRONG_NORM ('hydrocortisone cream') | WRONG_NORM ('hydrocortisone cream') |
| Ferrous sulfate (dose="200 mg", frequency="once a day", status="planned") | SEG0040 person_2 doctor: "I'll request a full blood count, it'll help with pallor i'm sending you for a ferritin lev" | MISSED | MISSED |

**allergies**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | no allergies [INCORRECT - placeholder written as an allergy entry (gold has no allergy)] | | |
| *(extra P01)* | no allergies [INCORRECT - placeholder written as an allergy entry (gold has no allergy)] | | |

**physical examination**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Conjunctival pallor (status="present", observed_by="doctor") | SEG0034 person_2 doctor: "Your eyelids are pale inside." | WRONG_NORM ('pale eyelids inside') | WRONG_NORM ('pale eyelids') |
| No cardiac murmur (status="absent", observed_by="doctor") | SEG0036 person_2 doctor: "Heart sounds are normal, I don't hear any murmur." | MISSED | MISSED |
| *(extra P01)* | normal heart sounds [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**review of systems**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| genitourinary (status="negative", reported_by="patient") | SEG0013 person_1 patient: "No, that's all fine." | MISSED | MISSED |
| *(extra P00)* | respiratory [UNSUPPORTED]; skin [UNSUPPORTED] | | |
| *(extra P01)* | respiratory [UNSUPPORTED]; skin [UNSUPPORTED] | | |

**clinical conditions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Gastro-oesophageal reflux disease (status="existing", reported_by="patient") | SEG0029 person_1 patient: "Acid reflux, for five years. I have eczema." | MISSED | MISSED |
| Eczema (status="existing", reported_by="patient") | SEG0029 person_1 patient: "Acid reflux, for five years. I have eczema." | MISSED | MISSED |
| *(extra P00)* | anemia [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |
| *(extra P01)* | anemia [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**clinical assessment**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Anaemia of some kind (certainty="provisional", stated_by="doctor") | SEG0037 person_2 doctor: "Okay, finished. Taking everything into account, this is probably anaemia of some kind." | CORRECT | CORRECT |

**investigations/procedures**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Complete blood count (status="planned", type="laboratory") | SEG0040 person_2 doctor: "I'll request a full blood count, it'll help with pallor i'm sending you for a ferritin lev" | WRONG_NORM ('full blood count') | WRONG_NORM ('full blood count') |
| Serum ferritin (status="planned", type="laboratory") | SEG0040 person_2 doctor: "I'll request a full blood count, it'll help with pallor i'm sending you for a ferritin lev" | WRONG_NORM ('ferritin level') | WRONG_NORM ('ferritin level') |

**clinical actions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| investigation/arrange complete blood count (status="planned", responsible_person="doctor") | SEG0040 person_2 doctor: "I'll request a full blood count, it'll help with pallor i'm sending you for a ferritin lev" | MISSED | MISSED |
| investigation/arrange serum ferritin (status="planned", responsible_person="doctor") | SEG0040 person_2 doctor: "I'll request a full blood count, it'll help with pallor i'm sending you for a ferritin lev" | MISSED | MISSED |
| medication/start ferrous sulfate 200 mg once a day (status="planned", responsible_person="doctor") | SEG0040 person_2 doctor: "I'll request a full blood count, it'll help with pallor i'm sending you for a ferritin lev" | MISSED | MISSED |
| counselling/advise iron tablet side effects (status="recommended", responsible_person="patient") | SEG0040 person_2 doctor: "I'll request a full blood count, it'll help with pallor i'm sending you for a ferritin lev" | MISSED | MISSED |
| counselling/seek urgent care if the symptoms get worse (status="recommended", responsible_person="patient") | SEG0040 person_2 doctor: "I'll request a full blood count, it'll help with pallor i'm sending you for a ferritin lev" | MISSED | MISSED |
| follow up/follow up consultation (status="planned", responsible_person="doctor") | SEG0042 person_2 doctor: "Please come and see me in two weeks. Okay, I think we're finished. Is everything clear?" | MISSED | MISSED |
| *(extra P00)* | follow up/please come and see me in two weeks [UNSUPPORTED] | | |
| *(extra P01)* | follow up/please come and see me in two weeks [UNSUPPORTED] | | |

**follow up**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| consultation/in two weeks (status="planned", time_reference="in two weeks") | SEG0042 person_2 doctor: "Please come and see me in two weeks. Okay, I think we're finished. Is everything clear?" | MISSED | MISSED |
| *(extra P00)* | consultation/2 weeks [UNSUPPORTED] | | |
| *(extra P01)* | consultation/2 weeks [UNSUPPORTED] | | |

**clinical uncertainties**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | date uncertain [UNSUPPORTED] | | |
| *(extra P01)* | date uncertain [UNSUPPORTED] | | |

**Not applicable (no gold fact and no prediction):** vital signs.

**Evidence (L).**
- P00: 1 evidence records; 0 are an exact single transcript segment; 21 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_multi_segment_or_whole_transcript_dump': 1, 'ev_empty_supports': 1, 'fact_path_missing_from_supports': 21, 'fact_not_mentioned_in_cited_text': 19}.
- P01: 1 evidence records; 0 are an exact single transcript segment; 25 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_multi_segment_or_whole_transcript_dump': 1, 'ev_empty_supports': 1, 'fact_path_missing_from_supports': 4, 'fact_no_evidence_ids': 21, 'fact_not_mentioned_in_cited_text': 2}.

### Record 00248   (P00: parsed, P01: parsed)

**Speakers (A).** Transcript: person_1 patient, person_2 doctor. Gold primary speakers: person_1 patient, person_2 doctor.
- P00: predicted [('person_1', 'patient'), ('person_2', 'doctor')]; all speakers+roles correct: True; missing none; wrong role none; invented ids none.
- P01: predicted [('person_1', 'patient'), ('person_2', 'doctor')]; all speakers+roles correct: True; missing none; wrong role none; invented ids none.

**Chief complaint (B).** Gold: 'feeling overwhelmed at work' / normalized 'Work-related stress' (reported by patient).
- P00: 'I've been feeling overwhelmed at work, and I wanted to get it checked.' / normalized 'I've been feeling overwhelmed at work, and I wanted to get it checked.' (reported_by patient) -> WRONG_NORM ('i ve been feeling overwhelmed at work and i wanted to get it checked')
- P01: 'I've been feeling overwhelmed at work, and I wanted to get it checked.' / normalized 'I've been feeling overwhelmed at work, and I wanted to get it checked.' (reported_by patient) -> WRONG_NORM ('i ve been feeling overwhelmed at work and i wanted to get it checked')

**symptoms**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Work-related stress (status="present", temporality="current", certainty="certain") | SEG0003 person_1 patient: "I've been feeling overwhelmed at work, and I wanted to get it checked." | MISSED | MISSED |
| Insomnia (status="present", temporality="current", certainty="certain") | SEG0011 person_1 patient: "Trouble switching off at night goes along with it, most of the time. Yeah, uh, about Troub" | MISSED | MISSED |
| *(extra P00)* | stress related symptoms [INCORRECT - gold has this fact in category 'clinical assessment'] | | |
| *(extra P01)* | stress related symptoms [INCORRECT - gold has this fact in category 'clinical assessment'] | | |

**negative findings**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Suicidal ideation (temporality="current", reported_by="patient") | SEG0012 person_2 doctor: "Have you had any thoughts of harming myself, chest pain or weight loss?" | MISSED | MISSED |
| Chest pain (temporality="current", reported_by="patient") | SEG0012 person_2 doctor: "Have you had any thoughts of harming myself, chest pain or weight loss?" | MISSED | MISSED |
| Weight loss (temporality="current", reported_by="patient") | SEG0012 person_2 doctor: "Have you had any thoughts of harming myself, chest pain or weight loss?" | MISSED | MISSED |
| Heavy alcohol use (temporality="current", reported_by="patient") | SEG0015 person_1 patient: "I haven't noticed any alcohol use." | MISSED | MISSED |
| No previous surgery (temporality="past", reported_by="patient") | SEG0022 person_2 doctor: "Any previous surgeries?" | MISSED | WRONG_STATUS: temporality: gold="past" pred="current" |
| *(extra P00)* | no fever [UNSUPPORTED] | | |
| *(extra P01)* | no allergies [EXTRA_SUPPORTED_BY_TRANSCRIPT]; no fever [UNSUPPORTED] | | |

**past medical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Gastro-oesophageal reflux disease (status="ongoing", reported_by="patient") | SEG0019 person_1 patient: "I have acid reflux, for nearly five years." | WRONG_NORM ('acid reflux') | WRONG_NORM ('acid reflux') |

**surgical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | no operations [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |
| *(extra P01)* | no operations [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**family history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P01)* | pollen allergy [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**social history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| exercise (status="current", reported_by="patient") | SEG0020 person_2 doctor: "right, right a few questions about your lifestyle now" | MISSED | MISSED |
| diet (status="current", reported_by="patient") | SEG0020 person_2 doctor: "right, right a few questions about your lifestyle now" | MISSED | MISSED |
| living (status="current", reported_by="patient") | SEG0020 person_2 doctor: "right, right a few questions about your lifestyle now" | MISSED | MISSED |
| *(extra P00)* | lifestyle [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |
| *(extra P01)* | lifestyle [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**medications**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Omeprazole (dose="20 mg", frequency="once a day", status="currently_used") | SEG0005 person_1 patient: "Omeprazole, 20 milligrams, once a day." | UNSUPPORTED: route: not in gold, pred="oral" | UNSUPPORTED: route: not in gold, pred="oral" |

**allergies**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Pollen (reaction="sneezing", status="reported", reported_by="patient") | SEG0025 person_1 patient: "Pollen. I come out in... well, sneezing." | PARTIAL: reaction: gold="sneezing" pred=null | PARTIAL: reaction: gold="sneezing" pred=null |

**vital signs**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Heart rate (value=71, unit="bpm", reported_by="doctor") | SEG0028 person_2 doctor: "Okay: pulse is 71 beats a minute, blood pressure 127 over 82, temperature is 36.6 degrees." | MISSED | MISSED |
| Blood pressure (value="127/82", unit="mmHg", reported_by="doctor") | SEG0028 person_2 doctor: "Okay: pulse is 71 beats a minute, blood pressure 127 over 82, temperature is 36.6 degrees." | WRONG_ATTRIB: reported_by: gold="doctor" pred="patient" | WRONG_ATTRIB: reported_by: gold="doctor" pred="patient" |
| Body temperature (value=36.6, unit="°C", reported_by="doctor") | SEG0028 person_2 doctor: "Okay: pulse is 71 beats a minute, blood pressure 127 over 82, temperature is 36.6 degrees." | WRONG_NORM ('temperature') | WRONG_NORM ('temperature') |
| *(extra P00)* | pulse [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |
| *(extra P01)* | pulse [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**physical examination**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | nothing else aches [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |
| *(extra P01)* | nothing else aches [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**review of systems**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| musculoskeletal (status="negative", reported_by="patient") | SEG0017 person_1 patient: "Nothing else aches." | MISSED | MISSED |
| *(extra P00)* | respiratory [UNSUPPORTED] | | |
| *(extra P01)* | respiratory [UNSUPPORTED] | | |

**clinical conditions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | stress related symptoms [INCORRECT - gold has this fact in category 'clinical assessment'] | | |
| *(extra P01)* | stress related symptoms [INCORRECT - gold has this fact in category 'clinical assessment'] | | |

**clinical assessment**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Stress-related symptoms (certainty="provisional", stated_by="doctor") | SEG0031 person_2 doctor: "So, based on your history, I think we're dealing with stress-related symptoms at this stag" | CORRECT | CORRECT |

**investigations/procedures**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Complete blood count (status="planned", type="laboratory") | SEG0034 person_2 doctor: "Let's book blood tests to look into stress-related symptoms." | WRONG_NORM ('blood tests') | WRONG_NORM ('blood tests') |

**clinical actions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| investigation/arrange complete blood count (status="planned", responsible_person="doctor") | SEG0034 person_2 doctor: "Let's book blood tests to look into stress-related symptoms." | MISSED | MISSED |
| counselling/advise talking therapy (status="recommended", responsible_person="patient") | SEG0036 person_2 doctor: "talking to someone, even a counsellor, helps more than people expect avoid taking any extr" | MISSED | MISSED |
| counselling/advise avoiding additional painkillers (status="recommended", responsible_person="patient") | SEG0036 person_2 doctor: "talking to someone, even a counsellor, helps more than people expect avoid taking any extr" | MISSED | MISSED |
| referral/refer to counselling (status="planned", responsible_person="doctor") | SEG0036 person_2 doctor: "talking to someone, even a counsellor, helps more than people expect avoid taking any extr" | WRONG_NORM ('counselling/i ll arrange the letter') | WRONG_NORM ('counselling/i ll arrange the letter') |
| counselling/seek urgent care if the symptoms get worse (status="recommended", responsible_person="patient") | SEG0038 person_2 doctor: "If the symptoms get worse, or you feel really unwell, please come to the emergency departm" | MISSED | MISSED |
| follow up/follow up consultation (status="planned", responsible_person="doctor") | SEG0038 person_2 doctor: "If the symptoms get worse, or you feel really unwell, please come to the emergency departm" | MISSED | MISSED |

**follow up**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| consultation/in four weeks (status="planned", time_reference="in four weeks") | SEG0038 person_2 doctor: "If the symptoms get worse, or you feel really unwell, please come to the emergency departm" | MISSED | MISSED |
| *(extra P00)* | consultation/4 weeks [UNSUPPORTED] | | |
| *(extra P01)* | consultation/4 weeks [UNSUPPORTED] | | |

**clinical uncertainties**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | conflicting statement [UNSUPPORTED] | | |
| *(extra P01)* | date uncertain [UNSUPPORTED] | | |

**Not applicable (no gold fact and no prediction):** none.

**Evidence (L).**
- P00: 1 evidence records; 0 are an exact single transcript segment; 19 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_multi_segment_or_whole_transcript_dump': 1, 'ev_empty_supports': 1, 'fact_path_missing_from_supports': 19, 'fact_not_mentioned_in_cited_text': 9}.
- P01: 3 evidence records; 2 are an exact single transcript segment; 22 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_empty_supports': 3, 'ev_near_copy_not_exact': 1, 'fact_path_missing_from_supports': 11, 'fact_not_mentioned_in_cited_text': 6, 'fact_no_evidence_ids': 11}.

### Record 00264   (P00: parsed, P01: parsed)

**Speakers (A).** Transcript: person_1 patient, person_2 doctor, person_3 nurse. Gold primary speakers: person_1 patient, person_2 doctor, person_3 nurse.
- P00: predicted [('person_1', 'patient'), ('person_2', 'doctor'), ('person_3', 'nurse')]; all speakers+roles correct: True; missing none; wrong role none; invented ids none.
- P01: predicted [('person_1', 'patient'), ('person_2', 'doctor'), ('person_3', 'nurse')]; all speakers+roles correct: True; missing none; wrong role none; invented ids none.

**Chief complaint (B).** Gold: 'blood on the toilet paper' / normalized 'Rectal bleeding' (reported by patient).
- P00: 'blood on the toilet paper' / normalized 'blood on the toilet paper' (reported_by patient) -> WRONG_NORM ('blood on the toilet paper')
- P01: 'blood on the toilet paper' / normalized 'blood on the toilet paper' (reported_by patient) -> WRONG_NORM ('blood on the toilet paper')

**symptoms**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Rectal bleeding (status="present", temporality="current", certainty="certain") | SEG0003 person_1 patient: "Honestly, it's blood on the toilet paper, and my family pushed me to come." | WRONG_NORM ('blood on the toilet paper') | WRONG_NORM ('blood on the toilet paper') |
| Perianal itching (status="present", temporality="current", certainty="certain") | SEG0009 person_1 patient: "Um, you know, it usually comes with an itchy bottom. The itchy bottom? That's been for fou" | MISSED | MISSED |
| Painful defecation (status="present", temporality="current", certainty="certain") | SEG0009 person_1 patient: "Um, you know, it usually comes with an itchy bottom. The itchy bottom? That's been for fou" | MISSED | MISSED |
| Rectal bleeding (status="resolved", temporality="past", certainty="certain") | SEG0010 person_2 doctor: "Have you had blood on the toilet paper before, or is this the first time?" | MISSED | MISSED |

**negative findings**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Fever (temporality="current", reported_by="patient") | SEG0021 person_1 patient: "No fever, black stools or abdominal pain, none of it." | WRONG_NORM ('no fever') | WRONG_NORM ('no fever') |
| Melaena (temporality="current", reported_by="patient") | SEG0021 person_1 patient: "No fever, black stools or abdominal pain, none of it." | MISSED | MISSED |
| Abdominal pain (temporality="current", reported_by="patient") | SEG0021 person_1 patient: "No fever, black stools or abdominal pain, none of it." | MISSED | MISSED |
| Weight loss (temporality="current", reported_by="patient") | SEG0023 person_1 patient: "I haven't had weight loss or family history of bowel cancer, no." | MISSED | MISSED |
| Family history of bowel cancer (temporality="current", reported_by="patient") | SEG0023 person_1 patient: "I haven't had weight loss or family history of bowel cancer, no." | MISSED | MISSED |
| *(extra P00)* | no allergies [UNSUPPORTED]; no previous surgery [UNSUPPORTED] | | |
| *(extra P01)* | no allergies [UNSUPPORTED]; no previous surgery [UNSUPPORTED] | | |

**past medical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Anaemia (status="ongoing", reported_by="patient") | SEG0027 person_1 patient: "I have low haemoglobin. I have an irregular heartbeat, for nearly five years." | MISSED | MISSED |
| Atrial fibrillation (status="ongoing", reported_by="patient") | SEG0027 person_1 patient: "I have low haemoglobin. I have an irregular heartbeat, for nearly five years." | WRONG_NORM ('irregular heartbeat') | WRONG_NORM ('irregular heartbeat') |
| *(extra P00)* | low hemoglobin [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |
| *(extra P01)* | low hemoglobin [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**surgical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Appendicectomy (reported_by="patient") | SEG0029 person_1 patient: "Right, yes, I had my appendix out, about eight years ago." | WRONG_NORM ('appendix out') | WRONG_NORM ('appendix out') |

**social history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| alcohol (status="former", reported_by="patient") | SEG0034 person_2 doctor: "Right, do you drink alcohol?" | MISSED | MISSED |
| diet (status="current", reported_by="patient") | SEG0037 person_1 patient: "I try to avoid too much sugar." | MISSED | WRONG_STATUS: status: gold="current" pred="" |
| living (status="current", reported_by="patient") | SEG0038 person_2 doctor: "Who's at home with you?" | MISSED | MISSED |

**medications**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Iron tablets (frequency="once a day", status="currently_used", reported_by="patient") | SEG0031 person_1 patient: "Iron tablets, once a day." | UNSUPPORTED: dose: not in gold, pred="once a day" | UNSUPPORTED: dose: not in gold, pred="once a day" |
| Apixaban (dose="5 mg", frequency="twice a day", status="currently_used") | SEG0033 person_1 patient: "Apixaban. I take it 5 milligrams, twice a day. I take Anovate cream, twice a day." | CORRECT | UNSUPPORTED: route: not in gold, pred="oral" |
| Hydrocortisone/lidocaine (frequency="twice a day", status="currently_used", reported_by="patient") | SEG0033 person_1 patient: "Apixaban. I take it 5 milligrams, twice a day. I take Anovate cream, twice a day." | WRONG_NORM ('anovate cream') | WRONG_NORM ('anovate cream') |
| A soothing cream (frequency="twice a day", status="planned", reported_by="doctor") | SEG0041 person_2 doctor: "A colonoscopy is what I'd like next, for rectal bleeding. You'll be taking a soothing crea" | MISSED | MISSED |

**allergies**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | unknown [INCORRECT - placeholder written as an allergy entry (gold has no allergy)] | | |
| *(extra P01)* | unknown [INCORRECT - placeholder written as an allergy entry (gold has no allergy)] | | |

**vital signs**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Heart rate (value=71, unit="bpm", reported_by="nurse") | SEG0012 person_3 nurse: "Doctor, I've got the readings for you. Heart rate 71, oxygen saturation is 99 percent, tem" | WRONG_ATTRIB: reported_by: gold="nurse" pred="patient" | CORRECT |
| Oxygen saturation (value=99, unit="%", reported_by="nurse") | SEG0012 person_3 nurse: "Doctor, I've got the readings for you. Heart rate 71, oxygen saturation is 99 percent, tem" | WRONG_ATTRIB: reported_by: gold="nurse" pred="patient" | CORRECT |
| Body temperature (value=36.9, unit="°C", reported_by="nurse") | SEG0012 person_3 nurse: "Doctor, I've got the readings for you. Heart rate 71, oxygen saturation is 99 percent, tem" | MISSED | MISSED |
| Blood pressure (value="124/77", unit="mmHg", reported_by="nurse") | SEG0012 person_3 nurse: "Doctor, I've got the readings for you. Heart rate 71, oxygen saturation is 99 percent, tem" | WRONG_ATTRIB: reported_by: gold="nurse" pred="patient" | CORRECT |

**physical examination**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| External haemorrhoid (status="present", observed_by="doctor") | SEG0017 person_2 doctor: "There's a small external pile at the edge, and I don't see any fissure." | WRONG_NORM ('small external pile at the edge') | WRONG_NORM ('small external pile at the edge') |
| Non-tender abdomen (status="present", observed_by="doctor") | SEG0019 person_2 doctor: "Tummy is soft and non-tender." | WRONG_NORM ('tummy is soft and non tender') | WRONG_NORM ('tummy is soft and non tender') |

**review of systems**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| musculoskeletal (status="negative", reported_by="patient") | SEG0025 person_1 patient: "Nothing else aches." | MISSED | MISSED |
| *(extra P00)* | gastrointestinal [UNSUPPORTED] | | |
| *(extra P01)* | gastrointestinal [UNSUPPORTED] | | |

**clinical conditions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | hemorrhoids [INCORRECT - gold has this fact in category 'clinical assessment'] | | |
| *(extra P01)* | hemorrhoids [INCORRECT - gold has this fact in category 'clinical assessment'] | | |

**clinical assessment**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Haemorrhoids (certainty="provisional", stated_by="doctor") | SEG0040 person_2 doctor: "Taking everything into account, I think we're dealing with haemorrhoids at this stage. Tha" | CORRECT | CORRECT |
| Anal fissure (certainty="differential", stated_by="doctor") | SEG0040 person_2 doctor: "Taking everything into account, I think we're dealing with haemorrhoids at this stage. Tha" | MISSED | MISSED |

**investigations/procedures**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Colonoscopy (status="planned", type="other") | SEG0041 person_2 doctor: "A colonoscopy is what I'd like next, for rectal bleeding. You'll be taking a soothing crea" | PARTIAL: type: gold="other" pred="imaging" | PARTIAL: type: gold="other" pred="imaging" |

**clinical actions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| investigation/arrange colonoscopy (status="planned", responsible_person="doctor") | SEG0041 person_2 doctor: "A colonoscopy is what I'd like next, for rectal bleeding. You'll be taking a soothing crea" | WRONG_NORM ('investigation/colonoscopy') | WRONG_NORM ('investigation/colonoscopy') |
| medication/start hemorrhoid cream twice a day (status="planned", responsible_person="doctor") | SEG0041 person_2 doctor: "A colonoscopy is what I'd like next, for rectal bleeding. You'll be taking a soothing crea" | MISSED | MISSED |
| counselling/advise warm sitz baths and avoiding straining (status="recommended", responsible_person="patient") | SEG0041 person_2 doctor: "A colonoscopy is what I'd like next, for rectal bleeding. You'll be taking a soothing crea" | MISSED | MISSED |
| counselling/seek urgent care if you pass a lot of blood or feel faint (status="recommended", responsible_person="patient") | SEG0041 person_2 doctor: "A colonoscopy is what I'd like next, for rectal bleeding. You'll be taking a soothing crea" | MISSED | MISSED |
| follow up/follow up consultation (status="planned", responsible_person="doctor") | SEG0041 person_2 doctor: "A colonoscopy is what I'd like next, for rectal bleeding. You'll be taking a soothing crea" | MISSED | MISSED |

**follow up**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| consultation/after the results are back (status="planned", time_reference="after the results are ba) | SEG0041 person_2 doctor: "A colonoscopy is what I'd like next, for rectal bleeding. You'll be taking a soothing crea" | MISSED | MISSED |
| *(extra P00)* | consultation/ [UNSUPPORTED] | | |
| *(extra P01)* | consultation/ [UNSUPPORTED] | | |

**clinical uncertainties**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | conflicting statement [UNSUPPORTED] | | |
| *(extra P01)* | date uncertain [UNSUPPORTED] | | |

**Not applicable (no gold fact and no prediction):** family history.

**Evidence (L).**
- P00: 1 evidence records; 0 are an exact single transcript segment; 24 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_text_not_in_transcript': 1, 'ev_empty_supports': 1, 'fact_not_mentioned_in_cited_text': 23, 'fact_path_missing_from_supports': 23, 'fact_no_evidence_ids': 1}.
- P01: 1 evidence records; 0 are an exact single transcript segment; 25 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_near_copy_not_exact': 1, 'ev_empty_supports': 1, 'fact_not_mentioned_in_cited_text': 2, 'fact_path_missing_from_supports': 5, 'fact_no_evidence_ids': 20}.

### Record 00266   (P00: parsed, P01: parsed)

**Speakers (A).** Transcript: person_1 patient, person_2 doctor. Gold primary speakers: person_1 patient, person_2 doctor.
- P00: predicted [('person_2', 'doctor')]; all speakers+roles correct: False; missing [('person_1', 'patient')]; wrong role none; invented ids none.
- P01: predicted [('person_1', 'patient'), ('person_2', 'doctor')]; all speakers+roles correct: True; missing none; wrong role none; invented ids none.

**Chief complaint (B).** Gold: 'feeling drowsy' / normalized 'Drowsiness' (reported by patient).
- P00: 'Mainly I've been feeling drowsy. That's why I came.' / normalized 'Mainly I've been feeling drowsy. That's why I came.' (reported_by patient) -> WRONG_NORM ('mainly i ve been feeling drowsy that s why i came')
- P01: 'Mainly I've been feeling drowsy. That's why I came.' / normalized 'Mainly I've been feeling drowsy. That's why I came.' (reported_by patient) -> WRONG_NORM ('mainly i ve been feeling drowsy that s why i came')

**symptoms**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Drowsiness (status="present", temporality="current", certainty="certain") | SEG0003 person_1 patient: "Mainly I've been feeling drowsy. That's why I came." | PARTIAL: severity: gold="4/10" pred=null; duration: gold={"value": 1, "unit": "weeks", "normalize pred={"value": null, "unit": null, "normalize | PARTIAL: severity: gold="4/10" pred=null; duration: gold={"value": 1, "unit": "weeks", "normalize pred={"value": null, "unit": null, "normalize |
| Post-ictal confusion (status="present", temporality="current", certainty="certain") | SEG0011 person_1 patient: "A four out of ten I suppose. Oh and a bit of confusion afterwards. That's been about the s" | MISSED | MISSED |
| Seizure (status="resolved", temporality="resolved", certainty="certain") | SEG0011 person_1 patient: "A four out of ten I suppose. Oh and a bit of confusion afterwards. That's been about the s" | MISSED | MISSED |

**negative findings**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Urinary incontinence (temporality="current", reported_by="patient") | SEG0012 person_2 doctor: "Any loss of bladder control, fever, headache or weakness on one side at all?" | MISSED | MISSED |
| Fever (temporality="current", reported_by="patient") | SEG0012 person_2 doctor: "Any loss of bladder control, fever, headache or weakness on one side at all?" | MISSED | WRONG_NORM ('no fever') |
| Headache (temporality="current", reported_by="patient") | SEG0012 person_2 doctor: "Any loss of bladder control, fever, headache or weakness on one side at all?" | MISSED | MISSED |
| Unilateral weakness (temporality="current", reported_by="patient") | SEG0012 person_2 doctor: "Any loss of bladder control, fever, headache or weakness on one side at all?" | MISSED | MISSED |
| Head injury (temporality="current", reported_by="patient") | SEG0015 person_1 patient: "no, uh, I haven't had any head injury" | MISSED | MISSED |

**past medical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Epilepsy (status="ongoing", reported_by="patient") | SEG0029 person_1 patient: "hmm you know I've had epilepsy for two years now" | CORRECT | CORRECT |
| Anxiety disorder (status="ongoing", reported_by="patient") | SEG0031 person_1 patient: "I have anxiety." | MISSED | MISSED |

**surgical history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Cholecystectomy (reported_by="patient") | SEG0021 person_1 patient: "just my gallbladder removed, in 2016" | WRONG_NORM ('gallbladder removal') | WRONG_NORM ('gallbladder removal') |

**family history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Colon cancer (relation="uncle", reported_by="patient") | SEG0019 person_1 patient: "Yeah, my uncle had colon cancer." | CORRECT | CORRECT |

**social history**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| exercise (status="current", reported_by="patient") | SEG0023 person_1 patient: "I play badminton on Sundays" | MISSED | MISSED |
| occupation (status="current", reported_by="patient") | SEG0025 person_1 patient: "I run a small shop, so I'm on my feet a lot" | WRONG_STATUS: status: gold="current" pred="" | WRONG_STATUS: status: gold="current" pred="ongoing" |
| living (status="current", reported_by="patient") | SEG0027 person_1 patient: "I share a flat with two friends" | MISSED | MISSED |

**medications**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Sodium valproate (dose="500 mg", frequency="twice a day", status="currently_used") | SEG0005 person_1 patient: "Sodium valproate i take it 500 milligrams twice a day for the fits i'm on escitalopram 10 " | UNSUPPORTED: route: not in gold, pred="oral" | UNSUPPORTED: route: not in gold, pred="oral" |
| Escitalopram (dose="10 mg", frequency="once a day", status="currently_used") | SEG0005 person_1 patient: "Sodium valproate i take it 500 milligrams twice a day for the fits i'm on escitalopram 10 " | UNSUPPORTED: route: not in gold, pred="oral" | UNSUPPORTED: route: not in gold, pred="oral" |

**allergies**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | sodium valproate [INCORRECT - a medication from the medication list written as an allergy] | | |
| *(extra P01)* | sodium valproate [INCORRECT - a medication from the medication list written as an allergy] | | |

**vital signs**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Body temperature (value=36.9, unit="°C", reported_by="doctor") | SEG0034 person_2 doctor: "Okay: temp 36.9 degrees, weight 79 kilos, pulse is 71 beats a minute, pressure 116 over 73" | MISSED | MISSED |
| Body weight (value=79, unit="kg", reported_by="doctor") | SEG0034 person_2 doctor: "Okay: temp 36.9 degrees, weight 79 kilos, pulse is 71 beats a minute, pressure 116 over 73" | WRONG_NORM ('weight') | WRONG_NORM ('weight') |
| Heart rate (value=71, unit="bpm", reported_by="doctor") | SEG0034 person_2 doctor: "Okay: temp 36.9 degrees, weight 79 kilos, pulse is 71 beats a minute, pressure 116 over 73" | MISSED | MISSED |
| Blood pressure (value="116/73", unit="mmHg", reported_by="doctor") | SEG0034 person_2 doctor: "Okay: temp 36.9 degrees, weight 79 kilos, pulse is 71 beats a minute, pressure 116 over 73" | PARTIAL: unit: gold="mmHg" pred="over" | PARTIAL: unit: gold="mmHg" pred="over" |
| Oxygen saturation (value=99, unit="%", reported_by="doctor") | SEG0034 person_2 doctor: "Okay: temp 36.9 degrees, weight 79 kilos, pulse is 71 beats a minute, pressure 116 over 73" | CORRECT | CORRECT |
| Body height (value=156, unit="cm", reported_by="doctor") | SEG0034 person_2 doctor: "Okay: temp 36.9 degrees, weight 79 kilos, pulse is 71 beats a minute, pressure 116 over 73" | WRONG_NORM ('height') | WRONG_NORM ('height') |
| Body mass index (value=32.5, unit="kg/m²", reported_by="doctor") | SEG0034 person_2 doctor: "Okay: temp 36.9 degrees, weight 79 kilos, pulse is 71 beats a minute, pressure 116 over 73" | MISSED | MISSED |
| *(extra P00)* | bmi [UNSUPPORTED]; pulse [EXTRA_SUPPORTED_BY_TRANSCRIPT]; temperature [UNSUPPORTED] | | |
| *(extra P01)* | bmi [UNSUPPORTED]; pulse [EXTRA_SUPPORTED_BY_TRANSCRIPT]; temperature [UNSUPPORTED] | | |

**physical examination**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Alert and oriented (status="present", observed_by="doctor") | SEG0037 person_2 doctor: "you're alert and orientated, speech is clear" | WRONG_NORM ('Alert and orientated') | WRONG_NORM ('Alert and orientated') |
| Symmetrical reflexes and power (status="present", observed_by="doctor") | SEG0039 person_2 doctor: "reflexes and power are symmetrical on both sides" | WRONG_NORM ('reflexes and power are symmetrical on both sides') | MISSED |
| *(extra P00)* | speech is clear [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |
| *(extra P01)* | speech is clear [EXTRA_SUPPORTED_BY_TRANSCRIPT] | | |

**review of systems**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| musculoskeletal (status="negative", reported_by="patient") | SEG0017 person_1 patient: "no, joints are fine" | MISSED | MISSED |
| *(extra P00)* | neurological [UNSUPPORTED] | | |
| *(extra P01)* | neurological [UNSUPPORTED] | | |

**clinical conditions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | breakthrough seizure on known epilepsy [INCORRECT - gold has this fact in category 'clinical assessment'] | | |
| *(extra P01)* | epilepsy [INCORRECT - gold has this fact in category 'past medical history'] | | |

**clinical assessment**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Breakthrough seizure on known epilepsy (certainty="provisional", stated_by="doctor") | SEG0040 person_2 doctor: "Good, that's the examination. Putting it all together, this is probably breakthrough seizu" | WRONG_NORM ('breakthrough seizure on known epilepsy is my leading thought not anything worse') | CORRECT |
| Provoked seizure from missed medication (certainty="differential", stated_by="doctor") | SEG0040 person_2 doctor: "Good, that's the examination. Putting it all together, this is probably breakthrough seizu" | MISSED | MISSED |

**investigations/procedures**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| Electroencephalogram (status="planned", type="other") | SEG0044 person_2 doctor: "let's get an EEG, for seizure i'll request a blood level of the tablet, it'll help with ad" | MISSED | MISSED |
| Antiepileptic drug level (status="planned", type="laboratory") | SEG0044 person_2 doctor: "let's get an EEG, for seizure i'll request a blood level of the tablet, it'll help with ad" | MISSED | MISSED |
| MRI brain (status="conditional", type="imaging") | SEG0045 person_2 doctor: "An MRI of the brain is something we might do if this doesn't improve next month if you hav" | WRONG_NORM ('MRI of the brain') | WRONG_NORM ('MRI of the brain') |
| *(extra P00)* | eeg [UNSUPPORTED] | | |
| *(extra P01)* | eeg [UNSUPPORTED] | | |

**clinical actions**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| investigation/arrange electroencephalogram (status="planned", responsible_person="doctor") | SEG0044 person_2 doctor: "let's get an EEG, for seizure i'll request a blood level of the tablet, it'll help with ad" | MISSED | MISSED |
| investigation/arrange antiepileptic drug level (status="planned", responsible_person="doctor") | SEG0044 person_2 doctor: "let's get an EEG, for seizure i'll request a blood level of the tablet, it'll help with ad" | MISSED | MISSED |
| counselling/advise no driving (status="recommended", responsible_person="patient") | SEG0044 person_2 doctor: "let's get an EEG, for seizure i'll request a blood level of the tablet, it'll help with ad" | MISSED | MISSED |
| counselling/advise medication adherence (status="recommended", responsible_person="patient") | SEG0044 person_2 doctor: "let's get an EEG, for seizure i'll request a blood level of the tablet, it'll help with ad" | MISSED | MISSED |
| counselling/advise taking medication with food (status="recommended", responsible_person="patient") | SEG0044 person_2 doctor: "let's get an EEG, for seizure i'll request a blood level of the tablet, it'll help with ad" | MISSED | MISSED |
| referral/refer to epilepsy clinic (status="planned", responsible_person="doctor") | SEG0044 person_2 doctor: "let's get an EEG, for seizure i'll request a blood level of the tablet, it'll help with ad" | MISSED | MISSED |
| investigation/consider magnetic resonance imaging brain if symptoms persist (status="conditional", responsible_person="doctor") | SEG0045 person_2 doctor: "An MRI of the brain is something we might do if this doesn't improve next month if you hav" | MISSED | MISSED |
| counselling/seek urgent care if you have another seizure lasting more than five minutes (status="recommended", responsible_person="patient") | SEG0045 person_2 doctor: "An MRI of the brain is something we might do if this doesn't improve next month if you hav" | MISSED | MISSED |
| follow up/follow up consultation (status="planned", responsible_person="doctor") | SEG0045 person_2 doctor: "An MRI of the brain is something we might do if this doesn't improve next month if you hav" | MISSED | MISSED |
| *(extra P00)* | investigation/magnetic resonance imaging of the brain is something we might do if this doesn t improve next month [UNSUPPORTED]; follow up/review you in four weeks [UNSUPPORTED]; investigation/request a blood level of the tablet [UNSUPPORTED] | | |
| *(extra P01)* | counselling/set a phone alarm if it helps [UNSUPPORTED]; investigation/magnetic resonance imaging of the brain [UNSUPPORTED]; investigation/request blood level of the tablet [UNSUPPORTED] | | |

**follow up**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| consultation/in four weeks (status="planned", time_reference="in four weeks") | SEG0045 person_2 doctor: "An MRI of the brain is something we might do if this doesn't improve next month if you hav" | MISSED | MISSED |
| *(extra P00)* | consultation/ [UNSUPPORTED] | | |
| *(extra P01)* | consultation/ [UNSUPPORTED] | | |

**clinical uncertainties**

| Gold fact | Transcript evidence (segment) | P00 | P01 |
|---|---|---|---|
| *(extra P00)* | conflicting statement [UNSUPPORTED] | | |
| *(extra P01)* | date uncertain [UNSUPPORTED] | | |

**Not applicable (no gold fact and no prediction):** none.

**Evidence (L).**
- P00: 1 evidence records; 1 are an exact single transcript segment; 29 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_wrong_speaker_id': 1, 'ev_wrong_or_empty_speaker_role': 1, 'ev_empty_supports': 1, 'fact_not_mentioned_in_cited_text': 29, 'fact_cites_intro_segment_unrelated': 29, 'fact_path_missing_from_supports': 29}.
- P01: 1 evidence records; 0 are an exact single transcript segment; 29 facts checked, 0 with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {'ev_multi_segment_or_whole_transcript_dump': 1, 'ev_empty_supports': 1, 'fact_path_missing_from_supports': 28, 'fact_not_mentioned_in_cited_text': 15, 'fact_no_evidence_ids': 1}.
