"""Read-only analysis of P00 vs P01 (Qwen3-1.7B) on the shared completed-30 id subset: formatting-vs-extraction decomposition, truncation, schema violations,
speaker/evidence, negation, latency and concrete gold-vs-prediction examples.  Development-only (50 prompt-dev ids; labels are generator-derived).
usage: python -B -s analyse_p00_p01_subset.py"""
import collections
import json
import re
import statistics as st
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
TRACK = HERE.parents[3]
sys.path.insert(0, str(TRACK / "scripts"))
import common_1_7b as C  # noqa: E402

sys.path.insert(0, str(C.EXP6 / "s1"))
import evaluate_s1 as E  # noqa: E402  (frozen helpers + dataset guard)
from direct_inference_baseline.evaluation import evaluation_runner as ER, schema_validator as SV  # noqa: E402
from direct_inference_baseline.evaluation.entity_matching import CATEGORIES, match_category, entity_list, prf  # noqa: E402

E1, E2 = TRACK / "experiments" / "EXP_001_DIRECT_INFERENCE", TRACK / "experiments" / "EXP_002_PROMPTING_INFERENCE"
RUNS = {"P00": (E1, "P00_direct_dev50"), "P01": (E2, "P01_schema_guided_dev50")}
man = {k: json.loads((e / "evaluations" / r / "run_manifest.json").read_text(encoding="utf-8-sig"))["records"] for k, (e, r) in RUNS.items()}
IDS = [i for i in E.IDS if i in man["P01"]]
assert len(IDS) == 30, len(IDS)
tr_of = E.tr_of if hasattr(E, "tr_of") else None


def pred_of(k, i):
    e, r = RUNS[k]
    p = e / "outputs" / "parsed" / r / f"encounter_{i}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def raw_of(k, i):
    e, r = RUNS[k]
    return json.loads((e / "outputs" / "raw" / r / f"encounter_{i}.json").read_text(encoding="utf-8"))


