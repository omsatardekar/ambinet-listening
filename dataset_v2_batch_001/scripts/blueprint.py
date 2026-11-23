"""STEP 1: scenario blueprints.  A blueprint fixes every clinical fact of an
encounter *before* any dialogue is written.  Blueprints are stored separately
from the inputs/labels and are never part of the evaluation files."""
import random
import re
import content_core as C
import content_p1, content_p2, content_p3  # noqa: F401  (register profiles)
from content_core import PROFILES, COND, SURG, FAMILY, SOCIAL, ALLERGY, ALLERGY_AVOID, DURATIONS, ONSETS, FREQS, SEVS, VITAL_BIAS

SPEC_QUOTA = [("General Medicine / Infectious Diseases", 75), ("Neurology", 55), ("Cardiology", 50),
              ("Respiratory Medicine", 50), ("Gastroenterology", 45), ("Musculoskeletal / Orthopaedics", 40),
              ("Dermatology", 35), ("Endocrinology", 35), ("Nephrology / Urology", 30),
              ("ENT / Ophthalmology", 25), ("Gynaecology", 20), ("Mental Health / Other", 40)]
CPLX_QUOTA = [("simple", 100), ("moderate", 175), ("complex", 150), ("challenging", 75)]

COMBOS = {
    "simple": [("DP", 80), ("DPN", 12), ("DPS", 8)],
    "moderate": [("DP", 50), ("DPN", 20), ("DPC", 10), ("DPF", 12), ("DPS", 8)],
    "complex": [("DPN", 18), ("DPC", 25), ("DPF", 22), ("DPNC", 15), ("DPS", 8), ("DPNF", 12)],
    "challenging": [("DPNC", 25), ("DPCF", 12), ("DPNF", 15), ("DPNCS", 10), ("DPCS", 8), ("DPFS", 8), ("DPNCF", 12), ("DPNS", 10)],
}
NUMW = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
        "ten": 10, "twelve": 12}
ACUTE = {"viral_fever", "dengue_season_fever", "gastro_dehydration", "post_travel_fever", "tonsillitis", "infected_wound",
         "heat_exhaustion", "uti_cystitis", "renal_colic", "right_lower_abdominal_pain", "diarrhoea_acute", "otitis_media",
         "red_eye_conjunctivitis", "sports_ankle_sprain", "gout_flare", "wrist_fall_injury", "acute_cough_bronchitis",
         "asthma_flare", "copd_exacerbation", "pneumonia_suspect", "urticaria_allergic", "syncope_workup",
         "leg_swelling_dvt_concern", "vertigo_bppv", "facial_numbness_stroke_followup", "seizure_followup", "sinusitis",
         "prolonged_fever_enteric"}
CHRONIC = {"hypertension_review", "t2dm_review_uncontrolled", "knee_osteoarthritis", "ckd_follow_up", "bph_lower_urinary_tract",
           "memory_concern", "ibs_pattern", "constipation_chronic", "psoriasis_plaques", "acne_vulgaris", "peripheral_neuropathy",
           "dyspnea_chronic_workup", "chronic_cough_gerd", "post_mi_review", "weight_gain_metabolic", "hearing_loss_tinnitus",
           "tension_headache_daily", "blurred_vision_gradual", "insomnia", "low_mood", "hypothyroid_symptoms"}
MALE_KEYS = {"bph_lower_urinary_tract"}
DESCRIPTORS = {"cough syrup", "moisturiser", "ors", "cranberry juice", "face wash", "ear drops", "a soothing cream",
               "coconut oil", "iron tablets", "vitamin d", "a soothing cream", "saline nasal spray", "nicotine patches",
               "folic acid", "melatonin", "zinc", "lactulose", "cream"}
VERBING = {"feeling", "getting", "losing", "putting", "needing", "using", "turning", "waking", "having", "wanting",
           "forgetting", "repeating", "misplacing", "passing", "going", "clearing", "coughing", "biting", "belching",
           "snoring", "sweating", "looking"}
