"""S0 deterministic repair layer (version S0.1.0).  Pure library: no file I/O, no model, no network.

What S0 does: fixes STRUCTURE and REPRESENTATION of a stored Stage-1 extraction (JSON) using only exact, deterministic rules, and logs every change.
What S0 never does: correct clinical content (medicine identity/dose/frequency/route, allergy identity, positive vs negative, polarity, diagnosis, follow-up meaning). Those are only FLAGGED.

Rules (approved scope):  A object->list for clinical_assessment/follow_up | B exact role-enum aliases (case/space), unknown values flagged | C allergy placeholders (never read as confirmed absence
unless the transcript states it explicitly) | D datetimes without transcript support -> null (original kept in the log) | E reported_by derived from a verified cited transcript segment | F flags only | G log.
Frozen schema untouched: S0 adds no field; allergy status categories live in the log, not in the JSON."""
from __future__ import annotations

import copy
import re

S0_VERSION = "S0.1.0"
ROLES = {"doctor", "patient", "nurse", "caregiver", "family_member", "clinical_staff", "unknown"}
RESP_ROLES = {"doctor", "patient", "nurse", "clinical_staff"}
ROLE_ALIAS = {r: r for r in ROLES}
ROLE_ALIAS.update({"family member": "family_member", "family-member": "family_member", "clinical staff": "clinical_staff", "clinical-staff": "clinical_staff"})
ROLE_FIELDS = ("reported_by", "observed_by", "stated_by", "requested_by", "responsible_person")
SHAPE_SECTIONS = {"clinical_assessment": {"assessment", "normalized_assessment"}, "follow_up": {"type", "time_reference", "status", "normalized_datetime"}}   # identifying fields
SHAPE_KEYS = {"clinical_assessment": {"assessment", "normalized_assessment", "certainty", "basis", "stated_by", "evidence_ids", "confidence"},
              "follow_up": {"type", "time_reference", "normalized_datetime", "status", "evidence_ids"}}   # frozen-schema key sets of the two sections
LIST_SECTIONS = ["symptoms", "negative_findings", "medications", "allergies", "vital_signs", "physical_examination", "review_of_systems", "clinical_conditions", "clinical_assessment",
                 "procedures_and_investigations", "clinical_actions", "follow_up", "clinical_uncertainties"]
HIST = ["past_medical_history", "surgical_history", "family_history", "social_history"]
# patient-origin sections for rule E: reported_by is the speaker who verbally supplied the fact (see REPORTED_BY_SEMANTICS.md)
RULE_E_SECTIONS = ["symptoms", "negative_findings", "medications", "allergies", "vital_signs", "medical_history.past_medical_history", "medical_history.surgical_history",
                   "medical_history.family_history", "medical_history.social_history"]
PLACEHOLDER_SUBSTANCE = {"none", "no", "nil", "n/a", "na", "no known allergies", "no allergies", "nka", "nkda", ""}
ALLERGY_Q = re.compile(r"allerg|reacted badly|react to", re.I)
DENY = re.compile(r"\b(no allergies|no known|none that i know|not that i know|nothing i'm aware|as far as i'?m aware|never been told i have|never had an allerg|not allergic|don't have any known)\b|^(no|nope|none|nothing)\b", re.I)
DENY_BLOCK = re.compile(r"\b(but|except|apart|although|yes|reaction|rash|hives|swelling|antibiotic|sometimes|maybe|not sure|can't remember|couldn't)\b", re.I)
ISO = re.compile(r"\d{4}-\d{2}-\d{2}|T\d{2}:\d{2}")
TS_LIKE = re.compile(r"^\d+(\.\d+)?\s*s$", re.I)
EXAM_PHRASES = re.compile(r"\b(let me|i'll have a look|i'll examine|come over here|tell me if|bear with me|hold still|take your time|lift your|take a deep breath|a little pressure|i'll listen|let me just)\b", re.I)
RETURN_VISIT = re.compile(r"come back|see you again|see me again|review|another look|back in|next visit|catch up|follow[- ]?up|after the (scan|results|test)", re.I)
ROUTES = {"oral", "topical", "inhaled", "nasal", "ophthalmic", "otic", "sublingual", "transdermal", "intramuscular", "intravenous", "subcutaneous", "rectal", "vaginal"}
PRESCRIBE = re.compile(r"(?:let's use|i'll start you on|i'm prescribing|we'll begin with|what i'm giving you is|the treatment will be|for this,|i'd like you to take|let's start)\s+([a-z0-9 \-]+?)(?:,|\s\d)", re.I)


