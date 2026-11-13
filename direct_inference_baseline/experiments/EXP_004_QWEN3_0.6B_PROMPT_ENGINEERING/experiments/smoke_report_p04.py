"""EXP_004 P04 smoke-test report generator (read-only on outputs; labels opened only here, after generation; the five approved prompt_dev ids only).
Writes reports/P04_smoke_test_report.md and evaluation/P04_smoke_5/smoke_metrics.json. Optional manual review file: evaluation/P04_smoke_5/manual_review.json
({ "<id>|<location>": {"verdict": "ok|questionable|wrong", "note": "..."} }) written by the reviewer AFTER reading the generated item table; it is merged on a second run."""
import json
import re
import statistics as st
import sys
from collections import Counter

from common import EXP4, S, SPLIT, write_json
from evidence_builder import entity_locations, verify_only_evidence_changed
from direct_inference_baseline.evaluation import evaluation_runner as ER
from direct_inference_baseline.evaluation import schema_validator as SV
from direct_inference_baseline.evaluation.entity_matching import CATEGORIES, KEYS, content_tokens, entity_list, match_category, norm_text, prf

RUN = "P04_smoke_5"
IDS = ["00035", "00037", "00040", "00215", "00248"]
assert all(i in SPLIT["prompt_dev_ids"] for i in IDS)
OUT = EXP4 / "outputs" / RUN
EV = EXP4 / "evaluation" / RUN
EV.mkdir(parents=True, exist_ok=True)
man = json.loads((EV / "run_manifest.json").read_text(encoding="utf-8"))["records"] if (EV / "run_manifest.json").exists() else json.loads((EXP4 / "evaluation" / RUN / "run_manifest.json").read_text(encoding="utf-8"))["records"]
p02man = json.loads((EXP4 / "evaluation" / "P02_comprehensive_extraction_dev50" / "run_manifest.json").read_text(encoding="utf-8"))["records"]
P02 = EXP4 / "outputs" / "P02_comprehensive_extraction_dev50" / "parsed_predictions" / "P02_comprehensive_extraction_dev50"
manual = json.loads((EV / "manual_review.json").read_text(encoding="utf-8")) if (EV / "manual_review.json").exists() else {}
QF = {"chief_complaint": ["value", "normalized_value"], "symptoms": ["name", "normalized_name", "body_site"], "negative_findings": ["finding", "normalized_name"], "medical_history.past_medical_history": ["condition", "normalized_condition"],
      "medical_history.surgical_history": ["procedure", "normalized_procedure"], "medical_history.family_history": ["condition", "normalized_condition", "relation"], "medical_history.social_history": ["category", "description", "details"],
      "medications": ["name", "normalized_name", "generic_name", "dose", "frequency"], "allergies": ["substance", "normalized_substance", "reaction"], "vital_signs": ["name", "normalized_name", "value"],
      "physical_examination": ["finding", "normalized_finding", "body_site"], "review_of_systems": ["system", "details"], "clinical_conditions": ["name", "normalized_name"], "clinical_assessment": ["assessment", "normalized_assessment"],
      "procedures_and_investigations": ["name", "normalized_name"], "clinical_actions": ["description"], "follow_up": ["time_reference"], "clinical_uncertainties": ["description"]}
mm = lambda s: f"{int(s)//60:02d}:{int(s)%60:02d}"
pct = lambda a, b: f"{100*a/b:.1f}%" if b else "n/a"
load = lambda p: json.loads(p.read_text(encoding="utf-8"))


def overlap(text, query):
    q = {t[:5] for t in content_tokens(norm_text(query))}
    if not q:
        return None
    words = norm_text(text).split()
    return sum(any(w.startswith(t) for w in words) for t in q) / len(q)


def seg_of_ev(rec, segs):
    t = norm_text(rec.get("transcript_text"))
    hit = [i for i, s in enumerate(segs) if t == norm_text(s["text"]) and s["speaker_id"] == rec.get("speaker_id") and mm(s["start_seconds"]) == rec.get("start_timestamp")]
    return hit[0] if hit else None


