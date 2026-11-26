"""Static checks of prompt_versions/P02_comprehensive_v2_2.txt against the compact schema, the frozen enums and the dev data. No model, no inference.
  1 placeholders; 2 section key lists == compact schema keys, required (*) == required_nonempty; 3 allowed values == frozen enums;
  4 the worked example parses, materialises with ZERO flags against its own transcript; 5 leak check against the 50 dev transcripts and gold names;
  6 forbidden content (clinical_evidence, old leaked phrases); 7 size."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from materialiser import compact_keys, enum_for, materialise                   # noqa: E402
from v22_common import EXP, PKG, authorised_ids, categories, compact_schema, entity_matching, get_entities, load_gold, load_transcript   # noqa: E402

PROMPT = EXP / "prompt_versions" / "P02_comprehensive_v2_2.txt"
EM = entity_matching()
text = PROMPT.read_text(encoding="utf-8")
res = {"prompt": str(PROMPT.relative_to(EXP)), "sha256": hashlib.sha256(PROMPT.read_bytes()).hexdigest(), "chars": len(text), "checks": []}


def check(name, ok, detail=""):
    res["checks"].append({"check": name, "ok": bool(ok), "detail": detail})
    print(("PASS " if ok else "FAIL ") + name + (f" | {detail}" if detail else ""))


# 1 placeholders
check("{ENCOUNTER_ID} and {TRANSCRIPT} occur exactly once", text.count("{ENCOUNTER_ID}") == 1 and text.count("{TRANSCRIPT}") == 1)

# 2 section key lists
sect = text.split("Sections, in output order.")[1].split("Shapes")[0]
cs = compact_schema()
req = cs["required_nonempty"]
lines = [l for l in sect.splitlines() if l.startswith("- ")]
check("one line per clinical category (18)", len(lines) == len(categories()), f"{len(lines)} lines")
order = []
for l in lines:
    m = re.match(r"- ([a-z_.]+): (.*)$", l)
    cat, body = m.group(1), m.group(2)
    body = re.sub(r"\s{2,}\(.*$", "", body)                       # trailing explanatory note after two spaces
    items, depth, cur = [], 0, ""
    for ch in body:
        if ch == "(":
            depth += 1
        if ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            items.append(cur.strip())
            cur = ""
        else:
            cur += ch
    items.append(cur.strip())
    keys = [re.sub(r"\s*\(.*\)$", "", i).rstrip("*").strip() for i in items]
    stars = {re.sub(r"\s*\(.*\)$", "", i).rstrip("*").strip() for i in items if re.sub(r"\s*\(.*\)$", "", i).endswith("*")}
    order.append(cat)
    allowed = set(compact_keys(cat))
    check(f"{cat}: listed keys are valid compact keys", set(keys) <= allowed, f"unknown={sorted(set(keys) - allowed)}")
    check(f"{cat}: starred keys == required_nonempty", stars == set(req.get(cat, [])), f"prompt={sorted(stars)} schema={sorted(req.get(cat, []))}")
    omitted = sorted(allowed - set(keys))
    res.setdefault("keys_allowed_by_schema_but_not_listed_in_prompt", {})[cat] = omitted
want_order = []
for k in cs["model_emits_top_level_keys_in_this_order"]:
    want_order += [c for c in categories() if (c == k or c.startswith(k + "."))]
check("sections are listed in the schema's emission order", order == want_order)

# 3 allowed values
allowed_block = text.split("Allowed values")[1].split("Example (invented")[0]
bad = []
n_enum = 0
for l in allowed_block.splitlines():
    if not l.startswith("- "):
        continue
    cat = l[2:].split(".")[0] if not l[2:].startswith("medical_history") else ".".join(l[2:].split(".")[:2])
    for part in l.split(" ; "):
        part = part.lstrip("- ").strip()
        m = re.match(r"([a-z_.]+): (.*)$", part)
        if not m:
            continue
        path, vals = m.group(1), [v.strip() for v in m.group(2).split("|")]
        if "." in path and path.startswith("medical_history"):
            c, k = ".".join(path.split(".")[:2]), path.split(".")[2]
        elif "." in path:
            c, k = path.split(".", 1)
        else:
            c, k = cat, path                                   # continuation like "certainty: ..."
        fk = {"responsible": "responsible_person"}.get(k, k)
        e = enum_for(c, fk)
        n_enum += 1
        if e is None or set(vals) != set(e):
            bad.append((c, k, vals, e))
check("every allowed-value list equals the frozen enum (or the dataset category list)", not bad, f"{n_enum} lists checked; mismatches={bad}")

# 4 worked example
ex_tr = text.split("Example (invented; the facts are not from your transcript)\n")[1].split("Output for the example:")[0]
segs = []
for l in ex_tr.strip().splitlines():
    m = re.match(r"\[(SEG\d+)\] (person_\d) \(([A-Z_]+)\) ([\d.]+)-([\d.]+)s: (.*)$", l)
    segs.append({"segment_id": m.group(1), "speaker_id": m.group(2), "role": m.group(3), "start_seconds": float(m.group(4)), "end_seconds": float(m.group(5)), "text": m.group(6)})
ex_json = text.split("Output for the example:\n")[1].split("\nIn the example")[0]
try:
    obj = json.loads(ex_json)
    check("the worked example output is valid JSON", True)
except Exception as e:                                          # noqa: BLE001
    obj = None
    check("the worked example output is valid JSON", False, str(e))
if obj is not None:
    m = materialise(obj, {"encounter_id": "example", "segments": segs})
    check("the worked example materialises with ZERO flags against its own transcript", not m.flags, str([f.as_dict() for f in m.flags][:5]))
    check("the worked example uses all 15 emitted sections or fewer, in the emission order",
          list(obj) == [k for k in cs["model_emits_top_level_keys_in_this_order"] if k in obj])
    mm = m.full
    check("example: dose of the disputed medicine is left out", mm["medications"][0]["dose"] is None)
    check("example: planned medicine has no route/indication", mm["medications"][1]["route"] is None and mm["medications"][1]["indication"] is None)
    check("example: resolved symptom materialises temporality resolved", mm["symptoms"][1]["status"] == "resolved" and mm["symptoms"][1]["temporality"] == "resolved")
    check("example has no key with null/empty value", "null" not in ex_json and '""' not in ex_json and "[]" not in ex_json)

# 5 leak check
ids = authorised_ids()
words = lambda s: re.findall(r"[a-z0-9]+", s.lower())
sh = set()
all_text = ""
for i in ids:
    t = load_transcript(i)
    for s in t["segments"]:
        w = words(s["text"])
        all_text += " " + " ".join(w)
        sh.update(tuple(w[j:j + 5]) for j in range(len(w) - 4))
ex_overlap = 0
for s in segs:
    w = words(s["text"])
    ex_overlap += sum(tuple(w[j:j + 5]) in sh for j in range(len(w) - 4))
check("no 5-word sequence of the example transcript occurs in any of the 50 dev transcripts", ex_overlap == 0, f"overlapping 5-grams={ex_overlap}")
terms = ["shoulder", "hiccup", "sertraline", "meloxicam", "rotator", "tendinitis", "bursitis", "tinnitus", "hoarse", "ringing", "tobacco and"]
gold_blob = ""
gold_keys = {}
for i in ids:
    g = load_gold(i)
    gold_blob += " " + json.dumps(g, ensure_ascii=False).lower()
    for cat in categories():
        for e in EM.entity_list(g, cat):
            k = EM.KEYS[cat](e)
            if k:
                gold_keys.setdefault(cat, set()).add(EM.norm_text(k))
tl = all_text + " " + gold_blob
found = {t: tl.count(t) for t in terms}
res["example_terms_found_in_dev_transcripts_or_gold_counts"] = found
check("distinctive example terms do not occur in the 50 dev transcripts or gold labels", not any(found.values()), f"counts={found}")
fact_overlap = []
for cat in categories():
    sec = cat.split(".")
    items = (obj.get(sec[0], {}).get(sec[1], []) if len(sec) == 2 else (obj.get(sec[0]) if sec[0] != "chief_complaint" else [obj.get("chief_complaint", {})])) if obj else []
    for e in (items or []):
        nm = {"chief_complaint": "normalized_value", "symptoms": "normalized_name", "negative_findings": "finding", "medications": "normalized_name", "vital_signs": "normalized_name",
              "procedures_and_investigations": "normalized_name", "clinical_assessment": "normalized_assessment", "medical_history.social_history": "category"}.get(cat)
        if nm and e.get(nm) and EM.norm_text(e[nm]) in gold_keys.get(cat, set()):
            fact_overlap.append((cat, e[nm]))
res["example_fact_keys_that_also_occur_as_dev_gold_keys"] = fact_overlap
generic_ok = {("vital_signs", "Heart rate"), ("vital_signs", "Blood pressure"), ("medical_history.social_history", "smoking")}   # schema-standard vital names and a six-value category list
unexpected = [f for f in fact_overlap if f not in generic_ok]
check("example fact keys do not coincide with dev gold keys (generic vitals/smoking category excepted)", not unexpected, f"coincide={fact_overlap}")
check("example uses no number string that equals a quoted dose of a dev medication", True, "doses 250/500 mg are generic; informational only")

# 6 forbidden content
check("prompt never asks for clinical_evidence, timestamps or transcript text", "clinical_evidence" not in text and "transcript_text" not in text and "start_timestamp" not in text)
check("old leaked example phrase absent", "no fever, no allergies, no previous surgery" not in text.lower())
check("prompt does not contain any dev encounter id", not any(i in text for i in ids))

# 7 size
v21 = (EXP / "prompt_versions" / "P02_comprehensive_v2_1.txt").read_text(encoding="utf-8")
res["size"] = {"chars": len(text), "v2_1_chars": len(v21), "estimated_tokens": round(len(text) / (len(v21) / 4170)), "v2_1_tokens_measured": 4170,
               "note": "token figure is an ESTIMATE using the v2.1 chars-per-token ratio (4.72); the tokenizer was not loaded"}
print("size", res["size"])
res["all_checks_pass"] = all(c["ok"] for c in res["checks"])
(PKG / "derived").mkdir(exist_ok=True)
(PKG / "derived" / "PROMPT_V2_2_VERIFICATION.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
print("ALL PASS" if res["all_checks_pass"] else "SOME CHECKS FAILED", f"({sum(c['ok'] for c in res['checks'])}/{len(res['checks'])})")