CLASS = {"Atorvastatin": "statin", "Rosuvastatin": "statin", "Pantoprazole": "ppi", "Omeprazole": "ppi", "Esomeprazole": "ppi",
         "Metformin": "biguanide", "Glimepiride": "sulfonylurea", "Amlodipine": "ccb", "Telmisartan": "arb", "Losartan": "arb",
         "Ramipril": "acei", "Diclofenac": "nsaid", "Ibuprofen": "nsaid", "Naproxen": "nsaid", "Etoricoxib": "nsaid",
         "Mefenamic acid": "nsaid", "Cetirizine": "antihistamine", "Levocetirizine": "antihistamine", "Sertraline": "antidepressant",
         "Escitalopram": "antidepressant", "Propranolol": "betablocker", "Metoprolol": "betablocker", "Bisoprolol": "betablocker",
         "Aspirin": "antiplatelet", "Clopidogrel": "antiplatelet", "Levothyroxine": "thyroid", "Amoxicillin": "antibiotic",
         "Amoxicillin/clavulanic acid": "antibiotic", "Azithromycin": "antibiotic", "Doxycycline": "antibiotic",
         "Cephalexin": "antibiotic", "Clindamycin": "antibiotic", "Nitrofurantoin": "antibiotic", "Trimethoprim": "antibiotic",
         "Levofloxacin": "antibiotic", "Paracetamol": "paracetamol", "Prednisolone": "steroid", "Tamsulosin": "alpha-blocker",
         "Furosemide": "diuretic", "Spironolactone": "diuretic", "Lactulose": "laxative", "Ferrous sulfate": "iron",
         "Fluconazole": "antifungal", "Terbinafine": "antifungal", "Colchicine": "gout", "Allopurinol": "gout"}
EXCL = {"new_thirst_polyuria": {"dm"}, "hypothyroid_symptoms": {"hypothyroid"}, "fatigue_workup": {"hypothyroid", "anemia"},
        "anemia_symptoms": {"anemia"}, "hyperthyroid_symptoms": {"hypothyroid"}, "weight_gain_metabolic": set(),
        "early_pregnancy_checkup": {"osteopor"}, "heavy_periods": {"anemia"}}
EPISODIC = ("pain", "ache", "palpitation", "vertigo", "dizz", "lighthead", "cough", "wheez", "seizure", "shak", "cramp", "flush",
            "sweat", "itch", "diarrh", "vomit", "nausea", "paraesthesia", "tingling", "burning", "spasm", "tinnitus", "sneez",
            "heartburn", "urticaria", "tightness", "syncope", "dyspn", "regurgitation", "belching", "rigors", "fever", "chills",
            "hypoglyc", "panic", "stiffness", "numbness", "breathless", "swelling", "welts")
NOSEV = ("weight", "hair", "pallor", "jaundice", "dark urine", "pale stool", "mole", "lesion", "snoring", "scarring", "bruising",
         "nail", "foamy", "warmth", "redness", "erythema", "discharge", "clots", "haematuria", "irritab", "misplac", "repetitive",
         "reduced smell", "appetite", "word-finding", "pitting", "pits", "head bump", "hunger", "heat intolerance", "cold intolerance",
         "ringing", "glare", "hoarse", "recall", "memory", "forget", "lost", "ketotic", "cloudy")
SPOKEN_UNIT = {"mg": "milligrams", "g": "gram", "micrograms": "micrograms", "ml": "ml", "units": "units"}


def strip_art(p):
    return re.sub(r"^(a|an|some|the)\s+", "", p)


def kind_of(p):
    return "ger" if p.split()[0].lower() in VERBING else "noun"


def spoken_dose(d):
    if not d:
        return ""
    m = re.match(r"^([\d.]+)\s+(\w+)$", d)
    if m and m.group(2) in SPOKEN_UNIT:
        return f"{m.group(1)} {SPOKEN_UNIT[m.group(2)]}"
    return d


def dose_halve_double(d, rng):
    m = re.match(r"^([\d.]+)\s+(mg|micrograms)$", d or "")
    if not m:
        return None
    v = float(m.group(1))
    v2 = v * 2 if rng.random() < .5 or v < 5 else v / 2
    if v2 < 1 or (v2 == v):
        return None
    s = f"{v2:g}"
    return f"{s} {m.group(2)}"


