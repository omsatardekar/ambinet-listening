"""Turn judge verdicts into metrics (per run, with bootstrap 95% confidence intervals) and write finetune_slm/evaluation/judge_eval/output/metrics_<judge>_<scope>.json + .md

    python -m finetune_slm.evaluation.judge_eval.aggregate --judge JUDGE --scope prompt_dev_set
    python -m finetune_slm.evaluation.judge_eval.aggregate --judge JUDGE --scope prompt_dev_set --agreement JUDGE2

Definitions (fact level, micro-averaged over encounters; "judge-F1" is NOT clinical accuracy):
  precision  = credited predicted facts / predicted facts      (credit: supported = 1; partially_supported = 0.5 only in the "lenient" variant)
  recall     = credited reference facts / reference facts      (credit: found = 1; partially_found = 0.5 only in the "lenient" variant)
  hallucination rate = (unsupported + contradicted) / predicted facts
  critical rate      = predicted facts flagged critical / predicted facts ; also the share of encounters with at least one
Tier 1 counts failed/unparsed encounters as zero predictions (recall 0). Tier 2 shows parsed encounters only, next to tier 1, never instead of it.
"""
from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any

from .flatten import flatten
from .registry import LABEL_DIR, RUNS

HERE = Path(__file__).resolve().parent
RESULTS, OUT = HERE / "results", HERE / "output"
BOOTSTRAP, SEED = 2000, 20261117


def _scope_ids(inventory: dict, scope: str) -> set[str]:
    s = inventory["summary"]
    if scope == "own":
        return set(e for r in inventory["runs"] if r["status"] == "ok" for e in r["attempted_ids"])
    return {"prompt_dev_set": set(s["prompt_dev_comparison_set"]["ids"]), "validation_set": set(s["validation_comparison_set"]["ids"])}.get(scope, set())


def encounter_row(result: dict | None, label_facts: list[dict]) -> dict[str, Any]:
    """Counts for one encounter; `result` None means the run produced nothing usable for it."""
    row = {"ref": len(label_facts), "pred": 0, "sup": 0, "part": 0, "bad": 0, "crit": 0, "found": 0, "pfound": 0, "parsed": result is not None, "fields": {}}
    for f in label_facts:
        row["fields"].setdefault(f["field"], Counter())["ref"] += 1
    if result is None:
        return row
    pf = {f["fid"]: f["field"] for f in result["predicted_facts"]}
    rf = {f["fid"]: f["field"] for f in result["reference_facts"]}
    row["pred"] = len(result["predicted_facts"])
    for v in result["precision"]:
        c = row["fields"].setdefault(pf[v["fid"]], Counter())
        c["pred"] += 1
        if v["verdict"] == "supported":
            row["sup"] += 1; c["sup"] += 1
        elif v["verdict"] == "partially_supported":
            row["part"] += 1; c["part"] += 1
        else:
            row["bad"] += 1; c["bad"] += 1
        if v.get("critical"):
            row["crit"] += 1
    for v in result["recall"]:
        c = row["fields"].setdefault(rf[v["fid"]], Counter())
        if v["verdict"] == "found":
            row["found"] += 1; c["found"] += 1
        elif v["verdict"] == "partially_found":
            row["pfound"] += 1; c["pfound"] += 1
    return row


def metrics(rows: list[dict]) -> dict[str, float | None]:
    S = lambda k: sum(r[k] for r in rows)                                        # noqa: E731
    pred, ref = S("pred"), S("ref")
    div = lambda a, b: (a / b) if b else None                                    # noqa: E731
    out: dict[str, float | None] = {"n_encounters": len(rows), "reference_facts": ref, "predicted_facts": pred}
    for tag, w in (("strict", 0.0), ("lenient", 0.5)):
        p, r = div(S("sup") + w * S("part"), pred), div(S("found") + w * S("pfound"), ref)
        out[f"precision_{tag}"], out[f"recall_{tag}"] = p, r
        out[f"judge_f1_{tag}"] = (2 * p * r / (p + r)) if p and r else (0.0 if p is not None and r is not None else None)
    out["hallucination_rate"] = div(S("bad"), pred)
    out["critical_rate"] = div(S("crit"), pred)
    out["encounters_with_critical"] = div(sum(1 for r in rows if r["crit"] > 0), len([r for r in rows if r["parsed"]])) if any(r["parsed"] for r in rows) else None
    return out


