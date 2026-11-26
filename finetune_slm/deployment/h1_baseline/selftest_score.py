"""Offline self-test of the Azure scoring script: request handling and the pure extraction pipeline with a FAKE generator. Loads no model, needs no Azure.

    python finetune_slm/deployment/h1_baseline/build_single_file_score.py   (once)
    python finetune_slm/deployment/h1_baseline/selftest_score.py
Tests BOTH the bundle's score.py and the single upload file (score_single_file.py), and replays a real stored EXP_008 model answer through the pipeline."""
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]                                   # repository root
req = json.loads((HERE / "sample_request.json").read_text(encoding="utf-8"))
compact = req["compact_transcript"]
stored = json.loads((ROOT / "finetune_slm/experiments/qwen3_0.6b_baseline/EXP_008_QWEN3_0.6B_HYBRID_P02_S1/outputs/H1_main30/raw_predictions/H1_main30/encounter_00037.json").read_text(encoding="utf-8"))
transcript37 = json.loads((ROOT / "finetune_slm/archive/dataset_v2_batch_001_corrected/output/inputs/encounter_00037.json").read_text(encoding="utf-8"))

sys.path.insert(0, str(HERE / "code_bundle"))
import score  # noqa: E402

spec = importlib.util.spec_from_file_location("single", HERE / "score_single_file.py")
single = importlib.util.module_from_spec(spec)
spec.loader.exec_module(single)
assert single.init.__module__ == "h1_score" and single.run.__module__ == "h1_score", "single file must delegate to the bundle's score.py"

for mod in (score, single):                                                  # 1. routing / validation, no model
    run = mod.run
    assert json.loads(run(json.dumps({"action": "nope"})))["error"] == "unknown_action"
    assert json.loads(run("not json"))["error"] == "bad_request"
    assert json.loads(run(json.dumps({"action": "submit", "compact_transcript": {"segments": []}})))["error"] == "invalid_compact_transcript"
    assert json.loads(run(json.dumps(req)))["error"] == "model_not_ready"
    assert json.loads(run(json.dumps({"action": "status", "job_id": "x"})))["error"] == "unknown_job"

# 2. pure pipeline: a real stored H1 answer must parse and pass through UNMODIFIED; truncation must be a failure
real = {"text": stored["response_text"], "finish_reason": stored["generation"]["finish_reason"], "input_tokens": stored["generation"]["prompt_tokens"],
        "output_tokens": stored["generation"]["completion_tokens"], "generation_seconds": 0.1}
res = score.run_extraction(transcript37, generate=lambda p: real)
assert res["ok"], res["metadata"]
expected = json.loads((ROOT / "finetune_slm/experiments/qwen3_0.6b_baseline/EXP_008_QWEN3_0.6B_HYBRID_P02_S1/outputs/H1_main30/parsed_predictions/H1_main30/encounter_00037.json").read_text(encoding="utf-8"))
assert res["extraction"] == expected, "the endpoint pipeline must return exactly the parser output of the experiment"
assert res["metadata"]["prompt_sha256"] == score.EXPECTED_PROMPT_SHA256 and res["metadata"]["evidence_citations"].startswith("not requested")
cut = score.run_extraction(compact, generate=lambda p: {**real, "text": real["text"][:40], "finish_reason": "length"})
assert not cut["ok"] and cut["metadata"]["parse_status"] == "truncated"
seen = {}
score.run_extraction(transcript37, generate=lambda p: seen.setdefault("prompt", p) and real)
assert "[SEG0001]" in seen["prompt"] and "JSON:" in seen["prompt"] and "{TRANSCRIPT}" not in seen["prompt"] and "{ENCOUNTER_ID}" not in seen["prompt"]
print("azure_ml_h1 self-test passed (no model loaded)")
