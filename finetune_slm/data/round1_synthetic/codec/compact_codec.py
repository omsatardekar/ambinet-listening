"""Lossless compact form of the clinical extraction JSON (no dependencies).

compact(label)  -> the short object the model is trained to write: every field whose value is the schema default (null, or [] for list fields) is left out.
expand(obj)     -> the full structure again, with every field present in the original order. expand(compact(x)) == x exactly for all 4,200 labels (see roundtrip_report.json).

The key order and defaults live in schema_keys.json (learned from the labels; every item of a section has the same keys in the same order).
Use expand() on the model output before parsing / showing it, so the rest of the project keeps the full format.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_SPEC_FILE = Path(__file__).with_name("schema_keys.json")
_SPEC: dict | None = None


def spec() -> dict:
    global _SPEC
    if _SPEC is None:
        _SPEC = json.loads(_SPEC_FILE.read_text(encoding="utf-8"))
    return _SPEC


def _is_default(value: Any, default: Any) -> bool:
    return value == default and type(value) is type(default)


def compact(obj: Any, path: str = "L") -> Any:
    sp = spec()
    if isinstance(obj, dict):
        node = sp.get(path)
        out = {}
        for key, value in obj.items():
            default = node["defaults"].get(key) if node else None
            if _is_default(value, default):
                continue
            child = compact(value, f"{path}.{key}")
            out[key] = child
        return out
    if isinstance(obj, list):
        return [compact(x, path + "[]") for x in obj]
    return obj


def expand(obj: Any, path: str = "L", warnings: list | None = None) -> Any:
    sp = spec()
    if isinstance(obj, dict):
        node = sp.get(path)
        if node is None:                       # a free-form dict (should not happen); return as is
            return obj
        out = {}
        for key in node["keys"]:
            if key in obj:
                out[key] = expand(obj[key], f"{path}.{key}", warnings)
            else:
                d = node["defaults"].get(key)
                out[key] = [] if d == [] else d
        if warnings is not None:
            for key in obj:
                if key not in node["keys"]:
                    warnings.append(f"unknown key dropped at {path}: {key}")
        return out
    if isinstance(obj, list):
        return [expand(x, path + "[]", warnings) for x in obj]
    return obj
