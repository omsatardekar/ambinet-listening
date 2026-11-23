import json
from collections import Counter

from direct_inference_baseline.config import settings as S
from direct_inference_baseline.evaluation import dataset_split as DS


def test_split_sizes_overlap_and_coverage():
    dev, test, rows, _ = DS.build_split()
    ids = [r["encounter_id"] for r in rows]
    assert len(dev) == 100 and len(test) == 400
    assert not set(dev) & set(test)
    assert sorted(dev + test) == sorted(ids) and len(set(ids)) == 500


def test_split_reproducible_and_saved_files_match():
    a, b = DS.build_split(), DS.build_split()
    assert a[0] == b[0] and a[1] == b[1]
    assert DS.load_split("development") == a[0] and DS.load_split("test") == a[1]


def test_split_is_stratified():
    dev, test, rows, _ = DS.build_split()
    by = {r["encounter_id"]: r for r in rows}
    tot = Counter(r["complexity"] for r in rows)
    d = Counter(by[i]["complexity"] for i in dev)
    for k, n in tot.items():
        assert abs(d[k] - n * 0.2) <= 2          # within 2 encounters of the ideal 20%
    tot = Counter(r["specialty"] for r in rows)
    d = Counter(by[i]["specialty"] for i in dev)
    for k, n in tot.items():
        assert abs(d[k] - n * 0.2) <= 2


def test_frozen_dataset_verified_and_unchanged_by_checks():
    before = S.sha256_file(S.CHECKSUMS)
    r = S.verify_frozen_dataset()
    assert r["verified"] and r["files_checked"] == 1001
    assert S.sha256_file(S.CHECKSUMS) == before


def test_no_prediction_or_report_inside_frozen_dataset():
    assert not any(p.suffix == ".json" and "direct_inference" in p.name for p in S.DATASET_DIR.rglob("*"))
    assert S.OUTPUT_DIR.resolve().is_relative_to(S.MODULE_DIR.resolve())
