# Ambient Clinical Listening

Talk to your patient — Ambient Clinical listens, writes the **transcript**, picks out the **clinical entities** with a small language model, and prepares the **SOAP note** with an agent.

This repository contains the whole pipeline: hands-free capture → speaker-aware transcript → clinical extraction → SOAP note, together with every experiment, dataset and evaluation that led to the extraction model. See [The pipeline](#the-pipeline) and [Setting up modules 3 and 4](#setting-up-modules-3-and-4).

- **Hands-free recording ("Asha").** Say **"Hey Asha"**, then **"Start recording"**. Say **"Hey Asha, stop recording"** to save. Recordings are saved as WAV files on your machine and are never uploaded.
- **Upload.** Upload a WAV recording and create the transcript.
- **A modern, responsive interface** with a Siri-style voice overlay, live progress, and a chat-style transcript.

> **Clinical safety:** This is a demonstration. Transcripts are drafts that a qualified clinician must review. Do not use real patient data unless your organisation has approved the environment and data handling.

## Versions

| Tag | What it is |
|---|---|
| `v1.0` | First release (Whisper-based voice control, original interface). |
| `v2.0` | Fast, strict offline voice control (about 0.25 s reaction time, commands trimmed from recordings). |
| `v3.0` | **Current.** Completely redesigned interface (dark glass theme, animations, responsive) plus a full setup guide. |

Switch between them with `git checkout v1.0`, `git checkout v2.0`, `git checkout v3.0`, and `git checkout main` for the latest.

---

# Setup from zero (Windows 10/11)

Follow these steps in order on a fresh machine. Everything is copy-paste.

## Step 1 — Install the tools

Install each of these once. After installing, **close and reopen PowerShell** so the new tools are found.

| Tool | Version | Download | Important |
|---|---|---|---|
| Git | any recent | https://git-scm.com/download/win | Keep the default options. |
| Python | **3.12** (3.11 also works) | https://www.python.org/downloads/ | **Tick "Add python.exe to PATH"** on the first installer screen. |
| Node.js | **18 LTS or newer** (20/22 LTS recommended) | https://nodejs.org | Includes `npm`. |
| Google Chrome or Microsoft Edge | recent | — | Needed for microphone access. |

You also need:

- A working **microphone** (built-in or USB), not muted in Windows Sound settings.
- **Internet** for installing packages and for the project's cloud services (the voice model is included in the repository).
- The **`.env` values** for the project's cloud resources. Ask the project owner for them (Step 5).

Check the installs (each should print a version):

```powershell
git --version
python --version
node --version
npm --version
```

## Step 2 — Allow PowerShell scripts (one time)

The launcher is a PowerShell script. Run this once so Windows lets you run it:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

## Step 3 — Get the code

```powershell
git clone https://github.com/omsatardekar/ambinet-listening.git
cd ambinet-listening
```

## Step 4 — Create the Python environment

The launcher expects the virtual environment to be named `.venv` inside the project folder.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

Your prompt should now start with `(.venv)`. (If `python` is not found, reinstall Python with "Add to PATH" ticked.)

## Step 5 — Add your configuration

```powershell
Copy-Item .env.example .env
notepad .env
```

Paste in the values the project owner gave you (storage, speech and agent settings), save, and close. `.env.example` lists every setting; empty optional ones use sensible defaults.

**Never commit `.env`** — it is already in `.gitignore`.

## Step 6 — Install the frontend packages

(The launcher does this automatically on first run; doing it now makes the first start faster.)

```powershell
cd frontend
npm install
cd ..
```

## Step 7 — Run it

From the project folder, with `(.venv)` active:

```powershell
.\start_demo.ps1
```

The launcher checks the Python packages, starts the backend at **http://127.0.0.1:8000** and the interface at **http://127.0.0.1:5173**, then opens your browser. Press **Ctrl+C** in the terminal to stop both.

**Voice model:** the voice model is already included in this repository (`models/vosk-model-small-en-in-0.4`), so nothing is downloaded and it works behind company firewalls and SSL-inspecting proxies. It is loaded once when the server starts. Wait until the terminal prints **`Voice control is ready`**.

When the browser asks for the **microphone**, click **Allow**.

### Running the two services by hand (macOS / Linux, or without the launcher)

```bash
# Terminal 1 — backend (from the project root, venv active)
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

# Terminal 2 — interface
cd frontend
npm install
npx vite --host 127.0.0.1 --port 5173
```

---

# Using the app

## Hands-free recording

1. The header shows that Asha is listening once the microphone is live.
2. Say **"Hey Asha"**. A glowing card appears — *"Asha is listening"* — and waits up to 10 seconds for your command.
3. Say **"Start recording"**. The card turns to recording mode with a timer and a wave that follows your voice.
4. Say **"Hey Asha, stop recording"** (or press **Stop and save**). The recording is saved and you can play it straight away.
5. Open **Recordings** (bottom right) to see every saved file. Files are stored in `offline_recordings/`.

Rules Asha follows:

- She only wakes on **"Hey Asha"**.
- **"Start recording"** only works right after "Hey Asha". Said on its own it is ignored.
- **"Stop recording"** only works together with "Hey Asha".
- The words of the commands themselves are **not** included in the saved recording.
- You can say it in one breath: "Hey Asha, start recording".

## Upload a recording

Drop a WAV file into the upload card (or browse for one), choose a transcription style, and press **Create transcript**. Live progress appears below, followed by the conversation transcript.

---

# Check that it works

- Open **http://127.0.0.1:8000/api/health**. `azure_configured` should be `true` and `wake_word.available` should be `true` once the voice model has loaded.
- Run the tests (from the project root, venv active):

  ```powershell
  $env:PYTHONPATH = "$PWD\scripts"
  python -m pytest -q tests
  ```

---

# Troubleshooting

| Symptom | What to check |
|---|---|
| `running scripts is disabled on this system` | Run the command in Step 2, then try again. |
| `python` / `node` / `git` not found | Install it (Step 1) and **open a new PowerShell window**. |
| Launcher says the virtual environment was not found | Make sure the folder is named exactly `.venv` in the project root (Step 4). |
| Header says Asha is getting ready for a long time | Wait for "Voice control is ready" in the terminal. Make sure the `models/vosk-model-small-en-in-0.4` folder exists and is complete (re-clone or `git checkout -- models` if not). |
| "Microphone blocked" | Click the lock icon in the address bar, allow the microphone for `127.0.0.1:5173`, reload. |
| "Waiting for microphone", or a silent-input warning | Choose the right input device in Windows Sound settings and check its level. |
| "Hey Asha" is not recognised | The header shows what was last heard. Speak clearly at normal volume, close to the microphone, and pause briefly after each phrase. |
| Upload says transcription is unavailable | Check `.env` and `http://127.0.0.1:8000/api/health`. |
| Port 8000 or 5173 already in use | Close the other program, or stop the earlier run with Ctrl+C. |
| Blank or old interface after updating | Run `npm install` in `frontend/`, then hard-refresh the browser (Ctrl+Shift+R). |

---

# The pipeline

```text
Module 1  Hands-free capture ("Hey Asha")                      ->  WAV on this machine
Module 2  Transcription (Azure Speech) + reconstruction (Foundry agent)
                                                                ->  {NN}final_transcript.json, {NN}slm_input.json   (Azure Blob)
Module 3  Clinical extraction: Qwen3-0.6B with the frozen H1 prompt, hosted on Azure ML
                                                                ->  extraction-output / {NN}extraction.json
Module 4  SOAP note: a Foundry prompt agent, from the extraction output only
                                                                ->  soap-output / {NN}soap.json and {NN}soap.md
```

| Module | Code | Panel in the app |
|---|---|---|
| 1 and 2 | `backend/app/`, `scripts/`, `frontend/src/VoiceAssistant.tsx`, `prompts/agent_instructions_v2.md` | recording, upload, transcript |
| 3 | `clinical_extraction/` (own README), `azure_ml_h1/` (hosting package), `frontend/src/ExtractionPanel.tsx` | **Clinical summary** |
| 4 | `soap_generation/` (own README), `prompts/soap_agent_instructions_v1.md`, `scripts/generate_soap.py`, `scripts/create_soap_agent.py`, `frontend/src/SoapPanel.tsx` | **SOAP note** |

The extraction model is meant to be replaced by a fine-tuned one: only `EXTRACTION_ENDPOINT_URL` and `EXTRACTION_ENDPOINT_KEY` change. The SOAP step reads the saved extraction and nothing else, so its quality follows the extraction model's quality.

---

# Setting up modules 3 and 4

Do this after modules 1 and 2 work on the machine (Steps 1 to 7 above).

1. **Git LFS (once per machine), before cloning or pulling.** The OpenVINO model files and the generated test recordings are stored with Git LFS.
   ```powershell
   git lfs install
   git pull
   git lfs pull
   ```
2. **New Python packages** (the reconstruction stage and the SOAP step use the Foundry agent SDK):
   ```powershell
   python -m pip install -r requirements-dev.txt
   cd frontend; npm install; cd ..
   ```
3. **Sign in to Azure** (the Foundry agents use your Azure CLI sign-in): `az login`.
4. **Settings in `.env`** (copy any missing names from `.env.example`; ask the project owner for the values):

   | Setting | Meaning |
   |---|---|
   | `EXTRACTION_ENDPOINT_URL`, `EXTRACTION_ENDPOINT_KEY` | the hosted extraction model (Azure ML endpoint). Leave empty to use the local model instead (see `clinical_extraction/README.md`) |
   | `AZURE_STORAGE_EXTRACTION_CONTAINER` | container for the extraction JSON (`extraction-output`, created automatically) |
   | `AZURE_STORAGE_SOAP_CONTAINER` | container for the SOAP notes (`soap-output`, created automatically) |
   | `SOAP_BACKEND=agent`, `SOAP_AGENT_NAME=clinical-soap-note`, `SOAP_AGENT_VERSION=<n>` | the SOAP agent. It already exists in the Foundry project; use the version the owner gives you |
   | `SOAP_INCLUDE_TRANSCRIPT=0` | keep `0`: the SOAP step works from the extraction output only |

   Only if you use a **different Foundry project**: create the agent there once with `python scripts/create_soap_agent.py --model <deployment name> --update-env`, which also writes the version into `.env`. After editing `prompts/soap_agent_instructions_v1.md`, run it again and restart the backend.
5. **Run:** `.\start_demo.ps1`. In the app: record or upload a conversation, wait for the transcript, press **Generate summary** (clinical summary), then **Generate SOAP note**.
6. **Check:** `http://127.0.0.1:8000/api/extraction/health` and `http://127.0.0.1:8000/api/soap/health` should both report `"ready": true`.
7. **Tests (no Azure needed):**
   ```powershell
   python -m pytest -q clinical_extraction/tests soap_generation/tests
   cd frontend; npx tsc --noEmit
   ```

**Test recordings.** `scenarios/` holds 20 hand-written consultations and `output/` the 20 generated recordings (about 11 minutes each, synthetic speech). Upload them in the app to exercise the whole pipeline; `scenarios/README.md` explains how to generate more with `scripts/ambient_tts.py`.

---

# Experiments and evaluation (everything is in this repository)

| Folder | What it holds |
|---|---|
| `direct_inference_baseline/` | Qwen3-0.6B experiments EXP_001 to EXP_008 (CPU baseline, GPU, OpenVINO, prompt engineering, repair, simplified extraction, the hybrid prompt H1 that is deployed), code, outputs, reports, logs. The 0.6B OpenVINO model (1.2 GB) is in Git LFS |
| `direct_inference_1_7B/` | Qwen3-1.7B track (P00, P01, P02): scripts, manifests, prompts, evaluations, reports. The 3.4 GB weights file is not in Git, see below |
| `judge_eval/` | the LLM-as-judge evaluation of all runs (`METHODOLOGY.md`, `REPORT.md`, results) |
| `dataset_v2_batch_001_corrected/`, `dataset_v2_batch_001/` | the synthetic encounters (Batch 001 and Batch 002, 500 each) with paired transcripts and ground-truth labels, validation reports |
| `azure_ml_h1/` | how the 0.6B model is hosted on Azure ML (scoring script, environment, step-by-step guide) |
| `docs/MODULE3_FINETUNING_FOCUS.md` | the failure classes seen in six live runs, what the fine-tuning has to cover, and the checks to measure it |
| `PROJECT_DOCUMENTATION_AND_PRESENTATION/` | the master experiment report, fine-tuning roadmap and the metrics comparison table (CSV) |
| `archive/` | obsolete experiments, kept for the record |

---

# What is not in Git

| Item | Why | What to do |
|---|---|---|
| `.env` | secrets | copy `.env.example` and ask the project owner for the values |
| `.venv`, `.venv-extraction`, `.../env_openvino` | virtual environments | create them (Step 4; `python -m clinical_extraction.setup_local_model` for the local extraction environment) |
| `direct_inference_1_7B/models/Qwen3-1.7B-ov-fp16/openvino_model.bin` | 3.4 GB, over GitHub's 2 GiB Git LFS limit | recreate with `direct_inference_1_7B/scripts/convert_model.py` (see `direct_inference_1_7B/OMITTED_FROM_GIT.json` for the checksum) or copy it over from the original machine. Only needed to re-run the 1.7B experiments |
| `**/ov_cache`, `direct_inference_1_7B/models/hf_cache` | machine-specific compile caches and a model download | regenerated automatically or by `scripts/download_model.py` |
| `.tts_cache/` | cache of synthesized speech | regenerated by `scripts/ambient_tts.py` |
| `extraction_data/`, `soap_data/`, `offline_recordings/` | local job data and your own recordings (patient-related) | created at run time |
| `office_transfer_package/` and `*.zip` | not needed on other machines | none |

---

# Project layout

```text
backend/app/              FastAPI server: API, WebSocket voice channel, voice control, pipeline; registers the /api/extraction and /api/soap routes
frontend/src/            React + Vite interface (App.tsx, VoiceAssistant.tsx, ExtractionPanel.tsx + extraction/, SoapPanel.tsx + soap/)
models/                   Offline voice models, included in the repository (no download needed)
offline_recordings/       Your saved recordings (git-ignored, may contain sensitive audio)
scripts/                  Transcription, reconstruction, test-speech generation (ambient_tts.py), SOAP command-line tools
prompts/                  Reconstruction agent (agent_instructions_v2.md) and SOAP agent (soap_agent_instructions_v1.md) instructions
clinical_extraction/      Module 3: extraction service, Azure/local model clients, evidence linking, tests
soap_generation/          Module 4: SOAP service, checks, rendering, tests
azure_ml_h1/              Hosting package for the extraction model on Azure ML
scenarios/ and output/    20 hand-written test consultations and their generated recordings
direct_inference_baseline/, direct_inference_1_7B/, judge_eval/, dataset_v2_batch_001*/   experiments, evaluation and datasets (see above)
tests/                    pytest suite of modules 1 and 2
docs/                     architecture.md, output_schema.md, MODULE3_FINETUNING_FOCUS.md
start_demo.ps1            One-command launcher for both services
requirements.txt          Pinned Python runtime dependencies
.env.example              Every setting the app reads, with no secret values
```

See [docs/architecture.md](docs/architecture.md) for the processing design and [docs/output_schema.md](docs/output_schema.md) for the transcript format.

## Known issues

- Two tests (`tests/test_backend_pipeline.py` with `foundry_fast`, and `tests/test_foundry_fast_transcription.py`) currently fail. They predate the voice-control and interface work and need a separate fix.
- `tests/test_audio_validation.py` needs `PYTHONPATH` set to the `scripts` folder (see "Check that it works").
