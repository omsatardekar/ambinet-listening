# P02 workspace cleanup report

Date 2026-11-15. Nothing was deleted: obsolete artifacts were moved to `archive/obsolete_experiments_after_P01/` with their original directory structure. The prepared list was checked against the protected P01 / P00 / current-P02 files before any move (dry run), and a SHA-256 inventory taken before the move was compared with one taken after.

## Result

| Check | Result |
|---|---|
| P00 + P01 baseline files (outputs, evaluations, configs, logs, reports, prompts, freeze manifests, runner/analysis scripts, EXP_001 tree) | 318 files: **0 missing, 0 changed** (SHA-256) |
| corrected dataset (inputs + labels + schema), `clinical_extraction_schema.json`, frozen strict matcher `entity_matching.py` | 3096 files: **0 missing, 0 changed** (SHA-256) |
| P02 prompt SHA-256 | before `31c61b484e367b1f4a2d2aceacdcbedbf127646962ddac08c4a2dd7fa9957bbb`, after `31c61b484e367b1f4a2d2aceacdcbedbf127646962ddac08c4a2dd7fa9957bbb` — **identical** (`prompt_versions/P02_v3_p01_schema_no_evidence.txt` → `prompt_versions/P02_p01_schema_no_evidence.txt`, plain rename, bytes unchanged) |
| 30-record manifest | `manifests/P02_v3_30_IDS.json` → `manifests/P02_30_IDS.json`; file SHA-256 identical (`224df72388a537d444adc47763c771d88b78d17ca66e282eb502d223e4202fa1`), same 30 ids in the same order; equal to P01's 30 ids |
| Compiled-model caches (`ov_cache`) | file count and bytes unchanged |
| Static prompt validation (`p02/code/verify_prompt.py`) | 15 of 15 pass (re-run after the move) |
| Unit tests (`p02/code/test_p02.py`) | 7 of 7 pass (re-run after the move) |
| Token counts (`p02/code/count_tokens.py`) | calibration exact on all 30 P01 records; same figures as before the move |
| P01 reproduction through the renamed evaluator path | P 0.283, R 0.156, F1 0.201 (170 TP / 431 FP / 923 FN), identical to before |
| Runner pre-flight with the new names (`FREEZE_P02.json`, `configs/P02_CONFIG.json`) | all checks pass; 0.6B tree identical to its inventory |

## Renamed (active)

| Old | New |
|---|---|
| `p02_v3/` (implementation) | `p02/` (code, derived, schema) |
| `prompt_versions/P02_v3_p01_schema_no_evidence.txt` | `prompt_versions/P02_p01_schema_no_evidence.txt` |
| `manifests/P02_v3_30_IDS.json` | `manifests/P02_30_IDS.json` |
| `reports/P02_v3_STAGE1_AUDIT.md` | `reports/P02_STAGE1_AUDIT.md` |
| `reports/P02_v3_PROMPT_DESIGN_AND_VALIDATION.md` | `reports/P02_PROMPT_DESIGN_AND_VALIDATION.md` |
| run id `P02_v3_dev30` | run id `P02` (`FREEZE_P02.json`, `P02_CONFIG.json`, `outputs/*/P02`) |
| `p02_v3/code/*_v3.py` | `p02/code/{verify_prompt,test_p02,count_tokens,stop_rules}.py`; `backfill_evidence.py`, `analyse_run.py` keep their names |
| `p02_v2_2/code/v22_common.py`, `evaluate_v22.py` | `p02/code/p02_common.py`, `p02_evaluate.py` (copied, imports and path strings edited; logic untouched) |
| `p02_v2_2/code/{evidence_resolver,materialiser,convert_gold}.py` | `p02/code/` same names (copied; imports edited) |
| `p02_v2_2/schema/compact_output_schema_v2_2.json` | `p02/schema/support_schema.json` (byte copy) |

