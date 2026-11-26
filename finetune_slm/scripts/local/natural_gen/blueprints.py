"""Situation families and natural-speech features for the second-round training data (natural, medium and hard consultations).

Each family is a real-life kind of visit with what truly exists in it and where the traps are. build_specs() combines a family with a random
setting (age, sex, names, language flavour, speakers), a difficulty (medium / hard) and a few natural-speech features, so that no two encounters
share a skeleton. The generator is told to write the conversation the way people really talk, not as a checklist.
"""
import random

FAMILIES = [
 ("exertional_chest_tightness", "Man or woman 50-70 who comes 'for a check-up' and only slowly admits a tight feeling in the chest when climbing stairs or walking fast; first denies chest pain, later describes the tightness. Takes a BP tablet and aspirin on and off. Doctor orders ECG and bloods."),
 ("child_fever_two_parents", "Parent brings a toddler or school-age child with fever and cough; the two parents (or parent and grandparent) disagree about how long, how high, and what was given (paracetamol vs ibuprofen, doses by 'spoon'). Child says only a few words."),
 ("elderly_polypharmacy_carer", "Older patient with a live-in carer or daughter who manages the pill box; names of tablets are described ('the little white one', 'the water tablet'), one was stopped by another doctor, one is double-counted. Doctor reviews and changes one medicine."),
 ("diabetes_review_insulin_confusion", "Type 2 diabetic on tablets plus insulin; patient and nurse give different insulin doses, patient skips doses on work days, reads home sugar numbers aloud in a muddled way ('one-eighty-something fasting'). Foot and eye questions."),
 ("ace_inhibitor_cough", "Hypertension patient with a dry cough for weeks that they connect to 'a cold'; recently started ramipril or enalapril; they mention a relative's lisinopril. Doctor thinks aloud, changes the drug but does not give a firm diagnosis of the cough."),
 ("anxiety_palpitations", "Young adult with palpitations and breathlessness, worse at night and before exams or work meetings; downplays stress, drinks a lot of coffee and energy drinks, vapes; friend or partner contributes. Doctor orders ECG and thyroid tests, discusses breathing exercises."),
 ("mechanical_back_pain_red_flags", "Manual worker or office worker with low back pain for 'a few weeks or since the move'; doctor asks about red flags (numbness, bladder, weight loss, fever) one by one; patient answers some clearly, some vaguely or with a story. Painkiller use mentioned."),
 ("recurrent_uti_woman", "Woman with burning urine again; says 'third time this year' then corrects to 'maybe the fourth'; took leftover antibiotic from a sister; embarrassed; vaginal symptoms denied, then partly admitted. Urine test ordered."),
 ("migraine_new_pattern", "Person with long headaches who now has a different pattern (worse in the morning, or with vomiting); takes sumatriptan or paracetamol often; partner says snoring and tiredness too; patient dismisses it. Doctor does a quick neuro exam and orders a scan conditionally."),
 ("asthma_flare_inhaler", "Teenager or adult wheezy after a cold; confuses blue and brown inhaler; uses the reliever 'maybe five, six times a day'; peak flow numbers read by the nurse. Doctor adds a steroid course."),
 ("rash_possible_allergy", "Itchy rash after 'something I ate or the new cream or the antibiotic'; patient unsure which; a family member says the same happened with penicillin in childhood, patient denies. No firm diagnosis; patch test or antihistamine."),
 ("early_pregnancy_bleeding", "Woman about 8-10 weeks pregnant with spotting and cramps; unsure of dates ('the last period was around Diwali, or after'); anxious; partner waits outside then joins. Scan and blood tests planned today, strict return advice."),
 ("heavy_periods_anaemia", "Tired, breathless woman with heavy periods for a year; counts pads and clots in vague terms; takes iron 'sometimes'; hair loss; relative mentions thyroid in the family. Blood tests, maybe pelvic scan."),
 ("thyroid_fatigue", "Middle-aged person tired and cold for months, weight up, constipated, low mood; pins it on work and age; mother had thyroid disease; one old thyroid test result recalled wrongly ('borderline, they said'). Blood test planned."),
 ("knee_osteoarthritis", "Older patient with knee pain going down stairs and at night; uses diclofenac gel and sometimes tablets from the pharmacy; says no stomach problems and then mentions heartburn; weight discussed; physio or injection discussed, not decided."),
 ("low_mood_sleep", "Adult with poor sleep, low energy and loss of interest for months after a job loss or bereavement; partner or parent speaks for them; patient says 'I'm fine' then partly opens up; denies thoughts of self-harm clearly (doctor asks gently); medication discussed but not started today."),
 ("traveller_gastroenteritis", "Diarrhoea and vomiting after a trip or a wedding meal; others at the event are ill; patient counts bowel movements loosely; takes loperamide against advice; mild dehydration signs; stool test conditional; advice on fluids."),
 ("copd_smoker_review", "Long-term smoker with morning cough and breathlessness; minimises smoking ('about ten a day... maybe twenty'), inhalers used irregularly, a recent chest infection; spirometry numbers read aloud; quitting support offered."),
 ("new_hypertension_found", "Patient attends for something minor (a knee or a form) and the nurse finds high BP; BP read aloud twice with different numbers; patient says it is white coat; family history of stroke said in passing; no tablets started today, home monitoring arranged."),
 ("gout_flare", "Man with a very painful swollen big toe since last night; drinks beer at weekends, takes a water tablet; had the same 'a year back'; says no injury then recalls kicking a chair; colchicine or NSAID plan; blood uric acid test."),
 ("child_ear_pain", "Mother and a child with ear pain and night crying after a cold; mother says no fever, grandmother says it was hot; mother unsure about the amoxicillin the child had 'long ago, got a rash maybe'; doctor decides on watchful waiting with a back-up plan."),
 ("elderly_falls_dizziness", "Older patient who fell twice 'but not really fell, slid down'; dizzy on standing; takes several BP and sleeping tablets; daughter reports what the patient minimises; nurse reads lying and standing BP; doctor changes one tablet."),
 ("persistent_cough_after_virus", "Cough for six weeks after flu; worse at night; patient says no weight loss, then says clothes are loose; recent travel or TB contact denied by patient but a family member recalls a cousin's illness; doctor orders chest X-ray, avoids naming a cause."),
 ("statin_stopped_med_review", "Patient on routine review who admits stopping the cholesterol tablet after reading something online, still takes the BP tablet but 'every other day'; mentions husband's diabetes pills; doctor does not scold, plans repeat blood tests and revisits the statin decision in a month."),
 ("alcohol_disclosure", "Person attending for stomach pain and poor sleep; alcohol answered casually ('socially'), later 'a bottle of wine most nights, perhaps'; doctor non-judgemental; liver blood tests ordered; stomach medicine started."),
 ("memory_concerns_spouse", "Spouse brings an older person who 'is fine' but repeats questions, forgets appointments and got lost; patient disagrees on many points; medicines managed by spouse; doctor plans bloods and a memory assessment, no diagnosis said aloud."),
 ("post_op_wound_check", "Patient 10 days after a hernia, appendix or caesarean operation; wound redness and discharge, fever the night before; nurse removes dressing and describes it; patient is vague about antibiotic course ('five days... or was it seven'); wound swab and antibiotic change."),
 ("pharmacy_tech_and_patient_refill", "Routine repeat-prescription review at a small clinic with a pharmacy technician present; patient wants a stronger painkiller; tablet names and doses are discussed in detail, one dose is read from the pharmacy list and differs from the patient's own; doctor declines the stronger medicine."),
]

