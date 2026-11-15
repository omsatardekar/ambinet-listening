"""Prompt-only review with an INVENTED consultation (no model, no dev data, no gold). It checks that (1) the rules the prompt states are present, (2) an output written by following those rules
passes shape / enum / temporality / speaker / evidence / vital-sign / follow-up checks, and the evidence backfill adapter accepts it, and (3) deliberately wrong variants are each caught.
This validates the prompt's internal consistency and the checks; it does NOT measure model behaviour. Run: python -B -I prompt_review_synthetic.py"""
import copy
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from backfill_evidence import backfill     # noqa: E402

PKG = Path(__file__).resolve().parents[1]
EXP = PKG.parent
PROMPT = (EXP / "prompt_versions" / "P02_p01_schema_no_evidence.txt").read_text(encoding="utf-8")
tmpl = json.loads(PROMPT.split("Output format (")[1].split("\n", 1)[1].split("\nTranscript (encounter")[0])

# ---------------------------------------------------------------- invented transcript
LINES = [("person_3", "NURSE", "Pressure is 142 over 90, pulse 88, temperature 37.2 degrees, saturation 95 percent."), ("person_2", "DOCTOR", "Hello, what brings you in today?"),
         ("person_1", "PATIENT", "I've had a throbbing pain behind my right ear for five days and it hasn't gone away."), ("person_2", "DOCTOR", "Any fever or vomiting?"),
         ("person_1", "PATIENT", "No fever, and I haven't been sick either."), ("person_2", "DOCTOR", "Any hearing trouble?"),
         ("person_1", "PATIENT", "Sometimes my hearing goes muffled for a few minutes, a couple of times a day, then it clears."), ("person_1", "PATIENT", "I had a sore throat last week but that stopped on Sunday."),
         ("person_2", "DOCTOR", "Any allergies? Do you take any medicines?"), ("person_1", "PATIENT", "No known allergies. I take 40 mg of famotidine every morning."),
         ("person_2", "DOCTOR", "I can see redness behind your right ear and it is tender to touch."),
         ("person_2", "DOCTOR", "This could be an ear infection, though I can't rule out a nerve problem. I'll arrange an ear scan, so keep your ear dry, avoid flying, and call us if the pain gets worse. Let's meet again after the scan results."),
         ("person_1", "PATIENT", "My father had glaucoma."), ("person_1", "PATIENT", "I live with my sister and I work as a bus driver.")]
TR = {"encounter_id": "99999", "segments": [{"segment_id": f"SEG{i + 1:04d}", "speaker_id": s, "role": r, "start_seconds": 2.0 * i, "end_seconds": 2.0 * i + 1.5, "text": t} for i, (s, r, t) in enumerate(LINES)]}
TEXT = {s["segment_id"]: s["text"].lower() for s in TR["segments"]}
ROLE = {s["segment_id"]: s["role"].lower() for s in TR["segments"]}


def item(section, ev, **kw):
    base = copy.deepcopy(tmpl[section][0] if section in tmpl else tmpl["medical_history"][section][0])
    base.update(kw)
    base["evidence_ids"] = ev
    return base


S = lambda n: f"SEG{n:04d}"
GOOD = copy.deepcopy(tmpl)
GOOD.update({"encounter_id": "99999", "chief_complaint": {"value": "pain behind my right ear", "normalized_value": "ear pain", "reported_by": "patient", "evidence_ids": [S(3)]},
             "encounter_metadata": {"encounter_date": None, "encounter_type": "outpatient_consultation", "language": "en", "primary_speakers": [
                 {"speaker_id": "person_3", "role": "nurse", "role_confidence": None}, {"speaker_id": "person_2", "role": "doctor", "role_confidence": None}, {"speaker_id": "person_1", "role": "patient", "role_confidence": None}]}})
GOOD["symptoms"] = [item("symptoms", [S(3)], name="pain behind my right ear", normalized_name="ear pain", category="ENT", status="present", duration={"value": 5, "unit": "days", "normalized": "5 days"}, temporality="current", body_site="right ear", reported_by="patient", certainty="certain"),
                    item("symptoms", [S(7)], name="my hearing goes muffled", normalized_name="muffled hearing", category="ENT", status="present", frequency="a couple of times a day", temporality="current", reported_by="patient", certainty="certain"),
                    item("symptoms", [S(8)], name="sore throat", normalized_name="sore throat", category="ENT", status="resolved", temporality="resolved", reported_by="patient", certainty="certain")]
