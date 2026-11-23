"""Writes final_dev100_report.md and comparison_with_EXP_001_dev100.md from the evaluator outputs (no inference, no label access)."""
import json, glob, pathlib
E3 = pathlib.Path(__file__).resolve().parents[1]
L = lambda p: json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
R = L(E3 / "evaluation/exp_003_dev_100/evaluation_report.json"); S5 = L(E3 / "evaluation/exp_003_dev_smoke_5/evaluation_report.json")
E1 = L(glob.glob(str(E3.parent / "EXP_001*/reports/evaluation_report.json"))[0])
F = L(E3 / "failure_report_dev100.json"); P = L(E3 / "evaluation/dev100_performance_details.json")
f = lambda x: "n/a" if x is None else f"{x:.3f}"
e = R["end_to_end"]; vo = R["valid_only"]; j = R["json_and_schema"]; m = e["strict"]["micro"]
w = []; a = w.append
a("# EXP_003 final 100-record development report - Qwen3-0.6B, OpenVINO FP16, Intel UHD 620 GPU\n")
a("Status: COMPLETED. All 100 development encounters (5 smoke-test + 95 remaining) were run; the 400 locked-test encounters were NOT touched. No prompt optimisation, fine-tuning, LoRA or RAG. Stopped for review.\n")
a("## Run integrity\n* Same model (Qwen3-0.6B rev c1899de2..., OpenVINO FP16 from EXP_002), same prompt (sha256 78c5ab95...f604, asserted), same decoding (greedy, enable_thinking=False, max_new_tokens 6144), same runner/parser/validator/evaluator, GPU only (no CPU fallback), fresh pipeline per encounter.")
a("* The 95 ids = development split minus the 5 smoke ids, disjoint from the 400 test ids (asserted). The smoke run `exp_003_dev_smoke_5` and its artifacts are unchanged (its 46 checksums still verify). The two runs were *copied* into `exp_003_dev_100` for evaluation.")
a("* File-access audit of the 95-encounter inference: 700 files opened, **0 label or blueprint files** (`logs/inference_remaining_95_file_access_audit.json`). Labels were opened only by the evaluator afterwards.")
a("* Verified after the run: EXP_001 checksums 55/55 OK; EXP_002 converted model 11/11 hashes OK; frozen dataset verified (1,001 files); git status shows only the pre-existing untracked items.\n")
a("## Outputs by status (recorded separately; `failure_report_dev100.json`)\n| Class | Count | Encounters |\n|---|---|---|")
a(f"| Valid JSON | {F['parsed_valid_json']} | |\n| Failed (all) | {F['failed_total']} | |\n| Malformed / invalid JSON | {len(F['malformed_invalid_json'])} | {', '.join(F['malformed_invalid_json'])} |")
a("| Truncated (token limit) | 0 | |\n| Empty | 0 | |\n| Not a JSON object | 0 | |\n| Inference errors | 0 | |\n| Degenerate repetition flagged | 0 | |")
a(f"| Schema-compliant (of 94 valid) | 0 | all 94 violate the schema: {F['schema_violation_totals']} |")
a("\nAll 100 generations ended with finish_reason=stop. The six malformed outputs are complete-looking JSON with a syntax error (missing comma delimiter), not token-limit cuts; they were not repaired and score as failures.\n")
a("## Aggregate metrics (strict matching; end-to-end counts failures as empty predictions)\n| Metric | End-to-end (100) | Valid-only (94) |\n|---|---|---|")
vm = vo["strict"]["micro"]
for lab, k in [("TP", "tp"), ("FP", "fp"), ("FN", "fn"), ("Micro precision", "precision"), ("Micro recall", "recall"), ("Micro F1", "f1")]:
    a(f"| {lab} | {m[k] if k in ('tp','fp','fn') else f(m[k])} | {vm[k] if k in ('tp','fp','fn') else f(vm[k])} |")
