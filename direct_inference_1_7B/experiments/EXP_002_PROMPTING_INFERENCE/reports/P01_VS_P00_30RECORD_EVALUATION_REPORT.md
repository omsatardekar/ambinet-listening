# Qwen3-1.7B: P00 (direct) vs P01 (schema-guided) on the same 30 records

**DEVELOPMENT-ONLY.** The 50 prompt-development records were used earlier to develop the 0.6B prompts, and the labels are generator-derived (not human-verified). Nothing here is independent or clinical validation. n = 30 records, so small differences are within noise.

## 1. Scope and what was run
- P01 was launched on the 50 frozen ids and **stopped by instruction after exactly 30 completed records** (`logs/P01_stopped_at_30.txt`: 30 raw outputs at 21:15 IST; record 31 was never started). Records 31–50 were not run. The 30 are the first 30 of the frozen 50 in id order: `00035 … 00266`.
- P00 uses its saved 50-record outputs, re-scored on **these same 30 ids** with the same evaluator. No P00 inference was re-run. The original 50-record P00 baseline and its evaluation are untouched.
- Unchanged for both: Qwen3-1.7B @ `70d244cc`, OpenVINO FP16 on GPU, greedy, thinking off, `max_new_tokens` 4096, same transcript rendering, same strict canonical evaluator. Failed or truncated outputs count as zero predictions, so every metric is over all 30 records.
- P01 prompt: sha256 `b51121cd18b4f798971204b280d81eb5ea43498822f472a165210c6d82543ad8` (P00 plus a "structure rules" block, see section 6). Frozen before inference in `manifests/FREEZE_P01_schema_guided_dev50.json`.
- Integrity: validation, locked-test and sealed files were not opened by the evaluation (audit in `METRICS.json`). The 0.6B tree is identical to its pre-rename inventory and the frozen 0.6B P00–P05 files are unchanged (`logs/integrity_after_stop_P01_30.json`). **Disclosure:** because the run was stopped, its own end-of-run audit file (`file_access_audit_P01…json`) and exit checks were not written. The only P01-frozen file whose hash now differs is `scripts/evaluate_run.py`, which I extended afterwards (subset option); no inference-side file changed.
- Run time: inference sum 9.12 h; wall clock 12:03 → 21:15 IST (9 h 12 min) for 30 records.

## 2. Headline: P00 vs P01, same 30 records
| Metric | P00, 30 records | P01, 30 records | 0.6B P02 (ref.) |
|---|---:|---:|---:|
| Strict micro precision | 0.258 | 0.283 | 0.226 |
| Strict micro recall | 0.117 | 0.156 | 0.083 |
| **Strict micro F1** | **0.161** | **0.201** | 0.122 |
| TP / FP / FN | 128 / 369 / 965 | 170 / 431 / 923 | 91 / 312 / 1002 |
| Strict macro P / R / F1 | 0.216 / 0.127 / 0.154 | 0.234 / 0.156 / 0.180 | 0.201 / 0.105 / 0.128 |
| Valid JSON (of 30) | 23 | 25 | 30 |
| Parse failures | 7 (all truncation) | 5 (4 truncation, 1 invalid JSON, `00206`) | 0 |
| Truncated outputs (4096 cap) | 7 | 4 | 0 |
| Fully canonical-schema-compliant records | 0 | 0 | 0 |
| Schema violations, total (per parsed record) | 504 (21.9) | 614 (24.6) | 637 |
| Evidence grounding, strict / partial | 0.006 / 0.008 | 0.018 / 0.180 | 0.000 / – |
| Speaker attribution accuracy | 0.603 | 0.674 | 0.377 |
| Mean latency per record | 1091 s | 1094 s | 233 s |
| Median latency | 1006 s | 1047 s | – |
| Decode / overall tokens per s | 2.84 / 2.55 | 2.76 / 2.45 | 6.74 / 5.73 |
| Mean output tokens | 2811 | 2709 | 1345 |
| Peak system memory used (sampled) | 14,701 MB | 16,141 MB | – |

Full tables: `evaluations/P01_schema_guided_dev50/subset30/METRICS.json`, `CATEGORY_METRICS.json`, `ANALYSIS.json`, `reports/P01_schema_guided_dev50_subset30_EVALUATION.md`.

## 3. How much of the gain is extraction and how much is formatting?
P01 scores +0.040 micro F1 over P00. Splitting the 30 records by whether each output parsed:

| Group | Records | P00 TP | P01 TP | Reading |
|---|---:|---:|---:|---|
| Parsed in both | 20 | 115 | 126 | **Pure extraction change**: F1 0.208 → 0.220 (+0.012), recall 0.167 → 0.183 |
| P00 truncated, P01 parsed ("recovered") | 5 (`00040 00060 00127 00155 00210`) | 0 | 44 | Scoring artefact of finishing vs not finishing |
| P00 parsed, P01 truncated/invalid ("lost") | 3 (`00037 00092 00206`) | 13 | 0 | The same effect in reverse |
| Failed in both | 2 (`00168 00204`) | 0 | 0 | |

- Net TP gain +42 = **+11 from extraction on stable records, +31 from changes in which records finished** (+44 recovered, −13 lost). So roughly three quarters of the headline gain is completion-driven, and only about a quarter is better extraction on records both prompts completed.
- The +0.012 F1 on 20 records (115 → 126 TP) is small and not statistically distinguishable from noise.
- Clinically, P01's real improvement is modest. The headline gain is mostly "fewer outputs died at the cap" and that change is itself fragile: three records got worse.

## 4. JSON, schema and truncation
**P01's formatting instructions did not take effect.**
- Layout: 30/30 outputs in both runs are still pretty-printed with indentation (the compact-layout rule was ignored). Mean output tokens (parsed) 2420 vs 2451.
- Schema violations went **up** (614 vs 504; 24.6 vs 21.9 per parsed record). Kinds in P01: 395 missing fields, 212 enum violations, 5 missing top-level keys, 2 unexpected fields, 0 wrong-type errors. P00: 298 / 200 / 0 / 6 / 0.
- Missing fields are dominated by the `confidence` key (the model omits `"confidence": null` even though the prompt now says it is mandatory): top items are `vital_signs[].confidence` (57), `clinical_actions` (26), `negative_findings` (26), `physical_examination` (25), `symptoms` (24), `medications` (24).
- Enum violations: speaker ids such as `person_1`/`person_2` are still written in `reported_by`/`observed_by` (e.g. `symptoms[].reported_by='person_1'` ×15, `vital_signs[].reported_by='person_1'` ×15, `medications[]` ×12, `past_medical_history[]` ×13) despite the explicit "never write a speaker id" rule; `social_history.status` is `''` or `'ongoing'` (not an allowed value, 26 cases) and `social_history.category` invalid (23). No record is fully canonical-schema compliant in either run, so "schema compliance" is 0/30 for both.
- Truncation: 4/30 (P01) vs 7/30 (P00), all four cut inside the last big section, `clinical_evidence` (`00037 00092 00168 00204`). The evidence section is shorter on average in P01 (1733 vs 2269 characters), which coincides with the lower cap rate, but the mechanism is not established and the layout did not change. One new failure type appeared: `00206` stopped normally at 3620 tokens but produced invalid JSON. Two records (`00168`, `00204`) fail in both runs.
- Conclusion: 4 of 30 (13%) still do not finish within 4096 tokens, so truncation remains a blocker for any prompt that keeps the full evidence section.

## 5. Per-category results (strict; P01 on 30 records; P00 in brackets)
| Category | TP / FP / FN | P / R / F1 | P00 F1 |
|---|---:|---|---:|
| chief complaint | 2 / 23 / 28 | 0.08 / 0.07 / 0.07 | 0.11 |
| symptoms | 12 / 24 / 79 | 0.33 / 0.13 / 0.19 | 0.13 |
| negative findings | 4 / 36 / 164 | 0.10 / 0.02 / 0.04 | 0.02 |
| past medical history | 6 / 27 / 44 | 0.18 / 0.12 / 0.14 | 0.13 |
| surgical history | 2 / 20 / 14 | 0.09 / 0.12 / 0.11 | 0.11 |
| family history | 6 / 14 / 11 | 0.30 / 0.35 / 0.32 | 0.32 |
| social history | 13 / 16 / 75 | 0.45 / 0.15 / 0.22 | 0.08 |
| **medications** | 37 / 7 / 35 | 0.84 / 0.51 / 0.64 | 0.55 |
| allergies | 3 / 18 / 10 | 0.14 / 0.23 / 0.18 | 0.19 |
| vital signs | 51 / 40 / 78 | 0.56 / 0.40 / 0.46 | 0.39 |
| physical examination | 0 / 39 / 46 | 0.00 / 0.00 / 0.00 | 0.00 |
| review of systems | 0 / 21 / 40 | 0.00 / 0.00 / 0.00 | 0.00 |
| clinical conditions | 0 / 29 / 20 | 0.00 / 0.00 / 0.00 | 0.00 |
| clinical assessment | 17 / 8 / 31 | 0.68 / 0.35 / 0.47 | 0.42 |
| investigations and procedures | 15 / 23 / 34 | 0.39 / 0.31 / 0.34 | 0.27 |
| clinical actions | 1 / 41 / 164 | 0.02 / 0.01 / 0.01 | 0.00 |
| follow-up | 1 / 22 / 25 | 0.04 / 0.04 / 0.04 | 0.04 |
| clinical uncertainties | 0 / 23 / 25 | 0.00 / 0.00 / 0.00 | 0.00 |

