# P05 Root-Cause Investigation (Stage 1 first)

Written for: the study owner deciding what to fix before another development stage. Investigation only: nothing was implemented, no frozen P00-P05 artifact, the dataset, or the validation outputs were modified, no model was run, and the locked-test records, labels and sealed hash file were not touched.

> Findings are diagnostic hypotheses from one 50-record validation set that is now consumed, backed by counts from the stored outputs. They are not proof of cause (no counterfactual runs were made) and not clinical conclusions. The AI audit findings they rest on were produced by the same session that built P05.

## 1. Bottom line

1. The audited clinical errors were created by the Stage-1 model's single-pass JSON generation, not by Python. In all 50 records the parsed JSON equals the raw model JSON (two raw outputs carry ```json fences that the parser strips; no content is changed). The evidence builder touches only evidence fields (integrity check passed in all 50). So the parser, validator and builder introduced none of the audited fact errors.
2. The Python pipeline has two real weaknesses of its own: (a) it cannot read facts the model puts in the wrong container shape (20 of 50 records give `clinical_assessment` as a bare object instead of a list, and 14 of 50 give `follow_up` that way; the frozen evaluator and the P05 pipeline skip them), and (b) retrieval cites any lexical match for a wrong fact, and it misses clear evidence in 7 of the 15 audited abstentions (ties, vocabulary, one mis-sectioned item).
3. The highest-risk model failure patterns are: medication filed as an allergy, doses carried to the wrong drug, two drugs fused into one entry, prescribed drugs left out (14 of 20 prescription phrases, heuristic), a polarity inversion in negative findings, wrong `reported_by`, and invented follow-ups, dates and allergy statuses.
4. Several failures trace to the P02 prompt itself (instructions that push a 0.6B model to fill sections, replace lay terms, and produce a very large schema) and to the schema size (about 17 sections in one pass). These are hypotheses to test, not established.

## 2. Method and data used

- Inputs read: the 45 audit scores (`audit_results/P05_AI_independent_audit/`), P02 raw responses and parsed JSON (`outputs/P05_validation_50/stage1/`), P05 decisions, the P02 prompt, the 50 validation transcripts (inputs only), the retrieval source `p05_retrieval.py` (read only).
- Not read: any label file, evaluator gold results, locked-test data. The consumed validation set was used only to characterise error patterns, never to tune.
- Scripts used are saved in `analysis_scripts/` (read-only analyses; they write nothing to project data). Counts below are produced by them. Several are heuristics (marked "heuristic") that use transcript text only.
- Corpus size: 50 records, 661 emitted entities in the list sections (711 facts including the 50 chief complaints).

## 3. Component trace (what each stage did to the audited items)

| Stage | Role | Finding |
|---|---|---|
| Prompt build | P02 prompt + transcript with timestamps `[SEGxxxx] speaker (ROLE) a-b s: text` | Prompt asks for 17 sections, evidence ids, quality checks, normalization to medical terms; contains no date or example facts. |
| Model (Stage 1) | Qwen3-0.6B, greedy, one pass, 624-3277 output tokens | Origin of all 8 incorrect or unverifiable cited facts and of 10 of the 15 audited abstentions (the other 5 originate in retrieval). |
| Parser | strips fences, `json.loads` | Raw == parsed for 50/50 after fence removal (00034 and 00173 had fences). No defect. |
| Validator / evaluator | counts malformed containers as empty | Loses 20 `clinical_assessment` and 14 `follow_up` objects (shape errors by the model; no repair step exists). |
| Retrieval (P05 Stage 2) | lexical match to a segment, abstains on rule conflicts | Cited a text-overlapping segment for every wrong fact (8 of 8 unsupported or contradicted citations); missed evidence in 7 of 15 abstentions. |
| Evidence builder (P05 Stage 3) | formats evidence from the transcript | No defect found; minor noise from the extra question or second segment (A23, A28). |

## 4. Per-item classification of the 45 audit findings