per, rows, appendix = {}, [], []
pool = {"p04": Counter(), "p02": Counter()}
agree = Counter()
for eid in IDS:
    tr = load(S.INPUT_DIR / f"encounter_{eid}.json"); segs = tr["segments"]; rec = man.get(eid, {})
    gold = ER.load_gold(eid)
    inter_p, final_p = OUT / "intermediate_predictions" / f"encounter_{eid}.json", OUT / "parsed_predictions" / RUN / f"encounter_{eid}.json"
    inter = load(inter_p) if inter_p.exists() else None
    final = load(final_p) if final_p.exists() else None
    rep = load(OUT / "build_reports" / f"encounter_{eid}.json") if (OUT / "build_reports" / f"encounter_{eid}.json").exists() else None
    raw = load(OUT / "raw_predictions" / RUN / f"encounter_{eid}.json") if (OUT / "raw_predictions" / RUN / f"encounter_{eid}.json").exists() else None
    p02p = load(P02 / f"encounter_{eid}.json") if (P02 / f"encounter_{eid}.json").exists() else None
    e = {"status": rec.get("status"), "parse_status": rec.get("parse_status"), "parse_notes": rec.get("parse_notes"), "finish_reason": rec.get("finish_reason"), "failure_type": rec.get("failure_type"),
         "prompt_tokens": rec.get("prompt_tokens"), "completion_tokens": rec.get("completion_tokens"), "latency_s": rec.get("latency_seconds"),
         "tokens_per_s": round(rec["completion_tokens"] / rec["latency_seconds"], 2) if rec.get("latency_seconds") else None, "n_segments": len(segs)}
    # schema
    e["schema_compliant"], e["schema_violation_counts"] = rec.get("schema_compliant"), rec.get("schema_violation_counts")
    e["schema_evidence_field_violations"] = sum(1 for v in SV.validate(final).violations if "evidence" in v["message"] or "supports" in v["message"]) if final else None
    # extraction
    sc = ER.score_encounter(gold, final, tr)["strict"]
    tp, fp, fn = (sum(v[k] for v in sc.values()) for k in ("tp", "fp", "fn"))
    e["extraction"] = {"tp": tp, "fp": fp, "fn": fn, **prf(tp, fp, fn)}
    sc2 = ER.score_encounter(gold, p02p, tr)["strict"]
    tp2, fp2, fn2 = (sum(v[k] for v in sc2.values()) for k in ("tp", "fp", "fn"))
    r2 = p02man.get(eid, {})
    e["p02"] = {"status": r2.get("status"), "tp": tp2, "fp": fp2, "fn": fn2, **prf(tp2, fp2, fn2), "items": tp2 + fp2, "completion_tokens": r2.get("completion_tokens"), "latency_s": r2.get("latency_seconds"),
                "schema_violations_total": sum((r2.get("schema_violation_counts") or {}).values()), "schema_compliant": r2.get("schema_compliant")}
    for k, v in (("tp", tp), ("fp", fp), ("fn", fn)):
        pool["p04"][k] += v
    for k, v in (("tp", tp2), ("fp", fp2), ("fn", fn2)):
        pool["p02"][k] += v
    if final and rep and inter:
        locs = entity_locations(final)
        e["facts_total"] = rep["entities"]; e["facts_with_valid_ref"] = rep["entities_with_valid_citation"]; e["facts_without_ref"] = rep["entities_uncited"]
        e["refs_exact"], e["refs_normalised_spelling"], e["refs_invalid"], e["refs_duplicates_removed"] = rep["ids_exact"], rep["ids_normalised"], rep["ids_invalid"], rep["ids_duplicate_removed"]
        e["invalid_ref_examples"] = rep["invalid_examples"]; e["items_source_key_missing"], e["items_source_key_wrong_type"] = rep["key_missing"], rep["key_wrong_type"]
        e["ids_per_item_distribution"] = rep["ids_per_item_distribution"]; e["items_with_more_than_6_ids"] = rep["items_with_more_than_6_ids"]
        e["evidence_records"] = rep["evidence_records"]
        e["builder_integrity_flag_in_report"] = rep["integrity_identical_except_evidence_fields"]
        e["builder_integrity_recomputed"] = verify_only_evidence_changed(inter, final)
        e["model_wrote_own_evidence_ids_items"], e["model_wrote_clinical_evidence_records"] = rep["model_evidence_ids_dropped"], rep["model_clinical_evidence_discarded"]
        # independent record correctness against the transcript
        ok = Counter()
        evl = final.get("clinical_evidence") or []
        pos_by_id = {}
        for r in evl:
            ok["records"] += 1
            i = seg_of_ev(r, segs)
            if i is None:
                continue
            s = segs[i]; pos_by_id[r["evidence_id"]] = i
            ok["text_exact"] += r["transcript_text"] == s["text"]; ok["speaker_id"] += r["speaker_id"] == s["speaker_id"]; ok["role_lowercase"] += r["speaker_role"] == str(s["role"]).lower()
            ok["start_floor"] += r["start_timestamp"] == mm(s["start_seconds"]); ok["end_floor"] += r["end_timestamp"] == mm(s["end_seconds"]); ok["found_in_transcript"] += 1
        e["record_correctness"] = dict(ok)
        # supports consistency
        loc_ent = dict(locs); sup = Counter()
        for r in evl:
            for s_ in r.get("supports") or []:
                sup["supports_entries"] += 1
                ent = loc_ent.get(s_)
                sup["supports_entries_pointing_to_existing_item"] += ent is not None
                sup["supports_entries_reciprocal"] += ent is not None and r["evidence_id"] in (ent.get("evidence_ids") or [])
        for l, ent in locs:
            for x in ent.get("evidence_ids") or []:
                sup["item_evidence_ids"] += 1
                rr = next((r for r in evl if r["evidence_id"] == x), None)
                sup["item_evidence_ids_resolving"] += rr is not None
                sup["item_evidence_ids_listed_in_supports"] += rr is not None and l in (rr.get("supports") or [])
        sup["records_with_empty_supports"] = sum(not (r.get("supports")) for r in evl)
        e["supports_correctness"] = dict(sup)
        # citation positions, greetings, questionable flags, gold agreement
        ev_by_id = {r["evidence_id"]: r for r in evl}
        gold_evid = {r["evidence_id"]: seg_of_ev(r, segs) for r in gold.get("clinical_evidence", [])}
        gloc = {id(x): l for l, x in entity_locations(gold)}; floc = {id(x): l for l, x in locs}
        tp_pairs = {}
        for c in CATEGORIES:
            m = match_category(entity_list(gold, c), entity_list(final, c), c)
            for ge, pe in m["pairs"]:
                tp_pairs[floc[id(pe)]] = ge
        positions = Counter(); flags = Counter(); tab = []
        for l, ent in locs:
            cat = l.split("[")[0]
            query = " ".join(str(ent.get(f)) for f in QF[cat] if ent.get(f) not in (None, ""))
            ids = ent.get("evidence_ids") or []
            cited = [(x, pos_by_id.get(x)) for x in ids]
            item = {"loc": l, "key": (str(KEYS[cat](ent)) if KEYS[cat](ent) else query)[:70], "cited": [], "flags": [], "gold_matched": l in tp_pairs, "hit_gold": None}
            only_question = bool(cited) and all(i is not None and segs[i]["text"].strip().endswith("?") for _, i in cited)
            for x, i in cited:
                if i is None:
                    continue
                s = segs[i]; positions[min(i, 5)] += 1
                ov = overlap(s["text"], query)
                short = len(s["text"].split()) <= 8
                item["cited"].append({"seg": s["segment_id"], "who": f"{s['speaker_id']}/{s['role']}", "text": s["text"][:130], "overlap": None if ov is None else round(ov, 2)})
                if ov == 0:
                    item["flags"].append("no lexical overlap")
                if i <= 1 and (ov in (0, None) or short):
                    item["flags"].append("opening/greeting segment")
            if only_question:
                item["flags"].append("question-only citation")
            if not ids:
                item["flags"].append("no reference")
            item["flags"] = sorted(set(item["flags"]))
            for fl in item["flags"]:
                flags[fl] += 1
            if l in tp_pairs:
                ge = tp_pairs[l]
                G = {gold_evid.get(x) for x in (ge.get("evidence_ids") or []) if gold_evid.get(x) is not None}
                sel = {i for _, i in cited if i is not None}
                if G:
                    item["hit_gold"] = bool(sel & G)
                    agree["matched_items_with_gold_citation"] += 1; agree["hit"] += bool(sel & G); agree["sel"] += len(sel); agree["inter"] += len(sel & G); agree["gold"] += len(G)
                    agree[f"{eid}_n"] += 1; agree[f"{eid}_hit"] += bool(sel & G)
            mr = manual.get(f"{eid}|{l}")
            if mr:
                item["manual"] = mr
            tab.append(item)
        e["citation_position_distribution_0_to_5plus"] = dict(sorted(positions.items()))
        e["citations_in_first_two_segments"] = positions.get(0, 0) + positions.get(1, 0)
        e["total_citations"] = sum(positions.values())
        e["auto_flag_counts"] = dict(flags)
        e["items_with_auto_flag_questionable"] = sum(1 for t in tab if set(t["flags"]) - {"no reference"})
        e["manual_verdict_counts"] = dict(Counter(t["manual"]["verdict"] for t in tab if "manual" in t))
        e["items_questionable_total"] = sum(1 for t in tab if (set(t["flags"]) - {"no reference"}) or (t.get("manual") or {}).get("verdict") in ("questionable", "wrong"))
        e["items_questionable_manual_only"] = sum(1 for t in tab if not (set(t["flags"]) - {"no reference"}) and (t.get("manual") or {}).get("verdict") in ("questionable", "wrong"))
        e["gold_agreement"] = {"matched_items_(strict_TP)": len(tp_pairs), "of_which_with_gold_citation": agree[f"{eid}_n"], "hit_any": agree[f"{eid}_hit"], "matched_over_extracted": pct(len(tp_pairs), rep["entities"])}
        rows += [(eid, t) for t in tab]
        appendix.append((eid, inter, final))
    elif raw:
        appendix.append((eid, {"RAW_MODEL_OUTPUT_NOT_PARSED": raw.get("response_text", "")[:6000]}, None))
    per[eid] = e

