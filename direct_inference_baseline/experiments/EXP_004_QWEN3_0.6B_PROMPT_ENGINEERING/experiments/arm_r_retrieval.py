"""EXP_004 ARM R: zero-inference retrieval control. Existing P02 outputs (50 prompt_dev ids, NOT modified) + the transcript -> lexical segment retrieval -> evidence_builder -> final-schema JSON -> existing evaluator.
No model call, no GPU. Labels are opened only after the final outputs are written (evaluation), never by the retrieval or the builder. Development ids only.

PRE-REGISTERED CONFIGURATIONS (fixed in this file before any Arm R result was looked at; 'R_simple' reproduces the earlier probe in analysis/evidence_design_probe.py, which I had already seen):
  R_main   : query = stems (first 5 chars of content tokens, evaluator tokeniser) of ALL descriptive text fields of the item (QUERY_FIELDS); segment score = IDF-weighted share of query stems found in the segment,
             IDF per encounter = ln(1 + N_segments / df) (df = segments containing the stem); pick the top-1 segment; ties -> more matched stems, then earliest segment; ABSTAIN (no citation) if score < 0.5.
  R_simple : query = the evaluator's primary key only (KEYS), unweighted share of stems found, top-1 segment, ties -> earliest, never abstains.
Parameters: stem length 5, abstention threshold 0.5, 1 segment per item (retrieval never returns a question+answer pair), no role or position information is used."""
import copy
import json
import math
import random
import re
import statistics as st
import subprocess
import sys
from collections import Counter, defaultdict

from common import EXP4, SPLIT, S, write_json
from evidence_builder import build_evidence, entity_locations, verify_only_evidence_changed
from direct_inference_baseline.evaluation import evaluation_runner as ER
from direct_inference_baseline.evaluation import schema_validator as SV
from direct_inference_baseline.evaluation.dataset_split import load_split
from direct_inference_baseline.evaluation.entity_matching import CATEGORIES, KEYS, content_tokens, entity_list, match_category, norm_text

IDS = SPLIT["prompt_dev_ids"]
assert not set(IDS) & set(load_split("test"))
P02 = EXP4 / "outputs" / "P02_comprehensive_extraction_dev50" / "parsed_predictions" / "P02_comprehensive_extraction_dev50"
OUT = EXP4 / "arm_R"
QUERY_FIELDS = {"chief_complaint": ["value", "normalized_value"], "symptoms": ["name", "normalized_name", "body_site"], "negative_findings": ["finding", "normalized_name"],
                "medical_history.past_medical_history": ["condition", "normalized_condition"], "medical_history.surgical_history": ["procedure", "normalized_procedure"],
                "medical_history.family_history": ["condition", "normalized_condition", "relation"], "medical_history.social_history": ["category", "description", "details"],
                "medications": ["name", "normalized_name", "generic_name", "dose", "frequency"], "allergies": ["substance", "normalized_substance", "reaction"],
                "vital_signs": ["name", "normalized_name", "value"], "physical_examination": ["finding", "normalized_finding", "body_site"], "review_of_systems": ["system", "details"],
                "clinical_conditions": ["name", "normalized_name"], "clinical_assessment": ["assessment", "normalized_assessment"], "procedures_and_investigations": ["name", "normalized_name"],
                "clinical_actions": ["description"], "follow_up": ["time_reference"], "clinical_uncertainties": ["description"]}
THRESHOLD, STEM = 0.5, 5
CFG = {"R_main": {"fields": "all", "idf": True, "threshold": THRESHOLD}, "R_simple": {"fields": "primary_key", "idf": False, "threshold": 0.0}}


def stems_of(text):
    return [t[:STEM] for t in content_tokens(norm_text(text))]


def seg_words(segs):
    return [[w for w in norm_text(s["text"]).split()] for s in segs]


def has(stem, words):
    return any(w.startswith(stem) for w in words)


def category_of(loc):
    sec = loc.split("[")[0]
    return sec if sec == "chief_complaint" or sec.startswith("medical_history.") or sec in QUERY_FIELDS else sec


def query_text(cat, ent, cfg):
    if cfg["fields"] == "primary_key":
        k = KEYS[cat](ent)
        return str(k).split("|")[-1] if k else ""
    return " ".join(str(ent.get(f)) for f in QUERY_FIELDS[cat] if ent.get(f) not in (None, ""))


