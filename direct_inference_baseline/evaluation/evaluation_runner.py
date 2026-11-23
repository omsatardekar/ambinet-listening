"""Evaluation of a finished inference experiment against the frozen labels.

Labels are read ONLY here, after predictions were generated and saved. Two scoring views are always reported side by side:
  valid_only : encounters whose output parsed as a JSON object (failed encounters excluded - shows quality when the model succeeds)
  end_to_end : every attempted encounter; an encounter without a usable prediction contributes all its gold entities as FN
               (this is a scoring convention only; nothing is written back as a prediction)
Coverage and failure rate are reported next to every accuracy figure."""
from __future__ import annotations

import csv
import json
import statistics as st
from collections import Counter, defaultdict
from datetime import datetime, timezone

from ..config import settings as S
from . import attribute_metrics as AM
from . import clinical_metrics as CM
from . import evidence_evaluator as EE
from . import schema_validator as SV
from .entity_matching import CATEGORIES, entity_list, match_category, micro_macro, prf

CLINICAL_NAMES = {"Symptom Extraction F1": "symptoms", "Negative Finding F1": "negative_findings", "Medication Extraction F1": "medications",
                  "Allergy Extraction F1": "allergies"}
HISTORY_CATS = ["medical_history.past_medical_history", "medical_history.surgical_history", "medical_history.family_history", "medical_history.social_history"]


def load_gold(eid: str) -> dict:
    return json.loads((S.LABEL_DIR / f"encounter_{eid}.json").read_text(encoding="utf-8"))


def score_encounter(gold: dict, pred: dict | None, transcript: dict) -> dict:
    """Raw counters for one encounter. pred=None means no usable prediction (all gold entities are FN)."""
    pred = pred if isinstance(pred, dict) else {}
    res = {"strict": {}, "fuzzy": {}}
    pairs_by_cat, fp_by_cat = {}, {}
    for cat in CATEGORIES:
        m = match_category(entity_list(gold, cat), entity_list(pred, cat), cat, fuzzy=True)
        res["strict"][cat] = {"tp": m["tp"], "fp": m["fp"], "fn": m["fn"]}
        ft = m["tp"] + len(m["fuzzy_pairs"])
        res["fuzzy"][cat] = {"tp": ft, "fp": m["fp"] - len(m["fuzzy_pairs"]), "fn": m["fn"] - len(m["fuzzy_pairs"])}
        pairs_by_cat[cat] = m["pairs"]
        fp_by_cat[cat] = m["fp_entities"]
    res["attributes"] = AM.score_pairs(pairs_by_cat)
    res["vitals"] = dict(CM.vital_signs(gold, pred))
    res["speaker"] = dict(CM.speaker_attribution(gold, pairs_by_cat))
    res["negation"] = dict(CM.negation(gold, pred))
    res["grounding"] = EE.evaluate_grounding(pred, transcript)
    res["unsupported"] = EE.unsupported_claims(pred, transcript, fp_by_cat)
    return res


def _sum_counts(rows, key):
    c = Counter()
    for r in rows:
        c.update({k: v for k, v in r[key].items() if isinstance(v, int)})
    return dict(c)


