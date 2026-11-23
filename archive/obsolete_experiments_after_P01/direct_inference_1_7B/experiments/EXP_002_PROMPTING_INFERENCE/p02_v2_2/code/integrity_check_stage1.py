"""Stage 1 integrity check (read-only): nothing frozen or original was modified.
 1. the 50 authorised dev inputs and labels against the dataset's own CHECKSUMS.sha256 (only those 100 files are hashed; no other label is opened)
 2. every hash recorded in FREEZE_P02_v2_1_pilot8.json (prompt v2.1, runner, client, evaluator, ids, conversion record, pilot ids)
 3. frozen schema, entity matcher, schema validator, evidence evaluator against git (tracked files: `git status` must show them unmodified)
 4. no file outside p02_v2_2/, the v2.2 prompt, and the report was created or changed during Stage 1 (modification times since --since)"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from v22_common import DATA, EXP, PKG, ROOT, TRACK, authorised_ids, read_json     # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--since-epoch", type=float, required=True, help="start of Stage 1 (file modification times later than this are listed)")
A = ap.parse_args()
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
out = {"checked_at": time.ctime()}

# 1 dataset
ids = set(authorised_ids())
exp = {}
for line in (DATA / "output" / "CHECKSUMS.sha256").read_text(encoding="utf-8").splitlines():
    parts = line.split()
    if len(parts) >= 2:
        h, rel = parts[0], parts[-1].lstrip("*")
        if any(f"encounter_{i}.json" in rel for i in ids) and ("/inputs/" in rel.replace("\\", "/") or "/labels/" in rel.replace("\\", "/")):
            exp[rel] = h
bad = [r for r, h in exp.items() if sha(DATA / r) != h]
out["dataset_dev_files"] = {"checked": len(exp), "mismatches": bad, "ok": len(exp) == 100 and not bad}

# 2 freeze manifest
fz = read_json(TRACK / "manifests" / "FREEZE_P02_v2_1_pilot8.json")


res2 = []
for section, base in (("files", TRACK), ("evaluator_files_0_6B", ROOT / "direct_inference_baseline")):
    for rel, h in fz[section].items():
        p = base / rel
        res2.append({"path": f"{section}:{rel}", "recorded": h[:12], "now": sha(p)[:12] if p.exists() else None, "match": p.exists() and sha(p) == h})
cfg = EXP / "configs" / "P02_v2_1_pilot8_CONFIG.json"
res2.append({"path": "config", "recorded": fz["config_sha256"][:12], "now": sha(cfg)[:12], "match": sha(cfg) == fz["config_sha256"]})
out["freeze_manifest_hashes"] = {"entries": res2, "all_match": all(r["match"] for r in res2), "n": len(res2),
                                 "note": "files and evaluator_files_0_6B sections plus the config hash recorded in FREEZE_P02_v2_1_pilot8.json (includes entity_matching.py, schema_validator.py, evidence_evaluator.py, the baseline inference runner and evaluator)"}

# 3 git
g = subprocess.run(["git", "status", "--short", "--untracked-files=no"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
out["git_tracked_modifications"] = g.splitlines()
out["git_tracked_clean"] = (g == "")

# 4 files changed since Stage 1 began
skip = ("env_openvino", "ov_cache", ".git", "hf_cache", "__pycache__", "Qwen3-1.7B-ov-fp16", "models")
changed = []
for base in (ROOT / "direct_inference_1_7B", ROOT / "direct_inference_baseline", ROOT / "dataset_v2_batch_001_corrected", ROOT / "dataset_v2_batch_001"):
    for p in base.rglob("*"):
        if any(s in p.parts for s in skip) or not p.is_file():
            continue
        if p.stat().st_mtime > A.since_epoch:
            changed.append(str(p.relative_to(ROOT)).replace("\\", "/"))
allowed_prefix = ("direct_inference_1_7B/experiments/EXP_002_PROMPTING_INFERENCE/p02_v2_2/",)
allowed_files = {"direct_inference_1_7B/experiments/EXP_002_PROMPTING_INFERENCE/prompt_versions/P02_comprehensive_v2_2.txt",
                 "direct_inference_1_7B/experiments/EXP_002_PROMPTING_INFERENCE/reports/P02_v2_2_STAGE1_VALIDATION.md"}
unexpected = [c for c in changed if not c.startswith(allowed_prefix) and c not in allowed_files]
out["files_changed_since_stage1_start"] = {"total": len(changed), "outside_allowed_new_files": unexpected, "ok": not unexpected}
out["all_ok"] = out["dataset_dev_files"]["ok"] and out["freeze_manifest_hashes"]["all_match"] and out["git_tracked_clean"] and out["files_changed_since_stage1_start"]["ok"]
(PKG / "derived").mkdir(exist_ok=True)
(PKG / "derived" / "INTEGRITY_CHECK.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
print(json.dumps({k: (v if not isinstance(v, dict) else {a: b for a, b in v.items() if a != "entries"}) for k, v in out.items()}, indent=1)[:2500])
