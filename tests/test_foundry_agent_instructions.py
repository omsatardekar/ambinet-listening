import json

from scripts.foundry_agent import FoundryAgent


def test_current_reconstruction_instructions_are_sent_with_each_request(monkeypatch):
    instructions = "Preserve every source turn and keep uncertain attribution for review."
    captured_payload = {}

    class Response:
        ok = True

        @staticmethod
        def json():
            return {"output_text": json.dumps({"speaker_registry": [], "utterances": []})}

    agent = FoundryAgent(
        endpoint="https://example.invalid",
        api_key="test-key",
        model="test-model",
        agent_name="test-agent",
    )

    def fake_request(_method, _url, **kwargs):
        captured_payload.update(json.loads(kwargs["json"]["input"]))
        return Response()

    monkeypatch.setattr(agent, "_request", fake_request)

    agent.reconstruct({"segments": []}, instructions)

    assert captured_payload["reconstruction_instructions"] == instructions
