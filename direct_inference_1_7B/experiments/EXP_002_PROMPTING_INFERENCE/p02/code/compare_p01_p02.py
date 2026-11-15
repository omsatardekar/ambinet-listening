"""P01 vs P02 on the SAME records, same strict matcher, same metrics. Read-only on all outputs; writes derived/P01_vs_P02_COMPARISON.json, derived/P02_ANALYSIS.json, derived/P01_ANALYSIS_same_ids.json,
the backfilled P02 records (outputs/materialised/P02/) and reports/P02_VS_P01_METRICS.md.
usage: python -B -I compare_p01_p02.py [--ids-from-p02-completed]   (default: the 30 ids of manifests/P02_30_IDS.json; with the flag only the records P02 has finished, so a partial run is compared on equal ids)"""
import argparse
import json
import statistics as st
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyse_run import fuzzy_diagnostic, speaker_analysis, partial_examples, fp_examples      # noqa: E402
from backfill_evidence import backfill                                                          # noqa: E402
from p02_common import EXP, TRACK, categories, load_transcript                                  # noqa: E402
from p02_evaluate import evaluate, load_run                                                     # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--ids-from-p02-completed", action="store_true")
A = ap.parse_args()
ALL = json.loads((TRACK / "manifests" / "P02_30_IDS.json").read_text(encoding="utf-8"))["ids"]
O = EXP / "outputs"
D = lambda r: (O / "parsed" / r, O / "failed" / r, O / "raw" / r)
ids = [i for i in ALL if (O / "raw" / "P02" / f"encounter_{i}.json").exists()] if A.ids_from_p02_completed else ALL
RUNS = {"P01": ("P01_schema_guided_dev50", "performance_P01_schema_guided_dev50.json"), "P02": ("P02", "performance_P02.json")}


def memory(perf_file, n_ids):
    p = json.loads((EXP / "logs" / perf_file).read_text(encoding="utf-8"))["per_call_in_order"]
    g = lambda k: [c[k] for c in p if c.get(k) is not None]
    return {"calls_logged": len(p), "peak_process_rss_mb_max": max(g("sampled_peak_process_rss_mb")), "peak_working_set_mb_max": max(g("peak_working_set_mb_process_so_far")),
            "min_system_available_mb_lowest": min(g("sampled_min_system_available_mb")), "system_available_mb_before_each_call_min": min(g("system_available_mb_before")),
            "load_compile_seconds_mean": round(st.mean(g("load_compile_seconds")), 1), "prefill_tokens_per_second_median": st.median(g("prefill_tokens_per_second")),
            "decode_tokens_per_second_median": st.median(g("decode_tokens_per_second")), "input_tokens_median": st.median(g("input_tokens")), "output_tokens_median": st.median(g("output_tokens"))}


res = {"ids": ids, "n_records": len(ids), "runs": {}}
for name, (run, perf) in RUNS.items():
    recs = load_run(*D(run), ids)
    E = evaluate(recs, "full", label=name)
    out = {k: v for k, v in E.items() if k != "_scored"}
    out["speaker_attribution_on_matched_facts"] = speaker_analysis(recs)
    out["fuzzy_completeness_diagnostic_not_official"] = fuzzy_diagnostic(recs)
    out["partial_extraction_examples"] = partial_examples(recs)
    out["false_positive_examples"] = fp_examples(recs)
    out["failure_types"] = dict(Counter(r["failure"] for r in recs.values() if r["status"] == "failed"))
    out["records_missing"] = [i for i, r in recs.items() if r["status"] == "missing"]
    out["runtime_and_memory"] = memory(perf, len(ids)) if (EXP / "logs" / perf).exists() else None
    if name == "P02":
        # backend evidence backfill on the parsed P02 records (new files; the model's own parsed output is never altered)
        mdir = O / "materialised" / "P02"
        mdir.mkdir(parents=True, exist_ok=True)
        tot, kinds = Counter(), Counter()
        for i, r in recs.items():
            if r["status"] == "parsed":
                full, flags, stt = backfill(r["obj"], load_transcript(i))
                (mdir / f"encounter_{i}.json").write_text(json.dumps(full, indent=1, ensure_ascii=False), encoding="utf-8")
                tot.update({k: v for k, v in stt.items() if isinstance(v, int)})
                kinds.update(f["kind"] for f in flags)
        out["backend_backfill"] = {"counts": dict(tot), "flag_kinds": dict(kinds), "valid_ref_share": round(tot["refs_valid"] / tot["refs_total"], 4) if tot["refs_total"] else None}
    res["runs"][name] = out
    (EXP / "p02" / "derived" / ("P02_ANALYSIS.json" if name == "P02" else "P01_ANALYSIS_same_ids.json")).write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str), encoding="utf-8")

# ------------------------------------------------------------------ markdown (metrics laid out like the P01 reports: overall, per category, validity, tokens, time)
a, b = res["runs"]["P01"], res["runs"]["P02"]
f3 = lambda x: "-" if x is None else f"{x:.3f}"
d3 = lambda x, y: "-" if x is None or y is None else f"{y - x:+.3f}"
L = [f"# P02 vs P01 — same {len(ids)} records, strict matcher (development-only)\n", "F1 is precision/recall over matched facts, not accuracy. Failed records score zero predictions in the headline (tier 1).\n",
     "## Overall (tier 1: all records)\n", "| Metric | P01 | P02 | change |", "|---|---|---|---|"]
