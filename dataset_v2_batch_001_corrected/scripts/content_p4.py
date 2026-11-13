"""Profiles part 4 (added in the corrected build to reduce scenario reuse; same DSL as content_core.P)."""
from content_core import P
from content_p1 import GM, NE, CA, RE
from content_p2 import GI, MS, DE, EN
from content_p3 import NU, EO, GY, MH

NEW_KEYS = []
_n0 = [0]


def _mark():
    from content_core import PROFILES
    for p in PROFILES[_n0[0]:]:
        NEW_KEYS.append(p["key"])
    _n0[0] = len(PROFILES)


from content_core import PROFILES as _PR
_n0[0] = len(_PR)

# ------------------------------------------------------------------ General medicine
P(GM, "chikungunya_like_arthralgia",
  [("fever and joint pains", "Fever with arthralgia", "constitutional", None, "", "paracetamol"),
   ("swollen painful wrists and ankles", "Wrist and ankle swelling", "musculoskeletal", "wrists", "morning;moving", "rest"),
   ("a blotchy rash on the trunk", "Rash", "dermatological", "trunk", "", ""),
   ("a headache", "Headache", "neurological", "head", "", "paracetamol"),
   ("feeling wiped out", "Fatigue", "constitutional", None, "", "")],
  [("bleeding", "Bleeding"), ("vomiting", "Vomiting"), ("red eyes", "Red eyes"), ("neck stiffness", "Neck stiffness"), ("cough", "Cough"), ("diarrhoea", "Diarrhoea")],
  ["htn"], [("Dolo", "Paracetamol", "650 mg", "when it flares")],
  [("Both wrists and several finger joints are puffy and tender.", [("wrists and several finger joints are puffy", "Wrist and finger joint swelling", "wrists", "present")]),
   ("A fine rash over the chest and back, not itchy to touch.", [("fine rash over the chest", "Truncal rash", "trunk", "present")])],
  [("a viral fever with joint involvement, possibly chikungunya", ["dengue fever", "an early inflammatory arthritis"])],
  [("a chikungunya test", "Chikungunya serology", "laboratory", "fever with joint pain"), ("a full blood count", "Complete blood count", "laboratory", "fever"), ("a dengue test", "Dengue NS1 antigen", "laboratory", "fever")],
  [("paracetamol", "Paracetamol", "650 mg", "oral", "three times a day", "for five days", "fever and joint pain", None)],
  [("Avoid anti-inflammatory painkillers until we know it isn't dengue.", "Avoid NSAIDs until dengue excluded")],
  ["after the results are back", "in four days"], vit="febrile")

P(GM, "neck_lump_lymphadenopathy",
  [("a lump on the side of my neck", "Neck lump", "constitutional", "neck", "", ""),
   ("a sore throat a while back", "Sore throat", "ENT", "throat", "", ""),
   ("feeling feverish in the evenings", "Evening fever", "constitutional", None, "", ""),
   ("itching all over", "Generalised itching", "dermatological", None, "", ""),
   ("night sweats", "Night sweats", "constitutional", None, "", "")],
  [("weight loss", "Weight loss"), ("pain in the lump", "Painful lump"), ("difficulty swallowing", "Dysphagia"), ("cough", "Cough"), ("lumps elsewhere", "Other lumps"), ("tooth problems", "Dental problems")],
  [], [],
  [("There's a firm, mobile lump about two centimetres under the left jaw, not tender.", [("firm, mobile lump", "Mobile non-tender cervical lymph node", "left neck", "present")]),
   ("I can't feel other glands in the neck, armpits or groin.", [("can't feel other glands", "No other lymphadenopathy", "neck", "absent")])],
  [("a reactive lymph node after a throat infection", ["a persistent infection", "something that needs a tissue diagnosis"])],
  [("blood tests", "Complete blood count and CRP", "laboratory", "neck lump"), ("an ultrasound of the neck", "Neck ultrasound", "imaging", "neck lump")],
  [],
  [("Check the lump once a week and let me know if it grows or becomes hard.", "Self-monitoring of lump")],
  ["after the scan", "in three weeks"])

P(GM, "covid_like_illness",
  [("a dry cough and fever", "Cough and fever", "respiratory", "chest", "", "paracetamol"),
   ("losing my sense of smell", "Anosmia", "ENT", "nose", "", ""),
   ("a sore throat", "Sore throat", "ENT", "throat", "", "warm drinks"),
   ("body aches", "Myalgia", "musculoskeletal", "generalised", "", "rest"),
   ("tiredness", "Fatigue", "constitutional", None, "", "")],
  [("shortness of breath", "Shortness of breath"), ("chest pain", "Chest pain"), ("vomiting", "Vomiting"), ("diarrhoea", "Diarrhoea"), ("confusion", "Confusion"), ("a rash", "Rash")],
  ["asthma", "htn"], [PCM := ("paracetamol", "Paracetamol", "500 mg", "when needed")],
  [("Chest is clear, no crackles or wheeze.", [("no crackles or wheeze", "No adventitious breath sounds", "chest", "absent")]),
   ("Throat is mildly red.", [("mildly red", "Mild pharyngeal erythema", "throat", "present")])],
  [("a viral respiratory illness, possibly COVID-19", ["influenza", "a common cold"])],
  [("a COVID test", "SARS-CoV-2 test", "laboratory", "viral respiratory illness"), ("a pulse oximeter reading", "Pulse oximetry", "other", "respiratory symptoms")],
  [("paracetamol", "Paracetamol", "500 mg", "oral", "every six hours if needed", "for three days", "fever and aches", None)],
  [("Stay home until you're fever-free and wear a mask around others for a few days.", "Isolation and masking advice")],
  ["if it's not better in five days", "in a week"], vit="febrile", today=["a pulse oximeter reading"], red="you become short of breath")

