import json, re, sys, collections
from pathlib import Path
E4 = Path(sys.argv[1]); DS = Path(sys.argv[2])
PAR = E4/"outputs/P05_validation_50/stage1/parsed_predictions/P05_validation_50"
RAW = E4/"outputs/P05_validation_50/stage1/raw_predictions/P05_validation_50"
ids = json.loads((E4/"experiments/split_v1.json").read_text(encoding="utf-8"))["validation_ids"]
P = {e: json.loads((PAR/f"encounter_{e}.json").read_text(encoding="utf-8")) for e in ids}
T = {e: json.loads((DS/f"encounter_{e}.json").read_text(encoding="utf-8")) for e in ids}
SEC = {"symptoms":("name","normalized_name"),"negative_findings":("finding","normalized_name"),"medications":("name","normalized_name"),"allergies":("substance","normalized_substance"),
 "physical_examination":("finding","normalized_finding"),"clinical_conditions":("name","normalized_name"),"clinical_assessment":("assessment","normalized_assessment"),
 "procedures_and_investigations":("name","normalized_name"),"clinical_actions":("description",None),"vital_signs":("name","normalized_name")}
STOP = set("the and with for from that this have has been are was were your you not any".split())
def toks(s): return [t for t in re.findall(r"[a-z]+", str(s).lower()) if len(t) >= 4 and t not in STOP]
ungr = collections.Counter(); ex = collections.defaultdict(list); drift = []; dup = 0; ent = 0
for e,p in P.items():
    text = " ".join(s["text"].lower() for s in T[e]["segments"])
    words = set(re.findall(r"[a-z]+", text))
    for k,(f,nf) in SEC.items():
        seen = set()
        for x in (p.get(k) or []):
            if not isinstance(x, dict): continue
            ent += 1
            tk = toks(x.get(f))
            if tk and not any(any(w.startswith(t[:5]) for w in words) for t in tk):
                ungr[k]+=1; ex[k].append((e, x.get(f)))
            if nf and x.get(nf) and x.get(f):
                a, b = set(t[:5] for t in toks(x[f])), set(t[:5] for t in toks(x[nf]))
                if a and b and not (a & b): drift.append((e,k,x[f],x[nf]))
            key = (k, str(x.get(f)).lower())
            if key in seen: dup += 1
            seen.add(key)
print("entities checked", ent, "ungrounded (no content word of the plain field occurs in the transcript):", sum(ungr.values()), dict(ungr))
for k,v in ex.items(): print("  ", k, v[:6])
print("normalization drift (plain vs normalized share no word stem):", len(drift)); print(drift[:25])
print("exact duplicate items within a section:", dup)
# repetition: raw length and 00223
for e in ("00223","00096","00096"):
    r = json.loads((RAW/f"encounter_{e}.json").read_text(encoding="utf-8"))["response_text"]
    print(e, "raw chars", len(r), "scheduled_datetime lines", r.count("scheduled_datetime"), "2023-04-10 occurrences", r.count("2023-04-10"))
p = P["00223"]
print("00223 procedures:", [(x.get("name"), x.get("scheduled_datetime")) for x in p["procedures_and_investigations"]])
print("00223 clinical_evidence records", len(p.get("clinical_evidence") or []))
# scheduled_datetime non-null per record, transcript mentions of a date
n=0; dated=0
for e,p in P.items():
    for x in p.get("procedures_and_investigations") or []:
        if x.get("scheduled_datetime"):
            n+=1
            if re.search(r"\b(19|20)\d\d\b|january|february|march|april|may |june|july|august|september|october|november|december|monday|tuesday|wednesday|thursday|friday", " ".join(s["text"].lower() for s in T[e]["segments"])): dated+=1
print("procedures with a scheduled_datetime:", n, "in a transcript that mentions any date/weekday:", dated)
# interplay: do hallucinated negatives sit at index 0?
idx = collections.Counter()
for e,p in P.items():
    for i,x in enumerate(p.get("negative_findings") or []): idx[min(i,3)]+=1
print("negative_findings by list position", dict(idx))
# follow-up items: transcript contains a real return-visit phrase?
fu = re.compile(r"come back|see you again|see me again|review|another look|back in|next visit|catch up|follow", re.I)
a=b=0
for e,p in P.items():
    has = any(fu.search(s["text"]) and str(s["role"]).upper()=="DOCTOR" for s in T[e]["segments"])
    for x in p.get("follow_up") or []:
        a+=1; b+= (not has)
print("follow_up items:", a, "in records where no doctor segment contains a return-visit phrase:", b)
