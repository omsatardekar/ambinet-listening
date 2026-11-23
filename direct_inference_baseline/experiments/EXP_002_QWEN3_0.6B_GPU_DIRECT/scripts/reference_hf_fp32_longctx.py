"""Float32 transformers reference (EXP_001 numerics) on the SAME synthetic long prompt, greedy, max 128 new tokens. usage: <snapshot_dir>"""
import json, sys, time
from pathlib import Path
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

E = Path(__file__).resolve().parents[1]
S = sys.argv[1]
P = json.loads((E / "results" / "longctx_prompt.json").read_text(encoding="utf-8"))
tok = AutoTokenizer.from_pretrained(S)
model = AutoModelForCausalLM.from_pretrained(S, dtype=torch.float32).eval()
text = tok.apply_chat_template([{"role": "user", "content": P["user_message"]}], tokenize=False, add_generation_prompt=True, enable_thinking=False)
ids = tok(text, return_tensors="pt", add_special_tokens=False)
t = time.perf_counter()
with torch.no_grad():
    out = model.generate(**ids, max_new_tokens=128, do_sample=False, temperature=None, top_p=None, top_k=None)
dt = time.perf_counter() - t
new = out[0][ids["input_ids"].shape[1]:].tolist()
res = {"label": "hf_fp32_reference_longctx", "prompt_tokens": ids["input_ids"].shape[1], "output_tokens": len(new), "total_seconds": round(dt, 1),
       "generated_text": tok.decode(new, skip_special_tokens=True)}
(E / "results" / "longctx_hf_fp32_reference.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
print(res["prompt_tokens"], res["output_tokens"], res["total_seconds"])
