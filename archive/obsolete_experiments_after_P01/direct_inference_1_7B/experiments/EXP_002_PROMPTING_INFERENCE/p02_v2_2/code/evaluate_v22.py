"""Independent P02 v2.2 evaluator (new file; the frozen evaluator and the baseline package are not touched).

Entity matching reuses the frozen STRICT matcher function file (entity_matching.py, loaded read-only as a module) so that v2.2 numbers are comparable with
P00/P01/P02 v2.1. Everything else (reference validity, reference overlap, discrepancy handling, lexical unsupported-claim indicators, token statistics)
is new and lives here.

Inputs per run: the runner's parsed/ and failed/ folders (a record is `parsed` exactly when the runner parsed it) and optionally raw/ for token counts.
  --format compact : parsed files hold the v2.2 compact JSON; they are materialised (materialiser.py) before scoring.
  --format full    : parsed files hold full-schema records (P00, P01, P02 v2.1); scored as they are.
Failed or missing outputs score as ZERO predictions (headline = all records). A parsed-only paired view is reported separately.
Labels and transcripts can be read only for the 50 authorised dev ids.  quality_checks is NOT assessed (owner decision pending) and is reported as such."""
from __future__ import annotations

import argparse
import json
import re
import statistics as st
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from convert_gold import build_ev_map, to_compact                         # noqa: E402
from evidence_resolver import DEFAULT_MAX_REFS, EvidenceResolver          # noqa: E402
from materialiser import materialise                                       # noqa: E402
from v22_common import (PKG, authorised_ids, categories, compact_json_len, entity_matching, est_tokens, get_entities, load_gold,   # noqa: E402
                        load_transcript, mmss)

EM = entity_matching()
TOKEN_CAP = 4096
NOT_ASSESSED = {"quality_checks": "not assessed: how quality_checks is produced is an unresolved owner decision (see STAGE1 report)"}