def toks(text):
    return re.findall(r"[a-z0-9']+", str(text).lower().replace("’", "'"))


class Log:
    def __init__(self, enc):
        self.enc, self.rows = enc, []

    def add(self, kind, path, original, repaired, rule, reason, deterministic=True, review=False):
        self.rows.append({"encounter_id": self.enc, "kind": kind, "path": path, "original": original, "repaired": repaired, "rule": rule, "reason": reason,
                          "deterministic": deterministic, "human_review_required": review})


def _entities(pred):
    """yield (location, section_key, index, entity dict) for every dict item of the list sections and the history sections"""
    for sec in LIST_SECTIONS:
        v = pred.get(sec)
        if isinstance(v, list):
            for i, x in enumerate(v):
                if isinstance(x, dict):
                    yield f"{sec}[{i}]", sec, i, x
    mh = pred.get("medical_history")
    if isinstance(mh, dict):
        for sub in HIST:
            v = mh.get(sub)
            if isinstance(v, list):
                for i, x in enumerate(v):
                    if isinstance(x, dict):
                        yield f"medical_history.{sub}[{i}]", f"medical_history.{sub}", i, x
    if isinstance(pred.get("chief_complaint"), dict):
        yield "chief_complaint", "chief_complaint", 0, pred["chief_complaint"]


def _reindex(pred, section, mapping):
    """after adding/removing list items: rewrite location strings in clinical_evidence.supports and uncertainty references. mapping: old index -> new index or None (removed)."""
    def fix(loc):
        m = re.fullmatch(re.escape(section) + r"\[(\d+)\]", loc)
        if not m:
            return loc
        new = mapping.get(int(m.group(1)), int(m.group(1)))
        return None if new is None else f"{section}[{new}]"
    for ev in pred.get("clinical_evidence") or []:
        if isinstance(ev, dict) and isinstance(ev.get("supports"), list):
            ev["supports"] = [x for x in (fix(s) if isinstance(s, str) else s for s in ev["supports"]) if x is not None]
    for u in pred.get("clinical_uncertainties") or []:
        if isinstance(u, dict) and isinstance(u.get("related_entities"), list):
            u["related_entities"] = [x for x in (fix(s) if isinstance(s, str) else s for s in u["related_entities"]) if x is not None]
    qc = pred.get("quality_checks")
    if isinstance(qc, dict) and isinstance(qc.get("ambiguous_entities"), list):
        qc["ambiguous_entities"] = [x for x in (fix(s) if isinstance(s, str) else s for s in qc["ambiguous_entities"]) if x is not None]


# ------------------------------------------------------------------ rule A
def rule_a(pred, log):
    for sec, idf in SHAPE_SECTIONS.items():
        v = pred.get(sec)
        if not isinstance(v, dict):
            continue
        simple = all(not isinstance(x, (list, dict)) for k, x in v.items() if k != "evidence_ids")
        if v and (set(v) & idf) and simple and set(v) <= SHAPE_KEYS[sec]:
            pred[sec] = [v]
            for ev in pred.get("clinical_evidence") or []:
                if isinstance(ev, dict) and isinstance(ev.get("supports"), list):
                    ev["supports"] = [f"{sec}[0]" if s == sec else s for s in ev["supports"]]
            log.add("change", sec, "<object>", "[<object>] (one-item list)", "A_object_to_list", f"{sec} was a bare object with the item's own fields; wrapped into a one-element list, content unchanged")
        else:
            log.add("flag", sec, "<object>", "<object>", "A_ambiguous_object", f"{sec} is an object that is empty or not clearly one item; preserved unchanged", True, True)


# ------------------------------------------------------------------ rule B
def rule_b(pred, log):
    for loc, sec, i, x in _entities(pred):
        for f in ROLE_FIELDS:
            v = x.get(f)
            if not isinstance(v, str) or not v:
                continue
            canon = ROLE_ALIAS.get(v.strip().lower())
            allowed = RESP_ROLES if f == "responsible_person" else ROLES
            if canon and canon in allowed:
                if canon != v:
                    x[f] = canon
                    log.add("change", f"{loc}.{f}", v, canon, "B_exact_enum_alias", "same role value written with different case or a defined spelling alias")
            else:
                log.add("flag", f"{loc}.{f}", v, v, "B_unknown_enum_value", f"'{v}' is not an allowed {f} value; not converted (no semantic guessing)", True, True)


