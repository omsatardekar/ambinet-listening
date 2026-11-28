"""Batch 004 profiles, chunk 3 (24 scenarios: atypical presentations, medicine problems, mixed best/worst). Not clinically reviewed."""
from content_core import P

GMP = "General Medicine / Primary Care"; CAR = "Cardiology"; RES = "Respiratory Medicine"; GAS = "Gastroenterology"; END = "Endocrinology"; NEU = "Neurology"
MSK = "Musculoskeletal / Orthopaedics"; DER = "Dermatology"; GYN = "Gynaecology"; ENT = "ENT / Ophthalmology"; INF = "Infectious Diseases"; URG = "Urgent Care / Other"

P(GMP, "b4_worst_cancer_red_flags",
  [("losing weight without trying", "Unintentional weight loss", "constitutional", None, "", ""), ("a cough that won't go", "Persistent cough", "respiratory", "chest", "", ""), ("drenching night sweats", "Night sweats", "constitutional", None, "", ""), ("a lump in my neck", "Neck lump", "other", "neck", "", "")],
  [("fever", "Fever"), ("chest pain", "Chest pain"), ("bone pain", "Bone pain")], [], [],
  [("There is a firm, painless lump in the left side of your neck about three centimetres.", [("firm, painless lump in the left side of your neck", "Firm painless left cervical mass", "neck", "present")])],
  [("symptoms that need an urgent cancer work-up", ["a chronic infection", "a lymphoma"])], [("an urgent chest X-ray", "Chest X-ray", "imaging", "cough and weight loss"), ("blood tests", "Full blood count and inflammatory markers", "laboratory", "weight loss"), ("an ultrasound of the neck", "Neck ultrasound", "imaging", "neck lump")], [], [("I am referring you on an urgent pathway, which means an appointment within two weeks.", "Arrange urgent two-week-wait referral")],
  ["after the scans"], refs=[("the rapid diagnostic clinic", "Urgent referral to rapid diagnostic clinic")])
P(GMP, "b4_best_travel_vaccination",
  [("planning a trip", "Travel health advice", "constitutional", None, "", ""), ("a mild sore arm from last injection", "Mild arm soreness", "musculoskeletal", "arm", "", "")],
  [("fever", "Fever"), ("rash", "Rash"), ("recent illness", "Recent illness")], [], [],
  [("Your temperature is normal and you look well.", [("temperature is normal", "Normal temperature", "general", "present")])],
  [("fit to have travel vaccinations", [])], [], [("hepatitis A vaccine", "Hepatitis A vaccine", "1 dose", "intramuscular", "once", "single dose", "travel", None)], [("Drink bottled water and use insect repellent.", "Advise travel precautions")], ["in six months for the booster"])
P(CAR, "b4_worst_aortic_dissection",
  [("tearing chest pain going to my back", "Tearing chest pain", "cardiovascular", "chest", "", ""), ("sudden onset", "Sudden onset pain", "cardiovascular", None, "", ""), ("feeling faint", "Presyncope", "neurological", None, "", "lying down")],
  [("a cough", "Cough"), ("fever", "Fever"), ("leg swelling", "Leg swelling")], ["htn"], [],
  [("The blood pressure is different in your two arms and you are sweaty.", [("blood pressure is different in your two arms", "Inter-arm blood pressure difference", "arms", "present"), ("sweaty", "Diaphoresis", "general", "present")])],
  [("a possible tear in the main artery", ["a heart attack"])], [("an urgent CT scan of the chest and abdomen", "CT aortogram", "imaging", "tearing chest pain"), ("an ECG", "Electrocardiogram", "cardiac", "chest pain")], [], [("Do not move, I am calling an ambulance and you are going to a specialist centre.", "Arrange emergency ambulance")],
  ["straight away"], vit="htn", today=["an ECG"], refs=[("the cardiac surgical team", "Refer urgently to cardiothoracic team")])
