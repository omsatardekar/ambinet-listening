"""Long-context test (synthetic prompt). usage: run_longctx.py <CPU|GPU> <label> <cache_subdir>
One process; 2 timed generations of the identical prompt, EACH in a freshly constructed LLMPipeline (so no KV-cache/prefix reuse from the previous run:
a reused pipeline skips prefill for an identical prompt, which was observed and is documented in results/superseded_prefix_cache_artifact/).
Greedy, enable_thinking=False, max_new_tokens=128. The compiled-model cache (ov_cache/<cache_subdir>) is shared by both runs."""
import gc, json, sys, time
from pathlib import Path
import psutil
import openvino_genai as ovg

E = Path(__file__).resolve().parents[1]
MODEL = E / "models" / "Qwen3-0.6B-ov-fp16"
dev, label, sub = sys.argv[1], sys.argv[2], sys.argv[3]
CACHE = E / "ov_cache" / sub
CACHE.mkdir(parents=True, exist_ok=True)
MAXNEW = 128
P = json.loads((E / "results" / "longctx_prompt.json").read_text(encoding="utf-8"))
proc = psutil.Process()
rss0 = proc.memory_info().rss
runs = []
for i in (1, 2):
    t0 = time.perf_counter()
    pipe = ovg.LLMPipeline(str(MODEL), dev, CACHE_DIR=str(CACHE))
    load_s = time.perf_counter() - t0
    rss_loaded = proc.memory_info().rss
    tok = pipe.get_tokenizer()
    prompt = tok.apply_chat_template([{"role": "user", "content": P["user_message"]}], add_generation_prompt=True, extra_context={"enable_thinking": False})
    cfg = ovg.GenerationConfig()
    cfg.max_new_tokens = MAXNEW
    cfg.do_sample = False
    cfg.apply_chat_template = False
    t1 = time.perf_counter()
    res = pipe.generate([prompt], cfg)
    wall = time.perf_counter() - t1
    pm = res.perf_metrics
    n_out, n_in = pm.get_num_generated_tokens(), pm.get_num_input_tokens()
    ttft = pm.get_ttft().mean / 1000.0
    tpot = pm.get_tpot().mean / 1000.0
    mem = proc.memory_info()
    runs.append({"run": i, "pipeline_load_seconds": round(load_s, 3), "prompt_tokens": n_in, "output_tokens": n_out,
                 "ttft_s(prefill+first token)": round(ttft, 3), "tokenization_ms": round(pm.get_tokenization_duration().mean, 2),
                 "decode_tokens_per_second": round(1.0 / tpot, 3) if tpot else None, "ms_per_output_token_after_first": round(tpot * 1000, 1),
                 "total_generation_wall_s": round(wall, 3), "prefill_tokens_per_second": round(n_in / ttft, 1),
                 "rss_mb_after_load": round(rss_loaded / 2**20), "rss_mb_after_run": round(mem.rss / 2**20),
                 "peak_working_set_mb_so_far": round(getattr(mem, "peak_wset", 0) / 2**20), "generated_text": res.texts[0]})
    del pipe, res, pm, tok
    gc.collect()
out = {"label": label, "device": dev, "cache_dir": f"ov_cache/{sub}", "settings": {"do_sample": False, "enable_thinking": False, "max_new_tokens": MAXNEW},
       "prompt_sha256_user_message": P["user_message_sha256"], "rss_mb_before_first_load": round(rss0 / 2**20), "runs": runs}
(E / "results" / f"longctx_{label}.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
for r in runs:
    print(label, {k: v for k, v in r.items() if k != "generated_text"})
