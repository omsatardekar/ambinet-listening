"""Qwen3-1.7B runner: ONE prompt version on the 50 frozen prompt-development ids, OpenVINO FP16 on the Intel GPU, greedy, thinking off.  Resumable.

usage (project OpenVINO env):
  python -B -s run_prompt.py --experiment EXP_001_DIRECT_INFERENCE --run-id P00_direct_dev50 --prompt <file> --label P00 [--max-new-tokens 4096] [--freeze-only | --preflight-only]
Every invocation: pre-flight (ids, prompt hash, model files, 0.6B tree + frozen files unchanged), writes/verifies an immutable freeze manifest (prompt, config, scripts, ids, conversion record),
then runs inference under StrictAccessSpy (labels never opened; validation/locked-test/sealed files blocked), then a post-run audit.
Optional pilot controls (all default to the previous behaviour, so earlier runs are unaffected):
  --ids <file>                 run exactly the ids listed (in that order) in a frozen JSON file {"ids": [...]}, which must be a duplicate-free subset of the frozen 50 (never validation/test ids)
  --min-available-ram-gb <G>   hard gate, evaluated immediately before the first model load (after the freeze manifest exists): the run is refused (exit 2, no model loaded) unless system-wide
                               available RAM >= G GiB.  The threshold is never lowered automatically; there is no per-record threshold (available RAM is only logged per record by the client)
  --retries <N>                retries for transient inference errors (default 3, the previous value; the pilot uses 0)
  --stop-on-oom                stop the whole run at the first out-of-memory error and write logs/OOM_STOP_<run>.json with the exact error (exit 5); default: record the failed record and continue
Exit codes: 2 pre-flight or RAM gate failed, 4 forbidden access / frozen hash changed, 5 stopped on an out-of-memory error.  The existing runner, parser and evaluator are used unmodified."""
import argparse
import datetime
import json
import logging
import os
import re
import stat
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common_1_7b as C  # noqa: E402
import integrity_1_7b as INT  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--experiment", required=True)
ap.add_argument("--run-id", required=True)
ap.add_argument("--prompt", required=True, help="prompt file (absolute or relative to the track)")
ap.add_argument("--label", required=True, help="prompt label, e.g. P00")
ap.add_argument("--max-new-tokens", type=int, default=C.MAX_NEW_TOKENS)
ap.add_argument("--ids-spec", default="prompt_dev", choices=["prompt_dev", "smoke1"], help="smoke1 = the first prompt_dev id only (technical smoke test; results are not experiment results)")
ap.add_argument("--freeze-only", action="store_true")
ap.add_argument("--preflight-only", action="store_true")
ap.add_argument("--ids", default=None, help="frozen JSON file {\"ids\": [...]} (absolute or relative to the track): run exactly these ids, in this order; must be a subset of the frozen 50 (default: all 50)")
ap.add_argument("--min-available-ram-gb", type=float, default=None, help="hard pre-launch gate in GiB of system-wide available RAM, checked before the first model load; never lowered automatically (default: no gate)")
ap.add_argument("--retries", type=int, default=3, help="retries for transient inference errors (default 3 = previous behaviour)")
ap.add_argument("--stop-on-oom", action="store_true", help="stop the run at the first out-of-memory error and report the exact error (default: record the failure and continue, as before)")
A = ap.parse_args()

EXP = C.TRACK / "experiments" / A.experiment
PROMPT = Path(A.prompt) if Path(A.prompt).is_absolute() else C.TRACK / A.prompt
RUN = A.run_id
now = lambda: datetime.datetime.now().astimezone().isoformat(timespec="seconds")
checks, ok = {}, True


def check(name, cond, detail=None):
    global ok
    checks[name] = {"pass": bool(cond), "detail": detail}
    ok &= bool(cond)
    print(("PASS " if cond else "FAIL ") + name, flush=True)


