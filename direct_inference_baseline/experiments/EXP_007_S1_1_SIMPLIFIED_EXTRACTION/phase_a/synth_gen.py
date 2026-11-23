"""Synthetic consultation generator for Phase A (template-based, seeded; NO project data). Returns lines [(speaker_id, ROLE, start_s, text)] and the expected facts known by construction."""
import random

COMPLAINTS = [("a dry cough", ["dry cough", "shortness of breath"], "two weeks"), ("chest tightness", ["chest tightness", "tiredness"], "three days"),
              ("lower back pain", ["back pain", "leg numbness"], "one month"), ("a sore throat", ["sore throat", "headache"], "four days"),
              ("stomach pain", ["stomach pain", "nausea"], "a week"), ("dizziness", ["dizziness", "blurred vision"], "five days"),
              ("a painful knee", ["knee pain", "swelling"], "ten days"), ("a skin rash", ["skin rash", "itching"], "three weeks"),
              ("ear pain", ["ear pain", "hearing loss"], "six days"), ("burning urine", ["burning urine", "fever"], "two days")]
NEGS = ["chest pain", "vomiting", "weight loss", "night sweats", "palpitations", "blood in stool", "fainting", "ankle swelling"]
MEDS = [("amlodipine", "five milligrams", "once a day"), ("metformin", "five hundred milligrams", "twice a day"), ("atorvastatin", "twenty milligrams", "at night"),
        ("omeprazole", "twenty milligrams", "every morning"), ("levothyroxine", "fifty micrograms", "every morning"), ("salbutamol", "two puffs", "when needed"),
        ("lisinopril", "ten milligrams", "once a day"), ("sertraline", "fifty milligrams", "once a day")]
NEWMEDS = [("amoxicillin", "five hundred milligrams", "three times a day"), ("ibuprofen", "four hundred milligrams", "three times a day"), ("cetirizine", "ten milligrams", "once a day"),
           ("prednisolone", "twenty milligrams", "once a day"), ("paracetamol", "five hundred milligrams", "when needed")]
HIST = [("diabetes", "eight years"), ("high blood pressure", "five years"), ("asthma", "since childhood"), ("thyroid problem", "three years"), ("high cholesterol", "two years")]
SURG = ["appendix removal", "knee arthroscopy", "gallbladder removal", "hernia repair"]
FAM = [("heart disease", "father"), ("diabetes", "mother"), ("stroke", "grandmother"), ("cancer", "uncle")]
DX = ["viral infection", "muscle strain", "reflux", "chest infection", "allergic reaction", "urinary infection"]
TESTS = [("blood test", "laboratory"), ("chest x-ray", "imaging"), ("ecg", "cardiac"), ("urine test", "laboratory")]
FOLLOW = ["in two weeks", "in one week", "in three days", "next month"]
EXAM = [("tenderness", "abdomen"), ("wheeze", "chest"), ("swelling", "knee"), ("redness", "throat")]
ALLERGY = [("penicillin", "rash"), ("aspirin", "swelling"), ("latex", "itching"), ("shellfish", "hives")]


