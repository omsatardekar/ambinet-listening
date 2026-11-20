# clinical_extraction — Module 3: clinical extraction (Qwen3-0.6B + frozen H1 prompt)

Additive module. It does not change wake-word, transcription, the backend venv or any frozen experiment file.

```
Blob  {NN}slm_input.json (SLM container) ──► job (persisted) ──► model  ──► extraction_raw.json + metadata.json (+ evidence.json)
                                                                  │                         │
                                      Azure ML endpoint (default) or                 frontend panel  ◄── /api/extraction/*
                                      local OpenVINO (h1_worker.py)                         │
                                                                         Blob  {NN}extraction.json  (container AZURE_STORAGE_EXTRACTION_CONTAINER, created automatically)
```

**Which model runs is decided by configuration:**
* **Azure endpoint (default)** whenever `EXTRACTION_ENDPOINT_URL` and `EXTRACTION_ENDPOINT_KEY` are set in `.env`. Hosting the 0.6B model there: see `azure_ml_h1/README.md`. Replacing the model later (for example by a fine-tuned one) only needs a new endpoint URL/key, or just a new deployment on the same endpoint, because the request protocol (`submit` / `status` / `result`) stays the same.
* **Local** (Qwen3-0.6B on this computer) when no endpoint is configured, or when `EXTRACTION_BACKEND=local`. Useful without Azure, but it needs about 3.5 GiB of free RAM per job (the panel shows an "insufficient memory" error otherwise).

## Local model: setup on a new machine (only needed for the local option)
Prerequisites: Python 3.10–3.13 (3.12 tested), [Git LFS](https://git-lfs.com) if the folder comes from GitHub, ~4 GB free RAM while a job runs, and an `.env` with the storage settings (copy `.env.example`).
```powershell
# 1. backend + frontend as usual
python -m venv .venv ; .venv\Scripts\python -m pip install -r requirements.txt          # Linux/macOS: .venv/bin/python
cd frontend ; npm install ; cd ..
# 2. the local model (one command; creates .venv-extraction, installs OpenVINO, fetches the weights via Git LFS, verifies hashes)
python -m clinical_extraction.setup_local_model
# 3. start the backend as before; the panel now runs the model on this machine
```
Nothing needs to be configured afterwards: the backend finds `.venv-extraction` by itself. Check at any time: `GET /api/extraction/health` (`"ready": true`) or `python -m clinical_extraction.cli check`.

* **Device:** GPU if OpenVINO sees one (Intel GPU: what every EXP_008 number was measured on), otherwise CPU, which works but is slower. Force with `EXTRACTION_DEVICE=CPU|GPU`.
* **Memory:** a job does not start below 3.5 GiB of available RAM (`EXTRACTION_H1_MIN_AVAILABLE_RAM_GIB`); the 0.6B model peaks at about 3.1 GB.
* **Model weights:** `direct_inference_baseline/experiments/EXP_002_QWEN3_0.6B_GPU_DIRECT/models/Qwen3-0.6B-ov-fp16/` (1.2 GB, Git LFS). If the folder was shared as a zip, the weights are already inside; if only pointer files arrived, run `git lfs pull`.
* The first run on a device compiles the model (cached in `extraction_data/ov_cache`), so it is slower than later runs.

## What is frozen (checked by the worker before any model is loaded)
* Prompt `direct_inference_baseline/experiments/EXP_008_QWEN3_0.6B_HYBRID_P02_S1/prompts/H1_hybrid_prompt.txt`, SHA-256 `dc10ba065c9f1acaa237d106bd97b451ddfe1efcd94117b727d6585511f79cd8` (`config/H1_FREEZE.json`).
* Model files: sizes and the SHA-256 of `openvino_model.bin` against `EXP_002_.../conversion_record.json`.
* Generation: greedy, thinking off, `max_new_tokens` 6144, a fresh pipeline per encounter — identical to the EXP_008 run. The model output is parsed with the existing parser and checked with the existing schema validator; it is never repaired or rewritten.

## What to expect (measured, EXP_008, 30 synthetic encounters)
* 30/30 outputs parsed, none cut off; about 225 s per encounter (median) on the Intel GPU.
* Quality is a draft: judge-F1 0.352 against the gpt-5.4 judge, with missed history sections and some invented items. Every result is shown as an unvalidated draft for clinician review.
* The H1 prompt does not ask for transcript segment ids (the 0.6B model cannot cite reliably), so `evidence_ids` stay empty. Instead the backend matches each fact's content words against the transcript (`evidence.match_segments`, top 3 segments, score >= 50%) and the panel shows them as **"matched by the backend (not cited by the model)"** with the match score; a fact with no similar segment is shown as such. The raw model output is never changed. The matches are saved in `evidence.json` and in the `{NN}extraction.json` blob.
* Schema warnings are expected on some outputs (for example a section written as one object instead of a list) and are listed on the job, not hidden.

## Files
| file | role |
|---|---|
| `h1_worker.py` | the local inference process (runs in the OpenVINO environment) |
| `setup_local_model.py` | one-command setup for a new machine |
| `service.py`, `api.py`, `job_store.py` | job queue, states, REST + server-sent events (`/api/extraction/*`) |
| `blob_source.py`, `blob_sink.py` | read `{NN}slm_input.json`, save `{NN}extraction.json` |
| `evidence.py` | resolves model-cited segment ids (empty for H1, used by the Azure P02 option) |
| `remote_client.py` | optional Azure ML endpoint client (`EXTRACTION_BACKEND=azure`) |
| `inference_worker.py` | the earlier frozen 1.7B P02 worker; kept for the record, no longer started by the service |
| `requirements-extraction.txt` | packages of the separate OpenVINO environment |

## Tests and one-off runs
```powershell
.venv\Scripts\python -m pytest clinical_extraction/tests -q                      # no model, no Azure
.venv\Scripts\python -m clinical_extraction.cli run --compact <compact.json>      # ONE encounter through the same service code, no web server
```

## API
`POST /api/extraction/start {"run_id"|"encounter_id"}`, `GET /api/extraction/{job}/status|events|result|evidence`, `GET /api/extraction/health`.
Registration (the only change to an existing backend file): `register_extraction_routes(app, run_result=progress_manager.result)` in `backend/app/main.py`.
