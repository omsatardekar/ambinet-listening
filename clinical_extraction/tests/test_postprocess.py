from clinical_extraction import postprocess


def _base():
    return {
        "negative_findings": [{"finding": "cough", "normalized_name": "Cough", "evidence_ids": ["SEG0024"]},
                              {"finding": "asthma", "normalized_name": "Asthma", "evidence_ids": ["SEG0040"]}],
        "medical_history": {"past_medical_history": [{"condition": "asthma", "normalized_condition": "Asthma", "status": "ongoing", "evidence_ids": ["SEG0041"]}]},
        "procedures_and_investigations": [{"name": "Rapid blood test for malaria", "normalized_name": "Malaria rapid test", "type": "laboratory", "evidence_ids": ["SEG0072"]},
                                          {"name": "blood film", "normalized_name": "Malaria blood film", "type": "laboratory", "evidence_ids": ["SEG0072"]}],
        "clinical_actions": [{"action_type": "investigation", "description": "Arrange Malaria rapid test", "evidence_ids": ["SEG0072", "SEG0073"]},
                             {"action_type": "investigation", "description": "Arrange Malaria blood film", "evidence_ids": ["SEG0072"]},
                             {"action_type": "counselling", "description": "Drink water little and often", "evidence_ids": ["SEG0077"]}],
    }


def test_contradicted_negative_is_removed_and_reported():
    out, changes = postprocess.clean(_base())
    assert [n["finding"] for n in out["negative_findings"]] == ["cough"]
    c = [c for c in changes if c["rule"] == "contradicted_negative"]
    assert len(c) == 1 and c[0]["removed"] == "No asthma"
    assert "contradicts the medical history" in postprocess.warning_for(c[0])


def test_duplicate_tests_are_merged_and_evidence_is_kept():
    out, changes = postprocess.clean(_base())
    assert [a["description"] for a in out["clinical_actions"]] == ["Drink water little and often"]          # counselling untouched
    assert out["procedures_and_investigations"][0]["evidence_ids"] == ["SEG0072", "SEG0073"]
    assert all(postprocess.warning_for(c) is None for c in changes if c["rule"] == "merged_duplicate_test")


def test_different_test_is_not_merged_and_unrelated_negative_is_kept():
    x = _base()
    x["clinical_actions"].append({"action_type": "investigation", "description": "Arrange chest x-ray", "evidence_ids": ["SEG0090"]})
    x["negative_findings"].append({"finding": "diabetes", "evidence_ids": ["SEG0050"]})
    out, _ = postprocess.clean(x)
    assert any(a["description"] == "Arrange chest x-ray" for a in out["clinical_actions"])
    assert any(n["finding"] == "diabetes" for n in out["negative_findings"])


def test_nothing_to_do_returns_the_same_object_and_input_is_never_modified():
    clean = {"negative_findings": [{"finding": "rash"}], "medical_history": {"past_medical_history": []}, "procedures_and_investigations": [], "clinical_actions": []}
    out, changes = postprocess.clean(clean)
    assert out is clean and changes == []
    x = _base()
    before = repr(x)
    postprocess.clean(x)
    assert repr(x) == before


def test_missing_sections_do_not_crash():
    assert postprocess.clean({})[1] == []
    assert postprocess.clean({"negative_findings": None, "medical_history": None, "clinical_actions": None})[1] == []


def _sym(name, **kw):
    base = {"name": name, "category": "constitutional", "status": "present", "temporality": "current", "body_site": None, "frequency": None, "onset": None, "evidence_ids": []}
    base.update(kw)
    return base


def test_repeated_symptom_with_article_is_merged_evidence_united_and_conflict_warned():
    x = {"symptoms": [_sym("night sweats", frequency="Most nights", evidence_ids=["SEG0017"]), _sym("flushes", evidence_ids=["SEG0018"]),
                      _sym("the night sweats", frequency="34 times a week", evidence_ids=["SEG0018", "SEG0019"]), _sym("the flushes", evidence_ids=["SEG0018"])]}
    out, changes = postprocess.clean(x)
    assert [s["name"] for s in out["symptoms"]] == ["night sweats", "flushes"]
    assert out["symptoms"][0]["evidence_ids"] == ["SEG0017", "SEG0018", "SEG0019"] and out["symptoms"][0]["frequency"] == "Most nights"
    warn = [postprocess.warning_for(c) for c in changes if c["rule"] == "repeated_symptom"]
    assert warn[0] and "34 times a week" in warn[0] and warn[1] is None                     # only the conflicting merge is shown to the clinician


def test_symptoms_that_differ_in_site_time_or_status_are_not_merged():
    x = {"symptoms": [_sym("pain", body_site="chest"), _sym("pain", body_site="back"), _sym("pain", body_site="chest", temporality="past"),
                      _sym("pain", body_site="chest", status="absent"), _sym("the cough")]}
    out, _ = postprocess.clean(x)
    assert len(out["symptoms"]) == 5 and out["symptoms"][-1]["name"] == "cough"            # article removed, nothing merged


def test_missing_body_site_on_the_copy_still_merges():
    x = {"symptoms": [_sym("headache", body_site="front"), _sym("the headache")]}
    out, changes = postprocess.clean(x)
    assert len(out["symptoms"]) == 1 and changes[0]["rule"] == "repeated_symptom"


def test_sentence_like_symptom_is_flagged_not_removed():
    x = {"symptoms": [_sym("I'm not a snappy person"), _sym("I've overdone it"), _sym("fever"), _sym("Imbalance"), _sym("itchy skin")]}
    out, changes = postprocess.clean(x)
    flagged = [c["name"] for c in changes if c["rule"] == "speech_wording"]
    assert flagged == ["I'm not a snappy person", "I've overdone it"] and len(out["symptoms"]) == 5
    assert "copied from speech" in postprocess.warning_for(changes[0])


def test_name_contained_in_another_name_merges_only_with_the_same_frequency_and_keeps_the_specific_name():
    x = {"symptoms": [_sym("sweats", frequency="Most nights", evidence_ids=["SEG0001"]), _sym("night sweats", frequency="Most nights", evidence_ids=["SEG0002"]),
                      _sym("pain", frequency="daily"), _sym("chest pain", frequency="rarely"), _sym("fatigue"), _sym("severe fatigue")]}
    out, _ = postprocess.clean(x)
    assert [s["name"] for s in out["symptoms"]] == ["night sweats", "pain", "chest pain", "fatigue", "severe fatigue"]
    assert out["symptoms"][0]["evidence_ids"] == ["SEG0001", "SEG0002"]
