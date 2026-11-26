"""Isolated inference wrapper for the FROZEN P02 model. Runs in the separate OpenVINO environment (never the backend venv).

usage:  <openvino python> -B -s inference_worker.py --input <compact.json> --out <dir> [--check]

Reuses the frozen components unchanged: OVClient17B (device "GPU", greedy, thinking off, max_new_tokens from common_1_7b), inference_runner.build_prompt,
output_parser.parse_response and the existing schema validator. It does not import run_prompt.py, the 50-record manifest or the development dataset, and it
does not repair or rewrite the model output. Progress is reported to the parent as JSON lines on stdout ({"event": ...}); no transcript or extraction text is
printed. Exit codes: 0 finished (see result.json), 2 pre-condition failed (nothing loaded), 3 inference error.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TRACK = ROOT / "finetune_slm/experiments/qwen3_1.7b_track"
sys.path.insert(0, str(TRACK / "scripts"))
sys.path.insert(0, str(ROOT / "finetune_slm"))                                           # the package direct_inference_baseline lives in finetune_slm/

EXPECTED_PROMPT_SHA256 = "f6d5202f26d97c2d73c9d00adbca050bc7114ad8b0272749eeff8d0757de09b0"
PROMPT_FILE = TRACK / "experiments" / "EXP_002_PROMPTING_INFERENCE" / "prompt_versions" / "P02_p01_schema_no_evidence.txt"
FREEZE = TRACK / "manifests" / "FREEZE_P02.json"
CONVERSION = TRACK / "manifests" / "CONVERSION_RECORD_Qwen3-1.7B.json"
MODEL_DIR = TRACK / "models" / "Qwen3-1.7B-ov-fp16"
REQUIRED = ["openvino_model.xml", "openvino_model.bin", "openvino_tokenizer.xml", "openvino_tokenizer.bin", "openvino_detokenizer.xml", "openvino_detokenizer.bin",
            "config.json", "tokenizer.json", "tokenizer_config.json", "chat_template.jinja"]


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


def verify_preconditions(out: Path, ram_gate_gib: float | None, check_only: bool) -> dict:
    prompt_sha = sha256_file(PROMPT_FILE)
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))["files"]
    frozen_prompt = next((v for k, v in freeze.items() if k.endswith("P02_p01_schema_no_evidence.txt")), None)
    if not (prompt_sha == EXPECTED_PROMPT_SHA256 == frozen_prompt):
        fail(out, "prompt_hash_mismatch", "The P02 prompt does not match the frozen hash.", prompt_sha=prompt_sha)
    for name, expected in freeze.items():                                          # frozen runner, client, common, integrity files
        p = TRACK / name
        if name.startswith("scripts/") and name != "scripts/evaluate_run.py" and p.exists() and sha256_file(p) != expected:
            fail(out, "frozen_file_changed", f"A frozen file changed: {name}")
    missing = [n for n in REQUIRED if not (MODEL_DIR / n).exists()]
    if missing:
        fail(out, "model_files_missing", f"Missing model files: {', '.join(missing)}. Copy them from the model package; nothing is downloaded automatically.")
    rec = json.loads(CONVERSION.read_text(encoding="utf-8"))
    bin_info = rec["converted_files"]["openvino_model.bin"]
    bin_path = MODEL_DIR / "openvino_model.bin"
    if bin_path.stat().st_size != bin_info["bytes"]:
        fail(out, "model_weights_size_mismatch", f"openvino_model.bin has {bin_path.stat().st_size} bytes, expected {bin_info['bytes']}.")
    marker = out.parent.parent / "model_verified.json"                              # skips re-hashing 3.4 GB when size+mtime are unchanged
    stamp = {"size": bin_path.stat().st_size, "mtime_ns": bin_path.stat().st_mtime_ns, "sha256": bin_info["sha256"]}
    if not (marker.exists() and json.loads(marker.read_text(encoding="utf-8")) == stamp):
        if sha256_file(bin_path) != bin_info["sha256"]:
            fail(out, "model_weights_hash_mismatch", "openvino_model.bin SHA-256 does not match the conversion record.")
        marker.write_text(json.dumps(stamp), encoding="utf-8")
    for fname in ("openvino_model.xml", "openvino_tokenizer.xml", "openvino_detokenizer.xml", "config.json", "tokenizer.json"):
        if sha256_file(MODEL_DIR / fname) != rec["converted_files"][fname]["sha256"]:
            fail(out, "model_file_hash_mismatch", f"{fname} does not match the conversion record.")
    import psutil
    available = psutil.virtual_memory().available / 2**30
    if ram_gate_gib is not None and not check_only and available < ram_gate_gib:
        fail(out, "insufficient_memory", f"Available RAM {available:.2f} GiB is below the required {ram_gate_gib:.1f} GiB. Close other applications and retry.", available_gib=round(available, 3))
    return {"prompt_sha256": prompt_sha, "model_weights_sha256": bin_info["sha256"], "available_ram_gib_before_load": round(available, 3)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--ram-gate-gib", type=float, default=8.0)
    ap.add_argument("--cache-dir", default=None)
    ap.add_argument("--check", action="store_true", help="verify files and imports only; load no model")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    emit("preparing", message="Verifying prompt and model files")
    pre = verify_preconditions(out, a.ram_gate_gib, a.check)

    import common_1_7b as C                                                         # frozen helpers (imports only constants and the 0.6B read-only code)
    from direct_inference_baseline.evaluation import schema_validator as SV
    from direct_inference_baseline.inference import inference_runner as IR
    from direct_inference_baseline.inference.base_client import PermanentInferenceError, TransientInferenceError
    from direct_inference_baseline.inference.output_parser import parse_response
    from ov_client_1_7b import OVClient17B

    if a.check:
        emit("check_ok", **pre, max_new_tokens=C.MAX_NEW_TOKENS)
        (out / "result.json").write_text(json.dumps({"ok": True, "check_only": True, **pre}, indent=1), encoding="utf-8")
        return

    compact = json.loads(Path(a.input).read_text(encoding="utf-8"))
    template = PROMPT_FILE.read_text(encoding="utf-8")
    emit("reading_transcript", message="Building the P02 prompt")
    prompt = IR.build_prompt(compact["encounter_id"], compact, template)           # frozen builder: {ENCOUNTER_ID} / {TRANSCRIPT} substitution only
    cache_dir = Path(a.cache_dir) if a.cache_dir else out.parent.parent / "ov_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    client = OVClient17B("GPU", C.OV_MODEL_DIR, cache_dir)                          # device is the frozen "GPU"; no fallback is added here

    started = datetime.now(timezone.utc).isoformat()
    emit("loading_model", message="Loading the model onto the GPU and starting generation")
    t0 = time.perf_counter()
    emit("extracting", message="Model is generating the extraction")
    try:
        result = client.generate(prompt, C.MAX_NEW_TOKENS, retries=0)              # retries 0, as in the P02 run
    except (TransientInferenceError, PermanentInferenceError, MemoryError, RuntimeError) as exc:
        text = f"{type(exc).__name__}: {str(exc)[:300]}"
        low = text.lower()
        code = "out_of_memory" if ("memory" in low or "out of" in low) else "inference_error"
        fail(out, code, "The model could not complete the extraction." if code == "inference_error" else "Out of memory during extraction.", exit_code=3, detail=text)
    wall = time.perf_counter() - t0
    ended = datetime.now(timezone.utc).isoformat()

    emit("validating_output", message="Parsing and validating the output")
    parsed = parse_response(result.text, result.finish_reason)
    schema = None
    if parsed.status == "ok":
        report = SV.validate(parsed.data)
        schema = {"compliant": bool(report.compliant), "violation_counts": dict(report.counts), "violations_sample": list(report.violations[:15])}
        (out / "extraction_raw.json").write_text(json.dumps(parsed.data, ensure_ascii=False, indent=1), encoding="utf-8")    # exactly the parser's object
    (out / "model_response_raw.txt").write_text(result.text or "", encoding="utf-8")
    perf = (result.notes or [{}])[0] if isinstance(result.notes, list) and result.notes else {}
    metadata = {
        "encounter_id": compact["encounter_id"], "prompt_sha256": pre["prompt_sha256"], "prompt_file": str(PROMPT_FILE.relative_to(ROOT)).replace("\\", "/"),
        "model": client.describe(), "model_weights_sha256": pre["model_weights_sha256"], "device": client.device, "max_new_tokens": C.MAX_NEW_TOKENS,
        "started_at": started, "ended_at": ended, "wall_seconds": round(wall, 1), "input_tokens": result.prompt_tokens, "output_tokens": result.completion_tokens,
        "finish_reason": result.finish_reason, "parse_status": parsed.status, "parse_notes": parsed.notes, "schema_validation": schema,
        "performance": {k: perf.get(k) for k in ("load_compile_seconds", "first_token_latency_s(prefill+1st token)", "prefill_tokens_per_second", "decode_tokens_per_second",
                                                    "generation_wall_seconds", "sampled_peak_process_rss_mb", "sampled_min_system_available_mb", "system_available_mb_before")},
        "available_ram_gib_before_load": pre["available_ram_gib_before_load"], "retries": 0,
    }
    (out / "result.json").write_text(json.dumps({"ok": parsed.status == "ok", "code": None if parsed.status == "ok" else parsed.status, "metadata": metadata}, indent=1), encoding="utf-8")
    emit("finished", parse_status=parsed.status, finish_reason=result.finish_reason)
    if os.name == "nt":                                                             # make sure all handles are released
        sys.stdout.flush()


if __name__ == "__main__":
    main()