# --------------- pooled and gates
valid = [i for i in IDS if per[i].get("facts_total") is not None]
tot = lambda k: sum(per[i].get(k, 0) or 0 for i in valid)
facts, withref, noref = tot("facts_total"), tot("facts_with_valid_ref"), tot("facts_without_ref")
rx, rn, ri = tot("refs_exact"), tot("refs_normalised_spelling"), tot("refs_invalid")
recs_n = [per[i]["evidence_records"] for i in valid]
p02_items = sum(per[i]["p02"]["items"] for i in IDS)
gates = {
    "S1_all_parse_build_validator": {"parsed": f"{len(valid)}/5", "builder_ok": f"{len(valid)}/5", "evidence_field_violations_in_final": sum(per[i]["schema_evidence_field_violations"] or 0 for i in valid),
                                      "pass": len(valid) == 5 and all((per[i]["schema_evidence_field_violations"] or 0) == 0 for i in valid)},
    "S2_valid_refs": {"facts_with_valid_ref": f"{withref}/{facts} ({pct(withref, facts)})", "emitted_ids_valid": f"{rx + rn}/{rx + rn + ri} ({pct(rx + rn, rx + rn + ri)})", "exact_only_share": pct(rx, rx + rn + ri),
                      "pass": facts > 0 and withref / facts >= 0.9 and (rx + rn + ri) > 0 and (rx + rn) / (rx + rn + ri) >= 0.9},
    "S3_records_ge_5_in_at_least_4_of_5": {"records_per_encounter": {i: per[i].get("evidence_records") for i in IDS}, "encounters_with_ge_5": sum(1 for r in recs_n if r >= 5), "pass": sum(1 for r in recs_n if r >= 5) >= 4},
    "S5_not_collapsed": {"p04_items": facts, "p02_items_same_ids": p02_items, "ratio": round(facts / p02_items, 3) if p02_items else None, "mean_output_tokens_all_5_records": round(st.mean(per[i]["completion_tokens"] for i in IDS), 1),
                         "pass": bool(valid) and facts >= 0.7 * p02_items and st.mean(per[i]["completion_tokens"] for i in IDS) <= 3000},
    "S6_builder_integrity": {"identical_except_evidence_fields": f"{sum(per[i]['builder_integrity_recomputed']['identical_except_evidence_fields'] for i in valid)}/{len(valid)}", "invalid_or_missing_refs_reported_separately": True,
                             "records_the_builder_processed": len(valid), "not_applicable": [i for i in IDS if i not in valid], "pass": len(valid) >= 1 and all(per[i]["builder_integrity_recomputed"]["identical_except_evidence_fields"] and per[i]["builder_integrity_recomputed"]["n_items_before"] == per[i]["builder_integrity_recomputed"]["n_items_after"] for i in valid)}}
