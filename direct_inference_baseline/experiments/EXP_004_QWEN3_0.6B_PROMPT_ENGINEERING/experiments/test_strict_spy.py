"""Negative tests: the strict spy must STOP (PermissionError) on a locked-test transcript, a locked-test label, the sealed hash file and an unauthorised validation record, and must allow approved prompt_dev records. Zero inference."""
import json, sys
from common import EXP4, S, SPLIT, write_json
import dev_guard as G
test_id = json.loads((S.SPLIT_DIR / "test_ids.json").read_text(encoding="utf-8"))[0]
val_id = SPLIT["validation_ids"][0]; dev_id = SPLIT["prompt_dev_ids"][0]
res = {}
def attempt(name, fn, allow_validation=False):
    try:
        with G.StrictAccessSpy(allow_validation=allow_validation) as spy:
            fn()
        res[name] = "ALLOWED"
    except PermissionError as e:
        res[name] = "STOPPED: " + str(e)[:90]
    except Exception as e:  # noqa: BLE001
        res[name] = f"OTHER ERROR {type(e).__name__}"
attempt("locked_test_transcript_read_text", lambda: (S.INPUT_DIR / f"encounter_{test_id}.json").read_text(encoding="utf-8"))
attempt("locked_test_transcript_read_bytes", lambda: (S.INPUT_DIR / f"encounter_{test_id}.json").read_bytes())
attempt("locked_test_label_open", lambda: open(S.LABEL_DIR / f"encounter_{test_id}.json", encoding="utf-8").read())
attempt("sealed_hash_file", lambda: G.SEALED.read_text(encoding="utf-8"))
attempt("validation_transcript_without_authorisation", lambda: (S.INPUT_DIR / f"encounter_{val_id}.json").read_text(encoding="utf-8"))
res["validation_transcript_with_authorisation_flag"] = "ALLOWED" if G.StrictAccessSpy(allow_validation=True).forbidden(S.INPUT_DIR / f"encounter_{val_id}.json") is None else "BLOCKED"   # permission logic only: the file is NOT opened
attempt("approved_prompt_dev_transcript", lambda: (S.INPUT_DIR / f"encounter_{dev_id}.json").read_text(encoding="utf-8"))
attempt("approved_prompt_dev_label_for_evaluation", lambda: (S.LABEL_DIR / f"encounter_{dev_id}.json").read_text(encoding="utf-8"))
with G.StrictAccessSpy() as _spy:
    (S.LABEL_DIR / f"encounter_{dev_id}.json").read_text(encoding="utf-8")
res["label_read_is_detected_by_audit"] = "DETECTED" if len(_spy.label_or_blueprint_accesses()) >= 1 and _spy.report()["label_files_opened"] >= 1 else "NOT DETECTED"
ok = (all(res[k].startswith("STOPPED") for k in ("locked_test_transcript_read_text", "locked_test_transcript_read_bytes", "locked_test_label_open", "sealed_hash_file", "validation_transcript_without_authorisation"))
      and res["validation_transcript_with_authorisation_flag"] == "ALLOWED" and res["approved_prompt_dev_transcript"] == "ALLOWED" and res["approved_prompt_dev_label_for_evaluation"] == "ALLOWED" and res["label_read_is_detected_by_audit"] == "DETECTED")
write_json(EXP4 / "evaluation" / "strict_spy_negative_tests.json", {"results": res, "all_pass": ok, "note": "no validation or locked-test file was opened by this test: forbidden paths raise before the open, and the authorised-validation case checks the permission rule without opening the file"})
print(json.dumps(res, indent=1), ok)
