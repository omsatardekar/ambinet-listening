"""Local Hugging Face Transformers client (CPU). Uses the Qwen3 chat template in NON-thinking mode and greedy decoding."""
from __future__ import annotations

import os
import time

from ..config.model_config import GenerationConfig
from .base_client import BaseClient, GenerationResult, PermanentInferenceError, TransientInferenceError


class HuggingFaceClient(BaseClient):
    provider = "huggingface"

    def __init__(self, model_id: str = "Qwen/Qwen3-0.6B", device: str = "cpu", cfg: GenerationConfig | None = None):
        self.model_id, self.device, self.cfg = model_id, device, cfg or GenerationConfig()
        self.tok = self.model = None

    def load(self):
        if self.model is not None:
            return self
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        nt = os.getenv("HF_NUM_THREADS")
        if nt:
            torch.set_num_threads(int(nt))
        self.tok = AutoTokenizer.from_pretrained(self.model_id)
        dtype = getattr(torch, self.cfg.torch_dtype)
        self.model = AutoModelForCausalLM.from_pretrained(self.model_id, dtype=dtype).to(self.device).eval()
        return self

    def _revision(self):
        """Commit hash of the downloaded snapshot (taken from the local Hugging Face cache path)."""
        try:
            from huggingface_hub import try_to_load_from_cache
            p = try_to_load_from_cache(self.model_id, "config.json")
            return str(p).replace("\\", "/").split("/snapshots/")[1].split("/")[0] if p else None
        except Exception:
            return None

    def describe(self) -> dict:
        d = {"provider": "huggingface", "model_id": self.model_id, "deployment_name": None, "device": self.device,
             "generation": self.cfg.as_dict(),
             "parameter_support": {"temperature": "not applied (greedy)", "top_p": "not applied (greedy)", "top_k": "not applied (greedy)",
                                   "max_new_tokens": "applied", "enable_thinking": "applied via chat template (False)"}}
        d["model_revision_commit"] = self._revision()
        if self.model is not None:
            import torch
            d["torch_threads"] = torch.get_num_threads()
            d["parameters"] = sum(p.numel() for p in self.model.parameters())
        return d

    def _generate_once(self, user_prompt: str, max_new_tokens: int) -> GenerationResult:
        import torch
        self.load()
        msgs = [{"role": "user", "content": user_prompt}]
        text = self.tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, enable_thinking=self.cfg.enable_thinking)
        enc = self.tok(text, return_tensors="pt").to(self.device)
        n_in = enc["input_ids"].shape[1]
        torch.manual_seed(self.cfg.seed)
        t0 = time.perf_counter()
        try:
            with torch.inference_mode():
                out = self.model.generate(**enc, max_new_tokens=max_new_tokens, do_sample=False, temperature=None, top_p=None, top_k=None,
                                          repetition_penalty=self.cfg.repetition_penalty, pad_token_id=self.tok.pad_token_id)
        except RuntimeError as e:      # e.g. transient out-of-memory
            if "out of memory" in str(e).lower() or "alloc" in str(e).lower():
                raise TransientInferenceError(str(e)) from e
            raise PermanentInferenceError(str(e)) from e
        dt = time.perf_counter() - t0
        gen = out[0, n_in:]
        eos_ids = {self.tok.eos_token_id, self.tok.convert_tokens_to_ids("<|im_end|>")} - {None}
        finished = len(gen) > 0 and int(gen[-1]) in eos_ids
        return GenerationResult(text=self.tok.decode(gen, skip_special_tokens=True), finish_reason="stop" if finished else "length",
                                prompt_tokens=int(n_in), completion_tokens=int(len(gen)), latency_seconds=dt)
