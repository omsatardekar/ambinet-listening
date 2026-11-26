# S1 prompt design (frozen before inference; hashes in `manifests/S1_FREEZE_MANIFEST.json`)

## What changed relative to P02
| Aspect | P02 (frozen, cf50ce8e...) | S1 |
|---|---|---|
| Output sections | 20 top-level keys, 17 entity sections, items of 5-17 fields | 20 top-level keys (17 lists, chief complaint, allergy status, id), items of 2-6 fields |
| Evidence | `evidence_ids` on every item plus a `clinical_evidence` list with segment text and MM:SS times | none |
| Quality / confidence | `quality_checks` object, null `confidence` on every item | none |
| Normalization | plain and `normalized_*` fields, "replace everyday wording by the medical term" | one name per fact in the speaker's own words, short, lower case |
| Output boilerplate | explicit null/[] fields for every unused attribute | only the fields that carry a fact |
| Allergy handling | an allergies list, "no allergies" belonging in negative findings | an explicit `allergy_status` (reported / none_stated / unknown / not_asked) plus a list of real allergies |
| Negative findings | "no fever" style names allowed | name of the absent thing without "no"/"not" |
| Medications | status currently_used / discontinued / planned | status current / stopped / new, one item per medicine, explicit rule never to copy a dose or route between medicines |
| Prompt length (instructions + template, before the transcript) | 1,184 words / 9,688 bytes | 729 words / 5,053 bytes |
Unchanged: the transcript renderer (segment id, speaker, role, times, text), the model, the OpenVINO FP16 GPU runtime, greedy decoding, thinking off, `max_new_tokens` 6144, the evaluator.

## Coverage of the 22 required information categories
Chief complaint, symptoms (with duration and present/resolved), positive findings (symptoms) and negative findings, medical history, current conditions confirmed by the doctor, surgical history, family history, social history, current / historical (stopped) / newly prescribed medicines (status), allergies with an explicit status, vital signs, physical examination, review of systems, clinical assessment (provisional / differential), investigations (type and status), procedures, clinical actions, follow-up. Not requested of the model: evidence, citation, timestamps, retrieval, quality or confidence judgements, extra normalization, clinical uncertainties (P02 left that section empty in 50 of 50 records, so nothing is lost relative to P02).

## Rules written into the prompt (task Part 4)
Medicines one per item and never merged; a mentioned medicine is not assumed current; allergy states kept apart and a medicine is not an allergy; a doctor's question is not a fact; positive and negative kept apart with negation scope and a symptom not in both lists; speaker role copied from the line, and who reads out a vital sign is the speaker (no inference about who measured it); no dates or appointment times unless said, follow-up "when" is the spoken words; no invention, empty lists are correct; possibilities stay provisional/differential.

## Design choices that deserve scrutiny
- The prompt does not contain example facts (to avoid the copying seen in P02 where schema words such as "absent" and "provisional" became entries); empty template strings are still shown, so placeholder copying remains possible and is measured.
- `vital_signs.name` and `social_history.category` are closed lists taken from the frozen schema's own terminology (vital names are standard clinical names). This narrows free text and may favour matching; it is not normalization of synonyms.
- Removing normalization may cost strict matches, because the evaluator keys on the normalized name when it is present in the gold labels and on the plain name otherwise. This is part of what is being tested.
- The S1 `current_conditions` list exists only so the canonical `clinical_conditions` category can be compared with P02; it makes the task slightly larger than the minimum.

## Adapter (`s1/s1_adapter.py`, 25 unit tests)
Field renames, schema constants and definitional mappings listed in `MAPPING_NOTES`; no invention, no evidence ids, no deduplication, no correction; unmappable structures are skipped and counted as adapter failures. Both raw and adapted outputs are kept.
