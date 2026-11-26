"""Leakage check for the added P02 block: gold match-keys of the 100 development labels vs the added text (whole-word, case-insensitive). Also duplicate-rate baselines for P00/P01 outputs (no labels)."""
import json, re, sys, types, difflib
from collections import Counter
from pathlib import Path
try:
    import dotenv
except ImportError:
    sys.modules["dotenv"] = types.SimpleNamespace(load_dotenv=lambda *a, **k: False)
sys.dont_write_bytecode = True
EXP4 = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(EXP4.parents[2]))
from direct_inference_baseline.evaluation import evaluation_runner as ER
from direct_inference_baseline.evaluation.dataset_split import load_split
from direct_inference_baseline.evaluation.entity_matching import CATEGORIES, KEYS, entity_list, norm_text
p0 = (EXP4/"prompts"/"P00_original_baseline.txt").read_text(encoding="utf-8"); p2 = (EXP4/"prompts"/"P03_evidence_grounded.txt").read_text(encoding="utf-8")
added = " ".join(l[1:] for l in difflib.unified_diff(p0.splitlines(), p2.splitlines(), lineterm="", n=0) if l.startswith("+") and not l.startswith("+++")).lower()
keys = Counter()
for e in load_split("development"):
    g = ER.load_gold(e)
    for c in CATEGORIES:
        for x in entity_list(g, c):
            v = KEYS[c](x)
            if v and c not in ("clinical_actions", "follow_up"): keys[norm_text(v)] += 1
hits = sorted(k for k in keys if len(k) > 2 and re.search(r"(?<![a-z])" + re.escape(k) + r"(?![a-z])", added))
res = {"gold_keys_checked": len(keys), "keys_found_in_added_text": hits}
print(json.dumps(res, indent=1)); (EXP4/"evaluation"/"P03_leakage_check.json").write_text(json.dumps(res, indent=1), encoding="utf-8")

# additional: any 5+-word run of the gold evidence texts (development labels) inside the added text?
ev_hits = 0
for e in load_split("development"):
    for r in ER.load_gold(e).get("clinical_evidence", []):
        w = norm_text(r.get("transcript_text")).split()
        for i in range(0, max(0, len(w) - 4)):
            if " ".join(w[i:i+5]) in norm_text(added): ev_hits += 1
print("gold evidence 5-word runs found in added text:", ev_hits)
res["gold_evidence_5word_runs_in_added_text"] = ev_hits
(EXP4/"evaluation"/"P03_leakage_check.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
