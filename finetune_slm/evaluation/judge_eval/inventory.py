"""Step 1: inventory of every registered run. Reads only. Writes finetune_slm/evaluation/judge_eval/output/inventory.json and inventory.md.

    python -m finetune_slm.evaluation.judge_eval.inventory
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from .registry import INPUT_DIR, LABEL_DIR, ROOT, RUNS, VALIDATION_SPLIT_RUNS

OUT = Path(__file__).resolve().parent / "output"
ID = re.compile(r"(\d{5})")


def ids_in(rel: str | None) -> set[str]:
    if not rel or not (ROOT / rel).is_dir():
        return set()
    return {m.group(1) for f in (ROOT / rel).glob("*.json") if (m := ID.search(f.name))}


def usable(rel: str) -> set[str]:
    """Prediction files that are real JSON objects carrying an encounter_id (guards against empty or non-object files)."""
    good = set()
    for f in (ROOT / rel).glob("*.json"):
        m = ID.search(f.name)
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except ValueError:
            continue
        if m and isinstance(data, dict) and data.get("encounter_id") is not None:
            good.add(m.group(1))
    return good


def main() -> int:
    labels, inputs = ids_in_path(LABEL_DIR), ids_in_path(INPUT_DIR)
    rows, problems = [], []
    for run in RUNS:
        row = {"run_id": run.run_id, "model": run.model, "experiment": run.experiment, "prompt": run.prompt, "group": run.group, "note": run.note, "parsed_dir": run.parsed}
        if not (ROOT / run.parsed).is_dir():
            row["status"] = "MISSING_DIRECTORY"
            problems.append(f"{run.run_id}: parsed directory not found: {run.parsed}")
            rows.append(row)
            continue
        parsed, raw, failed = usable(run.parsed), ids_in(run.raw), ids_in(run.failed)
        attempted = raw or (parsed | failed)
        row.update(status="ok", attempted=len(attempted), parsed=len(parsed & attempted), failed_or_unparsed=len(attempted - parsed),
                   attempted_basis="raw_dir" if raw else "parsed+failed", attempted_ids=sorted(attempted), parsed_ids=sorted(parsed),
                   without_label=sorted(attempted - labels), without_input=sorted(attempted - inputs))
        if row["without_label"] or row["without_input"]:
            problems.append(f"{run.run_id}: encounters without label/input: {row['without_label'][:5]} {row['without_input'][:5]}")
        rows.append(row)
    ok_core = [r for r in rows if r["status"] == "ok" and r["group"] == "core"]
    dev = [r for r in ok_core if r["run_id"] not in VALIDATION_SPLIT_RUNS]
    common = sorted(set.intersection(*(set(r["attempted_ids"]) for r in dev))) if dev else []
    by_id = {r["run_id"]: set(r["attempted_ids"]) for r in ok_core}
    val_ids = sorted(by_id.get("q06_exp004_P05", set()) & by_id.get("q06_exp003_direct_dev100", set()))
    others_hit_val = {k: len(v & set(val_ids)) for k, v in by_id.items() if k not in VALIDATION_SPLIT_RUNS and k != "q06_exp003_direct_dev100"}
    summary = {"dataset": "finetune_slm/archive/dataset_v2_batch_001_corrected", "labels": len(labels), "inputs": len(inputs), "runs": len(rows),
               "prompt_dev_comparison_set": {"description": "encounters attempted by every core run except P05", "count": len(common), "ids": common},
               "validation_comparison_set": {"description": "P05 vs EXP_003 only", "count": len(val_ids), "ids": val_ids,
                                             "other_runs_overlap_with_it": others_hit_val},
               "problems": problems}
    OUT.mkdir(exist_ok=True)
    (OUT / "inventory.json").write_text(json.dumps({"summary": summary, "runs": rows}, indent=2), encoding="utf-8")
    lines = ["| run | model | prompt | group | attempted | parsed | failed/unparsed | note |", "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['run_id']} | {r['model']} | {r['prompt']} | {r['group']} | {r.get('attempted', '-')} | {r.get('parsed', '-')} | "
                     f"{r.get('failed_or_unparsed', '-')} | {r['note'] if r.get('status') == 'ok' else r['status']} |")
    text = "\n".join(lines) + (f"\n\nPrompt-dev comparison set (every core run except P05): {len(common)} encounters.\n"
                                       f"Validation comparison set (P05 vs EXP_003 only): {len(val_ids)} encounters; overlap with other runs: {others_hit_val}\n"
                                       f"Problems: {problems or 'none'}\n")
    (OUT / "inventory.md").write_text(text, encoding="utf-8")
    print(text)
    return 1 if problems else 0


def ids_in_path(path: Path) -> set[str]:
    return {m.group(1) for f in path.glob("*.json") if (m := ID.search(f.name))}


if __name__ == "__main__":
    raise SystemExit(main())