P(CAR, "b4_mid_heart_failure_review",
  [("getting breathless lying flat", "Orthopnoea", "respiratory", None, "lying flat", "extra pillows"), ("swollen ankles", "Ankle swelling", "cardiovascular", "ankles", "evening", "feet up"), ("tiredness", "Fatigue", "constitutional", None, "", "")],
  [("chest pain", "Chest pain"), ("fainting", "Syncope"), ("palpitations", "Palpitations")], ["hf", "htn"], [],
  [("There is pitting swelling of both ankles and a few crackles at the lung bases.", [("pitting swelling of both ankles", "Bilateral pitting ankle oedema", "ankles", "present"), ("crackles at the lung bases", "Bibasal crackles", "chest", "present")])],
  [("heart failure with some fluid on board", ["a kidney problem"])], [("blood tests", "Urea, electrolytes and BNP", "laboratory", "heart failure"), ("an echocardiogram", "Echocardiogram", "imaging", "heart failure")],
  [("furosemide", "Furosemide", "40 mg", "oral", "once a day in the morning", "ongoing", "fluid retention", None)], [("Weigh yourself every morning and tell us if you gain two kilos in three days.", "Advise daily weights")], ["in two weeks"], vit="hypox", refs=[("the heart failure nurse", "Refer to heart failure nurse")])
P(RES, "b4_worst_severe_asthma_attack",
  [("I can't get my breath", "Severe dyspnoea", "respiratory", "chest", "", "sitting up"), ("a very tight chest", "Chest tightness", "respiratory", "chest", "", ""), ("not being able to finish a sentence", "Speaking in short phrases", "respiratory", None, "", ""), ("wheezing", "Wheeze", "respiratory", "chest", "", "")],
  [("fever", "Fever"), ("chest pain", "Chest pain"), ("a blue tinge", "Cyanosis")], ["asthma"], [("a blue reliever inhaler", "Salbutamol", "100 micrograms", "every few minutes")],
  [("You are using your neck muscles to breathe, and your oxygen is low.", [("using your neck muscles to breathe", "Accessory muscle use", "neck", "present"), ("oxygen is low", "Hypoxia", "general", "present")])],
  [("a severe asthma attack", ["a chest infection"])], [("a peak flow", "Peak expiratory flow", "other", "asthma attack"), ("a chest X-ray", "Chest X-ray", "imaging", "severe breathlessness")],
  [("prednisolone", "Prednisolone", "40 mg", "oral", "once now", "single dose", "asthma attack", None), ("salbutamol", "Salbutamol", "5 mg", "nebulised", "now", "single dose", "asthma attack", None)], [("Sit upright and take slow breaths while the nebuliser is set up.", "Advise sitting upright")], ["straight away"], vit="hypox", refs=[("the emergency team", "Refer to emergency team")])
P(RES, "b4_best_post_viral_cough",
  [("a lingering cough", "Post-viral cough", "respiratory", "chest", "talking;cold air", "honey"), ("a tickle in my throat", "Throat tickle", "ENT", "throat", "", "")],
  [("fever", "Fever"), ("coughing up blood", "Haemoptysis"), ("weight loss", "Weight loss"), ("shortness of breath", "Shortness of breath")], [], [("honey and lemon", "Honey", None, "at night")],
  [("Your chest is clear and your oxygen is normal.", [("chest is clear", "Clear chest", "chest", "present"), ("oxygen is normal", "Normal oxygen saturation", "general", "present")])],
  [("a post-viral cough that is settling", ["early asthma"])], [], [], [("It should settle over the next two to three weeks; steam and honey can help.", "Advise expectant management")], ["if it lasts beyond eight weeks"], red="you cough up blood")
