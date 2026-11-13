"""OpenVINO GenAI client for EXP_003 (subclass of the existing BaseClient; the existing module is not modified).
A FRESH LLMPipeline is created for every encounter: a reused LLMPipeline keeps the previous prompt's KV cache and skips prefill for a shared prefix,
which would make timings and numerics depend on encounter order (observed in EXP_002). Compiled-model caching (CACHE_DIR) keeps the reload cheap."""
import gc
import time

import psutil

from common import CACHE_DIR, OV_MODEL_DIR, SOURCE_REVISION  # noqa: F401
from direct_inference_baseline.inference.base_client import BaseClient, GenerationResult, PermanentInferenceError, TransientInferenceError


class OpenVINOGenAIClient(BaseClient):
    provider = "openvino_genai"

    def __init__(self, device: str = "GPU", model_dir=OV_MODEL_DIR, cache_dir=CACHE_DIR, enable_thinking: bool = False):
        self.device, self.model_dir, self.cache_dir, self.enable_thinking = device, model_dir, cache_dir, enable_thinking
        self.perf_log = []

    def describe(self) -> dict:
        import openvino
        import openvino_genai
        return {"provider": self.provider, "model_id": "Qwen/Qwen3-0.6B", "model_revision_commit": SOURCE_REVISION, "deployment_name": None,
                "device": self.device, "runtime": "openvino_genai.LLMPipeline", "openvino": openvino.get_version(), "openvino_genai": openvino_genai.__version__,
                "converted_model_dir": "experiments/EXP_002_QWEN3_0.6B_GPU_DIRECT/models/Qwen3-0.6B-ov-fp16", "weights_precision": "FP16 (converted from BF16 source weights)",
                "compiled_model_cache": "EXP_003/ov_cache",
                "generation": {"do_sample": False, "enable_thinking": self.enable_thinking, "chat_template": "tokenizer.apply_chat_template(add_generation_prompt=True, enable_thinking=False); GenAI template disabled",
                               "pipeline_per_encounter": True},
                "parameter_support": {"temperature": "not applied (greedy)", "top_p": "not applied (greedy)", "top_k": "not applied (greedy)", "max_new_tokens": "applied",
                                      "enable_thinking": "applied via chat template (False)"}}

    def _generate_once(self, user_prompt: str, max_new_tokens: int) -> GenerationResult:
        import openvino_genai as ovg
        proc = psutil.Process()
        try:
            t0 = time.perf_counter()
            pipe = ovg.LLMPipeline(str(self.model_dir), self.device, CACHE_DIR=str(self.cache_dir))
            load_s = time.perf_counter() - t0
            tok = pipe.get_tokenizer()
            prompt = tok.apply_chat_template([{"role": "user", "content": user_prompt}], add_generation_prompt=True,
                                             extra_context={"enable_thinking": self.enable_thinking})
            g = pipe.get_generation_config()          # keeps the model's own EOS / stop token ids, like transformers' generation_config
            g.max_new_tokens = max_new_tokens
            g.do_sample = False
            g.apply_chat_template = False
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
        eff = {k: getattr(g, k, None) for k in ("max_new_tokens", "do_sample", "temperature", "top_p", "top_k", "repetition_penalty", "num_beams", "eos_token_id",
                                                 "apply_chat_template")}
        eff["stop_token_ids"] = sorted(getattr(g, "stop_token_ids", []) or [])
        perf = {"load_compile_seconds": round(load_s, 3), "first_token_latency_s(prefill+1st token)": round(ttft, 3),
                "prefill_tokens_per_second": round(n_in / ttft, 1) if ttft else None, "decode_tokens_per_second": round(1 / tpot, 3) if tpot else None,
                "generation_wall_seconds": round(wall, 3), "input_tokens": n_in, "output_tokens": n_out,
                "tokens_per_second_overall": round(n_out / wall, 3) if wall else None, "rss_mb_after": round(mem.rss / 2**20),
                "peak_working_set_mb_process_so_far": round(getattr(mem, "peak_wset", 0) / 2**20), "effective_generation_config": eff}
        self.perf_log.append(perf)
        text = res.texts[0]
        finish = "length" if n_out >= max_new_tokens else "stop"
        del pipe, res, pm, tok
        gc.collect()
        return GenerationResult(text=text, finish_reason=finish, prompt_tokens=n_in, completion_tokens=n_out, latency_seconds=wall, notes=[perf])   # generation only, like EXP_001 (load time is in notes)
