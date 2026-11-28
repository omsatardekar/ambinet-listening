"""Batch 004 profiles, chunk 1 (25 scenarios, mixed best case / worst case). Same compact DSL as Batch 001/002 (content_core.P). Not clinically reviewed."""
from content_core import P

GMP = "General Medicine / Primary Care"; CAR = "Cardiology"; RES = "Respiratory Medicine"; GAS = "Gastroenterology"; END = "Endocrinology"; NEU = "Neurology"
MSK = "Musculoskeletal / Orthopaedics"; DER = "Dermatology"; GYN = "Gynaecology"; ENT = "ENT / Ophthalmology"; INF = "Infectious Diseases"; URG = "Urgent Care / Other"

# ---- GMP
P(GMP, "b4_best_viral_cold_reassurance",  # best case: self-limiting
  [("a runny nose", "Rhinorrhoea", "ENT", "nose", "", "tissues"), ("a scratchy throat", "Sore throat", "ENT", "throat", "swallowing", "warm drinks"), ("a mild cough", "Cough", "respiratory", "chest", "", "honey and lemon"), ("sneezing", "Sneezing", "ENT", None, "", "")],
  [("fever", "Fever"), ("shortness of breath", "Shortness of breath"), ("chest pain", "Chest pain"), ("ear pain", "Ear pain")],
  [], [("throat lozenges", "Benzocaine", None, "when needed")],
  [("Your throat is a little red and your chest is clear.", [("throat is a little red", "Mild pharyngeal erythema", "throat", "present"), ("chest is clear", "Clear chest", "chest", "present")])],
  [("a simple viral cold", ["early flu"])], [], [], [("Rest, plenty of fluids, and paracetamol if you ache.", "Advise rest, fluids and simple analgesia")],
  ["if it is not better in ten days"], red="you develop a high fever or trouble breathing")
P(GMP, "b4_worst_sepsis_red_flags",  # worst case
  [("shaking chills and a high temperature", "Fever with rigors", "constitutional", None, "", "blankets"), ("feeling confused", "Confusion", "neurological", None, "", ""), ("a racing heart", "Palpitations", "cardiovascular", "chest", "", ""), ("very little urine", "Reduced urine output", "genitourinary", None, "", "")],
  [("a stiff neck", "Neck stiffness"), ("a rash", "Rash"), ("chest pain", "Chest pain")], [], [],
  [("You are hot, your heart is racing and your blood pressure is low, which worries me.", [("heart is racing", "Tachycardia", "chest", "present"), ("blood pressure is low", "Hypotension", "arms", "present")])],
  [("possible sepsis needing urgent treatment", ["a severe urine or chest infection"])],
  [("blood cultures", "Blood cultures", "laboratory", "fever with low blood pressure"), ("lactate and blood tests", "Lactate and inflammatory markers", "laboratory", "sepsis"), ("a chest X-ray", "Chest X-ray", "imaging", "fever")], [], [("I want to admit you to hospital now for fluids and antibiotics.", "Arrange urgent hospital admission")],
  ["straight away"], vit="febrile", refs=[("the emergency team", "Refer to emergency team")], red="you cannot be brought in today")
P(GMP, "b4_best_healthy_checkup",
  [("no real problems", "No complaints", "constitutional", None, "", ""), ("an occasional headache", "Occasional headache", "neurological", "head", "", "water"), ("a bit of back stiffness", "Mild back stiffness", "musculoskeletal", "back", "sitting long", "stretching")],
  [("chest pain", "Chest pain"), ("weight loss", "Weight loss"), ("shortness of breath", "Shortness of breath")], ["lipid"], [],
  [("Your heart and lungs sound normal.", [("heart and lungs sound normal", "Normal heart and lung sounds", "chest", "present")])],
  [("a healthy adult with no worrying findings", [])], [("a cholesterol blood test", "Lipid profile", "laboratory", "routine check"), ("a fasting sugar test", "Fasting glucose", "laboratory", "routine check")], [], [("Keep up regular exercise and a balanced diet.", "Advise exercise and diet")],
  ["in twelve months"], red="new symptoms appear")
