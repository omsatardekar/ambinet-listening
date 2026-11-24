"""Speaker gate: only the enrolled voice may trigger "Hey Asha" commands.

Sits between the phrase recognizer (wakeword.py) and speaker_verification.py (ECAPA-TDNN).

  * Enrolment reuses the microphone stream that is already flowing to the backend: the gate
    collects ``ENROLL_SPEECH_SECONDS`` of actual speech, builds a voiceprint and saves it.
  * Verification scores the audio of each recognised command phrase against the voiceprint.
  * Everything stays on this machine. The voiceprint is biometric data and is git-ignored.

The heavy imports (PyTorch, SpeechBrain) happen in a background thread so the server and the
rest of the voice control start immediately. If they are missing the gate reports
``available = False`` and voice commands keep working for everyone (nothing is gated).
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Any

import numpy as np

from . import speaker_verification as sv

logger = logging.getLogger("ambient_demo.speaker_gate")

SAMPLE_RATE = sv.SAMPLE_RATE
ENROLL_SPEECH_SECONDS = float(os.getenv("SPEAKER_ENROLL_SECONDS", "15"))
ENROLL_TIMEOUT_SECONDS = 60.0
# Command phrases ("hey asha", "start recording") are short; a lower bar than a full utterance.
DEFAULT_GATE_THRESHOLD = float(os.getenv("SPEAKER_THRESHOLD", "0.25"))
MIN_PHRASE_SECONDS = 0.4


def tile_to_minimum(audio: np.ndarray, seconds: float = sv.MIN_SECONDS) -> np.ndarray:
    """Repeat a short phrase until it is long enough for the encoder (it needs >= 1.5 s)."""
    target = int(seconds * SAMPLE_RATE)
    if audio.size >= target:
        return audio
    repeats = int(np.ceil(target / max(1, audio.size)))
    return np.tile(audio, repeats)[:target]


class SpeakerGate:
    def __init__(self, data_dir: Path):
        self._dir = Path(data_dir)
        self._voiceprint_path = self._dir / "voiceprint.npy"
        self._settings_path = self._dir / "settings.json"
        self._lock = threading.RLock()
        self._encoder: sv.SpeakerEncoder | None = None
        self._loading = False
        self._error: str | None = None
        self._voiceprint: np.ndarray | None = None
        self._enabled = True
        self._threshold = DEFAULT_GATE_THRESHOLD
        # enrolment capture
        self._enrolling = False
        self._enroll_chunks: list[np.ndarray] = []
        self._enroll_samples = 0
        self._enroll_started = 0.0
        self._enroll_status = "idle"       # idle | capturing | processing | done | failed
        self._enroll_message: str | None = None
        # last verification, shown in the UI so the threshold can be tuned
        self._last_score: float | None = None
        self._last_ok: bool | None = None
        self._last_at = 0.0
        self._load_files()

    # ── lifecycle ────────────────────────────────────────────────────

    def start(self) -> None:
        """Load the ECAPA model in the background."""
        with self._lock:
            if self._loading or self._encoder is not None:
                return
            self._loading = True
        threading.Thread(target=self._load_encoder, name="speaker-model", daemon=True).start()

    def _load_encoder(self) -> None:
        try:
            encoder = sv.SpeakerEncoder(savedir=self._dir / "model")
            encoder.embed(np.zeros(int(sv.MIN_SECONDS * SAMPLE_RATE), dtype=np.float32) + 1e-3)  # warm-up
            with self._lock:
                self._encoder = encoder
                self._error = None
            logger.info("Speaker verification model is ready")
        except Exception as exc:  # missing torch/speechbrain, no network for the first download, ...
            logger.warning("Speaker verification unavailable: %s", exc)
            with self._lock:
                self._error = f"{type(exc).__name__}: {exc}"
        finally:
            with self._lock:
                self._loading = False

    def _load_files(self) -> None:
        try:
            if self._voiceprint_path.exists():
                self._voiceprint = sv.load_voiceprint(self._voiceprint_path)
            if self._settings_path.exists():
                settings = json.loads(self._settings_path.read_text())
                self._enabled = bool(settings.get("enabled", True))
                self._threshold = float(settings.get("threshold", self._threshold))
        except Exception:
            logger.exception("Could not read the saved voiceprint or speaker settings")
            self._voiceprint = None

    def _save_settings(self) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        self._settings_path.write_text(json.dumps({"enabled": self._enabled, "threshold": self._threshold}))

    # ── state ────────────────────────────────────────────────────────

    @property
    def ready(self) -> bool:
        return self._encoder is not None

    @property
    def enrolled(self) -> bool:
        return self._voiceprint is not None

    @property
    def enrolling(self) -> bool:
        return self._enrolling

    @property
    def active(self) -> bool:
        """True when commands must come from the enrolled voice."""
        with self._lock:
            return self._enabled and self._voiceprint is not None

    def status(self) -> dict[str, Any]:
        with self._lock:
            now = time.monotonic()
            return {
                "available": self._encoder is not None,
                "loading": self._loading,
                "error": self._error,
                "enrolled": self._voiceprint is not None,
                "enabled": self._enabled,
                "active": self._enabled and self._voiceprint is not None,
                "threshold": self._threshold,
                "enrolling": self._enrolling,
                "enroll_status": self._enroll_status,
                "enroll_message": self._enroll_message,
                "enroll_progress": self.enroll_progress(),
                "enroll_target_seconds": ENROLL_SPEECH_SECONDS,
                "last_score": self._last_score,
                "last_ok": self._last_ok,
                "last_age": round(now - self._last_at, 1) if self._last_at else None,
            }

    def enroll_progress(self) -> float:
        with self._lock:
            if self._enroll_status in ("processing", "done"):
                return 1.0
            return min(1.0, self._enroll_samples / (ENROLL_SPEECH_SECONDS * SAMPLE_RATE))

    # ── settings ─────────────────────────────────────────────────────

    def configure(self, enabled: bool | None = None, threshold: float | None = None) -> None:
        with self._lock:
            if enabled is not None:
                self._enabled = enabled
            if threshold is not None:
                if not -1.0 <= threshold <= 1.0:
                    raise ValueError("The threshold must be between -1 and 1.")
                self._threshold = threshold
            self._save_settings()

    def delete_voiceprint(self) -> None:
        with self._lock:
            self._voiceprint = None
            self._enroll_status = "idle"
            self._enroll_message = None
            self._last_score = self._last_ok = None
            self._last_at = 0.0
            if self._voiceprint_path.exists():
                self._voiceprint_path.unlink()

    # ── enrolment ────────────────────────────────────────────────────

    def begin_enrollment(self) -> None:
        with self._lock:
            if self._encoder is None:
                raise RuntimeError(self._error or "The speaker model is still loading. Try again in a moment.")
            if self._enrolling:
                raise RuntimeError("Enrolment is already running.")
            self._enrolling = True
            self._enroll_chunks = []
            self._enroll_samples = 0
            self._enroll_started = time.monotonic()
            self._enroll_status = "capturing"
            self._enroll_message = "Speak naturally: read something aloud or describe your day."

    def cancel_enrollment(self) -> None:
        with self._lock:
            if self._enrolling:
                self._enrolling = False
                self._enroll_chunks = []
                self._enroll_samples = 0
                self._enroll_status = "idle"
                self._enroll_message = "Enrolment cancelled."

    def feed(self, frame: bytes, is_speech: bool) -> bool:
        """Offer one 16 kHz PCM frame during enrolment. Returns True when the capture just completed."""
        with self._lock:
            if not self._enrolling:
                return False
            if time.monotonic() - self._enroll_started > ENROLL_TIMEOUT_SECONDS:
                self._enrolling = False
                self._enroll_status = "failed"
                self._enroll_message = "Not enough speech was heard. Check the microphone and try again."
                return False
            if not is_speech:
                return False
            samples = np.frombuffer(frame, dtype=np.int16).astype(np.float32) / 32768.0
            self._enroll_chunks.append(samples)
            self._enroll_samples += samples.size
            if self._enroll_samples < ENROLL_SPEECH_SECONDS * SAMPLE_RATE:
                return False
            audio = np.concatenate(self._enroll_chunks)
            self._enrolling = False
            self._enroll_chunks = []
            self._enroll_status = "processing"
            self._enroll_message = "Building your voiceprint…"
        threading.Thread(target=self._finish_enrollment, args=(audio,), name="speaker-enroll", daemon=True).start()
        return True

    def _finish_enrollment(self, audio: np.ndarray) -> None:
        try:
            assert self._encoder is not None
            embeddings = [self._encoder.embed(window) for window in sv.split_windows(audio)]
            if not embeddings:
                raise ValueError("No usable speech found.")
            voiceprint = sv.average_voiceprint(embeddings)
            self._dir.mkdir(parents=True, exist_ok=True)
            sv.save_voiceprint(voiceprint, self._voiceprint_path)
            with self._lock:
                self._voiceprint = voiceprint
                self._enabled = True
                self._save_settings()
                self._enroll_status = "done"
                self._enroll_message = "Voice enrolled. Only your voice can now trigger Asha."
            logger.info("Voiceprint saved from %d windows", len(embeddings))
        except Exception as exc:
            logger.exception("Enrolment failed")
            with self._lock:
                self._enroll_status = "failed"
                self._enroll_message = f"Enrolment failed: {exc}"

    # ── verification ─────────────────────────────────────────────────

    def verify(self, audio: np.ndarray) -> tuple[bool, float | None]:
        """Does this phrase come from the enrolled voice? Fails closed if scoring breaks."""
        with self._lock:
            encoder, voiceprint, threshold = self._encoder, self._voiceprint, self._threshold
        if voiceprint is None:
            return True, None
        if encoder is None:
            # Gate is on but the model is not loaded (still starting, or missing): do not let anyone through.
            return False, None
        try:
            if audio.size < int(MIN_PHRASE_SECONDS * SAMPLE_RATE):
                return False, None
            score = sv.cosine_score(voiceprint, encoder.embed(tile_to_minimum(audio)))
        except Exception:
            logger.exception("Speaker scoring failed")
            return False, None
        ok = sv.is_same_speaker(score, threshold)
        with self._lock:
            self._last_score, self._last_ok, self._last_at = score, ok, time.monotonic()
        logger.info("Speaker check score=%.3f threshold=%.2f -> %s", score, threshold, "accepted" if ok else "rejected")
        return ok, score
