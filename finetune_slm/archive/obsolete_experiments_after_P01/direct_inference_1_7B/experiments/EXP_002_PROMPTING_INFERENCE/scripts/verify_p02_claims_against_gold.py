"""Verifies every factual / structural claim that the P02 prompt makes about the label conventions against the 50 authorised prompt-development gold labels
(read through the dataset guard; no validation or locked-test data) and against the frozen schema's reference rules.  Read-only; no inference.
usage: python -B -s verify_p02_claims_against_gold.py   -> evaluations/p02_review/PROMPT_CLAIMS_VS_GOLD.json"""
import collections
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
TRACK = HERE.parents[3]
sys.path.insert(0, str(TRACK / "scripts"))
import common_1_7b as C  # noqa: E402

sys.path.insert(0, str(C.EXP6 / "s1"))
import evaluate_s1 as E  # noqa: E402
from direct_inference_baseline.evaluation import evaluation_runner as ER  # noqa: E402
from direct_inference_baseline.evaluation import schema_validator as SV  # noqa: E402

REV = TRACK / "experiments" / "EXP_002_PROMPTING_INFERENCE" / "evaluations" / "p02_review"
SCH = json.loads((C.S.FINAL_SCHEMA).read_text(encoding="utf-8"))
res = {}
spy = C.G.StrictAccessSpy(allow_validation=False)
with spy:
    labels = {i: ER.load_gold(i) for i in E.IDS}
    trs = {i: json.loads((C.S.INPUT_DIR / f"encounter_{i}.json").read_text(encoding="utf-8")) for i in E.IDS}


def claim(name, n_ok, n, detail=""):
    res[name] = {"pass": n_ok == n, "ok": n_ok, "of": n, "detail": detail}


def norm(t):
    return re.sub(r"\s+", " ", str(t)).strip().lower()


ids = list(E.IDS)
_nsp = [len({s["speaker_id"] for s in trs[i]["segments"]}) for i in ids]
claim("every_record_has_at_least_two_speakers_prompt_states_no_upper_bound", sum(n >= 2 for n in _nsp), len(ids), f"speaker counts {dict(collections.Counter(_nsp))} (the earlier draft's '2 to 4' was wrong: two dev records have 5 and 6)")
claim("roles_on_lines_within_schema_roles", sum(all(s["role"].lower() in SCH["roles"] for s in trs[i]["segments"]) for i in ids), len(ids))
claim("speaker_attribution_available_false_iff_UNKNOWN_role_line", sum((not labels[i]["quality_checks"]["speaker_attribution_available"]) == any(s["role"] == "UNKNOWN" for s in trs[i]["segments"]) for i in ids), len(ids))
claim("negation_detected_true_iff_negative_findings", sum(labels[i]["quality_checks"]["negation_detected"] == bool(labels[i]["negative_findings"]) for i in ids), len(ids))
claim("temporality_detected_true_in_every_label", sum(labels[i]["quality_checks"]["temporality_detected"] is True for i in ids), len(ids))
claim("requires_clinician_review_true_iff_uncertainties", sum(labels[i]["quality_checks"]["requires_clinician_review"] == bool(labels[i]["clinical_uncertainties"]) for i in ids), len(ids))
CT = ("conflicting_statement", "medication_discrepancy", "allergy_disputed", "duration_disagreement")
claim("contradictions_detected_count_equals_uncertainties_of_4_conflict_types", sum(len(labels[i]["quality_checks"]["contradictions_detected"]) == sum(u["type"] in CT for u in labels[i]["clinical_uncertainties"]) for i in ids), len(ids))
claim("unsupported_clinical_claims_always_empty", sum(labels[i]["quality_checks"]["unsupported_clinical_claims"] == [] for i in ids), len(ids))
# ambiguous entities
amb_types = collections.Counter()
amb_ok = 0
for i in ids:
    g = labels[i]
    amb = set(g["quality_checks"]["ambiguous_entities"])
    by_type = {u["type"]: set(u["related_entities"]) for u in g["clinical_uncertainties"]}
    for u in g["clinical_uncertainties"]:
        if set(u["related_entities"]) & amb:
            amb_types[u["type"]] += 1
    expect = set()
    for t in ("unknown_speaker", "incomplete_medication_name"):
        expect |= by_type.get(t, set())
    amb_ok += amb == expect
claim("ambiguous_entities_equals_related_entities_of_unknown_speaker_and_incomplete_medication_name", amb_ok, len(ids), f"uncertainty types touching ambiguous_entities: {dict(amb_types)}")
# uncertainties
rel = collections.Counter()
for i in ids:
    for u in labels[i]["clinical_uncertainties"]:
        rel["n"] += 1
        rel["related_nonempty"] += bool(u["related_entities"])
        rel["res_ok"] += u["resolution_status"] == ("partially_resolved" if u["type"] == "duration_disagreement" else "unresolved")