# ---- CAR
P(CAR, "b4_worst_stemi_chest_pain",
  [("crushing chest pain", "Crushing chest pain", "cardiovascular", "chest", "exertion", "rest"), ("pain going into my left arm", "Left arm pain", "cardiovascular", "left arm", "", ""), ("sweating", "Diaphoresis", "constitutional", None, "", ""), ("feeling sick", "Nausea", "gastrointestinal", None, "", "")],
  [("a cough", "Cough"), ("leg swelling", "Leg swelling"), ("fever", "Fever")], ["htn", "lipid"], [],
  [("You are pale and sweaty, and your pulse is fast.", [("pale and sweaty", "Pallor and sweating", "general", "present"), ("pulse is fast", "Tachycardia", "wrist", "present")])],
  [("a possible heart attack", ["unstable angina"])], [("an ECG", "Electrocardiogram", "cardiac", "chest pain"), ("a troponin blood test", "Troponin", "laboratory", "chest pain")],
  [("aspirin", "Aspirin", "300 mg", "oral", "once now", "single dose", "possible heart attack", "aspirin")], [("Stay lying down and do not eat or drink.", "Advise rest and nil by mouth")],
  ["straight away"], vit="tachy", today=["an ECG"], refs=[("the cardiac team", "Refer urgently to cardiac team")], red="the pain returns")
P(CAR, "b4_best_benign_ectopics",
  [("skipped beats", "Palpitations", "cardiovascular", "chest", "caffeine;lying down", "deep breaths"), ("a flutter in my chest", "Chest flutter", "cardiovascular", "chest", "", ""), ("being a bit anxious", "Anxiety", "psychiatric", None, "", "")],
  [("fainting", "Syncope"), ("chest pain", "Chest pain"), ("shortness of breath", "Shortness of breath"), ("dizziness", "Dizziness")], [], [("herbal calming tea", "Chamomile", None, "in the evening")],
  [("Your pulse is regular and your heart sounds are normal.", [("pulse is regular", "Regular pulse", "wrist", "present"), ("heart sounds are normal", "Normal heart sounds", "chest", "present")])],
  [("harmless extra heartbeats", ["an anxiety-related palpitation"])], [("an ECG", "Electrocardiogram", "cardiac", "palpitations")], [], [("Cut back on coffee and energy drinks and keep a diary of when it happens.", "Advise caffeine reduction and symptom diary")],
  ["if it carries on after a month"], today=["an ECG"], red="you faint or have chest pain")
# ---- RES
P(RES, "b4_worst_pulmonary_embolus",
  [("sudden shortness of breath", "Sudden dyspnoea", "respiratory", "chest", "breathing in", "sitting up"), ("sharp pain when I breathe in", "Pleuritic chest pain", "respiratory", "chest", "deep breaths", ""), ("a swollen painful calf", "Calf swelling", "cardiovascular", "calf", "walking", ""), ("coughing up a little blood", "Haemoptysis", "respiratory", None, "", "")],
  [("fever", "Fever"), ("a wheeze", "Wheeze"), ("chest tightness", "Chest tightness")], [], [],
  [("Your left calf is swollen and tender, and your oxygen is lower than I'd like.", [("left calf is swollen", "Left calf swelling", "left calf", "present"), ("oxygen is lower than I'd like", "Low oxygen saturation", "general", "present")])],
  [("a possible blood clot in the lung", ["a chest infection"])], [("a CT scan of the chest", "CT pulmonary angiogram", "imaging", "breathlessness"), ("a D-dimer blood test", "D-dimer", "laboratory", "possible clot")], [],
  [("You need to go to hospital now for a scan.", "Arrange urgent hospital assessment")], ["straight away"], vit="hypox", refs=[("the medical team", "Refer urgently to medical team")], red="you feel faint")
P(RES, "b4_best_mild_hayfever_cough",
  [("a dry cough in the evenings", "Dry cough", "respiratory", "throat", "pollen season", "antihistamine"), ("itchy eyes", "Itchy eyes", "ophthalmological", "eyes", "outdoors", ""), ("sneezing fits", "Sneezing", "ENT", None, "", "")],
  [("wheeze", "Wheeze"), ("fever", "Fever"), ("shortness of breath", "Shortness of breath")], [], [("loratadine", "Loratadine", "10 mg", "once a day")],
  [("Your chest is clear and your nose looks a little swollen inside.", [("chest is clear", "Clear chest", "chest", "present"), ("nose looks a little swollen", "Swollen nasal mucosa", "nose", "present")])],
  [("seasonal hay fever causing the cough", ["early asthma"])], [], [("fluticasone nasal spray", "Fluticasone", "50 micrograms", "nasal", "once a day", "for the season", "hay fever", None)], [("Keep windows closed on high-pollen days and wash your hair at night.", "Advise pollen avoidance")],
  ["in a month"], red="you start wheezing")
