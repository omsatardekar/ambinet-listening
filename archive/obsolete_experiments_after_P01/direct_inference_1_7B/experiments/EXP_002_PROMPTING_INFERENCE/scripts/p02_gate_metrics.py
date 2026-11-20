"""Gate metrics for the proposed P02 pilot (and their reference values from the SAVED P00 / P01 outputs).  Pure analysis of saved files + the frozen evaluator; no inference.
Computes, for a set of run outputs on the exact pilot ids:
  tier 1 strict micro P/R/F1 (as scored, failed = zero predictions)         -- PRIMARY
  tier 2 paired parsed-output comparison (records parsed by both systems)   -- extraction only
  tier 3 structural-recovery diagnostic (failed outputs closed structurally; incomplete; never counted as completed)  -- DIAGNOSTIC ONLY
  evidence metrics (records per encounter, exact single lines, blobs, valid ids, correct supports), format metrics (empty strings, person_N roles, speakers, quality flags, schema violations).
DEVELOPMENT-ONLY.  usage: python -B -s p02_gate_metrics.py   -> evaluations/p02_review/PILOT_GATE_REFERENCES.json"""
import collections
import difflib
import json
import re
import statistics as st
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
TRACK = HERE.parents[3]
sys.path.insert(0, str(TRACK / "scripts"))
import common_1_7b as C  # noqa: E402

sys.path.insert(0, str(C.EXP6 / "s1"))
import evaluate_s1 as E  # noqa: E402
from direct_inference_baseline.evaluation import evaluation_runner as ER, schema_validator as SV, evidence_evaluator as EE  # noqa: E402
from direct_inference_baseline.evaluation.entity_matching import CATEGORIES, KEYS, entity_list, match_category, prf  # noqa: E402

PILOT = ["00168", "00204", "00037", "00092", "00152", "00157", "00042", "00165"]
E1, E2 = TRACK / "experiments" / "EXP_001_DIRECT_INFERENCE", TRACK / "experiments" / "EXP_002_PROMPTING_INFERENCE"
RUNS = {"P00": (E1, "P00_direct_dev50"), "P01": (E2, "P01_schema_guided_dev50")}
REV = E2 / "evaluations" / "p02_review"
ROLE_FIELDS = ("reported_by", "observed_by", "stated_by", "requested_by", "responsible_person", "speaker_role", "role")
SEC = [c for c in CATEGORIES]


def norm(t):
    return re.sub(r"\s+", " ", str(t)).strip().lower()


def close_structurally(text):
    t = text.strip()
    stack, in_str, esc, snaps = [], False, False, []
    for n, ch in enumerate(t):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch in "{[":
            stack.append(ch)
        elif ch in "}]":
            if not stack:
                break
            stack.pop()
            snaps.append((n + 1, "".join(stack)))
    for end, stk in reversed(snaps):
        cand = t[:end] + "".join("}" if c == "{" else "]" for c in reversed(stk))
        try:
            return json.loads(cand)
        except Exception:  # noqa: BLE001
            continue
    return None


def load_run(k, i):
    """returns (status, parsed_or_None, raw_text, record)"""
    e, r = RUNS[k]
    man = json.loads((e / "evaluations" / r / "run_manifest.json").read_text(encoding="utf-8-sig"))["records"][i]
    raw = json.loads((e / "outputs" / "raw" / r / f"encounter_{i}.json").read_text(encoding="utf-8"))["response_text"]
    pp = e / "outputs" / "parsed" / r / f"encounter_{i}.json"
    parsed = None
    if pp.exists():
        parsed = json.loads(pp.read_text(encoding="utf-8"))
        parsed = parsed.get("parsed", parsed) if isinstance(parsed, dict) and "parsed" in parsed else parsed
    return man["status"], parsed, raw, man


