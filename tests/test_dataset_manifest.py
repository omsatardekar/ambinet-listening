import pytest
from pathlib import Path
import json

@pytest.mark.skipif(not (Path(__file__).parents[1] / "scenarios").is_dir(), reason="scenario corpus is not part of the repository")
def test_scenario_distribution_and_uniqueness():
    root = Path(__file__).parents[1] / "scenarios"
    paths = sorted(root.glob("*/scenario.json"))
    assert len(paths) == 50
    data = [json.loads(p.read_text(encoding="utf-8")) for p in paths]
    assert len({d["encounter_id"] for d in data}) == 50
    dist = {k: sum(d["difficulty"] == k for d in data) for k in ("easy", "medium", "hard")}
    assert dist == {"easy": 15, "medium": 20, "hard": 15}
    assert all((p.parent / "dialogue.txt").exists() for p in paths)