# ---- GAS
P(GAS, "b4_worst_upper_gi_bleed",
  [("vomiting blood", "Haematemesis", "gastrointestinal", None, "", ""), ("black tarry stools", "Melaena", "gastrointestinal", None, "", ""), ("feeling faint", "Presyncope", "neurological", None, "standing", "lying down"), ("stomach pain", "Epigastric pain", "gastrointestinal", "upper abdomen", "", "")],
  [("chest pain", "Chest pain"), ("fever", "Fever")], [], [("ibuprofen", "Ibuprofen", "400 mg", "three times a day")],
  [("You look pale, your pulse is fast and your tummy is tender at the top.", [("look pale", "Pallor", "general", "present"), ("tender at the top", "Epigastric tenderness", "abdomen", "present")])],
  [("a possible bleeding stomach ulcer", ["a bleed from the gullet"])], [("urgent blood tests", "Haemoglobin and cross-match", "laboratory", "bleeding"), ("an endoscopy", "Upper GI endoscopy", "other", "bleeding")], [], [("Please stop the ibuprofen and do not eat or drink.", "Advise stopping NSAIDs and nil by mouth")],
  ["straight away"], vit="tachy", refs=[("the emergency team", "Refer to emergency team")], red="you vomit again")
P(GAS, "b4_best_functional_bloating",
  [("bloating after meals", "Post-prandial bloating", "gastrointestinal", "abdomen", "large meals;fizzy drinks", "walking"), ("a lot of wind", "Flatulence", "gastrointestinal", None, "", ""), ("loose stools now and then", "Intermittent loose stools", "gastrointestinal", None, "stress", "")],
  [("blood in the stool", "Blood in stool"), ("weight loss", "Weight loss"), ("night-time diarrhoea", "Nocturnal diarrhoea"), ("vomiting", "Vomiting")], ["anxiety"], [("peppermint capsules", "Peppermint oil", None, "after meals")],
  [("Your tummy is soft and not tender, and I can't feel any lumps.", [("soft and not tender", "Soft non-tender abdomen", "abdomen", "present"), ("can't feel any lumps", "No abdominal mass", "abdomen", "absent")])],
  [("a functional bowel pattern, with no alarm features", ["irritable bowel syndrome"])], [("a coeliac blood test", "Coeliac serology", "laboratory", "bloating")], [], [("Try smaller meals and keep a food and symptom diary for four weeks.", "Advise food and symptom diary")],
  ["in six weeks"], red="you see blood in the stool or lose weight")
# ---- END
P(END, "b4_worst_dka_presentation",
  [("being very thirsty", "Polydipsia", "endocrine", None, "", "water"), ("passing a lot of urine", "Polyuria", "genitourinary", None, "", ""), ("vomiting", "Vomiting", "gastrointestinal", None, "", ""), ("deep fast breathing", "Kussmaul breathing", "respiratory", None, "", ""), ("tummy pain", "Abdominal pain", "gastrointestinal", "abdomen", "", "")],
  [("chest pain", "Chest pain"), ("a cough", "Cough")], ["dm"], [],
  [("You are dry, breathing deeply and your breath smells fruity.", [("breathing deeply", "Deep rapid breathing", "chest", "present"), ("breath smells fruity", "Ketotic breath", "mouth", "present")])],
  [("diabetic ketoacidosis", ["a severe infection"])], [("a blood sugar and ketone test", "Capillary glucose and ketones", "other", "thirst and vomiting"), ("blood gas and electrolytes", "Venous blood gas and electrolytes", "laboratory", "DKA")], [], [("You need to go to hospital now for insulin and fluids.", "Arrange urgent hospital admission")],
  ["straight away"], vit="tachy", today=["a blood sugar and ketone test"], refs=[("the emergency team", "Refer to emergency team")], red="you cannot get there now")
