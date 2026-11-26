| run | model | prompt | group | attempted | parsed | failed/unparsed | note |
|---|---|---|---|---|---|---|---|
| q06_exp003_direct_dev100 | Qwen3-0.6B | direct | core | 100 | 94 | 6 | 5 smoke + 95 remaining = 100 development encounters |
| q06_exp004_P01 | Qwen3-0.6B | P01 schema focused | core | 50 | 50 | 0 |  |
| q06_exp004_P02 | Qwen3-0.6B | P02 comprehensive extraction | core | 50 | 50 | 0 |  |
| q06_exp004_P03 | Qwen3-0.6B | P03 evidence grounded | core | 35 | 33 | 2 | partial run (stopped early) |
| q06_exp004_P04_smoke5 | Qwen3-0.6B | P04 (5-record smoke only) | extra | 5 | 4 | 1 |  |
| q06_exp004_P05 | Qwen3-0.6B | P05 validation (retrieval pipeline) | core | 50 | 50 | 0 | final predictions after the P05 pipeline |
| q06_exp006_S1 | Qwen3-0.6B | S1 simplified extraction | core | 50 | 37 | 13 | adapted to the full schema by a deterministic adapter |
| q06_exp007_S1_1_B1 | Qwen3-0.6B | S1.1 arm B1 | core | 50 | 45 | 5 |  |
| q06_exp007_S1_1_B2 | Qwen3-0.6B | S1.1 arm B2 | core | 50 | 31 | 19 |  |
| q06_exp005_P02_repaired | Qwen3-0.6B | P02 stage1 + deterministic repair | extra | 50 | 50 | 0 | post-processed output |
| q06_exp005_P05_repaired | Qwen3-0.6B | P05 final + deterministic repair | extra | 50 | 50 | 0 | post-processed output |
| q17_P00_direct | Qwen3-1.7B | P00 direct | core | 50 | 35 | 15 |  |
| q17_P01_schema_guided | Qwen3-1.7B | P01 schema guided | core | 30 | 25 | 5 |  |
| q17_P02 | Qwen3-1.7B | P02 (frozen) | core | 30 | 28 | 2 |  |
| q06_exp008_v6b_seg_evidence_smoke3 | Qwen3-0.6B | H1 variant v6b_seg_evidence (3 spare ids) | extra | 3 | 3 | 0 | prompt-selection smoke run |
| q06_exp008_v6c_no_empty_bullet_smoke3 | Qwen3-0.6B | H1 variant v6c_no_empty_bullet (3 spare ids) | extra | 3 | 3 | 0 | prompt-selection smoke run |
| q06_exp008_v6d_minimal_smoke3 | Qwen3-0.6B | H1 variant v6d_minimal (3 spare ids) | extra | 3 | 3 | 0 | prompt-selection smoke run |
| q06_exp008_H1_main30 | Qwen3-0.6B | H1 hybrid (full P02 schema + faithfulness rules, no examples) | core | 30 | 30 | 0 | frozen prompt sha256 dc10ba06... |

Prompt-dev comparison set (every core run except P05): 30 encounters.
Validation comparison set (P05 vs EXP_003 only): 50 encounters; overlap with other runs: {'q06_exp004_P01': 0, 'q06_exp004_P02': 0, 'q06_exp004_P03': 0, 'q06_exp006_S1': 0, 'q06_exp007_S1_1_B1': 0, 'q06_exp007_S1_1_B2': 0, 'q17_P00_direct': 0, 'q17_P01_schema_guided': 0, 'q17_P02': 0, 'q06_exp008_H1_main30': 0}
Problems: none
