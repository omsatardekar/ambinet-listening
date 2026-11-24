import numpy as np

from backend.app.speaker_gate import SpeakerGate, tile_to_minimum
from backend.app import speaker_verification as sv


class FakeEncoder:
    def embed(self, audio):
        return sv.l2_normalize(np.array([0.0, 1.0 if audio.mean() > 0 else -1.0, 0.0]))


def make_gate(tmp_path, voiceprint=None):
    gate = SpeakerGate(tmp_path)
    gate._encoder = FakeEncoder()
    if voiceprint is not None:
        gate._voiceprint = sv.l2_normalize(np.array(voiceprint, dtype=np.float32))
    return gate


def test_short_phrases_are_tiled_to_the_encoder_minimum():
    out = tile_to_minimum(np.ones(8000, dtype=np.float32))
    assert out.size == int(sv.MIN_SECONDS * sv.SAMPLE_RATE)


def test_gate_is_inactive_until_a_voice_is_enrolled(tmp_path):
    gate = make_gate(tmp_path)
    assert not gate.active
    assert gate.verify(np.ones(16000, dtype=np.float32)) == (True, None)


def test_matching_voice_is_accepted_and_other_voice_rejected(tmp_path):
    gate = make_gate(tmp_path, voiceprint=[0, 1, 0])
    assert gate.verify(np.ones(16000, dtype=np.float32) * 0.1)[0] is True
    assert gate.verify(-np.ones(16000, dtype=np.float32) * 0.1)[0] is False


def test_gate_fails_closed_when_the_model_is_not_loaded(tmp_path):
    gate = make_gate(tmp_path, voiceprint=[0, 1, 0])
    gate._encoder = None
    assert gate.verify(np.ones(16000, dtype=np.float32))[0] is False


def test_settings_and_voiceprint_survive_a_restart(tmp_path):
    gate = make_gate(tmp_path, voiceprint=[1, 0, 0])
    sv.save_voiceprint(gate._voiceprint, tmp_path / "voiceprint.npy")
    gate.configure(enabled=False, threshold=0.5)
    again = SpeakerGate(tmp_path)
    assert again.enrolled and not again.status()["enabled"] and again.status()["threshold"] == 0.5
    again.delete_voiceprint()
    assert not SpeakerGate(tmp_path).enrolled
