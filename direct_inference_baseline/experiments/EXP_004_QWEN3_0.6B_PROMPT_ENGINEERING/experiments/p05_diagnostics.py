"""EXP_004 P05 zero-inference diagnostics on EXISTING outputs (no model, no GPU). prompt_dev 50 ids only; validation and locked-test ids are never read (asserted); P02 artifacts are only read, never written.
 (B) retrieval on GOLD facts (large n, per category): the retrieval quality ceiling, independent of extraction quality
 (A) retrieval on the facts P02 actually extracted that strictly (or fuzzily) match a gold item: real model wording, small n
 (C) all P02 items: abstention reasons, post-hoc conflict rates
 (D) integration: R_cons ids -> the existing builder -> final-schema JSON copies in p05_diagnostics/ (P02 untouched) + the existing evaluator
Parameters are fixed in p05_retrieval.py before any result was computed. The retrieval rules were calibrated on the gold probe of the SAME 50 records, so the results are development results, not an independent test."""
import copy
import json
import random
import subprocess
import sys
from collections import Counter, defaultdict

from common import EXP4, S, SPLIT, write_json
import p05_retrieval as R
from evidence_builder import build_evidence, entity_locations, verify_only_evidence_changed
from direct_inference_baseline.evaluation import evaluation_runner as ER
from direct_inference_baseline.evaluation import schema_validator as SV
from direct_inference_baseline.evaluation.dataset_split import load_split
from direct_inference_baseline.evaluation.entity_matching import CATEGORIES, entity_list, match_category, norm_text

IDS = SPLIT["prompt_dev_ids"]
assert not set(IDS) & set(load_split("test")) and not set(IDS) & set(SPLIT["validation_ids"])
P02 = EXP4 / "outputs" / "P02_comprehensive_extraction_dev50" / "parsed_predictions" / "P02_comprehensive_extraction_dev50"
OUT = EXP4 / "p05_diagnostics"
OUT.mkdir(exist_ok=True)
mm = lambda s: f"{int(s)//60:02d}:{int(s)%60:02d}"
GROUPS = {"positive findings (chief complaint, symptoms, conditions)": ["chief_complaint", "symptoms", "clinical_conditions"], "negative findings": ["negative_findings"], "medications": ["medications"], "allergies": ["allergies"],
          "vital signs": ["vital_signs"], "family history": ["medical_history.family_history"], "surgical history": ["medical_history.surgical_history"],
          "assessment, procedures and clinical actions": ["clinical_assessment", "procedures_and_investigations", "clinical_actions"],
          "other (past history, social history, exam, review of systems, follow-up, uncertainties)": ["medical_history.past_medical_history", "medical_history.social_history", "physical_examination", "review_of_systems", "follow_up", "clinical_uncertainties"],
          "speaker-sensitive facts (categories with a hard speaker-class rule)": list(R.EXPECT_CLASS)}
ENC, GOLDSEG, TR = {}, {}, {}
for eid in IDS:
    tr = json.loads((S.INPUT_DIR / f"encounter_{eid}.json").read_text(encoding="utf-8")); TR[eid] = tr
    ENC[eid] = R.Enc(tr["segments"])
    g = ER.load_gold(eid); seg_of = {}
    for r in g.get("clinical_evidence", []):
        t = norm_text(r["transcript_text"])
        hit = [i for i, s in enumerate(tr["segments"]) if t == norm_text(s["text"]) and s["speaker_id"] == r["speaker_id"] and mm(s["start_seconds"]) == r["start_timestamp"]]
        seg_of[r["evidence_id"]] = hit[0] if hit else None
    GOLDSEG[eid] = (g, seg_of)


def gold_set(eid, ge):
    seg_of = GOLDSEG[eid][1]
    return {seg_of[x] for x in (ge.get("evidence_ids") or []) if seg_of.get(x) is not None}


