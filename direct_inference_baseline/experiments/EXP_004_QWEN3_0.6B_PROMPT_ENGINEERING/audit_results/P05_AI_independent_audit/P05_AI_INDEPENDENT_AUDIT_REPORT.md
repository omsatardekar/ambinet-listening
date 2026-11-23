# P05 Validation: AI Independent Technical Audit Report

> This assessment was conducted by an AI system acting in specialist technical-audit roles. It is not a human review, clinician assessment, clinical validation, or approval for real-world healthcare deployment.

Written for: the study owner deciding whether P05 proceeds to another development stage. Scope: the 45 existing audit items in `audit/P05_validation_50/` (30 cited, 15 abstained). P05 is not clinically validated.

## 1. Executive summary

Cited facts (denominator 30, stratified sample, not a population estimate):
- Underlying fact: 14 correct (46.7%), 8 partially correct (26.7%), 7 incorrect (23.3%), 1 not verifiable (3.3%).
- Evidence support: 18 fully supported (60.0%), 4 partially (13.3%), 4 unsupported (13.3%), 4 contradicted (13.3%).
- When the fact was correct, the cited evidence supported it in 14 of 14 cases. Every one of the 8 unsupported or contradicted citations attached to a fact that was itself wrong or fabricated (extraction error, not a retrieval failure).
- 12 of 30 (40.0%) carry a major documentation issue; the serious ones are a medication recorded as an allergy (A10), a wrong prescribed drug (A13), a tenfold dose error (A28), positive findings recorded as absent (A17, A21), fabricated allergy status, follow-up and datetime (A07, A35, A45).
- Speaker attribution (`reported_by`) was incorrect in 7 of 30 (23.3%), mostly patient or nurse statements attributed to the doctor.

Abstained facts (denominator 15): abstention appropriate 6 (40.0%), inappropriate 7 (46.7%), uncertain 2 (13.3%). All 6 appropriate abstentions were on facts that were wrong or vacuous (the abstention rule protected against bad citations). The 7 inappropriate ones were retrieval misses where a clear segment existed: ties between several matching segments (3), vocabulary mismatch such as hypertension versus high blood pressure (3), and a procedure filed under past medical history (1).

Plan threshold: the plan's concern flag (fewer than 75% of cited facts supported) is raised whether "supported" means fully (60.0%) or fully or partially (73.3%).

Recommendation: investigate further before treating P05 as an advancing configuration. The citation layer behaves sensibly given a correct fact; the dominant defects come from the stage-1 extraction (P02) and are only made visible, not fixed, by evidence. Details in section 8.

## 2. Scope and methodology

- Items: A01 to A45 exactly as sampled (seed 20261113); no replacement and no resampling.
- Procedure: read the phase 1 packet (facts and full transcripts, no citations), judged each fact against the transcript, then read the phase 2 packet (system citations or abstentions) and scored evidence, speaker, polarity/context and abstention appropriateness. Rubric fixed in the instruction before any scoring and not altered afterwards.
- Dimensions kept separate: A fact correctness (the fact versus the transcript), B evidence support (does the cited text support the fact as written), C speaker attribution (`reported_by`/`observed_by`/`requested_by` versus who actually spoke), D polarity and context, E documentation quality.
- Rules used: attribute errors (reported_by, relation, unit, extra fields) count under C or E and under A only when the core fact's content is wrong or lost; a fact is "Correct" when its core content is right even if reported_by is wrong. No use of gold labels or the evaluator.
- Confidence: High 34, Medium 10, Low 1 of 45 (see CSV).

## 3. Reviewer role disclosure and independence limits

- The reviewer is an AI acting simultaneously as clinical NLP engineer, documentation auditor, evidence auditor and evaluation lead.
- It is the same AI session that designed, froze and ran P05. It is not independent of the system's design, which is a real bias risk (for example, it may be more forgiving of design choices it made). No external model or person checked these judgments.
- Blindness was only partial. Phase 1 content was read first, but the first rows of the phase 2 packet were seen while inspecting its structure, and the whole phase 2 packet was read before final scoring. Aggregate P05 evaluation results from earlier in this session were also known.
- No label files, evaluator outputs or gold evidence were opened for scoring; the packets contained no gold information (a text search of the audit folder for the word "gold" matched nothing). The system key `audit_key.json` was text-scanned for that word during that search but its content was not read.
- Not a clinician: transcripts are synthetic and the judgments are technical, not clinical.

