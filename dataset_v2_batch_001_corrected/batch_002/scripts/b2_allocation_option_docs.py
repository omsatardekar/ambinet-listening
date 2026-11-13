"""Documents Option A and Option B of the Batch 002 allocation as separate, NOT executed strategies, and builds the record-by-record review list for the flagged training candidates (retained unchanged).
Reads allocation_proposal.json/csv and Batch 002 files; writes only into batch_002/allocation_proposal/. Nothing in Batch 001/Batch 002 data is modified; locked records are not opened.
usage: python -B b2_allocation_option_docs.py"""
import collections
import csv
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
B2 = Path(__file__).resolve().parents[1]
AP = B2 / "allocation_proposal"
J = lambda p: json.loads(Path(p).read_text(encoding="utf-8"))
P = J(AP / "allocation_proposal.json")
ROWS = {r["encounter_id"]: r for r in csv.DictReader(open(AP / "allocation_proposal.csv", encoding="utf-8"))}
ids = sorted(ROWS)
IN = {i: J(B2 / f"output/inputs/encounter_{i}.json") for i in ids}
LB = {i: J(B2 / f"output/labels/encounter_{i}.json") for i in ids}
BP = {i: J(B2 / f"scenario_blueprints/blueprint_{i}.json") for i in ids}
N = lambda t: re.sub(r"[^a-z0-9' ]+", " ", t.lower().replace("’", "'")).split()
sh = lambda w, n=5: {" ".join(w[k:k + n]) for k in range(max(0, len(w) - n + 1))}
SH = {i: sh(N(" ".join(s["text"] for s in IN[i]["segments"]))) for i in ids}
SEGS = lambda mem: [" ".join(N(s["text"])) for i in mem for s in IN[i]["segments"] if len(N(s["text"])) >= 5]


def measure(train, mem):
    inv = collections.defaultdict(set)
    for i in train:
        for g in SH[i]:
            inv[g].add(i)
    st = set(SEGS(train))
    mj = 0.0
    for i in mem:
        c = collections.Counter(j for g in SH[i] for j in inv.get(g, ()))
        for j, k in c.items():
            mj = max(mj, k / (len(SH[i]) + len(SH[j]) - k))
    sg = SEGS(mem)
    prof_tr = {ROWS[i]["profile"] for i in train}
    return {"records": len(mem), "max_5gram_jaccard_to_training": round(mj, 3), "share_segments_ge5_words_verbatim_in_training": round(sum(t in st for t in sg) / len(sg), 3),
            "records_with_profile_in_training": sum(ROWS[i]["profile"] in prof_tr for i in mem), "distinct_profiles": len({ROWS[i]["profile"] for i in mem})}


A = {s: P["ids"][s] for s in ("training_candidate", "development", "internal_holdout")}
Bd = P["alternative_B_profile_disjoint_for_comparison"]
B = {"development": Bd["development_ids"], "internal_holdout": Bd["holdout_ids"]}
B["training_candidate"] = [i for i in ids if i not in set(B["development"]) | set(B["internal_holdout"])]
assert sorted(sum(B.values(), [])) == ids and sorted(sum(A.values(), [])) == ids
mA = {k: measure(A["training_candidate"], A[k]) for k in ("development", "internal_holdout")}
mB = {k: measure(B["training_candidate"], B[k]) for k in ("development", "internal_holdout")}
for name, d in (("A_stratified", A), ("B_profile_disjoint", B)):
    (AP / f"option_{name}_ids.json").write_text(json.dumps({"status": "PROPOSAL ONLY - NOT EXECUTED", "option": name, "counts": {k: len(v) for k, v in d.items()}, "ids": {k: sorted(v) for k, v in d.items()}}, indent=1), encoding="utf-8")
spec = lambda d, k: dict(sorted(collections.Counter(ROWS[i]["specialty"] for i in d[k]).items()))
tier = lambda d, k: dict(sorted(collections.Counter(ROWS[i]["tier"] for i in d[k]).items()))
ov = Bd["holdout_share_of_segments_verbatim_in_training"]