P(END, "b4_best_stable_thyroid_review",
  [("feeling well", "No complaints", "constitutional", None, "", ""), ("slightly dry skin", "Dry skin", "dermatological", "skin", "", "moisturiser")],
  [("weight change", "Weight change"), ("palpitations", "Palpitations"), ("feeling cold", "Cold intolerance"), ("constipation", "Constipation")], ["hypothyroid"], [],
  [("Your pulse is steady and your thyroid feels normal in size.", [("pulse is steady", "Regular pulse", "wrist", "present"), ("thyroid feels normal in size", "Normal thyroid size", "neck", "present")])],
  [("well-controlled thyroid replacement", [])], [("a thyroid blood test", "Thyroid function test", "laboratory", "annual review")], [], [("Keep taking the tablet on an empty stomach, apart from coffee.", "Advise thyroxine timing")],
  ["in twelve months"], red="you notice palpitations or weight change")
# ---- NEU
P(NEU, "b4_worst_stroke_fast",
  [("my face drooping on one side", "Facial droop", "neurological", "face", "", ""), ("weakness in my right arm", "Right arm weakness", "neurological", "right arm", "", ""), ("slurred speech", "Dysarthria", "neurological", None, "", ""), ("a sudden headache", "Sudden headache", "neurological", "head", "", "")],
  [("a seizure", "Seizure"), ("loss of consciousness", "Loss of consciousness"), ("fever", "Fever")], ["htn", "af"], [],
  [("Your right face droops, your right arm is weak and your speech is slurred.", [("right face droops", "Right facial droop", "face", "present"), ("right arm is weak", "Right arm weakness", "right arm", "present"), ("speech is slurred", "Slurred speech", "mouth", "present")])],
  [("a possible stroke, within the treatment window", ["a migraine with aura"])], [("an urgent CT scan of the head", "CT head", "imaging", "possible stroke"), ("a blood sugar test", "Capillary glucose", "other", "stroke symptoms")], [], [("Call an ambulance now, you need hospital immediately.", "Arrange urgent ambulance transfer")],
  ["straight away"], vit="htn", today=["a blood sugar test"], refs=[("the stroke team", "Refer urgently to stroke team")], red="the symptoms change")
P(NEU, "b4_best_tension_headache",
  [("a tight band around my head", "Tension-type headache", "neurological", "head", "long screen days;stress", "a walk;a warm shower"), ("a stiff neck", "Neck stiffness", "musculoskeletal", "neck", "", "stretching"), ("tired eyes", "Eye strain", "ophthalmological", "eyes", "screens", "breaks")],
  [("sickness", "Nausea"), ("sensitivity to light", "Photophobia"), ("weakness", "Weakness"), ("blurred vision", "Blurred vision")], [], [("paracetamol", "Paracetamol", "1 gram", "when needed")],
  [("Your neck and shoulder muscles are tight, and your eye movements are normal.", [("neck and shoulder muscles are tight", "Tight neck and shoulder muscles", "neck", "present"), ("eye movements are normal", "Normal eye movements", "eyes", "present")])],
  [("tension-type headache", ["eye strain"])], [("an eye test", "Optometry eye examination", "other", "eye strain")], [], [("Take screen breaks every hour and try regular neck stretches.", "Advise screen breaks and neck stretches")],
  ["in four weeks"], red="the headache becomes sudden and severe")
# ---- MSK
P(MSK, "b4_worst_cauda_equina",
  [("severe lower back pain", "Severe low back pain", "musculoskeletal", "lower back", "bending", ""), ("numbness between my legs", "Saddle numbness", "neurological", "groin", "", ""), ("trouble passing urine", "Urinary retention", "genitourinary", None, "", ""), ("weakness in both legs", "Bilateral leg weakness", "neurological", "legs", "", "")],
  [("fever", "Fever"), ("a recent fall", "Recent fall")], [], [],
  [("You have numbness in the saddle area and your leg strength is reduced.", [("numbness in the saddle area", "Saddle anaesthesia", "perineum", "present"), ("leg strength is reduced", "Reduced leg strength", "legs", "present")])],
  [("possible cauda equina syndrome needing an urgent scan", ["a large disc prolapse"])], [("an urgent MRI of the spine", "MRI lumbar spine", "imaging", "possible cauda equina")], [], [("You need to go to hospital now for an emergency scan.", "Arrange urgent hospital assessment")],
  ["straight away"], refs=[("the spinal team", "Refer urgently to spinal team")], red="the numbness spreads")