Where 1.7B is **worse than 0.6B P02** (same 30 records): chief complaint (F1 0.07 vs 0.20), review of systems (0.00 vs 0.09), allergies (0.18 vs 0.24), and surgical/family history are level or lower; it also writes more unsupported claims (79 vs 49), and cannot complete 4–5 of the 30 records. 0.6B P02 has 0 failed records.

## 6. What P01 changed (hypothesis and outcome)
- Hypothesis: explicit structure rules (array types, lower-case roles, mandatory null `confidence`, enum-only values, compact layout) would raise valid-JSON and schema compliance and cut truncation without changing extraction.
- Changes (only added text, one block before "Output format"): the 0.6B-P01 structure rules plus two lines (compact layout; `symptoms.category` must be from the list).
- Outcome: the schema targets were **not met** (violations up, 0 compliant records, `person_N` still used, layout unchanged). Valid JSON 23 → 25 and truncation 7 → 4 improved but flip individual records both ways (+5/−3). The compact-layout and category rules cannot be separated from the other rules, so the result is the combined effect of all rules.

## 7. Evidence grounding and speaker attribution
- Evidence grounding (601 predicted entities): strict 11 (1.8%), lenient 2, partially supported 108 (18.0%), unsupported 480 (79.9%). P00: 3/497 strict (0.6%). The `clinical_evidence` records do not reproduce the exact transcript text the evaluator expects, and the prompt gives no segment ids to cite, so this is a design problem, not just a P01 problem.
- Speaker attribution: 0.674 (97/144) vs 0.603 (70/116). By gold role in P01: patient 56/71 (79%), doctor 30/53 (57%), nurse 11/14 (79%), family member 0/6. Part of the remaining error is the `person_N` ids written instead of roles.
- Unsupported claims (evaluator-flagged): 79 (13% of predictions) vs 77. 352 of P01's 431 false positives are nevertheless supported by the transcript (extra but true, or phrased differently), so strict precision understates real precision.

