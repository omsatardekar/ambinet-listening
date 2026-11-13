"""EXP_004 development-only dataset guard (PROPOSED safeguard for future runs; not yet used by any runner).
Problem (documented in reports/08_locked_test_access_audit.md): the existing runner's frozen-dataset check re-hashes ALL 500 input transcripts (400 locked-test transcripts) at the start of every run.
The existing module cannot be edited, so a future development runner installs this guard at run time (same pattern as common.use_run): it replaces `settings.verify_frozen_dataset` and `settings.MANIFEST_CSV`
so that only the explicitly requested development records are hashed and only a development-only manifest is read.
  * dev_safeguards/dev_checksums.sha256            hashes of the 100 development inputs and labels (derived from the dataset's CHECKSUMS.sha256 text; no transcript or label was opened to derive it)
  * dev_safeguards/locked_test_checksums.SEALED.sha256  hashes of the 400 locked-test inputs and labels, kept apart and NEVER loaded by development code
  * dev_safeguards/dev_manifest.csv                 manifest rows of the 100 development ids only
Requested ids must be a subset of the 50 prompt_dev ids unless allow_validation=True is passed explicitly. The frozen dataset is never modified."""
from __future__ import annotations

import csv
import json
from pathlib import Path

from common import EXP4, S, SPLIT, sha256_file

DEV_DIR = EXP4 / "dev_safeguards"
DEV_CHECKSUMS, SEALED, DEV_MANIFEST, MANIFEST_HASH = (DEV_DIR / n for n in ("dev_checksums.sha256", "locked_test_checksums.SEALED.sha256", "dev_manifest.csv", "dataset_manifest_csv_checksum.txt"))


def _ids_from_split(name):
    return json.loads((S.SPLIT_DIR / f"{name}_ids.json").read_text(encoding="utf-8"))   # id lists only; no record is opened


def build_files():
    """One-time derivation. Reads: the text of CHECKSUMS.sha256, the id lists of the split, and the metadata CSV (needed to write dev_manifest.csv). Opens NO transcript and NO label."""
    DEV_DIR.mkdir(exist_ok=True)
    dev, test = set(_ids_from_split("development")), set(_ids_from_split("test"))
    dev_lines, test_lines, other = [], [], []
    for line in S.CHECKSUMS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        h, rel = line.split("  ", 1)
        stem = Path(rel).stem.replace("encounter_", "")
        if ("/inputs/" in rel or "/labels/" in rel) and stem in dev:
            dev_lines.append(line)
        elif ("/inputs/" in rel or "/labels/" in rel) and stem in test:
            test_lines.append(line)
        else:
            other.append(line)
    DEV_CHECKSUMS.write_text("\n".join(dev_lines) + "\n", encoding="utf-8", newline="\n")
    SEALED.write_text("# LOCKED TEST HASHES - SEALED. Development code must never read this file.\n" + "\n".join(test_lines) + "\n", encoding="utf-8", newline="\n")
    MANIFEST_HASH.write_text("\n".join(other) + "\n", encoding="utf-8", newline="\n")
    with open(S.MANIFEST_CSV, newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f)]
        names = list(rows[0].keys())
    with open(DEV_MANIFEST, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=names)
        w.writeheader()
        w.writerows([r for r in rows if r["encounter_id"] in dev])
    return {"dev_lines": len(dev_lines), "sealed_test_lines": len(test_lines), "other_lines": len(other)}


def verify_ids(ids, include_labels=False, allow_validation=False, expected_override=None):
    allowed = set(SPLIT["prompt_dev_ids"]) | (set(SPLIT["validation_ids"]) if allow_validation else set())
    assert set(ids) <= allowed, "only approved prompt-development ids may be hashed (validation needs allow_validation=True)"
    expected = {}
    for line in DEV_CHECKSUMS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        h, rel = line.split("  ", 1)
        stem = Path(rel).stem.replace("encounter_", "")
        if stem in ids and ("/inputs/" in rel or include_labels):
            expected[rel.strip()] = h
    if expected_override:
        expected.update(expected_override)
    bad = [rel for rel, h in expected.items() if not (S.DATASET_DIR / rel).exists() or sha256_file(S.DATASET_DIR / rel) != h]
    return {"files_checked": len(expected), "mismatches": bad, "verified": not bad, "dataset_manifest_sha256": sha256_file(S.FINAL_MANIFEST), "scope": "development-only", "ids": sorted(ids)}


