"""Offline self-test of the fine-tuned scoring script. Loads no model, needs no Azure.

    python finetune_slm/deployment/source/build_single_file_score.py --name step156 --label ... --weights-sha ...   (once; the last build decides which model's pinned hashes the bundle test uses)
    python finetune_slm/deployment/source/selftest_score.py
1. request routing (bundle score.py and the single upload file);
2. PROMPT: for all 973 locked-test encounters, the prompt built from the compact transcript (with timestamps, as the front end sends it) equals the dataset prompt byte for byte;
3. PIPELINE: the 973 stored step-400 raw outputs are replayed through run_extraction with a fake generator: every valid output must pass UNCHANGED (== expand of the stored raw JSON),
   the 6 invalid ones must be repaired, garbage must end as failed after one regeneration, truncation must fail without regeneration."""
import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]                                   # repository root
sys.path.insert(0, str(HERE / os.environ.get("SCORE_BUNDLE", "code_bundle")))
import score  # noqa: E402
from compact_codec import expand  # noqa: E402

req = json.loads((HERE / "sample_request.json").read_text(encoding="utf-8"))
spec = importlib.util.spec_from_file_location("single", HERE.parent / "step156_round2" / "score_single_file_step156.py")
single = importlib.util.module_from_spec(spec)
spec.loader.exec_module(single)
assert single.init.__module__ == "ft_score" and single.run.__module__ == "ft_score"
for mod in (score, single):
    run = mod.run
    assert json.loads(run(json.dumps({"action": "nope"})))["error"] == "unknown_action"
    assert json.loads(run("not json"))["error"] == "bad_request"
    assert json.loads(run(json.dumps({"action": "submit", "compact_transcript": {"segments": []}})))["error"] == "invalid_compact_transcript"
    assert json.loads(run(json.dumps(req)))["error"] == "model_not_ready"
    assert json.loads(run(json.dumps({"action": "status", "job_id": "x"})))["error"] == "unknown_job"
print("1. routing ok")

rows = [json.loads(l) for l in open(ROOT / "finetune_slm/data/round1_synthetic/test/test.jsonl", encoding="utf-8")]
for r in rows:
    compact = json.loads((ROOT / "finetune_slm/data/round1_synthetic/test/raw_inputs" / f"encounter_{r['id']}.json").read_text(encoding="utf-8"))
    assert score.build_prompt(compact) == r["messages"][0]["content"], f"prompt differs for {r['id']}"
print(f"2. prompt identical to the dataset prompt for {len(rows)} encounters (front-end input with timestamps)")

OUTD = ROOT / "finetune_slm/runs/round1_step400/test_step400_outputs"
n_ok = n_rep = n_alt = 0
repaired_ids = []
for r in rows:
    eid = r["id"]
    compact = json.loads((ROOT / "finetune_slm/data/round1_synthetic/test/raw_inputs" / f"encounter_{eid}.json").read_text(encoding="utf-8"))
    text = (OUTD / f"{eid}_2_model_raw.json").read_text(encoding="utf-8")
    gen = {"text": text, "finish_reason": "stop", "input_tokens": 0, "output_tokens": 0, "generation_seconds": 0.0}
    res = score.run_extraction(compact, generate=lambda p, s=False: gen)
    assert res["ok"], (eid, res["metadata"]["guard_notes"])
    try:
        expect = expand(json.loads(text))
    except json.JSONDecodeError:
        assert res["metadata"]["extraction_status"] == "repaired" and res["metadata"]["needs_review"]
        n_rep += 1
        repaired_ids.append(eid)
        continue
    expect["encounter_id"] = compact["encounter_id"]
    if res["extraction"] != expect or res["metadata"]["extraction_status"] != "ok":
        n_alt += 1
    n_ok += 1
assert n_alt == 0, f"{n_alt} valid outputs were altered"
assert n_rep == 6, repaired_ids
print(f"3. pipeline: {n_ok} valid outputs passed unchanged, {n_rep} invalid outputs repaired {repaired_ids}")

