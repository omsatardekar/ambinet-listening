"""Measure a dataset directory (used for the BEFORE/AFTER comparison).
usage: python audit_metrics.py <dataset_root> [out.json]
The filler lexicon is the phrase inventory of the ORIGINAL generator (the mechanisms the audit criticised)."""
import collections
import glob
import json
import re
import statistics as st
import sys
from pathlib import Path

root = Path(sys.argv[1])
ORIG_POOLS = Path(__file__).resolve().parents[2] / "dataset_v2_batch_001" / "scripts"
sys.path.insert(0, str(ORIG_POOLS))
import dialogue_pools as OP  # noqa: E402  (original pools; read-only)

N = lambda t: re.sub(r"[^a-z0-9' ]+", " ", t.lower().replace("’", "'")).split()
NN = lambda t: " ".join(N(t))
filler_strings = []
for pair in OP.RAPPORT + OP.CONTEXT_CHAT + OP.RECORDS_CHECK + OP.LIFE:
    filler_strings += list(pair)
filler_strings += OP.EXPLAIN + OP.HOLD_A + OP.HOLD_B + OP.EXAM_EXPLAIN + OP.TEACH_Q + OP.EXPLAIN_R
filler_strings += ["Let me just recap so I've got it right"]
filler_norm = [NN(x) for x in filler_strings if len(N(x)) >= 3]
ACKS = {"okay", "alright", "sure", "right", "mm", "mm hm", "i see", "yes", "yeah", "okay i will", "okay doctor", "alright thank you",
        "okay i understand", "understood", "okay i'll do that", "yes i'll do that", "hm", "mm hmm", "go on", "okay i'm following", "alright thanks"}
ins = {Path(f).stem[10:]: json.load(open(f, encoding="utf-8")) for f in sorted(glob.glob(str(root / "output/inputs/*.json")))}
labs = {Path(f).stem[10:]: json.load(open(f, encoding="utf-8")) for f in sorted(glob.glob(str(root / "output/labels/*.json")))}
bps = {Path(f).stem[10:]: json.load(open(f, encoding="utf-8")) for f in sorted(glob.glob(str(root / "scenario_blueprints/*.json")))}
seg_total = word_total = 0
seg_by_enc = collections.defaultdict(set)
filler_seg = filler_words = filler_sec = 0
ack_seg = 0
short_seg = 0
for i, d in ins.items():
    for s in d["segments"]:
        seg_total += 1
        t = NN(s["text"])
        w = len(t.split())
        word_total += w
        if w >= 3:
            seg_by_enc[t].add(i)
        if t in ACKS or (w <= 3 and any(t.startswith(a) for a in ("okay", "alright", "sure", "right"))):
            ack_seg += 1
        if w <= 3:
            short_seg += 1
        hit = [f for f in filler_norm if f in t]
        if hit:
            filler_seg += 1
            filler_sec += s["duration_seconds"]
            filler_words += sum(len(f.split()) for f in hit)
n_enc = len(ins)
common = {t: len(v) for t, v in seg_by_enc.items() if len(v) >= 0.05 * n_enc}
common_cover = 0
for i, d in ins.items():
    for s in d["segments"]:
        if NN(s["text"]) in common:
            common_cover += 1
top = collections.Counter({t: len(v) for t, v in seg_by_enc.items()}).most_common(12)
openings = collections.Counter(NN(d["segments"][0]["text"]) for d in ins.values())
closings = collections.Counter(NN(d["segments"][-1]["text"]) for d in ins.values())
prof = collections.Counter(b["profile"] for b in bps.values())
durs = [d["segments"][-1]["end_seconds"] for d in ins.values()]
segs = [len(d["segments"]) for d in ins.values()]
cat = collections.Counter()
conf_nonnull = 0
confirmed_by = 0
reported_cat = 0
for l in labs.values():
    def walk(o):
        global conf_nonnull, confirmed_by
        if isinstance(o, dict):
            if "confidence" in o and o["confidence"] is not None:
                conf_nonnull += 1
            if "role_confidence" in o and o["role_confidence"] is not None:
                conf_nonnull += 1
            if "confirmed_by" in o:
                confirmed_by += 1
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(l)
    for s in l["symptoms"]:
        cat[s["category"]] += 1
        if s["category"] == "reported":
            reported_cat += 1
acts = collections.Counter()
act_per_enc = []
for l in labs.values():
    act_per_enc.append(len(l["clinical_actions"]))
    for a in l["clinical_actions"]:
        acts[(a["action_type"], a["description"])] += 1
generic = collections.Counter()
for (t, dsc), c in acts.items():
    if dsc.startswith("Seek urgent care"):
        generic["Seek urgent care..."] += c
    else:
        generic[dsc] += c
allergy_repr = collections.Counter()
for l in labs.values():
    nk = any(n["finding"] == "Allergies" for n in l["negative_findings"])
    al = bool(l["allergies"])
    allergy_repr["explicit_none" if nk else "reported_allergy" if al else "not_discussed_or_empty"] += 1
out = {
    "records": n_enc, "profiles_distinct": len(prof), "profile_reuse_max": max(prof.values()), "profile_reuse_mean": round(st.mean(prof.values()), 2),
    "segments_total": seg_total, "words_total": word_total,
    "filler_segments": filler_seg, "filler_segment_share": round(filler_seg / seg_total, 4), "filler_seconds": round(filler_sec, 1),
    "filler_seconds_share_of_total": round(filler_sec / sum(durs), 4), "filler_words_share": round(filler_words / word_total, 4),
    "encounters_with_any_filler": sum(1 for i, d in ins.items() if any(any(f in NN(s["text"]) for f in filler_norm) for s in d["segments"])),
    "ack_segment_share(okay/alright/sure/right…)": round(ack_seg / seg_total, 4), "segments_<=3_words_share": round(short_seg / seg_total, 4),
    "distinct_segment_texts_in_>=5pct_encounters": len(common), "share_of_segments_that_are_those_texts": round(common_cover / seg_total, 4),
    "top_repeated_segments(text,#encounters)": top, "opening_unique": len(openings), "opening_max_share": round(openings.most_common(1)[0][1] / n_enc, 4),
    "closing_unique": len(closings), "closing_max_share": round(closings.most_common(1)[0][1] / n_enc, 4),
    "duration_mean": round(st.mean(durs), 1), "duration_min": min(durs), "duration_max": max(durs),
    "segments_mean": round(st.mean(segs), 1), "segments_min": min(segs), "segments_max": max(segs), "segments_outside_35_70": sum(not 35 <= s <= 70 for s in segs),
    "symptom_category_counts": dict(cat), "symptoms_with_category_reported": reported_cat,
    "confirmed_by_fields": confirmed_by, "non_null_confidence_fields": conf_nonnull,
    "allergy_representation": dict(allergy_repr),
    "actions_per_encounter_mean": round(st.mean(act_per_enc), 2), "encounters_with_zero_actions": sum(1 for a in act_per_enc if a == 0),
    "encounters_with_followup": sum(1 for l in labs.values() if l["follow_up"]),
    "encounters_with_safety_net_action": sum(1 for l in labs.values() if any(a["description"].startswith("Seek urgent care") for a in l["clinical_actions"])),
    "most_common_action_descriptions": generic.most_common(8),
}
if len(sys.argv) > 2:
    Path(sys.argv[2]).write_text(json.dumps(out, indent=1), encoding="utf-8")
print(json.dumps(out, indent=1)[:5000])