def bootstrap(rows: list[dict], keys: tuple[str, ...]) -> dict[str, list[float | None]]:
    rng = random.Random(SEED)
    samples: dict[str, list[float]] = {k: [] for k in keys}
    for _ in range(BOOTSTRAP):
        m = metrics([rows[rng.randrange(len(rows))] for _ in rows])
        for k in keys:
            if m[k] is not None:
                samples[k].append(m[k])
    ci = {}
    for k, vals in samples.items():
        vals.sort()
        ci[k] = [vals[int(0.025 * len(vals))], vals[min(len(vals) - 1, int(0.975 * len(vals)))]] if vals else [None, None]
    return ci


def per_field(rows: list[dict]) -> dict[str, dict]:
    total: dict[str, Counter] = {}
    for r in rows:
        for field, c in r["fields"].items():
            total.setdefault(field, Counter()).update(c)
    div = lambda a, b: round(a / b, 3) if b else None                            # noqa: E731
    return {f: {"reference": c["ref"], "predicted": c["pred"], "recall_lenient": div(c["found"] + 0.5 * c["pfound"], c["ref"]),
                "precision_lenient": div(c["sup"] + 0.5 * c["part"], c["pred"])} for f, c in sorted(total.items())}


def kappa(pairs: list[tuple[str, str]]) -> tuple[float | None, float | None]:
    if not pairs:
        return None, None
    n = len(pairs)
    observed = sum(a == b for a, b in pairs) / n
    ca, cb = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    expected = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return observed, ((observed - expected) / (1 - expected) if expected < 1 else None)


