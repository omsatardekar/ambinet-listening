"""Local voice control for the browser recorder.

Everything runs on this machine; no audio leaves the device.

    browser mic (16 kHz PCM frames over WebSocket)
        ├──► recording writer (only while a session is active) -> offline_recordings/<id>.wav
        └──► energy VAD ──► Vosk recognizer locked to a tiny command grammar ──► command state machine

Why this design is fast and strict
  * The recognizer is a streaming Vosk model restricted to a grammar of exactly the control phrases
    ("hey asha", "start recording", "stop recording"; everything else is ``[unk]``). It is loaded
    once when the server starts and kept in memory, so there is no per-command model load.
  * A phrase is decoded as soon as the speaker pauses for ``END_SILENCE_SECONDS`` (~0.3 s), not after
    a slow full-sentence transcription, so commands react in a few hundred milliseconds.
  * Commands are gated: "start recording" only works after "Hey Asha" (the assistant is awake), and
    "stop recording" only works together with "Hey Asha".
  * Vosk gives word timings, so the saved WAV starts right after "start recording" and ends right
    before "Hey Asha, stop recording": the control phrases are not part of the recording.
"""

from __future__ import annotations

import collections
import json
import logging
import os
import queue
import re
import secrets
import threading
import time
import urllib.request
import wave
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import numpy as np

logger = logging.getLogger("ambient_demo.wakeword")

SAMPLE_RATE = 16000
FRAME_SAMPLES = 512
FRAME_SECONDS = FRAME_SAMPLES / SAMPLE_RATE
COMMAND_WINDOW_SECONDS = 10.0      # how long Asha waits for "start recording" after "Hey Asha"
STOP_WINDOW_SECONDS = 8.0          # "Hey Asha ... stop recording" may be said as two phrases
MAX_LISTED_RECORDINGS = 200
SILENCE_LEVEL = 0.003
SILENCE_WARNING_SECONDS = 5.0
END_SILENCE_SECONDS = 0.30         # pause that closes a phrase and triggers decoding
MAX_PHRASE_SECONDS = 12.0          # force a decode during long speech
MIN_SPEECH_FRAMES = 3              # ignore clicks shorter than ~100 ms
PRE_ROLL_FRAMES = 10               # audio fed to the recognizer before the detected onset
RING_FRAMES = 160                  # ~5 s of recent audio kept for exact start trimming
START_TRIM_SECONDS = 0.10          # drop this much after "recording" so its tail is not saved
STOP_TRIM_SECONDS = 0.08           # cut this much before "hey" so its onset is not saved
MIN_CONFIDENCE = 0.45
SESSION_ID_PATTERN = re.compile(r"^\d{8}-\d{6}-[a-f0-9]{6}$")

MODEL_NAME = os.getenv("ASHA_VOICE_MODEL", "vosk-model-small-en-in-0.4")
MODEL_ROOT = Path(os.getenv("ASHA_MODEL_DIR", Path(__file__).resolve().parents[2] / "models"))
MODEL_URL = f"https://alphacephei.com/vosk/models/{MODEL_NAME}.zip"

HEY_WORDS = ("hey", "hay", "hi", "hello", "okay")
ASHA_WORDS = ("asha",)  # the only spelling present in the model vocabulary
RECORD_WORDS = {"recording", "record"}
GRAMMAR = json.dumps(
    [f"{hey} {asha}" for hey in HEY_WORDS for asha in ASHA_WORDS]
    + ["start recording", "stop recording", "hey asha start recording", "hey asha stop recording", "[unk]"]
)


@dataclass(frozen=True)
class Token:
    word: str
    start: int   # absolute frame index (across the whole service lifetime)
    end: int
    conf: float = 1.0


def tokens_from_result(result: dict[str, Any], offset_frame: int) -> list[Token]:
    """Words of a Vosk final result with absolute frame positions ([unk] filler is dropped)."""
    tokens: list[Token] = []
    for item in result.get("result") or []:
        word = str(item.get("word", "")).lower()
        if not word or word == "[unk]":
            continue
        tokens.append(
            Token(
                word,
                offset_frame + int(float(item.get("start", 0.0)) * SAMPLE_RATE),
                offset_frame + int(float(item.get("end", 0.0)) * SAMPLE_RATE),
                float(item.get("conf", 1.0)),
            )
        )
    return tokens


