import wave

import pytest

from backend.app.wakeword import (
    FRAME_SAMPLES,
    SAMPLE_RATE,
    WakeWordService,
    contains_wake_word,
    has_start_command,
    has_stop_command,
    normalize_words,
)


@pytest.mark.parametrize(
    "text",
    ["Hey Asha.", "Hey Aisha", "Hiya Shah.", "Hey Shah", "Okay, Asha", "Asha", "Hello 1 2 Hey Asha"],
)
def test_wake_phrase_variants_are_recognised(text):
    assert contains_wake_word(normalize_words(text)) >= 0


@pytest.mark.parametrize(
    "text",
    ["Asia, can you check the dose", "the patient has asthma", "we should stop taking the tablets"],
)
def test_ordinary_speech_does_not_wake_the_assistant(text):
    assert contains_wake_word(normalize_words(text)) < 0


def test_start_and_stop_commands_are_matched_in_context():
    assert has_start_command(normalize_words("Hey Asha, start recording"))
    assert has_stop_command(normalize_words("hey asha stop recording"))
    assert has_stop_command(normalize_words("Stop the recording."))
    assert not has_start_command(normalize_words("I started recording my notes last week"))


def test_start_before_wake_word_is_ignored(tmp_path):
    service = WakeWordService(tmp_path / "offline_recordings")
    service._available = True

    service._handle_text("Start recording.", start_frame=0)

    assert service.snapshot()["state"] == "listening"
    assert service.snapshot()["current"] is None


def test_wake_then_start_then_stop_saves_one_wav(tmp_path):
    service = WakeWordService(tmp_path / "offline_recordings")
    service._available = True

    service._handle_text("Hey Asha", start_frame=0)
    assert service.snapshot()["state"] == "awake"

    service._handle_text("start recording", start_frame=0)
    assert service.snapshot()["state"] == "recording"

    frame = bytes(FRAME_SAMPLES * 2)
    for _ in range(8):
        service._writer.writeframesraw(frame)
        service._total_frames += FRAME_SAMPLES

    service._handle_text("Hey Asha, stop recording", start_frame=service._total_frames)

    snapshot = service.snapshot()
    assert snapshot["state"] == "listening"
    saved = snapshot["recordings"][0]
    wav_path = service.audio_path(saved["session_id"])
    assert wav_path is not None
    assert wav_path.parent == tmp_path / "offline_recordings"
    with wave.open(str(wav_path), "rb") as audio:
        assert (audio.getnchannels(), audio.getsampwidth(), audio.getframerate()) == (1, 2, SAMPLE_RATE)
        assert audio.getnframes() == FRAME_SAMPLES * 8


def test_stop_trims_audio_after_the_stop_phrase(tmp_path):
    service = WakeWordService(tmp_path / "offline_recordings")
    service._available = True
    service._handle_text("Hey Asha", start_frame=0)
    service._handle_text("start recording", start_frame=0)

    frame = bytes(FRAME_SAMPLES * 2)
    for _ in range(10):
        service._writer.writeframesraw(frame)
        service._total_frames += FRAME_SAMPLES

    # The stop phrase began after 4 frames; everything from there on is dropped.
    service._handle_text("stop recording", start_frame=4 * FRAME_SAMPLES)

    saved = service.snapshot()["recordings"][0]
    with wave.open(str(service.audio_path(saved["session_id"])), "rb") as audio:
        assert audio.getnframes() == 4 * FRAME_SAMPLES
