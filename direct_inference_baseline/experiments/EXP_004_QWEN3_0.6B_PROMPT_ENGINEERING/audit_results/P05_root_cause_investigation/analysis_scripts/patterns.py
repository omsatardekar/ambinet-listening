import json, re, sys, collections
from pathlib import Path
E4 = Path(sys.argv[1])
DS = Path(sys.argv[2])  # dataset inputs dir (validation transcripts only are opened)
RAW = E4/"outputs/P05_validation_50/stage1/raw_predictions/P05_validation_50"
PAR = E4/"outputs/P05_validation_50/stage1/parsed_predictions/P05_validation_50"
DEC = E4/"outputs/P05_validation_50/decisions"
ids = json.loads((E4/"experiments/split_v1.json").read_text(encoding="utf-8"))["validation_ids"]
P = {e: json.loads((PAR/f"encounter_{e}.json").read_text(encoding="utf-8")) for e in ids}
T = {e: json.loads((DS/f"encounter_{e}.json").read_text(encoding="utf-8")) for e in ids}
def lst(p, k): return [x for x in (p.get(k) or []) if isinstance(x, dict)]
def hist(p, sub): return [x for x in ((p.get("medical_history") or {}).get(sub) or []) if isinstance(x, dict)]
out = {}
# parser wrapper
for e in ("00034","00173"):
    r = json.loads((RAW/f"encounter_{e}.json").read_text(encoding="utf-8"))["response_text"]
    print("raw head", e, repr(r[:60]), "tail", repr(r[-40:]))
# counts
tot = collections.Counter()
for e,p in P.items():
    for k in ("symptoms","negative_findings","medications","allergies","vital_signs","physical_examination","review_of_systems","clinical_conditions","clinical_assessment","procedures_and_investigations","clinical_actions","follow_up"):
        tot[k]+=len(lst(p,k))
    for s in ("past_medical_history","surgical_history","family_history","social_history"): tot["mh."+s]+=len(hist(p,s))
print("entities per section", dict(tot), "total", sum(tot.values()))
# symptom category
c = collections.Counter(x.get("category") for p in P.values() for x in lst(p,"symptoms")); print("symptom.category", c.most_common())
b = collections.Counter(x.get("body_site") for p in P.values() for x in lst(p,"symptoms")); print("symptom.body_site top", b.most_common(8))
cert = collections.Counter(x.get("certainty") for p in P.values() for x in lst(p,"symptoms")); print("symptom.certainty", cert.most_common())
# enum violations
ALLOWED = {"allergies":{"allergy_type":{"medication","food","environmental"},"status":{"reported","uncertain","historical","disputed"}},
 "medications":{"status":{"currently_used","discontinued","planned"}},
 "clinical_actions":{"action_type":{"investigation","medication","counselling","referral","follow_up","other"},"status":{"planned","completed","recommended","conditional"},"responsible_person":{"doctor","patient","nurse","clinical_staff"}},
 "procedures_and_investigations":{"type":{"laboratory","imaging","cardiac","other"},"status":{"planned","completed","conditional"}},
 "follow_up":{"status":{"planned","conditional"}},"clinical_assessment":{"certainty":{"provisional","differential"}},
 "symptoms":{"status":{"present","resolved"},"certainty":{"certain","uncertain","disputed"},"temporality":{"current","past","resolved"}}}
viol = collections.Counter(); ex = collections.defaultdict(collections.Counter)
for p in P.values():
    for k,fs in ALLOWED.items():
        for x in lst(p,k):
            for f,al in fs.items():
                v = x.get(f)
                if v is not None and v not in al: viol[(k,f)]+=1; ex[(k,f)][v]+=1
print("enum violations", {f"{a}.{b}":n for (a,b),n in viol.items()})
for kf,cn in ex.items(): print("   ", kf, cn.most_common(5))
# reported_by case and roles
rb = collections.Counter()
for p in P.values():
    for k in ("symptoms","negative_findings","medications","allergies","vital_signs","clinical_conditions"):
        for x in lst(p,k): rb[x.get("reported_by")]+=1
    for s in ("past_medical_history","surgical_history","family_history"):
        for x in hist(p,s): rb[x.get("reported_by")]+=1