claim("uncertainty_related_entities_always_non_empty", rel["related_nonempty"], rel["n"])
claim("uncertainty_resolution_partially_resolved_only_for_duration_disagreement", rel["res_ok"], rel["n"])
# related_entities targets per schema reference rule
TARGET = {"allergy_uncertain": {"allergies"}, "allergy_disputed": {"negative_findings", "allergies"}, "uncertain_dose": {"medications"}, "medication_discrepancy": {"medications"}, "adherence_uncertain": {"medications"},
          "incomplete_medication_name": {"medications"}, "date_uncertain": {"symptoms"}, "duration_disagreement": {"symptoms"}, "unknown_speaker": {"symptoms"}, "conflicting_statement": {"negative_findings", "symptoms"}}
tot = ok = 0
for i in ids:
    for u in labels[i]["clinical_uncertainties"]:
        tot += 1
        ok += {re.sub(r"\[\d+\]", "", r) for r in u["related_entities"]} == TARGET[u["type"]]
claim("related_entities_sections_match_schema_reference_rule_per_type", ok, tot)
# duration disagreement / dose conventions
dd = [(i, g) for i in ids for g in [labels[i]] if any(u["type"] == "duration_disagreement" for u in g["clinical_uncertainties"])]
claim("duration_disagreement_symptom_duration_value_null_with_approximately_range", sum(any(s["duration"] and s["duration"]["value"] is None and "approximately" in s["duration"]["normalized"] for s in g["symptoms"]) for _, g in dd), len(dd))
md = [(i, g) for i in ids for g in [labels[i]] if any(u["type"] == "medication_discrepancy" for u in g["clinical_uncertainties"])]
claim("medication_discrepancy_has_a_medication_with_dose_null", sum(any(m["dose"] is None for m in g["medications"]) for _, g in md), len(md))
im = [(i, g) for i in ids for g in [labels[i]] if any(u["type"] == "incomplete_medication_name" for u in g["clinical_uncertainties"])]
claim("incomplete_medication_name_has_generic_and_normalized_name_null", sum(any(m["generic_name"] is None and m["normalized_name"] is None for m in g["medications"]) for _, g in im), len(im))
# certainty ties
tot = ok = 0
for i in ids:
    g = labels[i]
    types = {u["type"] for u in g["clinical_uncertainties"]}
    for s in g["symptoms"]:
        if s["certainty"] == "disputed":
            tot += 1
            ok += "conflicting_statement" in types
claim("symptom_certainty_disputed_has_conflicting_statement_uncertainty", ok, tot)
# conditions duplicated in PMH
tot = ok = 0
for i in ids:
    pm = {norm(x["normalized_condition"]) for x in labels[i]["medical_history"]["past_medical_history"]}
    for c in labels[i]["clinical_conditions"]:
        tot += 1
        ok += norm(c["normalized_name"]) in pm
claim("every_clinical_condition_also_in_past_medical_history", ok, tot)
# actions
ca = collections.Counter()
for i in ids:
    for a in labels[i]["clinical_actions"]:
        if a["status"] == "conditional":
            ca[a["action_type"]] += 1
claim("conditional_actions_only_investigation_or_follow_up", sum(v for k, v in ca.items() if k in ("investigation", "follow_up")), sum(ca.values()), str(dict(ca)))
# route
tot = ok = 0
exceptions = []
for i in ids:
    g = labels[i]
    evs = {e["evidence_id"]: e["transcript_text"].lower() for e in g["clinical_evidence"]}
    for m in g["medications"]:
        txt = " ".join(evs.get(x, "") for x in m["evidence_ids"])
        has = bool(re.search(r"by mouth|orally", txt))
        tot += 1
        if m["route"] == "oral":
            ok += has
        elif not has:
            ok += 1
        else:  # route null although the cited lines say by mouth: acceptable only when the line is shared with another medicine
            shared = any(o is not m and set(o["evidence_ids"]) & set(m["evidence_ids"]) for o in g["medications"])
            ok += shared
            exceptions.append((i, m["name"], "line shared with another medicine" if shared else "UNEXPLAINED"))
