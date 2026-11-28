"""Rebuild staging/output from every draft in drafts/ (compile + unmodified validator). Prints failures only."""
import glob, json, sys, shutil
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import compile_draft as C
H = Path(__file__).resolve().parent
out = H / "staging" / "output"
if out.exists():
    shutil.rmtree(out)
(out / "inputs").mkdir(parents=True); (out / "labels").mkdir(parents=True)
ok = bad = 0
for f in sorted(glob.glob(str(H / "drafts" / "draft_*.json"))):
    d = json.load(open(f))
    inp, lab, errs = C.compile_draft(d)
    R = C.VD.validate_record(inp, lab)
    if errs or R.errors:
        bad += 1; print(d["encounter_id"], "FAIL", (errs + [e["message"] for e in R.errors])[:2]); continue
    e = d["encounter_id"]
    (out / "inputs" / f"encounter_{e}.json").write_text(json.dumps(inp, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "labels" / f"encounter_{e}.json").write_text(json.dumps(lab, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    ok += 1
print("compiled", ok, "failed", bad)
