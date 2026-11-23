# Prompt comparison (filled in as experiments complete; all rows use identical encounter ids and settings)

Reference rows come from EXP_003 outputs (no new inference). Subsets: `prompt_dev` (50 ids) and `validation` (50 ids), `experiments/split_v1.json`.

| Prompt | Subset | Valid JSON | Schema compliant | Micro P | Micro R | Micro F1 | Macro F1 | Mean latency (s) | Status |
|---|---|---|---|---|---|---|---|---|---|
| P00 | prompt_dev | 48/50 | 0 | 0.237 | 0.026 | 0.047 | 0.048 | 152.9 | reference (EXP_003) |
| P00 | validation | 46/50 | 0 | 0.280 | 0.028 | 0.051 | 0.061 | 155.1 | reference (EXP_003) |
| P01 schema-focused (prompt_dev 50) | 50/0 | 0 | 658 (P00 444) | 110/345/1750 | 0.242 / 0.059 | 0.095 (P00 0.047) | 0.086 | **REJECT** (violations +48%, wrong_type -36%) |
| P02 comprehensive (prompt_dev 50) | 50/0 | 0 | 1064 (P00 444) | 153/522/1707 | 0.227 / 0.082 | 0.121 (P00 0.047) | 0.122 | **KEEP at development stage only (8/8 criteria); NOT validated, NOT final; validation postponed by user decision** |
| P03 evidence-grounded (PARTIAL: 35 of 50 prompt_dev ids, stopped by user) | 33/2 | 0 | 313 (P00 same ids 338) | 40/138/1243 (P00 38/123/1245) | 0.225 / 0.031 | 0.055 (P00 0.053, same 35 ids) | 0.057 | PARTIAL, not final; REJECTED AS DESIGNED by user (0% strict grounding, 1 evidence record per encounter) |
| P04 integrated segment-id evidence (revised v2), SMOKE TEST on 5 prompt_dev ids only | 4/5 parsed (00037 invalid JSON) | 0 | 88 in 4 records | 9/31/154 (P02 same ids 20/62/143) | 0.225 / 0.055 | 0.089 (P02 0.163, same 5 ids) | - | REJECTED AS DESIGNED by user; smoke gates S1, S2, S3, S5 FAIL; S6 PASS; evidence references: 11 of 40 facts clearly appropriate (my reading) |
| P05-P06 | - | - | - | - | - | - | - | not run |

Macro F1 here is the mean of the 18 category F1s on the subset totals (as in the EXP_003 evaluator).


| P05 (design only): P02 extraction + conservative retrieval evidence (R_cons v4), zero-inference diagnostics on P02 outputs | - | - | - | extraction identical to P02 (153/522/1707) | - | - | - | on 153 matched facts: 93.5% cited, 98.6% hit when cited; 27.4% of P02 facts abstained; development results only |

| P05 frozen (R_cons v4), validation pending | - | - | - | - | - | - | - | development diagnostics only; validation not started |
