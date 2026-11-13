"""EXP_003 five-record development smoke test: existing runner + existing prompt/parser/schema validator, OpenVINO GPU client. Labels are never opened here."""
import json
import logging
import sys
import time

from common import EXP3, EXPERIMENT_ID, MAX_NEW_TOKENS, SMOKE_IDS, S, FileAccessSpy, write_json
from ov_client import OpenVINOGenAIClient
from direct_inference_baseline.inference import inference_runner as IR

(EXP3 / "logs").mkdir(exist_ok=True)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                    handlers=[logging.StreamHandler(), logging.FileHandler(EXP3 / "logs" / "inference.log", encoding="utf-8")])
client = OpenVINOGenAIClient("GPU")
desc = client.describe()
logging.info("starting %s ids=%s device=%s", EXPERIMENT_ID, SMOKE_IDS, desc["device"])
t0 = time.perf_counter()
with FileAccessSpy() as spy:
    manifest = IR.run_inference(client, SMOKE_IDS, "development", MAX_NEW_TOKENS, experiment_id=EXPERIMENT_ID, resume=True, retries=3, base_seconds=2.0)
wall = time.perf_counter() - t0
leak = spy.label_or_blueprint_accesses()
write_json(EXP3 / "logs" / "inference_file_access_audit.json", {"files_opened_count": len(spy.opened), "label_or_blueprint_files_opened": leak,
                                                               "note": "audit covers builtins.open / Path.read_text / Path.read_bytes during inference"})
write_json(EXP3 / "logs" / "performance_per_encounter.json", {"experiment_id": EXPERIMENT_ID, "device": "GPU", "total_wall_seconds_this_invocation": round(wall, 1),
                                                              "per_call_in_order": client.perf_log, "note": "peak working set is cumulative for the process (max so far)"})
recs = manifest["records"]
print(json.dumps({"experiment_id": EXPERIMENT_ID, "records": len(recs), "parsed": sum(r["status"] == "parsed" for r in recs.values()),
                  "failed": sum(r["status"] == "failed" for r in recs.values()), "label_accesses": len(leak)}, indent=1))
sys.exit(1 if leak else 0)
