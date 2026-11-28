"""Batch 002 whole-set checks: per-record validator, lexical evidence grounding totals, and duplicate / near-duplicate detection
against all Batch 001 transcripts and within Batch 002.   Read-only.
usage: python dataset_checks.py --new-root DIR [--ref-root DIR] [--start 501 --end 1000] --out FILE
"""
import argparse
import collections
import hashlib
import itertools
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "validation"))
import validate_dataset as VD  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--new-root", default=str(ROOT))
ap.add_argument("--ref-root", default=str(ROOT))
ap.add_argument("--start", type=int, default=501)
ap.add_argument("--end", type=int, default=1000)
ap.add_argument("--ref-start", type=int, default=1)
ap.add_argument("--ref-end", type=int, default=500)
ap.add_argument("--out", required=True)
ap.add_argument("--near", type=float, default=0.45, help="5-gram Jaccard at or above this = near duplicate (project threshold)")
A = ap.parse_args()


def load(root, a, b):
    I, L = {}, {}
    for i in range(a, b + 1):
        e = f"{i:05d}"
        pi, pl = Path(root) / "output/inputs" / f"encounter_{e}.json", Path(root) / "output/labels" / f"encounter_{e}.json"
        if pi.exists() and pl.exists():
            I[e], L[e] = json.loads(pi.read_text(encoding="utf-8")), json.loads(pl.read_text(encoding="utf-8"))
    return I, L


NI, NL = load(A.new_root, A.start, A.end)
RI, RL = load(A.ref_root, A.ref_start, A.ref_end)
full = lambda inp: " ".join(s["text"] for s in inp["segments"])
rep = {"new_records": len(NI), "reference_records": len(RI)}

# --- per record validation + lexical grounding
fail, lex, errs = {}, collections.Counter(), collections.Counter()
warn = collections.Counter()
for e in sorted(NI):
    R = VD.validate_record(NI[e], NL[e])
    lex.update(R.lex)
    for w in R.warnings:
        warn[w["check"]] += 1
    if R.errors:
        fail[e] = [x["message"][:150] for x in R.errors[:5]]
        errs.update(x["check"] for x in R.errors)
cats = sorted({c for c, _ in lex})
rep["validator"] = {"pass": len(NI) - len(fail), "fail": len(fail), "failures": fail, "errors_by_check": dict(errs), "warnings_by_check": dict(warn)}
rep["evidence_grounding"] = {"facts_checked": sum(lex[(c, "checked")] for c in cats), "facts_grounded": sum(lex[(c, "passed")] for c in cats),
                             "by_category": {c: {"checked": lex[(c, "checked")], "passed": lex[(c, "passed")]} for c in cats}}
rep["pairing"] = {"ids_match": set(NI) == set(NL), "ids_unique": len(set(NI)) == len(NI),
                  "ids_contiguous": sorted(NI) == [f"{i:05d}" for i in range(A.start, A.end + 1)] if len(NI) == A.end - A.start + 1 else False}

# --- duplicates
allI = {("n", e): NI[e] for e in NI}
allI.update({("r", e): RI[e] for e in RI})
sh = {k: VD.shingles(full(v)) for k, v in allI.items()}
inv = collections.defaultdict(list)
for k, S in sh.items():
    for g in S:
        inv[g].append(k)
pair = collections.Counter()
for g, lst in inv.items():
    if 1 < len(lst) <= 60:
        for a, b in itertools.combinations(sorted(lst), 2):
            if a[0] == "n" or b[0] == "n":
                pair[(a, b)] += 1
sims = []
for (a, b), c in pair.items():
    j = c / (len(sh[a]) + len(sh[b]) - c)
    sims.append((j, a, b))
sims.sort(reverse=True)
near = [{"a": f"{a[0]}:{a[1]}", "b": f"{b[0]}:{b[1]}", "jaccard_5gram": round(j, 3)} for j, a, b in sims if j >= A.near]
digest = collections.Counter(hashlib.md5(full(v).encode()).hexdigest() for v in allI.values())
exact = sum(c - 1 for c in digest.values() if c > 1)
nn = [s for s in sims if s[1][0] == "n" and s[2][0] == "n"]
nr = [s for s in sims if (s[1][0] == "n") != (s[2][0] == "n")]
norm = lambda t: re.sub(r"\s+", " ", t.lower().replace("’", "'")).strip()
seg_owner = collections.defaultdict(set)
for k, v in allI.items():
    for s in v["segments"]:
        if len(s["text"].split()) >= 8:
            seg_owner[norm(s["text"])].add(k)
