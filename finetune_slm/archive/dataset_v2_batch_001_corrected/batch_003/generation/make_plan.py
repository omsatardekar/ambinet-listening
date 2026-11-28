"""Build the Batch 002 scenario plan (500 entries, ids 00501-01000).  Deterministic (seed 20261118).
Each entry fixes the situation, speakers, which label sections should be rich / sparse / absent, and special uncertainty features.
The plan constrains *what information exists*, the author decides *how it is said*.  Not evaluation data."""
import json
import random
from pathlib import Path
from situations import SITUATIONS, SPEC_COUNTS

HERE = Path(__file__).resolve().parent
rng = random.Random(20261118)

KINDS = [  # (kind, weight, description)
    ("sparse_single", 13, "single complaint, brief advice; most label sections empty"),
    ("minimal_followup", 4, "short routine/results visit with very few entities"),
    ("medication_focused", 9, "existing prescription, adherence/side effects/dose; few or no new symptoms"),
    ("medication_review", 4, "structured review of several medicines; little else"),
    ("allergy_focused", 6, "allergy / past drug reaction is a main topic; medication list may be absent"),
    ("chronic_followup", 12, "chronic condition review; some symptoms ongoing, some resolved"),
    ("acute_consult", 12, "new acute problem, focused history"),
    ("emergency", 6, "urgent assessment, quick history, decisive actions"),
    ("preventive_check", 6, "routine/preventive consult, few or no symptoms"),
    ("post_treatment", 6, "follow-up after treatment/procedure/admission"),
    ("caregiver_assisted", 0, "caregiver or family member supplies part of the history (assigned by speakers)"),
    ("staff_interaction", 0, "nurse and/or clinical staff do real work (vitals, booking)"),
    ("complex", 12, "multiple symptoms, history, medicines, allergy information, vitals, exam, assessment, follow-up"),
]
KIND_W = [(k, w) for k, w, _ in KINDS if w]
KIND_DESC = {k: d for k, _, d in KINDS}

STYLES_PATIENT = ["terse, answers in few words", "chatty, adds side stories", "anxious, asks worried questions", "vague, uses everyday words for symptoms",
                  "precise, brings notes or a symptom diary", "forgetful, corrects themselves", "stoic, downplays problems", "hesitant, trails off, needs prompting",
                  "talkative but disorganised, jumps between topics", "polite and formal", "impatient, short on time"]
STYLES_DOCTOR = ["warm, unhurried", "brisk and efficient", "thorough, explains reasoning", "plain-spoken, uses analogies", "asks open questions, lets silences sit",
                 "reassuring, repeats key points back", "direct, lists options", "curious, follows tangents briefly"]
DIALECT = ["British English", "British English", "British English", "North American English", "North American English", "Indian English", "Australian English", "Irish English"]
OPENERS = ["patient speaks first", "doctor greets by checking the name", "nurse brings the patient in and hands over briefly", "doctor refers to the previous visit or a letter",
           "patient apologises for being late", "patient jumps straight into the problem", "doctor asks how the patient prefers to be addressed", "small talk about weather/parking first",
           "caregiver speaks first (if present), otherwise patient answers with a question", "doctor starts with the reason noted on the booking"]


def pick(w):
    r = rng.uniform(0, sum(x for _, x in w))
    for k, x in w:
        r -= x
        if r <= 0:
            return k
    return w[-1][0]


def speakers_for(kind, spec):
    """returns list of roles (besides always DOCTOR and PATIENT)"""
    extra = []
    if spec == "Pediatrics":
        extra.append(pick([("FAMILY_MEMBER", 85), ("CAREGIVER", 15)]))
    elif spec == "Geriatrics":
        r = rng.random()
        extra.append("CAREGIVER" if r < .5 else "FAMILY_MEMBER" if r < .8 else None)
    elif kind == "caregiver_assisted":
        extra.append(pick([("CAREGIVER", 55), ("FAMILY_MEMBER", 45)]))
    elif kind == "staff_interaction":
        extra.append(pick([("NURSE", 60), ("CLINICAL_STAFF", 20), ("BOTH", 20)]))
    elif kind in ("emergency",):
        extra.append(pick([("NURSE", 60), (None, 25), ("FAMILY_MEMBER", 15)]))
    else:
        extra.append(pick([(None, 62), ("NURSE", 14), ("CLINICAL_STAFF", 7), ("FAMILY_MEMBER", 9), ("CAREGIVER", 8)]))
    out = []
    for e in extra:
        if e == "BOTH":
            out += ["NURSE", "CLINICAL_STAFF"]
        elif e:
            out.append(e)
    # extra third parties
    if out and rng.random() < .22:
        cand = [r for r in ("NURSE", "CLINICAL_STAFF", "FAMILY_MEMBER", "CAREGIVER") if r not in out]
        if "CAREGIVER" in out and "FAMILY_MEMBER" in cand and rng.random() < .5:
            cand = ["FAMILY_MEMBER", "NURSE"]
        out.append(rng.choice(cand))
    return out


