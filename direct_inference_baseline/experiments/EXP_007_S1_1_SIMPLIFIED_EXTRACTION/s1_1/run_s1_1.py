"""EXP_007 S1.1 runner (Phase B). One arm per invocation.
usage (project OpenVINO env):  python -B -s run_s1_1.py --freeze               (pre-flight + freeze all arms; no inference)
                               python -B -s run_s1_1.py --arm B1 [--preflight-only]
Runs on exactly the 50 P02 prompt_dev records, under StrictAccessSpy; everything is written inside EXP_007. The existing inference runner (IR.run_inference), parser and OpenVINO client are used
unmodified; the ONLY run-time differences are (a) a process-local override of the transcript renderer for arms B2/B3 (R1: 'role: text'), (b) grammar-constrained decoding via a subclass in
s1_1/client_s1_1.py for arm B3, (c) max_new_tokens 2048 (approved). Exit codes: 2 pre-flight failed, 3 model/runtime differs from P02, 4 forbidden access or frozen hash changed."""
import datetime
import hashlib
import json
import logging
import os
import stat
import subprocess
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
EXP7 = HERE.parent
EXP4 = EXP7.parent / "EXP_004_QWEN3_0.6B_PROMPT_ENGINEERING"
EXP6 = EXP7.parent / "EXP_006_S1_SIMPLIFIED_EXTRACTION"
ROOT = EXP7.parents[2]
sys.path.insert(0, str(EXP4 / "experiments"))
sys.path.insert(0, str(HERE))
from common import EXP2, SOURCE_REVISION, SPLIT, S, sha256_file, write_json  # noqa: E402
import dev_guard as G  # noqa: E402
import sidecar as SC  # noqa: E402

ARGV = sys.argv[1:]
FREEZE_MODE = "--freeze" in ARGV
PREFLIGHT_ONLY = "--preflight-only" in ARGV
ARM = ARGV[ARGV.index("--arm") + 1] if "--arm" in ARGV else None
_PA = EXP7 / "manifests" / "PHASE_A_AMENDED_DECISION.json"      # Amendment 001; the original PHASE_A_RESULT.json is kept unchanged and is also frozen below
_DEC = json.loads(_PA.read_text(encoding="utf-8"))["decision"] if _PA.exists() else {}
ARMS = [a for a, k in (("B1", "B1_B2"), ("B2", "B1_B2"), ("B3", "B3")) if _DEC.get(k) == "run"]      # arms permitted by the predefined Phase A gates
now = lambda: datetime.datetime.now().astimezone().isoformat(timespec="seconds")
P02_MAN_PATH = EXP4 / "evaluation" / "P02_comprehensive_extraction_dev50" / "run_manifest.json"
P02_MAN = json.loads(P02_MAN_PATH.read_text(encoding="utf-8-sig"))
IDS = P02_MAN["encounter_ids"]
FREEZE = EXP7 / "manifests" / "S1_1_FREEZE_MANIFEST.json"
FROZEN_REL = ["design/PHASE_A_GATES.json", "manifests/PHASE_A_RESULT.json", "manifests/PHASE_A_AMENDED_DECISION.json", "design/AMENDMENT_001_PROMPT_SELECTION.md", "phase_a/results/U_P2_R0.json", "design/S1_1_output_schema.json", "design/S1_1_output_grammar.ebnf", "design/S1_1_output_grammar_G2_cap20.ebnf",
              "design/S1_1_output_grammar_G3_cap20_prefix.ebnf", "config/S1_1_ACCEPTANCE_AND_DEFINITIONS.json", "s1_1/s1_1_adapter.py", "s1_1/sidecar.py", "s1_1/client_s1_1.py", "s1_1/run_s1_1.py",
              "s1_1/evaluate_s1_1.py", "s1_1/test_s1_1_adapter.py"] + [f"config/S1_1_{a}_CONFIG.json" for a in ARMS] + [f"prompts/arm/S1_1_{a}_PROMPT.txt" for a in ARMS]
(EXP7 / "manifests").mkdir(exist_ok=True)
(EXP7 / "logs").mkdir(exist_ok=True)
checks, ok = {}, True


def check(name, cond, detail=None):
    global ok
    checks[name] = {"pass": bool(cond), "detail": detail}
    ok &= bool(cond)
    print(("PASS " if cond else "FAIL ") + name)


def git_tracked_changes():
    out = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True, timeout=120).stdout.splitlines()
    return [l for l in out if not l.startswith("??")]