P(GAS, "b4_worst_acute_appendicitis",
  [("pain that started around my belly button then moved to the right", "Migratory abdominal pain", "gastrointestinal", "right lower abdomen", "moving;coughing", "lying still"), ("feeling sick", "Nausea", "gastrointestinal", None, "", ""), ("no appetite", "Anorexia", "gastrointestinal", None, "", ""), ("a low fever", "Low-grade fever", "constitutional", None, "", "")],
  [("diarrhoea", "Diarrhoea"), ("urinary symptoms", "Urinary symptoms"), ("a cough", "Cough")], [], [],
  [("It hurts most low on the right and it hurts when I let go of the pressure.", [("hurts most low on the right", "Right iliac fossa tenderness", "abdomen", "present"), ("hurts when I let go of the pressure", "Rebound tenderness", "abdomen", "present")])],
  [("possible appendicitis", ["a urine infection", "gynaecological pain"])], [("urgent blood tests", "Full blood count and CRP", "laboratory", "abdominal pain"), ("an ultrasound or CT scan", "Abdominal imaging", "imaging", "possible appendicitis")], [], [("You need to go to hospital now and not eat or drink.", "Arrange urgent surgical assessment")],
  ["straight away"], vit="febrile", refs=[("the surgical team", "Refer urgently to surgical team")])
P(GAS, "b4_best_simple_constipation",
  [("hard stools", "Hard stools", "gastrointestinal", None, "low fibre", "water"), ("going less often", "Infrequent bowel opening", "gastrointestinal", None, "", ""), ("mild bloating", "Bloating", "gastrointestinal", "abdomen", "", "")],
  [("blood in the stool", "Blood in stool"), ("weight loss", "Weight loss"), ("vomiting", "Vomiting"), ("severe pain", "Severe abdominal pain")], [], [("a fibre supplement", "Ispaghula husk", "1 sachet", "daily")],
  [("Your tummy is soft with no tenderness.", [("soft with no tenderness", "Soft non-tender abdomen", "abdomen", "present")])],
  [("simple constipation from low fibre", [])], [], [("lactulose", "Lactulose", "15 ml", "oral", "twice a day", "two weeks", "constipation", None)], [("Eat more fruit, vegetables and oats, and drink two litres of water.", "Advise fibre and fluids")], ["if it persists after a month"])
P(END, "b4_mid_pcos_irregular_periods",
  [("irregular periods", "Irregular periods", "genitourinary", None, "", ""), ("acne", "Acne", "dermatological", "face", "", ""), ("extra hair on my chin", "Hirsutism", "dermatological", "chin", "", ""), ("putting on weight", "Weight gain", "constitutional", None, "", "")],
  [("headaches", "Headache"), ("a milky nipple discharge", "Galactorrhoea"), ("palpitations", "Palpitations")], [], [],
  [("Your weight is up a little, and there is acne on the jaw and some coarse hairs on the chin.", [("acne on the jaw", "Jawline acne", "face", "present"), ("coarse hairs on the chin", "Hirsutism", "chin", "present")])],
  [("polycystic ovary syndrome", ["a thyroid problem", "high prolactin"])], [("hormone blood tests", "Androgens, LH, FSH and prolactin", "laboratory", "irregular periods"), ("a pelvic ultrasound", "Pelvic ultrasound", "imaging", "irregular periods"), ("a thyroid test", "Thyroid function test", "laboratory", "irregular periods")], [("metformin", "Metformin", "500 mg", "oral", "twice a day with food", "ongoing", "polycystic ovaries", None)], [("Regular exercise and a lower-sugar diet help the periods settle.", "Advise lifestyle measures")], ["after the results"])
P(END, "b4_worst_adrenal_crisis_steroid_stop",
  [("feeling extremely weak", "Severe weakness", "constitutional", None, "", ""), ("vomiting", "Vomiting", "gastrointestinal", None, "", ""), ("dizzy when I stand", "Postural dizziness", "neurological", None, "standing", "lying down"), ("tummy pain", "Abdominal pain", "gastrointestinal", "abdomen", "", "")],
  [("fever", "Fever"), ("chest pain", "Chest pain")], [], [("my steroid tablets", "Prednisolone", "5 mg", "stopped last week")],
  [("Your blood pressure is very low and your skin is cool.", [("blood pressure is very low", "Hypotension", "arms", "present"), ("skin is cool", "Cool peripheries", "skin", "present")])],
  [("a possible adrenal crisis after stopping steroids", ["a severe infection"])], [("blood tests", "Sodium, potassium, glucose and cortisol", "laboratory", "adrenal crisis")], [("hydrocortisone", "Hydrocortisone", "100 mg", "intramuscular", "once now", "single dose", "adrenal crisis", None)], [("I am giving an injection now and calling an ambulance.", "Give hydrocortisone and arrange ambulance")], ["straight away"], vit="lowbp", refs=[("the emergency team", "Refer to emergency team")])
