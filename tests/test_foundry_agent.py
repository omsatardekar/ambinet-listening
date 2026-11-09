import json

from scripts.foundry_agent import FoundryAgent


class FakeResponse:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self._body = body
        self.text = ""
        self.headers = {}
        self.ok = status_code < 400

    def json(self):
        return self._body


class FakeSession:
    def __init__(self, responses):
        self.headers = {}
        self.responses = iter(responses)
        self.requests = []

    def request(self, method, url, **kwargs):
        self.requests.append((method, url, kwargs))
        return next(self.responses)


def make_agent(responses):
    agent = FoundryAgent(
        endpoint="https://foundry.example",
        api_key="test-key",
        model="deployment",
        agent_name="clinical-reconstruction",
        max_retries=0,
    )
    session = FakeSession(responses)
    agent.session = session
    return agent, session


def test_force_update_creates_a_new_version_for_an_existing_agent():
    agent, session = make_agent([
        FakeResponse(200, {"name": "clinical-reconstruction"}),
        FakeResponse(201, {"name": "clinical-reconstruction", "version": "2"}),
    ])

    result = agent.ensure_agent("updated instructions", force_update=True)

    assert result["version"] == "2"
    assert [request[0] for request in session.requests] == ["GET", "POST"]
    method, url, kwargs = session.requests[1]
    assert method == "POST"
    assert url == (
        "https://foundry.example/agents/clinical-reconstruction/versions"
        "?api-version=v1"
    )
    assert kwargs["json"] == {
        "definition": {
            "kind": "prompt",
            "model": "deployment",
            "instructions": "updated instructions",
        }
    }


def test_existing_agent_is_reused_without_force_update():
    agent, session = make_agent([
        FakeResponse(200, {"name": "clinical-reconstruction"}),
    ])

    agent.ensure_agent("new instructions")

    assert len(session.requests) == 1
    assert session.requests[0][0] == "GET"


def test_reconstruction_request_distinguishes_doctor_nurse_and_other_clinical_staff():
    agent, session = make_agent([
        FakeResponse(200, {"output_text": "{}"}),
    ])

    agent.reconstruct({"segments": []}, "instructions")

    request_payload = json.loads(session.requests[0][2]["json"]["input"])
    role_rules = request_payload["output_rules"]
    assert "Use DOCTOR only" in role_rules
    assert "Use NURSE only" in role_rules
    assert "Use OTHER_CLINICAL_STAFF only" in role_rules


def test_missing_agent_is_created():
    agent, session = make_agent([
        FakeResponse(404, {}),
        FakeResponse(201, {"name": "clinical-reconstruction", "version": "1"}),
    ])

    agent.ensure_agent("initial instructions")

    assert [request[0] for request in session.requests] == ["GET", "POST"]
    method, url, kwargs = session.requests[1]
    assert method == "POST"
    assert url == "https://foundry.example/agents?api-version=v1"
    assert kwargs["json"]["name"] == "clinical-reconstruction"
