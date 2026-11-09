# Ambient Clinical Listening

A demo of an ambient clinical workflow: capture an encounter by voice or upload, transcribe it, reconstruct a speaker-aware draft transcript, and review it.

- **Hands-free recording.** Say **"Hey Asha"**, then **"start recording"**. Say **"Hey Asha, stop recording"** to save. Recordings are saved as WAV files on this machine and are never uploaded.
- **Upload.** Upload a WAV file and run the Azure transcription pipeline.

> **Clinical safety:** This is a demonstration. Reconstructed transcripts are drafts that a qualified clinician must review. Do not use real patient data unless your organisation has approved the environment and data handling.

---

## 1. Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Windows 10/11 | — | `start_demo.ps1` is a PowerShell launcher. macOS/Linux users can run the steps in section 5 manually. |
| Python | 3.12 (3.11 also works) | Install from python.org and tick "Add to PATH". |
| Node.js | 18 LTS or newer | Includes `npm`. |
| Google Chrome or Microsoft Edge | recent | Needed for microphone access on `http://127.0.0.1:5173`. |
| Microphone | — | Built-in or USB. Make sure it is not muted in Windows Sound settings. |
| Internet | — | Needed for Azure, and once for the first Whisper speech-model download (about 150 MB). |

You also need access to the project's Azure resources. Ask the project owner for the values for `.env` (section 3).

## 2. Get the code

```powershell
git clone https://github.com/omsatardekar/ambinet-listening.git
cd ambinet-listening
```

## 3. Set up Python

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

`requirements-dev.txt` installs everything in `requirements.txt` plus `pytest` for the tests. For a runtime-only install, use `requirements.txt`.

The first install of `faster-whisper` also downloads the speech model the first time the server starts, not during `pip install`.

## 4. Configure secrets

```powershell
Copy-Item .env.example .env
notepad .env
```

Fill in the values in `.env`. The file lists every setting the app reads. Empty optional values fall back to sensible defaults.

**Never commit `.env`.** It is listed in `.gitignore`.

## 5. Run the demo

From the project root, with the virtual environment active:

```powershell
.\start_demo.ps1
```

The launcher:

1. Checks the Python packages and installs any that are missing.
2. Runs `npm install` in `frontend/` the first time.
3. Starts the backend at **http://127.0.0.1:8000** and the frontend at **http://127.0.0.1:5173**.

Open **http://127.0.0.1:5173** in Chrome or Edge and allow microphone access when asked. Press **Ctrl+C** in the terminal to stop both services.

To run the two services by hand (macOS/Linux, or without the launcher):

```bash
# Terminal 1 - backend (from the project root)
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

# Terminal 2 - frontend
cd frontend
npm install
npx vite --host 127.0.0.1 --port 5173
```

## 6. Using the app

**Hands-free recording (Hey Asha)**

1. The header shows **"Listening for 'Hey Asha'"** once the microphone is live.
2. Say **"Hey Asha"**. A full-screen card appears and waits for up to 10 seconds.
3. Say **"start recording"**. The card shows a timer and a green wave that follows your voice.
4. Say **"Hey Asha, stop recording"**, or press **Stop and save**. The card shows the saved recording with a player.
5. Open **Recordings** (bottom left) to see every saved file. Files are in `offline_recordings/`.

You can also say "Hey Asha, start recording" as one phrase.

**Upload**

Drop a WAV file into the upload card (or choose one), then select **Create transcript**. Progress and the final transcript appear below.

## 7. Check that it works

- Backend health and configuration: **http://127.0.0.1:8000/api/health**. `azure_configured` should be `true`, and `wake_word.available` should be `true` once the speech model has loaded.
- Tests (from the project root, venv active):

  ```powershell
  $env:PYTHONPATH = "$PWD\scripts"
  python -m pytest -q tests
  ```

## 8. Troubleshooting

| Symptom | What to check |
|---|---|
| Header says "Voice unavailable" or "Loading voice model" | The first start downloads the Whisper model. Wait for "Voice control is ready" in the backend terminal. |
| "Microphone blocked" | Click the lock icon in the address bar and allow the microphone for `127.0.0.1:5173`, then reload. |
| "Waiting for microphone" or a warning about silent input | Pick the right input device in Windows Sound settings and check its level. |
| "Hey Asha" is not recognised | The header shows what was last heard. Speak clearly at normal volume, close to the microphone. |
| Upload says the service is not configured | Check `.env` and `http://127.0.0.1:8000/api/health`. |
| Port 8000 or 5173 is already in use | Close the other program, or stop the earlier demo with Ctrl+C. |
| `python` is not found | Reinstall Python with "Add to PATH" ticked, then open a new terminal. |

## 9. Project layout

```text
backend/app/        FastAPI server: API, WebSocket voice channel, Whisper voice control, pipeline
frontend/src/       React + Vite UI (App.tsx, VoiceAssistant.tsx for hands-free recording)
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

- Two tests in `tests/test_backend_pipeline.py` and `tests/test_foundry_fast_transcription.py` currently fail. They predate the voice-control work and need a separate fix.
