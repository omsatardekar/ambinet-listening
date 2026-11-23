"""Shared clinical content pools for the Batch 001 generator.

Everything here is hand-authored reference content (symptom wording, drugs,
conditions...).  The generator samples from it; it never invents clinical
facts outside these pools.  NOT clinically reviewed by a qualified human.
"""

PROFILES = []


def P(spec, key, syms, negs, conds, otc, exam, assess, inv, rx, counsel,
      fu, vit="normal", refs=(), today=(), red="the symptoms get worse"):
    """Register a clinical scenario profile (compact tuple DSL).

    syms   : (names 'a|b', norm, category, site, 'aggr;aggr', 'relief;relief')
             first symptom is the primary complaint
    negs   : (phrase, Normalized)
    conds  : keys into COND (plausible chronic background)
    otc    : (name, generic, dose, freq) self-medication for the complaint
    exam   : (doctor statement, [(finding_literal, norm, site, status)])
    assess : (primary, [differentials])   -- never "confirmed"
    inv    : (spoken name, normalized, type, indication)
    rx     : (name, generic, dose, route, freq, duration, indication, avoid_tag)
    counsel: (spoken advice, action description)
    refs   : (spoken referral, description)
    today  : investigations a nurse can already have done today (names in inv)
    """
    for st, sl in exam:
        for f in sl:
            assert f[0].lower() in st.lower(), (key, f[0])
    for a in assess:
        assert a[0]
    PROFILES.append(dict(spec=spec, key=key, syms=list(syms), negs=list(negs),
                         conds=list(conds), otc=list(otc), exam=list(exam),
                         assess=list(assess), inv=list(inv), rx=list(rx),
                         counsel=list(counsel), fu=list(fu), vit=vit,
                         refs=list(refs), today=list(today), red=red))


# ---- chronic conditions: key -> (patient phrase, normalized, medication options)
# medication option: (name, generic, dose, freq, route, indication phrase)
COND = {
    "htn": ("high blood pressure", "Hypertension", [
        ("amlodipine", "Amlodipine", "5 mg", "once a day", "oral", "my pressure"),
        ("telmisartan", "Telmisartan", "40 mg", "once a day", "oral", "my pressure"),
        ("losartan", "Losartan", "50 mg", "once a day", "oral", "my blood pressure"),
        ("ramipril", "Ramipril", "5 mg", "every morning", "oral", "my blood pressure")]),
    "dm": ("diabetes", "Type 2 diabetes mellitus", [
        ("metformin", "Metformin", "500 mg", "twice a day", "oral", "my sugar"),
        ("Glycomet", "Metformin", "500 mg", "twice a day", "oral", "my sugar"),
        ("glimepiride", "Glimepiride", "2 mg", "before breakfast", "oral", "my sugar")]),
    "asthma": ("asthma", "Asthma", [
        ("Asthalin inhaler", "Salbutamol", None, "when needed", "inhaled", "my asthma"),
        ("Seretide inhaler", "Salmeterol/fluticasone", None, "twice a day", "inhaled", "my asthma")]),
    "copd": ("COPD", "Chronic obstructive pulmonary disease", [
        ("Tiotropium inhaler", "Tiotropium", None, "once a day", "inhaled", "my chest")]),
    "hypothyroid": ("an underactive thyroid", "Hypothyroidism", [
        ("thyroxine", "Levothyroxine", "75 micrograms", "every morning", "oral", "my thyroid"),
        ("Thyronorm", "Levothyroxine", "50 micrograms", "every morning", "oral", "my thyroid")]),
    "lipid": ("high cholesterol", "Hypercholesterolaemia", [
        ("atorvastatin", "Atorvastatin", "20 mg", "at night", "oral", "my cholesterol"),
        ("rosuvastatin", "Rosuvastatin", "10 mg", "at night", "oral", "my cholesterol")]),
    "gerd": ("acid reflux", "Gastro-oesophageal reflux disease", [
        ("pantoprazole", "Pantoprazole", "40 mg", "before breakfast", "oral", "my acidity"),
        ("omeprazole", "Omeprazole", "20 mg", "once a day", "oral", "the reflux")]),
    "migraine": ("migraines", "Migraine", [
        ("sumatriptan", "Sumatriptan", "50 mg", "when needed", "oral", "my migraines")]),
    "epilepsy": ("epilepsy", "Epilepsy", [
        ("levetiracetam", "Levetiracetam", "500 mg", "twice a day", "oral", "the seizures"),
        ("sodium valproate", "Sodium valproate", "500 mg", "twice a day", "oral", "the fits")]),
    "depression": ("depression", "Depression", [
        ("sertraline", "Sertraline", "50 mg", "once a day", "oral", "my mood"),
        ("escitalopram", "Escitalopram", "10 mg", "once a day", "oral", "my mood")]),
    "anxiety": ("anxiety", "Anxiety disorder", [
        ("escitalopram", "Escitalopram", "10 mg", "once a day", "oral", "the anxiety")]),
    "oa": ("arthritis in my knees", "Osteoarthritis of the knee", [
        ("diclofenac", "Diclofenac", "50 mg", "when needed", "oral", "the joint pain"),
        ("paracetamol", "Paracetamol", "650 mg", "when needed", "oral", "the knee pain")]),
    "af": ("an irregular heartbeat", "Atrial fibrillation", [
        ("apixaban", "Apixaban", "5 mg", "twice a day", "oral", "the heart rhythm"),
        ("bisoprolol", "Bisoprolol", "2.5 mg", "once a day", "oral", "the heart rhythm")]),
    "ihd": ("heart disease", "Ischaemic heart disease", [
        ("aspirin", "Aspirin", "75 mg", "once a day", "oral", "my heart"),
        ("clopidogrel", "Clopidogrel", "75 mg", "once a day", "oral", "the stent")]),
    "gout": ("gout", "Gout", [
        ("allopurinol", "Allopurinol", "100 mg", "once a day", "oral", "the gout")]),
    "hf": ("heart failure", "Heart failure", [
        ("furosemide", "Furosemide", "40 mg", "every morning", "oral", "the fluid"),
        ("spironolactone", "Spironolactone", "25 mg", "once a day", "oral", "my heart")]),
    "bph": ("an enlarged prostate", "Benign prostatic hyperplasia", [
        ("tamsulosin", "Tamsulosin", "0.4 mg", "at night", "oral", "the prostate")]),
    "eczema": ("eczema", "Eczema", [
        ("hydrocortisone cream", "Hydrocortisone", None, "when needed", "topical", "the eczema")]),
    "ckd": ("kidney disease", "Chronic kidney disease", []),
    "anemia": ("low haemoglobin", "Anaemia", [
        ("iron tablets", "Ferrous sulfate", None, "once a day", "oral", "my blood count")]),
    "osteopor": ("thin bones", "Osteoporosis", [
        ("alendronate", "Alendronic acid", "70 mg", "once a week", "oral", "my bones")]),
}

