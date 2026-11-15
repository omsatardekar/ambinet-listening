"""Evaluation of one finished Qwen3-1.7B run with the UNCHANGED canonical 0.6B evaluator (strict multiset matching on normalized primary keys; the frozen helpers of EXP_006/EXP_007 are imported
read-only), against the 0.6B references on the SAME 50 prompt-development ids, plus any additional 1.7B runs given with --also.  Failed outputs contribute zero predictions (headline = all 50 records,
all 18 canonical categories).  Parsed-only numbers are NOT produced as headline results.  Labels are opened here only (after inference), prompt-dev ids only, under StrictAccessSpy.
usage: python -B -s evaluate_run.py --experiment EXP_001_DIRECT_INFERENCE --run-id P00_direct_dev50 --label P00 [--also EXP_001_DIRECT_INFERENCE/P00_direct_dev50 ...]"""
import argparse
import collections
import json
import statistics as st
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common_1_7b as C  # noqa: E402

sys.path.insert(0, str(C.EXP6 / "s1"))
sys.path.insert(0, str(C.LEGACY / "experiments" / "EXP_007_S1_1_SIMPLIFIED_EXTRACTION" / "s1_1"))
import evaluate_s1 as E  # noqa: E402   (frozen EXP_006 evaluator helpers; importing installs the development-only dataset guard, main() is not run)
import evaluate_s1_1 as E11  # noqa: E402  (frozen EXP_007 helpers: system_block, eff, perf_add)
from direct_inference_baseline.evaluation import schema_validator as SV  # noqa: E402
from direct_inference_baseline.evaluation.entity_matching import CATEGORIES, prf  # noqa: E402


# RUNTIME-ONLY robustness wrapper (no frozen file is edited): the frozen same_duration() raises ValueError when a model emits a non-numeric
# duration "value" (e.g. "10 days").  Such a prediction is a malformed attribute and is scored as a MISMATCH instead of crashing the evaluation.
# Cases that did not crash are scored identically, so 0.6B numbers are unaffected.
from direct_inference_baseline.evaluation import attribute_metrics as AM  # noqa: E402
_orig_same_duration = AM.same_duration
MALFORMED_DURATION_COUNT = [0]


def _safe_same_duration(g, p):
    try:
        return _orig_same_duration(g, p)
    except (ValueError, TypeError):
        MALFORMED_DURATION_COUNT[0] += 1
        return False


for _k, _f in list(AM.ATTRS.items()):
    if _f is _orig_same_duration:
        AM.ATTRS[_k] = _safe_same_duration

ap = argparse.ArgumentParser()
ap.add_argument("--experiment", required=True)
ap.add_argument("--run-id", required=True)
ap.add_argument("--label", required=True)
ap.add_argument("--also", nargs="*", default=[], help="other 1.7B runs as EXPERIMENT/RUN_ID (same 50 ids)")
ap.add_argument("--subset-from-run", default=None, help="EXPERIMENT/RUN_ID: score only the frozen ids that this run has completed (shared id subset for every system)")
ap.add_argument("--tag", default="", help="suffix for output locations, e.g. subset30 (never overwrites the full-50 evaluation)")
A = ap.parse_args()
IDS = E.IDS
assert IDS == json.loads((C.TRACK / "manifests" / "FROZEN_50_PROMPT_DEV_IDS.json").read_text(encoding="utf-8"))["ids"]
if A.subset_from_run:
    _e, _r = A.subset_from_run.split("/")
    _done = json.loads((C.TRACK / "experiments" / _e / "evaluations" / _r / "run_manifest.json").read_text(encoding="utf-8-sig"))["records"]
    IDS[:] = [i for i in IDS if i in _done and _done[i].get("status") in ("parsed", "failed")]   # in place: E, E11 share this list object
N = len(IDS)


def load_dir(d):
    return {eid: json.loads((d / f"encounter_{eid}.json").read_text(encoding="utf-8")) for eid in IDS if (d / f"encounter_{eid}.json").exists()}


def run_paths(exp, run):
    e = C.TRACK / "experiments" / exp
    return e, json.loads((e / "evaluations" / run / "run_manifest.json").read_text(encoding="utf-8-sig")), e / "outputs" / "parsed" / run, e / "logs" / f"performance_{run}.json"


def struct_of(man_records):
    s = collections.Counter()
    for eid in IDS:
        r = man_records.get(eid)
        if not r:
            s["missing_record"] += 1
            continue
        s["attempted"] += 1
        s["valid_json"] += r.get("status") == "parsed"
        s["invalid_json"] += r.get("status") == "failed"
        s["failure_" + str(r.get("failure_type"))] += r.get("status") == "failed"
        s["token_cap_hits"] += r.get("finish_reason") == "length"
        s["schema_compliant_records"] += bool(r.get("schema_compliant"))
        for k, v in (r.get("schema_violation_counts") or {}).items():
            s["violations_" + k] += v
    return dict(s)


