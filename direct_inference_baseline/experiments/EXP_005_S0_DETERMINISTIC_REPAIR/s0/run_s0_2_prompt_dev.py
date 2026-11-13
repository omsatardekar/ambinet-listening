"""Run S0.2 on the S0.1-repaired prompt_dev copies (data/repaired/<source>) -> data/repaired_s0_2/<source>. prompt_dev ids only (StrictAccessSpy). Originals/S0.1 copies are only read.
Reports schema violations before (original) / after S0.1 / after S0.2 by kind, category and field, preservation of every existing value, idempotency, and the unchanged strict evaluator scores.
usage: python -B -s run_s0_2_prompt_dev.py   (from EXP_005)"""
import collections
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
EXP5 = HERE.parent
EXP4 = EXP5.parent / "EXP_004_QWEN3_0.6B_PROMPT_ENGINEERING"
sys.path.insert(0, str(EXP4 / "experiments"))
sys.path.insert(0, str(HERE))
from common import S, SPLIT  # noqa: E402
import dev_guard as G  # noqa: E402
import s0_repair as R1  # noqa: E402
import s0_2_fill_nullable as F  # noqa: E402
from direct_inference_baseline.evaluation import evaluation_runner as ER  # noqa: E402
from direct_inference_baseline.evaluation import schema_validator as SV  # noqa: E402

IDS = SPLIT["prompt_dev_ids"]
SOURCES = {"P02_stage1": False, "P05_final_v4": True}
TEMPLATE = (EXP4 / "prompts" / "P02_comprehensive_extraction.txt").read_text(encoding="utf-8")
G.install(IDS, include_labels=True, allow_validation=False)


def leaves(o, p=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from leaves(v, f"{p}.{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from leaves(v, f"{p}[{i}]")
    else:
        yield p, o


def by(rep):
    kind, cat, field = collections.Counter(), collections.Counter(), collections.Counter()
    for v in rep.violations:
        kind[v["kind"]] += 1
        m = re.sub(r"\[\d+\]", "", v["message"])
        cat[(v["kind"], m.split(".")[0] if not m.startswith("medical_history") else ".".join(m.split(".")[:2]))] += 1
        field[(v["kind"], m.split("=")[0])] += 1
    return kind, cat, field


def main():
    assert not F.verify_against_template(TEMPLATE), "nullable table inconsistent with the model template"
    res = {"s0_2_version": F.S0_2_VERSION, "template_consistency_problems": [], "scope": "prompt_dev (50 ids)", "sources": {}}
    spy = G.StrictAccessSpy(allow_validation=False)
    with spy:
        for src, trusted in SOURCES.items():
            o_dir, s1_dir, s2_dir = EXP5 / "data/original" / src, EXP5 / "data/repaired" / src, EXP5 / "data/repaired_s0_2" / src
            s2_dir.mkdir(parents=True, exist_ok=True)
            rows, tot = [], {"orig": [collections.Counter() for _ in range(3)], "s01": [collections.Counter() for _ in range(3)], "s02": [collections.Counter() for _ in range(3)]}
            comp = collections.Counter()
            changed_existing, idem_changes, pipe_changes, score = [], 0, 0, {"s01": collections.Counter(), "s02": collections.Counter()}
            for eid in IDS:
                orig = json.loads((o_dir / f"encounter_{eid}.json").read_text(encoding="utf-8"))
                s1 = json.loads((s1_dir / f"encounter_{eid}.json").read_text(encoding="utf-8"))
                s2, log = F.fill(s1, eid)
                (s2_dir / f"encounter_{eid}.json").write_text(json.dumps(s2, indent=2, ensure_ascii=False), encoding="utf-8")
                rows += log
                for name, obj in (("orig", orig), ("s01", s1), ("s02", s2)):
                    r = SV.validate(obj)
                    comp[name] += r.compliant
                    for acc, c in zip(tot[name], by(r)):
                        acc.update(c)
                # preservation: every leaf of S0.1 (including nulls and empty strings) is unchanged in S0.2
                l1, l2 = dict(leaves(s1)), dict(leaves(s2))
                changed_existing += [(eid, p) for p, v in l1.items() if p not in l2 or l2[p] != v]
                # idempotency of S0.2, and of the whole pipeline (S0.1 then S0.2) applied again
                _, again = F.fill(s2, eid)
                idem_changes += len(again)
                tr = json.loads((S.INPUT_DIR / f"encounter_{eid}.json").read_text(encoding="utf-8"))
                p1, log1, _ = R1.repair(s2, tr["segments"], eid, trusted)
                pipe_changes += len([r for r in log1 if r["kind"] == "change"])
                gold = ER.load_gold(eid)
                for name, obj in (("s01", s1), ("s02", s2)):
                    sc = ER.score_encounter(gold, obj, tr)["strict"]
                    for k in ("tp", "fp", "fn"):
                        score[name][k] += sum(v[k] for v in sc.values())
            with open(EXP5 / "logs" / f"transformations_s0_2_{src}.jsonl", "w", encoding="utf-8") as f:
                for r in rows:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
            sect = lambda c: {f"{k[0]}|{k[1]}": v for k, v in sorted(c.items(), key=lambda kv: -kv[1])}
            res["sources"][src] = {
                "records": len(IDS), "schema_compliant_records": {k: f"{v}/{len(IDS)}" for k, v in comp.items()},
                "violations_total": {k: sum(tot[k][0].values()) for k in tot}, "violations_by_kind": {k: dict(tot[k][0]) for k in tot},
                "violations_by_category_top": {k: dict(list(sect(tot[k][1]).items())[:25]) for k in tot},
                "remaining_after_s0_2_by_field_top": dict(list(sect(tot["s02"][2]).items())[:20]),
                "fields_filled_with_null": len(rows), "fields_filled_by_name": dict(collections.Counter(r["path"].split(".")[-1] for r in rows).most_common()),
                "existing_values_changed_or_removed": len(changed_existing), "existing_values_changed_examples": changed_existing[:5],
                "idempotency_second_s0_2_pass_changes": idem_changes, "idempotency_second_full_pipeline_pass_s0_1_changes_after_s0_2": pipe_changes,
                "informational_strict_scores_s0_1": dict(score["s01"]), "informational_strict_scores_s0_2": dict(score["s02"]),
            }
    res["file_access_audit"] = {"locked_test_files_opened": G.locked_test_accesses(spy.opened), "sealed_hash_file_opened": any("SEALED" in x for x in spy.opened),
                                "validation_records_opened": spy.report()["validation_records_opened"]}
    (EXP5 / "results" / "s0_2_metrics.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    for s, d in res["sources"].items():
        print(s, d["schema_compliant_records"], d["violations_total"], d["violations_by_kind"]["s02"], "filled", d["fields_filled_with_null"], "changed existing", d["existing_values_changed_or_removed"],
              "idem", d["idempotency_second_s0_2_pass_changes"], d["idempotency_second_full_pipeline_pass_s0_1_changes_after_s0_2"], d["informational_strict_scores_s0_1"] == d["informational_strict_scores_s0_2"])
    print(res["file_access_audit"])


if __name__ == "__main__":
    main()