P(MSK, "b4_best_simple_ankle_strain",
  [("a sore ankle", "Ankle pain", "musculoskeletal", "ankle", "walking", "rest;ice"), ("a little swelling", "Ankle swelling", "musculoskeletal", "ankle", "", "elevation")],
  [("numbness", "Numbness"), ("a crack or pop", "Audible pop"), ("pain in the foot", "Foot pain")], [], [("ibuprofen gel", "Ibuprofen", None, "three times a day")],
  [("There's mild swelling over the outside of the ankle, and you can put your weight on it.", [("mild swelling over the outside of the ankle", "Mild lateral ankle swelling", "ankle", "present"), ("put your weight on it", "Weight-bearing intact", "ankle", "present")])],
  [("a mild ankle sprain", ["a minor fracture"])], [], [], [("Rest, ice, a compression bandage and keep it raised for two days.", "Advise rest, ice, compression and elevation")],
  ["if it is not better in two weeks"], red="you cannot put weight on it")
# ---- DER
P(DER, "b4_worst_necrotising_infection",
  [("a red hot swelling on my leg", "Cellulitis", "dermatological", "leg", "", ""), ("pain much worse than it looks", "Severe skin pain", "dermatological", "leg", "touch", ""), ("a high fever", "Fever", "constitutional", None, "", ""), ("dark blisters", "Skin blistering", "dermatological", "leg", "", "")],
  [("an insect bite", "Insect bite"), ("a cut", "Recent injury")], ["dm"], [],
  [("The skin on your leg is dusky with blisters and is very tender, and you are feverish.", [("skin on your leg is dusky", "Dusky skin", "leg", "present"), ("very tender", "Marked tenderness", "leg", "present")])],
  [("a severe deep skin infection needing urgent surgery review", ["severe cellulitis"])], [("urgent blood tests", "Inflammatory markers and lactate", "laboratory", "severe skin infection"), ("an urgent surgical review", "Urgent surgical assessment", "other", "possible necrotising infection")], [], [("I am sending you to hospital now, do not wait.", "Arrange urgent hospital admission")],
  ["straight away"], vit="febrile", refs=[("the surgical team", "Refer urgently to surgical team")], red="you cannot go now")
P(DER, "b4_best_mild_contact_dermatitis",
  [("an itchy patch on my wrist", "Itchy rash", "dermatological", "wrist", "my new watch strap", "moisturiser"), ("dry flaky skin", "Dry flaky skin", "dermatological", "wrist", "", ""), ("a bit of redness", "Redness", "dermatological", "wrist", "", "")],
  [("blisters", "Blisters"), ("fever", "Fever"), ("spreading", "Spreading rash")], [], [("a plain moisturiser", "Emollient", None, "twice a day")],
  [("There's a neat red patch where the watch strap sits, with a little scaling.", [("neat red patch where the watch strap sits", "Well-demarcated erythema at strap site", "wrist", "present")])],
  [("mild contact dermatitis from the watch strap", ["eczema"])], [], [("hydrocortisone cream", "Hydrocortisone", "1%", "topical", "once a day", "one week", "contact dermatitis", None)], [("Stop wearing that strap and keep the skin moisturised.", "Advise avoiding trigger and emollient use")],
  ["if it has not cleared in two weeks"], red="it spreads or blisters")
# ---- GYN
P(GYN, "b4_worst_ectopic_pregnancy",
  [("sharp pain low on one side", "Unilateral pelvic pain", "genitourinary", "pelvis", "", ""), ("light vaginal bleeding", "Vaginal bleeding", "genitourinary", None, "", ""), ("shoulder tip pain", "Shoulder tip pain", "musculoskeletal", "shoulder", "", ""), ("feeling faint", "Presyncope", "neurological", None, "", "lying down")],
  [("fever", "Fever"), ("vaginal discharge", "Abnormal discharge")], [], [],
  [("Your tummy is tender low on the right and you look pale.", [("tender low on the right", "Right iliac fossa tenderness", "abdomen", "present"), ("look pale", "Pallor", "general", "present")])],
  [("a possible ectopic pregnancy", ["a ruptured ovarian cyst"])], [("a pregnancy test", "Urine pregnancy test", "laboratory", "pelvic pain and bleeding"), ("an urgent pelvic scan", "Transvaginal ultrasound", "imaging", "possible ectopic")], [], [("You need to go to the hospital now for an emergency scan.", "Arrange urgent gynaecology assessment")],
  ["straight away"], vit="tachy", today=["a pregnancy test"], refs=[("the gynaecology team", "Refer urgently to gynaecology")], red="the pain gets worse or you faint")
