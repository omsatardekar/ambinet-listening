from pathlib import Path
import wave
from ambient_tts import SR

def test_output_wav_format_when_generated():
    root = Path(__file__).parents[1] / "output" / "clinical_audio_dataset"
    wavs = list(root.glob("encounter_*/audio.wav"))
    if not wavs:
        return  # Audio is intentionally not generated during project packaging.
    for path in wavs:
        with wave.open(str(path), "rb") as w:
            assert (w.getnchannels(), w.getsampwidth(), w.getframerate()) == (1, 2, SR)
