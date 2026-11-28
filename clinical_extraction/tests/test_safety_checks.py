"""Safety checks built from the real m3_01 run (encounter 19): false penicillin allergy next to amoxicillin, BP 100/60 that was not said."""
from clinical_extraction import safety_checks


def _seg(text, role="PATIENT"):
    return {"status": "resolved", "text": text, "role": role}


def _derived(**paths):
    return {"facts": [{"path": p, "segments": segs} for p, segs in paths.items()]}


EXT = {
    "allergies": [{"substance": "penicillin", "status": "reported"}],
    "medications": [{"name": "amoxicillin with clavulanic acid", "generic_name": "Amoxicillin", "status": "planned"},
                    {"name": "metformin", "status": "currently_used"}],
    "vital_signs": [{"name": "Heart rate", "value": 88, "unit": "bpm"}, {"name": "Temperature", "value": 38.3, "unit": "°C"},
                    {"name": "Weight", "value": 52, "unit": "kg"}, {"name": "Blood pressure", "value": "100/60", "unit": "mmHg"}],
}
DER = _derived(**{
    "allergies[0]": [_seg("Okay. Any reaction to any medicine?", "DOCTOR"), _seg("No. Never. I have taken penicillin and everything.")],
    "vital_signs[0]": [_seg("88, and regular. Weight is 52 kg on the scale, and that's nearly 7 less than in March.", "NURSE")],
    "vital_signs[1]": [_seg("38.3. That's a proper fever.", "DOCTOR")],
    "vital_signs[2]": [_seg("Weight is fifty-two kilos on the scale.", "NURSE")],
    "vital_signs[3]": [_seg("88, and regular. Weight is 52 kg on the scale.", "NURSE")],
})


def test_real_run_gives_the_three_warnings():
    found = safety_checks.check(EXT, DER)
    rules = [f["rule"] for f in found]
    assert rules == ["allergy_denied_in_source", "allergy_vs_medicine", "vital_not_in_source"]
    assert "Blood pressure 100/60" in found[2]["warning"] and found[1]["family"] == "penicillin"


def test_genuine_allergy_is_not_flagged_as_denied():
    ext = {"allergies": [{"substance": "penicillin"}]}
    der = _derived(**{"allergies[0]": [_seg("I have taken penicillin once and I came out in a rash.")]})
    assert safety_checks.check(ext, der) == []


def test_unrelated_allergy_and_medicine_not_flagged_and_stopped_medicine_ignored():
    ext = {"allergies": [{"substance": "peanuts"}, {"substance": "penicillin"}],
           "medications": [{"name": "metformin", "status": "currently_used"}, {"name": "amoxicillin", "status": "stopped"}]}
    assert safety_checks.check(ext, {"facts": []}) == []


def test_vital_read_from_spoken_numbers_and_missing_citation():
    ext = {"vital_signs": [{"name": "Blood pressure", "value": "109/77"}, {"name": "Pulse", "value": 72}]}
    der = _derived(**{"vital_signs[0]": [_seg("One oh nine over seventy-seven. That's low for you.", "NURSE")], "vital_signs[1]": []})
    assert safety_checks.check(ext, der) == []


def test_nothing_suspicious_and_bad_input():
    assert safety_checks.check({}, {"facts": []}) == [] and safety_checks.check(None, None) == []
