"""EXP_007 evaluation of one S1.1 arm versus P02 (primary) and S1.0 (secondary) on the same 50 prompt_dev records, UNCHANGED canonical evaluator (via the frozen EXP_006 evaluate_s1 helpers).
usage: python -B -s evaluate_s1_1.py --arm B1|B2|B3        |      python -B -s evaluate_s1_1.py --compare
Reads prompt_dev transcripts and labels only (StrictAccessSpy); writes only inside EXP_007."""
import collections
import json
import os
import statistics as st
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
EXP7 = HERE.parent
EXP6 = EXP7.parent / "EXP_006_S1_SIMPLIFIED_EXTRACTION"
DATA = Path(os.environ.get("S1_1_EVAL_ROOT", str(EXP7)))   # arm data root (default: EXP_007); the override exists only for dry runs on mock data
sys.path.insert(0, str(EXP6 / "s1"))
sys.path.insert(0, str(HERE))
import evaluate_s1 as E  # noqa: E402  (frozen S1.0 evaluator module: importing installs the dev guard; main() is not run)
import s1_1_adapter as A  # noqa: E402
from direct_inference_baseline.evaluation import schema_validator as SV  # noqa: E402
from direct_inference_baseline.evaluation.entity_matching import CATEGORIES, entity_list, prf  # noqa: E402
from direct_inference_baseline.inference.output_parser import parse_response  # noqa: E402

G, ER, IDS = E.G, E.ER, E.IDS
DEFS = json.loads((EXP7 / "config" / "S1_1_ACCEPTANCE_AND_DEFINITIONS.json").read_text(encoding="utf-8"))
TH = DEFS["acceptance_thresholds_approved"]
JUNK = {"", "none", "null", "n/a", "na", "unknown", "nothing", "-"}
EXCL1 = ["clinical_conditions"]
EXCL2 = ["clinical_conditions", "clinical_uncertainties"]


def micro_from(res, exclude=()):
    t = {k: sum(res[e]["strict"][c][k] for e in IDS for c in CATEGORIES if c not in exclude) for k in ("tp", "fp", "fn")}
    return {**t, **prf(t["tp"], t["fp"], t["fn"])}


def load_dir(d):
    return {eid: json.loads((d / f"encounter_{eid}.json").read_text(encoding="utf-8")) for eid in IDS if (d / f"encounter_{eid}.json").exists()}


def dup(P):
    return sum(sum(n - 1 for n in collections.Counter(E.norm_text(k) for k in (E.KEYS[c](e) for e in entity_list(p, c)) if k).values() if n > 1) for p in P.values() for c in CATEGORIES)


def loop_or_empty(s11, parse_notes):
    loops = []
    for k, f in A.PRIMARY.items():
        v = s11.get(k)
        names = [str(x.get(f, "")).strip().lower() for x in v if isinstance(x, dict)] if isinstance(v, list) else []
        if len(names) >= 3 and (max(names.count(n) for n in set(names)) >= 3 or sum(n in JUNK for n in names) >= 3):
            loops.append(k)
    cc = s11.get("chief_complaint", "")
    cc = cc if isinstance(cc, str) else ""
    allempty = all(not (isinstance(s11.get(k), list) and s11.get(k)) for k in A.PRIMARY)
    empty = len(cc.strip()) < 4 or not any(c.isalnum() for c in cc) or allempty
    degenerate = any("degenerate repetition" in n for n in (parse_notes or []))
    return loops, empty, degenerate


def eff(recs):
    return {"input_tokens_mean": round(st.mean(r["prompt_tokens"] for r in recs), 1), "output_tokens_mean": round(st.mean(r["completion_tokens"] for r in recs), 1),
            "output_tokens_median": st.median(r["completion_tokens"] for r in recs), "output_tokens_max": max(r["completion_tokens"] for r in recs),
            "total_tokens_mean": round(st.mean(r["prompt_tokens"] + r["completion_tokens"] for r in recs), 1), "latency_s_mean": round(st.mean(r["latency_seconds"] for r in recs), 1),
            "latency_s_median": round(st.median(r["latency_seconds"] for r in recs), 1), "latency_s_total": round(sum(r["latency_seconds"] for r in recs), 1),
            "tokens_per_second_overall_mean": round(st.mean(r["completion_tokens"] / r["latency_seconds"] for r in recs), 2)}


def perf_add(e, path):
    p = Path(path)
    pc = json.loads(p.read_text(encoding="utf-8"))["per_call_in_order"] if p.exists() else []
    if pc:
        e["decode_tokens_per_second_mean"] = round(st.mean(x["decode_tokens_per_second"] for x in pc), 2)
        e["prefill_tokens_per_second_mean"] = round(st.mean(x["prefill_tokens_per_second"] for x in pc), 1)
        e["peak_working_set_mb_max"] = max(x.get("peak_working_set_mb_process_so_far", 0) for x in pc)
    return e