def exp6_snapshot():
    snap = {}
    for p in sorted(EXP6.rglob("*")):
        if p.is_file() and not any(x in p.parts for x in ("ov_cache", "gpu_compiler", "__pycache__")):
            snap[str(p.relative_to(EXP6)).replace("\\", "/")] = sha256_file(p)
    return snap


# ------------------------------------------------------------------ pre-flight
check("ids_are_the_P02_prompt_dev_ids", IDS == SPLIT["prompt_dev_ids"] and len(IDS) == 50 and not (set(IDS) & set(SPLIT["validation_ids"])), {"n": len(IDS)})
fm = json.loads((EXP4 / "P05_FREEZE_MANIFEST.json").read_text(encoding="utf-8"))
check("P05_freeze_manifest_hash_unchanged", sha256_file(EXP4 / "P05_FREEZE_MANIFEST.json") == "e383d3a352a6e431bc74c49c8c409d15a6e02831b05ee73e47aec472fd56fae0")
bad = [f for f, h in fm["frozen_files_sha256"].items() if sha256_file(EXP4 / f) != h]
check("frozen_P00_P05_files_unchanged", not bad, {"checked": len(fm["frozen_files_sha256"]), "mismatch": bad})
check("evaluator_files_unchanged", all(sha256_file(S.MODULE_DIR / f) == h for f, h in fm["evaluator_files_sha256"].items()))
check("schema_files_unchanged", sha256_file(S.ROOT_SCHEMA) == fm["schema_sha256"]["root_schema"] and sha256_file(S.FINAL_SCHEMA) == fm["schema_sha256"]["final_schema"])
check("P02_prompt_unchanged", sha256_file(EXP4 / "prompts" / "P02_comprehensive_extraction.txt") == "cf50ce8efe850cda76fe6eadebf45391fa0461a657e52de5783edb31ccdde5d1" == P02_MAN["prompt_sha256"])
inv = [l.split(None, 1) for l in (EXP4 / "checksums" / "experiment_checksums.sha256").read_text(encoding="utf-8").splitlines() if "P02_comprehensive_extraction_dev50" in l]
badp = [p for h, p in inv if sha256_file(EXP4 / p.strip().lstrip("*").lstrip("./")) != h]
check("P02_outputs_and_evaluation_files_match_the_EXP_004_inventory", inv and not badp, {"files": len(inv), "mismatch": badp[:3]})
conv = json.loads((EXP2 / "conversion_record.json").read_text(encoding="utf-8"))["converted_files"]
mism = [f for f, v in conv.items() if sha256_file(EXP2 / "models" / "Qwen3-0.6B-ov-fp16" / f) != v["sha256"]]
check("openvino_fp16_model_files_match_EXP_002_record", not mism, {"files": len(conv), "mismatch": mism})
check("model_revision_same_as_P02", SOURCE_REVISION == "c1899de289a04d12100db370d81485cdf75e47ca" == P02_MAN["model"]["model_revision_commit"])
tc = git_tracked_changes()
check("no_tracked_file_in_the_repository_modified (git)", not tc, tc[:5])
fzm = json.loads(FREEZE.read_text(encoding="utf-8")) if FREEZE.exists() else None
if fzm:
    s6 = exp6_snapshot()
    check("EXP_006_files_unchanged_since_freeze", s6 == fzm["exp006_snapshot"], {"files": len(s6)})
G.install(IDS, include_labels=False, allow_validation=False)
spy = G.StrictAccessSpy(allow_validation=False)
check("access_guard_blocks_validation_test_and_sealed_paths (predicate, no file opened)",
      spy.forbidden(S.INPUT_DIR / f"encounter_{SPLIT['validation_ids'][0]}.json") and spy.forbidden(S.INPUT_DIR / f"encounter_{G._ids_from_split('test')[0]}.json")
      and spy.forbidden(G.SEALED) and not spy.forbidden(S.INPUT_DIR / f"encounter_{IDS[0]}.json"))
with spy:
    fz = S.verify_frozen_dataset(inputs_only=True)
    check("only_prompt_dev_inputs_hashed_and_verified", fz["verified"] and set(fz["ids"]) == set(IDS), {"files_checked": fz["files_checked"]})
spy_pre = spy.report()
check("preflight_no_forbidden_access", not spy_pre["locked_test_files_opened"] and not spy_pre["sealed_hash_file_opened"] and not spy_pre["validation_records_opened"])
cfgs = {}
for a in ARMS:
    p = EXP7 / "config" / f"S1_1_{a}_CONFIG.json"
    if p.exists():
        cfgs[a] = json.loads(p.read_text(encoding="utf-8"))