em, vmm = e['strict']['macro'], vo['strict']['macro']
a(f"| Macro P / R / F1 | {f(em['precision'])} / {f(em['recall'])} / {f(em['f1'])} | {f(vmm['precision'])} / {f(vmm['recall'])} / {f(vmm['f1'])} |")
a(f"| Fuzzy micro F1 (secondary) | {f(e['fuzzy']['micro']['f1'])} | {f(vo['fuzzy']['micro']['f1'])} |")
mh = e['medical_history_combined_strict']
a(f"| Medical history combined (strict) | P {f(mh['precision'])} R {f(mh['recall'])} F1 {f(mh['f1'])} | |")
a(f"\nSchema: required-field completeness {j['required_field_completeness_valid_json']*100:.1f}%, unexpected-field rate {j['unexpected_field_rate']*100:.2f}%, violations {j['violation_kinds']}. Macro F1 averages 18 categories; undefined precision stays n/a.\n")
a("## Category-level strict results (end-to-end)\n| Category | TP | FP | FN | Precision | Recall | F1 |\n|---|---|---|---|---|---|---|")
for c, v in e["strict"]["per_category"].items():
    a(f"| {c} | {v['tp']} | {v['fp']} | {v['fn']} | {f(v['precision'])} | {f(v['recall'])} | {f(v['f1'])} |")
a("\nOnly medications (0.299), allergies (0.282), surgical history (0.145), symptoms (0.095) and chief complaint (0.041) show meaningful signal; vital signs 0.039; clinical_uncertainties 1 TP and 0 FP. Negative findings, physical examination, review of systems, clinical conditions, assessment, procedures, actions and follow-up are 0.0 (assessment and follow-up: no predictions at all, so precision is n/a).\n")
v = e["vital_signs"]; s = e["speaker_attribution"]; g = e["evidence_grounding"]; u = e["unsupported_claims"]; n = e["negation_polarity"]
a("## Clinical quality detail\n"
  f"* **Vital signs:** {v['correct']} correct of {v['gold_vitals']} gold ({v['accuracy']*100:.2f}%); name found for {v['name_found']}.\n"
  f"* **Speaker attribution:** {s['correct']}/{s['evaluated']} = {s['accuracy']*100:.1f}% (patient {s['gold_role_patient_correct']}/{s['gold_role_patient']}, doctor {s['gold_role_doctor_correct']}/{s['gold_role_doctor']}, nurse 0/{s['gold_role_nurse']}, family member 0/{s['gold_role_family_member']}).\n"
  f"* **Evidence grounding** ({g['total']} predicted entities): strict {g['grounded_strict']} ({g['grounded_strict_rate']*100:.1f}%), lenient {g['grounded_lenient']}, partial {g['partially_supported']}, unsupported {g['unsupported']} ({g['unsupported_rate']*100:.1f}%).\n"
  f"* **Unsupported claims:** {u['unsupported_claims']} of {u['predicted_entities']} predictions ({u['unsupported_claim_rate_of_predictions']*100:.1f}%); of {u['false_positives']} false positives, {u['extra_but_transcript_supported']} are extras the transcript does support (mostly under-extraction, not hallucination).\n"
  f"* **Negation:** {n['gold_negatives']} gold negative findings, {n['gold_negatives']-n['missing']} reproduced; {n['polarity_flip_negative_reported_as_present']} polarity flip.\n"
  "* Attribute accuracy on matched entities is in `evaluation/exp_003_dev_100/evaluation_report.json` (e.g. medication dose 83.7%, status 82.6%, frequency 45.7%; symptom severity 7%, duration 0%).\n")
a("## Breakdowns (strict micro F1, end-to-end)\n| Complexity | Encounters | Valid | F1 |\n|---|---|---|---|")
for k, b in R["breakdown"]["complexity"].items():
    a(f"| {k} | {b['encounters']} | {b['valid_json']} | {f(b['strict_micro']['f1'])} |")
a("\n| Specialty | Encounters | Valid | F1 |\n|---|---|---|---|")
for k, b in R["breakdown"]["specialty"].items():
    a(f"| {k} | {b['encounters']} | {b['valid_json']} | {f(b['strict_micro']['f1'])} |")
