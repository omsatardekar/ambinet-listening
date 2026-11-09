from backend.app.progress import ProgressManager


def test_progress_replays_events_and_exposes_completed_result():
    progress = ProgressManager()
    run_id, duplicate = progress.create("visit.wav", "sha256-value")

    assert not duplicate
    progress.update(
        run_id,
        "audio_upload",
        "completed",
        "Audio uploaded.",
        15,
        stage_status="completed",
    )
    progress.update(
        run_id,
        "speech_transcription",
        "in_progress",
        "Speech is processing.",
        23,
        stage_status="in_progress",
    )

    events, terminal = progress.events_after(run_id, 1)

    assert [event["sequence"] for event in events] == [2, 3]
    assert events[-1]["stage"] == "speech_transcription"
    assert events[-1]["run_status"] == "running"
    assert not terminal

    result = {"processing_status": "NEEDS_REVIEW", "utterances": []}
    progress.update(
        run_id,
        "final_transcript",
        "completed",
        "Final uploaded.",
        100,
        stage_status="completed",
    )
    progress.complete(run_id, result)

    assert progress.status(run_id)["status"] == "completed"
    assert progress.result(run_id) == result
    completed_events, terminal = progress.events_after(run_id, 0)
    assert terminal
    assert completed_events[-1]["run_status"] == "completed"


def test_duplicate_fingerprint_reuses_the_existing_run():
    progress = ProgressManager()
    first_run, duplicate = progress.create("visit.wav", "same-content")
    second_run, duplicate_again = progress.create("renamed.wav", "same-content")

    assert not duplicate
    assert duplicate_again
    assert second_run == first_run
    assert progress.status(second_run)["filename"] == "visit.wav"