def system_block(name, preds):
    res, agg = E.score_all(preds)
    cl, ex = E.analyse(name, preds)
    cl.pop("speaker_errors", None)      # placeholder in the frozen S1.0 helper; speaker accuracy comes from the canonical evaluator below
    sv = [SV.validate(p) for p in preds.values()]
    cnt = dict(sum((collections.Counter(x.counts) for x in sv), collections.Counter()))
    block = {"strict_micro": agg["strict"]["micro"], "strict_macro": agg["strict"]["macro"], "tp_fp_fn": micro_from(res), "fuzzy_micro": agg["fuzzy"]["micro"],
             "micro_excl_clinical_conditions": micro_from(res, EXCL1), "micro_excl_clinical_conditions_and_uncertainties": micro_from(res, EXCL2),
             "speaker_attribution": agg["speaker_attribution"], "negation_polarity": agg["negation_polarity"], "unsupported_claims": agg["unsupported_claims"], "attributes": agg["attributes"],
             "vital_signs": agg["vital_signs"], "clinical_errors": cl, "allergy_status_examples": ex.get("allergy_status", [])[:6],
             "canonical_schema_violations": cnt, "canonical_fully_compliant_records": sum(x.compliant for x in sv), "records_with_output": len(preds), "duplicate_facts": dup(preds)}
    return res, agg, block


def cat_rows(agg):
    return E.cat_table(agg)


