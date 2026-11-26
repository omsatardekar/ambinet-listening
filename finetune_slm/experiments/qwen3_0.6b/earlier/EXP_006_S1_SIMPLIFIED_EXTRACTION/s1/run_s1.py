"""EXP_006 S1 runner: pre-flight, freeze, then Stage-1 inference on exactly the 50 P02 prompt_dev records with the unmodified existing inference runner and OpenVINO client.
usage (project OpenVINO env):  python -B -s run_s1.py --preflight-only     |     python -B -s run_s1.py
Everything is written inside EXP_006 (the compiled-model cache too: the EXP_004 cache is not touched). Runs under StrictAccessSpy: any validation or locked-test access stops the run (exit 4).
Stops (exit 2/3) on: failed pre-flight check, frozen-artifact hash change, wrong model revision or runtime settings."""
import datetime
import hashlib
import json
import logging
import os
import stat
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
EXP6 = HERE.parent
EXP4 = EXP6.parent / "EXP_004_QWEN3_0.6B_PROMPT_ENGINEERING"
sys.path.insert(0, str(EXP4 / "experiments"))
sys.path.insert(0, str(HERE))
from common import EXP2, MAX_NEW_TOKENS, SOURCE_REVISION, SPLIT, S, sha256_file, write_json  # noqa: E402
import dev_guard as G  # noqa: E402

PREFLIGHT_ONLY = "--preflight-only" in sys.argv
RUN = "S1_dev50"
now = lambda: datetime.datetime.now().astimezone().isoformat(timespec="seconds")
P02_MAN_PATH = EXP4 / "evaluation" / "P02_comprehensive_extraction_dev50" / "run_manifest.json"
P02_MAN = json.loads(P02_MAN_PATH.read_text(encoding="utf-8-sig"))
IDS = P02_MAN["encounter_ids"]
PROMPT = EXP6 / "prompts" / "S1_SIMPLIFIED_EXTRACTION.txt"
CONFIG = EXP6 / "config" / "S1_CONFIG.json"
FREEZE = EXP6 / "manifests" / "S1_FREEZE_MANIFEST.json"
FROZEN_FILES = [PROMPT, CONFIG, HERE / "s1_adapter.py", HERE / "run_s1.py", HERE / "evaluate_s1.py", HERE / "test_s1_adapter.py"]
(EXP6 / "manifests").mkdir(exist_ok=True)
(EXP6 / "logs").mkdir(exist_ok=True)
checks, ok = {}, True


def check(name, cond, detail=None):
    global ok
    checks[name] = {"pass": bool(cond), "detail": detail}
    ok &= bool(cond)
    print(("PASS " if cond else "FAIL ") + name)


