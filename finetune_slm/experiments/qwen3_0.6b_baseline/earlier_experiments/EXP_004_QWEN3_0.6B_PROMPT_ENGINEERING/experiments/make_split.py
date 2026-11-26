"""EXP_004: deterministic, stratified, reproducible partition of the 100 EXP_003 development encounters into
  prompt_dev (50)  - used to design/iterate prompts, and
  validation (50)  - never used to tune prompts; only to select the final prompt.
Strata = specialty x complexity (frozen manifest.csv). Within each stratum (sorted keys) ids are shuffled with a seeded RNG and dealt alternately
(a global toggle carries across strata so the totals are exactly 50/50). The locked 400 test ids are never read. Reads only manifest.csv, the split id file
and the frozen transcript inputs (for token-length balance); no labels, no model."""
import csv
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP4 = HERE.parent
BASE = EXP4.parents[1]                      # direct_inference_baseline
DATA = BASE.parent / "dataset_v2_batch_001_corrected"
SEED = 20260401
dev = json.loads((BASE / "data/splits/development_ids.json").read_text(encoding="utf-8"))
dev = dev["encounter_ids"] if isinstance(dev, dict) else dev
test = json.loads((BASE / "data/splits/test_ids.json").read_text(encoding="utf-8"))
test = test["encounter_ids"] if isinstance(test, dict) else test
assert len(dev) == 100 and not (set(dev) & set(test))
rows = {r["encounter_id"]: r for r in csv.DictReader(open(DATA / "output/manifest.csv", newline="", encoding="utf-8"))}
strata = defaultdict(list)
for e in dev:
    strata[(rows[e]["specialty"], rows[e]["complexity"])].append(e)
rng = random.Random(SEED)
pd_ids, val_ids, toggle = [], [], 0
for k in sorted(strata):
    ids = sorted(strata[k])
    rng.shuffle(ids)
    for e in ids:
        (pd_ids if toggle == 0 else val_ids).append(e)
        toggle ^= 1
pd_ids, val_ids = sorted(pd_ids), sorted(val_ids)
assert len(pd_ids) == len(val_ids) == 50 and not set(pd_ids) & set(val_ids) and set(pd_ids) | set(val_ids) == set(dev)
SMOKE = ["00021", "00032", "00034", "00035", "00037"]


def tokens(e):
    t = json.loads((DATA / f"output/inputs/encounter_{e}.json").read_text(encoding="utf-8"))
    return sum(len(s["text"].split()) for s in t["segments"])


def profile(ids):
    return {"n": len(ids), "complexity": dict(sorted(Counter(rows[e]["complexity"] for e in ids).items())),
            "specialty": dict(sorted(Counter(rows[e]["specialty"] for e in ids).items())),
            "speaker_count": dict(sorted(Counter(rows[e]["speaker_count"] for e in ids).items())),
            "mean_transcript_words": round(sum(tokens(e) for e in ids) / len(ids), 1),
            "mean_duration_seconds": round(sum(float(rows[e]["duration_seconds"]) for e in ids) / len(ids), 1)}


out = {"experiment": "EXP_004", "seed": SEED, "method": "specialty x complexity strata, seeded shuffle, alternating deal with a global toggle",
       "source_split": "data/splits/development_ids.json (100 ids, seed 20260301)", "locked_test_ids_used": 0,
       "prompt_dev_ids": pd_ids, "validation_ids": val_ids, "smoke5_ids": SMOKE,
       "smoke5_in_prompt_dev": [e for e in SMOKE if e in pd_ids], "smoke5_in_validation": [e for e in SMOKE if e in val_ids],
       "profile_prompt_dev": profile(pd_ids), "profile_validation": profile(val_ids), "profile_all_100": profile(dev),
       "rules": ["Prompt wording may be inspected/tuned using prompt_dev only.", "validation is run once per candidate prompt and is used only to choose between finished prompts.",
                 "The 400 locked test encounters are never used.", "Label-derived text (gold terms, entity names) must not be copied into any prompt."]}
(HERE / "split_v1.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
print(json.dumps({k: out[k] for k in ("smoke5_in_prompt_dev", "smoke5_in_validation", "profile_prompt_dev", "profile_validation")}, indent=1)[:3500])