GOOD["negative_findings"] = [item("negative_findings", [S(5)], finding="No fever", normalized_name="fever", reported_by="patient", temporality="current"),
                             item("negative_findings", [S(5)], finding="haven't been sick", normalized_name="vomiting", reported_by="patient", temporality="current"),
                             item("negative_findings", [S(10)], finding="No known allergies", normalized_name="No known allergies", reported_by="patient", temporality="current")]
GOOD["medical_history"]["family_history"] = [item("family_history", [S(13)], condition="glaucoma", normalized_condition="glaucoma", relation="father", reported_by="patient")]
GOOD["medical_history"]["social_history"] = [item("social_history", [S(14)], category="living", description="lives with sister", status="current", details="I live with my sister", reported_by="patient"),
                                             item("social_history", [S(14)], category="occupation", description="bus driver", status="current", details="I work as a bus driver", reported_by="patient")]
GOOD["medications"] = [item("medications", [S(10)], name="famotidine", normalized_name="famotidine", dose="40 mg", frequency="every morning", status="currently_used", reported_by="patient")]
GOOD["vital_signs"] = [item("vital_signs", [S(1)], name="pressure", normalized_name="Blood pressure", value="142/90", unit="mmHg", reported_by="nurse"),
                       item("vital_signs", [S(1)], name="pulse", normalized_name="Heart rate", value=88, unit="bpm", reported_by="nurse"),
                       item("vital_signs", [S(1)], name="temperature", normalized_name="Body temperature", value=37.2, unit="°C", reported_by="nurse"),
                       item("vital_signs", [S(1)], name="saturation", normalized_name="Oxygen saturation", value=95, unit="%", reported_by="nurse")]
GOOD["physical_examination"] = [item("physical_examination", [S(11)], finding="redness behind your right ear", normalized_finding="retroauricular erythema", body_site="right ear", status="present", observed_by="doctor"),
                                item("physical_examination", [S(11)], finding="tender to touch", normalized_finding="tenderness", body_site="right ear", status="present", observed_by="doctor")]
GOOD["clinical_assessment"] = [item("clinical_assessment", [S(12)], assessment="ear infection", normalized_assessment="ear infection", certainty="provisional", stated_by="doctor"),
                               item("clinical_assessment", [S(12)], assessment="nerve problem", normalized_assessment="nerve problem", certainty="differential", stated_by="doctor")]
GOOD["procedures_and_investigations"] = [item("procedures_and_investigations", [S(12)], name="ear scan", normalized_name="ear scan", type="imaging", status="planned", requested_by="doctor", indication="ear infection")]
GOOD["clinical_actions"] = [item("clinical_actions", [S(12)], action_type="investigation", description="arrange an ear scan", status="planned", responsible_person="doctor"),
                            item("clinical_actions", [S(12)], action_type="counselling", description="keep your ear dry", status="recommended", responsible_person="patient"),
                            item("clinical_actions", [S(12)], action_type="counselling", description="avoid flying", status="recommended", responsible_person="patient"),
                            item("clinical_actions", [S(12)], action_type="counselling", description="call us if the pain gets worse", status="conditional", responsible_person="patient"),
                            item("clinical_actions", [S(12)], action_type="follow_up", description="meet again after the scan results", status="planned", responsible_person="doctor", time_reference={"value": "after the scan results", "normalized_date": None})]
GOOD["follow_up"] = [item("follow_up", [S(12)], type="consultation", time_reference="after the scan results", normalized_datetime=None, status="planned")]
GOOD["clinical_evidence"] = []
for _sec in ("allergies", "review_of_systems", "clinical_conditions", "clinical_uncertainties"):       # nothing stated in this consultation: empty list, as the prompt requires
    GOOD[_sec] = []
GOOD["medical_history"]["past_medical_history"] = []
GOOD["medical_history"]["surgical_history"] = []

