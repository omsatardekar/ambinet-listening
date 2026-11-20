"""One-command setup of the LOCAL extraction model (Qwen3-0.6B, OpenVINO) on a new machine. Cross-platform (Windows, Linux, macOS).

    python -m clinical_extraction.setup_local_model            # from the repository root, with any Python 3.10 to 3.13

What it does (each step prints what happened; nothing is downloaded except Python packages and, if needed, the Git-LFS model weights):
  1. creates the separate environment  .venv-extraction  (the backend venv is never touched)
  2. installs clinical_extraction/requirements-extraction.txt into it
  3. makes sure the 1.2 GB model weights are real files (Git LFS), running `git lfs pull` for that folder if they are still pointers
  4. runs the worker's --check: frozen prompt hash, model file sizes + SHA-256, the OpenVINO import and the device that will be used (GPU if present, else CPU)
After it succeeds nothing has to be configured: the backend finds .venv-extraction by itself (EXTRACTION_PYTHON is only needed for a custom location).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENV = ROOT / ".venv-extraction"
REQUIREMENTS = ROOT / "clinical_extraction" / "requirements-extraction.txt"
MODEL_DIR = ROOT / "direct_inference_baseline" / "experiments" / "EXP_002_QWEN3_0.6B_GPU_DIRECT" / "models" / "Qwen3-0.6B-ov-fp16"
WORKER = ROOT / "clinical_extraction" / "h1_worker.py"


def step(msg: str) -> None:
    print(f"\n== {msg}", flush=True)


def run(cmd: list[str], **kw) -> int:
    print("  $", " ".join(str(c) for c in cmd), flush=True)
    return subprocess.call([str(c) for c in cmd], **kw)


def venv_python() -> Path:
    return VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def main() -> int:
    if not (3, 10) <= sys.version_info[:2] <= (3, 13):
        print(f"Python {sys.version_info.major}.{sys.version_info.minor} is not supported by the pinned OpenVINO packages; use Python 3.10 to 3.13 (3.12 is what the project was tested with).")
        return 2
    step("1/4 environment")
    if not venv_python().exists():
        if run([sys.executable, "-m", "venv", VENV]) != 0:
            return 2
    else:
        print("  .venv-extraction already exists; reusing it")
    step("2/4 packages")
    if run([venv_python(), "-m", "pip", "install", "--disable-pip-version-check", "-r", REQUIREMENTS]) != 0:
        print("Package installation failed. Check the internet connection and that this Python version has wheels for the pinned versions.")
        return 2
    step("3/4 model weights (Git LFS)")
    weights = MODEL_DIR / "openvino_model.bin"
    if not weights.exists() or weights.stat().st_size < 1024:
        include = str(MODEL_DIR.relative_to(ROOT)).replace("\\", "/") + "/*"
        if run(["git", "lfs", "install"], cwd=ROOT) != 0 or run(["git", "lfs", "pull", f"--include={include}"], cwd=ROOT) != 0:
            print("Could not fetch the weights with Git LFS. Install Git LFS (https://git-lfs.com) and run:  git lfs pull")
            print(f"or copy the folder {MODEL_DIR.relative_to(ROOT)} from the project owner.")
            return 2
    print(f"  openvino_model.bin: {weights.stat().st_size:,} bytes" if weights.exists() else "  openvino_model.bin missing")
    step("4/4 check (loads no model)")
    check_dir = ROOT / "extraction_data" / "check" / "jobs" / "setup"
    code = run([venv_python(), "-B", "-s", WORKER, "--out", check_dir, "--check"])
    result = check_dir / "result.json"
    info = json.loads(result.read_text(encoding="utf-8")) if result.exists() else {}
    if code != 0 or not info.get("ok"):
        print("\nCheck FAILED:", info.get("message") or info)
        return 2
    print(f"\nReady. Device that will be used: {info.get('device')}. Start the backend as usual; the extraction panel now runs the model on this computer.")
    print("Optional: set EXTRACTION_DEVICE=CPU or GPU in .env to force a device. Run the unit tests: python -m pytest clinical_extraction/tests -q")
    return 0


if __name__ == "__main__":
    sys.exit(main())
