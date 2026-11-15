"""STEP 2-4: realise a blueprint as a natural multi-speaker dialogue (Module 2
transcript) and derive the ground-truth extraction from the *same* turns.

Every extracted fact is created at the moment the turn that states it is
written, and the turn index is attached to the entity -- evidence therefore
cannot drift from the transcript.  Fields that are never spoken stay null."""
import random
import re
from collections import defaultdict
from blueprint import strip_art, spoken_dose, dur_obj
import dialogue_pools as T
import content_core as CC

ROLE = {"D": "DOCTOR", "P": "PATIENT", "N": "NURSE", "C": "CAREGIVER", "F": "FAMILY_MEMBER", "S": "CLINICAL_STAFF", "U": "UNKNOWN"}
PATHS = ["symptoms", "negative_findings", "medical_history.past_medical_history", "medical_history.surgical_history",
         "medical_history.family_history", "medical_history.social_history", "medications", "allergies", "vital_signs",
         "physical_examination", "review_of_systems", "clinical_conditions", "clinical_assessment",
         "procedures_and_investigations", "clinical_actions", "follow_up", "clinical_uncertainties"]
HES = ["Um, ", "Uh, ", "Well, ", "So, ", "I mean, ", "Yeah, ", "Okay, so ", "Hmm, ", "Right, ", "Oh, "]
RATE = {"D": 2.9, "P": 2.5, "N": 3.0, "C": 2.6, "F": 2.6, "S": 3.0, "U": 2.4}
NUMW = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"]


def cap(s):
    return s[:1].upper() + s[1:]


def lower_first(s):
    if re.match(r"^(I\b|I'|I’)", s):
        return s
    return s[:1].lower() + s[1:]


def yours(p):
    p = re.sub(r"\bmy\b", "your", p)
    p = re.sub(r"\bI'm\b", "you're", p)
    p = re.sub(r"\bI\b", "you", p)
    p = re.sub(r"\bme\b", "you", p)
    return p


def jn(items):
    items = list(items)
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]


def jor(items):
    items = list(items)
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " or " + items[-1]


