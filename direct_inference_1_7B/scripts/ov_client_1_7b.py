"""OpenVINO GenAI client for Qwen3-1.7B (GPU).  Same generation approach as the 0.6B EXP_003/EXP_004 client (fresh LLMPipeline per encounter, manual Qwen chat template with
thinking disabled, greedy decoding, model's own EOS ids), with two additions required by the 1.7B plan:
  * system-wide memory sampling during load+generation (the UHD 620 uses shared system RAM, so process RSS alone under-reports),
  * a hard refusal to run on anything but the requested device (no CPU fallback; GenAI raises if the device is unavailable)."""
import gc
import threading
import time

import psutil

import common_1_7b as C
from direct_inference_baseline.inference.base_client import BaseClient, GenerationResult, PermanentInferenceError, TransientInferenceError


class MemorySampler:
    """Samples system-wide used/available RAM and this process' RSS every 0.5 s."""

    def __init__(self, interval=0.5):
        self.interval, self._stop = interval, threading.Event()
        self.peak_used_mb = self.min_available_mb = self.peak_rss_mb = None

    def _run(self):
        p = psutil.Process()
        while not self._stop.is_set():
            vm = psutil.virtual_memory()
            used, avail, rss = (vm.total - vm.available) / 2**20, vm.available / 2**20, p.memory_info().rss / 2**20
            self.peak_used_mb = used if self.peak_used_mb is None else max(self.peak_used_mb, used)
            self.min_available_mb = avail if self.min_available_mb is None else min(self.min_available_mb, avail)
            self.peak_rss_mb = rss if self.peak_rss_mb is None else max(self.peak_rss_mb, rss)
            self._stop.wait(self.interval)

    def __enter__(self):
        self._t = threading.Thread(target=self._run, daemon=True)
        self._t.start()
        return self

    def __exit__(self, *a):
        self._stop.set()
        self._t.join(timeout=3)


class OVClient17B(BaseClient):
    provider = "openvino_genai"

    def __init__(self, device: str = "GPU", model_dir=C.OV_MODEL_DIR, cache_dir=None, enable_thinking: bool = False):
        assert device == "GPU", "the 1.7B track is GPU-first; any other device must be a separately documented, approved diagnostic"
        self.device, self.model_dir, self.cache_dir, self.enable_thinking = device, model_dir, cache_dir, enable_thinking
        self.perf_log = []

    def describe(self) -> dict:
        import openvino
        import openvino_genai
        return {"provider": self.provider, "model_id": C.MODEL_ID, "model_revision_commit": C.REVISION, "deployment_name": None, "device": self.device,
                "runtime": "openvino_genai.LLMPipeline", "openvino": openvino.get_version(), "openvino_genai": openvino_genai.__version__,
                "converted_model_dir": str(self.model_dir.relative_to(C.TRACK)).replace("\\", "/"), "weights_precision": "FP16 (converted from BF16 source weights)",
                "compiled_model_cache": str(self.cache_dir),
                "generation": {"do_sample": False, "enable_thinking": self.enable_thinking, "chat_template": "tokenizer.apply_chat_template(add_generation_prompt=True, enable_thinking=False); GenAI template disabled",
                               "pipeline_per_encounter": True},
                "parameter_support": {"temperature": "not applied (greedy)", "top_p": "not applied (greedy)", "top_k": "not applied (greedy)", "max_new_tokens": "applied",
                                      "enable_thinking": "applied via chat template (False)"}}

    def _generate_once(self, user_prompt: str, max_new_tokens: int) -> GenerationResult:
        import openvino_genai as ovg
        proc = psutil.Process()
        base_avail = psutil.virtual_memory().available / 2**20
        try:
            with MemorySampler() as ms:
                t0 = time.perf_counter()
                pipe = ovg.LLMPipeline(str(self.model_dir), self.device, CACHE_DIR=str(self.cache_dir))
                load_s = time.perf_counter() - t0
                tok = pipe.get_tokenizer()
                prompt = tok.apply_chat_template([{"role": "user", "content": user_prompt}], add_generation_prompt=True, extra_context={"enable_thinking": self.enable_thinking})
                g = pipe.get_generation_config()
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
        eff = {k: getattr(g, k, None) for k in ("max_new_tokens", "do_sample", "temperature", "top_p", "top_k", "repetition_penalty", "num_beams", "eos_token_id", "apply_chat_template")}
        eff["stop_token_ids"] = sorted(getattr(g, "stop_token_ids", []) or [])
        perf = {"load_compile_seconds": round(load_s, 3), "first_token_latency_s(prefill+1st token)": round(ttft, 3), "prefill_tokens_per_second": round(n_in / ttft, 1) if ttft else None,
                "decode_tokens_per_second": round(1 / tpot, 3) if tpot else None, "generation_wall_seconds": round(wall, 3), "input_tokens": n_in, "output_tokens": n_out,
                "tokens_per_second_overall": round(n_out / wall, 3) if wall else None, "rss_mb_after": round(mem.rss / 2**20),
                "peak_working_set_mb_process_so_far": round(getattr(mem, "peak_wset", 0) / 2**20),
                "sampled_peak_process_rss_mb": round(ms.peak_rss_mb or 0), "sampled_peak_system_used_mb": round(ms.peak_used_mb or 0),
                "sampled_min_system_available_mb": round(ms.min_available_mb or 0), "system_available_mb_before": round(base_avail), "effective_generation_config": eff}
        self.perf_log.append(perf)
        text = res.texts[0]
        finish = "length" if n_out >= max_new_tokens else "stop"
        del pipe, res, pm, tok
        gc.collect()
        return GenerationResult(text=text, finish_reason=finish, prompt_tokens=n_in, completion_tokens=n_out, latency_seconds=wall, notes=[perf])
