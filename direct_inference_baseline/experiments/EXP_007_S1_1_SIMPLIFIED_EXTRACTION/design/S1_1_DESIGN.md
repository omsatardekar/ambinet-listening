# EXP_007 – S1.1 design proposal (for approval; NO 50-record inference has been run)

Status: design + isolated technical feasibility only. Everything in `feasibility/` used **hand-written synthetic transcripts**; no project transcript was run through the model, no label, validation (50) or locked-test (400) record or sealed hash file was opened, Batch 002 was not used. The only project data read was the 50 prompt-dev **input** transcripts, for a token-count/role-ambiguity study (no model output, no labels). S1.0 (EXP_006) and all EXP_001–006 artifacts are unchanged. Any later run on the 50 prompt-dev records is further tuning on records already used for P02 and S1.0: **not independent validation**. P02 stays the primary baseline; the post-hoc parsed-only S1.0 figure (0.154) is a diagnostic only and is not used as S1.0's result (S1.0 = 0.1192).

## 1. Findings on the four problems

### A. Template copying – cause and fix
S1.0 showed the model a full template of empty strings. It echoed it: 83/580 items had a blank primary field, schema words became content ("provisional", "no"), `chief_complaint` was dropped, `allergy_status` blank in 14/37.
Isolated test, prompt with **no template** (natural-language field descriptions, `feasibility/results/run.json`, 6 unconstrained runs): **0 of 6 gave valid JSON that follows the intended structure** (5 not parseable: markdown fences and a different structure, e.g. `reported_by` as a separate list, `follow_up` as a string; 1 parseable but 20 schema violations). So removing the template alone is not enough for this model; the structure must come from somewhere. Options: (i) constrained decoding (below), (ii) a compact non-empty example – rejected for now because the model copies examples too.
Draft S1.1 prompt: `design/S1_1_DRAFT_PROMPT.txt` – 545 words / 3,551 bytes (S1.0 729 / 5,053; P02 1,184 / 9,688); no template, no blank strings; one natural-language line per section.

