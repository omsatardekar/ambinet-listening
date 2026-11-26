"""Exact prompt token counts with the TOKENIZER FILE ONLY (tokenizer.json via the `tokenizers` library). No model weights, no OpenVINO, no inference.
Counts the rendered user prompt (template + transcript) the way the runner builds it, plus the Qwen chat wrapper the client adds (fixed text, counted explicitly).
Calibration: the same method on the P02 v2.1 prompt and record 00168 must give the 5,901 input tokens that the v2.1 run measured."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tokenizers import Tokenizer                                   # noqa: E402
from v22_common import EXP, PKG, TRACK, load_transcript            # noqa: E402

TOK = Tokenizer.from_file(str(TRACK / "models" / "Qwen3-1.7B-ov-fp16" / "tokenizer.json"))
WRAP_PRE, WRAP_POST = "<|im_start|>user\n", "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"     # Qwen3 chat template, enable_thinking=False


def render(tr):
    return "\n".join(f"[{s['segment_id']}] {s['speaker_id']} ({s['role']}) {s['start_seconds']:.2f}-{s['end_seconds']:.2f}s: {s['text']}" for s in tr["segments"])


def build(template, eid):
    return template.replace("{ENCOUNTER_ID}", eid).replace("{TRANSCRIPT}", render(load_transcript(eid)))


n = lambda s: len(TOK.encode(s, add_special_tokens=False).ids)
v21 = (EXP / "prompt_versions" / "P02_comprehensive_v2_1.txt").read_text(encoding="utf-8")
v22 = (EXP / "prompt_versions" / "P02_comprehensive_v2_2.txt").read_text(encoding="utf-8")
out = {"tokenizer": "models/Qwen3-1.7B-ov-fp16/tokenizer.json (tokenizer only)", "wrapper_tokens": n(WRAP_PRE + WRAP_POST)}
out["calibration_v2_1_00168"] = {"counted": n(WRAP_PRE + build(v21, "00168") + WRAP_POST), "measured_by_the_v2_1_run": 5901}
out["calibration_ok"] = abs(out["calibration_v2_1_00168"]["counted"] - 5901) <= 3
empty = lambda t: t.replace("{ENCOUNTER_ID}", "").replace("{TRANSCRIPT}", "")
out["template_only_tokens"] = {"P02_v2_1": n(empty(v21)), "P02_v2_2": n(empty(v22))}
ids = ["00168", "00204", "00037", "00092", "00152", "00157"]
out["per_record_input_tokens_v2_2"] = {i: n(WRAP_PRE + build(v22, i) + WRAP_POST) for i in ids}
out["per_record_input_tokens_v2_1"] = {i: n(WRAP_PRE + build(v21, i) + WRAP_POST) for i in ids}
(PKG / "derived").mkdir(exist_ok=True)
(PKG / "derived" / "PROMPT_TOKEN_COUNTS.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
print(json.dumps(out, indent=1))