# ------------------------------------------------------------------ rule C
def allergy_status(segs):
    """Transcript-based status of the allergy question: explicit_no_known_allergies | unknown | not_assessed. Returns (status, answer_role, answer_segment_index, note)."""
    q = [k for k, s in enumerate(segs) if ALLERGY_Q.search(s["text"]) and s["role"].upper() in ("DOCTOR", "NURSE", "CLINICAL_STAFF")]
    if not q:
        return ("not_assessed" if not any(ALLERGY_Q.search(s["text"]) for s in segs) else "unknown"), None, None, "no clinician allergy question" if not any(ALLERGY_Q.search(s["text"]) for s in segs) else "allergy mentioned but no clinician question"
    k = q[0]
    ans = next((n for n in range(k + 1, min(k + 4, len(segs))) if segs[n]["role"].upper() not in ("DOCTOR", "NURSE", "CLINICAL_STAFF")), None)
    if ans is None:
        return "unknown", None, None, "allergy question without a reply"
    text = segs[ans]["text"].strip()
    other = [s for s in segs[ans + 1: ans + 4] if s["role"].upper() in ("CAREGIVER", "FAMILY_MEMBER") and re.search(r"react|allerg", s["text"], re.I)]
    if other:
        return "unknown", segs[ans]["role"].lower(), ans, "another speaker disputes or qualifies the answer"
    if DENY.search(text) and not DENY_BLOCK.search(text) and len(text.split()) <= 14:
        return "explicit_no_known_allergies", segs[ans]["role"].lower(), ans, "short explicit denial after the allergy question"
    return "unknown", segs[ans]["role"].lower(), ans, "answer is not an explicit denial"


def rule_c(pred, segs, log):
    al = pred.get("allergies")
    status = None
    if isinstance(al, list):
        keep, mapping, removed = [], {}, []
        for i, a in enumerate(al):
            if isinstance(a, dict) and str(a.get("substance") or "").strip().lower() in PLACEHOLDER_SUBSTANCE and str(a.get("normalized_substance") or "").strip().lower() in PLACEHOLDER_SUBSTANCE | {None}:
                removed.append((i, a))
                mapping[i] = None
            else:
                mapping[i] = len(keep)
                keep.append(a)
        if removed:
            status, role, ans, note = allergy_status(segs)
            for i, a in removed:
                log.add("change", f"allergies[{i}]", a, None, "C_allergy_placeholder_removed", f"entry named '{a.get('substance')}' is not an allergy; removed. Transcript status: {status} ({note})", True, status != "explicit_no_known_allergies")
            pred["allergies"] = keep
            _reindex(pred, "allergies", mapping)
            if status == "explicit_no_known_allergies":
                nf = pred.get("negative_findings")
                if not isinstance(nf, list):
                    nf = pred["negative_findings"] = []
                have = any(isinstance(n, dict) and (str(n.get("finding")).lower() == "allergies" or "no known allergies" in str(n.get("normalized_name")).lower()) for n in nf)
                if not have:
                    new = {"finding": "Allergies", "normalized_name": "No known allergies", "status": "absent", "assertion": "negative", "reported_by": role if role in ROLES else "patient", "temporality": "current",
                           "evidence_ids": [], "confidence": None}
                    nf.append(new)
                    log.add("change", f"negative_findings[{len(nf) - 1}]", None, new, "C_explicit_no_known_allergies_represented", f"schema representation of an explicit denial; source: segment SEG{ans + 1:04d} ({role}): \"{segs[ans]['text'][:80]}\"", True, False)
    # flag: allergy substance that is also a current medicine (identity is never auto-corrected)
    meds = pred.get("medications") if isinstance(pred.get("medications"), list) else []
    names = {str(m.get(k) or "").lower() for m in meds if isinstance(m, dict) for k in ("name", "normalized_name", "generic_name")} - {""}
    for i, a in enumerate(pred.get("allergies") or []):
        if isinstance(a, dict) and str(a.get("substance") or "").lower() in names:
            log.add("flag", f"allergies[{i}]", a.get("substance"), a.get("substance"), "F_medication_listed_as_allergy", "allergy substance is also a listed medicine; identity not changed", True, True)
    return status


# ------------------------------------------------------------------ rule D
def supported_datetime(value, text_tokens, text):
    v = str(value).strip().lower()
    if not v:
        return True
    if v in text:
        return True
    parts = [p for p in re.findall(r"[a-z]+|\d+", v) if p not in ("t", "z", "at", "am", "pm", "s")]
    return bool(parts) and all(p in text_tokens for p in parts)