def evaluate_arm(arm):
    cfg = json.loads((DATA / "config" / f"S1_1_{arm}_CONFIG.json").read_text(encoding="utf-8"))
    run = cfg["run_id"]
    man = json.loads((DATA / "manifests" / run / "run_manifest.json").read_text(encoding="utf-8"))
    parsed_dir, adapted_dir = DATA / "outputs" / "parsed" / run, DATA / "outputs" / "adapted" / run
    adapted_dir.mkdir(parents=True, exist_ok=True)
    out_dir = DATA / "evaluation" / arm
    (out_dir / "record_metrics").mkdir(parents=True, exist_ok=True)
    spy = G.StrictAccessSpy(allow_validation=False)
    with spy:
        p02 = E.load_p02()
        s10 = load_dir(EXP6 / "outputs" / "adapted" / "S1_dev50")
        arm_pred, struct, issues, problems, flags = {}, collections.Counter(), collections.Counter(), [], collections.Counter()
        per_rec = {}
        for eid in IDS:
            rec = man["records"].get(eid, {})
            struct["attempted"] += rec != {}
            struct["valid_json"] += rec.get("parse_status") == "ok"
            struct["parse_failures"] += rec.get("status") == "failed"
            struct["failure_invalid_json"] += rec.get("failure_type") == "invalid_json"
            struct["failure_truncated"] += rec.get("failure_type") == "truncated"
            struct["failure_other"] += rec.get("status") == "failed" and rec.get("failure_type") not in ("invalid_json", "truncated")
            struct["token_cap_hits"] += rec.get("finish_reason") == "length"
            struct["generation_failures(inference_error)"] += rec.get("failure_type") == "inference_error"
            pth = parsed_dir / f"encounter_{eid}.json"
            if not pth.exists():
                continue
            s11 = json.loads(pth.read_text(encoding="utf-8"))
            sc = json.loads((DATA / "outputs" / "sidecar" / f"encounter_{eid}.json").read_text(encoding="utf-8"))
            iss = A.validate_s11(s11)
            for i in iss:
                issues[i["kind"]] += 1
            struct["s11_format_fully_valid_records"] += not iss
            loops, empty, degenerate = loop_or_empty(s11, rec.get("parse_notes"))
            struct["records_with_repetition_loop"] += bool(loops) or degenerate
            struct["records_with_empty_collapse"] += empty
            ad, probs, fl = A.adapt(s11, eid, sc)
            problems += [dict(p, encounter_id=eid) for p in probs]
            for f in fl:
                flags[f["kind"]] += 1
            struct["adapter_failure_records"] += ad is None or any(q["kind"] == "adapter_failure" for q in probs)
            if ad is not None:
                arm_pred[eid] = ad
                (adapted_dir / f"encounter_{eid}.json").write_text(json.dumps(ad, indent=2, ensure_ascii=False), encoding="utf-8")
                struct["records_with_zero_entities"] += sum(len(entity_list(ad, c)) for c in CATEGORIES) == 0
            per_rec[eid] = {"parse_status": rec.get("parse_status"), "finish_reason": rec.get("finish_reason"), "loops": loops, "degenerate": degenerate, "empty_collapse": empty, "format_issues": len(iss), "flags": len(fl)}
        ra, aa, ba = system_block(arm, arm_pred)
        r2, a2, b2 = system_block("P02", p02)
        r1, a1, b1 = system_block("S1.0", s10)
        for eid in IDS:
            rec = {"encounter_id": eid, "arm": per_rec.get(eid), arm: {c: ra[eid]["strict"][c] for c in CATEGORIES}, "S1.0": {c: r1[eid]["strict"][c] for c in CATEGORIES}, "P02": {c: r2[eid]["strict"][c] for c in CATEGORIES}}
            for k in (arm, "S1.0", "P02"):
                rec[k + "_micro"] = prf(*(sum(rec[k][c][x] for c in CATEGORIES) for x in ("tp", "fp", "fn")))
            (out_dir / "record_metrics" / f"encounter_{eid}.json").write_text(json.dumps(rec, indent=1, default=str), encoding="utf-8")
        cats = {arm: cat_rows(aa), "S1.0": cat_rows(a1), "P02": cat_rows(a2)}
        collapse = [c for c in CATEGORIES if cats[arm][c]["tp"] == 0 and cats["P02"][c]["tp"] >= 3]
        regress = [c for c in CATEGORIES if cats["P02"][c]["recall"] and cats[arm][c]["recall"] is not None and cats[arm][c]["recall"] < 0.5 * cats["P02"][c]["recall"]]
        recs = [man["records"][i] for i in IDS if i in man["records"] and "completion_tokens" in man["records"][i]]
        e_arm = perf_add(eff(recs), DATA / "logs" / f"performance_{arm}.json") if recs else {}
        e_arm["wall_seconds_run"] = json.loads((DATA / "manifests" / f"S1_1_{arm}_RUN_SETTINGS.json").read_text(encoding="utf-8")).get("wall_seconds_this_invocation")
        e02 = perf_add(eff([E.P02_MAN["records"][i] for i in IDS]), E.P02_RUN / "performance.json")
        e10 = perf_add(eff([json.loads((EXP6 / "manifests" / "S1_dev50" / "run_manifest.json").read_text(encoding="utf-8"))["records"][i] for i in IDS]), EXP6 / "logs" / "performance.json")
        audit = {"locked_test_files_opened": G.locked_test_accesses(spy.opened), "sealed_hash_file_opened": any("SEALED" in x for x in spy.opened), "validation_records_opened": spy.report()["validation_records_opened"],
                 "label_files_opened_prompt_dev_only": spy.report()["label_files_opened"]}
    sp = ba["speaker_attribution"]
    acc = {"micro_f1_ge_0.1507": ba["strict_micro"]["f1"] >= TH["micro_f1_min"], "valid_json_ge_48": struct["valid_json"] >= TH["valid_json_min_of_50"], "speaker_accuracy_ge_0.42": (sp.get("accuracy") or 0) >= TH["speaker_attribution_accuracy_min"],
           "no_category_collapse": not collapse}
    agg = {"experiment": "EXP_007 S1.1", "arm": arm, "run_id": run, "config": cfg, "scope": "prompt_dev (50 ids, development-set results only; further tuning on these records is not independent validation)", "ids": IDS,
           arm: ba, "P02": b2, "S1.0": b1,
           "structural": {"arm": dict(struct), "s11_format_issues_by_kind": dict(issues), "adapter_problems": problems[:40], "speaker_role_flags": dict(flags), "per_record": per_rec},
           "category_collapse_vs_P02": collapse, "category_regressions_gt50pct_recall_drop_vs_P02": regress,
           "acceptance": {"criteria": acc, "all_pass": all(acc.values()), "thresholds": TH}, "efficiency": {arm: e_arm, "P02": e02, "S1.0": e10}, "file_access_audit": audit}
    (out_dir / f"S1_1_{arm}_AGGREGATE_METRICS.json").write_text(json.dumps(agg, indent=1, default=str), encoding="utf-8")
    (out_dir / f"S1_1_{arm}_CATEGORY_METRICS.json").write_text(json.dumps(cats, indent=1, default=str), encoding="utf-8")
    print(json.dumps({"arm": arm, "micro": ba["strict_micro"], "P02_micro": b2["strict_micro"], "S1.0_micro": b1["strict_micro"], "struct": dict(struct), "speaker_acc": sp.get("accuracy"), "collapse": collapse,
                      "acceptance": acc, "audit": audit}, indent=1, default=str))


if __name__ == "__main__":
    if "--arm" in sys.argv:
        evaluate_arm(sys.argv[sys.argv.index("--arm") + 1])
    else:
        print("usage: --arm B1|B2|B3")