def count(w):
    return pick(list(w.items()))


TABLE = {  # per-kind distributions of section targets: values are {n: weight}
    "sparse_single": dict(sym={1: 70, 2: 30}, neg={0: 45, 1: 35, 2: 20}, meds={"none": 80, "existing1": 14, "planned1": 6}, allergy={"not_discussed": 90, "explicit_none": 6, "reported": 4},
                          vit={"none": 80, "few": 15, "full": 5}, exam={0: 55, 1: 35, 2: 10}, ros={0: 85, 1: 15}, pmh={0: 70, 1: 30}, surg={0: 94, 1: 6}, fam={0: 92, 1: 8}, soc={0: 70, 1: 30},
                          assess={"none": 55, "provisional": 35, "differential": 10}, inv={0: 70, 1: 25, 2: 5}, fu={"none": 45, "conditional": 40, "planned": 15}),
    "minimal_followup": dict(sym={0: 45, 1: 45, 2: 10}, neg={0: 60, 1: 30, 2: 10}, meds={"none": 55, "existing1": 30, "existing2": 15}, allergy={"not_discussed": 92, "explicit_none": 8},
                             vit={"none": 55, "few": 35, "full": 10}, exam={0: 55, 1: 35, 2: 10}, ros={0: 90, 1: 10}, pmh={0: 55, 1: 35, 2: 10}, surg={0: 95, 1: 5}, fam={0: 95, 1: 5}, soc={0: 75, 1: 25},
                             assess={"none": 55, "provisional": 45}, inv={0: 55, 1: 35, 2: 10}, fu={"none": 30, "planned": 55, "conditional": 15}),
    "medication_focused": dict(sym={0: 35, 1: 40, 2: 25}, neg={0: 35, 1: 35, 2: 20, 3: 10}, meds={"existing1": 35, "existing2": 40, "existing3": 25}, allergy={"not_discussed": 85, "explicit_none": 10, "reported": 5},
                               vit={"none": 55, "few": 35, "full": 10}, exam={0: 60, 1: 30, 2: 10}, ros={0: 80, 1: 20}, pmh={1: 50, 2: 35, 3: 15}, surg={0: 90, 1: 10}, fam={0: 90, 1: 10}, soc={0: 70, 1: 25, 2: 5},
                               assess={"none": 55, "provisional": 40, "differential": 5}, inv={0: 55, 1: 35, 2: 10}, fu={"none": 25, "planned": 60, "conditional": 15}),
    "medication_review": dict(sym={0: 55, 1: 35, 2: 10}, neg={0: 45, 1: 35, 2: 20}, meds={"existing3": 40, "existing4": 40, "existing5": 20}, allergy={"not_discussed": 70, "explicit_none": 15, "reported": 10, "reported_unknown_reaction": 5},
                              vit={"none": 40, "few": 40, "full": 20}, exam={0: 65, 1: 30, 2: 5}, ros={0: 85, 1: 15}, pmh={2: 50, 3: 40, 4: 10}, surg={0: 85, 1: 15}, fam={0: 90, 1: 10}, soc={0: 60, 1: 30, 2: 10},
                              assess={"none": 70, "provisional": 30}, inv={0: 50, 1: 35, 2: 15}, fu={"none": 30, "planned": 60, "conditional": 10}),
    "allergy_focused": dict(sym={0: 20, 1: 50, 2: 30}, neg={0: 30, 1: 40, 2: 30}, meds={"none": 35, "existing1": 25, "existing2": 15, "planned1": 25}, allergy={"reported": 40, "reported_unknown_reaction": 15, "historical": 20, "uncertain": 15, "explicit_none": 10},
                            vit={"none": 55, "few": 30, "full": 15}, exam={0: 45, 1: 40, 2: 15}, ros={0: 80, 1: 20}, pmh={0: 40, 1: 40, 2: 20}, surg={0: 90, 1: 10}, fam={0: 85, 1: 15}, soc={0: 70, 1: 30},
                            assess={"none": 40, "provisional": 45, "differential": 15}, inv={0: 60, 1: 35, 2: 5}, fu={"none": 35, "planned": 40, "conditional": 25}),
    "chronic_followup": dict(sym={1: 25, 2: 40, 3: 30, 4: 5}, neg={0: 15, 1: 30, 2: 30, 3: 25}, meds={"existing1": 20, "existing2": 40, "existing3": 40}, allergy={"not_discussed": 70, "explicit_none": 15, "reported": 10, "historical": 5},
                             vit={"none": 25, "few": 35, "full": 40}, exam={0: 35, 1: 40, 2: 25}, ros={0: 55, 1: 35, 2: 10}, pmh={1: 25, 2: 45, 3: 30}, surg={0: 75, 1: 25}, fam={0: 70, 1: 30}, soc={0: 30, 1: 35, 2: 25, 3: 10},
                             assess={"none": 25, "provisional": 55, "differential": 10, "both": 10}, inv={0: 30, 1: 40, 2: 25, 3: 5}, fu={"none": 15, "planned": 70, "conditional": 15}),
    "acute_consult": dict(sym={1: 30, 2: 40, 3: 25, 4: 5}, neg={0: 15, 1: 25, 2: 35, 3: 25}, meds={"none": 40, "existing1": 25, "planned1": 20, "planned2": 15}, allergy={"not_discussed": 62, "explicit_none": 20, "reported": 12, "historical": 6},
                          vit={"none": 25, "few": 40, "full": 35}, exam={0: 20, 1: 45, 2: 30, 3: 5}, ros={0: 65, 1: 30, 2: 5}, pmh={0: 30, 1: 40, 2: 30}, surg={0: 80, 1: 20}, fam={0: 80, 1: 20}, soc={0: 40, 1: 40, 2: 20},
                          assess={"none": 25, "provisional": 50, "differential": 15, "both": 10}, inv={0: 30, 1: 40, 2: 25, 3: 5}, fu={"none": 25, "planned": 35, "conditional": 40}),
    "emergency": dict(sym={1: 20, 2: 40, 3: 30, 4: 10}, neg={0: 10, 1: 30, 2: 35, 3: 25}, meds={"none": 35, "existing1": 25, "existing2": 20, "planned1": 20}, allergy={"not_discussed": 45, "explicit_none": 30, "reported": 18, "uncertain": 7},
                      vit={"few": 25, "full": 75}, exam={1: 35, 2: 45, 3: 20}, ros={0: 80, 1: 20}, pmh={0: 30, 1: 40, 2: 30}, surg={0: 75, 1: 25}, fam={0: 85, 1: 15}, soc={0: 55, 1: 35, 2: 10},
                      assess={"none": 25, "provisional": 45, "differential": 20, "both": 10}, inv={1: 35, 2: 40, 3: 25}, fu={"none": 40, "planned": 25, "conditional": 35}),
    "preventive_check": dict(sym={0: 55, 1: 35, 2: 10}, neg={0: 20, 1: 30, 2: 30, 3: 20}, meds={"none": 50, "existing1": 30, "existing2": 20}, allergy={"not_discussed": 75, "explicit_none": 20, "reported": 5},
                             vit={"none": 15, "few": 35, "full": 50}, exam={0: 40, 1: 40, 2: 20}, ros={0: 40, 1: 40, 2: 20}, pmh={0: 30, 1: 40, 2: 30}, surg={0: 70, 1: 30}, fam={0: 50, 1: 35, 2: 15}, soc={1: 30, 2: 40, 3: 30},
                             assess={"none": 70, "provisional": 30}, inv={0: 25, 1: 40, 2: 30, 3: 5}, fu={"none": 30, "planned": 60, "conditional": 10}),
    "post_treatment": dict(sym={0: 20, 1: 40, 2: 30, 3: 10}, neg={0: 20, 1: 35, 2: 30, 3: 15}, meds={"existing1": 30, "existing2": 40, "existing3": 20, "none": 10}, allergy={"not_discussed": 75, "explicit_none": 10, "reported": 10, "historical": 5},
                           vit={"none": 30, "few": 35, "full": 35}, exam={0: 25, 1: 45, 2: 30}, ros={0: 70, 1: 25, 2: 5}, pmh={1: 40, 2: 40, 3: 20}, surg={0: 50, 1: 50}, fam={0: 90, 1: 10}, soc={0: 55, 1: 35, 2: 10},
                           assess={"none": 35, "provisional": 50, "differential": 15}, inv={0: 30, 1: 45, 2: 20, 3: 5}, fu={"none": 20, "planned": 65, "conditional": 15}),
    "caregiver_assisted": dict(sym={1: 20, 2: 40, 3: 30, 4: 10}, neg={0: 15, 1: 30, 2: 35, 3: 20}, meds={"none": 15, "existing1": 25, "existing2": 30, "existing3": 30}, allergy={"not_discussed": 55, "explicit_none": 10, "reported": 14, "historical": 5, "uncertain": 8, "disputed": 10},
                               vit={"none": 25, "few": 35, "full": 40}, exam={0: 25, 1: 45, 2: 30}, ros={0: 65, 1: 30, 2: 5}, pmh={1: 25, 2: 45, 3: 30}, surg={0: 65, 1: 35}, fam={0: 70, 1: 30}, soc={0: 30, 1: 40, 2: 30},
                               assess={"none": 25, "provisional": 50, "differential": 15, "both": 10}, inv={0: 35, 1: 40, 2: 20, 3: 5}, fu={"none": 20, "planned": 50, "conditional": 30}),
    "staff_interaction": dict(sym={1: 25, 2: 40, 3: 30, 4: 5}, neg={0: 15, 1: 30, 2: 35, 3: 20}, meds={"none": 20, "existing1": 25, "existing2": 25, "planned1": 15, "existing3": 15}, allergy={"not_discussed": 55, "explicit_none": 20, "reported": 15, "uncertain": 10},
                              vit={"few": 25, "full": 75}, exam={0: 30, 1: 45, 2: 25}, ros={0: 65, 1: 30, 2: 5}, pmh={0: 25, 1: 40, 2: 35}, surg={0: 75, 1: 25}, fam={0: 80, 1: 20}, soc={0: 40, 1: 40, 2: 20},
                              assess={"none": 25, "provisional": 50, "differential": 15, "both": 10}, inv={0: 25, 1: 40, 2: 30, 3: 5}, fu={"none": 20, "planned": 55, "conditional": 25}),
    "complex": dict(sym={3: 40, 4: 40, 5: 20}, neg={2: 25, 3: 35, 4: 25, 5: 15}, meds={"existing2": 25, "existing3": 35, "existing4": 20, "planned1": 10, "planned2": 10}, allergy={"reported": 45, "reported_unknown_reaction": 10, "historical": 10, "explicit_none": 20, "uncertain": 10, "disputed": 5},
                    vit={"full": 85, "few": 15}, exam={2: 45, 3: 40, 4: 15}, ros={1: 60, 2: 40}, pmh={2: 40, 3: 40, 4: 20}, surg={1: 70, 2: 30}, fam={1: 60, 2: 40}, soc={2: 30, 3: 40, 4: 30},
                    assess={"provisional": 45, "differential": 20, "both": 35}, inv={2: 40, 3: 40, 4: 20}, fu={"planned": 70, "conditional": 30}),
}
FEATURES = ["date_uncertain", "uncertain_dose", "adherence_uncertain", "incomplete_medication_name", "allergy_uncertain", "duration_disagreement",
            "conflicting_statement", "medication_discrepancy", "allergy_disputed", "unknown_speaker"]