audit = load(OUT / "file_access_audit.json") if (OUT / "file_access_audit.json").exists() else {}
gates["S6_builder_integrity"]["label_files_opened_during_inference"] = len(audit.get("label_or_blueprint_files_opened", []))
gha = load(EXP4 / "evaluation" / "frozen_dataset_hash_access_audit.json")
gates["S6_builder_integrity"]["locked_test_transcripts_opened_only_for_checksum_by_existing_runner"] = gha["locked_test_transcripts_opened_for_checksum"]
gates["S6_builder_integrity"]["locked_test_transcripts_used_for_prompting_parsing_or_evaluation"] = len([f for f in (OUT / "parsed_predictions" / RUN).glob("encounter_*.json") if f.stem.replace("encounter_", "") not in IDS]) + len([f for f in (OUT / "raw_predictions" / RUN).glob("encounter_*.json") if f.stem.replace("encounter_", "") not in IDS])
gates["S6_builder_integrity"]["pass"] &= gates["S6_builder_integrity"]["label_files_opened_during_inference"] == 0 and gates["S6_builder_integrity"]["locked_test_transcripts_used_for_prompting_parsing_or_evaluation"] == 0
pooled = {"p04": {**dict(pool["p04"]), **prf(pool["p04"]["tp"], pool["p04"]["fp"], pool["p04"]["fn"])}, "p02": {**dict(pool["p02"]), **prf(pool["p02"]["tp"], pool["p02"]["fp"], pool["p02"]["fn"])}}
ga = {"matched_items_(strict_TP)_total": sum(per[i]["gold_agreement"]["matched_items_(strict_TP)"] for i in valid) if valid else 0, "matched_items_with_gold_citation_denominator": agree["matched_items_with_gold_citation"],
      "hit_any": agree["hit"], "hit_any_rate": round(agree["hit"] / agree["matched_items_with_gold_citation"], 4) if agree["matched_items_with_gold_citation"] else None,
      "set_precision": round(agree["inter"] / max(1, agree["sel"]), 4), "set_recall": round(agree["inter"] / max(1, agree["gold"]), 4), "extracted_items": facts,
      "matched_coverage_of_extracted": pct(agree["matched_items_with_gold_citation"], facts), "provisional_threshold": 0.739}