# --------------------------------------------------------------------------------------------- ids (frozen once, before any inference)
P02_MAN = json.loads((C.EXP4 / "evaluation" / "P02_comprehensive_extraction_dev50" / "run_manifest.json").read_text(encoding="utf-8-sig"))
IDS_FILE = C.TRACK / "manifests" / "FROZEN_50_PROMPT_DEV_IDS.json"
if not IDS_FILE.exists():
    ids = list(C.PROMPT_DEV_IDS)
    assert ids == P02_MAN["encounter_ids"] and len(ids) == 50 and not set(ids) & set(C.SPLIT["validation_ids"]) and len(set(ids)) == 50
    C.write_json(IDS_FILE, {"purpose": "the 50 original prompt-development encounter ids, identical to the 0.6B P02 / S1 / S1.1 runs; frozen before any 1.7B inference",
                            "source": "EXP_004/experiments/split_v1.json prompt_dev_ids (== EXP_004 P02 run manifest encounter_ids)", "history": "these 50 records were previously used for Qwen3-0.6B prompt development (P00-P05, S1, S1.1): "
                            "all 1.7B results on them are DEVELOPMENT-ONLY, not independent validation", "ids": ids, "created": now()})
    os.chmod(IDS_FILE, stat.S_IREAD)
FROZEN_IDS = json.loads(IDS_FILE.read_text(encoding="utf-8"))["ids"]
IDS = FROZEN_IDS if A.ids_spec == "prompt_dev" else FROZEN_IDS[:1]
IDS_SUBSET_FILE = None
if A.ids:
    IDS_SUBSET_FILE = Path(A.ids) if Path(A.ids).is_absolute() else C.TRACK / A.ids
    _sub = json.loads(IDS_SUBSET_FILE.read_text(encoding="utf-8")) if IDS_SUBSET_FILE.exists() else {}
    IDS = list(_sub.get("ids", []))
    _inside = str(IDS_SUBSET_FILE.resolve()).lower().startswith(str(C.TRACK.resolve()).lower())
    check("ids_file_is_inside_the_track_folder", _inside, str(IDS_SUBSET_FILE))
    if not _inside:
        IDS_SUBSET_FILE = None          # fails the pre-flight cleanly (exit 2); nothing below needs a track-relative path
    check("ids_file_is_an_ordered_duplicate_free_subset_of_the_frozen_50_and_no_validation_id",
          A.ids_spec == "prompt_dev" and bool(IDS) and len(set(IDS)) == len(IDS) and set(IDS) <= set(FROZEN_IDS) and not set(IDS) & set(C.SPLIT["validation_ids"]) and len(IDS) == _sub.get("n_ids", len(IDS)),
          {"file": A.ids, "ids": IDS})
    check("ids_file_is_read_only", IDS_SUBSET_FILE is not None and IDS_SUBSET_FILE.exists() and not os.access(IDS_SUBSET_FILE, os.W_OK))
check("ids_are_the_frozen_50_prompt_dev_ids", FROZEN_IDS == P02_MAN["encounter_ids"] == C.PROMPT_DEV_IDS and len(FROZEN_IDS) == 50 and not set(FROZEN_IDS) & set(C.SPLIT["validation_ids"]))
check("prompt_file_exists", PROMPT.exists(), str(PROMPT))
if A.label == "P00":
    check("P00_prompt_is_the_unchanged_0.6B_direct_prompt", C.sha256_file(PROMPT) == C.P00_EXPECTED_SHA, C.sha256_file(PROMPT))
need = ["openvino_model.xml", "openvino_model.bin", "openvino_tokenizer.xml", "openvino_detokenizer.xml", "config.json", "tokenizer.json"]
check("converted_model_files_present", all((C.OV_MODEL_DIR / f).exists() for f in need))
rec = json.loads(C.CONVERSION_RECORD.read_text(encoding="utf-8")) if C.CONVERSION_RECORD.exists() else {}
check("conversion_record_matches_model_xml_and_bin_size", bool(rec) and rec["converted_files"]["openvino_model.xml"]["sha256"] == C.sha256_file(C.OV_MODEL_DIR / "openvino_model.xml")
      and rec["converted_files"]["openvino_model.bin"]["bytes"] == (C.OV_MODEL_DIR / "openvino_model.bin").stat().st_size and rec["source_revision"] == C.REVISION)
