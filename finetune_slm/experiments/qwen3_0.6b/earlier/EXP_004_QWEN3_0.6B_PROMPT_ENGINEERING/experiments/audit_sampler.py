"""EXP_004 P05 human-audit sampler and packet builder. NO LABELS are used: the sample is drawn from the system's own decisions (cited / abstained, reason, group) with a fixed seed, so it cannot be selected on correctness.
usage: audit_sampler.py <scope> <run_dir> <stage1_parsed_dir> <seed> <out_dir>
  30 cited facts stratified over the clinical groups, 15 abstained facts stratified over the abstention reasons (shortfalls are redistributed deterministically).
Outputs: audit_key.json (system status - kept by the study team), phase1_blinded_packet.md + phase1_responses_template.csv (facts and full transcripts only: the reviewer does not see citations or abstentions),
         phase2_unblinded_packet.md + phase2_responses_template.csv (the system's citation or abstention shown), reviewer_form.md.
Run on the validation outputs only AFTER the validation run and only with the recorded authorisation (validation transcripts are read). A pilot on prompt_dev outputs tests the format."""
import csv
import json
import random
import sys
from pathlib import Path

from common import EXP4, S, SPLIT, write_json
import dev_guard as G
import p05_eval_lib as L

scope, run_dir, stage1_dir, seed, out_dir = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3]), int(sys.argv[4]), Path(sys.argv[5])
IDS = {"prompt_dev": SPLIT["prompt_dev_ids"], "validation": SPLIT["validation_ids"]}[scope]
if scope == "validation" and not G.validation_authorized():
    print("STOP: validation not authorised"); sys.exit(3)
G.install(IDS, include_labels=False, allow_validation=(scope == "validation"))
out_dir.mkdir(parents=True, exist_ok=True)
CITED_ALLOC = {"positive findings (chief complaint, symptoms, conditions)": 4, "negative findings": 4, "medications": 3, "allergies": 2, "vital signs": 3, "family history": 3, "surgical history": 2,
               "assessment, procedures and clinical actions": 5, "other (past history, social history, exam, review of systems, follow-up, uncertainties)": 4}
ABST_ALLOC = {"no_candidate": 4, "speaker_class_mismatch": 3, "polarity_conflict": 3, "ambiguous_many_equal_matches": 3, "other": 2}
GROUP_OF = {c: g for g, cats in L.GROUPS.items() if not g.startswith("speaker-sensitive") for c in cats}
SKIP = {"evidence_ids", "confidence", "source_segments"}


def fact_text(ent):
    parts = []
    for k, v in ent.items():
        if k in SKIP or v in (None, "", [], {}) or isinstance(v, (dict, list)):
            continue
        parts.append(f"{k}: {v}")
    return "; ".join(parts)