# ------------------------------------------------------------------ Neurology
P(NE, "headache_uncertain_onset",
  [("headaches for a while", "Headache", "neurological", "head", "coughing;bending down", "painkillers"),
   ("pressure behind the eyes", "Retro-orbital pressure", "neurological", "eyes", "", ""),
   ("occasional nausea", "Nausea", "gastrointestinal", None, "", ""),
   ("blurry vision at times", "Intermittent blurred vision", "ophthalmological", "eyes", "", ""),
   ("neck tightness", "Neck tightness", "musculoskeletal", "neck", "", "")],
  [("weakness", "Weakness"), ("fever", "Fever"), ("seizures", "Seizure"), ("confusion", "Confusion"), ("a head injury", "Head injury"), ("jaw pain on chewing", "Jaw claudication")],
  ["htn"], [("paracetamol", "Paracetamol", "500 mg", "when it hurts")],
  [("Visual fields are full to confrontation and the optic discs look normal.", [("optic discs look normal", "Normal optic discs", "eyes", "present")]),
   ("Power and reflexes are equal on both sides.", [("equal on both sides", "Symmetrical power and reflexes", "limbs", "present")])],
  [("a headache disorder of uncertain type", ["tension-type headache", "a secondary headache we should exclude"])],
  [("an MRI of the brain", "MRI brain", "imaging", "headaches with visual symptoms"), ("an eye pressure check", "Intraocular pressure measurement", "other", "headache with blurred vision")],
  [], [("Note down each headache with the date, time and what you were doing.", "Headache diary")],
  ["after the scan", "in four weeks"], refs=[("a neurologist", "Refer to neurology")], red="you get sudden worst-ever headache or weakness")

P(NE, "possible_seizure_history",
  [("a strange episode where I blanked out", "Episode of altered awareness", "neurological", None, "lack of sleep", ""),
   ("staring spells that others noticed", "Staring spells", "neurological", None, "", ""),
   ("a metallic taste before it", "Aura", "neurological", None, "", ""),
   ("feeling groggy afterwards", "Post-episode drowsiness", "neurological", None, "", "sleeping"),
   ("an odd smell before it", "Olfactory aura", "neurological", None, "", "")],
  [("tongue biting", "Tongue biting"), ("losing control of the bladder", "Urinary incontinence"), ("jerking movements", "Convulsive movements"), ("a head injury", "Head injury"), ("alcohol before it", "Alcohol use"), ("a fever", "Fever")],
  ["anxiety"], [],
  [("You're alert, speech is normal and cranial nerves are intact.", [("cranial nerves are intact", "Intact cranial nerves", "head", "present")]),
   ("Coordination is normal on finger-to-nose testing.", [("coordination is normal", "Normal coordination", "limbs", "present")])],
  [("a possible focal seizure that needs investigating", ["a faint", "a panic episode"])],
  [("an EEG", "Electroencephalogram", "other", "possible seizure"), ("an MRI of the brain", "MRI brain", "imaging", "possible seizure"), ("blood tests", "Complete blood count and electrolytes", "laboratory", "episode of altered awareness")],
  [], [("Don't drive until we've looked into this.", "No driving pending review")],
  ["after the results are back", "in four weeks"], refs=[("the neurology clinic", "Refer to neurology clinic")], red="you have another episode that lasts more than a few minutes")

P(NE, "bells_palsy",
  [("my face drooping on the right side", "Right facial droop", "neurological", "right face", "", ""),
   ("not being able to close my right eye fully", "Incomplete right eye closure", "neurological", "right eye", "", "eye drops"),
   ("pain behind the right ear", "Right retroauricular pain", "ENT", "right ear", "", ""),
   ("food tasting odd", "Altered taste", "neurological", "tongue", "", ""),
   ("a watery eye", "Epiphora", "ophthalmological", "right eye", "", "")],
  [("arm or leg weakness", "Limb weakness"), ("slurred speech", "Slurred speech"), ("a headache", "Headache"), ("a rash around the ear", "Ear rash"), ("hearing changes", "Hearing change"), ("a recent tick bite", "Tick bite")],
  ["dm", "htn"], [],
  [("You can't wrinkle the right forehead or puff out the right cheek.", [("can't wrinkle the right forehead", "Right forehead weakness", "right face", "present")]),
   ("Left side of the face moves normally, and arm and leg strength is normal.", [("arm and leg strength is normal", "Normal limb strength", "limbs", "present")])],
  [("a Bell's palsy pattern", ["a stroke", "a viral nerve infection"])],
  [("blood sugar testing", "Blood glucose", "laboratory", "facial palsy")],
  [("prednisolone", "Prednisolone", "50 mg", "oral", "once a day", "for seven days", "facial weakness", None)],
  [("Use lubricating drops through the day and tape the eye shut at night.", "Eye protection")],
  ["in a week", "in two weeks"], red="the weakness spreads to your arm or leg, or your speech changes")

