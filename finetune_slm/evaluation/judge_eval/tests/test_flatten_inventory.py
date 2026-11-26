"""Tests for flatten.py and the inventory (read-only; need the repository data, skipped otherwise).
Run from the repository root:  python -m pytest judge_eval/tests -q
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from finetune_slm.evaluation.judge_eval.flatten import FIELDS, flatten                      # noqa: E402
from finetune_slm.evaluation.judge_eval.registry import LABEL_DIR, RUNS                     # noqa: E402


def test_drops_provenance_and_empties_and_normalized_duplicates():
    doc = {"medications": [{"name": "aspirin", "normalized_name": "Aspirin", "dose": "75 mg", "route": None, "frequency": "", "evidence_ids": ["EV_1"], "confidence": 0.9, "status": "currently_used"}]}
    facts = flatten(doc)
    assert len(facts) == 1
    assert facts[0]["field"] == "medications" and facts[0]["text"] == "aspirin (dose=75 mg, status=currently_used)"
    assert "evidence_ids" not in facts[0]["attributes"] and "normalized_name" not in facts[0]["attributes"]


def test_history_dict_assessment_and_plain_strings_are_tolerated():
    doc = {"medical_history": {"past_medical_history": [{"condition": "asthma", "status": "ongoing"}], "family_history": []},
           "clinical_assessment": {"assessment": "possible chest infection", "certainty": "provisional"},
           "symptoms": ["cough"], "negative_findings": None, "follow_up": "not a list"}
    facts = flatten(doc)
    assert [f["field"] for f in facts] == ["medical_history.past_medical_history", "symptoms", "clinical_assessment", "follow_up"]
    assert facts[-1]["text"] == "not a list"                     # a bare string is one fact, never split into characters
    assert flatten("garbage") == [] and flatten(None) == [] and flatten({}) == []


def test_fact_ids_are_stable_and_per_field():
    facts = flatten({"symptoms": [{"name": "cough"}, {"name": "fever"}]})
    assert [f["fid"] for f in facts] == ["symptoms[0]", "symptoms[1]"]


@pytest.mark.skipif(not (LABEL_DIR / "encounter_00037.json").exists(), reason="dataset missing")
def test_real_label_flattens_with_known_fields_only():
    label = json.loads((LABEL_DIR / "encounter_00037.json").read_text(encoding="utf-8"))
    facts = flatten(label)
    assert len(facts) > 10 and all(f["field"] in FIELDS for f in facts)
    assert not any("EV_" in f["text"] for f in facts)


@pytest.mark.skipif(not (LABEL_DIR / "encounter_00037.json").exists(), reason="dataset missing")
def test_every_registered_parsed_prediction_flattens_without_error():
    checked = 0
    for run in RUNS:
        directory = ROOT / run.parsed
        for path in sorted(directory.glob("*.json"))[:5]:
            assert isinstance(flatten(json.loads(path.read_text(encoding="utf-8"))), list)
            checked += 1
    assert checked > 0