docA = ["# Option A: stratified allocation (NOT EXECUTED)", "",
        "Retained as a separately documented strategy by owner decision. Seed 20261115; stratified by specialty x tier (36 cells); exact 400 training candidates / 50 development / 50 internal holdout. Ids: `option_A_stratified_ids.json` and column `proposed_split` of `allocation_proposal.csv`.", "",
        "## What it is good for", "", "- Monitoring in-distribution extraction quality on new samples of scenarios the model has trained on; balanced specialty and difficulty coverage (every specialty at least 4 development and 4 holdout records).", "",
        "## What it cannot show", "",
        f"- Generalisation to unseen scenarios: {mA['internal_holdout']['records_with_profile_in_training']}/50 holdout records share their scenario profile with training records, and {mA['internal_holdout']['share_segments_ge5_words_verbatim_in_training']:.0%} of the holdout's long segments occur verbatim in training. Max 5-gram Jaccard to any training record {mA['internal_holdout']['max_5gram_jaccard_to_training']} (development {mA['development']['max_5gram_jaccard_to_training']}).",
        "- Any result on this holdout is an in-distribution result on generator-derived labels, not clinical validation.", "",
        "## Composition", "", f"- Development specialties {spec(A, 'development')}; tiers {tier(A, 'development')}", f"- Holdout specialties {spec(A, 'internal_holdout')}; tiers {tier(A, 'internal_holdout')}", f"- Training specialties {spec(A, 'training_candidate')}; tiers {tier(A, 'training_candidate')}", "",
        "The 41 flagged training candidates stay in the training candidates with their flags (see `FLAGGED_TRAINING_CANDIDATES_REVIEW.md`). The 50 holdout records must not be used for training or prompt tuning.", ""]
(AP / "OPTION_A_stratified.md").write_text("\n".join(docA), encoding="utf-8")
docB = ["# Option B: profile-disjoint holdout and development (NOT EXECUTED)", "",
        "Retained as a separately documented strategy by owner decision. Whole scenario profiles are held out (seed 20261116, round-robin over specialties). Ids: `option_B_profile_disjoint_ids.json`.", "",
        "## IMPORTANT DISCLOSURE: this is NOT a clean generalisation test", "",
        f"- **{ov:.0%} of the holdout's long segments (>=5 words) occur verbatim in the training set** (measured: {mB['internal_holdout']['share_segments_ge5_words_verbatim_in_training']:.1%}). The overlap comes from the shared dialogue engine's routine questions, answers and acknowledgements, not from clinical content; it is nearly as high as in Option A ({mA['internal_holdout']['share_segments_ge5_words_verbatim_in_training']:.0%}).",
        "- Holding out profiles removes scenario overlap only. The sampled medicines, histories, allergy patterns, speaker patterns and the whole conversational scaffold are still shared with training. The same generator, the same author and the same pools produced all records, so a model can still exploit shared structure.",
        "- The holdout covers only 6 of the 12 specialties and 6 of the 60 profiles; sizes are approximate (51 / 51 / 398). A good score would indicate robustness to unseen profiles of the same generator, not robustness to real clinical conversations.", "",
        "## Measured separation", "", "| | Development | Holdout |", "|---|---:|---:|",
        f"| Records | {mB['development']['records']} | {mB['internal_holdout']['records']} |", f"| Profiles shared with training | {mB['development']['records_with_profile_in_training']} records | {mB['internal_holdout']['records_with_profile_in_training']} records |",
        f"| Distinct profiles | {mB['development']['distinct_profiles']} | {mB['internal_holdout']['distinct_profiles']} |", f"| Max 5-gram Jaccard to training | {mB['development']['max_5gram_jaccard_to_training']} | {mB['internal_holdout']['max_5gram_jaccard_to_training']} |",
        f"| Verbatim long-segment share in training | {mB['development']['share_segments_ge5_words_verbatim_in_training']:.1%} | {mB['internal_holdout']['share_segments_ge5_words_verbatim_in_training']:.1%} |", "",
        "## Composition", "", f"- Holdout profiles: {', '.join(Bd['holdout_profiles'])}", f"- Development profiles: {', '.join(Bd['development_profiles'])}", f"- Holdout specialties {spec(B, 'internal_holdout')}; tiers {tier(B, 'internal_holdout')}", f"- Development specialties {spec(B, 'development')}; tiers {tier(B, 'development')}", f"- Training specialties {spec(B, 'training_candidate')}; tiers {tier(B, 'training_candidate')}", "",
        "Not stratified by specialty or difficulty. Flagged training candidates stay in training with their flags. A genuinely clean generalisation test needs data from a different generator or real recordings; Batch 003 planning addresses part of this (see `BATCH_003_PLANNING.md`).", ""]