FEATURE_NOTE = {
    "date_uncertain": "a speaker cannot say when one symptom began (symptom certainty uncertain)",
    "uncertain_dose": "a speaker gives a dose tentatively ('maybe 20 mg') for a medicine; dose recorded as stated and flagged",
    "adherence_uncertain": "prescribed frequency stated but someone says doses are missed / is unsure it is taken as prescribed (e.g. patient says regularly, caregiver says often missed: keep both statements)",
    "incomplete_medication_name": "a speaker cannot name a medicine (describes its appearance/purpose); name = the description, generic/normalized null",
    "allergy_uncertain": "a possible allergy with no nameable substance and/or reaction",
    "duration_disagreement": "patient and third party give different durations for the same symptom; summarised as an approximate range (value null)",
    "conflicting_statement": "patient denies a symptom, caregiver/family reports it (symptom certainty 'disputed', reported_by third party, patient denial in negative_findings)",
    "medication_discrepancy": "two sources give different doses for the same current medicine; dose null",
    "allergy_disputed": "patient denies allergies, caregiver/family recalls a possible reaction; both kept",
    "unknown_speaker": "one utterance could not be attributed (role UNKNOWN, e.g. a voice from the doorway / unclear who answered) and concerns a symptom",
}


def features_for(kind, roles, meds, allergy):
    third = [r for r in roles if r in ("CAREGIVER", "FAMILY_MEMBER")]
    nurse = "NURSE" in roles
    p = {"sparse_single": .12, "minimal_followup": .1, "medication_focused": .45, "medication_review": .5, "allergy_focused": .35, "chronic_followup": .4,
         "acute_consult": .3, "emergency": .2, "preventive_check": .15, "post_treatment": .3, "caregiver_assisted": .6, "staff_interaction": .35, "complex": .55}[kind]
    if third:
        p = max(p, .55)
    out = []
    if rng.random() > p:
        return out
    has_med = meds.startswith("existing") or meds.startswith("planned")
    cand = [("date_uncertain", 3)]
    if has_med:
        cand += [("uncertain_dose", 3), ("adherence_uncertain", 3), ("incomplete_medication_name", 1.5)]
        if meds.startswith("existing") and (third or nurse):
            cand += [("medication_discrepancy", 2)]
    if allergy == "uncertain":
        out.append("allergy_uncertain")
    if allergy == "disputed":
        out.append("allergy_disputed")
    elif third and allergy in ("not_discussed", "explicit_none") and rng.random() < .15:
        pass  # disputed allergies are planned through the allergy target, never added late
    if third:
        cand += [("duration_disagreement", 2.5), ("conflicting_statement", 2.5)]
    if rng.random() < .08:
        cand += [("unknown_speaker", 3)]
    n = 1 if rng.random() < .65 else 2 if rng.random() < .8 else 3
    for _ in range(n):
        c = [x for x in cand if x[0] not in out]
        if not c:
            break
        out.append(pick(c))
    if third and kind == "caregiver_assisted" and not [f for f in out if f in ("adherence_uncertain", "duration_disagreement", "conflicting_statement", "medication_discrepancy", "allergy_disputed")] and rng.random() < .5:
        out.append("duration_disagreement" if "duration_disagreement" not in out else "conflicting_statement")
    return out