SYSTEMS = {}   # name -> (preds, man_records, eff, struct)
spy = C.G.StrictAccessSpy(allow_validation=False)
with spy:
    # 0.6B references
    m3 = json.loads((C.EXP3 / "run_manifest_dev100.json").read_text(encoding="utf-8-sig"))["records"]
    p00_06 = load_dir(C.EXP3 / "parsed_predictions" / "exp_003_dev_100")
    SYSTEMS["0.6B P00 direct"] = (p00_06, m3, E11.perf_add(E11.eff([m3[i] for i in IDS if "completion_tokens" in m3[i]]), C.EXP3 / "logs" / "performance_dev100.json"))
    SYSTEMS["0.6B P02 best prompt (dev)"] = (E.load_p02(), E.P02_MAN["records"], E11.perf_add(E11.eff([E.P02_MAN["records"][i] for i in IDS]), E.P02_RUN / "performance.json"))
    # 1.7B runs
    for tag in [f"{A.experiment}/{A.run_id}"] + A.also:
        exp, run = tag.split("/")
        e, man, pdir, perf = run_paths(exp, run)
        recs = man["records"]
        SYSTEMS[f"1.7B {run}"] = (load_dir(pdir), recs, E11.perf_add(E11.eff([recs[i] for i in IDS if i in recs and "completion_tokens" in recs[i]]), perf))
    this = f"1.7B {A.run_id}"
    blocks, aggs, results = {}, {}, {}
    for name, (preds, recs, effi) in SYSTEMS.items():
        res, agg, block = E11.system_block(name, preds)
        results[name], aggs[name], blocks[name] = res, agg, block
        block["structural"] = struct_of(recs)
        block["efficiency"] = effi
        block["evidence_grounding"] = agg.get("evidence_grounding")
        block["category_table"] = E.cat_table(agg)
        block["micro_ids_scored"] = len(IDS)
    audit = {"locked_test_files_opened": C.G.locked_test_accesses(spy.opened), "sealed_hash_file_opened": any("SEALED" in x for x in spy.opened), "validation_records_opened": spy.report()["validation_records_opened"],
             "label_files_opened_prompt_dev_only": spy.report()["label_files_opened"]}

EXP = C.TRACK / "experiments" / A.experiment
out = EXP / "evaluations" / A.run_id / A.tag if A.tag else EXP / "evaluations" / A.run_id
(out / "record_metrics").mkdir(parents=True, exist_ok=True)
for eid in IDS:
    rec = {"encounter_id": eid}
    for name in blocks:
        rec[name] = {c: results[name][eid]["strict"][c] for c in CATEGORIES}
        rec[name + " micro"] = prf(*(sum(rec[name][c][x] for c in CATEGORIES) for x in ("tp", "fp", "fn")))
    (out / "record_metrics" / f"encounter_{eid}.json").write_text(json.dumps(rec, indent=1, default=str), encoding="utf-8")
collapse = {n: [c for c in CATEGORIES if blocks[n]["category_table"][c]["tp"] == 0 and blocks["0.6B P02 best prompt (dev)"]["category_table"][c]["tp"] >= 3] for n in blocks}
full = {"experiment": A.experiment, "run_id": A.run_id, "label": A.label, "scope": f"prompt_dev subset: {N} of the 50 original prompt-development ids (previously used for 0.6B prompt development). DEVELOPMENT-ONLY results, not independent validation, "
        "labels are generator-derived (not human-verified, not clinical validation).", "ids": IDS, "systems": blocks, "category_collapse_vs_0_6B_P02": collapse, "file_access_audit": audit}
(out / "METRICS.json").write_text(json.dumps(full, indent=1, default=str), encoding="utf-8")
(out / "CATEGORY_METRICS.json").write_text(json.dumps({n: b["category_table"] for n, b in blocks.items()}, indent=1, default=str), encoding="utf-8")


# ------------------------------------------------------------------ markdown summary
def f(x, d=3):
    return "-" if x is None else (f"{x:.{d}f}" if isinstance(x, float) else str(x))


names = list(blocks)
rows = []


def row(label, fn):
    rows.append("| " + label + " | " + " | ".join(str(fn(blocks[n])) for n in names) + " |")


