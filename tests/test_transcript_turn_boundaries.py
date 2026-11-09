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


def _finalize(segments, utterances, registry=None):
    registry = registry or [
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


def _utt(speaker, text, indices, confidence=0.9):
    role = "PATIENT" if speaker == "person_1" else "DOCTOR"
    return {"canonical_speaker_id": speaker, "role": role, "text": text,
            "source_segment_indices": indices, "attribution_confidence": confidence,
            "attribution_status": "CONFIDENT", "reconstruction_type": "UNCHANGED"}


def test_consecutive_same_speaker_segments_become_one_utterance():
    segments = [
        _seg("speaker_1", 0, "I brought the packet slash notes with me."),
        _seg("speaker_1", 3, "I am not sure which detail matters though."),
        _seg("speaker_2", 6, "Start wherever it makes sense."),
    ]
    result = _finalize(segments, [
        _utt("person_1", "I brought the packet/notes with me. I am not sure which detail matters though.", [0, 1]),
        _utt("person_2", "Start wherever it makes sense.", [2]),
    ])
    first = result["utterances"][0]
    assert first["source_segment_indices"] == [0, 1]
    assert first["canonical_speaker_id"] == "person_1"
    assert first["reconstruction_type"] == "MERGED_FRAGMENTS"
    assert first["start_seconds"] == 0 and first["end_seconds"] == 5
    assert len(result["utterances"]) == 2
    assert not any(f["type"] == "MERGED_SOURCE_TURNS_REVIEW" for f in result["review_flags"])


def test_stray_one_word_fragment_with_other_speaker_id_is_repaired():
    segments = [
        _seg("speaker_1", 0, "We."),
        _seg("speaker_2", 1, "Can work through it together."),
        _seg("speaker_2", 4, "Start wherever it makes sense to you."),
    ]
    result = _finalize(segments, [
        _utt("person_2", "We can work through it together. Start wherever it makes sense to you.", [0, 1, 2]),
    ])
    assert len(result["utterances"]) == 1
    assert result["utterances"][0]["source_segment_indices"] == [0, 1, 2]
    assert result["utterances"][0]["canonical_speaker_id"] == "person_2"


def test_fragment_merge_needs_confidence():
    segments = [_seg("speaker_1", 0, "We."), _seg("speaker_2", 1, "Can work through it together.")]
    result = _finalize(segments, [_utt("person_2", "We can work through it together.", [0, 1], confidence=0.4)])
    assert len(result["utterances"]) == 2
    assert any(f["type"] == "MERGED_SOURCE_TURNS_REVIEW" for f in result["review_flags"])


def test_non_consecutive_segments_are_never_merged():
    segments = [
        _seg("speaker_1", 0, "My head hurts."),
        _seg("speaker_2", 3, "Since when?"),
        _seg("speaker_1", 6, "Since Monday."),
    ]
    result = _finalize(segments, [_utt("person_1", "My head hurts. Since Monday.", [0, 2])])
    assert any(f["type"] == "MERGED_SOURCE_TURNS_REVIEW" for f in result["review_flags"])
    assert all(item["canonical_speaker_id"] == "UNKNOWN" for item in result["utterances"] if item["source_segment_indices"] in ([0], [2]))


def test_merge_to_unregistered_or_unknown_speaker_is_separated():
    segments = [_seg("speaker_1", 0, "First part."), _seg("speaker_1", 3, "Second part.")]
    result = _finalize(segments, [_utt("UNKNOWN", "First part. Second part.", [0, 1])])
    assert [item["source_segment_indices"] for item in result["utterances"]] == [[0], [1]]


def test_v2_prompt_is_v1_plus_addendum_and_v1_is_unchanged():
    from pathlib import Path

    prompts = Path(__file__).resolve().parents[1] / "prompts"
    v1 = (prompts / "agent_instructions.md").read_text(encoding="utf-8").replace("\r\n", "\n").strip()
    v2 = (prompts / "agent_instructions_v2.md").read_text(encoding="utf-8").replace("\r\n", "\n")
    assert "prompt-version: 2" in v2.splitlines()[0]
    assert v1 in v2
    assert "ADDENDUM v2" in v2 and "slash" in v2
