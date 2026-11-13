# P04 - integrated clinical extraction with segment-id citations and a deterministic evidence builder (FOR APPROVAL; no inference has been run)

Status of earlier work (recorded): P03 is REJECTED AS DESIGNED (partial, 35/50 records; all partial artifacts preserved). P02 is KEEP at the development stage only (validation postponed; not validated, not final). P00-P03, the frozen dataset, labels, schema and evaluator are untouched.
Everything below was done offline (no GPU, no model call): analysis scripts in `analysis/`, a prototype builder and its tests in `experiments/`, and the prompt files in `prompts/`.

## 1. Findings (the seven points you asked about)

### 1.1 Is the template's EV_001 record anchoring Qwen to one evidence record?
Evidence consistent with anchoring (observational; causation is not proven):
* The P00 template shows exactly one evidence record (`EV_001`) and gives non-empty `evidence_ids` (`["EV_001"]`) for **one** section only, `chief_complaint`; every other section shows `[]` (`prompts/P00_original_baseline.txt` lines 33-52).
* Across **all four prompts** (P00, P01, P02, P03; 181 outputs on prompt_dev), **every single output has exactly one evidence record** (48/48, 50/50, 50/50, 33/33). No output ever wrote a second record, even under P03, which asked for one per line.
* `chief_complaint` cites evidence in 100% of outputs of every prompt (48/48, 50/50, 50/50, 33/33); in P00 and P01 almost no other section does (P01: one medication). In P02, which extracts more, the other sections cite `EV_001` 177 times, i.e. they reuse the single template record.
* The model does mint further ids: P00 cites EV_002-EV_004 (6 references) and P02 cites EV_002-EV_004 (39 references), but no corresponding record is ever written. So the model "wants" more than one citation but never produces the records. A likely second cause is that the evidence list comes last, after all items, and has to repeat whole sentences; a 0.6B model does not do this bookkeeping.
* Untested: a template-only change cannot be separated from the citation-by-id change in P04 (both change at once). The smoke test can show whether multi-id citation appears, not why.

### 1.2 How the original transcript represents segments, speakers, roles and times
Checked on all 100 development inputs (4,749 segments; `analysis/evidence_design_probe.json`):
* Segment object: `segment_id` ("SEG0001", ...), `speaker_id` ("person_1", ...), `role` (capitals), `start_seconds`, `end_seconds`, `duration_seconds`, `text`.
* Rendered to the model (existing `render_transcript`): `[SEG0003] person_1 (PATIENT) 15.77-26.37s: text`.
* 100/100 encounters: ids well-formed and sequential from SEG0001; speaker ids `person_N`; each speaker has exactly one role; times non-decreasing; no empty text. Mean 47.5 segments per encounter (32-67). Roles seen: DOCTOR, PATIENT, NURSE, FAMILY_MEMBER, CAREGIVER, CLINICAL_STAFF, UNKNOWN.
* 46 segments repeat the text of another segment in the same encounter (short replies), so **text alone cannot identify a segment, but the id always can**. This is a reason for ids over copied text.

### 1.3 Can Qwen return supporting segment IDs?
**Not known; it can only be tested by inference, which I have not run.** What is known offline:
* The task is simpler than P03's: copy a short printed token (SEG0007) per item instead of copying sentences, speaker ids, roles and times into a separate list at the end. Dangling ids already occur (EV_002-004), so the model readily emits identifiers.
* P03 showed the model can copy a real line verbatim (97% of records had text found in the transcript), so copying a printed id is within reach, but picking the right line for each item is the open question.
* The 3-5 record smoke test is designed to answer it (section 7.1). Failure modes I expect: placeholder copied literally ("<segment id>"), ids repeated for every item, always the first lines, or leaving the list empty.

### 1.4 Evidence correctness: what "supported" can and cannot mean
I measured the existing evaluator's grounding metric offline on the **gold labels themselves** and on cheap baselines (prompt_dev, 50 ids):