# ------------------------------------------------------------------ Cardiology
P(CA, "ectopic_beats_no_pain",
  [("skipped beats", "Palpitations (skipped beats)", "cardiovascular", "chest", "coffee;lying on the left", "walking"),
   ("a thump in the chest at night", "Nocturnal palpitations", "cardiovascular", "chest", "lying on the left", ""),
   ("occasional lightheadedness", "Lightheadedness", "neurological", None, "", "sitting down"),
   ("feeling anxious about it", "Anxiety", "psychiatric", None, "", ""),
   ("poor sleep", "Insomnia", "neurological", None, "", "")],
  [("chest pain", "Chest pain"), ("fainting", "Syncope"), ("breathlessness", "Shortness of breath"), ("leg swelling", "Leg swelling"), ("a family history of sudden death", "Family history of sudden death"), ("energy drinks", "Energy drink use")],
  ["anxiety", "hypothyroid"], [],
  [("Pulse is regular at the moment, with a couple of early beats while I listened.", [("couple of early beats", "Occasional ectopic beats", "chest", "present")]),
   ("Heart sounds are normal with no murmur.", [("no murmur", "No cardiac murmur", "chest", "absent")])],
  [("benign extra heartbeats, though we should confirm", ["a rhythm problem", "a thyroid cause"])],
  [("an ECG", "Electrocardiogram", "cardiac", "palpitations"), ("a Holter monitor", "24-hour Holter monitor", "cardiac", "palpitations"), ("a thyroid test", "Thyroid function test", "laboratory", "palpitations")],
  [], [("Try cutting out caffeine for two weeks and see if the beats settle.", "Caffeine reduction trial")],
  ["after the results are back", "in four weeks"], today=["an ECG"])

P(CA, "ankle_swelling_drug_induced",
  [("swollen ankles in the evening", "Ankle swelling", "cardiovascular", "ankles", "standing all day", "raising the legs"),
   ("tight shoes by the end of the day", "Evening foot swelling", "cardiovascular", "feet", "", ""),
   ("a flushed face sometimes", "Facial flushing", "cardiovascular", "face", "", ""),
   ("a heavy feeling in the legs", "Leg heaviness", "musculoskeletal", "legs", "", ""),
   ("a bit of a headache", "Headache", "neurological", "head", "", "")],
  [("breathlessness lying flat", "Orthopnoea"), ("chest pain", "Chest pain"), ("one leg more swollen than the other", "Asymmetric leg swelling"), ("weight gain", "Weight gain"), ("reduced urine", "Reduced urine output"), ("calf pain", "Calf pain")],
  ["htn"], [],
  [("Mild pitting swelling around both ankles, equal on both sides.", [("pitting swelling around both ankles", "Bilateral ankle pitting oedema", "ankles", "present")]),
   ("Chest is clear and the neck veins aren't raised.", [("neck veins aren't raised", "Normal jugular venous pressure", "neck", "present")])],
  [("ankle swelling possibly from a blood pressure tablet", ["heart-related fluid retention", "a venous problem"])],
  [("kidney function tests", "Renal function test", "laboratory", "leg swelling"), ("a urine protein test", "Urine albumin-creatinine ratio", "laboratory", "leg swelling"), ("an echocardiogram", "Echocardiogram", "imaging", "leg swelling")],
  [], [("Raise your legs when you're sitting and try compression socks.", "Leg elevation and compression socks")],
  ["in three weeks", "after the results are back"], vit="htn")

P(CA, "breathlessness_multifactorial",
  [("getting out of puff on the stairs", "Exertional dyspnoea", "respiratory", "chest", "stairs;carrying shopping", "resting"),
   ("feeling tired", "Fatigue", "constitutional", None, "", "resting"),
   ("a dry cough at night", "Nocturnal cough", "respiratory", "chest", "", ""),
   ("ankles puffing up", "Ankle swelling", "cardiovascular", "ankles", "", ""),
   ("having put on weight", "Weight gain", "constitutional", None, "", "")],
  [("chest pain", "Chest pain"), ("palpitations", "Palpitations"), ("wheezing", "Wheeze"), ("coughing up blood", "Haemoptysis"), ("fever", "Fever"), ("calf swelling", "Calf swelling")],
  ["htn", "dm", "anemia"], [],
  [("Heart sounds are normal and the chest is clear.", [("heart sounds are normal", "Normal heart sounds", "chest", "present")]),
   ("Your BMI is on the high side and you look a little pale.", [("look a little pale", "Pallor", "general", "present")])],
  [("breathlessness with several possible contributors", ["heart failure", "anaemia", "deconditioning"])],
  [("blood tests", "Complete blood count, ferritin and BNP", "laboratory", "breathlessness"), ("an echocardiogram", "Echocardiogram", "imaging", "breathlessness"), ("a chest X-ray", "Chest X-ray", "imaging", "breathlessness")],
  [], [("A short daily walk, building up slowly, is a sensible start.", "Graded walking programme")],
  ["after the results are back", "in four weeks"])

