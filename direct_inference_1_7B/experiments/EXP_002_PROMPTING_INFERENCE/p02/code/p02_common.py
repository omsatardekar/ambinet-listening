"""P02 v2.2 shared helpers. Pure standard library: no OpenVINO, no transformers, no model, no network.

Read-only use of the corrected dataset and of the frozen schema / entity matcher. Nothing outside p02/ is ever written by this package.
Labels and transcripts can only be read for the 50 authorised prompt-development ids (validation, locked-test and sealed data are unreachable here)."""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
PKG = HERE.parent                                   # .../EXP_002_PROMPTING_INFERENCE/p02
EXP = PKG.parent
TRACK = EXP.parents[1]                              # .../direct_inference_1_7B
ROOT = TRACK.parent                                 # repository root
DATA = ROOT / "dataset_v2_batch_001_corrected"      # the ONLY dataset these tools read
INPUT_DIR = DATA / "output" / "inputs"
LABEL_DIR = DATA / "output" / "labels"
FROZEN_SCHEMA = DATA / "schema" / "final_label_schema.json"
COMPACT_SCHEMA = PKG / "schema" / "support_schema.json"
FROZEN_IDS_FILE = TRACK / "manifests" / "FROZEN_50_PROMPT_DEV_IDS.json"
ENTITY_MATCHING_PATH = ROOT / "direct_inference_baseline" / "evaluation" / "entity_matching.py"

CHARS_PER_TOKEN = 3.04                              # observed once: 12,460 characters = 4,096 tokens (estimate only)


def read_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8-sig"))


def authorised_ids() -> list[str]:
    d = read_json(FROZEN_IDS_FILE)
    ids = d["ids"] if isinstance(d, dict) else d
    return [i if isinstance(i, str) else i["id"] for i in ids]


def _check_id(eid: str):
    if not re.fullmatch(r"\d{5}", str(eid)):
        raise ValueError(f"bad encounter id {eid!r}")
    if eid not in set(authorised_ids()):
        raise PermissionError(f"encounter {eid} is not one of the 50 authorised prompt-development ids; this tool refuses to read it")


def load_transcript(eid: str) -> dict:
    _check_id(eid)
    return read_json(INPUT_DIR / f"encounter_{eid}.json")


def load_gold(eid: str) -> dict:
    _check_id(eid)
    return read_json(LABEL_DIR / f"encounter_{eid}.json")


_FROZEN = None
_COMPACT = None
_EM = None


def frozen_schema() -> dict:
    global _FROZEN
    if _FROZEN is None:
        _FROZEN = read_json(FROZEN_SCHEMA)
    return _FROZEN


def compact_schema() -> dict:
    global _COMPACT
    if _COMPACT is None:
        _COMPACT = read_json(COMPACT_SCHEMA)
    return _COMPACT


def entity_matching():
    """The frozen strict matcher, loaded from its file as a pure-function module (no package import, nothing executed except its definitions)."""
    global _EM
    if _EM is None:
        spec = importlib.util.spec_from_file_location("v22_frozen_entity_matching", ENTITY_MATCHING_PATH)
        _EM = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_EM)
    return _EM


def categories() -> list[str]:
    """The 18 clinical categories in frozen order (medical_history is split into its four subsections)."""
    return list(frozen_schema()["categories"])


def category_keys(cat: str) -> list[str]:
    return list(frozen_schema()["categories"][cat]["keys"])


def get_entities(record: dict, cat: str):
    """List of entity dicts for a category of a FULL record (chief_complaint returns a one-item list or [])."""
    if cat == "chief_complaint":
        cc = record.get("chief_complaint")
        return [cc] if isinstance(cc, dict) and cc else []
    o = record
    for part in cat.split("."):
        if not isinstance(o, dict) or part not in o:
            return []
        o = o[part]
    return o if isinstance(o, list) else []


def location(cat: str, idx: int) -> str:
    return "chief_complaint" if cat == "chief_complaint" else f"{cat}[{idx}]"


def mmss(seconds: float) -> str:
    """Gold convention: whole seconds, rounded down, MM:SS."""
    s = int(seconds)
    return "%02d:%02d" % (s // 60, s % 60)


def compact_json_len(o) -> int:
    return len(json.dumps(o, separators=(",", ":"), ensure_ascii=False))


def est_tokens(chars: int) -> int:
    return round(chars / CHARS_PER_TOKEN)
