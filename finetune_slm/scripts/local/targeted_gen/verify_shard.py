"""Run natural_gen.verify_natural on a shard of the raw files (file index modulo K == R), looping until every file of the shard is verified.

  python -m finetune_slm.scripts.local.targeted_gen.verify_shard --shard 0 --of 3 --workers 8 --expect 470

Same checks and same files as verify_natural; only the work is split so several processes can run at once. Stops when the shard has no unverified file and at least
`--expect` raw files exist (generation finished).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "finetune_slm"))
from finetune_slm.evaluation.judge_eval.client import Judge  # noqa: E402
from finetune_slm.scripts.local.natural_gen import verify_natural as V  # noqa: E402


def unverified(files: list[Path]) -> list[Path]:
    out = []
    for f in files:
        try:
            if not json.loads(f.read_text(encoding="utf-8")).get("verify"):
                out.append(f)
        except Exception:                                                     # noqa: BLE001  (still being written)
            pass
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="finetune_slm/data/round4_targeted/raw")
    ap.add_argument("--shard", type=int, required=True)
    ap.add_argument("--of", type=int, required=True)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--expect", type=int, default=470)
    a = ap.parse_args()
    judge, writer = Judge("JUDGE"), Judge("JUDGE2")
    raw = ROOT / a.raw
    while True:
        files = sorted(raw.glob("*.json"))
        mine = [f for f in files if int(f.stem) % a.of == a.shard]
        todo = unverified(mine)
        if not todo:
            if len(files) >= a.expect:
                print("shard done", a.shard, flush=True)
                return 0
            time.sleep(30)
            continue
        with ThreadPoolExecutor(max_workers=a.workers) as ex:
            for f, r in zip(todo, ex.map(lambda f: V.verify_one(judge, writer, f), todo)):
                print(f.stem, r, flush=True)


if __name__ == "__main__":
    sys.exit(main())