FEATURES = [
 "self_correction: a speaker states a number, drug name or duration and then corrects it in the same turn or later ('seventy-five... no, hundred and fifty'). The label holds only the corrected value.",
 "spoken_numbers: doses, vitals and durations are spoken as words or sloppy speech ('a hundred and two point five', 'one-forty over ninety', 'five-ish years', 'twenty milligram'); the label writes them normally (102.5, 140/90, 20 mg) and does not turn vague ones into exact ones.",
 "denial_then_admission: the patient first denies a symptom, then later describes it. The label records the symptom as present (the later, fuller answer) and does NOT also record the earlier denial as a negative finding.",
 "third_party_medicine: someone mentions a medicine or condition that belongs to a relative or friend (the sister's biotin, the husband's metformin). It must not appear as the patient's own; a relative's illness can only be family history if said as such.",
 "stopped_or_never_taken: a medicine the patient stopped, was never given or only took once ('I stopped it in March'). Status discontinued, not current; a medicine never taken is not recorded as a medication.",
 "tangent_small_talk: a long tangent or small talk (traffic, cricket, the weather, a grandchild) that holds NO clinical content; nothing from it is extracted.",
 "interruptions_trailing_off: people interrupt each other, trail off, or the answer comes two turns after the question.",
 "colloquial_drug_names: medicines referred to by colour, purpose or brand ('the water tablet', 'Crocin', 'my sugar tablets', 'the purple inhaler'); the name is recorded as said, the normalized name only if it is clear.",
 "doctor_thinks_aloud: the doctor lists possible causes or says what they will not conclude yet. Only record a clinical assessment if the doctor actually states a leading or differential impression; 'let's see what the tests say' is not an assessment.",
 "hedged_plan: the doctor hedges ('we might do a scan if it does not settle', 'let's see in two weeks'). Conditional vs planned status must follow the words.",
 "disputed_numbers: the nurse reads a value and the patient or relative disagrees or remembers another (a dose, a weight, a BP). Keep both and record an uncertainty.",
 "vague_dates: the patient cannot date things ('since Diwali or after', 'last winter, or the one before'); no invented date; a date_uncertain item.",
 "relative_speaks_for_patient: a relative answers for the patient and the patient partly contradicts; reported_by follows who said it.",
 "test_result_recalled: the patient reports an old test or result ('they said it was borderline'); recorded as reported history/investigation only as far as said, not as a confirmed value.",
 "ambiguous_answer: an answer that sounds like yes but is really 'maybe' ('mm, I suppose', 'sometimes, not really'); recorded with uncertainty or not at all, never as a firm fact.",
 "doctor_misses_topics: the doctor does not ask about everything; topics never discussed are simply absent (no invented denials, no allergy line if allergies were never mentioned).",
 "patient_answers_other_question: the patient answers a different question than the one asked, and the doctor repeats or lets it go.",
 "doctor_changes_mind: the doctor says one plan, then changes it after new information; the label holds the final plan.",
]

