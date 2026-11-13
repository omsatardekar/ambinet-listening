import copy
import json

import pytest

from direct_inference_baseline.config import settings as S
from direct_inference_baseline.evaluation import attribute_metrics as AM
from direct_inference_baseline.evaluation import evaluation_runner as ER
from direct_inference_baseline.evaluation import schema_validator as SV
from direct_inference_baseline.evaluation.entity_matching import match_category, micro_macro, norm_text, prf


def sym(n, **kw):
    return {"normalized_name": n, "name": n, **kw}


# ------------------------------------------------------------------ normalisation
def test_normalisation_rules():
    assert norm_text("  500 Milligrams. ") == "500 mg"
    assert norm_text("Chest-Pain!") == "chest pain"
    assert norm_text("The ECG") == "electrocardiogram"
    assert norm_text("Oesophageal oedema") == "esophageal edema"
    assert norm_text("98 percent") == "98 %"
    assert norm_text("37.5") == "37.5"                       # decimal point preserved
    assert norm_text(None) == ""


# ------------------------------------------------------------------ controlled TP/FP/FN
def test_strict_matching_counts_hand_computed():
    gold = [sym("Fever"), sym("Headache"), sym("Cough"), sym("Cough")]
    pred = [sym("fever"), sym("headache."), sym("Nausea"), sym("Cough")]
    m = match_category(gold, pred, "symptoms")
    assert (m["tp"], m["fp"], m["fn"]) == (3, 1, 1)           # fever, headache, one cough; nausea FP; second cough FN
    r = prf(m["tp"], m["fp"], m["fn"])
    assert r["precision"] == pytest.approx(0.75) and r["recall"] == pytest.approx(0.75) and r["f1"] == pytest.approx(0.75)


def test_wrong_attribute_does_not_change_entity_counts():
    gold = [sym("Fever", severity="mild")]
    pred = [sym("Fever", severity="severe")]
    m = match_category(gold, pred, "symptoms")
    assert (m["tp"], m["fp"], m["fn"]) == (1, 0, 0)
    a = AM.score_pairs({"symptoms": m["pairs"]})["counts"]["symptoms.severity"]
    assert a["gold_nonnull"] == 1 and a.get("correct", 0) == 0


def test_undefined_metrics_are_none_not_perfect():
    assert prf(0, 0, 0)["f1"] is None and prf(0, 0, 0)["precision"] is None
    assert prf(0, 3, 0)["precision"] == 0 and prf(0, 3, 0)["recall"] is None
    pc = {"a": prf(2, 0, 0), "b": prf(0, 0, 0), "c": prf(0, 1, 1)}
    mm = micro_macro(pc)
    assert mm["macro"]["categories_excluded_undefined"] == ["b"]
    assert mm["macro"]["f1"] == pytest.approx((1.0 + 0.0) / 2)
    assert mm["micro"]["tp"] == 2 and mm["micro"]["fp"] == 1 and mm["micro"]["fn"] == 1


def test_fuzzy_is_separate_from_strict():
    gold, pred = [sym("urinary tract infection")], [sym("urinary tract infections")]
    m = match_category(gold, pred, "symptoms", fuzzy=True)
    assert m["tp"] == 0 and len(m["fuzzy_pairs"]) == 1


def test_attribute_accuracy_separates_invented_values():
    g = {"dose": None, "frequency": "twice a day", "route": None}
    p = {"dose": "10 mg", "frequency": "2 times a day", "route": None}
    c = AM.score_pairs({"medications": [(g, p)]})["counts"]
    assert c["medications.dose"]["gold_null"] == 1 and c["medications.dose"]["invented"] == 1
    assert c["medications.frequency"].get("correct", 0) == 0 and c["medications.frequency"]["gold_nonnull"] == 1
    assert AM.same_value("500 milligrams", "500 mg") and AM.same_value("138/86", "138 / 86")
    assert AM.same_duration({"value": 2, "unit": "weeks", "normalized": "2 weeks"}, {"value": 2.0, "unit": "Weeks", "normalized": None})


# ------------------------------------------------------------------ end-to-end on real frozen records (read-only)
GOLD_ID = "00001"


def _gold_and_tr():
    return ER.load_gold(GOLD_ID), json.loads((S.INPUT_DIR / f"encounter_{GOLD_ID}.json").read_text(encoding="utf-8"))


