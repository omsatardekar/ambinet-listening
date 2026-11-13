# P05 human-audit sampling plan (45 facts; a feasibility check, not a validation study)

## 1. Purpose and limits
To check, on a small sample, whether the transcript supports the extracted facts, whether the retrieved segments are relevant, speakers/polarity/family attribution are right, and whether abstentions were justified. 45 facts are **not** statistically representative; results are reported with that caveat and with the reviewer's qualifications. **The retrieval rules are not tuned on the audit after the validation run.**

## 2. Reviewer
Prefer a clinician or qualified clinical-documentation reviewer who took no part in designing R_cons v4 or the prompts. If none is available, record the reviewer's qualifications in `reviewer_form.md` and report the audit as a **limited independent review (or a non-independent / non-clinical review, as applicable), not clinical validation**. One reviewer; no adjudication; no inter-rater statistic (stated as a limitation).

## 3. Sample (drawn automatically, no labels, fixed seed)
* Pool: the facts of the 50 validation records (stage-1 P02 facts with the system's decision). Draw after the validation run only, by `audit_sampler.py validation ...` with seed **20261113**; the seed and the pool are saved in `audit_key.json`.
* 30 cited facts stratified by clinical group: positive findings 4; negative findings 4; medications 3; allergies 2; vital signs 3; family history 3; surgical history 2; assessment/procedures/clinical actions 5; other (past history, social history, examination, review of systems, follow-up, uncertainties) 4. Shortfalls are filled deterministically from the remaining cited facts.
* 15 abstained facts stratified by reason: no_candidate 4; speaker_class_mismatch 3; polarity_conflict 3; ambiguous_many_equal_matches 3; other reasons 2.
* Selection never uses gold labels or correctness, so it cannot favour easy facts.

## 4. Two-phase procedure (blinding)
* **Phase 1 - BLIND** (`phase1_blinded_packet.md`, `phase1_responses_template.csv`): the 45 facts in random order plus the full transcripts of their encounters; no citation, no abstention status. The reviewer records: is the fact supported (yes/partly/no/cannot tell), the segment(s) they consider the best evidence, speaker correct, polarity/negation correct, attribution correct (patient's own vs family member).
* **Phase 2 - UNBLINDED** (`phase2_unblinded_packet.md`, `phase2_responses_template.csv`), completed only after phase 1: for cited facts - is the selected segment relevant, does it support the fact, speaker, polarity, is a needed question included or an unnecessary one added, family attribution; for abstained facts - was usable evidence actually available (compared with the reviewer's own phase-1 segments).
* Format tested on a pilot drawn from prompt_dev (no reviewer; `integration_checks/audit_pilot_prompt_dev/`); the blinded packet was checked to contain no system output.

## 5. Scoring (`audit_score.py`, run on the returned CSVs; no tuning)
Reported separately: cited facts judged supported (yes; yes or partly), relevant, speaker/polarity/context/family attribution correct, reviewer's best segments overlapping the system's, fraction of cited facts whose underlying fact the transcript supports; abstained facts: abstention justified, usable evidence found in phase 1. Concern flag if fewer than 75% of audited cited facts are judged supported (no automatic rejection).

## 6. Independence statement to include in the report
Who reviewed, qualification, relationship to the design, blinding actually achieved, and the explicit statements 'limited feasibility review' and 'not clinical validation'.
