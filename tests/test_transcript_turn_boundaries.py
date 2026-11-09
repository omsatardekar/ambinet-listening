from backend.app.pipeline import transcript_processing


def test_coarse_diarization_does_not_assume_hidden_participants():
    encounter = transcript_processing.compact_encounter(
        {
            "speech_job_id": None,
            "segments": [
                {"speaker_id": "speaker_1", "start_seconds": 0, "duration_seconds": 2, "text": "Good morning."},
                {"speaker_id": "speaker_2", "start_seconds": 2, "duration_seconds": 2, "text": "Thank you."},
            ],
        },
        "01transcript.json",
    )

    assert "do not assume" in encounter["important_instruction"].lower()
    assert "do not invent speakers or roles" in encounter["important_instruction"].lower()
    assert len(encounter["segments"]) == 2


def test_merged_source_turns_are_separated_and_flagged_for_review():
    segments = [
        {
            "speaker_id": "speaker_1",
            "start_seconds": 0,
            "duration_seconds": 2,
            "text": "We should verify the dose.",
        },
        {
            "speaker_id": "speaker_2",
            "start_seconds": 2,
            "duration_seconds": 2,
            "text": "I can check the list.",
        },
    ]
    result = transcript_processing.validate_and_finalize(
        {
            "speaker_registry": [
                {
                    "canonical_speaker_id": "person_1",
                    "role": "DOCTOR",
                    "role_confidence": 0.9,
                    "attribution_status": "CONFIDENT",
                }
            ],
            "utterances": [
                {
                    "canonical_speaker_id": "person_1",
                    "role": "DOCTOR",
                    "text": "We should verify the dose. I can check the list.",
                    "source_segment_indices": [0, 1],
                    "attribution_confidence": 0.9,
                    "attribution_status": "CONFIDENT",
                    "reconstruction_type": "MERGED_FRAGMENTS",
                }
            ],
        },
        {"segments": segments, "recording_id": "01"},
        "01transcript.json",
    )

    assert [item["text"] for item in result["utterances"]] == [
        "We should verify the dose.",
        "I can check the list.",
    ]
    assert [item["canonical_speaker_id"] for item in result["utterances"]] == [
        "UNKNOWN",
        "UNKNOWN",
    ]
    assert result["processing_status"] == "NEEDS_REVIEW"
    assert result["speaker_registry"] == []
    assert any(flag["type"] == "MERGED_SOURCE_TURNS_REVIEW" for flag in result["review_flags"])



def _finalize(segments, utterances):
    registry = [
        {"canonical_speaker_id": "person_1", "role": "PATIENT", "role_confidence": 0.9,
         "attribution_status": "CONFIDENT"},
        {"canonical_speaker_id": "person_2", "role": "DOCTOR", "role_confidence": 0.9,
         "attribution_status": "CONFIDENT"},
    ]
    return transcript_processing.validate_and_finalize(
        {"speaker_registry": registry, "utterances": utterances},
        {"segments": segments, "recording_id": "01"},
        "01transcript.json",
    )


def _seg(speaker, start, text):
    return {"speaker_id": speaker, "start_seconds": start, "duration_seconds": 2, "text": text}


def _utt(speaker, text, index, status="CONFIDENT", confidence=0.9):
    return {"canonical_speaker_id": speaker, "text": text, "source_segment_indices": [index],
            "attribution_confidence": confidence, "attribution_status": status,
            "reconstruction_type": "UNCHANGED"}


def test_consecutive_same_speaker_utterances_become_one_turn():
    segments = [
        _seg("speaker_1", 0, "I brought the packet slash notes with me."),
        _seg("speaker_1", 3, "I am not sure which detail matters though."),
        _seg("speaker_2", 6, "Start wherever it makes sense."),
    ]
    result = _finalize(segments, [
        _utt("person_1", "I brought the packet slash notes with me.", 0),
        _utt("person_1", "I am not sure which detail matters though.", 1),
        _utt("person_2", "Start wherever it makes sense.", 2),
    ])
    first, second = result["utterances"]
    assert first["text"] == "I brought the packet/notes with me. I am not sure which detail matters though."
    assert first["source_segment_indices"] == [0, 1]
    assert first["reconstruction_type"] == "MERGED_FRAGMENTS"
    assert (first["start_seconds"], first["end_seconds"], first["duration_seconds"]) == (0, 5, 5)
    assert first["utterance_id"] == "U0001" and second["utterance_id"] == "U0002"
    assert second["canonical_speaker_id"] == "person_2"


