"""EXP_003 shared setup. Imports the EXISTING module code read-only (no copies, no edits) and redirects ALL of its output directories into EXP_003.
Run with the isolated EXP_002 OpenVINO environment:  env_openvino\\Scripts\\python.exe -I -B <script>"""
import builtins
import hashlib
import json
import sys
import types
from pathlib import Path

sys.dont_write_bytecode = True                       # never write .pyc files into the existing module folders
try:                                                  # the existing settings module imports python-dotenv; it is not installed in env_openvino
    import dotenv  # noqa: F401
except ImportError:                                   # stub: only load_dotenv is used, and no .env value is needed for local OpenVINO inference
    sys.modules["dotenv"] = types.SimpleNamespace(load_dotenv=lambda *a, **k: False)

EXP3 = Path(__file__).resolve().parents[1]
ROOT = EXP3.parents[2]
MODULE = ROOT / "direct_inference_baseline"
EXP1 = MODULE / "experiments" / "EXP_001_QWEN3_0.6B_CPU_BASELINE"
EXP2 = MODULE / "experiments" / "EXP_002_QWEN3_0.6B_GPU_DIRECT"
OV_MODEL_DIR = EXP2 / "models" / "Qwen3-0.6B-ov-fp16"
CACHE_DIR = EXP3 / "ov_cache"
EXPERIMENT_ID = "exp_003_dev_smoke_5"
SMOKE_IDS = ["00021", "00032", "00034", "00035", "00037"]
MAX_NEW_TOKENS = 6144
SOURCE_REVISION = "c1899de289a04d12100db370d81485cdf75e47ca"

sys.path.insert(0, str(ROOT))
from direct_inference_baseline.config import settings as S  # noqa: E402

# redirect every output location of the existing code into EXP_003 (inputs/labels/dataset paths are untouched)
S.RAW_DIR, S.PARSED_DIR, S.FAILED_DIR, S.REPORT_DIR = (EXP3 / n for n in ("raw_predictions", "parsed_predictions", "failed_predictions", "evaluation"))


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
        import re
        return [p for p in self.opened if re.search(r"output[\\/]labels|scenario_blueprints|blueprint", p, re.I)]
