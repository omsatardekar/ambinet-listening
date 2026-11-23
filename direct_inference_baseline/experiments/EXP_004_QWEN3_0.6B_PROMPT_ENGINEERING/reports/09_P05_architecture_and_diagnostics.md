# P05 - P02 extraction + conservative retrieval-based evidence: architecture proposal and zero-inference diagnostics (DESIGN ONLY)

Written for: you (review before any experiment). **No model inference was run and no GPU was used.** P00-P04, the frozen dataset, labels, schema and evaluator are unmodified; P02 artifacts were only read (all P05 outputs are in `p05_diagnostics/` and `dev_safeguards/`).
P04 is recorded as **REJECTED AS DESIGNED** (smoke test on 5 records; all five outputs, logs, metrics, prompts and reports preserved). P02 remains the best extraction prompt at the development stage (KEEP, development only; not validated, not final; validation postponed).

## 0. Summary of findings
1. **Arm R re-examined.** R_simple's higher agreement comes with behaviours you rejected. Among the facts it cites (50 prompt_dev records, gold facts used as queries): 24.4% are question-only citations, 16.0% are greeting-like lines, 23.3% sit on SEG0001, 18.0% have a polarity conflict and 22.9% come from the wrong speaker class. R_main removes the greeting problem by abstaining but still has question-only (20.7%), polarity (21.1%) and speaker (20.3%) problems and loses agreement.
2. **A conservative retrieval method can retain agreement while rejecting these cases.** The proposed R_cons (v4) on the 153 P02 facts that strictly match a gold item: cites 93.5%, **98.6% of cited facts hit a gold-cited segment**, 92.2% counting abstentions as misses (R_simple 88.9%, R_main 81.0%), with no question-only, SEG0001, kinship or speaker-class cases among cited items; the post-hoc detectors still flag a small residual: greeting-like 2.1% and polarity 1.4% of cited matched facts (0.4% and 0.2% on gold facts). A 'greeting-like' flag also fires on an opening sentence that contains both a greeting and the complaint, so it is not always an error; each flagged case still has to be read. On all 1,860 gold facts used as queries it cites 79.4% with 99.2% hit when cited.
3. **The price is abstention:** on all 679 facts P02 extracted, R_cons v4 abstains on 186 (27.4%). Whole categories are lexically unreachable (review of systems 20%, clinical uncertainties 16%, clinical actions 37% of gold facts have a matching word in a cited segment), so they will mostly carry no evidence.
4. **Semantic reading (mine, not independent).** In a stratified sample of 36 retrieved citations I judged 30 appropriate, 3 questionable and 3 wrong. The errors are mostly spurious extracted items that receive a plausible-looking citation; retrieval cannot fix extraction errors and can lend them false authority.
5. **Development caveats.** The rules were calibrated on the same 50 prompt_dev records and revised four times after looking at results (v1 -> v4, all disclosed in section 4). The numbers are development results, not independent; the preserved validation subset must be used once, after a freeze.
6. **Locked-test disclosure (section 1 and `reports/08_locked_test_access_audit.md`).** A new development-only guard hashes only approved ids and was tested with a file-access spy (0 locked-test files, 0 labels, sealed hash file never opened).

## 1. Locked-test access audit and safeguards (summary; full record in `reports/08_locked_test_access_audit.md`)
* **What happened (measured).** The existing runner's frozen-dataset check re-hashes all 500 input transcripts at the start of every `run_inference` call: 500 transcripts opened, 400 of them locked-test transcripts, 0 labels. Separately, a *full* integrity check (1,001 files, including the 400 locked-test labels, SHA-256 only) ran in the EXP_003 post-run evaluation scripts and at the start of one EXP_001 supplementary probe. Bytes were read for checksums only; no locked-test content was parsed, rendered, used in a prompt, analysed or evaluated, and no locked-test label content was ever read by any experiment code.
* **Safeguard built and tested (zero inference).** `experiments/dev_guard.py` (run-time redirect; no existing file changed): `settings.verify_frozen_dataset` is replaced by a check that hashes only explicitly requested prompt_dev ids (inputs only unless labels are requested); `settings.MANIFEST_CSV` is redirected to a 100-row development manifest; locked-test hashes are kept apart in a sealed file (`dev_safeguards/locked_test_checksums.SEALED.sha256`) that development code never loads; validation ids need an explicit flag. Test (`evaluation/dev_guard_test.json`): existing check opened 503 files including 400 locked-test transcripts; guarded check opened 7 files (the 5 requested transcripts and metadata), locked-test files 0, labels 0, sealed file opened: False; tampering detected; non-approved and validation ids rejected.
* **P05's retrieval stage needs none of this:** it reads only existing P02 outputs and the development transcripts. The guard matters for any future inference run.