(AP / "OPTION_B_profile_disjoint.md").write_text("\n".join(docB), encoding="utf-8")

# ------------------------------------------------------------------ record-by-record review list (flagged training candidates are RETAINED unchanged)
REVIEW = {"template_artifact_verb_form_in_symptom_phrase", "nsaid_with_common_caution_in_history", "two_current_or_planned_medicines_of_the_same_class", "resolved_symptom_phrase_is_a_gerund_clause"}
VERB = r"(?:feeling|getting|losing|putting|needing|using|turning|waking|having|wanting|forgetting|repeating|misplacing|passing|going|clearing|coughing|biting|belching|snoring|sweating|looking|being|dealing|trying|running)"
CLS = {"lisinopril": "ACE inhibitor", "ramipril": "ACE inhibitor", "losartan": "ARB", "telmisartan": "ARB", "valsartan": "ARB", "metoprolol": "beta-blocker", "bisoprolol": "beta-blocker", "carvedilol": "beta-blocker", "propranolol": "beta-blocker",
       "glimepiride": "sulfonylurea", "glibenclamide": "sulfonylurea", "gliclazide": "sulfonylurea", "atorvastatin": "statin", "rosuvastatin": "statin", "simvastatin": "statin", "pantoprazole": "PPI", "omeprazole": "PPI", "esomeprazole": "PPI", "lansoprazole": "PPI",
       "sertraline": "SSRI", "escitalopram": "SSRI", "fluoxetine": "SSRI", "aspirin": "antiplatelet", "clopidogrel": "antiplatelet", "cetirizine": "antihistamine", "chlorphenamine": "antihistamine"}
NEED = {"template_artifact_verb_form_in_symptom_phrase": "Read the quoted segment; decide whether the wording is acceptable informal speech or a generator artifact. Check that the symptom entity (and temporality) in the label still matches what is said. Evidence: the transcript segment and the label symptom entries listed here.",
        "resolved_symptom_phrase_is_a_gerund_clause": "Read the quoted segment where the resolved symptom is mentioned; confirm that the label marks it resolved/past and that the sentence is grammatical enough to train on. Evidence: segment text, label symptoms[*].temporality, blueprint symptom status.",
        "nsaid_with_common_caution_in_history": "A clinician or pharmacist judges whether prescribing/using this NSAID is plausible with the listed condition. Evidence: the medicine entry (status, who reported it), the history condition, and the profile's plan; options (not applied): keep as realistic noise, or regenerate later with an exclusion.",
        "two_current_or_planned_medicines_of_the_same_class": "Check whether the two medicines are an intended switch/duplication or an artefact of independent sampling. Evidence: both medication entries (status, dose) and the transcript segments citing them."}
