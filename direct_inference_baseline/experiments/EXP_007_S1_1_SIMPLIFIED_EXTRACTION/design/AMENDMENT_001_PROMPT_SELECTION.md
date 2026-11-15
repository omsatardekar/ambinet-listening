# AMENDMENT 001 – prompt-selection rule (POST-PHASE-A DESIGN AMENDMENT)

Date: 2026-11-13. Status: **post-Phase-A design amendment, made after the Phase A results were known, at the owner's explicit approval ("Option 2")**. It is not part of the original predefined gates and is not evidence that the original gates passed.

## 1. What the original design said and what happened
- Original selection rule (`design/PHASE_A_GATES.json`): choose the prompt with more valid-JSON outputs (then recall, then P1); original Gate P counted valid JSON and token-cap hits only.
- Phase A outcome as recorded (`manifests/PHASE_A_RESULT.json`, unchanged): the rule selected **P1** (10/10 valid JSON vs 9/10 for P2). Original **Gate P passed** only because it measured valid JSON and cap hits. Original **Gate C FAILED** for G1, G2 and G3, so **B3 (constrained decoding) is not authorised** and stays not run.
- Evidence that the rule selected a poor prompt (existing Phase A data, `phase_a/results/U_P1_R1.json`, `U_P2_R1.json`; 10 synthetic cases, unconstrained, R1):

| | P1 | P2 |
|---|---|---|
| valid JSON | 10/10 | 9/10 |
| strict schema-compliant records | 0/10 | 0/10 |
| mean top-level key coverage (of 18 required keys) | 0.80 | 1.00 |
| wrong-type errors (e.g. list expected, other given) | 104 | 0 |
| missing-field errors | 71 | 1 |
| medication recall | 0.00 | 0.56 |
| allergy status correct | 3/10 | 8/10 |
| symptom recall / negative-finding recall | 0.00 / 0.00 | 0.61 / 0.52 |
Neither prompt is strictly schema-compliant (both 0/10 under the strict validator, which flags enum drift and extra fields such as `reported_by` on investigations). P1 produced JSON in a structure of its own, P2 follows the intended structure.

## 2. The amended selection rule (applied to the existing Phase A evidence, no synthetic test changed)
A prompt is eligible for the unconstrained arms only if it satisfies BOTH:
- **Structural validity / schema conformance:** valid JSON ≥ 7/10 AND mean top-level key coverage ≥ 0.95 AND no wrong-type errors. (Strict 10/10 schema compliance is unattainable without constrained decoding – both candidates had 0/10 – so conformance is measured by key coverage and absence of wrong-type structure.)
- **Minimum content performance:** medication recall ≥ 0.50 AND allergy status correct ≥ 6/10.
Among eligible prompts choose the higher (medication recall + symptom recall); if none is eligible no unconstrained arm is authorised.
Application: P1 fails (coverage 0.80; 104 wrong-type errors; medication recall 0.00; allergy 3/10). **P2 passes** (9/10 valid; coverage 1.00; 0 wrong-type errors; medication recall 0.556; allergy 8/10). **P2 is selected.**
**Disclosure:** these thresholds were chosen after seeing the results. They separate the two candidates on evidence already in hand; they are not an independent test, and the 10 synthetic cases are short and template-based.

## 3. Gate P for the amended prompt (original criteria, unchanged)
Original Gate P also required valid JSON ≥ 7/10 on the original rendering R0 for the chosen prompt. Phase A never ran P2 on R0 (only P1 on R0). To apply the unchanged Gate P to P2 the missing cell `U_P2_R0` (same 10 existing synthetic cases, same driver code, same settings) is run once, before any Phase B inference. This adds one missing cell; no existing result is re-run or replaced. Gate P for P2 = valid JSON R1 ≥ 7/10 (9, existing) AND valid JSON R0 ≥ 7/10 (new cell) AND token-cap hits ≤ 1 in each. If this cell fails Gate P, B1 is not run and the result is reported (B2 depends only on the R1 evidence).

## 4. What is authorised after the amendment
B1 = P2 + original rendering (R0) + unconstrained; B2 = P2 + role-label rendering (R1) + unconstrained; same 50 prompt-development ids, `max_new_tokens` 2048, same model/runtime/greedy settings. **B3 is NOT authorised** (Gate C failed; constrained decoding not approved). No prompt tuning between B1 and B2. Prompts, configs, adapter, sidecar, runner and evaluator are frozen and hashed before any Phase B inference. Further tuning on these 50 records is not independent validation; P02 is the primary comparison, S1.0 secondary, Phase A P2 results shown for context only (synthetic, not comparable with real data).

## 5. Unchanged / preserved
Original gates, Phase A result, Phase A report and all Phase A outputs are untouched. The amended decision is recorded separately in `manifests/PHASE_A_AMENDED_DECISION.json`.