## 4. Files inspected and access limitations

Read: `audit/P05_validation_50/phase1_blinded_packet.md` (all), `phase2_unblinded_packet.md` (all), the first lines of `phase2_responses_template.csv`. Not read: `audit_key.json` (scanned only, above), `reviewer_form.md`, `sampler_file_access_audit.json`, any label, the 400 locked-test records, the sealed hash file, any model output beyond the packets. No file of the frozen configuration or original outputs was modified; results are only in `audit_results/P05_AI_independent_audit/`.
Limitations of access: only the sampled transcripts were available; whole-record context for facts not in the sample was not examined, so duplicates and omissions across a record could not be checked (see section 7).

## 5. Cited facts (30)

Columns A to E as in the rubric. Segment ids refer to the transcript segment numbers in the packet.

| Item | Enc | Category | Fact | Evidence | Speaker | Polarity/context | Quality | Error category | Reason (segments) |
|---|---|---|---|---|---|---|---|---|---|
| A01 | 00096 | clinical_conditions | Correct | Fully supported | Ambiguous | Correct | Minor issue | reported_by_questionable | Patient states underactive thyroid (SEG0019); doctor confirms it is on record (SEG0020). reported_by=doctor is arguable: patient reported, doctor acknowledged. |
| A05 | 00143 | medical_history.surgical_history | Correct | Fully supported | Correct | Correct | Acceptable | none | Question plus answer 'Just a bypass operation, six years ago' (SEG0024) supports procedure and timeframe. |
| A07 | 00034 | allergies | Not verifiable | Unsupported | Incorrect | Incorrect | Major issue | hallucinated_fact | No allergy question or answer exists in this encounter. Cited SEG0015 is a denial of vomiting blood, abdominal swelling, confusion and black stools, unrelated to allergies. 'No allergies, reported by doctor' is fabricated; truth is not verifiable from the transcript. |
| A08 | 00318 | medical_history.surgical_history | Correct | Fully supported | Incorrect | Correct | Minor issue | reported_by_wrong | Gallbladder removal 2016 stated by the patient (SEG0037) after the doctor's question. reported_by=doctor is wrong (patient). |
| A10 | 00071 | allergies | Incorrect | Contradicted | Correct | Incorrect | Major issue | medication_filed_as_allergy | Patient says 'I take amlodipine ... for my pressure' (SEG0035) and 'never been told I have allergies' (SEG0039). A current medication is recorded as an allergy: patient-safety relevant misclassification. The citation shows the drug is a medication. |
| A11 | 00359 | medical_history.family_history | Correct | Fully supported | Correct | Correct | Acceptable | none | Question plus 'My brother has asthma' supports condition and relation; family history, not the patient's own. |
| A12 | 00322 | negative_findings | Correct | Fully supported | Incorrect | Correct | Minor issue | reported_by_wrong | Patient denies low mood, shortness of breath, blood in stool or fever (SEG0018). Absence of fever is supported. reported_by=doctor is wrong (patient denial). Question (SEG0017) not cited but the answer lists the items. |
| A13 | 00445 | clinical_actions | Incorrect | Contradicted | Correct | Correct | Major issue | wrong_drug_name | Doctor prescribes fluticasone nasal spray 50 mcg daily for four weeks (SEG0043). 'Hydrocortisone nasal spray' is wrong: hydrocortisone is the patient's existing cream (SEG0028). Drug identity error on a prescription; the cited segment itself names fluticasone. |
| A14 | 00436 | physical_examination | Incorrect | Partially supported | Correct | Incorrect | Major issue | exam_manoeuvre_as_finding | Finding 'pressure in the right knee' comes from the doctor's instruction 'A little pressure here, tell me if it's tender' (SEG0012), an exam manoeuvre, not a finding. Actual findings: mild swelling of the right knee, grating (SEG0015), limited flexion (SEG0013). Cited SEG0015 supports site only. |
| A15 | 00395 | clinical_actions | Incorrect | Unsupported | Correct | Incorrect | Major issue | citation_resolves_but_not_semantic | 'Come over here and I'll have a look' (SEG0035) is an invitation to be examined, not a follow-up action. No follow-up is arranged in this encounter. The citation contains the phrase verbatim but does not support a follow-up. |
| A16 | 00203 | procedures_and_investigations | Partially correct | Fully supported | Correct | Correct | Minor issue | schema_misuse | Hearing test planned for hearing loss is stated (SEG0053). type=laboratory is wrong for audiometry. Cited segment is long but contains the relevant sentence. |
| A17 | 00096 | negative_findings | Incorrect | Contradicted | Correct | Incorrect | Major issue | polarity_error | Patient HAS thin bones (SEG0019; doctor confirms in SEG0020). Recorded as an absent finding. The cited answer 'no allergies to anything' (SEG0021) answers a different question and was attached as the 'negative'. |
| A19 | 00039 | vital_signs | Correct | Fully supported | Correct | Correct | Acceptable | none | Doctor reads 'SpO2 97 percent on room air'; value and unit correct. |
| A20 | 00420 | clinical_conditions | Correct | Fully supported | Ambiguous | Correct | Minor issue | reported_by_questionable | Patient reports heart failure (SEG0010); doctor confirms it is on record (SEG0013). Condition correct; reported_by=doctor arguable. |
| A21 | 00223 | negative_findings | Incorrect | Contradicted | Correct | Incorrect | Major issue | polarity_error_and_bad_normalization | Patient has COPD; doctor considers a COPD flare-up possible and prescribes for it (SEG0040, SEG0045). Recorded as an absent finding and normalized to 'coping disorder' (COPD misread). Cited text confirms COPD and then answers a surgery question ('No operations'). |
| A22 | 00203 | vital_signs | Correct | Fully supported | Incorrect | Correct | Minor issue | reported_by_wrong | BP 117/81 is read by the doctor (SEG0043); value and unit correct. reported_by=patient is wrong. |
| A23 | 00417 | physical_examination | Correct | Fully supported | Correct | Correct | Minor issue | noisy_second_citation | SEG0042 'widespread wheeze on both sides' supports the finding. SEG0046 (a long plan paragraph mentioning 'look into wheeze') adds nothing and is unnecessary. |
| A25 | 00021 | symptoms | Correct | Fully supported | Incorrect | Correct | Minor issue | reported_by_wrong | Patient reports a racing heart for about three months (SEG0012). reported_by=doctor is wrong. Segment also contains dizziness (a different symptom). |
| A28 | 00096 | medications | Partially correct | Partially supported | Incorrect | Incorrect | Major issue | wrong_dose_attached | Thyronorm is correct (SEG0025) but the dose is 500 mg; the patient's own statement is 50 micrograms (SEG0027). The 500 mg answer (SEG0025) belongs to Glycomet. A tenfold dose error; the correct dose segment was not cited. Also route='every morning' is not a route, and SEG0019 (diabetes, thyroid, bones) is irrelevant. |
| A30 | 00147 | medical_history.family_history | Partially correct | Fully supported | Correct | Correct | Minor issue | loss_of_specificity | 'My brother has asthma' (SEG0044). Relation recorded as 'family' instead of 'brother'; fact true but less specific. |
| A31 | 00386 | negative_findings | Partially correct | Partially supported | Ambiguous | Ambiguous | Major issue | conflicting_reports_not_represented | Patient denies fever (SEG0030) but the family member says fever was noticed (SEG0031) and the patient then wavers (SEG0032, not cited). Recording 'no fever' as settled hides a documented disagreement. |
| A32 | 00086 | medical_history.family_history | Partially correct | Fully supported | Correct | Correct | Minor issue | loss_of_specificity | 'My sister has thyroid problems' (SEG0013). Relation recorded as 'family', not 'sister'. |
| A35 | 00203 | follow_up | Incorrect | Unsupported | Not applicable | Incorrect | Major issue | hallucinated_fact | Cited statements are 'Let me check your vitals now' and 'I'll examine you now'. No consultation or follow-up is planned in this encounter. The 'now' time reference came from examination phrases. |
| A37 | 00240 | medications | Correct | Fully supported | Not applicable | Correct | Acceptable | none | Alendronate 70 mg once a week stated by the patient after the doctor's question. |
| A39 | 00034 | physical_examination | Correct | Fully supported | Correct | Correct | Acceptable | none | Doctor: 'The whites of your eyes are yellow.' |
| A40 | 00345 | vital_signs | Correct | Fully supported | Incorrect | Correct | Minor issue | reported_by_wrong | Height 162 cm is read out by the nurse (SEG0045). Value and unit correct; reported_by=DOCTOR is wrong (nurse). |
| A41 | 00064 | medications | Correct | Fully supported | Correct | Correct | Acceptable | none | Question plus 'it's Candid cream, twice a day'. Current use supported. |
| A42 | 00081 | symptoms | Partially correct | Fully supported | Correct | Correct | Minor issue | schema_misuse | Patient volunteers morning shakiness (SEG0005). certainty='uncertain' is unsupported (stated plainly) and category 'cardiovascular' is doubtful for a tremor; core symptom correct. |
| A43 | 00021 | clinical_assessment | Partially correct | Unsupported | Correct | Ambiguous | Major issue | vacuous_assessment_wrong_citation | The extracted assessment is the placeholder word 'differential' with basis 'racing heart and dizziness', not the doctor's stated diagnoses (anaemia; thyroid problem also possible, SEG0042, SEG0044). Cited SEG0048 is the ferrous sulfate prescription, not the assessment. |
| A45 | 00223 | procedures_and_investigations | Partially correct | Partially supported | Correct | Correct | Major issue | hallucinated_attribute | Chest X-ray ordered for breathlessness is stated (SEG0041). scheduled_datetime 2023-04-10T10:00:00Z appears nowhere in the transcript; fabricated attribute. |

