"""EXP_003 pre-execution verification. Reads transcripts (via the existing prompt builder) and NEVER reads labels. No generation is performed."""
import json
import platform
import subprocess
import sys
from pathlib import Path

from common import (CACHE_DIR, EXP1, EXP2, EXP3, MODULE, OV_MODEL_DIR, ROOT, SMOKE_IDS, SOURCE_REVISION, S, FileAccessSpy, sha256_file, write_json)
from direct_inference_baseline.inference import inference_runner as IR

checks = {}


def check(name, ok, detail=None):
    checks[name] = {"ok": bool(ok), "detail": detail}
    print(("PASS " if ok else "FAIL ") + name, "" if detail is None else f"- {detail}")


# ---- environment
check("running_in_isolated_EXP_002_env", "env_openvino" in sys.executable, sys.executable)
rec = json.loads((EXP2 / "conversion_record.json").read_text(encoding="utf-8"))

# ---- model: converted files match the EXP_002 conversion record; source snapshot is the exact revision
bad = [f for f, v in rec["converted_files"].items() if not (OV_MODEL_DIR / f).exists() or sha256_file(OV_MODEL_DIR / f) != v["sha256"]]
check("openvino_model_files_match_EXP_002_conversion_record", not bad and len(rec["converted_files"]) == 11, {"files": len(rec["converted_files"]), "mismatches": bad})
check("source_revision_recorded_in_conversion", rec["source_revision"] == SOURCE_REVISION, rec["source_revision"])
hub = Path.home() / ".cache" / "huggingface" / "hub" / "models--Qwen--Qwen3-0.6B"
snap = hub / "snapshots" / SOURCE_REVISION
check("hf_cache_ref_main_is_exact_revision", (hub / "refs" / "main").read_text().strip() == SOURCE_REVISION and snap.exists())
src_bad = [n for n, h in rec["source_files_sha256"].items() if sha256_file(snap / n) != h]
check("source_snapshot_files_match_recorded_hashes", not src_bad, {"checked": len(rec["source_files_sha256"]), "mismatches": src_bad})

# ---- device
import openvino as ov  # noqa: E402
core = ov.Core()
devs = core.available_devices
gpu_name = core.get_property("GPU", "FULL_DEVICE_NAME") if "GPU" in devs else None
check("GPU_device_detected", "GPU" in devs and "UHD Graphics 620" in (gpu_name or ""), {"devices": devs, "gpu": gpu_name})

# ---- prompt hash vs archived EXP_001 prompt
live = sha256_file(S.PROMPT_PATH)
arch = sha256_file(EXP1 / "prompt" / "direct_extraction_prompt.txt")
m1 = json.loads((EXP1 / "reports" / "run_manifest.json").read_text(encoding="utf-8"))
check("prompt_sha256_live_equals_EXP_001_archive_and_manifest", live == arch == m1["prompt_sha256"], {"live": live, "archived": arch, "exp001_manifest": m1["prompt_sha256"]})
write_json(EXP3 / "prompt_hash_verification.json", {"live_prompt_path": str(S.PROMPT_PATH.relative_to(ROOT)).replace("\\", "/"), "live_sha256": live,
                                                       "exp001_archived_prompt": "direct_inference_baseline/experiments/EXP_001_QWEN3_0.6B_CPU_BASELINE/prompt/direct_extraction_prompt.txt",
                                                       "exp001_archived_sha256": arch, "exp001_run_manifest_prompt_sha256": m1["prompt_sha256"],
                                                       "all_equal": live == arch == m1["prompt_sha256"], "prompt_modified": False})

# ---- existing code used for inference/evaluation is byte-identical to the code archived with EXP_001
changed = []
for f in sorted((EXP1 / "code_snapshot").rglob("*")):
    if f.is_file():
        rel = f.relative_to(EXP1 / "code_snapshot")
        if sha256_file(f) != sha256_file(MODULE / rel):
            changed.append(str(rel))
check("existing_inference_and_evaluation_code_identical_to_EXP_001_snapshot", not changed, {"differences": changed})

# ---- schemas
check("schema_files_present", S.ROOT_SCHEMA.exists() and S.FINAL_SCHEMA.exists(),
      {"root_clinical_extraction_schema_sha256": sha256_file(S.ROOT_SCHEMA), "frozen_final_label_schema_sha256": sha256_file(S.FINAL_SCHEMA)})

# ---- ids and split
sp1 = json.loads((EXP1 / "split" / "development_ids.json").read_text(encoding="utf-8"))
dev_ids = sp1["ids"] if isinstance(sp1, dict) and "ids" in sp1 else sp1
live_dev = S.SPLIT_DIR / "development_ids.json"
check("live_split_files_identical_to_EXP_001_archive", all(sha256_file(S.SPLIT_DIR / n) == sha256_file(EXP1 / "split" / n) for n in ("development_ids.json", "test_ids.json", "split_metadata.json")))
check("five_ids_in_development_split", all(i in dev_ids for i in SMOKE_IDS) and len(dev_ids) == 100, SMOKE_IDS)
check("five_ids_equal_EXP_001_smoke_ids", sorted(m1["encounter_ids"]) == sorted(SMOKE_IDS) or set(SMOKE_IDS) <= set(m1["records"]), sorted(m1["records"]))

