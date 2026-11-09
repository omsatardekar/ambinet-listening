import wave

from backend.app.wakeword import (
    FRAME_SAMPLES,
    SAMPLE_RATE,
    START_TRIM_SECONDS,
    STOP_TRIM_SECONDS,
    Token,
    WakeWordService,
    find_command,
    find_wake,
    tokens_from_result,
)

F = FRAME_SAMPLES


def _tokens(*items):
    """(word, start_frame_index, end_frame_index) in units of audio frames."""
    return [Token(word, start * F, end * F) for word, start, end in items]


def _service(tmp_path):
    service = WakeWordService(tmp_path / "offline_recordings")
    service._available = True
    return service


def _feed_frames(service, count):
    frame = bytes(F * 2)
    for _ in range(count):
        start = service._total_frames
        service._total_frames += F
        service._ring.append((start, frame))
        if service._writer is not None:
            service._writer.writeframesraw(frame)


def _wav_frames(service):
    saved = service.snapshot()["recordings"][0]
    with wave.open(str(service.audio_path(saved["session_id"])), "rb") as audio:
        assert (audio.getnchannels(), audio.getsampwidth(), audio.getframerate()) == (1, 2, SAMPLE_RATE)
        return audio.getnframes()


def test_tokens_skip_unknown_filler_and_use_absolute_frames():
    result = {"result": [
        {"word": "[unk]", "start": 0.0, "end": 0.1, "conf": 1.0},
        {"word": "hey", "start": 0.5, "end": 0.7, "conf": 0.9},
        {"word": "asha", "start": 0.7, "end": 1.0, "conf": 1.0},
    ]}
    tokens = tokens_from_result(result, offset_frame=1000)
    assert [t.word for t in tokens] == ["hey", "asha"]
    assert tokens[0].start == 1000 + 8000
    assert find_wake(tokens) == 1


def test_wake_needs_hey_and_enough_confidence():
    assert find_wake(_tokens(("asha", 0, 1))) == -1
    assert find_wake(_tokens(("hey", 0, 1), ("asha", 1, 2))) == 1
    weak = [Token("hey", 0, 1, 0.9), Token("asha", 1, 2, 0.2)]
    assert find_wake(weak) == -1


def test_commands_need_the_verb_directly_before_recording():
    tokens = _tokens(("start", 0, 1), ("recording", 1, 2), ("stop", 3, 4), ("recording", 4, 5))
    assert find_command(tokens, "start") == 1
    assert find_command(tokens, "stop") == 3
    assert find_command(_tokens(("recording", 0, 1), ("start", 1, 2)), "start") == -1


def test_start_recording_without_hey_asha_is_ignored(tmp_path):
    service = _service(tmp_path)
    service._handle_tokens(_tokens(("start", 0, 1), ("recording", 1, 2)))
    assert service.snapshot()["state"] == "listening"


def test_hey_asha_wakes_and_then_start_recording_starts(tmp_path):
    service = _service(tmp_path)
    service._handle_tokens(_tokens(("hey", 0, 1), ("asha", 1, 2)))
    assert service.snapshot()["state"] == "awake"
    service._handle_tokens(_tokens(("start", 10, 11), ("recording", 11, 12)))
    assert service.snapshot()["state"] == "recording"


def test_hey_asha_start_recording_in_one_breath(tmp_path):
    service = _service(tmp_path)
    service._handle_tokens(_tokens(("hey", 0, 1), ("asha", 1, 2), ("start", 3, 4), ("recording", 4, 5)))
    assert service.snapshot()["state"] == "recording"


def test_wake_window_expiry_requires_hey_asha_again(tmp_path):
    service = _service(tmp_path)
    service._handle_tokens(_tokens(("hey", 0, 1), ("asha", 1, 2)))
    service._armed_until = 0.0
    service._handle_tokens(_tokens(("start", 10, 11), ("recording", 11, 12)))
    assert service.snapshot()["state"] != "recording"


def test_saved_wav_starts_after_the_start_phrase(tmp_path):
    service = _service(tmp_path)
    _feed_frames(service, 20)
    # "start recording" ended at frame 10; the file must begin after the trim margin.
    service._handle_tokens(_tokens(("hey", 2, 4), ("asha", 4, 6), ("start", 7, 9), ("recording", 9, 10)))
    _feed_frames(service, 6)
    service._stop_cut = None
    service.stop_recording("button")
    first = 10 * F + int(START_TRIM_SECONDS * SAMPLE_RATE)
    first = -(-first // F)  # first whole frame at or after the trim point
    assert _wav_frames(service) == (26 - first) * F


def test_stop_needs_hey_asha_and_cuts_before_it(tmp_path):
    service = _service(tmp_path)
    service._handle_tokens(_tokens(("hey", 0, 1), ("asha", 1, 2), ("start", 2, 3), ("recording", 3, 4)))
    start_at = service._session_start_frame
    _feed_frames(service, 30)

    # "stop recording" alone must not stop the recording
    service._handle_tokens(_tokens(("stop", 40, 41), ("recording", 41, 42)))
    assert service.snapshot()["state"] == "recording"

    # "Hey Asha, stop recording": hey begins at frame 20
    service._handle_tokens(_tokens(("hey", 20, 21), ("asha", 21, 22), ("stop", 23, 24), ("recording", 24, 25)))
    assert service.snapshot()["state"] == "listening"
    cut = 20 * F - int(STOP_TRIM_SECONDS * SAMPLE_RATE)
    assert _wav_frames(service) == cut - start_at


def test_hey_asha_and_stop_recording_as_two_phrases(tmp_path):
    service = _service(tmp_path)
    service._handle_tokens(_tokens(("hey", 0, 1), ("asha", 1, 2), ("start", 2, 3), ("recording", 3, 4)))
    start_at = service._session_start_frame
    _feed_frames(service, 30)

    service._handle_tokens(_tokens(("hey", 20, 21), ("asha", 21, 22)))
    assert service.snapshot()["state"] == "recording"
    assert service.snapshot()["stop_armed"]
    service._handle_tokens(_tokens(("stop", 30, 31), ("recording", 31, 32)))

    assert service.snapshot()["state"] == "listening"
    assert _wav_frames(service) == 20 * F - int(STOP_TRIM_SECONDS * SAMPLE_RATE) - start_at


def test_button_start_and_stop_keep_all_audio(tmp_path):
    service = _service(tmp_path)
    assert service.start_recording("button")
    _feed_frames(service, 8)
    service.stop_recording("button")
    assert _wav_frames(service) == 8 * F
