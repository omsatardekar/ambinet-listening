"""Local voice control for the browser recorder.

Pipeline (everything runs on this machine; no audio leaves the device):

    browser mic (16 kHz PCM frames over WebSocket)
        ├──► recording writer (only while a session is active) -> offline_recordings/<id>.wav
        └──► utterance segmenter (energy VAD) ──► Whisper worker ──► command matcher

The matcher works on transcribed text, so "Hey Asha", "start recording" and "stop recording"
are recognised the same way the CLI assistant recognises them, and the name "Asha" does not
need to be in a keyword vocabulary.
"""

from __future__ import annotations

import difflib
import logging
import os
import queue
import re
import secrets
import threading
import time
import wave
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import numpy as np

logger = logging.getLogger("ambient_demo.wakeword")

SAMPLE_RATE = 16000
FRAME_SAMPLES = 512
FRAME_SECONDS = FRAME_SAMPLES / SAMPLE_RATE
COMMAND_WINDOW_SECONDS = 10.0
MAX_LISTED_RECORDINGS = 200
WHISPER_MODEL = os.getenv("ASHA_WAKE_MODEL", "base.en")
SILENCE_LEVEL = 0.003
SILENCE_WARNING_SECONDS = 5.0
END_SILENCE_SECONDS = 0.6      # pause that closes an utterance
MAX_UTTERANCE_SECONDS = 15.0   # force a cut during long speech so commands are heard promptly
MIN_UTTERANCE_SECONDS = 0.4
PRE_ROLL_SECONDS = 0.25
SESSION_ID_PATTERN = re.compile(r"^\d{8}-\d{6}-[a-f0-9]{6}$")

FILLERS = {"hey", "hi", "hiya", "hello", "ok", "okay", "oh", "so", "um", "uh", "a"}
ASHA_ALIASES = {"asha", "ashah", "aasha", "aisha", "asa", "esha", "ashaa", "osha", "ahsa", "ashia", "ashya", "shah", "sha"}
HOTWORDS = "Hey Asha, start recording, stop recording"


@dataclass
class _Utterance:
    audio: np.ndarray
    start_frame: int  # absolute frame index (across the whole service lifetime)


def normalize_words(text: str) -> list[str]:
    return re.findall(r"[a-z]+", text.lower().replace("'", ""))


def contains_wake_word(words: list[str]) -> int:
    """Return the index just after a leading 'Hey Asha' (or -1).

    Exact spellings match anywhere at the start. Looser spellings (e.g. "Shah") only match
    when a greeting filler such as "hey" or "hiya" comes first, so "Asia" in normal speech
    does not wake the assistant.
    """
    i = 0
    while i < len(words) and words[i] in FILLERS:
        i += 1
    if i >= len(words):
        return -1
    greeted = i > 0
    for span in (1, 2):
        candidate = "".join(words[i:i + span])
        if candidate in ASHA_ALIASES or (greeted and _is_close_to_asha(candidate)):
            return i + span
    return -1


def _is_close_to_asha(candidate: str) -> bool:
    return len(candidate) >= 3 and difflib.SequenceMatcher(None, candidate, "asha").ratio() >= 0.7


def has_start_command(words: list[str]) -> bool:
    return any(
        words[i] == "start" and i + 1 < len(words) and words[i + 1] in {"recording", "record", "recordings"}
        for i in range(len(words))
    )


def has_stop_command(words: list[str]) -> bool:
    return any(
        words[i] == "stop" and any(w in {"recording", "record", "recordings"} for w in words[i + 1:i + 3])
        for i in range(len(words))
    )