for k in ("precision", "recall", "f1"):
    x, y = a["entities_tier1_all_records_failed_as_zero"]["micro"][k], b["entities_tier1_all_records_failed_as_zero"]["micro"][k]
    L.append(f"| micro {k} | {f3(x)} | {f3(y)} | {d3(x, y)} |")
for k in ("tp", "fp", "fn"):
    x, y = a["entities_tier1_all_records_failed_as_zero"]["micro"][k], b["entities_tier1_all_records_failed_as_zero"]["micro"][k]
    L.append(f"| {k.upper()} | {x} | {y} | {y - x:+d} |")
for k in ("precision", "recall", "f1"):
    x, y = a["entities_tier1_all_records_failed_as_zero"]["macro"][k], b["entities_tier1_all_records_failed_as_zero"]["macro"][k]
    L.append(f"| macro {k} (categories) | {f3(x)} | {f3(y)} | {d3(x, y)} |")
L += ["", "## Parsed records only (tier 2, shown next to tier 1, never instead)\n", "| Metric | P01 | P02 |", "|---|---|---|"]
for k in ("precision", "recall", "f1"):
    L.append(f"| micro {k} | {f3(a['entities_tier2_parsed_records_only']['micro'][k])} ({a['entities_tier2_parsed_records_only']['records']} rec) | {f3(b['entities_tier2_parsed_records_only']['micro'][k])} ({b['entities_tier2_parsed_records_only']['records']} rec) |")
L += ["", "## Validity and size\n", "| | P01 | P02 |", "|---|---|---|"]
va, vb = a["validity"], b["validity"]
L += [f"| records / parsed / failed | {a['records']} / {va['parsed']} / {va['failed']} | {b['records']} / {vb['parsed']} / {vb['failed']} |", f"| truncated at 4,096 | {va['truncated_at_token_cap']} | {vb['truncated_at_token_cap']} |",
      f"| failure types | {a['failure_types']} | {b['failure_types']} |", f"| output tokens median / max | {a['output_tokens']['median']} / {a['output_tokens']['max']} | {b['output_tokens']['median']} / {b['output_tokens']['max']} |",
      f"| generation seconds median / max / total | {a['generation_time_seconds']['median']:.0f} / {a['generation_time_seconds']['max']:.0f} / {a['generation_time_seconds']['total']:.0f} | {b['generation_time_seconds']['median']:.0f} / {b['generation_time_seconds']['max']:.0f} / {b['generation_time_seconds']['total']:.0f} |"]
ma, mb = a["runtime_and_memory"], b["runtime_and_memory"]
if ma and mb:
    for k in ("input_tokens_median", "prefill_tokens_per_second_median", "decode_tokens_per_second_median", "peak_process_rss_mb_max", "min_system_available_mb_lowest"):
        L.append(f"| {k} | {ma[k]} | {mb[k]} |")
L += ["", "## Per category (tier 1)\n", "| Category | gold | P01 pred | P02 pred | P01 TP | P02 TP | P01 P / R / F1 | P02 P / R / F1 |", "|---|---|---|---|---|---|---|---|"]
for c in categories():
    x, y = a["entities_tier1_all_records_failed_as_zero"]["per_category"][c], b["entities_tier1_all_records_failed_as_zero"]["per_category"][c]
    L.append(f"| {c} | {x['gold']} | {x['pred']} | {y['pred']} | {x['tp']} | {y['tp']} | {f3(x['precision'])} / {f3(x['recall'])} / {f3(x['f1'])} | {f3(y['precision'])} / {f3(y['recall'])} / {f3(y['f1'])} |")
L += ["", "## Speaker attribution (on facts the matcher paired with a gold fact)\n", "| | P01 | P02 |", "|---|---|---|"]
sa, sb = a["speaker_attribution_on_matched_facts"]["total"], b["speaker_attribution_on_matched_facts"]["total"]
for k in ("pairs", "correct_role", "wrong_role", "not_a_role_value", "missing"):
    L.append(f"| {k} | {sa.get(k, 0)} | {sb.get(k, 0)} |")
L += ["", "## Evidence (separate from entity metrics)\n", f"- P01 (model-written evidence block): {a['evidence_reference_validity']}", f"- P02 raw model output (segment ids): {b['evidence_reference_validity']}",
      f"- P02 backend backfill: {b.get('backend_backfill')}", "", "## Additional completeness diagnostic (matcher's fuzzy mode; NOT the official metric)\n", "| Category | P01 fuzzy recall | P02 fuzzy recall | P01 pred/gold | P02 pred/gold |", "|---|---|---|---|---|"]
for c in categories():
    x, y = a["fuzzy_completeness_diagnostic_not_official"][c], b["fuzzy_completeness_diagnostic_not_official"][c]
    L.append(f"| {c} | {f3(x['fuzzy_recall'])} | {f3(y['fuzzy_recall'])} | {x['count_ratio_pred_over_gold']} | {y['count_ratio_pred_over_gold']} |")
(EXP / "reports" / "P02_VS_P01_METRICS.md").write_text("\n".join(L) + "\n", encoding="utf-8")
(EXP / "p02" / "derived" / "P01_vs_P02_COMPARISON.json").write_text(json.dumps({k: res[k] for k in ("ids", "n_records")}, indent=1), encoding="utf-8")
print("\n".join(L[:22]))