print("reported_by values", rb.most_common(12))
# placeholders
ph = collections.Counter()
for e,p in P.items():
    for x in lst(p,"negative_findings"):
        if str(x.get("finding")).lower().strip() in ("absent","none","negative",""): ph["negative_findings.finding placeholder"]+=1
    for x in lst(p,"clinical_assessment"):
        if str(x.get("assessment")).lower().strip() in ("provisional","differential",""): ph["clinical_assessment.assessment placeholder"]+=1
    for x in lst(p,"allergies"):
        if str(x.get("substance")).lower().strip() in ("none","no","nil",""): ph["allergies.substance none"]+=1
    for x in lst(p,"follow_up"):
        if re.fullmatch(r"[\d.]+s", str(x.get("normalized_datetime") or "")): ph["follow_up.normalized_datetime looks like a transcript timestamp"]+=1
    for x in lst(p,"procedures_and_investigations"):
        if x.get("scheduled_datetime"): ph["procedures.scheduled_datetime non-null"]+=1
    for x in lst(p,"medications"):
        r = str(x.get("route") or "")
        if r and not re.search(r"oral|mouth|iv|topical|inhal|nasal|sublingual|intramusc|subcut|ophthal|rectal|transderm|ear", r.lower()): ph["medications.route not a route"]+=1
print("placeholders", dict(ph))
# 'no allergy' fabricated when no allergy question
allergy_q = re.compile(r"allerg|react(ed)? badly", re.I)
fab = []
for e,p in P.items():
    asked = any(allergy_q.search(s["text"]) for s in T[e]["segments"] if s["text"].strip().endswith("?") or allergy_q.search(s["text"]))
    for x in lst(p,"allergies"):
        if str(x.get("substance")).lower() in ("none","no","nil") and not asked: fab.append(e)
print("'none' allergy items in records with no allergy question:", fab)
# no-allergy items overall
print("records whose allergies list is exactly 'none' placeholder:", sum(1 for p in P.values() if any(str(x.get('substance')).lower()=='none' for x in lst(p,'allergies'))))
# negative finding vs symptom/condition overlap
def keys(x, fs): return " ".join(str(x.get(f) or "") for f in fs).lower()
ov = []
for e,p in P.items():
    pos = [keys(x,("name","normalized_name")) for x in lst(p,"symptoms")+lst(p,"clinical_conditions")] + [keys(x,("condition","normalized_condition")) for x in hist(p,"past_medical_history")]
    for x in lst(p,"negative_findings"):
        n = keys(x,("finding","normalized_name"))
        n2 = re.sub(r"\bno\b|\bnot\b|\bdenies\b","",n).strip()
        if n2 and any(n2 and (n2 in q or (q and q in n2)) for q in pos if q.strip()): ov.append((e,n))
print("negative_findings that also appear as a positive symptom/condition in the same record:", len(ov), ov[:12])
print("total negative findings:", tot["negative_findings"])
# medication appears in allergies
mal = []
for e,p in P.items():
    meds = [keys(x,("name","normalized_name")) for x in lst(p,"medications")]
    for x in lst(p,"allergies"):
        s = str(x.get("substance") or "").lower()
        if s and any(s[:6] in m for m in meds): mal.append((e,s))
