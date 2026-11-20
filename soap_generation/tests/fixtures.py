"""Small synthetic documents for the SOAP tests (no real data)."""
import copy

SEG = lambda i, role, t, text: {"segment_id": f"SEG{i:04d}", "status": "resolved", "role": role, "speaker_id": "p", "start_seconds": t, "end_seconds": t + 4, "text": text, "match_score": 0.9}  # noqa: E731


def fact(path, *segments):
    return {"path": path, "fact_label": path, "segments": list(segments), "source": "backend_matched" if segments else "none", "flags": []}


# an extraction with the kinds of mistakes seen in the live runs (see docs/MODULE3_FINETUNING_FOCUS.md)
BAD_EXTRACTION = {
    "encounter_id": "03",
    "chief_complaint": {"value": "I'm not letting go", "reported_by": "patient", "evidence_ids": []},
    "symptoms": [{"name": "bruises", "status": "present", "body_site": "forearms", "duration": {"value": 3, "unit": "weeks", "normalized": "3 weeks"}, "evidence_ids": []},
                 {"name": "tiredness", "status": "present", "evidence_ids": []}],
    "negative_findings": [{"finding": "tiredness", "status": "absent", "evidence_ids": []}],
    "medical_history": {"past_medical_history": [{"condition": "heart trouble", "status": "ongoing", "evidence_ids": []}], "surgical_history": [], "family_history": [], "social_history": []},
    "medications": [
        {"name": "Rennie", "dose": "75", "frequency": "twice a day", "status": "currently_used", "evidence_ids": []},
        {"name": "aspirin", "dose": "75", "frequency": "twice a day", "status": "currently_used", "evidence_ids": []},
        {"name": "clopidogrel", "dose": "75", "frequency": "twice a day", "status": "currently_used", "evidence_ids": []},
        {"name": "simvastatin", "dose": "20 mg", "frequency": "at night", "status": "currently_used", "evidence_ids": []}],
    "allergies": [{"substance": "Rennie", "allergy_type": "medication", "reaction": "burning", "status": "reported", "evidence_ids": []}],
    "vital_signs": [{"name": "blood pressure", "value": "119/74", "unit": "mmHg", "evidence_ids": []},
                    {"name": "oxygen saturation", "value": "98", "unit": "mmHg", "evidence_ids": []},
                    {"name": "Blood", "value": "15 poundsa month", "evidence_ids": []}],
    "physical_examination": [{"finding": "bruises on the forearms", "body_site": "forearms", "observed_by": "doctor", "evidence_ids": []}],
    "clinical_assessment": [{"assessment": "tiredness", "certainty": "provisional", "stated_by": "doctor", "evidence_ids": []}],
    "procedures_and_investigations": [{"name": "blood test", "type": "laboratory", "status": "planned", "evidence_ids": []}],
    "clinical_actions": [],
    "follow_up": {"type": "consultation", "time_reference": "52.48s", "status": "planned"},
    "clinical_uncertainties": [{"type": "date_uncertain", "description": "date of the last tablet", "resolution_status": "unresolved", "evidence_ids": []}],
}

BAD_DOC = {
    "document_type": "clinical_extraction", "encounter_id": "03", "extraction": BAD_EXTRACTION,
    "evidence": {"facts": [
        fact("symptoms[0]", SEG(10, "PATIENT", 30, "I have bruises on my arms, they just come.")),
        fact("vital_signs[0]", SEG(20, "DOCTOR", 200, "One nineteen over seventy-four. Very good.")),
        fact("medications[3]", SEG(30, "CAREGIVER", 90, "Simvastatin, twenty, that's at night.")),
        fact("physical_examination[0]", SEG(40, "DOCTOR", 210, "A few small bruises on your forearms.")),
        fact("procedures_and_investigations[0]", SEG(50, "DOCTOR", 260, "I'd like to take some blood to check a low blood count.")),
        fact("medications[0]"), fact("allergies[0]"), fact("follow_up")]},
}

GOOD_NOTE = {
    "note_type": "Outpatient progress note (SOAP)",
    "encounter": {"encounter_id": "03", "date_of_service": "", "patient_age_sex": "", "visit_type": "Outpatient follow-up visit", "participants": ["Patient", "Physician", "Caregiver"], "informants": ["Patient", "Caregiver"]},
    "subjective": {
        "chief_complaint": "Easy bruising, stomach burning and fatigue.",
        "hpi": "Patient reports easy bruising on both forearms for about 3 weeks. Per caregiver, bruises appear without a known injury.",
        "hpi_elements": {"onset": "", "location": "forearms", "duration": "3 weeks", "character": "", "aggravating": "", "alleviating": "", "timing": "", "severity": "", "associated": ""},
        "review_of_systems": {"positive": [{"system": "Skin", "finding": "easy bruising"}], "negative": [], "not_reviewed": ""},
        "past_medical_history": ["Heart disease"], "past_surgical_history": [], "family_history": [], "social_history": [],
        "medications": [{"name": "Simvastatin", "dose": "20 mg", "route": "", "frequency": "at night", "status": "taking", "comment": ""}],
        "allergies": {"status": "not_documented", "items": [], "comment": ""},
    },
    "objective": {"vital_signs": [{"name": "Blood pressure", "value": "119/74", "unit": "mmHg", "comment": ""}],
                  "physical_exam": [{"system": "Skin", "finding": "A few small bruises on the forearms"}], "diagnostics": [], "comment": ""},
    "assessment": {"summary": "Patient with known heart disease and easy bruising.",
                   "problems": [{"number": 1, "problem": "Easy bruising", "status": "new", "clinician_impression": "Possibly related to medication.", "reasoning": "Bruises on the forearms.",
                                 "icd10_suggestion": {"code": "R23.8", "description": "Other skin changes"}}], "differential": []},
    "plan": {"by_problem": [{"problem_number": 1, "diagnostics": ["Blood test to check blood count"], "treatment": [], "patient_education": [], "referrals": [], "follow_up": ""}],
             "return_precautions": [], "follow_up": "", "care_coordination": []},
    "clinician_review": {"items_to_verify": [{"ref": "allergies[0]", "topic": "Rennie listed as an allergy", "reason": "No passage supports an allergy; it appears to be an antacid."}],
                         "documentation_gaps": ["Allergies not discussed"], "attestation": ""},
}


def good_note():
    return copy.deepcopy(GOOD_NOTE)