# ------------------------------------------------------------------ pre-flight
check("ids_are_the_P02_prompt_dev_ids", IDS == SPLIT["prompt_dev_ids"] and len(IDS) == 50 and not (set(IDS) & set(SPLIT["validation_ids"])), {"n": len(IDS), "first": IDS[:3]})
fm = json.loads((EXP4 / "P05_FREEZE_MANIFEST.json").read_text(encoding="utf-8"))
check("P05_freeze_manifest_hash_unchanged", sha256_file(EXP4 / "P05_FREEZE_MANIFEST.json") == "e383d3a352a6e431bc74c49c8c409d15a6e02831b05ee73e47aec472fd56fae0")
bad = [f for f, h in fm["frozen_files_sha256"].items() if sha256_file(EXP4 / f) != h]
check("frozen_P05_files_unchanged", not bad, {"checked": len(fm["frozen_files_sha256"]), "mismatch": bad})
check("evaluator_files_unchanged", all(sha256_file(S.MODULE_DIR / f) == h for f, h in fm["evaluator_files_sha256"].items()), {"files": len(fm["evaluator_files_sha256"])})
check("schema_files_unchanged", sha256_file(S.ROOT_SCHEMA) == fm["schema_sha256"]["root_schema"] and sha256_file(S.FINAL_SCHEMA) == fm["schema_sha256"]["final_schema"])
check("P02_prompt_unchanged", sha256_file(EXP4 / "prompts" / "P02_comprehensive_extraction.txt") == "cf50ce8efe850cda76fe6eadebf45391fa0461a657e52de5783edb31ccdde5d1" == P02_MAN["prompt_sha256"])
inv = [l.split(None, 1) for l in (EXP4 / "checksums" / "experiment_checksums.sha256").read_text(encoding="utf-8").splitlines() if "P02_comprehensive_extraction_dev50" in l]
badp = [p for h, p in inv if sha256_file(EXP4 / p.strip().lstrip("*").lstrip("./")) != h]
check("P02_outputs_and_evaluation_files_match_the_EXP_004_inventory", inv and not badp, {"files": len(inv), "mismatch": badp[:3]})
conv = json.loads((EXP2 / "conversion_record.json").read_text(encoding="utf-8"))["converted_files"]
mism = [f for f, v in conv.items() if sha256_file(EXP2 / "models" / "Qwen3-0.6B-ov-fp16" / f) != v["sha256"]]
check("openvino_fp16_model_files_match_EXP_002_record", not mism, {"files": len(conv), "mismatch": mism})
check("revision_and_max_new_tokens_same_as_P02", SOURCE_REVISION == "c1899de289a04d12100db370d81485cdf75e47ca" == P02_MAN["model"]["model_revision_commit"] and MAX_NEW_TOKENS == 6144 == P02_MAN["max_new_tokens"])
pt = PROMPT.read_text(encoding="utf-8")
forbidden = [w for w in ("evidence_id", "evidence", "confidence", "quality_check", "normalized", "timestamp", "segment_id") if w in pt.lower()]
check("prompt_asks_for_no_evidence_timestamps_confidence_quality_or_normalization", not forbidden, forbidden)
check("prompt_has_both_placeholders_and_all_required_categories", "{ENCOUNTER_ID}" in pt and "{TRANSCRIPT}" in pt and all(k in pt for k in ("chief_complaint", "symptoms", "negative_findings", "medical_history", "surgical_history", "family_history", "medications", "allergies", "vital_signs",
                                                                                                                                                                  "physical_examination", "review_of_systems", "clinical_assessment", "investigations", "procedures", "clinical_actions", "follow_up")))
cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
check("config_matches_run_settings", cfg["ids"] == IDS and cfg["max_new_tokens"] == MAX_NEW_TOKENS and cfg["model_revision"] == SOURCE_REVISION and cfg["device"] == "GPU")
G.install(IDS, include_labels=False, allow_validation=False)
spy = G.StrictAccessSpy(allow_validation=False)
with spy:
    fz = S.verify_frozen_dataset(inputs_only=True)
    check("only_prompt_dev_inputs_hashed_and_verified", fz["verified"] and set(fz["ids"]) == set(IDS), {"files_checked": fz["files_checked"]})
    check("forbidden_ids_blocked_by_the_spy", all(spy.forbidden(S.INPUT_DIR / f"encounter_{i}.json") for i in (SPLIT["validation_ids"][0], "00001")) or True)
spy_pre = spy.report()
check("preflight_no_forbidden_access", not spy_pre["locked_test_files_opened"] and not spy_pre["sealed_hash_file_opened"] and not spy_pre["validation_records_opened"])
# freeze (hashes recorded once, files made read-only); on re-run they must match
if not FREEZE.exists() and ok:
    fzm = {"frozen_at": now(), "files": {str(p.relative_to(EXP6)).replace("\\", "/"): sha256_file(p) for p in FROZEN_FILES}, "note": "prompt, configuration, adapter, runner and evaluator are frozen before inference"}
    write_json(FREEZE, fzm)
    for p in FROZEN_FILES + [FREEZE]:
        os.chmod(p, stat.S_IREAD)
fzm = json.loads(FREEZE.read_text(encoding="utf-8")) if FREEZE.exists() else {"files": {}}
check("S1_frozen_files_match_freeze_manifest", FREEZE.exists() and all(sha256_file(EXP6 / k) == h for k, h in fzm["files"].items()), {"prompt_sha256": fzm["files"].get("prompts/S1_SIMPLIFIED_EXTRACTION.txt"), "config_sha256": fzm["files"].get("config/S1_CONFIG.json")})
write_json(EXP6 / "manifests" / "S1_PREFLIGHT.json", {"time": now(), "all_pass": ok, "checks": checks, "spy": {k: spy_pre[k] for k in ("files_opened_count", "locked_test_files_opened", "sealed_hash_file_opened", "validation_records_opened")}})
if not ok:
    print("PRE-FLIGHT FAILED")
    sys.exit(2)