## 2. Architecture
```
Stage 1  frozen P02 prompt + Qwen3-0.6B (unchanged model, settings, outputs; existing P02 outputs are reused for diagnostics)  ->  extracted facts (P02 JSON)
Stage 2  retrieval (Python, transcript + extracted fact only; no labels): candidate segments per fact
Stage 3  conservative filtering: no fallback, question handling, speaker class, polarity, kinship, value, ambiguity, ABSTENTION with reason code
Stage 4  existing evidence builder (experiments/evidence_builder.py, unchanged): ids -> evidence records + supports -> final frozen-schema JSON
```
P02 extraction is untouched; the builder only adds evidence fields (integrity check `verify_only_evidence_changed` passed for 50/50 records in every variant; extraction counts are identical to P02: strict TP/FP/FN 153/522/1707). A fact with no accepted segment keeps `evidence_ids: []` (the builder never invents a reference); abstentions are recorded with a reason code in a side file, not in the schema.

## 3. Arm R investigation: R_main vs R_simple, and what a conservative method keeps
Arm R recap (50 records, P02 outputs): R_simple 88.9% and R_main 81.1% gold-segment agreement on 153 matched facts; R_simple falls back to SEG0001 for 76 facts. The ladder below applies the same data to a stepwise build-up of the conservative method. Rows R_simple and R_main re-implement the Arm R configurations (they reproduce 88.9% and 81.0% on the 153 matched facts, i.e. the Arm R figures up to one fact).
**Evaluation sets.** (B) 1,860 gold facts of the 50 prompt_dev records used as the "extracted facts" (their gold-cited segments are the reference; this isolates retrieval quality from extraction quality and gives enough facts per category, including negative findings, which P02 never matched). (A) 153 P02 facts that strictly match a gold item (real model wording, small n). (C) all 679 P02 facts (no reference; used for abstention behaviour).
**Table 1 - ladder on gold facts (B).** Hit = a selected segment is one of the gold-cited segments. "Hit when cited" excludes abstentions; "hit, abstentions as misses" does not.
| Step | cited | hit when cited | hit, abstentions as misses | set precision | set recall |
|---|---|---|---|---|---|
| R_simple | 100.0% | 65.9% | 65.9% | 65.9% | 37.6% |
| R_main | 77.4% | 94.9% | 73.5% | 94.9% | 42.0% |
| C1 coverage, no fallback | 86.1% | 92.3% | 79.5% | 92.3% | 45.4% |
| C2 + specificity | 86.1% | 92.3% | 79.5% | 92.3% | 45.4% |
| C3 + question->answer | 85.3% | 92.2% | 78.7% | 92.0% | 49.7% |
| C4 + speaker class | 84.4% | 96.5% | 81.4% | 96.8% | 51.3% |
| C5 + polarity | 78.9% | 95.6% | 75.5% | 96.0% | 47.5% |
| C6 + kinship | 78.9% | 95.8% | 75.6% | 96.2% | 47.6% |
| C7 + vital value | 78.9% | 96.3% | 76.0% | 96.6% | 47.8% |
| C8 + ambiguity (= R_cons v1) | 77.2% | 98.4% | 76.0% | 87.9% | 50.5% |
| C5b item-aware polarity (v2) | 81.5% | 96.5% | 78.6% | 96.8% | 49.7% |
| C7b v2 through vital value | 81.5% | 97.1% | 79.1% | 97.4% | 50.0% |
| C8b + ambiguity (= R_cons v2) | 79.6% | 99.2% | 79.0% | 88.5% | 52.7% |
| C8c + local negation cue (= R_cons v3) | 79.4% | 99.2% | 78.8% | 88.5% | 52.5% |
| C8d + context question for short replies (= R_cons v4) | 79.4% | 99.2% | 78.8% | 88.3% | 60.0% |

