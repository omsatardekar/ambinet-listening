"""LoRA fine-tuning of Qwen3-0.6B for clinical extraction (plain PyTorch + transformers + peft; no TRL, so no trainer-API drift).

Prompt/loss layout (identical to inference with thinking off):
  <|im_start|>user\n{short prompt + transcript}<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n  <- masked (no loss)
  {compact JSON}<|im_end|>                                                                                <- loss

Examples (pilot, 2 optimizer steps, then full run):
  python train_lora.py --out /data/finetune/runs/pilot --max_steps 2
  python train_lora.py --out /data/finetune/runs/run1 --epochs 3
Resume after an interruption: add --resume to the same command.
"""
import argparse, json, math, os, random, time
import torch

p = argparse.ArgumentParser()
p.add_argument("--model", default="/data/finetune/model_qwen3_0.6b/base_model")
p.add_argument("--train", default="/data/finetune/dataset_v2/data/train_oversampled.jsonl")
p.add_argument("--val", default="/data/finetune/dataset_v2/data/validation.jsonl")
p.add_argument("--out", required=True)
p.add_argument("--max_len", type=int, default=6656)
p.add_argument("--epochs", type=float, default=3)
p.add_argument("--max_steps", type=int, default=0, help="stop after this many optimizer steps (pilot)")
p.add_argument("--grad_accum", type=int, default=16)
p.add_argument("--lr", type=float, default=1e-4)
p.add_argument("--warmup", type=float, default=0.03)
p.add_argument("--rank", type=int, default=64)
p.add_argument("--alpha", type=int, default=128)
p.add_argument("--dropout", type=float, default=0.05)
p.add_argument("--eval_every", type=int, default=100, help="optimizer steps between validations")
p.add_argument("--eval_n", type=int, default=60, help="validation examples per evaluation")
p.add_argument("--save_every", type=int, default=100)
p.add_argument("--seed", type=int, default=20261127)
p.add_argument("--device", default="cuda")
p.add_argument("--no_amp", action="store_true", help="disable fp16 autocast (CPU smoke test)")
p.add_argument("--no_ckpt", action="store_true", help="disable gradient checkpointing (CPU smoke test)")
p.add_argument("--base_dtype", default="fp32", choices=["fp32", "fp16"], help="dtype of the frozen base weights (fp16 = less memory traffic; LoRA weights stay fp32)")
p.add_argument("--resume", action="store_true")
p.add_argument("--init_adapter", default="", help="continue training from this LoRA checkpoint (round 2); optimizer and schedule start fresh")
p.add_argument("--limit_train", type=int, default=0, help="use only the first N training examples (smoke test)")
a = p.parse_args()

from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model, PeftModel

os.makedirs(a.out, exist_ok=True)
random.seed(a.seed); torch.manual_seed(a.seed)
LOG = open(os.path.join(a.out, "train_log.txt"), "a", encoding="utf-8")
def log(*x):
    s = " ".join(str(i) for i in x); print(s, flush=True); LOG.write(s + "\n"); LOG.flush()

tok = AutoTokenizer.from_pretrained(a.model)
IM_END = tok.convert_tokens_to_ids("<|im_end|>")
HEAD = "<|im_start|>user\n"; MID = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"

def encode(rec):
    user, ans = rec["messages"][0]["content"], rec["messages"][1]["content"]
    pi = tok(HEAD + user + MID, add_special_tokens=False)["input_ids"]
    ai = tok(ans, add_special_tokens=False)["input_ids"] + [IM_END]
    return pi, ai

def load(path, limit=0):
    out = []
    for line in open(path, encoding="utf-8"):
        r = json.loads(line); pi, ai = encode(r)
        if len(pi) + len(ai) > a.max_len:
            log("SKIP too long", r["id"], len(pi) + len(ai)); continue
        out.append((r["id"], r.get("split", ""), pi, ai))
        if limit and len(out) >= limit: break
    return out

