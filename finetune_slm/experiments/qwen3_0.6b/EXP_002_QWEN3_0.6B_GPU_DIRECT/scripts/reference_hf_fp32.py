"""Reference: the SAME exact snapshot in float32 via transformers (same as EXP_001 numerics), same generic prompt, greedy, 64 tokens.
Used only to judge whether OpenVINO FP16 (CPU/GPU) output is faithful. usage: reference_hf_fp32.py <snapshot_dir>"""
import json, sys, time
from pathlib import Path
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

E = Path(__file__).resolve().parents[1]
S = sys.argv[1]
P = "List ten common fruits, one per line, each with a one-sentence description of its taste."
tok = AutoTokenizer.from_pretrained(S)
model = AutoModelForCausalLM.from_pretrained(S, dtype=torch.float32).eval()
text = tok.apply_chat_template([{"role": "user", "content": P}], tokenize=False, add_generation_prompt=True, enable_thinking=False)
ids = tok(text, return_tensors="pt", add_special_tokens=False)
t = time.perf_counter()
with torch.no_grad():
    out = model.generate(**ids, max_new_tokens=64, do_sample=False, temperature=None, top_p=None, top_k=None)
dt = time.perf_counter() - t
new = out[0][ids["input_ids"].shape[1]:].tolist()
res = {"label": "hf_fp32_reference", "input_tokens": ids["input_ids"].shape[1], "generated_tokens": len(new), "seconds": round(dt, 2),
       "token_ids": new, "generated_text": tok.decode(new, skip_special_tokens=True), "rendered_prompt": text}
(E / "results" / "gen_hf_fp32_reference.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps({k: v for k, v in res.items() if k != "token_ids"}, indent=2, ensure_ascii=False))
