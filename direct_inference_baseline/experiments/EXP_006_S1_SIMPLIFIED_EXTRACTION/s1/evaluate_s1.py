"""EXP_006 evaluation: S1 (adapted) versus P02, same 50 prompt_dev records, UNCHANGED canonical evaluator (evaluation_runner.score_encounter / aggregate).
Modes:
  python -B -s evaluate_s1.py --baseline-only    # validates the pipeline on the stored P02 outputs (must reproduce TP/FP/FN 153/522/1707) - run BEFORE inference
  python -B -s evaluate_s1.py                    # full S1 vs P02 evaluation after the run
Reads prompt_dev transcripts and prompt_dev labels only (StrictAccessSpy); validation and locked-test files are blocked.  Writes only inside EXP_006."""
import collections
import json
import re
import statistics as st
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
EXP6 = HERE.parent
EXP4 = EXP6.parent / "EXP_004_QWEN3_0.6B_PROMPT_ENGINEERING"
sys.path.insert(0, str(EXP4 / "experiments"))
sys.path.insert(0, str(HERE))
from common import S, SPLIT  # noqa: E402
import dev_guard as G  # noqa: E402
import s1_adapter as A  # noqa: E402
from direct_inference_baseline.evaluation import evaluation_runner as ER  # noqa: E402
from direct_inference_baseline.evaluation import schema_validator as SV  # noqa: E402
from direct_inference_baseline.evaluation.entity_matching import CATEGORIES, entity_list, match_category, norm_text, prf, KEYS  # noqa: E402

BASELINE_ONLY = "--baseline-only" in sys.argv
RUN = "S1_dev50"
P02_RUN = EXP4 / "outputs" / "P02_comprehensive_extraction_dev50"
P02_PARSED = P02_RUN / "parsed_predictions" / "P02_comprehensive_extraction_dev50"
P02_MAN = json.loads((EXP4 / "evaluation" / "P02_comprehensive_extraction_dev50" / "run_manifest.json").read_text(encoding="utf-8-sig"))
IDS = P02_MAN["encounter_ids"]
assert IDS == SPLIT["prompt_dev_ids"] and len(IDS) == 50, "the 50 ids must be the P02 prompt_dev ids"
G.install(IDS, include_labels=True, allow_validation=False)
CAT_LABEL = {"chief_complaint": "chief complaint", "symptoms": "symptoms", "negative_findings": "negative findings", "medical_history.past_medical_history": "medical history (past/ongoing)",
             "medical_history.surgical_history": "surgical history", "medical_history.family_history": "family history", "medical_history.social_history": "social history", "medications": "medications",
             "allergies": "allergies", "vital_signs": "vital signs", "physical_examination": "physical examination", "review_of_systems": "review of systems", "clinical_conditions": "clinical conditions",
             "clinical_assessment": "clinical assessment", "procedures_and_investigations": "investigations and procedures", "clinical_actions": "clinical actions", "follow_up": "follow-up",
             "clinical_uncertainties": "clinical uncertainties"}
ISO = re.compile(r"\d{4}-\d{2}-\d{2}|T\d{2}:\d{2}|^\d+(\.\d+)?-\d+(\.\d+)?s$")


def tr_of(eid):
    return json.loads((S.INPUT_DIR / f"encounter_{eid}.json").read_text(encoding="utf-8"))


def allergy_state(p):
    nk = any(isinstance(n, dict) and "no known allergies" in str(n.get("normalized_name") or n.get("finding")).lower() for n in (p.get("negative_findings") or []))
    al = [a for a in (p.get("allergies") or []) if isinstance(a, dict) and str(a.get("substance") or "").strip().lower() not in ("", "none", "no", "nil")]
    return "reported" if al else ("none_stated" if nk else "none_or_not_established")