leg = INT.verify_legacy_tree()
check("0.6B_tree_identical_to_pre_rename_inventory", leg["ok"], {k: leg[k] for k in ("files_expected", "n_mismatched", "n_missing", "n_new", "mismatched", "missing", "new_unexpected")})
fz06 = INT.verify_frozen_0_6b()
check("0.6B_frozen_P00_P05_evaluator_and_schema_unchanged", fz06["ok"], fz06)
check("access_guard_blocks_validation_test_and_sealed_paths (predicate, no file opened)", all(C.G.StrictAccessSpy(allow_validation=False).forbidden(p) for p in (
      C.S.INPUT_DIR / f"encounter_{C.SPLIT['validation_ids'][0]}.json", C.S.DATASET_DIR / "output" / "inputs" / f"encounter_{json.loads((C.S.SPLIT_DIR / 'test_ids.json').read_text())[0]}.json", C.G.SEALED)))

# --------------------------------------------------------------------------------------------- config + freeze
(EXP / "configs").mkdir(parents=True, exist_ok=True)
CONFIG = EXP / "configs" / f"{RUN}_CONFIG.json"
cfg = {"experiment": A.experiment, "run_id": RUN, "prompt_label": A.label, "prompt_file": str(PROMPT.relative_to(C.TRACK)).replace("\\", "/"), "prompt_sha256": C.sha256_file(PROMPT) if PROMPT.exists() else None,
       "ids": IDS, "ids_file": "manifests/FROZEN_50_PROMPT_DEV_IDS.json", "ids_spec": A.ids_spec, "ids_subset_file": str(IDS_SUBSET_FILE.relative_to(C.TRACK)).replace("\\", "/") if IDS_SUBSET_FILE else None,
       "pilot_controls": {"min_available_ram_gb_GiB": A.min_available_ram_gb, "retries": A.retries, "stop_on_oom": A.stop_on_oom},
       "model_id": C.MODEL_ID, "model_revision": C.REVISION,
       "runtime": "openvino_genai.LLMPipeline, FP16 IR converted with optimum-intel (see manifests/CONVERSION_RECORD_Qwen3-1.7B.json), fresh pipeline per encounter", "device": "GPU",
       "generation": {"do_sample": False, "enable_thinking": False, "max_new_tokens": A.max_new_tokens,
                      "note": "0.6B EXP_003/EXP_004/P02 runs used max_new_tokens 6144; 4096 is the approved initial value for 1.7B (longest 0.6B P02 output 2,674 tokens); token-cap hits are recorded"},
       "transcript_rendering": "existing renderer (IR.render_transcript), unchanged", "output_contract": "canonical clinical_extraction_schema.json (unchanged)", "compiled_model_cache": str((EXP / "ov_cache").relative_to(C.TRACK)).replace("\\", "/"),
       "dataset_scope": "development-only (50 prompt-dev ids, previously used for 0.6B prompt development; not independent validation)"}
FREEZE = C.TRACK / "manifests" / f"FREEZE_{RUN}.json"
FILES = [PROMPT, HERE / "run_prompt.py", HERE / "ov_client_1_7b.py", HERE / "common_1_7b.py", HERE / "integrity_1_7b.py", HERE / "evaluate_run.py", IDS_FILE, C.CONVERSION_RECORD] + ([IDS_SUBSET_FILE] if IDS_SUBSET_FILE else [])
if not A.preflight_only and not A.freeze_only and A.ids_spec != "smoke1" or A.freeze_only:
    pass
if FREEZE.exists():
    fz = json.loads(FREEZE.read_text(encoding="utf-8"))
    cur = {str(p.relative_to(C.TRACK)).replace("\\", "/"): C.sha256_file(p) for p in FILES if p.exists()}
    bad = [k for k, h in fz["files"].items() if cur.get(k) != h]
    if CONFIG.exists() and C.sha256_file(CONFIG) != fz["config_sha256"]:
        bad.append("config")
    check("run_matches_its_freeze_manifest", not bad, bad)
else:
    check("run_has_no_freeze_yet (will be created now)", True)
C.write_json(EXP / "logs" / f"preflight_{RUN}.json", {"time": now(), "all_pass": ok, "checks": checks})
if not ok:
    print("PRE-FLIGHT FAILED")
    sys.exit(2)
