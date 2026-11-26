"""Round 2 of the isolated feasibility test: compact EBNF grammar compiled from the draft schema (synthetic transcripts only).
usage: python -B structured_feasibility_ebnf.py"""
import gc
import json
import sys
import time
from pathlib import Path

import openvino_genai as ovg

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import structured_feasibility as F  # noqa: E402  (same isolated test module; builds its own pipeline)

GRAMMAR = (F.EXP7 / "design" / "S1_1_output_grammar.ebnf").read_text(encoding="utf-8")


def run_one(prompt, max_new):
    t0 = time.perf_counter()
    pipe = ovg.LLMPipeline(str(F.MODEL), "GPU", CACHE_DIR=str(F.CACHE))
    load_s = time.perf_counter() - t0
    tok = pipe.get_tokenizer()
    text_in = tok.apply_chat_template([{"role": "user", "content": prompt}], add_generation_prompt=True, extra_context={"enable_thinking": False})
    g = pipe.get_generation_config()
    g.max_new_tokens, g.do_sample, g.apply_chat_template = max_new, False, False
    g.structured_output_config = ovg.StructuredOutputConfig(grammar=GRAMMAR)
    t1 = time.perf_counter()
    res = pipe.generate([text_in], g)
    wall = time.perf_counter() - t1
    pm = res.perf_metrics
    o = {"text": res.texts[0], "load_s": round(load_s, 2), "gen_s": round(wall, 2), "in_tokens": int(pm.get_num_input_tokens()), "out_tokens": int(pm.get_num_generated_tokens())}
    del pipe, res
    gc.collect()
    return o


if __name__ == "__main__":
    only = sys.argv[1] if len(sys.argv) > 1 else "all"
    jobs = [("syn1", "R1")] if only == "smoke" else [(c, m) for c in F.CASES for m in ("R1", "R0")]
    log = []
    for case, m in jobs:
        try:
            o = run_one(F.build_prompt(F.CASES[case], m), 1500)
            r = F.check(o["text"])
            row = {"case": case, "render": m, "constrained": "ebnf_compact", **{x: o[x] for x in ("load_s", "gen_s", "in_tokens", "out_tokens")}, **r, "text": o["text"]}
        except Exception as e:
            row = {"case": case, "render": m, "constrained": "ebnf_compact", "exception": f"{type(e).__name__}: {str(e)[:400]}"}
        log.append(row)
        print({x: row.get(x) for x in ("case", "render", "gen_s", "out_tokens", "valid_json", "schema_ok", "reported_by_values", "chief_complaint", "exception")}, flush=True)
        (F.RES / f"ebnf_{only}.json").write_text(json.dumps(log, indent=1, ensure_ascii=False), encoding="utf-8")