def micro(preds, gold, ids):
    t = collections.Counter()
    for i in ids:
        for c in CATEGORIES:
            m = match_category(entity_list(gold[i], c), entity_list(preds.get(i) or {}, c), c)
            t["tp"] += m["tp"]; t["fp"] += m["fp"]; t["fn"] += m["fn"]
    return {**prf(t["tp"], t["fp"], t["fn"]), "tp": t["tp"], "fp": t["fp"], "fn": t["fn"]}


def cat_counts(preds, gold, ids, cats):
    out = {}
    for c in cats:
        tp = fn = 0
        for i in ids:
            m = match_category(entity_list(gold[i], c), entity_list(preds.get(i) or {}, c), c)
            tp += m["tp"]; fn += m["fn"]
        out[c] = {"matched_by_key": tp, "gold": tp + fn}
    return out


def evidence_metrics(preds, trs):
    """preds: id -> parsed output (only parsed outputs).  Returns the review's evidence measures."""
    o = collections.Counter()
    per_record = {}
    for i, p in preds.items():
        segs = trs[i]["segments"]
        segmap = {norm(s["text"]): s for s in segs}
        evs = [e for e in (p.get("clinical_evidence") or []) if isinstance(e, dict)]
        by_id = {e.get("evidence_id"): e for e in evs}
        per_record[i] = len(evs)
        o["encounters"] += 1
        o["evidence_records"] += len(evs)
        for e in evs:
            t = norm(e.get("transcript_text", ""))
            if t in segmap:
                o["exact_single_line"] += 1
                s = segmap[t]
                o["speaker_id_matches_line"] += e.get("speaker_id") == s["speaker_id"]
                o["role_matches_line"] += str(e.get("speaker_role", "")).lower() == s["role"].lower()
                mm = lambda x: f"{int(x) // 60:02d}:{int(x) % 60:02d}"  # noqa: E731
                o["timestamps_match_line"] += e.get("start_timestamp") == mm(s["start_seconds"]) and e.get("end_timestamp") == mm(s["end_seconds"])
            elif sum(norm(s["text"]) in t for s in segs) >= 2:
                o["multi_line_or_whole_transcript_blob"] += 1
            elif t and max(difflib.SequenceMatcher(None, t, norm(s["text"])).ratio() for s in segs) >= 0.85:
                o["near_copy_not_exact"] += 1
            else:
                o["text_not_in_transcript"] += 1
        # facts
        paths = {}
        for c in CATEGORIES:
            for n, ent in enumerate(entity_list(p, c)):
                paths["chief_complaint" if c == "chief_complaint" else f"{c}[{n}]"] = ent
        for pth, ent in paths.items():
            ids = [x for x in (ent.get("evidence_ids") or []) if isinstance(x, str)]
            o["facts"] += 1
            if not ids:
                o["facts_without_evidence_ids"] += 1
                continue
            o["facts_with_evidence_ids"] += 1
            if all(x in by_id for x in ids):
                o["facts_with_all_ids_valid"] += 1
                cited = " ".join(str(by_id[x].get("transcript_text", "")) for x in ids)
                cat_of = pth.split("[")[0]
                o["facts_whose_cited_text_mentions_the_fact"] += bool(EE.lexical_support(KEYS[cat_of](ent) or "", cited, False))
            for x in ids:
                if x in by_id:
                    o["citation_pairs"] += 1
                    o["citation_pairs_with_path_in_supports"] += pth in (by_id[x].get("supports") or [])
                else:
                    o["citation_pairs"] += 1
        for e in evs:
            for sp in e.get("supports") or []:
                o["supports_paths"] += 1
                ent = paths.get(sp)
                o["supports_paths_resolving_and_reciprocal"] += bool(ent) and e.get("evidence_id") in (ent.get("evidence_ids") or [])
    d = dict(o)
    d["mean_evidence_records_per_encounter"] = round(st.mean(per_record.values()), 2) if per_record else None
    d["evidence_records_per_encounter"] = per_record
    r = lambda a, b: round(a / b, 3) if b else None  # noqa: E731
    d["pct_exact_single_line"] = r(o["exact_single_line"], o["evidence_records"])
    d["pct_facts_with_valid_evidence_ids"] = r(o["facts_with_all_ids_valid"], o["facts"])
    d["pct_facts_with_relevant_cited_text"] = r(o["facts_whose_cited_text_mentions_the_fact"], o["facts"])
    d["pct_citation_pairs_with_correct_supports"] = r(o["citation_pairs_with_path_in_supports"], o["citation_pairs"])
    d["pct_supports_paths_resolving_and_reciprocal"] = r(o["supports_paths_resolving_and_reciprocal"], o["supports_paths"])
    return d