**Table 2 - ladder on the 153 P02 facts that match gold (A).**
| Step | cited | hit when cited | hit, abstentions as misses | set precision | set recall |
|---|---|---|---|---|---|
| R_simple | 100.0% | 88.9% | 88.9% | 88.9% | 45.5% |
| R_main | 97.4% | 83.2% | 81.0% | 83.2% | 41.5% |
| C1 coverage, no fallback | 100.0% | 86.9% | 86.9% | 86.9% | 44.5% |
| C2 + specificity | 100.0% | 86.9% | 86.9% | 86.9% | 44.5% |
| C3 + question->answer | 100.0% | 86.9% | 86.9% | 86.1% | 45.5% |
| C4 + speaker class | 97.4% | 94.0% | 91.5% | 93.5% | 47.8% |
| C5 + polarity | 94.1% | 94.4% | 88.9% | 94.4% | 45.5% |
| C6 + kinship | 94.1% | 94.4% | 88.9% | 94.4% | 45.5% |
| C7 + vital value | 94.1% | 95.8% | 90.2% | 95.8% | 46.2% |
| C8 + ambiguity (= R_cons v1) | 91.5% | 97.9% | 89.5% | 90.6% | 48.5% |
| C5b item-aware polarity (v2) | 96.1% | 93.9% | 90.2% | 93.4% | 47.2% |
| C7b v2 through vital value | 96.1% | 95.2% | 91.5% | 94.7% | 47.8% |
| C8b + ambiguity (= R_cons v2) | 93.5% | 98.6% | 92.2% | 89.5% | 51.2% |
| C8c + local negation cue (= R_cons v3) | 93.5% | 98.6% | 92.2% | 89.5% | 51.2% |
| C8d + context question for short replies (= R_cons v4) | 93.5% | 98.6% | 92.2% | 86.4% | 57.2% |

**Table 3 - behaviours you asked to eliminate, among CITED facts (B, gold facts).** Detectors are applied to every method's selection after the fact (polarity: a positive fact whose words are negated in its evidence, or a negative finding with no negation cue; kinship: a family-history fact without a kin term, or an own-history fact in a kin clause; speaker class: non-question evidence from the wrong speaker class for the categories where >= 95% of gold evidence has one class).
| Method | question-only | greeting-like | at SEG0001 | polarity conflict | kin conflict | speaker-class conflict |
|---|---|---|---|---|---|---|
| R_simple | 24.4% | 16.0% | 23.3% | 18.0% | 0.5% | 22.9% |
| R_main | 20.7% | 0.0% | 0.0% | 21.1% | 0.1% | 20.3% |
| R_cons v4 | 0.0% | 0.4% | 0.0% | 0.2% | 0.0% | 0.0% |

Reading: question-only citations, SEG0001 picks, kinship conflicts and speaker-class conflicts are removed by construction in R_cons. The greeting-like and polarity detectors keep a small residual (0.4% and 0.2% on gold facts; 2.1% and 1.4% on matched P02 facts; 0.8% and 1.4% on all P02 facts): the greeting-like detector also flags opening sentences that contain a greeting and the complaint, and the polarity detector uses a wider window than the filter's local rule. These cases are not guaranteed errors but must be read in any audit.

