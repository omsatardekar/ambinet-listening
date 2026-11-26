"""Generate with a (LoRA) checkpoint and check the output: valid JSON, expands to the full structure, rough item-level agreement with the reference.

  python generate_check.py --adapter /data/finetune/runs/pilot/checkpoint_step2 --data /data/finetune/dataset_v2/data/validation.jsonl --n 3
  python generate_check.py --adapter none --n 3            # the untouched base model, for comparison
Only validation data is used here; the locked test file is touched once, at the very end, with the final scorer.
"""
import argparse, json, os, re, sys, time
import torch

p = argparse.ArgumentParser()
p.add_argument("--model", default="/data/finetune/model_qwen3_0.6b/base_model")
p.add_argument("--adapter", default="none")
p.add_argument("--data", default="/data/finetune/dataset_v2/data/validation.jsonl")
p.add_argument("--codec", default="/data/finetune/dataset_v2/codec")
p.add_argument("--n", type=int, default=3)
p.add_argument("--offset", type=int, default=0)
p.add_argument("--max_new_tokens", type=int, default=4096)
p.add_argument("--out", default="")
p.add_argument("--sort", action="store_true", help="sort the selected examples by length before batching (faster)")
p.add_argument("--split", default="", help="only examples with this split value, e.g. validation_unseen")
p.add_argument("--save", default="", help="folder: write transcript, raw model output, expanded full JSON and the correct label per example")
p.add_argument("--device", default="cuda")
p.add_argument("--batch", type=int, default=1, help="sequences generated together (faster for many examples)")
a = p.parse_args()
sys.path.insert(0, a.codec)
import compact_codec as CC
from transformers import AutoModelForCausalLM, AutoTokenizer

dev = torch.device(a.device)
tok = AutoTokenizer.from_pretrained(a.model)
IM_END = tok.convert_tokens_to_ids("<|im_end|>")
model = AutoModelForCausalLM.from_pretrained(a.model, dtype=torch.float16 if dev.type == "cuda" else torch.float32, attn_implementation="sdpa").to(dev)
if a.adapter != "none":
    from peft import PeftModel
    model = PeftModel.from_pretrained(model, a.adapter)
    model = model.merge_and_unload()                   # merged weights generate faster than an unmerged adapter
model.eval()
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
if a.sort: rows.sort(key=lambda r: len(r["messages"][0]["content"]) + len(r["messages"][1]["content"]))   # similar lengths together: less padding, faster batches
tok.padding_side = "left"
if tok.pad_token_id is None: tok.pad_token_id = IM_END
res = []
for b0 in range(0, len(rows), a.batch):
    chunk = rows[b0: b0 + a.batch]
    texts = [HEAD + r["messages"][0]["content"] + MID for r in chunk]
    enc = tok(texts, add_special_tokens=False, return_tensors="pt", padding=True).to(dev)
    t0 = time.time()
    with torch.no_grad():
        out = model.generate(**enc, max_new_tokens=a.max_new_tokens, do_sample=False, eos_token_id=IM_END, pad_token_id=tok.pad_token_id)
    secs = time.time() - t0
    for r, o, am in zip(chunk, out, enc["attention_mask"]):
        new = o[enc["input_ids"].shape[1]:]
        stop = (new == IM_END).nonzero()
        ended = len(stop) > 0
        if ended: new = new[: int(stop[0])]
        text = tok.decode(new, skip_special_tokens=True)
        ref = r["messages"][1]["content"]
        rec = {"id": r["id"], "prompt_tokens": int(am.sum()), "new_tokens": len(new), "batch_seconds": round(secs, 1), "ended_normally": bool(ended)}
        try:
            obj = json.loads(text); rec["valid_json"] = True
            warn = []; full = CC.expand(obj, warnings=warn); rec["expands"] = True; rec["unknown_keys"] = len(warn)
            refo = CC.expand(json.loads(ref)); a_, b_ = items(full), items(refo)
            tp = len(a_ & b_); pr = tp / len(a_) if a_ else 0; rc = tp / len(b_) if b_ else 0
            rec.update(items_pred=len(a_), items_ref=len(b_), precision=round(pr, 3), recall=round(rc, 3), f1=round(2 * pr * rc / (pr + rc), 3) if pr + rc else 0)
        except Exception as e:
            rec["valid_json"] = False; rec["error"] = str(e)[:120]; rec["tail"] = text[-200:]
        print(json.dumps(rec), flush=True); res.append(rec)
        if a.save:
            os.makedirs(a.save, exist_ok=True)
            open(os.path.join(a.save, r["id"] + "_1_transcript.txt"), "w", encoding="utf-8").write(r["messages"][0]["content"])
            open(os.path.join(a.save, r["id"] + "_2_model_raw.json"), "w", encoding="utf-8").write(text)
            try: open(os.path.join(a.save, r["id"] + "_3_model_full.json"), "w", encoding="utf-8").write(json.dumps(CC.expand(json.loads(text)), indent=1, ensure_ascii=False))
            except Exception: pass
            open(os.path.join(a.save, r["id"] + "_4_correct_label_full.json"), "w", encoding="utf-8").write(json.dumps(CC.expand(json.loads(ref)), indent=1, ensure_ascii=False))
ok = [x for x in res if x.get("valid_json")]
print(f"SUMMARY n={len(res)} valid_json={len(ok)} ended_normally={sum(x['ended_normally'] for x in res)} mean_f1={(sum(x.get('f1', 0) for x in ok) / len(ok)) if ok else 0:.3f} new_tokens_total={sum(x['new_tokens'] for x in res)}")
if a.out: open(a.out, "w", encoding="utf-8").write(chr(10).join(json.dumps(x) for x in res))
