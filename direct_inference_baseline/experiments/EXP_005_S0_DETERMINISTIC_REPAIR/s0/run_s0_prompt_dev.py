"""Run S0 on COPIES of the stored prompt-development outputs (50 prompt_dev ids only; validation and locked-test records are never opened: StrictAccessSpy raises on any such access).
Sources: P02 stage-1 parsed predictions (rule E not applicable) and P05 prompt_dev final predictions v4 (cited evidence from the P05 retrieval; rule E applicable).
Writes (all inside EXP_005): data/original/<source>/ (byte copies), data/repaired/<source>/, logs/*.jsonl, results/s0_metrics.json.  Originals in EXP_004 are only read.
usage: python -B run_s0_prompt_dev.py"""
import collections
import hashlib
import json
import shutil
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
EXP5 = HERE.parent
EXP4 = EXP5.parent / "EXP_004_QWEN3_0.6B_PROMPT_ENGINEERING"
sys.path.insert(0, str(EXP4 / "experiments"))
sys.path.insert(0, str(HERE))
from common import S, SPLIT  # noqa: E402  (EXP_004 frozen helper; imports the existing project modules read-only)
import dev_guard as G  # noqa: E402
import s0_repair as R  # noqa: E402
from direct_inference_baseline.evaluation import evaluation_runner as ER  # noqa: E402
from direct_inference_baseline.evaluation import schema_validator as SV  # noqa: E402
from direct_inference_baseline.evaluation.entity_matching import CATEGORIES, entity_list  # noqa: E402

IDS = SPLIT["prompt_dev_ids"]
assert len(IDS) == 50
SOURCES = {"P02_stage1": (EXP4 / "outputs/P02_comprehensive_extraction_dev50/parsed_predictions/P02_comprehensive_extraction_dev50", False),
           "P05_final_v4": (EXP4 / "p05_diagnostics/final_predictions_v4", True)}
sha = lambda b: hashlib.sha256(b).hexdigest()
G.install(IDS, include_labels=True, allow_validation=False)
count_entities = lambda p: sum(len(entity_list(p, c)) for c in CATEGORIES)


def sizes(p):
    n = 0
    for sec in R.LIST_SECTIONS:
        v = p.get(sec)
        n += len(v) if isinstance(v, list) else 0
    for sub in R.HIST:
        v = (p.get("medical_history") or {}).get(sub) if isinstance(p.get("medical_history"), dict) else None
        n += len(v) if isinstance(v, list) else 0
    return n


