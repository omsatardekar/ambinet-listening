"""EXP_004 P04 pre-work (READ-ONLY, no inference): evidence structure and design probes. Development ids only (100 development / 50 prompt_dev); validation and test never read.
 A. transcript structure (segment ids, speakers, roles, times) in the dev inputs
 B. conventions of the gold evidence records (dev labels): one record = one segment? numbering, role mapping, timestamps, supports format, citations per item
 C. ceiling: the existing evaluator's grounding applied to the GOLD labels themselves
 D. baselines for 'which segment supports this item' on P02 outputs: first segment, random, lexical retrieval, scored (i) with the evaluator's lexical test and
    (ii) against the gold-cited segments for strictly matched entities (a semantic proxy that retrieval cannot cheat by construction)."""
import json
import random
import re
import statistics as st
import sys
import types
from collections import Counter, defaultdict
from pathlib import Path

try:
    import dotenv  # noqa
except ImportError:
    sys.modules["dotenv"] = types.SimpleNamespace(load_dotenv=lambda *a, **k: False)
sys.dont_write_bytecode = True
EXP4 = Path(__file__).resolve().parents[1]
ROOT = EXP4.parents[2]
sys.path.insert(0, str(ROOT))
from direct_inference_baseline.config import settings as S  # noqa: E402
from direct_inference_baseline.evaluation import evaluation_runner as ER  # noqa: E402
from direct_inference_baseline.evaluation import evidence_evaluator as EE  # noqa: E402
from direct_inference_baseline.evaluation.dataset_split import load_split  # noqa: E402
from direct_inference_baseline.evaluation.entity_matching import CATEGORIES, KEYS, content_tokens, entity_list, match_category, norm_text  # noqa: E402

split = json.loads((EXP4 / "experiments" / "split_v1.json").read_text(encoding="utf-8"))
DEV = load_split("development")
assert not set(DEV) & set(load_split("test"))
PD = split["prompt_dev_ids"]
mm = lambda s: f"{int(s)//60:02d}:{int(s)%60:02d}"
load_in = lambda e: json.loads((S.INPUT_DIR / f"encounter_{e}.json").read_text(encoding="utf-8"))
out = {}

# ---------------- A. transcript structure
A = Counter(); roles = Counter(); spk_roles = defaultdict(set); nseg = []
for e in DEV:
    t = load_in(e); segs = t["segments"]; nseg.append(len(segs))
    A["encounters"] += 1
    ids = [s["segment_id"] for s in segs]
    A["segment_id_format_ok"] += all(re.fullmatch(r"SEG\d{4}", i) for i in ids)
    A["segment_ids_sequential_from_1"] += ids == [f"SEG{i+1:04d}" for i in range(len(ids))]
    A["speaker_id_format_ok"] += all(re.fullmatch(r"person_\d+", s["speaker_id"]) for s in segs)
    A["times_monotonic"] += all(segs[i]["start_seconds"] <= segs[i + 1]["start_seconds"] for i in range(len(segs) - 1))
    A["start_le_end"] += all(s["start_seconds"] <= s["end_seconds"] for s in segs)
    A["empty_text_segments"] += sum(not s["text"].strip() for s in segs)
    A["segments_total"] += len(segs)
    sr = defaultdict(set)
    for s in segs:
        roles[s["role"]] += 1; sr[s["speaker_id"]].add(s["role"])
    A["speaker_has_single_role"] += all(len(v) == 1 for v in sr.values())
    # duplicate texts (retrieval/ambiguity risk)
    c = Counter(norm_text(s["text"]) for s in segs)
    A["segments_with_duplicate_text_in_encounter"] += sum(v for v in c.values() if v > 1)
out["A_transcript_structure"] = {**dict(A), "segments_per_encounter_mean": round(st.mean(nseg), 1), "min": min(nseg), "max": max(nseg), "role_vocabulary": dict(roles),
                                 "rendered_line_format": "[SEG0003] person_1 (PATIENT) 15.77-26.37s: text  (inference_runner.render_transcript)"}

# ---------------- B. gold evidence conventions (dev labels)
B = Counter(); role_map = defaultdict(Counter); loc_pat = Counter(); ids_per_item = []; seg_per_item = []; role_of_cited = Counter()
LOC = re.compile(r"^(chief_complaint|[a-z_]+(\.[a-z_]+)?\[\d+\])$")


