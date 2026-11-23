"""Compares EXP_003 with the archived EXP_001 results (read-only). Writes evaluation/comparison_with_EXP_001.json; the narrative report is written separately."""
import json
from pathlib import Path

from common import EXP1, EXP3, EXPERIMENT_ID, write_json

e1 = json.loads((EXP1 / "reports" / "evaluation_report.json").read_text(encoding="utf-8"))
e3 = json.loads((EXP3 / "evaluation" / EXPERIMENT_ID / "evaluation_report.json").read_text(encoding="utf-8"))
m1 = json.loads((EXP1 / "reports" / "run_manifest.json").read_text(encoding="utf-8"))
m3 = json.loads((EXP3 / "run_manifest.json").read_text(encoding="utf-8"))
ids = list(m3["records"])


def diff(a, b, path=""):
    """All leaf differences between two JSON structures (floats compared exactly)."""
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            out += diff(a.get(k, "<missing>"), b.get(k, "<missing>"), f"{path}/{k}")
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            out += diff(x, y, f"{path}[{i}]")
    elif a != b:
        out.append({"path": path, "exp001": a, "exp003": b})
    return out


def common_prefix(a, b):
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n


sections = ["valid_only", "end_to_end", "breakdown", "json_and_schema"]
quality_diffs = {s: diff(e1[s], e3[s]) for s in sections}
per = {}
for eid in ids:
    r1 = json.loads((EXP1 / "predictions" / "raw_predictions" / f"encounter_{eid}.json").read_text(encoding="utf-8"))
    r3 = json.loads((EXP3 / "raw_predictions" / EXPERIMENT_ID / f"encounter_{eid}.json").read_text(encoding="utf-8"))
    t1, t3 = r1["response_text"], r3["response_text"]
    p1 = json.loads((EXP1 / "predictions" / "parsed_predictions" / f"encounter_{eid}.json").read_text(encoding="utf-8"))
    p3 = json.loads((EXP3 / "parsed_predictions" / EXPERIMENT_ID / f"encounter_{eid}.json").read_text(encoding="utf-8"))
    a, b = m1["records"][eid], m3["records"][eid]
    per[eid] = {"input_tokens": [a["prompt_tokens"], b["prompt_tokens"]], "output_tokens": [a["completion_tokens"], b["completion_tokens"]],
                "latency_seconds": [a["latency_seconds"], b["latency_seconds"]], "raw_text_identical": t1 == t3, "parsed_json_identical": p1 == p3,
                "raw_chars": [len(t1), len(t3)], "common_prefix_chars": common_prefix(t1, t3),
                "first_divergence": None if t1 == t3 else {"exp001": t1[max(0, common_prefix(t1, t3) - 40):common_prefix(t1, t3) + 60],
                                                           "exp003": t3[max(0, common_prefix(t1, t3) - 40):common_prefix(t1, t3) + 60]},
                "top_level_keys_equal": list(p1) == list(p3), "finish_reason": [a["finish_reason"], b["finish_reason"]]}
perf1, perf3 = e1["performance"], e3["performance"]
out = {"encounters": ids, "evaluation_sections_with_any_difference": {s: len(d) for s, d in quality_diffs.items()},
       "evaluation_differences_sample": {s: d[:20] for s, d in quality_diffs.items() if d},
       "headline": {"exp001": e1["headline"], "exp003": e3["headline"]}, "per_encounter": per,
       "performance": {"exp001": {k: perf1[k] for k in ("latency_seconds", "completion_tokens", "prompt_tokens", "tokens_per_second", "total_latency_hours")},
                       "exp003": {k: perf3[k] for k in ("latency_seconds", "completion_tokens", "prompt_tokens", "tokens_per_second", "total_latency_hours")}},
       "model": {"exp001": m1["model"], "exp003": m3["model"]}, "prompt_sha256": [m1["prompt_sha256"], m3["prompt_sha256"]],
       "encounter_ids_equal": sorted(m1["records"]) == sorted(m3["records"])}
write_json(EXP3 / "evaluation" / "comparison_with_EXP_001.json", out)
print(json.dumps({"diff_counts": out["evaluation_sections_with_any_difference"], "headline": out["headline"]}, indent=1))
for eid, p in per.items():
    print(eid, "tokens", p["output_tokens"], "latency", p["latency_seconds"], "raw_identical", p["raw_text_identical"], "parsed_identical", p["parsed_json_identical"], "prefix", p["common_prefix_chars"], "/", p["raw_chars"])
for s, d in quality_diffs.items():
    print(s, len(d), [x["path"] for x in d[:8]])
