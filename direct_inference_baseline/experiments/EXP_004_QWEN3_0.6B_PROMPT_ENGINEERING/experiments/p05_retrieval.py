"""EXP_004 P05: conservative retrieval of supporting transcript segments for already-extracted facts (library; ZERO inference; uses only the transcript and the extracted item - never labels).
Design (see reports/09_P05_architecture_and_diagnostics.md). Pipeline per fact:
  1 candidate generation: a segment is a candidate if, for at least one descriptive text field of the item, the IDF-weighted share of that field's content-word stems found in the segment >= TAU
     (field-wise max, so a spoken plain wording suffices when the standard term was not spoken); at least one matched stem must be 'specific' (rare in the encounter). NO fallback: no candidate -> abstain.
  2 question handling: a question line is context, never proof. A candidate question is replaced by its answer (the next non-question line of the other speaker); the question is kept only when the answer is a short reply
     that cannot be interpreted without it. A question with no usable answer is dropped.
  3 speaker class: the non-question evidence must be said by the speaker class that can state such a fact (calibrated on gold, see EXPECT_CLASS).
  4 polarity: a negative finding needs a negation cue in its evidence; any other fact is rejected when its anchor words are negated in the evidence.
  5 kinship: a family-history fact needs a kin term in its evidence; an own-history fact is rejected when the anchor sits in a kin clause ("my mother has ...") without a first-person marker.
  6 value: a vital sign with a numeric value needs those numbers in the evidence.
  7 ambiguity: all surviving candidates within BAND of the best score are cited (at most MAX_TIED); more than that -> abstain.
Every abstention carries a reason code. Parameters are module constants and are fixed before results are seen."""
from __future__ import annotations

import math
import re
from collections import Counter

from direct_inference_baseline.evaluation.entity_matching import KEYS, content_tokens, norm_text

STEM, TAU, SPEC_DF_ABS, SPEC_DF_REL, BAND, MAX_TIED, SHORT_ANSWER_WORDS = 5, 0.6, 3, 0.15, 0.05, 3, 10
CLIN = {"doctor", "nurse", "clinical_staff"}
PAT_SIDE = {"patient", "caregiver", "family_member"}
# expected speaker class of the NON-QUESTION evidence per category (None = any). Set from the gold rule-validity probe (analysis/p05_rule_validity_probe.json); see the design document.
EXPECT_CLASS: dict = {  # hard filter only where >= 95% of the gold non-question evidence has that class (prompt_dev gold probe): clinician 99-100%, patient side 95-100%; all other categories: any speaker
    "vital_signs": "clinician", "physical_examination": "clinician", "clinical_assessment": "clinician", "procedures_and_investigations": "clinician", "clinical_actions": "clinician", "follow_up": "clinician",
    "chief_complaint": "patient_side", "medical_history.surgical_history": "patient_side", "medical_history.family_history": "patient_side", "allergies": "patient_side", "review_of_systems": "patient_side",
    "negative_findings": "patient_side"}
NEG = {"no", "not", "never", "none", "nothing", "nobody", "without", "denies", "denied", "deny", "absent", "negative", "nil", "nope", "neither", "nor", "cannot", "cant"}
NEG_SUFFIX = ("n't",)
AFFIRM = {"yes", "yeah", "yep", "correct", "sometimes", "mhm", "sure", "right", "exactly"}
KIN = {"mother", "mom", "mum", "father", "dad", "brother", "sister", "sibling", "siblings", "parent", "parents", "grandmother", "grandfather", "grandma", "grandpa", "grandparent", "grandparents",
       "aunt", "uncle", "cousin", "son", "daughter", "child", "children", "wife", "husband", "family", "relatives", "relative"}
FIRST_PERSON = {"i", "my", "me", "myself", "ive", "i've", "im", "i'm"}
SMALLTALK = {"hello", "hi", "hey", "morning", "afternoon", "evening", "thanks", "thank", "welcome", "bye", "goodbye", "sit", "pleasure"}
QF = {"chief_complaint": ["value", "normalized_value"], "symptoms": ["name", "normalized_name", "body_site"], "negative_findings": ["finding", "normalized_name"],
      "medical_history.past_medical_history": ["condition", "normalized_condition"], "medical_history.surgical_history": ["procedure", "normalized_procedure"],
      "medical_history.family_history": ["condition", "normalized_condition"], "medical_history.social_history": ["category", "description", "details"],
      "medications": ["name", "normalized_name", "generic_name"], "allergies": ["substance", "normalized_substance", "reaction"], "vital_signs": ["name", "normalized_name"],
      "physical_examination": ["finding", "normalized_finding", "body_site"], "review_of_systems": ["system", "details"], "clinical_conditions": ["name", "normalized_name"],
      "clinical_assessment": ["assessment", "normalized_assessment"], "procedures_and_investigations": ["name", "normalized_name"], "clinical_actions": ["description"],
      "follow_up": ["time_reference"], "clinical_uncertainties": ["description"]}
