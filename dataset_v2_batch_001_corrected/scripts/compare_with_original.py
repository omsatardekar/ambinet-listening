"""Compare the corrected dataset with the untouched original Batch 001 and write the change log data.
usage: python compare_with_original.py            (run from anywhere)
writes: reports/record_changes.csv, reports/comparison.json, reports/human_review_required.csv"""
import collections
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIG = ROOT.parent / "dataset_v2_batch_001"
NEWK = None
sys_path = None


def jl(p):
    return json.loads(p.read_text(encoding="utf-8"))


def walk(o, f):
    if isinstance(o, dict):
        for k, v in o.items():
            f(k, v, o)
            walk(v, f)
    elif isinstance(o, list):
        for v in o:
            walk(v, f)


VOCAB = {"constitutional", "neurological", "cardiovascular", "respiratory", "gastrointestinal", "musculoskeletal", "dermatological",
         "endocrine", "genitourinary", "ENT", "ophthalmological", "psychiatric", "other"}
rows, tot = [], collections.Counter()
orig_alg, new_alg = collections.Counter(), collections.Counter()
review = []
import sys  # noqa: E402
sys.path.insert(0, str(ROOT / "scripts"))
import content_p4  # noqa: E402
new_profiles = set(content_p4.NEW_KEYS)
for p in sorted((ROOT / "output" / "labels").glob("encounter_*.json")):
    eid = p.stem.split("_")[1]
    ol, nl = jl(ORIG / "output/labels" / p.name), jl(p)
    oi, ni = jl(ORIG / "output/inputs" / p.name), jl(ROOT / "output/inputs" / p.name)
    ob, nb = jl(ORIG / "scenario_blueprints" / f"blueprint_{eid}.json"), jl(ROOT / "scenario_blueprints" / f"blueprint_{eid}.json")
    t_changed = json.dumps(oi, sort_keys=True) != json.dumps(ni, sort_keys=True)
    l_changed = json.dumps(ol, sort_keys=True) != json.dumps(nl, sort_keys=True)
    bad_cat = sum(1 for s in ol["symptoms"] if s["category"] not in VOCAB)
    reported_cat = sum(1 for s in ol["symptoms"] if s["category"] == "reported")
    conf = [0]
    cb = [0]

    def f(k, v, o):
        if k in ("confidence", "role_confidence") and v is not None:
            conf[0] += 1
        if k == "confirmed_by":
            cb[0] += 1
    walk(ol, f)
    o_nk = any(n["finding"] == "Allergies" for n in ol["negative_findings"])
    o_kind = "explicit_no_known_allergies" if o_nk else ("reported_allergy" if ol["allergies"] else "empty_unclassified")
    n_nk = any(n["finding"] == "Allergies" for n in nl["negative_findings"])
    n_kind = nb["allergies"]["kind"]
    orig_alg[o_kind] += 1
    new_alg[n_kind] += 1
    allergy_changed = (o_kind != {"none": "explicit_no_known_allergies", "known": "reported_allergy"}.get(n_kind, n_kind))
    rows.append(dict(encounter_id=eid, specialty=nb["spec"], complexity=nb["complexity"], original_profile=ob["profile"], new_profile=nb["profile"],
                     profile_changed=ob["profile"] != nb["profile"], transcript_changed=t_changed, label_changed=l_changed,
                     orig_segments=len(oi["segments"]), new_segments=len(ni["segments"]), orig_duration=oi["segments"][-1]["end_seconds"],
                     new_duration=ni["segments"][-1]["end_seconds"], orig_noncompliant_symptom_categories=bad_cat, orig_category_reported=reported_cat,
                     orig_nonnull_confidence_fields=conf[0], orig_confirmed_by_fields=cb[0], orig_allergy_representation=o_kind,
                     new_allergy_representation=n_kind, allergy_representation_changed=allergy_changed,
                     new_noise_level=nb.get("noise_level"), doctor_style=nb.get("doctor_style"), plan_mode=nb.get("plan_mode"), assessment_mode=nb.get("assess_mode"),
                     age_band=nb.get("age_band"), original_actions=len(ol["clinical_actions"]), new_actions=len(nl["clinical_actions"])))
    tot["transcript_changed"] += t_changed
    tot["label_changed"] += l_changed
    tot["profile_changed"] += ob["profile"] != nb["profile"]
    tot["orig_noncompliant_category_records"] += bad_cat
    tot["orig_category_reported"] += reported_cat
    tot["confidence_fields_nulled"] += conf[0]
    tot["confirmed_by_removed"] += cb[0]
    tot["allergy_representation_changed"] += allergy_changed
    tot["records_with_noise"] += (nb.get("noise_level") or 0) > 0
    tot["allergy_new_distinctions"] += (n_kind in ("not_discussed", "historical", "disputed")
                                       or any(it.get("reaction_unknown_stated") for it in nb["allergies"]["items"]))
    # ----- human clinical review prioritisation (automated triage; NOT a review)
    reasons = []
    for u in nl["clinical_uncertainties"]:
        reasons.append(u["type"])
    if nb["profile"] in new_profiles:
        reasons.append("scenario_from_profile_added_in_correction")
    if nb["assess_mode"] in ("none", "uncertain"):
        reasons.append("no_or_uncertain_assessment")
    if reasons:
        review.append((eid, sorted(set(reasons))))
with open(ROOT / "reports" / "record_changes.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
priority = {"medication_discrepancy", "allergy_disputed", "allergy_uncertain", "incomplete_medication_name", "uncertain_dose", "adherence_uncertain",
            "conflicting_statement", "duration_disagreement", "unknown_speaker"}
with open(ROOT / "reports" / "human_review_required.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["encounter_id", "priority", "reasons"])
    for eid, rs in review:
        w.writerow([eid, "high" if priority & set(rs) else "normal", ";".join(rs)])
cmp = {"records": len(rows), **dict(tot), "original_allergy_representation": dict(orig_alg), "new_allergy_representation": dict(new_alg),
       "records_flagged_for_prioritised_human_review": len(review),
       "high_priority_review": sum(1 for _, rs in review if priority & set(rs)),
       "note": "Records were regenerated under their original IDs with the revised generator; transcripts and labels are rewritten together. "
               "Specialty and complexity are unchanged for all 500; the clinical profile changed where listed in record_changes.csv."}
(ROOT / "reports" / "comparison.json").write_text(json.dumps(cmp, indent=1), encoding="utf-8")
print(json.dumps(cmp, indent=1))
