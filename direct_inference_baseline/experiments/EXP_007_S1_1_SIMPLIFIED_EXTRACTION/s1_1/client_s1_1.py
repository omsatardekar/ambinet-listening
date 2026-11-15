"""Client for arm B3: the existing OpenVINOGenAIClient (EXP_004, unmodified) subclassed in this experiment ONLY. Adds grammar-constrained decoding (and an optional answer prefix) to generation.
Everything else is the parent's behaviour (fresh pipeline per encounter, greedy, chat template with thinking off, same perf log). The project runtime is not modified."""
import gc
import time
from pathlib import Path

import openvino_genai as ovg
import psutil

from ov_client import OpenVINOGenAIClient  # noqa: E402  (EXP_004 experiments dir is on sys.path in the runner)
from direct_inference_baseline.inference.base_client import GenerationResult, PermanentInferenceError, TransientInferenceError  # noqa: E402


class GrammarClient(OpenVINOGenAIClient):
    def __init__(self, device, cache_dir, grammar_text, prefix=""):
        super().__init__(device, cache_dir=cache_dir)
        self.grammar_text, self.prefix = grammar_text, prefix

    def describe(self) -> dict:
        d = super().describe()
        d["structured_decoding"] = {"type": "EBNF grammar (compiled from the S1.1 schema)", "answer_prefix": self.prefix or None}
        return d

    def _generate_once(self, user_prompt: str, max_new_tokens: int) -> GenerationResult:
        proc = psutil.Process()
        try:
            t0 = time.perf_counter()
            pipe = ovg.LLMPipeline(str(self.model_dir), self.device, CACHE_DIR=str(self.cache_dir))
            load_s = time.perf_counter() - t0
            tok = pipe.get_tokenizer()
            prompt = tok.apply_chat_template([{"role": "user", "content": user_prompt}], add_generation_prompt=True, extra_context={"enable_thinking": self.enable_thinking}) + self.prefix
            g = pipe.get_generation_config()
            g.max_new_tokens = max_new_tokens
            g.do_sample = False
            g.apply_chat_template = False
            g.structured_output_config = ovg.StructuredOutputConfig(grammar=self.grammar_text)
            t1 = time.perf_counter()
            res = pipe.generate([prompt], g)
            wall = time.perf_counter() - t1
        except RuntimeError as e:
            if "out of" in str(e).lower() and "memory" in str(e).lower():
                raise TransientInferenceError(str(e)) from e
            raise PermanentInferenceError(f"{type(e).__name__}: {e}") from e
        pm = res.perf_metrics
        n_out, n_in = int(pm.get_num_generated_tokens()), int(pm.get_num_input_tokens())
        ttft, tpot = pm.get_ttft().mean / 1000.0, pm.get_tpot().mean / 1000.0
        mem = proc.memory_info()
        perf = {"load_compile_seconds": round(load_s, 3), "first_token_latency_s(prefill+1st token)": round(ttft, 3), "prefill_tokens_per_second": round(n_in / ttft, 1) if ttft else None,
                "decode_tokens_per_second": round(1 / tpot, 3) if tpot else None, "generation_wall_seconds": round(wall, 3), "input_tokens": n_in, "output_tokens": n_out,
                "tokens_per_second_overall": round(n_out / wall, 3) if wall else None, "rss_mb_after": round(mem.rss / 2**20), "peak_working_set_mb_process_so_far": round(getattr(mem, "peak_wset", 0) / 2**20),
                "effective_generation_config": {"max_new_tokens": max_new_tokens, "do_sample": False, "structured_output": "grammar", "answer_prefix": self.prefix or None}}
        self.perf_log.append(perf)
        text = self.prefix + res.texts[0]                          # the prefix was supplied in the assistant turn; it is part of the answer
        finish = "length" if n_out >= max_new_tokens else "stop"
        del pipe, res, pm, tok
        gc.collect()
        return GenerationResult(text=text, finish_reason=finish, prompt_tokens=n_in, completion_tokens=n_out, latency_seconds=wall, notes=[perf])
