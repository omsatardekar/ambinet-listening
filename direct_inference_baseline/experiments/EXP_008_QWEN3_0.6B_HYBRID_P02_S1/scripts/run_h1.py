"""EXP_008 runner: Qwen3-0.6B (OpenVINO FP16, Intel GPU) with the H1 hybrid prompt (full P02 schema + S1.1 B1 discipline, no example facts).

usage (project OpenVINO env, from anywhere):
    env_openvino\\Scripts\\python.exe -B -s run_h1.py <run_id> <ids_spec> [--prompt <file under prompts/>]
    ids_spec = smoke  (3 development ids that are NOT among the 30 evaluated ones; used only to check the prompt before freezing)
             | main30 (exactly the 30 ids of the 1.7B P02 run: direct_inference_1_7B/manifests/P02_30_IDS.json)

The existing inference runner, parser, schema validator and OpenVINO client are imported READ-ONLY (same as EXP_004/EXP_007); every output goes into
EXP_008/outputs/<run_id>/. Labels are never opened here (file-access audit). Greedy decoding, thinking off, a fresh pipeline per encounter,
max_new_tokens 6144 (the longest 0.6B full-schema output so far was 2,674 tokens). Resumable: finished encounters are skipped.
"""
import json
import logging
import sys
import time
from pathlib import Path

import psutil

EXP8 = Path(__file__).resolve().parents[1]
EXP4 = EXP8.parent / "EXP_004_QWEN3_0.6B_PROMPT_ENGINEERING"
ROOT = EXP8.parents[2]
sys.path.insert(0, str(EXP4 / "experiments"))
sys.dont_write_bytecode = True
from common import OV_MODEL_DIR, S, FileAccessSpy, sha256_file, write_json     # noqa: E402  (EXP_004 shared setup; also puts the repository root on sys.path)
from ov_client import OpenVINOGenAIClient                                       # noqa: E402
from direct_inference_baseline.evaluation.dataset_split import load_split       # noqa: E402
from direct_inference_baseline.inference import inference_runner as IR         # noqa: E402

MAX_NEW_TOKENS = 6144
MIN_AVAILABLE_RAM_GIB = 3.5          # the 0.6B runs peaked at about 3.1 GB working set (EXP_004 performance logs); the 8 GiB gate belongs to the 1.7B P02 runs
CACHE_DIR = EXP8 / "ov_cache"
# Words that the old 1.7B P02 prompt used as worked examples and that a small model copied into its answers. The H1 prompt must contain none of them.
FORBIDDEN_IN_PROMPT = ["hip pain", "gallstone", "aunt", "98.6", "138/86", "muscle strain", "disc problem", "sinus", "shoulder", "blood results", "left eyelid",
                       "hoarse", "hiccup", "gout", "blurred vision", "small white tablet", "twitch", "flutter", "fever", "ankle", "stomach", "evening"]


def ids_for(spec: str) -> list[str]:
    frozen50 = json.loads((ROOT / "direct_inference_1_7B/manifests/FROZEN_50_PROMPT_DEV_IDS.json").read_text(encoding="utf-8"))["ids"]
    thirty = json.loads((ROOT / "direct_inference_1_7B/manifests/P02_30_IDS.json").read_text(encoding="utf-8"))["ids"]
    if spec == "main30":
        assert thirty == frozen50[:30], "the 30 ids must be the first 30 of the frozen 50 (same as P01/P02 of the 1.7B track)"
        return thirty
    if spec == "smoke":
        spare = [i for i in frozen50 if i not in thirty]
        assert len(spare) == 20
        return spare[:3]
    if spec.startswith("one:"):                                       # a single spare (non-evaluated) id, for fast prompt checks
        one = spec.split(":", 1)[1]
        assert one in frozen50 and one not in thirty, "single-id checks are only allowed on the 20 spare ids, never on the 30 evaluated ones"
        return [one]
    raise SystemExit("ids_spec must be smoke, one:<spare id> or main30")


