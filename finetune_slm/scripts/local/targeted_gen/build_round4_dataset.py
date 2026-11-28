"""Assemble the round-4 training files from the verified targeted encounters plus a replay sample of round-1 training data.

  python -m finetune_slm.scripts.local.targeted_gen.build_round4_dataset --raw finetune_slm/data/round4_targeted/raw --out finetune_slm/data/round4_targeted/run4 --replay 500

An encounter is used only when ALL hold: the model verifier accepted it (verify_natural.is_accepted), the automatic checks passed (validate_labels), and the example fits the length limit
(--max-chars of prompt + answer, default 16000 characters, about 5,000 tokens: round 2's very long examples were where the repetition loops came from).
  train_run4.jsonl       accepted encounters of the training families + `--replay` random round-1 training examples
  validation_run4.jsonl  the 250 round-1 validation examples + accepted encounters of the HELD-OUT families (never trained on)
Same record format as round 2 (id, source_batch, split, scenario_group, messages[user, assistant]); the short prompt is unchanged.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "finetune_slm"))
from finetune_slm.scripts.local.natural_gen.verify_natural import is_accepted  # noqa: E402

HELD_OUT_FAMILIES = {"sinusitis_after_cold", "kidney_stone_colic", "restless_legs_pregnancy", "bell_palsy_new", "hay_fever_season", "tennis_elbow_painter", "inguinal_hernia_lump"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="finetune_slm/data/round4_targeted/raw")
    ap.add_argument("--out", default="finetune_slm/data/round4_targeted/run4")
    ap.add_argument("--replay", type=int, default=500)
    ap.add_argument("--max-chars", type=int, default=16000)
    ap.add_argument("--seed", type=int, default=20261126)
    a = ap.parse_args()
    template = (ROOT / "finetune_slm/data/round1_synthetic/prompt/short_prompt.txt").read_text(encoding="utf-8")
    train, val, why = [], [], Counter()
    traps = Counter()
    for f in sorted((ROOT / a.raw).glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        v, auto = d.get("verify"), d.get("auto_checks")
        if not v:
            why["not verified"] += 1
            continue
        if not is_accepted(v, bool(v.get("revised"))):
            why["verifier rejected"] += 1
            continue
        if not auto or not auto["ok"]:
            why["automatic checks failed" if auto else "automatic checks not run"] += 1
            continue
        eid = d["spec"]["id"]
        user = template.replace("{ENCOUNTER_ID}", eid).replace("{TRANSCRIPT}", "\n".join(d["turns_text"]))
        answer = json.dumps(d["compact_label"], ensure_ascii=False, separators=(",", ":"))
        if len(user) + len(answer) > a.max_chars:
            why["too long"] += 1
            continue
        held = d["spec"]["family"] in HELD_OUT_FAMILIES
        rec = {"id": eid, "source_batch": "targeted_round4", "split": "validation_natural" if held else "train", "scenario_group": "tgt_" + d["spec"]["family"],
               "messages": [{"role": "user", "content": user}, {"role": "assistant", "content": answer}]}
        (val if held else train).append(rec)
        for t in d["spec"]["traps"]:
            traps[t["key"]] += 1
    r1 = [json.loads(l) for l in open(ROOT / "finetune_slm/data/round1_synthetic/data/train.jsonl", encoding="utf-8")]
    random.Random(a.seed).shuffle(r1)
    replay = r1[: a.replay]
    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    rows = train + replay
    random.Random(a.seed + 1).shuffle(rows)
    (out / "train_run4.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    val_rows = [json.loads(l) for l in open(ROOT / "finetune_slm/data/round1_synthetic/data/validation.jsonl", encoding="utf-8")] + val
    (out / "validation_run4.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in val_rows) + "\n", encoding="utf-8")
    print(f"targeted train {len(train)} (+ replay {len(replay)}) = {len(rows)} | validation {len(val_rows)} (targeted held-out {len(val)})")
    print("excluded:", dict(why)); print("traps in the training part:", dict(traps))
    return 0


if __name__ == "__main__":
    sys.exit(main())