SURG = [  # (patient phrase, normalized, timeframe)
    ("my appendix out", "Appendicectomy", "about eight years ago"),
    ("my gallbladder removed", "Cholecystectomy", "in 2016"),
    ("a hernia repair", "Hernia repair", "about five years back"),
    ("my tonsils out", "Tonsillectomy", "when I was a child"),
    ("a C-section", "Caesarean section", "about ten years ago"),
    ("a knee arthroscopy", "Knee arthroscopy", "three years ago"),
    ("cataract surgery on my right eye", "Cataract surgery", "last year"),
    ("a hysterectomy", "Hysterectomy", "about twelve years ago"),
    ("a stent put in my heart", "Coronary stenting", "two years ago"),
    ("a lump removed from my back", "Excision of back lump", "years ago"),
    ("a bypass operation", "Coronary artery bypass grafting", "six years ago"),
    ("my thyroid operated on", "Thyroid surgery", "a long time ago"),
]

FAMILY = [  # (spoken phrase, normalized, relation)
    ("My father had a heart attack", "Myocardial infarction", "father"),
    ("My mother has diabetes", "Diabetes mellitus", "mother"),
    ("My mother had high blood pressure", "Hypertension", "mother"),
    ("My brother has asthma", "Asthma", "brother"),
    ("My father had a stroke", "Stroke", "father"),
    ("My sister has thyroid problems", "Thyroid disorder", "sister"),
    ("My grandmother had breast cancer", "Breast cancer", "grandmother"),
    ("My father had kidney stones", "Kidney stones", "father"),
    ("My uncle had colon cancer", "Colon cancer", "uncle"),
    ("My mother has migraines", "Migraine", "mother"),
    ("My father was diabetic", "Diabetes mellitus", "father"),
    ("My sister has epilepsy", "Epilepsy", "sister"),
]

# (category, status, spoken statements with optional detail, description, details)
SOCIAL = [
    ("smoking", "current", "I smoke about ten cigarettes a day", "Current smoker", "about ten cigarettes a day"),
    ("smoking", "current", "I smoke, yes, around five a day", "Current smoker", "around five a day"),
    ("smoking", "former", "I used to smoke but I quit five years ago", "Former smoker", "quit five years ago"),
    ("smoking", "former", "I stopped smoking about two years back", "Former smoker", "stopped smoking about two years back"),
    ("smoking", "never", "I've never smoked", "Never smoked", None),
    ("smoking", "never", "No, I don't smoke and never have", "Never smoked", None),
    ("alcohol", "current", "I have a couple of drinks on the weekend", "Occasional alcohol use", "a couple of drinks on the weekend"),
    ("alcohol", "current", "A beer or two most evenings, to be honest", "Regular alcohol use", "a beer or two most evenings"),
    ("alcohol", "never", "I don't drink at all", "Does not drink alcohol", None),
    ("alcohol", "former", "I gave up drinking about three years ago", "Former alcohol use", "gave up drinking about three years ago"),
]