check("arm_configs_present_and_use_the_50_ids_and_cap_2048", set(cfgs) == set(ARMS) and all(c["ids"] == IDS and c["max_new_tokens"] == 2048 and c["model_revision"] == SOURCE_REVISION and c["device"] == "GPU" for c in cfgs.values()))
for a in ARMS:
    pf = EXP7 / "prompts" / "arm" / f"S1_1_{a}_PROMPT.txt"
    t = pf.read_text(encoding="utf-8") if pf.exists() else ""
    bad_words = [w for w in ("evidence", "confidence", "quality_check", "normalized", "timestamp", "segment_id", "person_1") if w in t.lower() and w != "person_1"]
    check(f"{a}_prompt_resolved_has_transcript_placeholder_and_no_forbidden_task_words", "{TRANSCRIPT}" in t and "{LAYOUT}" not in t and not bad_words, bad_words)
if FREEZE_MODE and ok and not FREEZE.exists():
    write_json(FREEZE, {"frozen_at": now(), "files": {r: sha256_file(EXP7 / r) for r in FROZEN_REL}, "exp006_snapshot": exp6_snapshot(), "note": "all Phase B arms' prompts, configs, adapter, sidecar code, client, runner, evaluator and tests frozen before any Phase B inference"})
    for r in FROZEN_REL + ["manifests/S1_1_FREEZE_MANIFEST.json"]:
        os.chmod(EXP7 / r, stat.S_IREAD)
    fzm = json.loads(FREEZE.read_text(encoding="utf-8"))
if fzm:
    check("S1_1_frozen_files_match_freeze_manifest", all(sha256_file(EXP7 / k) == h for k, h in fzm["files"].items()), {k: v for k, v in list(fzm["files"].items())[:0]})
else:
    check("S1_1_freeze_manifest_exists", False)
write_json(EXP7 / "manifests" / ("S1_1_PREFLIGHT_FREEZE.json" if FREEZE_MODE else f"S1_1_PREFLIGHT_{ARM}.json"), {"time": now(), "all_pass": ok, "checks": checks})
if not ok:
    print("PRE-FLIGHT FAILED")
    sys.exit(2)
if FREEZE_MODE or PREFLIGHT_ONLY:
    print("pre-flight passed" + (" and frozen" if FREEZE_MODE else ""))
    sys.exit(0)
assert ARM in ARMS, "--arm B1|B2|B3 required"
cfg = cfgs[ARM]
RUN = cfg["run_id"]

# ------------------------------------------------------------------ inference
from ov_client import OpenVINOGenAIClient  # noqa: E402
from direct_inference_baseline.inference import inference_runner as IR  # noqa: E402
from client_s1_1 import GrammarClient  # noqa: E402

CACHE = EXP7 / "ov_cache"
PROMPT = EXP7 / "prompts" / "arm" / f"S1_1_{ARM}_PROMPT.txt"
MAXTOK = cfg["max_new_tokens"]
if cfg["grammar"]:
    gram = (EXP7 / "design" / cfg["grammar"]["file"]).read_text(encoding="utf-8")
    client0 = GrammarClient("GPU", CACHE, gram, cfg["grammar"]["answer_prefix"])
else:
    client0 = OpenVINOGenAIClient("GPU", cache_dir=CACHE)
desc = client0.describe()
p02d = P02_MAN["model"]
same = {k: desc.get(k) == p02d.get(k) for k in ("provider", "model_id", "model_revision_commit", "device", "runtime", "openvino", "openvino_genai", "converted_model_dir", "weights_precision")}
check("model_runtime_identical_to_P02_run (provider, model, revision, device, runtime versions, weights)", all(same.values()), same)
if not all(same.values()):
    print("STOP: model/runtime differs from the P02 run")
    sys.exit(3)
