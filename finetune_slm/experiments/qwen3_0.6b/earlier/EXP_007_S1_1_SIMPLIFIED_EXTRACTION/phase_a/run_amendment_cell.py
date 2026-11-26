"""Amendment 001: runs the single missing Gate-P cell U_P2_R0 (P2 prompt, original rendering R0, unconstrained) on the 10 EXISTING synthetic cases with the existing Phase A driver code.
No existing result file is re-run or replaced (run_variant returns a cached file if it exists, and U_P2_R0.json does not exist yet). Synthetic data only."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_phase_a as R  # noqa: E402  (main block is guarded; importing does not run Phase A)

assert not (R.RES / "U_P2_R0.json").exists(), "cell already exists; not re-running"
v = R.run_variant("U_P2_R0", "P2", "R0", None)
print(json.dumps(v["summary"]))
