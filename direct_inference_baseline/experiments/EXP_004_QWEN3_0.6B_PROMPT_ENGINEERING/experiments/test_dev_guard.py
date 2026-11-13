"""Zero-inference test of dev_guard.py: (1) derive the separate hash files, (2) under a file-access spy the guarded 'frozen dataset check' opens only the requested development transcripts and no locked-test file,
(3) tampering is detected, (4) the existing unguarded check is shown for contrast (measured, not run on a model)."""
import json
import sys

from common import EXP4, S, FileAccessSpy, SPLIT, write_json
import dev_guard as G

res = {"build": G.build_files()}
ids = ["00035", "00037", "00040", "00215", "00248"]
orig = S.verify_frozen_dataset
with FileAccessSpy() as spy0:
    orig(inputs_only=True)                                  # the existing behaviour (contrast)
res["existing_check_contrast"] = {"files_opened": len(spy0.opened), "locked_test_files_opened": len(G.locked_test_accesses(spy0.opened))}
G.install(ids)
with FileAccessSpy() as spy:
    r = S.verify_frozen_dataset(inputs_only=True)
opened_inputs = sorted(p for p in spy.opened if "/output/inputs/" in p.replace("\\", "/"))
res["guarded_check"] = {"verified": r["verified"], "files_checked": r["files_checked"], "transcripts_opened": [p.replace("\\", "/").split("/")[-1] for p in opened_inputs], "label_files_opened": len(spy.label_or_blueprint_accesses()),
                        "locked_test_files_opened": G.locked_test_accesses(spy.opened), "sealed_hash_file_opened": any("SEALED" in p for p in spy.opened), "files_opened_total": len(spy.opened)}
bad = G.verify_ids(ids, expected_override={"output/inputs/encounter_00035.json": "0" * 64})
res["tamper_detected"] = {"verified": bad["verified"], "mismatches": bad["mismatches"]}
try:
    G.verify_ids(["00001"])
    res["non_approved_id_rejected"] = False
except AssertionError:
    res["non_approved_id_rejected"] = True
try:
    G.verify_ids(SPLIT["validation_ids"][:1])
    res["validation_id_rejected_without_flag"] = False
except AssertionError:
    res["validation_id_rejected_without_flag"] = True
ok = (res["guarded_check"]["verified"] and len(opened_inputs) == 5 and not res["guarded_check"]["locked_test_files_opened"] and res["guarded_check"]["label_files_opened"] == 0 and not res["guarded_check"]["sealed_hash_file_opened"]
      and not res["tamper_detected"]["verified"] and res["non_approved_id_rejected"] and res["validation_id_rejected_without_flag"])
res["all_tests_pass"] = ok
write_json(EXP4 / "evaluation" / "dev_guard_test.json", res)
print(json.dumps(res, indent=1))
sys.exit(0 if ok else 1)
