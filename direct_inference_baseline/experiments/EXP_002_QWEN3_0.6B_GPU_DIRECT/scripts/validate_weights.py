"""Phase 3 step 1: validate converted FP16 weights (NaN/Inf) and BF16->FP16 overflow/underflow risk in the SOURCE weights.
Read-only. No generation, no dataset."""
import json, sys
from pathlib import Path
import numpy as np
import openvino as ov
import torch
from safetensors import safe_open

E = Path(__file__).resolve().parents[1]
M = E / "models" / "Qwen3-0.6B-ov-fp16"
S = Path(sys.argv[1]) / "model.safetensors"
FP16_MAX, FP16_MIN_SUB, FP16_MIN_NORM = 65504.0, 2.0 ** -24, 2.0 ** -14

# --- converted model
core = ov.Core()
m = core.read_model(str(M / "openvino_model.xml"))
conv = {"tensors_fp16": 0, "tensors_fp32": 0, "elements_fp16": 0, "nonfinite_fp16": 0, "nonfinite_fp32": 0, "max_abs_fp16": 0.0, "max_abs_fp32": 0.0,
        "tensors_with_nonfinite": [], "unreadable": 0}
for op in m.get_ops():
    if op.get_type_name() != "Constant":
        continue
    t = str(op.get_output_element_type(0))
    if "float16" not in t and "float32" not in t:
        continue
    try:
        a = np.asarray(op.get_data()).astype(np.float32, copy=False)
    except Exception:
        conv["unreadable"] += 1
        continue
    k = "fp16" if "float16" in t else "fp32"
    bad = int((~np.isfinite(a)).sum())
    conv[f"tensors_{k}"] += 1
    conv[f"nonfinite_{k}"] += bad
    if bad:
        conv["tensors_with_nonfinite"].append(op.get_friendly_name())
    if k == "fp16":
        conv["elements_fp16"] += a.size
    fin = a[np.isfinite(a)]
    if fin.size:
        conv[f"max_abs_{k}"] = max(conv[f"max_abs_{k}"], float(np.abs(fin).max()))

# --- source bf16 -> fp16 risk
src = {"tensors": 0, "elements": 0, "nonfinite": 0, "max_abs": 0.0, "overflow_gt_fp16_max": 0, "nonzero_flushed_to_zero": 0,
       "nonzero_in_fp16_subnormal_range": 0, "tensors_overflowing": [], "dtypes": {}}
with safe_open(str(S), framework="pt") as f:
    for name in f.keys():
        x = f.get_tensor(name)
        src["dtypes"][str(x.dtype)] = src["dtypes"].get(str(x.dtype), 0) + 1
        a = x.to(torch.float32).numpy()
        src["tensors"] += 1
        src["elements"] += a.size
        nf = ~np.isfinite(a)
        src["nonfinite"] += int(nf.sum())
        fin = np.where(nf, 0.0, a)
        ab = np.abs(fin)
        src["max_abs"] = max(src["max_abs"], float(ab.max()) if ab.size else 0.0)
        ov_n = int((ab > FP16_MAX).sum())
        src["overflow_gt_fp16_max"] += ov_n
        if ov_n:
            src["tensors_overflowing"].append(name)
        nz = ab > 0
        src["nonzero_flushed_to_zero"] += int((nz & (ab < FP16_MIN_SUB / 2)).sum())
        src["nonzero_in_fp16_subnormal_range"] += int((nz & (ab < FP16_MIN_NORM)).sum())

verdict = {
    "converted_weights_finite": conv["nonfinite_fp16"] == 0 and conv["nonfinite_fp32"] == 0,
    "source_weights_finite": src["nonfinite"] == 0,
    "bf16_to_fp16_overflow_risk": src["overflow_gt_fp16_max"] > 0,
}
out = {"converted_model": conv, "source_bf16": src, "fp16_limits": {"max": FP16_MAX, "min_subnormal": FP16_MIN_SUB, "min_normal": FP16_MIN_NORM},
       "verdict": verdict,
       "caveat": "Weights only. FP16 ACTIVATION overflow at run time (e.g. large residual-stream values) is not covered by this check; it is assessed by comparing generated tokens against a float32 reference."}
(E / "results").mkdir(exist_ok=True)
(E / "results" / "weight_validation.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
print(json.dumps(out, indent=2))