## 6. Abstained facts (15)

| Item | Enc | Category | System reason | Abstention | Relevant segment? | Error category | Explanation |
|---|---|---|---|---|---|---|---|
| A02 | 00203 | symptoms | ambiguous_many_equal_matches | Inappropriate | Yes | retrieval_miss_tie | Relevant: SEG0005 (also SEG0007). Caregiver states 'trouble hearing in my left ear' (SEG0005); duration given by patient (SEG0007). Clear primary evidence exists. Abstaining on several equal matches was a defensible conservative choice. Attributes certainty='uncertain' and category='cardiovascular' are wrong, an extraction problem. |
| A03 | 00223 | symptoms | polarity_conflict | Appropriate | Ambiguous | extraction_error_fact_invalid | Relevant: SEG0019 (condition, not symptom). 'High blood pressure' as a current symptom is a misclassified history condition (patient says 'yes, high blood pressure', SEG0019); the measured BP was normal (SEG0035). No segment supports it as a current symptom. |
| A04 | 00119 | negative_findings | no_candidate | Appropriate | No | extraction_error_fact_invalid | Relevant: none. The finding text is the word 'absent': a vacuous entity. No segment can support it. |
| A06 | 00021 | clinical_actions | speaker_class_mismatch | Appropriate | No | extraction_error_fact_invalid | Relevant: SEG0025 is a current medication, not an action. 'Take omeprazole, completed, planned, by doctor' is incoherent. Omeprazole is a current home medicine reported by a family member (SEG0025); the doctor prescribes ferrous sulfate (SEG0048). |
| A09 | 00081 | negative_findings | polarity_conflict | Appropriate | No | extraction_error_polarity | Relevant: SEG0005 contradicts. The patient reports morning shakiness (SEG0005, SEG0007); recording it as absent is wrong, so abstaining was correct. |
| A18 | 00367 | clinical_conditions | polarity_conflict | Inappropriate | Yes | retrieval_miss_polarity_rule | Relevant: SEG0022-23, SEG0038. Patient: 'high blood pressure for nearly five years' (SEG0022); doctor confirms (SEG0023) and says 'hypertension that isn't well controlled' (SEG0038). Sufficient evidence; likely blocked by negation-like wording. Retrieval could reasonably cite SEG0022-23. |
| A24 | 00147 | symptoms | ambiguous_many_equal_matches | Inappropriate | Yes | retrieval_miss_tie | Relevant: SEG0005. Patient: 'I've been having headaches for a while' (SEG0005). Many later segments mention headaches, hence the tie, but SEG0005 is the unambiguous primary report. |
| A26 | 00395 | negative_findings | speaker_class_mismatch | Appropriate | No | extraction_error_polarity | Relevant: SEG0003 contradicts. Patient presents with tiredness all the time (SEG0003) and the doctor's impression is persistent tiredness (SEG0039). 'Persistent tiredness absent' is wrong, so abstention was correct. |
| A27 | 00345 | review_of_systems | speaker_class_mismatch | Appropriate | Ambiguous | extraction_error_fact_invalid | Relevant: SEG0005, SEG0011 (positive); SEG0036-40 (urinary negatives). ROS status 'negative' with details 'stress urinary incontinence' is self-contradictory: the patient has urgency and leakage on coughing (SEG0005, SEG0011). Urinary negatives that exist (no burning, no difficulty emptying, no blood) are not what the details say. |
| A29 | 00034 | follow_up | no_anchor_words | Uncertain | Ambiguous | extraction_error_vague_fact | Relevant: SEG0049. Doctor arranges a liver-specialist referral and a next visit (SEG0049). The extracted fact 'consultation, 388.63s' is vague and carries a meaningless datetime; whether it should be cited is debatable. |
| A33 | 00151 | symptoms | ambiguous_many_equal_matches | Inappropriate | Yes | retrieval_miss_tie | Relevant: SEG0003 (also SEG0005). Patient: 'it's a fever for days' (SEG0003), duration SEG0005. Clear primary evidence exists. reported_by=doctor is wrong; fact exists. |
| A34 | 00173 | clinical_assessment | no_candidate | Uncertain | Yes | extraction_error_vacuous_fact | Relevant: SEG0038. Doctor: 'I'm honestly not certain yet. It could be gastro-oesophageal reflux, or it might be gastritis' (SEG0038). The fact consists of placeholder words ('provisional', 'differential'), so no content words exist to retrieve with; the defect is in extraction. |
| A36 | 00345 | allergies | no_candidate | Inappropriate | Yes | retrieval_miss_vocabulary | Relevant: SEG0031-35. Patient: 'no allergies' (SEG0032); caregiver suspects ibuprofen (SEG0033); doctor records the disagreement (SEG0035). Evidence is present, so abstaining was a miss; note the fact 'none' oversimplifies a disputed answer. |
| A38 | 00176 | clinical_conditions | no_candidate | Inappropriate | Yes | retrieval_miss_vocabulary | Relevant: SEG0028. Patient: 'I've got high blood pressure' (SEG0028). 'Hypertension' versus 'high blood pressure' is a vocabulary mismatch; evidence is clear. |
| A44 | 00190 | medical_history.past_medical_history | no_anchor_words | Inappropriate | Yes | retrieval_miss_schema_field | Relevant: SEG0014-15. Patient: 'I had a hernia repair, about five years back' (SEG0015). The fact is a procedure filed under past medical history, which is a category mismatch, and the retrieval found no anchors despite 'hernia repair' being present. |

