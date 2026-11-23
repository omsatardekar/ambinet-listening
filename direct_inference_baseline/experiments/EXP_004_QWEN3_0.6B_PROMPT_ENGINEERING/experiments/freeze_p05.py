"""Write P05_FREEZE_MANIFEST.json: SHA-256 of every file that defines the P05 validation (retrieval source and configuration, builder, pipeline, evaluator and its dependencies, schema files, gates, guard, runner, P02 prompt, split) and
record whether the evaluator files are byte-identical to the EXP_001 code snapshot. Re-running changes nothing unless a file changed. usage: freeze_p05.py   (then make the listed files read-only)."""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import EXP4, EXP2, S, sha256_file  # noqa: E402

FROZEN = ["experiments/p05_retrieval.py", "experiments/p05_config.json", "experiments/make_p05_config.py", "experiments/evidence_builder.py", "experiments/p05_pipeline.py", "experiments/p05_eval_lib.py",
          "experiments/evaluate_p05.py", "experiments/run_p05_validation.py", "experiments/dev_guard.py", "experiments/common.py", "experiments/ov_client.py", "experiments/P05_validation_gates.json",
          "experiments/audit_sampler.py", "experiments/audit_score.py", "experiments/record_authorization.py", "experiments/test_dev_guard.py", "experiments/test_strict_spy.py", "experiments/test_evidence_builder.py", "experiments/split_v1.json", "prompts/P02_comprehensive_extraction.txt", "dev_safeguards/dev_checksums.sha256", "dev_safeguards/dev_manifest.csv"]
EVAL = ["evaluation/__init__.py", "evaluation/attribute_metrics.py", "evaluation/clinical_metrics.py", "evaluation/dataset_split.py", "evaluation/entity_matching.py", "evaluation/evaluation_runner.py",
        "evaluation/evidence_evaluator.py", "evaluation/schema_validator.py", "inference/inference_runner.py", "inference/output_parser.py", "config/settings.py"]
snap = EXP4.parent / "EXP_001_QWEN3_0.6B_CPU_BASELINE" / "code_snapshot"
m = {"purpose": "P05 frozen configuration for the validation run (provisional development gates)", "frozen_files_sha256": {f: sha256_file(EXP4 / f) for f in FROZEN},
     "evaluator_files_sha256": {f: sha256_file(S.MODULE_DIR / f) for f in EVAL},
     "evaluator_identical_to_EXP_001_snapshot": {f: (sha256_file(snap / f) == sha256_file(S.MODULE_DIR / f)) if (snap / f).exists() else None for f in EVAL},
     "schema_sha256": {"root_schema": sha256_file(S.ROOT_SCHEMA), "final_schema": sha256_file(S.FINAL_SCHEMA)}, "p02_prompt_sha256": sha256_file(EXP4 / "prompts" / "P02_comprehensive_extraction.txt"),
     "openvino_model_files_sha256": {k: v["sha256"] for k, v in json.loads((EXP2 / "conversion_record.json").read_text(encoding="utf-8"))["converted_files"].items()},
     "model": {"id": "Qwen/Qwen3-0.6B", "revision": "c1899de289a04d12100db370d81485cdf75e47ca", "runtime": "OpenVINO GenAI FP16 on Intel UHD 620 GPU", "decoding": "greedy, thinking off, max_new_tokens 6144"},
     "retrieval_revisions": ["v1: pre-registered (polarity rejects any negated anchor)", "v2 (post-hoc): item-aware polarity", "v3 (post-hoc): local negation cue for negative findings", "v4 (post-hoc): preceding question added to short replies"]}
canon = json.dumps(m, indent=1, sort_keys=True)
out = EXP4 / "P05_FREEZE_MANIFEST.json"
out.write_text(canon, encoding="utf-8", newline="\n")
print(out.name, hashlib.sha256(out.read_bytes()).hexdigest())
print("evaluator identical to EXP_001 snapshot:", {k: v for k, v in m["evaluator_identical_to_EXP_001_snapshot"].items() if v is not True} or "all True")