# ---------------------------------------------------------------- allowed values parsed from the prompt itself
allowed = {}
for ln in PROMPT.split("\nAllowed values\n")[1].split("\n\nStructure rules")[0].splitlines():
    if not ln.startswith("- ") or ln.startswith("- negative_findings"):
        continue
    parts = [p.strip() for p in ln[2:].split(" ; ")]
    sec = parts[0].split(".")[0]
    for p in parts:
        k, _, v = p.partition(":")
        k = k.strip()
        key = k if "." in k else f"{sec}.{k}"
        allowed[key] = {x.strip().strip('"') for x in v.split("|")}
allowed["negative_findings.status"], allowed["negative_findings.assertion"], allowed["negative_findings.temporality"] = {"absent"}, {"negative"}, {"current", "past"}
SECTIONS = ["symptoms", "negative_findings", "medications", "allergies", "vital_signs", "physical_examination", "review_of_systems", "clinical_conditions", "clinical_assessment", "procedures_and_investigations", "clinical_actions", "follow_up", "clinical_uncertainties"]
SPK = {"chief_complaint": "reported_by", "symptoms": "reported_by", "negative_findings": "reported_by", "medications": "reported_by", "allergies": "reported_by", "vital_signs": "reported_by", "physical_examination": "observed_by",
       "review_of_systems": "reported_by", "clinical_assessment": "stated_by", "family_history": "reported_by", "social_history": "reported_by", "past_medical_history": "reported_by", "surgical_history": "reported_by", "clinical_conditions": "reported_by"}
NEG = re.compile(r"\b(no|never|without|denies|not)\b|n't")
RES = re.compile(r"stopped|no longer|resolved|went away|disappeared|(?<!hasn't )gone")
CUR = re.compile(r"hasn't gone|still|for \w+ days")


def all_items(o):
    for sec in SECTIONS:
        for it in o.get(sec, []):
            yield sec, it
    for sub in ("past_medical_history", "surgical_history", "family_history", "social_history"):
        for it in o["medical_history"].get(sub, []):
            yield sub, it
    yield "chief_complaint", o["chief_complaint"]


def review(o):
    """returns a list of violation kinds"""
    v = []
    if o.get("clinical_evidence") not in ([],):
        v.append("model_wrote_evidence_records")
    if list(o) != list(tmpl):
        v.append("top_level_keys")
    for sec, it in all_items(o):
        ref = tmpl["chief_complaint"] if sec == "chief_complaint" else tmpl[sec][0] if sec in tmpl else tmpl["medical_history"][sec][0]
        if list(it) != list(ref):
            v.append(f"item_keys:{sec}")
        for k, val in it.items():
            e = allowed.get(f"{sec}.{k}")
            if e and isinstance(val, str) and val not in e:
                v.append(f"enum:{sec}.{k}")
        ev = it.get("evidence_ids") or []
        if not ev:
            v.append(f"no_evidence:{sec}")
        if len(ev) > 4:
            v.append(f"too_many_refs:{sec}")
        for x in ev:
            if x not in TEXT:
                v.append(f"invalid_segment_id:{x}")
        cited = " ".join(TEXT.get(x, "") for x in ev)
        f = SPK.get(sec)
        if f and it.get(f) is not None and ev and not any(ROLE.get(x) == it[f] for x in ev):
            v.append(f"speaker_not_in_cited_lines:{sec}")
        if sec == "symptoms":
            if (it["status"], it["temporality"]) not in {("present", "current"), ("resolved", "resolved"), ("resolved", "past")}:
                v.append("status_temporality_combination")
            if RES.search(cited) and it["status"] != "resolved":
                v.append("resolved_symptom_written_as_current")
            if CUR.search(cited) and not RES.search(cited) and it["temporality"] != "current":
                v.append("ongoing_symptom_written_as_past_or_resolved")
        if sec == "negative_findings" and not NEG.search(cited):
            v.append("negative_finding_without_negation_in_cited_line")
        if sec == "vital_signs":
            if it["normalized_name"] == "Blood pressure" and not re.fullmatch(r"\d{2,3}/\d{2,3}", str(it["value"])):
                v.append("blood_pressure_not_both_numbers")
        if sec == "follow_up" and it["time_reference"].lower() not in cited:
            v.append("follow_up_time_not_in_cited_text")
    rep, flags, st = backfill(o, TR)
    v += [f"backfill:{f['kind']}" for f in flags if f["kind"] != "excessive_references"]
    return v


