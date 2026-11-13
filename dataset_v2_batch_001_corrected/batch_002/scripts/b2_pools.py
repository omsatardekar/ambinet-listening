"""Batch 002 content pools. Applied in memory at generation time by generate_batch_002.py; NO Batch 001 file is modified.

What this module does (all in-process, via in-place list/dict mutation of the unmodified Batch 001 modules):
  * extends the chronic-condition medication options with look-alike drug names (metformin/metoprolol, lisinopril/losartan, carbamazepine/carbimazole-style pairs...)
  * REPLACES the surgical, family-history, allergy and social-history surface pools with new Batch 002 wording (so Batch 002 does not reuse Batch 001 phrasings)
  * adds neutral (placeholder-free) conversation pools: greetings, closings, back-channels, hesitations, rapport, patient elaborations
  * registers acute/chronic duration hints and condition exclusions for the new profiles
Everything here is hand-authored general-knowledge content; none of it was clinically reviewed."""
import content_core as C
import blueprint as BP
import dialogue as DL
import dialogue_pools as T

# ------------------------------------------------------------------ medication options (look-alike names, weekly/daily dosing contrasts)
EXTRA_OPTIONS = {
    "htn": [("metoprolol", "Metoprolol", "50 mg", "twice a day", "oral", "my pressure"), ("lisinopril", "Lisinopril", "10 mg", "once a day", "oral", "my pressure"), ("valsartan", "Valsartan", "80 mg", "once a day", "oral", "my blood pressure"),
            ("hydrochlorothiazide", "Hydrochlorothiazide", "12.5 mg", "every morning", "oral", "my pressure")],
    "dm": [("glibenclamide", "Glibenclamide", "5 mg", "before breakfast", "oral", "my sugar"), ("sitagliptin", "Sitagliptin", "100 mg", "once a day", "oral", "my sugar"),
           ("gliclazide", "Gliclazide", "80 mg", "twice a day", "oral", "my sugar")],
    "lipid": [("simvastatin", "Simvastatin", "20 mg", "at night", "oral", "my cholesterol")],
    "gerd": [("lansoprazole", "Lansoprazole", "30 mg", "before breakfast", "oral", "my acidity")],
    "depression": [("fluoxetine", "Fluoxetine", "20 mg", "every morning", "oral", "my mood"), ("mirtazapine", "Mirtazapine", "15 mg", "at night", "oral", "my mood")],
    "epilepsy": [("carbamazepine", "Carbamazepine", "200 mg", "twice a day", "oral", "the seizures"), ("lamotrigine", "Lamotrigine", "100 mg", "twice a day", "oral", "the fits")],
    "af": [("metoprolol", "Metoprolol", "50 mg", "twice a day", "oral", "the heart rhythm"), ("warfarin", "Warfarin", "3 mg", "in the evening", "oral", "the blood thinning")],
    "hf": [("carvedilol", "Carvedilol", "6.25 mg", "twice a day", "oral", "my heart"), ("metoprolol", "Metoprolol", "50 mg", "twice a day", "oral", "my heart")],
    "ihd": [("metoprolol", "Metoprolol", "50 mg", "twice a day", "oral", "my heart")],
    "asthma": [("Foracort inhaler", "Budesonide/formoterol", None, "twice a day", "inhaled", "my asthma")],
    "oa": [("naproxen", "Naproxen", "250 mg", "twice a day", "oral", "the knee pain")],
    "gout": [("febuxostat", "Febuxostat", "80 mg", "once a day", "oral", "the gout")],
    "hypothyroid": [("Eltroxin", "Levothyroxine", "100 micrograms", "every morning", "oral", "my thyroid")],
    "migraine": [("propranolol", "Propranolol", "40 mg", "twice a day", "oral", "the migraine prevention")],
}
EXTRA_CLASS = {"Lisinopril": "acei", "Valsartan": "arb", "Hydrochlorothiazide": "diuretic", "Glibenclamide": "sulfonylurea", "Sitagliptin": "dpp4", "Gliclazide": "sulfonylurea",
               "Simvastatin": "statin", "Lansoprazole": "ppi", "Fluoxetine": "antidepressant", "Mirtazapine": "antidepressant", "Carbamazepine": "anticonvulsant", "Lamotrigine": "anticonvulsant",
               "Metoprolol": "betablocker", "Warfarin": "anticoagulant", "Carvedilol": "betablocker", "Naproxen": "nsaid", "Febuxostat": "gout", "Propranolol": "betablocker",
               "Ciprofloxacin/dexamethasone ear drops": "antibiotic", "Flucloxacillin": "antibiotic", "Phenoxymethylpenicillin": "antibiotic"}