def post_flags(cat, item, enc, sel):  # polarity_conflict here: positive item with negated anchor, or negative finding without a cue anywhere (weaker than the v3 local rule)
    """post-hoc conflict detectors applied to ANY selection (also to the unfiltered baselines)."""
    f = Counter()
    if not sel:
        return f
    nonq = [i for i in sel if not enc.q[i]] or list(sel)
    f["question_only"] += all(enc.q[i] for i in sel)
    f["greeting_like"] += any(i <= 1 and (set(enc.raw[i]) & R.SMALLTALK) and len(enc.words[i]) <= 12 for i in sel)
    f["position0"] += 0 in sel
    fields = R.query_fields(cat, item)
    matched = list({s for st in fields.values() for s in st if any(R.sm(s, w) for i in nonq for w in enc.words[i])})
    if cat == "negative_findings":
        f["polarity_conflict"] += not any(R.has_neg(enc.raw[i]) for i in nonq)
    elif not R.item_negative(cat, item):   # item-aware definition for ALL rows: a positive item whose anchor is negated in its evidence
        f["polarity_conflict"] += any(R.anchor_negated(enc, i, matched) for i in nonq)
    if cat == "medical_history.family_history":
        f["kin_conflict"] += not any(R.has_kin(enc.raw[i]) for i in nonq)
    elif cat in R.OWN_HISTORY:
        f["kin_conflict"] += any(R.kin_conflict(enc, i, matched) for i in nonq)
    exp = R.EXPECT_CLASS.get(cat)
    if exp:
        f["speaker_class_conflict"] += any(R.role_class(enc.role[i]) != exp for i in nonq)
    return f


def evaluate(items, name, steps):
    """items: list of (eid, cat, item, goldset)"""
    tot = defaultdict(Counter)
    for eid, cat, item, G in items:
        enc = ENC[eid]
        d = R.run_ladder_step(name, steps, cat, item, enc)
        sel = set(d["segments"])
        for key in (cat, "ALL"):
            k = tot[key]; k["n"] += 1
            if d["decision"] == "cited":
                k["cited"] += 1; k["hit"] += bool(sel & G); k["inter"] += len(sel & G); k["sel"] += len(sel); k["context_question"] += bool(d.get("context_question"))
                for fl, v in post_flags(cat, item, enc, sel).items():
                    k[fl] += v
            else:
                k["abstain_" + d["reason"]] += 1
            k["gold"] += len(G)
    return tot


def row(k):
    n, c = k["n"], k["cited"]
    return {"n": n, "cited": c, "cited_rate": round(c / n, 3) if n else None, "hit_when_cited": round(k["hit"] / c, 3) if c else None, "hit_any_all_items": round(k["hit"] / n, 3) if n else None,
            "set_precision": round(k["inter"] / k["sel"], 3) if k["sel"] else None, "set_recall": round(k["inter"] / k["gold"], 3) if k["gold"] else None,
            **{f"{fl}_of_cited": (round(k[fl] / c, 3) if c else None) for fl in ("question_only", "greeting_like", "position0", "polarity_conflict", "kin_conflict", "speaker_class_conflict")},
            "abstain_reasons": {x[8:]: v for x, v in k.items() if x.startswith("abstain_")}}


def group_rows(tot):
    out = {}
    for g, cats in GROUPS.items():
        k = Counter()
        for c in cats:
            k.update(tot.get(c, Counter()))
        out[g] = row(k) if k["n"] else None
    return out


# ---------------------------------------------------------------- items
gold_items, p02_strict, p02_fuzzy, p02_all = [], [], [], []
for eid in IDS:
    g = GOLDSEG[eid][0]
    pred = json.loads((P02 / f"encounter_{eid}.json").read_text(encoding="utf-8"))
    for c in CATEGORIES:
        for ge in entity_list(g, c):
            G = gold_set(eid, ge)
            if G:
                gold_items.append((eid, c, ge, G))
        gl, pl = entity_list(g, c), entity_list(pred, c)
        m = match_category(gl, pl, c, fuzzy=True)
        for ge, pe in m["pairs"]:
            G = gold_set(eid, ge)
            if G:
                p02_strict.append((eid, c, pe, G))
        for ge, pe in m["fuzzy_pairs"]:
            G = gold_set(eid, ge)
            if G:
                p02_fuzzy.append((eid, c, pe, G))
        for pe in pl:
            p02_all.append((eid, c, pe, set()))
