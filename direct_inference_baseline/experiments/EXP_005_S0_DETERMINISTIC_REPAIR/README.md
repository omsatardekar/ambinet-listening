# EXP_005: S0 deterministic repair (S0.1.0)

Separate experiment folder (no EXP_001-004 file is modified; their outputs are only read). Deterministic Python repair of stored Stage-1 outputs; no model, inference, prompt change or fine-tuning.

| Path | Content |
|---|---|
| `s0/s0_repair.py` | the repair library (rules A-F, log rows) |
| `s0/run_s0_prompt_dev.py` | evaluation on 50 prompt_dev encounters (P02 stage 1 and P05 final v4) under StrictAccessSpy |
| `s0/test_s0_repair.py` | 23 synthetic unit tests |
| `data/original/<source>/`, `data/repaired/<source>/` | byte copies of the inputs and the repaired outputs, side by side (50 files each) |
| `logs/transformations_<source>.jsonl` | every change and flag: encounter, JSON path, original, repaired, rule, reason, deterministic, human review required |
| `results/s0_metrics.json` | all measured numbers and the file-access audit |
| `s0/s0_2_fill_nullable.py`, `s0/run_s0_2_prompt_dev.py`, `s0/test_s0_2.py`, `data/repaired_s0_2/`, `logs/transformations_s0_2_*.jsonl`, `results/s0_2_metrics.json` | S0.2: fill absent nullable fields with null (approved) |
| `reports/S0_EVALUATION_REPORT.md`, `reports/S0_2_EVALUATION_REPORT.md`, `reports/REPORTED_BY_SEMANTICS.md` | evaluations; `reported_by` decision and schema compatibility |
| `recovery/` | investigation record and a hash-verified copy of the missing EXP_004 `P05_validation_50.zip` found in the Recycle Bin |

Run (project OpenVINO environment, any Python 3 works): `python -B s0/test_s0_repair.py`, then `python -B -s s0/run_s0_prompt_dev.py` from this folder.
Scope: prompt_dev ids only. Validation and locked-test records are blocked by `dev_guard.StrictAccessSpy`; the audit in `results/s0_metrics.json` shows 0 such accesses.