if not FREEZE.exists() and A.ids_spec == "prompt_dev":
    C.write_json(CONFIG, cfg)
    C.write_json(FREEZE, {"run_id": RUN, "created": now(), "config_sha256": C.sha256_file(CONFIG), "files": {str(p.relative_to(C.TRACK)).replace("\\", "/"): C.sha256_file(p) for p in FILES},
                          "evaluator_files_0_6B": json.loads((C.EXP4 / "P05_FREEZE_MANIFEST.json").read_text(encoding="utf-8"))["evaluator_files_sha256"],
                          "note": "created before the first inference of this run; any later change of a listed file stops the run (exit 4)"})
    for p in (CONFIG, FREEZE):
        os.chmod(p, stat.S_IREAD)
    print("frozen:", FREEZE.name)


# --------------------------------------------------------------------------------------------- RAM gate (system-wide available RAM, GiB = 2**30 bytes; no model is loaded here)
def ram_reading():
    import psutil
    vm = psutil.virtual_memory()
    big = sorted(((p.info["name"], round(p.info["memory_info"].rss / 2**20)) for p in psutil.process_iter(["name", "memory_info"]) if p.info.get("memory_info")), key=lambda x: -x[1])[:8]
    return {"time": now(), "available_GiB": round(vm.available / 2**30, 3), "total_GiB": round(vm.total / 2**30, 3), "largest_processes_name_and_rss_MiB": big}


def ram_gate(stage):
    """hard gate: refuse to continue (exit 2) when available RAM < --min-available-ram-gb; never lowers the threshold; returns the reading"""
    r = ram_reading()
    r.update(stage=stage, threshold_GiB=A.min_available_ram_gb)
    if A.min_available_ram_gb is not None and r["available_GiB"] < A.min_available_ram_gb:
        C.write_json(EXP / "logs" / f"RAM_GATE_FAILED_{RUN}.json", r)
        print(f"RAM GATE FAILED ({stage}): {r['available_GiB']} GiB available < {A.min_available_ram_gb} GiB required; no model was loaded. Close large applications and re-run; the threshold is not lowered automatically.\n"
              f"largest processes (name, MiB): {r['largest_processes_name_and_rss_MiB']}", flush=True)
        sys.exit(2)
    return r


if A.freeze_only or A.preflight_only:
    if A.min_available_ram_gb is not None:
        _r = ram_reading()
        print(f"RAM gate (report only in this mode): {_r['available_GiB']} GiB available vs {A.min_available_ram_gb} GiB required -> {'WOULD PASS' if _r['available_GiB'] >= A.min_available_ram_gb else 'WOULD FAIL'}")
    print("pre-flight passed" + (" and frozen" if A.freeze_only else ""))
    sys.exit(0)

# --------------------------------------------------------------------------------------------- inference
from ov_client_1_7b import OVClient17B  # noqa: E402
from direct_inference_baseline.inference import inference_runner as IR  # noqa: E402
from direct_inference_baseline.inference.base_client import PermanentInferenceError, TransientInferenceError  # noqa: E402

RAM_AT_LAUNCH = ram_gate("immediately before the first model load")      # exits 2 here if below the threshold: nothing has been loaded yet

cache = EXP / "ov_cache"
cache.mkdir(exist_ok=True)
base = EXP / "outputs"
C.S.RAW_DIR, C.S.PARSED_DIR, C.S.FAILED_DIR, C.S.REPORT_DIR = (base / "raw", base / "parsed", base / "failed", EXP / "evaluations")
C.S.PROMPT_PATH = PROMPT
C.G.install(IDS, include_labels=False, allow_validation=False)
(EXP / "logs").mkdir(exist_ok=True)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", handlers=[logging.StreamHandler(), logging.FileHandler(EXP / "logs" / f"inference_{RUN}.log", encoding="utf-8")])
PERF = EXP / "logs" / f"performance_{RUN}.json"


OOM_RE = re.compile(r"out of (device |host |gpu )?(memory|resources)|bad_alloc|failed to allocate|cannot allocate|allocation (failed|failure)|CL_OUT_OF|MEM_OBJECT_ALLOCATION", re.I)


def is_oom_error(e):
    return isinstance(e, MemoryError) or bool(OOM_RE.search(f"{type(e).__name__}: {e}"))