RC codes: **M1** wrong section or schema/enum/placeholder, **M2** attribute carry-over or entity fusion, **M3** polarity inversion, **M4** fabrication, **M5** wrong `reported_by`, **M6** loss of specificity or conflict flattening, **P1** prompt design conflict, **R1** retrieval cites for a wrong fact, **R2** retrieval miss (tie, vocabulary, negation cue, field mapping), **N** none.
"Primary" is where the error originated; "secondary" is a contributing stage.

| Item | Primary (stage) | Secondary | Trace and likely cause |
|---|---|---|---|
| A01 | M5 model | | Patient said it, doctor confirmed; `reported_by: doctor`. |
| A02 | R2 retrieval tie | M1 (category cardiovascular, certainty uncertain) | Equal matches in SEG0005, 0051, 0053. |
| A03 | M1 model | | Hypertension is emitted as a symptom (section confusion); cause: the model lists conditions twice. |
| A04 | M1 model | | Finding text is the word "absent" (schema token copied). |
| A05 | N | | |
| A06 | M1/M4 model | | Current home drug emitted as "completed action by doctor". |
| A07 | M4 model | P1, R1 | `allergies: none` in a record with no allergy question; prompt rule "do not leave a section empty" is a plausible driver; retrieval then cited an unrelated denial. |
| A08 | M5 model | | Patient statement attributed to doctor. |
| A09 | M3 model | | Patient's own symptom emitted as an absent finding. |
| A10 | M1 model | R1 | Amlodipine is in both `medications` (correct) and `allergies` (wrong); the allergy question follows the medication turns. Same pattern in 00386 (Seretide) and 00445 (hydrocortisone). |
| A11 | N | | |
| A12 | M5 model | | Patient denial attributed to doctor. |
| A13 | M2 model | | In 00445, the existing hydrocortisone cream received the new nasal spray's dose (50 mcg), route (nasal), duration (4 weeks) and indication; the prescription entry says "hydrocortisone nasal spray"; fluticasone is absent from the whole output. |
| A14 | M4 model | | Doctor's instruction "A little pressure here" copied as an exam finding. |
| A15 | M4 model | R1 | "I'll have a look" copied as a follow-up action. |
| A16 | M1 model | | `type: laboratory` for a hearing test. |
| A17 | M3 model | R1 | Thin bones (a patient condition) emitted as an absent finding. Retrieval then attached the allergy answer to a doctor turn that mentions thin bones before a different question. |
| A18 | R2 retrieval (vocabulary, negation cue) | P1 | The model replaced "high blood pressure" by "hypertension" as asked; the only lexical match "hypertension that isn't well controlled" has a negation cue, so the polarity rule abstained. |
| A19 | N | | |
| A20 | M5 model | | As A01. |
| A21 | M3 model | R1, normalization drift | COPD flare-up emitted as absent and normalized to "coping disorder" in four sections of 00223. Retrieval attached the surgery answer to the turn that mentions COPD. |
| A22 | M5 model | | Doctor-read value attributed to patient. |
| A23 | N | R1 minor (noisy second segment) | |
| A24 | R2 retrieval tie | | Headache mentioned in many segments. |
| A25 | M5 model | | |
| A26 | M3 model | | Chief complaint "tiredness" emitted as an absent finding. |
| A27 | M1 model | | Status "negative" with positive details (contradictory). |
| A28 | M2 model | R1 noise | Glycomet's "500 milligrams" copied to Thyronorm; the true 50 micrograms appears in the next patient turn. |
| A29 | M4 model | | `normalized_datetime: 388.63s` is a transcript timestamp (SEG0050 starts at 389.2s). |
| A30, A32 | M6 model | | Relation "family" instead of brother or sister. |
| A31 | M6 model | P1 | Conflict between patient and family member flattened; `clinical_uncertainties` is empty in 50 of 50 records. |
| A33 | R2 retrieval tie | M5 | |
| A34 | M1 model | | Assessment equals the schema word "provisional". |
| A35 | M4 model | R1 | Exam talk ("I'll examine you now") emitted as a planned consultation. |
| A36 | M1 model | R2 | "No allergy" represented as an allergy named "none" (invalid enum); no anchor words to retrieve. |
| A37 | N | | |
| A38 | R2 retrieval (vocabulary) | P1 | "hypertension" versus "high blood pressure". |
| A39 | N | | |
| A40 | M5 model | | Nurse reading attributed to the doctor. |
| A41 | N | | |
| A42 | M1 model | | Category `cardiovascular`, certainty `uncertain` (see 5.5). |
| A43 | M1 model | R1 | Placeholder assessment; retrieval cited the prescription. |
| A44 | M1 model | R2 | Surgical item placed in past-medical-history with a `procedure` key; retrieval queries only `condition` fields there, so it found no anchors. |
| A45 | M4 model | | Invented ISO timestamp. |

