"""Builds the interim markdown report (reads only the interim snapshot's evaluator output plus the archived EXP_001 / smoke reports)."""
import glob, json, pathlib
E3 = pathlib.Path(__file__).resolve().parents[1]
snap = sorted(glob.glob(str(E3 / "evaluation" / "interim_*")))[-1]
L = lambda p: json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
I = L(glob.glob(snap + "/evaluation/*/evaluation_report.json")[0])
S5 = L(E3 / "evaluation/exp_003_dev_smoke_5/evaluation_report.json")
E1 = L(glob.glob(str(E3.parent / "EXP_001*/reports/evaluation_report.json"))[0])
sel = L(snap + "/interim_selection.json")
f = lambda x: "n/a" if x is None else f"{x:.3f}"
def row(r):
    e = r["end_to_end"]; m = e["strict"]["micro"]; M = e["strict"]["macro"]; j = r["json_and_schema"]; p = r["performance"]
    return dict(n=r["coverage"]["attempted"], valid=j["valid_json"], inval=j["attempted"] - j["valid_json"], trunc=j["truncated_rate"], schema=j["schema_compliant_among_valid_json"],
        comp=j["required_field_completeness_valid_json"], tp=m["tp"], fp=m["fp"], fn=m["fn"], P=m["precision"], R=m["recall"], F=m["f1"], MF=M["f1"],
        vit=e["vital_signs"]["accuracy"], spk=e["speaker_attribution"]["accuracy"], ev=e["evidence_grounding"]["unsupported_rate"], uc=e["unsupported_claims"]["unsupported_claim_rate_of_predictions"],
        lat=p["latency_seconds"]["mean"], tps=p["tokens_per_second"]["mean"], out=p["completion_tokens"]["mean"])
c = {"Interim EXP_003 (62, excl. smoke 5)": row(I), "EXP_003 smoke (5)": row(S5), "EXP_001 CPU (5)": row(E1)}
names = list(c)
lines = []
w = lines.append
w(f"# EXP_003 INTERIM evaluation - snapshot {sel['timestamp_utc']}\n")
w("**INTERIM RESULT ONLY. This is not the final 100-record development evaluation.** The inference run `exp_003_dev_remaining_95` was still running (not touched); the final evaluation will be produced later by `combine_and_evaluate_dev100.py` and will not overwrite this file.\n")
w(f"## Scope and safety\n* Completed predictions evaluated: **{sel['included_count']}** of the 95 remaining development encounters (the 5 smoke-test encounters are NOT in this number). Skipped as incomplete/partial: {len(sel['skipped_not_complete'])}.")
w("* Selection: only manifest records with final status whose raw (and parsed) JSON files were fully readable were taken; these files were **copied** into this timestamped snapshot (sha256-verified) and the existing evaluator ran on the copy. The live run's folders were only read, never written. Currently running or unanswered encounters are excluded.")
w("* The existing evaluator (`evaluation/evaluation_runner.py`, unmodified) was run in a separate process; labels were opened only there. The inference process never receives labels (its audit is written on completion).")
w("* No prompt, model, decoding, schema, dataset or evaluator change; no new inference.\n")
w("## Headline comparison\n| Metric | " + " | ".join(names) + " |\n|---|" + "---|" * 3)
for lab, k, fmt in [("Predictions evaluated", "n", str), ("Valid JSON", "valid", str), ("Invalid JSON", "inval", str), ("Truncated rate", "trunc", f),
        ("Schema-compliant (of valid)", "schema", f), ("Required-field completeness", "comp", f), ("TP", "tp", str), ("FP", "fp", str), ("FN", "fn", str), ("Micro precision", "P", f), ("Micro recall", "R", f),
        ("Micro F1", "F", f), ("Macro F1", "MF", f), ("Vital-sign accuracy", "vit", f), ("Speaker attribution accuracy", "spk", f), ("Unsupported-evidence rate", "ev", f),
        ("Unsupported-claim rate (of predictions)", "uc", f), ("Mean latency / encounter (s)", "lat", f), ("Mean tokens/s", "tps", f), ("Mean output tokens", "out", f)]:
    w(f"| {lab} | " + " | ".join(fmt(c[n][k]) for n in names) + " |")
