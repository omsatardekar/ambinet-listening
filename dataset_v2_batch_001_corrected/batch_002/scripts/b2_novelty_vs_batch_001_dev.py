"""Novelty of Batch 002 versus Batch 001, measured ONLY against the 100 Batch 001 development records (ids listed in the frozen split_v1.json: 50 prompt_dev + 50 validation).
The 400 locked-test transcripts/labels/blueprints are never opened (forbidden), so this is a SAMPLE comparison; disjointness from the locked records rests on construction
(Batch 001 profiles are not registered in Batch 002; new ids; new seed), not on measurement.
usage: python -B b2_novelty_vs_batch_001_dev.py"""
import collections
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
B2 = Path(__file__).resolve().parents[1]
PARENT = B2.parent
SPLIT = PARENT.parent / "direct_inference_baseline" / "experiments" / "EXP_004_QWEN3_0.6B_PROMPT_ENGINEERING" / "experiments" / "split_v1.json"
split = json.loads(SPLIT.read_text(encoding="utf-8"))
dev = sorted(set(split["prompt_dev_ids"]) | set(split["validation_ids"]))
assert len(dev) == 100 and all(1 <= int(i) <= 500 for i in dev)
N = lambda t: re.sub(r"[^a-z0-9' ]+", " ", t.lower().replace("’", "'")).split()


def sh(words, n=5):
    return {" ".join(words[i:i + n]) for i in range(max(0, len(words) - n + 1))}


def load(root, i):
    return json.loads((root / "output/inputs" / f"encounter_{i}.json").read_text(encoding="utf-8"))


b1 = {i: load(PARENT, i) for i in dev}                     # development records only
b1_bp = {i: json.loads((PARENT / "scenario_blueprints" / f"blueprint_{i}.json").read_text(encoding="utf-8")) for i in dev}
b2 = {p.stem[10:]: json.loads(p.read_text(encoding="utf-8")) for p in sorted((B2 / "output/inputs").glob("*.json"))}
b2_bp = {p.stem[10:]: json.loads(p.read_text(encoding="utf-8")) for p in sorted((B2 / "scenario_blueprints").glob("*.json"))}
text = lambda d: [s["text"] for s in d["segments"]]
sh1 = {i: sh(N(" ".join(text(d)))) for i, d in b1.items()}
sh2 = {i: sh(N(" ".join(text(d)))) for i, d in b2.items()}
inv = collections.defaultdict(set)
for i, S in sh1.items():
    for g in S:
        inv[g].add(i)
maxj, over = 0.0, []
for i, S in sh2.items():
    c = collections.Counter()
    for g in S:
        for j in inv.get(g, ()):
            c[j] += 1
    for j, k in c.items():
        jac = k / (len(S) + len(sh1[j]) - k)
        maxj = max(maxj, jac)
        if jac >= 0.45:
            over.append((i, j, round(jac, 3)))
seg1 = {" ".join(N(t)) for d in b1.values() for t in text(d) if len(N(t)) >= 5}
seg2_all = [" ".join(N(t)) for d in b2.values() for t in text(d) if len(N(t)) >= 5]
shared = sum(1 for t in seg2_all if t in seg1)
# within-batch baseline: share of Batch 002 segments (>=5 words) that also occur in another Batch 002 encounter
cnt = collections.Counter()
for d in b2.values():
    for t in {" ".join(N(x)) for x in text(d) if len(N(x)) >= 5}:
        cnt[t] += 1
within = sum(1 for t in seg2_all if cnt[t] > 1)
prof1 = {b["profile"] for b in b1_bp.values()}
prof2 = {b["profile"] for b in b2_bp.values()}
ass1 = {b["assess"]["primary"].lower() for b in b1_bp.values()}
ass2 = {b["assess"]["primary"].lower() for b in b2_bp.values()}
sym1 = {s["norm"].lower() for b in b1_bp.values() for s in b["syms"]}
sym2 = {s["norm"].lower() for b in b2_bp.values() for s in b["syms"]}
med1 = {m["name"].lower() for b in b1_bp.values() for m in b["meds"]} | {r["name"].lower() for b in b1_bp.values() for r in b["rx"]}
med2 = {m["name"].lower() for b in b2_bp.values() for m in b["meds"]} | {r["name"].lower() for b in b2_bp.values() for r in b["rx"]}
sur1 = {s["norm"] for b in b1_bp.values() for s in b["surg"]}
sur2 = {s["norm"] for b in b2_bp.values() for s in b["surg"]}
surface1 = {s["phrase"] for b in b1_bp.values() for s in b["surg"]} | {f["spoken"] for b in b1_bp.values() for f in b["fam"]}
surface2 = {s["phrase"] for b in b2_bp.values() for s in b["surg"]} | {f["spoken"] for b in b2_bp.values() for f in b["fam"]}
res = {
    "scope": "Batch 002 (500) versus the 100 Batch 001 DEVELOPMENT records only; the 400 locked-test records were not opened",
    "max_5gram_jaccard_batch002_vs_any_dev_record": round(maxj, 3), "pairs_with_jaccard_ge_0.45": len(over),
    "batch002_segments_ge5_words": len(seg2_all), "of_which_verbatim_in_dev100_transcripts": shared, "share_verbatim_in_dev100": round(shared / len(seg2_all), 4),
    "batch002_segments_ge5_words_repeated_in_another_batch002_encounter": within, "share_repeated_within_batch002": round(within / len(seg2_all), 4),
    "profile_keys_in_dev100": len(prof1), "profile_keys_in_batch002": len(prof2), "profile_keys_in_common": len(prof1 & prof2),
    "assessment_primary_strings_in_common_with_dev100": sorted(ass1 & ass2)[:20], "assessment_primary_distinct_batch002": len(ass2),
    "symptom_normalized_names_batch002": len(sym2), "symptom_names_in_common_with_dev100": len(sym1 & sym2),
    "drug_names_batch002": len(med2), "drug_names_in_common_with_dev100": len(med1 & med2), "drug_names_only_in_batch002": len(med2 - med1),
    "surgery_normalized_in_common": len(sur1 & sur2), "surgery_or_family_surface_phrases_in_common_with_dev100": len(surface1 & surface2),
    "note": "drug and symptom vocabulary legitimately overlaps (shared medical vocabulary); conversational scaffolding is produced by the same unmodified dialogue engine",
}
(B2 / "validation" / "novelty_vs_batch_001_dev.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
print(json.dumps(res, indent=1))