# ------------------------------------------------------------------ Respiratory
P(RE, "cough_variant_asthma",
  [("a dry cough at night", "Nocturnal cough", "respiratory", "chest", "cold air;laughing", "warm drinks"),
   ("a tickle in the chest", "Chest tickle", "respiratory", "chest", "", ""),
   ("coughing after exercise", "Exercise-induced cough", "respiratory", "chest", "running", "resting"),
   ("a runny nose in the mornings", "Rhinorrhoea", "ENT", "nose", "", ""),
   ("a mild wheeze at times", "Wheeze", "respiratory", "chest", "", "")],
  [("fever", "Fever"), ("coughing up phlegm", "Productive cough"), ("weight loss", "Weight loss"), ("night sweats", "Night sweats"), ("chest pain", "Chest pain"), ("heartburn", "Heartburn")],
  ["eczema"], [],
  [("A faint wheeze when you breathe out forcefully.", [("faint wheeze", "Forced expiratory wheeze", "chest", "present")])],
  [("cough-variant asthma", ["post-nasal drip", "reflux-related cough"])],
  [("a peak flow reading", "Peak expiratory flow", "other", "chronic cough"), ("breathing tests", "Spirometry", "other", "chronic cough")],
  [("salbutamol inhaler", "Salbutamol", "100 micrograms", "inhaled", "two puffs when needed", "for two weeks", "cough and wheeze", None)],
  [("Try the inhaler before exercise and note whether the cough settles.", "Inhaler trial before exercise")],
  ["in two weeks", "in four weeks"], today=["a peak flow reading"])

P(RE, "pleuritic_pain_viral",
  [("sharp pain in the left chest when I breathe in", "Pleuritic chest pain", "respiratory", "left chest", "deep breaths;coughing", "shallow breathing"),
   ("a dry cough", "Cough", "respiratory", "chest", "", ""),
   ("a low fever a few days ago", "Fever", "constitutional", None, "", ""),
   ("aching all over", "Myalgia", "musculoskeletal", "generalised", "", ""),
   ("a sore throat earlier", "Sore throat", "ENT", "throat", "", "")],
  [("leg swelling", "Leg swelling"), ("coughing up blood", "Haemoptysis"), ("palpitations", "Palpitations"), ("recent long travel", "Recent long travel"), ("an injury to the chest", "Chest injury"), ("breathlessness at rest", "Dyspnoea at rest")],
  [], [("ibuprofen", "Ibuprofen", "400 mg", "when it hurts")],
  [("I can hear a faint rub on the left side.", [("faint rub on the left", "Pleural rub", "left chest", "present")]),
   ("Air entry is equal on both sides.", [("equal on both sides", "Equal air entry", "chest", "present")])],
  [("viral pleurisy", ["a chest infection", "a clot in the lung that we should rule out"])],
  [("a chest X-ray", "Chest X-ray", "imaging", "pleuritic pain"), ("an ECG", "Electrocardiogram", "cardiac", "chest pain")],
  [], [("Regular pain relief makes it easier to take deep breaths, which protects the lung.", "Regular analgesia to allow deep breathing")],
  ["in a week", "after the X-ray"], today=["an ECG"], red="you become breathless or the pain changes")

# ------------------------------------------------------------------ Gastroenterology
P(GI, "biliary_colic",
  [("pain under the right ribs after fatty meals", "Right upper quadrant pain", "gastrointestinal", "right upper abdomen", "fatty food", "lying still"),
   ("pain going to the shoulder blade", "Referred shoulder-blade pain", "gastrointestinal", "right scapula", "", ""),
   ("nausea with it", "Nausea", "gastrointestinal", None, "", ""),
   ("bloating", "Bloating", "gastrointestinal", "abdomen", "", ""),
   ("belching", "Belching", "gastrointestinal", None, "", "")],
  [("fever", "Fever"), ("yellow eyes", "Jaundice"), ("dark urine", "Dark urine"), ("pale stools", "Pale stools"), ("vomiting", "Vomiting"), ("weight loss", "Weight loss")],
  ["lipid", "dm"], [],
  [("Mild tenderness under the right ribs, and no pain when you breathe in while I press.", [("no pain when you breathe in", "Negative Murphy's sign", "right upper abdomen", "absent")]),
   ("The rest of the tummy is soft.", [("rest of the tummy is soft", "Soft abdomen", "abdomen", "present")])],
  [("gallstone pain", ["gastritis", "a liver problem"])],
  [("an ultrasound of the abdomen", "Abdominal ultrasound", "imaging", "right upper quadrant pain"), ("liver function tests", "Liver function test", "laboratory", "right upper quadrant pain")],
  [], [("Smaller, lower-fat meals will probably keep the pain down until we've seen the scan.", "Low-fat small meals")],
  ["after the scan", "in two weeks"], red="the pain lasts for hours, you get a fever or turn yellow")