row("Strict micro P", lambda b: f(b["strict_micro"]["precision"]))
row("Strict micro R", lambda b: f(b["strict_micro"]["recall"]))
row("**Strict micro F1**", lambda b: "**" + f(b["strict_micro"]["f1"], 4) + "**")
row("TP / FP / FN", lambda b: f"{b['tp_fp_fn']['tp']}/{b['tp_fp_fn']['fp']}/{b['tp_fp_fn']['fn']}")
row("Strict macro P / R / F1", lambda b: f"{f(b['strict_macro']['precision'])} / {f(b['strict_macro']['recall'])} / {f(b['strict_macro']['f1'], 4)}")
row("Micro F1 excl. clinical_conditions", lambda b: f(b["micro_excl_clinical_conditions"]["f1"], 4))
row("Micro F1 excl. conditions+uncertainties", lambda b: f(b["micro_excl_clinical_conditions_and_uncertainties"]["f1"], 4))
row(f"Valid JSON (of {N})", lambda b: b["structural"].get("valid_json", 0))
row("Invalid JSON / token-cap hits", lambda b: f"{b['structural'].get('invalid_json', 0)} / {b['structural'].get('token_cap_hits', 0)}")
row("Fully canonical-schema-compliant records", lambda b: b["canonical_fully_compliant_records"])
row("Canonical schema violations (total)", lambda b: sum((b["canonical_schema_violations"] or {}).values()))
row("Evidence grounding (strict / lenient+)", lambda b: f"{f((b['evidence_grounding'] or {}).get('grounded_strict_rate'))} / {f((b['evidence_grounding'] or {}).get('grounded_lenient_or_better_rate'))}")
row("Speaker attribution accuracy", lambda b: f(b["speaker_attribution"].get("accuracy")))
row("Medication recall (strict)", lambda b: f(b["category_table"]["medications"]["recall"]))
row("Medication precision (strict)", lambda b: f(b["category_table"]["medications"]["precision"]))
row("Dose errors / checked on matched", lambda b: f"{b['clinical_errors'].get('dose_errors_on_matched', 0)}/{b['clinical_errors'].get('dose_checked_on_matched', 0)}")
row("Missing prescribed meds (of gold planned)", lambda b: f"{b['clinical_errors'].get('missing_prescribed_medications(gold planned, unmatched)')}/{b['clinical_errors'].get('gold_planned_medications')}")
row(f"Allergy status errors (of {N})", lambda b: b["clinical_errors"].get("allergy_status_errors"))
row("Allergy category recall", lambda b: f(b["category_table"]["allergies"]["recall"]))
row("Negation: gold negatives correct rate", lambda b: f(b["negation_polarity"].get("gold_negatives_correct_rate")))
row("Polarity flips (neg->pos / pos->neg)", lambda b: f"{b['negation_polarity'].get('polarity_flip_negative_reported_as_present', 0)}/{b['negation_polarity'].get('polarity_flip_present_reported_as_negative', 0)}")
row("Temporality accuracy (symptoms, gold non-null)", lambda b: f((b["attributes"].get("by_field", {}).get("symptoms.temporality") or {}).get("accuracy_on_gold_nonnull")))
row("Unsupported claims", lambda b: b["unsupported_claims"].get("unsupported_claims"))
row("Contradictions (same item pos+neg)", lambda b: b["clinical_errors"].get("contradictions_same_item_positive_and_negative_in_prediction"))
row("Duplicate facts", lambda b: b["duplicate_facts"])
row("Mean input / output tokens", lambda b: f"{f(b['efficiency'].get('input_tokens_mean'), 0)} / {f(b['efficiency'].get('output_tokens_mean'), 0)}")
row("Mean latency per record (s)", lambda b: f(b["efficiency"].get("latency_s_mean"), 1))
row("Tokens/s overall (mean) / decode / prefill", lambda b: f"{f(b['efficiency'].get('tokens_per_second_overall_mean'), 2)} / {f(b['efficiency'].get('decode_tokens_per_second_mean'), 2)} / {f(b['efficiency'].get('prefill_tokens_per_second_mean'), 1)}")
row("Peak process working set (MB)", lambda b: b["efficiency"].get("peak_working_set_mb_max", "-"))
cat_rows = ["| Category (recall / F1) | " + " | ".join(names) + " |", "|---|" + "---|" * len(names)]
for c in CATEGORIES:
    cat_rows.append(f"| {E.CAT_LABEL[c]} | " + " | ".join(f"{f(blocks[n]['category_table'][c]['recall'])} / {f(blocks[n]['category_table'][c]['f1'])}" for n in names) + " |")
md = [f"# {A.run_id}: evaluation (development-only, {N} prompt-dev ids)", "", full["scope"], "",
      f"Headline = all {N} records, all 18 canonical categories, failed outputs counted as zero predictions. Unchanged canonical evaluator.", "",
      "| Metric | " + " | ".join(names) + " |", "|---|" + "---|" * len(names), *rows, "", "## Per-category (strict)", "", *cat_rows, "",
      f"Category collapse vs 0.6B P02 (TP=0 where P02 TP>=3): {json.dumps(collapse)}", "",
      f"File-access audit: locked-test opened {len(audit['locked_test_files_opened'])}, sealed hash file opened {audit['sealed_hash_file_opened']}, validation records opened {len(audit['validation_records_opened'])}."]
(C.TRACK / "experiments" / A.experiment / "reports").mkdir(parents=True, exist_ok=True)
(EXP / "reports" / f"{A.run_id}{'_' + A.tag if A.tag else ''}_EVALUATION.md").write_text("\n".join(md), encoding="utf-8")
print("\n".join(md))
