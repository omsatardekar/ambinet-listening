"""Verifies the downloaded Qwen3-1.7B snapshot against the Hugging Face repository metadata for the pinned revision: file list, sizes and (for LFS files) SHA-256 from the Hub's
own LFS pointers, plus the snapshot directory name == expected revision.  Only public model metadata is requested.  Writes manifests/DOWNLOAD_VERIFICATION_Qwen3-1.7B.json.
usage: python -B -s verify_download.py   (exit 0 = verified)"""
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common_1_7b as C  # noqa: E402

snap_root = C.HF_CACHE / "models--Qwen--Qwen3-1.7B" / "snapshots"
snaps = [p.name for p in snap_root.iterdir()] if snap_root.exists() else []
api = json.load(urllib.request.urlopen(f"https://huggingface.co/api/models/{C.MODEL_ID}/revision/{C.REVISION}?blobs=true", timeout=60))
files = {s["rfilename"]: s for s in api["siblings"]}
snap = snap_root / C.REVISION
res, ok = {}, True
want = ["config.json", "generation_config.json", "merges.txt", "model-00001-of-00002.safetensors", "model-00002-of-00002.safetensors", "model.safetensors.index.json", "tokenizer.json", "tokenizer_config.json", "vocab.json"]
for name in want:
    p = snap / name
    exp = files.get(name, {})
    entry = {"exists": p.exists(), "expected_size": exp.get("size")}
    if p.exists():
        h = hashlib.sha256()
        with open(p, "rb") as fh:
            for c in iter(lambda: fh.read(1 << 22), b""):
                h.update(c)
        entry.update(size=p.stat().st_size, sha256=h.hexdigest(), size_ok=p.stat().st_size == exp.get("size"))
        lfs = (exp.get("lfs") or {}).get("sha256")
        entry["expected_lfs_sha256"] = lfs
        entry["sha256_ok"] = (h.hexdigest() == lfs) if lfs else None
        entry["pass"] = entry["size_ok"] and entry["sha256_ok"] is not False
    else:
        entry["pass"] = False
    ok &= entry["pass"]
    res[name] = entry
out = {"model": C.MODEL_ID, "expected_revision": C.REVISION, "hub_reported_revision_sha": api.get("sha"), "snapshot_dirs_present": snaps, "revision_matches": api.get("sha") == C.REVISION and snaps == [C.REVISION],
       "files": res, "verified": bool(ok and api.get("sha") == C.REVISION and snaps == [C.REVISION])}
C.write_json(C.TRACK / "manifests" / "DOWNLOAD_VERIFICATION_Qwen3-1.7B.json", out)
print(json.dumps({k: v for k, v in out.items() if k != "files"}, indent=1))
print({n: e["pass"] for n, e in res.items()})
sys.exit(0 if out["verified"] else 1)
