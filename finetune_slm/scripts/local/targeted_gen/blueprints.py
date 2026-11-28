"""Blueprints for the round-4 targeted dataset.

Every encounter gets one or two TARGET TRAPS: situations built from the mistakes the step-400 model really made in the live tests (docs/11).
In each trap the conversation contains the confusing thing, and the label must show the correct handling (often: leave something out, or label it differently).
Situations (FAMILIES) are different from the themes of the 20 hand-written test scenarios and from the locked test, so nothing here leaks into the evaluation.
Generic natural-speech features (generate_natural.FEATURES) are added on top, and every transcript is written like speech-to-text output.
"""
import random

from finetune_slm.scripts.local.natural_gen.blueprints import DOCTOR_STYLES, EXTRA_SPEAKERS, FEATURES, FLAVOURS, STYLES

# (key, situation). None of these repeats a theme of scenarios/ m3_01-m3_20.
FAMILIES = [
 ("sciatica_leg_pain", "Person with low back pain shooting down one leg for three weeks, worse sitting; takes ibuprofen; a colleague's advice on exercises; doctor examines straight-leg raise and plans physio, no scan yet."),
 ("plantar_heel_pain", "Runner or shop worker with heel pain on the first steps in the morning for two months; new shoes mentioned; doctor suggests stretches and insoles; no tests."),
 ("kidney_stone_colic", "Sudden severe loin pain going to the groin overnight, vomiting once, blood in urine; pain score given loosely; urine dip result read aloud; painkiller and scan planned today."),
 ("hyperthyroid_palpitations", "Younger adult losing weight with a fast heartbeat, sweating, shaky hands, eats more than usual; hair thinning not mentioned; a sister has thyroid disease; blood tests and ECG planned."),
 ("sinusitis_after_cold", "Blocked nose, facial pressure and green discharge ten days after a cold; second week of tiredness; uses nasal spray daily; doctor explains most settle without antibiotics, gives a back-up plan."),
 ("child_eczema_flare", "Mother brings a child with itchy dry patches behind the knees and elbows, worse at night, scratching; creams named by colour; father has asthma; doctor adjusts steroid cream and moisturiser advice."),
 ("vegetarian_iron_deficiency", "Tired young woman, strict vegetarian, breathless on stairs, craving ice; periods normal by her account; blood tests planned; diet advice."),
 ("panic_attack_first", "Young adult after a first episode of sudden chest tightness, shaking and fear on a train; thinks it was a heart attack; no drugs; partner phones in details; doctor orders ECG, teaches breathing."),
 ("carpal_tunnel_night_hands", "Middle-aged office or factory worker with night-time numbness in thumb, index and middle fingers, shakes hands to wake them; dropping cups; splint advice, nerve test conditional."),
 ("shingles_early", "Older person with burning pain on one side of the chest and a few blisters for two days; remembers chickenpox as a child; doctor prescribes antiviral today and gives infection advice about contact with a pregnant relative."),
 ("ankle_sprain_football", "Young player who twisted the ankle yesterday; swelling, can bear weight with pain; doctor applies Ottawa rules aloud, no X-ray unless it worsens; rest and elevation advice."),
 ("gallstone_pain_fatty_food", "Woman with right-upper stomach pain after fatty meals, lasting hours, once with vomiting; takes antacid; mother had gallbladder surgery; blood tests and ultrasound planned."),
 ("hay_fever_season", "Sneezing, itchy eyes and runny nose every spring; takes cetirizine 'sometimes'; sister is allergic to dust; no wheeze; doctor changes antihistamine and adds eye drops."),
 ("viral_conjunctivitis_child_school", "Parent with a child with red sticky eye after a cold; school wants a note; one eye then both; no eye pain; doctor advises hygiene, no antibiotic, explains return advice."),
 ("pcos_acne_irregular", "Young woman with acne and irregular periods for two years, some facial hair, weight gain; mother had diabetes; bloods and pelvic scan planned; contraceptive pill discussed, not started."),
 ("bph_night_urination", "Older man getting up three to four times at night, weak stream, dribbling; drinks tea in the evening; denies blood in urine; PSA and urine tests planned, tamsulosin discussed."),
 ("vertigo_positional", "Spinning for a few seconds when turning in bed or looking up, since last week; nausea; no hearing loss, no ear pain; doctor does a positional test and teaches the exercise."),
 ("tinnitus_ringing_one_ear", "Ringing in the right ear for a month, worse in quiet; works with loud machinery without ear protection; some muffled hearing; hearing test referral."),
 ("ibs_alternating_bowels", "Person with cramps relieved by passing stool, bloating, alternating constipation and loose stools for a year; stress at work; denies blood and weight loss after prompting; bloods planned, diet advice."),
 ("epilepsy_followup_driving", "Adult with epilepsy on levetiracetam, seizure-free for two years, asks about driving; missed doses when travelling; relative saw a 'blank spell' last month; doctor reviews and plans a blood test."),
 ("warfarin_inr_review", "Older patient on warfarin for atrial fibrillation; INR result read aloud; antibiotic started elsewhere; green leafy diet changes; dose adjusted and recheck in a week."),
 ("post_stroke_followup", "Patient three months after a mild stroke with a spouse; slight weakness in the left hand; takes aspirin, atorvastatin and an amlodipine tablet; blood pressure read aloud; walking and speech discussed."),
 ("postnatal_low_mood", "Mother six weeks after delivery, tearful, not sleeping even when the baby sleeps; partner present and anxious; denies harming herself or the baby when asked directly; support and follow-up planned."),
 ("newborn_jaundice_feeding", "Parents with a ten-day-old baby, yellow skin and feeding every four hours; weight read by the nurse; breast milk plus formula; blood test for bilirubin planned today."),
 ("contraception_advice_young_woman", "Young woman asks about contraception, previous pill caused headaches, smokes occasionally; blood pressure read; options discussed; implant leaflet given, decision next visit."),
 ("male_uti_prostatitis", "Man with burning urine, frequency and lower back ache for four days; fever mild; denies discharge; no recent travel; urine test and antibiotic planned, conditional on result."),
 ("inguinal_hernia_lump", "Manual worker with a groin lump that appears on lifting and goes away lying down; mild ache by evening; no vomiting; surgical referral planned, advice on lifting."),
 ("ckd_review_bloods", "Older diabetic with kidney disease on review; creatinine and eGFR read aloud; takes ibuprofen from a shop against advice; ramipril continued, painkiller advice changed."),
 ("hepatitis_travel_jaundice", "Person with yellow eyes, dark urine and tiredness after eating at roadside stalls on a trip; others at the trip also ill; alcohol denied; liver blood tests and hepatitis serology planned."),
 ("scabies_household", "Itchy rash between fingers and at the waist, worse at night, partner and child also itch; permethrin cream explained step by step; household treatment and washing advice."),
 ("dental_abscess_facial_swelling", "Cheek swelling and throbbing toothache for three days after a crown; fever mild; dentist unavailable; doctor prescribes antibiotic, warns about swallowing or breathing difficulty."),
 ("breast_lump_found", "Woman in her forties who found a painless lump in the left breast in the shower; no nipple discharge; mother had breast cancer at fifty-five; examination described; urgent clinic referral."),
 ("changing_mole", "Person with a mole on the back that partner says has changed in colour; bleeding once; sunburn history; doctor describes the mole by features and plans a dermatology referral."),
 ("sickle_cell_pain_crisis", "Young adult with known sickle cell disease and bone pains for two days, fever mild; takes folic acid and hydroxyurea; fluids and painkiller plan; blood tests planned."),
 ("hypertension_medicine_side_effects", "Patient on amlodipine and a water tablet with swollen ankles and passing urine often; blood pressure read at clinic and at home with different numbers; doctor changes one medicine."),
 ("lymph_node_neck_swelling", "Young adult with a painless neck lump for three weeks, night sweats once, no fever now; recent cat scratch mentioned; doctor examines and orders blood tests and ultrasound."),
 ("restless_legs_pregnancy", "Pregnant woman at 30 weeks with creeping legs at night and poor sleep; ferritin discussed; takes folic acid and iron; midwife check booked."),
 ("tennis_elbow_painter", "Painter or carpenter with outer elbow pain for six weeks, worse lifting a cup; takes ibuprofen; physio and brace advice; no injection yet."),
 ("lactose_intolerance_bloating", "Person with bloating and loose stools after milk and ice cream for months, no weight loss; tried to avoid dairy for a week; blood test for coeliac planned; diet diary asked."),
 ("hip_replacement_followup", "Older patient six weeks after a hip replacement with a daughter; wound healed; walks with a stick; takes aspirin for clots and painkiller; swelling of the calf asked about and denied."),
 ("thalassaemia_trait_pregnant_partner", "Couple, wife pregnant, husband found to carry thalassaemia trait at a camp; both anxious; blood tests for the wife planned; genetic counselling discussed."),
 ("night_cramps_calves", "Older person with calf cramps at night for two months; takes a water tablet; drinks little water; magnesium from the shop; blood tests for potassium planned; stretching advice."),
 ("jaw_pain_clicking", "Person with jaw pain on chewing and clicking, worse with stress, teeth grinding noticed by partner; no fever; mouth guard and soft diet advice."),
 ("bell_palsy_new", "Person woke with one side of the face drooping, cannot close the eye, cannot whistle; no arm weakness, no speech problem, ear pain a day before; doctor examines and starts steroids, eye care explained."),
 ("measles_contact_unvaccinated_child", "Parents of a child with rash and fever after a classmate had measles; vaccination status vague; doctor examines, counts days, plans notification and isolation advice."),
 ("hypoglycaemia_diabetic_elderly", "Older diabetic on gliclazide and metformin with morning sweating and shakiness; skips breakfast; daughter reports confusion once; doctor reviews doses and plans a blood test."),
 ("chronic_cough_ex_smoker", "Former smoker who quit last year with a long-standing morning cough and brown phlegm; weight stable; no chest pain; spirometry planned; vaccination advice."),
]

