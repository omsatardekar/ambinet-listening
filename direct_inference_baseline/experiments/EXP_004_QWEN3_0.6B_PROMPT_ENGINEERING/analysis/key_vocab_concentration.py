"""EXP_004 P02 pre-work (read-only): how concentrated are gold match-keys per category on the 50 prompt_dev ids? Counts only, no strings stored."""
import json, sys, types
from collections import Counter
from pathlib import Path
try:
    import dotenv
except ImportError:
    sys.modules["dotenv"] = types.SimpleNamespace(load_dotenv=lambda *a, **k: False)
sys.dont_write_bytecode = True
EXP4 = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(EXP4.parents[2]))
from direct_inference_baseline.evaluation import evaluation_runner as ER
from direct_inference_baseline.evaluation.entity_matching import CATEGORIES, KEYS, entity_list, norm_text
ids = json.loads((EXP4/"experiments"/"split_v1.json").read_text(encoding="utf-8"))["prompt_dev_ids"]
out = {}
for c in CATEGORIES:
    k = Counter()
    for e in ids:
        for g in entity_list(ER.load_gold(e), c):
            v = KEYS[c](g)
            if v: k[norm_text(v) if c not in ("clinical_actions","follow_up") else v] += 1
    n = sum(k.values())
    out[c] = {"items": n, "distinct_keys": len(k), "top5_share": round(sum(x for _, x in k.most_common(5))/max(1,n), 2), "top20_share": round(sum(x for _, x in k.most_common(20))/max(1,n), 2), "singleton_keys": sum(1 for x in k.values() if x == 1)}
    print(c, out[c])
json.dump(out, open(EXP4/"analysis"/"key_vocab_concentration_dev50.json","w"), indent=1)
