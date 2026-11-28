"""Batch 002 structural audit: the checks of scripts/final_schema_audit.py (copied verbatim; that script is left untouched because it hard-codes
500 records and Batch 001 blueprints) applied to encounters 00501-01000.  The only change is the allergy-representation check, which in Batch 001
is compared with a blueprint; here it is checked for internal consistency with the schema's `allergy_representation` rules.
usage: python audit_batch_002.py [--data-root DIR] [--start 501 --end 1000] [--write FILE]"""
import argparse
import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "validation"))
import validate_dataset as VD  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--data-root", default=str(ROOT))
ap.add_argument("--start", type=int, default=501)
ap.add_argument("--end", type=int, default=1000)
ap.add_argument("--write", default=None)
A = ap.parse_args()
DATA = Path(A.data_root)
S = json.loads((ROOT / "schema" / "final_label_schema.json").read_text(encoding="utf-8"))
ROLES = set(S["roles"])
fails = collections.defaultdict(list)
checks = collections.Counter()


def check(name, ok, msg=""):
    checks[name] += 1
    if not ok:
        fails[name].append(msg)


def jl(p):
    return json.loads(p.read_text(encoding="utf-8"))


def getlist(l, cat):
    o = l
    for part in cat.split("."):
        o = o[part]
    return o


def loc_resolve(l, loc):
    return VD.resolve(l, loc)


ids = [f"{i:05d}" for i in range(A.start, A.end + 1)]
labels = {i: jl(DATA / "output/labels" / f"encounter_{i}.json") for i in ids if (DATA / "output/labels" / f"encounter_{i}.json").exists()}
inputs = {i: jl(DATA / "output/inputs" / f"encounter_{i}.json") for i in ids if (DATA / "output/inputs" / f"encounter_{i}.json").exists()}
check("file_counts_and_pairing", set(labels) == set(inputs), f"{len(labels)} labels / {len(inputs)} inputs")
check("validator_key_sets_match_schema", all(VD.EXPECT[c] == set(v["keys"]) for c, v in S["categories"].items()), "EXPECT differs from schema")
check("validator_enums_match_schema", VD.ENUMS == {k: set(v) for k, v in S["enums"].items()}, "ENUMS differ")
check("validator_top_keys_match_schema", VD.TOP_KEYS == S["top_level_keys"], "TOP_KEYS differ")

observed = collections.defaultdict(collections.Counter)
CONTRA = {"conflicting_statement", "medication_discrepancy", "allergy_disputed", "duration_disagreement"}
UNC_TARGET = {"allergy_uncertain": {"allergies"}, "allergy_disputed": {"allergies", "negative_findings"},
              "medication_discrepancy": {"medications"}, "uncertain_dose": {"medications"}, "adherence_uncertain": {"medications"},
              "incomplete_medication_name": {"medications"}, "date_uncertain": {"symptoms"}, "duration_disagreement": {"symptoms"},
              "unknown_speaker": {"symptoms"}, "conflicting_statement": {"symptoms", "negative_findings"}}