write_json(EV / "smoke_metrics.json", {"per_encounter": per, "gates": gates, "pooled_extraction": pooled, "gold_segment_agreement": ga, "items": [{"id": a, **b} for a, b in rows]})

# --------------- markdown
L = []
w = L.append
w("# P04 smoke-test report (5 records) - FOR REVIEW. A smoke test is a feasibility check; it does not show that P04 works or that evidence is semantically correct.\n")
rs = load(OUT / "run_settings.json") if (OUT / "run_settings.json").exists() else {}
pf = load(OUT / "preflight.json") if (OUT / "preflight.json").exists() else {}
w(f"Run `{RUN}`; prompt `prompts/P04_integrated_segment_evidence.txt` sha256 `{rs.get('prompt_sha256_verified_before_inference')}` (verified before and after inference: {rs.get('prompt_sha256_verified_after_inference') == rs.get('prompt_sha256_verified_before_inference')}).")
w(f"Ids: {', '.join(IDS)} (all prompt_dev, none in validation or the locked test set). Start {rs.get('start_local')}, end {rs.get('end_local')}, wall {rs.get('wall_seconds')} s.")
w(f"Pre-flight: all {len(pf.get('checks', {}))} checks passed = {pf.get('all_pass')} (prompt hash, ids/splits, OpenVINO FP16 model files vs the EXP_002 conversion record, settings identical to the P02 and P03 run manifests, 6144-token cap, Qwen3-0.6B rev c1899de2, OpenVINO GenAI GPU, greedy, thinking off). File-access audit: {gates['S6_builder_integrity']['label_files_opened_during_inference']} label/blueprint files opened, {gates['S6_builder_integrity']['locked_test_transcripts_opened_only_for_checksum_by_existing_runner']} locked-test transcripts were read ONLY to compute their SHA-256 in the existing runner's frozen-dataset verification (see section 6); {gates['S6_builder_integrity']['locked_test_transcripts_used_for_prompting_parsing_or_evaluation']} were used for prompting, parsing or evaluation.\n")
w("## 1. Gates (smoke criteria S1-S6)\n| Gate | Result | Detail |\n|---|---|---|")
for k, v in gates.items():
    w(f"| {k} | **{'PASS' if v['pass'] else 'FAIL'}** | {json.dumps({a: b for a, b in v.items() if a != 'pass'}, ensure_ascii=False)} |")