OWN_HISTORY = {"symptoms", "medical_history.past_medical_history", "medical_history.surgical_history", "clinical_conditions", "chief_complaint"}
VITAL_SYN = {"blood pressure": [["press"]], "temperature": [["temp"]], "heart rate": [["pulse"], ["heart", "rate"]], "pulse": [["pulse"], ["heart", "rate"]], "oxygen saturation": [["satur"], ["spo"]],
             "respiratory rate": [["breath"], ["respirat"]], "weight": [["weigh"]], "height": [["tall"], ["heigh"]]}


def raw_tokens(text):
    return re.findall(r"[a-z0-9']+", str(text).lower().replace("’", "'"))


def has_neg(raw):
    return any(t in NEG or t.endswith(NEG_SUFFIX) for t in raw)


def has_kin(raw):
    return any(t in KIN for t in raw)


def stems_of(text):
    return list(dict.fromkeys(t[:STEM] for t in content_tokens(norm_text(text))))


def sm(stem, w):
    return w.startswith(stem) or (len(w) >= 4 and stem.startswith(w))


class Enc:
    def __init__(self, segs):
        self.segs, self.N = segs, len(segs)
        self.words = [norm_text(s["text"]).split() for s in segs]
        self.raw = [raw_tokens(s["text"]) for s in segs]
        self.role = [str(s["role"]).lower() for s in segs]
        self.q = [s["text"].strip().endswith("?") for s in segs]
        self.speaker = [s["speaker_id"] for s in segs]
        self._df = {}

    def df(self, st):
        if st not in self._df:
            self._df[st] = sum(any(sm(st, w) for w in ws) for ws in self.words)
        return self._df[st]

    def idf(self, st):
        return math.log(1 + self.N / max(1, self.df(st)))

    def specific(self, st):
        return 0 < self.df(st) <= max(SPEC_DF_ABS, math.ceil(SPEC_DF_REL * self.N))


def query_fields(cat, item):
    """field name -> list of anchor stems (several alternatives for vital-sign synonyms)."""
    out = {}
    for f in QF[cat]:
        v = item.get(f)
        if v not in (None, "") and not isinstance(v, (dict, list)):
            s = stems_of(str(v))
            if s:
                out[f] = s
    if cat == "vital_signs":
        phrase = norm_text(item.get("normalized_name") or item.get("name") or "")
        for key, alts in VITAL_SYN.items():
            if key in phrase:
                for n, a in enumerate(alts):
                    out[f"syn_{key}_{n}"] = a
    return out


def field_cov(enc, stems, i):
    """(IDF-weighted share of `stems` found in segment i, any matched stem specific?, matched stems)"""
    den = sum(enc.idf(s) for s in stems)
    m = [s for s in stems if any(sm(s, w) for w in enc.words[i])]
    return (sum(enc.idf(s) for s in m) / den if den else 0.0), any(enc.specific(s) for s in m), m


def anchor_negated(enc, i, matched):
    """True when a matched anchor word is preceded (within 6 tokens) or followed (within 2) by a negation cue in segment i."""
    raw = enc.raw[i]
    pos = [k for k, w in enumerate(raw) if any(w.startswith(s) or (len(w) >= 4 and s.startswith(w)) for s in matched)]
    for p in pos:
        if has_neg(raw[max(0, p - 6):p] + raw[p + 1:p + 3]):
            return True
    return False


def kin_conflict(enc, i, matched):
    """True when a kin term precedes a matched anchor within 6 tokens with no first-person marker in between (a statement about a relative)."""
    raw = enc.raw[i]
    pos = [k for k, w in enumerate(raw) if any(w.startswith(s) or (len(w) >= 4 and s.startswith(w)) for s in matched)]
    for p in pos:
        window = raw[max(0, p - 6):p]
        ks = [k for k, w in enumerate(window) if w in KIN]
        if ks and not any(w in FIRST_PERSON for w in window[ks[-1]:]):
            return True
    return False


