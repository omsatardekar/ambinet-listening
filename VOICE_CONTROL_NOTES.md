# "Hey Asha" voice control: how it works (my private notes)

Not committed to Git. Written from the actual code in `backend/app/wakeword.py`,
`backend/app/main.py` and `frontend/src/VoiceAssistant.tsx`.

---

## 1. The 30-second picture

```
 BROWSER (React)                                     BACKEND (FastAPI, Python)
 ───────────────                                     ─────────────────────────
 Microphone                                          /api/wake/ws  (WebSocket)
   │ getUserMedia                                        │
   ▼                                                     ▼
 ScriptProcessor: resample -> 16 kHz mono 16-bit    accept_audio()  ──► queue (max 512 frames)
   │ cuts into 512-sample frames (32 ms each)            │
   └──── binary WebSocket message per frame ────────────►│   audio worker thread
                                                         ▼
                                                  _process_frame (every 32 ms)
                                                   ├─► if recording: write frame to the WAV
                                                   ├─► keep frame in a 5 s ring buffer
                                                   └─► energy VAD ─► Vosk (command grammar)
                                                                         │ words + timings
                                                                         ▼
                                                              command state machine
                                                                         │
 VoiceAssistant.tsx  ◄──── JSON state messages over the same WebSocket ──┘
   draws overlay, wave, timer, "heard" text
```

Everything runs **locally**. The audio never leaves the machine. Azure is only
used later, when you upload a recording for transcription.

---

## 2. Which model, and why we moved off Whisper

**Now: Vosk** (`vosk==0.3.45`), model `vosk-model-small-en-in-0.4` (Indian English,
about 55 MB). A second model, `vosk-model-small-en-us-0.15`, is in the repo as a
fallback. Both are committed in `models/`, so nothing is downloaded (this fixed the
company-laptop SSL problem). Switch model with `ASHA_VOICE_MODEL` in `.env`.

**Before (v1): `faster-whisper` `base.en`.** Why it was bad for this:

| | Whisper (v1) | Vosk (now) |
|---|---|---|
| Kind of model | Full-sentence transcriber | Streaming recognizer |
| What it has to do | Transcribe anything you say, then we search the text for "hey asha" | Only recognize 3 phrases |
| Reaction time | 3 to 4 seconds (wait for 0.6 s of silence, then slow transcription) | about 0.25 s after you stop speaking (decode about 15 ms) |
| Accuracy for our case | Often wrote "Hey Asia / Asher / Aisha", so wake word missed | Locked to a grammar, can only output our phrases |
| Word timings | Not used | Per-word start/end times, used to trim the commands out of the WAV |
| Model load | Heavy | Small, loaded once at startup |

The core reason: Whisper answers "what did they say?" (open vocabulary, slow, guesses
names). We only need "was it one of these three phrases?". Vosk with a restricted
grammar answers that directly, and is much faster.

### The grammar (very important)
```
"hey asha", "hay asha", "hi asha", "hello asha", "okay asha",
"start recording", "stop recording",
"hey asha start recording", "hey asha stop recording", "[unk]"
```
- `[unk]` is the "anything else" bucket, so normal conversation is thrown away.
- Only the spelling **"asha"** exists in this model's vocabulary. A word that is not in
  the vocabulary is silently dropped from a grammar. That is why we do not list
  "aasha" or "asia".
- Each word must also have confidence >= 0.45 (`MIN_CONFIDENCE`).

---

## 3. What happens to the audio, step by step

1. **Browser capture.** `getUserMedia` (echo cancellation on, noise suppression off,
   auto gain on). An `AudioContext` at 16 kHz (if the browser cannot, it resamples
   from 48 kHz itself). Frames of 512 samples (32 ms) are sent as binary WebSocket
   messages.
2. **Backend re-framing.** `main.py` buffers incoming bytes and slices exact
   1024-byte frames (512 samples x 2 bytes), then calls `voice_service.accept_audio`.
3. **Queue.** A bounded queue (512 frames, about 16 s). If the worker falls behind,
   the oldest frame is dropped, so latency never builds up.
