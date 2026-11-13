"""Verify the proposed smoke-test ids: each must be a prompt_dev id, none in validation, none in the locked test set. Reads only the split files."""
import json, sys, types
from pathlib import Path
try:
    import dotenv
except ImportError:
    sys.modules["dotenv"] = types.SimpleNamespace(load_dotenv=lambda *a, **k: False)
sys.dont_write_bytecode = True
EXP4 = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(EXP4.parents[2]))
from direct_inference_baseline.evaluation.dataset_split import load_split
sp = json.loads((EXP4/"experiments"/"split_v1.json").read_text(encoding="utf-8"))
test, dev = set(load_split("test")), set(load_split("development"))
ids = ["00035", "00037", "00040", "00215", "00248"]
res = {i: {"in_prompt_dev_50": i in sp["prompt_dev_ids"], "in_validation_50": i in sp["validation_ids"], "in_development_100": i in dev, "in_locked_test_400": i in test} for i in ids}
ok = all(v["in_prompt_dev_50"] and not v["in_validation_50"] and v["in_development_100"] and not v["in_locked_test_400"] for v in res.values())
out = {"smoke_ids": ids, "per_id": res, "all_ok": ok, "sizes": {"prompt_dev": len(sp["prompt_dev_ids"]), "validation": len(sp["validation_ids"]), "development": len(dev), "test": len(test)},
       "overlaps": {"prompt_dev_and_validation": len(set(sp["prompt_dev_ids"]) & set(sp["validation_ids"])), "prompt_dev_and_test": len(set(sp["prompt_dev_ids"]) & test), "validation_and_test": len(set(sp["validation_ids"]) & test)}}
(EXP4/"evaluation"/"P04_smoke_ids_check.json").write_text(json.dumps(out, indent=1), encoding="utf-8"); print(json.dumps(out, indent=1))
