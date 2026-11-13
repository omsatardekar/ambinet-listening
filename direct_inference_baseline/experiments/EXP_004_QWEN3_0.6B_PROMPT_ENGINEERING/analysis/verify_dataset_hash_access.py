"""Measure what the existing runner's frozen-dataset verification opens (no model, no GPU): which files, and are any labels or test transcripts parsed? Read-only."""
import json, sys, types
from pathlib import Path
try:
    import dotenv
except ImportError:
    sys.modules["dotenv"] = types.SimpleNamespace(load_dotenv=lambda *a, **k: False)
sys.dont_write_bytecode = True
EXP4 = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(EXP4/"experiments"))
from common import S, FileAccessSpy, SPLIT
from direct_inference_baseline.evaluation.dataset_split import load_split
test = set(load_split("test"))
with FileAccessSpy() as spy:
    r = S.verify_frozen_dataset(inputs_only=True)
inp = [p for p in spy.opened if "\inputs\\" in p or "/inputs/" in p]
t_in = [p for p in inp if any(f"encounter_{i}.json" in p for i in test)]
res = {"files_checked": r["files_checked"], "verified": r["verified"], "files_opened": len(spy.opened), "input_transcripts_opened": len(inp), "locked_test_transcripts_opened_for_checksum": len(t_in),
       "label_files_opened": len(spy.label_or_blueprint_accesses()), "mechanism": "settings.verify_frozen_dataset(inputs_only=True) re-hashes every frozen input transcript against CHECKSUMS.sha256 at the start of every run_inference call (bytes read for SHA-256; content not parsed, not rendered, not used)"}
(EXP4/"evaluation"/"frozen_dataset_hash_access_audit.json").write_text(json.dumps(res, indent=1), encoding="utf-8"); print(json.dumps(res, indent=1))
