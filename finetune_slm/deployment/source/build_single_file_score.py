"""Builds the ONE file to upload as the scoring script for the fine-tuned model (the Studio wizard takes a single file).

    python finetune_slm/deployment/source/build_single_file_score.py --name step156 --label "..." --weights-sha <sha256 of the converted openvino_model.bin>     (repository root; standard library only)

Without --weights-sha a PENDING marker is written: fine for the offline self-test, but the file then refuses to start on Azure (init() compares the real hash).
1. assembles finetune_slm/deployment/source/code_bundle/: score.py, json_guard.py, the compact codec (+ schema_keys.json), the short prompt (hash verified), pinned_hashes.json,
   and the existing validator / evidence resolver / schemas (copied, not edited);
2. embeds the bundle as a base64 ZIP in finetune_slm/deployment/source/score_single_file.py, which unpacks it at start-up and hands init()/run() to score.py.
"""
import argparse
import base64
import hashlib
import io
import json
import shutil
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]                                   # repository root (finetune_slm/deployment/source -> ../../..)
OUT = HERE / "code_bundle"                                    # re-pointed to code_bundle_<name> in main(): each model has its own bundle folder, nothing is shared or overwritten
SHORT_PROMPT = ROOT / "finetune_slm/data/round1_synthetic" / "prompt" / "short_prompt.txt"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def ignore(_dir, names):
    return [n for n in names if n == "__pycache__" or n.endswith(".pyc")]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights-sha", default="PENDING_" + "0" * 56)
    ap.add_argument("--name", required=True, help="step156 or step400: the output file is score_single_file_<name>.py")
    ap.add_argument("--window-chars", type=int, default=7000, help="transcript characters per window; a consultation that fits is processed in one pass")
    ap.add_argument("--window-overlap", type=int, default=4, help="segments shared between neighbouring windows")
    ap.add_argument("--label", required=True, help="model description written into the response metadata")
    a = ap.parse_args()
    global OUT
    OUT = HERE / ("code_bundle" if a.name == "step156" else f"code_bundle_{a.name}")
    if OUT.exists():
        shutil.rmtree(OUT, onexc=lambda f, p, e: (__import__('os').chmod(p, 0o700), f(p)))
    OUT.mkdir()
    for f in ("score.py",):
        shutil.copy(HERE / f, OUT / f)
    shutil.copy(ROOT / "finetune_slm" / "scripts" / "shared" / "json_guard.py", OUT / "json_guard.py")
    shutil.copy(ROOT / "finetune_slm" / "scripts" / "shared" / "chunking.py", OUT / "chunking.py")
    for f in ("compact_codec.py", "schema_keys.json"):
        shutil.copy(ROOT / "finetune_slm/data/round1_synthetic" / "codec" / f, OUT / f)
    shutil.copy(SHORT_PROMPT, OUT / "short_prompt.txt")
    for rel in ("direct_inference_baseline/__init__.py", "direct_inference_baseline/config", "direct_inference_baseline/inference", "direct_inference_baseline/evaluation",
                "clinical_extraction_schema.json", "dataset_v2_batch_001_corrected/schema/final_label_schema.json"):          # path inside the bundle (the validator expects this layout)
        src, dst = ROOT / rel, OUT / rel
        if rel.startswith("dataset_v2_batch_001_corrected"):
            src = ROOT / "finetune_slm" / "archive" / rel                              # the folder now lives in the archive
        elif rel.startswith("direct_inference_baseline"):
            src = ROOT / "finetune_slm" / rel                                          # the package now lives in finetune_slm/
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dst, ignore=ignore) if src.is_dir() else shutil.copy(src, dst)
    (OUT / "clinical_extraction").mkdir()
    for f in ("__init__.py", "config.py", "compact.py", "evidence.py"):
        shutil.copy(ROOT / "clinical_extraction" / f, OUT / "clinical_extraction" / f)
    pinned = {"model_label": a.label, "window_chars": a.window_chars, "window_overlap": a.window_overlap, "short_prompt_sha256": sha(OUT / "short_prompt.txt"), "openvino_model_bin_sha256": a.weights_sha,
              "codec_sha256": sha(OUT / "compact_codec.py"), "schema_keys_sha256": sha(OUT / "schema_keys.json"), "json_guard_sha256": sha(OUT / "json_guard.py"), "chunking_sha256": sha(OUT / "chunking.py")}
    (OUT / "pinned_hashes.json").write_text(json.dumps(pinned, indent=1), encoding="utf-8")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(OUT.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(OUT).as_posix())
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    tag = hashlib.sha256(buf.getvalue()).hexdigest()[:12]
    template = '''"""Self-contained Azure ML scoring script for the fine-tuned Qwen3-0.6B (generated by build_single_file_score.py). Embeds the code bundle; delegates to the real score.py. Do not edit."""
import base64, importlib.util, io, os, sys, tempfile, zipfile

_B64 = "%(b64)s"
_DIR = os.path.join(tempfile.gettempdir(), "ft_bundle_%(tag)s")
if not os.path.exists(os.path.join(_DIR, "score.py")):
    zipfile.ZipFile(io.BytesIO(base64.b64decode(_B64))).extractall(_DIR)
sys.path.insert(0, _DIR)
_spec = importlib.util.spec_from_file_location("ft_score", os.path.join(_DIR, "score.py"))
_mod = importlib.util.module_from_spec(_spec)
sys.modules["ft_score"] = _mod
_spec.loader.exec_module(_mod)
init = _mod.init
run = _mod.run
'''
    target = HERE.parent / {"step156": "step156_round2", "step400": "step400_round1"}[a.name] / f"score_single_file_{a.name}.py"
    target.write_text(template % {"b64": b64, "tag": tag}, encoding="utf-8")
    print(f"written {target}  ({target.stat().st_size / 1024:.0f} KB, bundle id {tag}); weights hash: {a.weights_sha[:16]}...; prompt hash {pinned['short_prompt_sha256'][:16]}...")
    if a.weights_sha.startswith("PENDING"):
        print("WARNING: weights hash is PENDING - rebuild with --weights-sha after the OpenVINO conversion before uploading")
    return 0


if __name__ == "__main__":
    sys.exit(main())
