"""Descriptive statistics of a set of encounters (read-only). usage: python analyze_dataset.py <data-root> <start> <end> <out.json>"""
import collections as C, csv, json, statistics as S, sys
from pathlib import Path
root, a, b, out = Path(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
ids = [f"{i:05d}" for i in range(a, b + 1)]
I = {i: json.loads((root / f"output/inputs/encounter_{i}.json").read_text()) for i in ids}
L = {i: json.loads((root / f"output/labels/encounter_{i}.json").read_text()) for i in ids}
def dist(xs): 
    xs = list(xs); q = S.quantiles(xs, n=4) if len(xs) > 3 else [0, 0, 0]
    return {"min": min(xs), "q1": round(q[0], 1), "median": S.median(xs), "q3": round(q[2], 1), "max": max(xs), "mean": round(S.mean(xs), 2)}
def nz(path, f=lambda l, p: len(l[p])):
    c = [f(l, path) for l in L.values()]; return {"encounters_with_none": sum(1 for x in c if x == 0), "encounters_with_any": sum(1 for x in c if x), "count_distribution": dict(sorted(C.Counter(c).items())), "total_entities": sum(c)}
R = {"records": len(ids)}
R["segments_per_encounter"] = dist(len(i["segments"]) for i in I.values())
R["duration_seconds"] = dist(i["segments"][-1]["end_seconds"] for i in I.values())
R["words_per_segment"] = dist(len(s["text"].split()) for i in I.values() for s in i["segments"])
R["speakers_per_encounter"] = dict(sorted(C.Counter(len({s["speaker_id"] for s in i["segments"]}) for i in I.values()).items()))
R["roles_present_per_encounter"] = {"|".join(k): v for k, v in C.Counter(tuple(sorted({s["role"] for s in i["segments"]})) for i in I.values()).most_common()}
R["segments_by_role"] = dict(C.Counter(s["role"] for i in I.values() for s in i["segments"]))
R["encounters_with_role"] = {r: sum(1 for i in I.values() if any(s["role"] == r for s in i["segments"])) for r in ["DOCTOR", "PATIENT", "NURSE", "CAREGIVER", "FAMILY_MEMBER", "CLINICAL_STAFF", "UNKNOWN"]}
R["encounters_with_3plus_speakers"] = sum(1 for i in I.values() if len({s["speaker_id"] for s in i["segments"]}) >= 3)
R["encounter_types"] = dict(C.Counter(l["encounter_metadata"]["encounter_type"] for l in L.values()))
for p in ["symptoms", "negative_findings", "medications", "allergies", "vital_signs", "physical_examination", "review_of_systems", "clinical_conditions", "clinical_assessment", "procedures_and_investigations", "clinical_actions", "follow_up", "clinical_uncertainties"]:
    R[p] = nz(p)
for p in ["past_medical_history", "surgical_history", "family_history", "social_history"]:
    R["medical_history." + p] = nz(p, lambda l, q: len(l["medical_history"][q]))
R["symptom_categories"] = dict(C.Counter(s["category"] for l in L.values() for s in l["symptoms"]).most_common())
R["symptom_status"] = dict(C.Counter((s["status"], s["temporality"]) .__repr__() for l in L.values() for s in l["symptoms"]))
R["symptom_certainty"] = dict(C.Counter(s["certainty"] for l in L.values() for s in l["symptoms"]))
R["top_symptoms"] = C.Counter(s["normalized_name"] for l in L.values() for s in l["symptoms"]).most_common(25)
R["medication_status"] = dict(C.Counter(m["status"] for l in L.values() for m in l["medications"]))
R["medication_fields_present"] = {k: sum(1 for l in L.values() for m in l["medications"] if m[k]) for k in ["dose", "frequency", "route", "duration", "indication", "generic_name"]}
R["top_medications"] = C.Counter(m["normalized_name"] for l in L.values() for m in l["medications"] if m["normalized_name"]).most_common(25)
def allergy_kind(l, i):
    nk = [n for n in l["negative_findings"] if n["finding"] == "Allergies"]; al = l["allergies"]; mentioned = any("allerg" in s["text"].lower() for s in I[i]["segments"])
    return "explicit_none" if nk and not al else ("not_discussed" if not al and not mentioned else "+".join(sorted({a["status"] for a in al})) )
R["allergy_representation"] = dict(C.Counter(allergy_kind(l, i) for i, l in L.items()).most_common())
R["vital_sign_names"] = dict(C.Counter(v["name"] for l in L.values() for v in l["vital_signs"]).most_common())
R["vital_signs_per_encounter"] = dict(sorted(C.Counter(len(l["vital_signs"]) for l in L.values()).items()))
R["negative_finding_top"] = C.Counter(n["normalized_name"] for l in L.values() for n in l["negative_findings"]).most_common(20)
R["assessment_certainty"] = dict(C.Counter(a["certainty"] for l in L.values() for a in l["clinical_assessment"]))
R["top_assessments"] = C.Counter(a["normalized_assessment"] for l in L.values() for a in l["clinical_assessment"]).most_common(20)
R["uncertainty_types"] = dict(C.Counter(u["type"] for l in L.values() for u in l["clinical_uncertainties"]).most_common())
R["encounters_with_any_uncertainty"] = sum(1 for l in L.values() if l["clinical_uncertainties"])
R["action_types"] = dict(C.Counter((a["action_type"], a["status"]) .__repr__() for l in L.values() for a in l["clinical_actions"]).most_common())
R["investigation_types_status"] = dict(C.Counter((p["type"], p["status"]).__repr__() for l in L.values() for p in l["procedures_and_investigations"]).most_common())
R["follow_up_status"] = dict(C.Counter(f["status"] for l in L.values() for f in l["follow_up"]))
R["social_history_categories"] = dict(C.Counter(s["category"] for l in L.values() for s in l["medical_history"]["social_history"]))
R["empty_section_profile"] = dict(sorted(C.Counter(sum(1 for p in ["symptoms", "negative_findings", "medications", "allergies", "vital_signs", "physical_examination", "review_of_systems", "clinical_assessment", "procedures_and_investigations", "follow_up", "clinical_uncertainties"] if not l[p]) for l in L.values()).items()))
R["opening_words_top"] = C.Counter(" ".join(i["segments"][0]["text"].split()[:3]).lower() for i in I.values()).most_common(10)
mf = root / "output/manifest.csv"
if mf.exists():
    rows = [r for r in csv.DictReader(mf.open()) if a <= int(r["encounter_id"]) <= b]
    R["specialty"] = dict(C.Counter(r["specialty"] for r in rows).most_common()); R["complexity"] = dict(C.Counter(r["complexity"] for r in rows))
Path(out).write_text(json.dumps(R, indent=1, ensure_ascii=False))
print("wrote", out)
