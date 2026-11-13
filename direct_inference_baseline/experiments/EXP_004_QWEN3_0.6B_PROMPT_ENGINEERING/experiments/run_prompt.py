"""EXP_004 generic inference runner: one prompt version x one fixed list of encounter ids, GPU, EXP_003 settings. Resumable.
usage: run_prompt.py <run_id> <prompt_file> <ids_spec>   ids_spec = prompt_dev | validation | repro3
Labels are never opened here (file-access audit written next to the outputs). Only development ids are accepted."""
import json
import logging
import sys
import time

from common import EXP4, MAX_NEW_TOKENS, SPLIT, S, FileAccessSpy, sha256_file, use_run, write_json
from ov_client import OpenVINOGenAIClient
from direct_inference_baseline.evaluation.dataset_split import load_split
from direct_inference_baseline.inference import inference_runner as IR

run_id, prompt_file, spec = sys.argv[1:4]
IDS = {"prompt_dev": SPLIT["prompt_dev_ids"], "validation": SPLIT["validation_ids"], "repro3": SPLIT["prompt_dev_ids"][:3]}[spec]
dev, test = set(load_split("development")), set(load_split("test"))
assert set(IDS) <= dev and not set(IDS) & test, "only development ids may be used; the locked test set is never touched"
base = use_run(run_id, prompt_file)
assert not (EXP4 / "outputs" / run_id / "raw_predictions" / run_id).exists() or True
base.mkdir(parents=True, exist_ok=True)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                    handlers=[logging.StreamHandler(), logging.FileHandler(base / "inference.log", encoding="utf-8")])
PERF = base / "performance.json"


class LoggedClient(OpenVINOGenAIClient):
    def _generate_once(self, user_prompt, max_new_tokens):
        res = super()._generate_once(user_prompt, max_new_tokens)
        prev = json.loads(PERF.read_text(encoding="utf-8")) if PERF.exists() else {"run_id": run_id, "device": "GPU", "per_call_in_order": []}
        prev["per_call_in_order"].append(self.perf_log[-1])
        PERF.write_text(json.dumps(prev, indent=1), encoding="utf-8")
        return res


logging.info("run %s prompt %s sha256 %s ids=%d (%s)", run_id, prompt_file, sha256_file(S.PROMPT_PATH), len(IDS), spec)
client = LoggedClient("GPU")
t0 = time.perf_counter()
with FileAccessSpy() as spy:
    manifest = IR.run_inference(client, IDS, "development", MAX_NEW_TOKENS, experiment_id=run_id, resume=True, retries=3, base_seconds=2.0)
leak = spy.label_or_blueprint_accesses()
write_json(base / "file_access_audit.json", {"files_opened_count": len(spy.opened), "label_or_blueprint_files_opened": leak, "wall_seconds_this_invocation": round(time.perf_counter() - t0, 1)})
recs = manifest["records"]
print(json.dumps({"run": run_id, "prompt_sha256": sha256_file(S.PROMPT_PATH), "records": len(recs), "parsed": sum(r["status"] == "parsed" for r in recs.values()),
                  "failed": sum(r["status"] == "failed" for r in recs.values()), "label_accesses": len(leak)}, indent=1))
sys.exit(1 if leak else 0)
