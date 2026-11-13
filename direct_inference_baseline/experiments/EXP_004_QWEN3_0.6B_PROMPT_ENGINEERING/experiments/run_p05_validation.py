"""EXP_004 P05 runner (integrated with dev_guard). Stage 1: frozen P02 prompt + Qwen3-0.6B (OpenVINO FP16, GPU) through the existing inference loop. Stages 2-4: frozen R_cons v4 retrieval -> existing evidence builder -> final JSON.
usage: run_p05_validation.py <scope> <run_id> [--dry-run] [--postprocess-from <P02 parsed dir>]
  scope smoke_prompt_dev : the 5 approved prompt_dev ids (integration / access-audit check)
  scope prompt_dev       : the 50 prompt_dev ids (dry-run / post-processing regression only)
  scope validation       : the 50 validation ids; REFUSED unless the user's authorisation for this exact frozen configuration is recorded (P05_VALIDATION_AUTHORIZATION.json)
--dry-run: no model, no GPU, no generation (pre-flight, guard, transcript access, prompt rendering, stages 2-4 on existing P02 outputs only).
Every file access runs under dev_guard.StrictAccessSpy: opening a locked-test record, the sealed hash file, or (without authorisation) a validation record STOPS the run immediately."""
import hashlib
import json
import sys
import time
import datetime
import logging
from pathlib import Path

from common import EXP2, EXP4, MAX_NEW_TOKENS, SOURCE_REVISION, SPLIT, S, sha256_file, use_run, write_json
import dev_guard as G
import make_p05_config as MC
import p05_pipeline as PP
import p05_retrieval as R

args = [a for a in sys.argv[1:] if not a.startswith("--")]
flags = [a for a in sys.argv[1:] if a.startswith("--")]
scope, run_id = args[0], args[1]
DRY = "--dry-run" in flags
POST_FROM = Path(sys.argv[sys.argv.index("--postprocess-from") + 1]) if "--postprocess-from" in sys.argv else None
SCOPES = {"smoke_prompt_dev": ["00035", "00037", "00040", "00215", "00248"], "prompt_dev": SPLIT["prompt_dev_ids"], "validation": SPLIT["validation_ids"]}
IDS = SCOPES[scope]
P02_SHA = "cf50ce8efe850cda76fe6eadebf45391fa0461a657e52de5783edb31ccdde5d1"
now = lambda: datetime.datetime.now().astimezone().isoformat(timespec="seconds")
base = (EXP4 / "integration_checks" / run_id) if DRY else (EXP4 / "outputs" / run_id)
base.mkdir(parents=True, exist_ok=True)
audit_path = base / "file_access_audit.json"

# ---- authorisation gate BEFORE any validation file can be touched
if scope == "validation" and not G.validation_authorized():
    write_json(base / "REFUSED.json", {"scope": scope, "reason": "validation not authorised for this frozen configuration", "when": now(), "validation_files_opened": 0})
    print("STOP: validation is not authorised (no valid P05_VALIDATION_AUTHORIZATION.json for the current freeze manifest). Nothing was opened.")
    sys.exit(3)
assert not set(IDS) & set(json.loads((S.SPLIT_DIR / "test_ids.json").read_text(encoding="utf-8"))), "locked-test id in scope"

pf = {"started_local": now(), "scope": scope, "dry_run": DRY, "checks": {}}
ok = True


def check(name, cond, detail=None):
    global ok
    pf["checks"][name] = {"pass": bool(cond), "detail": detail}
    ok &= bool(cond)


