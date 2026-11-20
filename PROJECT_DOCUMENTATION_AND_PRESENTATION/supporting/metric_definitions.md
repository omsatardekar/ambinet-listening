# Metric definitions

Implemented by the frozen evaluator `direct_inference_baseline/evaluation/entity_matching.py` (`prf`, `micro_macro`) and `evaluation_runner.py` (`aggregate`).

## Counts
- **TP (true positive):** a predicted fact whose normalised key equals a gold fact's key (multiset: matched one-to-one, `TP = Σ min(gold_count, pred_count)` per key).
- **FP (false positive):** predicted facts not matched = `predicted − TP`.
- **FN (false negative):** gold facts not found = `gold − TP`.
- There is **no true-negative count**: "facts that correctly were not output" is undefined.

## Formulas
- Precision = TP / (TP + FP) — of what we output, how much is right.
- Recall = TP / (TP + FN) — of what is there, how much we found.
- F1 = 2 × Precision × Recall / (Precision + Recall) — harmonic mean; punishes imbalance. Undefined (reported `null`/`n/a`) when a denominator is 0; never replaced by 0 or 1.
- Worked example (1.7B P02, 30 records): TP 234, FP 490, FN 859 → P = 234/724 = 0.323; R = 234/1,093 = 0.214; F1 = 2×0.323×0.214/(0.323+0.214) = 0.258.

## Micro vs macro
- **Micro:** pool TP/FP/FN over *all* categories and records, then compute P/R/F1 once. Large categories (e.g. clinical actions 165, negative findings 168, vitals 129 gold facts) dominate.
- **Macro:** compute F1 per category (18 here), then average. Every category weighs the same; categories with F1 undefined are excluded from the macro average (the evaluator lists them). Macro answers "how good across categories", micro answers "how good across facts".
- Do **not** call the average of category F1s "accuracy".

## Why F1 is not accuracy
Accuracy = correct decisions / all decisions. That needs a fixed set of items each judged right or wrong (including "nothing here" cases). In extraction the number of facts varies per record, outputs can contain extra facts, and missing facts are not "decisions". F1 measures the overlap between two *sets* of facts (found vs expected). An F1 of 0.258 means "balance of 32% precision and 21% recall", not "25.8% accuracy".

## Tiers used in our reports
- **Tier 1 (headline):** all records; failed/unparseable outputs count as zero predictions (all their gold facts are FN).
- **Tier 2:** parsed records only — shown beside tier 1, never instead (it hides failures).
- **Fuzzy (diagnostic, non-official):** extra pairing of leftovers by token Jaccard ≥ 0.75 or difflib ratio ≥ 0.85; never mixed with strict.

## Other measures
| Measure | Definition | Note |
|---|---|---|
| JSON validity | parsed (valid JSON object) / attempted | failed types: `truncated`, `invalid_json`, `empty`, `not_object` |
| Schema compliance | records with zero schema violations (`schema_validator.py`: missing_field, wrong_type, enum_violation, unexpected_field) | 0 fully compliant for P00/P01 in all runs; not measured for P02 |
| Record-level success rate | parsed / attempted | completion, not correctness |
| Token-cap failure | output reached `max_new_tokens` and JSON incomplete | cap = 4,096 (1.7B) |
| Speaker attribution accuracy | role on matched facts equals gold role (evaluator excludes unknown/unreliable roles) | analysis-script variant counts all matched facts; different denominators |
| Evidence-ID validity | cited segment ids that exist in the transcript | does not prove the segment supports the fact |
| Evidence grounding (evaluator) | lexical support of predicted entity by its cited text: strict/lenient/partial/unsupported | different thing from id validity |
| Unsupported claims (evaluator) | strict FPs lexically unsupported anywhere in the transcript | lexical, not clinical |
| Attribute accuracy | on already-matched facts, value of dose/status/temporality… equals gold | conditional accuracy |

## Accuracy: what is and is not available
- Field-level exact match and record-level accuracy are **not computed**; "overall accuracy" is **not available**.
- If needed in future (without changing history): report strict micro F1 as primary, add a separately-named semantic/adjudicated F1, a "critical-facts-complete" record rate, and attribute accuracy on matched facts (see `04_FINE_TUNING_AND_FUTURE_ROADMAP.md` §6).

## Fact-level accuracy (added metric)
Fact-level accuracy = TP / (TP + FP + FN). It is the share of all facts that appear in either the gold or the output (the union) that the model got right. It is the closest honest "overall accuracy" for an extraction task, because it counts both extra facts and missed facts as errors. It is also called Jaccard / critical success index. It is **not** classification accuracy, and it is always lower than F1 (F1 = 2a/(1+a) where a is this value). Computed from the strict TP/FP/FN of each run, so it uses the same matcher and the same failure handling (failed records = zero predictions). Not computable where TP/FP/FN were not recorded (S1.1 B1/B2). Added to the CSV as `fact_level_accuracy_tp_over_tp_fp_fn`. Record-level accuracy (all facts in a record correct) is still not computed.
