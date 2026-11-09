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
