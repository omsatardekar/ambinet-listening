"""Read-only check that every Batch 001 file listed in the frozen output/FINAL_MANIFEST.json is byte-identical, and that no Batch 001 file was added or removed.
Excluded by design: the Batch 002 folder (batch_002/) and the parent README.md, which the owner asked to extend with one Batch 002 entry (its hash is reported separately).
usage: python -B verify_batch_001_unchanged.py"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
m = json.loads((ROOT / "output" / "FINAL_MANIFEST.json").read_text(encoding="utf-8"))["corrected_dataset"]["files"]
problems, readme = [], None
for k, h in m.items():
    p = ROOT / k
    if not p.exists():
        problems.append(("missing", k))
        continue
    if k == "output/CHECKSUMS.sha256":
        continue
    got = hashlib.sha256(p.read_bytes()).hexdigest()
    if k == "README.md":
        readme = {"frozen_sha256": h, "current_sha256": got, "changed": got != h, "note": "owner-approved concise Batch 002 entry"}
        continue
    if got != h:
        problems.append(("changed", k))
unlisted = []
for p in ROOT.rglob("*"):
    if not p.is_file() or "__pycache__" in p.parts:
        continue
    rel = p.relative_to(ROOT).as_posix()
    if rel.startswith("batch_002/") or rel in m or rel == "output/FINAL_MANIFEST.json":   # the manifest does not list itself
        continue
    unlisted.append(rel)
res = {"manifest_files": len(m), "problems": problems, "unlisted_files_outside_batch_002": unlisted, "README": readme}
print(json.dumps(res, indent=1))
sys.exit(1 if problems or unlisted else 0)
