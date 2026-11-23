"""Static validation of prompt_versions/P02_v3_p01_schema_no_evidence.txt against the frozen P01 prompt. No model, no inference.
Checks: placeholders; template == P01 template key-for-key and order-for-order (only the evidence placeholders differ); allowed-values block byte-identical to P01;
schema-valid placeholders; no old leaked P01 phrase; invented examples do not overlap with the 50 dev transcripts/gold; no dev encounter ids; encoding."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "p02_v2_2" / "code"))
from v22_common import EXP, authorised_ids, load_gold, load_transcript, categories, entity_matching   # noqa: E402

PKG = Path(__file__).resolve().parents[1]
P01 = (EXP / "prompt_versions" / "P01_schema_guided.txt").read_bytes()
NEW_PATH = EXP / "prompt_versions" / "P02_v3_p01_schema_no_evidence.txt"
NEWB = NEW_PATH.read_bytes()
p01, new = P01.decode("utf-8"), NEWB.decode("utf-8")
res = {"prompt": str(NEW_PATH.relative_to(EXP)), "sha256": hashlib.sha256(NEWB).hexdigest(), "p01_sha256": hashlib.sha256(P01).hexdigest(), "checks": []}


def check(name, ok, detail=""):
    res["checks"].append({"check": name, "ok": bool(ok), "detail": detail})
    print(("PASS " if ok else "FAIL ") + name + (f" | {detail}" if detail else ""))


def template(t):
    body = t.split("Output format (")[1].split("\n", 1)[1].split("\nTranscript (encounter")[0]
    return json.loads(body)


def shape(o):
    if isinstance(o, dict):
        return {k: shape(v) for k, v in o.items()}
    if isinstance(o, list):
        return [shape(o[0])] if o and isinstance(o[0], dict) else ("list" if o == [] else "list_of_scalars")
    return type(o).__name__


def keypaths(o, pre=""):
    out = []
    if isinstance(o, dict):
        for k, v in o.items():
            out.append(pre + k)
            out += keypaths(v, pre + k + ".")
    elif isinstance(o, list) and o and isinstance(o[0], dict):
        out += keypaths(o[0], pre + "[].")
    return out


check("no BOM, no CRLF, valid UTF-8", not NEWB.startswith(b"\xef\xbb\xbf") and b"\r" not in NEWB)
check("{ENCOUNTER_ID} and {TRANSCRIPT} occur exactly once", new.count("{ENCOUNTER_ID}") == 1 and new.count("{TRANSCRIPT}") == 1)
tp, tn = template(p01), template(new)
check("template parses as JSON in both prompts", True)
kp, kn = keypaths(tp), keypaths(tn)
kp = [k for k in kp if not k.startswith("clinical_evidence.")]      # the model no longer writes evidence records: only those sub-keys are intentionally absent
check("same 20 top-level keys in the same order", list(tp) == list(tn) and len(tn) == 20, str(list(tn)))
check("every nested key path and its order is identical to P01 (field names, nesting, order)", kp == kn, f"{len(kp)} paths")
diffs = []
for k in tp:
    if json.dumps(tp[k], sort_keys=False) != json.dumps(tn[k], sort_keys=False):
        diffs.append(k)
check("the only template sections that differ are chief_complaint (evidence placeholder) and clinical_evidence", set(diffs) == {"chief_complaint", "clinical_evidence"}, str(diffs))
check("clinical_evidence is [] in the new template; P01 had one record", tn["clinical_evidence"] == [] and len(tp["clinical_evidence"]) == 1)
check("chief_complaint differs only in the evidence_ids placeholder", {k: v for k, v in tp["chief_complaint"].items() if k != "evidence_ids"} == {k: v for k, v in tn["chief_complaint"].items() if k != "evidence_ids"}, f"{tp['chief_complaint']['evidence_ids']} -> {tn['chief_complaint']['evidence_ids']}")
check("quality_checks and encounter_metadata are byte-identical to P01", tp["quality_checks"] == tn["quality_checks"] and tp["encounter_metadata"] == tn["encounter_metadata"])
sect = lambda t: t.split("Allowed values\n")[1].split("\n\nStructure rules")[0]
check("Allowed-values block is byte-identical to P01 (every enum unchanged)", sect(p01) == sect(new))
check("old leaked phrase 'no fever, no allergies, no previous surgery' is gone", "no fever, no allergies, no previous surgery" not in new.lower())
ids = authorised_ids()
check("prompt contains no dev encounter id", not any(i in new for i in ids))
check("model is told to write no EV_ ids / no evidence records", "clinical_evidence is always []" in new and "never EV_ ids" in new)

# leak check: examples + guide vs the 50 dev transcripts and gold
words = lambda s: re.findall(r"[a-z0-9]+", s.lower())
sh, all_text = set(), ""
for i in ids:
    for s in load_transcript(i)["segments"]:
        w = words(s["text"])
        all_text += " " + " ".join(w)
        sh.update(tuple(w[j:j + 5]) for j in range(len(w) - 4))
gold_blob = ""
for i in ids:
    gold_blob += " " + json.dumps(load_gold(i), ensure_ascii=False).lower()
blob = all_text + " " + gold_blob
ex = new.split("Short examples of behaviour")[1].split("Before you write the JSON")[0]
quoted = re.findall(r'"([^"]{20,})"', ex)
ov = 0
for q in quoted:
    w = words(q)
    ov += sum(tuple(w[j:j + 5]) in sh for j in range(len(w) - 4))
check("no 5-word sequence of any quoted example sentence occurs in a dev transcript", ov == 0, f"overlapping 5-grams={ov}")
terms = ["blurred vision", "hip pain", "hip", "clicking", "zinc", "magnesium", "gout", "grandfather", "swimming", "eye test", "drink more water"]
present = {t: (t in blob) for t in terms}
res["example_content_terms_present_in_dev_data"] = present
check("none of the example-specific clinical terms occurs anywhere in the 50 dev transcripts or gold", not any(present.values()), str({k: v for k, v in present.items() if v}))
res["size"] = {"chars": len(new), "p01_chars": len(p01)}
res["all_checks_pass"] = all(c["ok"] for c in res["checks"])
(PKG / "derived").mkdir(exist_ok=True)
(PKG / "derived" / "PROMPT_V3_VERIFICATION.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
print("ALL PASS" if res["all_checks_pass"] else "SOME CHECKS FAILED", f"({sum(c['ok'] for c in res['checks'])}/{len(res['checks'])})")