def find_wake(tokens: list[Token]) -> int:
    """Index of the 'asha' token in the first "<hey> asha" (or -1)."""
    for i in range(1, len(tokens)):
        if (
            tokens[i].word in ASHA_WORDS
            and tokens[i - 1].word in HEY_WORDS
            and min(tokens[i].conf, tokens[i - 1].conf) >= MIN_CONFIDENCE
        ):
            return i
    return -1


def find_command(tokens: list[Token], verb: str, after: int = 0) -> int:
    """Index of the 'recording' token in "<verb> recording" at or after ``after`` (or -1)."""
    for i in range(max(1, after), len(tokens)):
        if (
            tokens[i].word in RECORD_WORDS
            and tokens[i - 1].word == verb
            and min(tokens[i].conf, tokens[i - 1].conf) >= MIN_CONFIDENCE
        ):
            return i
    return -1


def ensure_model(path: Path | None = None) -> Path:
    """Return the local Vosk model folder, downloading it once if it is not on disk yet."""
    target = path or MODEL_ROOT / MODEL_NAME
    if (target / "am").is_dir():
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    archive = target.parent / f"{MODEL_NAME}.zip"
    logger.info("Downloading the voice model once (%s) ...", MODEL_URL)
    urllib.request.urlretrieve(MODEL_URL, archive)
    with zipfile.ZipFile(archive) as bundle:
        bundle.extractall(target.parent)
    archive.unlink(missing_ok=True)
    if not (target / "am").is_dir():
        raise RuntimeError(f"The voice model was not found in {target} after download.")
    return target