P(NEU, "b4_mid_vertigo_bppv",
  [("the room spinning when I turn over in bed", "Positional vertigo", "neurological", "head", "turning in bed;looking up", "lying still"), ("feeling sick", "Nausea", "gastrointestinal", None, "", ""), ("being unsteady for a few minutes", "Transient unsteadiness", "neurological", None, "", "")],
  [("hearing loss", "Hearing loss"), ("ringing in the ear", "Tinnitus"), ("weakness", "Weakness"), ("double vision", "Double vision")], [], [],
  [("When I tip you back, the eyes flick for about twenty seconds, and the hearing is normal.", [("eyes flick for about twenty seconds", "Positional nystagmus", "eyes", "present")])],
  [("benign positional vertigo", ["a vestibular neuritis"])], [], [], [("I'll do a repositioning manoeuvre now and show you exercises for home.", "Perform repositioning manoeuvre and teach exercises")], ["in two weeks"])
P(NEU, "b4_worst_status_seizure_arrival",
  [("a long seizure", "Prolonged seizure", "neurological", None, "", ""), ("being drowsy and confused afterwards", "Post-ictal confusion", "neurological", None, "", ""), ("biting my tongue", "Tongue biting", "neurological", "tongue", "", "")],
  [("a head injury", "Head injury"), ("fever", "Fever")], ["epilepsy"], [],
  [("You are drowsy and confused, and there is blood on your tongue.", [("drowsy and confused", "Altered consciousness", "general", "present"), ("blood on your tongue", "Tongue laceration", "tongue", "present")])],
  [("a prolonged seizure in a person with epilepsy", ["a missed dose of medicine"])], [("a blood sugar", "Capillary glucose", "other", "seizure"), ("blood tests including drug levels", "Electrolytes and anticonvulsant level", "laboratory", "seizure")], [("lorazepam", "Lorazepam", "4 mg", "intravenous", "once now", "single dose", "prolonged seizure", None)], [("Lie on your side while we monitor you.", "Advise recovery position")], ["straight away"], vit="tachy", today=["a blood sugar"], refs=[("the emergency team", "Refer to emergency team")])
P(MSK, "b4_worst_septic_arthritis",
  [("a hot swollen painful knee", "Hot swollen knee", "musculoskeletal", "knee", "any movement", ""), ("not being able to walk on it", "Unable to weight-bear", "musculoskeletal", "knee", "", ""), ("fever and chills", "Fever and chills", "constitutional", None, "", "")],
  [("a recent injury", "Recent injury"), ("other joint pain", "Other joint pain"), ("a rash", "Rash")], [], [],
  [("The knee is hot, swollen and extremely painful when I move it even slightly.", [("knee is hot, swollen", "Hot swollen knee", "knee", "present"), ("extremely painful when I move it", "Pain on passive movement", "knee", "present")])],
  [("possible septic arthritis", ["a gout attack"])], [("urgent blood tests", "Inflammatory markers and cultures", "laboratory", "septic arthritis"), ("a joint aspiration", "Knee aspiration", "other", "hot swollen knee")], [], [("You need to go to hospital now for a joint washout assessment.", "Arrange urgent orthopaedic assessment")], ["straight away"], vit="febrile", refs=[("the orthopaedic team", "Refer urgently to orthopaedics")])
