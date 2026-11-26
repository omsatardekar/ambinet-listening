"""EXP_004 P04 SMOKE TEST runner (five approved prompt_dev ids only). Same model/runtime/settings as EXP_003/P00-P03; only the prompt and the evidence-builder step differ.
Pipeline: existing inference loop (unchanged) -> model output = INTERMEDIATE JSON (saved raw) -> existing parse -> evidence_builder -> FINAL JSON -> existing validator -> saved as parsed prediction.
The existing inference module is not modified: its parse step is wrapped at run time (same pattern as common.use_run). Labels are never opened here (file-access audit)."""
import copy
import datetime
import hashlib
import json
import platform
import sys
import time

from common import EXP4, EXP2, EXP3, MAX_NEW_TOKENS, SOURCE_REVISION, SPLIT, S, FileAccessSpy, sha256_file, use_run, write_json
from ov_client import OpenVINOGenAIClient
from evidence_builder import build_evidence, verify_only_evidence_changed
from direct_inference_baseline.evaluation import schema_validator as SV
from direct_inference_baseline.evaluation.dataset_split import load_split
from direct_inference_baseline.inference import inference_runner as IR
import logging

RUN = "P04_smoke_5"
PROMPT = "P04_integrated_segment_evidence.txt"
APPROVED_SHA = "e05c8beaf82380bdd9581acd07fc77940a363346eb003d44295364683c5aaf55"
IDS = ["00035", "00037", "00040", "00215", "00248"]
base = use_run(RUN, PROMPT)
for d in ("raw_predictions", "parsed_predictions", "failed_predictions", "intermediate_predictions", "build_reports"):
    (base / d).mkdir(parents=True, exist_ok=True)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", handlers=[logging.StreamHandler(), logging.FileHandler(base / "inference.log", encoding="utf-8")])
now = lambda: datetime.datetime.now().astimezone().isoformat(timespec="seconds")

# ---------------- pre-flight (abort on any mismatch)
pf = {"started_local": now(), "checks": {}}
ok = True


def check(name, cond, detail=None):
    global ok
    pf["checks"][name] = {"pass": bool(cond), "detail": detail}
    ok &= bool(cond)


sha = sha256_file(S.PROMPT_PATH)
check("prompt_sha256_equals_approved", sha == APPROVED_SHA, {"actual": sha, "approved": APPROVED_SHA})
dev, test = set(load_split("development")), set(load_split("test"))
check("ids_are_exactly_the_five_approved", IDS == ["00035", "00037", "00040", "00215", "00248"] and len(set(IDS)) == 5)
check("ids_in_prompt_dev_50", all(i in SPLIT["prompt_dev_ids"] for i in IDS))
check("ids_not_in_validation_50", not set(IDS) & set(SPLIT["validation_ids"]))
check("ids_not_in_locked_test_400", not set(IDS) & test and set(IDS) <= dev)
conv = json.loads((EXP2 / "conversion_record.json").read_text(encoding="utf-8"))["converted_files"]
mism = [f for f, v in conv.items() if (EXP2 / "models" / "Qwen3-0.6B-ov-fp16" / f).exists() and sha256_file(EXP2 / "models" / "Qwen3-0.6B-ov-fp16" / f) != v["sha256"]]
missing = [f for f in conv if not (EXP2 / "models" / "Qwen3-0.6B-ov-fp16" / f).exists()]
check("openvino_fp16_model_files_match_EXP_002_conversion_record", not mism and not missing, {"files_checked": len(conv), "mismatch": mism, "missing": missing})
check("max_new_tokens_6144", MAX_NEW_TOKENS == 6144)
check("source_revision", SOURCE_REVISION == "c1899de289a04d12100db370d81485cdf75e47ca")
client = OpenVINOGenAIClient("GPU")
desc = client.describe()
prev = {k: json.loads((EXP4 / "evaluation" / k / "run_manifest.json").read_text(encoding="utf-8")) for k in ("P02_comprehensive_extraction_dev50", "P03_evidence_grounded_dev50")}
for k, m in prev.items():
    check(f"model_runtime_settings_identical_to_{k}", m["model"] == desc and m["max_new_tokens"] == MAX_NEW_TOKENS, {"differences": [x for x in desc if m["model"].get(x) != desc[x]]})
