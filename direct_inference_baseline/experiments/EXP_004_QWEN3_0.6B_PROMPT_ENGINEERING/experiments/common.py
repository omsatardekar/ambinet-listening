"""EXP_004 shared setup: imports the EXISTING module code read-only and redirects ALL of its output directories into EXP_004.
Prompt versions are selected per run through S.PROMPT_PATH (the existing runner reads the template from there). Nothing in EXP_001-003 is written.
Run with the isolated EXP_002 OpenVINO environment: env_openvino\\Scripts\\python.exe -B -s <script>"""
import builtins
import hashlib
import json
import re
import sys
import types
from pathlib import Path

sys.dont_write_bytecode = True
try:
    import dotenv  # noqa: F401
except ImportError:
    sys.modules["dotenv"] = types.SimpleNamespace(load_dotenv=lambda *a, **k: False)

EXP4 = Path(__file__).resolve().parents[1]
ROOT = EXP4.parents[2]
MODULE = ROOT / "direct_inference_baseline"
EXP2 = MODULE / "experiments" / "EXP_002_QWEN3_0.6B_GPU_DIRECT"
EXP3 = MODULE / "experiments" / "EXP_003_QWEN3_0.6B_OPENVINO_GPU_DIRECT"
OV_MODEL_DIR = EXP2 / "models" / "Qwen3-0.6B-ov-fp16"
CACHE_DIR = EXP4 / "ov_cache"
MAX_NEW_TOKENS = 6144
SOURCE_REVISION = "c1899de289a04d12100db370d81485cdf75e47ca"
SPLIT = json.loads((EXP4 / "experiments" / "split_v1.json").read_text(encoding="utf-8"))

sys.path.insert(0, str(ROOT))
from direct_inference_baseline.config import settings as S  # noqa: E402


def use_run(run_id: str, prompt_file: str):
    """Point the existing code's output directories at EXP_004/outputs/<run_id>/... and its prompt at prompts/<prompt_file>."""
    base = EXP4 / "outputs" / run_id
    S.RAW_DIR, S.PARSED_DIR, S.FAILED_DIR = (base / n for n in ("raw_predictions", "parsed_predictions", "failed_predictions"))
    S.REPORT_DIR = EXP4 / "evaluation"
    S.PROMPT_PATH = EXP4 / "prompts" / prompt_file
    return base


def sha256_file(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write_json(p, obj):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


class FileAccessSpy:
    """Records every file the process opens so that label / blueprint access can be shown to be zero during inference."""
    def __init__(self):
        self.opened = []

    def __enter__(self):
        self._o, self._t, self._b = builtins.open, Path.read_text, Path.read_bytes
        spy = self

        def o(f, *a, **k):
            spy.opened.append(str(f))
            return spy._o(f, *a, **k)

        def t(p, *a, **k):
            spy.opened.append(str(p))
            return spy._t(p, *a, **k)

        def b(p, *a, **k):
            spy.opened.append(str(p))
            return spy._b(p, *a, **k)
        builtins.open, Path.read_text, Path.read_bytes = o, t, b
        return self

    def __exit__(self, *exc):
        builtins.open, Path.read_text, Path.read_bytes = self._o, self._t, self._b

    def label_or_blueprint_accesses(self):
        return [p for p in self.opened if re.search(r"output[\\/]labels|scenario_blueprints|blueprint", p, re.I)]