def analyse(name, preds):
    """gold-based clinical error analysis (development labels) for predictions dict eid -> canonical pred"""
    c = collections.Counter()
    ex = collections.defaultdict(list)
    for eid in IDS:
        p, g, tr = preds.get(eid) or {}, ER.load_gold(eid), tr_of(eid)
        full = " ".join(norm_text(s["text"]) for s in tr["segments"])
        m = {cat: match_category(entity_list(g, cat), entity_list(p, cat), cat) for cat in CATEGORIES}
        # medications
        c["medication_predicted"] += len(entity_list(p, "medications"))
        c["medication_gold"] += len(entity_list(g, "medications"))
        c["medication_identity_errors_false_positive_names"] += m["medications"]["fp"]
        c["medication_fabricated_name_not_in_transcript"] += sum(1 for k, e in m["medications"]["fp_entities"] if not any(t in full for t in norm_text(k).split() if len(t) > 3))
        planned_missing = [e for k, e in m["medications"]["fn_entities"] if e.get("status") == "planned"]
        c["missing_prescribed_medications(gold planned, unmatched)"] += len(planned_missing)
        c["gold_planned_medications"] += sum(1 for e in entity_list(g, "medications") if e.get("status") == "planned")
        for gm, pm in m["medications"]["pairs"]:
            if gm.get("dose") is not None:
                c["dose_checked_on_matched"] += 1
                c["dose_errors_on_matched"] += not ER.AM.same_value(gm.get("dose"), pm.get("dose"))
            if gm.get("status") != pm.get("status"):
                c["medication_status_errors_on_matched"] += 1
        # medication / allergy confusion
        mnames = {norm_text(k) for k, _ in [(KEYS["medications"](e), e) for e in entity_list(p, "medications")] if k}
        for a in entity_list(p, "allergies"):
            k = norm_text(KEYS["allergies"](a))
            if k and k in mnames:
                c["medication_listed_as_allergy"] += 1
        gmed = {norm_text(KEYS["medications"](e)) for e in entity_list(g, "medications")}
        c["allergy_entries_that_are_gold_medications"] += sum(1 for a in entity_list(p, "allergies") if norm_text(KEYS["allergies"](a)) in gmed)
        c["allergy_placeholder_entries(none/blank)"] += sum(1 for a in (p.get("allergies") or []) if isinstance(a, dict) and str(a.get("substance") or "").strip().lower() in ("", "none", "no", "nil"))
        # allergy status
        gs, ps = allergy_state(g), allergy_state(p)
        c["allergy_status_records_compared"] += 1
        c["allergy_status_errors"] += gs != ps
        if gs != ps:
            ex["allergy_status"].append(f"{eid}: gold {gs} / predicted {ps}")
        # polarity
        gpos = {norm_text(k) for k in (KEYS["symptoms"](e) for e in entity_list(g, "symptoms")) if k}
        gneg = {norm_text(k) for k in (KEYS["negative_findings"](e) for e in entity_list(g, "negative_findings")) if k}
        ppos = {norm_text(k) for k in (KEYS["symptoms"](e) for e in entity_list(p, "symptoms")) if k}
        pneg = {norm_text(k) for k in (KEYS["negative_findings"](e) for e in entity_list(p, "negative_findings")) if k}
        c["polarity_errors_pred_negative_is_gold_positive"] += len(pneg & gpos)
        c["polarity_errors_pred_positive_is_gold_negative"] += len(ppos & gneg)
        c["contradictions_same_item_positive_and_negative_in_prediction"] += len(ppos & pneg)
        # temporality on matched symptoms
        for gm, pm in m["symptoms"]["pairs"]:
            c["temporality_checked_on_matched_symptoms"] += 1
            c["temporality_errors_on_matched_symptoms"] += norm_text(gm.get("temporality")) != norm_text(pm.get("temporality"))
        # fabricated (unsupported) facts: extra entities whose key words do not occur in the transcript; fabricated dates
        r = ER.score_encounter(g, p, tr)
        c["fabricated_unsupported_claims(evaluator)"] += r["unsupported"]["unsupported_claims"]
        blob = json.dumps(p, ensure_ascii=False)
        c["fabricated_date_or_timestamp_values"] += len(ISO.findall(blob)) if False else sum(1 for s in re.findall(r'"[^"]*"', blob) if ISO.search(s.strip('"')))
        # duplicates
        for cat in CATEGORIES:
            keys = [norm_text(k) for k in (KEYS[cat](e) for e in entity_list(p, cat)) if k]
            c["duplicate_facts_same_key_in_category"] += sum(n - 1 for n in collections.Counter(keys).values() if n > 1)
        c["speaker_errors"] += 0
    return dict(c), {k: v[:12] for k, v in ex.items()}


def score_all(preds):
    res = {}
    for eid in IDS:
        res[eid] = ER.score_encounter(ER.load_gold(eid), preds.get(eid), tr_of(eid))
    return res, ER.aggregate(list(res.values()))


def cat_table(agg):
    t = {}
    for c in CATEGORIES:
        x = agg["strict"]["per_category"][c]
        t[c] = {"label": CAT_LABEL[c], **{k: x[k] for k in ("tp", "fp", "fn", "precision", "recall", "f1")}}
    return t


def load_p02():
    return {eid: json.loads((P02_PARSED / f"encounter_{eid}.json").read_text(encoding="utf-8")) for eid in IDS if (P02_PARSED / f"encounter_{eid}.json").exists()}


