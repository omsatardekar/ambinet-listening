# Invalid JSON, truncation and recovery analysis (Qwen3-1.7B, P00 and P01, 30 development records)

**DEVELOPMENT-ONLY. No inference was run for this analysis.** It uses only saved raw outputs, the tokenizer files of the pinned snapshot (no model loaded), the frozen evaluator and the installed library's public API listing. No configuration, token limit, device, precision or frozen artifact was changed. Data: `evaluations/p00_p01_audit/{TRUNCATION_ANALYSIS.json, TOKEN_BREAKDOWN.json, TRUNCATION_TOKEN_SUMMARY.json, CLOSURE_DIAGNOSTIC_SCORES.json}`; script `scripts/analyse_truncation_tokens.py`.

## 1. What failed
12 of 60 outputs (30 records x 2 prompts) are not valid JSON: P00 7/30, P01 5/30. `00168` and `00204` fail under both prompts.

| Run | ID | finish | tokens | cut location | JSON state at cut | evidence tokens before cut | clinical sections complete | missing after structural closure | chars discarded |
|---|---|---|---:|---|---|---:|---|---|---:|
| P00 | 00040 | length | 4096 | clinical_evidence | inside a string, 3 containers open | 1708 | yes | clinical_evidence, quality_checks | 4079 |
| P00 | 00060 | length | 4096 | clinical_evidence | inside a string, 3 containers open | 1128 | yes | clinical_evidence, quality_checks | 2659 |
| P00 | 00127 | length | 4096 | clinical_evidence | inside a string, 3 containers open | 1770 | yes | clinical_evidence, quality_checks | 4553 |
| P00 | 00155 | length | 4096 | clinical_evidence | inside a string, 3 containers open | 2111 | **no** (model omitted `follow_up`) | follow_up, clinical_evidence, quality_checks | 5338 |
| P00 | 00168 | length | 4096 | clinical_evidence | inside a string, 3 containers open | 2072 | yes | quality_checks | 35 |
| P00 | 00204 | length | 4096 | quality_checks | between values, 2 containers open | 1623 | yes | none | 40 |
| P00 | 00210 | length | 4096 | clinical_evidence | inside a string, 3 containers open | 1225 | yes | clinical_evidence, quality_checks | 2830 |
| P01 | 00037 | length | 4096 | clinical_evidence | inside a string, 3 containers open | 1567 | yes | clinical_evidence, quality_checks | 3675 |
| P01 | 00092 | length | 4096 | clinical_evidence | inside a string, 3 containers open | 1709 | yes | clinical_evidence, quality_checks | 4133 |
| P01 | 00168 | length | 4096 | clinical_evidence | inside a string, 3 containers open | 1995 | yes | quality_checks | 172 |
| P01 | 00204 | length | 4096 | clinical_evidence | inside a string, 3 containers open | 1293 | yes | clinical_evidence, quality_checks | 3090 |
| P01 | 00206 | **stop** | 3620 | quality_checks | between values, 2 containers open | 1853 | yes | quality_checks | 248 |

Across the full 50-record P00 baseline the same pattern holds: 14 of its 15 truncations are in `clinical_evidence`, the 15th (`00204`) in `quality_checks` (this includes the other 8 failures outside the 30-record subset; those outputs were checked only for the cut location, not audited).

## 2. Answers to the specific questions
1. **Cause of the parse failures.** 11 of 12 are the generation limit (`finish_reason=length`, 4,096 tokens; error "Unterminated string" 10 times and "Expecting ',' delimiter" once). One (P01 `00206`) is genuine malformed JSON: the model stopped normally (`finish=stop`, 3,620 tokens) after writing the evidence record with `}` but without the closing `]` of the evidence array, and without the final `}` of the object. Inserting exactly those two closers makes the whole object valid with no content change (tested in memory on a copy; the saved outputs were not modified).
2. **Token cap.** Yes for 11 of 12. The cut is almost always inside the `transcript_text` string of an evidence record.
3. **Malformed quotes, commas, brackets.** No stray quotes or commas were found in the 12 outputs; the failures are an unfinished string (10), one missing closing brace after the last value (P00 `00204`: the output ends one `}` short of complete, at token 4,096) and the two omitted closers in `00206`. Other malformations seen in evidence that did parse: duplicate evidence ids (`EV_001` repeated in `00168` under both prompts), timestamps that are not `MM:SS` (`"146:57"`, `"00:00"`), empty `speaker_id`/`speaker_role`.
4. **Repeated fields / unexpected structures.** No degenerate repetition loop. A third to a half of lines in truncated outputs are repeated lines (share 0.43 to 0.63), but that is because the evidence field holds a copy of the transcript, whose lines begin with `person_1 (PATIENT) 14.98-20.76s:` and because the pretty-printed layout repeats key lines. The one compact output (`00206`) has 0.0.
5. **Too many tokens on evidence?** Yes. In the truncated outputs the evidence text emitted before the cut was 1,128 to 2,111 tokens (28% to 52% of the 4,096). In the outputs that finished, the evidence section is a one-record blob averaging 487 tokens (P00) and 369 tokens (P01), 15 to 20% of the output.
6. **Categories with long output.** Mean tokens per section in completed P01 outputs: medical_history 281, vital_signs 239, symptoms 221, medications 199, negative_findings 116, physical_examination 120, encounter_metadata 115 (single-speaker lists are short, four-speaker lists are not), clinical_actions 121, evidence 369, quality_checks 56. No clinical section is unreasonably long; the cost is spread, and whitespace is the largest single item (section 3).
7. **Can generation preserve partial output safely?** Not today. The runner keeps the raw text only when a generation call returns, so a process killed mid-record (as at the 30-record stop) loses the partial text. A streamer callback that appends tokens to a file would fix this without touching any generation setting (requires a code change, see section 5).
8. **Can the system detect a cap hit before treating the output as complete?** It already does: `finish_reason == "length"` marks the record failed/truncated and no output is treated as complete (P00 and P01 manifests). Gap: `00206` shows `finish=stop` does not imply valid JSON, so validity must always be tested after parsing, which the runner does.
9. **Safe continuation or repair.** See section 5. Structural repair works on all 12; continuation was not tested (needs inference).
10. **Validation of a repaired result against the canonical schema.** Done in memory for all 12: every closed object parses; the schema validator then lists missing top-level keys (see table); 11 of 12 contain every clinical section.