P(MSK, "b4_best_tennis_elbow_simple",
  [("pain on the outside of my elbow", "Lateral elbow pain", "musculoskeletal", "elbow", "gripping;lifting the kettle", "rest"), ("a weaker grip", "Reduced grip strength", "musculoskeletal", "hand", "", "")],
  [("numbness", "Numbness"), ("neck pain", "Neck pain"), ("swelling", "Swelling")], [], [("ibuprofen gel", "Ibuprofen", None, "three times a day")],
  [("It's tender over the bony point on the outside, and it hurts when I resist your wrist going up.", [("tender over the bony point on the outside", "Lateral epicondyle tenderness", "elbow", "present")])],
  [("tennis elbow", [])], [], [], [("Rest it, use a forearm strap and do the stretches I'll show you.", "Advise rest, strap and stretches")], ["if it is not better in six weeks"])
P(DER, "b4_worst_stevens_johnson_like",
  [("a painful widespread rash", "Widespread painful rash", "dermatological", "body", "", ""), ("sores in my mouth", "Oral ulceration", "ENT", "mouth", "", ""), ("sore red eyes", "Conjunctivitis", "ophthalmological", "eyes", "", ""), ("a fever", "Fever", "constitutional", None, "", "")],
  [("a new medicine", "Recent new medicine"), ("an insect bite", "Insect bite")], [], [("a new antibiotic", "Co-trimoxazole", "960 mg", "twice a day for a week")],
  [("There are dusky red patches with blistering and the skin peels when I rub it lightly.", [("dusky red patches with blistering", "Dusky blistering rash", "body", "present"), ("skin peels when I rub it", "Nikolsky sign", "skin", "present")])],
  [("a severe drug reaction of the skin", ["a viral rash"])], [("blood tests", "Full blood count, liver and kidney function", "laboratory", "severe drug reaction"), ("an urgent dermatology review", "Urgent dermatology assessment", "other", "severe drug reaction")], [], [("Stop the antibiotic now and I am sending you to hospital immediately.", "Stop drug and arrange urgent admission")], ["straight away"], vit="febrile", refs=[("the dermatology team", "Refer urgently to dermatology")])
P(DER, "b4_best_viral_rash_child",
  [("a pink spotty rash", "Pink maculopapular rash", "dermatological", "trunk", "", ""), ("a mild temperature", "Low-grade fever", "constitutional", None, "", ""), ("a runny nose", "Rhinorrhoea", "ENT", "nose", "", "")],
  [("a stiff neck", "Neck stiffness"), ("breathlessness", "Breathlessness"), ("a rash that does not fade", "Non-blanching rash"), ("drowsiness", "Drowsiness")], [], [("paracetamol syrup", "Paracetamol", "5 ml", "when needed")],
  [("The spots fade when pressed and he is playful and drinking well.", [("spots fade when pressed", "Blanching rash", "trunk", "present"), ("playful and drinking well", "Well-appearing child", "general", "present")])],
  [("a harmless viral rash", ["an allergic rash"])], [], [], [("Fluids and paracetamol if he is hot or uncomfortable.", "Advise fluids and paracetamol")], ["if it lasts more than a week"], red="the spots do not fade when pressed or he becomes drowsy")
P(GYN, "b4_worst_pelvic_inflammatory_sepsis",
  [("pelvic pain", "Pelvic pain", "genitourinary", "pelvis", "moving", ""), ("a smelly discharge", "Offensive vaginal discharge", "genitourinary", None, "", ""), ("a high fever", "Fever", "constitutional", None, "", ""), ("pain with sex", "Dyspareunia", "genitourinary", None, "", "")],
  [("a recent pregnancy", "Recent pregnancy"), ("vomiting", "Vomiting")], [], [],
  [("You are very tender low in the tummy, and it hurts when I move the cervix.", [("very tender low in the tummy", "Lower abdominal tenderness", "abdomen", "present"), ("hurts when I move the cervix", "Cervical excitation", "pelvis", "present")])],
  [("severe pelvic inflammatory disease", ["an abscess"])], [("swabs", "High vaginal and endocervical swabs", "laboratory", "pelvic infection"), ("blood tests", "Inflammatory markers", "laboratory", "fever"), ("a pelvic scan", "Pelvic ultrasound", "imaging", "pelvic pain")], [("ceftriaxone", "Ceftriaxone", "1 gram", "intramuscular", "once now", "single dose", "pelvic infection", "penicillin")], [("You need hospital treatment today.", "Arrange urgent hospital assessment")], ["straight away"], vit="febrile", refs=[("the gynaecology team", "Refer urgently to gynaecology")])