class WakeWordService:
    """Voice-controlled recorder. Every recording is one WAV file in ``recordings_dir``."""

    def __init__(self, recordings_dir: Path):
        self._recordings_dir = Path(recordings_dir)
        self._lock = threading.RLock()
        self._listeners: list[Callable[[dict[str, Any]], None]] = []
        self._audio_queue: queue.Queue[bytes] = queue.Queue(maxsize=512)
        self._utterances: queue.Queue[_Utterance | None] = queue.Queue(maxsize=50)
        self._stop = threading.Event()
        self._model: Any = None
        self._worker: threading.Thread | None = None
        self._transcriber: threading.Thread | None = None
        self._writer: wave.Wave_write | None = None
        self._session_id: str | None = None
        self._session_started_at: str | None = None
        self._session_started_mono = 0.0
        self._session_start_frame = 0
        self._total_frames = 0
        self._state = "listening"
        self._armed_until = 0.0
        self._level = 0.0
        self._noise = 0.002
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
        # utterance segmentation state (worker thread only)
        self._seg: list[np.ndarray] = []
        self._seg_start_frame = 0
        self._seg_silence = 0.0
        self._in_speech = False
        self._pre_roll: list[np.ndarray] = []

    # ── lifecycle ────────────────────────────────────────────────────

    def start(self) -> None:
        if self._worker is not None:
            return
        self._loading = True
        self._emit("loading")
        try:
            from faster_whisper import WhisperModel

            self._model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
            self._recordings_dir.mkdir(parents=True, exist_ok=True)
            self._stop.clear()
            self._worker = threading.Thread(target=self._process_audio, name="asha-voice-input", daemon=True)
            self._transcriber = threading.Thread(target=self._transcribe_loop, name="asha-voice-stt", daemon=True)
            self._worker.start()
            self._transcriber.start()
            with self._lock:
                self._available = True
                self._loading = False
                self._error = None
                self._state = "listening"
            self._emit("ready")
            logger.info("Voice control is ready (Whisper %s, local only)", WHISPER_MODEL)
        except Exception as exc:
            logger.exception("Could not start voice control")
            with self._lock:
                self._available = False
                self._loading = False
                self._error = str(exc)
                self._state = "unavailable"
            self._emit("unavailable")

    def shutdown(self) -> None:
        self._stop.set()
        if self._writer is not None:
            self.stop_recording("shutdown")
        for thread in (self._worker, self._transcriber):
            if thread is not None:
                thread.join(timeout=3)
        self._worker = None
        self._transcriber = None
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
            elapsed = time.monotonic() - self._session_started_mono if self._writer is not None else 0.0
            armed_left = max(0.0, self._armed_until - time.monotonic()) if self._state == "awake" else 0.0
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
                "level": round(self._level, 3),
                "audio_connected": time.monotonic() - self._last_audio_at < 3.0,
                "input_silent": self._input_silent,
                "last_command": self._last_command,
                "heard": self._heard,
                "heard_age": round(time.monotonic() - self._heard_at, 1) if self._heard_at else None,
                "recordings": list(self._recordings),
                "error": self._error,
                "event": self._last_event,
            }

    def health(self) -> dict[str, Any]:
        state = self.snapshot()
        return {"available": state["available"], "state": state["state"], "error": state["error"]}

    # ── recording ────────────────────────────────────────────────────

    def start_recording(self, source: str = "button") -> bool:
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
            self._writer = writer
            self._session_id = session_id
            self._session_started_at = started.isoformat(timespec="seconds")
            self._session_started_mono = time.monotonic()
            self._session_start_frame = self._total_frames
            self._armed_until = 0.0
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
            path = self._path_for(session_id)
            if cut_at_frame is not None:
                keep = max(0, cut_at_frame - self._session_start_frame)
                _truncate_wav(path, keep)
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

    # ── worker 1: frames -> recording file + utterance segments ──────

    def _process_audio(self) -> None:
        while not self._stop.is_set():
            try:
                frame = self._audio_queue.get(timeout=0.1)
            except queue.Empty:
                self._expire_wake_window()
                continue
            pcm = np.frombuffer(frame, dtype=np.int16)
            audio = pcm.astype(np.float32) / 32768
            peak = float(np.abs(pcm.astype(np.int32)).max()) / 32768
            rms = float(np.sqrt(np.mean(audio * audio)))
            with self._lock:
                self._level = max(peak, self._level * 0.82)
                start_frame = self._total_frames
                self._total_frames += pcm.size
                if self._writer is not None:
                    self._writer.writeframesraw(frame)
            self._track_silence(peak)
            self._segment(audio, rms, start_frame)
            self._expire_wake_window()

    def _segment(self, audio: np.ndarray, rms: float, start_frame: int) -> None:
        threshold = max(0.012, self._noise * 3.5)
        is_speech = rms > threshold
        if not is_speech and not self._in_speech:
            self._noise = 0.97 * self._noise + 0.03 * rms
            self._pre_roll.append(audio)
            max_pre = int(PRE_ROLL_SECONDS / FRAME_SECONDS)
            del self._pre_roll[:-max_pre]
            return
        if not self._in_speech:
            self._in_speech = True
            self._seg = list(self._pre_roll)
            self._seg_start_frame = start_frame - sum(chunk.size for chunk in self._pre_roll)
            self._pre_roll = []
            self._seg_silence = 0.0
        self._seg.append(audio)
        self._seg_silence = 0.0 if is_speech else self._seg_silence + FRAME_SECONDS
        seconds = sum(chunk.size for chunk in self._seg) / SAMPLE_RATE
        if self._seg_silence >= END_SILENCE_SECONDS or seconds >= MAX_UTTERANCE_SECONDS:
            self._close_segment()

    def _close_segment(self) -> None:
        seconds = sum(chunk.size for chunk in self._seg) / SAMPLE_RATE
        if seconds >= MIN_UTTERANCE_SECONDS:
            utterance = _Utterance(np.concatenate(self._seg), self._seg_start_frame)
            try:
                self._utterances.put_nowait(utterance)
            except queue.Full:
                logger.warning("Voice backlog full; dropping one utterance")
        self._seg = []
        self._in_speech = False
        self._seg_silence = 0.0

    # ── worker 2: Whisper transcription + command matching ───────────

    def _transcribe_loop(self) -> None:
        while not self._stop.is_set():
            try:
                utterance = self._utterances.get(timeout=0.2)
            except queue.Empty:
                continue
            if utterance is None:
                break
            audio = utterance.audio
            peak = float(np.max(np.abs(audio))) if audio.size else 0.0
            if 0.01 < peak < 0.6:
                # Quiet microphones transcribe poorly; normalise each phrase to a usable level.
                audio = audio * min(20.0, 0.8 / peak)
            try:
                segments, _ = self._model.transcribe(
                    audio,
                    language="en",
                    beam_size=1,
                    vad_filter=False,
                    condition_on_previous_text=False,
                    without_timestamps=True,
                    hotwords=HOTWORDS,
                )
                text = " ".join(segment.text.strip() for segment in segments).strip()
            except Exception:
                logger.exception("Speech recognition failed for one utterance")
                continue
            logger.info("Heard (%.1fs, peak %.2f): %r", audio.size / SAMPLE_RATE, peak, text)
            if text:
                self._handle_text(text, utterance.start_frame)

    def _handle_text(self, text: str, start_frame: int) -> None:
        words = normalize_words(text)
        with self._lock:
            self._heard = text
            self._heard_at = time.monotonic()
            recording = self._writer is not None
            awake = self._state == "awake" and time.monotonic() <= self._armed_until
        self._emit("heard")
        if not words:
            return

        if recording:
            if has_stop_command(words):
                self._set_command("stop")
                logger.info("Stop command heard: %r", text)
                self.stop_recording("voice", cut_at_frame=start_frame)
            return

        wake_end = contains_wake_word(words)
        if wake_end >= 0:
            self._set_command("wake")
            logger.info("Wake word heard: %r", text)
            with self._lock:
                self._state = "awake"
                self._armed_until = time.monotonic() + COMMAND_WINDOW_SECONDS
            self._emit("wake_detected")
            # Command spoken in the same breath: "Hey Asha, start recording"
            if has_start_command(words[wake_end:]):
                self._set_command("start")
                self.start_recording("voice")
            return

        if awake and has_start_command(words):
            self._set_command("start")
            logger.info("Start command heard: %r", text)
            self.start_recording("voice")

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
    with wave.open(str(path), "rb") as reader:
        params = reader.getparams()
        data = reader.readframes(min(keep_frames, reader.getnframes()))
    tmp = path.with_suffix(".tmp")
    with wave.open(str(tmp), "wb") as writer:
        writer.setparams(params)
        writer.writeframes(data)
    os.replace(tmp, path)