STYLES = [
 "chatty, goes off on tangents", "terse, one-word answers", "anxious, asks many questions", "dismissive, minimises everything",
 "polite and formal", "tired and irritable", "very detailed, over-explains", "uncertain, 'I don't know, doctor'",
]
DOCTOR_STYLES = [
 "brisk, closed questions", "warm, open questions", "thinks aloud and explains", "distracted by the computer, asks for repeats", "careful, summarises back",
]
FLAVOURS = ["Indian English", "British English", "American English", "Irish English", "Australian English", "South African English"]
EXTRA_SPEAKERS = [
 [], [], ["NURSE"], ["FAMILY_MEMBER"], ["CAREGIVER"], ["NURSE", "FAMILY_MEMBER"], ["CLINICAL_STAFF"], ["FAMILY_MEMBER", "NURSE"], ["CAREGIVER", "NURSE"],
]


def build_specs(n: int, first_id: int, seed: int = 20261125) -> list[dict]:
    rng = random.Random(seed)
    specs = []
    fam_cycle = []
    while len(fam_cycle) < n:
        order = FAMILIES[:]
        rng.shuffle(order)
        fam_cycle += order
    for i in range(n):
        key, desc = fam_cycle[i]
        hard = i % 2 == 0
        feats = rng.sample(FEATURES, 4 if hard else 2)
        extra = rng.choice(EXTRA_SPEAKERS)
        if key in ("child_fever_two_parents", "child_ear_pain"):
            extra = ["FAMILY_MEMBER"] + [x for x in extra if x != "FAMILY_MEMBER"][:1]
        if key in ("elderly_polypharmacy_carer", "memory_concerns_spouse") and not extra:
            extra = ["CAREGIVER"] if key == "elderly_polypharmacy_carer" else ["FAMILY_MEMBER"]
        specs.append({"id": f"{first_id + i}", "family": key, "situation": desc, "difficulty": "hard" if hard else "medium", "features": feats,
                      "extra_speakers": extra, "patient_style": rng.choice(STYLES), "doctor_style": rng.choice(DOCTOR_STYLES), "flavour": rng.choice(FLAVOURS),
                      "target_turns": rng.randint(46, 84) if hard else rng.randint(36, 62)})
    return specs
