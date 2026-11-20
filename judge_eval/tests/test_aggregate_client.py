"""Tests for the metric arithmetic, agreement statistic, judge reply parsing and client behaviour (no network).
Run from the repository root:  python -m pytest judge_eval/tests -q
"""
import io
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from judge_eval import client as client_module                      # noqa: E402
from judge_eval.aggregate import encounter_row, kappa, metrics      # noqa: E402
from judge_eval.client import Judge, JudgeError, parse_json_reply   # noqa: E402
from judge_eval.judge_run import _validated                         # noqa: E402


def result(precision, recall, pred_fields=None, ref_fields=None):
    pf = [{"fid": f"p{i}", "field": (pred_fields or ["symptoms"] * len(precision))[i], "text": "x", "attributes": {}} for i in range(len(precision))]
    rf = [{"fid": f"r{i}", "field": (ref_fields or ["symptoms"] * len(recall))[i], "text": "x", "attributes": {}} for i in range(len(recall))]
    return {"predicted_facts": pf, "reference_facts": rf,
            "precision": [{"fid": f"p{i}", "verdict": v[0], "critical": v[1]} for i, v in enumerate(precision)],
            "recall": [{"fid": f"r{i}", "verdict": v} for i, v in enumerate(recall)]}


def test_metric_arithmetic_strict_and_lenient():
    label = [{"fid": f"r{i}", "field": "symptoms"} for i in range(4)]
    row = encounter_row(result([("supported", False), ("partially_supported", False), ("unsupported", False), ("contradicted", True)], ["found", "partially_found", "missing", "missing"]), label)
    m = metrics([row])
    assert m["precision_strict"] == 0.25 and m["precision_lenient"] == 0.375
    assert m["recall_strict"] == 0.25 and m["recall_lenient"] == 0.375
    assert m["hallucination_rate"] == 0.5 and m["critical_rate"] == 0.25 and m["encounters_with_critical"] == 1.0
    assert abs(m["judge_f1_lenient"] - 0.375) < 1e-9


def test_failed_encounter_counts_as_zero_predictions_but_keeps_reference_facts():
    label = [{"fid": f"r{i}", "field": "medications"} for i in range(3)]
    good = encounter_row(result([("supported", False)], ["found", "missing", "missing"]), label)
    failed = encounter_row(None, label)
    m = metrics([good, failed])
    assert m["reference_facts"] == 6 and m["predicted_facts"] == 1 and m["recall_strict"] == pytest.approx(1 / 6)
    assert metrics([good])["recall_strict"] == pytest.approx(1 / 3)           # tier 2 (parsed only) is higher, and both are reported


def test_kappa_perfect_and_chance():
    assert kappa([("a", "a"), ("b", "b"), ("a", "a")]) == (1.0, 1.0)
    observed, k = kappa([("a", "b"), ("b", "a")])
    assert observed == 0.0 and k < 0
    assert kappa([]) == (None, None)


def test_parse_json_reply_handles_fences_and_rejects_prose():
    assert parse_json_reply('```json\n{"a": 1}\n```') == {"a": 1}
    assert parse_json_reply('Sure! {"a": 2} done') == {"a": 2}
    with pytest.raises(JudgeError):
        parse_json_reply("no json here")


def test_verdict_validation_requires_every_fid_and_known_verdicts():
    good = json.dumps({"verdicts": [{"fid": "a", "verdict": "supported"}, {"fid": "b", "verdict": "unsupported"}]})
    assert len(_validated(good, ["a", "b"], ("supported", "unsupported"))) == 2
    with pytest.raises(JudgeError):
        _validated(good, ["a", "b", "c"], ("supported", "unsupported"))          # missing fact
    with pytest.raises(JudgeError):
        _validated(good, ["a", "b"], ("found",))                                  # verdict vocabulary mismatch


def test_client_detects_style_caches_replies_and_never_leaks_the_key(tmp_path, monkeypatch):
    monkeypatch.setattr(client_module, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(client_module, "_load_dotenv_if_needed", lambda: None)
    monkeypatch.setenv("JUDGE_ENDPOINT_URL", "https://example.test/openai/v1/responses")
    monkeypatch.setenv("JUDGE_API_KEY", "TOP-SECRET")
    monkeypatch.setenv("JUDGE_DEPLOYMENT", "m")
    judge = Judge("JUDGE")
    assert judge.style == "responses" and judge.configured()
    calls = []

    class Resp(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *a): return False

    def ok(request, timeout):
        calls.append(request.get_header("Api-key"))
        return Resp(json.dumps({"output": [{"type": "message", "content": [{"type": "output_text", "text": "{\"x\": 1}"}]}], "usage": {"input_tokens": 3}}).encode())

    monkeypatch.setattr(urllib.request, "urlopen", ok)
    first = judge.call("s", "u")
    second = judge.call("s", "u")
    assert first.text == '{"x": 1}' and not first.cached and second.cached and len(calls) == 1 and calls[0] == "TOP-SECRET"

    def denied(request, timeout):
        raise urllib.error.HTTPError("https://example.test", 401, "bad TOP-SECRET", {}, io.BytesIO(b"TOP-SECRET"))

    monkeypatch.setattr(urllib.request, "urlopen", denied)
    with pytest.raises(JudgeError) as info:
        judge.call("s", "different")
    assert info.value.code == "judge_auth_failed" and "TOP-SECRET" not in info.value.message

    monkeypatch.setenv("JUDGE_ENDPOINT_URL", "https://example.test/openai/v1/chat/completions")
    assert Judge("JUDGE").style == "chat"