def format_metrics(preds, trs, mans):
    o = collections.Counter()
    sv = collections.Counter()
    for i, p in preds.items():
        o["parsed"] += 1

        def walk(x, key=None):
            if isinstance(x, dict):
                for k, v in x.items():
                    walk(v, k)
            elif isinstance(x, list):
                for v in x:
                    walk(v, key)
            elif isinstance(x, str):
                if x == "":
                    o["empty_string_values"] += 1
                if key in ROLE_FIELDS and re.fullmatch(r"person_\d+", x):
                    o["person_id_written_as_role"] += 1
        walk(p)
        tr_sp = {(s["speaker_id"], s["role"].lower()) for s in trs[i]["segments"]}
        ps = {(s.get("speaker_id"), s.get("role")) for s in (p.get("encounter_metadata") or {}).get("primary_speakers", []) if isinstance(s, dict)}
        o["all_speakers_listed_with_correct_role"] += ps == tr_sp
        qc = p.get("quality_checks") or {}
        o["quality_negation_flag_consistent"] += bool(qc.get("negation_detected")) == bool(entity_list(p, "negative_findings"))
        o["quality_review_flag_consistent"] += bool(qc.get("requires_clinician_review")) == bool(entity_list(p, "clinical_uncertainties"))
        rep = SV.validate(p)
        o["schema_fully_compliant_records"] += not rep.violations
        for v in rep.violations:
            sv[v["kind"]] += 1
            if v["kind"] == "missing_field" and v["message"].endswith(".confidence"):
                sv["missing_field:confidence"] += 1
        o["output_tokens_completed_sum"] += mans[i].get("completion_tokens") or 0
    d = dict(o)
    d["schema_violations"] = dict(sv)
    d["schema_violations_per_parsed_record"] = round(sum(v for k, v in sv.items() if ":" not in k) / o["parsed"], 1) if o["parsed"] else None
    d["mean_output_tokens_completed"] = round(o["output_tokens_completed_sum"] / o["parsed"]) if o["parsed"] else None
    return d


def compute(label_to_loader, ids, gold, trs):
    """label_to_loader: label -> function(id) -> (status, parsed, raw, man)"""
    res = {}
    for k, ld in label_to_loader.items():
        rows = {i: ld(i) for i in ids}
        parsed = {i: r[1] for i, r in rows.items() if r[1] is not None}
        closed = {i: (r[1] if r[1] is not None else close_structurally(r[2])) for i, r in rows.items()}
        res[k] = {"status": {i: r[0] for i, r in rows.items()}, "n_parsed": len(parsed), "n_failed": len(ids) - len(parsed), "n_cap_hits": sum(r[3].get("finish_reason") == "length" for r in rows.values()),
                  "tier1_strict_as_scored": micro(parsed, gold, ids), "tier3_structural_closure_diagnostic_INCOMPLETE": micro({i: c for i, c in closed.items() if c is not None}, gold, ids),
                  "evidence": evidence_metrics(parsed, trs), "format": format_metrics(parsed, trs, {i: rows[i][3] for i in parsed}), "_parsed": parsed}
    return res