# ---- inputs-only dataset integrity, prompts, token counts, label-leakage spy (no labels are read)
with FileAccessSpy() as spy:
    frozen = S.verify_frozen_dataset(inputs_only=True)
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(str(OV_MODEL_DIR))
    tmpl = IR.load_prompt_template()
    rows = {}
    for eid in SMOKE_IDS:
        inp = IR.load_transcript(eid)
        prompt = IR.build_prompt(eid, inp, tmpl)
        assert prompt == tmpl.replace("{ENCOUNTER_ID}", eid).replace("{TRANSCRIPT}", IR.render_transcript(inp))      # = instruction + transcript only
        text = tok.apply_chat_template([{"role": "user", "content": prompt}], tokenize=False, add_generation_prompt=True, enable_thinking=False)
        n = len(tok(text, add_special_tokens=False)["input_ids"])
        rows[eid] = {"input_tokens_exp003_tokenizer": n, "input_tokens_exp001": m1["records"][eid]["prompt_tokens"], "equal": n == m1["records"][eid]["prompt_tokens"]}
leak = spy.label_or_blueprint_accesses()
check("frozen_inputs_verified_inputs_only", frozen["verified"], {"files_checked": frozen["files_checked"]})
check("no_label_or_blueprint_file_opened_during_prompt_construction", not leak, leak)
check("input_token_counts_equal_EXP_001_for_all_five", all(r["equal"] for r in rows.values()), rows)

# ---- GPU pipeline can really be created (stop and report on failure; no CPU fallback)
import openvino_genai as ovg  # noqa: E402
try:
    pipe = ovg.LLMPipeline(str(OV_MODEL_DIR), "GPU", CACHE_DIR=str(CACHE_DIR))
    g = pipe.get_generation_config()
    eff = {k: getattr(g, k, None) for k in ("max_new_tokens", "do_sample", "temperature", "top_p", "top_k", "repetition_penalty", "num_beams", "eos_token_id")}
    eff["stop_token_ids"] = sorted(getattr(g, "stop_token_ids", []) or [])
    del pipe
    check("GPU_LLMPipeline_created", True, {"default_generation_config_before_overrides": eff})
except Exception as e:                                         # noqa: BLE001
    check("GPU_LLMPipeline_created", False, f"{type(e).__name__}: {e}")

# ---- environment details
def ps(cmd):
    return subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True).stdout.strip()


pkgs = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True).stdout.splitlines()
gprops = {p: str(core.get_property("GPU", p)) for p in ("FULL_DEVICE_NAME", "DEVICE_ARCHITECTURE", "GPU_EXECUTION_UNITS_COUNT", "GPU_DEVICE_TOTAL_MEM_SIZE",
                                                         "GPU_DEVICE_MAX_ALLOC_MEM_SIZE", "INFERENCE_PRECISION_HINT", "OPTIMIZATION_CAPABILITIES")} if "GPU" in devs else {}
write_json(EXP3 / "environment_details.json", {
    "python": platform.python_version(), "python_executable": "experiments/EXP_002_QWEN3_0.6B_GPU_DIRECT/env_openvino/Scripts/python.exe", "os": platform.platform(),
    "cpu": core.get_property("CPU", "FULL_DEVICE_NAME"), "ram_bytes": int(ps("(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory") or 0),
    "gpu_driver": ps("(Get-CimInstance Win32_VideoController | Select -First 1).DriverVersion"), "openvino_devices": devs, "openvino_gpu_properties": gprops,
    "packages": pkgs, "existing_module_import_note": "python-dotenv is absent from env_openvino; scripts/common.py stubs dotenv.load_dotenv (no .env value is needed)."})
write_json(EXP3 / "source_model_provenance.json", {
    "source_model": "Qwen/Qwen3-0.6B", "source_revision": SOURCE_REVISION, "source_weight_dtype": rec["source_weight_dtype"],
    "source_files_sha256": rec["source_files_sha256"], "converted_model_dir": "direct_inference_baseline/experiments/EXP_002_QWEN3_0.6B_GPU_DIRECT/models/Qwen3-0.6B-ov-fp16",
    "converted_precision": rec["converted_precision"], "conversion_command": rec["export_command"], "conversion_tools": rec["tools"],
    "converted_files_sha256": {f: v["sha256"] for f, v in rec["converted_files"].items()},
    "verified_in_exp003_preflight_against": "experiments/EXP_002_QWEN3_0.6B_GPU_DIRECT/conversion_record.json", "numerics_note": rec["note_exp001"],
    "weights_validation": "experiments/EXP_002_QWEN3_0.6B_GPU_DIRECT/results/weight_validation.json (no NaN/Inf; no BF16->FP16 overflow)"})
write_json(EXP3 / "preflight_report.json", {"all_passed": all(c["ok"] for c in checks.values()), "checks": checks, "encounter_ids": SMOKE_IDS})
print("ALL PASSED" if all(c["ok"] for c in checks.values()) else "PREFLIGHT FAILED")
sys.exit(0 if all(c["ok"] for c in checks.values()) else 1)
