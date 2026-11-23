# P03 design - evidence-grounded prompt (FOR APPROVAL; nothing has been run)

Prompt file: `prompts/P03_evidence_grounded.txt`  sha256 `4f7ee6f763aa886ec8090f7bb680f40eaa2f7f89e37175dfd6b8ce29daad5c9f`
Diff against P00: `prompts/P03_evidence_grounded.diff` (one inserted block of 9 lines, about 2.5k characters, about 600 tokens, placed in the same position as the P02 block; nothing else changed). Not frozen until you approve; any edit changes the hash.
P03 is built from P00 only: no P01 structure rules, no P02 coverage rules.

## 0. Status decision recorded
P02 is **KEEP at the development stage only** (50 prompt_dev records, 8/8 criteria). Its validation run is **postponed by user decision (2026-11-12)**. P02 is NOT validated and NOT final; no document may describe it as such. (Recorded in the decisions log, changelog, comparison table and manifest.)

## 1. Why evidence, and what the P00 outputs actually do (prompt_dev 50 ids, existing outputs, no new inference)
Script `experiments/evidence_diagnostics.py` (unmodified evaluator for the grounding/speaker/unsupported numbers; supplementary checks defined in the script; no labels used for the supplementary checks). The evaluator-based numbers for P01 and P02 reproduce the figures already reported (4/416 and 0/669 unsupported), which validates the script.

| P00 on the 50 ids | |
|---|---|
| Entities evaluated | 207 |
| Grounding (evaluator): strict / lenient / partial / unsupported | 3 / 2 / 15 / **187 (90.3%)** |
| Entities with any evidence_ids | 33.5% |
| evidence_ids that resolve to an existing record | 91.4% |
| **Evidence records per encounter** | **1.0 in every encounter** (template example copied once) |
| Evidence text found in the transcript | 81.3% (60.4% equal to a whole segment) |
| Evidence speaker_id correct for its text | **33.3%** |
| Evidence timestamps matching the segment (+-1 s) | **0%** |
| Evidence `supports` non-empty | **0%** |
| Speaker attribution (evaluator) | 46.3% (41 evaluated) |
| Unsupported claims (evaluator) | 1.9% of predictions |
| Extraction micro P / R / F1 | 0.237 / 0.026 / 0.047 |

Reading: the model fills a single evidence record and points many items at it. This is a structural habit (one record, empty `supports`, placeholder timestamps), and it is instruction-addressable in principle. P01 and P02 were not designed for this and did not change it (P01: 4/455 grounded, P02: 0/675).
Metric caveat (from the evaluator docstring): "grounded" needs a real segment record AND lexical overlap between the item's primary key and the cited text. Strict understates (normalised names are not always spoken) and lenient overstates; neither measures clinical correctness. The existing evaluator does not check timestamps, `supports` locations or one-record-per-line; those are measured only by my supplementary script and are labelled as such.

## 2. Hypothesis and strategy
Hypothesis: an explicit procedure (one record per supporting line, numbered in order of first citation, verbatim text, the speaker/role/time printed on that line, a non-empty `supports` list, item `evidence_ids` pointing at it, no item without a line) will raise the share of items tied to a real segment. It may reduce extraction (the model may drop items it cannot cite), lengthen outputs (more records, +about 40-60 tokens each) and risk JSON errors; the criteria guard these. Whether a 0.6B model can keep track of record numbering while generating sections before the evidence list is exactly what is being tested; the template (unchanged from P00) still shows a single example evidence record, which may anchor the model. I deliberately did not edit the template (that would be a structural change beyond "instructions only").

Exact added block (the rest of the prompt is P00):
```
Evidence rules (these concern how every item is tied to the transcript, not what is extracted)
- Each transcript line has the form: [segment id] speaker id (ROLE) start-end seconds: text. One clinical_evidence record describes exactly ONE transcript line.
- Create one clinical_evidence record for every transcript line that states at least one extracted item. Number the records EV_001, EV_002, EV_003, ... in the order in which you first cite them. Text from two different lines never goes into one record.
- transcript_text: copy the text of that line exactly as written, word for word (the whole line text, or one complete sentence of it). Do not paraphrase, shorten, translate or correct it.
- speaker_id: the speaker id printed on that same line (for example person_1), never the id of a different line. speaker_role: the role printed on that line, in lower case.
- start_timestamp and end_timestamp: the start and end seconds printed on that line, written as MM:SS in whole seconds (for example 75.30 becomes 01:15). Never invent a time.
- supports: the list of locations of the items that this record supports, written as in the output format, for example "chief_complaint", "symptoms[0]", "medications[1]", "medical_history.surgical_history[0]". It must not be empty.
- evidence_ids of an item: the ids of the record(s) whose line states that item. Every item lists at least one id, and every id that is used exists as a clinical_evidence record. A record may be listed by several items only when that same line states all of them.
- If no transcript line states an item, do not output that item. Never create evidence for text that is not in the transcript.
```
Mapping to your eight points: (1) evidence_ids bullet; (2) transcript_text bullet; (3) speaker_id bullet; (4) supports bullet; (5) timestamp bullet; (6) the "only when the same line states all of them" clause; (7) never invent times/evidence; (8) last bullet.
Notes: the line format is the existing transcript rendering, so this describes the input, not labels. The role is lower-cased because the transcript prints it in capitals and the evaluator checks the role field separately from the id; this is an evidence-field rule, not a P01 schema rule. The timestamp example (75.30 -> 01:15) is arbitrary and the evaluator-side check allows +-1 s so truncation vs rounding does not matter.