## 8. Clinical extraction accuracy (P01, 30 records)
- **Medications (strongest):** 37/72 recalled, precision 0.84, **0 dose errors on 33 matched**, 14 of 17 gold *planned* prescriptions missed. Record `00042`: gold metformin 500 mg twice a day, telmisartan 40 mg once a day, glimepiride 1 mg before breakfast (status *planned*); P01 extracts all three with correct doses, but marks glimepiride `currently_used` instead of `planned`. Record `00157`: gold cetirizine 10 mg + fluticasone nasal spray 50 µg; P01 gets cetirizine, **misses fluticasone** (a newly prescribed drug), and gives frequency "day to day" (gold "when it flares").
- **Allergies (weak):** 3 correct, 18 spurious, 10 missed; 22 of 30 records have an allergy-status error. Typical cases: the model lists a *medication as an allergy* (`00042`: glimepiride), writes the placeholder "none" (`00157`) where gold is an empty list, and a naming mismatch in five records (model "antibiotic" vs gold "antibiotic unspecified"), which is semantically right but scores as miss + false positive.
- **Symptoms:** 12/91 recalled (13%), precision 0.33. Typically one symptom per record where gold lists two or three: `00157` gold Sneezing + Nasal congestion, P01 sneezing only; `00042` gold Polydipsia + Fatigue, P01 "constant thirst" (paraphrase of polydipsia, scored a miss; fatigue absent). `00040` gold hand numbness, nocturnal paraesthesia, wrist pain; P01 "tingling in fingers".
- **Negative findings (very weak):** gold 168, predicted 40, **correct 4 (2.4%)**. The four hits are all "No previous surgery". Gold denials such as `00035` palpitations, chest pain, confusion, "no known allergies"; `00042` chest pain, vomiting, weight loss, foot ulcers; `00157` anosmia, facial pain, fever, shortness of breath are mostly not extracted anywhere (only 20 of 137 gold negatives appear in any category). No polarity flips (0), so when negatives are written they are not turned into positives; the problem is omission.
- **Temporality:** 9/12 correct (0.75) on matched symptoms, same as P00; the sample is tiny.
- **Vital signs:** 51/129 recalled. Many are naming mismatches under strict matching ("pulse" vs gold Heart rate, "SpO2" vs Oxygen saturation, "height/weight" vs Body height/Body weight, "temperature" vs Body temperature). `00157` has five gold vitals and P01 emits none.
- **Assessment / investigations:** assessment 17/48 (0.68 precision); investigations 15/49. Examples: correct "Carpal tunnel syndrome", "Nerve conduction study", "HbA1c"; near-misses scored as wrong: "kidney function tests" vs "Renal function test", "allergy test" vs "Allergen skin prick test", "This is probably diabetes that isn't well controlled" vs "Diabetes that isn't well controlled" (the model copies the doctor's sentence instead of the diagnosis).
- **Zero-score categories:** physical examination (model writes sentence-length quotes: "feet look fine no ulcers or sores and the pulses are palpable" vs gold "no foot ulcers"), review of systems, clinical conditions (model puts "diabetes" under medical history while gold uses clinical conditions, e.g. "type 2 diabetes mellitus"), clinical uncertainties (model guesses `date_uncertain` (e.g. `00040`, `00042`, `00060`) where gold has adherence/allergy/duration uncertainty), and clinical actions (gold has 165 actions, about 5.5 per record; the model produces 42 and 1 matches). The `00035` follow-up is predicted as `consultation|310.19 310.89s`, a timestamp copied into a time reference.

## 9. Most important problems to improve
1. **Truncation / output budget:** 4/30 still hit the cap, always inside `clinical_evidence`. The evidence section carries almost no scored value (1.8% strict grounding) but costs a large share of the 4096 tokens. This is the largest lever for completed records.
2. **P01's format rules are ignored** (roles as `person_N`, missing `confidence`, invalid enums, indented output). Prompt text alone does not enforce the schema at 1.7B; zero records are canonical-compliant.
3. **Negative findings and clinical actions:** recall 2% and 1%, the two biggest FN pools (164 and 164 missed).
4. **Name normalisation versus the strict canonical matcher:** many "false positives" are paraphrases of the gold item (thyroxine/levothyroxine, heart attack/myocardial infarction, pulse/heart rate). Part of the remaining gap is surface form, not clinical understanding; 352 of 431 FPs are transcript-supported.
5. **Allergies:** medication-as-allergy errors, "none" placeholders, and 22/30 status errors.
6. **Symptom completeness:** about 13% recall; the model stops after one or two symptoms.
7. **Planned medications:** 14/17 prescriptions made in the consultation are missed or given the wrong status.
8. **Evidence and attribution:** evidence grounding 1.8% strict; doctor-stated items attributed correctly only 57% of the time; family members 0/6.
9. **Memory headroom:** sampled system memory peaked at 16,141 MB (of about 16,190 MB), against 14,701 MB for P00. The laptop is at its limit during generation. This did not cause a failure in these 30 records, but it leaves no margin.

## 10. Limits of this comparison
- 30 records from one development subset that was also used for the 0.6B prompts; results are not independent.
- Greedy decoding is deterministic per prompt, but the 5 recovered / 3 lost records show that small prompt changes move individual outputs across the 4096 cap, so the P01-vs-P00 difference on completion is not attributable to any single rule.
- P01 combines several instructions; no ablation was run.
- Failed outputs count as zero, per the agreed headline convention. Parsed-only scores (extraction-only, section 3) are shown for diagnosis and are not the headline.
- Records 31–50 were not run for P01, so the 50-record P00 baseline and the 30-record P01 results are different sample sizes and must not be compared directly.

**Status:** stopped as instructed. P02, P03 and P04 were not started, no prompt was modified, and no new inference was run.
