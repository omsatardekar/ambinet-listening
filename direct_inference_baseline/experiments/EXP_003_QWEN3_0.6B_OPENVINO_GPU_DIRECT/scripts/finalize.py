"""Writes inference_config.json, experiment_manifest.json and the artifact checksums for EXP_003 (nothing is regenerated or altered)."""
import json
from datetime import datetime, timezone

from common import EXP1, EXP3, EXPERIMENT_ID, MAX_NEW_TOKENS, SMOKE_IDS, SOURCE_REVISION, sha256_file, write_json

m = json.loads((EXP3 / "run_manifest.json").read_text(encoding="utf-8"))
perf = json.loads((EXP3 / "logs" / "performance_per_encounter.json").read_text(encoding="utf-8"))
write_json(EXP3 / "inference_config.json", {
    "runtime": "openvino_genai.LLMPipeline", "device": "GPU (Intel UHD Graphics 620); CPU fallback NOT used", "model": m["model"],
    "decoding": {"do_sample": False, "max_new_tokens": MAX_NEW_TOKENS, "enable_thinking": False, "repetition_penalty": 1.0},
    "effective_generation_config_from_runtime": perf["per_call_in_order"][0]["effective_generation_config"],
    "compiled_model_cache_dir": "ov_cache (inside EXP_003)", "pipeline_per_encounter": True, "retry_policy": m["retry_policy"], "prompt_sha256": m["prompt_sha256"],
    "prompt_text_embedded_in": "run_manifest.json", "schema_validation": "existing evaluation/schema_validator.py (root schema reconciled with frozen final_label_schema.json)",
    "parser": "existing inference/output_parser.py (no repair)", "evaluator": "existing evaluation/evaluation_runner.py, byte-identical to EXP_001 code snapshot",
    "split": m["split"], "split_seed": m["split_seed"], "encounter_ids": SMOKE_IDS})
files = sorted(p for p in EXP3.rglob("*") if p.is_file() and "ov_cache" not in p.parts and "__pycache__" not in p.parts
               and p.name not in ("experiment_manifest.json", "experiment_checksums.sha256"))
write_json(EXP3 / "experiment_manifest.json", {
    "experiment_id": "EXP_003_QWEN3_0.6B_OPENVINO_GPU_DIRECT", "run_id": EXPERIMENT_ID,
    "status": "COMPLETED - FIVE-ENCOUNTER DEVELOPMENT SMOKE TEST ONLY", "encounters_inferred": SMOKE_IDS, "development_encounters_remaining_not_run": 95,
    "locked_test_executed": False, "full_development_run_executed": False, "no_fine_tuning": True, "no_prompt_optimization": True, "no_rag": True, "no_quantization": True,
    "no_hosted_endpoint": True, "model": {"id": "Qwen/Qwen3-0.6B", "source_revision": SOURCE_REVISION, "converted_precision": "FP16 (from BF16 source)", "openvino_model_from": "EXP_002"},
    "prompt_sha256": m["prompt_sha256"], "prompt_identical_to_EXP_001": True, "dataset": m["dataset"], "git_commit_at_run": m["git_commit"],
    "git_note": "direct_inference_baseline/ is untracked in git; the existing module code was verified byte-identical to the EXP_001 code snapshot.",
    "label_files_opened_during_inference": 0, "headline": json.loads((EXP3 / "evaluation" / EXPERIMENT_ID / "evaluation_report.json").read_text(encoding="utf-8"))["headline"],
    "comparison_baseline": str(EXP1.relative_to(EXP3.parents[1])).replace("\\", "/"), "created_utc": datetime.now(timezone.utc).isoformat(),
    "artifact_sha256": {p.relative_to(EXP3).as_posix(): sha256_file(p) for p in files},
    "excluded_from_hashes": ["ov_cache/ (regenerable compiled-model cache)", "this manifest", "checksums file"]})
lines = [f"{sha256_file(p)}  {p.relative_to(EXP3).as_posix()}" for p in sorted(p for p in EXP3.rglob("*") if p.is_file() and "ov_cache" not in p.parts
         and "__pycache__" not in p.parts and p.name != "experiment_checksums.sha256")]
(EXP3 / "checksums").mkdir(exist_ok=True)
(EXP3 / "checksums" / "experiment_checksums.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(len(files), "artifacts hashed;", len(lines), "in checksum file")