w("\n## Category-level strict F1 (interim 62 | smoke 5 | EXP_001 5) with TP/FP/FN for the interim run\n| Category | Interim F1 | TP | FP | FN | P | R | Smoke F1 | EXP_001 F1 |\n|---|---|---|---|---|---|---|---|---|")
for cat, v in I["end_to_end"]["strict"]["per_category"].items():
    g = lambda r: r["end_to_end"]["strict"]["per_category"].get(cat, {}).get("f1")
    w(f"| {cat} | {f(v['f1'])} | {v['tp']} | {v['fp']} | {v['fn']} | {f(v['precision'])} | {f(v['recall'])} | {f(g(S5))} | {f(g(E1))} |")
e = I["end_to_end"]
w(f"\n## Other interim detail\n* Vital signs: {e['vital_signs']['correct']} correct of {e['vital_signs']['gold_vitals']} gold ({e['vital_signs']['accuracy']:.4f}); name found {e['vital_signs']['name_found']}.")
w(f"* Speaker attribution: {e['speaker_attribution']['correct']}/{e['speaker_attribution']['evaluated']} correct.")
g = e["evidence_grounding"]; u = e["unsupported_claims"]
w(f"* Evidence grounding of {g['total']} predicted entities: strict {g['grounded_strict']}, lenient {g['grounded_lenient']}, partial {g['partially_supported']}, unsupported {g['unsupported']}.")
w(f"* Unsupported claims: {u['unsupported_claims']} of {u['predicted_entities']}; extra-but-transcript-supported false positives: {u['extra_but_transcript_supported']}.")
w(f"* Negation: gold negatives {e['negation_polarity']['gold_negatives']}, reproduced 0 correctly, polarity flips {e['negation_polarity']['polarity_flip_negative_reported_as_present']}.")
j = I["json_and_schema"]
w(f"* Schema violations (valid JSON only): {j['violation_kinds']}. Failures by type: {j['failures_by_type']} (no truncations, no empty outputs, no inference errors; all finish_reason=stop).")
w("* The 5 invalid outputs are complete-looking JSON ending normally (not token-limit truncation) but with a syntax error (`Expecting ',' delimiter`) - encounters " + ", ".join(k for k, r in L(snap + "/evaluation/exp_003_dev_remaining_95_interim/run_manifest.json")["records"].items() if r["status"] != "parsed") + ". They are scored as failures; nothing was repaired.")
p = I["performance"]
w(f"\n## Performance (interim)\nMean latency {p['latency_seconds']['mean']:.1f} s (median {p['latency_seconds']['median']:.1f}, max {p['latency_seconds']['max']:.1f}); mean {p['tokens_per_second']['mean']:.2f} tok/s; mean output {p['completion_tokens']['mean']:.0f} tokens; total {p['total_latency_hours']:.2f} h of generation so far.")
w("\n## Interpretation and caveats\n* Interim sample of 62 (valid JSON 57); all numbers will change as the run completes. 'End-to-end' scoring counts the 5 invalid outputs as zero-prediction failures; valid-only scores are in the snapshot's `evaluation_report.json`.\n* Compared with the 5-record baseline, the larger sample shows low-but-nonzero micro F1 and notably better medication/allergy extraction; the 5-record figures were not representative. The 5-record sets are different encounters, so the comparison is indicative, not like-for-like.\n* The model still omits most schema sections (recall ~3%), so schema compliance is 0%.\n* Runtime/format/hardware differ from EXP_001 (Transformers FP32 CPU vs OpenVINO FP16 GPU); on the shared 5 encounters entity metrics were identical.")
out = E3 / "evaluation" / f"INTERIM_report_{sel['timestamp_utc']}.md"
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(out)
