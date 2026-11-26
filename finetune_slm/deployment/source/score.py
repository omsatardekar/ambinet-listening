"""Azure ML scoring script for the FINE-TUNED Qwen3-0.6B (LoRA step 400, merged, OpenVINO FP16). Replaces finetune_slm/deployment/h1_baseline/score.py; same protocol, so the application needs no change:
    {"action": "submit", "compact_transcript": {...}}   -> {"job_id": ..., "state": "queued"}
    {"action": "status", "job_id": "..."}               -> {"state": queued|running|completed|failed, ...}
    {"action": "result", "job_id": "..."}               -> {"ok": true, "extraction": <full-structure JSON>, "metadata": {...}, "evidence": {...}}
Differences from the H1 version (the model is trained, so the pipeline follows the TRAINING format exactly):
  * prompt  = finetune_slm/data/round1_synthetic/prompt/short_prompt.txt (SHA-256 pinned) + one line per segment `[SEG0001] person_1 (DOCTOR): text`. Timestamps from the front end are NOT sent
    (the model was trained without them; they carry no clinical information). Only segment_id, speaker_id, role and text are used.
  * the model writes the COMPACT form (empty fields left out); codec.expand() restores the full structure (all keys, original order) before the existing validator and evidence resolver.
  * guard: parse -> deterministic repair of the known malformed patterns (json_guard.py; every repair is listed in metadata and sets needs_review) -> if still invalid, ONE regeneration
    with light sampling (greedy would repeat the same text) -> else failed (extraction_status "failed", clinician review required). A valid output is never altered.
The weights hash is checked in init(); the prompt hash is pinned too. Device from OV_DEVICE (default CPU).
"""
from __future__ import annotations

import hashlib
import json
import os
import queue
import re
import sys
import threading
import time
import types
import uuid
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
try:
    import dotenv  # noqa: F401
except ImportError:
    sys.modules["dotenv"] = types.SimpleNamespace(load_dotenv=lambda *a, **k: False)

PINNED = json.loads((HERE / "pinned_hashes.json").read_text(encoding="utf-8"))          # written by build_single_file_score.py (weights hash comes from the conversion)
EXPECTED_PROMPT_SHA256 = PINNED["short_prompt_sha256"]
EXPECTED_WEIGHTS_SHA256 = PINNED["openvino_model_bin_sha256"]
WINDOW_CHARS, WINDOW_OVERLAP = int(PINNED.get("window_chars", 7000)), int(PINNED.get("window_overlap", 4))                         # transcript characters per window (about 1,800 tokens) and segments shared between neighbouring windows
MODEL_ID = PINNED.get("model_label", "Qwen/Qwen3-0.6B + LoRA, merged")
MAX_NEW_TOKENS = 4096                                      # the longest compact answer in the test set is about 11,600 characters (< 4,000 tokens)
PROMPT_FILE = HERE / "short_prompt.txt"

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
    base = Path(os.environ.get("AZUREML_MODEL_DIR", ""))
    if (base / "openvino_model.xml").exists():
        return base
    hits = sorted(base.rglob("openvino_model.xml"))
    if not hits:
        raise FileNotFoundError(f"openvino_model.xml not found under AZUREML_MODEL_DIR={base}")
    return hits[0].parent


def init() -> None:
    model_dir = _find_model_dir()
    if _sha256(PROMPT_FILE) != EXPECTED_PROMPT_SHA256:
        raise RuntimeError("short prompt hash mismatch")
    if _sha256(model_dir / "openvino_model.bin") != EXPECTED_WEIGHTS_SHA256:
        raise RuntimeError("openvino_model.bin SHA-256 mismatch")
    _state.update(model_dir=model_dir, device=os.environ.get("OV_DEVICE", "CPU"), ready=True)
    threading.Thread(target=_worker, name="ft-worker", daemon=True).start()


def build_prompt(compact: dict) -> str:
    """Exactly the training input: short prompt with {ENCOUNTER_ID} and one line per segment. Timestamps are ignored."""
    lines = []
    for s in compact["segments"]:
        text = re.sub(r"\s+", " ", s["text"]).strip()
        lines.append(f"[{s['segment_id']}] {s['speaker_id']} ({s['role']}): {text}")
    return PROMPT_FILE.read_text(encoding="utf-8").replace("{ENCOUNTER_ID}", compact["encounter_id"]).replace("{TRANSCRIPT}", "\n".join(lines))


def _generate(prompt: str, sample: bool = False) -> dict:
    import openvino_genai as ovg
    pipe = ovg.LLMPipeline(str(_state["model_dir"]), _state["device"])
    tok = pipe.get_tokenizer()
    templated = tok.apply_chat_template([{"role": "user", "content": prompt}], add_generation_prompt=True, extra_context={"enable_thinking": False})
    g = pipe.get_generation_config()
    g.max_new_tokens, g.apply_chat_template = MAX_NEW_TOKENS, False
    if sample:
        g.do_sample, g.temperature, g.top_p = True, 0.3, 0.9
    else:
        g.do_sample = False
    t0 = time.perf_counter()
    res = pipe.generate([templated], g)
    wall = time.perf_counter() - t0
    pm = res.perf_metrics
    n_out, n_in = int(pm.get_num_generated_tokens()), int(pm.get_num_input_tokens())
    out = {"text": res.texts[0], "finish_reason": "length" if n_out >= MAX_NEW_TOKENS else "stop", "input_tokens": n_in, "output_tokens": n_out, "generation_seconds": round(wall, 1)}
    del pipe, res
    return out