def install(ids, include_labels=False, allow_validation=False):
    """Run-time redirect (no file of the existing module is changed)."""
    S.verify_frozen_dataset = lambda inputs_only=False: verify_ids(ids, include_labels=include_labels and not inputs_only, allow_validation=allow_validation)
    S.MANIFEST_CSV = DEV_MANIFEST


def locked_test_accesses(opened_paths):
    """Paths in an audit list that point to a locked-test transcript or label (inputs/labels of ids outside the development split) or to the sealed hash file."""
    dev = set(_ids_from_split("development"))
    out = []
    for p in opened_paths:
        q = str(p).replace("\\", "/")
        if q.endswith("locked_test_checksums.SEALED.sha256"):
            out.append(p)
        elif ("/output/inputs/" in q or "/output/labels/" in q) and Path(q).stem.replace("encounter_", "") not in dev:
            out.append(p)
    return out


# ---------------------------------------------------------------------------------------------------------------- strict enforcement (added for P05; the original functions above are unchanged)
import builtins
import hashlib
import re

AUTH_FILE = EXP4 / "P05_VALIDATION_AUTHORIZATION.json"
FREEZE_MANIFEST = EXP4 / "P05_FREEZE_MANIFEST.json"


def validation_authorized():
    """True only when the user's explicit authorisation was recorded for THIS frozen configuration: the file must exist, say authorized=true for scope validation_50, and carry the SHA-256 of the current freeze manifest."""
    if not AUTH_FILE.exists() or not FREEZE_MANIFEST.exists():
        return False
    try:
        a = json.loads(AUTH_FILE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return False
    return bool(a.get("authorized") is True and a.get("scope") == "validation_50" and a.get("freeze_manifest_sha256") == hashlib.sha256(FREEZE_MANIFEST.read_bytes()).hexdigest())


class StrictAccessSpy:
    """File-access spy that STOPS the run (raises PermissionError at the moment of the attempt) when code tries to open a locked-test transcript/label, the sealed hash file, or - unless allowed - a validation transcript/label.
    Records every path opened. Patches builtins.open, Path.open, Path.read_text and Path.read_bytes (the ways the existing code and the hash functions read files)."""

    def __init__(self, allow_validation=False):
        self.opened, self.allow_validation = [], allow_validation
        self.test = set(_ids_from_split("test"))
        self.validation = set(SPLIT["validation_ids"])

    def forbidden(self, p):
        q = str(p).replace("\\", "/")
        if q.endswith("locked_test_checksums.SEALED.sha256"):
            return "sealed locked-test hash file"
        if "/output/inputs/" in q or "/output/labels/" in q:
            stem = Path(q).stem.replace("encounter_", "")
            if stem in self.test:
                return "locked-test record"
            if stem in self.validation and not self.allow_validation:
                return "validation record without authorisation"
        return None

    def __enter__(self):
        spy = self
        self._o, self._po, self._t, self._b = builtins.open, Path.open, Path.read_text, Path.read_bytes

        def check(p):
            spy.opened.append(str(p))
            why = spy.forbidden(p)
            if why:
                raise PermissionError(f"STOP: {why}: {p}")

        def o(f, *a, **k):
            check(f)
            return spy._o(f, *a, **k)

        def po(p, *a, **k):
            check(p)
            return spy._po(p, *a, **k)

        def t(p, *a, **k):
            check(p)
            return spy._t(p, *a, **k)

        def b(p, *a, **k):
            check(p)
            return spy._b(p, *a, **k)
        builtins.open, Path.open, Path.read_text, Path.read_bytes = o, po, t, b
        return self

    def __exit__(self, *exc):
        builtins.open, Path.open, Path.read_text, Path.read_bytes = self._o, self._po, self._t, self._b

    def label_or_blueprint_accesses(self):
        return [p for p in self.opened if re.search(r"output[\\/]labels|scenario_blueprints|blueprint", p, re.I)]

    def report(self):
        norm = [p.replace("\\", "/") for p in self.opened]
        return {"files_opened_count": len(self.opened), "locked_test_files_opened": G_locked(self.opened), "sealed_hash_file_opened": any(p.endswith("locked_test_checksums.SEALED.sha256") for p in norm),
                "label_files_opened": len(self.label_or_blueprint_accesses()), "input_transcripts_opened": sorted({Path(p).stem.replace("encounter_", "") for p in norm if "/output/inputs/" in p}),
                "validation_records_opened": sorted({Path(p).stem.replace("encounter_", "") for p in norm if ("/output/inputs/" in p or "/output/labels/" in p) and Path(p).stem.replace("encounter_", "") in self.validation})}


def G_locked(opened):
    return locked_test_accesses(opened)