Imports and paths changed in the copied files: the `sys.path` lines (now the file's own directory), `from v22_common` → `from p02_common`, `from evaluate_v22` → `from p02_evaluate`, the support-schema file name, the prompt / run-id / manifest names, and the 'refusing to write outside p02_v2_2/' guard text. Nothing else.

## Archived (moved, structure preserved)

205 files in 25 folders under `archive/obsolete_experiments_after_P01/direct_inference_1_7B/`:

- **Manifests:** freeze manifests of the v2.1 pilot, v2.2 pilot and the pre-rename P02 run; the 6-record and 8-record pilot id lists.
- **Prompts:** `P02_comprehensive_v2_1.txt`, `P02_comprehensive_v2_2.txt`, and the drafts v1 / v2 / v2.1.
- **Configs / logs / outputs / evaluations:** everything of the v2.1 pilot (3 records) and the v2.2 pilot (6 records): raw, parsed and failed outputs, run settings, performance, stop-rule logs, RAM-gate record, template verifications, `run_exit_codes.txt`; the pre-rename P02 config and pre-flight; `PILOT_REFERENCE_METRICS.json` (a pilot-only derivative).
- **Scripts:** the five P02-draft analysis scripts (`gold_schema_conventions.py`, `p02_gate_metrics.py`, `pilot_reference_metrics.py`, `verify_p02_claims_against_gold.py`, `verify_p02_template.py`).
- **Reports:** `P02_COMPREHENSIVE_PROMPT_DRAFT`, the old `P02_EXPERIMENT_PLAN`, `P02_FINAL_REVIEW_CHANGELOG`, `P02_SINGLE_CALL_VS_DECOMPOSED_APPROACH`, `P02_v2_2_PROPOSAL`, `P02_v2_2_STAGE1_VALIDATION`, `P02_v2_2_PILOT_FAILURE_INVESTIGATION`.
- **Packages:** the whole `p02_v2_2/` (compact-schema package: gold converter output, 30 tests, stage-1 validation) and the pre-rename `p02_v3/` (original text of the files now in `p02/`).

The key findings of the archived experiments are preserved in the active `reports/P02_EXPERIMENT_PLAN.md` (section 'Why earlier P02 attempts were archived') and in the project memory; the full documents remain readable in the archive.

## Preserved in place (not moved)

- **P01 and P00:** all of `EXP_001_DIRECT_INFERENCE/`; in `EXP_002_PROMPTING_INFERENCE/`: P01 prompt, config, raw/parsed/failed outputs, evaluations (including `subset30` metrics and `p00_p01_audit`), logs, the five P00/P01 reports, `PILOT_RUNNER_CHANGES.diff` and its test output (documentation of the runner controls P02 uses), and the three P00/P01 analysis scripts.
- **Active P02:** `p02/` (code, derived, schema, README), `prompt_versions/P02_p01_schema_no_evidence.txt`, `manifests/P02_30_IDS.json`, `FREEZE_P02.json`, `configs/P02_CONFIG.json`, and the reports `P02_STAGE1_AUDIT`, `P02_PROMPT_DESIGN_AND_VALIDATION`, `P02_EXPERIMENT_PLAN`.
- **Shared infrastructure:** runner and client scripts in `direct_inference_1_7B/scripts/` (including the archived pre-pilot runner copy), model files and conversion record, the frozen 50-id list, the corrected dataset, the schema, the strict matcher, the `ov_cache` folders, `.venv`, Git history and all source / frontend / backend / wake-word / speech code.
- **Not touched on purpose:** the whole Qwen3-0.6B tree `direct_inference_baseline/` (EXP_001–EXP_007). Its P00–P05 experiments are frozen 0.6B work, not intermediate 1.7B P02 versions, and the 1.7B runner's pre-flight verifies that tree against a frozen inventory (moving it would stop every run). Its own 'P02' names are unrelated to this experiment.

## Notes and warnings

- `manifests/P02_30_IDS.json` keeps its original bytes, so its `purpose` string still says 'P02 v3 30-record run'. I did not edit it, to keep the frozen list byte-identical.
- Two runner-side scripts differ from the P01 freeze hashes: `scripts/run_prompt.py` (your approved D3 change) and `scripts/evaluate_run.py` (last written 2026-11-14 20:48, in an earlier session). Both were already so before this cleanup; neither was touched now.
- The archive is untracked by Git like the rest of `direct_inference_1_7B/`; nothing was committed or pushed.
## Later change (same day)
After the cleanup a 30-record run was started with the then-current prompt and stopped after one record when the prompt was to be strengthened; its artifacts are in `archive/obsolete_experiments_after_P01/_aborted_P02_run_first_prompt/` (and a throwaway pre-flight in `_prompt_load_check_artifacts/`). The prompt SHA-256 quoted above (`31C61B48…`) is the cleanup-time prompt; the active prompt is now the strengthened one (`F6D5202F…`, see `P02_PROMPT_DESIGN_AND_VALIDATION.md`).
