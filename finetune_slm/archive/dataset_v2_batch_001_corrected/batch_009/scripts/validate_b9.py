import sys, json, glob
from pathlib import Path
sys.dont_write_bytecode = True
H = Path(__file__).resolve().parent; P = H.parents[1]
sys.path[:0] = [str(P / "scripts"), str(P / "validation"), str(H)]
import blueprint, b2_profiles_1, b2_profiles_2, b2_profiles_3, b9_profiles_1, b2_pools
b2_pools.apply()
import validate_dataset as VD
bad = 0
for f in sorted(glob.glob(str(H.parent / "output/inputs/*.json"))):
    inp = json.load(open(f, encoding="utf-8")); lab = json.load(open(f.replace("inputs", "labels"), encoding="utf-8"))
    R = VD.validate_record(inp, lab)
    if R.errors: bad += 1; print(Path(f).name, R.errors[0])
print("failing", bad)
