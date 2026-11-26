"""Judge the fine-tuned model's outputs on the locked test set with the SAME judge, prompts and metrics as every earlier run, and
compare with the frozen-prompt baseline (EXP_008 H1) on the 30 encounters both were run on.

  python -m finetune_slm.evaluation.judge_eval.ft_judge judge  --outputs finetune_slm/runs/round1_step400/test_step400_outputs --run-id ft_step400_test --set exp008     # 30 encounters
  python -m finetune_slm.evaluation.judge_eval.ft_judge judge  --outputs finetune_slm/runs/round1_step400/test_step400_outputs --run-id ft_step400_test --set all         # all 973 (resumable)
  python -m finetune_slm.evaluation.judge_eval.ft_judge report --run-id ft_step400_test

Inputs: model output = <outputs>/<id>_3_model_full.json (the expanded full structure). A missing file (the model wrote invalid JSON) counts as
ZERO predictions, exactly as in earlier runs. Transcript and reference label come from finetune_slm/data/round1_synthetic/test/raw_inputs and raw_labels (verified
identical to the batch-1 files the earlier runs used). Results: finetune_slm/evaluation/judge_eval/results/JUDGE/<run-id>/<id>.json (same format as before).
Synthetic data only. The judge is gpt-5.4 in Foundry (see METHODOLOGY.md); every reply is cached.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .aggregate import bootstrap, encounter_row, metrics, per_field
from .client import Judge, JudgeError
from .flatten import flatten
from .judge_run import RESULTS, _ask
from .prompts import PRECISION_SYSTEM, PRECISION_VERDICTS, PROMPT_HASHES, RECALL_SYSTEM, RECALL_VERDICTS, precision_user, recall_user
from .registry import ROOT

V2 = ROOT / "finetune_slm/data/round1_synthetic"
OUTPUT = Path(__file__).resolve().parent / "output"
BASE_RUN = "q06_exp008_H1_main30"            # the frozen-prompt baseline (30 encounters, judged earlier)
KEYS = ("precision_lenient", "recall_lenient", "judge_f1_lenient", "judge_f1_strict", "hallucination_rate", "critical_rate")


def manifest() -> dict[str, dict]:
    return {r["encounter_id"]: r for r in csv.DictReader(open(V2 / "manifest.csv", encoding="utf-8"))}


def test_ids() -> list[str]:
    return sorted(str(i) for i in json.loads((V2 / "test" / "TEST_LOCK.json").read_text(encoding="utf-8"))["test_ids"])


def exp008_ids() -> list[str]:
    d = ROOT / "finetune_slm" / "evaluation" / "judge_eval" / "results" / "JUDGE" / BASE_RUN
    return sorted(p.stem for p in d.glob("*.json"))


def pick(which: str) -> list[str]:
    ids, m = test_ids(), manifest()
    if which == "exp008":
        return [i for i in exp008_ids() if i in set(ids)]
    if which == "testA":
        return [i for i in ids if m[i]["split"] == "test_benchmark"]
    if which == "testB":
        return [i for i in ids if m[i]["split"] == "test"]
    return ids


def judge_one(judge: Judge, outputs: Path, run_id: str, enc: str) -> dict:
    compact = json.loads((V2 / "test" / "raw_inputs" / f"encounter_{enc}.json").read_text(encoding="utf-8"))
    label = flatten(json.loads((V2 / "test" / "raw_labels" / f"encounter_{enc}.json").read_text(encoding="utf-8")))
    f = outputs / f"{enc}_3_model_full.json"
    predicted, present = [], False
    if f.exists() and f.stat().st_size > 0:                                 # an empty file = the model wrote invalid JSON (counts as no output)
        try:
            predicted, present = flatten(json.loads(f.read_text(encoding="utf-8"))), True
        except (ValueError, TypeError):
            predicted, present = [], False
    res = {"run_id": run_id, "encounter_id": enc, "judge": judge.describe(), "prompt_sha256": PROMPT_HASHES, "n_reference": len(label),
           "n_predicted": len(predicted), "reference_facts": label, "predicted_facts": predicted, "model_output_present": present}
    usage: dict[str, int] = {}
    if predicted:
        with ThreadPoolExecutor(max_workers=2) as passes:
            fp = passes.submit(_ask, judge, PRECISION_SYSTEM, precision_user(compact, predicted), [x["fid"] for x in predicted], PRECISION_VERDICTS, 6000 + 120 * len(predicted))
            fr = passes.submit(_ask, judge, RECALL_SYSTEM, recall_user(label, predicted), [x["fid"] for x in label], RECALL_VERDICTS, 6000 + 120 * len(label))
            (pv, u), (rv, u2) = fp.result(), fr.result()
        for d in (u, u2):
            for k, v in d.items():
                if isinstance(v, int):
                    usage[k] = usage.get(k, 0) + v
    else:
        pv = []
        rv = [{"fid": x["fid"], "verdict": "missing", "matched": [], "reason": "no facts were extracted"} for x in label]
    res.update(precision=pv, recall=rv, usage=usage)
    return res


def cmd_judge(a) -> int:
    judge = Judge("JUDGE")
    if not judge.configured():
        raise SystemExit("JUDGE is not configured in .env")
    outputs = (ROOT / a.outputs).resolve()
    out_dir = RESULTS / "JUDGE" / a.run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    ids = pick(a.set)
    if a.limit:
        ids = ids[: a.limit]
    todo = [e for e in ids if not (out_dir / f"{e}.json").exists()]
    print(f"{len(todo)} of {len(ids)} encounters to judge with {judge.describe()}", flush=True)
    fails = 0
    with ThreadPoolExecutor(max_workers=max(1, a.workers)) as pool:
        futs = {pool.submit(judge_one, judge, outputs, a.run_id, e): e for e in todo}
        for n, fu in enumerate(as_completed(futs), 1):
            e = futs[fu]
            try:
                (out_dir / f"{e}.json").write_text(json.dumps(fu.result(), ensure_ascii=False, indent=1), encoding="utf-8")
                print(f"[{n}/{len(todo)}] {e} ok", flush=True)
            except JudgeError as exc:
                fails += 1
                print(f"[{n}/{len(todo)}] {e} FAILED {exc.code}: {exc.message}", flush=True)
    return 1 if fails else 0


def rows_for(run: str, ids: list[str]) -> list[dict]:
    rows = []
    for e in ids:
        label = flatten(json.loads((V2 / "test" / "raw_labels" / f"encounter_{e}.json").read_text(encoding="utf-8")))
        p = RESULTS / "JUDGE" / run / f"{e}.json"
        res = json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
        if res is not None and not res.get("predicted_facts"):
            res = None                                                    # nothing usable: zero predictions
        rows.append(encounter_row(res, label))
    return rows


def fmt(m: dict, ci: dict | None = None) -> str:
    def f(k):
        v = m.get(k)
        s = "n/a" if v is None else f"{v:.3f}"
        if ci and ci.get(k) and ci[k][0] is not None:
            s += f" [{ci[k][0]:.3f}, {ci[k][1]:.3f}]"
        return s
    return f"| {m['n_encounters']} | {f('precision_lenient')} | {f('recall_lenient')} | {f('judge_f1_lenient')} | {f('judge_f1_strict')} | {f('hallucination_rate')} | {f('critical_rate')} |"


HEAD = "| encounters | precision | recall | judge-F1 (lenient) | judge-F1 (strict) | hallucination | critical |\n|---|---|---|---|---|---|---|\n"


def cmd_report(a) -> int:
    m = manifest()
    ids_all = [e for e in pick("all") if (RESULTS / "JUDGE" / a.run_id / f"{e}.json").exists() or a.include_missing]
    judged = {e for e in ids_all}
    e8 = [e for e in pick("exp008") if e in judged]
    lines = [f"# Fine-tuned model ({a.run_id}) vs frozen-prompt baseline: judge evaluation\n",
             "Same judge (gpt-5.4, Foundry), same frozen prompts, same metrics as `METHODOLOGY.md`. Judge-F1 is agreement under one judge model's reading of one rubric, not clinical accuracy. Synthetic data only; labels are not clinician reviewed.\n"]
    out = {"run_id": a.run_id}
    if e8:
        rb, rf = rows_for(BASE_RUN, e8), rows_for(a.run_id, e8)
        mb, mf = metrics(rb), metrics(rf)
        cb, cf = bootstrap(rb, KEYS), bootstrap(rf, KEYS)
        lines += [f"## 1. Like-for-like: the {len(e8)} encounters both models were run on (Test A, EXP_008 ids)\n", "| model | " + HEAD.split("\n")[0][1:], "|---|" + HEAD.split("\n")[1][1:],
                  "| frozen H1 prompt, base Qwen3-0.6B | " + fmt(mb, cb)[1:], "| fine-tuned, step 400, short prompt | " + fmt(mf, cf)[1:], ""]
        lines.append(f"Encounters where the model output was valid JSON: baseline {sum(r['parsed'] for r in rb)}/{len(rb)}, fine-tuned {sum(r['parsed'] for r in rf)}/{len(rf)}.\n")
        out["exp008_like_for_like"] = {"baseline": mb, "fine_tuned": mf, "baseline_ci": cb, "fine_tuned_ci": cf}
    groups = {"Test A (Batch 1 benchmark)": [e for e in ids_all if m[e]["split"] == "test_benchmark"], "Test B (curated)": [e for e in ids_all if m[e]["split"] == "test"]}
    lines += ["## 2. Fine-tuned model on the locked test set (no baseline exists for these encounters)\n", "| subset | " + HEAD.split("\n")[0][1:], "|---|" + HEAD.split("\n")[1][1:]]
    out["test"] = {}
    for name, ids in list(groups.items()) + [("All judged test encounters", ids_all)]:
        if ids:
            r = rows_for(a.run_id, ids); mm = metrics(r); cc = bootstrap(r, KEYS)
            lines.append(f"| {name} | " + fmt(mm, cc)[1:]); out["test"][name] = {"metrics": mm, "ci": cc, "valid_json": sum(x["parsed"] for x in r), "n": len(r)}
    lines.append("")
    by_batch: dict[str, list[str]] = {}
    for e in ids_all:
        if m[e]["split"] == "test":
            by_batch.setdefault(m[e]["source_batch"], []).append(e)
    if by_batch:
        lines += ["### Test B by source batch\n", "| batch | " + HEAD.split("\n")[0][1:], "|---|" + HEAD.split("\n")[1][1:]]
        for b, ids in sorted(by_batch.items()):
            lines.append(f"| {b} | " + fmt(metrics(rows_for(a.run_id, ids)))[1:])
        lines.append("")
    if ids_all:
        pf = per_field(rows_for(a.run_id, ids_all))
        lines += ["## 3. Per section (all judged test encounters, lenient)\n", "| section | reference facts | predicted facts | recall | precision |", "|---|---|---|---|---|"]
        for k, v in pf.items():
            lines.append(f"| {k} | {v['reference']} | {v['predicted']} | {v['recall_lenient']} | {v['precision_lenient']} |")
        lines.append("")
        out["per_field"] = pf
    nov = [e for e in pick("all") if not (RESULTS / "JUDGE" / a.run_id / f"{e}.json").exists()]
    lines.append(f"Encounters not yet judged: {len(nov)}. Encounters whose model output was invalid JSON are judged with zero predictions (all their reference facts count as missed).\n")
    OUTPUT.mkdir(exist_ok=True)
    (OUTPUT / f"ft_{a.run_id}.md").write_text("\n".join(lines), encoding="utf-8")
    (OUTPUT / f"ft_{a.run_id}.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("\n".join(lines))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    j = sub.add_parser("judge"); j.add_argument("--outputs", required=True); j.add_argument("--run-id", required=True)
    j.add_argument("--set", default="exp008", choices=["exp008", "testA", "testB", "all"]); j.add_argument("--workers", type=int, default=4); j.add_argument("--limit", type=int)
    r = sub.add_parser("report"); r.add_argument("--run-id", required=True); r.add_argument("--include-missing", action="store_true")
    a = ap.parse_args(argv)
    return cmd_judge(a) if a.cmd == "judge" else cmd_report(a)


if __name__ == "__main__":
    sys.exit(main())
