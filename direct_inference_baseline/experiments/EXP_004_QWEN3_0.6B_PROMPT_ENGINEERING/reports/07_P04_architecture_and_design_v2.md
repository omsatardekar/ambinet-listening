# P04 - integrated clinical extraction with segment-id citations and a deterministic evidence builder - REVISED DESIGN (v2; FOR APPROVAL; no model inference has been run)

Version history: v1 (`reports/07_P04_architecture_and_design.md`, prompt draft sha256 a4c17897...ab68) is preserved unchanged. This v2 incorporates your review decisions D1-D5. The superseded prompt draft and its diffs are in `prompts/superseded_drafts/`.
Status: P03 REJECTED AS DESIGNED (partial). P02 KEEP at the development stage only (validation postponed; not validated, not final). The 50 prompt_dev records are **not** an independent validation set; the separate 50-record validation subset is preserved untouched for evaluation after prompt freeze; the 400 locked test records are untouched. The P04 prompt is **not frozen**.

## 0. Revisions made in v2
| Your decision | Change |
|---|---|
| D2 question/answer evidence | Source rules now say: select the lines that directly state or confirm the fact; include a question line only when needed to interpret the response; a question alone is never proof; the patient's answer is the evidence for a denied symptom (generic example, no clinical term). |
| D2 greetings | "never a line only because it comes first" and "a greeting line is almost never the source" removed. Now: select evidence by meaning, not by position; do not cite greetings or small talk unless they contain clinically relevant information. |
| D2 number of ids | "one to three ids" removed. Now: the minimum number of segments needed; several when the fact genuinely requires them; no extra segments when one suffices. The **builder's default cap of 4 ids per item was removed too** (no truncation; long lists are only reported as `items_with_more_than_6_ids`). An explicit cap can still be passed for analysis. |
| D3 smoke test | Ids verified (section 7.1); S1, S2, S3, S5 kept; S4 now report-only (position distribution, greeting citations, segment-by-segment inspection); S6 clarified with an automatic integrity check; actual intermediate and final JSON will be shown for all five records. |
| D4 arm R | Run offline (results in section 7.4). |
| D5 | Gates kept as provisional development gates; V5 reference defined precisely (section 7.2). |

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
**Not known; it can only be tested by inference, which I have not run.** What is known offline (and see arm R, section 7.4, for what a code-only retriever achieves):
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

## 4. The P04 prompt (revised)
Files: `prompts/P04_integrated_segment_evidence.txt`, **sha256 `e05c8beaf82380bdd9581acd07fc77940a363346eb003d44295364683c5aaf55`**; diffs `prompts/P04_integrated_segment_evidence.diff_vs_P00` (67 lines), `.diff_vs_P02` (54 lines), `.diff_vs_draft1` (7 lines, the v1 -> v2 wording change). Not frozen; any further edit changes the hash. Superseded draft: sha256 a4c17897...ab68 (never run).
Construction: P00 + the P02 coverage block (verbatim) + the Source rules below + the replaced evidence rule + the template changes of section 3. Relative to P02 it changes exactly three things:
1. The P00 evidence rule (1 line) becomes: `- Every extracted item lists in source_segments the segment id(s) of the transcript line(s) that state it (see the Source rules).`
2. New block after the coverage block (**revised wording**):
```
Source rules (these concern which transcript lines an item comes from, not what is extracted)
- Every transcript line starts with its segment id in square brackets, for example [SEG0007]. Write ids exactly as printed, in the form SEG0007, without brackets.
- For every extracted item, source_segments lists the id of each line that directly states or confirms the item. Select the minimum number of transcript segments needed to support each fact. Use several segments when the fact genuinely requires them; do not add more segments when one is sufficient.
- Include a question line only when it is necessary to interpret the response; a question alone is never proof of a clinical fact. For example, when the doctor asks whether the patient has a symptom and the patient answers no, the patient's answer is the evidence for the denied symptom.
- Select evidence by meaning, not by position in the transcript. Do not cite greetings or small talk unless they contain clinically relevant information.
- Never write evidence records, speaker ids, times or quotations of transcript text: they are added automatically from the ids.
- If no transcript line states an item, do not output that item.
```
3. The template: `"source_segments": ["<segment id>"]` in all 18 places, no `clinical_evidence` record.
Length 10,887 characters (P00 7,032; P02 9,688). Expected: about 4,700 prompt tokens; output near P02's (about 1,350 tokens); about 4 minutes per record.
Wording choices: the example in the third bullet uses no clinical term, so it cannot overlap label vocabulary. Removing the numeric limit and the first-line remarks also removes the two label-informed choices flagged in v1; what remains is only the general principle that the answer line is the evidence, which you specified.

