"""Integrity helpers: (1) the 0.6B tree must stay byte-identical to the inventory taken BEFORE the rename (manifests/PRE_RENAME_INVENTORY_0_6B.json),
(2) the 0.6B frozen evaluator / schema / P00-P05 files must match the P05 freeze manifest."""
import json
import os
import hashlib

import common_1_7b as C

HEAVY = ("env_openvino", "ov_cache")
IGNORE_NEW = ("__pycache__",)


def verify_legacy_tree():
    """Returns {"ok": bool, "files_expected", "mismatched", "missing", "new_unexpected"}.  Re-hashes ~3,600 files (about 15 s)."""
    inv = json.loads((C.TRACK / "manifests" / "PRE_RENAME_INVENTORY_0_6B.json").read_text(encoding="utf-8"))["entries"]
    root = str(C.LEGACY)
    seen, bad, new = set(), [], []
    for dp, dn, fn in os.walk(root):
        for f in fn:
            p = os.path.join(dp, f)
            rel = os.path.relpath(p, root).replace("\\", "/")
            seen.add(rel)
            exp = inv.get(rel)
            if exp is None:
                if not any(x in rel for x in IGNORE_NEW):
                    new.append(rel)
                continue
            if "sha256" in exp:
                h = hashlib.sha256()
                with open(p, "rb") as fh:
                    for c in iter(lambda: fh.read(1 << 20), b""):
                        h.update(c)
                if h.hexdigest() != exp["sha256"]:
                    bad.append(rel)
            elif os.path.getsize(p) != exp["size"] and not any(rel.startswith(x) or f"/{x}/" in "/" + rel for x in ()):
                bad.append(rel)
    missing = [r for r in inv if r not in seen]
    return {"ok": not bad and not missing and not new, "files_expected": len(inv), "mismatched": bad[:20], "n_mismatched": len(bad), "missing": missing[:20], "n_missing": len(missing), "new_unexpected": new[:20], "n_new": len(new)}


def verify_frozen_0_6b():
    fm = json.loads((C.EXP4 / "P05_FREEZE_MANIFEST.json").read_text(encoding="utf-8"))
    bad = [f for f, h in fm["frozen_files_sha256"].items() if C.sha256_file(C.EXP4 / f) != h]
    bad += [f for f, h in fm["evaluator_files_sha256"].items() if C.sha256_file(C.S.MODULE_DIR / f) != h]
    sch = fm["schema_sha256"]
    ok_schema = C.sha256_file(C.S.ROOT_SCHEMA) == sch["root_schema"] and C.sha256_file(C.S.FINAL_SCHEMA) == sch["final_schema"]
    return {"ok": not bad and ok_schema and C.sha256_file(C.EXP4 / "P05_FREEZE_MANIFEST.json") == "e383d3a352a6e431bc74c49c8c409d15a6e02831b05ee73e47aec472fd56fae0", "mismatch": bad, "schema_ok": ok_schema}
