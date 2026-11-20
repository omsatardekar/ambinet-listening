"""Does the new evaluator reproduce the measurements already documented from the old runs? (read-only; no inference)

Documented references (from evaluations/p00_p01_audit/PILOT_REFERENCE_METRICS.json and the P02 v2.2 proposal, section 2):
  * P00 and P01 strict micro counts on the 8 pilot ids, failed outputs scored as zero predictions
  * P02 v2.1, encounter 00168: gold/actual fact counts per section and the evidence-block findings
  * P02 v2.1, three records: output tokens, finish reasons
Comparable only where the quantity exists in the old outputs: the old runs are FULL-format outputs, so they exercise --format full."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evaluate_v22 import evaluate, load_run                                  # noqa: E402
from v22_common import EXP, PKG, TRACK, read_json                           # noqa: E402

PILOT = read_json(TRACK / "manifests" / "PILOT8_P02_IDS.json")["ids"]
REF = read_json(EXP / "evaluations" / "p00_p01_audit" / "PILOT_REFERENCE_METRICS.json")
E1 = TRACK / "experiments" / "EXP_001_DIRECT_INFERENCE" / "outputs"
E2 = EXP / "outputs"
checks = []


def check(name, got, want):
    ok = got == want
    checks.append({"check": name, "got": got, "documented": want, "match": ok})
    print(("PASS " if ok else "FAIL ") + name, "| got", got, "| documented", want)


for run, (p, f, r) in {"P00": (E1 / "parsed/P00_direct_dev50", E1 / "failed/P00_direct_dev50", E1 / "raw/P00_direct_dev50"),
                       "P01": (E2 / "parsed/P01_schema_guided_dev50", E2 / "failed/P01_schema_guided_dev50", E2 / "raw/P01_schema_guided_dev50")}.items():
    A = evaluate(load_run(p, f, r, PILOT), "full", label=f"{run} on the 8 pilot ids")
    m = A["entities_tier1_all_records_failed_as_zero"]["micro"]
    want = REF["micro"][run]["as_scored"]
    check(f"{run} strict micro tp/fp/fn on 8 pilot ids (failed = zero predictions)", [m["tp"], m["fp"], m["fn"]], [want["tp"], want["fp"], want["fn"]])
    check(f"{run} precision/recall/F1", [round(m["precision"], 4), round(m["recall"], 4), round(m["f1"], 4)],
          [round(want["precision"], 4), round(want["recall"], 4), round(want["f1"], 4)])
    status = {s["id"]: s["status"] for s in A["_scored"]}
    check(f"{run} parsed/failed status per id", {k: ("parsed" if v == "parsed" else "FAILED") for k, v in status.items()}, REF["status"][run])

V21 = E2 / "parsed/P02_v2_1_pilot8"
A = evaluate(load_run(V21, E2 / "failed/P02_v2_1_pilot8", E2 / "raw/P02_v2_1_pilot8", PILOT[:3]), "full", label="P02 v2.1, the 3 records that ran")
sc = {s["id"]: s for s in A["_scored"]}
s168 = sc["00168"]
documented_counts = {"symptoms": (3, 1), "negative_findings": (7, 0), "review_of_systems": (1, 0), "clinical_conditions": (1, 0), "clinical_assessment": (2, 1),
                     "clinical_actions": (6, 1), "clinical_uncertainties": (1, 0)}
for cat, want in documented_counts.items():
    check(f"00168 P02 v2.1 {cat}: gold/pred facts", (s168["n_gold"][cat], s168["n_pred"][cat]), want)
eb = s168["evidence_block"]
for key, want in {"evidence_records": 36, "fact_references": 48, "distinct_fact_references": 18, "refs_that_are_transcript_segment_ids": 48,
                  "refs_resolving_to_model_own_evidence_record": 0, "text_mismatch": 2, "speaker_mismatch": 0, "start_timestamp_mismatch": 36, "end_timestamp_mismatch": 35}.items():
    check(f"00168 P02 v2.1 evidence block: {key}", eb[key], want)
check("00168 P02 v2.1 transcript segments without an evidence record", eb["transcript_segments_without_an_evidence_record"], ["SEG0006"])
check("3 records: status", [sc[i]["status"] for i in PILOT[:3]], ["parsed", "failed", "failed"])
check("3 records: finish reasons", [sc[i]["tokens"]["finish_reason"] for i in PILOT[:3]], ["stop", "length", "length"])
check("3 records: completion tokens", [sc[i]["tokens"]["completion_tokens"] for i in PILOT[:3]], [3789, 4096, 4096])
check("3 records: generation seconds (rounded)", [round(sc[i]["tokens"]["latency_seconds"]) for i in PILOT[:3]], [1597, 1803, 1759])
share = eb["evidence_block_share_of_output_chars"]
check("00168 evidence block share of parsed output characters, rounded to 2 dp (documented 66%)", round(share, 2), 0.66)
rep = {"checks": checks, "all_match": all(c["match"] for c in checks), "n_checks": len(checks), "n_match": sum(c["match"] for c in checks),
       "note": "P02 v2.1 entity precision/recall for these three records was never documented (the frozen evaluation was not run), so nothing to compare; the new evaluator's value is stored in p02_v2_1_3records_new_evaluator.json for the record."}
out = PKG / "derived"
out.mkdir(exist_ok=True)
(out / "reproduction_of_documented_measurements.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False), encoding="utf-8")
for v in [A]:
    v.pop("_scored", None)
(out / "p02_v2_1_3records_new_evaluator.json").write_text(json.dumps(A, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"\n{rep['n_match']}/{rep['n_checks']} documented measurements reproduced")
