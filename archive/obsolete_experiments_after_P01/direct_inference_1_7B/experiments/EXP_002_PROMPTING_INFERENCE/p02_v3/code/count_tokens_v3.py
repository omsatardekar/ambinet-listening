"""Exact input-token counts (tokenizer file only; no model) for P01 and P02 v3 on the 30 P01 ids, calibrated against the P01 run's measured prompt_tokens."""
import json
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "p02_v2_2" / "code"))
from tokenizers import Tokenizer                                   # noqa: E402
from v22_common import EXP, TRACK, load_transcript                 # noqa: E402

PKG = Path(__file__).resolve().parents[1]
TOK = Tokenizer.from_file(str(TRACK / "models" / "Qwen3-1.7B-ov-fp16" / "tokenizer.json"))
PRE, POST = "<|im_start|>user\n", "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
n = lambda s: len(TOK.encode(s, add_special_tokens=False).ids)
render = lambda tr: "\n".join(f"[{s['segment_id']}] {s['speaker_id']} ({s['role']}) {s['start_seconds']:.2f}-{s['end_seconds']:.2f}s: {s['text']}" for s in tr["segments"])
build = lambda t, e: t.replace("{ENCOUNTER_ID}", e).replace("{TRANSCRIPT}", render(load_transcript(e)))
ids = json.loads((PKG.parent / "outputs" / "raw" / "P01_schema_guided_dev50" / "encounter_00035.json").read_text(encoding="utf-8-sig")) and sorted(p.stem.split("_")[1] for p in (EXP / "outputs" / "raw" / "P01_schema_guided_dev50").glob("encounter_*.json"))
p01 = (EXP / "prompt_versions" / "P01_schema_guided.txt").read_text(encoding="utf-8")
v3 = (EXP / "prompt_versions" / "P02_v3_p01_schema_no_evidence.txt").read_text(encoding="utf-8")
out = {"ids": ids, "template_tokens": {"P01": n(p01.replace("{ENCOUNTER_ID}", "").replace("{TRANSCRIPT}", "")), "P02_v3": n(v3.replace("{ENCOUNTER_ID}", "").replace("{TRANSCRIPT}", ""))}}
cal = []
for e in ids:
    meas = json.loads((EXP / "outputs" / "raw" / "P01_schema_guided_dev50" / f"encounter_{e}.json").read_text(encoding="utf-8-sig"))["generation"]["prompt_tokens"]
    cal.append((e, n(PRE + build(p01, e) + POST), meas))
out["calibration_P01_counted_vs_measured"] = {"max_abs_diff": max(abs(c - m) for _, c, m in cal), "records": len(cal), "exact_matches": sum(c == m for _, c, m in cal)}
inp = {e: n(PRE + build(v3, e) + POST) for e in ids}
out["input_tokens_v3"] = {"min": min(inp.values()), "median": st.median(inp.values()), "max": max(inp.values()), "per_record": inp}
out["input_tokens_P01_measured_median"] = st.median(m for _, _, m in cal)
(PKG / "derived").mkdir(exist_ok=True)
(PKG / "derived" / "PROMPT_V3_TOKEN_COUNTS.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
print(json.dumps({k: v for k, v in out.items() if k != "input_tokens_v3"}, indent=1)); print({k: v for k, v in out["input_tokens_v3"].items() if k != "per_record"})
