import json, statistics as st
from pathlib import Path
E = Path(__file__).resolve().parents[1]
R = E / "results"
P = json.loads((R / "longctx_prompt.json").read_text(encoding="utf-8"))
exp = P["expected"]
L = lambda n: json.loads((R / f"longctx_{n}.json").read_text(encoding="utf-8"))
sets = {n: L(n) for n in ("gpu_longctx_coldcache", "gpu_longctx_warmcache", "cpu_longctx_coldcache", "cpu_longctx_warmcache")}
ref = json.loads((R / "longctx_hf_fp32_reference.json").read_text(encoding="utf-8"))
texts = {f"{n}/run{r['run']}": r["generated_text"] for n, d in sets.items() for r in d["runs"]}
texts["hf_fp32_reference"] = ref["generated_text"]


def score(t):
    got = [(e in t) for e in exp["first5"]]
    item_only = [e.split(": ", 1)[1].split(", ")[0] in t for e in exp["first5"]]
    return {"first5_exact_lines_correct": sum(got), "first5_item_names_present": sum(item_only), "last_item_mentioned": exp["last_item"] in t}


cmp = {"all_outputs_identical": len(set(texts.values())) == 1, "distinct_outputs": len(set(texts.values())),
       "identical_to_hf_fp32": {k: v == ref["generated_text"] for k, v in texts.items()}, "answer_scores": {k: score(v) for k, v in texts.items()}}
summ = {}
for n, d in sets.items():
    rs = d["runs"]
    summ[n] = {"device": d["device"], "runs": [{k: r[k] for k in ("run", "pipeline_load_seconds", "prompt_tokens", "output_tokens", "ttft_s(prefill+first token)", "prefill_tokens_per_second",
                                                                    "decode_tokens_per_second", "total_generation_wall_s", "peak_working_set_mb_so_far")} for r in rs],
               "mean_ttft_s": round(st.mean(r["ttft_s(prefill+first token)"] for r in rs), 2), "mean_decode_tps": round(st.mean(r["decode_tokens_per_second"] for r in rs), 2),
               "mean_total_s": round(st.mean(r["total_generation_wall_s"] for r in rs), 1)}
dev = {}
for d in ("GPU", "CPU"):
    rs = [r for n, v in sets.items() if v["device"] == d for r in v["runs"]]
    dev[d] = {"n_runs": len(rs), "ttft_s_min_mean_max": [min(r["ttft_s(prefill+first token)"] for r in rs), round(st.mean(r["ttft_s(prefill+first token)"] for r in rs), 1), max(r["ttft_s(prefill+first token)"] for r in rs)],
              "decode_tps_min_mean_max": [min(r["decode_tokens_per_second"] for r in rs), round(st.mean(r["decode_tokens_per_second"] for r in rs), 2), max(r["decode_tokens_per_second"] for r in rs)],
              "total_s_min_mean_max": [min(r["total_generation_wall_s"] for r in rs), round(st.mean(r["total_generation_wall_s"] for r in rs), 1), max(r["total_generation_wall_s"] for r in rs)],
              "peak_working_set_mb_max": max(r["peak_working_set_mb_so_far"] for r in rs)}
out = {"per_set": summ, "per_device_pooled(4 runs each)": dev, "output_comparison": cmp, "hf_fp32_reference": {k: ref[k] for k in ("prompt_tokens", "output_tokens", "total_seconds")},
       "sample_output": ref["generated_text"]}
(R / "longctx_analysis.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(out, indent=1, ensure_ascii=True))