## 3. Token economy (measured on the saved outputs, tokenizer of the pinned snapshot)
| Item | P00 | P01 |
|---|---:|---:|
| Prompt template tokens (without transcript) | 1,667 | 2,093 |
| Transcript tokens, mean / max over the 30 records | 2,088 / 2,960 | same |
| Mean input tokens per record (reported) | 3,767 | 4,193 |
| Mean output tokens, completed records | 2,419 | 2,450 |
| Same content re-serialised compactly (no whitespace) | 1,728 (-29%) | 1,699 (-31%) |
| Compact and without the `clinical_evidence` section | 1,269 (-48%) | 1,362 (-44%) |
| Compact, without evidence section, `confidence`, `role_confidence` and `evidence_ids` | 1,020 (-58%) | 1,102 (-55%) |
| Largest completed output as emitted / compact without evidence | 4,063 / 2,057 | 3,618 / 2,033 |

- Cost per token: decode 2.76 to 2.84 tokens/s means 0.36 s per output token; prefill 38 tokens/s. A 4,200-token input costs about 110 s, a 2,450-token output about 890 s: **output tokens are roughly 90% of the runtime**.
- Indentation and line breaks alone are 29% to 31% of the output tokens of the completed records. P01's "compact layout" rule did not change this (30 of 30 outputs were still indented); the model copies the layout of the template it is shown.
- Counterfactual arithmetic (not a prediction of P02): the non-evidence content of every one of the 12 failed outputs was 1,766 to 2,966 tokens as emitted, so with the evidence copy removed all 12 would have fit in 4,096 tokens. A P02 that extracts more items will lengthen the clinical sections: a 60% increase would push the longest (2,966) above the cap if layout stays as indented, but not if the output is compact (2,966 x 0.7 x 1.6 = 3,320).

## 4. Diagnostic: what structural closure would have recovered (analysis only)
Method (`close_structurally`, no content added): cut at the last complete element boundary, close the open arrays and objects, parse, run the canonical schema validator. The result is flagged incomplete; missing sections stay missing.

| | as scored (failed = zero) | diagnostic with structural closure |
|---|---|---|
| P00 micro F1 (TP / FP / FN) | 0.161 (128 / 369 / 965) | 0.212 (189 / 501 / 904) |
| P01 micro F1 (TP / FP / FN) | 0.201 (170 / 431 / 923) | 0.221 (202 / 537 / 891) |

- With the same recovery applied to both prompts the P01 advantage shrinks from 0.040 to 0.008. Most of the headline gain of P01 is who completed the record, not extraction.
- These closed outputs are **incomplete** (evidence tail and, for some, `quality_checks` missing; P00 `00155` also lacks `follow_up` because the model never wrote it). They are a diagnostic upper bound on what truncation cost, not a result. The headline metric keeps failed records at zero, per the agreed convention.

## 5. Options for avoiding lost records
Risk of "losing or fabricating clinical facts" is stated for every option. Runtime effects are estimates from the measured 0.36 s/output token and 38 tokens/s prefill unless marked "measure".

