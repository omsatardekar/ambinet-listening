"""PROPOSAL ONLY (nothing is executed or enforced): provisional allocation of Batch 002 into 400 training candidates / 50 development / 50 internal holdout, stratified by specialty x difficulty tier,
with a fixed seed, plus additional label-quality flags and leakage measurements. Writes only to batch_002/allocation_proposal/. Reads Batch 002 files (never modifies them). The Batch 001 locked
records are not opened.   usage: python -B b2_allocation_proposal.py"""
import collections
import csv
import hashlib
import json
import random
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
B2 = HERE.parent
OUT = B2 / "allocation_proposal"
OUT.mkdir(exist_ok=True)
SEED = 20261115
N_DEV = N_HOLD = 50
J = lambda p: json.loads(Path(p).read_text(encoding="utf-8"))
MAN = list(csv.DictReader(open(B2 / "output/manifest.csv", encoding="utf-8")))
ids = [m["encounter_id"] for m in MAN]
M = {m["encounter_id"]: m for m in MAN}
BP = {i: J(B2 / f"scenario_blueprints/blueprint_{i}.json") for i in ids}
LB = {i: J(B2 / f"output/labels/encounter_{i}.json") for i in ids}
IN = {i: J(B2 / f"output/inputs/encounter_{i}.json") for i in ids}

# ------------------------------------------------------------------ stratified assignment (error-diffusion quotas: exact totals, near-proportional in every cell)
cells = collections.defaultdict(list)
for i in ids:
    cells[(M[i]["specialty"], M[i]["tier"])].append(i)
rng = random.Random(SEED)
split = {}
cum = 0
prev_d = prev_h = 0
for key in sorted(cells):
    g = sorted(cells[key])
    rng.shuffle(g)
    cum += len(g)
    td, th = round(N_DEV * cum / len(ids)), round(N_HOLD * cum / len(ids))
    qd, qh = td - prev_d, th - prev_h
    prev_d, prev_h = td, th
    for i in g[:qd]:
        split[i] = "development"
    for i in g[qd:qd + qh]:
        split[i] = "internal_holdout"
    for i in g[qd + qh:]:
        split[i] = "training_candidate"
cnt = collections.Counter(split.values())
assert cnt == {"training_candidate": 400, "development": 50, "internal_holdout": 50}, cnt

# ------------------------------------------------------------------ additional label-quality flags (deterministic, conservative; flags are for human/engineer review, not rejections)
VERBING = r"(?:feeling|getting|losing|putting|needing|using|turning|waking|having|wanting|forgetting|repeating|misplacing|passing|going|clearing|coughing|biting|belching|snoring|sweating|looking|being|dealing|trying|running)"
NSAID = {"naproxen", "diclofenac", "ibuprofen", "etoricoxib", "aspirin", "mefenamic acid"}
CAUTION = {"asthma", "ckd", "gerd", "hf", "af", "ihd", "anemia"}
CLS = {"lisinopril": "acei", "ramipril": "acei", "losartan": "arb", "telmisartan": "arb", "valsartan": "arb", "amlodipine": "ccb", "metoprolol": "bb", "bisoprolol": "bb", "carvedilol": "bb", "propranolol": "bb",
       "metformin": "biguanide", "glimepiride": "su", "glibenclamide": "su", "gliclazide": "su", "sitagliptin": "dpp4", "atorvastatin": "statin", "rosuvastatin": "statin", "simvastatin": "statin",
       "pantoprazole": "ppi", "omeprazole": "ppi", "esomeprazole": "ppi", "lansoprazole": "ppi", "sertraline": "ssri", "escitalopram": "ssri", "fluoxetine": "ssri", "aspirin": "antiplatelet", "clopidogrel": "antiplatelet",
       "cetirizine": "antihist", "chlorphenamine": "antihist", "levocetirizine": "antihist", "prednisolone": "steroid", "paracetamol": "paracetamol"}