### B. Chief complaint
S1.0: key missing in 37/37 parsed outputs, because it was one blank string in a long template. S1.1: an explicit instruction (patient's main reason, patient's words, not the doctor's opening question) and the key is **required** in the output structure. Risk: the model may copy the whole sentence or the doctor's question; strict matching compares a normalised phrase, so verbatim sentences will match poorly (P02 chief-complaint F1 was only 0.14). Expect a modest gain at best.

### C. Speaker attribution – cause found
Rendered line (unchanged renderer): `[SEG0001] person_1 (PATIENT) 0.98-6.17s: text`. The S1.0 prompt said "Copy the role shown on the line", but the role is a bracketed upper-case token after an id; the model copied the id: `reported_by` was `person_1`…`person_4` in 278/417 fields, blank in 139, a role word in **0**. (P02 had no per-item speaker field to copy; its 0.42 came from a different mechanism.)
Test (synthetic): when the line label **is** the role word (`patient: …`), `reported_by` contained only role words in every run that produced items (every constrained run that produced items, in either rendering – including the looping ones; values `patient`, `doctor`, `nurse`; none of these runs used unconstrained decoding, where no per-item `reported_by` was produced reliably). Caveats: synthetic, 6–11 lines, one run each. In the 50 prompt-dev records no record has two speakers with the same role (0/50), so a role label is unambiguous there; 3 segments are `UNKNOWN`. Plan: label = lower-case role (`unknown` for UNKNOWN), speaker ids never shown. **No silent mapping**: the adapter never converts or guesses a `reported_by`; a value that is not a role present in that encounter is kept as given and flagged. Original speaker ids/roles are preserved in the per-encounter sidecar (section 3) and the raw output is always kept.

### D. JSON validity – structured decoding (OpenVINO GenAI 2026.4.1.0, GPU)
Feasible and works on this install: `StructuredOutputConfig(json_schema=…)`, `grammar=` (EBNF), regex and structural tags exist; it runs on the Intel GPU with the FP16 model without touching the project runtime (own pipeline in `feasibility/`, own cache `EXP_007/ov_cache`). Results, 3 synthetic cases × 2 renderings (all 12–18 runs in `feasibility/results/`):

| Mode | valid JSON | follows schema | notes |
|---|---|---|---|
| unconstrained, no template | 1/6 | 0/6 | fences / wrong structure |
| JSON-schema grammar | 2/6 | 2/6 | **4/6 hit the 1,500-token cap**: after a valid prefix the model emitted tabs/newlines forever (95 % whitespace) or looped on filler items |
| compact EBNF compiled from the same schema (no free whitespace, fixed key order, optional keys omitted) | 5/6 | 5/6 | whitespace loops gone; 1/6 repetition loop ("none" items until the cap); **3/6 collapsed to an empty extraction with `chief_complaint` = ","** (valid but useless) |

Honest reading: constrained decoding removes malformed syntax and enum violations (including speaker labels) **by construction**, but on this 0.6B model it introduced two new failure modes – degenerate repetition and forced-token collapse – and I have **no evidence yet that it preserves or improves extraction quality**. The synthetic transcripts are far shorter than real ones (37–66 lines, ~800 tokens in the proposed rendering), so these results do not predict real behaviour in either direction. Mitigations I would test next, on synthetic data only, before any dev-set run: bound array sizes in the grammar, start the answer with a forced `{`-prefix that fits the model's natural first tokens, and a smaller `max_new_tokens`. Whether the grammar changes the generation setup versus P02 is a **declared difference**; the existing runtime is untouched.

## 2. Proposed output structure (S1.1)
Same 17 sections as S1.0 minus two, 18 keys: `chief_complaint` (required, non-empty string), `symptoms`, `negative_findings`, `medical_history`, `surgical_history`, `family_history`, `social_history`, `medications`, `allergy_status` (enum), `allergies`, `vital_signs`, `physical_examination`, `review_of_systems`, `clinical_assessment`, `investigations`, `procedures`, `clinical_actions`, `follow_up`. Items carry only fields that hold a fact (optional fields may be omitted, never written as ""): primary field required and non-empty; `reported_by` ∈ {doctor, patient, nurse, caregiver, family_member, clinical_staff, unknown}; closed vocabularies as in S1.0. Dropped: `encounter_id` (set by the harness from the file name – nothing for the model to copy) and `current_conditions` (S1.0: 0 TP / 36 FP, P02 1 TP; its definition overlapped medical history). All 22 requested information categories remain covered; canonical `clinical_conditions` and `clinical_uncertainties` will be empty and scored as such (disclosed; P02 had 1 and 0 TP there). Files: `design/S1_1_output_schema.json`, `design/S1_1_output_grammar.ebnf` (compiled by `design/schema_to_ebnf.py`, 19 rules).

## 3. Transcript rendering investigation (not yet part of the prompt)
Measured on the 50 prompt-dev input transcripts with the model tokenizer: mean transcript tokens R0 (current: segment id, speaker id, role, times) **2,112**; R1 (`role: text`) **798** (−62 %, −1,314 tokens/encounter); R2 (`S12 role: text`) 932 (−56 %). S1.0 mean input was 3,316 tokens, so R1 cuts about 40 % of the whole prompt. At the measured prefill speed (~150 tok/s) that is roughly 9 s/encounter, a small latency gain; the larger expected benefit is a shorter context for a 0.6B model and no ids to copy.
Mapping for future evidence retrieval: the original transcript files are never modified. A **sidecar** per encounter lists, in order, `line_index → segment_id, speaker_id, role, start/end seconds` (example in `feasibility/results/render_token_study.json`). The model sees no ids, so nothing it writes can reference a line; retrieval must later locate facts by text matching against the original segments via the sidecar. This is a limitation: with R1 the model cannot cite a segment at all (S1.0 also did not).
Risks: loses the time context (no S1 field needs it); the model could confuse two speakers sharing a role (0/50 here; would need disambiguation, e.g. `family_member_2`, for other data); `unknown` speakers (3 segments); possible small effect from changed line format on extraction quality – untested on real transcripts. Recommendation: adopt R1 in the main S1.1 prompt **only as a separately reported arm** (see section 6), not silently.

## 4. Adapter design (new file `s1_1/s1_1_adapter.py` inside EXP_007; S1.0 adapter untouched)
Same principles as S1.0: deterministic, no invention, no correction, no evidence ids, no deduplication, raw + adapted kept, unmappable structures skipped and counted.
Changes: `encounter_id` taken from the file name; `chief_complaint` string copied to canonical `chief_complaint.value` (`reported_by` null, never assumed); no `current_conditions`; items keep only supplied fields (absent → null, never ""); `reported_by` copied as given, with an added check **against the sidecar** of that encounter: a role not present in that encounter, or any `person_N`, is recorded as `speaker_not_in_encounter` and left unchanged; no mapping from speaker id to role; unknown→`unknown`→null in canonical `reported_by` with the flag counted. Status/type mappings, allergy_status handling (none_stated → "Allergies/No known allergies" negative finding; unknown/not_asked → nothing), investigations+procedures merge: identical to S1.0 (documented in `MAPPING_NOTES`). Tests: synthetic unit tests (about 30), including no-invention, dose non-merging, no silent speaker mapping, absent-field handling and the sidecar flag. Frozen with SHA-256 before any run.

## 5. Expected changes versus S1.0 (hypotheses, not claims)
| Aspect | S1.0 measured | S1.1 expectation |
|---|---|---|
| Valid JSON | 37/50 | up to 50/50 with grammar (by construction), unless looping hits the cap |
| Blank/placeholder items | 83/580 | ~0 (non-empty primary fields required) |
| Chief complaint present | 0/37 | 50/50 (required); F1 uncertain |
| Speaker role words | 0/417 | high with R1 + grammar; real-length behaviour unknown |
| Input tokens (mean) | 3,316 | ~2,000 with R1 (−40 %) |
| Output tokens / latency | 617 / 107 s | similar or lower; **risk of loops costing up to the token cap** |
| Recall | 0.076 | unknown; a 0.6B model's recall limit is not addressed by formatting. Gains over 0.12 F1 are plausible but not assured; I do not expect 0.40 |
| Failure modes | template echo | repetition loops, forced-token collapse, empty extraction |

## 6. Experiment comparison plan (after approval only)
Phase A – synthetic only (no dev data): ≥10 more synthetic transcripts of realistic length; test the three mitigations; stop criteria: valid+schema-valid ≥ 90 %, no empty-collapse, no cap hits. Phase B – fixed, pre-declared arms on the same 50 prompt-dev records, same model/runtime/greedy settings, same evaluator, run in this order and **no tuning between arms**: B1 S1.1 prompt, original rendering, unconstrained (isolates prompt change); B2 S1.1 prompt, R1 rendering, unconstrained; B3 S1.1 prompt, R1, compact grammar (only if Phase A passes). Each scored on all 50 (failed outputs count as zero) against P02 (primary) and S1.0 (secondary); parsed-only subsets, if shown, labelled post-hoc diagnostics. Reported as S1.0: strict/fuzzy micro & macro, per-category (regressions disclosed), structural validity (S1.1-format vs canonical), clinical-error counts, speaker accuracy, tokens/latency/memory, plus loop/cap-hit counts. Proposed acceptance bar for retaining S1.1 (adjust if you wish): micro F1 ≥ P02 + 0.03 absolute, ≥ 48/50 valid JSON, speaker accuracy ≥ 0.42, no category collapse; the 0.40–0.45 target is not claimed unless measured. `max_new_tokens` proposed 2,048 for Phase B (S1.0 max 1,121; P02 max 2,674) to bound loops – this is a **declared change** from 6,144 and needs your approval; prompt/schema/grammar/adapter/config frozen and hashed before Phase B.

## 7. Decisions requested
1. Approve Phase A (synthetic-only mitigation tests) and then Phase B as above, or choose a subset of arms.
2. Drop `current_conditions` from the model output (recommended).
3. Rendering R1 as a separate arm (recommended) vs not at all.
4. Constrained decoding as an arm (recommended, gated by Phase A), accepting that it is a generation-setup change.
5. `max_new_tokens` 2,048 in Phase B.
6. The acceptance bar in section 6.
Not started: S2, S3, S4, fine-tuning, Batch 003, any change to the repository.

---
## Amendment 001 (post-Phase-A, 2026-11-13) – see `design/AMENDMENT_001_PROMPT_SELECTION.md`
Phase A outcome: original Gate P passed (with P1), **Gate C failed** (G1, G2, G3), so B3 is not authorised. The original prompt-selection rule (valid JSON first) selected P1, which Phase A showed to be poor on content. After Phase A the owner approved an amended rule (structural conformance AND minimum content performance), which selects P2 on the existing evidence; one missing Gate-P cell (P2 on the original rendering) is run before inference. Phase B is reduced to B1 (P2 + R0) and B2 (P2 + R1), unconstrained, 2,048-token cap. The amendment is post hoc and is not presented as a pass of the original gates. Sections 1-7 above are kept unchanged as the original design record.
