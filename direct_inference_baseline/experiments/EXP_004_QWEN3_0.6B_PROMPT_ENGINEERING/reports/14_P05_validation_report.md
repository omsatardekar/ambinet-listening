# P05 validation report (50 validation records) — authorised run, frozen configuration

Freeze manifest SHA-256: e383d3a352a6e431bc74c49c8c409d15a6e02831b05ee73e47aec472fd56fae0 (unchanged before and after the run; 0 frozen-file mismatches; evaluator files byte-identical; P02 prompt sha cf50ce8e… unchanged).
Run: 2026-11-13 03:38–07:06 local, wall 12,480 s (3.47 h), GPU UHD 620, OpenVINO FP16, greedy, thinking off, max_new_tokens 6144. 50/50 records parsed on the first attempt.
Outputs: outputs/P05_validation_50/, evaluation/P05_validation_50/, evaluation/P05_validation_50_eval/p05_evaluation.json, logs/P05_validation_stdout_stderr.log, audit/P05_validation_50/.

## Access audit
Runner: 928 file opens; locked-test files 0; sealed hash file not opened; label files 0; only the 50 validation transcripts opened.
Evaluator: 501 opens; locked-test 0; sealed not opened; only validation transcripts and the 50 validation labels (counter shows 100 label opens, i.e. each label opened twice by the unmodified evaluator). Sampler: 0 labels, 0 locked-test.
The pre-existing disclosure (reports/08) still applies: earlier runs hashed locked-test files, never parsed them.

## Five quantities, reported separately
1. Citation coverage (all 711 extracted facts): 530 cited = 74.5%; 181 abstained.
   Abstentions: no_candidate 55, speaker_class_mismatch 55, polarity_conflict 32, no_anchor_words 14, ambiguous 13, kinship_conflict 8, question_without_answer 2, only_generic 1, value_not_in_evidence 1.
2. Agreement with gold-cited segments when cited (149 strictly matched facts): 134 cited; hit when cited 99.3%.
   [CORRECTED WORDING, see "Correction note" below: 99.3% = 133/134. 134/149 = 89.9% is the coverage on matched facts, a different quantity.]
3. Agreement counting abstentions as misses: 89.3% (R_simple 86.6%, R_main 83.2%). [= 133/149]
4. Human-review semantic correctness: PENDING. Packets generated (audit/P05_validation_50/, seed 20261113, 30 cited + 15 abstained); no reviewer has scored them.
5. Correctness of the underlying fact (stage 1 = final, identical counts): strict micro P 0.212, R 0.085, F1 0.121 (TP 149, FP 553, FN 1612). Development-stage P02 numbers, not final. 134 of 530 cited facts match gold; the rest are cited but not verified as correct facts.
Gold agreement is not clinical accuracy.

## Frozen gates: all 15 passed
Extraction counts identical; builder integrity 50/50; 0 invalid ids; 0 schema violations; 489/489 evidence records correct; 772/772 supports reciprocal; question-only 0; kinship 0; speaker-class 0 (cited facts matched set); greeting-like 0.75% (1 fact); polarity 0; segment0 0; coverage 74.5% (≥60%); hit when cited 99.3% (≥90%); abstentions-as-misses 89.3% (≥ R_simple − 5).
On all 530 cited facts: greeting-like 2, polarity 2 (0.4% each).

## Weak spots (for the record, no tuning done)
Coverage by group: negative findings 26.4% (14/53), follow-up 22.7% (5/22), chief complaint 54% (speaker-class abstentions 21), family history 52.9% (8 kinship abstentions), review of systems 60.9%; medications 100%, vital signs 96.3%, surgical history 100%.
Matched-fact denominator is only 149 (21% of extracted facts), so group-level hit rates are small-sample.
Evaluator grounding is lexical and circular for retrieval; it is not evidence of correctness.
Compared with prompt_dev: coverage on matched facts 89.9% (dev 93.5%), hit when cited 99.3% (98.6%) — consistent, not better; R_cons was tuned on prompt_dev through four disclosed revisions, so validation is the first independent look.

## Performance
Mean generation 245 s/encounter; mean 4,290 input and 1,426 output tokens; max output 3,277 (no truncation at 6,144).
Stages 2–4 are deterministic and negligible in time.

## Status
Not final. No locked-test use. The human audit (D3) is not yet done. No further experiment started.

## Correction note (2026-11-13, reporting only; run outputs, evaluator and frozen files unchanged)
Source: experiments/p05_eval_lib.py (row, accumulate) and experiments/evaluate_p05.py; numbers from evaluation/P05_validation_50_eval/p05_evaluation.json (matched_facts_R_cons.ALL, all_facts_R_cons.ALL). The 99.3% / 134-of-149 apparent conflict is a wording ambiguity in this report, not a calculation error; the evaluator's figures are unchanged.

| Quantity | Numerator | Denominator | Value | Formula (code) |
|---|---|---|---|---|
| Citation coverage, all extracted facts | 530 cited | 711 extracted facts | 74.5% | cited / n over every predicted fact (no gold needed) |
| Coverage on matched facts | 134 cited | 149 strictly matched facts (all have a gold citation) | 89.9% | row(): cited / n on the matched set |
| Agreement when cited (retrieval hit rate) | 133 hits | 134 cited matched facts | 99.3% | hit / cited; hit = retrieved segment set intersects gold-cited set |
| Agreement, abstentions as misses | 133 hits | 149 matched facts | 89.3% | hit / n |
| Segment-set precision / recall vs gold (cited matched facts) | inter/sel; inter/gold | | 0.896 / 0.553 | segment-level overlap, fact-level counted over cited only (recall denominator counts gold segments of all 149 facts) |
| Cited facts whose fact strictly matches gold | 134 | 530 cited facts | 25.3% | NOT citation precision; a property of the extracted fact |
| Underlying extraction strict P / R / F1 | TP 149 | TP+FP 702; TP+FN 1761 | 0.212 / 0.085 / 0.121 | evaluator strict micro; independent of citations |

Verification: 0.9925 x 134 = 133.0 and 0.8926 x 149 = 133.0 (same 133 hits); 134 + 15 abstained matched facts = 149; the matched set (149) equals the evaluator's matched_total, so every strict match had a gold citation.
Distinctions: retrieval agreement = hit rates (99.3% when cited, 89.3% with abstentions as misses, defined only on the 149 matched facts); citation coverage = cited share (74.5% all facts, 89.9% matched facts); citation precision against gold = segment-set precision 0.896 (matched cited facts only; there is no gold citation for the other 396 extracted facts, so citation precision over all 530 cited facts is not measurable); extraction P/R/F1 are properties of the stage-1 facts only.
Residual item: 711 facts were extracted but TP+FP = 702. All 711 are in strict categories and entity_list returns 711; evaluator keyed() drops entities whose key is empty or None, which is the only filter before TP/FP, so 9 facts with an empty key are in the coverage denominator but not in precision. Inferred from code, not itemised per fact.
Also: set recall 0.553 is segment-level over matched facts (it penalises retrieving fewer segments than gold cites), so it must not be read as fact recall.
