"""Azure ML scoring script for Qwen3-0.6B (OpenVINO FP16) with the frozen H1 prompt (EXP_008).

Same asynchronous protocol as the earlier 1.7B endpoint, so the application only needs a new endpoint URL/key (or nothing, if the deployment is added to the same endpoint):
    {"action": "submit", "compact_transcript": {...}}   -> {"job_id": ..., "state": "queued"}            (returns immediately)
    {"action": "status", "job_id": "..."}               -> {"state": queued|running|completed|failed, ...}
    {"action": "result", "job_id": "..."}               -> {"ok": true, "extraction": <raw parsed model JSON>, "metadata": {...}, "evidence": {...}}
Why asynchronous: a managed online endpoint cuts a request at 180 s; an extraction can take longer. Jobs live in memory of ONE instance (instance_count must stay 1; a restart loses them).

Deviations from the EXP_008 experiment (it ran on an Intel GPU): the device comes from OV_DEVICE (default "CPU"; Azure ML GPU sizes are NVIDIA), so outputs are not guaranteed
to be token-identical to the experiment. Everything else follows the experiment: greedy decoding, thinking off, max_new_tokens 6144, a fresh pipeline per job, the frozen H1 prompt
(SHA-256 checked), the existing prompt builder, parser and schema validator. The output is never repaired. The weights are SHA-256 checked once in init().
"""
from __future__ import annotations

import hashlib
import json
import os
import queue
import sys
import threading
import time
import types
import uuid
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent                    # the bundle: score.py + frozen modules, assembled by prepare_code_dir.ps1
sys.path.insert(0, str(HERE))
try:
    import dotenv  # noqa: F401
except ImportError:                                       # the frozen 0.6B code calls load_dotenv(); the inference image does not need python-dotenv
    sys.modules["dotenv"] = types.SimpleNamespace(load_dotenv=lambda *a, **k: False)

EXPECTED_PROMPT_SHA256 = "dc10ba065c9f1acaa237d106bd97b451ddfe1efcd94117b727d6585511f79cd8"          # H1 (EXP_008 config/H1_FREEZE.json)
EXPECTED_WEIGHTS_SHA256 = "ba7fbd17b63ab208ea1cbe26dc41e7b2d31e9128f22a7b08d69e4b12253b0c75"         # Qwen3-0.6B-ov-fp16 openvino_model.bin (EXP_002 conversion_record.json)
MAX_NEW_TOKENS = 6144                                     # same as the EXP_008 run
PROMPT_FILE = HERE / "H1_hybrid_prompt.txt"

_state: dict = {"ready": False, "error": None}
_jobs: dict[str, dict] = {}
_queue: "queue.Queue[str]" = queue.Queue()
_lock = threading.Lock()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while block := f.read(1 << 22):
            h.update(block)
    return h.hexdigest()


def _find_model_dir() -> Path:
    # Azure ML mounts a custom-container model at <model_mount_path>/<model name>/<version>/<registered folder>, so the depth varies: search recursively.
    base = Path(os.environ.get("AZUREML_MODEL_DIR", ""))
    if (base / "openvino_model.xml").exists():
        return base
    hits = sorted(base.rglob("openvino_model.xml"))
    if not hits:
        raise FileNotFoundError(f"openvino_model.xml not found under AZUREML_MODEL_DIR={base}")
    return hits[0].parent


def init() -> None:
    """Azure ML calls this once per instance. Fails loudly (and keeps the endpoint unhealthy) if anything frozen does not match."""
    model_dir = _find_model_dir()
    if _sha256(PROMPT_FILE) != EXPECTED_PROMPT_SHA256:
        raise RuntimeError("H1 prompt hash mismatch")
    if _sha256(model_dir / "openvino_model.bin") != EXPECTED_WEIGHTS_SHA256:
        raise RuntimeError("openvino_model.bin SHA-256 mismatch")
    _state.update(model_dir=model_dir, device=os.environ.get("OV_DEVICE", "CPU"), ready=True)
    threading.Thread(target=_worker, name="h1-worker", daemon=True).start()          # ONE worker: one generation at a time


def _generate(prompt: str) -> dict:
    """Mirrors the EXP_008 client (fresh pipeline per job, tokenizer chat template with thinking off, greedy decoding) except for the device; see the module docstring."""
    import openvino_genai as ovg
    pipe = ovg.LLMPipeline(str(_state["model_dir"]), _state["device"])
    tok = pipe.get_tokenizer()
    templated = tok.apply_chat_template([{"role": "user", "content": prompt}], add_generation_prompt=True, extra_context={"enable_thinking": False})
    g = pipe.get_generation_config()
    g.max_new_tokens, g.do_sample, g.apply_chat_template = MAX_NEW_TOKENS, False, False
    t0 = time.perf_counter()
    res = pipe.generate([templated], g)
    wall = time.perf_counter() - t0
    pm = res.perf_metrics
    n_out, n_in = int(pm.get_num_generated_tokens()), int(pm.get_num_input_tokens())
    out = {"text": res.texts[0], "finish_reason": "length" if n_out >= MAX_NEW_TOKENS else "stop", "input_tokens": n_in, "output_tokens": n_out, "generation_seconds": round(wall, 1)}
    del pipe, res
    return out


