# dataset_v2_batch_001_corrected

Corrected version of Batch 001 (500 synthetic encounters, paired Module-2 transcripts and ground-truth extractions). The original
`../dataset_v2_batch_001/` is unchanged and is the source this was derived from. Start with `reports/DATASET_QUALITY_AUDIT.md`.

* `output/inputs`, `output/labels`: 500 + 500 JSON files, `manifest.csv`, `stats.json`, `CHECKSUMS.sha256`
* `scenario_blueprints/`: internal generation facts (not evaluation data)
* `validation/`: `validation_report.json`, `evidence_validation.json`, `duplicate_report.json`, `schema_validation.json`,
  `clinical_consistency_report.json`, `dialogue_realism_report.json`, `negative_controls.json`, `quality_log.txt`
* `schema/final_label_schema.json`: FINAL schema (enums with definitions, key sets, reference rules); `reports/FINAL_SCHEMA.md` is generated from it
* `reports/`: audit, changelog, remaining limitations, `record_changes.csv`, `comparison.json`, `human_review_required.csv`, before/after metrics
* `scripts/`: generator, validator driver, negative-control self-test, comparison and audit-metrics tools

All validation is automated. No clinician reviewed any record. Confidence fields are `null`. `confirmed_by` is not used.
Evaluation use only; do not use for fine-tuning.

```
python scripts/generate_batch.py                    # deterministic regeneration (same slots/ids as the original)
python scripts/validate_batch.py --dataset-checks
python scripts/validator_selftest.py                # 22 negative controls
python scripts/compare_with_original.py
python scripts/final_schema_audit.py            # final schema audit (read-only)
python scripts/make_final_manifest.py --verify  # frozen-manifest check (corrected + original)
```

**Batch 002 (added later):** `batch_002/` holds 500 further synthetic encounters (ids 20001-20500) with their own outputs, validation, manifest and README; this Batch 001 content above is unchanged. Start with `batch_002/README.md`.