print(f"items: gold facts {len(gold_items)}, P02 strict-matched {len(p02_strict)}, P02 fuzzy-only matched {len(p02_fuzzy)}, P02 all extracted {len(p02_all)}")
res = {"counts": {"gold_facts_with_gold_citation": len(gold_items), "p02_strict_matched": len(p02_strict), "p02_fuzzy_only_matched": len(p02_fuzzy), "p02_all_items": len(p02_all)}, "ladder": {}}
for name, steps in R.LADDER:
    b = evaluate(gold_items, name, steps); a = evaluate(p02_strict, name, steps); af = evaluate(p02_strict + p02_fuzzy, name, steps); c = evaluate(p02_all, name, steps)
    res["ladder"][name] = {"B_gold_facts": {"ALL": row(b["ALL"]), "by_group": group_rows(b), "by_category": {k: row(v) for k, v in b.items() if k != "ALL"}},
                           "A_p02_strict_matched": {"ALL": row(a["ALL"]), "by_group": group_rows(a), "by_category": {k: row(v) for k, v in a.items() if k != "ALL"}},
                           "A2_p02_strict_plus_fuzzy_matched": {"ALL": row(af["ALL"])},
                           "C_p02_all_items": {"ALL": row(c["ALL"]), "by_category": {k: row(v) for k, v in c.items() if k != "ALL"}}}
write_json(OUT / "p05_ladder_results.json", res)
hdr = f"{'step':30s} | {'B gold facts: cited hit|cited hit-all  P   R':44s} | {'A P02-matched: n cited hit|cited hit-all':40s} | C all P02: cited"
print(hdr)
for name, _ in R.LADDER:
    b, a, c = res["ladder"][name]["B_gold_facts"]["ALL"], res["ladder"][name]["A_p02_strict_matched"]["ALL"], res["ladder"][name]["C_p02_all_items"]["ALL"]
    print(f"{name:30s} | {b['cited_rate']:.3f} {b['hit_when_cited'] or 0:.3f} {b['hit_any_all_items']:.3f} {b['set_precision'] or 0:.3f} {b['set_recall'] or 0:.3f} | {a['n']:3d} {a['cited_rate']:.3f} {a['hit_when_cited'] or 0:.3f} {a['hit_any_all_items']:.3f} | {c['cited_rate']:.3f}")
print("\nR_cons v4 by group (B gold facts): n cited_rate hit_when_cited hit_all set_P set_R | (A P02-matched) n cited hit_when_cited")
f = res["ladder"]["C8d + context question for short replies (= R_cons v4)"]
for g in GROUPS:
    b, a = f["B_gold_facts"]["by_group"][g], f["A_p02_strict_matched"]["by_group"][g]
    if b:
        print(f"{g[:48]:48s} {b['n']:5d} {b['cited_rate']:.2f} {b['hit_when_cited'] or 0:.2f} {b['hit_any_all_items']:.2f} {b['set_precision'] or 0:.2f} {b['set_recall'] or 0:.2f} | " + (f"{a['n']:3d} {a['cited_rate']:.2f} {a['hit_when_cited'] or 0:.2f}" if a else "n=0"))

# ---------------------------------------------------------------- (D) integration on copies of P02 outputs (v1 and v2)
sample_v2 = defaultdict(list)


