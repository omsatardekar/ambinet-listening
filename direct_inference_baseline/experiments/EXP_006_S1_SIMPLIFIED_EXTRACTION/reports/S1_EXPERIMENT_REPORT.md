# EXP_006 – S1 Simplified Stage-1 Extraction: experiment report

**Scope: development-set results on the 50 prompt-development records only.** Labels are generator-derived (not human-verified). Nothing here is clinical validation or evidence of generalisation.

## 1. Objective and hypothesis
Tested (not assumed): removing evidence ids, segment refs, excerpts, timestamps, quality checks, confidence, grounding/citation judgements, extra normalisation and explanatory text from the Stage-1 task, with a compact output (S1), improves strict precision/recall/F1 and reduces output tokens, malformed JSON and latency relative to P02 (strict micro F1 0.1207 on the same 50 records).

**Verdict on the hypothesis: partly supported.** Supported: output tokens (−54 %), latency (−55 %), precision (0.227 → 0.279), fewer fabricated dates/contradictions. **Not supported:** F1 (0.1207 → 0.1192, no change), recall (0.0823 → 0.0758), malformed JSON (0 → 13 of 50 records). The 0.40–0.45 F1 target was **not** reached (measured 0.119).

## 2. Prompt design differences (details in `prompts/PROMPT_DESIGN.md`)
P02: 17 entity sections with 5–17 fields each, evidence ids + `clinical_evidence` list, `quality_checks`, `confidence`, plain + normalised fields; 1,184 words / 9,688 bytes.
S1: 20 compact keys, 2–6 fields per item, no evidence/quality/confidence/normalisation, explicit `allergy_status`, closed vocabularies for vital names and social-history categories, rules for medications, allergies, negation, speaker role, temporality; 729 words / 5,053 bytes. Transcript renderer unchanged (ids and times still shown).

## 3. Exact record ids (50, identical to the P02 prompt-development ids)
00035 00037 00040 00042 00060 00069 00077 00092 00120 00127 00141 00152 00155 00157 00162 00165 00168 00182 00187 00189 00202 00204 00206 00210 00215 00221 00238 00248 00264 00266 00288 00289 00291 00350 00393 00397 00402 00403 00409 00416 00426 00429 00454 00455 00460 00462 00469 00471 00475 00497