def seg_index(ev, segs):
    """indices of segments equal to the evidence record (text, speaker, floor start)"""
    t = norm_text(ev.get("transcript_text"))
    return [i for i, s in enumerate(segs) if t == norm_text(s["text"]) and s["speaker_id"] == ev.get("speaker_id") and mm(s["start_seconds"]) == ev.get("start_timestamp")]


def gold_entities(gold):
    for c in CATEGORIES:
        for i, e in enumerate(entity_list(gold, c)):
            yield c, i, e


gold_cites = {}  # (eid, cat, idx) -> set of segment indices (unambiguous only)
for e in DEV:
    g = ER.load_gold(e); segs = load_in(e)["segments"]
    evl = g.get("clinical_evidence") or []
    B["encounters"] += 1; B["evidence_records"] += len(evl)
    idx = {}
    for r in evl:
        hit = seg_index(r, segs)
        B["ev_matches_exactly_one_segment"] += len(hit) == 1
        B["ev_matches_zero_segments"] += len(hit) == 0
        B["ev_matches_several_segments"] += len(hit) > 1
        if hit:
            idx[r["evidence_id"]] = hit[0]
            s = segs[hit[0]]
            B["ev_end_floor_ok"] += r.get("end_timestamp") == mm(s["end_seconds"])
            role_map[s["role"]][r.get("speaker_role")] += 1
            B["ev_speaker_id_ok"] += r.get("speaker_id") == s["speaker_id"]
    order = [idx[r["evidence_id"]] for r in evl if r["evidence_id"] in idx]
    B["ev_listed_in_segment_order"] += order == sorted(order)
    B["ev_ids_consecutive_EV_001"] += [r["evidence_id"] for r in evl] == [f"EV_{i+1:03d}" for i in range(len(evl))]
    B["ev_ids_unique_segments"] += len(set(order)) == len(order)
    ev_by_id = {r["evidence_id"]: r for r in evl}
    locs = {f"{c}[{i}]" if c != "chief_complaint" else c: (c, i, ent) for c, i, ent in gold_entities(g)}
    # gold uses medical_history.sub[i] for history; normalise the location string family
    for r in evl:
        for sp in r.get("supports") or []:
            loc_pat["chief_complaint" if sp == "chief_complaint" else re.sub(r"\d+", "N", sp)] += 1
            B["supports_refs"] += 1
            B["supports_ref_format_ok"] += bool(LOC.match(sp))
    n_items = 0
    for c, i, ent in gold_entities(g):
        n_items += 1
        ids = ent.get("evidence_ids") or []
        B["gold_items"] += 1; B["gold_items_with_evidence_ids"] += bool(ids)
        ids_per_item.append(len(ids))
        segset = {idx[x] for x in ids if x in idx}
        gold_cites[(e, c, i)] = segset
        seg_per_item.append(len(segset))
        for x in segset:
            role_of_cited[segs[x]["role"]] += 1
        for x in ids:  # reciprocity gold: evidence record lists this entity in supports
            loc = "chief_complaint" if c == "chief_complaint" else (f"{c}[{i}]")
            B["gold_ids_reciprocal"] += loc in (ev_by_id.get(x, {}).get("supports") or [])
            B["gold_ids_total"] += 1
B_out = dict(B)
B_out.update({"role_map_transcript_to_evidence_speaker_role": {k: dict(v) for k, v in role_map.items()}, "supports_location_patterns": dict(loc_pat.most_common(30)),
              "evidence_ids_per_item_mean": round(st.mean(ids_per_item), 2), "evidence_ids_per_item_p90": sorted(ids_per_item)[int(0.9 * len(ids_per_item))], "evidence_ids_per_item_max": max(ids_per_item),
              "segments_cited_per_item_mean": round(st.mean(seg_per_item), 2), "role_of_cited_segments": dict(role_of_cited),
              "segments_cited_per_item_distribution": dict(sorted(Counter(seg_per_item).items()))})
out["B_gold_evidence_conventions_dev100"] = B_out

# ---------------- C. evaluator ceiling on gold labels (prompt_dev 50)
tot = Counter(); bycat = defaultdict(Counter)
for e in PD:
    r = EE.evaluate_grounding(ER.load_gold(e), load_in(e))
    for k in ("grounded_strict", "grounded_lenient", "partially_supported", "unsupported", "total"):
        tot[k] += r[k]
    for c, v in r["by_category"].items():
        for k, x in v.items():
            bycat[c][k] += x