def role_class(role):
    return "clinician" if role in CLIN else "patient_side" if role in PAT_SIDE else "other"


NEG_STATUS = {"absent", "negative", "never", "denied", "none", "no", "not_present", "not present"}


def item_negative(cat, item):
    """True when the extracted item itself states an absence/denial (status field or negation word in its own wording)."""
    if cat == "negative_findings":
        return True
    for f in ("status", "assertion"):
        v = str(item.get(f) or "").strip().lower()
        if v in NEG_STATUS or v.startswith("no ") or v.startswith("not "):
            return True
    txt = " ".join(str(item.get(f)) for f in QF[cat] if item.get(f) not in (None, "") and not isinstance(item.get(f), (dict, list)))
    return has_neg(raw_tokens(txt))


STEPS_ALL = ("specific", "qa", "speaker", "polarity", "kin", "value", "ambiguity")          # v1: polarity rule as first written (pre-registered)
STEPS_V4 = ("specific", "qa", "speaker", "polarity3", "kin", "value", "ambiguity", "ctx")      # v4: v3 + the preceding question is added to a SHORT reply that cannot be read without it (post-hoc, disclosed)
STEPS_V3 = ("specific", "qa", "speaker", "polarity3", "kin", "value", "ambiguity")           # v3: v2 + negative findings need a LOCAL negation cue (post-hoc, disclosed)
STEPS_V2 = ("specific", "qa", "speaker", "polarity2", "kin", "value", "ambiguity")           # v2: item-aware polarity, introduced AFTER the v1 ladder showed its cost (post-hoc, disclosed)



def add_context(enc, segs, steps):
    """A short non-question reply (<= SHORT_ANSWER_WORDS words) directly after a question of the other speaker is not interpretable alone ('No, none of that at all.'): include that question as context."""
    if "ctx" not in steps:
        return sorted(segs), False
    out, ctx = set(segs), False
    for i in list(segs):
        if not enc.q[i] and len(enc.words[i]) <= SHORT_ANSWER_WORDS and i - 1 >= 0 and enc.q[i - 1] and enc.speaker[i - 1] != enc.speaker[i] and (i - 1) not in out:
            out.add(i - 1); ctx = True
    return sorted(out), ctx

