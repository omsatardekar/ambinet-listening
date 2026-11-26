# EXP_007 S1.1 – Phase A report (synthetic-only feasibility gates)

**Outcome: Gate P passed, Gate C failed for all three grammar variants (G1, G2, G3). Phase B was NOT started.** Reason: the instruction was "if a gate fails, stop and report"; B3 is not authorised by the predefined rule, and I did not run B1/B2 either (see section 5). Nothing was changed after the gates were fixed.

Scope: 10 template-generated synthetic consultations (seed 20261113, 34–38 lines each, shorter turns than real data; slightly below the planned 36–52 lines – disclosed, gates unchanged). No project transcript, label, validation (50), locked-test (400), sealed hash file or Batch 002 record was used. Model/runtime as in EXP_006 (Qwen3-0.6B, OpenVINO FP16, GPU, greedy, thinking off), `max_new_tokens` 2048. Run time 61.9 min, one uninterrupted process (no resume was needed; one result file per variant, none duplicated or partial). Frozen inputs and hashes: `manifests/PHASE_A_FREEZE.json`; gates: `design/PHASE_A_GATES.json`; result: `manifests/PHASE_A_RESULT.json`; per-case outputs and scores: `phase_a/results/*.json`.
Note: Phase A scoring uses the project's parser (strips ``` fences), so the earlier feasibility numbers (plain `json.loads`) are not comparable with these.

## 1. Prompt selection (predefined rule: more valid JSON → higher recall → P1)
| Variant (unconstrained, R1) | valid JSON | schema-compliant | medication recall | allergy status correct | empty collapse |
|---|---|---|---|---|---|
| P1 (no skeleton) | 10/10 | 0/10 | 0.00 | 3/10 | 1 |
| P2 (with angle-bracket skeleton) | 9/10 | 0/10 | 0.56 | 8/10 | 0 |
**Rule selected P1** (10 > 9 valid JSON). **This exposes a weakness in the rule I wrote:** it counted only valid JSON, and P1's JSON follows its own invented structure (0/10 schema-compliant, no medications found), whereas P2 is far better on content. I applied the rule as written; I recommend amending it (see section 6) rather than silently switching to P2.

## 2. Gate P (prompt, unconstrained; applies to B1/B2) – PASSED
valid JSON R1 10/10 (≥7) ✔; valid JSON R0 10/10 (≥7) ✔; token-cap hits 0 and 0 (≤1) ✔. The gate counted valid JSON and cap hits only. On content, P1/R0 is poor: 9/10 empty collapse, 9/10 with `reported_by` outside the role vocabulary, 0.0 medication and allergy-status recall – the gate does not detect this.

## 3. Gate C (constrained; applies to B3) – FAILED (G1, G2, G3)
| Criterion | G1 compact grammar | G2 + cap 20 | G3 + cap 20 + forced prefix |
|---|---|---|---|
| valid JSON 10/10 | ✔ 10 | ✔ 10 | ✔ 10 |
| schema-compliant ≥9 | ✔ 10 | ✔ 10 | ✔ 10 |
| no token-cap hit / truncation | ✔ 0 | ✔ 0 | ✔ 0 |
| no empty collapse | ✔ 0 | ✔ 0 | **✘ 1** |
| no repetition loops | ✔ 0 | ✔ 0 | ✔ 0 |
| chief complaint keyword ≥7/10 | ✔ 10 | ✔ 10 | ✔ 10 |
| medication recall ≥0.60 | ✔ 0.63 | ✔ 0.63 | **✘ 0.43** |
| allergy status correct ≥7/10 | ✔ 9 | ✔ 9 | ✔ 9 |
| roles correct ≥0.90 of matched items | **✘ 0.75** | **✘ 0.75** | **✘ 0.71** |
| no role outside vocabulary | ✔ 0 | ✔ 0 | ✔ 0 |
| symptoms recall >0.20 | ✔ 1.00 | ✔ 1.00 | ✔ 0.65 |
| negative findings recall >0.20 | **✘ 0.00** | **✘ 0.00** | ✔ 0.30 |
| vital signs recall >0.20 | ✔ 0.70 | ✔ 0.70 | ✔ 0.50 |
| investigations recall >0.20 | **✘ 0.00** | **✘ 0.00** | ✔ 0.30 |
| follow-up recall >0.20 | **✘ 0.00** | **✘ 0.00** | ✔ 0.40 |
| medications recall (category) | ✔ | ✔ | ✔ |
G2 outputs are identical to G1 (the cap never bound), so it fails identically. The variants were evaluated in the predefined order; none passed, so **no B3 variant exists**. No further variant was tried (would need approval).