class WakeWordService:
    """Voice-controlled recorder. Every recording is one WAV file in ``recordings_dir``."""

    def __init__(self, recordings_dir: Path):
        self._recordings_dir = Path(recordings_dir)
        self._lock = threading.RLock()
        self._listeners: list[Callable[[dict[str, Any]], None]] = []
        self._audio_queue: queue.Queue[bytes] = queue.Queue(maxsize=512)
        self._stop = threading.Event()
        self._model: Any = None
        self._vosk: Any = None
        self._worker: threading.Thread | None = None
        self._writer: wave.Wave_write | None = None
        self._session_id: str | None = None
        self._session_started_at: str | None = None
        self._session_started_mono = 0.0
        self._session_start_frame = 0
        self._total_frames = 0
        self._state = "listening"
        self._armed_until = 0.0
        self._stop_cut: int | None = None      # frame where a pending "Hey Asha" began (while recording)
        self._stop_cut_until = 0.0
        self._level = 0.0
        self._noise = 0.002
        self._speech_rms = 0.05
        self._last_audio_at = 0.0
        self._quiet_since: float | None = None
        self._input_silent = False
        self._last_command: str | None = None
        self._heard = ""
        self._heard_at = 0.0
        self._available = False
        self._loading = False
        self._error: str | None = None
        self._last_event = "starting"
        self._recordings = self._load_recordings()
        # phrase segmentation state (audio worker thread only)
        self._ring: collections.deque[tuple[int, bytes]] = collections.deque(maxlen=RING_FRAMES)
        self._recognizer: Any = None
        self._in_speech = False
        self._seg_offset = 0
        self._seg_frames = 0
        self._seg_speech_frames = 0
        self._seg_silence = 0

    # ── lifecycle ────────────────────────────────────────────────────

    def start(self) -> None:
        if self._worker is not None:
            return
        self._loading = True
        self._emit("loading")
        try:
            import vosk

            vosk.SetLogLevel(-1)
            self._vosk = vosk
            self._model = vosk.Model(str(ensure_model()))   # loaded once, kept for the process lifetime
            self._recognizer = self._new_recognizer()
            self._warm_up()
            self._recordings_dir.mkdir(parents=True, exist_ok=True)
            self._stop.clear()
            self._worker = threading.Thread(target=self._process_audio, name="asha-voice-input", daemon=True)
            self._worker.start()
            with self._lock:
                self._available = True
                self._loading = False
                self._error = None
                self._state = "listening"
            self._emit("ready")
            logger.info("Voice control is ready (%s, local only)", MODEL_NAME)
        except Exception as exc:
            logger.exception("Could not start voice control")
            with self._lock:
                self._available = False
                self._loading = False
                self._error = str(exc)
                self._state = "unavailable"
            self._emit("unavailable")

    def _new_recognizer(self) -> Any:
        recognizer = self._vosk.KaldiRecognizer(self._model, SAMPLE_RATE, GRAMMAR)
        recognizer.SetWords(True)
        return recognizer

    def _warm_up(self) -> None:
        """Run one dummy decode so the first real command is not slower than the rest."""
        silence = bytes(FRAME_SAMPLES * 2)
        for _ in range(8):
            self._recognizer.AcceptWaveform(silence)
        self._recognizer.FinalResult()

    def shutdown(self) -> None:
        self._stop.set()
        if self._writer is not None:
            self.stop_recording("shutdown")
        if self._worker is not None:
            self._worker.join(timeout=3)
        self._worker = None
        with self._lock:
            self._available = False

    def add_listener(self, listener: Callable[[dict[str, Any]], None]) -> None:
        self._listeners.append(listener)

    def remove_listener(self, listener: Callable[[dict[str, Any]], None]) -> None:
        if listener in self._listeners:
            self._listeners.remove(listener)

    # ── state for the browser ────────────────────────────────────────

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._session_started_mono if self._writer is not None else 0.0
            armed_left = max(0.0, self._armed_until - now) if self._state == "awake" else 0.0
            return {
                "type": "state",
                "available": self._available,
                "loading": self._loading,
                "state": self._state,
                "wake_word": "Hey Asha",
                "current": (
                    {"session_id": self._session_id, "started_at": self._session_started_at}
                    if self._session_id else None
                ),
                "elapsed": round(elapsed, 1),
                "armed_seconds": round(armed_left, 1),
                "stop_armed": self._writer is not None and self._stop_cut is not None and now <= self._stop_cut_until,
                "level": round(self._level, 3),
                "audio_connected": now - self._last_audio_at < 3.0,
                "input_silent": self._input_silent,
                "last_command": self._last_command,
                "heard": self._heard,
                "heard_age": round(now - self._heard_at, 1) if self._heard_at else None,
                "recordings": list(self._recordings),
                "error": self._error,
                "event": self._last_event,
            }

    def health(self) -> dict[str, Any]:
        state = self.snapshot()
        return {"available": state["available"], "state": state["state"], "error": state["error"]}

    # ── recording ────────────────────────────────────────────────────

    def start_recording(self, source: str = "button", trim_from_frame: int | None = None) -> bool:
        """Open a new WAV. With ``trim_from_frame`` the file begins at that absolute frame
        (taken from the recent-audio ring) so the spoken "start recording" is left out."""
        with self._lock:
            if not self._available:
                raise RuntimeError("Voice recording is not available.")
            if self._writer is not None:
                return False
            self._recordings_dir.mkdir(parents=True, exist_ok=True)
            started = datetime.now().astimezone()
            session_id = started.strftime("%Y%m%d-%H%M%S-") + secrets.token_hex(3)
            writer = wave.open(str(self._path_for(session_id)), "wb")
            writer.setnchannels(1)
            writer.setsampwidth(2)
            writer.setframerate(SAMPLE_RATE)
            first_frame = self._total_frames
            if trim_from_frame is not None:
                for frame_start, frame_bytes in self._ring:
                    if frame_start >= trim_from_frame:
                        if first_frame == self._total_frames:
                            first_frame = frame_start
                        writer.writeframesraw(frame_bytes)
            self._writer = writer
            self._session_id = session_id
            self._session_started_at = started.isoformat(timespec="seconds")
            self._session_started_mono = time.monotonic()
            self._session_start_frame = first_frame
            self._armed_until = 0.0
            self._stop_cut = None
            self._state = "recording"
        self._emit(f"recording_started:{source}")
        logger.info("Recording started (%s)", source)
        return True

    def stop_recording(self, source: str = "button", cut_at_frame: int | None = None) -> dict[str, Any] | None:
        with self._lock:
            if self._writer is None or self._session_id is None:
                return None
            session_id = self._session_id
            started_at = self._session_started_at
            self._writer.close()
            self._writer = None
            self._session_id = None
            self._session_started_at = None
            self._state = "listening"
            self._armed_until = 0.0
            self._stop_cut = None
            path = self._path_for(session_id)
            if cut_at_frame is not None:
                _truncate_wav(path, max(0, cut_at_frame - self._session_start_frame))
            duration = round(_wav_duration(path), 1)
            entry = self._entry(session_id, started_at, duration)
            self._recordings.insert(0, entry)
            del self._recordings[MAX_LISTED_RECORDINGS:]
        self._emit(f"recording_saved:{source}")
        logger.info("Recording saved: %s (%.1fs)", session_id, duration)
        return entry

    def audio_path(self, session_id: str) -> Path | None:
        if not SESSION_ID_PATTERN.fullmatch(session_id):
            return None
        path = self._path_for(session_id)
        return path if path.is_file() else None

    # ── audio input (called from the WebSocket handler) ──────────────

    def accept_audio(self, frame: bytes) -> None:
        if len(frame) != FRAME_SAMPLES * 2:
            raise ValueError(f"Audio frames must contain exactly {FRAME_SAMPLES} PCM samples.")
        with self._lock:
            self._last_audio_at = time.monotonic()
        try:
            self._audio_queue.put_nowait(frame)
        except queue.Full:
            try:
                self._audio_queue.get_nowait()
                self._audio_queue.put_nowait(frame)
            except queue.Empty:
                pass

    # ── audio worker: frames -> recording file + phrase decoding ─────

    def _process_audio(self) -> None:
        while not self._stop.is_set():
            try:
                frame = self._audio_queue.get(timeout=0.1)
            except queue.Empty:
                self._expire_wake_window()
                continue
            try:
                self._process_frame(frame)
            except Exception:
                logger.exception("Voice processing failed for one audio frame")

    def _process_frame(self, frame: bytes) -> None:
        pcm = np.frombuffer(frame, dtype=np.int16)
        audio = pcm.astype(np.float32) / 32768
        peak = float(np.abs(pcm.astype(np.int32)).max()) / 32768
        rms = float(np.sqrt(np.mean(audio * audio)))
        with self._lock:
            self._level = max(peak, self._level * 0.82)
            start_frame = self._total_frames
            self._total_frames += pcm.size
            self._ring.append((start_frame, frame))
            if self._writer is not None:
                self._writer.writeframesraw(frame)
        self._track_silence(peak)
        self._segment(frame, rms, start_frame)
        self._expire_wake_window()

    def _segment(self, frame: bytes, rms: float, start_frame: int) -> None:
        is_speech = rms > max(0.008, self._noise * 3.0)
        if not self._in_speech:
            if not is_speech:
                self._noise = 0.97 * self._noise + 0.03 * rms
                return
            self._in_speech = True
            # A fresh recognizer per phrase (~0.3 ms) keeps its word timings relative to this phrase.
            self._recognizer = self._new_recognizer()
            preroll = list(self._ring)[-(PRE_ROLL_FRAMES + 1):-1]
            self._seg_offset = preroll[0][0] if preroll else start_frame
            self._seg_frames = 0
            self._seg_speech_frames = 0
            self._seg_silence = 0
            for _, pre_bytes in preroll:
                self._feed(pre_bytes)
        self._feed(frame)
        if is_speech:
            self._seg_speech_frames += 1
            self._seg_silence = 0
            self._speech_rms = 0.98 * self._speech_rms + 0.02 * rms
        else:
            self._seg_silence += 1
        if (
            self._seg_silence * FRAME_SECONDS >= END_SILENCE_SECONDS
            or self._seg_frames * FRAME_SECONDS >= MAX_PHRASE_SECONDS
        ):
            self._finish_phrase()

    def _feed(self, frame: bytes) -> None:
        self._seg_frames += 1
        # Quiet microphones recognise poorly: bring the speech level to a usable range.
        gain = min(8.0, max(1.0, 0.06 / max(self._speech_rms, 1e-4)))
        if gain > 1.05:
            samples = np.frombuffer(frame, dtype=np.int16).astype(np.float32) * gain
            frame = np.clip(samples, -32768, 32767).astype(np.int16).tobytes()
        self._recognizer.AcceptWaveform(frame)

    def _finish_phrase(self) -> None:
        self._in_speech = False
        started = time.monotonic()
        result = json.loads(self._recognizer.FinalResult())
        if self._seg_speech_frames < MIN_SPEECH_FRAMES:
            return
        logger.info("Heard %r (decoded in %.0f ms)", result.get("text", ""), (time.monotonic() - started) * 1000)
        self._handle_tokens(tokens_from_result(result, self._seg_offset))

    # ── command state machine ────────────────────────────────────────

    def _handle_tokens(self, tokens: list[Token]) -> None:
        """Act on one decoded phrase. Tokens carry absolute frame positions."""
        if not tokens:
            return
        with self._lock:
            self._heard = " ".join(token.word for token in tokens)
            self._heard_at = time.monotonic()
        self._emit("heard")

        now = time.monotonic()
        with self._lock:
            recording = self._writer is not None
            awake = self._state == "awake" and now <= self._armed_until
            pending_cut = self._stop_cut if now <= self._stop_cut_until else None

        wake = find_wake(tokens)
        if recording:
            stop = find_command(tokens, "stop")
            if stop >= 0:
                if 0 <= wake < stop:
                    cut = tokens[wake - 1].start
                elif pending_cut is not None:
                    cut = pending_cut
                else:
                    logger.info("Ignoring 'stop recording' without 'Hey Asha'")
                    return
                self._set_command("stop")
                logger.info("Stop command heard")
                self.stop_recording("voice", cut_at_frame=max(0, cut - int(STOP_TRIM_SECONDS * SAMPLE_RATE)))
            elif wake >= 0:
                with self._lock:
                    self._stop_cut = tokens[wake - 1].start
                    self._stop_cut_until = now + STOP_WINDOW_SECONDS
                self._set_command("wake")
                self._emit("stop_armed")
            return

        if wake >= 0:
            self._set_command("wake")
            logger.info("Wake word heard")
            with self._lock:
                self._state = "awake"
                self._armed_until = now + COMMAND_WINDOW_SECONDS
            self._emit("wake_detected")
            start = find_command(tokens, "start", after=wake + 1)
            if start >= 0:
                self._begin_voice_recording(tokens[start])
            return

        if awake:
            start = find_command(tokens, "start")
            if start >= 0:
                self._begin_voice_recording(tokens[start])

    def _begin_voice_recording(self, last_word: Token) -> None:
        self._set_command("start")
        logger.info("Start command heard")
        self.start_recording("voice", trim_from_frame=last_word.end + int(START_TRIM_SECONDS * SAMPLE_RATE))

    def _set_command(self, command: str) -> None:
        with self._lock:
            self._last_command = command

    # ── helpers ──────────────────────────────────────────────────────

    def _track_silence(self, peak: float) -> None:
        now = time.monotonic()
        if peak >= SILENCE_LEVEL:
            self._quiet_since = None
            if self._input_silent:
                self._input_silent = False
                logger.info("Microphone input is active again")
            return
        if self._quiet_since is None:
            self._quiet_since = now
        elif not self._input_silent and now - self._quiet_since >= SILENCE_WARNING_SECONDS:
            self._input_silent = True
            logger.warning(
                "Microphone input has been silent for %.0fs. Check the browser microphone "
                "selection and the Windows input device level.",
                SILENCE_WARNING_SECONDS,
            )

    def _expire_wake_window(self) -> None:
        with self._lock:
            expired = self._state == "awake" and time.monotonic() > self._armed_until
            if expired:
                self._state = "listening"
        if expired:
            self._emit("wake_window_expired")

    def _path_for(self, session_id: str) -> Path:
        return self._recordings_dir / f"{session_id}.wav"

    def _entry(self, session_id: str, started_at: str | None, duration_s: float) -> dict[str, Any]:
        return {
            "session_id": session_id,
            "started_at": started_at,
            "duration_s": duration_s,
            "audio_url": f"/api/wake/recordings/{session_id}/audio",
        }

    def _emit(self, event: str) -> None:
        with self._lock:
            self._last_event = event
        state = self.snapshot()
        for listener in tuple(self._listeners):
            try:
                listener(state)
            except Exception:
                logger.exception("Voice state listener failed")

    def _load_recordings(self) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        if not self._recordings_dir.is_dir():
            return entries
        for path in self._recordings_dir.glob("*.wav"):
            session_id = path.stem
            if not SESSION_ID_PATTERN.fullmatch(session_id):
                continue
            try:
                duration = round(_wav_duration(path), 1)
                started = datetime.strptime(session_id[:15], "%Y%m%d-%H%M%S").astimezone()
            except (OSError, EOFError, wave.Error, ValueError):
                logger.warning("Skipping unreadable recording %s", path.name)
                continue
            entries.append(self._entry(session_id, started.isoformat(timespec="seconds"), duration))
        entries.sort(key=lambda item: item["session_id"], reverse=True)
        return entries[:MAX_LISTED_RECORDINGS]


def _wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as reader:
        rate = reader.getframerate() or SAMPLE_RATE
        return reader.getnframes() / rate


def _truncate_wav(path: Path, keep_frames: int) -> None:
    """Cut a mono 16-bit WAV to ``keep_frames`` samples in place (no rewrite of the audio)."""
    with wave.open(str(path), "rb") as reader:
        keep = min(keep_frames, reader.getnframes())
        width = reader.getsampwidth() * reader.getnchannels()
    data_bytes = keep * width
    with open(path, "r+b") as handle:
        handle.truncate(44 + data_bytes)       # the stdlib writer emits a canonical 44-byte header
        handle.seek(4)
        handle.write((36 + data_bytes).to_bytes(4, "little"))
        handle.seek(40)
        handle.write(data_bytes.to_bytes(4, "little"))