out = []
for i in sorted(ids):
    r = ROWS[i]
    if r["proposed_split"] != "training_candidate" or not (set(r["quality_flags"].split(";")) & REVIEW):
        continue
    flags = [f for f in r["quality_flags"].split(";") if f in REVIEW]
    segs = IN[i]["segments"]
    L = LB[i]
    for f in flags:
        quote, where, detail = "", "", ""
        if f in ("template_artifact_verb_form_in_symptom_phrase", "resolved_symptom_phrase_is_a_gerund_clause"):
            for k, s in enumerate(segs):
                if s["role"] in ("PATIENT", "CAREGIVER", "FAMILY_MEMBER") and re.search(r"\b(did have|had|have had) " + VERB + r"\b", s["text"].lower()):
                    quote, where = s["text"], f"SEG{k + 1:04d} ({s['role']})"
                    break
            detail = "label symptoms: " + "; ".join(f"{x['normalized_name']} [{x['status']}/{x['temporality']}]" for x in L["symptoms"])
            if not quote:   # resolved gerund symptom flagged from the blueprint: find the phrase
                ph = [s["phrase"] for s in BP[i]["syms"] if s.get("status") == "resolved" and s.get("kind") == "ger"]
                for k, sg in enumerate(segs):
                    if ph and any(p.lower() in sg["text"].lower() for p in ph) and sg["role"] != "DOCTOR":
                        quote, where = sg["text"], f"SEG{k + 1:04d} ({sg['role']})"
                        break
        elif f == "nsaid_with_common_caution_in_history":
            nsaid = [m for m in L["medications"] if (m["generic_name"] or m["name"]).lower() in {"naproxen", "diclofenac", "ibuprofen", "etoricoxib", "aspirin", "mefenamic acid"}]
            conds = [c["normalized_condition"] for c in L["medical_history"]["past_medical_history"]]
            detail = "NSAID: " + "; ".join(f"{m['name']} {m['dose'] or ''} [{m['status']}, reported by {m['reported_by']}]" for m in nsaid) + " | history: " + ", ".join(conds)
            ev = {e["evidence_id"]: e for e in L["clinical_evidence"]}
            if nsaid and nsaid[0]["evidence_ids"]:
                e = ev[nsaid[0]["evidence_ids"][0]]
                quote = e["transcript_text"][:220]
                where = f"{e['evidence_id']} ({e['speaker_role']})"
        else:
            cur = [m for m in L["medications"] if m["status"] in ("currently_used", "planned")]
            by = collections.defaultdict(list)
            for m in cur:
                c = CLS.get((m["generic_name"] or m["name"]).lower())
                if c:
                    by[c].append(f"{m['name']} {m['dose'] or ''} [{m['status']}]")
            detail = "; ".join(f"{c}: {', '.join(v)}" for c, v in by.items() if len(v) > 1)
        out.append({"encounter_id": i, "specialty": r["specialty"], "tier": r["tier"], "profile": r["profile"], "flag": f, "issue_detail": detail, "quoted_evidence": quote, "location": where,
                    "evidence_needed_to_resolve": NEED[f], "current_decision": "RETAIN unchanged with flag (owner decision); no exclusion, regeneration or edit"})
with open(AP / "flagged_training_candidates_review.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(out[0]))
    w.writeheader()
    w.writerows(out)
recs = sorted({o["encounter_id"] for o in out})
md = ["# Flagged training candidates: record-by-record review list", "",
      f"Owner decision: the {len(recs)} flagged training candidates are RETAINED in the dataset with their flags; nothing is excluded, regenerated or modified. This list identifies each issue and the evidence needed to resolve it. {len(out)} flag rows for {len(recs)} records (a record can carry several flags). The same rows are in `flagged_training_candidates_review.csv`.", "",
      "Flags are deterministic review prompts made by `b2_allocation_proposal.py`; they do not mean the label is wrong.", "",
      "| Flag | Rows |", "|---|---:|"]
for k, v in collections.Counter(o["flag"] for o in out).most_common():
    md.append(f"| {k} | {v} |")
md += ["", "## What is needed to resolve each flag type", ""] + [f"- **{k}**: {v}" for k, v in NEED.items()] + ["", "## Records", "", "| Id | Specialty / tier | Flag | Detail | Quoted evidence |", "|---|---|---|---|---|"]
for o in out:
    q = (f"{o['location']}: " + o["quoted_evidence"].replace("|", "/")[:170]) if o["quoted_evidence"] else "-"
    md.append(f"| {o['encounter_id']} | {o['specialty']} / {o['tier']} | {o['flag']} | {o['issue_detail'].replace('|', '/')[:200]} | {q} |")
(AP / "FLAGGED_TRAINING_CANDIDATES_REVIEW.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print(json.dumps({"A": mA, "B": mB, "flag_rows": len(out), "records": len(recs), "B_counts": {k: len(v) for k, v in B.items()}}, indent=1))