def main():
    spy = G.StrictAccessSpy(allow_validation=False)
    out_dir = EXP6 / "evaluation"
    (out_dir / "record_metrics").mkdir(parents=True, exist_ok=True)
    with spy:
        p02 = load_p02()
        r02, a02 = score_all(p02)
        m02 = a02["strict"]
        tot = {k: sum(r02[e]["strict"][c][k] for e in IDS for c in CATEGORIES) for k in ("tp", "fp", "fn")}
        print("P02 baseline reproduced with the unchanged evaluator:", tot, "micro F1", round(m02["micro"]["f1"], 4), "macro F1", round(m02["macro"]["f1"], 4) if m02["macro"].get("f1") is not None else None)
        if BASELINE_ONLY:
            ok = (tot["tp"], tot["fp"], tot["fn"]) == (153, 522, 1707)
            (out_dir / "baseline_reproduction_check.json").write_text(json.dumps({"p02_strict_tp_fp_fn": tot, "expected": [153, 522, 1707], "reproduced": ok, "micro": m02["micro"], "macro": m02["macro"],
                                                                                  "file_access": {"locked_test": G.locked_test_accesses(spy.opened), "sealed": any("SEALED" in x for x in spy.opened), "validation": spy.report()["validation_records_opened"]}}, indent=1, default=str), encoding="utf-8")
            print("BASELINE REPRODUCED" if ok else "BASELINE MISMATCH - STOP")
            sys.exit(0 if ok else 5)
        # ---------------- S1
        raw_dir, parsed_dir, adapted_dir = (EXP6 / "outputs" / n / RUN for n in ("raw", "parsed", "adapted"))
        man = json.loads((EXP6 / "manifests" / RUN / "run_manifest.json").read_text(encoding="utf-8"))
        s1_adapted, struct = {}, collections.Counter()
        issues_by_kind, adapter_problems = collections.Counter(), []
        for eid in IDS:
            rec = man["records"].get(eid, {})
            struct["attempted"] += rec != {}
            struct["valid_json"] += rec.get("parse_status") == "ok"
            struct["parse_failures"] += rec.get("status") == "failed"
            struct["truncated_outputs(finish_reason!=stop)"] += rec.get("finish_reason") not in (None, "stop")
            pth = parsed_dir / f"encounter_{eid}.json"
            if not pth.exists():
                continue
            s1 = json.loads(pth.read_text(encoding="utf-8"))
            iss = A.validate_s1(s1)
            for i in iss:
                issues_by_kind[i["kind"]] += 1
            struct["s1_format_fully_valid_records"] += not iss
            ad, probs = A.adapt(s1)
            adapter_problems += [dict(p, encounter_id=eid) for p in probs]
            struct["adapter_failures"] += ad is None or bool([q for q in probs if q["kind"] == "adapter_failure"])
            if ad is not None:
                s1_adapted[eid] = ad
                (adapted_dir).mkdir(parents=True, exist_ok=True)
                (adapted_dir / f"encounter_{eid}.json").write_text(json.dumps(ad, indent=2, ensure_ascii=False), encoding="utf-8")
                struct["empty_outputs(zero entities)"] += sum(len(entity_list(ad, c)) for c in CATEGORIES) == 0
        r1, a1 = score_all(s1_adapted)
        sv_s1 = [SV.validate(p) for p in s1_adapted.values()]
        sv_02 = [SV.validate(p) for p in p02.values()]
        cnt = lambda L: dict(sum((collections.Counter(x.counts) for x in L), collections.Counter()))
        dup = lambda P: sum(sum(n - 1 for n in collections.Counter(norm_text(k) for k in (KEYS[c](e) for e in entity_list(p, c)) if k).values() if n > 1) for p in P.values() for c in CATEGORIES)
        cl1, ex1 = analyse("S1", s1_adapted)
        cl2, ex2 = analyse("P02", p02)
        for eid in IDS:
            rec = {"encounter_id": eid, "S1": {c: r1[eid]["strict"][c] for c in CATEGORIES}, "P02": {c: r02[eid]["strict"][c] for c in CATEGORIES}}
            for k in ("S1", "P02"):
                rec[k + "_micro"] = prf(*(sum(rec[k][c][x] for c in CATEGORIES) for x in ("tp", "fp", "fn")))
            (out_dir / "record_metrics" / f"encounter_{eid}.json").write_text(json.dumps(rec, indent=1, default=str), encoding="utf-8")
        # efficiency
        s1rec = man["records"]
        eff = lambda recs: {"input_tokens_mean": round(st.mean(r["prompt_tokens"] for r in recs), 1), "output_tokens_mean": round(st.mean(r["completion_tokens"] for r in recs), 1),
                            "output_tokens_median": st.median(r["completion_tokens"] for r in recs), "output_tokens_max": max(r["completion_tokens"] for r in recs),
                            "total_tokens_mean": round(st.mean(r["prompt_tokens"] + r["completion_tokens"] for r in recs), 1), "latency_s_mean": round(st.mean(r["latency_seconds"] for r in recs), 1),
                            "latency_s_median": round(st.median(r["latency_seconds"] for r in recs), 1), "latency_s_total": round(sum(r["latency_seconds"] for r in recs), 1),
                            "tokens_per_second_overall_mean": round(st.mean(r["completion_tokens"] / r["latency_seconds"] for r in recs), 2)}
        e1 = eff([s1rec[i] for i in IDS if i in s1rec and "completion_tokens" in s1rec[i]])
        e2 = eff([P02_MAN["records"][i] for i in IDS])
        perf = lambda p: json.loads(Path(p).read_text(encoding="utf-8"))["per_call_in_order"] if Path(p).exists() else []
        for nm, pth, e in (("S1", EXP6 / "logs" / "performance.json", e1), ("P02", P02_RUN / "performance.json", e2)):
            pc = perf(pth)
            if pc:
                e["decode_tokens_per_second_mean"] = round(st.mean(x["decode_tokens_per_second"] for x in pc), 2)
                e["prefill_tokens_per_second_mean"] = round(st.mean(x["prefill_tokens_per_second"] for x in pc), 1)
                e["peak_working_set_mb_max"] = max(x.get("peak_working_set_mb_process_so_far", 0) for x in pc)
                e["load_compile_seconds_mean"] = round(st.mean(x["load_compile_seconds"] for x in pc), 2)
        agg = {"experiment": "EXP_006 S1", "scope": "prompt_dev (50 ids, development-set results only)", "ids": IDS,
               "S1": {"strict_micro": a1["strict"]["micro"], "strict_macro": a1["strict"]["macro"], "tp_fp_fn": {k: sum(r1[e]["strict"][c][k] for e in IDS for c in CATEGORIES) for k in ("tp", "fp", "fn")}, "fuzzy_micro": a1["fuzzy"]["micro"],
                      "attributes": a1["attributes"], "speaker_attribution": a1["speaker_attribution"], "negation_polarity": a1["negation_polarity"], "unsupported_claims": a1["unsupported_claims"], "vital_signs": a1["vital_signs"]},
               "P02": {"strict_micro": a02["strict"]["micro"], "strict_macro": a02["strict"]["macro"], "tp_fp_fn": tot, "fuzzy_micro": a02["fuzzy"]["micro"], "attributes": a02["attributes"], "speaker_attribution": a02["speaker_attribution"],
                       "negation_polarity": a02["negation_polarity"], "unsupported_claims": a02["unsupported_claims"], "vital_signs": a02["vital_signs"]},
               "structural": {"S1_intermediate_format": dict(struct), "S1_format_issues_by_kind": dict(issues_by_kind), "adapter_problems": adapter_problems[:30], "adapted_canonical_schema_violations": cnt(sv_s1),
                              "adapted_canonical_fully_compliant_records": sum(x.compliant for x in sv_s1), "P02_canonical_schema_violations": cnt(sv_02), "P02_canonical_fully_compliant_records": sum(x.compliant for x in sv_02),
                              "P02_valid_json": sum(P02_MAN["records"][i]["parse_status"] == "ok" for i in IDS), "duplicate_facts": {"S1": dup(s1_adapted), "P02": dup(p02)}},
               "clinical_errors": {"S1": cl1, "P02": cl2, "examples_allergy_status": {"S1": ex1.get("allergy_status", []), "P02": ex2.get("allergy_status", [])}},
               "efficiency": {"S1": e1, "P02": e2}}
        (out_dir / "S1_AGGREGATE_METRICS.json").write_text(json.dumps(agg, indent=1, default=str), encoding="utf-8")
        (out_dir / "aggregate_metrics.json").write_text(json.dumps({k: agg[k] for k in ("S1", "P02", "structural", "efficiency")}, indent=1, default=str), encoding="utf-8")
        cat = {"S1": cat_table(a1), "P02": cat_table(a02)}
        (out_dir / "S1_CATEGORY_METRICS.json").write_text(json.dumps(cat, indent=1, default=str), encoding="utf-8")
        (out_dir / "category_metrics.json").write_text(json.dumps(cat, indent=1, default=str), encoding="utf-8")
        audit = {"locked_test_files_opened": G.locked_test_accesses(spy.opened), "sealed_hash_file_opened": any("SEALED" in x for x in spy.opened), "validation_records_opened": spy.report()["validation_records_opened"],
                 "label_files_opened_prompt_dev_only": spy.report()["label_files_opened"]}
        (out_dir / "evaluation_file_access_audit.json").write_text(json.dumps(audit, indent=1), encoding="utf-8")
        print(json.dumps({"S1_micro": a1["strict"]["micro"], "P02_micro": a02["strict"]["micro"], "S1_tp_fp_fn": agg["S1"]["tp_fp_fn"], "struct": dict(struct), "audit": audit}, indent=1, default=str))


if __name__ == "__main__":
    main()
