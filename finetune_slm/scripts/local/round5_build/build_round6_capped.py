"""Round 6 (a short last try after round 5): the same cleaned data, but every counselling list in the NATURAL labels is capped at 4 items.

  python -m finetune_slm.scripts.local.round5_build.build_round6_capped

Why (docs/08_TRAINING_ROUND5.md, section 5.1): the unfinished outputs of round 5 end inside the counselling list of `clinical_actions`; natural labels have up to 13 counselling items,
round 1 at most 4. Advice such as "sleep well, eat well" is meant to be shown by the backend as a small separate section of at most 4 recommendations, not mixed into the plan
(tests, referrals, medicines, follow-up). Only `clinical_actions` items with action_type "counselling" are capped (the first 4 in the order written); nothing else is touched and
the schema is unchanged. Round-1 labels already have at most 4 and are not edited.
Training file: every natural example once (capped) + a random sample of round-1 examples. Validation: the round-5 validation file with the natural labels capped too.
"""
from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
CAP = 4


def cap_label(answer: str, cap: int) -> tuple[str, int]:
    label = json.loads(answer)
    acts = label.get("clinical_actions")
    if not isinstance(acts, list):
        return answer, 0
    kept, n, removed = [], 0, 0
    for a in acts:
        if isinstance(a, dict) and a.get("action_type") == "counselling":
            n += 1
            if n > cap:
                removed += 1
                continue
        kept.append(a)
    if removed:
        label["clinical_actions"] = kept
        return json.dumps(label, ensure_ascii=False, separators=(",", ":")), removed
    return answer, 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="finetune_slm/data/round5_clean_mix/run5")
    ap.add_argument("--out", default="finetune_slm/data/round6_capped_counselling/run6")
    ap.add_argument("--cap", type=int, default=CAP)
    ap.add_argument("--r1", type=int, default=600)
    ap.add_argument("--seed", type=int, default=20261129)
    a = ap.parse_args()
    src, out = ROOT / a.src, ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    stats = Counter()

    def fix(rows):
        res = []
        for r in rows:
            if r["source_batch"].endswith("_clean"):
                ans, rem = cap_label(r["messages"][1]["content"], a.cap)
                if rem:
                    r = {**r, "messages": [r["messages"][0], {"role": "assistant", "content": ans}]}
                    stats["examples capped"] += 1
                    stats["counselling items removed"] += rem
            res.append(r)
        return res

    train = [json.loads(l) for l in open(src / "train_run5.jsonl", encoding="utf-8")]
    nat = fix([r for r in train if r["source_batch"].endswith("_clean")])
    seen, nat_once = set(), []
    for r in nat:                                                  # the file holds each natural example twice; keep it once
        if r["id"] not in seen:
            seen.add(r["id"]); nat_once.append(r)
    r1 = [r for r in train if not r["source_batch"].endswith("_clean")]
    random.Random(a.seed).shuffle(r1)
    rows = nat_once + r1[: a.r1]
    random.Random(a.seed + 1).shuffle(rows)
    (out / "train_run6.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    val = fix([json.loads(l) for l in open(src / "validation_run5.jsonl", encoding="utf-8")])
    (out / "validation_run6.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in val) + "\n", encoding="utf-8")
    res = {"natural_unique": len(nat_once), "round1": min(a.r1, len(r1)), "train_total": len(rows), "validation_total": len(val), "cap": a.cap, **dict(stats)}
    (out / "build_stats.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