| Method (what picks the segment) | Strict+lenient lexical grounded | Cites a gold-cited segment (strict-TP items, n=153) |
|---|---|---|
| Gold labels (ceiling for the metric) | 66.0% (strict 43.2%, partial 34.0%) | n/a |
| P03 model-written evidence (partial run) | 0% | not computed |
| First segment (the P03 behaviour) | 0.1% | 0.0% |
| Random segment | 3.4% | 4.6% (4.0% expected) |
| **Lexical best-segment retrieval on P02's items** | **86.7%** (strict 82.5%) | **88.9%** (136/153) |

Consequences:
1. A segment id that exists is trivially true (the builder guarantees it); it proves nothing about support.
2. The evaluator's lexical grounding **can be gamed**: a retriever that picks the segment by the same lexical test scores 86.7%, above the gold's own 66%. It is a circular measure and must not be the main evidence-correctness metric. Its ceiling on gold is 66%, and 20-26% for social history, review of systems and uncertainties.
3. The metric I can trust as a semantic proxy is **agreement with the gold-cited segments** for entities that strictly match a gold entity (hit@any, set precision/recall, all-gold-segments recall). It cannot be gamed by lexical overlap with the item's own key alone, but it exists only for the matched items (n about 150 on 50 records), so it says nothing about false-positive items.
4. A deterministic lexical retriever already reaches 88.9% hit on matched items. If Qwen's own ids do not beat this, the model-based citation adds nothing over code. This gives a **zero-inference control arm (R)**: apply the same builder with retrieval-chosen ids to the existing P02 outputs. I propose to run arm R (CPU only) as the baseline that Qwen's ids must be compared with. Caveat: retrieval is evaluated on items whose keys already match gold, which favours it.
5. For items that do not match gold (most items), correctness can only be judged by a person. Proposal: a stratified human audit of 30 items (section 7.3), done by you or a delegate; I can pre-annotate but my annotations would not be independent.

### 1.5 Fit with the frozen schema (nothing is modified)
* The schema's `clinical_evidence` record has exactly: `evidence_id, speaker_id, speaker_role, transcript_text, start_timestamp, end_timestamp, supports` (validator `NESTED["clinical_evidence"]`). Every item carries `evidence_ids` (the entity key sets in the validator/frozen schema).
* There is no place for segment ids in the **final** output, so `source_segments` exists only in the **intermediate** model output; the builder removes it and writes the schema fields. The final JSON passes through the unmodified validator/evaluator.
* Dataset conventions that the builder must reproduce, all measured on the 100 development labels: one record = one whole segment (3,516/3,516); numbered EV_001... in segment order (100/100 encounters); `speaker_role` = lower-case role (1:1 mapping for all 7 roles); times = floor(seconds) as MM:SS (all start/end fields); `supports` = `section[index]` / `medical_history.sub[index]` / `chief_complaint`, reciprocal to the items' `evidence_ids` (6,432/6,432).
* Note: the example in the root `clinical_extraction_schema.json` writes supports like `SYM_001`, which is not what the labels use (`symptoms[0]`); I follow the labels, which is also what the P00 prompt text says. The evaluator does not read `supports` at all.
* Every gold item has evidence ids (3,621/3,621), on average 1.78 segments per item (1: 1,635 items, 2: 1,595, 3: 163, 4: 128, 5+: about 100). The gold never cites SEG0001 and cites the first two segments for 0.1% of ids (chief complaint 4%, mean position 2.8).

### 1.6 Preserving P02's gains
P04 keeps the P02 coverage block **verbatim** and changes nothing else in the extraction instructions. The only extraction-relevant changes are the template's evidence placeholders and the replaced evidence rule. Whether this is "preserved" is a measurable claim: the criteria require extraction metrics on the same 50 ids to stay within tolerance of P02.

