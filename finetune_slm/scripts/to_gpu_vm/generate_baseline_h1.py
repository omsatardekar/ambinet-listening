"""Frozen-prompt BASELINE on the GPU VM: the untouched base Qwen3-0.6B with the frozen H1 hybrid prompt (EXP_008), on the same inputs as the
fine-tuned model, so before and after can be compared on the same encounters.

  python generate_baseline_h1.py --data /data/finetune/module3_recordings.jsonl --prompt /data/finetune/H1_hybrid_prompt.txt --save /data/finetune/runs/m3_baseline

Same settings as the original H1 run: greedy decoding, thinking off, max_new_tokens 6144, full-structure JSON written by the model itself.
Differences from the original run (state them in the report): PyTorch fp16 on an NVIDIA T4 instead of OpenVINO FP16 on an Intel GPU, and the
transcript lines carry no timestamps (identical text to what the fine-tuned model sees).
Output per encounter: <id>_2_model_raw.txt and, if the text parses as JSON, <id>_3_model_full.json.
"""
import argparse, json, os, re, time
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

p = argparse.ArgumentParser()
p.add_argument("--model", default="/data/finetune/model_qwen3_0.6b/base_model")
p.add_argument("--data", required=True)
p.add_argument("--prompt", required=True)
p.add_argument("--save", required=True)
p.add_argument("--n", type=int, default=0)
p.add_argument("--batch", type=int, default=4)
p.add_argument("--max_new_tokens", type=int, default=6144)
a = p.parse_args()

tok = AutoTokenizer.from_pretrained(a.model); tok.padding_side = "left"
IM_END = tok.convert_tokens_to_ids("<|im_end|>")
if tok.pad_token_id is None: tok.pad_token_id = IM_END
model = AutoModelForCausalLM.from_pretrained(a.model, dtype=torch.float16, attn_implementation="sdpa").to("cuda").eval()
template = open(a.prompt, encoding="utf-8").read()
HEAD = "<|im_start|>user\n"; MID = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
rows = [json.loads(l) for l in open(a.data, encoding="utf-8")]
if a.n: rows = rows[: a.n]
os.makedirs(a.save, exist_ok=True)

def transcript_of(user):
    m = re.search(r"Transcript \(encounter [^)]*\)\n(.*?)\n\nJSON:", user, re.S)
    return m.group(1)

def parse(text):
    try: return json.loads(text)
    except Exception: pass
    i, j = text.find("{"), text.rfind("}")
    if i >= 0 and j > i:
        try: return json.loads(text[i:j + 1])
        except Exception: return None
    return None

n_ok = 0
for b0 in range(0, len(rows), a.batch):
    chunk = rows[b0: b0 + a.batch]
    prompts = [HEAD + template.replace("{ENCOUNTER_ID}", r["id"]).replace("{TRANSCRIPT}", transcript_of(r["messages"][0]["content"])) + MID for r in chunk]
    enc = tok(prompts, add_special_tokens=False, return_tensors="pt", padding=True).to("cuda")
    t0 = time.time()
    with torch.no_grad():
        out = model.generate(**enc, max_new_tokens=a.max_new_tokens, do_sample=False, eos_token_id=IM_END, pad_token_id=tok.pad_token_id)
    for r, o in zip(chunk, out):
        new = o[enc["input_ids"].shape[1]:]; stop = (new == IM_END).nonzero(); ended = len(stop) > 0
        if ended: new = new[: int(stop[0])]
        text = tok.decode(new, skip_special_tokens=True)
        open(os.path.join(a.save, r["id"] + "_2_model_raw.txt"), "w", encoding="utf-8").write(text)
        obj = parse(text)
        if obj is not None:
            open(os.path.join(a.save, r["id"] + "_3_model_full.json"), "w", encoding="utf-8").write(json.dumps(obj, indent=1, ensure_ascii=False)); n_ok += 1
        print(json.dumps({"id": r["id"], "new_tokens": len(new), "ended_normally": bool(ended), "valid_json": obj is not None, "batch_seconds": round(time.time() - t0, 1)}), flush=True)
print(f"SUMMARY n={len(rows)} valid_json={n_ok}")