w("\nS4 is report-only (section 5). Passing S1-S3, S5 and S6 means the pipeline is feasible and structurally sound; it says nothing about whether the cited segments genuinely support the facts (section 5 and 6).\n")
w("## 2. Per-encounter summary\n| Item | " + " | ".join(IDS) + " |\n|---|" + "---|" * len(IDS))
def row(label, f):
    w(f"| {label} | " + " | ".join(str(f(per[i])) for i in IDS) + " |")
row("JSON parse result (status / finish)", lambda e: f"{e['status']} / {e['finish_reason']}")
row("Schema compliant (final)", lambda e: e["schema_compliant"])
row("Schema violations (final), by kind", lambda e: json.dumps(e["schema_violation_counts"]))
row("Evidence-field violations in final", lambda e: e["schema_evidence_field_violations"])
row("Extracted facts", lambda e: e.get("facts_total"))
row("Facts with >=1 valid reference", lambda e: e.get("facts_with_valid_ref"))
row("Facts with no reference", lambda e: e.get("facts_without_ref"))
row("Refs exact / spelling-normalised / invalid / duplicate-removed", lambda e: f"{e.get('refs_exact')} / {e.get('refs_normalised_spelling')} / {e.get('refs_invalid')} / {e.get('refs_duplicates_removed')}")
row("Invalid-ref examples", lambda e: e.get("invalid_ref_examples"))
row("Items with missing / mistyped source_segments", lambda e: f"{e.get('items_source_key_missing')} / {e.get('items_source_key_wrong_type')}")
row("Evidence records created", lambda e: e.get("evidence_records"))
row("Segments in transcript", lambda e: e["n_segments"])
row("Ids per item (n ids: n items)", lambda e: json.dumps(e.get("ids_per_item_distribution")))
row("Citations / in first two segments", lambda e: f"{e.get('total_citations')} / {e.get('citations_in_first_two_segments')}")
row("Citation position (index 0..5+)", lambda e: json.dumps(e.get("citation_position_distribution_0_to_5plus")))
row("Items auto-flagged questionable (lexical/greeting/question-only)", lambda e: e.get("items_with_auto_flag_questionable"))
row("Items questionable incl. manual review", lambda e: e.get("items_questionable_total"))
row("Records: text exact / speaker / role / start / end vs transcript", lambda e: (lambda c: f"{c.get('text_exact')}/{c.get('speaker_id')}/{c.get('role_lowercase')}/{c.get('start_floor')}/{c.get('end_floor')} of {c.get('records')}")(e.get("record_correctness", {})))
row("Supports: entries / to existing item / reciprocal; item ids listed in supports", lambda e: (lambda c: f"{c.get('supports_entries')}/{c.get('supports_entries_pointing_to_existing_item')}/{c.get('supports_entries_reciprocal')}; {c.get('item_evidence_ids_listed_in_supports')} of {c.get('item_evidence_ids')}")(e.get("supports_correctness", {})))
row("Records with empty supports", lambda e: (e.get("supports_correctness") or {}).get("records_with_empty_supports"))
row("Builder integrity (only evidence fields changed)", lambda e: (e.get("builder_integrity_recomputed") or {}).get("identical_except_evidence_fields"))
row("Model wrote own evidence_ids items / clinical_evidence records (ignored)", lambda e: f"{e.get('model_wrote_own_evidence_ids_items')} / {e.get('model_wrote_clinical_evidence_records')}")
row("Completion tokens / prompt tokens", lambda e: f"{e['completion_tokens']} / {e['prompt_tokens']}")
row("Latency s / tokens per s", lambda e: f"{e['latency_s']} / {e['tokens_per_s']}")
row("Extraction TP/FP/FN (strict)", lambda e: f"{e['extraction']['tp']}/{e['extraction']['fp']}/{e['extraction']['fn']}")
row("Precision / recall / F1", lambda e: f"{(e['extraction']['precision'] or 0):.3f}/{(e['extraction']['recall'] or 0):.3f}/{(e['extraction']['f1'] or 0):.3f}")
w("\n## 3. Comparison with P02 on exactly the same five ids (P02 = existing 50-record outputs, same model and settings)\n| | P04 smoke | P02 |\n|---|---|---|")
for lab, a, b in (("Strict TP / FP / FN (pooled)", f"{pooled['p04']['tp']} / {pooled['p04']['fp']} / {pooled['p04']['fn']}", f"{pooled['p02']['tp']} / {pooled['p02']['fp']} / {pooled['p02']['fn']}"),
                  ("Micro precision / recall / F1", f"{(pooled['p04']['precision'] or 0):.3f} / {(pooled['p04']['recall'] or 0):.3f} / {(pooled['p04']['f1'] or 0):.3f}", f"{(pooled['p02']['precision'] or 0):.3f} / {(pooled['p02']['recall'] or 0):.3f} / {(pooled['p02']['f1'] or 0):.3f}"),
                  ("Items extracted", facts, p02_items),
                  ("Schema violations total (final / as written by the model)", sum(sum((per[i]['schema_violation_counts'] or {}).values()) for i in IDS), sum(per[i]['p02']['schema_violations_total'] for i in IDS)),
                  ("Fully schema-compliant records", sum(bool(per[i]['schema_compliant']) for i in IDS), sum(bool(per[i]['p02']['schema_compliant']) for i in IDS)),
                  ("Mean completion tokens", round(st.mean(per[i]['completion_tokens'] for i in IDS), 1), round(st.mean(per[i]['p02']['completion_tokens'] for i in IDS), 1)),
                  ("Mean latency s", round(st.mean(per[i]['latency_s'] for i in IDS), 1), round(st.mean(per[i]['p02']['latency_s'] for i in IDS), 1)),
                  ("Evidence records per encounter", ", ".join(str(per[i].get("evidence_records")) for i in IDS), "1, 1, 1, 1, 1 (one template record in every P02 output)")):
    w(f"| {lab} | {a} | {b} |")