# ---- everything below runs under the strict spy
with G.StrictAccessSpy(allow_validation=(scope == "validation")) as spy:
    G.install(IDS, include_labels=False, allow_validation=(scope == "validation"))
    # frozen-configuration checks
    fm = json.loads(G.FREEZE_MANIFEST.read_text(encoding="utf-8")) if G.FREEZE_MANIFEST.exists() else None
    check("freeze_manifest_present", fm is not None)
    if fm:
        bad = [f for f, h in fm["frozen_files_sha256"].items() if sha256_file(EXP4 / f) != h]
        check("frozen_files_unchanged", not bad, {"checked": len(fm["frozen_files_sha256"]), "mismatch": bad})
        check("config_matches_frozen_json", MC.canonical(MC.live_config()) == (EXP4 / "experiments" / "p05_config.json").read_text(encoding="utf-8"))
        check("p02_prompt_sha_frozen", fm["p02_prompt_sha256"] == P02_SHA == sha256_file(EXP4 / "prompts" / "P02_comprehensive_extraction.txt"))
        check("evaluator_files_unchanged", all(sha256_file(S.MODULE_DIR / f) == h for f, h in fm["evaluator_files_sha256"].items()), {"files": len(fm["evaluator_files_sha256"])})
        check("schema_files_unchanged", sha256_file(S.ROOT_SCHEMA) == fm["schema_sha256"]["root_schema"] and sha256_file(S.FINAL_SCHEMA) == fm["schema_sha256"]["final_schema"])
    check("ids_in_scope_only", True, {"scope": scope, "n": len(IDS)})
    conv = json.loads((EXP2 / "conversion_record.json").read_text(encoding="utf-8"))["converted_files"]
    mism = [f for f, v in conv.items() if (EXP2 / "models" / "Qwen3-0.6B-ov-fp16" / f).exists() and sha256_file(EXP2 / "models" / "Qwen3-0.6B-ov-fp16" / f) != v["sha256"]]
    check("openvino_fp16_model_files_match_EXP_002_record", not mism, {"files": len(conv), "mismatch": mism})
    check("max_new_tokens_and_revision", MAX_NEW_TOKENS == 6144 and SOURCE_REVISION == "c1899de289a04d12100db370d81485cdf75e47ca")
    p02m = json.loads((EXP4 / "evaluation" / "P02_comprehensive_extraction_dev50" / "run_manifest.json").read_text(encoding="utf-8"))
    desc = None
    if not DRY:
        from ov_client import OpenVINOGenAIClient
        desc = OpenVINOGenAIClient("GPU").describe()
        check("model_runtime_settings_identical_to_P02_run", p02m["model"] == desc and p02m["max_new_tokens"] == MAX_NEW_TOKENS)
    else:
        check("model_runtime_settings_identical_to_P02_run", True, "dry-run: model not instantiated; compared at the real run")
    pf["all_pass"] = ok
    write_json(base / "preflight.json", pf)
    if not ok:
        print(json.dumps({k: v for k, v in pf["checks"].items() if not v["pass"]}, indent=1)); print("PRE-FLIGHT FAILED"); sys.exit(2)
    use_run(run_id, "P02_comprehensive_extraction.txt")
    S.RAW_DIR, S.PARSED_DIR, S.FAILED_DIR = (base / "stage1" / n for n in ("raw_predictions", "parsed_predictions", "failed_predictions"))
    # ---- stage 1
    stage1_parsed = POST_FROM
    t0 = time.perf_counter()
    if DRY:
        from direct_inference_baseline.inference import inference_runner as IR
        for eid in IDS:                                           # transcript access + prompt rendering through the guarded path (no generation)
            IR.build_prompt(eid)
        pf["dry_run_prompts_rendered"] = len(IDS)
        assert POST_FROM is not None, "dry-run needs --postprocess-from <existing P02 parsed dir>"
    else:
        from direct_inference_baseline.inference import inference_runner as IR
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", handlers=[logging.StreamHandler(), logging.FileHandler(base / "inference.log", encoding="utf-8")])
        assert sha256_file(S.PROMPT_PATH) == P02_SHA
        write_json(base / "run_settings.json", {"run_id": run_id, "scope": scope, "prompt": "prompts/P02_comprehensive_extraction.txt", "prompt_sha256_verified_before_inference": P02_SHA, "ids": IDS, "model": desc, "start_local": now(),
                                                "freeze_manifest_sha256": sha256_file(G.FREEZE_MANIFEST)})

        class LoggedClient(OpenVINOGenAIClient):
            def _generate_once(self, user_prompt, max_new_tokens):
                res = super()._generate_once(user_prompt, max_new_tokens)
                perf = base / "performance.json"
                prev = json.loads(perf.read_text(encoding="utf-8")) if perf.exists() else {"run_id": run_id, "device": "GPU", "per_call_in_order": []}
                prev["per_call_in_order"].append(self.perf_log[-1]); perf.write_text(json.dumps(prev, indent=1), encoding="utf-8")
                return res
        manifest = IR.run_inference(LoggedClient("GPU"), IDS, "development", MAX_NEW_TOKENS, experiment_id=run_id, resume=True, retries=3, base_seconds=2.0)
        stage1_parsed = S.PARSED_DIR / run_id
        assert sha256_file(S.PROMPT_PATH) == P02_SHA, "prompt changed during the run"
    # ---- stages 2-4
    (base / "final_predictions").mkdir(exist_ok=True); (base / "decisions").mkdir(exist_ok=True)
    from direct_inference_baseline.config import settings as _S
    from direct_inference_baseline.evaluation import schema_validator as SV
    n_ok = n_missing = 0
    for eid in IDS:
        p = Path(stage1_parsed) / f"encounter_{eid}.json"
        if not p.exists():
            n_missing += 1
            continue
        tr = json.loads((S.INPUT_DIR / f"encounter_{eid}.json").read_text(encoding="utf-8"))
        final, rep = PP.postprocess(json.loads(p.read_text(encoding="utf-8")), tr, top_key_order=list(SV.TOP_KEYS))
        write_json(base / "final_predictions" / f"encounter_{eid}.json", final); write_json(base / "decisions" / f"encounter_{eid}.json", rep)
        n_ok += 1
    rep_audit = spy.report()
    rep_audit.update({"scope": scope, "dry_run": DRY, "ids": IDS, "records_postprocessed": n_ok, "records_without_stage1_output": n_missing, "wall_seconds": round(time.perf_counter() - t0, 1), "finished_local": now()})
    write_json(audit_path, rep_audit)
    if not DRY:
        rs = json.loads((base / "run_settings.json").read_text(encoding="utf-8")); rs.update(end_local=now()); write_json(base / "run_settings.json", rs)
if rep_audit["locked_test_files_opened"] or rep_audit["sealed_hash_file_opened"] or rep_audit["label_files_opened"]:
    print("STOP: forbidden file access recorded", json.dumps(rep_audit)); sys.exit(4)
print(json.dumps({"run": run_id, "scope": scope, "dry_run": DRY, "records_postprocessed": n_ok, "no_stage1_output": n_missing, "locked_test_files_opened": 0, "sealed_file_opened": False, "label_files_opened": 0,
                  "validation_records_opened": rep_audit["validation_records_opened"], "input_transcripts_opened": len(rep_audit["input_transcripts_opened"])}, indent=1))