claim("route_oral_only_for_the_medicine_the_by_mouth_words_refer_to", ok, tot, f"routes: oral {sum(m['route'] == 'oral' for i in ids for m in labels[i]['medications'])}; exceptions (by-mouth words in a shared line, route null): {exceptions}")
# vitals value typing
tot = ok = 0
for i in ids:
    for v in labels[i]["vital_signs"]:
        tot += 1
        isbp = v["normalized_name"].lower() == "blood pressure"
        ok += (isinstance(v["value"], str) and bool(re.fullmatch(r"\d+/\d+", v["value"]))) if isbp else (isinstance(v["value"], (int, float)) and not isinstance(v["value"], bool))
claim("vital_value_is_number_except_blood_pressure_which_is_systolic_slash_diastolic_text", ok, tot)
claim("vital_value_never_null_or_empty", sum(v["value"] not in (None, "") for i in ids for v in labels[i]["vital_signs"]), sum(len(labels[i]["vital_signs"]) for i in ids))
# symptoms
tot = ok = 0
for i in ids:
    for s in labels[i]["symptoms"]:
        tot += 1
        ok += (s["status"] == "present" and s["temporality"] == "current") or (s["status"] == "resolved" and s["temporality"] in ("resolved", "past"))
claim("symptom_status_temporality_combinations_present_current_or_resolved_resolved_or_past", ok, tot)
cat_ok = tot2 = 0
for i in ids:
    for s in labels[i]["symptoms"]:
        tot2 += 1
        cat_ok += isinstance(s["category"], str) and s["category"] in SV._VOCAB
claim("symptom_category_is_string_in_the_13_value_vocabulary_never_null", cat_ok, tot2, f"values used: {sorted({s['category'] for i in ids for s in labels[i]['symptoms']})}; 'other' used {sum(s['category'] == 'other' for i in ids for s in labels[i]['symptoms'])} times")
# single-value enums
claim("pmh_status_all_ongoing", sum(x["status"] == "ongoing" for i in ids for x in labels[i]["medical_history"]["past_medical_history"]), sum(len(labels[i]["medical_history"]["past_medical_history"]) for i in ids))
claim("ros_all_negative_details_null", sum(x["status"] == "negative" and x["details"] is None for i in ids for x in labels[i]["review_of_systems"]), sum(len(labels[i]["review_of_systems"]) for i in ids))
claim("physical_examination_body_site_never_null", sum(x["body_site"] is not None for i in ids for x in labels[i]["physical_examination"]), sum(len(labels[i]["physical_examination"]) for i in ids), "documented deviation: template keeps null")
claim("surgical_timeframe_never_null", sum(x["timeframe"] is not None for i in ids for x in labels[i]["medical_history"]["surgical_history"]), sum(len(labels[i]["medical_history"]["surgical_history"]) for i in ids), "documented deviation: template keeps null")
# allergy representation
tot = ok = 0
for i in ids:
    g = labels[i]
    neg_all = [n for n in g["negative_findings"] if n["normalized_name"] == "No known allergies"]
    types = {u["type"] for u in g["clinical_uncertainties"]}
    for a in g["allergies"]:
        tot += 1
        if a["status"] == "uncertain":
            ok += "allergy_uncertain" in types
        elif a["status"] == "disputed":
            ok += "allergy_disputed" in types and bool(neg_all)
        else:
            ok += True
    if neg_all and g["allergies"] and not any(a["status"] == "disputed" for a in g["allergies"]):
        res.setdefault("_allergy_neg_and_entry_without_dispute", []).append(i)
claim("allergy_uncertain_and_disputed_carry_their_uncertainty_and_negative_finding", ok, tot)
claim("no_known_allergies_negative_never_with_allergy_entries_unless_disputed", len(ids) - len(res.get("_allergy_neg_and_entry_without_dispute", [])), len(ids))
claim("allergy_severity_always_unknown", sum(a["severity"] == "unknown" for i in ids for a in labels[i]["allergies"]), sum(len(labels[i]["allergies"]) for i in ids))
# full validator on gold: the evaluator's schema validator accepts every gold label
rep = [SV.validate(labels[i]) for i in ids]
claim("evaluator_schema_validator_reports_zero_violations_on_every_gold_label", sum(not r.violations for r in rep), len(ids), str([r.violations[:1] for r in rep if r.violations][:2]))
res.pop("_allergy_neg_and_entry_without_dispute", None)
failed = {k: v for k, v in res.items() if not v["pass"]}
(REV / "PROMPT_CLAIMS_VS_GOLD.json").write_text(json.dumps({"ids": len(ids), "claims": res, "failed": list(failed)}, indent=1), encoding="utf-8")
print(f"{len(res)} claims, {len(failed)} not exact")
for k, v in res.items():
    print(("OK  " if v["pass"] else "DIFF"), k, f"{v['ok']}/{v['of']}", v["detail"][:150])