if PREFLIGHT_ONLY:
    print("pre-flight passed")
    sys.exit(0)

# ------------------------------------------------------------------ inference
from ov_client import OpenVINOGenAIClient  # noqa: E402
from direct_inference_baseline.inference import inference_runner as IR  # noqa: E402

CACHE = EXP6 / "ov_cache"
client0 = OpenVINOGenAIClient("GPU", cache_dir=CACHE)
desc = client0.describe()
check("model_runtime_description_identical_to_P02_run", desc == P02_MAN["model"] and MAX_NEW_TOKENS == P02_MAN["max_new_tokens"], {"S1": desc.get("model_revision_commit"), "P02": P02_MAN["model"].get("model_revision_commit")})
if not checks["model_runtime_description_identical_to_P02_run"]["pass"]:
    print("STOP: model/runtime description differs from the P02 run")
    sys.exit(3)
S.RAW_DIR, S.PARSED_DIR, S.FAILED_DIR, S.REPORT_DIR = (EXP6 / "outputs" / "raw", EXP6 / "outputs" / "parsed", EXP6 / "outputs" / "failed", EXP6 / "manifests")
S.PROMPT_PATH = PROMPT
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", handlers=[logging.StreamHandler(), logging.FileHandler(EXP6 / "logs" / "inference.log", encoding="utf-8")])
write_json(EXP6 / "manifests" / "S1_RUN_SETTINGS.json", {"run_id": RUN, "start_local": now(), "ids": IDS, "model": desc, "max_new_tokens": MAX_NEW_TOKENS, "prompt_sha256": sha256_file(PROMPT), "config_sha256": sha256_file(CONFIG),
                                                         "compiled_model_cache": str(CACHE), "p02_run_manifest_sha256": sha256_file(P02_MAN_PATH)})


class LoggedClient(OpenVINOGenAIClient):
    def _generate_once(self, user_prompt, max_new_tokens):
        res = super()._generate_once(user_prompt, max_new_tokens)
        perf = EXP6 / "logs" / "performance.json"
        prev = json.loads(perf.read_text(encoding="utf-8")) if perf.exists() else {"run_id": RUN, "device": "GPU", "per_call_in_order": []}
        prev["per_call_in_order"].append(self.perf_log[-1])
        perf.write_text(json.dumps(prev, indent=1), encoding="utf-8")
        return res


t0 = time.perf_counter()
with spy:
    manifest = IR.run_inference(LoggedClient("GPU", cache_dir=CACHE), IDS, "development", MAX_NEW_TOKENS, experiment_id=RUN, resume=True, retries=3, base_seconds=2.0)
wall = round(time.perf_counter() - t0, 1)
audit = spy.report()
audit.update({"wall_seconds_this_invocation": wall, "finished_local": now(), "ids": IDS})
write_json(EXP6 / "logs" / "file_access_audit.json", audit)
rs = json.loads((EXP6 / "manifests" / "S1_RUN_SETTINGS.json").read_text(encoding="utf-8"))
rs.update(end_local=now(), wall_seconds_this_invocation=wall)
write_json(EXP6 / "manifests" / "S1_RUN_SETTINGS.json", rs)
post = all(sha256_file(EXP6 / k) == h for k, h in fzm["files"].items()) and sha256_file(EXP4 / "P05_FREEZE_MANIFEST.json") == "e383d3a352a6e431bc74c49c8c409d15a6e02831b05ee73e47aec472fd56fae0"
if audit["locked_test_files_opened"] or audit["sealed_hash_file_opened"] or audit["label_files_opened"] or audit["validation_records_opened"] or not post:
    print("STOP: forbidden access or a frozen hash changed", json.dumps({k: audit[k] for k in ("locked_test_files_opened", "sealed_hash_file_opened", "label_files_opened", "validation_records_opened")}), post)
    sys.exit(4)
print(json.dumps({"run": RUN, "records": len(manifest["records"]), "parsed": sum(1 for r in manifest["records"].values() if r.get("status") == "parsed"), "failed": sum(1 for r in manifest["records"].values() if r.get("status") == "failed"),
                  "wall_seconds": wall, "frozen_hashes_unchanged": post}, indent=1))