## 4. Retrieval algorithm and candidate-selection rules (R_cons v4)
Pure function of the transcript and one extracted fact (`experiments/p05_retrieval.py`; parameters are module constants fixed before results: stem length 5, TAU 0.6, specificity df <= max(3, 15% of segments), band 0.05, at most 3 tied segments, short reply <= 10 words).
1. **Anchors.** Content words (the evaluator's tokeniser) of the fact's descriptive fields (per-category field list: name, normalised name, body site, finding, condition, procedure, substance, reaction, system, description, relation excluded...). Vital signs also get generic abbreviation synonyms (blood pressure -> pressure, temperature -> temp, heart rate -> pulse, ...).
2. **Candidates.** A segment is a candidate if, for at least one field, the IDF-weighted share of that field's anchors found in the segment is >= 0.6 (field-wise maximum, so the spoken plain wording suffices when the standard term was not spoken), and at least one matched anchor is *specific* (rare in the encounter). **No fallback:** no candidate -> abstain (`no_candidate` / `only_generic_matches` / `no_anchor_words`).
3. **Question handling.** A question line is context, never proof. A candidate that is a question is replaced by its answer (next non-question line of the other speaker) if the answer itself contains the anchors; if the answer is a short reply it cannot be read without the question, the pair is kept; a question without a usable answer is dropped. In v4, a *short reply* selected on its own (<= 10 words, directly after a question by the other speaker) also gets its question added.
4. **Speaker class.** Hard rule only where the gold probe shows >= 95% purity of non-question evidence: clinician for vital signs, examination, assessment, procedures, clinical actions, follow-up; patient side (patient, caregiver, family member) for chief complaint, surgical and family history, allergies, review of systems, negative findings. No rule elsewhere (patient/doctor mixes are common). The model's own `reported_by` is *not* used (P02's role fields are unreliable: 42% speaker attribution).
5. **Polarity.** A negative finding needs a negation cue next to its anchor (or a negative short reply); any other fact whose own wording is not an absence is rejected when its anchor is negated in the evidence; facts that are themselves absences outside negative findings (status absent/negative/never/none or a negation word in their wording) get no polarity constraint because it cannot be validated lexically.
6. **Kinship.** A family-history fact needs a kin term in its evidence; an own-history fact is rejected when its anchor sits in a kin clause without a first-person marker.
7. **Value.** A vital sign with a numeric value needs those numbers in the evidence.
8. **Ambiguity.** Survivors within 0.05 of the best score are all cited (genuine repeats), at most 3; more -> abstain (`ambiguous_many_equal_matches`).
**Abstention reason codes:** no_anchor_words, no_candidate, only_generic_matches, question_without_answer, speaker_class_mismatch, polarity_conflict, kinship_conflict, value_not_in_evidence, ambiguous_many_equal_matches.
**Revision history (disclosed).** v1 (as first written and fixed before results) -> polarity rule rejected positives whenever any anchor was negated, which cost 5.5 points of coverage on gold facts in sections that legitimately hold negatives (social history, examination, assessment, review of systems) -> **v2** item-aware polarity (post-hoc) -> reading the review sample showed a symptom filed as a negative finding passed because the cue could be anywhere in the segment -> **v3** local negation cue (post-hoc) -> the same review showed a bare "No, none of that at all." cited without its question -> **v4** context question (post-hoc). Each step was motivated by what I read on prompt_dev; none was tested on held-out data. Parameter sensitivity (TAU 0.5/0.6/0.7, short-reply 10/25 words; `p05_sensitivity.json`) moves hit-when-cited by under 0.4 points and coverage by under 3.7 points; parameters were left at their a-priori values.

