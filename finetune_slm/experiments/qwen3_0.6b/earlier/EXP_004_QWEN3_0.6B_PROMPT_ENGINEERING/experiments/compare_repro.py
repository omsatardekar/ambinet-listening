"""Byte-level comparison of the P00 reproducibility re-run against the original EXP_003 raw outputs (no labels)."""
import hashlib, json, pathlib
E4 = pathlib.Path(__file__).resolve().parents[1]; E3 = E4.parent / "EXP_003_QWEN3_0.6B_OPENVINO_GPU_DIRECT"
rows = {}
for f in sorted((E4 / "outputs/P00_repro3/raw_predictions/P00_repro3").glob("encounter_*.json")):
    new = json.loads(f.read_text(encoding="utf-8"))
    src = E3 / "raw_predictions/exp_003_dev_remaining_95" / f.name
    if not src.exists():
        src = E3 / "raw_predictions/exp_003_dev_smoke_5" / f.name
    old = json.loads(src.read_text(encoding="utf-8"))
    a, b = old["response_text"], new["response_text"]
    n = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), None if len(a) == len(b) else min(len(a), len(b)))
    rows[f.stem] = {"identical_bytes": a == b, "sha256_old": hashlib.sha256(a.encode()).hexdigest()[:16], "sha256_new": hashlib.sha256(b.encode()).hexdigest()[:16],
                    "chars_old": len(a), "chars_new": len(b), "first_difference_char": n, "tokens_old": old.get("generation", {}).get("completion_tokens"), "tokens_new": new.get("generation", {}).get("completion_tokens"),
                    "source_run": src.parent.name}
out = {"ids": list(rows), "identical": sum(r["identical_bytes"] for r in rows.values()), "n": len(rows), "per_encounter": rows}
(E4 / "evaluation/P00_repro3_comparison.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
print(json.dumps(out, indent=1))
