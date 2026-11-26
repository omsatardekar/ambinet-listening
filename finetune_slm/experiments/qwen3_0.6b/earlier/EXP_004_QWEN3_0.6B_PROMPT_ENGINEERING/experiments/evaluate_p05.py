"""EXP_004 P05 evaluation (after generation; unchanged existing evaluator functions; reports each quantity separately).
usage: evaluate_p05.py <scope: prompt_dev|validation> <stage1_parsed_dir> <run_dir> <out_dir> [<stage1_run_manifest.json>]
  stage1_parsed_dir = P02 parsed predictions (stage 1); run_dir contains final_predictions/ and decisions/ written by run_p05_validation.py.
Scope control: labels of the scope ids only; the validation scope needs the recorded authorisation (dev_guard.validation_authorized). StrictAccessSpy stops the run on any locked-test access."""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from common import EXP4, S, SPLIT, write_json
import dev_guard as G
import p05_retrieval as R
import p05_eval_lib as L
from evidence_builder import entity_locations
from direct_inference_baseline.evaluation import evaluation_runner as ER
from direct_inference_baseline.evaluation import schema_validator as SV
from direct_inference_baseline.evaluation.entity_matching import CATEGORIES, entity_list, match_category, norm_text, prf

scope, stage1_dir, run_dir, out_dir = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4])
stage1_manifest = json.loads(Path(sys.argv[5]).read_text(encoding="utf-8"))["records"] if len(sys.argv) > 5 else None
IDS = {"prompt_dev": SPLIT["prompt_dev_ids"], "validation": SPLIT["validation_ids"]}[scope]
if scope == "validation" and not G.validation_authorized():
    print("STOP: validation evaluation needs the recorded authorisation for the frozen configuration"); sys.exit(3)
G.install(IDS, include_labels=True, allow_validation=(scope == "validation"))
GATES = json.loads((EXP4 / "experiments" / "P05_validation_gates.json").read_text(encoding="utf-8"))
out_dir.mkdir(parents=True, exist_ok=True)
mm = lambda s: f"{int(s)//60:02d}:{int(s)%60:02d}"


