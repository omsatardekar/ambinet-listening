"""Batch 004 plan: 500 new, harder scenarios (ids 01001-01500). Seeded; situations are new relative to Batches 1-3."""
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
random.seed(20261121)
S = {
    "General Medicine": ["tiredness that turns out to be several small problems", "patient arrives with a printed internet diagnosis", "two unrelated complaints, one hidden at the end", "repeat visit, symptoms keep changing description", "weight loss the patient is pleased about", "patient asks for a test they read about", "new symptoms after a recent holiday abroad", "vague 'not myself' complaint relayed by a carer", "medication stopped by patient without telling anyone", "results letter misunderstood by patient", "persistent cough blamed on the new house", "night-time itching with no rash", "patient minimises chest tightness while talking about the garden"],
    "Cardiology": ["palpitations only when lying on the left", "exertional breathlessness in a woman told it was anxiety", "fainting while standing in a queue", "new murmur found at a dental check", "blood pressure differs between the two arms", "chest pain that eases on leaning forward", "leg swelling after starting a new tablet", "fitness-tracker alert for irregular rhythm", "athlete with an abnormal pre-participation ECG", "post-stent patient wants to stop aspirin"],
    "Respiratory Medicine": ["chronic cough on an ACE inhibitor, patient refuses to change", "breathless after a long flight", "night cough blamed on the dog", "wheeze that only happens at work", "pleuritic chest pain two weeks after a cold", "occupational dust exposure review", "hoarse voice in a former smoker", "confusion between two inhaler devices", "partner reports breathing pauses in sleep"],
    "Gastroenterology": ["swallowing difficulty that comes and goes", "bloating in a woman who also reports tiredness", "change in bowel habit after antibiotics", "upper abdominal pain after an alcohol binge", "weight loss with normal appetite", "itch and dark urine", "blood on tissue in an embarrassed young man", "coeliac question after a family diagnosis", "reflux that is worse lying on the right side"],
    "Neurology": ["episodes of staring and lost time", "tremor that disappears when holding a cup", "facial numbness for a day, now gone", "headaches that wake the patient at night", "numb fingertips with neck stiffness", "dizzy spells on turning in bed", "memory complaints driven by a worried spouse", "restless legs disturbing the household", "sudden word-finding trouble last Tuesday"],
    "Orthopedics": ["shoulder pain that radiates down the arm at night", "hip pain referred from the back", "child with a limp and no injury", "knee pain after a new running programme", "wrist pain in a new parent", "heel pain after a long flight", "back pain after a minor fall in an older woman", "swollen toe after a night out", "post-fracture check with poor wound healing"],
    "Dermatology": ["a mole the patient says has changed", "rash after starting a new tablet", "itchy scalp and hair thinning", "blisters in an older adult", "persistent nail changes", "recurrent boils", "patch of skin that has lost colour", "rash on the hands in a nurse", "scaling in the ear canal"],
    "Endocrinology": ["fatigue with cold intolerance", "palpitations and weight loss with a tremor", "thirst and frequent urination in an adult", "low sugar episodes in the afternoon", "patient on steroids with new symptoms", "thyroid tablets taken with coffee", "a lump in the neck noticed in the mirror", "polycystic ovary question in a teenager"],
    "Nephrology": ["swollen face in the morning", "blood in the urine without pain", "kidney function dropped after painkillers", "dialysis access concern", "kidney stones recurring", "itching all over in a patient with kidney disease"],
    "ENT": ["one-sided hearing loss after a flight", "ringing in one ear", "persistent hoarseness", "recurrent nosebleeds on blood thinners", "dizziness with ear fullness", "sore throat that will not clear", "a lump under the jaw", "child who is not responding when called"],
    "Ophthalmology": ["sudden floaters and flashes", "painful red eye in a contact-lens wearer", "gradual blurring in one eye", "double vision when tired", "dry gritty eyes with a dry mouth", "eyelid lump that keeps returning"],
    "Pediatrics": ["infant with feeding difficulty", "toddler with a rash and fever", "school-age child with recurrent stomach aches", "adolescent with fainting episodes", "baby who is slow to gain weight", "child with a persistent night cough", "teenager with acne and low mood", "child who has stopped eating after a choking scare"],
    "Geriatrics": ["new confusion after a change of medicines", "falls at night with a full bladder", "poor appetite at 88", "family disagrees about how independent the patient is", "sleepiness after a new painkiller", "carer exhaustion alongside the patient's own complaint", "swelling and cough after stopping a water tablet"],
    "Gynecology": ["irregular bleeding after fifty", "one-sided pelvic pain with nausea", "contraception change after migraines with aura", "worry about an early pregnancy", "painful sex since menopause", "breast pain in the middle of the cycle", "postpartum low mood and bleeding", "recurrent thrush after antibiotics"],
    "Psychiatry": ["panic attacks after a car crash", "low mood with the patient insisting it is physical", "insomnia after a shift-work change", "teenager reluctant to attend school", "alcohol use the patient plays down", "grief that has lasted a year", "obsessive checking at night", "medication side effects the patient hides"],
    "Rheumatology": ["morning stiffness lasting hours", "hand pain after a viral illness", "dry eyes and joint pains", "heel pain and back stiffness in a young man", "hot swollen knee in an older patient", "muscle aches after starting a statin"],
    "Emergency Medicine": ["fall from a ladder with delayed pain", "abdominal pain that moved to one side", "reaction after a meal out", "burn from a kitchen accident", "fever in a patient on chemotherapy", "paracetamol overdose reported by a friend", "bee sting with throat tightness", "head injury in a patient on a blood thinner", "chest pain at a gym"],
    "Infectious Diseases": ["fever after returning from travel", "recurrent urinary infections", "persistent sore throat and swollen glands", "cough and night sweats", "rash after a hike", "needle-stick injury follow-up", "diarrhoea in a returned traveller", "HIV test request without symptoms"],
}
KINDS = {"complex": 0.22, "acute_consult": 0.14, "chronic_followup": 0.14, "sparse_single": 0.10, "medication_focused": 0.10, "caregiver_assisted": 0.10, "emergency": 0.06, "allergy_focused": 0.06, "post_treatment": 0.05, "preventive_check": 0.03}
FEATS = ["date_uncertain", "uncertain_dose", "adherence_uncertain", "incomplete_medication_name", "allergy_uncertain", "conflicting_statement", "duration_disagreement", "medication_discrepancy", "allergy_disputed"]
STYLE_P = ["chatty, adds side stories", "terse, answers in few words", "anxious, asks worried questions", "stoic, downplays problems", "precise, brings notes", "forgetful, corrects themselves", "impatient, short on time", "hesitant, trails off", "polite and formal", "vague, uses everyday words", "talkative but disorganised", "contradicts themselves gently"]
STYLE_D = ["warm, unhurried", "brisk and efficient", "thorough, explains reasoning", "plain-spoken, uses analogies", "asks open questions, lets silences sit", "reassuring, repeats key points back", "direct, lists options", "curious, follows tangents briefly"]
DIAL = ["British English", "North American English", "Australian English", "Irish English", "Indian English"]
OPEN = ["patient jumps straight into the problem", "doctor greets by checking the name", "patient speaks first", "doctor refers to the previous visit or a letter", "doctor starts with the reason noted on the booking", "patient apologises for being late", "small talk about weather/parking first", "doctor asks how the patient prefers to be addressed", "relative translates the first sentences", "patient hands over a written list of questions", "patient corrects the doctor on a detail of the booking"]

