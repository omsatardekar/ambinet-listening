# P05 integrated guard, runner changes and file-access spy report (D5 items 5-7, 10)

## 1. What changed (all new files; no existing module or dataset file modified)
| File | Purpose |
|---|---|
| `experiments/dev_guard.py` (extended) | adds `StrictAccessSpy` (stops the run the moment code tries to open a locked-test transcript/label, the sealed hash file, or a validation record without authorisation), `validation_authorized()` (the authorisation must carry the SHA-256 of the current freeze manifest), `AUTH_FILE`, `FREEZE_MANIFEST`; the earlier `build_files`, `verify_ids`, `install`, `locked_test_accesses` are unchanged |
| `experiments/run_p05_validation.py` | the integrated runner: pre-flight (frozen hashes, config, P02 prompt, evaluator, schema, model files, settings), `dev_guard.install(ids)` (replaces `settings.verify_frozen_dataset` and `settings.MANIFEST_CSV` at run time), the whole run under `StrictAccessSpy`, stage 1 through the existing inference loop, stages 2-4, audit file; scopes `smoke_prompt_dev`, `prompt_dev`, `validation` (refused without authorisation); `--dry-run` = no model, no GPU |
| `experiments/p05_pipeline.py`, `p05_eval_lib.py`, `evaluate_p05.py` | stages 2-4 as pure functions; evaluation with separate metrics and the frozen gates; evaluation also runs under the strict spy |
| `experiments/audit_sampler.py`, `audit_score.py`, `record_authorization.py`, `freeze_p05.py`, `make_p05_config.py` | audit packets and scoring; authorisation record; freeze manifest; configuration dump |
**Disclosed defect found and fixed during this work:** the first version of the new spy class had a label-detection regular expression that lost a backslash (it did not match Windows label paths), so its "label files opened" line could not have detected a label read; locked-test blocking was unaffected (path-normalised; negative tests passed). It was fixed, a regression test was added (`label_read_is_detected_by_audit`), the freeze was regenerated, and all final tests below were run on the corrected frozen files. Earlier runs (EXP_001-EXP_004 audits) used `common.FileAccessSpy`, whose regular expression is correct; the draft-freeze checks `integration_checks/P05_dryrun_*` and `P05_final_*` pre-date the fix and are kept for the record.

## 2. File-access spy against the integrated runner (frozen files; `integration_checks/P05_final2_*`)
| Run | Records post-processed | Input transcripts opened | Locked-test files | Sealed hash file | Label files | Validation records | Files opened | Pre-flight |
|---|---|---|---|---|---|---|---|---|
| `smoke_prompt_dev` dry run | 5 | 5 | 0 | False | 0 | 0 | 157 | 10/10 pass |
| `prompt_dev` dry run (50 records) | 50 | 50 | 0 | False | 0 | 0 | 607 | 10/10 pass |
| evaluation of the 50-record dry run | - | 50 | 0 | False | 100 read events (50 development labels, each read counted twice) | 0 | 501 | - |
| `validation` scope without authorisation | 0 | 0 | 0 | False | 0 | 0 | refused at start (exit 3) | not reached |
Compared with the old behaviour (503 files opened including 400 locked-test transcripts at the start of every run), the guarded runner opens only the transcripts of the requested ids. The inference/post-processing phases open **0** label files; the evaluation opens only development labels.
**Negative tests** (`evaluation/strict_spy_negative_tests.json`, all pass = True): a locked-test transcript (read_text and read_bytes), a locked-test label and the sealed hash file were each **stopped with PermissionError before opening**; a validation transcript without authorisation was stopped; approved prompt_dev reads were allowed; the authorised-validation permission rule was checked without opening any validation file; a label read is detected by the audit.
**Evaluation regression on the frozen files:** identical to the development diagnostics (coverage 72.6%; hit when cited 98.6%; hit with abstentions as misses 92.2%; all gates pass on prompt_dev, which is not independent).

## 3. Remaining metadata reads (unchanged and documented)
The one-time derivation of `dev_safeguards/*` read `manifest.csv` (metadata) and the text of `CHECKSUMS.sha256`; the integrated runner redirects `settings.MANIFEST_CSV` to the 100-row development manifest. The previous checksum-only reads of locked-test transcripts and labels (documented in `reports/08_locked_test_access_audit.md`) remain documented as they were; they are not changed or hidden by this work.

## 4. Confirmations
* No inference and no GPU job has started (`--dry-run` instantiates no model; no process is running; no `outputs/P05_*` directory exists).
* No validation record, locked-test record or sealed file was opened by any test above.
* P00-P04, the frozen dataset, schema and evaluator are unchanged (evaluator files byte-identical to the EXP_001 snapshot).
* Freeze manifest SHA-256: `e383d3a352a6e431bc74c49c8c409d15a6e02831b05ee73e47aec472fd56fae0`.