a("\nSpecialty groups have 4-15 encounters; differences are within noise and should not be over-read.\n")
a("## Performance (100 encounters, `evaluation/dev100_performance_details.json`)\n| | Mean | Median | Min | Max | p95 |\n|---|---|---|---|---|---|")
for lab, k in [("Input tokens", "input_tokens"), ("Output tokens", "output_tokens"), ("Model load (warm cache), s", "load_compile_seconds"), ("First-token latency (prefill+1st), s", "first_token_latency_s(prefill+1st token)"),
               ("Prefill tok/s", "prefill_tokens_per_second"), ("Decode tok/s", "decode_tokens_per_second"), ("Generation time, s", "generation_wall_seconds"), ("Overall tok/s", "tokens_per_second_overall"), ("RSS after call, MB", "rss_mb_after")]:
    d = P[k]
    a(f"| {lab} | {d['mean']} | {d['median']} | {d['min']} | {d['max']} | {d['p95']} |")
a(f"\nTotal generation {P['total_generation_hours']} h for {P['total_output_tokens']:,} output tokens; peak process working set {P['peak_working_set_mb_max_over_run']} MB (maximum over the two processes). The 95-encounter run took 4.16 h wall (14,974 s).")
a("Extrapolation (estimate): the 400 locked-test encounters would take about 400 x 154 s = 17 h of generation.\n")
a("## GPU errors and warnings\nThe same two Intel graphics-compiler kernel-header messages as in EXP_002 (\"Input V38 intersects with V37\"; \"Explicit input 2 must not follow an implicit input 0\") were logged on pipeline creation (`logs/gpu_compiler/kernel.errors.txt`). No crashes, 0 inference errors, no out-of-memory, no OpenVINO runtime warnings; every encounter succeeded. The messages had no visible effect on outputs. (The `NativeCommandError` line at the top of the stdout log is PowerShell wrapping the compiler stderr text.)\n")
a("## Findings and limits\n* The baseline is weak: strict micro recall 2.7%, F1 0.049, 0% schema compliance. The model emits short JSON (mean 875 tokens) that omits most schema sections, regardless of backend.\n* Precision on what it does emit is moderate (25.7%), with medications at 76.7%.\n* 6% malformed JSON is a real reliability problem for a pipeline that needs parseable output.\n* Strict matching is conservative, but fuzzy micro F1 is only slightly higher (0.052), so the gap is genuine under-extraction rather than wording differences.\n* These are development-split results for one fixed prompt; they are not a locked-test estimate.\n")
a("## Not done (per instruction)\nNo locked-test (400) evaluation, prompt optimisation, fine-tuning, LoRA, RAG or quantisation. Awaiting your approval before anything further.\n")
(E3 / "final_dev100_report.md").write_text("\n".join(w) + "\n", encoding="utf-8")

