"""Fast batch generation with vLLM (paged attention, continuous batching) + the same checks as generate_check.py.

Run it inside the SEPARATE vLLM environment (/data/finetune/venv_vllm), not the training venv.

  python generate_vllm.py --adapter runs/run1/checkpoint_step400 --split validation_unseen --n 60 --out runs/vllm_unseen_step400.jsonl
  python generate_vllm.py --adapter none --split validation_unseen --n 60         # untouched base model with the short prompt

Same record format as generate_check.py: valid_json, expands, item-level precision/recall/F1 against the reference.
Only validation data by default; the locked test file is used once, at the very end.
"""
import argparse, json, os, re, sys, time

p = argparse.ArgumentParser()
p.add_argument("--model", default="/data/finetune/model_qwen3_0.6b/base_model")
p.add_argument("--adapter", default="none")
p.add_argument("--data", default="/data/finetune/dataset_v2/data/validation.jsonl")
p.add_argument("--codec", default="/data/finetune/dataset_v2/codec")
p.add_argument("--split", default="")
p.add_argument("--n", type=int, default=60)
p.add_argument("--offset", type=int, default=0)
p.add_argument("--max_new_tokens", type=int, default=4096)
p.add_argument("--max_model_len", type=int, default=10240)
p.add_argument("--gpu_mem", type=float, default=0.88)
p.add_argument("--out", default="")
p.add_argument("--save", default="", help="folder: write transcript, raw output, expanded full JSON and the correct label per example")
a = p.parse_args()
sys.path.insert(0, a.codec)
import compact_codec as CC
from vllm import LLM, SamplingParams
from vllm.lora.request import LoRARequest

HEAD = "<|im_start|>user\n"; MID = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
KEYS = ("name", "finding", "condition", "substance", "procedure", "assessment", "description", "value", "time_reference", "system", "relation", "details", "type")

def items(obj):
    out = set()
    for sec, v in obj.items():
        if sec in ("encounter_id", "extraction_status", "encounter_metadata", "clinical_evidence", "quality_checks"): continue
        subs = [(sec, v)] if isinstance(v, (list, dict)) else []
        if sec == "medical_history" and isinstance(v, dict): subs = [(f"{sec}.{k}", x) for k, x in v.items()]
        for s, x in subs:
            for it in (x if isinstance(x, list) else [x]):
                if isinstance(it, dict):
                    t = next((str(it[k]).lower().strip() for k in KEYS if it.get(k)), "")
                    if t: out.add((s, re.sub(r"\W+", " ", t).strip()))
    return out

rows = [json.loads(l) for l in open(a.data, encoding="utf-8")]
if a.split: rows = [r for r in rows if r.get("split") == a.split]
rows = rows[a.offset: a.offset + a.n]

use_lora = a.adapter != "none"
llm = LLM(model=a.model, dtype="half", max_model_len=a.max_model_len, gpu_memory_utilization=a.gpu_mem,
          enable_lora=use_lora, max_lora_rank=64, enable_prefix_caching=True, seed=0)
sp = SamplingParams(temperature=0.0, max_tokens=a.max_new_tokens, stop_token_ids=[llm.get_tokenizer().convert_tokens_to_ids("<|im_end|>")], skip_special_tokens=True)
lora = LoRARequest("ckpt", 1, os.path.abspath(a.adapter)) if use_lora else None
prompts = [HEAD + r["messages"][0]["content"] + MID for r in rows]
t0 = time.time()
outs = llm.generate(prompts, sp, lora_request=lora)
secs = time.time() - t0

res = []
for r, o in zip(rows, outs):
    c = o.outputs[0]; text = c.text; ref = r["messages"][1]["content"]
    rec = {"id": r["id"], "prompt_tokens": len(o.prompt_token_ids), "new_tokens": len(c.token_ids), "ended_normally": c.finish_reason == "stop"}
    try:
        obj = json.loads(text); rec["valid_json"] = True
        warn = []; full = CC.expand(obj, warnings=warn); rec["expands"] = True; rec["unknown_keys"] = len(warn)
        refo = CC.expand(json.loads(ref)); a_, b_ = items(full), items(refo)
        tp = len(a_ & b_); pr = tp / len(a_) if a_ else 0; rc = tp / len(b_) if b_ else 0
        rec.update(items_pred=len(a_), items_ref=len(b_), precision=round(pr, 3), recall=round(rc, 3), f1=round(2 * pr * rc / (pr + rc), 3) if pr + rc else 0)
    except Exception as e:
        rec["valid_json"] = False; rec["error"] = str(e)[:120]; rec["tail"] = text[-200:]
    res.append(rec)
    if a.save:
        os.makedirs(a.save, exist_ok=True)
        open(os.path.join(a.save, r["id"] + "_1_transcript.txt"), "w", encoding="utf-8").write(r["messages"][0]["content"])
        open(os.path.join(a.save, r["id"] + "_2_model_raw.json"), "w", encoding="utf-8").write(text)
        try: open(os.path.join(a.save, r["id"] + "_3_model_full.json"), "w", encoding="utf-8").write(json.dumps(CC.expand(json.loads(text)), indent=1, ensure_ascii=False))
        except Exception: pass
        open(os.path.join(a.save, r["id"] + "_4_correct_label_full.json"), "w", encoding="utf-8").write(json.dumps(CC.expand(json.loads(ref)), indent=1, ensure_ascii=False))
ok = [x for x in res if x.get("valid_json")]
if a.out: open(a.out, "w", encoding="utf-8").write(chr(10).join(json.dumps(x) for x in res))
print(f"SUMMARY n={len(res)} valid_json={len(ok)} ended_normally={sum(x['ended_normally'] for x in res)} mean_f1={(sum(x.get('f1', 0) for x in ok) / len(ok)) if ok else 0:.3f} new_tokens_total={sum(x['new_tokens'] for x in res)} seconds={secs:.0f} tok_per_s={sum(x['new_tokens'] for x in res) / secs:.0f}")