## 4. What the constrained outputs show (G1; synthetic, 10 cases; descriptive)
- **Solved:** syntax (10/10 valid), enum/role vocabulary (no `person_N`, no blank placeholders), chief complaint present (10/10), no loops or whitespace runaway, ~348 output tokens (vs 617 for S1.0) and ~48 s per case.
- **Role attribution is wrong in a systematic way:** vital signs read by the **nurse** were attributed to `doctor` in 9 of 21 matched items although the line label said `nurse`; one current medication was attributed to the doctor. The model often defaults to `doctor` for measurements.
- **Large omissions (zero in all 10 cases):** negative findings, investigations, follow-up, clinical actions, physical examination; newly prescribed medicines found in only 1 of 10 cases. Symptoms/history/family/medications/vitals are extracted.
- **Content errors:** doses copied across medicines or into the name (e.g. a stopped medicine given the dose of another medicine; "sertraline fifty milligrams" as a name), invented route "oral", blood-pressure value truncated to "143", durations like "none". These are the very failure modes the prompt rules forbid.
- Forcing the answer prefix (G3) restored negatives/investigations/follow-up recall (0.30–0.40) but lowered medication recall (0.43) and produced 1 empty collapse – a trade-off, not a fix.
Caveat: 10 short synthetic cases, single greedy run; indicative only. They do not predict behaviour on the real transcripts, and the synthetic expected-fact scorer is a simple substring match.

## 5. Authorisation decision and why Phase B did not start
Predefined rule: B1/B2 proceed iff Gate P passes; B3 iff Gate P and Gate C pass. Strictly, B1/B2 are therefore authorised and B3 is not. Your latest instruction says to stop and report if Phase A fails a gate, so I stopped. I also note that running B1/B2 with the rule-selected P1 would very likely be uninformative on this evidence (P1 unconstrained: 0/10 schema-compliant, 0.0 medication recall; R0: 9/10 empty collapse), at roughly 1 GPU-hour per arm. **I need your decision before any Phase B inference.**

## 6. Options for your decision (none started)
1. **Run B1 and B2 as authorised by the predefined rule** (P1 prompt), accepting that they will probably show the same structural/content failures; B3 not run. Cost ~2 GPU-hours.
2. **Amend the prompt-selection rule** (e.g. require schema compliance / medication recall, not valid JSON alone), which would select P2, then re-run only the P1-vs-P2 comparison is already done – no new inference needed for selection – and run B1/B2 with P2. This is a design change that needs your approval.
3. **Stop S1.1 here** and treat the finding as the result: formatting fixes (role labels, constrained decoding, no template) fix syntax and role vocabulary but not extraction recall or attribution for a 0.6B model; consider a different approach in a new, separately approved experiment (I do not start one).
4. Approve **one more constrained variant** (needs new gates; e.g. G3 with a different prefix, or a compact two-step prompt), clearly labelled as a post-gate design change.

## Integrity
Gates, prompts, grammars, generator and driver were hashed before inference (`PHASE_A_FREEZE.json`) and not edited afterwards. Protected data and experiments (P00–P05, EXP_001–006, schemas, datasets, validation, locked test, sealed hashes, Batch 002) were not opened or modified; `git status` shows no tracked-file change. No Phase B inference, freeze or evaluation ran. Dry-run evaluator test used copies of S1.0 outputs in the scratchpad (outside the repository). Prepared but not frozen/used: `s1_1/` (adapter + 36 passing tests, sidecar, client, runner, evaluator), `design/make_arm_configs.py`, `config/S1_1_ACCEPTANCE_AND_DEFINITIONS.json`.
