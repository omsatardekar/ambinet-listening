# EXP_004 pre-experiment analysis: EXP_003 error patterns and the development/validation split

Source: the finished EXP_003 100-record development run (94 valid predictions), re-scored with the **unmodified** evaluator functions.
Script: `analysis/error_analysis_exp003.py`; full numbers and examples: `analysis/error_analysis_exp003.json`. No inference was run.

## 1. What the 276 "transcript-supported false positives" really are
Of 284 strict false positives, 276 contain words found in the transcript (so they are not hallucinations) and 85 of the 284 have a *similar but unmatched* gold entity in the same
encounter. The strict matcher compares the normalised primary key (`normalized_name`, `normalized_value`, ...) exactly, so the dominant pattern is a **terminology / granularity mismatch**:
* Patient wording copied instead of a standard clinical term in the normalised field: `gallbladder removal` vs gold `cholecystectomy`; `diabetes` vs `type 2 diabetes mellitus`; `thick yellow discharge from the nose` vs `purulent nasal discharge`; `underactive thyroid` vs `hypothyroidism`; `heart attack` vs `myocardial infarction`.
* Generic names where the gold uses a specific one: vital signs `temperature` / `pulse` / `saturation` vs `body temperature` / `heart rate` / `oxygen saturation`; allergy `antibiotic` vs `antibiotic unspecified`.
* Wrong content in a field: `chief_complaint` is wrong in 90 of 94 outputs (whole phrases, sometimes another speaker's sentence, a vital-signs sentence, or the single word "severe"); `negative_findings` contain `no fever` while the matching gold item is a different finding; the placeholder string `none` is emitted as an allergy/social entity.
* Transcription noise copied verbatim (`amiodipine`, `glycomet`), two medications merged in one entity.
Implication: a prompt can plausibly help by asking for standard clinical terminology in the `normalized_*` fields. It cannot help where the gold uses a label convention the transcript does not state.

## 2. Under-extraction is the main limiter (recall 2.7%)
The model writes about 4 entities per encounter (382 over 94 outputs) where the gold has about 36 (3,621 over 100 encounters). Predicted vs gold entities (94 valid encounters): negative_findings 9 vs 512; clinical_actions 2 vs 461; vital_signs 22 vs 416; social_history 2 vs 278; clinical_assessment 0 vs 160; follow_up 0 vs 72; review_of_systems 1 vs 131; procedures 2 vs 149; physical_examination 15 vs 134; symptoms 115 vs 284; medications 60 vs 230.
Sections are empty in most encounters (e.g. negative_findings empty in 88/94, clinical_actions 92/94, vital_signs 86/94). In most missed gold items the gold wording is present in the transcript (FN with the key lexically in the transcript: vital signs 343/407, medications 153/184, clinical actions 294/461, negatives 428/512), so the information is available but not extracted.

## 3. Schema failures (0 of 94 valid outputs compliant; 429 missing, 219 enum, 150 wrong-type, 10 unexpected)
* `clinical_assessment` is emitted as a single JSON **object** in 94/94 outputs (schema: array); `physical_examination` object 25/94; `follow_up` object 13/94. The object usually holds a copied transcript sentence (not a real assessment).
* Every item should carry `confidence: null`; it is missing very often (medications 58 encounters, symptoms 32, allergies 23, vitals 22, ...).
* `encounter_metadata.primary_speakers` missing in 54; `clinical_evidence[].supports` missing in 50.
* Role enums: the transcript prints roles in capitals, and the model copies `DOCTOR`/`PATIENT` (39 times) or speaker ids such as `person_2` (18) or an empty string (21) instead of the lower-case roles; symptom `certainty` is null in 25; `symptoms.status`, `category` and `medications.route` values are outside the enum (35, 19, 22).

## 4. Evidence grounding (88.5% of predicted entities unsupported)
* Only **one** `clinical_evidence` record is produced per encounter (94 records for 94 encounters; the template's `EV_001` is copied). 242 of 382 entities have no `evidence_ids`; 9 point to ids that do not exist; 87 point to a record that is not a real transcript segment.
* Of those 94 records, 34 are a real segment with the correct speaker; in 45 the text is a real utterance but the `speaker_id` is wrong; in 15 the text is not a transcript segment.
* The extracted text frequently does not match the evidence it cites, because evidence is not part of the model's working process.

## 5. Speaker attribution and negation
* Speaker attribution is correct for 51% of matched entities (patient 39/76, doctor 7/9; nurse/family 0/4) and depends on a role field that is often capitalised or a speaker id.
* Negation: 0 of 543 gold negative findings reproduced; 1 polarity flip.

## 6. Reliability and prompt properties
* 6 of 100 outputs are malformed JSON (a missing comma delimiter); none was truncated; all stop normally.
* The prompt is 7,032 characters (about 3,770 input tokens per call with the transcript); the output template lists every section with empty placeholders, and the model tends to imitate the template's single example item.

## Caveat on independence
This analysis used all 94 valid development predictions, including those that fall in the validation half. Only aggregate patterns and generic terms were used, but the validation half is therefore **not a pristine hold-out**. The only untouched hold-out is the locked 400-record test, which stays unused. From now on, error inspection should use `prompt_dev` encounters only.

## Development / validation split (`experiments/split_v1.json`, `experiments/make_split.py`)
* Source: the 100 EXP_003 development ids (split seed 20260301). The 400 locked-test ids are not read.
* Method: strata = specialty x complexity from the frozen manifest; ids shuffled within each stratum with seed 20260401 and dealt alternately with a global toggle. Result is exactly **50 prompt_dev / 50 validation**, disjoint, reproducible by rerunning the script.
* Balance: complexity prompt_dev simple 9 / moderate 18 / complex 17 / challenging 6 vs validation 10 / 17 / 15 / 8; every one of the 12 specialties appears in both halves and the counts never differ by more than one encounter (e.g. Cardiology 6/5, General Medicine 8/7, Neurology 5/6); mean transcript length 511 vs 503 words; speaker counts similar.
* The 5 smoke encounters are split 2 / 3 (prompt_dev 00035, 00037; validation 00021, 00032, 00034).
* P00 reference on the same subsets (from EXP_003 outputs, no new inference): prompt_dev valid JSON 48/50, micro F1 0.047 (P 0.237, R 0.026), macro F1 0.048; validation valid JSON 46/50, micro F1 0.051 (P 0.280, R 0.028), macro F1 0.061 (`evaluation/P00_baseline_subset_metrics.json`).
* Rules: prompts are designed using `prompt_dev` only; `validation` is run once per finished candidate and used only to choose between candidates; no label-derived text (gold terms or entity names from labels) may be copied into a prompt.