# Target traps: (key, weight, what really happens in the conversation, how the label must treat it)
TRAPS = [
 ("reason_for_visit", 14,
  "The conversation OPENS with a remark, joke, apology for being late, small talk, or a trigger event (a relative's diagnosis, a neighbour's advice, the receptionist's note) BEFORE the real reason is stated. The patient states the real concern a few turns later.",
  "chief_complaint is the real concern in a short phrase in the patient's wording (e.g. 'worried about diabetes', 'voice gets tired'). NOT the opening remark, the joke or the trigger (the relative's illness goes into family_history only if it is a relative's condition said as such)."),
 ("ros_asked_only", 12,
  "The doctor asks only two to four review-of-systems questions (for example fever, weight, cough). Several other body systems are never asked about. One of the asked questions gets a vague or mixed answer.",
  "negative_findings / review_of_systems ONLY for items the doctor actually asked AND the patient answered, evidence = that question and answer. Never add review-of-systems entries for systems nobody asked about, and never cite an unrelated turn (for example a turn about tiredness) for a system review."),
 ("doctor_explanation_not_symptom", 12,
  "The doctor (or nurse) explains a mechanism or a diagnosis in the patient's body ('the voice box is irritated by reflux', 'diabetes dulls the nerves in the feet', 'the swelling is your body fighting infection'). A nurse or caregiver also mentions a fact about THEIR OWN life (their sister, their child, their own illness).",
  "Explanations by the doctor are NEVER symptoms, history or social history of the patient; they may only appear as clinical_assessment or counselling if the doctor stated them as such. A nurse's or caregiver's own life facts are not recorded as the patient's. Each symptom's reported_by is the person who really described it."),
 ("booked_vs_conditional", 10,
  "In the plan the doctor books some tests or visits for a definite time ('the nurse takes bloods Thursday morning', 'I'll see you in two weeks') and makes others conditional ('if those are borderline we do the third test', 'if it does not settle, a scan').",
  "Booked or arranged = status planned. Only the hedged ones are conditional. Never mark a booked test conditional or 'if needed'. Instructions for the booked test (fasting, time, medicine timing) belong to that test's action, not a separate invented plan item."),
 ("negatives_and_flips", 10,
  "The patient denies some symptoms (said as 'no', 'not really', 'never'), has a chronic condition named earlier (for example asthma or hypertension) and later the doctor asks about another symptom of it, and one answer is a double negative or a correction ('not that either', 'no... well, sometimes').",
  "Denials go in negative_findings with the exact thing denied, never in symptoms. NEVER write a negative about a condition the patient has said they have. A corrected answer keeps only the final version. A negative is never a symptom, and 'not painful' is the finding 'pain' absent, not a symptom called 'painless'."),
 ("clinical_wording_in_names", 10,
  "The patient describes things in colourful or sentence-like speech ('I've overdone it', 'I can't hear myself think', 'a frog in my throat', 'my feet feel dead', 'I feel like a wet rag').",
  "Every symptom name is a short clinical noun phrase of 1 to 5 words ('voice fatigue', 'numbness in both feet', 'tiredness'), never a full sentence, never starting with I/we/my. Pure idioms that are not symptoms ('I can't hear myself think' said about classroom noise) are NOT symptoms. The patient's own words stay in the cited turn, not in the name."),
 ("allergy_traps", 8,
  "The doctor asks about drug reactions. Variants (use ONE per encounter): (a) the patient says 'No, never, I have taken penicillin and everything' (no allergy); (b) the patient is unsure ('maybe the antibiotic or the painkiller, nobody told me which'); (c) a real allergy with the reaction described; (d) allergies are never asked.",
  "(a) NO allergy entry: negative_findings 'Allergies' absent. (b) allergy with status uncertain, the substance as described, the reaction if said, plus an allergy_uncertain uncertainty. (c) allergy with the reaction. (d) nothing at all. NEVER list a medicine the patient has taken without a reaction as an allergy, and the plan must not prescribe a drug of a recorded allergy's family."),
 ("vitals_and_prior_values", 8,
  "The nurse reads vital signs aloud in spoken words ('one oh nine over seventy-seven', 'thirty-eight point three') and also gives a PRIOR value ('last time in March you were sixty-eight', 'your last pressure was one-forty'). Someone may also correct a reading.",
  "vital_signs hold only the CURRENT measured values, written normally (109/77, 38.3, 52 kg). The prior value is NOT a vital sign; it is recorded in the weight/BP entry's own notes only if the schema allows, otherwise omitted. Every number must be exactly as said; never invent or round a value that was not said."),
 ("history_hidden_in_medicines", 6,
  "The patient lists medicines with their purpose ('amlodipine for the pressure', 'the cholesterol one at night', 'sugar tablets') and also mentions a herbal or shop remedy in passing ('only the Ayurvedic powder in the morning'). Their chronic conditions are never asked about directly.",
  "Each medicine is recorded with the dose and timing said for THAT medicine; the herbal remedy is a medicine too (currently_used). A condition the patient states through its medicine ('for the pressure') is a past_medical_history entry ONLY if the patient actually said the condition name or its everyday name ('the pressure' = hypertension, normalized); do not invent a duration."),
 ("family_and_social_in_one_turn", 6,
  "In ONE long answer the patient lists several relatives and their conditions ('my father had diabetes in his fifties, mother did not, another sister has pressure but no sugar'), and in another long answer their job, hours, diet, exercise and alcohol.",
  "Every relative with a stated condition is a separate family_history entry (relative, condition). Relatives said NOT to have a condition are not family_history entries. Occupation, hours, diet, exercise and alcohol/tobacco each become social_history entries as said (no inventions). Nothing from the doctor's questions is a fact."),
 ("caregiver_attribution", 6,
  "A caregiver or relative reports observations ('the cut healed in five days', 'she sleeps badly', 'he does not take the tablets on Sundays'); the patient agrees, disagrees or corrects one point. The nurse also reports a measurement that the patient mentioned before.",
  "reported_by follows who said it. A healing cut that healed normally is a negative finding (no slow-healing wounds) or nothing, NOT a symptom. A disputed fact is recorded with certainty disputed or as an uncertainty. A correction replaces the earlier value (Saturday, not Sunday)."),
 ("asr_noise_names", 4,
  "The transcript looks like speech-to-text: drug names are sometimes spelled wrongly ('Omprazole', 'Mizartan' for telmisartan, 'Metformine'), fragments and fillers appear ('Err', 'Of.', 'Mm.', 'Umm'), numbers are sometimes digits and sometimes words.",
  "Medicine names are recorded as written in the transcript (name) with a normalized/generic name ONLY when the true drug is certain from context (a drug 'for the pressure' written 'Mizartan' is NOT certain enough: leave generic_name empty). Fragments and fillers are never facts."),
]