def main():
    pools_c, pools_a, transcripts = {}, {}, {}
    from evidence_builder import entity_locations
    for eid in IDS:
        dp = run_dir / "decisions" / f"encounter_{eid}.json"
        if not dp.exists():
            continue
        dec = json.loads(dp.read_text(encoding="utf-8"))["decisions"]
        pred = json.loads((stage1_dir / f"encounter_{eid}.json").read_text(encoding="utf-8"))
        ent = dict(entity_locations(pred))
        transcripts[eid] = json.loads((S.INPUT_DIR / f"encounter_{eid}.json").read_text(encoding="utf-8"))["segments"]
        for d in dec:
            rec = {"encounter_id": eid, "location": d["location"], "category": d["category"], "group": GROUP_OF.get(d["category"], "other (past history, social history, exam, review of systems, follow-up, uncertainties)"),
                   "fact": fact_text(ent[d["location"]]), "decision": d["decision"], "reason": d["reason"], "segments": d["segments"], "context_question_added": d["context_question_added"]}
            (pools_c if d["decision"] == "cited" else pools_a).setdefault(rec["group"] if d["decision"] == "cited" else (rec["reason"] if rec["reason"] in ABST_ALLOC else "other"), []).append(rec)
    rng = random.Random(seed)

    def draw(pools, alloc, total):
        for k in pools:
            pools[k].sort(key=lambda r: (r["encounter_id"], r["location"]))
        chosen, taken = [], {k: 0 for k in alloc}
        for k, n in alloc.items():
            pool = pools.get(k, [])
            pick = rng.sample(pool, min(n, len(pool))); chosen += pick; taken[k] = len(pick)
        # redistribute shortfall deterministically over the remaining facts of the pools (round robin in sorted key order)
        need = total - len(chosen)
        rest = [r for k in sorted(pools) for r in pools[k] if r not in chosen]
        rng.shuffle(rest)
        chosen += rest[:max(0, need)]
        return chosen
    cited = draw(pools_c, CITED_ALLOC, 30); abst = draw(pools_a, ABST_ALLOC, 15)
    sample = cited + abst
    rng.shuffle(sample)
    for i, r in enumerate(sample, 1):
        r["fact_id"] = f"A{i:02d}"
    write_json(out_dir / "audit_key.json", {"scope": scope, "seed": seed, "n_cited": len(cited), "n_abstained": len(abst), "items": sample, "note": "KEY - do not give to the reviewer before phase 1 is complete"})
    enc_ids = sorted({r["encounter_id"] for r in sample})

    def transcript_md():
        out = ["## Transcripts (segment id | speaker | role | text)\n"]
        for eid in enc_ids:
            out.append(f"### Encounter {eid}\n")
            for s in transcripts[eid]:
                out.append(f"- {s['segment_id']} | {s['speaker_id']} | {s['role']} | {s['text']}")
            out.append("")
        return "\n".join(out)
    p1 = ["# Phase 1 (BLIND): does the transcript support each extracted fact?\n", "You are shown extracted facts (in random order) and the full transcripts. You are NOT shown any system citation. For each fact answer in `phase1_responses_template.csv`:",
          "- `supported` yes / partly / no / cannot_tell  (is the fact stated in the transcript, with correct polarity and for the right person?)", "- `supporting_segments` the segment id(s) YOU consider the best evidence (blank if none)",
          "- `speaker_ok` yes/no/na (is the fact attributed to the right speaker?)  - `polarity_ok` yes/no/na (negation/denial handled correctly?)  - `attribution_ok` yes/no/na (patient's own condition vs family member's, etc.)  - `comment`\n"]
    for r in sample:
        p1.append(f"- **{r['fact_id']}** (encounter {r['encounter_id']}, {r['category']}): {r['fact']}")
    (out_dir / "phase1_blinded_packet.md").write_text("\n".join(p1) + "\n\n" + transcript_md(), encoding="utf-8")
    with open(out_dir / "phase1_responses_template.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["fact_id", "supported", "supporting_segments", "speaker_ok", "polarity_ok", "attribution_ok", "comment"])
        for r in sample:
            w.writerow([r["fact_id"], "", "", "", "", "", ""])
    p2 = ["# Phase 2 (UNBLINDED): the system's citation or abstention\n", "Complete only after Phase 1. For CITED facts judge the selected segment(s); for ABSTAINED facts judge whether usable evidence existed (compare with your Phase 1 answer).",
          "Columns in `phase2_responses_template.csv`: `relevant` yes/partly/no (cited), `supports` yes/partly/no (cited), `speaker_ok`, `polarity_ok`, `context_ok` (is a needed question included / is an unnecessary question included?), `family_attribution_ok`, `abstention_justified` yes/no (abstained: no usable evidence existed), `comment`.\n"]
    for r in sample:
        segs = r["segments"]
        tx = {s["segment_id"]: s for s in transcripts[r["encounter_id"]]}
        if r["decision"] == "cited":
            body = " || ".join(f"{x} [{tx[x]['speaker_id']}/{tx[x]['role']}] {tx[x]['text']}" for x in segs)
            p2.append(f"- **{r['fact_id']}** {r['category']}: {r['fact']}\n  - SYSTEM CITED: {body}" + ("  (question added as context)" if r["context_question_added"] else ""))
        else:
            p2.append(f"- **{r['fact_id']}** {r['category']}: {r['fact']}\n  - SYSTEM ABSTAINED (reason: {r['reason']})")
    (out_dir / "phase2_unblinded_packet.md").write_text("\n".join(p2) + "\n", encoding="utf-8")
    with open(out_dir / "phase2_responses_template.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["fact_id", "relevant", "supports", "speaker_ok", "polarity_ok", "context_ok", "family_attribution_ok", "abstention_justified", "comment"])
        for r in sample:
            w.writerow([r["fact_id"], "", "", "", "", "", "", "", ""])
    (out_dir / "reviewer_form.md").write_text("# Reviewer form\n\nName / role: ______   Clinical qualification (e.g. physician, nurse, clinical-documentation specialist; years): ______\nInvolved in designing or tuning R_cons v4 or the extraction prompts? yes / no (must be no for an independent review): ______\nConflicts of interest: ______\n"
                                               "Time spent: ______\n\nStatement: this is a limited feasibility review of 45 facts, not clinical validation. If the reviewer is not a clinician or documentation specialist, or was involved in the design, the audit is reported as a limited review by a non-independent / non-clinical reviewer.\n", encoding="utf-8")
    print(json.dumps({"cited": len(cited), "abstained": len(abst), "encounters": len(enc_ids), "by_group": {g: sum(1 for r in cited if r["group"] == g) for g in CITED_ALLOC}, "abstain_by_reason": {k: sum(1 for r in abst if (r["reason"] if r["reason"] in ABST_ALLOC else "other") == k) for k in ABST_ALLOC}}, indent=1))


with G.StrictAccessSpy(allow_validation=(scope == "validation")) as spy:
    main()
write_json(out_dir / "sampler_file_access_audit.json", spy.report())
assert not G.locked_test_accesses(spy.opened) and not spy.label_or_blueprint_accesses()