def main():
    res = {"s0_version": R.S0_VERSION, "scope": "prompt_dev (50 ids)", "sources": {}}
    spy = G.StrictAccessSpy(allow_validation=False)
    with spy:
        for src, (d, trusted) in SOURCES.items():
            o_dir, r_dir = EXP5 / "data/original" / src, EXP5 / "data/repaired" / src
            for x in (o_dir, r_dir):
                x.mkdir(parents=True, exist_ok=True)
            rows, status_c = [], collections.Counter()
            v_orig, v_rep = collections.Counter(), collections.Counter()
            comp_o = comp_r = 0
            tp = {"orig": collections.Counter(), "rep": collections.Counter()}
            sec_before = sec_after = 0
            integrity_problems = []
            per_rule = collections.Counter()
            flagged_entities = set()
            rec_fix = collections.Counter()
            for eid in IDS:
                raw = (d / f"encounter_{eid}.json").read_bytes()
                (o_dir / f"encounter_{eid}.json").write_bytes(raw)
                assert sha((o_dir / f"encounter_{eid}.json").read_bytes()) == sha(raw)
                pred = json.loads(raw.decode("utf-8"))
                tr = json.loads((S.INPUT_DIR / f"encounter_{eid}.json").read_text(encoding="utf-8"))
                rep, log, st = R.repair(pred, tr["segments"], eid, evidence_trusted=trusted)
                (r_dir / f"encounter_{eid}.json").write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
                rows += log
                status_c[st or "no_allergy_placeholder"] += 1
                so, sr = SV.validate(pred), SV.validate(rep)
                comp_o += so.compliant
                comp_r += sr.compliant
                v_orig.update(so.counts)
                v_rep.update(sr.counts)
                sec_before += sizes(pred)
                sec_after += sizes(rep)
                # informational: frozen evaluator on prompt_dev labels (strict); not a clinical-accuracy claim
                gold = ER.load_gold(eid)
                for name, obj in (("orig", pred), ("rep", rep)):
                    sc = ER.score_encounter(gold, obj, tr)["strict"]
                    for k in ("tp", "fp", "fn"):
                        tp[name][k] += sum(v[k] for v in sc.values())
                # integrity: every difference between original and repaired must be covered by a logged change path
                changed_paths = {r["path"].split(".")[0].split("[")[0] for r in log if r["kind"] == "change"}
                for sec in set(pred) | set(rep):
                    if sec not in ("clinical_evidence",) and json.dumps(pred.get(sec), sort_keys=True) != json.dumps(rep.get(sec), sort_keys=True) and sec not in changed_paths:
                        if not (sec == "medical_history" and "medical_history" in changed_paths):
                            integrity_problems.append((eid, sec))
                for r in log:
                    if r["kind"] == "flag":
                        flagged_entities.add((eid, r["path"]))
                        # unsupported clinical content left unchanged
            for r in rows:
                per_rule[(r["kind"], r["rule"])] += 1
            changes = [r for r in rows if r["kind"] == "change"]
            flags = [r for r in rows if r["kind"] == "flag"]
            (EXP5 / "logs").mkdir(exist_ok=True)
            with open(EXP5 / "logs" / f"transformations_{src}.jsonl", "w", encoding="utf-8") as f:
                for r in rows:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
            pr = lambda c: {"precision": round(c["tp"] / max(1, c["tp"] + c["fp"]), 4), "recall": round(c["tp"] / max(1, c["tp"] + c["fn"]), 4),
                            "f1": round(2 * c["tp"] / max(1, 2 * c["tp"] + c["fp"] + c["fn"]), 4)}
            res["sources"][src] = {
                "records": len(IDS), "rule_E_applicable": trusted,
                "schema_compliant_records_original": f"{comp_o}/{len(IDS)}", "schema_compliant_records_repaired": f"{comp_r}/{len(IDS)}",
                "schema_violations_original": dict(v_orig), "schema_violations_repaired": dict(v_rep),
                "total_violations_original": sum(v_orig.values()), "total_violations_repaired": sum(v_rep.values()),
                "structural_corrections_total": len(changes), "corrections_by_rule": {k[1]: v for k, v in per_rule.items() if k[0] == "change"},
                "fields_changed": len([r for r in changes if "." in r["path"] or r["rule"] in ("A_object_to_list",)]), "flags_total": len(flags), "flags_by_rule": {k[1]: v for k, v in per_rule.items() if k[0] == "flag"},
                "changes_requiring_human_review": len([r for r in changes if r["human_review_required"]]), "changes_requiring_human_review_by_rule": dict(collections.Counter(r["rule"] for r in changes if r["human_review_required"])),
                "ambiguous_cases_preserved_and_flagged": per_rule[("flag", "A_ambiguous_object")] + per_rule[("flag", "B_unknown_enum_value")] + per_rule[("flag", "E_ambiguous_speakers")],
                "entities_in_list_sections_before": sec_before, "entities_in_list_sections_after": sec_after,
                "facts_dropped_placeholder_allergies": per_rule[("change", "C_allergy_placeholder_removed")], "facts_added_explicit_no_known_allergies": per_rule[("change", "C_explicit_no_known_allergies_represented")],
                "facts_recovered_by_object_to_list": per_rule[("change", "A_object_to_list")],
                "allergy_placeholder_status_by_record": dict(status_c),
                "unsupported_clinical_items_flagged_and_left_unchanged": len(flagged_entities),
                "integrity_problems_changes_not_covered_by_log": integrity_problems,
                "strict_evaluator_entities_original": count_entities.__call__ if False else None,
                "informational_strict_scores_prompt_dev_original": {**dict(tp["orig"]), **pr(tp["orig"])}, "informational_strict_scores_prompt_dev_repaired": {**dict(tp["rep"]), **pr(tp["rep"])},
            }
    res["file_access_audit"] = spy.report()
    res["file_access_audit"]["validation_or_locked_test_records_opened"] = [x for x in spy.opened if "/output/inputs/" in x.replace("\\", "/") or "/output/labels/" in x.replace("\\", "/")
                                                                              if not any(f"encounter_{i}.json" in x for i in IDS)]
    del res["sources"]["P02_stage1"]["strict_evaluator_entities_original"], res["sources"]["P05_final_v4"]["strict_evaluator_entities_original"]
    (EXP5 / "results").mkdir(exist_ok=True)
    (EXP5 / "results" / "s0_metrics.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    print(json.dumps({k: (v if k != "sources" else {s: {kk: vv for kk, vv in d.items() if kk in ("schema_compliant_records_original", "schema_compliant_records_repaired", "total_violations_original", "total_violations_repaired", "structural_corrections_total", "corrections_by_rule", "flags_total", "informational_strict_scores_prompt_dev_original", "informational_strict_scores_prompt_dev_repaired", "integrity_problems_changes_not_covered_by_log")} for s, d in v.items()}) for k, v in res.items()}, indent=1, default=str))


if __name__ == "__main__":
    main()
