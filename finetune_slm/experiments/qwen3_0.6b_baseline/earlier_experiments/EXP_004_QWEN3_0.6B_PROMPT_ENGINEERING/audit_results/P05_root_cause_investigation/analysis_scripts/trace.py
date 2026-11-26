import json, sys
from pathlib import Path
E4 = Path(sys.argv[1])
RAW = E4/"outputs/P05_validation_50/stage1/raw_predictions/P05_validation_50"
PAR = E4/"outputs/P05_validation_50/stage1/parsed_predictions/P05_validation_50"
DEC = E4/"outputs/P05_validation_50/decisions"
ids = json.loads((E4/"experiments/split_v1.json").read_text(encoding="utf-8"))["validation_ids"]
# 1. raw == parsed?
diff = []
for e in ids:
    raw = json.loads((RAW/f"encounter_{e}.json").read_text(encoding="utf-8"))["response_text"]
    try:
        r = json.loads(raw)
    except Exception as ex:
        diff.append((e, "raw not plain json: "+str(ex)[:60])); continue
    p = json.loads((PAR/f"encounter_{e}.json").read_text(encoding="utf-8"))
    if r != p: diff.append((e, "raw!=parsed"))
print("raw vs parsed differences:", diff)

def walk(p):
    out=[]
    for k,v in p.items():
        if k=="medical_history":
            for sk,sv in v.items():
                for i,x in enumerate(sv or []): out.append((f"{k}.{sk}[{i}]",x))
        elif isinstance(v,list) and k not in("clinical_evidence",):
            for i,x in enumerate(v):
                if isinstance(x,dict): out.append((f"{k}[{i}]",x))
        elif k=="chief_complaint" and isinstance(v,dict): out.append((k,v))
    return out

items = [("A01","00096","clinical_conditions","thyroid"),("A07","00034","allergies",None),("A08","00318","surgical_history","gallbladder"),("A10","00071","allergies","mlodipine"),
("A12","00322","negative_findings","fever"),("A13","00445","clinical_actions","hydrocortisone"),("A14","00436","physical_examination","pressure"),("A15","00395","clinical_actions","look"),
("A16","00203","procedures_and_investigations","hearing"),("A17","00096","negative_findings","thin"),("A21","00223","negative_findings","COPD"),("A22","00203","vital_signs","blood pressure"),
("A25","00021","symptoms","racing"),("A28","00096","medications","hyronorm"),("A31","00386","negative_findings","fever"),("A35","00203","follow_up",None),("A40","00345","vital_signs","height"),
("A42","00081","symptoms","shak"),("A43","00021","clinical_assessment",None),("A45","00223","procedures_and_investigations","X-ray"),("A30","00147","family_history","asthma"),("A32","00086","family_history","thyroid"),
("A02","00203","symptoms","hearing"),("A03","00223","symptoms","blood pressure"),("A04","00119","negative_findings","absent"),("A06","00021","clinical_actions","omeprazole"),("A09","00081","negative_findings","shak"),
("A18","00367","clinical_conditions","ypertension"),("A24","00147","symptoms","headache"),("A26","00395","negative_findings","tired"),("A27","00345","review_of_systems",None),("A29","00034","follow_up",None),
("A33","00151","symptoms","fever"),("A34","00173","clinical_assessment",None),("A36","00345","allergies",None),("A38","00176","clinical_conditions","ypertension"),("A44","00190","past_medical_history",None)]
want = sys.argv[2:]
for (i,e,cat,key) in items:
    if want and i not in want: continue
    p = json.loads((PAR/f"encounter_{e}.json").read_text(encoding="utf-8"))
    ev = {x.get("evidence_id"):x for x in (p.get("clinical_evidence") or []) if isinstance(x,dict)}
    dec = {d["location"]:d for d in json.loads((DEC/f"encounter_{e}.json").read_text(encoding="utf-8"))["decisions"]}
    print("=====",i,e,cat)
    n=0
    for loc,x in walk(p):
        if cat not in loc: continue
        s=json.dumps(x,ensure_ascii=False)
        if key is None or key.lower() in s.lower():
            n+=1
            core={k:v for k,v in x.items() if k not in("evidence_ids","confidence")}
            print(" ",loc,json.dumps(core,ensure_ascii=False)[:420])
            print("    model_evidence_ids:",x.get("evidence_ids"),[ (ev.get(t) or {}).get("transcript_text","?")[:90] for t in (x.get("evidence_ids") or [])][:3])
            d=dec.get(loc); print("    P05 decision:",(d or {}).get("decision"),(d or {}).get("reason"),(d or {}).get("segments"))
    if n==0: print("  (no matching entity)")