SURG_B2 = [  # (patient phrase, normalized, timeframe)
    ("my appendix taken out", "Appendicectomy", "when I was in my twenties"),
    ("keyhole surgery on my gallbladder", "Cholecystectomy", "two years back"),
    ("an operation for a hernia", "Hernia repair", "last spring"),
    ("my tonsils removed", "Tonsillectomy", "as a teenager"),
    ("a caesarean for my second baby", "Caesarean section", "nine years ago"),
    ("a meniscus repair on my knee", "Knee meniscal repair", "four years ago"),
    ("a cataract operation in my left eye", "Cataract surgery", "about a year ago"),
    ("my womb taken out", "Hysterectomy", "fifteen years ago"),
    ("two stents put in my heart", "Coronary stenting", "three years ago"),
    ("a mole taken off my arm", "Excision of skin lesion", "a few years ago"),
    ("a triple bypass", "Coronary artery bypass grafting", "eight years ago"),
    ("part of my thyroid removed", "Thyroid surgery", "years back"),
    ("a bunion operation", "Bunion surgery", "six years ago"),
    ("a varicose vein procedure", "Varicose vein surgery", "last year"),
    ("my septum straightened", "Septoplasty", "in my thirties"),
    ("a wisdom tooth extraction under sedation", "Wisdom tooth extraction", "five years ago"),
]
FAMILY_B2 = [  # (spoken phrase, normalized, relation) -- spoken contains had/has/was; relation word occurs literally
    ("My grandfather had a stroke", "Stroke", "grandfather"),
    ("My aunt has rheumatoid arthritis", "Rheumatoid arthritis", "aunt"),
    ("My son has asthma", "Asthma", "son"),
    ("My mother had a stroke", "Stroke", "mother"),
    ("My brother has epilepsy", "Epilepsy", "brother"),
    ("My father has Parkinson's disease", "Parkinson disease", "father"),
    ("My sister had breast cancer", "Breast cancer", "sister"),
    ("My uncle has high cholesterol", "Hypercholesterolaemia", "uncle"),
    ("My mother has an underactive thyroid", "Hypothyroidism", "mother"),
    ("My cousin has psoriasis", "Psoriasis", "cousin"),
    ("My grandmother had dementia", "Dementia", "grandmother"),
    ("My father had bowel cancer", "Colorectal cancer", "father"),
    ("My daughter has type 1 diabetes", "Type 1 diabetes mellitus", "daughter"),
]
ALLERGY_B2 = [  # (substance, normalized, type, reactions)
    ("amoxicillin", "Amoxicillin", "medication", ["a rash all over", "hives"]),
    ("erythromycin", "Erythromycin", "medication", ["bad stomach cramps", "a rash"]),
    ("diclofenac", "Diclofenac", "medication", ["wheezing", "swelling of my lips"]),
    ("trimethoprim", "Trimethoprim", "medication", ["a rash", "itching"]),
    ("tramadol", "Tramadol", "medication", ["vomiting", "feeling very drowsy"]),
    ("naproxen", "Naproxen", "medication", ["a rash", "stomach pain"]),
    ("walnuts", "Walnut", "food", ["my lips swelling", "hives"]),
    ("milk", "Cow's milk", "food", ["a rash", "stomach cramps"]),
    ("wheat", "Wheat", "food", ["bloating", "itchy skin"]),
    ("kiwi", "Kiwi fruit", "food", ["an itchy mouth", "hives"]),
    ("grass pollen", "Grass pollen", "environmental", ["sneezing", "itchy eyes"]),
    ("cat fur", "Cat dander", "environmental", ["sneezing", "wheezing"]),
    ("nickel", "Nickel", "environmental", ["a rash on my skin"]),
    ("plasters", "Adhesive plasters", "environmental", ["a red itchy rash"]),
]
ALLERGY_AVOID_B2 = {"amoxicillin": "penicillin", "erythromycin": "macrolide", "diclofenac": "nsaid", "trimethoprim": "sulfa", "tramadol": "opioid", "naproxen": "nsaid"}