## 2. Architecture
```
transcript (rendered with segment ids)  +  P04 prompt
        |  Qwen3-0.6B (unchanged model, settings)
        v
INTERMEDIATE JSON  = frozen schema, with "source_segments": ["SEG0007", ...] on every item and no clinical_evidence      [saved as the raw output]
        |  existing parser (parse_response)
        v
evidence_builder.build_evidence(intermediate, transcript)   (deterministic, transcript only, never reads labels)
        v
FINAL JSON = frozen schema (evidence_ids + clinical_evidence + supports)  -> existing validator -> existing evaluator (unmodified)
```
Integration without touching existing code: a new EXP_004 runner (same pattern as `run_prompt.py`) wraps the existing `inference_runner` loop at run time by replacing its parse step with "original parse, then build"; the original loop saves raw output (= intermediate), validates and saves the final JSON, and writes the usual manifest. The intermediate parsed JSON and the per-record builder report are saved alongside. Nothing in the existing modules changes.

## 3. Intermediate output format
Identical to the P00/P02 template except: (a) every `"evidence_ids": [...]` is replaced by `"source_segments": ["<segment id>"]` in all 18 places (a non-empty placeholder everywhere, so no section is shown with an empty list, which is the pattern that coincided with citing in one section only); (b) the `clinical_evidence` line is removed. Example item: `"symptoms": [{"name": "", ..., "reported_by": "", "certainty": "", "source_segments": ["<segment id>"], "confidence": null}]`.
Placeholder risk: the model may copy `<segment id>` literally. The builder rejects it as an invalid id (counted, never repaired).

## 4. The P04 prompt
Files: `prompts/P04_integrated_segment_evidence.txt`, **sha256 `a4c17897b89e90ff4eaea119ea5f4a995b2459652cdf24152b4f174fe217ab68`**; diffs `prompts/P04_integrated_segment_evidence.diff_vs_P00` (66 lines) and `.diff_vs_P02` (53 lines). Not frozen (needs your approval; the file is writable until then, and any edit changes the hash).
Construction: P00 + the P02 coverage block (verbatim) + a new Source rules block + a replaced evidence rule + the template changes in section 3. Relative to P02 it changes exactly three things:
1. The P00 evidence rule (1 line) becomes: `- Every extracted item lists in source_segments the segment id(s) of the transcript line(s) that state it (see the Source rules).`
2. New block inserted after the coverage block:
```
Source rules (these concern which transcript lines an item comes from, not what is extracted)
- Every transcript line starts with its segment id in square brackets, for example [SEG0007]. Write ids exactly as printed, in the form SEG0007, without brackets.
- For every extracted item, source_segments lists the id of the line in which the item is stated. Use one to three ids: the line that states the fact and, when it is needed to understand the fact, the line that asks about it (for example the doctor's question and the patient's answer).
- Choose the line where the fact is actually said, never a line only because it comes first. A greeting line is almost never the source of a clinical fact.
- Never write evidence records, speaker ids, times or quotations of transcript text: they are added automatically from the ids.
- If no transcript line states an item, do not output that item.
```
3. The template changes of section 3.
Prompt length: 10,588 characters (P00 7,032; P02 9,688), about 4,700 prompt tokens per encounter (P02 mean 4,329); expected output tokens about the same as P02 (about 1,350; the model no longer writes evidence records but adds one short id list per item). Expected latency about 4 min per record.

Label-informed choices that you should know about (the prompt contains no label text, no entity names, no label strings):
* "one to three ids ... the line that asks about it": informed by the gold convention that items cite 1.78 segments on average and typically a question plus its answer. This is a convention about citation, not clinical content.
* "A greeting line is almost never the source": informed by the P03 failure (76% of records cited the first segment) and by the gold (never cites SEG0001).
Decision D2 below lets you remove either.