| # | Option | Benefit | Limitation | Runtime / memory | Risk of losing or fabricating facts |
|---|---|---|---|---|---|
| A | **Compact template** (P02 draft shows a one-line-per-section template instead of an indented one) | Same content in 29-31% fewer tokens; also lowers truncation risk | The model may still indent (P01's rule failed); effect must be measured, not assumed | About -250 to -270 s per record if obeyed (about -23% of record time) | None: no fact is changed |
| B | **Constrain evidence** in the prompt (one record per cited line, copy one line, at most 2 ids per fact) (P02-A) | Removes the transcript-copy blob if obeyed | The model ignored an equivalent instruction idea in 0.6B P03 (evidence unchanged in kind); must be measured | Evidence 15-50% of the output today | None if obeyed; if ignored, unchanged |
| C | **Evidence-free model output + deterministic evidence builder** (P02-E) | Removes 44-48% of tokens (with A) and the whole truncation mode; evidence quality no longer depends on the model | Output contract differs from the model's own; the builder exists only for 0.6B (EXP_004 P05); evidence quality of 1.7B pipeline unmeasured | About -400 s per record against today's indented output (measure) | Evidence is retrieved from the transcript, never invented, but a wrong line can be attached to a fact: needs a gate on grounding |
| D | **Schema constants added by code** (all `confidence`, allergy `severity`, fixed enums, speakers from the transcript) | A further 10 points of tokens fewer; removes 339 of the 395 missing-field violations in P01 and all `primary_speakers` omissions (8 P01 records) | Output the model produces is a subset; final artifact must be validated | Reduces tokens further | None: constants are defined by the schema (`confidence` MUST be null) |
| E | **Safe partial-output persistence** (stream tokens to disk) | A killed or crashed record keeps its text; enables post-mortem and repair | Needs a small runner change; does not alter generation | Negligible | None |
| F | **Deterministic repair, tier 1: append missing closers** when the output ends cleanly after a complete value | Recovers P00 `00204` (one brace short) with zero loss | Only 1 of 12 failures qualifies | None | None |
| G | **Deterministic repair, tier 2: insert a missing closer before the next key** when the parse error shows a skipped closer | Recovers P01 `00206` (two closers) with zero loss | Needs rules; applies only when exactly one structural completion makes it valid | None | None; refused if more than one completion is valid |
| H | **Tier 3: cut at the last complete element and close** | Recovers all 12 structurally; loses only the tail of the last section | Result is incomplete; tail content is lost (evidence text) | None | Loses, never invents; must be labelled incomplete and listed as such |
| I | **Controlled continuation** (re-feed prompt plus the valid prefix, generate the rest) | Could finish a record whose clinical sections are done but evidence is not | Needs inference to test; re-prefill 110-160 s per record plus further decode; changes the generation procedure (needs approval); risk of repeating or contradicting the prefix | +120 to +900 s per continued record | A continuation could add unsupported content; its text must be validated and flagged |
| J | **Structured decoding** (`StructuredOutputConfig` with a JSON schema or grammar is present in the installed OpenVINO GenAI 2026.4.1) | Guarantees valid syntax and allowed enum values and required keys; would remove most enum/missing-field violations | **Unverified** on this GPU: token/s overhead unknown; does not prevent hitting the cap; forcing all fields may lengthen outputs; may change extraction quality. Not tested (no inference allowed) | Unknown, measure on one record | Could force placeholder values where the model has nothing to say |
| K | **Raise `max_new_tokens`** | Recovers records at the price of time | Not allowed now; changes a frozen setting; wastes tokens on the evidence blob | Up to +25 min per truncated record | None, but costs hours |
| L | **Split extraction from evidence into two calls** | Cleaner separation | Doubles prefill and adds a second generation | +100 s prefill + evidence decode | Evidence call can mis-cite |

Not recommended: completing a cut string, filling missing sections with defaults, or marking a repaired output `completed`.

## 6. Mandatory safety rules for any recovery code
1. The raw output is saved untouched first; repaired output is a new artifact with its own name.
2. A repaired record gets status `incomplete_recovered` (never `completed`), the list of missing top-level keys, the repair tier used, and the exact characters removed or inserted (the repair log).
3. Only structural characters (`]`, `}`) may be inserted, and only when exactly one insertion (or one pair) makes the JSON valid; otherwise the record stays failed.
4. No default values for missing clinical content, no re-generation without an approved plan.
5. The canonical schema validator runs after repair; failures stay failures.
6. Metrics: the headline continues to count failed records as zero predictions. A recovered output is reported in a separate line ("with deterministic recovery"), never merged into the headline.
7. Gate for any continuation/constrained-decoding experiment: a smoke test on one record whose result is not an experiment result, per the earlier smoke-test convention, and explicit approval first.

## 7. Recommended order (for approval; nothing implemented)
1. **A + B + D** are prompt/template choices already in the P02 draft or cheap code; they remove 30-58% of the output tokens and make the evidence blob unnecessary.
2. **E** (partial persistence) and **F, G** (zero-loss repair) are low-risk code additions to the runner, with no change to generation.
3. **C** (evidence-free output plus builder) if the pilot shows evidence collapse persists under P02-A.
4. **H** as the fallback for any record that still fails, labelled incomplete.
5. **I, J, K** only after measurement and explicit approval.
