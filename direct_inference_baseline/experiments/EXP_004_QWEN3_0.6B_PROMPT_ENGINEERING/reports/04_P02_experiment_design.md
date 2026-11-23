# P02 design - comprehensive clinical extraction (FOR APPROVAL; nothing has been run)

Prompt file: `prompts/P02_comprehensive_extraction.txt`  sha256 `cf50ce8efe850cda76fe6eadebf45391fa0461a657e52de5783edb31ccdde5d1`
Diff against P00: `prompts/P02_comprehensive_extraction.diff` (one inserted block of 12 bullet lines, about 2.7k characters, about 600 tokens; nothing else changed). The file is NOT frozen: any edit before approval changes the hash, which I will re-report.
P02 is built from P00 alone. It contains none of P01's structure rules, and no evidence, speaker or negation/temporality strategy.

## 1. Inputs reviewed (prompt_dev, 50 ids only; validation and test ids not read)
Aggregate-only analysis: `analysis/underextraction_dev50.py/.json`, `analysis/key_vocab_concentration.py/.json`. Gold items in the 50 records vs items extracted and strict TPs:

| Category | Gold | P00 pred / TP | P01 pred / TP | Gold items in record that P01 missed and that are lexically in the transcript |
|---|---|---|---|---|
| negative_findings | 273 | 6 / 0 | 15 / 0 | 230 of 273 |
| clinical_actions | 266 | 2 / 0 | 22 / 1 | 169 of 265 |
| vital_signs | 219 | 11 / 6 | 62 / 37 | 150 of 182 |
| social_history | 151 | 2 / 1 | 2 / 0 | 42 of 151 |
| symptoms | 150 | 59 / 9 | 82 / 11 | 109 of 139 |
| medications | 128 | 31 / 24 | 47 / 36 | 74 of 92 |
| past_medical_history | 94 | 7 / 1 | 7 / 1 | 37 of 93 |
| clinical_assessment | 89 | 0 / 0 | 7 / 6 | 83 of 83 |
| procedures | 82 | 2 / 0 | 19 / 6 | 55 of 76 |
| physical_examination | 80 | 10 / 0 | 27 / 0 | 61 of 80 |
| review_of_systems | 70 | 1 / 0 | 20 / 0 | 20 of 70 |
| follow_up | 45 | 0 / 0 | 16 / 1 | 44 of 44 |
| clinical_uncertainties | 44 | 1 / 1 | 8 / 0 | 21 of 44 |

