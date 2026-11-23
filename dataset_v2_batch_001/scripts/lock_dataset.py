"""Write SHA-256 checksums of every evaluation file so later edits/leaks into training data are detectable.
usage: python lock_dataset.py [--verify]"""
import hashlib, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "CHECKSUMS.sha256"
files = sorted(p for d in ("inputs", "labels") for p in (ROOT / "output" / d).glob("*.json")) + [ROOT / "output" / "manifest.csv"]
cur = {str(p.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
if "--verify" in sys.argv:
    old = dict(l.split("  ", 1)[::-1] for l in OUT.read_text().splitlines() if l.strip())
    bad = [k for k in set(old) | set(cur) if old.get(k) != cur.get(k)]
    print("LOCK OK" if not bad else f"MODIFIED/MISSING: {bad[:10]} ...")
    sys.exit(1 if bad else 0)
OUT.write_text("".join(f"{h}  {k}\n" for k, h in cur.items()), encoding="utf-8")
print(f"wrote {len(cur)} checksums to {OUT}")