if __name__ == "__main__":
    spy = C.G.StrictAccessSpy(allow_validation=False)
    assert all(i in E.IDS[:30] for i in PILOT) and len(PILOT) == 8
    out = {"pilot_ids": PILOT, "scope": "DEVELOPMENT-ONLY; thresholds are computed on exactly these eight ids from saved P00/P01 outputs"}
    with spy:
        gold = {i: ER.load_gold(i) for i in PILOT}
        trs = {i: json.loads((C.S.INPUT_DIR / f"encounter_{i}.json").read_text(encoding="utf-8")) for i in PILOT}
        loaders = {k: (lambda i, k=k: load_run(k, i)) for k in RUNS}
        res = compute(loaders, PILOT, gold, trs)
        # tier 2 reference subsets (case in which P02 parses all eight; recomputed at evaluation time on the real paired set)
        t2 = {}
        for k in RUNS:
            ids_k = [i for i in PILOT if res[k]["status"][i] == "parsed"]
            t2[f"{k}_parsed_ids"] = ids_k
            t2[f"{k}_on_its_parsed_ids"] = micro(res[k]["_parsed"], gold, ids_k)
        both = [i for i in PILOT if res["P00"]["status"][i] == "parsed" and res["P01"]["status"][i] == "parsed"]
        t2["P00_P01_both_parsed_ids"] = both
        t2["P00_on_both"] = micro(res["P00"]["_parsed"], gold, both)
        t2["P01_on_both"] = micro(res["P01"]["_parsed"], gold, both)
        cats = ["symptoms", "negative_findings", "clinical_actions", "medications", "allergies", "vital_signs", "review_of_systems", "physical_examination", "medical_history.social_history"]
        gcount = {c: sum(len(entity_list(gold[i], c)) for i in PILOT) for c in cats}
        planned = sum(1 for i in PILOT for g in entity_list(gold[i], "medications") if g.get("status") == "planned")
        cc = {k: {"as_scored_all8": cat_counts(res[k]["_parsed"], gold, PILOT, cats), "on_parsed_ids": cat_counts(res[k]["_parsed"], gold, t2[f"{k}_parsed_ids"], cats)} for k in RUNS}
        pm = {k: sum(match_category([g for g in entity_list(gold[i], "medications") if g.get("status") == "planned"], entity_list(res[k]["_parsed"].get(i) or {}, "medications"), "medications")["tp"] for i in PILOT) for k in RUNS}
        out.update({"gold_facts_total": sum(len(entity_list(gold[i], c)) for i in PILOT for c in CATEGORIES), "gold_counts_by_category": gcount, "gold_planned_medications": planned, "planned_medications_matched_by_key": pm,
                    "tier2_reference_subsets": t2, "category_matches": cc})
        for k in RUNS:
            out[k] = {x: y for x, y in res[k].items() if x != "_parsed"}
    (REV / "PILOT_GATE_REFERENCES.json").write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    for k in RUNS:
        b = out[k]
        print(k, "parsed", b["n_parsed"], "failed", b["n_failed"], "cap", b["n_cap_hits"], "tier1", {a: (round(v, 3) if isinstance(v, float) else v) for a, v in b["tier1_strict_as_scored"].items()})
        print("   tier3 diag", {a: (round(v, 3) if isinstance(v, float) else v) for a, v in b["tier3_structural_closure_diagnostic_INCOMPLETE"].items()})
        e = b["evidence"]
        print("   evidence", {x: e.get(x) for x in ("encounters", "evidence_records", "mean_evidence_records_per_encounter", "exact_single_line", "pct_exact_single_line", "multi_line_or_whole_transcript_blob", "facts", "facts_with_all_ids_valid", "pct_facts_with_valid_evidence_ids", "pct_facts_with_relevant_cited_text", "pct_citation_pairs_with_correct_supports", "pct_supports_paths_resolving_and_reciprocal")})
        print("   format", {x: v for x, v in b["format"].items() if x != "output_tokens_completed_sum"})
    print(json.dumps(out["tier2_reference_subsets"], default=str)[:1800])
    print(json.dumps({"gold": out["gold_counts_by_category"], "planned": [out["gold_planned_medications"], out["planned_medications_matched_by_key"]], "cc": out["category_matches"]}, default=str)[:2600])
