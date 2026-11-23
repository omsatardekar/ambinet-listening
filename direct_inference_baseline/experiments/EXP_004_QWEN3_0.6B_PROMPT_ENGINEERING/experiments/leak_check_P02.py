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
p0 = (EXP4/"prompts"/"P00_original_baseline.txt").read_text(encoding="utf-8"); p2 = (EXP4/"prompts"/"P02_comprehensive_extraction.txt").read_text(encoding="utf-8")
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
print(json.dumps(res, indent=1)); (EXP4/"evaluation"/"P02_leakage_check.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
# duplicate baseline
ids = json.loads((EXP4/"experiments"/"split_v1.json").read_text(encoding="utf-8"))["prompt_dev_ids"]
src = {"P00": EXP4.parent/"EXP_003_QWEN3_0.6B_OPENVINO_GPU_DIRECT"/"parsed_predictions"/"exp_003_dev_100", "P01": EXP4/"outputs"/"P01_schema_focused_dev50"/"parsed_predictions"/"P01_schema_focused_dev50"}
base = {}
for v, d in src.items():
    n = dup = 0
    for e in ids:
        f = d/f"encounter_{e}.json"
        if not f.exists(): continue
        pr = json.loads(f.read_text(encoding="utf-8"))
        for c in CATEGORIES:
            ks = [norm_text(KEYS[c](x)) for x in entity_list(pr, c) if KEYS[c](x)]
            n += len(ks); dup += len(ks) - len(set(ks))
    base[v] = {"predicted_items": n, "duplicate_items": dup, "duplicate_rate": round(dup/max(1, n), 3)}
print(base); (EXP4/"evaluation"/"P00_P01_duplicate_baseline_dev50.json").write_text(json.dumps(base, indent=1), encoding="utf-8")