def retrieve(cat, item, enc: Enc, steps=STEPS_ALL):
    """Returns {segments: sorted indices (possibly empty), decision, reason, score, context_question}. `steps` = enabled filters (ablation ladder)."""
    fields = query_fields(cat, item)
    if not fields:
        return {"segments": [], "decision": "abstain", "reason": "no_anchor_words", "score": 0.0}
    cand = []  # (score, i, matched_union)
    for i in range(enc.N):
        best, spec, mt = 0.0, False, []
        for f, st in fields.items():
            c, sp, m = field_cov(enc, st, i)
            if c > best + 1e-9:
                best, spec, mt = c, sp, m
        if best >= TAU:
            cand.append((best, i, mt, spec))
    if not cand:
        return {"segments": [], "decision": "abstain", "reason": "no_candidate", "score": 0.0}
    if "specific" in steps:
        cand = [c for c in cand if c[3]]
        if not cand:
            return {"segments": [], "decision": "abstain", "reason": "only_generic_matches", "score": 0.0}
    groups = []  # (score, tuple(segments), matched, evidence_idx(non-question members), context_question)
    for sc, i, mt, _ in cand:
        if "qa" in steps and enc.q[i]:
            j = i + 1
            if j < enc.N and not enc.q[j] and enc.speaker[j] != enc.speaker[i]:
                ans = field_cov(enc, next(iter(fields.values())), j)
                answer_has_anchor = any(field_cov(enc, st, j)[0] >= TAU for st in fields.values())
                if answer_has_anchor:
                    groups.append((sc, (j,), mt, (j,), False))
                elif len(enc.words[j]) <= SHORT_ANSWER_WORDS:
                    groups.append((sc, (i, j), mt, (j,), True))
            continue  # question with no usable answer: dropped
        groups.append((sc, (i,), mt, (i,), False))
    if not groups:
        return {"segments": [], "decision": "abstain", "reason": "question_without_answer", "score": 0.0}
    stage = "ok"
    if "speaker" in steps and EXPECT_CLASS.get(cat):
        keep = [g for g in groups if all(role_class(enc.role[k]) == EXPECT_CLASS[cat] for k in g[3])]
        if not keep:
            return {"segments": [], "decision": "abstain", "reason": "speaker_class_mismatch", "score": max(g[0] for g in groups)}
        groups = keep
    if "polarity" in steps:
        keep = []
        for g in groups:
            neg_seg = any(has_neg(enc.raw[k]) for k in g[3])
            if cat == "negative_findings":
                if neg_seg:
                    keep.append(g)
            else:
                negated = any(anchor_negated(enc, k, g[2]) for k in g[3]) or (g[4] and has_neg(enc.raw[g[3][0]]) and len(enc.words[g[3][0]]) <= SHORT_ANSWER_WORDS)
                if not negated:
                    keep.append(g)
        if not keep:
            return {"segments": [], "decision": "abstain", "reason": "polarity_conflict", "score": max(g[0] for g in groups)}
        groups = keep
    if "polarity3" in steps:
        keep = []
        neg_item = item_negative(cat, item)
        for g in groups:
            if cat == "negative_findings":
                # a denied finding needs a negation cue NEXT TO its anchor (or a negative short reply to its question), not anywhere in the segment
                ok = any(anchor_negated(enc, k, g[2]) for k in g[3]) or (g[4] and has_neg(enc.raw[g[3][0]]))
            elif neg_item:
                ok = True
            else:
                ok = not (any(anchor_negated(enc, k, g[2]) for k in g[3]) or (g[4] and has_neg(enc.raw[g[3][0]]) and len(enc.words[g[3][0]]) <= SHORT_ANSWER_WORDS))
            if ok:
                keep.append(g)
        if not keep:
            return {"segments": [], "decision": "abstain", "reason": "polarity_conflict", "score": max(g[0] for g in groups)}
        groups = keep
    if "polarity2" in steps:
        keep = []
        neg_item = item_negative(cat, item)
        for g in groups:
            neg_seg = any(has_neg(enc.raw[k]) for k in g[3])
            if cat == "negative_findings":
                ok = neg_seg                      # a denied finding needs a negation cue in its evidence
            elif neg_item:
                ok = True                         # the item itself is an absence/denial outside negative_findings: no polarity constraint (cannot be validated lexically)
            else:
                ok = not (any(anchor_negated(enc, k, g[2]) for k in g[3]) or (g[4] and has_neg(enc.raw[g[3][0]]) and len(enc.words[g[3][0]]) <= SHORT_ANSWER_WORDS))
            if ok:
                keep.append(g)
        if not keep:
            return {"segments": [], "decision": "abstain", "reason": "polarity_conflict", "score": max(g[0] for g in groups)}
        groups = keep
    if "kin" in steps:
        keep = []
        for g in groups:
            kin_here = any(has_kin(enc.raw[k]) for k in g[3])
            if cat == "medical_history.family_history":
                ok = kin_here
            elif cat in OWN_HISTORY:
                ok = not any(kin_conflict(enc, k, g[2]) for k in g[3])
            else:
                ok = True
            if ok:
                keep.append(g)
        if not keep:
            return {"segments": [], "decision": "abstain", "reason": "kinship_conflict", "score": max(g[0] for g in groups)}
        groups = keep
    if "value" in steps and cat == "vital_signs":
        nums = re.findall(r"\d+(?:\.\d+)?", str(item.get("value") or ""))
        if nums:
            keep = [g for g in groups if all(n in set(re.findall(r"\d+(?:\.\d+)?", " ".join(enc.segs[k]["text"] for k in g[1]))) for n in nums)]
            if not keep:
                return {"segments": [], "decision": "abstain", "reason": "value_not_in_evidence", "score": max(g[0] for g in groups)}
            groups = keep
    top = max(g[0] for g in groups)
    if "ambiguity" in steps:
        tied = sorted({g[1] for g in groups if g[0] >= top - BAND})
        if len(tied) > MAX_TIED:
            return {"segments": [], "decision": "abstain", "reason": "ambiguous_many_equal_matches", "score": top}
        segs = sorted({k for t in tied for k in t})
        segs, cx = add_context(enc, segs, steps)
        return {"segments": segs, "decision": "cited", "reason": "ok", "score": top, "context_question": cx or any(g[4] for g in groups if g[1] in tied)}
    best = min((g for g in groups if g[0] >= top - 1e-9), key=lambda g: g[1][0])
    segs, cx = add_context(enc, sorted(best[1]), steps)
    return {"segments": segs, "decision": "cited", "reason": "ok", "score": top, "context_question": cx or best[4]}


