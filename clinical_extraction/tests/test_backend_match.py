"""Backend segment matching for facts the model did not cite (the H1 prompt never asks for segment ids)."""
from clinical_extraction import evidence

COMPACT = {"encounter_id": "t", "segments": [
    {"segment_id": "SEG0001", "speaker_id": "p1", "role": "DOCTOR", "start_seconds": 0, "end_seconds": 2, "text": "What brings you in today?"},
    {"segment_id": "SEG0002", "speaker_id": "p2", "role": "PATIENT", "start_seconds": 3, "end_seconds": 6, "text": "I have had right knee pain for two weeks."},
    {"segment_id": "SEG0003", "speaker_id": "p1", "role": "DOCTOR", "start_seconds": 7, "end_seconds": 9, "text": "Any allergies to medication?"},
]}


def test_uncited_fact_is_matched_and_labelled():
    ex = {"symptoms": [{"name": "knee pain", "body_site": "right knee", "status": "present", "evidence_ids": []}]}
    out = evidence.resolve_all(ex, COMPACT)
    fact = out["facts"][0]
    assert fact["source"] == "backend_matched" and fact["segments"][0]["segment_id"] == "SEG0002"
    assert fact["segments"][0]["match_score"] >= 0.5
    assert out["totals"]["backend_matched_facts"] == 1 and out["totals"]["references"] == 0       # not counted as model citations
    assert ex["symptoms"][0]["evidence_ids"] == []                                                # raw output untouched


def test_invented_fact_finds_nothing():
    out = evidence.resolve_all({"symptoms": [{"name": "chest tightness", "evidence_ids": []}]}, COMPACT)
    assert out["facts"][0]["source"] == "none" and out["facts"][0]["segments"] == []
    assert out["totals"]["unmatched_facts"] == 1


def test_model_citation_wins_over_matching():
    ex = {"symptoms": [{"name": "knee pain", "evidence_ids": ["SEG0001"]}]}
    fact = evidence.resolve_all(ex, COMPACT)["facts"][0]
    assert fact["source"] == "model_cited" and [s["segment_id"] for s in fact["segments"]] == ["SEG0001"]


# ---- spoken numbers and placeholder fields (found on live runs 1 and 2) ------------------------------------------------------------
VITALS = {"encounter_id": "t", "segments": [
    {"segment_id": "SEG0001", "speaker_id": "p1", "role": "DOCTOR", "start_seconds": 0, "end_seconds": 3, "text": "Let me check your pulse and pressure."},
    {"segment_id": "SEG0002", "speaker_id": "p1", "role": "DOCTOR", "start_seconds": 4, "end_seconds": 7, "text": "Seventy-five, nice and steady."},
    {"segment_id": "SEG0003", "speaker_id": "p1", "role": "DOCTOR", "start_seconds": 8, "end_seconds": 12, "text": "One twenty-four over seventy-nine, that's perfectly good."},
    {"segment_id": "SEG0004", "speaker_id": "p2", "role": "NURSE", "start_seconds": 13, "end_seconds": 16, "text": "Thirty-eight point three."},
    {"segment_id": "SEG0005", "speaker_id": "p1", "role": "DOCTOR", "start_seconds": 17, "end_seconds": 20, "text": "Any allergies? Diclofenac gave him a rash, apparently."},
]}


def test_spoken_numbers_become_digits():
    assert evidence.spoken_numbers("One oh nine over seventy-seven.").split()[0] == "109/77"
    assert evidence.spoken_numbers("One twenty-four over seventy-nine").split()[0] == "124/79"
    assert evidence.spoken_numbers("Thirty-eight point three.") == "38.3"
    assert evidence.spoken_numbers("Seventy-five, nice and steady.") == "75"
    assert evidence.spoken_numbers("Oh, that may be it.") == ""


def test_vitals_are_linked_by_their_value():
    ex = {"vital_signs": [{"name": "blood pressure", "value": "124/79", "unit": "mmHg", "evidence_ids": []},
                          {"name": "heart rate", "value": "75", "unit": "bpm", "evidence_ids": []},
                          {"name": "temperature", "value": "38.3", "unit": "C", "evidence_ids": []}]}
    out = {f["path"]: f for f in evidence.resolve_all(ex, VITALS)["facts"]}
    assert [s["segment_id"] for s in out["vital_signs[0]"]["segments"]] == ["SEG0003"]
    assert [s["segment_id"] for s in out["vital_signs[1]"]["segments"]] == ["SEG0002"]
    assert [s["segment_id"] for s in out["vital_signs[2]"]["segments"]] == ["SEG0004"]


def test_placeholder_and_rarely_spoken_fields_do_not_hide_an_allergy():
    ex = {"allergies": [{"substance": "diclofenac", "allergy_type": "medication", "reaction": None, "severity": "unknown", "status": "reported", "evidence_ids": []}]}
    fact = evidence.resolve_all(ex, VITALS)["facts"][0]
    assert fact["source"] == "backend_matched" and fact["segments"][0]["segment_id"] == "SEG0005"
