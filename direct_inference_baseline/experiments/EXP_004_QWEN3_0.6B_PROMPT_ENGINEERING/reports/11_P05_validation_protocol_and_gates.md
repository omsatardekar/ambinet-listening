# P05 validation protocol and gates (final; validation NOT started)

Preconditions (all must hold; the runner enforces them): this reports/13 spy report approved by you; your explicit authorisation recorded by `experiments/record_authorization.py` (it writes `P05_VALIDATION_AUTHORIZATION.json` bound to the freeze manifest SHA-256 `e383d3a352a6e431bc74c49c8c409d15a6e02831b05ee73e47aec472fd56fae0`); every frozen file unchanged; pre-flight passes. Without the authorisation file the runner, the evaluation and the audit sampler exit before opening any validation record (tested: `integration_checks/P05_final2_refusal_check/REFUSED.json`, 0 validation files opened).

## 1. What runs (only the 50-record validation subset)
1. **Stage 1** - frozen P02 prompt, pinned Qwen3-0.6B, OpenVINO FP16, GPU UHD 620, greedy, thinking off, 6144 tokens, a fresh pipeline per encounter, the existing inference loop. Expected 3-4 hours (P02 on prompt_dev took 3.3 h). This is the first P02 run on the validation subset: its extraction numbers will be reported as P02 validation results **at development stage, not final**.
2. **Stages 2-4** - frozen R_cons v4 -> existing builder -> final JSON, per record, immediately after stage 1 in the same command; extraction asserted unchanged.
3. **Evaluation** - `evaluate_p05.py validation ...` with the unchanged evaluator functions and the frozen gates.
4. **Audit packets** - `audit_sampler.py validation ...` (seed fixed below), then the human audit.
Command (after authorisation): `run_p05_validation.py validation P05_validation_50` then `evaluate_p05.py validation <stage1 parsed> outputs/P05_validation_50 outputs/P05_validation_50/evaluation evaluation/P05_validation_50/run_manifest.json`.
Dry-run equivalents on prompt_dev were run on the frozen files (`integration_checks/P05_final2_*`): refusal test, 5-record and 50-record post-processing with the strict spy, evaluation regression (identical to the development diagnostics).

## 2. Hard stops
* Any attempt to open a locked-test transcript or label, the sealed hash file, or an unauthorised validation record raises `PermissionError` at the moment of the attempt (`StrictAccessSpy`); the run stops. Any label read during inference/post-processing is recorded and stops the run at the end of the phase.
* Pre-flight failure (prompt hash, config, frozen files, evaluator, schema, model files, settings).
* A change to a frozen file during the run.
Invalid-JSON stage-1 outputs are not a stop: they are reported (the record has no extraction and no evidence).

## 3. Gates (provisional development gates fixed now, `experiments/P05_validation_gates.json`, hash `693b32e65b53198c...`)
| Gate | Criterion |
|---|---|
| Extraction integrity | final extraction counts identical to stage 1; builder integrity true for every record |
| Structure | 0 invalid segment ids; 0 evidence-field schema violations; 100% of evidence records exactly correct (text, speaker, role, times); 100% of `supports` entries reciprocal |
| Behaviour among cited facts | question-only citations 0; kinship conflicts 0; speaker-class conflicts 0; greeting-like <= 3%; polarity conflict <= 3%; segment0 <= 3% (flags are heuristics; every flagged case is read and listed) |
| Agreement on strictly matched facts with a gold citation | denominator >= 30 for a verdict (else INCONCLUSIVE); hit when cited >= 90%; hit with abstentions as misses >= Arm R's R_simple - 5 points |
| Coverage | cited share of extracted facts >= 60% |
Reported, not gated: stage-1 extraction metrics; per-group coverage and agreement; abstention reasons; share of cited facts whose fact strictly matches gold; evaluator lexical grounding (circular); speaker attribution; evidence records per encounter (mean, minimum, maximum; a low count is not a failure by itself, D3 of the P04 review); the human-audit results (concern flag if fewer than 75% of audited cited facts are judged supported; no automatic rejection).
Decision rule: all gated criteria hold -> "passes the provisional development gates"; otherwise the failed gates are reported. The rules, parameters and gates are not changed after the validation results are seen. Gates were set before the validation run, after development results existed (the development run passes all of them, `integration_checks/P05_final2_promptdev50_dryrun/evaluation/p05_evaluation.json`), so they are not independent of development.

## 4. Reporting after validation
Present the results for your review before any further experiment: the five separately reported quantities (see the architecture document), gate table, per-group tables, abstention reasons, flagged-case reading, residual-error comparison with prompt_dev, human-audit results and limitations. No tuning, no new version, no locked-test access.

## 5. Preserved outputs
Raw model output, parsed stage-1 JSON, final JSON, per-fact decisions with reason codes, builder reports, performance log, run settings, file-access audit, evaluation JSON, audit packets and keys.