Denominators: 15 abstained items. Appropriate 6 (40.0%), Inappropriate 7 (46.7%), Uncertain 2 (13.3%). A relevant segment was present in 8 (53.3%), absent in 4 (26.7%), ambiguous in 3 (20.0%). Rates are not combined with the cited-fact results.

## 7. Error categories and examples

Extraction errors (the fact is wrong, so any citation is misleading):
- Polarity inversion: A17 (thin bones, which the patient has, recorded as absent), A21 (COPD flare-up recorded as absent and normalized to "coping disorder"). Same pattern in the abstained A09 and A26, where abstention prevented a false citation.
- Fabricated content: A07 (no allergy discussion exists), A35 (no follow-up exists), A45 (invented scheduled datetime), A29 (meaningless "388.63s").
- Medication/prescription errors: A10 (medication as allergy), A13 (wrong drug, hydrocortisone for fluticasone), A28 (500 mg for Thyronorm, which is 50 micrograms). These are the clinically most dangerous types.
- Exam manoeuvre taken as finding or action: A14, A15.
- Vacuous placeholder facts: A04, A34, A43.
- Attribution: `reported_by` wrong in A08, A12, A22, A25, A28, A40 and doubtful in A01, A20, A31; relation reduced to "family" in A30 and A32. Conflicting reports from patient and caregiver (A31, A36) are flattened into a single answer.
- Schema misuse: A16 (type=laboratory), A42 (certainty, category), medication route field holding a frequency.
Retrieval/evidence errors:
- Citations that resolve but do not support: A15, A35, A43, A07.
- Noise: unnecessary second segments (A23, A28).
- Missed evidence (abstention inappropriate): ties between equal matches A02, A24, A33; vocabulary mismatch A18, A36, A38; field mismatch A44.
Problem categories by cited-fact correctness (small counts, per `cited_by_category` in the JSON): allergies 0 of 2 correct, clinical actions 0 of 2, follow-up 0 of 1, negative findings 1 of 4 correct, physical examination 2 of 3, procedures 0 of 2 fully correct, family history 1 of 3 fully correct. Vital signs 3 of 3, surgical history 2 of 2, clinical conditions 2 of 2, medications 2 of 3 are the best behaved.

