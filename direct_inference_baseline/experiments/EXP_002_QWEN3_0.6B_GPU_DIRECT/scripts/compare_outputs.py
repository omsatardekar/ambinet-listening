import json
from pathlib import Path
R = Path(__file__).resolve().parents[1] / "results"
L = lambda n: json.loads((R / f"gen_{n}.json").read_text(encoding="utf-8"))
t = {n: L(n)["generated_text"] for n in ("gpu_cold_cache", "gpu_warm_cache", "cpu", "hf_fp32_reference")}
ref = t["hf_fp32_reference"]


def common_prefix(a, b):
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n


out = {"lengths_chars": {k: len(v) for k, v in t.items()},
       "identical": {"gpu_cold == gpu_warm": t["gpu_cold_cache"] == t["gpu_warm_cache"], "gpu == ov_cpu": t["gpu_cold_cache"] == t["cpu"],
                     "gpu == hf_fp32": t["gpu_cold_cache"] == ref, "ov_cpu == hf_fp32": t["cpu"] == ref},
       "common_prefix_chars_vs_hf_fp32": {k: common_prefix(v, ref) for k, v in t.items()},
       "common_prefix_chars_gpu_vs_ov_cpu": common_prefix(t["gpu_cold_cache"], t["cpu"])}
if t["gpu_cold_cache"] != ref:
    p = common_prefix(t["gpu_cold_cache"], ref)
    out["first_divergence_gpu_vs_hf"] = {"gpu": t["gpu_cold_cache"][max(0, p - 30):p + 40], "hf": ref[max(0, p - 30):p + 40]}
if t["cpu"] != ref:
    p = common_prefix(t["cpu"], ref)
    out["first_divergence_ov_cpu_vs_hf"] = {"ov_cpu": t["cpu"][max(0, p - 30):p + 40], "hf": ref[max(0, p - 30):p + 40]}
(R / "output_comparison.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(out, indent=2, ensure_ascii=True))
print("--- texts ---")
for k, v in t.items():
    print(k, "::", repr(v).encode("ascii", "backslashreplace").decode())