## 5. Evidence builder (prototype done and tested; `experiments/evidence_builder.py`)
* Inputs: intermediate JSON + the transcript file; no labels; deterministic; pure function (`build_evidence(intermediate, transcript, max_segments=4)`).
* Per item: accept ids that exist; tolerate only deterministic spelling variants (`seg3`, `[SEG0003]`, `SEG03`) and count them as "normalised"; reject everything else as "invalid" and count it; remove duplicates; cap at 4 ids per item (gold: 2.8% of items cite more than 4, 100 of 3,621; the cap affects them only).
* Builds one record per distinct cited segment, numbered in segment order, copying `speaker_id`, lower-case `role`, exact `text`, floor-second MM:SS times; `supports` lists the locations of every item that cites it (traversal order: chief complaint, symptoms, negatives, history lists, then the other sections).
* Never deletes, adds, reorders or edits extracted items or other fields. An item with no valid id is kept with `evidence_ids: []` and reported as uncited (the metric exposes it; the builder does not hide it). If the model wrote its own `evidence_ids` or `clinical_evidence`, they are ignored/discarded and counted.
* Per-record build report: entities, cited/uncited, ids exact/normalised/invalid/duplicate/over-cap, invalid examples, discarded model evidence, number of records.
* **Tests** (`experiments/test_evidence_builder.py`, passing): synthetic edge cases (invalid ids, spelling variants, duplicates, string instead of list, over-cap, model-written evidence, re-running on final output), and a **round trip on all 100 development gold labels**: gold evidence converted to segment ids, rebuilt by the builder, compared with the original: **3,516 of 3,516 records identical** (id, speaker, role, text, both timestamps), **supports identical (set and order) 3,516/3,516**, evidence ids per item identical in **100/100 encounters**, **0 schema violations** in the evidence fields. The builder therefore reproduces the dataset's evidence conventions exactly when it is given the correct ids.

## 6. Schema mapping
| Intermediate (model) | Final (frozen schema) |
|---|---|
| `item.source_segments: ["SEG0007","SEG0008"]` | `item.evidence_ids: ["EV_00k", "EV_00m"]` (segment order) |
| (not written by the model) | `clinical_evidence[k] = {evidence_id, speaker_id, speaker_role (lower case), transcript_text (exact), start_timestamp, end_timestamp (floor MM:SS), supports}` |
| `chief_complaint.source_segments` | `chief_complaint.evidence_ids`; `supports` entry `"chief_complaint"` |
| item in `medical_history.social_history[1]` | `supports` entry `"medical_history.social_history[1]"` |
All other keys pass through untouched; the schema, validator and evaluator are not modified.

## 7. Evaluation and pre-registered criteria
### 7.1 Smoke test (3-5 records; feasibility only, no performance claims; after your approval)
Ids (all prompt_dev): **00035, 00037, 00040** (P00 reproducibility records) and **00215, 00248** (the two failures you identified). Runner: new EXP_004 script, GPU, same settings (about 20 minutes). Gates for "proceed to a 50-record run" (descriptive otherwise):
* S1 5/5 intermediate outputs parse as JSON and 5/5 builder runs succeed with the final JSON accepted by the existing validator (no violation in evidence fields).
* S2 at least 90% of items have at least one valid id, and at least 90% of emitted ids are valid (not placeholders or non-existent ids).
* S3 at least 5 evidence records in at least 4 of 5 encounters (previous maximum: 1).
* S4 not more than 10% of cited ids are in the first two segments (gold: 0.1%; P03: 76% first segment).
* S5 not collapsed: items at least 70% of P02's items on the same 5 ids; mean output tokens at most 3,000.
* S6 audit: builder changes nothing except the evidence fields (checked by diff); 0 label files opened.
* Reported for information: hit@any against gold-cited segments on strict-TP items (too few to gate), items citing the greeting, ids per item, my read of the 00215 and 00248 evidence.

