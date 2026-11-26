# S1 error analysis (50 prompt-development records; gold labels are generator-derived)

Counts from `evaluation/S1_AGGREGATE_METRICS.json` (`clinical_errors`) and `evaluation/S1_OUTPUT_DIAGNOSTICS.json`. S1 vs P02.

## Medications
Predicted 56 vs 57 (gold 128). Matched 41 vs 46. False-positive names 12 vs 11; names not in transcript 0 vs 2. Missing prescribed (gold planned, unmatched) 25 vs 25 of 29 – the model still rarely extracts newly prescribed drugs. Dose errors on matched 3/36 vs 5/40. Status errors on matched 4 vs 5. One observed copy error: route filled with the frequency ("once a day"). Medication-as-allergy 2 vs 1.

## Allergies
Allergy-status errors 28 vs 28 of 50. `allergy_status` field blank in 14/37 parsed outputs, "reported" in 20, "none_stated" in 3; many gold records are "none_stated". 15 placeholder (blank/none) allergy entries in both systems; 13 blank allergy items in S1 raw output. The adapter turns `none_stated` into an explicit negative finding and does not convert unknown/blank into negative.

## Polarity / negative findings
Gold negatives 273; S1 recovered 6 (P02 0) – a real gain but tiny (2.2 % recall). Gold-positive predicted as negative 6 (+1 reverse) vs 4 for P02 (the evaluator's own polarity block counts 5 + 1; the two counters differ slightly in scope). Contradictions 4 vs 16. Negative finding "no" copied as content in some records.

## Speaker attribution (largest regression)
Accuracy 0.088 (9/102) vs 0.421 (53/126). Cause: `reported_by` is blank in 139 of 417 fields and holds transcript speaker ids (`person_1`…`person_4`, 278 fields) instead of the role. The adapter does not correct or infer these; invalid values are passed through (489 canonical enum violations).

## Temporality / fabrication
Fabricated date/time values 7 vs 66 (large improvement, consistent with removing timestamps from the task). Evaluator unsupported claims 60 vs 85. No invented appointments observed in the adapter output.

## Duplicates
9 vs 1 same-key duplicates (e.g. ECG listed as both investigation and procedure; the adapter preserves duplicates by design).

## Structural failure modes in S1 raw outputs
13 invalid-JSON outputs (missing comma, stop reached, no truncation); `chief_complaint` missing in 37/37 parsed; `clinical_assessment`/`follow_up` returned as strings or objects instead of lists (12 records, skipped and counted); placeholder items (83/580 blank primary field); schema words copied as content ("provisional", "no"); 492 enum violations.

## Interpretation
The simplification removed fabricated datetimes and cut tokens and latency by about half, and precision rose. But a 0.6B model given a template with empty strings tends to echo the template, so many fields are blank, wrong-typed or non-vocabulary, and records that fail to parse score zero. These are model-compliance failures, not adapter faults; the adapter was unchanged and its 25 tests passed before the run. Gold-based counts are heuristic, generator-derived, and based on small numbers.