## 5. Evidence builder (prototype done and tested; `experiments/evidence_builder.py`)
* Inputs: intermediate JSON + the transcript file; no labels; deterministic; pure function (`build_evidence(intermediate, transcript, max_segments=4)`).
* Per item: accept ids that exist; tolerate only deterministic spelling variants (`seg3`, `[SEG0003]`, `SEG03`) and count them as "normalised"; reject everything else as "invalid" and count it; remove duplicates; **no cap by default** (v2; gold: 100 of 3,621 items cite more than 4 segments, up to 13): items with more than 6 ids are counted in the build report, never truncated.
* Builds one record per distinct cited segment, numbered in segment order, copying `speaker_id`, lower-case `role`, exact `text`, floor-second MM:SS times; `supports` lists the locations of every item that cites it (traversal order: chief complaint, symptoms, negatives, history lists, then the other sections).
* Never deletes, adds, reorders or edits extracted items or other fields. An item with no valid id is kept with `evidence_ids: []` and reported as uncited (the metric exposes it; the builder does not hide it). If the model wrote its own `evidence_ids` or `clinical_evidence`, they are ignored/discarded and counted.
* Per-record build report: entities, cited/uncited, ids exact/normalised/invalid/duplicate/over-cap, invalid examples, discarded model evidence, number of records.
* **Integrity function** `verify_only_evidence_changed(intermediate, final)`: after removing only the evidence-related keys (item `source_segments`/`evidence_ids`, top-level `clinical_evidence`) from both, the two objects must be identical in values, categories, item order and key order. It is asserted in the tests, in arm R (50/50 against both the retrieval input and the original P02 output) and will be asserted for every P04 record.
* **Tests** (`experiments/test_evidence_builder.py`, passing): synthetic edge cases (invalid ids, spelling variants, duplicates, string instead of list, over-cap, model-written evidence, re-running on final output), and a **round trip on all 100 development gold labels**: gold evidence converted to segment ids, rebuilt by the builder, compared with the original: **3,516 of 3,516 records identical** (id, speaker, role, text, both timestamps), **supports identical (set and order) 3,516/3,516**, evidence ids per item identical in **100/100 encounters**, **0 schema violations** in the evidence fields, and the integrity check true for 100/100 encounters. Re-run after removing the cap: unchanged results. The builder therefore reproduces the dataset's evidence conventions exactly when it is given the correct ids.

## 6. Schema mapping
| Intermediate (model) | Final (frozen schema) |
|---|---|
| `item.source_segments: ["SEG0007","SEG0008"]` | `item.evidence_ids: ["EV_00k", "EV_00m"]` (segment order) |
| (not written by the model) | `clinical_evidence[k] = {evidence_id, speaker_id, speaker_role (lower case), transcript_text (exact), start_timestamp, end_timestamp (floor MM:SS), supports}` |
| `chief_complaint.source_segments` | `chief_complaint.evidence_ids`; `supports` entry `"chief_complaint"` |
| item in `medical_history.social_history[1]` | `supports` entry `"medical_history.social_history[1]"` |
All other keys pass through untouched; the schema, validator and evaluator are not modified.