Tally by primary origin (45 items): Stage-1 model 33 (M1 11, M5 7, M4 6, M3 4, M6 3, M2 2); retrieval 5 (A02, A18, A24, A33, A38); none 7 (A05, A11, A19, A23, A37, A39, A41; A23 has a minor retrieval noise note). Of the 15 abstained items, 10 originate in the model (A03, A04, A06, A09, A26, A27, A29, A34, A36, A44) and 5 in retrieval; the 7 abstentions judged inappropriate in the audit are those 5 plus A36 and A44, whose cause is a model format error that retrieval could not handle.
Counts are by item; many items also carry a secondary cause, shown in the table.

## 5. Recurring patterns (corpus-wide, all 50 stored outputs)

### 5.1 Section and schema confusion
- 16 of 38 allergy entries are the placeholder `none` (invalid `allergy_type`); 5 of the 16 sit in records with no allergy question (00034, 00203, 00375, 00395, 00404). The prompt itself says denied allergies belong in `negative_findings`.
- 3 of 38 allergy substances duplicate a listed medication (00071 amlodipine, 00386 Seretide, 00445 hydrocortisone).
- Enum violations: `clinical_actions.action_type` 15 (e.g. consultation, prescription, examination, a test name), `allergy_type` 16, `responsible_person` upper case 8, `symptoms.status: current` 4.
- Placeholder entities: 5 negative findings named "absent", 6 assessments that are the words provisional or differential.
- Container shape: `clinical_assessment` is a bare object in 20 of 50 records; `follow_up` in 14 of 50 (the content is often valid, e.g. "Ankle swelling possibly from a blood pressure tablet").

### 5.2 Polarity and negation
- Only one negative finding per record in 47 of 50 records (53 total), although the prompt asks for every denied finding; the transcripts deny many items each (visible in the audited encounters).
- Heuristic: 21 of 53 negative findings share a word with a positive symptom or condition of the same record (for example jaundice, cough, thin bones, fever). This is an upper bound on inversions because a record may contain both a denial and a positive for related words.
- Audited inversions: A09, A17, A21, A26.

### 5.3 Medication identity and dose
- 14 of 20 doctor prescription phrases (heuristic: "let's use", "I'll start you on", "I'm prescribing", "the treatment will be", ...) name a drug that is absent from `medications` and `clinical_actions` (examples: fluconazole 00064, clopidogrel 00359, tamsulosin 00143, lactulose 00139, ferrous sulfate 00021). Spot-check: 8 of 9 such drugs occur nowhere in the output.
- Dose provenance (heuristic, 43 doses parsable): 32 occur in a segment naming the drug, 8 in the next two segments, 3 only elsewhere in the transcript (Seretide 20 mg in 00386 and 30 mg in 00417, hydrocortisone cream 50 micrograms in 00445). A28 is not caught by this check because the wrong number is in the same segment as the drug; the transcript puts the dose before the drug name ("It's 500 milligrams. It's Thyronorm, every morning.").
- 17 medication `route` fields are not routes (for example "every morning", "day to day", "once a week").

### 5.4 Speaker attribution
- Among cited patient-origin facts whose answer segment is spoken by the patient (172): `reported_by` patient 76 (44%), doctor 69 (40%), empty 27 (16%). Values are also mixed-case (PATIENT 41, DOCTOR 34 against lower case 88 and 220). Negatives and vitals may follow different conventions, so 40% is a conservative reading.