sit = [(sp, s) for sp, lst in S.items() for s in lst]
rows = [sit[i % len(sit)] for i in range(500)]
random.shuffle(rows)
kinds = list(KINDS)
w = [KINDS[k] for k in kinds]
plan = []
for n, (sp, s) in enumerate(rows):
    kind = random.choices(kinds, w)[0]
    r = random.random()
    extra = []
    if kind == "caregiver_assisted":
        extra = [random.choice(["CAREGIVER", "FAMILY_MEMBER"])]
    elif r < 0.18:
        extra = ["NURSE"]
    elif r < 0.30:
        extra = ["FAMILY_MEMBER"]
    elif r < 0.36:
        extra = ["CAREGIVER"]
    elif r < 0.40:
        extra = ["CLINICAL_STAFF"]
    elif r < 0.46:
        extra = ["NURSE", "FAMILY_MEMBER"]
    sparse = kind == "sparse_single"
    feats = [] if sparse and random.random() < 0.6 else random.sample(FEATS, random.choice([0, 0, 1, 1, 2]))
    if ("conflicting_statement" in feats or "allergy_disputed" in feats or "duration_disagreement" in feats or "medication_discrepancy" in feats) and not extra:
        extra = [random.choice(["CAREGIVER", "FAMILY_MEMBER"])]
    allergy = random.choice(["not_discussed", "explicit_none", "reported", "reported", "historical", "uncertain", "reported_unknown_reaction"]) if not sparse else random.choice(["not_discussed", "not_discussed", "explicit_none"])
    if "allergy_uncertain" in feats:
        allergy = "uncertain"
    if "allergy_disputed" in feats:
        allergy = "disputed"
    med = random.choice(["none", "none", "existing1"]) if sparse else random.choice(["none", "existing1", "existing2", "existing3", "existing4", "planned1", "planned2"])
    tgt = {"symptoms": random.randint(1, 2) if sparse else random.randint(1, 5),
           "negative_findings": random.randint(0, 2) if sparse else random.randint(0, 5),
           "medications": med, "allergies": allergy,
           "vital_signs": random.choice(["none", "none", "few"]) if sparse else random.choice(["none", "few", "few", "full"]),
           "vitals_read_aloud_by": random.choice(["DOCTOR"] + (["NURSE"] if "NURSE" in extra else [])),
           "physical_examination": random.randint(0, 1) if sparse else random.randint(0, 4),
           "review_of_systems": random.randint(0, 2), "past_medical_history": random.randint(0, 4),
           "surgical_history": random.randint(0, 2), "family_history": random.randint(0, 2), "social_history": random.randint(0, 4),
           "clinical_assessment": random.choice(["none", "provisional", "provisional", "differential", "both"]),
           "investigations": random.randint(0, 4), "follow_up": random.choice(["none", "planned", "planned", "conditional"])}
    plan.append({"encounter_id": f"{1001 + n:05d}", "specialty": sp, "situation": s, "kind": kind, "extra_speakers": extra,
                 "entity_targets": tgt, "special_features": feats, "feature_notes": {},
                 "target_turns": random.randint(34, 64) if not sparse else random.randint(32, 42),
                 "style": {"patient": random.choice(STYLE_P), "doctor": random.choice(STYLE_D), "dialect": random.choice(DIAL), "opening": random.choice(OPEN)},
                 "patient_age": None})
(HERE / "plan").mkdir(exist_ok=True)
(HERE / "plan" / "scenario_plan.json").write_text(json.dumps(plan, indent=1), encoding="utf-8")
print(len(plan), len({p["situation"] for p in plan}), "distinct situations")
