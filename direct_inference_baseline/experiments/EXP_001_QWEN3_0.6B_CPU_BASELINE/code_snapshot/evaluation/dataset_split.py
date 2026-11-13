"""Deterministic stratified 100 development / 400 locked-test split.
Strata = specialty x complexity (from the frozen manifest.csv, read-only).  Largest-remainder allocation makes the totals exact."""
from __future__ import annotations

import csv
import json
import random
from collections import Counter, defaultdict

from ..config import settings as S

SEED = 20260301
N_DEV = 100


def _read_manifest():
    with open(S.MANIFEST_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build_split(seed: int = SEED, n_dev: int = N_DEV):
    rows = _read_manifest()
    strata = defaultdict(list)
    for r in rows:
        strata[(r["specialty"], r["complexity"])].append(r["encounter_id"])
    total = len(rows)
    rng = random.Random(seed)
    keys = sorted(strata)
    exact = {k: len(strata[k]) * n_dev / total for k in keys}
    alloc = {k: int(exact[k]) for k in keys}
    rem = n_dev - sum(alloc.values())
    order = sorted(keys, key=lambda k: (-(exact[k] - alloc[k]), rng.random()))
    for k in order[:rem]:
        alloc[k] += 1
    dev, test = [], []
    for k in keys:
        ids = sorted(strata[k])
        rng.shuffle(ids)
        dev += ids[:alloc[k]]
        test += ids[alloc[k]:]
    return sorted(dev), sorted(test), rows, {f"{k[0]} | {k[1]}": (len(strata[k]), alloc[k]) for k in keys}


def distributions(ids, rows):
    by = {r["encounter_id"]: r for r in rows}
    return {f: dict(Counter(by[i][f] for i in ids)) for f in ("specialty", "complexity", "speaker_count")}


def validate_split(dev, test, all_ids):
    assert not set(dev) & set(test), "overlap"
    assert len(dev) == len(set(dev)) and len(test) == len(set(test)), "duplicates inside a split"
    assert sorted(dev + test) == sorted(all_ids), "not every encounter appears exactly once"
    return True


def create_split(write: bool = True) -> dict:
    dev, test, rows, strata = build_split()
    all_ids = [r["encounter_id"] for r in rows]
    validate_split(dev, test, all_ids)
    dev2, test2, _, _ = build_split()                       # reproducibility: rebuild and compare
    reproducible = (dev == dev2 and test == test2)
    meta = {"seed": SEED, "method": "stratified by specialty x complexity, largest-remainder allocation, seeded shuffle",
            "n_total": len(all_ids), "n_development": len(dev), "n_test": len(test), "reproducible": reproducible, "no_overlap": True,
            "all_ids_accounted_for": True, "dataset_dir": "dataset_v2_batch_001_corrected",
            "dataset_manifest_sha256": S.sha256_file(S.FINAL_MANIFEST),
            "stratum_allocation (total, development)": strata,
            "distribution_total": distributions(all_ids, rows), "distribution_development": distributions(dev, rows),
            "distribution_test": distributions(test, rows),
            "limitations": ["Stratum sizes are small (min 1-2 per specialty x complexity cell); a few cells place all members in the test set.",
                            "Speaker count and other metadata are reported but not used as stratification keys."],
            "usage": "development = pipeline/connectivity/parsing checks only; test = locked evaluation. Never tune the prompt on test."}
    if write:
        S.SPLIT_DIR.mkdir(parents=True, exist_ok=True)
        (S.SPLIT_DIR / "development_ids.json").write_text(json.dumps(dev, indent=1), encoding="utf-8")
        (S.SPLIT_DIR / "test_ids.json").write_text(json.dumps(test, indent=1), encoding="utf-8")
        (S.SPLIT_DIR / "split_metadata.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    return meta


def load_split(name: str) -> list[str]:
    return json.loads((S.SPLIT_DIR / f"{name}_ids.json").read_text(encoding="utf-8"))