spy = C.G.StrictAccessSpy(allow_validation=False)
out = {"scope": "development-only; 30 shared ids; generator-derived labels"}
with spy:
    gold = {i: ER.load_gold(i) for i in IDS}
    P = {k: {i: pred_of(k, i) for i in IDS} for k in RUNS}
    P = {k: {i: (v.get("parsed", v) if isinstance(v, dict) and "parsed" in v else v) for i, v in d.items()} for k, d in P.items()}
    status = {k: {i: man[k][i]["status"] for i in IDS} for k in RUNS}

    def micro(k, ids):
        t = collections.Counter()
        for i in ids:
            for cat in CATEGORIES:
                m = match_category(entity_list(gold[i], cat), entity_list(P[k][i] or {}, cat), cat)
                t["tp"] += m["tp"]; t["fp"] += m["fp"]; t["fn"] += m["fn"]
        return {**prf(t["tp"], t["fp"], t["fn"]), "tp": t["tp"], "fp": t["fp"], "fn": t["fn"]}

    both = [i for i in IDS if status["P00"][i] == "parsed" and status["P01"][i] == "parsed"]
    rec01 = [i for i in IDS if status["P00"][i] == "failed" and status["P01"][i] == "parsed"]
    lost01 = [i for i in IDS if status["P00"][i] == "parsed" and status["P01"][i] == "failed"]
    both_fail = [i for i in IDS if status["P00"][i] == "failed" and status["P01"][i] == "failed"]
    out["decomposition"] = {"ids_parsed_in_both": both, "ids_failed_P00_parsed_P01(recovered)": rec01, "ids_parsed_P00_failed_P01(lost)": lost01, "ids_failed_in_both": both_fail,
                            "micro_all30": {k: micro(k, IDS) for k in RUNS}, "micro_both_parsed(pure extraction, same records)": {k: micro(k, both) for k in RUNS},
                            "micro_recovered_records_only": {k: micro(k, rec01) for k in RUNS}, "micro_lost_records_only": {k: micro(k, lost01) for k in RUNS}}
    # F1 contribution accounting: TP gained on all30 split by group
    out["tp_gain_by_group"] = {g: micro("P01", ids)["tp"] - micro("P00", ids)["tp"] for g, ids in (("both_parsed", both), ("recovered", rec01), ("lost", lost01), ("both_failed", both_fail))}

    # truncation
    keys = ["chief_complaint", "symptoms", "negative_findings", "medical_history", "medications", "allergies", "vital_signs", "physical_examination", "review_of_systems", "clinical_conditions",
            "clinical_assessment", "procedures_and_investigations", "clinical_actions", "follow_up", "clinical_uncertainties", "clinical_evidence", "quality_checks"]
    trunc = {}
    for k in RUNS:
        rows = []
        for i in IDS:
            r = man[k][i]
            if r.get("finish_reason") == "length" or r["status"] == "failed":
                t = raw_of(k, i)["response_text"]
                present = [x for x in keys if f'"{x}"' in t]
                rows.append({"id": i, "finish_reason": r.get("finish_reason"), "completion_tokens": r.get("completion_tokens"), "status": r["status"], "failure_type": r.get("failure_type"),
                             "valid_json": r["status"] == "parsed", "last_section_started": present[-1] if present else None, "chars": len(t), "has_leading_whitespace_layout": ("\n  " in t)})
        trunc[k] = rows
    out["truncation"] = trunc
    out["layout"] = {k: {"mean_output_tokens_parsed": round(st.mean([man[k][i]["completion_tokens"] for i in IDS if status[k][i] == "parsed"]), 0),
                         "newline_indent_in_output_share": round(sum("\n  " in raw_of(k, i)["response_text"] for i in IDS) / 30, 2),
                         "evidence_chars_mean": round(st.mean([len(raw_of(k, i)["response_text"]) - raw_of(k, i)["response_text"].find('"clinical_evidence"') for i in IDS if '"clinical_evidence"' in raw_of(k, i)["response_text"]]), 0)} for k in RUNS}

    # schema violations
    def gen(msg):
        return re.sub(r"\[\d+\]", "[]", msg)
    sv = {}
    for k in RUNS:
        kinds, fields, roles, enums = collections.Counter(), collections.Counter(), collections.Counter(), collections.Counter()
        for i in IDS:
            if P[k][i] is None:
                continue
            for v in SV.validate(P[k][i]).violations:
                kinds[v["kind"]] += 1
                m = gen(v["message"])
                fields[(v["kind"], m.split("=")[0])] += 1
                if v["kind"] == "enum_violation":
                    enums[m] += 1
                    if re.search(r"person_\d|=''|=None", m):
                        roles[re.search(r"=(.*)$", m).group(1) if "=" in m else m] += 1
        sv[k] = {"by_kind": dict(kinds), "top_fields": [[f"{a}: {b}", n] for (a, b), n in fields.most_common(18)], "top_enum_violations": enums.most_common(12), "bad_role_values": roles.most_common(8),
                 "wrong_type": kinds.get("wrong_type", 0), "records_with_zero_violations": sum(1 for i in IDS if P[k][i] is not None and not SV.validate(P[k][i]).violations),
                 "parsed_records": sum(1 for i in IDS if P[k][i] is not None)}
        # missing 'confidence' vs other missing fields
        sv[k]["missing_confidence"] = sum(n for (a, b), n in fields.items() if a == "missing_field" and b.endswith(".confidence"))
        sv[k]["missing_non_confidence"] = sum(n for (a, b), n in fields.items() if a == "missing_field" and not b.endswith(".confidence"))
    out["schema"] = sv

    # per category counts P00/P01 + examples
    cat = {}
    ex = {}
    for k in RUNS:
        for c in CATEGORIES:
            t = collections.Counter()
            for i in IDS:
                m = match_category(entity_list(gold[i], c), entity_list(P[k][i] or {}, c), c)
                t["tp"] += m["tp"]; t["fp"] += m["fp"]; t["fn"] += m["fn"]
            cat.setdefault(c, {})[k] = {**prf(t["tp"], t["fp"], t["fn"]), "tp": t["tp"], "fp": t["fp"], "fn": t["fn"]}
    out["per_category"] = cat
    for c in CATEGORIES:
        hits, miss, fps = [], [], []
        for i in IDS:
            if P["P01"][i] is None:
                continue
            m = match_category(entity_list(gold[i], c), entity_list(P["P01"][i], c), c)
            hits += [(i, g) for g, _ in m["pairs"]]
            miss += [(i, k_) for k_, _ in m["fn_entities"]]
            fps += [(i, k_) for k_, _ in m["fp_entities"]]
        ex[c] = {"correct": [f"{i}: {KEYS_str}" for i, KEYS_str in [(i, str(g)[:0]) for i, g in hits[:0]]],
                 "n_correct": len(hits), "missed_gold_keys": [f"{i}: {k_}" for i, k_ in miss[:5]], "n_missed": len(miss), "spurious_pred_keys": [f"{i}: {k_}" for i, k_ in fps[:5]], "n_spurious": len(fps)}
        # matched keys (correct examples)
        corr = []
        for i in IDS:
            if P["P01"][i] is None:
                continue
            m = match_category(entity_list(gold[i], c), entity_list(P["P01"][i], c), c)
            from direct_inference_baseline.evaluation.entity_matching import KEYS
            corr += [f"{i}: {KEYS[c](g)}" for g, _ in m["pairs"]]
        ex[c]["correct_examples"] = corr[:4]
        ex[c].pop("correct")
    out["examples"] = ex

    # negatives: where do gold negative findings go in P01 predictions?
    from direct_inference_baseline.evaluation.entity_matching import KEYS, norm_text
    neg = collections.Counter()
    neg_ex = []
    for i in IDS:
        if P["P01"][i] is None:
            continue
        p = P["P01"][i]
        blob = {c: " ".join(norm_text(KEYS[c](e) or "") for e in entity_list(p, c)) for c in CATEGORIES}
        for g in entity_list(gold[i], "negative_findings"):
            kk = norm_text(KEYS["negative_findings"](g))
            neg["gold_negatives"] += 1
            words = [w for w in kk.split() if len(w) > 3]
            where = [c for c in CATEGORIES if words and all(w in blob[c] for w in words)]
            neg["found_anywhere"] += bool(where)
            neg["found_in_negative_findings(any text)"] += "negative_findings" in where
            for c in where:
                neg["found_in:" + c] += 1
            if len(neg_ex) < 6:
                neg_ex.append({"id": i, "gold": kk, "found_in": where})
    out["negation_where_gold_negatives_appear"] = {"counts": dict(neg), "examples": neg_ex}
    # pred negative_findings count vs gold
    out["negative_counts"] = {k: {"gold": sum(len(entity_list(gold[i], "negative_findings")) for i in IDS), "pred": sum(len(entity_list(P[k][i] or {}, "negative_findings")) for i in IDS)} for k in RUNS}

    # latency
    lat = {}
    for k in RUNS:
        e, r = RUNS[k]
        perf = json.loads((e / "logs" / f"performance_{r}.json").read_text(encoding="utf-8"))["per_call_in_order"]
        order = [i for i in E.IDS if i in man[k]]
        l = [man[k][i]["latency_seconds"] for i in IDS]
        calls = {i: c for i, c in zip(order, perf)}
        dec = [calls[i]["decode_tokens_per_second"] for i in IDS if i in calls]
        ov = [calls[i]["tokens_per_second_overall"] for i in IDS if i in calls]
        pk = [calls[i]["sampled_peak_system_used_mb"] for i in IDS if i in calls]
        lat[k] = {"mean_s": round(st.mean(l), 1), "median_s": round(st.median(l), 1), "total_inference_hours": round(sum(l) / 3600, 2), "decode_tok_s_mean": round(st.mean(dec), 2), "overall_tok_s_mean": round(st.mean(ov), 2),
                  "mean_output_tokens": round(st.mean(man[k][i]["completion_tokens"] for i in IDS), 0), "peak_sampled_system_used_mb_max": max(pk), "peak_process_rss_mb_max": max(calls[i]["sampled_peak_process_rss_mb"] for i in IDS if i in calls)}
    out["latency"] = lat
    # evidence & speaker from full evaluation METRICS
    M = json.loads((E2 / "evaluations" / "P01_schema_guided_dev50" / "subset30" / "METRICS.json").read_text(encoding="utf-8"))["systems"]
    out["evidence_speaker"] = {n: {"evidence_grounding": b.get("evidence_grounding"), "speaker_attribution": b.get("speaker_attribution"), "unsupported_claims": b.get("unsupported_claims"), "attributes_by_field": (b.get("attributes") or {}).get("by_field"),
                                   "clinical_errors": b.get("clinical_errors"), "negation_polarity": b.get("negation_polarity"), "vital": b.get("vital_signs")} for n, b in M.items() if n.startswith("1.7B")}

dst = E2 / "evaluations" / "P01_schema_guided_dev50" / "subset30" / "ANALYSIS.json"
dst.write_text(json.dumps(out, indent=1, default=str, ensure_ascii=False), encoding="utf-8")
print("written", dst)
