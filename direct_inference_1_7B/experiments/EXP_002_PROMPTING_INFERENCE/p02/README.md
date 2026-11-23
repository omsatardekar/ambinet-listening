# p02 — implementation of the P02 experiment

Standard library only (plus `tokenizers` for `count_tokens.py`); no model is loaded by any file here. Run with `python -B -I <file>` from `p02/code/`.

| File | Purpose |
|---|---|
| `code/backfill_evidence.py` | segment ids in `evidence_ids` → `clinical_evidence` records + `EV_nnn` ids; invalid ids flagged, never repaired |
| `code/evidence_resolver.py` | the resolver it reuses: exact segment lookup → text, speaker id, role, MM:SS times |
| `code/p02_evaluate.py` | independent evaluator around the frozen strict matcher (`--format full` for P01/P02 outputs) |
| `code/analyse_run.py` | category-level, partial-extraction, speaker-attribution and fuzzy-diagnostic analysis of one run |
| `code/verify_prompt.py` | static prompt validation against the P01 prompt (template keys/order, enums, leak checks) |
| `code/prompt_review_synthetic.py` | prompt-only review on an invented consultation: reference output must pass, 10 wrong variants must be caught (no model) |
| `code/test_p02.py` | 7 unit/integration tests of the backfill (gold round trip on all 50 dev records) |
| `code/count_tokens.py` | exact input-token counts, tokenizer file only |
| `code/stop_rules.py` | the fixed early-stop watcher for the run |
| `code/p02_common.py`, `code/convert_gold.py`, `code/materialiser.py` | shared helpers (dev-id access guard, frozen schema access, gold↔evidence-segment map); `materialiser.py` and `schema/support_schema.json` come from the archived compact-format work and are kept only because the evaluator and helpers import them; the P02 output is NOT compact |
| `derived/` | validation and analysis results (JSON, test output) |

The runner is `direct_inference_1_7B/scripts/run_prompt.py` (unchanged). Prompt: `prompt_versions/P02_p01_schema_no_evidence.txt`. Ids: `manifests/P02_30_IDS.json`.