## 4. Model and runtime
Qwen/Qwen3-0.6B revision `c1899de289a04d12100db370d81485cdf75e47ca`; OpenVINO 2026.4.1 / GenAI 2026.4.1.0; FP16 IR from EXP_002; device GPU (Intel UHD 620); greedy, thinking off, `max_new_tokens` 6144; fresh pipeline per encounter. Pre-flight check "model_runtime_description_identical_to_P02_run" passed. Only difference: compiled-model cache directory inside EXP_006 (`manifests/S1_RUN_SETTINGS.json` still contains a copied string naming the EXP_004 cache; the cache actually used was `EXP_006/ov_cache`, and EXP_004's cache was not modified – newest file 07:01, before the 12:25 start).

## 5. Hashes (SHA-256, frozen before inference, unchanged afterwards – the runner re-checked them)
- prompt `29bacf3d631046c929d11f2774593e66d49a49134175cf2fb371273ef7f4c379`
- config `627d36e027d20ce0593a0f430ae9ffc4e8bfb8901764433acd9757b5106ec214`
- adapter `6b405abc88d485ed4bae09131033d62d51f42efd61cd7d52896450f16341a5da`
- runner `3f5e52799f009c1edfff0ea20ae89b338dfdbc63ad33a6de9401638fbc1b50fc`; evaluator script `dc272da2c94279f40424f575bc200e0459adc5596ef63d55806923e806388791`; adapter tests `35d6ebb0d242e9146699cce1d08e6d95da00370c1c0aca2ccdf10e19dbf47523`
- P05 freeze manifest `e383d3a352a6e431bc74c49c8c409d15a6e02831b05ee73e47aec472fd56fae0` (verified unchanged).

## 6. Overall results (canonical strict evaluator, unchanged; S1 scored after the S1 adapter)
| | TP | FP | FN | Precision | Recall | Micro F1 | Macro F1 |
|---|---|---|---|---|---|---|---|
| P02 (stored outputs, reproduced exactly) | 153 | 522 | 1707 | 0.227 | 0.082 | 0.1207 | 0.1222 |
| S1 | 141 | 364 | 1719 | 0.279 | 0.076 | 0.1192 | 0.1160 |
Fuzzy micro F1: S1 0.129, P02 0.135.

**Important qualifier.** 13 of 50 S1 outputs were not valid JSON and contribute zero predictions (all their gold counted as FN). On the 37 records where S1 parsed, S1 micro F1 is 0.154 versus P02 0.122 on the same 37 (`evaluation/S1_PARSED_SUBSET_COMPARISON.json`). This subset was chosen after seeing S1 outputs and by S1's own success, so it is a descriptive diagnostic, **not** a headline result.

## 7. Category results (strict F1; S1 vs P02)
Improvements: negative findings 0.038 vs 0.000; social history 0.048 vs 0.000; allergies 0.341 vs 0.300; vital signs 0.296 vs 0.272; investigations/procedures 0.219 vs 0.155; follow-up 0.270 vs 0.058.
**Regressions (disclosed):** chief complaint 0.000 vs 0.140 (S1 omitted the `chief_complaint` key in all 37 parsed outputs); symptoms 0.011 vs 0.108; surgical history 0.045 vs 0.130; family history 0.140 vs 0.178; past medical history 0.062 vs 0.069; medications 0.453 vs 0.497; review of systems 0.041 vs 0.107; physical examination 0.000 vs 0.014; clinical conditions 0.000 vs 0.024; clinical assessment 0.124 vs 0.140; clinical actions 0.000 vs 0.007. Clinical uncertainties 0.000 in both. Full TP/FP/FN: `evaluation/S1_CATEGORY_METRICS.json`. Many categories rest on a handful of matches; differences of 1–3 entities are not meaningful.

## 8. Clinical-error summary (details in `S1_ERROR_ANALYSIS.md`)
Fabricated date/timestamp values 7 vs 66; same-item positive+negative contradictions 4 vs 16; evaluator "unsupported claims" 60 vs 85; medication names not in transcript 0 vs 2; medications listed as allergy 2 vs 1; allergy-status errors 28 vs 28; polarity errors 7 vs 4; **speaker attribution accuracy 0.088 (9/102) vs 0.421 (53/126)** – a severe regression.

## 9. Structural validity
S1 raw: valid JSON 37/50, parse failures 13 (all "Expecting ',' delimiter"; finish_reason `stop`, none truncated), 0 empty outputs. **0 of 37 parsed outputs are fully S1-format valid** (492 enum violations, 64 missing keys, 21 missing fields, 14 wrong types). Adapter: 14 problems in 12 records (`clinical_assessment`/`follow_up` returned as non-lists; sections skipped). Adapted canonical: 489 enum violations, 0 other schema violations, 0 fully compliant records. P02: valid JSON 50/50, 0 fully compliant canonical records (814 missing fields, 208 enum, 33 wrong type, 9 unexpected). Duplicates 9 vs 1.

## 10. Latency and tokens (per encounter, means; 50 records)
| | input tokens | output tokens | total tokens | latency mean / median | decode tok/s | peak memory |
|---|---|---|---|---|---|---|
| P02 | 4,329 | 1,356 | 5,685 | 235.5 s / 232.9 s | 6.74 | 3,111 MB |
| S1 | 3,316 | 617 | 3,934 | 106.6 s / 107.0 s | 7.34 | 2,844 MB |
Total inference latency 11,773 s (P02) vs 5,329 s (S1); S1 run wall time 5,541 s. Input tokens remain large because the transcript renderer was unchanged. Efficiency gains are real and measured on this device.

## 11. What actually happened (root cause)
The 0.6B model largely copied the empty S1 template: placeholder items with blank fields (83 of 580 items blank in their primary field), `reported_by` blank in 139 of 417 fields and filled with the transcript's speaker ids (`person_1`…`person_4`, 278 fields) instead of roles, `allergy_status` blank in 14 of 37 records, `chief_complaint` never emitted, schema words as content (`"assessment": "provisional"`, `"finding": "no"`), and mixing fields (`"route": "once a day"`). Fewer, shorter outputs raised precision but did not raise recall. The adapter did not hide or repair any of this.

## 12. Limitations
- Development set only (50 records, same ones P02 was tuned on); S1 was designed after seeing P02 results on these records, so the comparison is not independent and any further tuning on them would not be validation.
- Single run, greedy; no variance estimate. Small counts per category.
- Labels are generator-derived, not human-verified; strict matching penalises acceptable paraphrase (fuzzy F1 shown for reference only).
- Adapter constants (e.g. none_stated → "No known allergies" negative finding, investigations/procedures merged, `clinical_conditions` fed from `current_conditions`) are definitional but could affect scores; invalid enum values such as `person_N` are passed through, not corrected.
- Pre-flight check `forbidden_ids_blocked_by_the_spy` in the frozen runner cannot fail (`or True`); spy behaviour is evidenced instead by EXP_004 negative tests and the final access audit (0 locked-test files, sealed hash file not opened, 0 validation records, 400 prompt-dev label files opened by the evaluator only).
- `speaker_errors` in the evaluator's clinical-error block is a placeholder 0; use the evaluator's speaker-attribution accuracy (section 8). The fabricated-date count uses a quirky expression; treat 7 vs 66 as approximate in size but clearly lower for S1.
- Timestamps and ids are still present in the rendered transcript (unchanged renderer); removing them was not tested.

## 13. Recommendation: **REVISE (do not retain S1.0 as is; do not reject the direction)**
The compact output keeps its efficiency and precision gains, but parse failures, template copying, missing chief complaint and broken speaker attribution outweigh them on recall and F1.

## 14. Recommended next experiment (not started)
S1.1 on **new** development material or clearly labelled as a further tuning pass on the same 50: (a) remove empty-string template values from the prompt (describe fields in words, no blank placeholders; chief complaint as an explicit instruction); (b) ask for speaker *role* words in a form the model can copy (or drop `reported_by` and derive it deterministically from the cited transcript line in the adapter only if approved); (c) enable schema-constrained/structured decoding in OpenVINO GenAI, if available, to remove the 13 parse failures; (d) optionally render the transcript without segment ids and times. Needs approval before any script/schema change.

## Compliance
Only EXP_006 files created; P00–P05, EXP_001–005, Batch 001/002, frozen schemas, existing scripts, validation (50) and locked-test (400) records untouched; `git status` shows no tracked-file modification; GitHub not touched; no Batch 002 inference; no S2–S4, LoRA or Batch 003.