def make_case(seed):
    r = random.Random(seed)
    L = []
    t = [1.0]

    def say(role, text):
        spk = {"PATIENT": "person_1", "DOCTOR": "person_2", "NURSE": "person_3"}[role]
        L.append((spk, role, t[0], text))
        t[0] += 4 + len(text) / 15

    comp, syms, dur = r.choice(COMPLAINTS)
    negs = r.sample(NEGS, 3)
    meds = r.sample(MEDS, 2)
    stopped = r.choice([None, r.choice([m for m in MEDS if m not in meds])])
    new = r.choice(NEWMEDS)
    hist = r.sample(HIST, 2)
    surg = r.choice(SURG)
    fam = r.choice(FAM)
    smoke = r.choice(["never smoked", "stopped smoking five years ago", "smoke ten cigarettes a day"])
    alc = r.choice(["only at weekends", "I do not drink"])
    allergy = r.choice([None, None, r.choice(ALLERGY)])          # None = patient says no allergies
    asked = r.random() > 0.15                                     # sometimes the doctor never asks
    exam = r.choice(EXAM)
    dx = r.choice(DX)
    test = r.choice(TESTS)
    fu = r.choice(FOLLOW)
    bp = (r.randint(110, 150), r.randint(70, 95)); pulse = r.randint(60, 100); temp = round(r.uniform(36.2, 38.4), 1)
    vit_role = r.choice(["NURSE", "DOCTOR"])
    say("PATIENT", "Good morning doctor."); say("DOCTOR", "Good morning, please sit down. So, what brings you in today?")
    say("PATIENT", f"I have been having {comp}."); say("DOCTOR", "And how long has that been going on?")
    say("PATIENT", f"About {dur} now."); say("DOCTOR", "Okay. Do you have any other symptoms along with it?")
    say("PATIENT", f"Yes, I also have {syms[1]}, and the {syms[0]} is worse at night."); say("DOCTOR", "I see. Let me ask about a few other things.")
    for n in negs:
        say("DOCTOR", f"Have you had any {n}?"); say("PATIENT", f"No, no {n}.")
    say("DOCTOR", "Do you have any medical conditions?"); say("PATIENT", f"Yes, {hist[0][0]} for {hist[0][1]}, and {hist[1][0]}, {hist[1][1]}.")
    say("DOCTOR", "Have you had any operations?"); say("PATIENT", f"I had a {surg} some years ago.")
    say("DOCTOR", f"Does anyone in the family have {fam[0]}?"); say("PATIENT", f"Yes, my {fam[1]} had {fam[0]}.")
    say("DOCTOR", "Do you smoke or drink alcohol?"); say("PATIENT", f"I {smoke}. Alcohol, {alc}.")
    say("DOCTOR", "Are you taking any regular medicines?")
    say("PATIENT", f"Yes, {meds[0][0]} {meds[0][1]} {meds[0][2]}, and {meds[1][0]} {meds[1][1]} {meds[1][2]}.")
    if stopped:
        say("DOCTOR", "Anything you used to take?"); say("PATIENT", f"I stopped {stopped[0]} last month, my doctor changed it.")
    if asked:
        say("DOCTOR", "Do you have any allergies to medicines or anything else?")
        say("PATIENT", "No, no allergies." if allergy is None else f"Yes, {allergy[0]} gives me {allergy[1]}.")
        astatus = "none_stated" if allergy is None else "reported"
    else:
        astatus = "not_asked"
    say(vit_role, f"Your blood pressure is {bp[0]} over {bp[1]}, pulse {pulse}, temperature {temp}.")
    say("DOCTOR", f"On examination I can see {exam[0]} in the {exam[1]}."); say("PATIENT", "Okay.")
    say("DOCTOR", f"I think this is most likely a {dx}."); say("PATIENT", "I see.")
    say("DOCTOR", f"I will prescribe {new[0]} {new[1]} {new[2]}."); say("DOCTOR", f"Let us also do a {test[0]}."); say("PATIENT", "Alright, thank you.")
    say("DOCTOR", f"Please come back {fu} so I can review you."); say("PATIENT", "Thank you doctor, goodbye.")
    exp = {"chief_keywords": [w for w in comp.split() if len(w) > 3 and w not in ("having",)] + [syms[0]], "symptoms": syms, "negatives": negs, "meds": [(m[0], "current", "patient") for m in meds] + [(new[0], "new", "doctor")],
           "stopped_med": stopped[0] if stopped else None, "allergy_status": astatus, "allergy_substance": allergy[0] if allergy else None,
           "vitals": [("blood pressure", vit_role.lower()), ("pulse", vit_role.lower()), ("temperature", vit_role.lower())], "investigations": [test[0]], "follow_up": fu,
           "history": [h[0] for h in hist], "surgical": surg, "family": fam[0]}
    return L, exp


def render(lines, mode):
    if mode == "R0":
        return "\n".join(f"[SEG{i + 1:04d}] {sp} ({role}) {t:.2f}-{t + 3.5:.2f}s: {txt}" for i, (sp, role, t, txt) in enumerate(lines))
    return "\n".join(f"{role.lower()}: {txt}" for sp, role, t, txt in lines)


CASES = {f"synA{i:02d}": make_case(20261113 + i) for i in range(1, 11)}