P(GYN, "b4_best_routine_contraception",
  [("wanting contraception", "Contraception request", "genitourinary", None, "", ""), ("slightly heavy periods", "Heavy periods", "genitourinary", None, "", "")],
  [("migraine with aura", "Migraine with aura"), ("blood clots", "History of blood clots"), ("smoking", "Smoking"), ("breast lumps", "Breast lumps")], [], [],
  [("Your blood pressure is normal.", [("blood pressure is normal", "Normal blood pressure", "arms", "present")])],
  [("suitable for hormonal contraception with no risk factors", [])], [], [("levonorgestrel and ethinylestradiol", "Levonorgestrel and ethinylestradiol", "150 micrograms and 30 micrograms", "oral", "once a day", "ongoing", "contraception", None)], [("Take the pill at the same time each day and use condoms if you miss two.", "Advise pill timing and missed-pill rule")],
  ["in three months"], red="you get leg swelling or severe headaches")
# ---- ENT
P(ENT, "b4_worst_epiglottitis_like",
  [("a severe sore throat", "Severe sore throat", "ENT", "throat", "swallowing", ""), ("difficulty swallowing", "Dysphagia", "ENT", "throat", "", ""), ("a muffled voice", "Muffled voice", "ENT", None, "", ""), ("drooling", "Drooling", "ENT", "mouth", "", ""), ("noisy breathing", "Stridor", "respiratory", "throat", "lying flat", "sitting forward")],
  [("a rash", "Rash"), ("a cough", "Cough")], [], [],
  [("You are sitting forward, drooling, and your breathing is noisy.", [("sitting forward", "Tripod posture", "general", "present"), ("breathing is noisy", "Stridor", "throat", "present")])],
  [("a possible airway infection that needs emergency care", ["severe tonsillitis"])], [("an urgent airway assessment", "Urgent ENT airway assessment", "other", "stridor and drooling")], [], [("Do not lie flat, I am calling an ambulance now.", "Arrange emergency ambulance")],
  ["straight away"], vit="hypox", refs=[("the emergency ENT team", "Refer urgently to ENT")], red="the breathing gets harder")
P(ENT, "b4_best_earwax",
  [("a blocked ear", "Ear blockage", "ENT", "ear", "showering", ""), ("muffled hearing on one side", "Reduced hearing", "ENT", "ear", "", ""), ("a feeling of fullness", "Ear fullness", "ENT", "ear", "", "")],
  [("ear pain", "Ear pain"), ("discharge", "Ear discharge"), ("dizziness", "Dizziness"), ("ringing", "Tinnitus")], [], [("olive oil drops", "Olive oil", None, "twice a day")],
  [("There's a lot of wax blocking the right ear canal.", [("lot of wax blocking the right ear canal", "Impacted cerumen", "right ear", "present")])],
  [("earwax blocking the ear", ["a middle ear fluid"])], [("ear irrigation", "Ear irrigation", "other", "wax")], [], [("Use the olive oil drops for a week and then we'll syringe the ear.", "Plan olive oil then irrigation")],
  ["in one week"], red="you get ear pain or dizziness")
