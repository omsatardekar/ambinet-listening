"""Run the UNMODIFIED Batch 001 audit tools against Batch 002 without editing them.
The Batch 001 scripts fix their dataset root with `ROOT = Path(__file__).resolve().parents[1]`, their record range with range(1, 501), and read the schema/generator from ROOT.
This wrapper reads each original script's source text, substitutes only those path/range constants in memory, and executes it; the original files on disk are never touched.
Tools run: final_schema_audit.py (schema/enum/key-set/allergy-representation/action-status audit), validator_selftest.py (negative controls), lock_dataset.py (output/CHECKSUMS.sha256),
validate_batch.py (record + dataset checks).   usage: python -B run_existing_tools_on_batch_002.py [audit] [selftest] [lock] [validate]   (default: all)"""
import io
import json
import sys
import contextlib
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
B2 = HERE.parent
PARENT = B2.parent
sys.path.insert(0, str(PARENT / "scripts"))
sys.path.insert(0, str(PARENT / "validation"))
sys.path.insert(0, str(HERE))
import blueprint  # noqa: E402,F401
import b2_profiles_1, b2_profiles_2, b2_profiles_3, b2_pools  # noqa: E402,F401
b2_pools.apply()
import validate_dataset  # noqa: E402,F401  (cached so the patched scripts reuse the already-registered module)

ORIG = PARENT / "scripts"
ROOT_LINE = "ROOT = Path(__file__).resolve().parents[1]"
SUBS = {
    "final_schema_audit.py": [(ROOT_LINE, f'ROOT = Path(r"{B2}")'), ('(ROOT / "schema" / "final_label_schema.json")', f'(Path(r"{PARENT}") / "schema" / "final_label_schema.json")'),
                              ('(ROOT / "scripts" / "dialogue.py")', f'(Path(r"{PARENT}") / "scripts" / "dialogue.py")')],
    "validator_selftest.py": [(ROOT_LINE, f'ROOT = Path(r"{B2}")'), ("range(1, 501)", "range(20001, 20501)")],
    "lock_dataset.py": [(ROOT_LINE, f'ROOT = Path(r"{B2}")')],
    "validate_batch.py": [(ROOT_LINE, f'ROOT = Path(r"{PARENT}")'), ('ap.add_argument("--root", default=str(ROOT))', f'ap.add_argument("--root", default=r"{B2}")'),
                          ("default=1)", "default=20001)"), ("default=500)", "default=20500)")],
}


def run(name):
    src = (ORIG / name).read_text(encoding="utf-8")
    for a, b in SUBS[name]:
        assert a in src, (name, a)
        src = src.replace(a, b)
    ns = {"__name__": "__main__", "__file__": str(B2 / "scripts" / name)}
    buf = io.StringIO()
    code = 0
    old_argv = sys.argv
    sys.argv = [name, "--dataset-checks"] if name == "validate_batch.py" else [name]
    with contextlib.redirect_stdout(buf):
        try:
            exec(compile(src, str(ORIG / name), "exec"), ns)
        except SystemExit as e:
            code = e.code or 0
    sys.argv = old_argv
    out = buf.getvalue()
    (B2 / "validation" / f"{name.replace('.py', '')}_batch_002_output.txt").write_text(out, encoding="utf-8")
    print(f"=== {name} (exit {code})")
    print("\n".join(out.splitlines()[-14:]))
    return code


if __name__ == "__main__":
    which = [a for a in sys.argv[1:]] or ["audit", "selftest", "lock", "validate"]
    table = {"audit": "final_schema_audit.py", "selftest": "validator_selftest.py", "lock": "lock_dataset.py", "validate": "validate_batch.py"}
    rc = {w: run(table[w]) for w in which}
    print(json.dumps(rc))