def integrate(tag, steps):
    odir = OUT / f"final_predictions_{tag}"
    odir.mkdir(exist_ok=True)
    D = Counter(); reasons = Counter(); results = []
    for eid in IDS:
        pred = json.loads((P02 / f"encounter_{eid}.json").read_text(encoding="utf-8")); enc = ENC[eid]; tr = TR[eid]
        inter = copy.deepcopy(pred)
        for loc, ent in entity_locations(inter):
            cat = loc.split("[")[0]
            d = R.retrieve(cat, ent, enc, steps)
            ent["source_segments"] = [enc.segs[i]["segment_id"] for i in d["segments"]]
            reasons[(cat, d["reason"])] += 1
            if d["decision"] == "cited" and tag == "v4":
                sample_v2[cat].append((eid, loc, ent, d))
        final, rep = build_evidence(inter, tr, top_key_order=list(SV.TOP_KEYS))
        assert verify_only_evidence_changed(pred, final)["identical_except_evidence_fields"]
        write_json(odir / f"encounter_{eid}.json", final)
        sv = SV.validate(final)
        D["items"] += rep["entities"]; D["cited"] += rep["entities_with_valid_citation"]; D["uncited"] += rep["entities_uncited"]; D["records"] += rep["evidence_records"]; D["ids_invalid"] += rep["ids_invalid"]
        D["evidence_field_violations"] += sum(1 for v in sv.violations if "evidence" in v["message"] or "supports" in v["message"])
        results.append(ER.score_encounter(ER.load_gold(eid), final, tr))
    ag = ER.aggregate(results); gr = ag["evidence_grounding"]; mi = ag["strict"]["micro"]
    by_reason = Counter()
    for (c, r), v in reasons.items():
        by_reason[r] += v
    return {"items": D["items"], "cited": D["cited"], "abstained": D["uncited"], "abstention_rate": round(D["uncited"] / D["items"], 3), "evidence_records_total": D["records"],
            "evidence_records_per_encounter": round(D["records"] / 50, 2), "ids_invalid": D["ids_invalid"], "evidence_field_schema_violations": D["evidence_field_violations"], "extraction_strict_micro": mi,
            "evaluator_grounding_strict_lenient_partial_unsupported_total": [gr["grounded_strict"], gr["grounded_lenient"], gr["partially_supported"], gr["unsupported"], gr["total"]],
            "speaker_attribution": ag["speaker_attribution"]["accuracy"], "abstain_reasons_overall": dict(by_reason),
            "abstain_reasons_by_category": {f"{c}|{r}": v for (c, r), v in sorted(reasons.items())}}


res["integration_D"] = {"v1": integrate("v1", R.STEPS_ALL), "v2": integrate("v2", R.STEPS_V2), "v3": integrate("v3", R.STEPS_V3), "v4": integrate("v4", R.STEPS_V4)}
write_json(OUT / "p05_ladder_results.json", res)
for tag in ("v1", "v2", "v3", "v4"):
    x = res["integration_D"][tag]
    print(f"\nD integration {tag}:", json.dumps({k: v for k, v in x.items() if k != "abstain_reasons_by_category"}))
rng = random.Random(20260415); sample = []
for g in ("positive findings (chief complaint, symptoms, conditions)", "negative findings", "medications", "allergies", "vital signs", "family history", "surgical history", "assessment, procedures and clinical actions", "other (past history, social history, exam, review of systems, follow-up, uncertainties)"):
    pool = [x for c in GROUPS[g] for x in sample_v2.get(c, [])]
    for eid, loc, ent, d in rng.sample(pool, min(4, len(pool))):
        enc = ENC[eid]
        key = next((str(ent.get(k)) for k in ("normalized_value", "normalized_name", "normalized_condition", "normalized_procedure", "normalized_finding", "normalized_substance", "normalized_assessment", "system", "category", "description", "name", "finding", "value", "time_reference") if ent.get(k)), "")
        sample.append({"id": eid, "loc": loc, "group": g[:30], "item": key[:60], "reported_by": str(ent.get("reported_by") or ent.get("observed_by") or ent.get("stated_by") or ""), "context_question": bool(d.get("context_question")),
                       "cited": [{"seg": enc.segs[i]["segment_id"], "who": f"{enc.speaker[i]}/{enc.role[i]}", "text": enc.segs[i]["text"][:150]} for i in d["segments"]]})
write_json(OUT / "r_cons_review_sample.json", sample)
print("sample items:", len(sample))