def pick(cat, ent, segs, words, df, cfg):
    q = list(dict.fromkeys(stems_of(query_text(cat, ent, cfg))))
    if not q:
        return None, 0.0
    N = len(segs)
    w = {t: (math.log(1 + N / max(1, df.get(t, 0))) if cfg["idf"] else 1.0) for t in q}
    den = sum(w.values())
    best = (-1.0, -1, 0)  # score, matched count, -index
    bi = 0
    for i, ws in enumerate(words):
        m = [t for t in q if has(t, ws)]
        sc = sum(w[t] for t in m) / den
        key = (round(sc, 9), len(m) if cfg["idf"] else 0, -i)
        if key > (round(best[0], 9), best[1], best[2]):
            best, bi = (sc, len(m), -i), i
    if best[0] < cfg["threshold"]:
        return None, best[0]
    return segs[bi]["segment_id"], best[0]


def sect_cat(loc):
    return loc.split("[")[0]


def segment_index(ev, segs):
    mm = lambda s: f"{int(s)//60:02d}:{int(s)%60:02d}"
    t = norm_text(ev.get("transcript_text"))
    return [i for i, s in enumerate(segs) if t == norm_text(s["text"]) and s["speaker_id"] == ev.get("speaker_id") and mm(s["start_seconds"]) == ev.get("start_timestamp")]