def agreement(first: str, second: str) -> dict[str, Any]:
    """Verdict-level agreement between two judges on the encounters both have judged. Facts are matched by (run, encounter, fid)."""
    prec, rec, pairs_seen = [], [], 0
    for path in sorted((RESULTS / first).glob("*/*.json")):
        other = RESULTS / second / path.parent.name / path.name
        if not other.exists():
            continue
        a, b = json.loads(path.read_text(encoding="utf-8")), json.loads(other.read_text(encoding="utf-8"))
        pairs_seen += 1
        bp = {v["fid"]: v["verdict"] for v in b["precision"]}
        br = {v["fid"]: v["verdict"] for v in b["recall"]}
        prec += [(v["verdict"], bp[v["fid"]]) for v in a["precision"] if v["fid"] in bp]
        rec += [(v["verdict"], br[v["fid"]]) for v in a["recall"] if v["fid"] in br]
    po, pk = kappa(prec)
    ro, rk = kappa(rec)
    return {"first": first, "second": second, "encounter_pairs": pairs_seen, "precision_verdicts": len(prec), "precision_agreement": po, "precision_kappa": pk,
            "recall_verdicts": len(rec), "recall_agreement": ro, "recall_kappa": rk}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge", default="JUDGE")
    ap.add_argument("--scope", default="prompt_dev_set", choices=["prompt_dev_set", "validation_set", "own"])
    ap.add_argument("--agreement", help="second judge to compare against (e.g. JUDGE2)")
    ap.add_argument("--ids", nargs="+", help="score only these encounter ids (e.g. the 3 prompt-selection ids); the report name gets a _custom suffix")
    args = ap.parse_args(argv)
    inventory = json.loads((OUT / "inventory.json").read_text(encoding="utf-8"))
    scope = _scope_ids(inventory, args.scope)
    if args.ids:
        scope = set(args.ids)
        args.scope = args.scope + "_custom"
    inv = {r["run_id"]: r for r in inventory["runs"] if r["status"] == "ok"}
    labels = {e: flatten(json.loads((LABEL_DIR / f"encounter_{e}.json").read_text(encoding="utf-8"))) for e in scope}
    report: dict[str, Any] = {"judge": args.judge, "scope": args.scope, "scope_encounters": len(scope), "runs": {}}
    for run in RUNS:
        folder = RESULTS / args.judge / run.run_id
        if run.run_id not in inv or not folder.exists():
            continue
        attempted = set(inv[run.run_id]["attempted_ids"]) & scope        # scope "own" = every attempted encounter of the run
        rows = []
        parsed_ids = set(inv[run.run_id]["parsed_ids"])
        for e in sorted(attempted):
            file = folder / f"{e}.json"
            if file.exists():
                rows.append(encounter_row(json.loads(file.read_text(encoding="utf-8")), labels[e]))
            elif e not in parsed_ids:                                            # failed / unparsed: zero predictions (tier 1). Parsed-but-not-yet-judged are skipped, never counted as failures.
                rows.append(encounter_row(None, labels[e]))
        judged = sum(r["parsed"] for r in rows)
        parsed_available = len(set(inv[run.run_id]["parsed_ids"]) & attempted)
        if not rows or judged == 0:
            continue
        keys = ("precision_lenient", "recall_lenient", "judge_f1_lenient", "precision_strict", "recall_strict", "judge_f1_strict", "hallucination_rate")
        tier1, tier2 = metrics(rows), metrics([r for r in rows if r["parsed"]])
        report["runs"][run.run_id] = {"model": run.model, "prompt": run.prompt, "attempted_in_scope": len(attempted), "parsed_in_scope": parsed_available,
                                      "judged": judged, "complete": judged == parsed_available, "tier1_all_attempted": tier1, "tier1_ci95": bootstrap(rows, keys),
                                      "tier2_parsed_only": tier2, "per_field": per_field(rows)}
    if args.agreement:
        report["agreement"] = agreement(args.judge, args.agreement)
    OUT.mkdir(exist_ok=True)
    stem = f"metrics_{args.judge}_{args.scope}"
    (OUT / f"{stem}.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    fmt = lambda x: "-" if x is None else f"{x:.3f}"                             # noqa: E731
    lines = [f"Judge {args.judge}, scope {args.scope} ({len(scope)} encounters). Judge-F1 is agreement under one judge model's reading of one rubric, not clinical accuracy.", "",
             "| run | att | judged | complete | precision (len) | recall (len) | judge-F1 (len) [95% CI] | judge-F1 strict | halluc. | critical/fact | parsed-only F1 (len) |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for rid, r in report["runs"].items():
        t, ci, t2 = r["tier1_all_attempted"], r["tier1_ci95"]["judge_f1_lenient"], r["tier2_parsed_only"]
        lines.append(f"| {rid} | {r['attempted_in_scope']} | {r['judged']} | {'yes' if r['complete'] else 'NO'} | {fmt(t['precision_lenient'])} | {fmt(t['recall_lenient'])} | "
                     f"{fmt(t['judge_f1_lenient'])} [{fmt(ci[0])}, {fmt(ci[1])}] | {fmt(t['judge_f1_strict'])} | {fmt(t['hallucination_rate'])} | {fmt(t['critical_rate'])} | {fmt(t2['judge_f1_lenient'])} |")
    if args.agreement:
        a = report["agreement"]
        lines += ["", f"Agreement {a['first']} vs {a['second']}: {a['encounter_pairs']} encounter pairs; precision verdicts {a['precision_verdicts']} agree {fmt(a['precision_agreement'])} kappa {fmt(a['precision_kappa'])}; "
                      f"recall verdicts {a['recall_verdicts']} agree {fmt(a['recall_agreement'])} kappa {fmt(a['recall_kappa'])}"]
    (OUT / f"{stem}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