# ---------------- comparison
c = []; b = c.append
sm = lambda r: r["end_to_end"]["strict"]["micro"]
b("# EXP_003 (100 development encounters) vs EXP_001 (5 encounters)\n")
b("**This is not a like-for-like comparison.** EXP_001 ran only the same five development encounters (00021, 00032, 00034, 00035, 00037) as the EXP_003 smoke test; it was never run on the other 95. The 100-record EXP_003 numbers therefore have no EXP_001 counterpart. Two valid comparisons exist: (A) the same 5 encounters, EXP_001 vs EXP_003 (identical entity metrics), and (B) EXP_003 on 5 vs 100 encounters (sample effect).\n")
b("## What differs between EXP_001 and EXP_003\n| Factor | EXP_001 | EXP_003 | Differs? |\n|---|---|---|---|\n| Model | Qwen3-0.6B rev c1899de2... | same | No |\n| Numerical format | BF16 weights loaded as FP32 | FP16-converted OpenVINO IR | **Yes** |\n| Runtime | HF Transformers | openvino_genai.LLMPipeline | **Yes** |\n| Hardware | i7-8665U CPU | Intel UHD 620 iGPU | **Yes** |\n| Prompt / decoding / schema / parser / evaluator | fixed (sha256 78c5ab95...), greedy, 6144 | identical (verified) | No |\n| Dataset / split | frozen v2 batch 001, development | same | No |\n| Encounters | 5 | 5 (smoke), then 100 | Sample size |\n")
b("Latency and any small output differences are the combined effect of format, runtime and hardware; none can be attributed to the GPU alone.\n")
b("## A. Same five encounters\n| Metric | EXP_001 | EXP_003 (5) |\n|---|---|---|")
for lab, fn in [("Micro P/R/F1", lambda r: f"{f(sm(r)['precision'])}/{f(sm(r)['recall'])}/{f(sm(r)['f1'])}"), ("TP/FP/FN", lambda r: f"{sm(r)['tp']}/{sm(r)['fp']}/{sm(r)['fn']}"), ("Macro F1", lambda r: f(r['end_to_end']['strict']['macro']['f1'])),
                ("Mean latency (s)", lambda r: f(r['performance']['latency_seconds']['mean'])), ("Mean tok/s", lambda r: f(r['performance']['tokens_per_second']['mean']))]:
    b(f"| {lab} | {fn(E1)} | {fn(S5)} |")
b("\nTwo of five outputs were byte-identical and three diverged slightly (details in `comparison_with_EXP_001.md`). Latency fell about 3.7x.\n")
b("## B. EXP_003, 5 encounters vs 100 encounters\n| Metric | EXP_003 (5) | EXP_003 (100) |\n|---|---|---|")
pc = lambda cat: (lambda r: f(r['end_to_end']['strict']['per_category'][cat]['f1']))
for lab, fn in [("Valid JSON", lambda r: f"{r['json_and_schema']['valid_json']}/{r['json_and_schema']['attempted']}"), ("Micro P/R/F1", lambda r: f"{f(sm(r)['precision'])}/{f(sm(r)['recall'])}/{f(sm(r)['f1'])}"), ("TP/FP/FN", lambda r: f"{sm(r)['tp']}/{sm(r)['fp']}/{sm(r)['fn']}"),
                ("Macro F1", lambda r: f(r['end_to_end']['strict']['macro']['f1'])), ("Medications F1", pc("medications")), ("Allergies F1", pc("allergies")), ("Symptoms F1", pc("symptoms")),
                ("Speaker attribution", lambda r: f(r['end_to_end']['speaker_attribution']['accuracy'])), ("Unsupported-evidence rate", lambda r: f(r['end_to_end']['evidence_grounding']['unsupported_rate'])),
                ("Mean latency (s)", lambda r: f(r['performance']['latency_seconds']['mean'])), ("Mean tok/s", lambda r: f(r['performance']['tokens_per_second']['mean']))]:
    b(f"| {lab} | {fn(S5)} | {fn(R)} |")
b("\nThe 5-record sample understated the model: with 100 encounters micro F1 rises 0.030 -> 0.049 and macro F1 0.019 -> 0.054, allergies and surgical history become non-zero, and 6 of 100 outputs are malformed JSON (none among the 5). Speed (about 154 s per encounter, 5.7 tok/s) is stable across the sample.\n")
b("## Conclusion\nOn the shared five encounters the OpenVINO FP16 GPU backend reproduces EXP_001's extraction quality and is about 3.7x faster. The 100-record development baseline for this model and prompt is micro F1 0.049 (valid-only 0.052), so the poor quality is a property of the model plus the fixed prompt, not of the backend. Because EXP_001 never covered the other 95 encounters, a 100-record CPU baseline does not exist; obtaining one would take roughly 100 x 634 s = 17.6 h of CPU generation and has not been run.\n")
(E3 / "comparison_with_EXP_001_dev100.md").write_text("\n".join(c) + "\n", encoding="utf-8")
print("ok")
