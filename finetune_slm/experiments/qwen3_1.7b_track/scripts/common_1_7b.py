"""Qwen3-1.7B track: shared constants and imports.  Run every script with the project's OpenVINO environment:
    <repo>/direct_inference_baseline/experiments/EXP_002_QWEN3_0.6B_GPU_DIRECT/env_openvino/Scripts/python.exe -B -s <script>
(after the approved rename the path is the same through the compatibility junction, see ../README.md "Recreating the junction").

The 0.6B research code is used READ-ONLY, always through the stable package name `direct_inference_baseline` (the junction), so that exactly one copy of each module exists
in a process.  Nothing in the 0.6B track is written by the 1.7B track."""
import hashlib
import json
import sys
import types
from pathlib import Path

sys.dont_write_bytecode = True
try:
    import dotenv  # noqa: F401
except ImportError:                               # the isolated OpenVINO env has no python-dotenv; the existing code only calls load_dotenv()
    sys.modules["dotenv"] = types.SimpleNamespace(load_dotenv=lambda *a, **k: False)

TRACK = Path(__file__).resolve().parents[1]
ROOT = TRACK.parent
LEGACY = ROOT / "direct_inference_baseline"                       # 0.6B package + experiments (junction to direct_inference_0_6B after the rename)
EXP4 = LEGACY / "experiments" / "EXP_004_QWEN3_0.6B_PROMPT_ENGINEERING"
EXP3 = LEGACY / "experiments" / "EXP_003_QWEN3_0.6B_OPENVINO_GPU_DIRECT"
EXP6 = LEGACY / "experiments" / "EXP_006_S1_SIMPLIFIED_EXTRACTION"

MODEL_ID = "Qwen/Qwen3-1.7B"
REVISION = "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e"
HF_CACHE = TRACK / "models" / "hf_cache"
OV_MODEL_DIR = TRACK / "models" / "Qwen3-1.7B-ov-fp16"
CONVERSION_RECORD = TRACK / "manifests" / "CONVERSION_RECORD_Qwen3-1.7B.json"
MAX_NEW_TOKENS = 4096                                              # approved initial value (the 0.6B runs used 6144; disclosed in the reports)
P00_PROMPT_SOURCE = LEGACY / "prompts" / "direct_extraction_prompt.txt"
P00_EXPECTED_SHA = "78c5ab95d0019d0b3c6801ae17f7fa29477dde37d123ecd4fda946e3dd14f604"   # identical to EXP_004/prompts/P00_original_baseline.txt

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(EXP4 / "experiments"))
import common as C4  # noqa: E402  (EXP_004 shared setup, imported read-only)
import dev_guard as G  # noqa: E402  (development-only dataset guard + StrictAccessSpy)
from direct_inference_baseline.config import settings as S  # noqa: E402

SPLIT = C4.SPLIT
PROMPT_DEV_IDS = SPLIT["prompt_dev_ids"]


def sha256_file(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write_json(p, obj):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")