# ---------------------------------------------------------------------------------------------------------------------------------
# helpers
NUMWORDS = {w: str(i) for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty".split())}
NUMWORDS.update({"couple": "2", "thirty": "30", "forty": "40", "fifty": "50", "sixty": "60", "seventy": "70", "eighty": "80", "ninety": "90", "hundred": "100", "half": "0.5", "once": "1", "twice": "2"})
NEG_CUE = re.compile(r"\b(no|not|never|none|nothing|nobody|without|denies|deny|haven't|havent|hasn't|hasnt|didn't|didnt|don't|dont|doesn't|doesnt|isn't|isnt|wasn't|wasnt|aren't|arent|n't|nope|neither|nor)\b|n't", re.I)
ORAL_CUE = re.compile(r"\b(mouth|oral|orally|swallow|swallowed|tablet|tablets)\b", re.I)
SMOKE_CUE = re.compile(r"smok|cigar|tobacco|vap|nicotine", re.I)
ALCOHOL_CUE = re.compile(r"alcohol|drink|beer|wine|spirit|pint|booze|teetotal", re.I)
PRIMARY_TEXT = {"chief_complaint": "value", "symptoms": "name", "negative_findings": "finding", "medical_history.past_medical_history": "condition",
                "medical_history.surgical_history": "procedure", "medical_history.family_history": "condition", "medical_history.social_history": "description",
                "medications": "name", "allergies": "substance", "vital_signs": "name", "physical_examination": "finding", "review_of_systems": "system",
                "clinical_conditions": "name", "clinical_assessment": "assessment", "procedures_and_investigations": "name", "clinical_actions": "description"}


def _numbers_in(text: str) -> set:
    t = str(text).lower()
    nums = set(re.findall(r"\d+(?:\.\d+)?", t))
    if re.search(r"\b(a|an|one)\s+(day|week|month|year|hour|minute|fortnight)s?\b", t):
        nums.add("1")                                   # "a week" = 1 week
    for w in re.findall(r"[a-z]+", t):
        if w in NUMWORDS:
            nums.add(NUMWORDS[w])
    return nums


def _pref_overlap(tokens_a, tokens_b) -> bool:
    for a in tokens_a:
        for b in tokens_b:
            if a == b or (len(a) >= 5 and len(b) >= 5 and a[:5] == b[:5]):
                return True
    return False


def _ratio(a, b):
    return round(a / b, 4) if b else None


def _prf(tp, fp, fn):
    return EM.prf(tp, fp, fn)


# ---------------------------------------------------------------------------------------------------------------------------------
# loading
def load_run(parsed_dir, failed_dir, raw_dir, ids):
    out = {}
    for eid in ids:
        p = Path(parsed_dir) / f"encounter_{eid}.json" if parsed_dir else None
        f = Path(failed_dir) / f"encounter_{eid}.json" if failed_dir else None
        r = Path(raw_dir) / f"encounter_{eid}.json" if raw_dir else None
        rec = {"id": eid, "status": "missing", "obj": None, "failure": None, "gen": {}}
        if p and p.exists():
            rec["status"], rec["obj"] = "parsed", json.loads(p.read_text(encoding="utf-8-sig"))
        elif f and f.exists():
            fj = json.loads(f.read_text(encoding="utf-8-sig"))
            rec["status"], rec["failure"] = "failed", fj.get("failure_type")
            rec["gen"]["finish_reason"] = fj.get("finish_reason")
        if r and r.exists():
            g = json.loads(r.read_text(encoding="utf-8-sig")).get("generation", {})
            rec["gen"].update({k: g.get(k) for k in ("finish_reason", "prompt_tokens", "completion_tokens", "latency_seconds")})
        out[eid] = rec
    return out


# ---------------------------------------------------------------------------------------------------------------------------------
# per-record scoring
def segments_of_pred_fact(ent, fmt, ctx):
    """(valid segment ids, number of invalid/unresolvable refs) of one predicted fact."""
    ids = ent.get("evidence_ids")
    ids = ids if isinstance(ids, list) else []
    segs, bad = [], 0
    for x in ids:
        if fmt == "compact":
            sid = ctx["ev_to_seg"].get(x)
        else:
            if isinstance(x, str) and x in ctx["res"].by_id:
                sid = x
            else:
                sid = ctx["own_ev_to_seg"].get(x)
        if sid:
            segs.append(sid)
        else:
            bad += 1
    return segs, bad


def _own_ev_map(pred, res):
    """Model evidence id -> transcript segment id, for FULL-format outputs. Accepted only when unambiguous:
    (1) `supports` holds exactly one valid segment id (the v2.1 model's habit), else
    (2) exactly one transcript segment equals the record's text, speaker, MM:SS start and end (the gold convention), else
    (3) exactly one transcript segment equals its text and speaker.  Anything else stays unresolved (never guessed)."""
    m = {}
    segs = [res.by_id[s] for s in res.order]
    for e in (pred.get("clinical_evidence") or []):
        if not isinstance(e, dict) or not isinstance(e.get("evidence_id"), str):
            continue
        sups = [s for s in (e.get("supports") or []) if isinstance(s, str) and s in res.by_id] if isinstance(e.get("supports"), list) else []
        if len(sups) == 1:
            m[e["evidence_id"]] = sups[0]
            continue
        c = [s["segment_id"] for s in segs if s["text"] == e.get("transcript_text") and s["speaker_id"] == e.get("speaker_id")
             and mmss(s["start_seconds"]) == e.get("start_timestamp") and mmss(s["end_seconds"]) == e.get("end_timestamp")]
        if len(c) != 1:
            c = [s["segment_id"] for s in segs if s["text"] == e.get("transcript_text") and s["speaker_id"] == e.get("speaker_id")]
        if len(c) == 1:
            m[e["evidence_id"]] = c[0]
    return m


def audit_full_evidence_block(pred, tr):
    """For FULL-format outputs: what the model-written clinical_evidence block and the fact references look like against the real transcript."""
    res = EvidenceResolver(tr)
    ev = [e for e in (pred.get("clinical_evidence") or []) if isinstance(e, dict)]
    a = Counter()
    seg_cited = []
    own = _own_ev_map(pred, res)
    for e in ev:
        sid = own.get(e.get("evidence_id"))
        s = res.by_id.get(sid)
        if s is None:
            a["evidence_records_with_unknown_segment"] += 1
            continue
        seg_cited.append(sid)
        a["text_mismatch"] += e.get("transcript_text") != s["text"]
        a["speaker_mismatch"] += e.get("speaker_id") != s["speaker_id"]
        a["start_timestamp_mismatch"] += e.get("start_timestamp") != mmss(s["start_seconds"])
        a["end_timestamp_mismatch"] += e.get("end_timestamp") != mmss(s["end_seconds"])
    own_ids = {e.get("evidence_id") for e in ev}
    refs = []
    for cat in categories():
        for ent in get_entities(pred, cat):
            if isinstance(ent, dict) and isinstance(ent.get("evidence_ids"), list):
                refs += ent["evidence_ids"]
    return {"evidence_records": len(ev), "fact_references": len(refs), "distinct_fact_references": len(set(map(str, refs))),
            "refs_that_are_transcript_segment_ids": sum(1 for r in refs if isinstance(r, str) and r in res.by_id),
            "refs_resolving_to_model_own_evidence_record": sum(1 for r in refs if r in own_ids),
            "records_with_unknown_segment": a["evidence_records_with_unknown_segment"], "text_mismatch": a["text_mismatch"], "speaker_mismatch": a["speaker_mismatch"],
            "start_timestamp_mismatch": a["start_timestamp_mismatch"], "end_timestamp_mismatch": a["end_timestamp_mismatch"],
            "transcript_segments_without_an_evidence_record": [s for s in res.order if s not in set(seg_cited)],
            "evidence_block_share_of_output_chars": _ratio(compact_json_len(pred.get("clinical_evidence") or []), compact_json_len(pred))}


def discrepancy_handling(gold, pred):
    """Medication-discrepancy handling: detected / linked to the right medicine / both conflicting values named / dose left null (no arbitrary choice)."""
    res = {"gold_cases": 0, "detected": 0, "linked_to_right_medication": 0, "both_values_named": 0, "dose_left_null": 0, "fully_handled": 0,
           "pred_discrepancies_without_gold_case": 0, "cases": []}
    gold_meds, pred_meds = get_entities(gold, "medications"), get_entities(pred, "medications")
    key = lambda e: EM.norm_text(EM.KEYS["medications"](e) or "")
    pred_discs = [u for u in get_entities(pred, "clinical_uncertainties") if isinstance(u, dict) and u.get("type") == "medication_discrepancy"]
    used = set()
    for gu in get_entities(gold, "clinical_uncertainties"):
        if gu.get("type") != "medication_discrepancy":
            continue
        res["gold_cases"] += 1
        m = re.match(r"medications\[(\d+)\]", (gu.get("related_entities") or [""])[0])
        gk = key(gold_meds[int(m.group(1))]) if m and int(m.group(1)) < len(gold_meds) else None
        values = sorted(set(re.findall(r"(\d+(?:\.\d+)?)\s*(mg|mcg|g|ml)\b", EM.norm_text(gu.get("description", "")))))
        case = {"medication": gk, "gold_values": [" ".join(v) for v in values], "detected": False, "linked": False, "both_values": False, "dose_null": None}
        hit = None
        for i, pu in enumerate(pred_discs):
            if i in used:
                continue
            related = []
            for r in (pu.get("related_entities") or []) if isinstance(pu.get("related_entities"), list) else []:
                mm = re.match(r"medications\[(\d+)\]", r) if isinstance(r, str) else None
                if mm and int(mm.group(1)) < len(pred_meds) and isinstance(pred_meds[int(mm.group(1))], dict):
                    related.append(key(pred_meds[int(mm.group(1))]))
            if gk and (gk in related or gk in EM.norm_text(pu.get("description", ""))):
                hit = (i, pu)
                break
        if hit:
            used.add(hit[0])
            case["detected"] = True
            case["linked"] = True
            dn = EM.norm_text(hit[1].get("description", ""))
            case["both_values"] = bool(values) and all(re.search(rf"\b{re.escape(v[0])}\s*{v[1]}\b", dn) for v in values)
            pm = [m_ for m_ in pred_meds if isinstance(m_, dict) and key(m_) == gk]
            case["dose_null"] = bool(pm) and all(m_.get("dose") in (None, "") for m_ in pm)
        res["detected"] += case["detected"]
        res["linked_to_right_medication"] += case["linked"]
        res["both_values_named"] += case["both_values"]
        res["dose_left_null"] += bool(case["dose_null"])
        full = case["detected"] and case["linked"] and case["both_values"] and bool(case["dose_null"])
        res["fully_handled"] += full
        case["fully_handled"] = full
        res["cases"].append(case)
    res["pred_discrepancies_without_gold_case"] = len(pred_discs) - len(used)
    return res


def unsupported_indicators(pred, tr, ctx, fmt):
    """LEXICAL indicators only (not clinical correctness)."""
    res = ctx["res"]
    all_text = " ".join(s["text"] for s in tr["segments"])
    c = Counter()
    examples = defaultdict(list)

    def flag(name, cat, i, ent, detail=""):
        c[name] += 1
        if len(examples[name]) < 5:
            examples[name].append({"location": f"{cat}[{i}]", "detail": detail})

    for cat in categories():
        for i, ent in enumerate(get_entities(pred, cat)):
            if not isinstance(ent, dict):
                continue
            c["facts_total"] += 1
            segs, bad = segments_of_pred_fact(ent, fmt, ctx)
            if not segs:
                flag("no_valid_reference", cat, i, ent)
                text = ""
            else:
                text = " ".join(res.by_id[s]["text"] for s in segs)
            ntext, ntoks = EM.norm_text(text), set(EM.content_tokens(text))
            pk = PRIMARY_TEXT.get(cat)
            if pk and segs and isinstance(ent.get(pk), str):
                toks = EM.content_tokens(ent[pk])
                if toks:
                    c["lexical_checked"] += 1
                    if not _pref_overlap(toks, ntoks):
                        flag("no_lexical_overlap_with_cited_text", cat, i, ent, f"{pk}={ent[pk]!r}")
            nums = []
            for k in ("dose", "severity", "value", "timeframe"):
                if ent.get(k) not in (None, ""):
                    nums.append((k, str(ent[k])))
            for k in ("duration", "time_reference"):
                v = ent.get(k)
                if isinstance(v, dict) and v.get("value") not in (None, ""):
                    nums.append((k, str(v["value"])))
                elif isinstance(v, str) and cat != "follow_up":
                    nums.append((k, v))
            if cat == "follow_up" and isinstance(ent.get("time_reference"), str):
                nums.append(("time_reference", ent["time_reference"]))
            if segs:
                have = _numbers_in(text)
                for k, v in nums:
                    for n in re.findall(r"\d+(?:\.\d+)?", v):
                        c["numbers_checked"] += 1
                        if n not in have and n.lstrip("0") not in have:
                            flag("number_not_in_cited_text", cat, i, ent, f"{k}={v!r}")
            blob = json.dumps(ent, ensure_ascii=False)
            for y in re.findall(r"\b\d{4}-\d{2}-\d{2}\b|\b(?:19|20)\d{2}\b", blob):
                c["dates_checked"] += 1
                if y not in all_text:
                    flag("date_not_in_transcript", cat, i, ent, y)
            if cat == "medications" and ent.get("route") not in (None, ""):
                c["routes_checked"] += 1
                if not ORAL_CUE.search(text):
                    flag("route_without_oral_cue_in_cited_text", cat, i, ent, f"route={ent['route']!r}")
            if cat == "medical_history.social_history" and ent.get("category") in ("smoking", "alcohol"):
                c["habits_checked"] += 1
                cue = SMOKE_CUE if ent["category"] == "smoking" else ALCOHOL_CUE
                if not cue.search(all_text):
                    flag("habit_not_mentioned_anywhere_in_transcript", cat, i, ent, ent["category"])
            if cat == "negative_findings" and segs:
                c["negations_checked"] += 1
                if not NEG_CUE.search(text):
                    flag("negative_finding_without_negation_cue", cat, i, ent, str(ent.get("finding")))
    return dict(c), dict(examples)


# ---------------------------------------------------------------------------------------------------------------------------------
def score_record(eid, rec, fmt, max_refs):
    tr, gold = load_transcript(eid), load_gold(eid)
    res = EvidenceResolver(tr, max_refs)
    gold_map, _ = build_ev_map(gold, tr)
    out = {"id": eid, "status": rec["status"], "cat": {}, "flags": {}, "refs": {}, "overlap": Counter(), "tokens": {}, "unsupported": ({}, {}), "discrepancy": None,
           "planned_meds": Counter(), "evidence_block": None, "n_gold": {}, "n_pred": {}}
    pred, mat = None, None
    if rec["status"] == "parsed":
        if fmt == "compact":
            mat = materialise(rec["obj"], tr, max_refs)
            pred = mat.full
            out["flags"] = mat.flag_counts()
            out["flag_list"] = [f.as_dict() for f in mat.flags][:200]
            out["unmapped_keys"] = len(mat.unmapped)
            out["defaults_applied"] = dict(mat.stats["defaults_applied"])
            out["speaker"] = {k: mat.stats[k] for k in ("speaker_derived", "speaker_explicit", "speaker_unresolved")}
            out["refs"] = {k: mat.stats[k] for k in ("refs_total", "refs_valid", "refs_invalid", "facts_without_refs", "facts_over_limit")}
            ctx = {"res": res, "ev_to_seg": {v: k for k, v in mat.evidence_by_ref.items()}}
        else:
            pred = rec["obj"]
            ctx = {"res": res, "own_ev_to_seg": _own_ev_map(pred, res)}
            out["evidence_block"] = audit_full_evidence_block(pred, tr)
            ev = out["evidence_block"]
            out["refs"] = {"refs_total": ev["fact_references"], "refs_valid": ev["refs_that_are_transcript_segment_ids"] + ev["refs_resolving_to_model_own_evidence_record"],
                           "refs_invalid": ev["fact_references"] - ev["refs_that_are_transcript_segment_ids"] - ev["refs_resolving_to_model_own_evidence_record"]}
    gold_rev = {v: k for k, v in gold_map.items()}
    for cat in categories():
        g_ents = EM.entity_list(gold, cat)
        p_ents = EM.entity_list(pred, cat) if pred is not None else []
        m = EM.match_category(g_ents, p_ents, cat)
        out["cat"][cat] = {k: m[k] for k in ("tp", "fp", "fn")}
        out["n_gold"][cat] = len(EM.keyed(g_ents, cat))
        out["n_pred"][cat] = len(EM.keyed(p_ents, cat))
        if pred is not None:
            for ge, pe in m["pairs"]:
                gs = {gold_map[x] for x in ge.get("evidence_ids", []) if x in gold_map}
                ps, bad = segments_of_pred_fact(pe, fmt, ctx)
                ps = set(ps)
                npred_raw = len(pe.get("evidence_ids") or []) if isinstance(pe.get("evidence_ids"), list) else 0
                out["overlap"]["pairs"] += 1
                out["overlap"]["gold_refs"] += len(gs)
                out["overlap"]["pred_refs_total"] += npred_raw
                out["overlap"]["pred_refs_valid_distinct"] += len(ps)
                out["overlap"]["intersection"] += len(gs & ps)
                out["overlap"]["pairs_with_any_overlap"] += bool(gs & ps)
                out["overlap"]["pairs_exact_set"] += (gs == ps)
        if cat == "medications":
            for ge, pe in m["pairs"]:
                if ge.get("status") == "planned":
                    out["planned_meds"]["matched_by_name"] += 1
                    out["planned_meds"]["matched_by_name_and_status"] += (pe.get("status") == "planned")
            out["planned_meds"]["gold_planned"] += sum(1 for e in g_ents if e.get("status") == "planned")
            out["planned_meds"]["pred_planned"] += sum(1 for e in p_ents if isinstance(e, dict) and e.get("status") == "planned")
    if pred is not None:
        out["discrepancy"] = discrepancy_handling(gold, pred)
        out["unsupported"] = unsupported_indicators(pred, tr, ctx, fmt)
    else:
        out["discrepancy"] = discrepancy_handling(gold, {})
    g = rec.get("gen", {})
    out["tokens"] = {"completion_tokens": g.get("completion_tokens"), "prompt_tokens": g.get("prompt_tokens"), "latency_seconds": g.get("latency_seconds"),
                     "finish_reason": g.get("finish_reason"), "output_chars_compact": compact_json_len(rec["obj"]) if rec["obj"] is not None else None}
    return out


def aggregate(scored: list[dict], label: str = "") -> dict:
    A = {"label": label, "records": len(scored), "not_assessed": NOT_ASSESSED}
    st_counts = Counter(s["status"] for s in scored)
    A["validity"] = {"parsed": st_counts.get("parsed", 0), "failed": st_counts.get("failed", 0), "missing": st_counts.get("missing", 0),
                     "parsed_share": _ratio(st_counts.get("parsed", 0), len(scored)),
                     "truncated_at_token_cap": sum(1 for s in scored if s["tokens"].get("finish_reason") == "length"),
                     "records_with_any_materialisation_flag": sum(1 for s in scored if s["status"] == "parsed" and s["flags"]),
                     "flag_totals": dict(sum((Counter(s["flags"]) for s in scored), Counter()))}

    def block(subset):
        per = {}
        for cat in categories():
            tp = sum(s["cat"][cat]["tp"] for s in subset)
            fp = sum(s["cat"][cat]["fp"] for s in subset)
            fn = sum(s["cat"][cat]["fn"] for s in subset)
            per[cat] = {**_prf(tp, fp, fn), "gold": sum(s["n_gold"][cat] for s in subset), "pred": sum(s["n_pred"][cat] for s in subset)}
        mm = EM.micro_macro({c: {k: v[k] for k in ("tp", "fp", "fn", "precision", "recall", "f1")} for c, v in per.items()})
        return {"records": len(subset), "micro": mm["micro"], "macro": mm["macro"], "per_category": per,
                "negative_findings": per["negative_findings"], "medications": per["medications"]}

    A["entities_tier1_all_records_failed_as_zero"] = block(scored)
    A["entities_tier2_parsed_records_only"] = block([s for s in scored if s["status"] == "parsed"])
    pm = Counter()
    for s in scored:
        pm.update(s["planned_meds"])
    A["planned_medication"] = {"gold_planned": pm["gold_planned"], "recall_by_name": _ratio(pm["matched_by_name"], pm["gold_planned"]),
                               "recall_by_name_and_status_planned": _ratio(pm["matched_by_name_and_status"], pm["gold_planned"]), "pred_planned": pm["pred_planned"]}
    d = Counter()
    for s in scored:
        for k, v in s["discrepancy"].items():
            if k != "cases":
                d[k] += v
    A["medication_discrepancy"] = {**{k: d[k] for k in d}, "cases": [dict(c, id=s["id"]) for s in scored for c in s["discrepancy"]["cases"]]}
    r = Counter()
    for s in scored:
        r.update(s["refs"])
    A["evidence_reference_validity"] = {**dict(r), "valid_share": _ratio(r["refs_valid"], r["refs_total"])}
    o = Counter()
    for s in scored:
        o.update(s["overlap"])
    A["evidence_reference_overlap_with_gold_on_matched_facts"] = {
        "matched_fact_pairs": o["pairs"], "gold_refs": o["gold_refs"], "pred_refs_total": o["pred_refs_total"], "intersection": o["intersection"],
        "precision_vs_gold_segments": _ratio(o["intersection"], o["pred_refs_valid_distinct"]), "recall_of_gold_segments": _ratio(o["intersection"], o["gold_refs"]),
        "pairs_with_any_overlap_share": _ratio(o["pairs_with_any_overlap"], o["pairs"]), "pairs_with_identical_segment_set_share": _ratio(o["pairs_exact_set"], o["pairs"]),
        "mean_pred_refs_per_matched_fact": _ratio(o["pred_refs_total"], o["pairs"]), "mean_gold_refs_per_matched_fact": _ratio(o["gold_refs"], o["pairs"])}
    u, ex = Counter(), defaultdict(list)
    for s in scored:
        if s["status"] == "parsed":
            u.update(s["unsupported"][0])
            for k, v in s["unsupported"][1].items():
                ex[k] += [dict(e, id=s["id"]) for e in v][: max(0, 4 - len(ex[k]))]
    rates = {}
    for ind, base in (("no_valid_reference", "facts_total"), ("no_lexical_overlap_with_cited_text", "lexical_checked"), ("number_not_in_cited_text", "numbers_checked"),
                      ("date_not_in_transcript", "dates_checked"), ("route_without_oral_cue_in_cited_text", "routes_checked"),
                      ("habit_not_mentioned_anywhere_in_transcript", "habits_checked"), ("negative_finding_without_negation_cue", "negations_checked")):
        rates[ind] = {"count": u[ind], "checked": u[base], "rate": _ratio(u[ind], u[base])}
    A["unsupported_claim_indicators_lexical_only"] = {"facts_total": u["facts_total"], "indicators": rates, "examples": dict(ex),
                                                       "caveat": "lexical heuristics, not clinical correctness; gold is scored with the same indicators as a floor (see the self-check)"}
    ct = [s["tokens"]["completion_tokens"] for s in scored if s["tokens"].get("completion_tokens") is not None]
    lt = [s["tokens"]["latency_seconds"] for s in scored if s["tokens"].get("latency_seconds") is not None]
    chars = [s["tokens"]["output_chars_compact"] for s in scored if s["tokens"].get("output_chars_compact") is not None]
    A["output_tokens"] = {"records_with_count": len(ct), "median": st.median(ct) if ct else None, "max": max(ct) if ct else None, "above_3300": sum(c > 3300 for c in ct),
                          "at_cap_4096": sum(c >= TOKEN_CAP for c in ct), "per_record": {s["id"]: s["tokens"].get("completion_tokens") for s in scored},
                          "estimated_tokens_from_output_chars_median": est_tokens(st.median(chars)) if chars else None, "estimate_note": "chars/3.04, an estimate"}
    A["generation_time_seconds"] = {"median": st.median(lt) if lt else None, "max": max(lt) if lt else None, "total": round(sum(lt), 1) if lt else None}
    if any(s["evidence_block"] for s in scored):
        A["full_format_evidence_block_audit"] = {s["id"]: s["evidence_block"] for s in scored if s["evidence_block"]}
    return A


def evaluate(records: dict, fmt: str, max_refs: int = DEFAULT_MAX_REFS, label: str = "") -> dict:
    scored = [score_record(eid, rec, fmt, max_refs) for eid, rec in records.items()]
    A = aggregate(scored, label)
    A["_scored"] = scored
    return A


# ---------------------------------------------------------------------------------------------------------------------------------
def gold_records(ids, fmt):
    """Gold as a 'run': compact (compact gold) or full (gold itself)."""
    recs = {}
    for eid in ids:
        gold, tr = load_gold(eid), load_transcript(eid)
        if fmt == "compact":
            m, _ = build_ev_map(gold, tr)
            obj, _ = to_compact(gold, tr, m)
        else:
            obj = gold
        recs[eid] = {"id": eid, "status": "parsed", "obj": obj, "failure": None, "gen": {}}
    return recs


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--gold-selfcheck", action="store_true", help="score compact gold (materialised) and full gold against gold")
    ap.add_argument("--parsed-dir")
    ap.add_argument("--failed-dir")
    ap.add_argument("--raw-dir")
    ap.add_argument("--format", choices=["compact", "full"], default="compact")
    ap.add_argument("--ids", nargs="*")
    ap.add_argument("--max-refs", type=int, default=DEFAULT_MAX_REFS)
    ap.add_argument("--label", default="")
    ap.add_argument("--out", help="output JSON path (must be inside p02_v2_2/)")
    A = ap.parse_args()
    ids = A.ids or authorised_ids()
    if A.gold_selfcheck:
        res = {"compact_gold": evaluate(gold_records(ids, "compact"), "compact", A.max_refs, "compact gold materialised vs gold"),
               "full_gold": evaluate(gold_records(ids, "full"), "full", A.max_refs, "full gold vs gold")}
    else:
        recs = load_run(A.parsed_dir, A.failed_dir, A.raw_dir, ids)
        res = evaluate(recs, A.format, A.max_refs, A.label)
    for v in ([res] if "_scored" in res else res.values()):
        v.pop("_scored", None)
    if A.out:
        o = Path(A.out).resolve()
        if PKG.resolve() not in o.parents:
            sys.exit("refusing to write outside p02_v2_2/")
        o.parent.mkdir(parents=True, exist_ok=True)
        o.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(res if not A.out else {"written": str(o)}, indent=1, ensure_ascii=False)[:3000])


if __name__ == "__main__":
    main()