def _parse(gen: dict):
    """text -> (full-structure object | None, notes). Truncated output (hit the token limit) is never repaired."""
    from compact_codec import expand
    from json_guard import parse_with_repair
    truncated = gen["finish_reason"] == "length"
    obj, notes = parse_with_repair(gen["text"])
    if truncated:
        notes = ["truncated: token limit reached"] + notes            # a repetition loop that hit the limit is repaired by rule R6 and always flagged
    if obj is None or not isinstance(obj, dict):
        return None, notes or ["no JSON object"]
    warnings: list = []
    return expand(obj, warnings=warnings), notes + warnings


def _extract_one(compact: dict, generate):
    """One window (or the whole transcript): generate, parse with the guard, one regeneration with light sampling if unparseable. -> (full | None, notes, gen, attempts)"""
    prompt = build_prompt(compact)
    gen = generate(prompt)
    full, notes = _parse(gen)
    attempts = 1
    if full is None:
        first_notes = notes
        gen = generate(prompt, True)
        full, notes = _parse(gen)
        attempts = 2
        notes = ["first attempt: " + "; ".join(first_notes)] + notes
    return full, notes, gen, attempts


def run_extraction(compact: dict, generate=_generate) -> dict:
    """Long consultations are cut into windows of about 1,800 tokens (the length the model was trained on), each window is extracted on its own and the results are merged."""
    from clinical_extraction import evidence
    from direct_inference_baseline.evaluation import schema_validator as SV
    from chunking import make_windows, merge
    started = datetime.now(timezone.utc).isoformat()
    windows = make_windows(compact["segments"], WINDOW_CHARS, WINDOW_OVERLAP)
    parts, all_notes, gens, failed, attempts = [], [], [], [], 0
    for k, w in enumerate(windows, 1):
        sub = {"encounter_id": compact["encounter_id"], "segments": w["segments"]} if len(windows) > 1 else compact
        full_w, notes, gen, att = _extract_one(sub, generate)
        attempts += att
        gens.append(gen)
        all_notes += [f"window {k}/{len(windows)}: {n}" for n in notes] if len(windows) > 1 else notes
        if full_w is None:
            failed.append(k)
        else:
            parts.append((w, full_w))
    full = merge(parts) if parts else None
    meta = {"encounter_id": compact["encounter_id"], "prompt_sha256": EXPECTED_PROMPT_SHA256, "model_weights_sha256": EXPECTED_WEIGHTS_SHA256, "device": _state.get("device"),
            "max_new_tokens": MAX_NEW_TOKENS, "prompt": "short prompt (trained format, no timestamps)", "model": {"model_id": MODEL_ID, "weights_precision": "FP16 (OpenVINO IR)"},
            "started_at": started, "ended_at": datetime.now(timezone.utc).isoformat(), "windows": len(windows), "failed_windows": failed,
            "input_tokens": sum(g["input_tokens"] for g in gens), "output_tokens": sum(g["output_tokens"] for g in gens),
            "finish_reason": "length" if any(g["finish_reason"] == "length" for g in gens) else "stop",
            "attempts": attempts, "guard_notes": all_notes, "generation_seconds": round(sum(g["generation_seconds"] for g in gens), 1)}
    if full is None:
        meta["extraction_status"] = "failed"
        meta["needs_review"] = True
        return {"ok": False, "metadata": meta}
    full["encounter_id"] = compact["encounter_id"]
    repaired = bool(failed) or any(re.search(r"(^|: )(R\d|first attempt|truncated)", n) for n in all_notes)
    report = SV.validate(full)
    meta["schema_validation"] = {"compliant": bool(report.compliant), "violation_counts": dict(report.counts)}
    meta["extraction_status"] = "partial" if failed else ("repaired" if repaired else "ok")
    meta["needs_review"] = bool(repaired or not report.compliant)
    return {"ok": True, "extraction": full, "metadata": meta, "evidence": evidence.resolve_all(full, compact)}


def _worker() -> None:
    while True:
        job_id = _queue.get()
        job = _jobs[job_id]
        job.update(state="running", started_at=time.time())
        try:
            job["result"] = run_extraction(job.pop("compact"))
            job["state"] = "completed" if job["result"]["ok"] else "failed"
            if not job["result"]["ok"]:
                job["error"] = {"code": "extraction_failed", "needs_review": True}
        except Exception as exc:                                                           # noqa: BLE001
            job.update(state="failed", error={"code": "inference_error", "type": type(exc).__name__})
        job["finished_at"] = time.time()


def handle(payload: dict) -> dict:
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
    try:
        payload = json.loads(raw_data) if isinstance(raw_data, (str, bytes)) else raw_data
        if not isinstance(payload, dict):
            raise ValueError("body must be a JSON object")
        return json.dumps(handle(payload), ensure_ascii=False)
    except Exception as exc:                                                                # noqa: BLE001
        return json.dumps({"error": "bad_request", "detail": type(exc).__name__})