SOCIAL_B2 = [  # (category, status, spoken, desc, details) ; details is a substring of spoken
    ("smoking", "current", "I smoke roughly a pack every two days", "Current smoker", "roughly a pack every two days"),
    ("smoking", "current", "I have about eight cigarettes in a day", "Current smoker", "about eight cigarettes in a day"),
    ("smoking", "former", "I gave up cigarettes last spring", "Former smoker", "gave up cigarettes last spring"),
    ("smoking", "former", "I quit smoking around ten years ago", "Former smoker", "quit smoking around ten years ago"),
    ("smoking", "never", "I've never touched a cigarette", "Never smoked", None),
    ("smoking", "never", "No, I've never smoked in my life", "Never smoked", None),
    ("alcohol", "current", "I'll have a glass of wine with dinner", "Occasional alcohol use", "a glass of wine with dinner"),
    ("alcohol", "current", "I only drink at family occasions", "Occasional alcohol use", "only drink at family occasions"),
    ("alcohol", "never", "Nothing, I'm teetotal", "Does not drink alcohol", None),
    ("alcohol", "former", "I used to drink heavily but I stopped four years ago", "Former alcohol use", "stopped four years ago"),
]
SOC_EXTRA_B2 = [  # (category, status, question, spoken, description, details)
    ("occupation", "current", "What line of work are you in?", "I'm a bus driver, so I sit for long hours", "Bus driver", "bus driver"),
    ("occupation", "current", "Are you in work at the moment?", "Yes, I work in a bakery, early starts", "Baker", "work in a bakery"),
    ("occupation", "current", "What do you do during the day?", "I look after my grandchildren most days", "Childcare for grandchildren", "look after my grandchildren"),
    ("occupation", "current", "Do you work outside the home?", "I'm a hairdresser, on my feet all day", "Hairdresser", "hairdresser"),
    ("occupation", "current", "And your job?", "I work in accounts at a hospital", "Accounts worker", "work in accounts at a hospital"),
    ("occupation", "current", "What's your work?", "I'm a plumber, lots of bending and kneeling", "Plumber", "plumber"),
    ("occupation", "retired", "Have you retired yet?", "I retired from the post office two years ago", "Retired", "retired from the post office"),
    ("exercise", "current", "Do you do any exercise?", "I swim twice a week", "Regular swimming", "swim twice a week"),
    ("exercise", "current", "Anything you do to stay fit?", "I do a yoga class on Thursdays", "Weekly yoga", "yoga class on Thursdays"),
    ("exercise", "none", "Do you get out much?", "Not much, I mostly stay in these days", "Little activity", "mostly stay in"),
    ("exercise", "current", "Are you active?", "I walk the dog every morning", "Daily dog walking", "walk the dog every morning"),
    ("exercise", "none", "How active are you?", "I hardly move around during the day", "Sedentary", "hardly move around"),
    ("diet", "current", "What does a normal day of food look like?", "Lots of rice, lentils and some fruit", "Rice and lentil based diet", "rice, lentils and some fruit"),
    ("diet", "current", "How are your meals?", "I grab fast food at lunch most days", "Frequent fast food", "fast food at lunch"),
    ("diet", "current", "Do you follow any particular diet?", "I'm vegetarian and have been for years", "Vegetarian diet", "vegetarian"),
    ("diet", "current", "Tell me about your eating.", "I drink a lot of tea and snack through the day", "Frequent snacking and tea", "a lot of tea and snack"),
    ("living", "current", "Who lives with you?", "My partner and our baby", "Lives with partner and baby", "my partner and our baby"),
    ("living", "current", "Do you live by yourself?", "No, I share a house with my brother", "Shares house with brother", "share a house with my brother"),
    ("living", "current", "Is there someone at home?", "My husband and I live above the shop", "Lives with husband", "my husband and I"),
    ("living", "current", "Are you on your own at home?", "I live with my elderly mother", "Lives with mother", "live with my elderly mother"),
]

GREET_D_B2 = ["Hello, come in. Mind the step.", "Good morning. I've just got your notes up.", "Hi, take a seat wherever you like.", "Morning, come on through.",
              "Right, thanks for waiting, come in.", "Evening. Let's make this quick but thorough.", "Hello, I'll be with you in a second, just sit down.", "Welcome. Make yourself comfortable."]