allergy_rep = collections.Counter()
for eid, l in labels.items():
    inp = inputs[eid]
    check("top_level_keys_exact", list(l.keys()) == S["top_level_keys"], eid)
    check("ids_match", l["encounter_id"] == inp["encounter_id"] == eid, eid)
    # ---- key sets (every nesting level)
    check("medical_history_keys", list(l["medical_history"].keys()) == S["nested_keys"]["medical_history"], eid)
    check("metadata_keys", list(l["encounter_metadata"].keys()) == S["nested_keys"]["encounter_metadata"], eid)
    check("quality_keys", list(l["quality_checks"].keys()) == S["nested_keys"]["quality_checks"], eid)
    for sp in l["encounter_metadata"]["primary_speakers"]:
        check("speaker_keys", list(sp.keys()) == S["nested_keys"]["primary_speakers"] and sp["role"] in ROLES, eid)
    for ev in l["clinical_evidence"]:
        check("evidence_keys", list(ev.keys()) == S["nested_keys"]["clinical_evidence"] and ev["speaker_role"] in ROLES, eid)
    for cat, spec in S["categories"].items():
        ents = [l[cat]] if cat == "chief_complaint" else getlist(l, cat)
        for e in ents:
            check(f"keys:{cat}", set(e) == set(spec["keys"]), f"{eid} {cat} {set(e) ^ set(spec['keys'])}")
            for rk in ("reported_by", "observed_by", "stated_by", "requested_by", "responsible_person"):
                if e.get(rk) is not None and rk != "responsible_person" and rk != "requested_by":
                    check("role_values", e[rk] in ROLES, f"{eid} {cat}.{rk}={e[rk]}")
            for dk in ("duration",):
                if e.get(dk):
                    check("duration_keys", list(e[dk]) == S["nested_keys"]["duration"], eid)
            if cat == "clinical_actions" and e["time_reference"]:
                check("time_reference_keys", list(e["time_reference"]) == S["nested_keys"]["time_reference"], eid)
    # ---- enums
    for epath, allowed in S["enums"].items():
        if epath in ("extraction_status",):
            vals = [l["extraction_status"]]
        elif epath == "encounter_metadata.encounter_type":
            vals = [l["encounter_metadata"]["encounter_type"]]
        else:
            cat = max((c for c in S["categories"] if epath.startswith(c + ".")), key=len)
            field = epath[len(cat) + 1:]
            vals = [e.get(field) for e in getlist(l, cat)]
        for v in vals:
            observed[epath][v] += 1
            check(f"enum:{epath}", v in allowed or (epath == "medications.route" and v is None), f"{eid} {v!r}")
    # ---- confidence null, no unapproved fields anywhere
    def walk(o, path=""):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in ("confidence", "role_confidence"):
                    check("confidence_null", v is None, f"{eid}{path}.{k}={v}")
                check("no_confirmed_by", k != "confirmed_by", eid)
                walk(v, f"{path}.{k}")
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, f"{path}[{i}]")
    walk(l)
    # ---- conditional vs planned vs completed
    acts, procs = l["clinical_actions"], l["procedures_and_investigations"]
    ev = {r["evidence_id"]: r for r in l["clinical_evidence"]}
    txt = lambda e: " ".join(ev[i]["transcript_text"].lower() for i in e["evidence_ids"])
    for a in acts:
        if a["status"] == "conditional":
            check("conditional_action_type", a["action_type"] in ("investigation", "follow_up"), f"{eid} {a['action_type']}")
            if a["action_type"] == "investigation":
                check("conditional_action_has_entity", any(p["status"] == "conditional" and set(p["evidence_ids"]) & set(a["evidence_ids"]) for p in procs), eid)
            else:
                check("conditional_followup_matches", any(f["status"] == "conditional" and f["time_reference"].startswith("if ") for f in l["follow_up"]), eid)
        if a["status"] == "completed":
            check("completed_action_is_nurse_done", a["action_type"] == "investigation" and a["responsible_person"] == "nurse", f"{eid} {a['description']}")
        if a["status"] == "recommended":
            check("recommended_not_order", a["action_type"] in ("counselling", "other") and a["responsible_person"] == "patient", f"{eid} {a['action_type']}")
        if a["status"] == "planned":
            toks = [w[:5] for w in re.findall(r"[a-z]{5,}", a["description"].lower()) if w not in ("arrange", "refer", "start", "follow", "consultation", "advise", "avoid")]
            bad = [x for x in re.split(r"(?<=[.!?])\s+", txt(a)) if re.search(r"hold off|not ordering|if it hasn't settled|we might do if|not now", x) and any(t in x for t in toks)]
            check("planned_not_conditional_text", not bad, f"{eid} {a['description']}")
    for p in procs:
        if p["status"] == "conditional":
            check("conditional_proc_fields", p["scheduled_datetime"] is None and p["requested_by"] == "doctor", eid)
            check("conditional_proc_has_action", any(a["status"] == "conditional" and a["action_type"] == "investigation" and set(a["evidence_ids"]) & set(p["evidence_ids"]) for a in acts), eid)
        if p["status"] == "planned":
            check("planned_proc_has_planned_action", any(a["status"] == "planned" and a["action_type"] == "investigation" and set(a["evidence_ids"]) & set(p["evidence_ids"]) for a in acts), eid)
        if p["status"] == "completed":
            check("completed_proc_wording", bool(re.search(r"\b(did|already|had)\b", txt(p))), eid)
    for f in l["follow_up"]:
        check("followup_status_matches_text", (f["status"] == "conditional") == f["time_reference"].startswith("if "), eid)
    for m in l["medications"]:
        if m["status"] == "planned":
            check("planned_med_has_action", any(a["action_type"] == "medication" and a["status"] == "planned" and set(a["evidence_ids"]) & set(m["evidence_ids"]) for a in acts), eid)
    # ---- allergy representation
    nk = [n for n in l["negative_findings"] if n["finding"] == "Allergies"]
    al = l["allergies"]
    mentioned = any("allerg" in s["text"].lower() for s in inp["segments"])
    st = {a["status"] for a in al}
    uncs = {u["type"] for u in l["clinical_uncertainties"]}
    if not al:
        ok = (len(nk) == 1 and mentioned) if nk else (not mentioned)       # explicit "no known allergies" or genuinely not discussed
    else:
        ok = (mentioned and st <= {"reported", "uncertain", "historical", "disputed"}
              and ("uncertain" not in st or "allergy_uncertain" in uncs)
              and ("disputed" not in st or (len(nk) == 1 and "allergy_disputed" in uncs)))
    check("allergy_representation_consistent", bool(ok), f"{eid} nk={len(nk)} allergies={sorted(st)} mentioned={mentioned}")
    allergy_rep["explicit_no_known_allergies" if (nk and not al) else "not_discussed" if not al else "+".join(sorted(st))] += 1
    check("no_nk_and_allergy_unless_disputed", not (nk and al) or "allergy_disputed" in uncs, eid)
    check("nk_requires_discussion", not nk or mentioned, eid)
    # ---- uncertainty references
    contra_types = 0
    for u in l["clinical_uncertainties"]:
        check("unc_evidence_nonempty", bool(u["evidence_ids"]), eid)
        check("unc_related_nonempty", bool(u["related_entities"]), eid)
        paths = set()
        for r in u["related_entities"]:
            ent = loc_resolve(l, r)
            check("unc_related_resolves", ent is not None, f"{eid} {r}")
            paths.add(r.split("[")[0])
        check("unc_target_type", paths <= UNC_TARGET[u["type"]], f"{eid} {u['type']} -> {paths}")
        if u["type"] == "allergy_disputed":
            rel = u["related_entities"]
            check("allergy_disputed_links_both", any(r.startswith("negative_findings") and loc_resolve(l, r)["finding"] == "Allergies" for r in rel)
                  and any(r.startswith("allergies") and loc_resolve(l, r)["status"] == "disputed" for r in rel), eid)
        if u["type"] == "allergy_uncertain":
            check("allergy_uncertain_status", all(loc_resolve(l, r)["status"] == "uncertain" for r in u["related_entities"]), eid)
        if u["type"] == "conflicting_statement":
            check("conflict_links_disputed_symptom", any(r.startswith("symptoms") and loc_resolve(l, r)["certainty"] == "disputed" for r in u["related_entities"]), eid)
        if u["type"] == "duration_disagreement":
            d = loc_resolve(l, u["related_entities"][0])["duration"]
            check("duration_disagreement_shape", d is not None and d["value"] is None and d["normalized"].startswith("approximately "), eid)
            check("duration_disagreement_status", u["resolution_status"] == "partially_resolved", eid)
        if u["type"] == "medication_discrepancy":
            check("discrepancy_dose_null", all(loc_resolve(l, r)["dose"] is None for r in u["related_entities"]), eid)
        if u["type"] in CONTRA:
            contra_types += 1
    check("contradictions_line_per_conflict", len(l["quality_checks"]["contradictions_detected"]) == contra_types, f"{eid} {len(l['quality_checks']['contradictions_detected'])} vs {contra_types}")
    for r in l["quality_checks"]["ambiguous_entities"]:
        check("ambiguous_resolves", loc_resolve(l, r) is not None, f"{eid} {r}")
    # disputed symptoms need an uncertainty
    for i, s in enumerate(l["symptoms"]):
        if s["certainty"] == "disputed":
            check("disputed_symptom_has_uncertainty", any(f"symptoms[{i}]" in u["related_entities"] and u["type"] == "conflicting_statement" for u in l["clinical_uncertainties"]), eid)
            check("disputed_symptom_third_party", s["reported_by"] in ("caregiver", "family_member"), eid)
    # allergies reference-only fields
    for a in al:
        check("allergy_severity_unknown", a["severity"] == "unknown", eid)
        check("allergy_reaction_null_when_disputed_or_uncertain", a["status"] not in ("disputed", "uncertain") or a["reaction"] is None, eid)


pair_fail = 0
for eid in labels:
    R = VD.validate_record(inputs[eid], labels[eid])
    if R.errors:
        pair_fail += 1
        fails["validator_pair"].append(f"{eid}: {R.errors[0]['message'][:100]}")
checks["validator_pair"] = len(labels)
report = {"audit": "Batch 002 structural audit (automated)", "records": len(labels), "checks_run": dict(checks), "total_check_evaluations": sum(checks.values()),
          "failures": {k: v[:10] for k, v in fails.items()}, "failure_count": sum(len(v) for v in fails.values()), "pairs_failing_validator": pair_fail,
          "observed_enum_values": {k: dict(v) for k, v in observed.items()}, "allergy_representation_counts": dict(allergy_rep),
          "status": "PASS" if not fails else "FAIL"}
if A.write:
    Path(A.write).write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
print(json.dumps({k: report[k] for k in ("records", "total_check_evaluations", "failure_count", "pairs_failing_validator", "status", "allergy_representation_counts")}, indent=1))
for k, v in fails.items():
    print(k, len(v), v[:5])
sys.exit(0 if not fails else 1)