def test_gold_as_prediction_scores_perfectly_and_is_schema_compliant():
    gold, tr = _gold_and_tr()
    assert SV.validate(gold).compliant, SV.validate(gold).violations[:3]
    r = ER.score_encounter(gold, gold, tr)
    for cat, c in r["strict"].items():
        assert c["fp"] == 0 and c["fn"] == 0
    agg = ER.aggregate([r])
    assert agg["strict"]["micro"]["f1"] == 1.0
    assert r["grounding"]["unsupported"] == 0 and r["unsupported"]["unsupported_claims"] == 0
    for k, v in agg["attributes"]["by_field"].items():
        if v["accuracy_on_gold_nonnull"] is not None:
            assert v["accuracy_on_gold_nonnull"] == 1.0, k


def test_empty_prediction_is_all_false_negatives():
    gold, tr = _gold_and_tr()
    r = ER.score_encounter(gold, None, tr)
    agg = ER.aggregate([r])
    assert agg["strict"]["micro"]["tp"] == 0 and agg["strict"]["micro"]["fp"] == 0 and agg["strict"]["micro"]["fn"] > 0
    assert agg["strict"]["micro"]["precision"] is None and agg["strict"]["micro"]["recall"] == 0
    assert agg["strict"]["micro"]["f1"] == 0


def test_controlled_edits_change_counts_exactly():
    gold, tr = _gold_and_tr()
    pred = copy.deepcopy(gold)
    removed = pred["symptoms"].pop(0)
    pred["medications"].append({**pred["medications"][0], "normalized_name": "Totally Invented Drug", "name": "invented", "evidence_ids": []} if pred["medications"] else
                               {"name": "Totally Invented Drug", "normalized_name": "Totally Invented Drug", "evidence_ids": []})
    r = ER.score_encounter(gold, pred, tr)
    assert r["strict"]["symptoms"]["fn"] == 1 and r["strict"]["symptoms"]["tp"] == len(gold["symptoms"]) - 1
    assert r["strict"]["medications"]["fp"] == 1
    assert r["unsupported"]["unsupported_claims"] == 1          # invented drug appears nowhere in the transcript


def test_negation_polarity_flip_detected():
    gold, tr = _gold_and_tr()
    assert gold["negative_findings"], "controlled example needs a gold negative finding"
    pred = copy.deepcopy(gold)
    n = pred["negative_findings"].pop(0)
    pred["symptoms"].append({"name": n["finding"], "normalized_name": n["normalized_name"], "status": "present", "evidence_ids": []})
    r = ER.score_encounter(gold, pred, tr)
    assert r["negation"]["polarity_flip_negative_reported_as_present"] == 1


def test_evidence_grounding_levels():
    gold, tr = _gold_and_tr()
    pred = copy.deepcopy(gold)
    pred["symptoms"][0]["evidence_ids"] = ["EV_999"]                          # dangling id -> unsupported
    r = ER.score_encounter(gold, pred, tr)
    assert r["grounding"]["unsupported"] >= 1
    pred2 = copy.deepcopy(gold)
    pred2["clinical_evidence"][0]["transcript_text"] = "Something the doctor never said."
    assert ER.score_encounter(gold, pred2, tr)["grounding"]["unsupported"] >= 1


def test_speaker_attribution_excludes_unknown_speaker_records():
    gold, tr = _gold_and_tr()
    g2 = copy.deepcopy(gold)
    g2["quality_checks"]["speaker_attribution_available"] = False
    r = ER.score_encounter(g2, g2, tr)
    assert r["speaker"].get("records_excluded_unknown_speaker") == 1 and "evaluated" not in r["speaker"]


# ------------------------------------------------------------------ schema validator
def test_schema_validator_flags_problems():
    gold, _ = _gold_and_tr()
    p = copy.deepcopy(gold)
    del p["allergies"]
    p["made_up"] = 1
    p["symptoms"][0]["bogus"] = 1
    p["symptoms"][0]["status"] = "maybe"
    del p["symptoms"][0]["severity"]
    rep = SV.validate(p)
    kinds = set(rep.counts)
    assert {"missing_top_level", "unexpected_top_level", "unexpected_field", "enum_violation", "missing_field"} <= kinds
    assert not rep.compliant and SV.completeness(rep) < 1


def test_schema_reconciliation_with_root_schema():
    assert SV.TOP_KEYS == list(json.loads(S.ROOT_SCHEMA.read_text(encoding="utf-8")).keys())
