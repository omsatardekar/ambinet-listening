"""EXP_004 P05 parameter sensitivity (zero inference, diagnostic only; the proposed parameters stay fixed a priori). prompt_dev only."""
import itertools, json, sys
from pathlib import Path
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.argv = ["x"]
import importlib
exec(open(_HERE / "p05_diagnostics.py", encoding="utf-8").read().split("# ---------------------------------------------------------------- items")[0])
exec("gold_items, p02_strict = [], []")
src = open(_HERE / "p05_diagnostics.py", encoding="utf-8").read()
items_code = src.split("# ---------------------------------------------------------------- items")[1].split("print(f\"items:")[0]
exec(items_code)
out = []
for tau, short, band in itertools.product((0.5, 0.6, 0.7), (10, 25), (0.05,)):
    R.TAU, R.SHORT_ANSWER_WORDS, R.BAND = tau, short, band
    b = evaluate(gold_items, "x", R.STEPS_V3)["ALL"]; a = evaluate(p02_strict, "x", R.STEPS_V3)["ALL"]
    rb, ra = row(b), row(a)
    out.append({"TAU": tau, "SHORT_ANSWER_WORDS": short, "B_cited": rb["cited_rate"], "B_hit_when_cited": rb["hit_when_cited"], "B_hit_all": rb["hit_any_all_items"], "A_cited": ra["cited_rate"], "A_hit_when_cited": ra["hit_when_cited"], "A_hit_all": ra["hit_any_all_items"]})
    print(out[-1])
R.TAU, R.SHORT_ANSWER_WORDS = 0.6, 10
write_json(OUT / "p05_sensitivity.json", out)