pf["describe"] = desc
pf["script_hashes"] = {n: sha256_file(EXP4 / "experiments" / n) for n in ("ov_client.py", "common.py", "evidence_builder.py", "run_p04_smoke.py")}
pf["python"] = sys.version.split()[0]; pf["platform"] = platform.platform()
pf["frozen_files"] = {"p00": sha256_file(EXP4 / "prompts" / "P00_original_baseline.txt"), "p02": sha256_file(EXP4 / "prompts" / "P02_comprehensive_extraction.txt")}
pf["all_pass"] = ok
write_json(base / "preflight.json", pf)
if not ok:
    print(json.dumps(pf["checks"], indent=1)); print("PRE-FLIGHT FAILED: not running inference"); sys.exit(2)
logging.info("pre-flight passed; prompt sha256 %s; ids %s", sha, IDS)

# ---------------- wrap the parse step: parse -> build evidence
_orig_parse, _orig_build_prompt = IR.parse_response, IR.build_prompt
cur = {}


def build_prompt_capture(eid, inp=None, template=None):
    inp = inp or IR.load_transcript(eid)
    cur["eid"], cur["inp"] = eid, inp
    return _orig_build_prompt(eid, inp, template)


def parse_and_build(text, finish_reason="stop"):
    pr = _orig_parse(text, finish_reason)
    if pr.status != "ok":
        return pr
    eid, inp = cur["eid"], cur["inp"]
    intermediate = copy.deepcopy(pr.data)
    write_json(base / "intermediate_predictions" / f"encounter_{eid}.json", intermediate)
    try:
        final, rep = build_evidence(intermediate, inp, top_key_order=list(SV.TOP_KEYS))
        integ = verify_only_evidence_changed(intermediate, final)
        rep["integrity_identical_except_evidence_fields"] = integ["identical_except_evidence_fields"]
        rep["n_items_before"], rep["n_items_after"] = integ["n_items_before"], integ["n_items_after"]
        write_json(base / "build_reports" / f"encounter_{eid}.json", rep)
        pr.data = final
        pr.notes = list(pr.notes) + ["evidence built from source_segments"]
    except Exception as e:  # noqa: BLE001 - recorded as a failure, never swallowed silently
        pr.status, pr.data = "builder_error", None
        pr.notes = list(pr.notes) + [f"builder error: {type(e).__name__}: {e}"]
    return pr


IR.parse_response, IR.build_prompt = parse_and_build, build_prompt_capture

PERF = base / "performance.json"


class LoggedClient(OpenVINOGenAIClient):
    def _generate_once(self, user_prompt, max_new_tokens):
        res = super()._generate_once(user_prompt, max_new_tokens)
        prev_ = json.loads(PERF.read_text(encoding="utf-8")) if PERF.exists() else {"run_id": RUN, "device": "GPU", "per_call_in_order": []}
        prev_["per_call_in_order"].append(self.perf_log[-1])
        PERF.write_text(json.dumps(prev_, indent=1), encoding="utf-8")
        return res


# hash verified again immediately before inference
assert sha256_file(S.PROMPT_PATH) == APPROVED_SHA
t0, start_local = time.perf_counter(), now()
write_json(base / "run_settings.json", {"run_id": RUN, "prompt_file": f"prompts/{PROMPT}", "prompt_sha256_verified_before_inference": APPROVED_SHA, "ids": IDS, "max_new_tokens": MAX_NEW_TOKENS, "model": desc,
                                        "start_local": start_local, "end_local": None, "note": "same model, FP16 OpenVINO, GPU, greedy, thinking off, 6144-token cap as EXP_003/P00-P03"})
client = LoggedClient("GPU")
with FileAccessSpy() as spy:
    manifest = IR.run_inference(client, IDS, "development", MAX_NEW_TOKENS, experiment_id=RUN, resume=True, retries=3, base_seconds=2.0)
leak = spy.label_or_blueprint_accesses()
assert sha256_file(S.PROMPT_PATH) == APPROVED_SHA, "prompt changed during the run"
end_local = now()
rs = json.loads((base / "run_settings.json").read_text(encoding="utf-8")); rs.update(end_local=end_local, wall_seconds=round(time.perf_counter() - t0, 1), prompt_sha256_verified_after_inference=sha256_file(S.PROMPT_PATH))
write_json(base / "run_settings.json", rs)
write_json(base / "file_access_audit.json", {"files_opened_count": len(spy.opened), "label_or_blueprint_files_opened": leak, "locked_test_inputs_opened": [p for p in spy.opened if any(f"encounter_{i}.json" in p for i in test - set(IDS))][:5]})
recs = manifest["records"]
print(json.dumps({"run": RUN, "records": len(recs), "parsed": sum(r["status"] == "parsed" for r in recs.values()), "failed": {k: r.get("failure_type") for k, r in recs.items() if r["status"] != "parsed"},
                  "label_accesses": len(leak)}, indent=1))
sys.exit(1 if leak else 0)
