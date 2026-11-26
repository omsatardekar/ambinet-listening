"""Run the two judge passes for (run, encounter) pairs and store one result file per pair (resumable: existing results are skipped).

    python -m finetune_slm.evaluation.judge_eval.judge_run --judge JUDGE --runs q17_P02 q06_exp004_P02 --limit 10
    python -m finetune_slm.evaluation.judge_eval.judge_run --judge JUDGE --runs all-core --ids-from prompt_dev_set
Results: finetune_slm/evaluation/judge_eval/results/<JUDGE>/<run_id>/<encounter>.json. Failed or unparsed encounters get no file here (the aggregation counts them as
zero predictions). Synthetic data only.
"""
from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from .client import Judge, JudgeError, parse_json_reply
from .flatten import flatten
from .prompts import (PRECISION_SYSTEM, PRECISION_VERDICTS, PROMPT_HASHES, RECALL_SYSTEM, RECALL_VERDICTS, precision_user, recall_user)
from .registry import INPUT_DIR, LABEL_DIR, ROOT, RUNS, Run

RESULTS = Path(__file__).resolve().parent / "results"
INVENTORY = Path(__file__).resolve().parent / "output" / "inventory.json"


def _validated(reply_text: str, fids: list[str], allowed: tuple[str, ...]) -> list[dict[str, Any]]:
    data = parse_json_reply(reply_text)
    items = data.get("verdicts") if isinstance(data, dict) else None
    if not isinstance(items, list):
        raise JudgeError("judge_bad_shape", "The judge reply has no 'verdicts' list.")
    by_fid = {i.get("fid"): i for i in items if isinstance(i, dict)}
    out = []
    for fid in fids:
        item = by_fid.get(fid)
        if item is None or item.get("verdict") not in allowed:
            raise JudgeError("judge_bad_shape", f"Missing or invalid verdict for {fid}.")
        out.append(item)
    return out


def _ask(judge: Judge, system: str, user: str, fids: list[str], allowed: tuple[str, ...], budget: int) -> tuple[list[dict], dict]:
    """One judge call with a single retry on a malformed reply (the retry bypasses the cache so a bad cached reply is not replayed)."""
    last: JudgeError | None = None
    usage_total: dict[str, int] = {}
    for attempt in range(2):
        reply = judge.call(system, user, max_output_tokens=budget, use_cache=(attempt == 0))
        for key, value in reply.usage.items():
            if isinstance(value, int):
                usage_total[key] = usage_total.get(key, 0) + value
        try:
            return _validated(reply.text, fids, allowed), usage_total
        except JudgeError as exc:
            last = exc
    raise last or JudgeError("judge_bad_shape", "unknown")


def judge_pair(judge: Judge, run: Run, encounter: str) -> dict[str, Any]:
    compact = json.loads((INPUT_DIR / f"encounter_{encounter}.json").read_text(encoding="utf-8"))
    label = flatten(json.loads((LABEL_DIR / f"encounter_{encounter}.json").read_text(encoding="utf-8")))
    predicted = flatten(json.loads((ROOT / run.parsed / f"encounter_{encounter}.json").read_text(encoding="utf-8")))
    result: dict[str, Any] = {"run_id": run.run_id, "encounter_id": encounter, "judge": judge.describe(), "prompt_sha256": PROMPT_HASHES,
                              "n_reference": len(label), "n_predicted": len(predicted), "reference_facts": label, "predicted_facts": predicted}
    usage: dict[str, int] = {}
    if predicted:
        with ThreadPoolExecutor(max_workers=2) as passes:                      # the two passes are independent: run them side by side
            fp = passes.submit(_ask, judge, PRECISION_SYSTEM, precision_user(compact, predicted), [f["fid"] for f in predicted], PRECISION_VERDICTS, 6000 + 120 * len(predicted))
            fr = passes.submit(_ask, judge, RECALL_SYSTEM, recall_user(label, predicted), [f["fid"] for f in label], RECALL_VERDICTS, 6000 + 120 * len(label))
            (pv, u), (rv, u2) = fp.result(), fr.result()
        for d in (u, u2):
            for k, v in d.items():
                usage[k] = usage.get(k, 0) + v
    else:                                                                      # nothing was extracted: no precision verdicts, everything is missing (no call needed)
        pv = []
        rv = [{"fid": f["fid"], "verdict": "missing", "matched": [], "reason": "no facts were extracted"} for f in label]
    result.update(precision=pv, recall=rv, usage=usage)
    return result


def pick_runs(names: list[str]) -> list[Run]:
    if names == ["all-core"]:
        return [r for r in RUNS if r.group == "core"]
    by_id = {r.run_id: r for r in RUNS}
    unknown = [n for n in names if n not in by_id]
    if unknown:
        raise SystemExit(f"unknown run ids: {unknown}")
    return [by_id[n] for n in names]


def pick_ids(run: Run, scope: str, limit: int | None, inventory: dict, every: int = 1) -> list[str]:
    """Encounters to judge for a run. 'prompt_dev_set' = the 30 shared by every core run except P05; 'validation_set' = the 50 of P05 (and EXP_003 on them);
    'own' = every parsed encounter of the run."""
    parsed = set({r["run_id"]: r["parsed_ids"] for r in inventory["runs"] if r["status"] == "ok"}[run.run_id])
    summary = inventory["summary"]
    if scope == "own":
        pool = parsed
    elif scope == "prompt_dev_set":
        pool = parsed & set(summary["prompt_dev_comparison_set"]["ids"])
    elif scope == "validation_set":
        pool = parsed & set(summary["validation_comparison_set"]["ids"])
    else:
        raise SystemExit("--scope must be prompt_dev_set, validation_set or own")
    ids = sorted(pool)[::max(1, every)]                                         # every=5 -> a deterministic 20% sample
    return ids[:limit] if limit else ids


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge", default="JUDGE", choices=["JUDGE", "JUDGE2"])
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--scope", default="prompt_dev_set")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--every", type=int, default=1, help="judge every Nth encounter (deterministic sample)")
    ap.add_argument("--ids", nargs="+", help="restrict to these encounter ids (intersected with the run's parsed encounters)")
    args = ap.parse_args(argv)
    if not INVENTORY.exists():
        raise SystemExit("run  python -m finetune_slm.evaluation.judge_eval.inventory  first")
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    judge = Judge(args.judge)
    if not judge.configured():
        raise SystemExit(f"{args.judge} is not configured in .env")
    jobs = []
    for run in pick_runs(args.runs):
        out_dir = RESULTS / args.judge / run.run_id
        out_dir.mkdir(parents=True, exist_ok=True)
        jobs += [(run, e, out_dir / f"{e}.json") for e in pick_ids(run, args.scope, args.limit, inventory, args.every) if (not args.ids or e in args.ids) and not (out_dir / f"{e}.json").exists()]
    print(f"{len(jobs)} pair(s) to judge with {judge.describe()}")
    failures = 0
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = {pool.submit(judge_pair, judge, run, enc): (run, enc, path) for run, enc, path in jobs}
        for done, future in enumerate(as_completed(futures), 1):
            run, enc, path = futures[future]
            try:
                path.write_text(json.dumps(future.result(), ensure_ascii=False, indent=1), encoding="utf-8")
                print(f"[{done}/{len(jobs)}] {run.run_id} {enc} ok")
            except JudgeError as exc:
                failures += 1
                print(f"[{done}/{len(jobs)}] {run.run_id} {enc} FAILED {exc.code}: {exc.message}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