## 5. Safe abstention strategy
* Abstain (cite nothing) whenever no segment passes all rules; never fall back to an early line, the best of poor matches or the model's own guess; never create a reference outside the transcript (the builder rejects invalid ids).
* Abstention costs coverage, not correctness: on 679 P02 facts R_cons v4 cites 493 and abstains on 186 (27.4%). Reasons: {"ok": 493, "no_candidate": 50, "speaker_class_mismatch": 45, "ambiguous_many_equal_matches": 33, "value_not_in_evidence": 1, "polarity_conflict": 38, "no_anchor_words": 13, "kinship_conflict": 6}. v1 abstained on 28.6% before the polarity and context revisions. By comparison Arm R's R_main left 11.6% uncited and R_simple 1.9% (it never abstains by design; its few uncited facts had no anchors at all).
* Reporting rule for any experiment: coverage (cited/total) and correctness-when-cited are reported separately and never merged; an abstained fact is "no evidence", not "wrong evidence".
**Table 4 - per category (gold facts used as queries, v4).**
| Category | gold facts | cited | hit when cited | main abstention reasons (v4) |
|---|---|---|---|---|
| chief_complaint | 50 | 98.0% | 100.0% | {"polarity_conflict": 1} |
| symptoms | 150 | 85.3% | 94.5% | {"ambiguous_many_equal_matches": 16, "polarity_conflict": 4, "question_without_answer": 2} |
| negative_findings | 273 | 98.2% | 100.0% | {"polarity_conflict": 4, "question_without_answer": 1} |
| medical_history.surgical_history | 27 | 100.0% | 100.0% | {} |
| medical_history.family_history | 29 | 100.0% | 100.0% | {} |
| medical_history.social_history | 151 | 93.4% | 100.0% | {"polarity_conflict": 7, "no_candidate": 3} |
| medications | 128 | 96.1% | 100.0% | {"polarity_conflict": 3, "ambiguous_many_equal_matches": 2} |
| vital_signs | 219 | 95.0% | 100.0% | {"question_without_answer": 7, "speaker_class_mismatch": 4} |
| review_of_systems | 70 | 20.0% | 100.0% | {"no_candidate": 50, "question_without_answer": 1, "speaker_class_mismatch": 5} |
| clinical_assessment | 89 | 83.1% | 98.6% | {"polarity_conflict": 15} |
| procedures_and_investigations | 82 | 91.5% | 98.7% | {"polarity_conflict": 6, "speaker_class_mismatch": 1} |
| clinical_actions | 266 | 30.5% | 100.0% | {"no_candidate": 168, "polarity_conflict": 13, "question_without_answer": 2, "speaker_class_mismatch": 2} |
| follow_up | 45 | 82.2% | 91.9% | {"speaker_class_mismatch": 5, "question_without_answer": 3} |
| medical_history.past_medical_history | 94 | 91.5% | 100.0% | {"ambiguous_many_equal_matches": 7, "polarity_conflict": 1} |
| allergies | 24 | 100.0% | 100.0% | {} |
| physical_examination | 80 | 92.5% | 100.0% | {"polarity_conflict": 3, "ambiguous_many_equal_matches": 3} |
| clinical_uncertainties | 44 | 15.9% | 100.0% | {"no_candidate": 37} |
| clinical_conditions | 39 | 82.1% | 100.0% | {"ambiguous_many_equal_matches": 6, "polarity_conflict": 1} |

## 6. Speaker, negation/polarity and family-history handling (validity checked on gold, prompt_dev)
The rules above were checked against how the gold labels cite evidence (`analysis/p05_rule_validity_probe.json`):
| Category | gold items | cite a question+answer pair | non-question evidence by patient side / clinician | negation cue in cited set | kin term in cited set | lexically reachable |
|---|---|---|---|---|---|---|
| chief_complaint | 50 | 0.0% | 100.0% / 0.0% | 14.0% | 10.0% | 100.0% |
| symptoms | 150 | 64.7% | 89.5% / 9.6% | 31.3% | 6.0% | 100.0% |
| negative_findings | 273 | 100.0% | 94.8% / 5.2% | 100.0% | 2.2% | 100.0% |
| medical_history.surgical_history | 27 | 100.0% | 100.0% / 0.0% | 0.0% | 7.4% | 100.0% |
| medical_history.family_history | 29 | 100.0% | 100.0% / 0.0% | 0.0% | 100.0% | 100.0% |
| medical_history.social_history | 151 | 57.6% | 70.2% / 29.8% | 19.9% | 14.6% | 98.0% |
| medications | 128 | 68.8% | 72.1% / 27.9% | 35.2% | 6.2% | 100.0% |
| vital_signs | 219 | 0.0% | 0.0% / 100.0% | 0.0% | 0.0% | 100.0% |
| review_of_systems | 70 | 100.0% | 100.0% / 0.0% | 82.9% | 0.0% | 20.0% |
| clinical_assessment | 89 | 0.0% | 0.0% / 100.0% | 59.6% | 0.0% | 100.0% |
| procedures_and_investigations | 82 | 1.2% | 1.2% / 98.8% | 48.8% | 0.0% | 100.0% |
| clinical_actions | 266 | 2.3% | 0.0% / 100.0% | 46.6% | 0.0% | 36.8% |
| follow_up | 45 | 0.0% | 0.0% / 100.0% | 24.4% | 0.0% | 100.0% |
| medical_history.past_medical_history | 94 | 86.2% | 71.2% / 28.8% | 19.1% | 5.3% | 100.0% |
| allergies | 24 | 100.0% | 100.0% / 0.0% | 45.8% | 0.0% | 100.0% |
| physical_examination | 80 | 0.0% | 0.0% / 100.0% | 40.0% | 0.0% | 100.0% |
| clinical_uncertainties | 44 | 59.1% | 93.6% / 2.6% | 86.4% | 6.8% | 15.9% |
| clinical_conditions | 39 | 48.7% | 66.1% / 33.9% | 23.1% | 5.1% | 100.0% |
* Gold evidence is almost never question-only; for patient-answered categories (negative findings, surgical and family history, allergies, review of systems) the gold cites a question plus its answer in 100% of items. This is why v4 adds the question to short replies and why a question is never used alone.
* A negation cue is present in 100% of gold negative-finding evidence and a kin term in 100% of gold family-history evidence, so those necessary conditions do not reject valid evidence; the hard speaker rules apply only where gold purity is >= 95%.
* **Known failure of the negation rule:** the cue window cannot see sentence boundaries, so a neighbouring clause ("... slur in my speech. I don't know ...") satisfied it once in the sample of 36.
* **Known failure of the context question:** it is added because it precedes a short reply, not because it concerns the item (00288: the "none" reply answers a question about fever, not allergies).