4. **Audio worker thread** (`_process_audio`) handles each frame:
   - updates the level meter and the "silent microphone" warning,
   - appends the frame to a **5-second ring buffer** (160 frames),
   - if a recording is active, writes the frame to the WAV file,
   - runs the segmenter.
5. **Segmenter (my own energy VAD).** Speech = frame loudness above
   `max(0.008, noise_floor x 3)`. The noise floor adapts while it is quiet. A phrase
   starts at the first loud frame (plus 10 frames of pre-roll so the first syllable is
   kept) and ends after **0.30 s of silence** (or 12 s max). Clicks shorter than about
   100 ms are ignored.
6. **Gain.** Before the recognizer, quiet speech is boosted (up to 8x) toward a usable
   level. This only affects recognition, not the saved WAV.
7. **Decode.** On phrase end we call `FinalResult()` on a **fresh recognizer**
   (creating one costs about 0.3 ms). A fresh one per phrase is required because
   Vosk's `Reset()` does not reset its word-time clock, which broke the timings.
8. **Tokens.** Result words become `Token(word, start_frame, end_frame, conf)` using
   **absolute frame numbers** since the server started, so they line up with the ring
   buffer and the WAV.
9. **State machine** (next section).

Why my own VAD instead of Vosk's partial results: in grammar mode the partial results
are unusable and Vosk's own final arrives about 1 s late. Doing the silence detection
ourselves and forcing the final at 0.30 s is what makes it feel instant.

**"Loaded once":** the Vosk `Model` is created once in `WakeWordService.start()`
(called from FastAPI startup), kept for the life of the process, and warmed up with a
dummy decode so the first real command is as fast as the rest. Nothing loads per
command. Health shows `wake_word.available = true` once ready, and the log prints
"Voice control is ready".

---

## 4. The rules (state machine)

States: `listening` -> `awake` -> `recording` -> back to `listening`
(`unavailable` / loading at startup).

| You say | Current state | Result |
|---|---|---|
| "Hey Asha" | listening | -> `awake` for 10 s (`COMMAND_WINDOW_SECONDS`). Overlay opens: "Asha is listening" |
| "Hey Asha, start recording" (one breath) | listening | wakes and starts recording immediately |
| "Start recording" | awake (within 10 s) | recording starts |
| "Start recording" | listening (no wake) | **ignored** |
| wake window passes | awake | back to `listening`, "Hey Asha" needed again |
| "Hey Asha, stop recording" | recording | recording stops, file saved |
| "Stop recording" alone | recording | **ignored** (needs "Hey Asha") |
| "Hey Asha" then, within 8 s, "stop recording" (two phrases) | recording | stops (`stop_armed`, `STOP_WINDOW_SECONDS`) |

Code: `_handle_tokens` in `wakeword.py`. `find_wake` needs `<hey|hay|hi|hello|okay> asha`;
`find_command` needs the verb directly before "recording".

### Why the commands are not in the saved recording
The recording is written continuously while active, so we cut afterwards, using word
timings:

- **Start:** the WAV begins at the end of the word "recording" **+ 0.10 s**
  (`START_TRIM_SECONDS`). Those early frames come from the 5 s ring buffer.
- **Stop:** the WAV is truncated at the start of "hey" **- 0.08 s**
  (`STOP_TRIM_SECONDS`). Done in place by rewriting the 44-byte WAV header
  (`_truncate_wav`), so no re-encoding and no delay.
- Button start/stop keeps all audio (no trimming).

---

## 5. Frontend <-> backend coordination

There are **two channels**, and the browser needs both.

### Channel A: WebSocket `/api/wake/ws` (continuous)
- **Browser -> backend:** binary microphone frames (the only thing it sends).
- **Backend -> browser:** JSON messages, two kinds:
  - `type: "state"`: full snapshot, sent immediately on connect and on every event
    (`loading`, `ready`, `wake_detected`, `recording_started:voice`, `heard`,
    `stop_armed`, `recording_saved:voice`, `wake_window_expired`, ...). Contains
    `state`, `current` session, `armed_seconds`, `stop_armed`, `heard` text,
    `recordings` list, `error`, `audio_connected`, `input_silent`.
  - `type: "meter"`: sent every **50 ms** by a background task: `level`,
    `elapsed`, `audio_connected`. This drives the wave animation and timer smoothly.