S.RAW_DIR, S.PARSED_DIR, S.FAILED_DIR, S.REPORT_DIR = (EXP7 / "outputs" / "raw", EXP7 / "outputs" / "parsed", EXP7 / "outputs" / "failed", EXP7 / "manifests")
S.PROMPT_PATH = PROMPT
if cfg["rendering"] == "R1":
    IR.render_transcript = SC.render_r1          # process-local override; the existing module file is not changed
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", handlers=[logging.StreamHandler(), logging.FileHandler(EXP7 / "logs" / f"inference_{ARM}.log", encoding="utf-8")])
write_json(EXP7 / "manifests" / f"S1_1_{ARM}_RUN_SETTINGS.json", {"run_id": RUN, "arm": ARM, "start_local": now(), "ids": IDS, "model": desc, "max_new_tokens": MAXTOK, "prompt_sha256": sha256_file(PROMPT),
                                                                  "config_sha256": sha256_file(EXP7 / "config" / f"S1_1_{ARM}_CONFIG.json"), "compiled_model_cache": str(CACHE),
                                                                  "declared_differences_from_P02": ["prompt", "output structure", "max_new_tokens 2048 (P02 6144)"] + (["R1 renderer (process-local override)"] if cfg["rendering"] == "R1" else []) + (["grammar-constrained decoding + answer prefix"] if cfg["grammar"] else [])})


class LoggedMixin:
    def _generate_once(self, user_prompt, max_new_tokens):
        res = super()._generate_once(user_prompt, max_new_tokens)
        perf = EXP7 / "logs" / f"performance_{ARM}.json"
        prev = json.loads(perf.read_text(encoding="utf-8")) if perf.exists() else {"run_id": RUN, "device": "GPU", "per_call_in_order": []}
        prev["per_call_in_order"].append(self.perf_log[-1])
        perf.write_text(json.dumps(prev, indent=1), encoding="utf-8")
        return res


class LoggedClient(LoggedMixin, OpenVINOGenAIClient):
    pass


class LoggedGrammarClient(LoggedMixin, GrammarClient):
    pass


client = LoggedGrammarClient("GPU", CACHE, gram, cfg["grammar"]["answer_prefix"]) if cfg["grammar"] else LoggedClient("GPU", cache_dir=CACHE)
t0 = time.perf_counter()
with spy:
    side_dir = EXP7 / "outputs" / "sidecar"
    side_dir.mkdir(parents=True, exist_ok=True)
    amb = []
    for eid in IDS:
        inp = IR.load_transcript(eid)
        sc = SC.build_sidecar(inp)
        if any(f["kind"] in ("ambiguous_role", "unmapped_role") for f in sc["flags"]):
            amb.append(eid)
        (side_dir / f"encounter_{eid}.json").write_text(json.dumps(sc, indent=1, ensure_ascii=False), encoding="utf-8")
    if amb and cfg["rendering"] == "R1":
        print("STOP: ambiguous or unmapped speaker roles in", amb)
        sys.exit(4)
    manifest = IR.run_inference(client, IDS, "development", MAXTOK, experiment_id=RUN, resume=True, retries=3, base_seconds=2.0)
wall = round(time.perf_counter() - t0, 1)
audit = spy.report()
audit.update({"wall_seconds_this_invocation": wall, "finished_local": now(), "ids": IDS, "arm": ARM})
write_json(EXP7 / "logs" / f"file_access_audit_{ARM}.json", audit)
rs = json.loads((EXP7 / "manifests" / f"S1_1_{ARM}_RUN_SETTINGS.json").read_text(encoding="utf-8"))
rs.update(end_local=now(), wall_seconds_this_invocation=wall)
write_json(EXP7 / "manifests" / f"S1_1_{ARM}_RUN_SETTINGS.json", rs)
post = all(sha256_file(EXP7 / k) == h for k, h in fzm["files"].items()) and sha256_file(EXP4 / "P05_FREEZE_MANIFEST.json") == "e383d3a352a6e431bc74c49c8c409d15a6e02831b05ee73e47aec472fd56fae0" and exp6_snapshot() == fzm["exp006_snapshot"] and not git_tracked_changes()
if audit["locked_test_files_opened"] or audit["sealed_hash_file_opened"] or audit["label_files_opened"] or audit["validation_records_opened"] or not post:
    print("STOP: forbidden access or a frozen hash changed", json.dumps({k: audit[k] for k in ("locked_test_files_opened", "sealed_hash_file_opened", "label_files_opened", "validation_records_opened")}), post)
    sys.exit(4)
recs = manifest["records"].values()
print(json.dumps({"run": RUN, "records": len(manifest["records"]), "parsed": sum(1 for r in recs if r.get("status") == "parsed"), "failed": sum(1 for r in recs if r.get("status") == "failed"),
                  "token_cap_hits": sum(1 for r in recs if r.get("finish_reason") == "length"), "wall_seconds": wall, "frozen_hashes_unchanged": post}, indent=1))