## 7. Evaluation and pre-registered criteria (revised)
### 7.1 Smoke test (feasibility; not started; needs your approval to run)
Ids: **00035, 00037, 00040, 00215, 00248**. Verified by `experiments/check_smoke_ids.py` -> `evaluation/P04_smoke_ids_check.json`: all five are in the 50-record prompt_dev subset, none is in the validation subset, none is in the locked 400-record test set; the subsets do not overlap (0/0/0).
Runner: a new EXP_004 script, GPU, the same settings; resumable; file-access audit. Gates:
* **S1** 5/5 intermediate outputs parse as JSON; the builder succeeds on 5/5; the final JSON is accepted by the existing validator with no violation in evidence fields.
* **S2** at least 90% of items have at least one valid id, and at least 90% of the emitted ids are valid (not placeholders or non-existent ids).
* **S3** at least 5 evidence records in at least 4 of 5 encounters (all earlier outputs: 1).
* **S5** items at least 70% of P02's item count on the same 5 ids; mean output tokens at most 3,000.
* **S4 (revised, report only, no rejection threshold):** the distribution of cited segment positions; the number of citations pointing to greetings or irrelevant opening lines; and a segment-by-segment inspection of whether each cited line genuinely supports its item (my reading, shown for your review, not independent, with doubtful cases flagged).
* **S6 (clarified):** (a) the builder modifies no extracted clinical value or category: `verify_only_evidence_changed(intermediate, final)` must be true for all five, with equal item counts and order, i.e. the builder only resolves references and creates evidence-related fields; (b) missing and invalid references are reported **separately** from the extraction: items with no or mistyped `source_segments`, ids invalid (not in the transcript, placeholder copies), ids normalised (spelling only), duplicates removed, items left uncited; they are not repaired beyond deterministic spelling normalisation; (c) 0 label or blueprint files opened.
* **Deliverable:** for each of the five records the report will show the **actual raw intermediate model JSON and the final built JSON** in full (also saved as files), a table item -> cited segment(s) with the segment text, and the builder report. Aggregates alone will not be presented.
Outcome: "proceed / revise / stop" for your decision; no performance claim.

### 7.2 Full 50-record development run (provisional development gates, not proof of final performance; needs its own approval)
Reference for extraction: P02 on the same 50 ids. Reference for evidence: P00 and arm R. **All metrics are reported separately; trade-offs between extraction coverage, precision, schema compliance and evidence quality are shown side by side (P00, P02, P04, arm R), not merged into one number.**
* **Extraction:** F1 >= 0.111; recall >= 0.075; precision >= 0.187; predicted items >= 85% of P02's (>= 575 of 675); valid JSON >= 46/50 with at most 2 non-stop finishes; mean output <= 3,000 tokens; unsupported claims <= 15%; duplicates <= 5%.
* **Evidence:** >= 90% of items with at least one valid evidence id; >= 95% of emitted ids valid; >= 8 evidence records per encounter on average; gold-segment agreement (hit-any on strict-TP items) >= 60% **and** within 15 percentage points of arm R (definition below); strict+lenient lexical grounding >= 30% (reported with the gameability warning); human audit >= 70% of audited items judged supported.
* **V5 definition, made precise now, before any P04 result:** the arm R reference is the **better** of the two pre-registered configurations on the same metric, R_simple at 88.9% (R_main 81.0%). "Within 15 points" therefore means P04 hit-any >= 73.9%, which is stricter than the 60% floor. P04's matched-item set will differ from P02's, so the comparison is approximate; both set sizes are reported.
* Structural evidence fields are correct by construction (arm R shows 100% for all of them), so they are not evidence of semantic quality; V5-V7 carry the weight.
* **Observation about V3 (>= 8 records per encounter), for your attention; not changed:** arm R, which cites exactly one segment per item for P02's 13.6 items per record, yields 6.88 (R_main) and 7.58 (R_simple) evidence records per encounter, below 8. The gold has about 35 records per encounter (1.78 segments per item, about 36 items). If Qwen cites one segment per item, V3 may fail for reasons unrelated to citation quality. You may keep V3 or relax it (for example to 6); I have not changed it.
Decision: KEEP only if all extraction and evidence gates pass; otherwise REJECT or redesign. Validation (the preserved 50 records) is run only after prompt freeze and your approval.

### 7.3 Human audit (V7)
Stratified sample of 30 items from the 50-record run; each shown with the item, the cited segment text(s), speaker and role; a reviewer you name marks supported / partly / not supported. A pilot sample of 30 arm R items is saved as `arm_R/R_main_qualitative_sample_30.json` to test the format; I read the first 16 (section 7.4); that reading is not independent.