shared_nn = sum(1 for t, o in seg_owner.items() if len([x for x in o if x[0] == "n"]) > 1)
shared_nr = sum(1 for t, o in seg_owner.items() if any(x[0] == "n" for x in o) and any(x[0] == "r" for x in o))
new_long = sum(1 for t, o in seg_owner.items() if any(x[0] == "n" for x in o))
new_seg_total = sum(1 for v in NI.values() for s in v["segments"] if len(s["text"].split()) >= 8)
new_seg_repeated = sum(1 for v in NI.values() for s in v["segments"] if len(s["text"].split()) >= 8 and len(seg_owner[norm(s["text"])]) > 1)
first = collections.Counter(norm(NI[e]["segments"][0]["text"]) for e in NI)
last = collections.Counter(norm(NI[e]["segments"][-1]["text"]) for e in NI)
op3 = collections.Counter(" ".join(norm(NI[e]["segments"][0]["text"]).split()[:3]) for e in NI)
fp = collections.Counter()
for e in NL:
    L = NL[e]
    fp[(tuple(sorted(s["normalized_name"] for s in L["symptoms"])), tuple(sorted(m["normalized_name"] or m["name"] for m in L["medications"])),
        tuple(sorted(a["normalized_assessment"] for a in L["clinical_assessment"])))] += 1
cc = collections.Counter(NL[e]["chief_complaint"]["normalized_value"].lower() for e in NL)
rcc = collections.Counter(RL[e]["chief_complaint"]["normalized_value"].lower() for e in RL)
combo = collections.Counter(tuple(sorted(s["normalized_name"] for s in NL[e]["symptoms"])) for e in NL if NL[e]["symptoms"])
ref_combo = {tuple(sorted(s["normalized_name"] for s in RL[e]["symptoms"])) for e in RL if RL[e]["symptoms"]}
rep["duplicates"] = {
    "method": "5-gram word Jaccard over full transcript text (same as Batch 001 validator, near threshold %.2f), md5 of full text, shared long segments (>= 8 words), label fingerprints" % A.near,
    "exact_duplicate_transcripts": exact,
    "near_duplicate_pairs": near,
    "max_jaccard_new_vs_new": round(nn[0][0], 3) if nn else 0.0, "max_jaccard_new_vs_batch001": round(nr[0][0], 3) if nr else 0.0,
    "top5_new_vs_new": [{"a": a[1], "b": b[1], "jaccard": round(j, 3)} for j, a, b in nn[:5]],
    "top5_new_vs_batch001": [{"new": (a if a[0] == "n" else b)[1], "batch001": (b if a[0] == "n" else a)[1], "jaccard": round(j, 3)} for j, a, b in nr[:5]],
    "long_segments_new_total": new_seg_total, "long_segments_new_text_also_in_other_encounter": new_seg_repeated,
    "long_segment_texts_shared_new_new": shared_nn, "long_segment_texts_shared_new_batch001": shared_nr,
    "identical_first_turn_groups": {t: c for t, c in first.items() if c > 1}, "identical_last_turn_groups": {t: c for t, c in last.items() if c > 1},
    "opening_three_words_top": op3.most_common(8),
    "label_fingerprint_duplicates(symptoms+meds+assessment)": sum(c - 1 for k, c in fp.items() if c > 1 and any(k)),
    "chief_complaint_normalized_repeats_new": {k: c for k, c in cc.items() if c > 1}, "chief_complaint_repeated_from_batch001": sum(1 for k in cc if k in rcc),
    "symptom_combo_repeats_new": sum(c - 1 for k, c in combo.items() if c > 1), "symptom_combo_also_in_batch001": sum(1 for k in combo if k in ref_combo),
}
rep["duplicates"]["duplicate_count"] = exact + len(near)
Path(A.out).write_text(json.dumps(rep, indent=1, ensure_ascii=False), encoding="utf-8")
print(json.dumps({"new": len(NI), "validator_pass": rep["validator"]["pass"], "fail": rep["validator"]["fail"],
                  "grounded": f"{rep['evidence_grounding']['facts_grounded']}/{rep['evidence_grounding']['facts_checked']}", "exact_dup": exact, "near_dup": len(near),
                  "max_j_new_new": rep["duplicates"]["max_jaccard_new_vs_new"], "max_j_new_b001": rep["duplicates"]["max_jaccard_new_vs_batch001"],
                  "ids_ok": rep["pairing"]}, indent=1))