def run_config(name, cfg):
    odir = OUT / name
    (odir / "final_predictions").mkdir(parents=True, exist_ok=True); (odir / "build_reports").mkdir(exist_ok=True); (odir / "retrieval_choices").mkdir(exist_ok=True)
    agg = Counter(); scores_all = []; positions = Counter(); results = []; per_enc = {}
    for eid in IDS:
        tr = json.loads((S.INPUT_DIR / f"encounter_{eid}.json").read_text(encoding="utf-8")); segs = tr["segments"]
        p02 = json.loads((P02 / f"encounter_{eid}.json").read_text(encoding="utf-8"))
        words = seg_words(segs); df_cache = {}
        df = type("DF", (), {"get": staticmethod(lambda tok, d=0: df_cache.setdefault(tok, sum(has(tok, ws) for ws in words)))})()
        inter = copy.deepcopy(p02)
        choices = {}
        for loc, ent in entity_locations(inter):
            cat = sect_cat(loc)
            sid, sc = pick(cat, ent, segs, words, df, cfg)
            ent["source_segments"] = [sid] if sid else []
            choices[loc] = {"segment": sid, "score": round(sc, 3)}
            scores_all.append(sc)
        final, rep = build_evidence(inter, tr, top_key_order=list(p02.keys()))
        integ = verify_only_evidence_changed(inter, final)
        assert integ["identical_except_evidence_fields"], "builder changed a non-evidence value"
        assert verify_only_evidence_changed(p02, final)["identical_except_evidence_fields"], "final differs from the P02 output outside the evidence fields"
        write_json(odir / "final_predictions" / f"encounter_{eid}.json", final)
        write_json(odir / "build_reports" / f"encounter_{eid}.json", rep)
        write_json(odir / "retrieval_choices" / f"encounter_{eid}.json", choices)
        sv = SV.validate(final)
        agg["entities"] += rep["entities"]; agg["uncited"] += rep["entities_uncited"]; agg["ids_invalid"] += rep["ids_invalid"]; agg["records"] += rep["evidence_records"]
        agg["model_evidence_ids_dropped"] += rep["model_evidence_ids_dropped"]; agg["model_clinical_evidence_discarded"] += rep["model_clinical_evidence_discarded"]
        agg["schema_evidence_field_violations"] += sum(1 for v in sv.violations if "evidence" in v["message"] or "supports" in v["message"])
        agg["schema_violations_total"] += len(sv.violations)
        for loc, c in choices.items():
            if c["segment"]:
                positions[min(int(c["segment"][3:]) - 1, 5)] += 1
        gold = ER.load_gold(eid)
        results.append(ER.score_encounter(gold, final, tr))
        # gold agreement on strictly matched items
        gseg = {}
        ev_by_id = {r["evidence_id"]: r for r in gold.get("clinical_evidence", [])}
        gidx = {r["evidence_id"]: (segment_index(r, segs) or [None])[0] for r in gold.get("clinical_evidence", [])}
        gloc = {id(e): l for l, e in entity_locations(gold)}
        ploc = {id(e): l for l, e in entity_locations(final)}
        for c in CATEGORIES:
            glist, plist = entity_list(gold, c), entity_list(final, c)
            m = match_category(glist, plist, c)
            for ge, pe in m["pairs"]:
                G = {gidx[x] for x in (ge.get("evidence_ids") or []) if gidx.get(x) is not None}
                loc = ploc[id(pe)]
                sel = choices[loc]["segment"]
                selset = {int(sel[3:]) - 1} if sel else set()
                agg["tp_items"] += 1
                if not G:
                    continue
                agg["tp_items_with_gold_cite"] += 1
                agg["tp_abstained"] += not selset
                agg["tp_hit_any"] += bool(selset & G)
                agg["tp_sel_total"] += len(selset); agg["tp_inter_total"] += len(selset & G); agg["tp_gold_total"] += len(G)
                agg["tp_random_expected_hits"] += len(selset) * len(G) / len(segs)
                agg["tp_first_segment_hit"] += 0 in G
                bycat = per_enc.setdefault("by_category", {}).setdefault(c, Counter()); bycat["n"] += 1; bycat["hit"] += bool(selset & G); bycat["abstain"] += not selset
    ag = ER.aggregate(results)
    st_micro = ag["strict"]["micro"]
    n = agg["tp_items_with_gold_cite"]
    summ = {"config": name, "parameters": cfg, "items": agg["entities"], "items_uncited_abstained": agg["uncited"], "abstention_rate": round(agg["uncited"] / agg["entities"], 4), "ids_invalid": agg["ids_invalid"],
            "evidence_records_total": agg["records"], "evidence_records_per_encounter": round(agg["records"] / len(IDS), 2),
            "builder_dropped_model_evidence_ids_items": agg["model_evidence_ids_dropped"], "builder_discarded_model_clinical_evidence_records": agg["model_clinical_evidence_discarded"],
            "schema_violations_total_final": agg["schema_violations_total"], "schema_violations_in_evidence_fields": agg["schema_evidence_field_violations"],
            "extraction_strict_micro": st_micro, "retrieval_score_mean": round(st.mean(scores_all), 3), "selected_segment_position_0_to_5plus": dict(sorted(positions.items())),
            "gold_agreement_on_strict_tp_items": {"n_items_with_gold_citation": n, "abstained": agg["tp_abstained"], "hit_any_rate": round(agg["tp_hit_any"] / n, 4),
                                                   "set_precision": round(agg["tp_inter_total"] / max(1, agg["tp_sel_total"]), 4), "set_recall": round(agg["tp_inter_total"] / agg["tp_gold_total"], 4),
                                                   "random_expected_hit_rate_same_set_size": round(agg["tp_random_expected_hits"] / n, 4), "first_segment_hit_rate": round(agg["tp_first_segment_hit"] / n, 4),
                                                   "by_category": {c: {"n": v["n"], "hit_any": round(v["hit"] / v["n"], 3), "abstained": v["abstain"]} for c, v in per_enc.get("by_category", {}).items()}},
            "evaluator_grounding": ag["evidence_grounding"], "evaluator_speaker_attribution": ag["speaker_attribution"], "evaluator_unsupported_claims": ag["unsupported_claims"]}
    # supplementary diagnostics (timestamps, supports consistency) through the existing diagnostics script
    subprocess.run([sys.executable, "-B", "-s", str(EXP4 / "experiments" / "evidence_diagnostics.py"), f"ArmR_{name}", str(odir / "final_predictions")], check=True, cwd=str(EXP4 / "logs" / "gpu_compiler"), stdout=subprocess.DEVNULL)
    d = json.loads((EXP4 / "evaluation" / f"evidence_diagnostics_ArmR_{name}.json").read_text(encoding="utf-8"))[0]
    summ["supplementary_structure"] = {k: v for k, v in d["supplementary"].items() if k != "counts"}
    write_json(odir / "arm_R_summary.json", summ)
    return summ


(OUT).mkdir(exist_ok=True)
(EXP4 / "logs" / "gpu_compiler").mkdir(parents=True, exist_ok=True)
summaries = {n: run_config(n, c) for n, c in CFG.items()}
write_json(OUT / "arm_R_summary_all.json", summaries)
print(json.dumps(summaries, indent=1, ensure_ascii=False))