out["C_evaluator_grounding_on_gold_prompt_dev50"] = {**dict(tot), "strict_rate": round(tot["grounded_strict"] / tot["total"], 3), "strict_plus_lenient_rate": round((tot["grounded_strict"] + tot["grounded_lenient"]) / tot["total"], 3),
                                                      "by_category_strict_plus_lenient": {c: round((v["grounded_strict"] + v["grounded_lenient"]) / v["total"], 2) for c, v in bycat.items() if v["total"]}}

# ---------------- D. retrieval baselines on P02 outputs (prompt_dev 50)
P02 = EXP4 / "outputs" / "P02_comprehensive_extraction_dev50" / "parsed_predictions" / "P02_comprehensive_extraction_dev50"
rng = random.Random(20260413)
D = Counter()


def stems(key):
    return [t[:5] for t in content_tokens(key.split("|")[-1] if "|" in key else key)]


def best_seg(key, segs):
    ts = stems(key)
    if not ts:
        return 0
    best, bi = -1.0, 0
    for i, s in enumerate(segs):
        hay = " ".join(w[:5] for w in norm_text(s["text"]).split())
        sc = sum(1 for t in ts if re.search(rf"(?<![a-z0-9]){re.escape(t)}", hay)) / len(ts)
        if sc > best + 1e-9:
            best, bi = sc, i
    return bi


for e in PD:
    segs = load_in(e)["segments"]; gold = ER.load_gold(e)
    pred = json.loads((P02 / f"encounter_{e}.json").read_text(encoding="utf-8"))
    gpos = {}
    for c in CATEGORIES:
        m = match_category(entity_list(gold, c), entity_list(pred, c), c)
        glist = entity_list(gold, c)
        for ge, pe in m["pairs"]:
            gi = next((i for i, x in enumerate(glist) if x is ge), None)
            gpos[id(pe)] = (c, gi)
        for pe in entity_list(pred, c):
            key = KEYS[c](pe)
            if not key:
                continue
            nk = norm_text(key) if "|" not in str(key) else key
            D["pred_items"] += 1
            for name, pick in (("first_segment", 0), ("random_segment", rng.randrange(len(segs))), ("lexical_best_segment", best_seg(nk, segs))):
                txt = segs[pick]["text"]
                D[f"{name}_strict_grounded"] += EE.lexical_support(nk, txt, True)
                D[f"{name}_lenient_or_better"] += EE.lexical_support(nk, txt, False)
                if id(pe) in gpos:
                    cc, gi = gpos[id(pe)]
                    G = gold_cites.get((e, cc, gi), set())
                    if G:
                        D[f"{name}_hit_gold_segments"] += pick in G
            if id(pe) in gpos:
                cc, gi = gpos[id(pe)]
                if gold_cites.get((e, cc, gi)):
                    D["tp_items_with_gold_citation"] += 1
                    D["tp_gold_cited_segments_total"] += len(gold_cites[(e, cc, gi)])
                    D["random_expected_hit_gold_segments"] += len(gold_cites[(e, cc, gi)]) / len(segs)
D = dict(D)
n = D["pred_items"]; t = D.get("tp_items_with_gold_citation", 0)
out["D_retrieval_baselines_P02_outputs_prompt_dev50"] = {**D, **{f"{k}_rate": round(D[f"{k}_strict_grounded"] / n, 3) for k in ("first_segment", "random_segment", "lexical_best_segment")},
                                                           **{f"{k}_strict_plus_lenient_rate": round(D[f"{k}_lenient_or_better"] / n, 3) for k in ("first_segment", "random_segment", "lexical_best_segment")},
                                                           **({f"{k}_gold_segment_hit_rate_on_tp_items": round(D.get(f"{k}_hit_gold_segments", 0) / t, 3) for k in ("first_segment", "random_segment", "lexical_best_segment")} if t else {}),
                                                           "random_expected_hit_rate_on_tp_items": round(D.get("random_expected_hit_gold_segments", 0) / t, 3) if t else None}
(EXP4 / "analysis" / "evidence_design_probe.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
print(json.dumps(out, indent=1, ensure_ascii=False))