def aggregate(results: list[dict]) -> dict:
    out = {"n_encounters": len(results)}
    for mode in ("strict", "fuzzy"):
        per_cat = {}
        for cat in CATEGORIES:
            tp = sum(r[mode][cat]["tp"] for r in results)
            fp = sum(r[mode][cat]["fp"] for r in results)
            fn = sum(r[mode][cat]["fn"] for r in results)
            per_cat[cat] = prf(tp, fp, fn)
        out[mode] = {"per_category": per_cat, **micro_macro(per_cat)}
    hist = {k: sum(out["strict"]["per_category"][c][k] for c in HISTORY_CATS) for k in ("tp", "fp", "fn")}
    out["medical_history_combined_strict"] = prf(**hist)
    att_counts = defaultdict(Counter)
    conf = defaultdict(lambda: defaultdict(Counter))
    for r in results:
        for k, v in r["attributes"]["counts"].items():
            att_counts[k].update(v)
        for k, m in r["attributes"]["confusion"].items():
            for g, pv in m.items():
                conf[k][g].update(pv)
    out["attributes"] = AM.summarize({k: dict(v) for k, v in att_counts.items()})
    out["confusion_matrices"] = {k: {g: dict(p) for g, p in m.items()} for k, m in conf.items()}
    v = _sum_counts(results, "vitals")
    out["vital_signs"] = {"accuracy": v.get("correct", 0) / v["gold_vitals"] if v.get("gold_vitals") else None, **v,
                          "name_found_rate": v.get("name_found", 0) / v["gold_vitals"] if v.get("gold_vitals") else None}
    sp = _sum_counts(results, "speaker")
    out["speaker_attribution"] = {"accuracy": sp.get("correct", 0) / sp["evaluated"] if sp.get("evaluated") else None, "denominator_evaluated": sp.get("evaluated", 0), **sp}
    ng = _sum_counts(results, "negation")
    out["negation_polarity"] = {"gold_negatives_correct_rate": ng.get("correct", 0) / ng["gold_negatives"] if ng.get("gold_negatives") else None, **ng}
    g = defaultdict(int)
    for r in results:
        for k in ("grounded_strict", "grounded_lenient", "partially_supported", "unsupported", "total"):
            g[k] += r["grounding"][k]
    tot = g["total"]
    out["evidence_grounding"] = {"predicted_entities_evaluated": tot, **dict(g),
                                 "grounded_strict_rate": g["grounded_strict"] / tot if tot else None,
                                 "grounded_lenient_or_better_rate": (g["grounded_strict"] + g["grounded_lenient"]) / tot if tot else None,
                                 "partially_supported_rate": g["partially_supported"] / tot if tot else None,
                                 "unsupported_rate": g["unsupported"] / tot if tot else None}
    up = {"predicted_entities": sum(r["unsupported"]["predicted_entities"] for r in results),
          "false_positives": sum(r["unsupported"]["false_positives"] for r in results),
          "unsupported_claims": sum(r["unsupported"]["unsupported_claims"] for r in results),
          "extra_but_transcript_supported": sum(r["unsupported"]["extra_but_transcript_supported"] for r in results)}
    up["unsupported_claim_rate_of_predictions"] = up["unsupported_claims"] / up["predicted_entities"] if up["predicted_entities"] else None
    up["unsupported_claim_rate_of_false_positives"] = up["unsupported_claims"] / up["false_positives"] if up["false_positives"] else None
    out["unsupported_claims"] = up
    return out


