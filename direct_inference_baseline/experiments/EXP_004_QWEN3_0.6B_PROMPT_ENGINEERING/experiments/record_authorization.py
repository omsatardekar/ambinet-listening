"""Record the user's explicit authorisation of the P05 validation run for THIS frozen configuration. NOT run until the user has authorised it in writing; the validation runner, evaluation and audit sampler refuse to open any
validation record without the file this script writes. usage: record_authorization.py "<exact user message authorising the validation run>"
The file binds the authorisation to the SHA-256 of P05_FREEZE_MANIFEST.json, so any later change to a frozen file invalidates it."""
import datetime
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP4 = HERE.parent
FREEZE = EXP4 / "P05_FREEZE_MANIFEST.json"
AUTH = EXP4 / "P05_VALIDATION_AUTHORIZATION.json"
if len(sys.argv) < 2 or len(sys.argv[1].strip()) < 20:
    print("refusing: pass the user's authorising message verbatim as the first argument"); sys.exit(2)
if AUTH.exists():
    print("refusing: an authorisation file already exists:", AUTH); sys.exit(2)
AUTH.write_text(json.dumps({"authorized": True, "scope": "validation_50", "freeze_manifest_sha256": hashlib.sha256(FREEZE.read_bytes()).hexdigest(), "user_authorisation_message": sys.argv[1],
                            "recorded_local": datetime.datetime.now().astimezone().isoformat(timespec="seconds")}, indent=1), encoding="utf-8")
print("recorded", AUTH)
