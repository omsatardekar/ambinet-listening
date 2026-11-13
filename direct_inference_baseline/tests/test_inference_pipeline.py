import builtins
import json
import re
from pathlib import Path

import pytest
import requests

from direct_inference_baseline.config import settings as S
from direct_inference_baseline.inference import inference_runner as IR
from direct_inference_baseline.inference.base_client import (BaseClient, GenerationResult, PermanentInferenceError, TransientInferenceError)
from direct_inference_baseline.inference.foundry_client import FoundryClient
from direct_inference_baseline.inference.output_parser import parse_response


# ------------------------------------------------------------------ parser
def test_parser_ok_fenced_and_think():
    assert parse_response('{"a": 1}').status == "ok"
    r = parse_response('<think>hmm</think>\n```json\n{"a": 1}\n```')
    assert r.status == "ok" and r.data == {"a": 1} and len(r.notes) == 2


def test_parser_truncated_is_not_repaired():
    r = parse_response('{"symptoms": [{"name": "fev', "length")
    assert r.status == "truncated" and r.data is None
    assert parse_response('{"symptoms": [', "stop").status == "invalid_json"


@pytest.mark.parametrize("text,status", [("", "empty"), (None, "empty"), ("   \n", "empty"), ("[1,2]", "not_object"),
                                          ("Sure! Here is the JSON: {\"a\":1}", "invalid_json"), ('{"a": 1} trailing', "invalid_json")])
def test_parser_failure_modes(text, status):
    assert parse_response(text).status == status


def test_parser_flags_repetition_loop():
    t = '{"a": [' + "\n".join(['"same line",'] * 40)
    r = parse_response(t, "length")
    assert r.status == "truncated" and any("repetition" in n for n in r.notes)


# ------------------------------------------------------------------ retry logic
class Scripted(BaseClient):
    provider = "fake"

    def __init__(self, script):
        self.script, self.calls, self.prompts = list(script), 0, []

    def describe(self):
        return {"provider": "fake", "model_id": "fake", "deployment_name": None}

    def _generate_once(self, user_prompt, max_new_tokens):
        self.calls += 1
        self.prompts.append(user_prompt)
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def ok(text='{"a": 1}', finish="stop"):
    return GenerationResult(text, finish, 10, 5, 0.1)


def test_transient_errors_retried_with_backoff_then_succeed():
    sleeps = []
    c = Scripted([TransientInferenceError("429"), TransientInferenceError("503"), ok()])
    r = c.generate("p", 10, retries=3, base_seconds=2, sleep=sleeps.append)
    assert r.attempts == 3 and c.calls == 3 and len(sleeps) == 2 and sleeps[1] > sleeps[0]


def test_retries_are_bounded_and_permanent_errors_not_retried():
    c = Scripted([TransientInferenceError("x")] * 10)
    with pytest.raises(TransientInferenceError):
        c.generate("p", 10, retries=2, sleep=lambda s: None)
    assert c.calls == 3
    c2 = Scripted([PermanentInferenceError("bad request"), ok()])
    with pytest.raises(PermanentInferenceError):
        c2.generate("p", 10, retries=3, sleep=lambda s: None)
    assert c2.calls == 1


def test_truncated_output_is_not_retried():
    c = Scripted([ok('{"a": [', "length"), ok()])
    r = c.generate("p", 10, sleep=lambda s: None)
    assert r.finish_reason == "length" and c.calls == 1


# ------------------------------------------------------------------ runner: failures are recorded, never replaced
def test_runner_records_failures_and_never_substitutes_empty_json(tmp_path, monkeypatch):
    for n in ("RAW_DIR", "PARSED_DIR", "FAILED_DIR", "REPORT_DIR"):
        monkeypatch.setattr(S, n, tmp_path / n)
    ids = ["00001", "00002", "00003", "00004"]
    c = Scripted([ok('{"encounter_id": "00001"}'), ok('{"symptoms": [', "length"), ok("not json at all"), PermanentInferenceError("boom")])
    m = IR.run_inference(c, ids, "development", 100, experiment_id="exp_test", sleep=lambda s: None)
    st = {i: (m["records"][i]["status"], m["records"][i].get("failure_type")) for i in ids}
    assert st["00001"] == ("parsed", None)
    assert st["00002"] == ("failed", "truncated") and st["00003"] == ("failed", "invalid_json") and st["00004"] == ("failed", "inference_error")
    assert sorted(p.stem[10:] for p in (tmp_path / "PARSED_DIR" / "exp_test").glob("*.json")) == ["00001"]
    assert sorted(p.stem[10:] for p in (tmp_path / "FAILED_DIR" / "exp_test").glob("*.json")) == ["00002", "00003", "00004"]
    assert len(list((tmp_path / "RAW_DIR" / "exp_test").glob("*.json"))) == 3        # raw responses kept for every answered call
    assert m["records"]["00001"]["schema_compliant"] is False                       # valid JSON but not schema compliant: kept distinct
    # resume does not repeat answered encounters (even malformed/truncated ones: greedy would repeat them); it re-attempts only the API failure
    c2 = Scripted([ok('{"encounter_id": "00004"}')])
    m2 = IR.run_inference(c2, ids, "development", 100, experiment_id="exp_test", sleep=lambda s: None)
    assert c2.calls == 1 and m2["records"]["00004"]["status"] == "parsed" and m2["records"]["00002"]["failure_type"] == "truncated"