def _ms(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    return {"mean": round(st.mean(xs), 3), "median": round(st.median(xs), 3), "p95": round(xs[int(0.95 * (len(xs) - 1))], 3), "min": round(xs[0], 3), "max": round(xs[-1], 3), "n": len(xs)}


def evaluate_experiment(experiment_id: str) -> dict:
    rep_dir = S.REPORT_DIR / experiment_id
    man = json.loads((rep_dir / "run_manifest.json").read_text(encoding="utf-8"))
    ids = man["encounter_ids"]
    recs = man["records"]
    meta = {r["encounter_id"]: r for r in csv.DictReader(open(S.MANIFEST_CSV, newline="", encoding="utf-8"))}
    attempted = [i for i in ids if i in recs]
    parsed = [i for i in attempted if recs[i]["status"] == "parsed"]
    per_enc, results_all, results_valid = {}, {}, []
    for eid in attempted:
        gold = load_gold(eid)
        tr = json.loads((S.INPUT_DIR / f"encounter_{eid}.json").read_text(encoding="utf-8"))
        pred = json.loads((S.PARSED_DIR / experiment_id / f"encounter_{eid}.json").read_text(encoding="utf-8")) if eid in parsed else None
        r = score_encounter(gold, pred, tr)
        results_all[eid] = r
        if eid in parsed:
            results_valid.append(r)
        micro = prf(*(sum(r["strict"][c][k] for c in CATEGORIES) for k in ("tp", "fp", "fn")))
        per_enc[eid] = {"specialty": meta[eid]["specialty"], "complexity": meta[eid]["complexity"], "status": recs[eid]["status"],
                        "failure_type": recs[eid].get("failure_type"), "strict_micro": micro, "attributes_counts": r["attributes"]["counts"],
                        "grounding": {k: r["grounding"][k] for k in ("grounded_strict", "grounded_lenient", "partially_supported", "unsupported", "total")},
                        "unsupported_claims": r["unsupported"]["unsupported_claims"]}
    # ---- JSON / schema metrics
    n_att = len(attempted)
    ftypes = Counter(recs[i].get("failure_type") for i in attempted if recs[i]["status"] == "failed")
    comp = [recs[i] for i in parsed]
    jm = {"attempted": n_att, "valid_json": len(parsed), "json_validity_rate": len(parsed) / n_att if n_att else None,
          "failures_by_type": dict(ftypes), "truncated_rate": ftypes.get("truncated", 0) / n_att if n_att else None,
          "malformed_json_rate": (ftypes.get("invalid_json", 0) + ftypes.get("empty", 0) + ftypes.get("not_object", 0)) / n_att if n_att else None,
          "inference_error_rate": ftypes.get("inference_error", 0) / n_att if n_att else None,
          "schema_compliant_among_valid_json": sum(1 for r in comp if r["schema_compliant"]) / len(comp) if comp else None,
          "schema_compliance_rate_end_to_end": sum(1 for r in comp if r["schema_compliant"]) / n_att if n_att else None,
          "required_field_completeness_valid_json": (sum(r["keys_present"] for r in comp) / sum(r["keys_expected"] for r in comp)) if comp and sum(r["keys_expected"] for r in comp) else None,
          "unexpected_field_rate": (sum(r["keys_unexpected"] for r in comp) / sum(r["keys_emitted"] for r in comp)) if comp and sum(r["keys_emitted"] for r in comp) else None,
          "violation_kinds": dict(sum((Counter(r["schema_violation_counts"]) for r in comp), Counter()))}
    # ---- performance / cost
    lat = [recs[i].get("latency_seconds") for i in attempted]
    toks = [recs[i].get("completion_tokens") for i in attempted]
    tps = [recs[i]["completion_tokens"] / recs[i]["latency_seconds"] for i in attempted if recs[i].get("completion_tokens") and recs[i].get("latency_seconds")]
    perf = {"latency_seconds": _ms(lat), "completion_tokens": _ms(toks), "prompt_tokens": _ms([recs[i].get("prompt_tokens") for i in attempted]),
            "tokens_per_second": _ms(tps), "total_completion_tokens": sum(t for t in toks if t),
            "total_latency_hours": round(sum(x for x in lat if x) / 3600, 3), "finish_reason": dict(Counter(recs[i].get("finish_reason") for i in attempted)),
            "degenerate_repetition_flagged": sum(1 for i in attempted if any("repetition" in n for n in recs[i].get("parse_notes", [])))}
    coverage = {"split": man["split"], "requested": len(ids), "attempted": n_att, "valid_json": len(parsed), "failed": n_att - len(parsed),
                "coverage_attempted": n_att / len(ids), "coverage_valid_json": len(parsed) / len(ids), "failure_rate": (n_att - len(parsed)) / n_att if n_att else None}
    # ---- breakdowns (end-to-end, strict)
    groups = {"specialty": defaultdict(list), "complexity": defaultdict(list)}
    for eid, r in results_all.items():
        groups["specialty"][meta[eid]["specialty"]].append(r)
        groups["complexity"][meta[eid]["complexity"]].append(r)
    breakdown = {}
    for gname, d in groups.items():
        breakdown[gname] = {}
        for k, rs in sorted(d.items()):
            ag = aggregate(rs)
            nv = sum(1 for e in per_enc if meta[e][gname] == k and per_enc[e]["status"] == "parsed")
            breakdown[gname][k] = {"encounters": len(rs), "valid_json": nv, "strict_micro": ag["strict"]["micro"], "strict_macro_f1": ag["strict"]["macro"]["f1"]}
    agg_valid, agg_e2e = aggregate(results_valid), aggregate(list(results_all.values()))
    headline = {"experiment_id": experiment_id, "coverage_valid_json": coverage["coverage_valid_json"], "json_validity_rate": jm["json_validity_rate"],
                "schema_compliance_rate_end_to_end": jm["schema_compliance_rate_end_to_end"],
                "strict_micro_f1_end_to_end": agg_e2e["strict"]["micro"]["f1"], "strict_macro_f1_end_to_end": agg_e2e["strict"]["macro"]["f1"],
                "strict_micro_f1_valid_only": agg_valid["strict"]["micro"]["f1"] if results_valid else None}
    report = {"experiment_id": experiment_id, "evaluated_utc": datetime.now(timezone.utc).isoformat(), "provenance": {
        k: man[k] for k in ("dataset", "split", "split_seed", "model", "max_new_tokens", "prompt_sha256", "git_commit", "retry_policy")},
        "coverage": coverage, "json_and_schema": jm, "valid_only": agg_valid if results_valid else None, "end_to_end": agg_e2e,
        "performance": perf, "breakdown": breakdown, "failures": {i: recs[i].get("failure_type") or recs[i].get("error") for i in attempted if recs[i]["status"] == "failed"},
        "headline": headline, "metric_definitions": METRIC_DEFINITIONS}
    (rep_dir / "evaluation_report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    (rep_dir / "per_encounter_results.jsonl").write_text("\n".join(json.dumps({"encounter_id": k, **v}, ensure_ascii=False) for k, v in per_enc.items()) + "\n", encoding="utf-8")
    (rep_dir / "confusion_matrices.json").write_text(json.dumps({"valid_only": agg_valid.get("confusion_matrices") if results_valid else None, "end_to_end": agg_e2e["confusion_matrices"]}, indent=1), encoding="utf-8")
    (rep_dir / "evaluation_report.md").write_text(render_markdown(report), encoding="utf-8")
    return report


METRIC_DEFINITIONS = {
    "entity_matching": "Strict: normalised primary key per category, multiset TP/FP/FN (see entity_matching.py). Fuzzy reported separately.",
    "undefined_values": "Precision/recall/F1 are null (undefined) when their denominator is zero; they are never set to 0 or 1. Macro averages only categories with a defined value.",
    "end_to_end vs valid_only": "end_to_end counts an encounter without a usable prediction as all-FN; valid_only excludes such encounters.",
    "attribute_accuracy": "On strictly matched entities only: accuracy over gold-non-null values, and a separate false-attribute rate where gold is null.",
    "grounding": "grounded_strict / grounded_lenient / partially_supported / unsupported, see evidence_evaluator.py (lexical, not clinical correctness).",
    "unsupported_claims": "Strict FPs whose key is not lexically supported anywhere in the transcript; denominator reported.",
}


def _f(x, pct=False):
    if x is None:
        return "n/a"
    return f"{x * 100:.1f}%" if pct else f"{x:.3f}"


def render_markdown(r: dict) -> str:
    c, j = r["coverage"], r["json_and_schema"]
    L = [f"# Direct inference baseline report - {r['experiment_id']}", "",
         f"Model: `{r['provenance']['model'].get('model_id') or r['provenance']['model'].get('deployment_name')}` via **{r['provenance']['model']['provider']}**; "
         f"split **{c['split']}**; dataset manifest `{r['provenance']['dataset']['manifest_sha256'][:12]}...`; prompt `{r['provenance']['prompt_sha256'][:12]}...`; max_new_tokens {r['provenance']['max_new_tokens']}.", "",
         "## Coverage and failures", "",
         f"Requested {c['requested']}, attempted {c['attempted']}, valid JSON {c['valid_json']} ({_f(c['coverage_valid_json'], True)} of requested), failed {c['failed']} (failure rate {_f(c['failure_rate'], True)}).",
         f"Failure types: {j['failures_by_type'] or 'none'}.", "",
         "## JSON and schema", "",
         "| Metric | Value |", "|---|---|",
         f"| JSON validity | {_f(j['json_validity_rate'], True)} |", f"| Truncated (hit token budget) | {_f(j['truncated_rate'], True)} |",
         f"| Malformed JSON (not truncated) | {_f(j['malformed_json_rate'], True)} |",
         f"| Schema compliance among valid JSON | {_f(j['schema_compliant_among_valid_json'], True)} |",
         f"| Schema compliance end-to-end | {_f(j['schema_compliance_rate_end_to_end'], True)} |",
         f"| Required field completeness (valid JSON) | {_f(j['required_field_completeness_valid_json'], True)} |",
         f"| Unexpected field rate | {_f(j['unexpected_field_rate'], True)} |", ""]
    for view, key in (("End-to-end (failures count as all-FN)", "end_to_end"), ("Valid-JSON encounters only", "valid_only")):
        a = r[key]
        if not a:
            continue
        s = a["strict"]
        L += [f"## Entity extraction - {view}", "", f"Encounters: {a['n_encounters']}. Strict exact normalised matching.", "",
              f"| | Precision | Recall | F1 | TP | FP | FN |", "|---|---|---|---|---|---|---|",
              f"| Micro | {_f(s['micro']['precision'])} | {_f(s['micro']['recall'])} | {_f(s['micro']['f1'])} | {s['micro']['tp']} | {s['micro']['fp']} | {s['micro']['fn']} |",
              f"| Macro | {_f(s['macro']['precision'])} | {_f(s['macro']['recall'])} | {_f(s['macro']['f1'])} | | | |", "",
              f"Fuzzy (reported separately): micro F1 {_f(a['fuzzy']['micro']['f1'])}, macro F1 {_f(a['fuzzy']['macro']['f1'])}.", "",
              "| Category | P | R | F1 | TP | FP | FN |", "|---|---|---|---|---|---|---|"]
        for cat, v in s["per_category"].items():
            L.append(f"| {cat} | {_f(v['precision'])} | {_f(v['recall'])} | {_f(v['f1'])} | {v['tp']} | {v['fp']} | {v['fn']} |")
        h = a["medical_history_combined_strict"]
        L += ["", f"Medical history (4 sub-categories pooled): P {_f(h['precision'])} R {_f(h['recall'])} F1 {_f(h['f1'])}.", "",
              "### Clinical metrics", "",
              f"* Vital sign accuracy: {_f(a['vital_signs']['accuracy'], True)} over {a['vital_signs'].get('gold_vitals', 0)} gold vitals (name found {_f(a['vital_signs']['name_found_rate'], True)}).",
              f"* Speaker attribution accuracy: {_f(a['speaker_attribution']['accuracy'], True)} over {a['speaker_attribution']['denominator_evaluated']} matched entities "
              f"(excluded: {a['speaker_attribution'].get('records_excluded_unknown_speaker', 0)} records with an unknown speaker, {a['speaker_attribution'].get('entities_excluded_unknown_or_unreliable', 0)} entities).",
              f"* Negation: {_f(a['negation_polarity']['gold_negatives_correct_rate'], True)} of gold negative findings reproduced; polarity flips: "
              f"{a['negation_polarity'].get('polarity_flip_negative_reported_as_present', 0)} (negative reported as present), {a['negation_polarity'].get('polarity_flip_present_reported_as_negative', 0)} (present reported as negative).",
              f"* Evidence grounding (of {a['evidence_grounding']['predicted_entities_evaluated']} predicted entities): strict {_f(a['evidence_grounding']['grounded_strict_rate'], True)}, "
              f"grounded incl. lenient {_f(a['evidence_grounding']['grounded_lenient_or_better_rate'], True)}, partially supported {_f(a['evidence_grounding']['partially_supported_rate'], True)}, unsupported {_f(a['evidence_grounding']['unsupported_rate'], True)}.",
              f"* Unsupported claims: {a['unsupported_claims']['unsupported_claims']} of {a['unsupported_claims']['predicted_entities']} predicted entities "
              f"({_f(a['unsupported_claims']['unsupported_claim_rate_of_predictions'], True)}); {a['unsupported_claims']['extra_but_transcript_supported']} further FPs are transcript-supported.", "",
              "### Attribute accuracy (matched entities)", "", "| Attribute | Accuracy (gold non-null) | n | False-attribute rate (gold null) | n |", "|---|---|---|---|---|"]
        for k, v in a["attributes"]["requested"].items():
            L.append(f"| {k} | {_f(v['accuracy'], True)} | {v['denominator_gold_nonnull_matched']} | {_f(v['false_attribute_rate'], True)} | {v['denominator_gold_null_matched']} |")
        L.append("")
    p = r["performance"]
    L += ["## Performance", "", f"* Latency per encounter (s): {p['latency_seconds']}", f"* Completion tokens: {p['completion_tokens']}", f"* Prompt tokens: {p['prompt_tokens']}",
          f"* Tokens/second: {p['tokens_per_second']}", f"* Total generation time: {p['total_latency_hours']} h; finish reasons {p['finish_reason']}; repetition flagged in {p['degenerate_repetition_flagged']} outputs.", "",
          "## By complexity (end-to-end, strict micro)", "", "| Complexity | Encounters | Valid JSON | P | R | F1 |", "|---|---|---|---|---|---|"]
    for k, v in r["breakdown"]["complexity"].items():
        m = v["strict_micro"]
        L.append(f"| {k} | {v['encounters']} | {v['valid_json']} | {_f(m['precision'])} | {_f(m['recall'])} | {_f(m['f1'])} |")
    L += ["", "## By specialty (end-to-end, strict micro)", "", "| Specialty | Encounters | Valid JSON | P | R | F1 |", "|---|---|---|---|---|---|"]
    for k, v in r["breakdown"]["specialty"].items():
        m = v["strict_micro"]
        L.append(f"| {k} | {v['encounters']} | {v['valid_json']} | {_f(m['precision'])} | {_f(m['recall'])} | {_f(m['f1'])} |")
    L += ["", "## Definitions", ""] + [f"* **{k}**: {v}" for k, v in r["metric_definitions"].items()]
    L += ["", "Automated evaluation only; scores reflect lexical/normalised matching to the frozen labels and are not a clinical-quality judgement."]
    return "\n".join(L) + "\n"
