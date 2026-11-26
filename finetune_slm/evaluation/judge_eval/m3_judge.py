"""Judge the fine-tuned model on the 20 hand-written Module 3 scenarios (no label file exists for them).

  python -m finetune_slm.evaluation.judge_eval.m3_judge --outputs finetune_slm/runs/round1_step400/m3_outputs --run-id m3_ft_step400

Two checks with the SAME judge and frozen prompts as the rest of the evaluation:
  precision pass : is each fact the model wrote supported by the transcript?  -> hallucination and critical-error rates, no label needed
  recall pass    : the reference facts are the `design` block of each scenario.json (what was put in on purpose: `facts`, plus the
                   `partial_or_uncertain` items, which should show up as a recorded doubt). Is each one conveyed by the model output?
The design block is a short human summary, not an exhaustive label, so recall here is a floor-style check; precision (invented or wrong
facts) is the more telling number. Input is the clean dialogue text, not an ASR transcript. Synthetic data only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .aggregate import encounter_row, metrics
from .client import Judge
from .flatten import flatten
from .judge_run import RESULTS, _ask
from .prompts import PRECISION_SYSTEM, PRECISION_VERDICTS, PROMPT_HASHES, RECALL_SYSTEM, RECALL_VERDICTS, precision_user, recall_user
from .registry import ROOT

OUT = Path(__file__).resolve().parent / "output"
LINE = re.compile(r"^\[(SEG\d{4})\] (person_\d+) \(([A-Z_]+)\): (.*)$")


def segments(user: str) -> list[dict]:
    return [{"segment_id": m.group(1), "speaker_id": m.group(2), "role": m.group(3), "text": m.group(4)} for l in user.splitlines() if (m := LINE.match(l))]


def design_facts(design: dict) -> list[dict]:
    facts = []
    for i, t in enumerate(design.get("facts", []), 1):
        facts.append({"fid": f"D{i}", "field": "design_fact", "text": t, "attributes": {}})
    for i, t in enumerate(design.get("partial_or_uncertain", []), 1):
        facts.append({"fid": f"U{i}", "field": "design_uncertainty", "text": "The record should show this doubt or gap, not a confident fact: " + t, "attributes": {}})
    return facts


def judge_one(judge: Judge, rec: dict, outputs: Path, run_id: str) -> dict:
    eid = rec["id"]
    compact = {"segments": segments(rec["messages"][0]["content"])}
    sc = json.loads((ROOT / "scenarios" / f"encounter_{eid}" / "scenario.json").read_text(encoding="utf-8"))
    ref = design_facts(sc["design"])
    f = outputs / f"{eid}_3_model_full.json"
    predicted = flatten(json.loads(f.read_text(encoding="utf-8"))) if f.exists() and f.stat().st_size else []
    res = {"run_id": run_id, "encounter_id": eid, "title": sc.get("title"), "prompt_sha256": PROMPT_HASHES, "n_segments": len(compact["segments"]),
           "reference_facts": ref, "predicted_facts": predicted}
    if predicted:
        with ThreadPoolExecutor(max_workers=2) as ex:
            fp = ex.submit(_ask, judge, PRECISION_SYSTEM, precision_user(compact, predicted), [x["fid"] for x in predicted], PRECISION_VERDICTS, 6000 + 120 * len(predicted))
            fr = ex.submit(_ask, judge, RECALL_SYSTEM, recall_user(ref, predicted), [x["fid"] for x in ref], RECALL_VERDICTS, 6000 + 120 * len(ref))
            (res["precision"], _), (res["recall"], _) = fp.result(), fr.result()
    else:
        res["precision"], res["recall"] = [], [{"fid": x["fid"], "verdict": "missing", "matched": [], "reason": "no output"} for x in ref]
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outputs", required=True); ap.add_argument("--run-id", required=True)
    ap.add_argument("--data", default="finetune_slm/data/module3_eval_inputs/module3_recordings.jsonl"); ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    judge = Judge("JUDGE")
    recs = [json.loads(l) for l in open(ROOT / a.data, encoding="utf-8")]
    outputs, d = (ROOT / a.outputs), RESULTS / "JUDGE" / a.run_id
    d.mkdir(parents=True, exist_ok=True)
    todo = [r for r in recs if not (d / f"{r['id']}.json").exists()]
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for r, res in zip(todo, ex.map(lambda r: judge_one(judge, r, outputs, a.run_id), todo)):
            (d / f"{r['id']}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8"); print("judged", r["id"], flush=True)
    rows, lines = [], []
    bad_lines, miss_lines = [], []
    per = []
    for r in recs:
        res = json.loads((d / f"{r['id']}.json").read_text(encoding="utf-8"))
        row = encounter_row(res, [x for x in res["reference_facts"]]); rows.append(row)
        pm = {x["fid"]: x for x in res["predicted_facts"]}
        for v in res["precision"]:
            if v["verdict"] != "supported":
                bad_lines.append(f"- {r['id']} [{v['verdict']}{', CRITICAL' if v.get('critical') else ''}] {pm[v['fid']]['field']}: {pm[v['fid']]['text']} — {v.get('reason', '')}")
        rm = {x["fid"]: x for x in res["reference_facts"]}
        for v in res["recall"]:
            if v["verdict"] != "found":
                miss_lines.append(f"- {r['id']} [{v['verdict']}] {rm[v['fid']]['text']} — {v.get('reason', '')}")
        m = metrics([row]); per.append((r["id"], row["pred"], m["precision_lenient"], m["recall_lenient"], m["hallucination_rate"], m["critical_rate"]))
    M = metrics(rows)
    fmt = lambda v: "n/a" if v is None else f"{v:.3f}"   # noqa: E731
    lines += ["# Realism check: fine-tuned step 400 on the 20 hand-written Module 3 scenarios\n",
              "Clean dialogue text as input (no ASR errors), trained line format. No label file: recall is against the scenario `design` block (floor-style), precision is against the transcript. Same judge and frozen prompts as the test-set evaluation. Synthetic data only.\n",
              "| encounters | precision | recall vs design | hallucination | critical |", "|---|---|---|---|---|",
              f"| {M['n_encounters']} | {fmt(M['precision_lenient'])} | {fmt(M['recall_lenient'])} | {fmt(M['hallucination_rate'])} | {fmt(M['critical_rate'])} |\n",
              "## Per encounter\n", "| encounter | predicted facts | precision | recall vs design | hallucination | critical |", "|---|---|---|---|---|---|"]
    lines += [f"| {i} | {p} | {fmt(a_)} | {fmt(b)} | {fmt(c)} | {fmt(e)} |" for i, p, a_, b, c, e in per]
    lines += [f"\n## Facts the judge did not find supported by the transcript ({len(bad_lines)})\n"] + bad_lines
    lines += [f"\n## Design facts or doubts the output did not convey fully ({len(miss_lines)})\n"] + miss_lines
    OUT.mkdir(exist_ok=True)
    (OUT / f"{a.run_id}.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[:24]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