GREET_P_B2 = ["Hi there.", "Morning, doctor, sorry about the rush.", "Hello, thanks for fitting me in.", "Hi doctor, I got here as fast as I could.", "Afternoon. Is this seat fine?"]
ASK_D_B2 = ["What would you like to start with today?", "Tell me what's brought you in.", "So what can I do for you?", "What's been worrying you?", "Where shall we begin?"]
CARE_ENTER_B2 = ["Hello, doctor. I'm here with them in case I can help.", "Good afternoon, doctor. I look after them so I thought I'd come.", "Doctor, I'll sit in if that's okay, I know what's been happening."]
CLOSE_D_B2 = ["That's everything on my side. Anything you're unsure about?", "Right, that's the plan. Do you want to ask me anything?", "I think we're done unless you have questions.", "Does all of that make sense?"]
CLOSE_P_B2 = ["That's clear, thanks.", "Right, I'll do that. Thank you, doctor.", "Okay, that makes sense. Thanks for explaining.", "Thank you, that's helpful.", "Good, thanks, I'll see you then."]
CLOSE_D2_B2 = ["Take care now.", "See you soon.", "All the best.", "Look after yourself."]
BACKCH_B2 = ["Yes.", "Mm, okay.", "Understood.", "Ah.", "Right, right.", "Okay, go on."]
P_OK_B2 = ["Yes, that's fine.", "Right.", "Of course.", "Okay, doctor.", "Yeah, no problem."]
EXAM_STEPS_B2 = ["Let me just feel here.", "Take a breath for me.", "Tell me if that's sore.", "I'll just listen to your chest.", "Lift your arm for me.", "Hold it there for a moment."]
HOLD_A_B2 = ["Sorry, I'm just finishing a note.", "One second, I want to get that written down.", "Bear with me, the system is slow."]
HOLD_B_B2 = ["Right, thanks for waiting.", "Okay, I'm back.", "Sorry about that, carry on."]
RAPPORT_B2 = [("Was it a long journey this morning?", "Not too bad, the roads were quiet."), ("Have you been waiting long?", "Only about ten minutes, honestly."),
              ("Is it your first time here?", "No, I came last year for something else."), ("Cold out there today?", "Freezing, I could hardly feel my hands.")]
P_ELAB_B2 = ["My neighbour said I should get it looked at.", "I didn't want to bother you but it keeps coming back.", "I've been putting this off for weeks.",
             "I told my wife I'd come today.", "I've been reading about it online and it worried me.", "Work has been very busy so I kept ignoring it."]
HESITATIONS_B2 = ["Erm, ", "Let me think, ", "Actually, ", "Sorry, what was I saying, ", "Ah, ", "Mm, "]

ACUTE_B2 = {"b2_acute_bronchitis_smoker", "b2_gastroenteritis_traveller", "b2_acute_otitis_externa", "b2_sinusitis_facial_pain", "b2_sudden_hearing_loss", "b2_tonsillitis_recurrent",
            "b2_uti_recurrent_cystitis", "b2_malaria_travel_return", "b2_cellulitis_leg", "b2_hepatitis_travel_jaundice", "b2_covid_like_illness_older", "b2_minor_burn_kitchen",
            "b2_laceration_finger_tetanus", "b2_allergic_reaction_new_medicine", "b2_head_injury_minor_fall", "b2_ankle_sprain_ottawa", "b2_shingles_early", "b2_vertigo_vestibular_neuritis",
            "b2_first_seizure_followup", "b2_early_pregnancy_bleeding", "b2_vaginal_discharge_thrush", "b2_gallstone_colic", "b2_hypoglycaemia_episodes", "b2_postural_dizziness",
            "b2_post_viral_cough_breathlessness", "b2_rectal_bleeding_haemorrhoids", "b2_diabetic_foot_ulcer", "b2_night_sweats_workup", "b2_dyspepsia_nsaid"}
CHRONIC_B2 = {"b2_unintentional_weight_loss", "b2_nocturnal_leg_cramps", "b2_b12_deficiency_symptoms", "b2_stable_angina_exertional", "b2_leg_oedema_heart_failure",
              "b2_uncontrolled_hypertension_headache", "b2_chronic_dry_cough", "b2_sleep_apnoea_snoring", "b2_constipation_adult", "b2_new_diabetes_symptoms",
              "b2_osteoporosis_fracture_risk", "b2_tension_headache_analgesic_overuse", "b2_memory_difficulty_older", "b2_hip_osteoarthritis_groin", "b2_plantar_fasciitis_heel",
              "b2_contact_dermatitis_hands", "b2_acne_scarring_isotretinoin_review", "b2_dry_eye_screen_use", "b2_pcos_irregular_cycles", "b2_perimenopause_hot_flushes",
              "b2_heavy_periods_iron_deficiency", "b2_low_mood_stress_work", "b2_hyperthyroid_symptoms", "b2_carpal_tunnel_numb_hands", "b2_lumbar_radiculopathy_sciatica",
              "b2_rotator_cuff_shoulder", "b2_suspicious_mole_biopsy", "b2_scabies_household", "b2_coronary_disease_antiplatelet_review", "b2_palpitations_paroxysmal"}