## 3. Leakage check
`experiments/leak_check_P03.py` -> `evaluation/P03_leakage_check.json`: 732 gold match keys from the 100 development labels vs the added text: **0 hits**; 5-word runs of the 100 development gold evidence texts found in the added text: **0**. The only specific strings are structural locations from the output format, the id `person_1` (which appears in the transcript format) and the number 75.30. For information: I did look at one development label's evidence timestamps to learn that dataset timestamps are whole-second MM:SS values; that observation is used only in the evaluation tolerance (+-1 s), and the prompt states only "MM:SS in whole seconds".

## 4. Controlled conditions
Same as P00-P02: Qwen3-0.6B rev c1899de2, OpenVINO FP16 (EXP_002), Intel UHD 620 GPU, fresh pipeline per encounter, greedy, thinking off, max_new_tokens 6144, existing parser/validator/evaluator, frozen schema, the same 50 `prompt_dev` ids, P00 reference = EXP_003 outputs for those ids. Run id `P03_evidence_grounded_dev50`; separate outputs/evaluation folders; label file-access audit. Single run, no iteration before your review. Validation and locked test not touched. Estimated time 4-6 h (P02 took 3.3 h at 1,356 output tokens; P03 outputs may be 1,500-2,500 tokens).

## 5. Pre-registered keep/reject criteria (fixed before inference; reference = P00 on the same 50 ids; all must hold)
Evidence (targets):
* E1. Entities with at least one valid cited evidence record (evaluator status other than `unsupported`) >= 50% (P00 9.7%; P02 0.9%).
* E2. Strict + lenient grounded >= 10% of entities (P00 2.4%). Strict alone and partial are reported. (Deliberately modest because of the lexical-overlap limitation above.)
* E3. Valid evidence records (text found in a segment with that segment's speaker_id; the evaluator's own `real_segment` test) >= 75% of records (P00 33%).
* E4. Evidence timestamps matching the cited segment within +-1 s >= 70% of records (P00 0%).
* E5. Evidence `supports` non-empty >= 80% of records, and >= 70% of `supports` entries point to an existing entity that lists that evidence id (P00 0%).
* E6. Mean evidence records per encounter >= 5 (P00 1.0), to exclude gains from a single record.
Non-regression guards:
* G1. Micro F1 >= 0.042 (not more than 0.005 below P00's 0.047) and micro precision >= 0.187.
* G2. Predicted entities >= 70% of P00's (>= 145 of 207): evidence rules must not just empty the output.
* G3. Valid JSON >= 46/50; at most 2 outputs with a non-stop finish; no output at the 6,144 limit; mean output tokens <= 3,500.
* G4. Unsupported claims <= 10% of predictions (P00 1.9%); duplicate items <= 5%.
* G5. Speaker attribution (evaluator) not lower than P00 by more than 5 points (>= 41.3%; P00 46.3%); evaluated denominators will differ and will be stated.
Reported, not gating: strict and lenient grounding, per-category grounding, schema compliance and violation counts (they will likely rise with more evidence records), fully compliant records, per-category P/R/F1, latency, tokens, comparison with P01/P02, empty sections.
Decision: KEEP only if every E and G criterion passes; otherwise REJECT. A targeted P03b (for example a template change) would need your approval.

## 6. Limits I already know about
* n=50, single deterministic run; criteria thresholds were set by me from the P00 baseline above and a priori judgement, not from any P03 output.
* Evidence quality is measured structurally and lexically (does the cited line exist and does it overlap the item), not clinically. An item can cite a real line that does not truly support it, and the lexical check will often pass or fail for naming reasons.
* The prompt asks the model to number evidence records while generating other sections first; a 0.6B model may fail at that, which would show up as unresolved ids or low supports reciprocity.

## 7. Decisions I need
1. Approve (or edit) the exact P03 text and hash; the template is left unchanged (a template edit would be a separate P03b).
2. Approve the criteria in section 5.
3. Approve the 4-6 h GPU run on the 50 prompt_dev ids.

## Addendum (2026-11-12): timestamp rule
Measured convention on the development labels: MM:SS = truncation of seconds (floor 7012/7032 fields; rounding 0/3526 where the fraction >= 0.5). The timestamp bullet now reads 'written as MM:SS in whole seconds: drop the decimals, never round up (for example 75.80 becomes 01:15 and 125.40 becomes 02:05)'. Final sha256 4f7ee6f763aa886ec8090f7bb680f40eaa2f7f89e37175dfd6b8ce29daad5c9f (the earlier draft hash da91bc71... was never run). Prompt frozen.
