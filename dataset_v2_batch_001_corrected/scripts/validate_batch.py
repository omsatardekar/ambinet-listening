"""Validate a range of written encounters (default: all) with the independent validator.

usage: python validate_batch.py [--root <dataset dir>] [--start 1] [--end 500] [--dataset-checks]
Automated checks only; nothing here is clinical review.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "validation"))
import validate_dataset as VD  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--start", type=int, default=1)
    ap.add_argument("--end", type=int, default=500)
    ap.add_argument("--dataset-checks", action="store_true", help="also run the whole-dataset checks (counts, quotas, duplicates)")
    a = ap.parse_args()
    root = Path(a.root)
    bad = checked = 0
    for i in range(a.start, a.end + 1):
        eid = f"{i:05d}"
        pi, pl = root / "output/inputs" / f"encounter_{eid}.json", root / "output/labels" / f"encounter_{eid}.json"
        if not (pi.exists() and pl.exists()):
            print(f"{eid}: MISSING FILE"); bad += 1; continue
        R = VD.validate_record(json.loads(pi.read_text(encoding="utf-8")), json.loads(pl.read_text(encoding="utf-8")))
        checked += 1
        if R.errors:
            bad += 1
            print(f"{eid}: FAIL", [e["message"][:120] for e in R.errors[:3]])
    print(f"checked {checked}, failed {bad}")
    if a.dataset_checks:
        rep, dup, ev = VD.run(root, write=False)
        print(json.dumps({k: rep[k] for k in ("total_input_files", "total_label_files", "input_label_ids_match", "pass_count", "fail_count",
                                               "specialty_distribution", "complexity_distribution")}, indent=1))
        print("evidence:", ev["alignment_status"], ev["facts_grounded"], "/", ev["facts_checked"], "| duplicates:", dup["duplicate_count"])
        bad += rep["fail_count"]
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
