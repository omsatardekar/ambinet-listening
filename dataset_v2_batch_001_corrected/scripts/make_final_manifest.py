"""Freeze: hash every file of the corrected dataset (and, separately, the untouched original), write output/FINAL_MANIFEST.json,
refresh output/CHECKSUMS.sha256 and mark evaluation files read-only.  `--verify` re-checks everything without writing.
Hashing only; never edits conversations."""
import hashlib
import json
import os
import stat
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIG = ROOT.parent / "dataset_v2_batch_001"
SKIP = {"__pycache__", "FINAL_MANIFEST.json"}


def files(base):
    return sorted(p for p in base.rglob("*") if p.is_file() and not (set(p.parts) & SKIP) and p.suffix != ".pyc")


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def tree(base):
    h = {str(p.relative_to(base)).replace("\\", "/"): sha(p) for p in files(base)}
    root = hashlib.sha256("".join(f"{v}  {k}\n" for k, v in sorted(h.items())).encode()).hexdigest()
    return h, root


def eval_files(base):
    return [p for d in ("inputs", "labels") for p in sorted((base / "output" / d).glob("*.json"))]


if "--verify" in sys.argv:
    m = json.loads((ROOT / "output" / "FINAL_MANIFEST.json").read_text(encoding="utf-8"))
    cur, root = tree(ROOT)
    ocur, oroot = tree(ORIG)
    bad = [k for k in set(m["corrected_dataset"]["files"]) | set(cur) if k != "output/CHECKSUMS.sha256" and m["corrected_dataset"]["files"].get(k) != cur.get(k)]
    obad = [k for k in set(m["original_dataset"]["files"]) | set(ocur) if m["original_dataset"]["files"].get(k) != ocur.get(k)]
    print("corrected dataset:", "VERIFIED" if not bad else f"CHANGED {bad[:5]}")
    print("original dataset :", "VERIFIED" if not obad else f"CHANGED {obad[:5]}")
    sys.exit(1 if bad or obad else 0)

for _p in eval_files(ROOT) + [ROOT / "output" / "manifest.csv", ROOT / "output" / "FINAL_MANIFEST.json", ROOT / "output" / "CHECKSUMS.sha256", ROOT / "schema" / "final_label_schema.json"]:
    if _p.exists():
        os.chmod(_p, stat.S_IREAD | stat.S_IWRITE)   # re-freezing hashes only; conversations are never rewritten
# per-file checksum list for the evaluation files (same format as before)
cs = {str(p.relative_to(ROOT)).replace("\\", "/"): sha(p) for p in eval_files(ROOT) + [ROOT / "output" / "manifest.csv"]}
(ROOT / "output" / "CHECKSUMS.sha256").write_text("".join(f"{h}  {k}\n" for k, h in cs.items()), encoding="utf-8")
chash, croot = tree(ROOT)
ohash, oroot = tree(ORIG)
stats = json.loads((ROOT / "output" / "stats.json").read_text(encoding="utf-8"))
audit = json.loads((ROOT / "validation" / "final_schema_audit.json").read_text(encoding="utf-8"))
manifest = {
    "dataset": "dataset_v2_batch_001_corrected", "status": "FROZEN (evaluation only; do not use for training)",
    "created_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
    "immutability": "SHA-256 of every file below. Evaluation files are also marked read-only (advisory). Any later change must be detectable with `python scripts/make_final_manifest.py --verify`.",
    "records": {"transcripts": 500, "labels": 500, "blueprints": 500},
    "schema": "schema/final_label_schema.json (definitions in reports/FINAL_SCHEMA.md)",
    "final_schema_audit": {"status": audit["status"], "check_evaluations": audit["total_check_evaluations"], "failures": audit["failure_count"]},
    "validation": {"pairs_passing_automated_validation": stats["validation_pass_count"], "pairs_failing": stats["validation_failure_count"],
                   "evidence_facts_grounded": f"{stats['evidence_facts_grounded']}/{stats['evidence_facts_checked']}", "duplicates": stats["duplicate_count"],
                   "clinical_review": "none performed"},
    "corrected_dataset": {"root_sha256": croot, "file_count": len(chash), "files": chash},
    "original_dataset": {"path": "../dataset_v2_batch_001", "role": "untouched source", "root_sha256": oroot, "file_count": len(ohash), "files": ohash},
}
(ROOT / "output" / "FINAL_MANIFEST.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
for p in eval_files(ROOT) + [ROOT / "output" / "manifest.csv", ROOT / "output" / "FINAL_MANIFEST.json", ROOT / "output" / "CHECKSUMS.sha256", ROOT / "schema" / "final_label_schema.json"]:
    os.chmod(p, stat.S_IREAD)
print("corrected root", croot, len(chash), "files")
print("original  root", oroot, len(ohash), "files")