def rule_d(pred, segs, log):
    text = " ".join(s["text"] for s in segs).lower()
    tk = set(toks(text))
    targets = []
    for i, x in enumerate(pred.get("procedures_and_investigations") or []):
        if isinstance(x, dict) and x.get("scheduled_datetime"):
            targets.append((f"procedures_and_investigations[{i}].scheduled_datetime", x, "scheduled_datetime"))
    for i, x in enumerate(pred.get("follow_up") or []):
        if isinstance(x, dict) and x.get("normalized_datetime"):
            targets.append((f"follow_up[{i}].normalized_datetime", x, "normalized_datetime"))
    for i, x in enumerate(pred.get("clinical_actions") or []):
        tr = x.get("time_reference") if isinstance(x, dict) else None
        if isinstance(tr, str) and (ISO.search(tr) or TS_LIKE.match(tr.strip())):
            targets.append((f"clinical_actions[{i}].time_reference", x, "time_reference"))
    for path, x, f in targets:
        v = x[f]
        if not supported_datetime(v, tk, text):
            x[f] = None
            log.add("change", path, v, None, "D_unsupported_datetime_nulled", "no date/time expression in the spoken transcript supports this value; set to null, original preserved in this log", True, False)


# ------------------------------------------------------------------ rule E
def verified_evidence_map(pred, segs):
    """evidence_id -> transcript segment index, only when the record reproduces a real segment exactly (speaker id, role, text)."""
    out = {}
    for ev in pred.get("clinical_evidence") or []:
        if not isinstance(ev, dict):
            continue
        c = [k for k, s in enumerate(segs) if s["text"] == ev.get("transcript_text") and s["speaker_id"] == ev.get("speaker_id") and str(s["role"]).lower() == str(ev.get("speaker_role"))]
        if len(c) == 1:
            out[ev.get("evidence_id")] = c[0]
    return out


def pure_question(t):
    t = t.strip()
    return t.endswith("?") and len(t.split()) <= 14 and not re.search(r"[.!]\s+\S", t)


def rule_e(pred, segs, log, trusted):
    if not trusted:
        log.add("flag", "*", None, None, "E_not_applicable", "cited evidence of this source is not a verified transcript citation (model-written evidence ids); no speaker derived", True, False)
        return 0
    ev = verified_evidence_map(pred, segs)
    changed = 0
    for loc, sec, i, x in _entities(pred):
        if sec not in RULE_E_SECTIONS and sec != "chief_complaint":
            continue
        idx = [ev[t] for t in (x.get("evidence_ids") or []) if t in ev]
        nonq = [k for k in idx if not pure_question(segs[k]["text"])]
        roles = {str(segs[k]["role"]).lower() for k in nonq}
        cur = x.get("reported_by")
        if len(roles) == 1:
            r = next(iter(roles))
            if r in ROLES and r != cur:
                x["reported_by"] = r
                # a patient-origin fact whose single cited statement is the doctor's (e.g. a recap) may have been SUPPLIED earlier by the patient: the change follows the cited segment but is flagged for review
                risky = cur in ("patient", "family_member", "caregiver") and r == "doctor" and sec != "vital_signs"
                log.add("change", f"{loc}.reported_by", cur, r, "E_reported_by_from_cited_segment", f"the only non-question cited segment (SEG{nonq[0] + 1:04d}) is spoken by the {r}" + ("; original named another speaker and the cited statement may be a recap" if risky else ""), True, risky)
                changed += 1
        elif len(roles) > 1 and cur not in roles:
            log.add("flag", f"{loc}.reported_by", cur, cur, "E_ambiguous_speakers", f"cited segments are spoken by several roles {sorted(roles)}; reported_by left unchanged", True, True)
    return changed


