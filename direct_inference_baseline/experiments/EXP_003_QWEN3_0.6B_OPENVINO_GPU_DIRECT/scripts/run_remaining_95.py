"""EXP_003 stage 2: the remaining 95 development encounters (development split minus the 5 smoke-test ids), same client, prompt, decoding and runner as the smoke test.
Writes to a NEW run id so the smoke-test run (exp_003_dev_smoke_5) is untouched. Resumable: re-running skips already-answered encounters. Labels are never opened here."""
import json
import logging
import sys
import time

from common import EXP3, MAX_NEW_TOKENS, SMOKE_IDS, S, FileAccessSpy, sha256_file, write_json
from ov_client import OpenVINOGenAIClient
from direct_inference_baseline.evaluation.dataset_split import load_split
from direct_inference_baseline.inference import inference_runner as IR

RUN_ID = "exp_003_dev_remaining_95"
dev = load_split("development")
assert len(dev) == 100 and set(SMOKE_IDS) <= set(dev)
ids = [i for i in dev if i not in SMOKE_IDS]
test_ids = set(load_split("test"))
assert len(ids) == 95 and not (set(ids) & test_ids), "locked test ids must never be touched"
assert sha256_file(S.PROMPT_PATH) == "78c5ab95d0019d0b3c6801ae17f7fa29477dde37d123ecd4fda946e3dd14f604", "prompt differs from EXP_001"

(EXP3 / "logs").mkdir(exist_ok=True)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                    handlers=[logging.StreamHandler(), logging.FileHandler(EXP3 / "logs" / "inference_remaining_95.log", encoding="utf-8")])
PERF = EXP3 / "logs" / "performance_remaining_95.json"


class LoggedClient(OpenVINOGenAIClient):
    """Identical behaviour; additionally persists the performance record after every encounter (so an interruption loses nothing)."""
    def _generate_once(self, user_prompt, max_new_tokens):
        res = super()._generate_once(user_prompt, max_new_tokens)
        prev = json.loads(PERF.read_text(encoding="utf-8")) if PERF.exists() else {"experiment_id": RUN_ID, "device": "GPU", "per_call_in_order": []}
        prev["per_call_in_order"].append(self.perf_log[-1])
        PERF.write_text(json.dumps(prev, indent=1), encoding="utf-8")
        return res


client = LoggedClient("GPU")
logging.info("starting %s: %d encounters, first=%s last=%s", RUN_ID, len(ids), ids[0], ids[-1])
t0 = time.perf_counter()
with FileAccessSpy() as spy:
    manifest = IR.run_inference(client, ids, "development", MAX_NEW_TOKENS, experiment_id=RUN_ID, resume=True, retries=3, base_seconds=2.0)
leak = spy.label_or_blueprint_accesses()
write_json(EXP3 / "logs" / "inference_remaining_95_file_access_audit.json",
           {"files_opened_count": len(spy.opened), "label_or_blueprint_files_opened": leak, "wall_seconds_this_invocation": round(time.perf_counter() - t0, 1)})
recs = manifest["records"]
print(json.dumps({"run": RUN_ID, "records": len(recs), "parsed": sum(r["status"] == "parsed" for r in recs.values()),
                  "failed": sum(r["status"] == "failed" for r in recs.values()), "label_accesses": len(leak)}, indent=1))
sys.exit(1 if leak else 0)