print("allergy substances that are also in the medication list:", mal)
# medication dose provenance
prov = collections.Counter(); bad=[]
for e,p in P.items():
    segs = [s["text"].lower() for s in T[e]["segments"]]
    for x in lst(p,"medications"):
        d = str(x.get("dose") or ""); nm = str(x.get("name") or "").lower()
        m = re.match(r"([\d.]+)\s*(milligram|microgram|mg|mcg|g|ml|unit)", d.lower())
        if not m: prov["no parsable dose"]+=1; continue
        num = m.group(1)
        idx = [i for i,s in enumerate(segs) if nm[:5] and nm[:5] in s]
        near = any(num in re.findall(r"[\d.]+", segs[j]) for i in idx for j in (i,i+1,i+2) if j < len(segs))
        same = any(num in re.findall(r"[\d.]+", segs[i]) for i in idx)
        anywhere = any(num in re.findall(r"[\d.]+", s) for s in segs)
        if same: prov["number in a segment naming the drug"]+=1
        elif near: prov["number in the next two segments (dose given after a question)"]+=1
        elif anywhere: prov["number elsewhere in transcript only"]+=1; bad.append((e,nm,d))
        else: prov["number nowhere in transcript"]+=1; bad.append((e,nm,d))
print("dose provenance (all meds with dose)", dict(prov)); print("  suspicious", bad[:14])
# prescriptions omitted: doctor prescription phrases -> drug in output
pat = re.compile(r"(?:let's use|i'll start you on|i'm prescribing|we'll begin with|what i'm giving you is|the treatment will be|for this,|i'd like you to take|let's start)\s+([a-z0-9 \-]+?)(?:,|\s\d)", re.I)
om=[]; seen=0
for e,p in P.items():
    blob = json.dumps({k:p.get(k) for k in("medications","clinical_actions")}).lower()
    for s in T[e]["segments"]:
        if str(s["role"]).upper()!="DOCTOR": continue
        for m in pat.finditer(s["text"]):
            nm = m.group(1).strip().lower()
            if nm in ("a","an","the") or len(nm)<4: continue
            seen+=1
            if nm[:5] not in blob: om.append((e,nm))
print("doctor prescription phrases found:", seen, "drug name absent from medications/clinical_actions:", len(om), om[:12])
# model's own evidence quality
ev = collections.Counter()
for e,p in P.items():
    segtxt = [s["text"] for s in T[e]["segments"]]
    recs = [x for x in (p.get("clinical_evidence") or []) if isinstance(x,dict)]
    ev["records"]+=len(recs)
    for r in recs:
        t = str(r.get("transcript_text") or "")
        if any(t and t[:30] in s for s in segtxt): ev["record text matches a real segment"]+=1
    for k in ("symptoms","negative_findings","medications","allergies","vital_signs","physical_examination","clinical_conditions","clinical_assessment","procedures_and_investigations","clinical_actions","follow_up"):
        for x in lst(p,k):
            ev["entities"]+=1
            ids_ = x.get("evidence_ids")
            if not ids_: ev["entities with empty/absent evidence_ids"]+=1
            elif ids_==["EV_001"]: ev["entities citing only EV_001"]+=1
print("Stage-1 self-evidence", dict(ev))
# reported_by vs role of the cited segment (P05 decisions) for patient-origin categories
mm = collections.Counter()
for e in ids:
    dec = json.loads((DEC/f"encounter_{e}.json").read_text(encoding="utf-8"))["decisions"]
    segs = T[e]["segments"]; p = P[e]
    for d in dec:
        if d["decision"]!="cited": continue
        loc = d["location"]; cat = loc.split("[")[0]
        if cat not in ("symptoms","negative_findings","medical_history.past_medical_history","medical_history.surgical_history","medical_history.family_history","clinical_conditions","medications","allergies"): continue
        # entity
        if cat.startswith("medical_history."):
            sub = cat.split(".")[1]; i = int(loc.split("[")[1][:-1]); x = hist(p,sub)[i]
        else:
            i = int(loc.split("[")[1][:-1]); x = lst(p,cat)[i]
        rb_ = str(x.get("reported_by") or "").lower()
        roles = [str(segs[int(s[3:])-1]["role"]).lower() for s in d["segments"] if not segs[int(s[3:])-1]["text"].strip().endswith("?")]
        if not roles: continue
        r0 = roles[-1]
        mm[("reported_by="+(rb_ or "empty"), "answer segment role="+r0)]+=1
print("reported_by vs role of cited answer segment (patient-origin sections):")
for k,v in sorted(mm.items(), key=lambda kv:-kv[1])[:14]: print("   ",k,v)