def build_specs(n: int, first_id: int, seed: int = 20261126) -> list[dict]:
    rng = random.Random(seed)
    keys = [t[0] for t in TRAPS]
    weights = [t[1] for t in TRAPS]
    by_key = {t[0]: t for t in TRAPS}
    fam_cycle: list[tuple] = []
    while len(fam_cycle) < n:
        order = FAMILIES[:]
        rng.shuffle(order)
        fam_cycle += order
    specs = []
    for i in range(n):
        key, desc = fam_cycle[i]
        primary = rng.choices(keys, weights=weights)[0]
        chosen = [primary]
        if rng.random() < 0.6:                                              # a second trap in most encounters, as in real consultations
            second = rng.choices(keys, weights=weights)[0]
            if second != primary:
                chosen.append(second)
        extra = rng.choice(EXTRA_SPEAKERS)
        if "caregiver_attribution" in chosen and not extra:
            extra = ["CAREGIVER"]
        if "doctor_explanation_not_symptom" in chosen and "NURSE" not in extra:
            extra = (extra + ["NURSE"])[:3]
        if key in ("child_eczema_flare", "viral_conjunctivitis_child_school", "newborn_jaundice_feeding", "measles_contact_unvaccinated_child"):
            extra = ["FAMILY_MEMBER"] + [x for x in extra if x != "FAMILY_MEMBER"][:1]
        if "allergy_traps" in chosen:
            allergy_variant = rng.choice(["a", "b", "c", "d"])
        else:
            allergy_variant = None
        specs.append({"id": f"{first_id + i}", "family": key, "situation": desc, "difficulty": "hard", "traps": [{"key": k, "happens": by_key[k][2], "label_rule": by_key[k][3]} for k in chosen],
                      "allergy_variant": allergy_variant, "features": rng.sample(FEATURES, 2), "extra_speakers": extra, "patient_style": rng.choice(STYLES),
                      "doctor_style": rng.choice(DOCTOR_STYLES), "flavour": rng.choice(FLAVOURS), "target_turns": rng.randint(30, 54)})
    return specs