cases = {"reference_output_following_the_rules": (lambda o: o, [])}


def mut(fn):
    def run(o):
        o = copy.deepcopy(o)
        fn(o)
        return o
    return run


cases.update({
    "ongoing_symptom_written_as_resolved/past": (mut(lambda o: o["symptoms"][0].update(status="resolved", temporality="past")), ["ongoing_symptom_written_as_past_or_resolved"]),
    "resolved_symptom_written_as_current": (mut(lambda o: o["symptoms"][2].update(status="present", temporality="current")), ["resolved_symptom_written_as_current"]),
    "blood_pressure_truncated_to_first_number": (mut(lambda o: o["vital_signs"][0].update(value=142)), ["blood_pressure_not_both_numbers"]),
    "nurse_measurement_attributed_to_patient": (mut(lambda o: o["vital_signs"][1].update(reported_by="patient")), ["speaker_not_in_cited_lines:vital_signs"]),
    "invented_segment_id": (mut(lambda o: o["symptoms"][1].update(evidence_ids=["SEG0099"])), ["invalid_segment_id:SEG0099", "backfill:invalid_reference"]),
    "model_wrote_EV_records_and_ids": (mut(lambda o: (o["clinical_evidence"].append({"evidence_id": "EV_001"}), o["symptoms"][0].update(evidence_ids=["EV_001"]))), ["model_wrote_evidence_records", "invalid_segment_id:EV_001"]),
    "negative_finding_from_a_question_only": (mut(lambda o: o["negative_findings"][0].update(evidence_ids=[S(4)])), ["negative_finding_without_negation_in_cited_line"]),
    "follow_up_dependent_on_results_turned_into_weeks": (mut(lambda o: o["follow_up"][0].update(time_reference="in two weeks")), ["follow_up_time_not_in_cited_text"]),
    "invalid_enum_for_temporality": (mut(lambda o: o["symptoms"][0].update(temporality="intermittent")), ["enum:symptoms.temporality", "status_temporality_combination"]),
    "template_key_dropped": (mut(lambda o: o["medications"][0].pop("evidence_ids")), ["item_keys:medications", "no_evidence:medications"]),
    "whole_conversation_cited": (mut(lambda o: o["symptoms"][0].update(evidence_ids=[S(i) for i in range(1, 9)])), ["too_many_refs:symptoms"]),
})
out, ok = {}, True
for name, (fn, expect) in cases.items():
    got = review(fn(GOOD))
    hit = all(any(g == e or g.startswith(e) for g in got) for e in expect) and (bool(got) if expect else not got)
    ok &= hit
    out[name] = {"expected_violations": expect, "reported": got, "pass": hit}
    print(("PASS " if hit else "FAIL ") + name + ("" if hit else f" | expected {expect} got {got}"))
rules = {"temporality: ongoing / resolved / earlier episode / intermittent": ["A duration is not an end", "status resolved, temporality past", "does not make it resolved"],
         "negation incl. cues and known-absence phrases": ["denies, without, never had", "No known allergies", "Never create a negative finding"],
         "speaker attribution": ["not patient", "person_1 is not always the patient", "stated_by doctor"],
         "evidence selection": ["smallest set of lines", "never reuse an id", "never invent an id", "clinical_evidence is always []"],
         "vital signs": ["both numbers", "usual unit", "Blood pressure, Heart rate"], "actions and follow-up": ["stays dependent on the results", "One sentence with several instructions gives several items"],
         "anti-hallucination": ["Never invent a fact to fill a field", "Do not assume missing information is negative"]}
cov = {k: all(p in PROMPT for p in v) for k, v in rules.items()}
for k, v in cov.items():
    print(("PASS " if v else "FAIL ") + "prompt states: " + k)
ok &= all(cov.values())
(PKG / "derived").mkdir(exist_ok=True)
(PKG / "derived" / "PROMPT_SYNTHETIC_REVIEW.json").write_text(json.dumps({"note": "invented consultation; validates prompt consistency and the checks, not model behaviour", "cases": out, "rule_coverage": cov, "all_pass": ok,
                                                                          "prompt_sha256": __import__("hashlib").sha256(PROMPT.encode()).hexdigest()}, indent=1, ensure_ascii=False), encoding="utf-8")
print("ALL PASS" if ok else "SOME FAILED")
