import pytest
from pathlib import Path
import json
from ambient_tts import parse_dialogue

@pytest.mark.skipif(not (Path(__file__).parents[1] / "scenarios").is_dir(), reason="scenario corpus is not part of the repository")
def test_all_scenario_dialogues_parse():
    root = Path(__file__).parents[1] / "scenarios"
    scenarios = sorted(root.glob("*/scenario.json"))
    assert len(scenarios) == 50
    for path in scenarios:
        data = json.loads(path.read_text(encoding="utf-8"))
        turns = parse_dialogue(path.parent / "dialogue.txt", data["speakers"])
        assert len(turns) >= 30