### 7.2 Full 50-record development run (criteria fixed now; the run needs a separate approval)
Reference for extraction is P02 on the same 50 ids; reference for evidence is P00 and arm R.
Extraction preservation: P1 micro F1 >= 0.111 (P02 0.121 minus 0.010) and micro recall >= 0.075 (P02 0.082) and precision >= 0.187; P2 predicted items >= 85% of P02's (575 of 675); P3 valid JSON >= 46/50 and at most 2 non-stop finishes, mean output <= 3,000 tokens; P4 unsupported claims <= 15%, duplicates <= 5%.
Evidence: V1 >= 90% of items carry a valid id; V2 >= 95% of emitted ids valid; V3 >= 8 evidence records per encounter on average (gold about 35; P00-P03: 1); V4 greeting trap: <= 3% of cited ids in the first two segments (gold 0.1%); V5 **semantic**: hit@any against gold-cited segments on strict-TP items >= 60%, and not below arm R's value by more than 15 points (if it is, the model's ids are worse than code retrieval and the architecture should use retrieval instead); V6 strict+lenient lexical grounded >= 30% (gold ceiling 66%; reported with the warning that it is gameable); V7 human audit (7.3) >= 70% of audited items judged supported.
Reported: strict/lenient/partial/unsupported grounding, per-category grounding, set precision/recall of cited segments, ids per item, uncited items per category, speaker attribution, schema compliance and violations (expected to resemble P02), latency, tokens.
Decision: KEEP only if all P, V criteria pass; otherwise REJECT or redesign.

### 7.3 Human audit (V7)
A stratified sample of 30 items (about 2 per category, mixed correct/incorrect extraction) from the 50-record run, each shown as: item key, cited segment text(s), speaker. A reviewer you name marks supported / partly / not supported. I can pre-annotate but that would not be independent. You can drop V7 or reduce the sample.

### 7.4 Arm R (no inference; I propose to run it before or alongside the smoke test)
Apply the builder to the existing **P02** outputs with retrieval-chosen ids. It produces final-schema JSON for the 50 prompt_dev ids and all evidence metrics at zero GPU cost, is the control for V5/V6, and shows what a code-only evidence step achieves on P02's extraction. It is a control, not a candidate (it makes the claim "evidence is a retrieval problem" testable). It needs no new approval beyond this design unless you prefer to hold it.

## 8. Leakage and integrity checks
* `experiments/leak_check_P04.py` -> `evaluation/P04_leakage_check.json`: 732 gold match keys of the 100 development labels vs all text added relative to P00 (the P02 block plus the new text): **0 hits**; 5-word runs of the development gold evidence texts: **0**.
* Prompt contains no gold segment id, entity name or sentence; only the arbitrary example id SEG0007.
* The builder never opens labels; the runner will use the same file-access audit as before (0 label/blueprint files during inference and building). The 5 smoke ids and all 50 are development ids; validation and the locked test set are not used (asserted in the runner).
* The unmodified existing evaluator and validator score the final output; analysis scripts read gold only after generation.

## 9. Limitations and risks
* Whether Qwen3-0.6B can choose correct ids is untested; the architecture may fail at step one (placeholders, same ids everywhere). The smoke test is built to find that cheaply.
* Evidence correctness beyond gold agreement on matched items and a 30-item human audit is not measurable by the current evaluator.
* The builder makes structure correct by construction, so structural evidence metrics (valid records, speakers, timestamps, supports consistency) are now trivially perfect for cited items. They must not be read as semantic correctness; that is why V5-V7 carry the weight.
* P02's extraction may degrade because the citation task competes for attention in a 0.6B model; P1-P2 test it.
* Changing both the template and the mechanism makes it impossible to say which caused any change in citation behaviour.
* The 4-id cap and tolerant id spellings are design choices; both are counted in the build report.
* This is not "P02 + P03": P03's evidence-record instructions are dropped entirely.

## 10. Decisions I need
* **D1** Approve the architecture (intermediate format + builder) and the prompt text/hash, or ask for changes.
* **D2** Label-informed wording: keep "one to three ids ... question and answer" and "a greeting line is almost never the source", or remove either.
* **D3** Approve the smoke-test ids (00035, 00037, 00040, 00215, 00248) and gates S1-S6.
* **D4** Approve running arm R (CPU only, no inference) as the retrieval control.
* **D5** Confirm the 50-record criteria in 7.2 (or edit); the 50-record run still needs its own approval after the smoke test.