### 7.4 Arm R - offline retrieval control (RUN; no model inference)
**Setup.** Inputs: the existing P02 outputs for the 50 prompt_dev ids (parsed predictions, **not modified**: `outputs/P02_comprehensive_extraction_dev50/`) and the same transcript inputs. Script `experiments/arm_r_retrieval.py`; outputs in `arm_R/` (final predictions, build reports, retrieval choices, summaries) and `evaluation/evidence_diagnostics_ArmR_*.json`. Development ids only; labels are opened only after the final outputs are written, never by the retrieval or the builder; no validation or test ids.
**Retrieval method (two configurations fixed in the script before any result was viewed; R_simple reproduces the earlier probe I had already seen).**
* Tokens: evaluator tokeniser (`content_tokens`), 5-character stems (parameter), word-prefix matching inside each segment.
* **R_main**: query = all descriptive text fields of the item (per-category field list in the script); segment score = IDF-weighted share of query stems found in it (IDF per encounter = ln(1 + N/df)); top-1 segment; ties -> more matched stems, then earliest; **abstain** (no citation) if the score is below **0.5** (parameter).
* **R_simple**: query = the evaluator's primary key only; unweighted share of stems found; top-1; ties -> earliest; never abstains.
* Both cite exactly one segment per item; no role, position or semantic information; the builder then creates the evidence records and `supports`.
**Results (50 records, 679 items).**
| | R_main | R_simple |
|---|---|---|
| Items cited / abstained (uncited) | 600 / 79 (11.6%) | 666 / 13 (1.9%) |
| Invalid ids | 0 | 0 |
| Evidence records per encounter | 6.88 | 7.58 |
| Selected segment position (index 0 = SEG0001; 5 = index 5 or later) | {'1': 2, '2': 33, '3': 21, '4': 20, '5': 524} | {'0': 76, '1': 2, '2': 42, '3': 20, '4': 27, '5': 499} |
| Gold-segment hit-any on strict-TP items (n = 153) | **81.0%** (4 abstentions counted as misses) | **88.9%** |
| Set precision / recall vs gold-cited segments | 83.2% / 41.5% | 88.9% / 45.5% |
| Random choice (same set size) / first-segment choice, hit rate | 3.8% / 0.0% | 4.0% / 0.0% |
| Evaluator grounding strict / lenient / partial / unsupported (of 675) | 516 / 27 / 57 / 75 | 557 / 28 / 81 / 9 |
| Structural: valid records, speaker, role, timestamps (exact floor), `supports` non-empty and reciprocal | 100% for all | 100% for all |
| Schema violations in evidence fields (final) | 0 | 0 |
| Extraction (strict TP/FP/FN; micro P/R/F1) | 153/522/1707; 0.227/0.082/0.121 | identical |
| Speaker attribution; unsupported claims (evaluator) | 42.1% (126 evaluated); 12.5% | identical |
Total schema violations fall from 1,064 (P02) to 945 because the evidence-field violations disappear; every other violation is unchanged (the builder fixes nothing else, by design).
**What this shows.**
* **Structurally valid: yes, by construction.** All ids resolve; every record is a real whole segment with the right speaker, role, floor-second timestamps and reciprocal `supports`. This proves the builder, not the semantics.
* **Extraction untouched:** the final outputs differ from the P02 outputs only in evidence fields (integrity check true for 50/50); strict extraction counts are identical (153/522/1707).
* **Semantic relevance against gold-cited segments on the 153 strictly matched items: R_simple 88.9%, R_main 81.0%** (random about 4%, first segment 0%). The pre-registered main configuration did **not** beat the simple one: the extra query fields and the abstention threshold cost about 8 points (symptoms 82% -> 45%, review of systems 50% -> 17%). I did not tune it after seeing this.
* **Greeting trap in the simple retriever:** R_simple falls back to SEG0001 for **76 items** when no stem matches (it never abstains): exactly the P03 failure. R_main abstains instead (0 items at SEG0001), at the cost of 11.6% uncited items.
* **The lexical metric is circular:** evaluator strict+lenient grounding is 80.4% (R_main) and 86.7% (R_simple), above the 66% the gold labels reach. A retriever that optimises word overlap scores high without understanding; the lexical figure is not evidence of correctness.
* **Qualitative reading (first 16 of the 30 sampled R_main items; my judgement, not independent):** 8 clearly right (a medication line for a named drug, a surgical-history line, the doctor's examination line for an examination finding, the vitals line for a vital sign); 4 abstentions (no wording overlap); 2-3 weak or wrong. Clearest error: a family-history item pointed at the patient's own diagnosis line ("I have diabetes, for about a year"): the words match but the person differs. One examination finding ("no fever") pointed at the temperature reading, which supports it only indirectly.
**Limitations of lexical retrieval.** (1) It needs shared words, so standardised terms that were not spoken (the P02 terminology rule) fail or abstain. (2) It cannot tell whom a fact is about (own vs family history) or polarity. (3) It picks one segment, so set recall is only 41-45% of the gold-cited segments (gold items cite 1.78 on average). (4) The agreement figure exists only for the 153 items that already match gold, where the key words are usually the spoken words: it is optimistic and says nothing about the other 522 extra items. (5) A reader can inspect only a sample; the human audit is still needed.
**Consequence for the design.** Qwen's ids must be compared with this baseline: if hit-any is clearly below it, a retrieval-based or hybrid evidence step (model proposes, code verifies or falls back) is the better architecture. That is an option for a later version, not part of P04.

## 8. Leakage and integrity checks
* `experiments/leak_check_P04.py` -> `evaluation/P04_leakage_check.json`: 732 gold match keys of the 100 development labels vs all text added relative to P00 (the P02 block plus the new text): **0 hits**; 5-word runs of the development gold evidence texts: **0**.
* Prompt contains no gold segment id, entity name or sentence; only the arbitrary example id SEG0007.
* The builder never opens labels; the runner will use the same file-access audit as before (0 label/blueprint files during inference and building). The 5 smoke ids and all 50 are development ids; validation and the locked test set are not used (asserted in the runner).
* The unmodified existing evaluator and validator score the final output; analysis scripts read gold only after generation.

* v2 re-run of `experiments/leak_check_P04.py` on the revised prompt: 732 gold keys -> **0 hits**; gold evidence 5-word runs -> **0**. The revised example uses no clinical term.
* The arm R run and the builder tests read gold only in evaluation/verification code, after the outputs were written; the builder and the retriever never open labels. No validation or test records were read.

## 9. Limitations and risks
* Whether Qwen3-0.6B can choose correct ids is untested; the architecture may fail at step one (placeholders, same ids everywhere). The smoke test is built to find that cheaply.
* Evidence correctness beyond gold agreement on matched items and a 30-item human audit is not measurable by the current evaluator.
* The builder makes structure correct by construction, so structural evidence metrics (valid records, speakers, timestamps, supports consistency) are now trivially perfect for cited items. They must not be read as semantic correctness; that is why V5-V7 carry the weight.
* P02's extraction may degrade because the citation task competes for attention in a 0.6B model; P1-P2 test it.
* Changing both the template and the mechanism makes it impossible to say which caused any change in citation behaviour.
* The builder has no id cap (long lists are reported); tolerant id-spelling normalisation is a design choice, counted separately in the build report.
* This is not "P02 + P03": P03's evidence-record instructions are dropped entirely.
* Arm R shows that code alone reaches about 81-89% gold-segment agreement on matched items, so a model that does worse adds no value over retrieval; this has to be checked in the smoke and 50-record runs.
* Removing the numeric limit and the first-line remarks could lead a 0.6B model to over-cite or to cite generically; the build report counts ids per item and the audit checks relevance.

## 10. Decisions I need
* **E1** Approve the revised prompt text and hash (section 4), or request edits. It is still not frozen.
* **E2** Approve the revised smoke-test gates and deliverables (section 7.1), including that I show the full intermediate and final JSON for all five records and my non-independent segment-by-segment reading.
* **E3** Confirm the precise V5 reference (the better arm R configuration: gold-segment agreement >= 73.9%) and decide whether to keep V3 (>= 8 records per encounter) given the arm R observation.
* **E4** Authorise execution of the smoke test (5 records, about 20 minutes of GPU) only after you have reviewed this revised design.