class Enc:
    def __init__(self, bp, F):
        self.bp, self.F = bp, F
        self.rng = random.Random(bp["seed"] * 977 + bp["attempt"] * 31 + F * 7 + 1)
        self.turns = []
        self.S = {p: [] for p in PATHS}
        self.cc = None
        self.prot = set()
        self.combo = set(bp["combo"])
        sx = bp["sex"]
        self.he, self.He, self.his = ("he", "He", "his") if sx == "M" else ("she", "She", "her")
        self.symref = {}
        self.unc_list = []
        self.contra = []
        self.ambig = []
        self.unknown_done = False
        self.feats = set(bp["features"])
        self.last_plan = {}
        self.used_el = set()

    # ------------------------------------------------------------------ core
    def ent(self, path, d):
        d["_t"] = set()
        self.S[path].append(d)
        return (path, len(self.S[path]) - 1)

    def get(self, ref):
        return self.cc if ref[0] == "chief_complaint" else self.S[ref[0]][ref[1]]

    def lit(self, *xs):
        for x in xs:
            if x:
                self.prot.add(str(x))

    def hum(self, who, text):
        rng, st = self.rng, self.bp["style"]
        if who == "D":
            if rng.random() < .12 and not text.startswith(("Mm", "Okay", "Right", "Alright", "So", "Let", "Hold", "Give")):
                return rng.choice(["Okay, ", "Right, ", "Alright, ", "So, "]) + lower_first(text)
            return text
        if who not in "PCFU":
            return text
        prob = dict(terse=.1, chatty=.25, anxious=.35, casual=.25, formal=.08, hesitant=.5)[st]
        masks = {}
        for n, l in enumerate(sorted(self.prot, key=len, reverse=True)):
            if len(l) > 2 and re.search(re.escape(l), text, flags=re.I):
                text = re.sub(re.escape(l), lambda m, n=n: masks.setdefault(f"\x00{n}\x00", m.group(0)) and f"\x00{n}\x00", text, flags=re.I)
        if rng.random() < prob and len(text.split()) > 3 and not text.startswith(tuple(HES)) and "\x00" not in text[:3]:
            text = rng.choice(HES) + lower_first(text)
        if rng.random() < prob * .6 and ", " in text:
            i = text.index(", ")
            if "\x00" not in text[max(0, i - 2):i + 4]:
                text = text[:i] + rng.choice([", um,", ", you know,", ", uh,"]) + text[i + 1:]
        if rng.random() < prob * .35 and not text.startswith(tuple(HES)):
            m = re.match(r"^(I've|I'm|It's|It|I|The|And|But|So)\b", text)
            if m:
                text = m.group(1) + ", " + text
        for k, v in masks.items():
            text = text.replace(k, v)
        return text

    def say(self, who, text, ents=(), gap=None, hum=True):
        if hum:
            text = self.hum(who, text)
        text = re.sub(r"\s+", " ", text).strip()
        if text and text[-1] not in ".?!—…\"":
            text += "."
        i = len(self.turns)
        self.turns.append(dict(who=who, text=text, gap=gap))
        for r in ents:
            self.get(r)["_t"].add(i)
        return i

    def tag(self, refs, *turn_idx):
        for r in refs:
            for t in turn_idx:
                self.get(r)["_t"].add(t)

    def unc(self, typ, desc, rel, turns, status="unresolved"):
        d = dict(type=typ, description=desc, related_entities=list(rel), resolution_status=status,
                 evidence_ids=[], confidence=1.0, _rel=list(rel))
        ref = self.ent("clinical_uncertainties", d)
        self.get(ref)["_t"].update(turns)
        return ref

    def r(self, seq):
        return self.rng.choice(seq)

    def elab(self, who="P", p=None):
        pr = dict(terse=.12, chatty=.75, anxious=.75, casual=.6, formal=.4, hesitant=.6)[self.bp["style"]] if p is None else p
        if who == "P" and self.rng.random() < pr:
            pool = [e for e in T.P_ELAB if e not in self.used_el]
            if not pool:
                return ""
            e1 = self.rng.choice(pool)
            self.used_el.add(e1)
            x = " " + e1
            pool = [e for e in pool if e not in self.used_el]
            if pool and self.rng.random() < .25:
                e2 = self.rng.choice(pool)
                self.used_el.add(e2)
                x += " " + e2
            return x
        return ""

    def delab(self, p=.3):
        return " " + self.r(T.D_ELAB) if self.rng.random() < p else ""

    def bc(self, p=.12):
        if self.bp["complexity"] in ("complex", "challenging"):
            p *= .4
        if self.rng.random() < p:
            self.say("D", self.r(T.D_BACKCH), hum=False, gap=self.rng.uniform(.2, .6))

    # ----------------------------------------------------------- symptoms
    def sym_ent(self, i, reporter="P"):
        s = self.bp["syms"][i]
        if i in self.symref:
            return self.symref[i]
        temporality = {"current": "current", "previous": "past"}[s["role"]]
        if s["status"] == "resolved" and s["role"] == "current":
            temporality = "resolved"
        d = {"name": cap(s["name"]), "normalized_name": s["norm"], "category": s["cat"], "status": s["status"],
             "severity": None, "duration": None, "frequency": None, "onset": None, "temporality": temporality,
             "body_site": s["site"], "associated_symptoms": [], "aggravating_factors": [], "relieving_factors": [],
             "reported_by": ROLE[reporter].lower(), "certainty": "certain", "evidence_ids": [], "confidence": 1.0}
        self.lit(s["phrase"], s["name"])
        ref = self.ent("symptoms", d)
        self.symref[i] = ref
        return ref

    def have_phrase(self, s):
        return f"been {s['phrase']}" if s["kind"] == "ger" else f"had {s['phrase']}"

    def dur_text(self, s):
        return s["dur"][0]

    def set_dur(self, ref, s):
        e = self.get(ref)
        if s["dur"]:
            e["duration"] = {"value": s["dur"][1], "unit": s["dur"][2], "normalized": s["dur"][3]}
            self.lit(s["dur"][0])
        elif s["onset"]:
            e["onset"] = s["onset"]
            self.lit(s["onset"])

    def dur_turn(self, s, ref, who="P"):
        """patient states duration/onset for symptom s."""
        if s["dur"]:
            txt = self.r(T.DUR_T).format(d=s["dur"][0])
        elif s["onset"] == "yesterday":
            txt = self.r(T.ONSET_Y)
        else:
            o = s["onset"]
            txt = self.r(T.ONSET_T).format(o=o, O=cap(o))
        self.set_dur(ref, s)
        return txt

    def freq_text(self, f):
        return self.r(T.FREQ_V).format(f=f) if f == "comes and goes" else self.r(T.FREQ_T).format(f=f)

    def sev_phrase(self, s, ref):
        e = self.get(ref)
        e["severity"] = s["sev"]
        if "/" in s["sev"]:
            n = int(s["sev"].split("/")[0])
            from blueprint import wchoice  # noqa
            return self.r(T.SEV_NUM_T).format(n=["", "", "", "three", "four", "five", "six", "seven", "eight"][n])
        self.lit(s["sev"])
        return self.r(T.SEV_T).format(s=s["sev"], S=cap(s["sev"]))

    def detail_bits(self, i, ref):
        s = self.bp["syms"][i]
        e = self.get(ref)
        bits = []
        if s["sev"]:
            bits.append(self.sev_phrase(s, ref))
        if s["freq"]:
            e["frequency"] = s["freq"]
            self.lit(s["freq"])
            bits.append(self.freq_text(s["freq"]))
        if s["aggr"]:
            e["aggravating_factors"] = list(s["aggr"])
            self.lit(*s["aggr"])
            bits.append(self.r(T.AGGR_T).format(a=jn(s["aggr"]), A=cap(jn(s["aggr"]))))
        if s["relief"]:
            e["relieving_factors"] = list(s["relief"])
            self.lit(*s["relief"])
            bits.append(self.r(T.RELIEF_T).format(r=jn(s["relief"]), R=cap(jn(s["relief"]))))
        return bits

    def detail_turns(self, i, ref):
        """question/answer turns for severity, frequency, factors of symptom i."""
        s, rng = self.bp["syms"][i], self.rng
        order = []
        if s["sev"]:
            order.append("sev")
        if s["freq"]:
            order.append("freq")
        if s["aggr"]:
            order.append("aggr")
        if s["relief"]:
            order.append("relief")
        rng.shuffle(order)
        e = self.get(ref)
        inc = "incomplete_answers" in self.feats and rng.random() < .4
        if len(order) >= 2 and not inc and rng.random() < .8:
            q = self.say("D", self.r(["Tell me a bit more about it: how bad it gets, how often, and whether anything makes it better or worse.",
                                      "Can you describe it a bit more for me? How strong it is, what the pattern is, what helps.",
                                      "Okay, give me more detail on it, whatever comes to mind."]) + self.delab(.25))
            bits = []
            for k in order:
                if k == "sev":
                    bits.append(self.sev_phrase(s, ref))
                elif k == "freq":
                    e["frequency"] = s["freq"]
                    self.lit(s["freq"])
                    bits.append(self.freq_text(s["freq"]))
                elif k == "aggr":
                    e["aggravating_factors"] = list(s["aggr"])
                    self.lit(*s["aggr"])
                    bits.append(self.r(T.AGGR_T).format(a=jn(s["aggr"]), A=cap(jn(s["aggr"]))))
                else:
                    e["relieving_factors"] = list(s["relief"])
                    self.lit(*s["relief"])
                    bits.append(self.r(T.RELIEF_T).format(r=jn(s["relief"]), R=cap(jn(s["relief"]))))
            a = self.say("P", " ".join(bits) + self.elab())
            self.tag([ref], q, a)
            return
        for k in order:
            if k == "sev":
                q = self.say("D", self.r(T.D_SEV))
                if inc and rng.random() < .5:
                    a0 = self.say("P", "Well, it's... hard to say, it's kind of... I don't know—", gap=rng.uniform(1.2, 2.5))
                    q2 = self.say("D", "Take your time. Mild, moderate, or severe, if you had to pick?")
                    a = self.say("P", self.sev_phrase(s, ref))
                    self.tag([ref], q, a0, q2, a)
                else:
                    a = self.say("P", self.sev_phrase(s, ref))
                    self.tag([ref], q, a)
            elif k == "freq":
                q = self.say("D", self.r(T.D_FREQ))
                e["frequency"] = s["freq"]
                self.lit(s["freq"])
                if inc and rng.random() < .5:
                    a0 = self.say("P", "It's, um... not exactly... well, hard to explain, I mean—", gap=rng.uniform(1, 2.2))
                    q2 = self.say("D", "Let me put it another way: how many times in a typical day or week?")
                    a = self.say("P", self.freq_text(s["freq"]))
                    self.tag([ref], q, a0, q2, a)
                else:
                    a = self.say("P", self.freq_text(s["freq"]))
                    self.tag([ref], q, a)
            elif k == "aggr":
                q = self.say("D", self.r(T.D_AGGR))
                e["aggravating_factors"] = list(s["aggr"])
                a = self.say("P", self.r(T.AGGR_T).format(a=jn(s["aggr"]), A=cap(jn(s["aggr"]))))
                self.lit(*s["aggr"])
                self.tag([ref], q, a)
            else:
                q = self.say("D", self.r(T.D_RELIEF))
                e["relieving_factors"] = list(s["relief"])
                a = self.say("P", self.r(T.RELIEF_T).format(r=jn(s["relief"]), R=cap(jn(s["relief"]))))
                self.lit(*s["relief"])
                self.tag([ref], q, a)
            self.bc(.08)

    def b_open(self):
        rng, bp = self.rng, self.bp
        mode = rng.random()
        if "N" in self.combo and mode < .5:
            self.say("N", self.r(T.NURSE_HANDOVER), hum=False)
            self.say("D", self.r(T.D_AFTER_NURSE))
            asked = True
        elif mode < .72:
            self.say("P", self.r(T.P_FIRST))
            self.say("D", self.r(T.D_AFTER_PFIRST))
            asked = True
        else:
            self.say("D", self.r(T.GREET_D))
            if rng.random() < .7:
                self.say("P", self.r(T.GREET_P))
            asked = False
        for k in "CF":
            if k in self.combo:
                self.say(k, self.r(T.CARE_ENTER))
                if rng.random() < .6:
                    self.say("D", self.r(T.D_TO_CARE))
                break
        if not asked:
            if self.F >= 1 and rng.random() < .75:
                self.f_rapport()
            self.say("D", self.r(T.ASK_D))
        s0 = bp["syms"][0]
        who = bp["cc_by"]
        phrase = s0["phrase"]
        self.lit(phrase, s0["name"])
        self.cc = dict(value=s0["name"], normalized_value=s0["norm"], reported_by=ROLE[who].lower(),
                       evidence_ids=[], confidence=1.0, _t=set())
        refs = [("chief_complaint", None)]
        if not s0.get("cc_only"):
            refs.append(self.sym_ent(0, who))
        ger = s0["kind"] == "ger"
        if who == "P":
            if ger:
                txt = self.r(["I've been {cc}.", "Mainly I've been {cc}. That's why I came.", "So, I've been {cc}, doctor.",
                              "I've been {cc}, and I wanted to get it checked."]).format(cc=phrase)
            else:
                txt = self.r(T.CC_T).format(cc=phrase)
        else:
            txt = self.r(T.CC_THIRD).format(cc=("been " + phrase) if ger else phrase, He=self.He)
            if ger:
                txt = txt.replace("been been", "been")
                txt = f"{self.He}'s been {phrase}, doctor." if "'s been" not in txt else txt
            elif "'s been" in txt:
                txt = txt.replace("'s been " + phrase, "'s been having " + phrase)
        i = self.say(who, txt + self.elab("P" if who == "P" else "x"), refs)
        self.unc_turn = i
        if who != "P":
            self.last_cc = i

    def b_narrative(self):
        bp, rng = self.bp, self.rng
        syms = bp["syms"]
        s0 = syms[0]
        refs0 = None if s0.get("cc_only") else self.symref[0]
        if refs0 is not None and (s0["dur"] or s0["onset"] or s0["uncertain_onset"]):
            q = self.say("D", self.r(T.D_HOWLONG) + self.delab(.25))
            if s0["uncertain_onset"]:
                a = self.say("P", self.r(T.P_DATE_UNC))
                self.tag([refs0], q, a)
                self.get(refs0)["certainty"] = "uncertain"
                self.unc("date_uncertain", f"Patient could not state when '{s0['name']}' began (\"might have been last month or the month before\").",
                         [refs0], [q, a])
                self.unc_turn = a
            else:
                who = "P"
                a = self.say(who, self.dur_turn(s0, refs0) + self.elab())
                self.tag([refs0], q, a)
                self.unc_turn = a
            self.after_first = a
        self.bc(.15)
        if refs0 is not None:
            self.detail_turns(0, refs0)
        # association
        if s0["assoc"] is not None:
            j = s0["assoc"]
            sj = syms[j]
            rj = self.sym_ent(j)
            q = self.say("D", self.r(T.D_ASSOC))
            a = self.say("P", self.r(T.ASSOC_T).format(q=sj["phrase"], Q=cap(sj["phrase"])))
            self.get(refs0)["associated_symptoms"] = [sj["norm"]]
            self.tag([refs0, rj], q, a)
        if "interruptions" in self.feats:
            self.interrupt()
        # other symptoms
        for i, s in enumerate(syms):
            if i == 0 or s["role"] == "previous" or s["status"] == "resolved":
                continue
            already = i in self.symref
            ref = self.sym_ent(i)
            mode = rng.random()
            if s.get("uncertain_onset"):
                a = self.say("P", f"As for {strip_art(s['phrase'])}, I honestly can't say when that began. It might have been last month or the month before.")
                self.get(ref)["certainty"] = "uncertain"
                self.tag([ref], a)
                self.unc("date_uncertain", f"Patient could not state when '{s['name']}' began (\"might have been last month or the month before\").", [ref], [a])
            elif already:
                if s["dur"] or s["onset"]:
                    dtxt = f"for {s['dur'][0]}" if s["dur"] else (s["onset"] if s["onset"] != "yesterday" else "since yesterday")
                    a = self.say("P", f"The {strip_art(s['phrase'])}? That's been {dtxt}." if s["kind"] == "noun" else f"As for {s['phrase']}, that's been {dtxt}.")
                    self.set_dur(ref, s)
                    self.tag([ref], a)
            elif mode < .35:
                q = self.say("D", yours(self.r(T.D_ALSO).format(p=s["phrase"])) if s["kind"] == "noun" else yours(f"Have you {self.have_phrase(s)}?"))
                if s["dur"] or s["onset"]:
                    if s["dur"]:
                        a = self.say("P", self.r(["Yes, for {d}.", "Yes, about the same, {d}.", "Yeah. {D}, I'd say."]).format(d=s["dur"][0], D=cap(s["dur"][0])))
                    elif s["onset"] == "yesterday":
                        a = self.say("P", "Yes, that started yesterday.")
                    else:
                        a = self.say("P", self.r(["Yes, {o}.", "Yeah, I've had that {o}."]).format(o=s["onset"]))
                    self.set_dur(ref, s)
                else:
                    a = self.say("P", self.r(T.P_YES))
                self.tag([ref], q, a)
            else:
                if s["kind"] == "ger":
                    base = self.r(["I've also been {p}", "And I've been {p} as well", "I've been {p} too"]).format(p=s["phrase"])
                    if s["dur"]:
                        a = self.say("P", f"{base}, for {s['dur'][0]}.")
                    elif s["onset"]:
                        a = self.say("P", f"{base}, {s['onset']}." if s["onset"] != "yesterday" else f"{base}, since yesterday.")
                    else:
                        a = self.say("P", base + ".")
                else:
                    if s["dur"]:
                        a = self.say("P", self.r(T.P_ALSO).format(p=s["phrase"], d=s["dur"][0]))
                    elif s["onset"] and s["onset"] != "yesterday":
                        a = self.say("P", self.r(T.P_ALSO_ON).format(p=s["phrase"], o=s["onset"]))
                    elif s["onset"]:
                        a = self.say("P", f"I've also had {s['phrase']}, since yesterday.")
                    else:
                        a = self.say("P", self.r(T.P_ALSO_BARE).format(p=s["phrase"], P=cap(s["phrase"])))
                self.set_dur(ref, s)
                self.tag([ref], a)
            if s["sev"] or s["freq"] or s["aggr"] or s["relief"]:
                if rng.random() < .7 and "incomplete_answers" not in self.feats:
                    bits = self.detail_bits(i, ref)
                    bits[0] = self.r(["As for {p}, ", "With {p}, ", "About {p}, "]).format(p=strip_art(s["phrase"])) + lower_first(bits[0])
                    t = self.say("P", " ".join(bits))
                    self.tag([ref], t)
                else:
                    self.detail_turns(i, ref)
            self.bc(.06)
        # resolved current symptoms (non-challenging flow) and previous episodes
        if "mixed_negation" not in self.feats:
            for i, s in enumerate(syms):
                if s["status"] == "resolved" and s["role"] == "current":
                    self.resolved_turn(i)
        for i, s in enumerate(syms):
            if s["role"] == "previous":
                bp = self.bp
                ref = self.sym_ent(i)
                self.get(ref)["onset"] = s["onset"]
                self.lit(s["onset"])
                ps = bp["syms"][i]
                pq = (f"Have you had {ps['phrase']} before, or is this the first time?" if ps["kind"] == "noun"
                      else f"Have you been {ps['phrase']} at any time before this?")
                q = self.say("D", yours(pq))
                a = self.say("P", self.r(T.P_PREV).format(w=s["onset"]))
                self.tag([ref], q, a)

    def resolved_turn(self, i, inline=None):
        s = self.bp["syms"][i]
        ref = self.sym_ent(i)
        if s["kind"] == "ger":
            txt = self.r(["I was {p} at one point, but that's gone now.", "I'd been {p}, but that went away."]).format(p=s["phrase"])
        else:
            txt = self.r(T.P_RESOLVED).format(p=s["phrase"], P=cap(s["phrase"]))
        a = self.say("P", txt)
        self.tag([ref], a)
        return a

    def interrupt(self):
        rng = self.rng
        others = [k for k in "CFN" if k in self.combo]
        who = rng.choice(others) if others else "D"
        if who == "D" or not others:
            a = self.say("P", "So what happened next was that I went to the—", gap=rng.uniform(.4, 1))
            b = self.say("D", "Sorry to stop you there. Let's take it one step at a time, and we'll come back to that.", gap=.1)
            c = self.say("P", "Okay. Sorry, I tend to get ahead of myself.")
        elif who in "CF":
            a = self.say("P", "And the other thing I wanted to mention is that I can't really—", gap=rng.uniform(.4, 1))
            b = self.say(who, "Tell the doctor about the other thing, that's what worries me.", gap=.1)
            c = self.say("P", "I was getting to that!")
            if rng.random() < .3:
                self.say("D", "That's fine, one at a time. I'll ask about everything.")
        else:
            a = self.say("P", "I was just going to say that the main thing is—", gap=rng.uniform(.4, 1))
            b = self.say("N", "Sorry to cut in, doctor, quick question: shall I bring the trolley in now or later?", gap=.1)
            c = self.say("D", "Later, thanks. Please go on.")
            pass

    # ------------------------------------------------------------ negatives
    def b_negs(self):
        bp, rng = self.bp, self.rng
        negs = list(bp["negs"])
        disp = bp["neg_dispute"]
        order = list(range(len(negs)))
        chunks, i = [], 0
        rng.shuffle(order)
        # disputed finding is asked on its own
        if disp is not None:
            order.remove(disp)
            chunks.append([disp])
        while order:
            k = rng.choice([2, 3, 3, 4]) if len(order) > 1 else 1
            chunks.append(order[:k])
            order = order[k:]
        rng.shuffle(chunks)
        mixed_done = "mixed_negation" not in self.feats
        res_idx = [i for i, s in enumerate(bp["syms"]) if s["status"] == "resolved" and s["role"] == "current"]
        for c in chunks:
            phrases = [strip_art(negs[j][0]) for j in c]
            refs = []
            for j in c:
                p = strip_art(negs[j][0])
                self.lit(p)
                refs.append(self.ent("negative_findings", {
                    "finding": cap(p), "normalized_name": negs[j][1], "status": "absent", "assertion": "negative",
                    "reported_by": "patient", "temporality": "current", "evidence_ids": [], "confidence": 1.0}))
            if len(c) == 1:
                q = self.say("D", self.r(T.NEG_Q1).format(a=phrases[0]))
            else:
                q = self.say("D", self.r(T.NEG_QN).format(l=jor(phrases)))
            mixed = (not mixed_done) and res_idx and len(c) >= 2
            if mixed:
                ri = res_idx[0]
                rs = bp["syms"][ri]
                rref = self.sym_ent(ri)
                if rs["kind"] == "ger":
                    res_txt = f"I was {rs['phrase']} at one point, but that went away on its own."
                else:
                    res_txt = f"I did have {rs['phrase']} at one point, but that went away on its own."
                a = self.say("P", f"No, no {phrases[0]}, no {phrases[1]}" + (f", no {phrases[2]}" if len(c) > 2 else "") + f". {res_txt}")
                self.tag(refs + [rref], q, a)
                mixed_done = True
            elif len(c) == 1:
                a = self.say("P", self.r(T.NEG_A1).format(a=phrases[0]))
                self.tag(refs, q, a)
            else:
                a = self.say("P", self.r(T.NEG_AN) if rng.random() < .55 else self.r(T.NEG_ANS).format(l=jor(phrases)))
                self.tag(refs, q, a)
            if disp is not None and c == [disp]:
                k = "C" if "C" in self.combo and ("F" not in self.combo or rng.random() < .6) else "F"
                p = phrases[0]
                sref_d = dict(name=cap(p), normalized_name=negs[disp][1], category="reported", status="present", severity=None,
                              duration=None, frequency=None, onset=None, temporality="current", body_site=None,
                              associated_symptoms=[], aggravating_factors=[], relieving_factors=[],
                              reported_by=ROLE[k].lower(), certainty="disputed", evidence_ids=[], confidence=.6)
                ref = self.ent("symptoms", sref_d)
                u = self.say(k, f"Actually, doctor, I did notice {p}. {self.He} doesn't always say.")
                pr = self.say("P", "No, I don't think I did. Maybe a little, I'm not sure.")
                d = self.say("D", "Alright, I'll note both what you've said and what you've noticed.")
                self.tag([ref], u)
                self.tag(refs, u, pr)
                self.tag([ref], pr)
                self.contra.append(f"Patient denies {p}; {ROLE[k].lower().replace('_', ' ')} reports {p} (unresolved).")
                self.unc("conflicting_statement", f"Patient denies {p} while the {ROLE[k].lower().replace('_', ' ')} reports it; not resolved in the encounter.",
                         [refs[0], ref], [a, u, pr])
            self.bc(.08)
        if not mixed_done and res_idx:
            self.resolved_turn(res_idx[0])
        # system-level review
        pool = {r[0]: r for r in T.ROS_POOL}
        for name in bp["ros"]:
            r = pool[name]
            ref = self.ent("review_of_systems", {"system": name, "status": "negative", "details": None, "reported_by": "patient",
                                                  "evidence_ids": [], "confidence": 1.0})
            q = self.say("D", r[2])
            a = self.say("P", self.r(r[3]))
            self.tag([ref], q, a)

    # ------------------------------------------------------------- history
    def b_pmh(self):
        bp, rng = self.bp, self.rng
        q = self.say("D", (self.r(["Do you have any medical conditions I should know about?", "Any medical conditions, anything you've been treated for?"]) if bp["pmh_none"] else self.r(T.D_PMH)) + self.delab(.3))
        if bp["pmh_none"]:
            ref = self.ent("negative_findings", {"finding": "Medical conditions", "normalized_name": "No known chronic conditions",
                                                  "status": "absent", "assertion": "negative", "reported_by": "patient",
                                                  "temporality": "current", "evidence_ids": [], "confidence": 1.0})
            self.lit("medical conditions")
            a = self.say("P", self.r(T.P_PMH_NONE))
            self.tag([ref], q, a)
            return
        who = "P"
        refs = []
        for p in bp["pmh"]:
            self.lit(p["cond"])
            reporter = "P"
            ref = self.ent("medical_history.past_medical_history", {
                "condition": p["cond"], "normalized_condition": p["norm"], "status": "ongoing", "duration": None,
                "reported_by": "patient", "evidence_ids": [], "confidence": 1.0})
            if p["dur"]:
                self.get(ref)["duration"] = {"value": p["dur"][1], "unit": p["dur"][2], "normalized": p["dur"][3]}
                self.lit(p["dur"][0])
                txt = self.r(T.P_PMH_DUR).format(c=p["cond"], C=cap(p["cond"]), d=p["dur"][0])
            else:
                txt = self.r(T.P_PMH1).format(c=p["cond"])
            a = self.say("P", txt + self.elab())
            self.tag([ref], q, a)
            p["_ref"] = ref
            p["_turn"] = a
            if len(bp["pmh"]) > 1 and rng.random() < .12:
                q = self.say("D", "Okay. Anything else?")
            else:
                q = self.say("D", self.r(T.D_BACKCH), hum=False) if rng.random() < .3 else q
        # doctor confirms conditions he is actively managing
        for ci in bp["conds_confirmed"]:
            p = bp["pmh"][ci]
            ref = self.ent("clinical_conditions", {"name": p["cond"], "normalized_name": p["norm"], "status": "existing",
                                                    "duration": None, "reported_by": "patient", "confirmed_by": "doctor",
                                                    "evidence_ids": [], "confidence": 1.0})
            t = self.say("D", self.r(["Right, so that's your known {c}. We'll keep that in mind today.",
                                      "Okay, {c}, that's already on your record. Good to know.",
                                      "Yes, I can see the {c} in your file as well."]).format(c=p["cond"]))
            self.tag([ref, p["_ref"]], t)
            self.tag([ref], p["_turn"])

    def b_surg(self):
        bp = self.bp
        q = self.say("D", self.r(["Any previous surgeries?", "Have you had any previous surgeries?"]) if not bp["surg"] else self.r(T.D_SURG))
        if bp["surg"]:
            for s in bp["surg"]:
                self.lit(s["proc"], s["when"])
                ref = self.ent("medical_history.surgical_history", {"procedure": s["proc"], "normalized_procedure": s["norm"],
                                                                      "timeframe": s["when"], "reported_by": "patient",
                                                                      "evidence_ids": [], "confidence": 1.0})
                a = self.say("P", self.r(T.P_SURG).format(s=s["phrase"], t=s["when"]) + self.elab(p=.25))
                self.tag([ref], q, a)
        else:
            ref = self.ent("negative_findings", {"finding": "Previous surgeries", "normalized_name": "No previous surgery", "status": "absent",
                                                  "assertion": "negative", "reported_by": "patient", "temporality": "past",
                                                  "evidence_ids": [], "confidence": 1.0})
            self.lit("previous surgeries")
            a = self.say("P", self.r(T.P_SURG_NONE))
            self.tag([ref], q, a)

    def b_fam(self):
        bp = self.bp
        q = self.say("D", self.r(T.D_FAM))
        for f in bp["fam"]:
            self.lit(f["rel"], f["cond"])
            ref = self.ent("medical_history.family_history", {"condition": f["cond"], "normalized_condition": f["norm"],
                                                               "relation": f["rel"], "reported_by": "patient",
                                                               "evidence_ids": [], "confidence": 1.0})
            a = self.say("P", f["spoken"] + ".")
            self.tag([ref], q, a)

    def b_soc(self):
        for s in self.bp["soc"]:
            q = self.say("D", self.r([x for x in T.D_SOC if (("smok" in x.lower()) == (s["cat"] == "smoking"))]))
            self.lit(s["spoken"], s["details"])
            ref = self.ent("medical_history.social_history", {"category": s["cat"], "description": s["desc"], "status": s["status"],
                                                               "details": s["details"], "reported_by": "patient",
                                                               "evidence_ids": [], "confidence": 1.0})
            a = self.say("P", s["spoken"] + ".")
            self.tag([ref], q, a)

    # ---------------------------------------------------------- medications
    def med_ent(self, m, status=None, reporter="P", name=None, normalized="auto", generic="auto"):
        nm = name or m["name"]
        desc = nm.lower() in __import__("blueprint").DESCRIPTORS
        g = None if desc else m["generic"] if generic == "auto" else generic
        d = {"name": nm, "normalized_name": (None if (desc and normalized == "auto") else g) if normalized == "auto" else normalized,
             "generic_name": g, "dose": None, "route": None, "frequency": None, "duration": None,
             "indication": None, "status": status or m["status"], "reported_by": ROLE[reporter].lower(),
             "evidence_ids": [], "confidence": 1.0}
        if desc:
            d["normalized_name"] = cap(nm)
        self.lit(nm)
        return self.ent("medications", d)

    def med_say(self, m, ref, who, drop_dose=False, tentative=False):
        e = self.get(ref)
        parts = []
        if m["dose"] and not drop_dose:
            dose = spoken_dose(m["dose"])
            e["dose"] = m["dose"]
            self.lit(dose)
            parts.append(dose + (", maybe" if tentative else ""))
        if m["freq"]:
            e["frequency"] = m["freq"]
            self.lit(m["freq"])
            parts.append(m["freq"])
        name = m["name"]
        ind = ""
        if m["ind"]:
            e["indication"] = m["ind"].replace("my ", "").replace("the ", "")
            ind = f" for {m['ind']}"
            self.lit(m["ind"])
        rest = (", " + ", ".join(parts)) if parts else ""
        if who == "P":
            tpl = self.r(["I take {n}{r}{i}.", "{N}{r}{i}.", "It's {n}{r}{i}.", "I'm on {n}{r}{i}.", "{N}. I take it{r2}{i}."])
        else:
            tpl = self.r(["{H} takes {n}{r}{i}.", "{H} is on {n}{r}{i}, I give it to {o}.", "It's {n}{r}{i}, doctor."])
        r2 = (" " + ", ".join(parts)) if parts else ""
        return tpl.format(n=name, N=cap(name), r=rest, r2=r2, i=ind, H=self.He, o="her" if self.bp["sex"] == "F" else "him")

    def b_meds(self):
        bp, rng = self.bp, self.rng
        if bp["meds_none"]:
            q = self.say("D", self.r(T.D_MEDS_NONE))
            ref = self.ent("negative_findings", {"finding": "Regular medication", "normalized_name": "No regular medication",
                                                  "status": "absent", "assertion": "negative", "reported_by": "patient",
                                                  "temporality": "current", "evidence_ids": [], "confidence": 1.0})
            self.lit("regular medication")
            a = self.say("P", self.r(T.P_MEDS_NONE))
            self.tag([ref], q, a)
            return
        q = self.say("D", self.r(T.D_MEDS) + self.delab(.3))
        for m in bp["meds"]:
            who = m["reporter"]
            if m["status"] == "discontinued":
                ref = self.med_ent(m)
                a = self.say("P", self.r(["I used to take {n}, but I stopped it.", "I was on {n} before. I stopped taking it.",
                                          "I'd been on {n}, not any more though, I stopped."]).format(n=m["name"]))
                self.tag([ref], q, a)
                continue
            if "name_forgotten" in m["flags"]:
                ref = self.med_ent(m, name=m["desc"], normalized=None, generic=None)
                self.get(ref)["name"] = m["desc"]
                self.lit(m["desc"])
                a1 = self.say("P", f"It's a... um, I can't remember what it's called. It's a {m['desc']}.", gap=rng.uniform(1, 2.3))
                self.get(ref)["indication"] = m["ind"].replace("my ", "").replace("the ", "")
                self.lit(m["ind"])
                q2 = self.say("D", "Do you remember what it's for?")
                a2 = self.say("P", f"For {m['ind']}, I believe. My {rng.choice(['daughter', 'wife', 'husband', 'son'] )} sets them out for me, I just take what I'm given.")
                self.tag([ref], q, a1, q2, a2)
                self.unc("incomplete_medication_name", f"Patient could not name the {m['desc']} (taken for {m['ind'].replace('my ', '')}); drug name and dose unknown.",
                         [ref], [a1, q2, a2])
                self.ambig.append(ref)
                continue
            ref = self.med_ent(m, reporter=who)
            if "discrepancy" in m["flags"]:
                other = m["other"]
                a = self.say("P", self.med_say(m, ref, "P"))
                dose2 = spoken_dose(m["dose2"])
                self.lit(dose2)
                if other == "N":
                    b = self.say("N", f"Doctor, our chart from the last visit lists it as {dose2}.")
                else:
                    b = self.say(other, f"Doctor, I think the last prescription for the {m['name']} was {dose2}. We changed it at the last visit.")
                c = self.say("D", self.r(T.D_RXQ))
                d = self.say("P", self.r(["Not with me. I'll bring it next time.", "No, I left it at home.", "I don't think I have it with me."]))
                self.get(ref)["dose"] = None
                self.tag([ref], q, a, b, c, d)
                p_dose = spoken_dose(m["dose"])
                self.unc("medication_discrepancy",
                         f"{m['name']}: patient states {m['dose']}; {ROLE[other].lower().replace('_', ' ')} states {m['dose2']}. Current dose not established.",
                         [ref], [a, b, c, d])
                self.contra.append(f"{m['name']} dose: patient {m['dose']} vs {ROLE[other].lower().replace('_', ' ')} {m['dose2']} (unresolved).")
                continue
            if "dose_uncertain" in m["flags"]:
                txt = self.med_say(m, ref, who, tentative=True)
                a = self.say(who, txt)
                c = self.say("D", self.r(T.D_PACKET))
                d = self.say(who if who != "P" else "P", self.r(["Not with me. I'll bring it next time.", "No, it's at home."]))
                self.tag([ref], q, a, c, d)
                self.unc("uncertain_dose", f"{m['name']}: dose ({m['dose']}) was given tentatively (\"maybe\") and not verified.", [ref], [a, c, d])
                continue
            if m["dose"] and rng.random() < .15:
                saved = m["dose"]
                txt = self.med_say(m, ref, who, drop_dose=True)
                a = self.say(who, txt)
                qd = self.say("D", self.r(T.D_DOSE))
                self.get(ref)["dose"] = saved
                dose = spoken_dose(saved)
                self.lit(dose)
                ad = self.say(who, self.r(["{d}.", "It's {d}.", "{d}, I think that's what's on the box."]).format(d=dose))
                self.tag([ref], q, a, qd, ad)
            else:
                a = self.say(who, self.med_say(m, ref, who) + self.elab("P" if who == "P" else "x", .25))
                self.tag([ref], q, a)
            if m["dur"]:
                qq = self.say("D", "How long have you been on it?")
                self.get(ref)["duration"] = {"value": m["dur"][1], "unit": m["dur"][2], "normalized": m["dur"][3]}
                self.lit(m["dur"][0])
                aa = self.say(who, self.r(["About {d}.", "{D} now.", "For {d}."]).format(d=m["dur"][0], D=cap(m["dur"][0])))
                self.tag([ref], qq, aa)
            self.bc(.08)

    def b_allergy(self):
        bp, rng = self.bp, self.rng
        q = self.say("D", self.r(T.D_ALLERGY) + self.delab(.25))
        al = bp["allergies"]
        if al["kind"] == "none":
            ref = self.ent("negative_findings", {"finding": "Allergies", "normalized_name": "No known allergies", "status": "absent",
                                                  "assertion": "negative", "reported_by": "patient", "temporality": "current",
                                                  "evidence_ids": [], "confidence": 1.0})
            self.lit("allergies")
            a = self.say("P", self.r(T.P_NKA))
            self.tag([ref], q, a)
        elif al["kind"] == "uncertain":
            it = al["items"][0]
            self.lit(it["sub"])
            ref = self.ent("allergies", {"substance": it["sub"], "normalized_substance": it["norm"], "allergy_type": "medication",
                                         "reaction": None, "severity": "unknown", "status": "uncertain", "reported_by": "patient",
                                         "evidence_ids": [], "confidence": .6})
            a = self.say("P", self.r(T.P_ALLERGY_UNC).format(s=it["sub"]))
            self.tag([ref], q, a)
            self.unc("allergy_uncertain", "Patient reports a possible reaction to an antibiotic but cannot name the drug or the reaction.", [ref], [q, a])
        else:
            for it in al["items"]:
                self.lit(it["sub"], it.get("reaction"))
                ref = self.ent("allergies", {"substance": it["sub"], "normalized_substance": it["norm"], "allergy_type": it["type"],
                                             "reaction": it.get("reaction"), "severity": "unknown", "status": "reported",
                                             "reported_by": "patient", "evidence_ids": [], "confidence": 1.0})
                if it.get("reaction"):
                    a = self.say("P", self.r(T.P_ALLERGY).format(s=it["sub"], S=cap(it["sub"]), r=it["reaction"]))
                else:
                    a = self.say("P", self.r(T.P_ALLERGY_NR).format(s=it["sub"], S=cap(it["sub"])))
                self.tag([ref], q, a)

    # ---------------------------------------------------------------- vitals
    def vital_text(self, v):
        n, _, val, unit = v
        if n == "Blood pressure":
            a, b = str(val).split("/")
            return self.r([f"blood pressure {a} over {b}", f"BP is {a} over {b}", f"pressure {a} over {b}"])
        if n == "Heart rate":
            return self.r([f"heart rate {val}", f"pulse {val}", f"pulse is {val} beats a minute"])
        if n == "Temperature":
            return self.r([f"temperature {val}", f"temp {val} degrees", f"temperature is {val} degrees"])
        if n == "Oxygen saturation":
            return self.r([f"saturation {val} percent", f"SpO2 {val} percent on room air", f"oxygen saturation is {val} percent"])
        if n == "Respiratory rate":
            return f"respiratory rate {val}"
        if n == "Weight":
            return f"weight {val} kilos"
        if n == "Height":
            return f"height {val} centimetres"
        return f"BMI works out to {val}"

    def b_vitals(self):
        bp, rng = self.bp, self.rng
        vit = bp["vitals"]
        if not vit:
            return
        by = bp["vitals_by"]
        refs = []
        for v in vit:
            refs.append(self.ent("vital_signs", {"name": v[0], "normalized_name": v[1], "value": v[2], "unit": v[3],
                                                  "reported_by": ROLE[by].lower(), "evidence_ids": [], "confidence": 1.0}))
        groups = [list(range(len(vit)))]
        if len(vit) > 3 and rng.random() < .5:
            k = rng.choice([2, 3])
            groups = [list(range(k)), list(range(k, len(vit)))]
        if by == "D":
            self.say("D", self.r(T.D_VIT_START))
            self.say("D", self.r(T.D_VIT_READ), gap=rng.uniform(6, 14))
            first = True
            for g in groups:
                txt = ", ".join(self.vital_text(vit[i]) for i in g)
                t = self.say("D", ("Okay: " if first else "And ") + txt + ".", [refs[i] for i in g], gap=rng.uniform(9, 22) if first else None, hum=False)
                first = False
            if rng.random() < .5:
                self.say("P", self.r(["Is that okay?", "Is that normal?", "Is that alright, doctor?"]))
                self.say("D", "We'll put it in context in a moment.")
        else:
            self.say("N", self.r(T.N_VIT_INTRO), hum=False)
            for g in groups:
                txt = ", ".join(self.vital_text(vit[i]) for i in g)
                self.say("N", cap(txt) + ".", [refs[i] for i in g], hum=False)
            self.say("D", self.r(["Thanks.", "Okay, noted.", "Good, thank you."]))

    # ------------------------------------------------------------------ exam
    def b_exam(self):
        bp, rng = self.bp, self.rng
        if not bp["exam"]:
            return
        self.say("D", self.r(T.D_EXAM_INTRO), gap=rng.uniform(1, 3))
        self.ack(T.P_OK, .5)
        for k, ex in enumerate(bp["exam"]):
            refs = []
            for f in ex["findings"]:
                refs.append(self.ent("physical_examination", {"finding": f[0][:1].upper() + f[0][1:], "normalized_finding": f[1],
                                                               "body_site": f[2], "status": f[3], "observed_by": "doctor",
                                                               "evidence_ids": [], "confidence": 1.0}))
                self.lit(f[0])
            self.say("D", self.r(T.EXAM_STEPS),
                     gap=rng.uniform(.8, 2.0))
            self.say("D", ex["stmt"], refs, gap=rng.uniform(7, 19), hum=False)
            if rng.random() < .25:
                self.say("P", self.r(T.P_OK))
        self.say("D", self.r(T.D_EXAM_DONE) + (" " + self.r(T.EXAM_EXPLAIN) if rng.random() < .6 else ""), gap=rng.uniform(2, 6))

    # ------------------------------------------------------------ assessment
    def b_assess(self):
        bp, rng = self.bp, self.rng
        a = bp["assess"]
        pa = strip_art(a["primary"])
        self.lit(pa)
        ref = self.ent("clinical_assessment", {"assessment": pa, "normalized_assessment": cap(pa), "certainty": "provisional",
                                                "basis": None, "stated_by": "doctor", "evidence_ids": [], "confidence": 1.0})
        self.assess_ref = ref
        intro = self.r(T.ASSESS_INTRO if bp["exam"] else T.ASSESS_INTRO_NOEXAM)
        prim = self.r(T.ASSESS_PRIM).format(a=a["primary"])
        t1 = self.say("D", intro + " " + (prim if intro.endswith(",") else cap(prim)) + (" " + self.r(T.ASSESS_EL if bp["exam"] else T.ASSESS_EL_NOEXAM) if rng.random() < .6 else ""), [ref], hum=False)
        refs = [ref]
        for d in a["diffs"]:
            dd = strip_art(d)
            self.lit(dd)
            r2 = self.ent("clinical_assessment", {"assessment": dd, "normalized_assessment": cap(dd), "certainty": "differential",
                                                   "basis": None, "stated_by": "doctor", "evidence_ids": [], "confidence": 1.0})
            self.say("D", cap(self.r(T.ASSESS_DIFF).format(d=d, D=cap(d))) if False else self.r(T.ASSESS_DIFF).format(d=d, D=cap(d)), [r2], hum=False)
            refs.append(r2)
        if rng.random() < .55:
            q = self.say("P", self.r(T.CONCERN_Q))
            inv = bp["inv"][0]["name"] if bp["inv"] else None
            if inv:
                ans = self.r(T.CONCERN_A).format(a=a["primary"], i=inv)
            else:
                ans = self.r(T.CONCERN_A_NOINV).format(a=a["primary"])
            d = self.say("D", ans, [ref], hum=False)
            self.tag([ref], d)
        self.assess_refs = refs

    # ------------------------------------------------------------------ plan
    def action(self, typ, desc, status, resp, tr=None):
        d = {"action_type": typ, "description": desc, "status": status, "responsible_person": resp, "time_reference": tr,
             "evidence_ids": [], "confidence": 1.0}
        return self.ent("clinical_actions", d)

    def b_plan(self):
        bp, rng = self.bp, self.rng
        for iv in bp["inv"]:
            self.lit(iv["name"])
            if iv["status"] == "completed" and iv["done_by"] == "P":
                q = self.say("D", self.r(T.D_PREV_INV))
                pref = self.ent("procedures_and_investigations", {"name": iv["name"], "normalized_name": iv["norm"], "type": iv["type"],
                                                                   "status": "completed", "requested_by": None, "indication": None,
                                                                   "scheduled_datetime": None, "evidence_ids": [], "confidence": 1.0})
                a = self.say("P", self.r(T.P_PREV_INV).format(n=iv["name"], w=iv["prev_when"]))
                self.tag([pref], q, a)
                continue
            if iv["status"] == "completed":
                pref = self.ent("procedures_and_investigations", {"name": iv["name"], "normalized_name": iv["norm"], "type": iv["type"],
                                                                   "status": "completed", "requested_by": "doctor", "indication": None,
                                                                   "scheduled_datetime": None, "evidence_ids": [], "confidence": 1.0})
                aref = self.action("investigation", f"{iv['norm']} performed before the consultation", "completed", "nurse")
                t = self.say("N", self.r(T.N_DONE).format(n=iv["name"]), [pref, aref], hum=False)
                self.say("D", self.r(T.D_DONE_ACK))
                continue
            pref = self.ent("procedures_and_investigations", {"name": iv["name"], "normalized_name": iv["norm"], "type": iv["type"],
                                                               "status": "planned", "requested_by": "doctor", "indication": iv["ind"],
                                                               "scheduled_datetime": None, "evidence_ids": [], "confidence": 1.0})
            aref = self.action("investigation", f"Arrange {iv['norm']}", "planned", "doctor")
            self.lit(iv["ind"])
            t = self.say("D", self.r(T.D_INV).format(n=iv["name"], i=iv["ind"]) + (" " + self.r(T.INV_EL) if rng.random() < .6 else ""), [pref, aref], hum=False)
            if iv["sched"]:
                w, tm = iv["sched"]
                self.lit(w, tm)
                s_ = self.say("S", self.r(T.S_APPT).format(w=w, t=tm), [pref], hum=False)
                self.get(pref)["scheduled_datetime"] = f"{w} at {tm}"
                self.get(aref)["responsible_person"] = "clinical_staff"
                self.tag([aref], s_)
                self.ack(T.P_APPT, .5, W=w)
            else:
                self.ack(T.P_INV_OK, .35)
        for rx in bp["rx"]:
            parts = []
            dose = spoken_dose(rx["dose"]) if rx["dose"] else ""
            if dose:
                parts.append(dose)
            if rx["freq"]:
                parts.append(rx["freq"])
            dobj, dsp = dur_obj(rx["dur"])
            parts.append(dsp)
            name = rx["name"]
            desc = name.lower() in __import__("blueprint").DESCRIPTORS
            m = {"name": name, "generic": rx["generic"]}
            ref = self.med_ent(m, status="planned", reporter="D")
            e = self.get(ref)
            e["dose"] = rx["dose"]
            e["frequency"] = rx["freq"]
            e["duration"] = dobj
            e["indication"] = rx["ind"]
            self.lit(dose, rx["freq"], dsp, rx["ind"])
            route_w = {"topical": "Apply it", "inhaled": "Use it", "nasal": "Spray it", "ophthalmic": "Put the drops in the eye", "sublingual": "Put it under the tongue", "transdermal": "Stick the patch on"}
            rw = None
            if rx["route"] in route_w:
                e["route"] = rx["route"]
            elif rx["route"] == "oral" and rng.random() < .35:
                e["route"] = "oral"
            rest = ", " + ", ".join(parts)
            tpl = self.r(["I'll start you on {n}{r}.", "Let's use {n}{r}.", "I'd like you to take {n}{r}.", "I'm prescribing {n}{r}."])
            txt = tpl.format(n=name, r=rest)
            if e["route"] == "oral":
                txt += " You take it by mouth."
            elif e["route"] in route_w:
                kw = {"topical": "on the skin", "inhaled": "as an inhaler", "nasal": "into the nose", "ophthalmic": "in the eye",
                      "sublingual": "under the tongue", "transdermal": "as a patch"}[e["route"]]
                txt += f" That's {kw}." if False else ""
                e["route"] = None if e["route"] != rx["route"] else None
            txt += self.r(T.D_RX_IND).format(i=rx["ind"])
            if rng.random() < .5:
                txt += " " + self.r(T.RX_EL)
            aref = self.action("medication", f"Start {rx['generic']}" + (f" {rx['dose']}" if rx["dose"] else "") + (f" {rx['freq']}" if rx["freq"] else ""),
                               "planned", "doctor")
            self.say("D", txt, [ref, aref], hum=False)
            self.ack(T.P_RX_OK, .4)
        for cnt in bp["counsel"]:
            aref = self.action("counselling", cnt[1], "planned", "patient")
            self.say("D", cnt[0], [aref], hum=False)
            self.bc(.08)
        for rf in bp["refs"]:
            aref = self.action("referral", rf[1], "planned", "doctor")
            self.say("D", self.r(T.D_REFER).format(r=rf[0]), [aref], hum=False)
            self.ack(["Okay.", "Alright, thank you.", "Sure, where do I go?"], .5)
        if bp["bring_rx"]:
            aref = self.action("other", "Bring latest prescription or medication box to next visit", "planned", "patient")
            self.say("D", "And please bring the latest prescription or the medicine boxes to the next visit, so we can settle the dose.", [aref], hum=False)
            self.say("P", "Okay, I will.")
        # safety net
        aref = self.action("counselling", f"Seek urgent care if {bp['red']}", "planned", "patient")
        self.say("D", self.r(CC.SAFETY).format(red=bp["red"]), [aref], hum=False)
        self.ack(T.P_UNDERSTOOD, .6)
        # follow-up
        fu = bp["fu"]
        status = "conditional" if fu.startswith("if ") else "planned"
        self.lit(fu)
        fref = self.ent("follow_up", {"type": "consultation", "time_reference": fu, "normalized_datetime": None, "status": status, "evidence_ids": []})
        aref = self.action("follow_up", "Follow-up consultation", status, "doctor", {"value": fu, "normalized_date": None})
        self.say("D", self.r(T.D_FU).format(t=fu), [fref, aref], hum=False)
        if "S" in self.combo and not any(iv["sched"] for iv in bp["inv"]):
            s_ = self.say("S", f"I'll book your follow-up at the front desk on your way out.", [fref, aref], hum=False)
        self.ack(T.P_FU_OK, .6)
        self.fu_ref, self.fu_act = fref, aref

    def ack(self, pool, p=.4, **kw):
        if self.rng.random() < p:
            self.say("P", self.r(pool).format(**kw) if kw else self.r(pool))

    def b_close(self):
        self.say("D", self.r(T.CLOSE_D))
        self.say("P", self.r(T.CLOSE_P))
        if self.rng.random() < .5:
            self.say("D", self.r(T.CLOSE_D2))

    # --------------------------------------------------------------- fillers
    def f_rapport(self):
        a, b = self.r(T.RAPPORT)
        self.say("D", a)
        self.say("P", b)

    def f_chat(self, k=None):
        a, b = T.CONTEXT_CHAT[k] if k is not None else self.r(T.CONTEXT_CHAT)
        self.say("D", a)
        self.say("P", b)

    def f_records(self, k=None):
        a, b = T.RECORDS_CHECK[k] if k is not None else self.r(T.RECORDS_CHECK)
        self.say("D", a, gap=self.rng.uniform(.5, 1.5))
        self.say("P", b, gap=self.rng.uniform(.3, .9))
        self.say("D", self.r(["Okay, here we go.", "Alright, I've got it.", "Right, thanks for waiting."]), gap=self.rng.uniform(6, 16))

    def f_recap(self):
        bp = self.bp
        s0 = bp["syms"][0]
        refs = [self.cc and ("chief_complaint", None)] if False else []
        if s0.get("cc_only") or 0 not in self.symref:
            return
        ref = self.symref[0]
        dur = f" for {s0['dur'][0]}" if s0["dur"] else (f", {s0['onset']}" if s0["onset"] and not s0["uncertain_onset"] else "")
        sev = f", {s0['sev']}" if s0["sev"] and "/" not in s0["sev"] else ""
        negs = [strip_art(n[0]) for n in bp["negs"][:2] if bp["neg_dispute"] is None or n != bp["negs"][bp["neg_dispute"]]]
        nref = [r for r in range(len(self.S["negative_findings"])) if self.S["negative_findings"][r]["finding"].lower() in [x.lower() for x in negs]]
        txt = f"Let me just recap so I've got it right. You've had {yours(s0['phrase'])}{dur}{sev}" if s0["kind"] == "noun" else \
            f"Let me just recap so I've got it right. You've been {yours(s0['phrase'])}{dur}{sev}"
        if negs:
            txt += f", and no {jor(negs)}"
        txt += "."
        t = self.say("D", txt, [ref] + [("negative_findings", r) for r in nref], hum=False)
        u = self.say("P", self.r(["Yes, that's right.", "That's it, yes.", "Exactly, that's what's been happening.", "Yes, you've got it."]))
        self.tag([ref] + [("negative_findings", r) for r in nref], u)

    def f_teach(self):
        bp = self.bp
        if not self.S["clinical_actions"]:
            return
        acts = [("clinical_actions", i) for i, a in enumerate(self.S["clinical_actions"]) if a["action_type"] in ("medication", "follow_up")][:2]
        if not acts:
            return
        meds = [a for a in acts if self.get(a)["action_type"] == "medication"]
        pieces = []
        refs = list(acts)
        for a in acts:
            d = self.get(a)
            if d["action_type"] == "medication":
                nm = d["description"].replace("Start ", "")
                mref = [i for i, m in enumerate(self.S["medications"]) if m["status"] == "planned" and nm.lower().startswith(m["generic_name"].lower() if m["generic_name"] else m["name"].lower())]
                for i in mref[:1]:
                    refs.append(("medications", i))
                    m = self.S["medications"][i]
                    pieces.append(f"take the {m['name']}" + (f", {spoken_dose(m['dose'])}" if m["dose"] else "") + (f", {m['frequency']}" if m["frequency"] else ""))
            else:
                pieces.append(f"come back {self.bp['fu']}")
        if not pieces:
            return
        q = self.say("D", self.r(T.TEACH_Q))
        t = self.say("P", "So, I " + " and ".join(pieces) + ". Is that right?")
        c = self.say("D", "Yes, exactly right.")
        self.tag(refs, q, t, c)

    def f_repeat(self):
        meds = [i for i, m in enumerate(self.S["medications"]) if m["status"] == "currently_used" and m["dose"] and m["reported_by"] == "patient"
                and not any(i in [r[1] for r in u["_rel"]] for u in self.S["clinical_uncertainties"])]
        if not meds:
            return
        i = self.rng.choice(meds)
        m = self.S["medications"][i]
        q = self.say("D", f"Just to be sure I've got this right, the {m['name']}, what dose was that again?")
        dose = spoken_dose(m["dose"])
        a = self.say("P", self.r(["{d}, like I said.", "It's {d}.", "{d}. Yes."]).format(d=dose))
        self.tag([("medications", i)], q, a)

    def f_explain(self, k=None):
        k = self.rng.randrange(len(T.EXPLAIN)) if k is None else k
        self.say("D", T.EXPLAIN[k], hum=False)
        self.say("P", T.EXPLAIN_R[k])

    def f_life(self, k=None):
        a, b = T.LIFE[k] if k is not None else self.r(T.LIFE)
        self.say("D", a)
        self.say("P", b)

    def f_hold(self, k=None):
        self.say("D", self.r(T.HOLD_A),
                 gap=self.rng.uniform(.5, 1.2))
        self.say("D", self.r(T.HOLD_B), gap=self.rng.uniform(8, 18))

    def f_unknown(self):
        """an utterance that cannot be attributed to any known speaker"""
        if self.unknown_done:
            return
        self.unknown_done = True
        refs = []
        t0 = getattr(self, "unc_turn", None)
        if t0 is None:
            return
        # attach to the entities supported by that earlier patient turn
        for p in PATHS:
            for i, e in enumerate(self.S[p]):
                if t0 in e["_t"] and p in ("symptoms",):
                    refs.append((p, i))
        u = self.say("U", self.r(["Yes, that's right, that's how it was.", "Mm, that's what happened, yes.", "Yes, exactly like that."]), hum=False)
        self.tag(refs, u)
        for rf in refs[:1]:
            self.ambig.append(rf)
        self.unc("unknown_speaker", "A confirming remark about the symptom timeline could not be attributed to any identified speaker.",
                 refs[:1], [u], "unresolved") if refs else None
        self.say("D", "Sorry, who said that? Never mind, let's move on.") if False else None

    # ----------------------------------------------------------------- build
    def build(self):
        bp, rng = self.bp, self.rng
        has_unknown = "unknown_speaker" in self.feats
        hist = ["pmh", "surg", "fam", "soc", "meds", "allergy"]
        order = [h for h in hist if not (h == "fam" and not bp["fam"]) and not (h == "soc" and not bp["soc"])
                 and not (h == "surg" and not (bp["surg"] or bp["surg_none"]))]
        rng.shuffle(order)
        blocks = [("open", self.b_open), ("narr", self.b_narrative), ("negs", self.b_negs)]
        if bp["vitals_by"] == "N" and rng.random() < .5:
            blocks.append(("vitals", self.b_vitals))
        fn = dict(pmh=self.b_pmh, surg=self.b_surg, fam=self.b_fam, soc=self.b_soc, meds=self.b_meds, allergy=self.b_allergy)
        for h in order:
            blocks.append((h, fn[h]))
        if not any(b[0] == "vitals" for b in blocks):
            blocks.append(("vitals", self.b_vitals))
        blocks += [("exam", self.b_exam), ("assess", self.b_assess), ("plan", self.b_plan)]
        variants = ([(self.f_chat, k) for k in range(len(T.CONTEXT_CHAT))] + [(self.f_records, k) for k in range(len(T.RECORDS_CHECK))]
                    + [(self.f_explain, k) for k in range(len(T.EXPLAIN))] + [(self.f_life, k) for k in range(len(T.LIFE))]
                    + [(self.f_hold, None), (self.f_repeat, None)])
        picks = rng.sample(variants, min(self.F, len(variants)))
        mid_fill = [(lambda f=f, k=k: f(k) if k is not None else f()) for f, k in picks]
        self.F_eff = len(mid_fill)
        pos = sorted(rng.sample(range(2, len(blocks) + 1), min(len(mid_fill), len(blocks) - 1))) if mid_fill else []
        pos_map = defaultdict(list)
        for p, f in zip(pos, mid_fill):
            pos_map[p].append(f)
        for bi, (name, f) in enumerate(blocks):
            if bi in pos_map:
                for ff in pos_map[bi]:
                    ff()
            f()
            if name == "narr" and has_unknown:
                self.f_unknown()
            if name == "assess" and self.F >= 2:
                self.f_recap()
            if name == "plan" and self.F >= 3:
                self.f_teach()
        if has_unknown and not self.unknown_done:
            self.f_unknown()
        self.b_close()
        return self

    # -------------------------------------------------------------- finalise
    def timeline(self):
        rng = self.rng
        t = round(rng.uniform(.5, 1.4), 2)
        out = []
        for i, tn in enumerate(self.turns):
            words = len(re.findall(r"[\w'’-]+", tn["text"]))
            hes = len(re.findall(r"\b(um|uh|hmm)\b", tn["text"], flags=re.I))
            rate = RATE[tn["who"]] * rng.uniform(.88, 1.12)
            if self.bp["style"] in ("hesitant", "anxious") and tn["who"] in "PCF":
                rate *= .92
            dur = max(.7, words / rate + .12 * tn["text"].count(",") + .35 * hes + (.5 if "…" in tn["text"] or "—" in tn["text"] else 0))
            if i == 0:
                start = t
            else:
                gap = tn["gap"] if tn["gap"] is not None else rng.uniform(.3, 1.6)
                if tn["gap"] is None and rng.random() < .07:
                    gap += rng.uniform(1.5, 3.5)
                start = t + gap
            start = round(start, 2)
            end = round(start + dur, 2)
            out.append((start, end))
            t = end
        return out

    @staticmethod
    def ts(x):
        s = int(x)
        return f"{s // 60:02d}:{s % 60:02d}"

    def merge_turns(self):
        out, remap = [], {}
        for i, tn in enumerate(self.turns):
            prev = out[-1] if out else None
            if (prev and prev["who"] == tn["who"] and tn["gap"] is None and prev["who"] in "DPNCFS"
                    and not prev["text"].rstrip().endswith(("?", "—", "…"))
                    and len(prev["text"].split()) + len(tn["text"].split()) <= 78):
                prev["text"] += " " + tn["text"]
                remap[i] = len(out) - 1
            else:
                out.append(dict(tn))
                remap[i] = len(out) - 1
        self.turns = out
        ents = [self.cc] if self.cc else []
        for p in PATHS:
            ents += self.S[p]
        for e in ents:
            e["_t"] = {remap[t] for t in e["_t"]}

    def finalize(self, enc_id):
        bp = self.bp
        self.merge_turns()
        times = self.timeline()
        spk = {}
        for tn in self.turns:
            if tn["who"] not in spk:
                spk[tn["who"]] = f"person_{len(spk) + 1}"
        segs = []
        for i, (tn, (s, e)) in enumerate(zip(self.turns, times)):
            segs.append({"segment_id": f"SEG{i + 1:04d}", "speaker_id": spk[tn["who"]], "role": ROLE[tn["who"]],
                         "start_seconds": s, "end_seconds": e, "duration_seconds": round(e - s, 2), "text": tn["text"]})
        inp = {"schema_version": "1.0", "encounter_id": enc_id, "segments": segs}
        # evidence
        ev_turns = sorted({t for p in PATHS for e in self.S[p] for t in e["_t"]} | (self.cc["_t"] if self.cc else set()))
        evid = {t: f"EV_{k + 1:03d}" for k, t in enumerate(ev_turns)}
        sup = defaultdict(list)

        def loc(p, i):
            return p if p == "chief_complaint" else f"{p}[{i}]"
        if self.cc:
            for t in self.cc["_t"]:
                sup[t].append("chief_complaint")
        for p in PATHS:
            for i, e in enumerate(self.S[p]):
                for t in e["_t"]:
                    sup[t].append(loc(p, i))
        evidence = []
        for t in ev_turns:
            tn, sg = self.turns[t], segs[t]
            evidence.append({"evidence_id": evid[t], "speaker_id": sg["speaker_id"], "speaker_role": ROLE[tn["who"]].lower(),
                             "transcript_text": sg["text"], "start_timestamp": self.ts(sg["start_seconds"]),
                             "end_timestamp": self.ts(sg["end_seconds"]), "supports": sup[t]})

        def clean(e):
            e = {k: v for k, v in e.items() if not k.startswith("_")}
            return e

        def fin(e):
            d = clean(e)
            d["evidence_ids"] = [evid[t] for t in sorted(e["_t"])]
            return d
        # resolve uncertainty relations
        for e in self.S["clinical_uncertainties"]:
            e["related_entities"] = [loc(*r) for r in e["_rel"]]
        L = {p: [fin(e) for e in self.S[p]] for p in PATHS}
        cc = fin(self.cc)
        # extraction-order for cc
        cc = {"value": cc["value"], "normalized_value": cc["normalized_value"], "reported_by": cc["reported_by"],
              "evidence_ids": cc["evidence_ids"]}
        present = [r for r in spk]
        speakers = [{"speaker_id": spk[k], "role": ROLE[k].lower(), "role_confidence": .5 if k == "U" else 1.0} for k in spk]
        syms = L["symptoms"]
        temporal = any(s["duration"] or s["onset"] or s["temporality"] != "current" for s in syms) or bool(L["medical_history.past_medical_history"])
        amb = [loc(*r) for r in self.ambig]
        quality = {"negation_detected": bool(L["negative_findings"]), "temporality_detected": temporal,
                   "speaker_attribution_available": "U" not in spk, "unsupported_clinical_claims": [],
                   "contradictions_detected": self.contra, "ambiguous_entities": amb,
                   "requires_clinician_review": bool(L["clinical_uncertainties"] or self.contra or amb)}
        for k in ("confidence",):
            pass
        label = {"encounter_id": enc_id, "extraction_status": "completed",
                 "encounter_metadata": {"encounter_date": None, "encounter_type": "outpatient_consultation", "language": "en",
                                        "primary_speakers": speakers},
                 "chief_complaint": cc, "symptoms": L["symptoms"], "negative_findings": L["negative_findings"],
                 "medical_history": {"past_medical_history": L["medical_history.past_medical_history"],
                                     "surgical_history": L["medical_history.surgical_history"],
                                     "family_history": L["medical_history.family_history"],
                                     "social_history": L["medical_history.social_history"]},
                 "medications": L["medications"], "allergies": L["allergies"], "vital_signs": L["vital_signs"],
                 "physical_examination": L["physical_examination"], "review_of_systems": L["review_of_systems"],
                 "clinical_conditions": L["clinical_conditions"], "clinical_assessment": L["clinical_assessment"],
                 "procedures_and_investigations": L["procedures_and_investigations"], "clinical_actions": L["clinical_actions"],
                 "follow_up": L["follow_up"], "clinical_uncertainties": L["clinical_uncertainties"],
                 "clinical_evidence": evidence, "quality_checks": quality}
        return inp, label, segs[-1]["end_seconds"], len(segs)