# ------------------------------------------------------------------ rule F (flags only)
def rule_f(pred, segs, log):
    text_all = " ".join(s["text"].lower() for s in segs)
    seg_low = [s["text"].lower() for s in segs]
    # placeholder entities
    for i, x in enumerate(pred.get("negative_findings") or []):
        if isinstance(x, dict) and str(x.get("finding")).strip().lower() in ("absent", "none", "negative", ""):
            log.add("flag", f"negative_findings[{i}]", x.get("finding"), x.get("finding"), "F_placeholder_negative_finding", "finding text is a schema word, not a finding", True, True)
    ca = pred.get("clinical_assessment")
    for i, x in enumerate(ca if isinstance(ca, list) else [ca] if isinstance(ca, dict) else []):
        if isinstance(x, dict) and str(x.get("assessment")).strip().lower() in ("provisional", "differential", ""):
            log.add("flag", f"clinical_assessment[{i}]", x.get("assessment"), x.get("assessment"), "F_placeholder_assessment", "assessment text is a schema word; diagnosis not stated in the item", True, True)
    # negative finding contradicting a positive item
    pos = []
    for sec, nf in (("symptoms", ("name", "normalized_name")), ("clinical_conditions", ("name", "normalized_name"))):
        for x in pred.get(sec) or []:
            if isinstance(x, dict):
                pos += [str(x.get(f) or "").lower() for f in nf]
    pos += [str(x.get("condition") or "").lower() for x in ((pred.get("medical_history") or {}).get("past_medical_history") or []) if isinstance(x, dict)]
    for i, x in enumerate(pred.get("negative_findings") or []):
        if isinstance(x, dict):
            n = re.sub(r"\b(no|not|denies)\b", "", str(x.get("normalized_name") or x.get("finding") or "").lower()).strip()
            if n and any(n == p or (len(n) > 4 and (n in p or p in n)) for p in pos if p):
                log.add("flag", f"negative_findings[{i}]", x.get("finding"), x.get("finding"), "F_negative_finding_overlaps_positive_item", "same word(s) also appear as a positive symptom/condition in this record (possible polarity error; not changed)", True, True)
    # medications: dose placement, route, prescribed-but-missing
    for i, m in enumerate(pred.get("medications") or []):
        if not isinstance(m, dict):
            continue
        r = str(m.get("route") or "").lower()
        if r and r not in ROUTES:
            log.add("flag", f"medications[{i}].route", m.get("route"), m.get("route"), "F_route_is_not_a_route", "route holds a frequency/other text; not changed", True, True)
        d = re.match(r"([\d.]+)", str(m.get("dose") or ""))
        nm = str(m.get("name") or "").lower()[:6]
        if d and nm:
            ix = [k for k, s in enumerate(seg_low) if nm in s]
            near = any(d.group(1) in re.findall(r"[\d.]+", seg_low[j]) for k in ix for j in range(k, min(k + 3, len(seg_low))))
            if not near:
                log.add("flag", f"medications[{i}].dose", m.get("dose"), m.get("dose"), "F_dose_not_near_drug_in_transcript", f"dose number {d.group(1)} is not stated in or just after a segment naming {m.get('name')}; not changed", True, True)
    blob = " ".join(str(x) for x in (pred.get("medications") or []) + (pred.get("clinical_actions") or [])).lower()
    for s in segs:
        if str(s["role"]).upper() == "DOCTOR":
            for mt in PRESCRIBE.finditer(s["text"]):
                nm = mt.group(1).strip().lower()
                if len(nm) >= 4 and nm not in ("a", "an", "the") and nm[:5] not in blob:
                    log.add("flag", "medications|clinical_actions", None, nm, "F_prescribed_drug_missing", f"doctor prescribing phrase names '{nm}' (SEG{segs.index(s) + 1:04d}) but no such entry exists; not added", True, True)
    # procedural talk extracted as finding / action / follow-up
    for sec, f in (("physical_examination", "finding"), ("clinical_actions", "description"), ("follow_up", "time_reference")):
        v = pred.get(sec)
        for i, x in enumerate(v if isinstance(v, list) else []):
            if isinstance(x, dict) and EXAM_PHRASES.search(str(x.get(f) or "")):
                log.add("flag", f"{sec}[{i}].{f}", x.get(f), x.get(f), "F_procedural_talk_extracted_as_content", "text is a clinician instruction/exam manoeuvre, not a finding or plan; not changed", True, True)
    if pred.get("follow_up") and not RETURN_VISIT.search(" ".join(s["text"] for s in segs if str(s["role"]).upper() == "DOCTOR")):
        log.add("flag", "follow_up", "present", "present", "F_follow_up_without_return_visit_phrase", "no doctor segment contains a return-visit phrase; follow-up not changed", True, True)


def repair(pred, segs, enc_id, evidence_trusted=False):
    """returns (repaired copy, log rows, allergy_status). `pred` is never modified."""
    out = copy.deepcopy(pred)
    log = Log(enc_id)
    rule_a(out, log)
    rule_b(out, log)
    status = rule_c(out, segs, log)
    rule_d(out, segs, log)
    rule_e(out, segs, log, evidence_trusted)
    rule_f(out, segs, log)
    return out, log.rows, status