P(GYN, "b4_best_early_pregnancy_normal",
  [("a missed period", "Missed period", "genitourinary", None, "", ""), ("feeling sick in the mornings", "Morning nausea", "gastrointestinal", None, "", "dry biscuits"), ("tender breasts", "Breast tenderness", "genitourinary", "breasts", "", "")],
  [("bleeding", "Vaginal bleeding"), ("severe pain", "Severe pelvic pain"), ("vomiting everything", "Severe vomiting")], [], [("a folic acid tablet", "Folic acid", "400 micrograms", "once a day")],
  [("Your blood pressure is normal.", [("blood pressure is normal", "Normal blood pressure", "arms", "present")])],
  [("a normal early pregnancy", [])], [("a pregnancy test", "Urine pregnancy test", "laboratory", "missed period"), ("a booking blood test", "Antenatal booking bloods", "laboratory", "pregnancy")], [], [("Keep taking folic acid and book in with the midwife.", "Advise folic acid and midwife booking")], ["in four weeks"], today=["a pregnancy test"], refs=[("the midwife", "Refer to community midwife")])
P(ENT, "b4_worst_sudden_hearing_loss",
  [("sudden hearing loss in one ear", "Sudden sensorineural hearing loss", "ENT", "ear", "", ""), ("ringing", "Tinnitus", "ENT", "ear", "", ""), ("a blocked feeling", "Aural fullness", "ENT", "ear", "", "")],
  [("ear pain", "Ear pain"), ("dizziness", "Dizziness"), ("discharge", "Ear discharge"), ("facial weakness", "Facial weakness")], [], [],
  [("The ear drum looks normal and the tuning fork is heard louder in the other ear.", [("ear drum looks normal", "Normal tympanic membrane", "ear", "present"), ("tuning fork is heard louder in the other ear", "Abnormal Weber test", "ear", "present")])],
  [("sudden hearing loss needing urgent treatment", ["a wax or fluid blockage"])], [("an urgent hearing test", "Pure tone audiometry", "other", "sudden hearing loss"), ("an MRI scan", "MRI internal auditory meatus", "imaging", "sudden hearing loss")], [("prednisolone", "Prednisolone", "60 mg", "oral", "once a day", "seven days", "sudden hearing loss", None)], [("This is time-critical, so I'm starting treatment today.", "Start urgent steroid treatment")], ["in one week"], refs=[("the ENT team", "Refer urgently to ENT")])
P(ENT, "b4_mid_dry_eye_screens",
  [("dry gritty eyes", "Dry eyes", "ophthalmological", "eyes", "screens;air conditioning", "eye drops"), ("tired eyes by evening", "Eye fatigue", "ophthalmological", "eyes", "", ""), ("occasional blurring that clears on blinking", "Transient blurring", "ophthalmological", "eyes", "", "blinking")],
  [("pain", "Eye pain"), ("redness", "Red eye"), ("light sensitivity", "Photophobia"), ("loss of vision", "Visual loss")], [], [("lubricating drops", "Carbomer", None, "four times a day")],
  [("Your eyelids look slightly crusted but the white of the eye is clear.", [("white of the eye is clear", "Clear conjunctiva", "eyes", "present")])],
  [("dry eye disease", ["blepharitis"])], [("an eye test", "Optometry eye examination", "other", "eye strain")], [], [("Take screen breaks every twenty minutes and use warm compresses on the lids.", "Advise screen breaks and lid hygiene")], ["in six weeks"])