def test_stray_fragment_is_joined_and_does_not_force_review():
    segments = [
        _seg("speaker_1", 0, "We."),
        _seg("speaker_2", 1, "Can work through it together."),
        _seg("speaker_2", 4, "Start wherever it makes sense to you."),
    ]
    result = _finalize(segments, [
        _utt("person_2", "We.", 0, status="NEEDS_REVIEW", confidence=0.55),
        _utt("person_2", "Can work through it together.", 1),
        _utt("person_2", "Start wherever it makes sense to you.", 2),
    ])
    assert len(result["utterances"]) == 1
    turn = result["utterances"][0]
    assert turn["text"] == "We can work through it together. Start wherever it makes sense to you."
    assert turn["source_segment_indices"] == [0, 1, 2]
    assert turn["original_azure_speaker_ids"] == ["speaker_1", "speaker_2"]


def test_complete_short_phrase_is_not_mangled_when_joined():
    segments = [_seg("speaker_2", 0, "Thank you."), _seg("speaker_2", 3, "I will keep it.")]
    result = _finalize(segments, [_utt("person_2", "Thank you.", 0), _utt("person_2", "I will keep it.", 1)])
    assert [u["text"] for u in result["utterances"]] == ["Thank you. I will keep it."]


def test_different_speakers_and_gaps_are_never_merged():
    segments = [
        _seg("speaker_1", 0, "My head hurts."),
        _seg("speaker_2", 3, "Since when?"),
        _seg("speaker_1", 6, "Since Monday."),
    ]
    result = _finalize(segments, [
        _utt("person_1", "My head hurts.", 0),
        _utt("person_2", "Since when?", 1),
        _utt("person_1", "Since Monday.", 2),
    ])
    assert [u["canonical_speaker_id"] for u in result["utterances"]] == ["person_1", "person_2", "person_1"]


def test_unknown_speakers_are_not_merged():
    segments = [_seg("speaker_1", 0, "First part."), _seg("speaker_1", 3, "Second part.")]
    result = _finalize(segments, [_utt("UNKNOWN", "First part.", 0), _utt("UNKNOWN", "Second part.", 1)])
    assert len(result["utterances"]) == 2


def test_merge_can_be_disabled(monkeypatch):
    monkeypatch.setattr(transcript_processing, "MERGE_SAME_SPEAKER_TURNS", False)
    segments = [_seg("speaker_1", 0, "One."), _seg("speaker_1", 3, "Two.")]
    result = _finalize(segments, [_utt("person_1", "One.", 0), _utt("person_1", "Two.", 1)])
    assert len(result["utterances"]) == 2


def test_dictated_slash_is_converted_without_touching_other_text():
    assert transcript_processing.normalize_dictation("BP was one twenty slash eighty") == "BP was one twenty/eighty"
    assert transcript_processing.normalize_dictation("120 slash 80") == "120/80"
    assert transcript_processing.normalize_dictation("Slash the dose") == "Slash the dose"


def test_v2_prompt_is_v1_plus_a_normalization_only_addendum():
    from pathlib import Path

    prompts = Path(__file__).resolve().parents[1] / "prompts"
    v1 = (prompts / "agent_instructions.md").read_text(encoding="utf-8").replace(chr(13) + chr(10), chr(10)).strip()
    v2 = (prompts / "agent_instructions_v2.md").read_text(encoding="utf-8").replace(chr(13) + chr(10), chr(10))
    assert "prompt-version: 2" in v2.splitlines()[0]
    assert v1 in v2
    addendum = v2.split("ADDENDUM v2", 1)[1]
    assert "slash" in addendum
    assert "MERGED_FRAGMENTS" not in addendum  # merging is done in code, not requested from the model


def test_estimated_progress_moves_forward_and_never_reaches_its_end():
    import time

    from backend.app.pipeline import _EstimatedProgress
    from backend.app.progress import ProgressManager

    progress = ProgressManager()
    run_id, _ = progress.create("a.wav", "fp")
    with _EstimatedProgress(progress, run_id, "speech_transcription", "m", "op", 20, 40, 5.0, interval=0.02):
        time.sleep(0.4)
    percent = progress.status(run_id)["percent"]
    assert 20 < percent < 40
    progress.update(run_id, "speech_transcription", "in_progress", "m", 10)
    assert progress.status(run_id)["percent"] == percent  # the bar never goes backwards