# ---- INF
P(INF, "b4_worst_meningitis",
  [("a severe headache", "Severe headache", "neurological", "head", "light", ""), ("a stiff neck", "Neck stiffness", "musculoskeletal", "neck", "", ""), ("a high fever", "Fever", "constitutional", None, "", ""), ("a rash that does not fade", "Non-blanching rash", "dermatological", "body", "", ""), ("hating the light", "Photophobia", "neurological", "eyes", "", "")],
  [("a recent head injury", "Head injury"), ("a cough", "Cough")], [], [],
  [("Your neck is stiff, you are feverish, and there are purple spots that do not fade when pressed.", [("neck is stiff", "Neck stiffness", "neck", "present"), ("purple spots that do not fade", "Non-blanching purpuric rash", "skin", "present")])],
  [("possible bacterial meningitis", ["meningococcal septicaemia"])], [("blood cultures", "Blood cultures", "laboratory", "possible meningitis"), ("a lumbar puncture", "Lumbar puncture", "other", "possible meningitis")], [("benzylpenicillin", "Benzylpenicillin", "1.2 grams", "intramuscular", "once now", "single dose", "possible meningitis", "penicillin")], [("Call an ambulance now, this is an emergency.", "Arrange emergency ambulance")],
  ["straight away"], vit="febrile", refs=[("the emergency team", "Refer to emergency team")], red="you cannot go now")
P(INF, "b4_best_simple_uti",
  [("burning when I pass urine", "Dysuria", "genitourinary", None, "", "drinking water"), ("going to the toilet often", "Urinary frequency", "genitourinary", None, "", ""), ("a dull ache low in my tummy", "Suprapubic ache", "genitourinary", "lower abdomen", "", "a hot water bottle")],
  [("fever", "Fever"), ("back pain", "Back pain"), ("blood in the urine", "Haematuria"), ("vaginal discharge", "Vaginal discharge")], [], [("cranberry juice", "Cranberry", None, "daily")],
  [("Your tummy is soft with slight tenderness just above the pubic bone.", [("soft", "Soft abdomen", "abdomen", "present"), ("slight tenderness just above the pubic bone", "Mild suprapubic tenderness", "lower abdomen", "present")])],
  [("an uncomplicated urinary infection", ["vaginal irritation"])], [("a urine dipstick", "Urinalysis", "laboratory", "burning urine")], [("nitrofurantoin", "Nitrofurantoin", "100 mg", "oral", "twice a day", "three days", "urinary infection", None)], [("Drink plenty of water and avoid holding urine.", "Advise fluids and regular voiding")],
  ["if it is not better in three days"], today=["a urine dipstick"], red="you get a fever or back pain")
# ---- URG
P(URG, "b4_worst_anaphylaxis",
  [("my throat closing up", "Throat tightness", "respiratory", "throat", "", ""), ("hives all over", "Urticaria", "dermatological", "body", "", ""), ("wheezing", "Wheeze", "respiratory", "chest", "", ""), ("feeling faint", "Presyncope", "neurological", None, "", "lying down"), ("swollen lips", "Lip swelling", "ENT", "lips", "", "")],
  [("a recent illness", "Recent illness"), ("chest pain", "Chest pain")], ["asthma"], [],
  [("Your lips are swollen, you have hives, you are wheezing and your pressure is low.", [("lips are swollen", "Angioedema", "lips", "present"), ("wheezing", "Wheeze", "chest", "present"), ("pressure is low", "Hypotension", "arms", "present")])],
  [("anaphylaxis", ["a severe allergic reaction"])], [("monitoring", "Cardiac and oxygen monitoring", "other", "anaphylaxis")], [("adrenaline", "Adrenaline", "0.5 mg", "intramuscular", "once now", "single dose", "anaphylaxis", None)], [("Lie flat with your legs raised, I am giving the injection now.", "Advise lying flat and give adrenaline")],
  ["straight away"], vit="lowbp", refs=[("the emergency team", "Refer to emergency team")], red="the symptoms return")
P(URG, "b4_best_minor_cut",
  [("a cut on my finger", "Finger laceration", "dermatological", "finger", "", "pressure;a plaster"), ("a little bleeding", "Minor bleeding", "dermatological", "finger", "", "")],
  [("numbness", "Numbness"), ("loss of movement", "Loss of finger movement"), ("a dirty blade", "Contaminated wound")], [], [],
  [("It's a clean shallow cut, no longer bleeding, and the finger moves normally.", [("clean shallow cut", "Clean shallow laceration", "finger", "present"), ("finger moves normally", "Normal finger movement", "finger", "present")])],
  [("a minor clean wound that needs only dressing", [])], [], [], [("I'll close it with adhesive strips and keep it dry for two days.", "Close wound with strips and advise dry dressing")],
  ["if it looks red or swollen"], red="the finger turns red, hot or swollen")