class OOMStop(BaseException):
    """raised only with --stop-on-oom.  A BaseException on purpose: neither BaseClient.generate's transient-retry loop nor inference_runner's per-record `except Exception` can swallow it,
    so an out-of-memory error stops the run instead of being recorded as one failed record followed by the next record."""


class LoggedClient(OVClient17B):
    def _generate_once(self, user_prompt, max_new_tokens):
        try:
            res = super()._generate_once(user_prompt, max_new_tokens)
        except (TransientInferenceError, PermanentInferenceError, MemoryError) as e:
            if A.stop_on_oom and is_oom_error(e):
                raise OOMStop(f"{type(e).__name__}: {e}") from e
            raise
        prev = json.loads(PERF.read_text(encoding="utf-8")) if PERF.exists() else {"run_id": RUN, "device": "GPU", "per_call_in_order": []}
        prev["per_call_in_order"].append(self.perf_log[-1])
        PERF.write_text(json.dumps(prev, indent=1), encoding="utf-8")
        return res


client = LoggedClient("GPU", C.OV_MODEL_DIR, cache)
C.write_json(EXP / "logs" / f"run_settings_{RUN}.json", {"run_id": RUN, "start_local": now(), "ids": IDS, "model": client.describe(), "max_new_tokens": A.max_new_tokens, "prompt_sha256": C.sha256_file(PROMPT),
                                                         "pilot_controls": {"min_available_ram_gb_GiB": A.min_available_ram_gb, "retries": A.retries, "stop_on_oom": A.stop_on_oom}, "ram_reading_before_first_model_load": RAM_AT_LAUNCH})
spy = C.G.StrictAccessSpy(allow_validation=False)
t0 = time.perf_counter()
try:
    with spy:
        manifest = IR.run_inference(client, IDS, "development", A.max_new_tokens, experiment_id=RUN, resume=True, retries=A.retries, base_seconds=2.0)
except OOMStop as e:
    _mp = EXP / "evaluations" / RUN / "run_manifest.json"
    _done = list(json.loads(_mp.read_text(encoding="utf-8-sig"))["records"]) if _mp.exists() else []
    _stop = {"run_id": RUN, "time": now(), "exact_error": str(e), "completed_records_before_stop": _done, "record_being_processed": next((i for i in IDS if i not in _done), None), "ids_in_run_order": IDS,
             "ram_at_stop": ram_reading(), "action": "run stopped; no retry, no device/precision/setting change; the run is resumable with the same command after the memory problem is resolved"}
    C.write_json(EXP / "logs" / f"OOM_STOP_{RUN}.json", _stop)
    C.write_json(EXP / "logs" / f"file_access_audit_{RUN}.json", {**spy.report(), "stopped_on_oom": True})
    print("STOP: out-of-memory error; run stopped without retry. Exact error:", str(e), flush=True)
    sys.exit(5)
wall = round(time.perf_counter() - t0, 1)
audit = spy.report()
audit.update({"wall_seconds_this_invocation": wall, "finished_local": now(), "ids": IDS})
C.write_json(EXP / "logs" / f"file_access_audit_{RUN}.json", audit)
leg2 = INT.verify_legacy_tree()
fz = json.loads(FREEZE.read_text(encoding="utf-8")) if FREEZE.exists() else {"files": {}}
unchanged = leg2["ok"] and all(C.sha256_file(C.TRACK / k) == h for k, h in fz["files"].items())
if audit["locked_test_files_opened"] or audit["sealed_hash_file_opened"] or audit["label_files_opened"] or audit["validation_records_opened"] or not unchanged:
    print("STOP: forbidden access or a frozen/0.6B hash changed", json.dumps({k: audit[k] for k in ("locked_test_files_opened", "sealed_hash_file_opened", "label_files_opened", "validation_records_opened")}), unchanged, leg2)
    sys.exit(4)
recs = manifest["records"].values()
print(json.dumps({"run": RUN, "records": len(manifest["records"]), "parsed": sum(1 for r in recs if r.get("status") == "parsed"), "failed": sum(1 for r in recs if r.get("status") == "failed"),
                  "token_cap_hits": sum(1 for r in recs if r.get("finish_reason") == "length"), "wall_seconds": wall, "frozen_and_0_6B_hashes_unchanged": unchanged}, indent=1))
