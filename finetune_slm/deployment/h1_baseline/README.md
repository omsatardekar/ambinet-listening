# Azure ML hosting — Qwen3-0.6B (OpenVINO FP16) with the frozen H1 prompt

Replaces the 1.7B deployment. Same protocol (`submit` → `status` → `result`), so the application needs **no code change**: it calls whatever endpoint is in `.env`.

**Status:** the scoring script is built and self-tested offline (no model) and its pipeline was run against the real model locally (see "Verified" at the end). **It has not been deployed to Azure by me** — the Azure steps below are the ones you already did for 1.7B, reused.

## What you upload / reuse
| What | Which | New or reused |
|---|---|---|
| Model files | the 11 files of `direct_inference_baseline/experiments/EXP_002_QWEN3_0.6B_GPU_DIRECT/models/Qwen3-0.6B-ov-fp16/` (1.2 GB, see list below) | **new** model asset |
| Scoring script | `azure_ml_h1/score_single_file.py` (67 KB; rebuild with `python azure_ml_h1/build_single_file_score.py`) | **new** file |
| Environment | `qwen3-ov-py312-scoring:1` (same OpenVINO versions, works for 0.6B) | **reused, do not rebuild** |
| VM | `Standard_D4as_v4`, 1 instance | same as before (0.6B needs about 3 GB RAM) |

The 11 model files (upload them all, no sub-folders needed): `chat_template.jinja`, `config.json`, `generation_config.json`, `openvino_detokenizer.bin`, `openvino_detokenizer.xml`, `openvino_model.bin` (1.19 GB), `openvino_model.xml`, `openvino_tokenizer.bin`, `openvino_tokenizer.xml`, `tokenizer.json`, `tokenizer_config.json`.

## Steps in Azure ML Studio (same screens as for 1.7B)
1. **Stop the 1.7B billing.** Endpoints → `qwen3-p02-extraction` → Deployments → select `qwen3-1-7b-openvino-fp16-1` → **Delete**. Keep the **endpoint**: then its URL and key stay the same and `.env` does not change.
2. **Register the model.** Models → **Register** → *From local files* → model type *Other/Custom* → name `qwen3-0-6b-openvino-fp16` (version 1) → upload the 11 files (or the folder `Qwen3-0.6B-ov-fp16`) → Register.
3. **Add a deployment to the existing endpoint.** Endpoints → `qwen3-p02-extraction` → **Add deployment** (real-time):
   * Model: `qwen3-0-6b-openvino-fp16`, version 1. Deployment name: e.g. `qwen3-0-6b-h1`.
   * Code and environment: customize → **scoring script: upload `azure_ml_h1/score_single_file.py`** → environment: Custom environments → **`qwen3-ov-py312-scoring:1`**.
   * No environment variables (the script defaults to CPU). VM `Standard_D4as_v4`, instance count **1** (jobs are kept in memory).
   * Probes (if shown): initial delay 600 s is more than needed (hashing 1.2 GB takes seconds); 300 s is fine.
   * Create. **Traffic 100 % to the new deployment** (Endpoint → Update traffic) — otherwise the endpoint does not use it.
4. **Test in Studio** (Endpoint → Test): first `{"action":"bogus"}` → expect `{"error": "unknown_action", ...}`; then paste `azure_ml_h1/sample_request.json` → `{"job_id": ..., "state": "queued"}`; then `{"action":"status","job_id":"<ID>"}` until `completed`, then `{"action":"result","job_id":"<ID>"}`. Note the time (CPU speed of the 0.6B model on this VM is **not measured yet**).
5. **In the application:** nothing to change if you kept the endpoint. The panel's "Azure" mode is the default whenever `EXTRACTION_ENDPOINT_URL` and `EXTRACTION_ENDPOINT_KEY` are in `.env`. If you created a **new endpoint** instead, put its REST URL (ends with `/score`) and primary key into those two variables and restart the backend.
6. **When you stop testing, delete the deployment** — the VM bills while it exists.

## The next (fine-tuned) version
Register the new model files as a new model asset/version, build a new scoring file, add a deployment as above and switch traffic. In `score.py` two constants pin what is allowed to run: `EXPECTED_WEIGHTS_SHA256` (hash of `openvino_model.bin`) and `EXPECTED_PROMPT_SHA256` (hash of the prompt file in the bundle). For a fine-tuned model change them to the new hashes (and `H1_PROMPT` in `build_single_file_score.py` if the prompt changes), then rebuild `score_single_file.py`. The protocol and the application stay the same.

## Known limits
* CPU, not the Intel GPU of the experiments: outputs can differ slightly from the EXP_008 numbers; speed on the VM is unmeasured.
* Jobs live in memory of one instance: a restart or redeploy loses a running job.
* A request is cut at 180 s by Azure, hence the submit/status/result protocol.
* The H1 prompt does not ask for transcript segment ids, so facts carry no citations.

## Files
`score.py` (scoring script) · `build_single_file_score.py` (assembles `code_bundle/` and writes `score_single_file.py`) · `selftest_score.py` (offline test) · `sample_request.json` (4-turn synthetic request).
