"""Merge a LoRA checkpoint into the base model and save a normal Hugging Face model folder (fp16).

  python merge_adapter.py --adapter /data/finetune/runs/run1/checkpoint_step400 --out /data/finetune/merged_step400

The result has the same architecture and file layout as the base model (config.json, model.safetensors, tokenizer files), so the
existing OpenVINO conversion step can be used on it unchanged.
"""
import argparse, os, shutil
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

p = argparse.ArgumentParser()
p.add_argument("--model", default="/data/finetune/model_qwen3_0.6b/base_model")
p.add_argument("--adapter", required=True)
p.add_argument("--out", required=True)
a = p.parse_args()

tok = AutoTokenizer.from_pretrained(a.model)
m = AutoModelForCausalLM.from_pretrained(a.model, dtype=torch.float32)           # merge in fp32, then store fp16
m = PeftModel.from_pretrained(m, a.adapter).merge_and_unload()
m = m.to(torch.float16)
os.makedirs(a.out, exist_ok=True)
m.save_pretrained(a.out, safe_serialization=True)
tok.save_pretrained(a.out)
for f in ("generation_config.json", "merges.txt", "vocab.json"):                   # keep the base files byte-identical where possible
    src = os.path.join(a.model, f)
    if os.path.exists(src): shutil.copy2(src, os.path.join(a.out, f))
print("saved", a.out, sorted(os.listdir(a.out)))