def dur_obj(s):
    """'for three days' / 'until we review' -> object + spoken string."""
    sp = s.replace("ongoing", "long term")
    m = re.match(r"for (\w+) (day|days|week|weeks|month|months)", s)
    if m and m.group(1) in NUMW:
        u = m.group(2) if m.group(2).endswith("s") else m.group(2) + "s"
        return {"value": NUMW[m.group(1)], "unit": u, "normalized": f"{NUMW[m.group(1)]} {u}"}, sp
    return {"value": None, "unit": None, "normalized": sp}, sp


def wchoice(rng, pairs):
    tot = sum(w for _, w in pairs)
    r = rng.uniform(0, tot)
    for k, w in pairs:
        r -= w
        if r <= 0:
            return k
    return pairs[-1][0]


def quota_plan(master_seed=20260101):
    rng = random.Random(master_seed)
    specs = [s for s, n in SPEC_QUOTA for _ in range(n)]
    cpl = [c for c, n in CPLX_QUOTA for _ in range(n)]
    rng.shuffle(cpl)
    by_spec = {}
    for s, c in zip(specs, cpl):
        by_spec.setdefault(s, []).append(c)
    plan = []
    for s, cs in by_spec.items():
        profs = [p for p in PROFILES if p["spec"] == s]
        order = []
        while len(order) < len(cs):
            blk = profs[:]
            rng.shuffle(blk)
            order += blk
        for c, p in zip(cs, order):
            plan.append((s, c, p["key"]))
    rng.shuffle(plan)
    return plan


PROF = {p["key"]: p for p in PROFILES}


def pick_dur(rng, key):
    if key in ACUTE:
        pool = [d for d in DURATIONS if d[2] == "days" or d[0] in ("about a week", "one week", "two weeks", "about two weeks")]
    elif key in CHRONIC:
        pool = [d for d in DURATIONS if d[2] in ("months", "years") or d[0] in ("four weeks", "three weeks")]
    else:
        pool = [d for d in DURATIONS if d[2] in ("days", "weeks", "months")]
    return rng.choice(pool)