### 5.5 Fabricated and defaulted values
- 10 procedures have a non-null `scheduled_datetime`; only 3 of those transcripts mention any date or weekday. In 00223 the same invented timestamp 2023-04-10T10:00:00Z occurs in five fields of the raw output (a self-copy pattern).
- 27 of 57 symptoms are labelled `cardiovascular` (body-site and certainty also default: 30 of 57 `uncertain`). The label bears no relation to the symptom (headache, hearing loss, fever, racing heart); a default attractor.
- 34 of 518 checked entities have no content word in the transcript: 12 negative findings (mostly "absent"), 8 allergies ("none"), 7 vitals (names written as "temperature" while the transcript says "temp"; a lexical artifact, not an invention), 5 assessments, 2 others.
- Normalization drift: 4 fields in one record ("COPD flare-up" to "coping disorder").
- No exact duplicates within a section were found.

### 5.6 Conflict and uncertainty handling
- `clinical_uncertainties` is empty in 50 of 50 records. Disputed reports (A31, A36) are therefore flattened to one value.

### 5.7 The model's own evidence is unusable
- 385 of 540 entities have empty or missing `evidence_ids`; 123 point only to EV_001, which holds the first segment text. This confirms why P05 replaced model citations by retrieval, and shows the evidence-id task consumes output tokens without value.

## 6. Model reasoning failures versus Python failures

Model reasoning or generation failures (Stage 1): section confusion (medication to allergy, condition to symptom), polarity inversion, attribute carry-over and entity fusion, omission of prescribed drugs, copying of schema words and instruction phrases as facts, defaulted category and certainty, invented timestamps, wrong `reported_by`, loss of kinship detail, ignoring the uncertainty section, malformed container shape.

Python failures:
- No container-shape normalization (lost `clinical_assessment` and `follow_up` objects).
- Retrieval: (a) attaches the answer after a doctor turn that holds several statements and a question, even when the matched words sit in the statement (A17, A21); (b) no validity gate, so it cites lexical overlap for a wrong fact (A07, A15, A35, A43); (c) abstains on ties instead of preferring the first patient statement (A02, A24, A33); (d) no lay-to-medical term mapping (A18, A38); (e) negation cue "isn't well controlled" is read as a polarity conflict (A18); (f) uses only the fields of the declared category, so a mis-sectioned item has no anchors (A44).
- No Python failure in parsing or evidence building was found. The P05 pipeline never alters a fact (integrity check).

## 7. Prompt-level contributors (hypotheses)

- "Do not leave a section empty if the transcript supports it" and "every allergy stated" may push the model to emit something when nothing was said (A07, `none` allergies).
- "Replace everyday wording by the medical term" in normalized fields: the model also normalizes the plain field, which breaks lexical retrieval (hypertension) and caused drift (coping disorder).
- The prompt both says denied allergies go to `negative_findings` and offers an allergies section with `severity` and `status` fields; the model often resolves this by writing `none` in allergies.
- The output schema has about 17 sections with many empty fields, evidence ids, quality checks and confidence fields; the model spends its limited capacity on boilerplate (mean output 1,426 tokens) and copies example tokens.
- The first segments of each transcript appear in the evidence records (EV_001), indicating the model anchors on the start of the prompt.

## 8. High-risk priority list

1. Medication identity: allergy confusion, fusion, omissions. (A10, A13; 14 of 20 prescriptions)
2. Medication dose: carry-over to a neighbouring drug. (A28)
3. Allergy status: invented `none`, placeholder representation. (A07, A36; 16 entries)
4. Negation and positive/negative findings. (A09, A17, A21, A26; one negative per record)
5. Speaker attribution. (8 audited cited items; 40% wrong in the corpus read)
6. Fabricated follow-up, dates and actions. (A15, A29, A35, A45; 10 invented datetimes)
7. Container-shape losses (20 and 14 records) and malformed enums.

## 9. What this investigation cannot show

- Which cause is dominant: no counterfactual experiment (for example removing the evidence fields or shrinking the schema) was run.
- True omissions: only a trigger-phrase heuristic for prescriptions and a lexical check for allergy questions; no gold comparison was used by design.
- Whether the same patterns hold outside this synthetic data and these 50 records.
- Whether any of this matters clinically; none of it validates or approves the system.

This assessment was conducted by an AI system acting in specialist technical-audit roles. It is not a human review, clinician assessment, clinical validation, or approval for real-world healthcare deployment.
