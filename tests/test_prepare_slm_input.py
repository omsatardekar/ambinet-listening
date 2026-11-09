from scripts import prepare_slm_input as slm_preparation


def test_prepare_compact_transcript_matches_slm_input_contract():
    source = {
        "schema_version": "1.0",
        "encounter_id": "01",
        "source_blob": "01transcript.json",
        "processing_status": "NEEDS_REVIEW",
        "review_flags": [{"type": "ROLE_UNCERTAIN"}],
        "utterances": [
            {
                "canonical_speaker_id": "person_1",
                "role": "DOCTOR",
                "start_seconds": 0.64,
                "end_seconds": 7.4,
                "duration_seconds": 6.76,
                "text": "What would you most like us to focus on today?",
            },
            {
                "canonical_speaker_id": "person_2",
                "role": "NURSE",
                "start_seconds": 8.76,
                "end_seconds": 15.0,
                "duration_seconds": 6.24,
                "text": "I can confirm the observation I took.",
            },
        ],
    }

    compact, manifest = slm_preparation.prepare_compact_transcript(source)

    assert compact == {
        "schema_version": "1.0",
        "encounter_id": "01",
        "segments": [
            {
                "segment_id": "SEG0001",
                "speaker_id": "person_1",
                "role": "DOCTOR",
                "start_seconds": 0.64,
                "end_seconds": 7.4,
                "duration_seconds": 6.76,
                "text": "What would you most like us to focus on today?",
            },
            {
                "segment_id": "SEG0002",
                "speaker_id": "person_2",
                "role": "NURSE",
                "start_seconds": 8.76,
                "end_seconds": 15.0,
                "duration_seconds": 6.24,
                "text": "I can confirm the observation I took.",
            },
        ],
    }
    assert manifest["review_status"] == "NEEDS_REVIEW"
    assert manifest["slm_eligible"] is False
