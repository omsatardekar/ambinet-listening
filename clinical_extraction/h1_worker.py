"""Local inference worker: Qwen3-0.6B (OpenVINO FP16) with the FROZEN H1 prompt (EXP_008). Runs in the separate OpenVINO environment, never in the backend venv.

usage:  <openvino python> -B -s h1_worker.py --input <compact.json> --out <dir> [--device AUTO|GPU|CPU] [--check]

Same generation as the EXP_008 runner: greedy decoding, thinking off, max_new_tokens 6144, a fresh LLMPipeline per encounter. The prompt text is built with the
existing builder (inference_runner.build_prompt) and verified against the frozen sha256 before anything is loaded. The model output is parsed with the existing
parser and checked with the existing schema validator; it is never repaired or rewritten. Progress goes to the parent as JSON lines on stdout ({"event": ...});
no transcript or extraction text is printed. Exit codes: 0 finished (see result.json), 2 pre-condition failed (nothing loaded), 3 inference error.
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import sys
import time
import types
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "finetune_slm"))                                           # the package direct_inference_baseline lives in finetune_slm/
sys.dont_write_bytecode = True
try:                                                                              # the existing settings module imports python-dotenv; the inference env does not need it
    import dotenv  # noqa: F401
except ImportError:
    sys.modules["dotenv"] = types.SimpleNamespace(load_dotenv=lambda *a, **k: False)

EXP8 = ROOT / "finetune_slm" / "experiments" / "qwen3_0.6b_baseline" / "EXP_008_QWEN3_0.6B_HYBRID_P02_S1"
EXP2 = ROOT / "finetune_slm" / "experiments" / "qwen3_0.6b_baseline" / "EXP_002_QWEN3_0.6B_GPU_DIRECT"
PROMPT_FILE = EXP8 / "prompts" / "H1_hybrid_prompt.txt"
FREEZE = EXP8 / "config" / "H1_FREEZE.json"
MODEL_DIR = EXP2 / "models" / "Qwen3-0.6B-ov-fp16"
CONVERSION = EXP2 / "conversion_record.json"
MAX_NEW_TOKENS = 6144
REQUIRED = ["openvino_model.xml", "openvino_model.bin", "openvino_tokenizer.xml", "openvino_tokenizer.bin", "openvino_detokenizer.xml", "openvino_detokenizer.bin",
            "config.json", "tokenizer.json", "tokenizer_config.json", "chat_template.jinja"]
MODEL_ID, MODEL_REVISION = "Qwen/Qwen3-0.6B", "c1899de289a04d12100db370d81485cdf75e47ca"


def emit(event: str, **kw) -> None:
    print(json.dumps({"event": event, **kw}), flush=True)


def sha256_file(path: Path, chunk: int = 1 << 22) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while block := f.read(chunk):
            h.update(block)
    return h.hexdigest()


def fail(out: Path, code: str, message: str, exit_code: int = 2, **extra) -> None:
    (out / "result.json").write_text(json.dumps({"ok": False, "code": code, "message": message, **extra}, indent=1), encoding="utf-8")
    emit("failed", code=code, message=message)
    sys.exit(exit_code)


def pick_device(requested: str) -> str:
    """GPU when OpenVINO sees one (the device used for every EXP_008 number), otherwise CPU. An explicit GPU/CPU request is honoured as given."""
    requested = (requested or "AUTO").upper()
    if requested in ("GPU", "CPU"):
        return requested
    import openvino as ov
    return "GPU" if any(d.startswith("GPU") for d in ov.Core().available_devices) else "CPU"


def verify_preconditions(out: Path, ram_gate_gib: float, check_only: bool) -> dict:
    frozen = json.loads(FREEZE.read_text(encoding="utf-8"))["prompt_sha256"]
    prompt_sha = sha256_file(PROMPT_FILE)
    if prompt_sha != frozen:
        fail(out, "prompt_hash_mismatch", "The H1 prompt does not match the frozen hash.", prompt_sha=prompt_sha)
    rec = json.loads(CONVERSION.read_text(encoding="utf-8"))["converted_files"]
    for name in REQUIRED:
        p = MODEL_DIR / name
        if not p.exists():
            fail(out, "model_files_missing", f"Model file missing: {name}. Run `git lfs pull` (the weights are stored with Git LFS) or copy the model folder.")
        if name in rec and p.stat().st_size != rec[name]["bytes"]:
            hint = " It is a Git LFS pointer, not the real file: run `git lfs install` and `git lfs pull`." if p.stat().st_size < 1024 and rec[name]["bytes"] > 4096 else ""
            fail(out, "model_file_size_mismatch", f"{name} has {p.stat().st_size} bytes, expected {rec[name]['bytes']}.{hint}")
    bin_path = MODEL_DIR / "openvino_model.bin"
    marker = out.parent.parent / "model_verified_h1.json"                         # skips re-hashing 1.2 GB when size and mtime are unchanged
    stamp = {"size": bin_path.stat().st_size, "mtime_ns": bin_path.stat().st_mtime_ns, "sha256": rec["openvino_model.bin"]["sha256"]}
    if not (marker.exists() and json.loads(marker.read_text(encoding="utf-8")) == stamp):
        if sha256_file(bin_path) != stamp["sha256"]:
            fail(out, "model_weights_hash_mismatch", "openvino_model.bin SHA-256 does not match the conversion record.")
        marker.write_text(json.dumps(stamp), encoding="utf-8")
    import psutil
    available = psutil.virtual_memory().available / 2**30
    if not check_only and available < ram_gate_gib:
        fail(out, "insufficient_memory", f"Available RAM {available:.2f} GiB is below the required {ram_gate_gib:.1f} GiB. Close other applications and retry.", available_gib=round(available, 3))
    return {"prompt_sha256": prompt_sha, "model_weights_sha256": stamp["sha256"], "available_ram_gib_before_load": round(available, 3)}


def generate(prompt: str, device: str, cache_dir: Path) -> dict:
    """Identical to the EXP_004/EXP_008 OpenVINO client: fresh pipeline, chat template applied by the tokenizer with thinking off, greedy decoding."""
    import openvino_genai as ovg
    t0 = time.perf_counter()
    pipe = ovg.LLMPipeline(str(MODEL_DIR), device, CACHE_DIR=str(cache_dir))
    load_s = time.perf_counter() - t0
    tok = pipe.get_tokenizer()
    templated = tok.apply_chat_template([{"role": "user", "content": prompt}], add_generation_prompt=True, extra_context={"enable_thinking": False})
    g = pipe.get_generation_config()
    g.max_new_tokens, g.do_sample, g.apply_chat_template = MAX_NEW_TOKENS, False, False
    t1 = time.perf_counter()
    res = pipe.generate([templated], g)
    wall = time.perf_counter() - t1
    pm = res.perf_metrics
    n_out, n_in = int(pm.get_num_generated_tokens()), int(pm.get_num_input_tokens())
    ttft, tpot = pm.get_ttft().mean / 1000.0, pm.get_tpot().mean / 1000.0
    out = {"text": res.texts[0], "finish_reason": "length" if n_out >= MAX_NEW_TOKENS else "stop", "input_tokens": n_in, "output_tokens": n_out,
           "load_compile_seconds": round(load_s, 2), "generation_wall_seconds": round(wall, 2), "first_token_latency_s": round(ttft, 2),
           "decode_tokens_per_second": round(1 / tpot, 2) if tpot else None}
    del pipe, res, pm, tok
    gc.collect()
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", help="compact transcript JSON")
    ap.add_argument("--out", required=True)
    ap.add_argument("--device", default="AUTO")
    ap.add_argument("--ram-gate-gib", type=float, default=3.5)
    ap.add_argument("--cache-dir", default=None)
    ap.add_argument("--check", action="store_true", help="verify files, imports and device only; load no model")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    emit("preparing", message="Verifying the prompt and the model files")
    pre = verify_preconditions(out, a.ram_gate_gib, a.check)
    from direct_inference_baseline.evaluation import schema_validator as SV
    from direct_inference_baseline.inference import inference_runner as IR
    from direct_inference_baseline.inference.output_parser import parse_response
    import openvino_genai  # noqa: F401  (fail early if the environment is incomplete)
    device = pick_device(a.device)
    if a.check:
        emit("check_ok", device=device, **pre, max_new_tokens=MAX_NEW_TOKENS)
        (out / "result.json").write_text(json.dumps({"ok": True, "check_only": True, "device": device, **pre}, indent=1), encoding="utf-8")
        return

    compact = json.loads(Path(a.input).read_text(encoding="utf-8"))
    emit("reading_transcript", message="Building the H1 prompt")
    prompt = IR.build_prompt(compact["encounter_id"], compact, PROMPT_FILE.read_text(encoding="utf-8"))
    cache_dir = Path(a.cache_dir) if a.cache_dir else out.parent.parent / "ov_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()
    emit("loading_model", message=f"Loading Qwen3-0.6B on {device}")
    t0 = time.perf_counter()
    emit("extracting", message="Model is generating the extraction")
    try:
        gen = generate(prompt, device, cache_dir)
    except (RuntimeError, MemoryError) as exc:
        text = f"{type(exc).__name__}: {str(exc)[:300]}"
        code = "out_of_memory" if ("memory" in text.lower() or "out of" in text.lower()) else "inference_error"
        fail(out, code, "Out of memory during extraction." if code == "out_of_memory" else "The model could not complete the extraction.", exit_code=3, detail=text)
    wall = time.perf_counter() - t0
    ended = datetime.now(timezone.utc).isoformat()

    emit("validating_output", message="Parsing and validating the output")
    parsed = parse_response(gen["text"], gen["finish_reason"])
    schema = None
    if parsed.status == "ok":
        report = SV.validate(parsed.data)
        schema = {"compliant": bool(report.compliant), "violation_counts": dict(report.counts), "violations_sample": list(report.violations[:15])}
        (out / "extraction_raw.json").write_text(json.dumps(parsed.data, ensure_ascii=False, indent=1), encoding="utf-8")      # exactly the parser's object
    (out / "model_response_raw.txt").write_text(gen["text"] or "", encoding="utf-8")
    import openvino
    metadata = {
        "encounter_id": compact["encounter_id"], "prompt": "H1 hybrid (EXP_008)", "prompt_sha256": pre["prompt_sha256"], "prompt_file": str(PROMPT_FILE.relative_to(ROOT)).replace("\\", "/"),
        "model": {"model_id": MODEL_ID, "model_revision_commit": MODEL_REVISION, "weights_precision": "FP16 (OpenVINO IR)", "runtime": f"openvino_genai {openvino_genai.__version__}, openvino {openvino.get_version()}"},
        "inference_location": "local_openvino", "model_weights_sha256": pre["model_weights_sha256"], "device": device,
        "generation": {"do_sample": False, "enable_thinking": False, "max_new_tokens": MAX_NEW_TOKENS, "fresh_pipeline_per_encounter": True},
        "max_new_tokens": MAX_NEW_TOKENS, "started_at": started, "ended_at": ended, "wall_seconds": round(wall, 1), "input_tokens": gen["input_tokens"], "output_tokens": gen["output_tokens"],
        "finish_reason": gen["finish_reason"], "parse_status": parsed.status, "parse_notes": parsed.notes, "schema_validation": schema,
        "evidence_citations": "not requested by the H1 prompt (evidence_ids are expected to be empty)",
        "performance": {k: gen[k] for k in ("load_compile_seconds", "generation_wall_seconds", "first_token_latency_s", "decode_tokens_per_second")},
        "available_ram_gib_before_load": pre["available_ram_gib_before_load"], "retries": 0,
    }
    (out / "result.json").write_text(json.dumps({"ok": parsed.status == "ok", "code": None if parsed.status == "ok" else parsed.status, "metadata": metadata}, indent=1), encoding="utf-8")
    emit("finished", parse_status=parsed.status, finish_reason=gen["finish_reason"])


if __name__ == "__main__":
    main()