def make_blueprint(idx, spec, cplx, key, seed, attempt=0):
    rng = random.Random(seed * 100 + attempt)
    pr = PROF[key]
    ci = {"simple": 0, "moderate": 1, "complex": 2, "challenging": 3}[cplx]
    sex = "F" if spec == "Gynaecology" or key in ("early_pregnancy_checkup", "heavy_periods", "menopausal_symptoms") \
        else ("M" if key in MALE_KEYS else rng.choice("MF"))
    bp = dict(idx=idx, spec=spec, profile=key, complexity=cplx, seed=seed, attempt=attempt, sex=sex,
              style=rng.choice(["terse", "chatty", "anxious", "casual", "formal", "hesitant"]))
    if cplx == "simple":
        bp["style"] = rng.choice(["terse", "chatty", "casual", "formal"])
    combo = wchoice(rng, COMBOS[cplx])
    if cplx == "challenging" and rng.random() < .35:
        combo += "U"
    bp["combo"] = combo
    has = lambda k: k in combo
    # ---------------------------------------------------------- symptoms
    pool = [s for s in pr["syms"] if s[2] != "general"]
    n_sym = {0: rng.choice([1, 2]), 1: rng.choice([2, 3]), 2: rng.choice([3, 4]), 3: rng.choice([3, 3, 4])}[ci]
    primary = pr["syms"][0]
    chosen = [primary] + rng.sample(pr["syms"][1:], min(n_sym - 1, len(pr["syms"]) - 1))
    syms = []
    for si, s in enumerate(chosen):
        names = s[0].split("|")
        phrase = rng.choice(names)
        d = dict(phrase=phrase, name=strip_art(phrase), norm=s[1], cat=s[2], site=s[3], kind=kind_of(phrase),
                 status="present", dur=None, onset=None, sev=None, freq=None, aggr=[], relief=[], reporter="P",
                 uncertain_onset=False, assoc=None, role="current")
        if s[2] != "general":
            if rng.random() < (1.0 if si == 0 and ci == 0 else .85 if si == 0 else .6):
                if rng.random() < .22 and key not in CHRONIC and s[2] != "psychiatric":
                    d["onset"] = rng.choice(ONSETS)
                else:
                    d["dur"] = pick_dur(rng, key)
            lowname = (s[1] + " " + d["name"]).lower()
            if rng.random() < (.65 if si == 0 else .3) + .05 * ci and not any(k in lowname for k in NOSEV):
                d["sev"] = rng.choice(SEVS) if rng.random() < .7 else f"{rng.randint(3, 8)}/10"
            if rng.random() < (.45 if si == 0 else .2) + .05 * ci and any(k in lowname for k in EPISODIC):
                d["freq"] = rng.choice(FREQS)
            ag = [a for a in s[4].split(";") if a]
            rl = [a for a in s[5].split(";") if a]
            if ag and rng.random() < (.5 if si == 0 else .2):
                d["aggr"] = rng.sample(ag, min(len(ag), rng.choice([1, 2])))
            if rl and rng.random() < (.4 if si == 0 else .15):
                d["relief"] = rng.sample(rl, min(len(rl), rng.choice([1, 1, 2])))
        syms.append(d)
    if primary[2] == "general":
        syms[0]["cc_only"] = True
        syms[0]["dur"] = syms[0]["onset"] = syms[0]["sev"] = syms[0]["freq"] = None
    # association between primary and a noun secondary
    nouns = [i for i, s in enumerate(syms) if i > 0 and s["kind"] == "noun" and not s.get("cc_only")]
    if nouns and not syms[0].get("cc_only") and rng.random() < .35:
        syms[0]["assoc"] = rng.choice(nouns)
    bp["cc_by"] = "P"
    if (has("C") or has("F")) and rng.random() < .5:
        bp["cc_by"] = "C" if has("C") and (not has("F") or rng.random() < .6) else "F"
    # ---------------------------------------------------------- features
    feats = []
    if cplx == "moderate":
        for f, p in (("uncertain_dose", .15), ("prev_episode", .2), ("resolved_sym", .15), ("date_uncertain", .1)):
            if rng.random() < p:
                feats.append(f)
    elif cplx in ("complex", "challenging"):
        cands = ["med_discrepancy", "date_uncertain", "conflict", "prev_episode", "resolved_sym", "uncertain_dose",
                 "uncertain_allergy", "discontinued_med"]
        rng.shuffle(cands)
        need = 2 if cplx == "complex" else 3
        # a discrepancy / conflict is the signature of complex encounters
        if (has("C") or has("F") or has("N")) and rng.random() < .75:
            feats.append("med_discrepancy")
        if (has("C") or has("F")) and rng.random() < .5 and "conflict" not in feats:
            feats.append("conflict")
        for f in cands:
            if len(feats) >= need + (0 if cplx == "complex" else 1):
                break
            if f not in feats:
                feats.append(f)
        if cplx == "challenging":
            feats += ["interruptions", "incomplete_answers", "mixed_negation"]
            if "U" in combo:
                feats.append("unknown_speaker")
            if rng.random() < .6:
                feats.append("name_forgotten")
    if "conflict" in feats and not (has("C") or has("F")):
        feats.remove("conflict")
    bp["features"] = feats
    # resolved symptom
    if ("resolved_sym" in feats or "mixed_negation" in feats) and len(syms) >= 2:
        t = rng.randrange(1, len(syms))
        syms[t].update(status="resolved", dur=None, onset=None, sev=None, freq=None, aggr=[], relief=[], assoc=None)
        for s in syms:
            if s["assoc"] == t:
                s["assoc"] = None
    if "date_uncertain" in feats:
        t = rng.randrange(0, len(syms))
        if not syms[t].get("cc_only") and syms[t]["status"] == "present":
            syms[t].update(dur=None, onset=None, uncertain_onset=True)
        else:
            feats.remove("date_uncertain")
    if "prev_episode" in feats:
        syms.append(dict(phrase=syms[0]["phrase"], name=syms[0]["name"], norm=syms[0]["norm"], cat=syms[0]["cat"],
                         site=syms[0]["site"], kind=syms[0]["kind"], status="resolved", dur=None, onset=rng.choice(C.PREV_EPISODE),
                         sev=None, freq=None, aggr=[], relief=[], reporter="P", uncertain_onset=False, assoc=None, role="previous"))
        if syms[0].get("cc_only"):
            feats.remove("prev_episode")
            syms.pop()
    bp["syms"] = syms
    # ---------------------------------------------------------- negatives
    nneg = {0: rng.choice([2, 3]), 1: rng.choice([3, 4, 5]), 2: rng.choice([4, 5, 6]), 3: rng.choice([5, 6])}[ci]
    sym_norms = {s["norm"].lower() for s in syms}
    negs = [n for n in pr["negs"] if n[1].lower() not in sym_norms]
    rng.shuffle(negs)
    negs = negs[:nneg]
    bp["negs"] = [list(n) for n in negs]
    bp["neg_dispute"] = None
    if "conflict" in feats:
        benign = [i for i, n in enumerate(negs) if n[1] in ("Fever", "Vomiting", "Diarrhoea", "Cough", "Rash", "Headache", "Nausea",
                                                              "Dizziness", "Chills", "Dysuria", "Constipation", "Palpitations", "Fatigue")]
        if benign:
            bp["neg_dispute"] = rng.choice(benign)
        else:
            feats.remove("conflict")
    ros_n = {0: 0, 1: rng.choice([0, 1]), 2: rng.choice([1, 2]), 3: rng.choice([1, 2])}[ci]
    cats = {s["cat"] for s in syms}
    ros = [r for r in __import__("dialogue_pools").ROS_POOL if r[1] not in cats]
    rng.shuffle(ros)
    bp["ros"] = [r[0] for r in ros[:ros_n]]
    # ---------------------------------------------------------- history
    excl = set(EXCL.get(key, set())) | ({"bph"} if sex == "F" else set())
    cond_keys = [k for k in dict.fromkeys(pr["conds"]) if k not in excl]
    npmh = {0: rng.choice([0, 0, 1]), 1: rng.choice([1, 1, 2]), 2: rng.choice([2, 2, 3]), 3: rng.choice([2, 3, 4])}[ci]
    others = [k for k in COND if k not in cond_keys and k not in ("ckd",) and k not in excl]
    keys = []
    for k in rng.sample(cond_keys, min(len(cond_keys), npmh)):
        keys.append(k)
    while len(keys) < npmh and others:
        k = rng.choice(others)
        others.remove(k)
        keys.append(k)
    # coherence: don't give a hypothyroid patient 'hyperthyroid' etc (not in pool); avoid copd+asthma both
    if "copd" in keys and "asthma" in keys:
        keys.remove("asthma")
    if key in ("hypothyroid_symptoms",) and "hypothyroid" in keys and rng.random() < .5:
        pass
    pmh = []
    for k in keys:
        phrase, norm, meds = COND[k]
        d = None
        if rng.random() < .5:
            d = rng.choice([x for x in DURATIONS if x[2] == "years"] + [("about ten years", 10, "years", "about 10 years"), ("five years", 5, "years", "5 years")])
        pmh.append(dict(key=k, cond=phrase, norm=norm, dur=d, reporter="P"))
    bp["pmh"] = pmh
    bp["pmh_none"] = not pmh
    bp["conds_confirmed"] = [i for i, p in enumerate(pmh) if rng.random() < (.45 if ci >= 1 else .3)][:2]
    bp["surg"] = []
    if ci >= 1 and rng.random() < .5 or (ci == 0 and rng.random() < .15):
        bad = {"Caesarean section", "Hysterectomy"} if sex == "M" else set()
        if spec == "Gynaecology":
            bad |= {"Hysterectomy"}
        if key in ("hypothyroid_symptoms", "hyperthyroid_symptoms"):
            bad |= {"Thyroid surgery"}
        s = rng.choice([x for x in SURG if x[1] not in bad])
        bp["surg"].append(dict(phrase=s[0], proc=re.sub(r"^(my|a|an)\s+", "", s[0]), norm=s[1], when=s[2]))
        if s[1] in ("Coronary stenting", "Coronary artery bypass grafting") and "ihd" not in [q["key"] for q in pmh]:
            ph, nm, _ = COND["ihd"]
            pmh.append(dict(key="ihd", cond=ph, norm=nm, dur=None, reporter="P"))
            bp["pmh_none"] = False
    bp["surg_none"] = (not bp["surg"]) and rng.random() < .5
    bp["fam"] = []
    if rng.random() < (.25 + .15 * ci):
        for f in rng.sample(FAMILY, 1 if ci < 2 else rng.choice([1, 2])):
            m = re.search(r"(?:had|has|was) (?:an? )?(.*)$", f[0])
            bp["fam"].append(dict(spoken=f[0], cond=m.group(1), norm=f[1], rel=f[2]))
    bp["soc"] = []
    if rng.random() < (.3 + .12 * ci):
        cat_pick = rng.sample(["smoking", "alcohol"], rng.choice([1, 2]))
        for c in cat_pick:
            o = rng.choice([x for x in SOCIAL if x[0] == c])
            bp["soc"].append(dict(cat=o[0], status=o[1], spoken=o[2], desc=o[3], details=o[4]))
    # ---------------------------------------------------------- medications
    meds = []
    for p in pmh:
        opts = COND[p["key"]][2]
        if opts and rng.random() < .85:
            o = rng.choice(opts)
            meds.append(dict(name=o[0], generic=o[1], dose=o[2], freq=o[3], route=o[4], ind=o[5] if rng.random() < .4 else None, ind_all=o[5],
                             dur=None, status="currently_used", reporter="P", flags=[], source="chronic"))
    if pr["otc"] and rng.random() < (.45 + .1 * ci):
        o = rng.choice(pr["otc"])
        meds.append(dict(name=o[0], generic=o[1], dose=o[2], freq=o[3] if len(o) > 3 else None, route=None, ind=None, dur=None,
                         status="currently_used", reporter="P", flags=[], source="otc"))
    # unique names
    seen, m2 = set(), []
    for m in meds:
        if m["name"].lower() not in seen:
            seen.add(m["name"].lower())
            m2.append(m)
    meds = m2[:4]
    for m in meds:
        if rng.random() < .15 and ci >= 1:
            m["dur"] = rng.choice([x for x in DURATIONS if x[2] in ("months", "years")][:])
    for p in pmh:
        p["meds"] = [m["name"] for m in meds if m["source"] == "chronic"]
    # medication features
    def with_dose():
        return [m for m in meds if m["dose"] and m["status"] == "currently_used" and not m["flags"]]
    if "uncertain_dose" in feats:
        c = with_dose()
        if c:
            rng.choice(c)["flags"].append("dose_uncertain")
        else:
            feats.remove("uncertain_dose")
    if "med_discrepancy" in feats:
        c = [m for m in with_dose() if dose_halve_double(m["dose"], rng)]
        who = [k for k in "CFN" if k in combo]
        if c and who:
            m = rng.choice(c)
            m["flags"].append("discrepancy")
            m["dose2"] = dose_halve_double(m["dose"], rng)
            m["other"] = rng.choice(who)
        else:
            feats.remove("med_discrepancy")
    if "name_forgotten" in feats:
        c = [m for m in meds if m["source"] == "chronic" and not m["flags"] and m["route"] == "oral"
             and m["name"].lower() not in DESCRIPTORS and m.get("ind_all")]
        if c:
            m = rng.choice(c)
            m["flags"].append("name_forgotten")
            m["desc"] = rng.choice(["small white one", "little pink tablet", "round yellow one"])
            m["ind"] = m.get("ind_all")
        else:
            feats.remove("name_forgotten")
    if "discontinued_med" in feats:
        have = {m["name"].lower() for m in meds}
        alts = [o for p_ in pmh for o in COND[p_["key"]][2] if o[0].lower() not in have and o[1] not in [m["generic"] for m in meds]]
        o = rng.choice(alts) if alts else None
        if o:
            meds.append(dict(name=o[0], generic=o[1], dose=None, freq=None, route=None, ind=None, dur=None,
                             status="discontinued", reporter="P", flags=[], source="chronic"))
        else:
            feats.remove("discontinued_med")
    # who reports medications when a carer/relative is present
    for k in "CF":
        if k in combo and meds and rng.random() < .6 and not any(m["flags"] for m in meds):
            for m in meds:
                m["reporter"] = k
            break
    bp["meds"] = meds
    bp["meds_none"] = not meds
    # ---------------------------------------------------------- allergies
    av = set()
    al = dict(kind="none", items=[])
    r = rng.random()
    if "uncertain_allergy" in feats:
        al = dict(kind="uncertain", items=[dict(sub="antibiotic", norm="Antibiotic (unspecified)", type="medication")])
    elif r < (.35 + .05 * ci):
        for a in rng.sample(ALLERGY, 1 if ci < 2 or rng.random() < .6 else 2):
            rx_ = rng.choice(a[3]) if rng.random() < .8 else None
            al["items"].append(dict(sub=a[0], norm=a[1], type=a[2], reaction=rx_))
            if a[0] in ALLERGY_AVOID:
                av.add(ALLERGY_AVOID[a[0]])
        al["kind"] = "known"
    bp["allergies"] = al
    # ---------------------------------------------------------- vitals
    wants_vit = rng.random() < ([.4, .75, .85, .8][ci])
    if "N" in combo:
        wants_vit = True
    bp["vitals_by"] = "N" if "N" in combo else "D"
    vit = None
    if wants_vit:
        rg = VITAL_BIAS[pr["vit"]]
        sbp, dbp = rng.randint(*rg[0]), rng.randint(*rg[1])
        dbp = min(dbp, sbp - 28)
        vit = [("Blood pressure", "Blood pressure", f"{sbp}/{dbp}", "mmHg"),
               ("Heart rate", "Heart rate", rng.randint(*rg[2]), "bpm")]
        if rng.random() < .8:
            vit.append(("Temperature", "Body temperature", round(rng.uniform(*rg[4]), 1), "°C"))
        if rng.random() < .75 or pr["spec"] == "Respiratory Medicine":
            vit.append(("Oxygen saturation", "Oxygen saturation", rng.randint(*rg[5]), "%"))
        if rng.random() < .4 or pr["spec"] == "Respiratory Medicine":
            vit.append(("Respiratory rate", "Respiratory rate", rng.randint(*rg[3]), "breaths/min"))
        if rng.random() < (.55 if pr["spec"] == "Endocrinology" else .15):
            w, h = rng.randint(52, 98), rng.randint(150, 186)
            vit.append(("Weight", "Body weight", w, "kg"))
            vit.append(("Height", "Body height", h, "cm"))
            if rng.random() < .7:
                vit.append(("BMI", "Body mass index", round(w / (h / 100) ** 2, 1), "kg/m²"))
        rng.shuffle(vit)
    bp["vitals"] = vit
    # ---------------------------------------------------------- exam
    ex = []
    if rng.random() < ([.55, .9, .95, .9][ci]) and pr["exam"]:
        ex = rng.sample(pr["exam"], min(len(pr["exam"]), rng.choice([1, 2]) if ci < 2 else rng.choice([2, 3])))
    bp["exam"] = [dict(stmt=e[0], findings=[list(f) for f in e[1]]) for e in ex]
    # drop denied findings that overlap (by content word) with anything positive in the scenario
    gen = {"pain", "swelling", "absent", "present", "normal", "history", "recent", "chest", "abdominal"}
    def toks(t):
        return {w for w in re.findall(r"[a-z]{5,}", t.lower()) if w not in gen}
    pos = set()
    for e in bp["exam"]:
        for f in e["findings"]:
            if f[3] == "present":
                pos |= toks(f[1])
    for s_ in syms:
        pos |= toks(s_["norm"]) | toks(s_["name"])
    for p_ in pmh:
        pos |= toks(p_["norm"])
    disp = bp["negs"][bp["neg_dispute"]][0] if bp["neg_dispute"] is not None else None
    bp["negs"] = [n for n in bp["negs"] if not (toks(n[1]) & pos) or n[0] == disp]
    if disp is not None:
        ix = [i for i, n in enumerate(bp["negs"]) if n[0] == disp]
        bp["neg_dispute"] = ix[0] if ix else None
        if bp["neg_dispute"] is None:
            feats.remove("conflict")
    # ---------------------------------------------------------- assessment / plan
    a = rng.choice(pr["assess"])
    nd = {0: 0, 1: rng.choice([0, 1]), 2: 1, 3: rng.choice([1, 2])}[ci]
    bp["assess"] = dict(primary=a[0], diffs=rng.sample(a[1], min(nd, len(a[1]))))
    inv_n = {0: 1, 1: rng.choice([1, 2]), 2: rng.choice([2, 3]), 3: rng.choice([2, 3])}[ci]
    invs = rng.sample(pr["inv"], min(inv_n, len(pr["inv"]))) if pr["inv"] else []
    inv_list = []
    for iv in invs:
        d = dict(name=iv[0], norm=iv[1], type=iv[2], ind=iv[3], status="planned", sched=None, prev_when=None, done_by=None)
        if iv[0] in pr["today"] and "N" in combo and rng.random() < .65:
            d["status"], d["done_by"] = "completed", "N"
        inv_list.append(d)
    if ci >= 2 and pr["inv"] and rng.random() < .22:
        c = [iv for iv in pr["inv"] if iv[2] in ("imaging", "laboratory", "cardiac") and iv[0] not in [x["name"] for x in inv_list]]
        if c:
            iv = rng.choice(c)
            inv_list.append(dict(name=iv[0], norm=iv[1], type=iv[2], ind=iv[3], status="completed", sched=None,
                                 prev_when=rng.choice(["last month", "a few months ago", "last year"]), done_by="P"))
    if "S" in combo:
        pl = [i for i in inv_list if i["status"] == "planned"]
        if not pl and pr["inv"]:
            iv = pr["inv"][0]
            inv_list.append(dict(name=iv[0], norm=iv[1], type=iv[2], ind=iv[3], status="planned", sched=None, prev_when=None, done_by=None))
            pl = [inv_list[-1]]
        if pl:
            pl[0]["sched"] = (rng.choice(C.WEEKDAYS), rng.choice(["9 am", "10 am", "11:30 am", "2 pm", "3:30 pm"]))
    bp["inv"] = inv_list
    avoid = set(av)
    if any(p["key"] == "ckd" for p in pmh) or any(p["key"] == "af" for p in pmh):
        avoid.add("nsaid")
    if key == "ckd_follow_up" or key == "early_pregnancy_checkup":
        avoid.add("nsaid")
    cur_generics = {m["generic"].lower() for m in meds}
    beta = any(p["key"] == "asthma" for p in pmh) or key == "asthma_flare"
    cur_classes = {CLASS.get(m["generic"]) for m in meds if m["status"] == "currently_used"} - {None}
    rx_ok = [r for r in pr["rx"] if (r[7] not in avoid) and r[1].lower() not in cur_generics and CLASS.get(r[1]) not in cur_classes
             and not (beta and r[1] in ("Propranolol", "Metoprolol"))]
    nrx = {0: 1, 1: rng.choice([1, 2]), 2: rng.choice([1, 2]), 3: rng.choice([2, 2, 3])}[ci]
    # never prescribe two drugs of the same generic
    rxs, seen_ind = [], set()
    cand = rx_ok[:]
    rng.shuffle(cand)
    for r_ in cand:
        if r_[6] in seen_ind or len(rxs) >= nrx:
            continue
        if CLASS.get(r_[1]) in {CLASS.get(x[1]) for x in rxs} - {None}:
            continue
        seen_ind.add(r_[6])
        rxs.append(r_)
    bp["rx"] = [dict(name=r[0], generic=r[1], dose=r[2], route=r[3], freq=r[4], dur=r[5], ind=r[6]) for r in rxs]
    cn = rng.sample(pr["counsel"], min(len(pr["counsel"]), rng.choice([1, 2]))) if pr["counsel"] else []
    extra = rng.sample(C.COUNSEL, rng.choice([1, 2]) if ci >= 1 else 1)
    bp["counsel"] = [list(c) for c in cn] + [list(c) for c in extra]
    if "smoking" in " ".join(c[1].lower() for c in bp["counsel"]) and not any(s["cat"] == "smoking" for s in bp["soc"]):
        bp["counsel"] = [c for c in bp["counsel"] if "smoking" not in c[1].lower()]
    bp["refs"] = [list(r) for r in pr["refs"]] if pr["refs"] and rng.random() < .55 else []
    bp["fu"] = rng.choice(pr["fu"])
    bp["red"] = pr["red"]
    bp["bring_rx"] = "med_discrepancy" in feats or "uncertain_dose" in feats
    bp["features"] = feats
    bp["target_sec"] = int(rng.gauss([335, 395, 430, 455][ci], 38))
    bp["target_sec"] = max(305, min(520, bp["target_sec"]))
    return bp
