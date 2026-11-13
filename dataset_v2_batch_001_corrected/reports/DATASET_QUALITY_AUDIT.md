# Batch 001 corrected: quality audit and corrections

Scope: 500 synthetic encounters, 500 Module-2 transcripts, 500 ground-truth labels. The original `dataset_v2_batch_001/` is untouched
(checksums verified with `python dataset_v2_batch_001/scripts/lock_dataset.py --verify`).
Everything below is **automated** measurement. **No clinician has reviewed any record.**

## How the correction was done (read this first)

The original transcripts could not be patched line by line: the audit problems (filler as a duration mechanism, one shared phrase
inventory, 83 reused profiles, schema/semantic defects) sit inside the generator, and a transcript and its label must change together.
So the generator was revised and **every record was regenerated under its original ID**, with transcript, label and blueprint produced
from the same revised blueprint. Consequences, stated plainly:

* Preserved for all 500: encounter ID, specialty, complexity tier, file layout, schemas, evidence/reference conventions.
* Preserved for 413 of 500: the underlying clinical profile (87 encounters were moved to one of 25 added profiles in the same specialty).
* **Not preserved:** the individual clinical facts of the original encounters (durations, medicines, histories, wording). They were
  re-sampled. If you require the original facts kept verbatim, this is a deviation you must decide on; the originals remain in
  `dataset_v2_batch_001/`.

## Findings and corrections

| # | Audit item | Before | After | How verified |
|---|---|---|---|---|
| 1 | `category` misused for attribution ("reported") | 92 symptoms; 145 symptoms outside a controlled vocabulary (also `gynaecological`, `nephrological`, `general`) | 0; every category is in a 13-term vocabulary (constitutional, neurological, cardiovascular, respiratory, gastrointestinal, musculoskeletal, dermatological, endocrine, genitourinary, ENT, ophthalmological, psychiatric, other). Disputed symptoms keep `certainty: "disputed"` and `reported_by: caregiver/family_member`, with a real category | validator `category_vocab`, `category_mismatch`; negative controls |
| 2 | Unapproved `confirmed_by` in `clinical_conditions` | 361 fields | 0; removed from generator, validator key sets, docs | `label_schema` key-set check; negative control |
| 3 | Fixed artificial confidence values | 17,977 non-null `confidence`/`role_confidence` fields | all `null` (fields kept for schema compatibility) | `confidence_not_null`; negative controls |
| 4 | Allergy / negative-finding representation | every encounter asked about allergies; only "none" vs "reported" | six distinguishable cases (counts below) | `allergy_consistency` rules |
| 5 | Template filler and repeated stock phrases | filler = 18.8% of segments and 19.6% of recording time, present in 486/500 encounters | 0.2% / 0.16%, 31/500 (the remaining hits are optional small talk and the doctor's recap) | `reports/metrics_*.json` |
| 6 | Profile reuse | 83 profiles, up to 8 encounters each (mean 6.0) | 108 profiles, max 6 (mean 4.6) | `duplicate_report.json` |
| 7 | Transcript realism | uniformly clean | 235 encounters carry restrained imperfections (case/punctuation loss, repeated words, spoken contractions); clinical terms, drug names, numbers are masked and never altered | `add_noise` design; evidence alignment still 100% |
| 8 | Generic actions | follow-up and "seek urgent care" in all 500; 7.3 actions per encounter | follow-up in 384, safety-net in 218; 14 encounters have no new action; 4.8 actions per encounter; counselling is `recommended`, not `planned`; considered-but-not-ordered tests are `conditional` | `clinical_consistency_report.json` |

Allergy cases in the corrected data (encounters): explicit "no known allergies" 218; allergies never discussed (nothing extracted, no invented
negative) 64; reported with reaction 95 (some with the reaction explicitly stated as not remembered); uncertain (drug unknown) 73;
historical 26; disputed between patient and caregiver 24 (both reports kept, `allergy_disputed` uncertainty, contradiction recorded).

## Repeated-phrase and filler statistics (same script on both datasets)

| Metric | Original | Corrected |
|---|---|---|
| Filler segments (original filler inventory) | 5,625 (18.75%) | 50 (0.22%) |
| Filler seconds | 40,300 s (19.6%) | 339 s (0.16%) |
| Encounters containing any filler phrase | 486 | 31 |
| Segments whose exact text occurs in >=5% of encounters | 37.5% | 26.6% |
| Distinct such texts | 234 | 170 |
| Acknowledgement-only segments (okay/alright/sure…) | 4.9% | 2.3% |
| Distinct opening lines / max share | 152 / 3.0% | 171 / 2.6% |
| Distinct closing lines / max share | 83 / 13.0% | 107 / 7.8% |
| Max pairwise 5-gram Jaccard | 0.086 | 0.092 |

Honest reading: the filler is gone and acknowledgement/closing repetition dropped markedly, but about a quarter of segments are still
stock history questions and short answers ("Any previous surgeries?", "No, nothing there."). That is reduced, not eliminated.

## Duration without filler

Removing filler shortened the encounters. Length now comes from clinical content (extra extractable social-history items such as
occupation, exercise, diet, living situation; more denied findings and system reviews; vitals and examination in most encounters) and from
slower speaking rates. In addition, encounters contain silent documentation/examination pauses (mean 39 s per encounter, about 10% of
recording time; no words are added). Duration 300.2-535.1 s (mean 382 s = 6.4 min, down from 6.9 min); segments 32-72 (mean 47.6, down
from 60). 8 encounters are outside 35-70 segments. Encounters that could not reach 5 minutes were regenerated, not stretched.

## Validation results (automated)

* 500/500 pass; 0 failures. 95 generation attempts failed validation during generation and were regenerated (`validation/quality_log.txt`).
* Evidence: 24,795 of 24,795 extracted values are found in their cited evidence text; every evidence record matches a transcript segment
  (speaker, role, text, timestamps).
* Duplicates: 0 exact, 0 near-duplicate pairs, 0 repeated clinical identities.
* 22 negative controls (validation/negative_controls.json) are all rejected, including: negated finding extracted as present, invented dose,
  invented allergy reaction, caregiver statement attributed to the patient, historical symptom labelled current, planned investigation
  labelled completed, unsupported diagnosis, unresolved dose disagreement converted to a dose, invalid evidence reference, wrong category,
  arbitrary confidence, `confirmed_by`, negative allergy finding for an allergy never discussed.

## Automated checks vs. manual review vs. unverified assumptions

* **Automated:** schema, vocabulary, null confidence, ids/timestamps/speakers, evidence alignment, lexical grounding of every value,
  negation/temporality/allergy/dose/investigation-status rules, duplicates, realism statistics.
* **Manual clinical review:** none performed. `reports/human_review_required.csv` is an automated triage (333 records; 239 high
  priority because they contain uncertainty, disagreement or unnamed medicines) - it is not a review result, and the remaining records are
  not "clean", they are simply unreviewed too.
* **Unverified assumptions:** clinical plausibility of all authored content (symptom/profile pairings, doses, plans, vital ranges),
  the wording of counselling summaries (description vs. spoken advice is not lexically checked), and whether the dialogue resembles real
  clinic speech.
