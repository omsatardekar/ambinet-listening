# Stage 3 - Qwen3-0.6B direct inference baseline

Independent module. It reads the frozen `dataset_v2_batch_001_corrected/` (transcripts for inference, labels only for evaluation),
the root `.env` and the root `.venv`. It modifies nothing outside this folder (the only root change is three appended `.env`
variables: `INFERENCE_PROVIDER`, `HF_MODEL_ID`, `HF_DEVICE`). No fine-tuning, LoRA, RAG, prompt optimisation or pipeline integration.

## Scope and honest status
* Provider in use: **local Hugging Face `Qwen/Qwen3-0.6B`, CPU, float32, greedy decoding, non-thinking mode** (`enable_thinking=False`).
  Qwen recommends sampling (T 0.7, top_p 0.8, top_k 20) for non-thinking mode; greedy is used for reproducibility. temperature/top_p/top_k are
  therefore recorded as not applied.
* The Foundry client (`inference/foundry_client.py`) is implemented and unit-tested with a mocked session, but the configured Foundry project
  has no Qwen3-0.6B deployment (only `gpt-5.5`), so it is **not used**. Structured-JSON mode for a future Qwen deployment is unverified (off by default).
* Output format = the complete finalized schema (`clinical_extraction_schema.json`, reconciled with `dataset_v2_batch_001_corrected/schema/final_label_schema.json`
  for the categories the root example leaves empty and for enum values; reconciliation is asserted at import time). Neither file is modified.
  Known differences between the root *example* and the frozen labels: `supports` uses locations (`symptoms[0]`), speaker ids are `person_N`, confidence is `null`.

## Method
* **Split** (`evaluation/dataset_split.py`): 100 development / 400 locked test, stratified by specialty x complexity (largest-remainder allocation, seed 20260301). IDs in `data/splits/`.
  Development = pipeline checks only; the test set is never used to change the prompt.
* **Prompt**: `prompts/direct_extraction_prompt.txt` (fixed; sha256 recorded per run). Input = instruction + transcript lines `[SEG0001] person_1 (DOCTOR) 0.80-3.28s: text`.
* **Output handling** (`inference/output_parser.py`): only a `<think>` block and a surrounding ``` fence are removed. Nothing is repaired or completed. Outcomes:
  `ok`, `truncated` (generation hit the token budget and JSON does not parse), `invalid_json`, `empty`, `not_object`. Failures are saved to `outputs/failed_predictions/`; they are never replaced by empty JSON.
  Raw responses are saved in `outputs/raw_predictions/`, parsed JSON objects in `outputs/parsed_predictions/`.
* **Retries**: bounded exponential backoff for transient errors (rate limit, 5xx, timeout, out-of-memory). A truncated answer is not retried (greedy decoding would repeat it).
* **Leakage guards** (tests): inference code never references the label directory, the runner never opens label or blueprint files, the prompt equals instruction + transcript exactly.

## Metrics (all definitions are also embedded in each report)
* **Entity matching (strict)**: normalised primary key per category (symptoms `normalized_name`, negative findings `normalized_name`, medications `normalized_name`
  (or `name` when null), allergies `normalized_substance`, medical history `normalized_condition` / `normalized_procedure` / social `category`, vitals / procedures `normalized_name`,
  actions `action_type|normalised description`, follow-up `type|time_reference`, uncertainties `type`, chief complaint `normalized_value`, etc.). Multiset TP/FP/FN; micro and macro (over categories with a defined F1).
  Normalisation: NFKC, lowercase, British->American spelling, unit words -> symbols, approved abbreviations (ecg, bp, spo2, cbc, mri, copd, gerd, uti), punctuation removed (decimals kept), articles dropped. No stemming or synonym mapping.
* **Fuzzy matching** (token Jaccard >= 0.75 or difflib ratio >= 0.85 on still-unmatched entities) is reported separately and never mixed into strict scores.
* **Undefined values**: precision/recall/F1 are `null` when the denominator is 0 (never 0 or 1).
* **Two views**: `end_to_end` (an encounter without a usable prediction counts all its gold entities as FN) and `valid_only`. Coverage and failure rate are shown with both.
* **Attributes** (on matched entities only; do not change entity counts): accuracy over gold non-null values and, separately, the rate of invented values where gold is null.
* **Clinical**: symptom / negative-finding / medication / allergy F1 (per-category rows), medical history (4 sub-categories, also pooled), vital-sign accuracy (name+value+unit), temporality accuracy,
  negation polarity flips, speaker attribution (excludes records with an UNKNOWN speaker and entities with unreliable roles; denominator reported),
  evidence grounding (grounded strict / lenient / partially supported / unsupported against real transcript segments), unsupported-claim rate (strict FPs lexically unsupported anywhere in the transcript; FNs are never hallucinations).
* **JSON/schema**: JSON validity, truncated vs malformed, schema compliance (zero structural violations), required-field completeness, unexpected-field rate.
* Everything is lexical/normalised matching to the labels, not a clinical-quality judgement.

## Commands (Windows PowerShell, from the project root)
```powershell
.\.venv\Scripts\Activate.ps1                                  # 1 activate the existing environment
python direct_inference_baseline\cli.py check-config          # 2 configuration (no secrets printed)
python direct_inference_baseline\cli.py verify-frozen         #   frozen dataset checksums
python direct_inference_baseline\cli.py verify-connectivity   # 3 loads Qwen3-0.6B locally and generates a few tokens
python direct_inference_baseline\cli.py split                 # 4 create/verify the 100/400 split
python direct_inference_baseline\cli.py smoke --split development --limit 1 --max-new-tokens 6144    # 5 development smoke test
python direct_inference_baseline\cli.py run --split test --i-approve-locked-test                      # 6 locked test inference (ONLY after approval)
python direct_inference_baseline\cli.py evaluate --experiment-id <id>                                 # 7+8 evaluation + reports
python -m pytest direct_inference_baseline\tests -p no:cacheprovider -q                               # unit tests
```
Reports: `outputs/reports/<experiment_id>/` (`run_manifest.json`, `evaluation_report.json`, `evaluation_report.md`, `per_encounter_results.jsonl`, `confusion_matrices.json`).
Optional environment variable `HF_NUM_THREADS` sets the CPU thread count.