def run_extraction(compact: dict, generate=_generate) -> dict:
    """Pure pipeline (injectable generator for tests): prompt -> model -> frozen parser -> frozen validator -> evidence resolution. No repair of the output."""
    from clinical_extraction import evidence
    from direct_inference_baseline.evaluation import schema_validator as SV
    from direct_inference_baseline.inference import inference_runner as IR
    from direct_inference_baseline.inference.output_parser import parse_response
    prompt = IR.build_prompt(compact["encounter_id"], compact, PROMPT_FILE.read_text(encoding="utf-8"))
    started = datetime.now(timezone.utc).isoformat()
    gen = generate(prompt)
    parsed = parse_response(gen["text"], gen["finish_reason"])
    meta = {"encounter_id": compact["encounter_id"], "prompt_sha256": EXPECTED_PROMPT_SHA256, "model_weights_sha256": EXPECTED_WEIGHTS_SHA256, "device": _state.get("device"),
            "max_new_tokens": MAX_NEW_TOKENS, "prompt": "H1 hybrid (EXP_008)", "model": {"model_id": "Qwen/Qwen3-0.6B", "weights_precision": "FP16 (OpenVINO IR)"},
            "evidence_citations": "not requested by the H1 prompt (evidence_ids are expected to be empty)", "started_at": started, "ended_at": datetime.now(timezone.utc).isoformat(), "input_tokens": gen["input_tokens"],
            "output_tokens": gen["output_tokens"], "finish_reason": gen["finish_reason"], "parse_status": parsed.status, "parse_notes": parsed.notes,
            "generation_seconds": gen["generation_seconds"], "frozen_client_used": False,
            "note": "Azure ML path: device from OV_DEVICE (CPU by default). Outputs are not guaranteed identical to the Intel-GPU experiment."}
    if parsed.status != "ok":
        return {"ok": False, "metadata": meta}                                           # truncated / invalid JSON is a failure, never a success
    report = SV.validate(parsed.data)
    meta["schema_validation"] = {"compliant": bool(report.compliant), "violation_counts": dict(report.counts)}
    return {"ok": True, "extraction": parsed.data, "metadata": meta, "evidence": evidence.resolve_all(parsed.data, compact)}


def _worker() -> None:
    while True:
        job_id = _queue.get()
        job = _jobs[job_id]
        job.update(state="running", started_at=time.time())
        try:
            job["result"] = run_extraction(job.pop("compact"))
            job["state"] = "completed" if job["result"]["ok"] else "failed"
            if not job["result"]["ok"]:
                job["error"] = {"code": job["result"]["metadata"]["parse_status"]}
        except Exception as exc:                                                           # noqa: BLE001  (message only; no transcript text is stored in errors)
            job.update(state="failed", error={"code": "inference_error", "type": type(exc).__name__})
        job["finished_at"] = time.time()


def handle(payload: dict) -> dict:
    """Request router (no model needed for submit/status validation)."""
    from clinical_extraction.compact import CompactTranscriptError, validate_compact
    action = payload.get("action")
    if action == "submit":
        compact = payload.get("compact_transcript")
        try:
            warnings = validate_compact(compact)
        except CompactTranscriptError as exc:
            return {"error": "invalid_compact_transcript", "detail": str(exc)}
        if not _state.get("ready"):
            return {"error": "model_not_ready"}
        with _lock:
            running = [j for j in _jobs.values() if j["state"] in ("queued", "running")]
            if running:
                return {"error": "busy", "detail": "One extraction at a time on this instance."}
            job_id = uuid.uuid4().hex
            _jobs[job_id] = {"state": "queued", "created_at": time.time(), "compact": compact, "warnings": warnings}
        _queue.put(job_id)
        return {"job_id": job_id, "state": "queued", "warnings": warnings}
    if action in ("status", "result"):
        job = _jobs.get(str(payload.get("job_id")))
        if job is None:
            return {"error": "unknown_job"}
        if action == "status":
            return {"job_id": payload["job_id"], "state": job["state"], "error": job.get("error"), "elapsed_seconds": round((job.get("finished_at") or time.time()) - job["created_at"], 1)}
        if job["state"] not in ("completed", "failed"):
            return {"error": "not_finished", "state": job["state"]}
        return job.get("result") or {"ok": False, "error": job.get("error")}
    return {"error": "unknown_action", "detail": "use submit, status or result"}


def run(raw_data) -> str:
    """Azure ML entry point."""
    try:
        payload = json.loads(raw_data) if isinstance(raw_data, (str, bytes)) else raw_data
        if not isinstance(payload, dict):
            raise ValueError("body must be a JSON object")
        return json.dumps(handle(payload), ensure_ascii=False)
    except Exception as exc:                                                                # noqa: BLE001
        return json.dumps({"error": "bad_request", "detail": type(exc).__name__})