Checks requested in the brief that this audit could not complete: omitted prescribed medications, missing follow-up actions, duplicate or contradictory fields, and unsupported assessments beyond the sampled items. These need whole-record review, which the 45-item sample does not provide.

## 8. Overall limitations

- 30 and 15 items, stratified by the sampler for group and reason, so percentages describe this sample, not the 530 cited and 181 abstained facts.
- Single AI reviewer, same session as the builder, partially unblinded (section 3); no inter-rater agreement; judgments on style (minor versus major) are subjective.
- Item-level judgments are checkable in the CSV; Medium and Low confidence items (A29 Low; Medium: A02, A03, A18, A24, A27, A33, A34, A36, A42, A44) should be re-read first by any human reviewer.
- Synthetic transcripts only; no real-world, clinical or safety conclusion.

## 9. Recommendations (no tuning performed)

1. Treat the extraction stage as the primary issue: at least 8 of 30 cited facts are wrong or fabricated, so citation quality cannot exceed fact quality. A later design could add a transcript-grounded fact-validity check before citing, for medications, allergies, polarity and follow-up.
2. Keep abstention for incoherent facts; all 6 abstentions judged appropriate were on wrong or vacuous facts.
3. Examine why sufficient evidence was missed (ties, hypertension versus high blood pressure, procedures filed under past medical history). These were visible in 7 of 15 abstentions.
4. Fix attribution semantics (who counts as the reporter for negatives and vital signs) before any further scoring.
5. Have a human reviewer, ideally not the builder, re-score the same items; the CSV is built for that.
No frozen file was changed and no new experiment was started.

## 10. Final conclusion

- Does the cited evidence generally support the generated facts? Only in part: 60.0% fully, 73.3% fully or partially. It reliably supports facts that are correct (14 of 14) but is attached to wrong facts as well (8 of 30 unsupported or contradicted).
- Were abstentions appropriate? Mixed: 40.0% appropriate and 46.7% inappropriate (misses), with 2 uncertain. They protect against invalid facts but miss clear evidence in about half of the sample.
- Most frequent errors: attribution (7), documentation placeholders and schema misuse (several), polarity/context (8 incorrect). Most serious: medication and allergy errors (A10, A13, A28) and inverted negatives (A17, A21).
- Most problematic categories: allergies, clinical actions, follow-up, negative findings, procedures attributes, family history relation. Better: vital signs, surgical history, conditions.
- Should P05 advance? Further investigation is needed before another development stage; the evidence layer is not the main bottleneck, the underlying facts are.
- What this audit cannot establish: clinical accuracy or safety, performance on the full 50 records or any other data, true recall, duplicates or omissions across whole records, inter-rater reliability, or independence from the system's builder.

This assessment was conducted by an AI system acting in specialist technical-audit roles. It is not a human review, clinician assessment, clinical validation, or approval for real-world healthcare deployment.