def main():
    tot_final, tot_s1 = Counter(), Counter()
    results_final = []
    A = {n: defaultdict(Counter) for n in ("R_cons", "R_simple", "R_main")}     # matched facts with a gold citation
    C = {n: defaultdict(Counter) for n in ("R_cons", "R_simple", "R_main")}     # all extracted facts (no reference; coverage and behaviour)
    struct, supp = Counter(), Counter()
    reasons = Counter(); cited_fact_match = Counter(); per_enc_records = []; matched_total = 0; all_facts = 0
    flagged = []
    for eid in IDS:
        s1p = stage1_dir / f"encounter_{eid}.json"
        if not s1p.exists():
            continue
        tr = L.load_transcript(eid); segs = tr["segments"]; enc = R.Enc(segs)
        pred = json.loads(s1p.read_text(encoding="utf-8"))
        final = json.loads((run_dir / "final_predictions" / f"encounter_{eid}.json").read_text(encoding="utf-8"))
        dec = json.loads((run_dir / "decisions" / f"encounter_{eid}.json").read_text(encoding="utf-8"))
        by_loc = {d["location"]: d for d in dec["decisions"]}
        gold, seg_of = L.gold_segment_map(eid, segs)
        # extraction unchanged?
        for name, obj, tot in (("stage1", pred, tot_s1), ("final", final, tot_final)):
            sc = ER.score_encounter(gold, obj, tr)["strict"]
            for k in ("tp", "fp", "fn"):
                tot[k] += sum(v[k] for v in sc.values())
        results_final.append(ER.score_encounter(gold, final, tr))
        # all extracted facts: coverage and behaviour (no gold needed)
        floc = {id(e): l for l, e in entity_locations(final)}
        s1loc = entity_locations(pred)
        for loc, ent in s1loc:
            cat = loc.split("[")[0]
            d = by_loc[loc]; all_facts += 1
            sel = {"decision": d["decision"], "reason": d["reason"], "segments": [int(x[3:]) - 1 for x in d["segments"]]}
            L.accumulate(C["R_cons"], cat, ent, enc, sel, set())
            for nm in ("R_simple", "R_main"):
                L.accumulate(C[nm], cat, ent, enc, R.run_ladder_step(nm, None, cat, ent, enc), set())
            reasons[(cat, d["reason"])] += 1
        # matched facts (strict TP) with a gold citation
        for c in CATEGORIES:
            m = match_category(entity_list(gold, c), entity_list(pred, c), c)
            ploc = {id(e): l for l, e in s1loc}
            for ge, pe in m["pairs"]:
                matched_total += 1
                l = ploc[id(pe)]; d = by_loc[l]
                cited_fact_match["cited" if d["decision"] == "cited" else "abstained"] += 1
                Gs = L.gold_set(seg_of, ge)
                if not Gs:
                    continue
                sel = {"decision": d["decision"], "reason": d["reason"], "segments": [int(x[3:]) - 1 for x in d["segments"]]}
                L.accumulate(A["R_cons"], c, pe, enc, sel, Gs)
                for nm in ("R_simple", "R_main"):
                    L.accumulate(A[nm], c, pe, enc, R.run_ladder_step(nm, None, c, pe, enc), Gs)
        # structural checks of the final evidence
        evl = final.get("clinical_evidence") or []
        loc_ent = dict(entity_locations(final))
        for r in evl:
            struct["records"] += 1
            hit = [i for i, s in enumerate(segs) if norm_text(r["transcript_text"]) == norm_text(s["text"]) and s["speaker_id"] == r["speaker_id"] and mm(s["start_seconds"]) == r["start_timestamp"]]
            if hit:
                s = segs[hit[0]]
                struct["records_fully_correct"] += (r["transcript_text"] == s["text"] and r["speaker_role"] == str(s["role"]).lower() and r["end_timestamp"] == mm(s["end_seconds"]))
            for sp in r.get("supports") or []:
                supp["supports_entries"] += 1
                ent = loc_ent.get(sp)
                supp["supports_reciprocal"] += ent is not None and r["evidence_id"] in (ent.get("evidence_ids") or [])
        struct["invalid_ids"] += dec["builder"]["ids_invalid"]
        struct["evidence_field_schema_violations"] += sum(1 for v in SV.validate(final).violations if "evidence" in v["message"] or "supports" in v["message"])
        struct["integrity_ok_records"] += bool(dec["builder"].get("integrity_identical_except_evidence_fields"))
        struct["records_evaluated"] += 1
        per_enc_records.append(len(evl))
    ag = ER.aggregate(results_final); gr = ag["evidence_grounding"]
    rA = {n: {"ALL": L.row(v["ALL"]), "by_group": L.group_rows(v), "by_category": {k: L.row(x) for k, x in v.items() if k != "ALL"}} for n, v in A.items()}
    rC = {n: {"ALL": L.row(v["ALL"]), "by_group": L.group_rows(v), "by_category": {k: L.row(x) for k, x in v.items() if k != "ALL"}} for n, v in C.items()}
    ext = prf(tot_s1["tp"], tot_s1["fp"], tot_s1["fn"])
    cons = rA["R_cons"]["ALL"]; simple = rA["R_simple"]["ALL"]; callrow = rC["R_cons"]["ALL"]
    gb, gs, gc, gg = GATES["behaviour_among_cited_facts"], GATES["agreement_with_gold_cited_segments_on_strictly_matched_facts"], GATES["coverage"], GATES["structure"]
    cnt = callrow["counts"]
    cited_n = callrow["cited"] or 1
    gates = {
        "extraction_counts_identical_to_stage1": tot_final == tot_s1,
        "builder_integrity_every_record": struct["integrity_ok_records"] == struct["records_evaluated"],
        "invalid_segment_ids": struct["invalid_ids"] <= gg["invalid_segment_ids_max"],
        "evidence_field_schema_violations": struct["evidence_field_schema_violations"] <= gg["evidence_field_schema_violations_max"],
        "records_text_speaker_role_time_correct": (struct["records_fully_correct"] / max(1, struct["records"])) >= gg["evidence_records_text_speaker_role_time_correct_min"],
        "supports_reciprocal": (supp["supports_reciprocal"] / max(1, supp["supports_entries"])) >= gg["supports_entries_reciprocal_min"],
        "question_only_citations": cnt["question_only"] <= gb["question_only_citations_max"],
        "kinship_conflicts": cnt["kin_conflict"] <= gb["kinship_conflicts_max"],
        "speaker_class_conflicts": cnt["speaker_class_conflict"] <= gb["speaker_class_conflicts_max"],
        "greeting_like_share": cnt["greeting_like"] / cited_n <= gb["greeting_like_share_max"],
        "polarity_conflict_share": cnt["polarity_conflict"] / cited_n <= gb["polarity_conflict_share_max"],
        "segment0_share": cnt["position0"] / cited_n <= gb["segment0_share_max"],
        "coverage_cited_share": callrow["coverage_cited_over_n"] >= gc["cited_share_of_extracted_facts_min"],
    }
    if cons["n"] >= gs["min_denominator_for_a_verdict"]:
        gates["hit_when_cited"] = (cons["hit_when_cited"] or 0) >= gs["hit_when_cited_min"]
        gates["hit_abstentions_as_misses_vs_R_simple"] = (100 * ((cons["hit_abstentions_as_misses"] or 0) - (simple["hit_abstentions_as_misses"] or 0))) >= gs["hit_abstentions_as_misses_min_relative_to_R_simple_pp"]
    else:
        gates["agreement_verdict"] = "INCONCLUSIVE (matched facts with a gold citation: %d < %d)" % (cons["n"], gs["min_denominator_for_a_verdict"])
    result = {
        "scope": scope, "records_evaluated": struct["records_evaluated"],
        "separately_reported": {
            "1_citation_coverage_all_extracted_facts": {"facts": callrow["n"], "cited": callrow["cited"], "coverage": callrow["coverage_cited_over_n"], "abstention_reasons": callrow["abstain_reasons"]},
            "2_agreement_with_gold_cited_segments_when_cited": {"matched_facts_with_gold_citation_denominator": cons["n"], "cited_among_them": cons["cited"], "hit_when_cited": cons["hit_when_cited"],
                                                               "matched_facts_total": matched_total, "matched_coverage_of_extracted_facts": round(matched_total / max(1, all_facts), 4)},
            "3_agreement_abstentions_counted_as_misses": cons["hit_abstentions_as_misses"],
            "4_human_review_semantic_correctness": "PENDING (audit plan: reports/12_P05_human_audit_plan.md); not computed here",
            "5_correctness_of_underlying_extracted_fact": {"strict_micro_P_R_F1_stage1": ext, "cited_facts_whose_fact_strictly_matches_gold": f"{cited_fact_match['cited']} of {callrow['cited']} cited facts",
                                                          "matched_facts_abstained": cited_fact_match["abstained"], "note": "evidence for a wrong fact is possible; coverage says nothing about fact correctness"},
        },
        "extraction_stage1_vs_final_strict_tp_fp_fn": {"stage1": dict(tot_s1), "final": dict(tot_final), "identical": tot_final == tot_s1},
        "matched_facts_R_cons": rA["R_cons"], "matched_facts_R_simple": rA["R_simple"], "matched_facts_R_main": rA["R_main"], "all_facts_R_cons": rC["R_cons"], "all_facts_R_simple_behaviour": rC["R_simple"]["ALL"], "all_facts_R_main_behaviour": rC["R_main"]["ALL"],
        "structure": {**dict(struct), "supports": dict(supp), "evidence_records_per_encounter": {"mean": round(sum(per_enc_records) / max(1, len(per_enc_records)), 2), "min": min(per_enc_records or [0]), "max": max(per_enc_records or [0])}},
        "evaluator_lexical_grounding_circular_not_correctness": {k: gr[k] for k in ("grounded_strict", "grounded_lenient", "partially_supported", "unsupported", "total")}, "speaker_attribution_unchanged_by_evidence": ag["speaker_attribution"]["accuracy"],
        "gates": {k: (v if isinstance(v, str) else bool(v)) for k, v in gates.items()}, "all_gates_pass": all(v is True for v in gates.values()),
        "stage1_valid_json": (sum(r["status"] == "parsed" for r in stage1_manifest.values()) if stage1_manifest else None)}
    write_json(out_dir / "p05_evaluation.json", result)
    print(json.dumps({k: result[k] for k in ("scope", "records_evaluated", "separately_reported", "gates", "all_gates_pass")}, indent=1, ensure_ascii=False))
    return result


with G.StrictAccessSpy(allow_validation=(scope == "validation")) as spy:
    main()
write_json(out_dir / "evaluation_file_access_audit.json", spy.report())
assert not G.locked_test_accesses(spy.opened)