def build():
    # situation list: each specialty's list consumed exactly once
    slots = []
    for spec, n in SPEC_COUNTS.items():
        sits = list(SITUATIONS[spec])
        assert len(sits) == n, spec
        for s in sits:
            slots.append((spec, s))
    rng.shuffle(slots)
    plan = []
    for i, (spec, sit) in enumerate(slots):
        eid = f"{501 + i:05d}"
        kind = pick(KIND_W)
        if spec == "Emergency Medicine" and rng.random() < .8:
            kind = "emergency"
        if spec == "Geriatrics" and kind in ("sparse_single", "preventive_check") and rng.random() < .5:
            kind = "caregiver_assisted"
        if spec == "Pediatrics" and kind == "complex":
            kind = "acute_consult"
        roles = speakers_for(kind, spec)
        if kind in ("sparse_single", "minimal_followup", "preventive_check") and "NURSE" in roles and rng.random() < .5:
            roles = [r for r in roles if r != "NURSE"] or []
        if any(r in roles for r in ("CAREGIVER", "FAMILY_MEMBER")) and kind not in ("complex", "emergency", "staff_interaction"):
            kind_eff = "caregiver_assisted" if kind in ("sparse_single", "acute_consult", "chronic_followup") and rng.random() < .5 else kind
        else:
            kind_eff = kind
        if kind_eff == "staff_interaction" and not ({"NURSE", "CLINICAL_STAFF"} & set(roles)):
            roles.append("NURSE")
        T = TABLE[kind_eff]
        sym, neg = count(T["sym"]), count(T["neg"])
        meds = pick(list(T["meds"].items()))
        allergy = pick(list(T["allergy"].items()))
        third = [r for r in roles if r in ("CAREGIVER", "FAMILY_MEMBER")]
        if allergy == "disputed" and not third:
            allergy = "reported"
        vit = pick(list(T["vit"].items()))
        vit_by = "NURSE" if ("NURSE" in roles and vit != "none" and rng.random() < .75) else "DOCTOR"
        ent = {"symptoms": sym, "negative_findings": neg, "medications": meds, "allergies": allergy, "vital_signs": vit, "vitals_read_aloud_by": vit_by if vit != "none" else None,
               "physical_examination": count(T["exam"]), "review_of_systems": count(T["ros"]),
               "past_medical_history": count(T["pmh"]), "surgical_history": count(T["surg"]), "family_history": count(T["fam"]), "social_history": count(T["soc"]),
               "clinical_assessment": pick(list(T["assess"].items())), "investigations": count(T["inv"]), "follow_up": pick(list(T["fu"].items()))}
        feats = features_for(kind_eff, roles, meds, allergy)
        for a_, f_ in (("uncertain", "allergy_uncertain"), ("disputed", "allergy_disputed")):
            if allergy == a_ and f_ not in feats:
                feats.append(f_)
        if "conflicting_statement" in feats and sym == 0:
            ent["symptoms"] = 1
        if "unknown_speaker" in feats and ent["symptoms"] == 0:
            ent["symptoms"] = 1
        if ("date_uncertain" in feats or "duration_disagreement" in feats) and ent["symptoms"] == 0:
            ent["symptoms"] = 1
        if feats and ent["negative_findings"] < 1 and "conflicting_statement" in feats:
            ent["negative_findings"] = 1
        if kind_eff in ("sparse_single", "minimal_followup"):
            turns = rng.randint(34, 42)
        elif kind_eff in ("complex",):
            turns = rng.randint(52, 74)
        elif kind_eff == "emergency":
            turns = rng.randint(38, 56)
        else:
            turns = rng.randint(36, 62)
        plan.append({"encounter_id": eid, "specialty": spec, "situation": sit, "kind": kind_eff, "kind_description": KIND_DESC[kind_eff],
                     "extra_speakers": roles, "entity_targets": ent, "special_features": feats,
                     "feature_notes": {f: FEATURE_NOTE[f] for f in feats}, "target_turns": turns,
                     "style": {"patient": rng.choice(STYLES_PATIENT), "doctor": rng.choice(STYLES_DOCTOR), "dialect": rng.choice(DIALECT), "opening": rng.choice(OPENERS)},
                     "patient_age": None})
    for p in plan:   # openings must not need a speaker the plan does not include
        o = p["style"]["opening"]
        if ("nurse" in o and "NURSE" not in p["extra_speakers"]) or ("caregiver speaks first" in o and not ({"CAREGIVER", "FAMILY_MEMBER"} & set(p["extra_speakers"]))):
            p["style"]["opening"] = "patient jumps straight into the problem" if "caregiver" in o else "doctor greets by checking the name"
    return plan


if __name__ == "__main__":
    plan = build()
    out = HERE / "plan"
    out.mkdir(exist_ok=True)
    (out / "scenario_plan.json").write_text(json.dumps(plan, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    import collections as C
    print(len(plan), "entries")
    print(C.Counter(p["kind"] for p in plan))
    print(C.Counter(tuple(sorted(p["extra_speakers"])) for p in plan).most_common())
    print("with features:", sum(1 for p in plan if p["special_features"]), C.Counter(f for p in plan for f in p["special_features"]))
    print("allergy:", C.Counter(p["entity_targets"]["allergies"] for p in plan))
    print("meds none:", sum(1 for p in plan if p["entity_targets"]["medications"] == "none"), "vitals none:", sum(1 for p in plan if p["entity_targets"]["vital_signs"] == "none"))