P(GI, "lactose_intolerance_bloating",
  [("bloating after milk or ice cream", "Postprandial bloating", "gastrointestinal", "abdomen", "milk;ice cream", "avoiding dairy"),
   ("loose stools after dairy", "Diarrhoea", "gastrointestinal", None, "milk", ""),
   ("rumbling and gas", "Flatulence", "gastrointestinal", None, "", ""),
   ("cramps", "Abdominal cramps", "gastrointestinal", "abdomen", "", ""),
   ("an occasional queasy feeling", "Nausea", "gastrointestinal", None, "", "")],
  [("blood in the stool", "Blood in stool"), ("weight loss", "Weight loss"), ("fever", "Fever"), ("night-time symptoms", "Nocturnal symptoms"), ("a rash", "Rash"), ("vomiting", "Vomiting")],
  [], [],
  [("Your tummy is soft and non-tender, with active bowel sounds.", [("non-tender", "Non-tender abdomen", "abdomen", "present")])],
  [("lactose intolerance", ["irritable bowel syndrome", "coeliac disease"])],
  [("a hydrogen breath test", "Hydrogen breath test", "other", "suspected lactose intolerance"), ("a coeliac test", "Tissue transglutaminase antibody", "laboratory", "bloating")],
  [], [("Try two weeks without dairy and tell me if it makes a difference.", "Dairy-free trial")],
  ["in three weeks"])

# ------------------------------------------------------------------ MSK
P(MS, "plantar_fasciitis",
  [("sharp heel pain with my first steps in the morning", "Heel pain", "musculoskeletal", "heel", "first steps;long standing", "stretching"),
   ("pain after standing at work", "Post-standing foot pain", "musculoskeletal", "foot", "standing", "sitting"),
   ("tightness in the calf", "Calf tightness", "musculoskeletal", "calf", "", "stretching"),
   ("a tender spot on the sole", "Plantar tenderness", "musculoskeletal", "sole", "", ""),
   ("limping a bit by the evening", "Limp", "musculoskeletal", "foot", "", "")],
  [("numbness in the foot", "Foot numbness"), ("swelling", "Swelling"), ("a recent injury", "Recent injury"), ("fever", "Fever"), ("pain in other joints", "Other joint pain"), ("back pain", "Back pain")],
  [], [("Volini gel", "Diclofenac gel", None, "twice a day")],
  [("Pressing on the inner heel brings on the pain.", [("pressing on the inner heel", "Medial calcaneal tenderness", "heel", "present")]),
   ("The ankle and foot move fully.", [("move fully", "Full ankle range of motion", "ankle", "present")])],
  [("plantar fasciitis", ["a heel spur", "a stress reaction in the bone"])],
  [("an X-ray of the foot", "Foot X-ray", "imaging", "heel pain")],
  [], [("Roll the sole over a bottle and stretch the calf against a wall twice a day.", "Plantar fascia stretching"), ("Supportive shoes with a cushioned heel help.", "Supportive footwear")],
  ["in six weeks"], refs=[("physiotherapy", "Refer to physiotherapy")])

P(MS, "cervical_radiculopathy",
  [("neck pain going down my right arm", "Neck pain with right arm radiation", "musculoskeletal", "neck", "turning my head;looking up", "resting my arm on my head"),
   ("tingling in the thumb and index finger", "Paraesthesia in right hand", "neurological", "right hand", "", ""),
   ("a weak grip on that side", "Right grip weakness", "musculoskeletal", "right hand", "", ""),
   ("stiffness in the neck", "Neck stiffness", "musculoskeletal", "neck", "", "heat"),
   ("waking with an ache in the arm", "Nocturnal arm ache", "musculoskeletal", "right arm", "", "")],
  [("weakness in the legs", "Leg weakness"), ("balance problems", "Balance problems"), ("bladder problems", "Bladder dysfunction"), ("fever", "Fever"), ("a recent fall", "Fall"), ("headache", "Headache")],
  ["dm"], [PCM := ("paracetamol", "Paracetamol", "500 mg", "when needed")],
  [("Tilting the head to the right brings on the arm tingling.", [("tilting the head to the right", "Positive Spurling test", "neck", "present")]),
   ("Biceps power is a little reduced on the right.", [("biceps power is a little reduced", "Reduced right biceps power", "right arm", "present")])],
  [("a pinched nerve in the neck", ["carpal tunnel syndrome", "a shoulder problem"])],
  [("an X-ray of the neck", "Cervical spine X-ray", "imaging", "neck and arm pain"), ("an MRI of the cervical spine", "MRI cervical spine", "imaging", "arm symptoms")],
  [("naproxen", "Naproxen", "250 mg", "oral", "twice a day after food", "for five days", "nerve-related neck pain", "nsaid")],
  [("Keep the neck moving gently and avoid long periods looking down at a phone.", "Neck mobility and posture advice")],
  ["in three weeks", "after the scan"], refs=[("physiotherapy", "Refer to physiotherapy")])

