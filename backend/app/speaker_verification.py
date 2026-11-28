"""ECAPA-TDNN speaker embeddings for voice enrollment and comparison.
This module only answers "does this audio match the enrolled voice?". It does not
start or stop recordings, and it is not wired into the WebSocket or wake-word flow yet.
Audio contract: mono float32 samples in [-1, 1] at 16 kHz.
The SpeechBrain import is lazy, so the helpers and tests work without PyTorch installed.
Run from the `backend` folder with the venv active:
    python -m app.speaker_verification enroll --out voiceprint.npy clip1.wav clip2.wav
    python -m app.speaker_verification verify --voiceprint voiceprint.npy test.wav
"""
from __future__ import annotations
import argparse
import os
import wave
from pathlib import Path
from typing import Sequence
import numpy as np
SAMPLE_RATE = 16000
MODEL_SOURCE = os.getenv("SPEAKER_MODEL_SOURCE", "speechbrain/spkrec-ecapa-voxceleb")
MODEL_DIR = Path(os.getenv("SPEAKER_MODEL_DIR", "pretrained_models/spkrec-ecapa-voxceleb"))
MIN_SECONDS = 1.5            # shorter speech gives unreliable embeddings
ENROLL_WINDOW_SECONDS = 3.0  # enrollment clips are cut into windows, one embedding each
# Starting point only. Tune on your own mic and room before relying on it.
DEFAULT_THRESHOLD = 0.25
# The model files are bundled in the repository (like the Vosk voice model), so nothing is downloaded and it works behind company firewalls.
BUNDLED_MODEL_DIR = Path(__file__).resolve().parents[2] / "models" / "spkrec-ecapa-voxceleb"


def bundled_model_ready() -> bool:
    return all((BUNDLED_MODEL_DIR / n).is_file() for n in ("hyperparams.yaml", "embedding_model.ckpt", "mean_var_norm_emb.ckpt", "classifier.ckpt", "label_encoder.ckpt"))


class SpeakerEncoder:
    """Wraps the pretrained ECAPA-TDNN model. Load once, reuse for every embedding."""
    def __init__(self, source: str = MODEL_SOURCE, savedir: Path = MODEL_DIR, device: str = "cpu"):
        from speechbrain.inference.speaker import EncoderClassifier  # lazy: heavy dependency
        from speechbrain.utils.fetching import LocalStrategy

        # COPY instead of the default SYMLINK: Windows blocks symlinks without admin or Developer Mode.
        self._encoder = EncoderClassifier.from_hparams(
            source=source,
            savedir=str(savedir),
            run_opts={"device": device},
            local_strategy=LocalStrategy.COPY,
        )
    def embed(self, samples: np.ndarray) -> np.ndarray:
        """Return one unit-length embedding (192 values) for a mono 16 kHz clip."""
        import torch
        audio = validate_audio(samples)
        wave_tensor = torch.from_numpy(audio).unsqueeze(0)  # shape (1, time)
        with torch.no_grad():
            embedding = self._encoder.encode_batch(wave_tensor)
        return l2_normalize(embedding.squeeze().cpu().numpy())
def validate_audio(samples: np.ndarray) -> np.ndarray:
    audio = np.asarray(samples, dtype=np.float32).reshape(-1)
    if not np.all(np.isfinite(audio)):
        raise ValueError("Audio contains NaN or infinite values.")
    if audio.size < int(MIN_SECONDS * SAMPLE_RATE):
        raise ValueError(f"Need at least {MIN_SECONDS} seconds of speech.")
    return audio
def l2_normalize(vector: np.ndarray) -> np.ndarray:
    vector = np.asarray(vector, dtype=np.float32).reshape(-1)
    norm = float(np.linalg.norm(vector))
    if norm == 0.0:
        raise ValueError("Cannot normalise a zero vector.")
    return vector / norm
def average_voiceprint(embeddings: Sequence[np.ndarray]) -> np.ndarray:
    """Combine enrollment embeddings into one unit-length voiceprint."""
    if not embeddings:
        raise ValueError("Enrollment needs at least one embedding.")
    stacked = np.stack([l2_normalize(e) for e in embeddings])
    return l2_normalize(stacked.mean(axis=0))
def cosine_score(voiceprint: np.ndarray, embedding: np.ndarray) -> float:
    """Similarity in [-1, 1]. Higher means more alike."""
    return float(np.dot(l2_normalize(voiceprint), l2_normalize(embedding)))
def is_same_speaker(score: float, threshold: float = DEFAULT_THRESHOLD) -> bool:
    return score >= threshold
def read_wav(path: Path) -> np.ndarray:
    """Read a mono 16-bit 16 kHz WAV as float32. Other formats are rejected, not resampled."""
    with wave.open(str(path), "rb") as wav:
        if wav.getnchannels() != 1 or wav.getsampwidth() != 2 or wav.getframerate() != SAMPLE_RATE:
            raise ValueError(f"{path}: expected mono, 16-bit, 16 kHz WAV.")
        raw = wav.readframes(wav.getnframes())
    return np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
def split_windows(audio: np.ndarray, window_seconds: float = ENROLL_WINDOW_SECONDS) -> list[np.ndarray]:
    """Cut audio into fixed windows. A short final window is kept only if it is long enough."""
    size = int(window_seconds * SAMPLE_RATE)
    windows = [audio[start:start + size] for start in range(0, len(audio), size)]
    return [w for w in windows if w.size >= int(MIN_SECONDS * SAMPLE_RATE)]
def enroll(encoder: SpeakerEncoder, wav_paths: Sequence[Path]) -> np.ndarray:
    embeddings: list[np.ndarray] = []
    for path in wav_paths:
        for window in split_windows(read_wav(Path(path))):
            embeddings.append(encoder.embed(window))
    if not embeddings:
        raise ValueError("No usable speech found in the enrollment clips.")
    return average_voiceprint(embeddings)
def save_voiceprint(voiceprint: np.ndarray, path: Path) -> None:
    # A voiceprint is biometric data. Keep it on this machine.
    np.save(str(path), voiceprint)
def load_voiceprint(path: Path) -> np.ndarray:
    return np.load(str(path))
def _main() -> None:
    parser = argparse.ArgumentParser(description="Enroll or verify a voice with ECAPA-TDNN.")
    commands = parser.add_subparsers(dest="command", required=True)
    enroll_cmd = commands.add_parser("enroll", help="Build a voiceprint from clean clips of one speaker.")
    enroll_cmd.add_argument("--out", required=True, type=Path)
    enroll_cmd.add_argument("clips", nargs="+", type=Path)
    verify_cmd = commands.add_parser("verify", help="Score a clip against a saved voiceprint.")
    verify_cmd.add_argument("--voiceprint", required=True, type=Path)
    verify_cmd.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    verify_cmd.add_argument("clip", type=Path)
    args = parser.parse_args()
    encoder = SpeakerEncoder()
    if args.command == "enroll":
        voiceprint = enroll(encoder, args.clips)
        save_voiceprint(voiceprint, args.out)
        print(f"Saved voiceprint to {args.out}")
        return
    voiceprint = load_voiceprint(args.voiceprint)
    embedding = encoder.embed(read_wav(args.clip))
    score = cosine_score(voiceprint, embedding)
    print(f"score={score:.3f} threshold={args.threshold:.3f} same_speaker={is_same_speaker(score, args.threshold)}")
if __name__ == "__main__":
    _main()