- Thread bridge: the audio worker is a normal Python thread, FastAPI is async. The
  service calls listeners; `main.py` uses `loop.call_soon_threadsafe(...)` to schedule
  the broadcast on the event loop (`schedule_state`).
- Reconnect: if the socket closes, the frontend retries every 2 s.
- Security: connections whose `Origin` is not `127.0.0.1/localhost` on port 5173 or
  8000 are closed (code 1008). Chunks over 64 KB are rejected (1009). Wrong frame
  size closes with 1003.

### Channel B: plain HTTP (actions and files)
| Endpoint | Used for |
|---|---|
| `GET /api/wake/state` | first snapshot on page load |
| `POST /api/wake/recording/start` | the on-screen Start button (409 if already recording) |
| `POST /api/wake/recording/stop` | the Stop and save button (409 if not recording) |
| `GET /api/wake/recordings/{id}/audio` | play a saved recording (id is validated by regex) |
| `GET /api/health` | header status, includes `wake_word.available` |

### Vite proxy
The page is served on `127.0.0.1:5173`; `vite.config.ts` proxies `/api` (with
`ws: true`) to `127.0.0.1:8000`, so the browser always talks to one origin and the
WebSocket upgrade works.

### Who decides what (the key design rule)
**The backend is the single source of truth.** The browser never decides that a
command was heard. It only (1) streams audio and (2) renders whatever `state` the
backend reports:

| Backend `state` | Frontend mode | Shown |
|---|---|---|
| `listening` | `idle` | header: Listening for "Hey Asha" |
| `awake` | `awake` | Siri-style overlay, "Asha is listening", 10 s countdown bar |
| `recording` | `recording` | overlay with timer + wave + Stop and save |
| back to `listening` after recording | saved clip | overlay with audio player (`savedClip`) |

Other frontend modes cover problems: `offline` (backend down), `loading` (model
loading), `unavailable`, `mic` (blocked or needed), `waiting` (no audio frames).
The header pill also shows the last heard phrase for about 6 s, which is very useful
for debugging recognition.

Both countdown and timer are computed in the browser from timestamps (ticker every
250 ms), the backend sends `armed_seconds` / `elapsed` as facts.

---

## 6. Tuning knobs (all in `backend/app/wakeword.py`)

| Constant | Default | Effect |
|---|---|---|
| `END_SILENCE_SECONDS` | 0.30 | Pause that ends a phrase. Lower = faster but may cut phrases in two |
| `COMMAND_WINDOW_SECONDS` | 10 | How long Asha waits for "start recording" |
| `STOP_WINDOW_SECONDS` | 8 | Gap allowed between "Hey Asha" and "stop recording" |
| `START_TRIM_SECONDS` / `STOP_TRIM_SECONDS` | 0.10 / 0.08 | Margins around commands in the saved WAV |
| `MIN_CONFIDENCE` | 0.45 | Raise if it wakes on random speech; lower if it misses you |
| `HEY_WORDS` | hey, hay, hi, hello, okay | Accepted greetings |
| `ASHA_VOICE_MODEL` (env) | `vosk-model-small-en-in-0.4` | Try `vosk-model-small-en-us-0.15` if the Indian model mishears you |

---

## 7. Known limits (be honest)

- I tested the speed and trimming with synthetic (text-to-speech) voices and unit tests
  (`tests/test_wakeword.py`, 11 tests). **Accuracy on real voices and accents is not
  proven**; the header shows what was heard, so check it when "Hey Asha" is missed.
- "Asha" is the only spelling in the vocabulary. Mumbling or a very different
  pronunciation may fail. Try the other model, or lower `MIN_CONFIDENCE`.
- Needs Chrome or Edge, microphone permission, and `localhost` / `127.0.0.1`.
- `ScriptProcessorNode` is deprecated in browsers but works everywhere today; it is
  used for its tiny buffer (low latency).
- Only one browser tab should hold the microphone stream; several tabs would send
  audio into the same recognizer.
- Voice recordings are saved locally in `offline_recordings/` (git-ignored). They are
  not uploaded unless you upload them yourself.