flags = {}
for i in ids:
    b, l, inp = BP[i], LB[i], IN[i]
    f = []
    pt = " ".join(s["text"].lower() for s in inp["segments"] if s["role"] in ("PATIENT", "CAREGIVER", "FAMILY_MEMBER"))
    if re.search(r"\b(did have|had|have had) " + VERBING + r"\b", pt):
        f.append("template_artifact_verb_form_in_symptom_phrase")
    meds = [(m["generic_name"] or m["name"]).lower() for m in l["medications"]]
    pm = {c for c in [p["key"] for p in b["pmh"]]}
    if ((set(meds) & (NSAID - {"aspirin"})) and (pm & CAUTION)) or ("aspirin" in meds and (pm & {"asthma", "ckd", "gerd", "anemia"})):   # aspirin in coronary disease is an indication, not a caution
        f.append("nsaid_with_common_caution_in_history")
    cur = [m for m in l["medications"] if m["status"] in ("currently_used", "planned")]
    cl = collections.Counter(CLS.get((m["generic_name"] or m["name"]).lower()) for m in cur if CLS.get((m["generic_name"] or m["name"]).lower()))
    if any(c > 1 and k not in ("paracetamol",) for k, c in cl.items()):
        f.append("two_current_or_planned_medicines_of_the_same_class")
    if any(m["status"] == "discontinued" and (m["generic_name"] or "").lower() in meds[:0] for m in l["medications"]):
        f.append("x")
    f = [x for x in f if x != "x"]
    sy = [s for s in b["syms"] if s.get("status") == "resolved" and s.get("kind") == "ger"]
    if sy:
        f.append("resolved_symptom_phrase_is_a_gerund_clause")
    if not l["clinical_assessment"]:
        f.append("no_assessment_stated_(intentional_abstention_case)")
    flags[i] = f
FLAG_REVIEW = {"template_artifact_verb_form_in_symptom_phrase", "nsaid_with_common_caution_in_history", "two_current_or_planned_medicines_of_the_same_class", "resolved_symptom_phrase_is_a_gerund_clause"}

# ------------------------------------------------------------------ leakage / similarity of the held-out sets to the training candidates
N = lambda t: re.sub(r"[^a-z0-9' ]+", " ", t.lower().replace("’", "'")).split()
sh = lambda w, n=5: {" ".join(w[k:k + n]) for k in range(max(0, len(w) - n + 1))}
SH = {i: sh(N(" ".join(s["text"] for s in IN[i]["segments"]))) for i in ids}
train = [i for i in ids if split[i] == "training_candidate"]
inv = collections.defaultdict(set)
for i in train:
    for g in SH[i]:
        inv[g].add(i)
seg_train = {" ".join(N(s["text"])) for i in train for s in IN[i]["segments"] if len(N(s["text"])) >= 5}
prof_train = collections.Counter(M[i]["profile"] for i in train)
leak = {}
for name in ("development", "internal_holdout"):
    mem = [i for i in ids if split[i] == name]
    mj = 0.0
    for i in mem:
        c = collections.Counter(j for g in SH[i] for j in inv.get(g, ()))
        for j, k in c.items():
            mj = max(mj, k / (len(SH[i]) + len(SH[j]) - k))
    segs = [" ".join(N(s["text"])) for i in mem for s in IN[i]["segments"] if len(N(s["text"])) >= 5]
    leak[name] = {"records": len(mem), "max_5gram_jaccard_to_any_training_candidate": round(mj, 3), "share_of_segments_ge5_words_verbatim_in_training_candidates": round(sum(t in seg_train for t in segs) / len(segs), 3),
                  "records_whose_profile_also_occurs_in_training_candidates": sum(M[i]["profile"] in prof_train for i in mem), "distinct_profiles": len({M[i]["profile"] for i in mem}),
                  "min_training_records_per_profile_of_these_records": min(prof_train[M[i]["profile"]] for i in mem)}

# ------------------------------------------------------------------ alternative B (for the owner to compare): profile-disjoint holdout and development (whole scenario profiles held out)
rngb = random.Random(SEED + 1)
by_prof = collections.defaultdict(list)
for i in ids:
    by_prof[M[i]["profile"]].append(i)
spec_of = {M[i]["profile"]: M[i]["specialty"] for i in ids}
def pick(exclude, target=50):
    pool = [p for p in by_prof if p not in exclude]
    rngb.shuffle(pool)
    chosen, used_specs, n = [], collections.Counter(), 0
    for p in sorted(pool, key=lambda p: (used_specs[spec_of[p]], rngb.random())):
        pass
    order = []
    left = {s: [p for p in pool if spec_of[p] == s] for s in sorted({spec_of[p] for p in pool})}
    while any(left.values()) and n < target - 4:
        for s in list(left):
            if left[s] and n < target - 4:
                p = left[s].pop()
                if n + len(by_prof[p]) <= target + 4:
                    chosen.append(p)
                    n += len(by_prof[p])
    return chosen, n
