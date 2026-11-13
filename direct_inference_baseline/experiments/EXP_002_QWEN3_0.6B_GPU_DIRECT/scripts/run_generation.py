"""Phase 3: generic (non-clinical) ~64-token generation with openvino_genai.LLMPipeline on one device.
usage: run_generation.py <CPU|GPU> <label>
Uses a fixed generic prompt only. No dataset, labels, transcripts or the clinical extraction prompt."""
import json, sys, time, os
from pathlib import Path
import psutil
import openvino_genai as ovg

E = Path(__file__).resolve().parents[1]
MODEL = E / "models" / "Qwen3-0.6B-ov-fp16"
CACHE = E / "ov_cache"
dev, label = sys.argv[1], sys.argv[2]
CACHE.mkdir(exist_ok=True)
(E / "results").mkdir(exist_ok=True)

GENERIC_PROMPT = "List ten common fruits, one per line, each with a one-sentence description of its taste."
proc = psutil.Process()
rss0 = proc.memory_info().rss

t0 = time.perf_counter()
pipe = ovg.LLMPipeline(str(MODEL), dev, CACHE_DIR=str(CACHE))
load_s = time.perf_counter() - t0
rss_loaded = proc.memory_info().rss

tok = pipe.get_tokenizer()
prompt = tok.apply_chat_template([{"role": "user", "content": GENERIC_PROMPT}], add_generation_prompt=True, extra_context={"enable_thinking": False})
cfg = ovg.GenerationConfig()
cfg.max_new_tokens = 64
cfg.do_sample = False
cfg.apply_chat_template = False        # template already applied above (enable_thinking=False)

stamps = []


def streamer(sub):
    stamps.append(time.perf_counter())
    return ovg.StreamingStatus.RUNNING


t1 = time.perf_counter()
res = pipe.generate([prompt], cfg)
gen_s = time.perf_counter() - t1
pm = res.perf_metrics
n_gen = pm.get_num_generated_tokens()
n_in = pm.get_num_input_tokens()
peak = getattr(proc.memory_info(), "peak_wset", None)
text = res.texts[0]
out = {
    "label": label, "device": dev, "model_dir": "models/Qwen3-0.6B-ov-fp16", "openvino_genai": ovg.get_version() if hasattr(ovg, "get_version") else None,
    "generic_prompt": GENERIC_PROMPT, "rendered_prompt_with_chat_template": prompt,
    "settings": {"do_sample": False, "max_new_tokens": 64, "enable_thinking": False, "apply_chat_template_in_genai": False, "cache_dir": "ov_cache"},
    "load_compile_seconds": round(load_s, 3),
    "ttft_ms_genai": round(pm.get_ttft().mean, 1), 
    "generation_wall_seconds": round(gen_s, 3), "input_tokens": n_in, "generated_tokens": n_gen,
    "tokens_per_second_overall(generated/gen_wall)": round(n_gen / gen_s, 3),
    "decode_tokens_per_second_genai(after first token)": round(pm.get_throughput().mean, 3),
    "memory_mb": {"rss_before_load": round(rss0 / 2**20), "rss_after_load": round(rss_loaded / 2**20), "peak_working_set": round(peak / 2**20) if peak else None},
    "generated_text": text,
}
(E / "results" / f"gen_{label}.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps({k: v for k, v in out.items() if k not in ("rendered_prompt_with_chat_template",)}, indent=2, ensure_ascii=False))


