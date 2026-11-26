"""Dump the R_cons v4 configuration (every constant, lexicon and rule switch of p05_retrieval.py that influences a decision) to p05_config.json. The validation runner re-derives this dictionary from the live module at start-up
and aborts if it differs from the frozen JSON, so the configuration that is hashed is the configuration that runs."""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: F401,E402  (puts the project root on sys.path)
import p05_retrieval as R  # noqa: E402
from evidence_builder import HISTORY, LIST_SECTIONS, MAX_SEGMENTS_PER_ITEM  # noqa: E402


def live_config():
    return {"method": "R_cons v4 (C8d)", "steps": list(R.STEPS_V4), "STEM": R.STEM, "TAU": R.TAU, "SPEC_DF_ABS": R.SPEC_DF_ABS, "SPEC_DF_REL": R.SPEC_DF_REL, "BAND": R.BAND, "MAX_TIED": R.MAX_TIED,
            "SHORT_ANSWER_WORDS": R.SHORT_ANSWER_WORDS, "CLIN": sorted(R.CLIN), "PAT_SIDE": sorted(R.PAT_SIDE), "EXPECT_CLASS": dict(sorted(R.EXPECT_CLASS.items())), "NEG": sorted(R.NEG), "NEG_SUFFIX": list(R.NEG_SUFFIX),
            "AFFIRM": sorted(R.AFFIRM), "KIN": sorted(R.KIN), "FIRST_PERSON": sorted(R.FIRST_PERSON), "SMALLTALK": sorted(R.SMALLTALK), "QF": {k: list(v) for k, v in sorted(R.QF.items())},
            "OWN_HISTORY": sorted(R.OWN_HISTORY), "VITAL_SYN": {k: [list(x) for x in v] for k, v in sorted(R.VITAL_SYN.items())}, "NEG_STATUS": sorted(R.NEG_STATUS),
            "builder": {"MAX_SEGMENTS_PER_ITEM": MAX_SEGMENTS_PER_ITEM, "LIST_SECTIONS": list(LIST_SECTIONS), "HISTORY": list(HISTORY), "id_spelling_normalisation": "SEG3/[SEG0003] accepted if the segment exists"}}


def canonical(cfg):
    return json.dumps(cfg, sort_keys=True, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    out = Path(__file__).resolve().parent / "p05_config.json"
    out.write_text(canonical(live_config()), encoding="utf-8", newline="\n")
    print(out, hashlib.sha256(out.read_bytes()).hexdigest())