## 7. Results by clinical group (R_cons v4; B = gold facts as queries, A = P02 facts matching gold)
**B (n = gold facts).**
| Group (n) | R_simple: cited / hit-all | R_main: cited / hit-all | **R_cons v4**: cited / hit when cited / hit-all |
|---|---|---|---|
| positive findings (chief complaint, symptoms, conditions) (n=239) | 100.0% / 54.8% | 86.2% / 76.2% | 87.4% / 96.7% / 84.5% |
| negative findings (n=273) | 100.0% / 85.3% | 90.1% / 89.0% | 98.2% / 100.0% / 98.2% |
| medications (n=128) | 100.0% / 84.4% | 100.0% / 100.0% | 96.1% / 100.0% / 96.1% |
| allergies (n=24) | 100.0% / 91.7% | 95.8% / 95.8% | 100.0% / 100.0% / 100.0% |
| vital signs (n=219) | 100.0% / 68.9% | 75.8% / 65.8% | 95.0% / 100.0% / 95.0% |
| family history (n=29) | 100.0% / 65.5% | 100.0% / 100.0% | 100.0% / 100.0% / 100.0% |
| surgical history (n=27) | 100.0% / 88.9% | 96.3% / 96.3% | 100.0% / 100.0% / 100.0% |
| assessment, procedures and clinical actions (n=437) | 100.0% / 76.4% | 66.6% / 65.0% | 52.6% / 99.1% / 52.2% |
| other (past history, social history, exam, review of systems, follow-up, uncertainties) (n=484) | 100.0% / 42.1% | 67.1% / 63.6% | 74.2% / 99.2% / 73.6% |
| speaker-sensitive facts (categories with a hard speaker-class rule) (n=1254) | 100.0% / 73.2% | 76.2% / 72.2% | 76.6% / 99.5% / 76.2% |

**A (P02 facts that strictly match a gold item; small n).**
| Group (n) | R_simple: cited / hit-all | R_main: cited / hit-all | **R_cons v4**: cited / hit when cited / hit-all |
|---|---|---|---|
| positive findings (chief complaint, symptoms, conditions) (n=19) | 100.0% / 78.9% | 94.7% / 57.9% | 68.4% / 92.3% / 63.2% |
| medications (n=46) | 100.0% / 97.8% | 97.8% / 87.0% | 100.0% / 100.0% / 100.0% |
| allergies (n=9) | 100.0% / 100.0% | 100.0% / 88.9% | 100.0% / 100.0% / 100.0% |
| vital signs (n=41) | 100.0% / 80.5% | 95.1% / 80.5% | 97.6% / 100.0% / 97.6% |
| family history (n=4) | 100.0% / 100.0% | 100.0% / 100.0% | 100.0% / 100.0% / 100.0% |
| surgical history (n=3) | 100.0% / 100.0% | 100.0% / 100.0% | 100.0% / 100.0% / 100.0% |
| assessment, procedures and clinical actions (n=18) | 100.0% / 94.4% | 100.0% / 94.4% | 88.9% / 100.0% / 88.9% |
| other (past history, social history, exam, review of systems, follow-up, uncertainties) (n=13) | 100.0% / 76.9% | 100.0% / 61.5% | 92.3% / 91.7% / 84.6% |
| speaker-sensitive facts (categories with a hard speaker-class rule) (n=91) | 100.0% / 84.6% | 97.8% / 81.3% | 93.4% / 98.8% / 92.3% |

