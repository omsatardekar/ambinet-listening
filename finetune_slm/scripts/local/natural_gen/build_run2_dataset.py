"""Assemble the round-2 training files from the verified natural encounters plus a replay sample of the round-1 training data.

  python -m finetune_slm.scripts.local.natural_gen.build_run2_dataset --raw finetune_slm/data/round2_natural/raw --out finetune_slm/data/round2_natural/run2 --replay 600

  train_run2.jsonl      accepted natural encounters of the training families + `--replay` random round-1 training examples (so the model does not forget the old distribution)
  validation_run2.jsonl the 250 round-1 validation examples + the accepted encounters of the HELD-OUT natural families (split `validation_natural`; these families are never trained on)
Same record format as finetune_slm/data/round1_synthetic (id, source_batch, split, scenario_group, messages[user, assistant]). The short prompt is used unchanged.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from finetune_slm.scripts.local.natural_gen.verify_natural import is_accepted  # noqa: E402
HELD_OUT_FAMILIES = {"heavy_periods_anaemia", "gout_flare", "memory_concerns_spouse", "asthma_flare_inhaler"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="finetune_slm/data/round2_natural/raw")
    ap.add_argument("--out", default="finetune_slm/data/round2_natural/run2")
    ap.add_argument("--replay", type=int, default=600)
    ap.add_argument("--strict", action="store_true", help="round 3: only labels with at most 1 unsupported fact and no critical omission")
    ap.add_argument("--seed", type=int, default=20261125)
    a = ap.parse_args()
    template = (ROOT / "finetune_slm/data/round1_synthetic/prompt/short_prompt.txt").read_text(encoding="utf-8")
    nat_train, nat_val, rejected = [], [], 0
    for f in sorted((ROOT / a.raw).glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        v = d.get("verify")
        if not v or not is_accepted(v, bool(v.get("revised"))) or (a.strict and (v["n_bad"] > 1 or any(o.get("critical") for o in v["omissions"]))):
            rejected += 1
            continue
        eid = d["spec"]["id"]
        user = template.replace("{ENCOUNTER_ID}", eid).replace("{TRANSCRIPT}", "\n".join(d["turns_text"]))
        held = d["spec"]["family"] in HELD_OUT_FAMILIES
        rec = {"id": eid, "source_batch": "natural_round2", "split": "validation_natural" if held else "train", "scenario_group": "nat_" + d["spec"]["family"],
               "messages": [{"role": "user", "content": user}, {"role": "assistant", "content": json.dumps(d["compact_label"], ensure_ascii=False, separators=(",", ":"))}]}
        (nat_val if held else nat_train).append(rec)
    train_r1 = [json.loads(l) for l in open(ROOT / "finetune_slm/data/round1_synthetic/data/train.jsonl", encoding="utf-8")]
    random.Random(a.seed).shuffle(train_r1)
    replay = train_r1[: a.replay]
    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    rows = nat_train + replay
    random.Random(a.seed + 1).shuffle(rows)
    (out / "train_run2.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    val = [json.loads(l) for l in open(ROOT / "finetune_slm/data/round1_synthetic/data/validation.jsonl", encoding="utf-8")] + nat_val
    (out / "validation_run2.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in val) + "\n", encoding="utf-8")
    print(f"natural train {len(nat_train)} (+ replay {len(replay)}) = {len(rows)} | validation {len(val)} (natural held-out {len(nat_val)}) | rejected/unverified {rejected}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