w("\nPer encounter (P04 TP/FP/FN vs P02): " + "; ".join(f"{i}: {per[i]['extraction']['tp']}/{per[i]['extraction']['fp']}/{per[i]['extraction']['fn']} vs {per[i]['p02']['tp']}/{per[i]['p02']['fp']}/{per[i]['p02']['fn']}" for i in IDS))
w("\nFive records are too few to say whether extraction was preserved; they only show whether it collapsed. The 50-record gates are the real test.\n")
w("## 4. Gold-segment agreement (provisional V5 reference 73.9%) - denominators first\n")
w(f"* Extracted facts: {ga['extracted_items']}; strictly matched to a gold item and carrying a gold citation (the denominator): **{ga['matched_items_with_gold_citation_denominator']}** ({ga['matched_coverage_of_extracted']} of extracted facts). Hit-any: {ga['hit_any']}/{ga['matched_items_with_gold_citation_denominator']} = {ga['hit_any_rate']}; set precision {ga['set_precision']}, set recall {ga['set_recall']}.")
w("* This applies only to the matched items, which is a small and favourable subset; it is **not overall clinical evidence accuracy** and says nothing about the facts that do not match a gold item. With so few matched items it cannot be compared with 73.9% in a meaningful way. Arm R's 88.9% is likewise a matched-items figure.\n")
w("## 5. Citation inspection (S4: report and inspect; no positional rejection)\n")
allpos = Counter()
for i in valid:
    allpos.update({int(k): v for k, v in per[i]["citation_position_distribution_0_to_5plus"].items()})