hold_p, nh = pick(set())
dev_p, nd = pick(set(hold_p))
altB = {"holdout_profiles": sorted(hold_p), "holdout_records": nh, "development_profiles": sorted(dev_p), "development_records": nd,
        "holdout_ids": sorted(i for p in hold_p for i in by_prof[p]), "development_ids": sorted(i for p in dev_p for i in by_prof[p]),
        "note": "not stratified by specialty x tier; sizes approximate (whole profiles); measures generalisation to unseen scenario profiles"}
trainB = [i for i in ids if M[i]["profile"] not in set(hold_p) | set(dev_p)]
invB = collections.defaultdict(set)
for i in trainB:
    for g in SH[i]:
        invB[g].add(i)
segB = {" ".join(N(s["text"])) for i in trainB for s in IN[i]["segments"] if len(N(s["text"])) >= 5}
segsH = [" ".join(N(s["text"])) for i in altB["holdout_ids"] for s in IN[i]["segments"] if len(N(s["text"])) >= 5]
altB["training_records"] = len(trainB)
altB["holdout_share_of_segments_verbatim_in_training"] = round(sum(t in segB for t in segsH) / len(segsH), 3)
altB["holdout_specialties"] = dict(collections.Counter(spec_of[p] for p in hold_p))
altB["holdout_tiers"] = dict(collections.Counter(M[i]["tier"] for i in altB["holdout_ids"]))

# ------------------------------------------------------------------ outputs
rows = []
for i in ids:
    m = M[i]
    rows.append({"encounter_id": i, "proposed_split": split[i], "specialty": m["specialty"], "tier": m["tier"], "generator_complexity": m["complexity"], "profile": m["profile"], "speaker_roles": m["speaker_roles"],
                 "allergy_kind": BP[i]["allergies"]["kind"], "quality_flags": ";".join(flags[i]), "needs_review_before_training": int(split[i] == "training_candidate" and bool(set(flags[i]) & FLAG_REVIEW))})
with open(OUT / "allocation_proposal.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
tab = lambda key: {k: dict(collections.Counter(r["proposed_split"] for r in rows if r[key] == k)) for k in sorted({r[key] for r in rows})}
spec_tier = {f"{r['specialty']}|{r['tier']}": 0 for r in rows}
for r in rows:
    spec_tier[f"{r['specialty']}|{r['tier']}"] += 0
cellsplit = collections.defaultdict(collections.Counter)
for r in rows:
    cellsplit[f"{r['specialty']} | {r['tier']}"][r["proposed_split"]] += 1
fl = collections.Counter(x for r in rows for x in r["quality_flags"].split(";") if x)
flsplit = {s: collections.Counter(x for r in rows if r["proposed_split"] == s for x in r["quality_flags"].split(";") if x) for s in ("training_candidate", "development", "internal_holdout")}
prop = {"status": "PROPOSAL ONLY - not executed, not enforced, awaiting owner approval", "seed": SEED, "method": "stratified by specialty x tier (Simple/Medium/Hard); error-diffusion quotas over cells sorted by (specialty, tier), within-cell shuffle with random.Random(seed) on sorted ids",
        "counts": dict(cnt), "by_specialty": tab("specialty"), "by_tier": tab("tier"), "by_generator_complexity": tab("generator_complexity"), "cell_counts": {k: dict(v) for k, v in sorted(cellsplit.items())},
        "quality_flag_counts_all": dict(fl), "quality_flag_counts_by_split": {k: dict(v) for k, v in flsplit.items()}, "training_candidates_needing_review": sum(r["needs_review_before_training"] for r in rows),
        "leakage_and_similarity": leak, "alternative_B_profile_disjoint_for_comparison": altB, "ids": {s: sorted(i for i in ids if split[i] == s) for s in ("training_candidate", "development", "internal_holdout")},
        "proposal_csv_sha256": hashlib.sha256((OUT / "allocation_proposal.csv").read_bytes()).hexdigest()}
(OUT / "allocation_proposal.json").write_text(json.dumps(prop, indent=1, ensure_ascii=False), encoding="utf-8")
print(json.dumps({k: prop[k] for k in ("counts", "by_tier", "by_generator_complexity", "quality_flag_counts_all", "training_candidates_needing_review")}, indent=1)); print({k: v for k, v in altB.items() if not k.endswith("ids") and k not in ("holdout_profiles","development_profiles")})
print(json.dumps(prop["by_specialty"], indent=0)[:900])
print("empty cells for dev/holdout:", sum(1 for v in cellsplit.values() if v["development"] == 0), sum(1 for v in cellsplit.values() if v["internal_holdout"] == 0), "of", len(cellsplit))