("Lexically in the transcript" uses the evaluator's lenient support test, so it is an upper-bound indication that the content was stated, not proof the item should match strictly.)

Main under-extraction patterns:
1. **Whole sections left empty.** P00 returns about 4 items per record against about 36 in the gold. Negative findings are empty in 38 of 50 P01 records, social history in 48, past history in 47.
2. **Volume matters.** P01 doubled the items per record (4.4 to 9.1) and F1 doubled; vital signs went from 11 to 62 items with 37 correct. Where the model writes more, it scores more.
3. **Count-heavy categories** (negatives 5.5/record, actions 5.3, vitals 4.4, social history 3.0) are where coverage can add the most.
4. **Chief complaint** is a single item per record that is rarely correct (1/50 strict in both versions); wording is free text.
5. **Terminology.** Earlier EXP_003 analysis: 276 of 284 false positives were transcript-supported, mostly wording and granularity mismatches.
6. **Closed vocabularies.** In the 50 development labels, social_history has 6 distinct match keys, vital_signs 8, review_of_systems 7, clinical_uncertainties 10 (schema enum), and past/surgical/family history and allergies 10-16 each. The strict evaluator compares these keys exactly. A prompt that does not state the vocabulary will rarely hit them even when it finds the right content. Free-text categories (clinical_actions: 151 distinct keys of 266 items; assessment 75 of 89; physical_examination 68 of 80) cannot be matched exactly by any prompt, so their strict F1 will stay low regardless.

Documented finding, not an explanation: P01, a schema-only prompt, nearly doubled recall (0.026 to 0.059) while precision stayed flat. I do not know why (longer prompt, explicit empty-list and array wording, or other); it has not been tested. P02 is compared against P00, and P01 is shown only as an informational second reference.

## 2. Strategy (comprehensive extraction only)
Prompt block `Coverage rules` (exact text is in the prompt file): (a) read in order and extract every stated item, one per finding, do not leave supported sections empty; (b) a coverage instruction for each of the 17 sections; (c) terminology: standard lower-case singular clinical term in `normalized_*` fields, original wording kept in the plain field, nothing added; (d) no duplicates, no unsupported items. The output template, allowed values, schema and evaluator are unchanged.

## 3. Leakage control and one decision for you
Standing rule: no label-derived text in prompts. Scripted check (`experiments/leak_check_P02.py` -> `evaluation/P02_leakage_check.json`): 732 distinct gold match keys of the 100 development labels vs the added text: **0 hits**.
My first draft did hit: I had listed common social-history topics and vital-sign names from general medical knowledge, and they coincide with the label vocabularies (alcohol, smoking, occupation, diet, exercise, living, blood pressure, respiratory rate, oxygen saturation). I removed them and wrote the lines generically. The cost is real: given point 6, the strict score on social history, vital signs and review of systems depends on the model choosing exactly the label vocabulary, which this prompt does not tell it.
**Decision 1:** keep the strict no-vocabulary rule (recommended; P02 as shown), or allow a standard-clinical-vocabulary list (standard vital-sign names, common social-history topics, body systems) in a separate, clearly labelled version? The second is generic medical knowledge but would overlap the label keys, so I would report its scores as "vocabulary-informed" and not mix them with P02.

## 4. Controlled conditions (identical to P00/P01)
Qwen3-0.6B rev c1899de2..., OpenVINO FP16 (EXP_002), Intel UHD 620 GPU, fresh pipeline per encounter, greedy, thinking off, max_new_tokens 6144, existing parser, schema validator and evaluator, frozen schema. Encounters: the same 50 `prompt_dev` ids. P00 reference: EXP_003 outputs on those ids (reproducibility 3/3 byte-identical). Run id `P02_comprehensive_extraction_dev50`; outputs in `outputs/P02_comprehensive_extraction_dev50/`, evaluation in `evaluation/P02_comprehensive_extraction_dev50/`; a label file-access audit as before. No prompt edits during the run. Single run, no iteration on prompt_dev before your review.

## 5. Pre-registered keep/reject criteria (fixed before inference; reference = P00 on the same 50 ids)
KEEP only if ALL hold:
1. Micro recall >= 0.050 (P00 0.026; about double).
2. Micro F1 improves by >= +0.030 over P00 (P00 0.047) and the paired bootstrap 95% interval for the difference has a lower bound above 0.
3. Micro precision >= 0.187 (not more than 0.05 below P00's 0.237).
4. Valid JSON >= 46/50 (P00 48, tolerance 2) and no output with finish_reason other than `stop` (truncation) in more than 2 records.
5. No category with P00 F1 above 0.1 loses more than 0.05 F1 (medications, allergies, surgical_history in the 50 ids).
6. Breadth: at least 3 of the 9 low-recall categories (negative_findings, social_history, review_of_systems, physical_examination, clinical_conditions, clinical_assessment, procedures_and_investigations, clinical_actions, follow_up) gain >= +0.03 recall.
7. Unsupported claims <= 15% of predicted items (P01: 8.8%) and duplicate items <= 5% of predicted items (P00 0.0%, P01 0.2%).
8. Mean output tokens <= 3,000 and no output hitting the 6,144 limit (guard against runaway lists).
Reported but not gating: schema violations (total, missing_field, wrong_type, invalid_enum, per item), fully compliant records, per-category P/R/F1, empty-section counts, speaker attribution, evidence grounding, latency, comparison with P01. Schema structure is untouched by P02 and is expected to resemble P00 (the assessment-as-object problem remains); more output also raises missing-field totals, so I will report violations per item as well.
REJECT if any criterion fails. A "keep with changes" version would be a new P02b on prompt_dev and only with your approval. Validation records are run only for a finalist.

## 6. Risks I can see in advance
* Longer prompt (+about 600 tokens) and longer outputs; a 0.6B model may produce repetition, malformed JSON or invented items when told to extract "every" item. Criteria 4, 7 and 8 are the guards.
* Exact-key scoring means large recall gains are unlikely on free-text categories even if extraction improves; gains will concentrate in negatives, vitals, history and medications.
* Cost: output could grow from 863 (P00) to about 2,000-2,500 tokens, at 5.6 tokens/s about 5-7 hours for 50 encounters (P01 took 2.9 h at 1,195 tokens). Resumable; logs per encounter.

## 7. Decisions I need
1. Vocabulary rule (section 3): keep P02 as shown (recommended) or add the separate vocabulary-informed version later.
2. Approve the exact prompt text and hash, the settings and the criteria in section 5 (or tell me what to change; changes give a new hash).
3. Approve the 5-7 h GPU run on the 50 prompt_dev ids.