w(f"Segment-position distribution of all citations (index 0 = SEG0001; 5 = index 5 or later): {dict(sorted(allpos.items()))}. Automatic flags (counts): " + json.dumps({k: sum(per[i]['auto_flag_counts'].get(k, 0) for i in valid) for k in ('opening/greeting segment', 'no lexical overlap', 'question-only citation', 'no reference')}) + ".")
w("Flags are heuristics: 'no lexical overlap' can be legitimate when the item uses a standard term that was not spoken; 'opening/greeting segment' = cited segment among the first two and either no overlap or <= 8 words. They are not verdicts. The full item-by-item table (item, cited segment text, flags, gold-match, manual review if present) follows.\n")
w("| id | item | cited segment(s) | flags | gold | manual |\n|---|---|---|---|---|---|")
for eid, t in rows:
    cs = "<br>".join(f"{c['seg']} {c['who']}: {c['text']}" for c in t["cited"]) or "-"
    mv = t.get("manual")
    w(f"| {eid} | {t['loc']} : {t['key']} | {cs.replace('|', '/')} | {', '.join(t['flags']) or '-'} | {'TP' + (' hit' if t['hit_gold'] else ' miss' if t['hit_gold'] is False else '') if t['gold_matched'] else '-'} | {(mv['verdict'] + ': ' + mv['note']).replace('|', '/') if mv else '-'} |")
nf = EV / "narrative.md"
if nf.exists():
    w(nf.read_text(encoding="utf-8"))
w("\n## 6. Limitations of this report\nFive encounters; one run; evidence-record counts are not a measure of correctly grounded facts; structural checks (records, speakers, timestamps, supports) are correct by construction when the references are valid; manual verdicts (if present) are my reading, not independent.\n")
w("## 7. Complete intermediate model JSON and final built JSON (all five records)\n")
for eid, inter, final in appendix:
    w(f"### {eid} - intermediate model JSON (what Qwen produced, parsed; before evidence building)\n```json\n{json.dumps(inter, indent=1, ensure_ascii=False)}\n```\n")
    if final:
        w(f"### {eid} - final built JSON (after the evidence builder; validator-checked)\n```json\n{json.dumps(final, indent=1, ensure_ascii=False)}\n```\n")
(EXP4 / "reports" / "P04_smoke_test_report.md").write_text("\n".join(L), encoding="utf-8")
print(json.dumps({"gates": {k: v["pass"] for k, v in gates.items()}, "facts": facts, "withref": withref, "records": recs_n, "pooled": pooled, "gold_agreement": ga}, indent=1))