# ------------------------------------------------------------------ labels are never read or sent by the inference side
def test_inference_code_never_references_labels():
    for p in (S.MODULE_DIR / "inference").glob("*.py"):
        t = p.read_text(encoding="utf-8")
        assert "LABEL_DIR" not in t and "output/labels" not in t and "\\labels" not in t, p.name
    assert "LABEL_DIR" not in (S.MODULE_DIR / "cli.py").read_text(encoding="utf-8")


def test_runner_never_opens_label_files_and_prompt_has_only_instruction_plus_transcript(tmp_path, monkeypatch):
    for n in ("RAW_DIR", "PARSED_DIR", "FAILED_DIR", "REPORT_DIR"):
        monkeypatch.setattr(S, n, tmp_path / n)
    opened = []
    real_open = builtins.open
    real_read = Path.read_text
    real_bytes = Path.read_bytes

    def spy_open(f, *a, **k):
        opened.append(str(f))
        return real_open(f, *a, **k)

    def spy_text(self, *a, **k):
        opened.append(str(self))
        return real_read(self, *a, **k)

    def spy_bytes(self, *a, **k):
        opened.append(str(self))
        return real_bytes(self, *a, **k)
    monkeypatch.setattr(builtins, "open", spy_open)
    monkeypatch.setattr(Path, "read_text", spy_text)
    monkeypatch.setattr(Path, "read_bytes", spy_bytes)
    c = Scripted([ok("{}")])
    IR.run_inference(c, ["00001"], "development", 50, experiment_id="exp_leak", sleep=lambda s: None)
    labels_touched = [o for o in opened if re.search(r"output[\\/]labels", o) or "scenario_blueprints" in o]
    assert labels_touched == []
    tr = json.loads((S.INPUT_DIR / "encounter_00001.json").read_text(encoding="utf-8"))
    expected = IR.load_prompt_template().replace("{ENCOUNTER_ID}", "00001").replace("{TRANSCRIPT}", IR.render_transcript(tr))
    assert c.prompts == [expected]
    gold = json.loads((S.LABEL_DIR / "encounter_00001.json").read_text(encoding="utf-8"))
    # label-only free text must not be present in what was sent
    for s in gold["clinical_actions"]:
        assert s["description"] not in c.prompts[0]


# ------------------------------------------------------------------ Foundry client (mocked session, no network)
class FakeResp:
    def __init__(self, code, body):
        self.status_code, self._b, self.ok, self.text = code, body, code < 400, json.dumps(body)

    def json(self):
        return self._b


class FakeSession:
    def __init__(self, resps):
        self.resps, self.sent = list(resps), []

    def post(self, url, headers=None, json=None, timeout=None):
        self.sent.append((url, headers, json))
        r = self.resps.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


def test_foundry_client_retries_and_sends_only_the_prompt():
    good = FakeResp(200, {"choices": [{"message": {"content": "{}"}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 7, "completion_tokens": 2}})
    sess = FakeSession([FakeResp(429, {}), requests.Timeout("t"), good])
    cl = FoundryClient("https://example.invalid/api/projects/p", "KEY", "qwen-deploy", session=sess)
    r = cl.generate("PROMPT ONLY", 50, retries=3, base_seconds=0, sleep=lambda s: None)
    assert r.attempts == 3 and r.completion_tokens == 2
    url, headers, body = sess.sent[-1]
    assert body["messages"] == [{"role": "user", "content": "PROMPT ONLY"}] and body["temperature"] == 0 and body["model"] == "qwen-deploy"
    assert "KEY" not in json.dumps(body) and "KEY" not in json.dumps(cl.describe())


def test_foundry_permanent_error_not_retried():
    sess = FakeSession([FakeResp(404, {"error": "no such deployment"})])
    cl = FoundryClient("https://example.invalid/api/projects/p", "KEY", "missing", session=sess)
    with pytest.raises(PermanentInferenceError):
        cl.generate("p", 5, retries=3, sleep=lambda s: None)
    assert len(sess.sent) == 1


def test_settings_repr_hides_secrets():
    t = repr(S.load_settings())
    assert S.foundry_key() == "" or S.foundry_key() not in t
    assert S.load_settings().foundry_endpoint == "" or S.load_settings().foundry_endpoint not in t