def main() -> int:
    args = sys.argv[1:]
    run_id, spec = args[0], args[1]
    prompt_name = args[args.index("--prompt") + 1] if "--prompt" in args else "H1_hybrid_prompt.txt"
    ids = ids_for(spec)
    dev, test = set(load_split("development")), set(load_split("test"))
    assert set(ids) <= dev and not set(ids) & test, "only development ids may be used; the locked test set is never touched"

    prompt_path = EXP8 / "prompts" / prompt_name
    text = prompt_path.read_text(encoding="utf-8")
    low = text.lower()
    leaked = [w for w in FORBIDDEN_IN_PROMPT if w in low]
    if "--no-leak-check" in args:                                    # ONLY for re-running an old prompt as a sanity check of this runner; never for the H1 prompt
        leaked = []
    assert not leaked, f"prompt contains old example words: {leaked}"
    assert "{TRANSCRIPT}" in text and "{ENCOUNTER_ID}" in text

    base = EXP8 / "outputs" / run_id
    S.RAW_DIR, S.PARSED_DIR, S.FAILED_DIR = (base / n for n in ("raw_predictions", "parsed_predictions", "failed_predictions"))
    S.REPORT_DIR = EXP8 / "evaluation"
    S.PROMPT_PATH = prompt_path
    base.mkdir(parents=True, exist_ok=True)
    (EXP8 / "logs").mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.StreamHandler(), logging.FileHandler(base / "inference.log", encoding="utf-8")])
    perf_path = base / "performance.json"

    for name in ("openvino_model.xml", "openvino_model.bin", "openvino_tokenizer.xml"):
        assert (OV_MODEL_DIR / name).exists(), f"model file missing: {name}"
    write_json(base / "run_settings.json", {
        "run_id": run_id, "ids_spec": spec, "n_ids": len(ids), "ids": ids, "prompt_file": str(prompt_path.relative_to(ROOT)), "prompt_sha256": sha256_file(prompt_path),
        "model": "Qwen/Qwen3-0.6B (revision c1899de289a04d12100db370d81485cdf75e47ca), OpenVINO FP16 IR from EXP_002", "model_dir": str(OV_MODEL_DIR.relative_to(ROOT)),
        "device": "GPU", "generation": {"do_sample": False, "enable_thinking": False, "max_new_tokens": MAX_NEW_TOKENS}, "pipeline": "fresh LLMPipeline per encounter",
        "min_available_ram_gib_before_each_encounter": MIN_AVAILABLE_RAM_GIB, "dataset": "dataset_v2_batch_001_corrected", "forbidden_words_checked_absent": FORBIDDEN_IN_PROMPT})

    class GuardedClient(OpenVINOGenAIClient):
        def _generate_once(self, user_prompt, max_new_tokens):
            waited = 0
            while psutil.virtual_memory().available / 2**30 < MIN_AVAILABLE_RAM_GIB:        # never start a generation without memory headroom
                if waited >= 1200:
                    raise RuntimeError(f"available RAM stayed below {MIN_AVAILABLE_RAM_GIB} GiB for 20 minutes; close other applications and resume (the run is resumable)")
                logging.warning("available RAM %.2f GiB < %.1f GiB; waiting", psutil.virtual_memory().available / 2**30, MIN_AVAILABLE_RAM_GIB)
                time.sleep(30)
                waited += 30
            res = super()._generate_once(user_prompt, max_new_tokens)
            prev = json.loads(perf_path.read_text(encoding="utf-8")) if perf_path.exists() else {"run_id": run_id, "device": "GPU", "per_call_in_order": []}
            prev["per_call_in_order"].append(self.perf_log[-1])
            perf_path.write_text(json.dumps(prev, indent=1), encoding="utf-8")
            return res

    logging.info("run %s | prompt %s sha256 %s | %d ids (%s) | max_new_tokens %d", run_id, prompt_name, sha256_file(prompt_path), len(ids), spec, MAX_NEW_TOKENS)
    client = GuardedClient("GPU", cache_dir=CACHE_DIR)
    t0 = time.perf_counter()
    with FileAccessSpy() as spy:
        manifest = IR.run_inference(client, ids, "development", MAX_NEW_TOKENS, experiment_id=run_id, resume=True, retries=3, base_seconds=2.0)
    leak = spy.label_or_blueprint_accesses()
    write_json(base / "file_access_audit.json", {"files_opened_count": len(spy.opened), "label_or_blueprint_files_opened": leak,
                                                 "wall_seconds_this_invocation": round(time.perf_counter() - t0, 1)})
    recs = manifest["records"]
    summary = {"run": run_id, "prompt_sha256": sha256_file(prompt_path), "records": len(recs), "parsed": sum(r["status"] == "parsed" for r in recs.values()),
               "failed": sum(r["status"] == "failed" for r in recs.values()), "length_cap_hits": sum(r.get("finish_reason") == "length" for r in recs.values()),
               "max_completion_tokens": max((r.get("completion_tokens") or 0) for r in recs.values()) if recs else 0, "label_accesses": len(leak)}
    write_json(base / "run_summary.json", summary)
    print(json.dumps(summary, indent=1))
    return 1 if leak else 0


if __name__ == "__main__":
    sys.exit(main())
