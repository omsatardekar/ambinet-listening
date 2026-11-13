# Locked-test access audit (accurate record of what earlier steps read)

Purpose: you asked for the checksum-only reads to be documented accurately and for future development runs to avoid them. Facts below come from the code, the run manifests and measured audits (not from memory). Nothing in the frozen dataset was modified.

## 1. Locked-test material: definition
400 of the 500 encounters (ids in `data/splits/test_ids.json`). Their transcripts are `output/inputs/encounter_<id>.json`, their labels `output/labels/encounter_<id>.json`. The dataset's `CHECKSUMS.sha256` lists 1,001 files: 500 transcripts, 500 labels, `manifest.csv`.

## 2. What was read, by mechanism
| Mechanism | Where | What it reads | Locked-test files touched |
|---|---|---|---|
| `verify_frozen_dataset(inputs_only=True)` at the start of every `run_inference` call | `inference/inference_runner.py` line 63; every main inference run: EXP_001 main run, all EXP_003 runs (5-record smoke, remaining 95, reproducibility), EXP_004 runs P00_repro3, P01, P02, P03 (partial) and the P04 smoke test | SHA-256 of all 500 transcripts and `manifest.csv` (run manifests record `frozen_files_verified: 501`) | **400 transcripts, hash only** (measured: 500 transcripts opened, 400 locked-test, 0 labels; `evaluation/frozen_dataset_hash_access_audit.json`) |
| full `verify_frozen_dataset()` | one EXP_001 supplementary probe run (manifest records `frozen_files_verified: 1001`); EXP_003 `scripts/evaluate.py` and `combine_and_evaluate_dev100.py` (`evaluation/frozen_dataset_verification_after_run.json` and `..._after_dev100.json`, both `files_checked: 1001`); `cli.py verify-frozen` and `tests/test_split_and_frozen.py` when invoked | SHA-256 of all 500 transcripts, all 500 labels, `manifest.csv` | **400 transcripts and 400 labels, hash only** |
| `manifest.csv` / split files | split creation; every evaluation (`evaluation_runner.evaluate_experiment` reads the manifest for specialty/complexity breakdowns); `load_split` | per-encounter metadata (specialty, complexity, duration, speaker count and roles, file paths, validation status) for all 500 encounters; id lists | metadata rows of locked-test encounters; no transcript or label content |
| evaluation and analysis code | evaluator, EXP_004 scripts | gold labels and transcripts of **development ids only** (EXP_004 scripts assert `ids ⊆ prompt_dev` and not in test) | none |

## 3. What this does and does not mean
* Bytes of locked-test transcripts (every run) and labels (the full integrity checks listed above) were read to compute SHA-256 values. The content was not parsed, rendered into a prompt, analysed, evaluated, used for tuning, or shown. No locked-test label content has been used by any experiment, and no encounter outside the development ids has ever been scored.
* My earlier statements that the locked test set was "untouched" are accurate in that sense but incomplete: the checksum reads above happened, including hash reads of locked-test **labels** in the EXP_003 post-run integrity checks and the EXP_001 supplementary probe. I should have stated this earlier. The first time I measured it was in the P04 smoke audit.
* Metadata (specialty, complexity, duration, speaker counts) of locked-test encounters has been read via `manifest.csv`; the development split itself was stratified from this metadata (seed 20260301).
* I cannot change the existing module without violating your restriction; so the safeguard is a run-time redirect.

## 4. Safeguard for future development experiments (built; tested without any model)
`experiments/dev_guard.py` (proposed; no runner has adopted it yet):
* Hashes only the explicitly requested approved ids (prompt_dev by default; validation only with an explicit flag), inputs only unless labels are requested.
* Locked-test hashes live in a separate sealed file, `dev_safeguards/locked_test_checksums.SEALED.sha256` (derived from the text of `CHECKSUMS.sha256`, without opening any test file); development code never loads it. `dev_safeguards/dev_checksums.sha256` holds the 100 development transcripts' and labels' hashes, `dev_manifest.csv` the 100 development manifest rows.
* Replaces `settings.verify_frozen_dataset` and `settings.MANIFEST_CSV` at run time (same pattern as `common.use_run`); nothing is written to the dataset or the existing module.
* `locked_test_accesses(opened_paths)` is the assertion helper for the file-access audit of every future run.
**Test result** (`evaluation/dev_guard_test.json`, all pass): existing check opened 503 files, 400 of them locked-test transcripts; guarded check hashed 5 requested transcripts and opened 7 files in total, 0 locked-test files, 0 labels, sealed file not opened; a tampered hash was detected; a non-approved id and a validation id (without the flag) were rejected.
Remaining unavoidable metadata read: the one-time derivation of `dev_manifest.csv` and `dev_checksums.sha256` reads `manifest.csv` and the text of `CHECKSUMS.sha256` (metadata and hash lists, not records).

## 5. Rules for future development runs
1. Install the guard before inference; assert `locked_test_accesses(spy.opened) == []` and 0 label files in the run's audit file.
2. Never call the full `verify_frozen_dataset()` or the EXP_003 evaluate scripts' integrity step during development; full verification (which hashes locked-test labels) happens only at an approved final stage, by a separate script, and is recorded.
3. Keep locked-test hashes and manifests in the sealed file; do not copy locked-test metadata into development artifacts.
4. Do not alter the frozen dataset.