# ------------- legacy Arm R configurations (re-implemented identically for the ladder's reference rows)
def _legacy_pick(cat, item, enc, simple):
    def stems_text(t):
        return [x[:STEM] for x in content_tokens(norm_text(t))]
    if simple:
        k = KEYS[cat](item)
        q = list(dict.fromkeys(stems_text(str(k).split("|")[-1] if k else "")))
    else:
        q = list(dict.fromkeys(stems_text(" ".join(str(item.get(f)) for f in _LEG_QF[cat] if item.get(f) not in (None, "")))))
    if not q:
        return {"segments": [], "decision": "abstain", "reason": "no_anchor_words", "score": 0.0}
    w = {t: (math.log(1 + enc.N / max(1, sum(any(x.startswith(t) for x in ws) for ws in enc.words))) if not simple else 1.0) for t in q}
    den = sum(w.values()); best, bi = (-1.0, -1, 0), 0
    for i, ws in enumerate(enc.words):
        m = [t for t in q if any(x.startswith(t) for x in ws)]
        sc = sum(w[t] for t in m) / den
        key = (round(sc, 9), len(m) if not simple else 0, -i)
        if key > (round(best[0], 9), best[1], best[2]):
            best, bi = (sc, len(m), -i), i
    if not simple and best[0] < 0.5:
        return {"segments": [], "decision": "abstain", "reason": "below_threshold", "score": best[0]}
    return {"segments": [bi], "decision": "cited", "reason": "ok", "score": best[0]}


_LEG_QF = {"chief_complaint": ["value", "normalized_value"], "symptoms": ["name", "normalized_name", "body_site"], "negative_findings": ["finding", "normalized_name"],
           "medical_history.past_medical_history": ["condition", "normalized_condition"], "medical_history.surgical_history": ["procedure", "normalized_procedure"],
           "medical_history.family_history": ["condition", "normalized_condition", "relation"], "medical_history.social_history": ["category", "description", "details"],
           "medications": ["name", "normalized_name", "generic_name", "dose", "frequency"], "allergies": ["substance", "normalized_substance", "reaction"], "vital_signs": ["name", "normalized_name", "value"],
           "physical_examination": ["finding", "normalized_finding", "body_site"], "review_of_systems": ["system", "details"], "clinical_conditions": ["name", "normalized_name"],
           "clinical_assessment": ["assessment", "normalized_assessment"], "procedures_and_investigations": ["name", "normalized_name"], "clinical_actions": ["description"],
           "follow_up": ["time_reference"], "clinical_uncertainties": ["description"]}

LADDER = [("R_simple", None), ("R_main", None), ("C1 coverage, no fallback", ()), ("C2 + specificity", ("specific",)), ("C3 + question->answer", ("specific", "qa")),
          ("C4 + speaker class", ("specific", "qa", "speaker")), ("C5 + polarity", ("specific", "qa", "speaker", "polarity")), ("C6 + kinship", ("specific", "qa", "speaker", "polarity", "kin")),
          ("C7 + vital value", ("specific", "qa", "speaker", "polarity", "kin", "value")), ("C8 + ambiguity (= R_cons v1)", STEPS_ALL),
          ("C5b item-aware polarity (v2)", ("specific", "qa", "speaker", "polarity2")), ("C7b v2 through vital value", ("specific", "qa", "speaker", "polarity2", "kin", "value")),
          ("C8b + ambiguity (= R_cons v2)", STEPS_V2),
          ("C8c + local negation cue (= R_cons v3)", STEPS_V3),
          ("C8d + context question for short replies (= R_cons v4)", STEPS_V4)]


def run_ladder_step(name, steps, cat, item, enc):
    if name == "R_simple":
        return _legacy_pick(cat, item, enc, True)
    if name == "R_main":
        return _legacy_pick(cat, item, enc, False)
    return retrieve(cat, item, enc, steps)