# ------------------------------------------------------------------ Dermatology
P(DE, "herpes_zoster",
  [("a painful band of blisters on the left side of my chest", "Unilateral vesicular rash", "dermatological", "left chest", "clothing rubbing", "cool cloths"),
   ("burning pain before the rash came", "Prodromal burning pain", "neurological", "left chest", "", ""),
   ("itching", "Itching", "dermatological", "left chest", "", ""),
   ("feeling achy", "Myalgia", "musculoskeletal", "generalised", "", ""),
   ("a mild fever", "Fever", "constitutional", None, "", "")],
  [("rash on the face", "Facial rash"), ("eye pain", "Eye pain"), ("weakness", "Weakness"), ("rash on the other side", "Bilateral rash"), ("blurred vision", "Blurred vision"), ("immune problems", "Immunosuppression")],
  ["dm", "htn"], [],
  [("Grouped blisters on a red base along one rib on the left, not crossing the midline.", [("grouped blisters", "Dermatomal vesicular rash", "left chest", "present")])],
  [("shingles", ["contact dermatitis", "an insect-bite reaction"])],
  [],
  [("aciclovir", "Aciclovir", "800 mg", "oral", "five times a day", "for seven days", "shingles", None),
   ("paracetamol", "Paracetamol", "1 g", "oral", "every six hours if needed", "for five days", "pain", None)],
  [("Keep the blisters clean and covered, and avoid contact with anyone pregnant or newborn until they crust.", "Cover blisters and avoid vulnerable contacts")],
  ["in a week", "in two weeks"], red="the rash spreads to your face or eye")

P(DE, "scabies_itch",
  [("terrible itching at night", "Nocturnal itching", "dermatological", None, "being warm in bed", ""),
   ("tiny spots between my fingers", "Interdigital papules", "dermatological", "fingers", "", ""),
   ("scratch marks on the wrists and waist", "Excoriations", "dermatological", "wrists", "", ""),
   ("a rash that started in the finger webs", "Finger-web rash", "dermatological", "fingers", "", ""),
   ("trouble sleeping because of it", "Insomnia", "neurological", None, "", "")],
  [("fever", "Fever"), ("pus", "Pus"), ("a rash on the face", "Facial rash"), ("itching in other family members", "Contacts itching"), ("new soaps", "New soap use"), ("joint pain", "Joint pain")],
  ["eczema"], [("cetirizine", "Cetirizine", "10 mg", "at night")],
  [("Tiny linear burrows between the fingers and scratched papules on the wrists.", [("linear burrows", "Scabies burrows", "fingers", "present")])],
  [("scabies", ["eczema", "an insect-bite reaction"])],
  [],
  [("permethrin cream", "Permethrin", None, "topical", "applied once, repeated in a week", "for two applications", "scabies", None)],
  [("Everyone in the house should be treated at the same time, and bedding washed hot.", "Treat household contacts and wash bedding")],
  ["in two weeks"])

# ------------------------------------------------------------------ Endocrinology
P(EN, "vitamin_d_b12_deficiency",
  [("aching bones and muscles", "Bone and muscle aches", "musculoskeletal", "generalised", "", "rest"),
   ("tiredness", "Fatigue", "constitutional", None, "", ""),
   ("tingling in the feet", "Foot paraesthesia", "neurological", "feet", "", ""),
   ("low mood", "Low mood", "psychiatric", None, "", ""),
   ("a sore tongue", "Glossitis", "ENT", "tongue", "", "")],
  [("fractures", "Fracture"), ("weight loss", "Weight loss"), ("fever", "Fever"), ("breathlessness", "Shortness of breath"), ("black stools", "Melaena"), ("poor diet", "Poor diet")],
  ["gerd"], [],
  [("Gentle pressure over the shin bone is tender.", [("pressure over the shin bone is tender", "Shin bone tenderness", "shin", "present")]),
   ("The tongue looks smooth and a little red.", [("smooth and a little red", "Smooth red tongue", "tongue", "present")])],
  [("a vitamin deficiency", ["an underactive thyroid", "anaemia"])],
  [("a vitamin D level", "Vitamin D level", "laboratory", "bone aches"), ("a vitamin B12 level", "Vitamin B12 level", "laboratory", "tingling and tiredness"), ("a full blood count", "Complete blood count", "laboratory", "fatigue")],
  [("vitamin D", "Cholecalciferol", "60000 units", "oral", "once a week", "for eight weeks", "possible deficiency", None)],
  [("Some midday sunlight on the arms for fifteen minutes helps.", "Sunlight exposure advice")],
  ["after the results are back", "in two months"])