ALLERGY = [  # (substance, normalized, type, reactions)
    ("penicillin", "Penicillin", "medication", ["a rash", "hives", "swelling of my face"]),
    ("sulfa drugs", "Sulfonamide", "medication", ["a rash", "itching all over"]),
    ("aspirin", "Aspirin", "medication", ["wheezing", "a rash"]),
    ("ibuprofen", "Ibuprofen", "medication", ["stomach pain", "a rash"]),
    ("codeine", "Codeine", "medication", ["vomiting", "feeling very drowsy"]),
    ("peanuts", "Peanuts", "food", ["hives", "my lips swelling"]),
    ("shellfish", "Shellfish", "food", ["hives", "vomiting"]),
    ("eggs", "Egg", "food", ["a rash", "stomach cramps"]),
    ("dust", "House dust", "environmental", ["sneezing", "itchy eyes"]),
    ("pollen", "Pollen", "environmental", ["sneezing", "a runny nose"]),
    ("latex", "Latex", "environmental", ["a rash on my hands"]),
]
ALLERGY_AVOID = {"penicillin": "penicillin", "aspirin": "nsaid", "ibuprofen": "nsaid",
                 "sulfa drugs": "sulfa", "codeine": "opioid"}

# (surface, value, unit, normalized)
DURATIONS = [
    ("two days", 2, "days", "2 days"), ("three days", 3, "days", "3 days"),
    ("about four days", 4, "days", "about 4 days"), ("five days", 5, "days", "5 days"),
    ("about a week", 1, "weeks", "about 1 week"), ("ten days", 10, "days", "10 days"),
    ("two weeks", 2, "weeks", "2 weeks"), ("about two weeks", 2, "weeks", "about 2 weeks"),
    ("three weeks", 3, "weeks", "3 weeks"), ("about a month", 1, "months", "about 1 month"),
    ("two months", 2, "months", "2 months"), ("about three months", 3, "months", "about 3 months"),
    ("six months", 6, "months", "6 months"), ("about a year", 1, "years", "about 1 year"),
    ("two years", 2, "years", "2 years"), ("nearly five years", 5, "years", "nearly 5 years"),
    ("one week", 1, "weeks", "1 week"), ("four weeks", 4, "weeks", "4 weeks"),
]
ONSETS = ["yesterday", "since yesterday", "since this morning", "since last night",
          "since Monday", "since last weekend", "since Friday", "since last Tuesday"]
FREQS = ["comes and goes", "all the time", "a few times a day", "a couple of times a week",
         "once or twice a day", "every other day", "on and off"]
SEVS = ["mild", "moderate", "severe"]
SEV_NUM = {3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight"}
PREV_EPISODE = ["last year", "a couple of years ago", "about six months ago", "last winter"]

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
FU_TIMES = ["in two weeks", "in a week", "next week", "in three days", "in four weeks",
            "in a month", "after the results are back", "in ten days", "in six weeks"]

# global counselling pool: (spoken, action description)
COUNSEL = [
    ("Make sure you're drinking plenty of fluids, two to three litres a day if you can, and get proper rest.", "Advise adequate fluid intake and rest"),
    ("Try to keep a simple diary of when it happens and what you were doing, and bring it to the next visit.", "Advise symptom diary"),
    ("Please take the tablets with food so they don't upset your stomach.", "Advise taking medication with food"),
    ("Cut down on salt and fried food for now, it really does make a difference.", "Advise reducing salt and fried food"),
    ("A short walk every day, even twenty minutes, will help more than you'd think.", "Advise daily walking"),
    ("Try to get to bed and wake up at the same time each day, and keep your phone away from the bed.", "Advise regular sleep routine"),
    ("If you smoke, this is a good moment to think about stopping, and we can help you with that.", "Advise smoking cessation"),
    ("Cut back on tea, coffee and fizzy drinks for a couple of weeks and see how things settle.", "Advise reducing caffeine intake"),
    ("Don't skip meals, and try to eat smaller portions more often through the day.", "Advise regular small meals"),
    ("Avoid taking any extra painkillers on top of what I'm prescribing without checking with us.", "Advise avoiding additional painkillers"),
]
SAFETY = [
    "If {red}, or you feel really unwell, please don't wait, come to the emergency department.",
    "I want you to come back or go to emergency straight away if {red}.",
    "Please don't sit on it if {red}. That's the point to get seen urgently.",
    "Keep an eye out, and if {red}, call us the same day or go to emergency.",
]

# vitals ranges by bias: (sbp, dbp, hr, rr, temp, spo2)
VITAL_BIAS = {
    "normal": ((108, 128), (68, 82), (64, 86), (14, 18), (36.4, 37.0), (97, 99)),
    "febrile": ((104, 126), (66, 80), (88, 108), (16, 22), (38.0, 39.4), (95, 98)),
    "htn": ((144, 172), (88, 104), (72, 94), (14, 18), (36.4, 37.0), (96, 99)),
    "tachy": ((112, 138), (70, 88), (104, 126), (16, 20), (36.5, 37.1), (96, 99)),
    "hypox": ((118, 142), (72, 90), (84, 104), (20, 26), (36.6, 37.6), (89, 94)),
    "lowbp": ((92, 104), (56, 66), (92, 112), (16, 20), (36.4, 37.2), (96, 99)),
}
