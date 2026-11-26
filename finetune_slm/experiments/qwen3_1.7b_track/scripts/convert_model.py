"""Converts the verified Qwen3-1.7B snapshot to OpenVINO FP16 with optimum-intel (same command family as EXP_002), measuring wall time and peak memory, and writes
manifests/CONVERSION_RECORD_Qwen3-1.7B.json (source and converted file hashes, tools, command, timing, peak memory).  Offline (HF_HUB_OFFLINE=1): only the verified local snapshot is used.
usage: python -B -s convert_model.py"""
import datetime
import hashlib
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common_1_7b as C  # noqa: E402

snap = C.HF_CACHE / "models--Qwen--Qwen3-1.7B" / "snapshots" / C.REVISION
ver = json.loads((C.TRACK / "manifests" / "DOWNLOAD_VERIFICATION_Qwen3-1.7B.json").read_text(encoding="utf-8"))
assert ver["verified"] and ver["expected_revision"] == C.REVISION, "download must be verified first"
assert not C.OV_MODEL_DIR.exists() or not any(C.OV_MODEL_DIR.iterdir()), "output directory is not empty; refusing to overwrite"
exe = Path(sys.executable).parent / "optimum-cli.exe"
cmd = [str(exe), "export", "openvino", "--model", str(snap), "--task", "text-generation-with-past", "--weight-format", "fp16", str(C.OV_MODEL_DIR)]
env = dict(os.environ, HF_HUB_OFFLINE="1", PYTHONIOENCODING="utf-8", HF_HOME=str(C.HF_CACHE.parent / "hf_home"))
log = C.TRACK / "experiments" / "EXP_001_DIRECT_INFERENCE" / "logs" / "conversion.log"
samples = {"peak_system_used_mb": 0.0, "min_system_available_mb": 1e9, "peak_tree_rss_mb": 0.0}
stop = threading.Event()


def sample(proc):
    try:
        p = psutil.Process(proc.pid)
    except psutil.Error:
        return
    while not stop.is_set():
        vm = psutil.virtual_memory()
        samples["peak_system_used_mb"] = max(samples["peak_system_used_mb"], (vm.total - vm.available) / 2**20)
        samples["min_system_available_mb"] = min(samples["min_system_available_mb"], vm.available / 2**20)
        try:
            rss = sum(x.memory_info().rss for x in [p] + p.children(recursive=True)) / 2**20
            samples["peak_tree_rss_mb"] = max(samples["peak_tree_rss_mb"], rss)
        except psutil.Error:
            pass
        stop.wait(1.0)


t0 = time.perf_counter()
start = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
with open(log, "w", encoding="utf-8") as lf:
    proc = subprocess.Popen(cmd, stdout=lf, stderr=subprocess.STDOUT, env=env)
    th = threading.Thread(target=sample, args=(proc,), daemon=True)
    th.start()
    rc = proc.wait()
    stop.set()
    th.join(timeout=3)
wall = round(time.perf_counter() - t0, 1)


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 22), b""):
            h.update(c)
    return h.hexdigest()


rec = {"track": "direct_inference_1_7B", "source_model": C.MODEL_ID, "source_revision": C.REVISION, "source_download_verification": "manifests/DOWNLOAD_VERIFICATION_Qwen3-1.7B.json",
       "source_files_sha256": {n: e["sha256"] for n, e in ver["files"].items()}, "source_weight_dtype": "bfloat16 (config torch_dtype=bfloat16)",
       "converted_precision": "FP16 weights (--weight-format fp16, no int8/int4 quantisation); bf16 -> fp16 as in EXP_002",
       "export_command": "optimum-cli export openvino --model <verified local snapshot> --task text-generation-with-past --weight-format fp16 models/Qwen3-1.7B-ov-fp16 (HF_HUB_OFFLINE=1)",
       "start_local": start, "exit_code": rc, "conversion_wall_seconds": wall, "memory_during_conversion": {k: round(v) for k, v in samples.items()}, "log": "experiments/EXP_001_DIRECT_INFERENCE/logs/conversion.log"}
try:
    import openvino
    from importlib.metadata import version
    rec["tools"] = {"openvino": openvino.get_version(), "optimum-intel": version("optimum-intel"), "optimum": version("optimum"), "transformers": version("transformers"), "nncf": version("nncf"), "python": sys.version.split()[0]}
except Exception as e:  # noqa: BLE001
    rec["tools"] = {"error": str(e)}
if rc == 0 and C.OV_MODEL_DIR.exists():
    rec["converted_files"] = {p.name: {"bytes": p.stat().st_size, "sha256": sha(p)} for p in sorted(C.OV_MODEL_DIR.iterdir()) if p.is_file()}
C.write_json(C.CONVERSION_RECORD, rec)
print(json.dumps({k: v for k, v in rec.items() if k not in ("source_files_sha256", "converted_files")}, indent=1))
sys.exit(rc)