P(EN, "diabetic_foot_review",
  [("numb patches on both feet", "Foot numbness", "neurological", "feet", "", ""),
   ("a small sore on the sole that is slow to heal", "Non-healing foot ulcer", "dermatological", "foot", "walking", ""),
   ("cramping in the calves when I walk", "Calf claudication", "cardiovascular", "calves", "walking", "stopping"),
   ("dry cracked heels", "Cracked heels", "dermatological", "heels", "", "moisturiser"),
   ("cold feet", "Cold feet", "cardiovascular", "feet", "", "")],
  [("fever", "Fever"), ("redness spreading up the foot", "Spreading erythema"), ("pus", "Pus"), ("foot pain at rest", "Rest pain"), ("black skin", "Skin discolouration"), ("smell from the foot", "Foot odour")],
  ["dm", "htn", "lipid"], [],
  [("There's a small shallow ulcer under the ball of the left foot, no pus or surrounding redness.", [("shallow ulcer", "Plantar ulcer", "left foot", "present"), ("no pus", "No purulent discharge", "left foot", "absent")]),
   ("Pulses at the ankle are weak.", [("pulses at the ankle are weak", "Reduced pedal pulses", "feet", "present")])],
  [("a diabetic foot ulcer with some circulation concern", ["an infected wound", "peripheral arterial disease"])],
  [("an HbA1c", "HbA1c", "laboratory", "diabetes control"), ("a foot X-ray", "Foot X-ray", "imaging", "foot ulcer"), ("a Doppler scan of the leg", "Arterial Doppler", "imaging", "poor pulses")],
  [], [("Look at your feet every day with a mirror and never go barefoot.", "Daily foot inspection")],
  ["in a week", "in two weeks"], vit="htn", refs=[("the podiatry clinic", "Refer to podiatry")], red="the sore becomes red, smelly or the foot turns dusky")

# ------------------------------------------------------------------ Nephrology / Urology
P(NU, "stress_incontinence",
  [("leaking urine when I cough or sneeze", "Stress urinary leakage", "genitourinary", None, "coughing;laughing;exercise", ""),
   ("needing to wear a pad", "Pad use", "genitourinary", None, "", ""),
   ("an urgent need to go sometimes", "Urinary urgency", "genitourinary", None, "", ""),
   ("getting up once at night", "Nocturia", "genitourinary", None, "", ""),
   ("a heavy dragging feeling low down", "Pelvic heaviness", "gynaecological", "pelvis", "", "")],
  [("burning when passing urine", "Dysuria"), ("blood in the urine", "Haematuria"), ("difficulty emptying", "Voiding difficulty"), ("back pain", "Back pain"), ("fever", "Fever"), ("constipation", "Constipation")],
  ["htn", "dm"], [],
  [("No bulge is visible when you cough, and the tummy is soft.", [("no bulge is visible", "No visible prolapse", "pelvis", "absent")])],
  [("stress urinary incontinence", ["an overactive bladder", "a urine infection"])],
  [("a urine test", "Urinalysis", "laboratory", "urinary leakage"), ("a bladder diary", "Bladder diary", "other", "urinary symptoms")],
  [], [("Pelvic floor exercises, three sets a day, make a real difference over a couple of months.", "Pelvic floor exercises")],
  ["in eight weeks", "in six weeks"], today=["a urine test"], refs=[("a pelvic-floor physiotherapist", "Refer to pelvic floor physiotherapy")])

# ------------------------------------------------------------------ ENT / Ophthalmology
P(EO, "swimmers_ear",
  [("an itchy painful right ear", "Right ear pain and itching", "ENT", "right ear", "touching the ear;lying on it", ""),
   ("a feeling of blockage", "Ear fullness", "ENT", "right ear", "", ""),
   ("a bit of discharge", "Ear discharge", "ENT", "right ear", "", ""),
   ("muffled hearing on that side", "Reduced hearing", "ENT", "right ear", "", ""),
   ("pain when I move my jaw", "Jaw movement pain", "ENT", "jaw", "chewing", "")],
  [("fever", "Fever"), ("dizziness", "Dizziness"), ("facial weakness", "Facial weakness"), ("swelling behind the ear", "Mastoid swelling"), ("a recent cold", "Recent cold"), ("ringing", "Tinnitus")],
  ["dm", "eczema"], [],
  [("The ear canal is red and swollen with some debris, and pulling the ear hurts.", [("pulling the ear hurts", "Tragal and pinna tenderness", "right ear", "present")]),
   ("I can't see the eardrum properly because of the swelling.", [("can't see the eardrum", "Obscured tympanic membrane", "right ear", "present")])],
  [("an outer ear infection", ["a middle ear infection", "a wax problem"])],
  [],
  [("ciprofloxacin ear drops", "Ciprofloxacin", None, "otic", "three times a day", "for seven days", "outer ear infection", None)],
  [("Keep water out of the ear and don't use cotton buds.", "Keep ear dry, avoid cotton buds")],
  ["in a week", "if it's not better in four days"])

P(EO, "dry_eye_screen_strain",
  [("gritty tired eyes", "Gritty eyes", "ophthalmological", "both eyes", "screens;air conditioning", "blinking breaks"),
   ("burning at the end of the day", "Eye burning", "ophthalmological", "both eyes", "", ""),
   ("watery eyes in the wind", "Reflex tearing", "ophthalmological", "both eyes", "wind", ""),
   ("blurry vision that clears when I blink", "Transient blurred vision", "ophthalmological", "both eyes", "", "blinking"),
   ("redness by the evening", "Eye redness", "ophthalmological", "both eyes", "", "")],
  [("eye pain", "Eye pain"), ("sensitivity to light", "Photophobia"), ("loss of vision", "Visual loss"), ("a discharge", "Eye discharge"), ("double vision", "Diplopia"), ("a dry mouth", "Dry mouth")],
  [], [("artificial tears", "Carboxymethylcellulose", None, "when needed")],
  [("The eyes look a little pink but the corneas are clear.", [("corneas are clear", "Clear corneas", "both eyes", "present")])],
  [("dry eye", ["digital eye strain", "an allergic eye problem"])],
  [("an eye check", "Eye examination", "other", "gritty eyes")],
  [("lubricating eye drops", "Carboxymethylcellulose", None, "ophthalmic", "four times a day", "for one month", "dry eye", None)],
  [("Look away from the screen every twenty minutes and blink fully.", "20-20-20 screen break rule")],
  ["in four weeks"])

