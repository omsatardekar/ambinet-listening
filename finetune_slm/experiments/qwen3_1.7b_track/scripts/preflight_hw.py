"""Read-only hardware / environment preflight for the Qwen3-1.7B track.  No model is loaded.  Writes manifests/HARDWARE_ENV_PREFLIGHT.json.
usage: python -B -s preflight_hw.py"""
import datetime
import json
import platform
import shutil
import sys
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common_1_7b as C  # noqa: E402

import openvino as ov  # noqa: E402
import openvino_genai  # noqa: E402

core = ov.Core()
devs = core.available_devices
gpu = {}
if "GPU" in devs:
    for p in ("FULL_DEVICE_NAME", "DEVICE_TYPE", "GPU_DEVICE_TOTAL_MEM_SIZE", "GPU_UARCH_VERSION", "OPTIMAL_BATCH_SIZE", "DEVICE_ARCHITECTURE", "GPU_EXECUTION_UNITS_COUNT", "GPU_MEMORY_STATISTICS"):
        try:
            gpu[p] = str(core.get_property("GPU", p))
        except Exception as e:  # noqa: BLE001
            gpu[p] = f"n/a ({type(e).__name__})"
vm = psutil.virtual_memory()
du = {d: round(shutil.disk_usage(d).free / 2**30, 1) for d in ("C:\\", "D:\\")}
try:
    import optimum.intel as oi  # noqa: F401
    import optimum
    import transformers
    vers = {"optimum": getattr(optimum, "__version__", "?"), "transformers": transformers.__version__}
    from importlib.metadata import version
    vers["optimum-intel"] = version("optimum-intel")
    vers["nncf"] = version("nncf")
except Exception as e:  # noqa: BLE001
    vers = {"error": str(e)}
cfg_ok = False
snap = None
snaps = list((C.HF_CACHE / "models--Qwen--Qwen3-1.7B" / "snapshots").glob("*")) if (C.HF_CACHE / "models--Qwen--Qwen3-1.7B" / "snapshots").exists() else []
if snaps:
    snap = snaps[0]
# memory budget (estimates, to be replaced by measurements)
P = 2.03e9
est = {"fp16_weights_GB": round(P * 2 / 2**30, 2), "kv_cache_per_token_KiB": round(2 * 28 * 8 * 128 * 2 / 1024, 1), "kv_cache_GB_at_4096_prompt+4096_gen": round(2 * 28 * 8 * 128 * 2 * 8192 / 2**30, 2),
       "note": "estimates from the model config; measured values are recorded by the smoke test and the baseline run"}
out = {"time": datetime.datetime.now().astimezone().isoformat(timespec="seconds"), "platform": platform.platform(), "python": sys.version.split()[0], "openvino": ov.get_version(), "openvino_genai": openvino_genai.__version__,
       "available_devices": devs, "gpu": gpu, "ram_total_GB": round(vm.total / 2**30, 2), "ram_available_GB": round(vm.available / 2**30, 2), "disk_free_GB": du, "toolchain": vers,
       "model": C.MODEL_ID, "revision": C.REVISION, "hf_cache": str(C.HF_CACHE), "snapshot_present": str(snap) if snap else None,
       "snapshot_files": sorted(p.name for p in snap.iterdir()) if snap else [], "memory_estimates": est,
       "gate": {"gpu_visible": "GPU" in devs, "ram_available_ge_8GB_for_conversion_and_compile": vm.available / 2**30 >= 8, "d_drive_free_ge_20GB": du["D:\\"] >= 20}}
C.write_json(C.TRACK / "manifests" / "HARDWARE_ENV_PREFLIGHT.json", out)
print(json.dumps(out, indent=1))
