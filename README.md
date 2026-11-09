# Ambient Clinical Listening

Talk to your patient — Ambient Clinical listens, writes the **transcript**, picks out the **clinical entities**, and prepares the **SOAP note**.

This repository contains the working front half of that journey today (hands-free capture → speaker-aware transcript). Clinical entity extraction and the SOAP note follow the transcript in the full platform.

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
- **Internet** for the first run: the one-time voice model (about 36 MB) and the project's cloud services.
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

**First run only:** the backend downloads the 36 MB voice model into the `models/` folder. Wait until the terminal prints **`Voice control is ready`**. After that the model is stored permanently and loaded once when the server starts — no download, no waiting, on later runs.

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
| Header says Asha is getting ready for a long time | The first start downloads the 36 MB voice model. Check your internet and wait for "Voice control is ready" in the terminal. If the download failed, delete the `models/` folder and start again. |
| "Microphone blocked" | Click the lock icon in the address bar, allow the microphone for `127.0.0.1:5173`, reload. |
| "Waiting for microphone", or a silent-input warning | Choose the right input device in Windows Sound settings and check its level. |
| "Hey Asha" is not recognised | The header shows what was last heard. Speak clearly at normal volume, close to the microphone, and pause briefly after each phrase. |
| Upload says transcription is unavailable | Check `.env` and `http://127.0.0.1:8000/api/health`. |
| Port 8000 or 5173 already in use | Close the other program, or stop the earlier run with Ctrl+C. |
| Blank or old interface after updating | Run `npm install` in `frontend/`, then hard-refresh the browser (Ctrl+Shift+R). |

---

# Project layout

```text
backend/app/        FastAPI server: API, WebSocket voice channel, voice control, pipeline
frontend/src/       React + Vite interface (App.tsx, VoiceAssistant.tsx for hands-free recording)
models/             Voice model, downloaded once on first start (git-ignored)
offline_recordings/ Your saved recordings (git-ignored, may contain sensitive audio)
scripts/            Transcription and reconstruction steps used by the pipeline
prompts/            Instructions for the reconstruction agent
tests/              pytest suite
docs/               architecture.md and output_schema.md
start_demo.ps1      One-command launcher for both services
requirements.txt    Pinned Python runtime dependencies
.env.example        Every setting the app reads, with no values
```

See [docs/architecture.md](docs/architecture.md) for the processing design and [docs/output_schema.md](docs/output_schema.md) for the transcript format.

## Known issues

- Two tests (`tests/test_backend_pipeline.py` with `foundry_fast`, and `tests/test_foundry_fast_transcription.py`) currently fail. They predate the voice-control and interface work and need a separate fix.
- `tests/test_audio_validation.py` needs `PYTHONPATH` set to the `scripts` folder (see "Check that it works").