compact = json.loads((ROOT / "finetune_slm/data/round1_synthetic/test/raw_inputs/encounter_00001.json").read_text(encoding="utf-8"))
calls = []
bad = lambda p, s=False: (calls.append(s), {"text": '{"encounter_id": "x", "broken": [', "finish_reason": "stop", "input_tokens": 1, "output_tokens": 1, "generation_seconds": 0.0})[1]  # noqa: E731
res = score.run_extraction(compact, generate=bad)
assert not res["ok"] and res["metadata"]["extraction_status"] == "failed" and res["metadata"]["needs_review"] and calls == [False, True]
calls.clear()
cut = score.run_extraction(compact, generate=lambda p, s=False: (calls.append(s), {"text": "{", "finish_reason": "length", "input_tokens": 1, "output_tokens": 4096, "generation_seconds": 0.0})[1])
assert not cut["ok"] and calls == [False, True]
print("4. garbage -> failed after one regeneration (also when truncated)")

# 5. windows: a long consultation (20 hand-written scenario m3_01) is cut into windows, the stored round-2 window outputs are replayed, the result is merged
import re as _re
rec = json.loads(next(l for l in open(ROOT / "finetune_slm/data/module3_eval_inputs/module3_recordings.jsonl", encoding="utf-8") if '"m3_01_foot_sore_bus_driver"' in l))
segs = [dict(zip(("segment_id", "speaker_id", "role", "text"), m.groups())) for l in rec["messages"][0]["content"].splitlines() if (m := _re.match(r"^\[(SEG\d{4})\] (person_\d+) \(([A-Z_]+)\): (.*)$", l))]
for i_, s_ in enumerate(segs):
    s_["start_seconds"], s_["end_seconds"] = float(i_ * 5), float(i_ * 5 + 4)
outs = [(ROOT / f"finetune_slm/runs/round2_natural_and_windows/m3_win_step156/m3_01_foot_sore_bus_driver__w{k}_2_model_raw.json").read_text(encoding="utf-8") for k in (1, 2)]
# the stored outputs were produced with 7,000-character windows: replay them with that size whatever the bundle uses
_pinned_w = (score.WINDOW_CHARS, score.WINDOW_OVERLAP)
score.WINDOW_CHARS, score.WINDOW_OVERLAP = 7000, 4
it = iter(outs)
res = score.run_extraction({"encounter_id": "m3_01", "segments": segs}, generate=lambda p, s=False: {"text": next(it), "finish_reason": "stop", "input_tokens": 1, "output_tokens": 1, "generation_seconds": 0.0})
assert res["ok"] and res["metadata"]["windows"] == 2 and res["metadata"]["extraction_status"] == "ok", res["metadata"]
ids = set(_re.findall(r"SEG\d{4}", json.dumps(res["extraction"])))
assert ids and ids <= {s_["segment_id"] for s_ in segs}, "evidence ids must be original ids"
assert max(int(i[3:]) for i in ids) > 60, "second window ids must be mapped back to the original numbering"
score.WINDOW_CHARS, score.WINDOW_OVERLAP = _pinned_w
# with the pinned size (14,000 for step 400) a consultation of this length is processed in ONE pass: no window can lose context
_one = score.make_windows if hasattr(score, "make_windows") else None
from chunking import make_windows as _mw
_n = len(_mw(segs, score.WINDOW_CHARS, score.WINDOW_OVERLAP))
print(f"   pinned window size {score.WINDOW_CHARS} chars / overlap {score.WINDOW_OVERLAP}: scenario m3_01 -> {_n} window(s)")
print(f"5. windows: 2 windows merged, {len(res['extraction']['symptoms'])} symptoms, evidence ids mapped back to the original numbering")

# 6. a repetition loop that hit the token limit is repaired and flagged
loop = (ROOT / "finetune_slm/runs/round2_natural_and_windows/m3_run2_step156/m3_13_forgetting_and_getting_lost_2_model_raw.json").read_text(encoding="utf-8")
res = score.run_extraction({"encounter_id": "m3_13", "segments": segs[:20]}, generate=lambda p, s=False: {"text": loop, "finish_reason": "length", "input_tokens": 1, "output_tokens": 4096, "generation_seconds": 0.0})
assert res["ok"] and res["metadata"]["extraction_status"] == "repaired" and res["metadata"]["needs_review"], res["metadata"]
print("6. repetition loop (token limit hit) -> repaired and flagged for review")
print("azure_ml_ft self-test passed (no model loaded)")