P(INF, "b4_worst_malaria_returned",
  [("high fevers every other day", "Cyclical fever", "constitutional", None, "", ""), ("shaking chills", "Rigors", "constitutional", None, "", ""), ("a severe headache", "Severe headache", "neurological", "head", "", ""), ("feeling confused", "Confusion", "neurological", None, "", "")],
  [("a cough", "Cough"), ("a rash", "Rash"), ("diarrhoea", "Diarrhoea")], [], [],
  [("You are hot and jaundiced, and your spleen is tender.", [("hot and jaundiced", "Fever and jaundice", "general", "present"), ("spleen is tender", "Splenic tenderness", "abdomen", "present")])],
  [("possible malaria after travel", ["dengue", "typhoid"])], [("urgent blood films", "Malaria blood film", "laboratory", "fever after travel"), ("blood tests", "Full blood count and liver function", "laboratory", "fever after travel")], [], [("You need hospital assessment today, this can become serious fast.", "Arrange urgent hospital assessment")], ["straight away"], vit="febrile", refs=[("the infectious diseases team", "Refer urgently to infectious diseases")])
P(INF, "b4_best_mild_covid_like",
  [("a sore throat", "Sore throat", "ENT", "throat", "swallowing", "warm drinks"), ("a mild cough", "Cough", "respiratory", "chest", "", ""), ("feeling tired", "Fatigue", "constitutional", None, "", "rest"), ("a headache", "Headache", "neurological", "head", "", "paracetamol")],
  [("breathlessness", "Breathlessness"), ("chest pain", "Chest pain"), ("confusion", "Confusion")], [], [("paracetamol", "Paracetamol", "1 gram", "when needed")],
  [("Your oxygen is normal and your chest is clear.", [("oxygen is normal", "Normal oxygen saturation", "general", "present"), ("chest is clear", "Clear chest", "chest", "present")])],
  [("a mild viral respiratory infection", [])], [("a COVID test", "COVID-19 antigen test", "laboratory", "respiratory symptoms")], [], [("Rest, fluids, and stay home until you feel well and the fever has settled.", "Advise rest and isolation")], ["if not improving in a week"], today=["a COVID test"], red="you become breathless")
P(URG, "b4_worst_overdose_paracetamol",
  [("taking a lot of tablets", "Paracetamol overdose", "other", None, "", ""), ("feeling sick", "Nausea", "gastrointestinal", None, "", ""), ("tummy pain", "Abdominal pain", "gastrointestinal", "upper abdomen", "", ""), ("feeling very low", "Low mood", "psychiatric", None, "", "")],
  [("chest pain", "Chest pain"), ("drowsiness", "Drowsiness")], ["depression"], [],
  [("You are awake and alert, with some tenderness under the right ribs.", [("awake and alert", "Alert", "general", "present"), ("tenderness under the right ribs", "Right upper quadrant tenderness", "abdomen", "present")])],
  [("a significant paracetamol overdose needing urgent treatment", ["a mixed overdose"])], [("a paracetamol level", "Serum paracetamol level", "laboratory", "overdose"), ("liver function tests", "Liver function tests", "laboratory", "overdose")], [("acetylcysteine", "Acetylcysteine", "per protocol", "intravenous", "over 21 hours", "per protocol", "paracetamol overdose", None)], [("You need to stay in hospital for treatment, and someone will speak to you about how you are feeling.", "Arrange admission and psychiatric assessment")], ["straight away"], refs=[("the emergency team", "Refer to emergency team")])
P(URG, "b4_best_insect_bite_reaction",
  [("a red itchy lump on my arm", "Insect bite reaction", "dermatological", "arm", "", "ice"), ("mild swelling", "Local swelling", "dermatological", "arm", "", "")],
  [("breathing trouble", "Breathing difficulty"), ("lip swelling", "Lip swelling"), ("dizziness", "Dizziness"), ("fever", "Fever")], [], [("an antihistamine", "Cetirizine", "10 mg", "once a day")],
  [("There is a small red lump with a central punctum and a little swelling around it, and no spreading redness.", [("small red lump with a central punctum", "Insect bite papule", "arm", "present")])],
  [("a local insect bite reaction", ["early cellulitis"])], [], [("hydrocortisone cream", "Hydrocortisone", "1%", "topical", "twice a day", "five days", "bite reaction", None)], [("Cool it with ice and avoid scratching.", "Advise ice and not scratching")], ["if the redness spreads"], red="the redness spreads or you feel unwell")