* Negative findings: P02's 51 negative-finding facts never matched gold, so group A has n=0; their evaluation rests on B (gold negative findings: cited 98.2%, 100.0% hit when cited).
* Speaker-sensitive facts (the categories with a hard speaker-class rule) are in the last row: the speaker-class conflict rate among cited facts is 0% by construction; whether the speaker is *right* is limited to the class level (patient side vs clinician), not the individual speaker.
* Assessment, procedures and clinical actions are the weakest in coverage (about half of gold facts cited) because gold actions are free text ("lexically reachable" 37% for actions).

## 8. Integration with the existing builder and final-schema mapping
`retrieve()` -> segment indices -> `source_segments` ids -> `build_evidence()` (unchanged) -> final JSON. Mapping to the frozen schema is exactly the one in `reports/07_P04_architecture_and_design_v2.md` section 6: `evidence_ids` per item (EV_001... in segment order), one `clinical_evidence` record per distinct cited segment (exact transcript text, speaker id, lower-case role, floor-second MM:SS times, `supports` paths), items without a citation keep `evidence_ids: []`. Integration run on copies of the 50 P02 outputs (`p05_diagnostics/final_predictions_v4/`): 679 facts, 493 cited, 186 abstained, 463 evidence records (9.26 per encounter; mean number of ids per cited fact is higher than 1 because of context questions), 0 invalid ids, 0 evidence-field schema violations, extraction unchanged, speaker attribution unchanged (42.1%), builder integrity true for 50/50. Evaluator lexical grounding strict/lenient/partial/unsupported of 675: [426, 23, 44, 182] (unsupported = uncited). **This lexical figure is circular** (retrieval optimises word overlap) and must not be read as correctness.
Other schema problems (assessment/follow-up as objects, missing confidence fields) are not touched: the architecture changes evidence only.

## 9. Evaluation plan against P02 and Arm R (proposal; thresholds are provisional development gates)
* **Stage-1 reference.** P02 on the same 50 prompt_dev records; extraction must be identical by construction (assert 153/522/1707 and `verify_only_evidence_changed` = true for every record). Any difference is a bug.
* **Evidence reference.** P02's own evidence (1 template record, 0% timestamp match), Arm R (R_main/R_simple) and the P04 smoke outputs where comparable.
* **Metrics, reported separately.** (i) coverage: cited / total facts, per category group; (ii) correctness when cited against gold-cited segments on matched facts (hit, set precision/recall) with the denominator and matched-item coverage always shown; (iii) behaviour counters among cited facts (question-only, greeting-like, SEG0001, polarity, kinship, speaker class): the first, SEG0001, kinship and speaker-class counters must be 0 by construction, the greeting-like and polarity counters are reported with each flagged case read; (iv) abstention reasons; (v) human audit of 30 cited facts (stratified by group, reviewer named by you) with the verdicts supported / partly / not supported, plus 15 abstained facts to check that abstention was justified; (vi) structural checks (valid ids, record/speaker/time correctness, supports consistency, builder integrity); (vii) lexical grounding (reported with the circularity warning); (viii) evidence records per encounter (reported only).
* **Provisional gates (development stage):** hit when cited >= 95% on matched P02 facts; hit with abstentions as misses >= Arm R's R_simple (88.9%); question-only, SEG0001, kinship and speaker-class counters 0 and the greeting-like and polarity counters <= 2% with every flagged case read; extraction identical; evidence-field violations 0; human audit >= 85% of cited facts supported with 0 greeting/question-only citations; coverage reported with a floor of 60% of P02 facts (below that the method is too conservative to be useful). Results on prompt_dev cannot count as evidence of generalisation because the rules were tuned there.
* **Independent test:** after you approve a freeze of `p05_retrieval.py` and its parameters, run once on the preserved 50-record validation subset (stage 1 would need P02 outputs for those ids, i.e. GPU inference on validation, which needs your separate approval and the guard from section 1). The 400 locked-test records stay untouched.