EXCL_B2 = {"b2_new_diabetes_symptoms": {"dm"}, "b2_hyperthyroid_symptoms": {"hypothyroid"}, "b2_heavy_periods_iron_deficiency": {"anemia"}, "b2_perimenopause_hot_flushes": set(),
           "b2_b12_deficiency_symptoms": {"anemia"}, "b2_palpitations_paroxysmal": {"af"}, "b2_pcos_irregular_cycles": {"osteopor"},
           # clinical-plausibility exclusions (not clinically reviewed): no teratogenic/contra-indicated chronic drugs in early pregnancy; no NSAID prescription with common NSAID cautions
           "b2_early_pregnancy_bleeding": {"osteopor", "lipid", "af", "htn", "hf", "gout", "epilepsy", "ckd"},
           "b2_rotator_cuff_shoulder": {"asthma", "ckd", "gerd", "hf", "af", "ihd", "anemia"}, "b2_lumbar_radiculopathy_sciatica": {"asthma", "ckd", "gerd", "hf", "af", "ihd", "anemia"},
           "b2_gallstone_colic": {"asthma", "ckd", "gerd", "hf", "af", "ihd", "anemia"}}
REQ_B2 = {"b2_leg_oedema_heart_failure": "hf", "b2_coronary_disease_antiplatelet_review": "ihd", "b2_diabetic_foot_ulcer": "dm", "b2_hypoglycaemia_episodes": "dm", "b2_osteoporosis_fracture_risk": "osteopor",
          "b2_acute_bronchitis_smoker": "copd", "b2_exertional_wheeze_young_asthma": "asthma"}


def _inplace(lst, new):
    lst[:] = new


def apply():
    """Idempotent: calling twice is harmless."""
    for k, opts in EXTRA_OPTIONS.items():
        have = {o[0] for o in C.COND[k][2]}
        C.COND[k][2].extend(o for o in opts if o[0] not in have)
    BP.CLASS.update(EXTRA_CLASS)
    _inplace(C.SURG, SURG_B2)
    _inplace(C.FAMILY, FAMILY_B2)
    _inplace(C.ALLERGY, ALLERGY_B2)
    C.ALLERGY_AVOID.clear()
    C.ALLERGY_AVOID.update(ALLERGY_AVOID_B2)
    _inplace(C.SOCIAL, SOCIAL_B2)
    _inplace(BP.SOC_EXTRA, SOC_EXTRA_B2)
    for lst, extra in ((T.GREET_D, GREET_D_B2), (T.GREET_P, GREET_P_B2), (T.ASK_D, ASK_D_B2), (T.CARE_ENTER, CARE_ENTER_B2), (T.CLOSE_D, CLOSE_D_B2), (T.CLOSE_P, CLOSE_P_B2),
                       (T.CLOSE_D2, CLOSE_D2_B2), (T.D_BACKCH, BACKCH_B2), (T.P_OK, P_OK_B2), (T.EXAM_STEPS, EXAM_STEPS_B2), (T.HOLD_A, HOLD_A_B2), (T.HOLD_B, HOLD_B_B2),
                       (T.RAPPORT, RAPPORT_B2), (T.P_ELAB, P_ELAB_B2), (DL.HES, HESITATIONS_B2)):
        for x in extra:
            if x not in lst:
                lst.append(x)
    # symptoms whose name already carries an intensity/event meaning get no separate mild/moderate/severe rating (avoids "light bleeding ... severe")
    from b2_pools_replace import REPLACE   # full replacement of the placeholder-free Batch 001 conversational pools (wording only)
    for name, new in REPLACE.items():
        getattr(T, name)[:] = new
    BP.NOSEV = tuple(BP.NOSEV) + ("bleeding", "spotting", "heavy period", "bump", "lump", "burn", "cut on", "laceration", "sudden", "fracture", "blister", "bite mark", "high fever", "fever with rigors", "injury", "twisted")
    BP.PROF.update({p["key"]: p for p in C.PROFILES})   # blueprint built its profile index at import time, before the Batch 002 profiles were registered
    BP.ACUTE.update(ACUTE_B2)
    BP.CHRONIC.update(CHRONIC_B2)
    BP.EXCL.update(EXCL_B2)
    BP.REQ.update(REQ_B2)