# ------------------------------------------------------------------ Gynaecology
P(GY, "irregular_periods_pcos",
  [("irregular periods", "Irregular menses", "gynaecological", None, "", ""),
   ("excess hair on my face", "Hirsutism", "dermatological", "face", "", ""),
   ("acne along the jaw", "Acne", "dermatological", "face", "", ""),
   ("putting on weight around the middle", "Central weight gain", "constitutional", None, "", ""),
   ("thinning hair on the scalp", "Scalp hair thinning", "dermatological", "scalp", "", "")],
  [("a missed period", "Missed period"), ("pelvic pain", "Pelvic pain"), ("milk from the breasts", "Galactorrhoea"), ("headaches with vision changes", "Visual symptoms with headache"), ("heavy bleeding", "Heavy bleeding"), ("trying for a baby", "Trying to conceive")],
  [], [],
  [("Facial acne along the jaw and some dark coarse hair on the chin.", [("dark coarse hair on the chin", "Facial hirsutism", "face", "present")])],
  [("possible polycystic ovary syndrome", ["a thyroid problem", "raised prolactin"])],
  [("a pelvic ultrasound", "Pelvic ultrasound", "imaging", "irregular periods"), ("hormone blood tests", "Hormone panel (LH, FSH, testosterone, prolactin)", "laboratory", "irregular periods"), ("a thyroid test", "Thyroid function test", "laboratory", "irregular periods")],
  [], [("Regular exercise and modest weight loss can bring cycles back.", "Lifestyle advice for PCOS")],
  ["after the results are back", "in six weeks"])

# ------------------------------------------------------------------ Mental health / other
P(MH, "alcohol_reduction_visit",
  [("wanting to cut down on drinking", "Request to reduce alcohol", "psychiatric", None, "stress;weekends", ""),
   ("morning shakiness", "Morning tremor", "neurological", "hands", "", ""),
   ("an upset stomach in the mornings", "Morning nausea", "gastrointestinal", None, "", ""),
   ("poor sleep", "Insomnia", "neurological", None, "", ""),
   ("feeling guilty about it", "Guilt", "psychiatric", None, "", "")],
  [("blackouts", "Blackouts"), ("seizures", "Seizure"), ("vomiting blood", "Haematemesis"), ("yellow eyes", "Jaundice"), ("thoughts of harming myself", "Suicidal ideation"), ("drinking in the morning", "Morning drinking")],
  ["gerd", "htn"], [],
  [("Hands show a fine tremor and your abdomen is soft with no tenderness.", [("fine tremor", "Fine tremor", "hands", "present")])],
  [("alcohol use that you'd like to reduce", ["alcohol-related liver strain", "anxiety driving the drinking"])],
  [("liver function tests", "Liver function test", "laboratory", "alcohol use"), ("blood tests", "Complete blood count", "laboratory", "alcohol use")],
  [], [("Plan a few alcohol-free days each week and track how much you drink.", "Reduce alcohol, drink diary")],
  ["in four weeks", "in a month"], refs=[("the alcohol support service", "Refer to alcohol support service")], red="you have severe shaking, confusion or seizures when you cut down")

P(MH, "adult_concentration_concern",
  [("trouble concentrating at work", "Poor concentration", "neurological", None, "noisy offices", ""),
   ("losing things all the time", "Misplacing objects", "neurological", None, "", "lists"),
   ("starting tasks and not finishing them", "Task incompletion", "psychiatric", None, "", ""),
   ("feeling restless", "Restlessness", "psychiatric", None, "", ""),
   ("poor sleep", "Insomnia", "neurological", None, "", "")],
  [("low mood", "Low mood"), ("anxiety attacks", "Panic attacks"), ("heavy caffeine", "High caffeine intake"), ("substance use", "Substance use"), ("headaches", "Headache"), ("a head injury", "Head injury")],
  ["anxiety"], [],
  [],
  [("difficulty with attention and organisation that needs a fuller assessment", ["anxiety", "poor sleep", "an underactive thyroid"])],
  [("a thyroid test", "Thyroid function test", "laboratory", "poor concentration"), ("blood tests", "Complete blood count", "laboratory", "poor concentration")],
  [], [("Keep a regular sleep schedule and write down your tasks each morning.", "Sleep schedule and task list")],
  ["in four weeks", "after the results are back"], refs=[("an adult attention clinic", "Refer to adult attention clinic")])

_mark()