train = load(a.train, a.limit_train); val = load(a.val)
rng = random.Random(a.seed)
vs = [v for v in val if v[1] == "validation_seen"]; vu = [v for v in val if v[1] == "validation_unseen"]
n_each = max(1, a.eval_n // 2)
vn = [v for v in val if v[1] == "validation_natural"]
val_fixed = rng.sample(vs, min(n_each, len(vs))) + rng.sample(vu, min(n_each, len(vu))) + vn
log(f"train examples {len(train)} | validation examples {len(val)} (evaluating {len(val_fixed)}) | answer tokens median {sorted(len(t[3]) for t in train)[len(train)//2]}")

dev = torch.device(a.device)
model = AutoModelForCausalLM.from_pretrained(a.model, dtype=torch.float16 if a.base_dtype == "fp16" else torch.float32, attn_implementation="sdpa")
model.to(dev)
if not a.no_ckpt:
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    model.enable_input_require_grads()
model.config.use_cache = False
cfg = LoraConfig(r=a.rank, lora_alpha=a.alpha, lora_dropout=a.dropout, bias="none", task_type="CAUSAL_LM",
                 target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"])
model = PeftModel.from_pretrained(model, a.init_adapter, is_trainable=True) if a.init_adapter else get_peft_model(model, cfg)
trainable = [q for q in model.parameters() if q.requires_grad]
for q in trainable: q.data = q.data.float()          # LoRA weights always in fp32
log("trainable parameters", sum(q.numel() for q in trainable))

def example_loss(pi, ai):
    ids = torch.tensor([pi + ai], device=dev)
    n = len(ai)
    out = model(input_ids=ids, logits_to_keep=n + 1)            # logits only for the last n+1 positions (saves ~4 GB)
    logits = out.logits[0, :-1].float()                          # position t predicts token t+1: the n answer tokens
    target = torch.tensor(ai, device=dev)
    return torch.nn.functional.cross_entropy(logits, target), n

amp = (not a.no_amp) and dev.type == "cuda"
scaler = torch.amp.GradScaler("cuda", enabled=amp)
opt = torch.optim.AdamW(trainable, lr=a.lr, weight_decay=0.0, betas=(0.9, 0.999))
steps_per_epoch = math.ceil(len(train) / a.grad_accum)
total_steps = a.max_steps or int(steps_per_epoch * a.epochs)
warm = max(1, int(total_steps * a.warmup))
def lr_at(s):
    if s < warm: return a.lr * (s + 1) / warm
    return a.lr * (0.1 + 0.9 * 0.5 * (1 + math.cos(math.pi * (s - warm) / max(1, total_steps - warm))))

step, start_example = 0, 0
state_path = os.path.join(a.out, "state.pt")
if a.resume and os.path.exists(state_path):
    st = torch.load(state_path, map_location=dev)
    model.load_state_dict(st["lora"], strict=False); opt.load_state_dict(st["opt"]); scaler.load_state_dict(st["scaler"])
    step, start_example = st["step"], st["example"]; log("RESUMED at step", step)

order = []
ep = 0
while len(order) < total_steps * a.grad_accum + 1:
    idx = list(range(len(train))); random.Random(a.seed + ep).shuffle(idx); order += idx; ep += 1

def evaluate():
    model.eval(); res = {"validation_seen": [0.0, 0], "validation_unseen": [0.0, 0], "validation_natural": [0.0, 0]}
    with torch.no_grad():
        for _id, sp, pi, ai in val_fixed:
            with torch.autocast("cuda", dtype=torch.float16, enabled=amp):
                loss, n = example_loss(pi, ai)
            res[sp][0] += float(loss) * n; res[sp][1] += n
    model.train()
    return {k: (v[0] / v[1] if v[1] else float("nan")) for k, v in res.items()}

def save(tag):
    d = os.path.join(a.out, tag); model.save_pretrained(d)
    torch.save({"lora": {k: v for k, v in model.state_dict().items() if "lora_" in k}, "opt": opt.state_dict(), "scaler": scaler.state_dict(), "step": step, "example": start_example}, state_path)
    log("saved", d)

model.train(); t0 = time.time(); tok_count = 0; skipped = 0
log(f"start: total optimizer steps {total_steps} (accum {a.grad_accum}), warm-up {warm}, lr {a.lr}, amp {amp}")
while step < total_steps:
    batch_ids = order[start_example: start_example + a.grad_accum]; start_example += a.grad_accum
    lsum, ntok_batch = 0.0, 0
    for i in batch_ids:
        _id, _sp, pi, ai = train[i]
        with torch.autocast("cuda", dtype=torch.float16, enabled=amp):
            loss, n = example_loss(pi, ai)
        if not torch.isfinite(loss):
            skipped += 1; log("non-finite loss, example skipped:", _id); continue
        scaler.scale(loss / len(batch_ids)).backward()
        lsum += float(loss) * n; ntok_batch += n; tok_count += len(pi) + len(ai)
    scaler.unscale_(opt); gn = torch.nn.utils.clip_grad_norm_(trainable, 1.0)
    for g in opt.param_groups: g["lr"] = lr_at(step)
    scaler.step(opt); scaler.update(); opt.zero_grad(set_to_none=True); step += 1
    el = time.time() - t0
    mem = torch.cuda.max_memory_allocated() / 2**30 if dev.type == "cuda" else 0
    log(f"step {step}/{total_steps} loss {lsum / max(1, ntok_batch):.4f} grad_norm {float(gn):.2f} lr {lr_at(step - 1):.2e} | {tok_count / el:.0f} tok/s | peak GPU {mem:.1f} GiB | elapsed {el / 60:.1f} min | skipped {skipped}")
    if step % a.eval_every == 0 or step == total_steps:
        r = evaluate(); log(f"VALIDATION step {step}: seen {r['validation_seen']:.4f} | unseen {r['validation_unseen']:.4f} | natural {r['validation_natural']:.4f}")
    if step % a.save_every == 0 or step == total_steps:
        save(f"checkpoint_step{step}")
log("finished", f"{(time.time() - t0) / 60:.1f} min")
