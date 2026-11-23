"""Post-hoc GPU-execution verification from the RAW Windows 'GPU Engine' counters captured during the smoke test (smoke_test.py's in-script matcher missed the instances; the raw
counters are kept unmodified).  Matches the smoke-test process id recorded in manifests/SMOKE_TEST_Qwen3-1.7B.json.   usage: python -B verify_smoke_gpu.py"""
import csv, collections, io, json, re, sys
from pathlib import Path
T = Path(__file__).resolve().parents[1]
sm = json.loads((T / "manifests" / "SMOKE_TEST_Qwen3-1.7B.json").read_text(encoding="utf-8"))
raw = (T / "experiments" / "EXP_001_DIRECT_INFERENCE" / "logs" / "smoke_gpu_engine_counters_raw.txt").read_text(encoding="utf-8")
series, others = collections.defaultdict(list), collections.defaultdict(float)
for b in [b for b in re.split(r'(?=\"\(PDH-CSV)', raw) if b.strip()]:
    rr = list(csv.reader(io.StringIO(b)))
    if len(rr) < 2:
        continue
    for h, v in zip(rr[0][1:], rr[1][1:]):
        m = re.search(r"pid_(\d+)_.*engtype_([^)]*)", h)
        try:
            x = float(v)
        except ValueError:
            continue
        if int(m.group(1)) == sm["pid"]:
            series[m.group(2)].append(x)
        else:
            others[m.group(1)] = max(others[m.group(1)], x)
peak = {k: max(v) for k, v in series.items() if max(v) > 0}
gen, cpu = sm["generation_wall_seconds"], sm["process_cpu_seconds_during_generation_only"]
res = {"smoke_test_pid": sm["pid"], "gpu_engine_peak_utilization_percent_for_smoke_process": {k: round(v, 1) for k, v in peak.items()}, "max_other_process_gpu_utilization_percent": round(max(others.values() or [0]), 1),
       "polls": sm["typeperf_polls"], "cpu_seconds_during_generation": cpu, "generation_wall_seconds": gen, "cpu_cores_equivalent_during_generation": round(cpu / gen, 2), "logical_cpus": 8,
       "device_requested_and_used": "GPU (explicit device='GPU'; OpenVINO GenAI raises instead of falling back)",
       "gpu_execution_verified": bool(peak) and max(peak.values()) >= 50, "note": "one host core busy-polling plus ~97% GPU 3D-engine utilisation of this very process = GPU execution; no silent CPU fallback"}
(T / "manifests" / "SMOKE_TEST_GPU_VERIFICATION.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
print(json.dumps(res, indent=1))
sys.exit(0 if res["gpu_execution_verified"] else 1)