## 10. Zero-inference diagnostic plan - what was run and what is pending
Run (artifacts in `p05_diagnostics/`, `analysis/`, `arm_R/`): D1 gold rule-validity probe; D2 retrieval ladder on gold facts; D3 ladder on P02 matched facts; D4 abstention and conflict rates on all P02 facts; D5 builder integration on copies of P02 outputs v1-v4 with the existing evaluator; D6 qualitative read of 36 selections plus the 12 cited-but-not-gold cases; D7 parameter sensitivity; D8 locked-test guard test.
Pending (need your approval): human audit; rule freeze; validation run (needs GPU for stage 1); a decision on better lexical reach for review of systems, clinical actions and uncertainties (see limitations).

## 11. Leakage and locked-test safeguards
* The retrieval and the builder open no labels and no test files (static code; the audit script and the guard test measure it). Labels are used only in analysis scripts that read prompt_dev gold after outputs exist.
* **Label-informed development choices (disclosed):** the speaker-class map (from the gold probe), the decision to keep a question with a short reply (gold cites question+answer pairs), the need for kin and negation cues (gold necessary conditions), the item-aware polarity and local-cue revisions (from reading prompt_dev results). No label text is embedded in code; lexicons are generic English (negation words, kin terms, small-talk words, vital-sign abbreviations). These choices are not independent of prompt_dev.
* Only prompt_dev ids (asserted) are used; validation and locked-test ids are never read by the diagnostics (assertions in the scripts). Future inference runs must install `dev_guard.install(ids)` and assert `locked_test_accesses(spy.opened) == []`.
* The frozen dataset, schema, evaluator and P00-P04 artifacts are unmodified.

## 12. Expected limitations and failure cases
1. **Extraction errors get evidence.** A wrong extracted item with a matching word receives a plausible citation (a surgery "heart disease" cited to a line about an irregular heartbeat; a symptom filed as a negative finding). Evidence presence must never be reported as item correctness.
2. **Lexical collisions.** The follow-up "in three days" was cited to a line saying the paracetamol is for three days; "Pelvic heaviness" to a line about a urine test.
3. **Repeated mentions.** The same fact appears in several lines; retrieval may cite the doctor's later summary where the gold cites the history-taking exchange (most of the 12 cited-but-not-gold cases are legitimate alternative mentions, so gold agreement understates quality there and cannot be taken as a precise measure).
4. **Terminology.** Standardised terms that were not spoken fail unless the plain wording is spoken; synonyms (viral vs bacterial throat infection) can attach the wrong statement.
5. **Unreachable categories.** Review of systems, clinical uncertainties and many clinical actions have no word overlap with the evidence the gold cites (reach 20%, 16%, 37%): they will mostly be uncited. A semantic matcher (a small embedding or cross-encoder model) would be needed; it is not part of this proposal.
6. **Scope of negation and kinship** is a window heuristic, not a parser; context questions are not checked for relevance.
7. **Single segment bias:** the retriever cites the best segment (plus tied repeats and context questions); gold items cite on average 1.78 segments, so segment recall is limited (set recall 60.0% on gold facts).
8. **Not independent:** rules were calibrated and revised on the same 50 records; the numbers will fall on new data.
9. **No evidence for facts in P02's object-typed sections** (assessment/follow-up emitted as objects in 20 of 50 records) because those items are skipped by the structure-based walk.

## 13. Decisions I need
* **F1** Approve P05 as the next direction (P02 extraction + R_cons evidence) and its evaluation plan/gates (section 9), or change them.
* **F2** Decide whether to accept the lexical unreachability of review of systems, clinical actions and uncertainties (abstain) or to explore a semantic matcher later.
* **F3** Name a reviewer for the human audit (30 cited + 15 abstained facts), or tell me to skip it.
* **F4** Decide if/when to freeze the retrieval rules and authorise the validation run (stage-1 GPU inference on the validation subset, using the new guard), after the human audit.
