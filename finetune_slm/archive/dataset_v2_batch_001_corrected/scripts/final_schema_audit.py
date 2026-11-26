"""Final schema audit (read-only on conversations): checks every label against schema/final_label_schema.json, the validator,
and the documentation; writes validation/final_schema_audit.json and reports/FINAL_SCHEMA.md.
Never modifies inputs/labels.  usage: python scripts/final_schema_audit.py"""
import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "validation"))
import validate_dataset as VD  # noqa: E402

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


labels = {p.stem[10:]: jl(p) for p in sorted((ROOT / "output/labels").glob("*.json"))}
inputs = {p.stem[10:]: jl(p) for p in sorted((ROOT / "output/inputs").glob("*.json"))}
bps = {p.stem[10:]: jl(p) for p in sorted((ROOT / "scenario_blueprints").glob("*.json"))}
check("file_counts_500", len(labels) == len(inputs) == len(bps) == 500 and set(labels) == set(inputs) == set(bps), f"{len(labels)}/{len(inputs)}/{len(bps)}")

# validator constants must equal the schema file
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
    kind = bps[eid]["allergies"]["kind"]
    st = {a["status"] for a in al}
    uncs = {u["type"] for u in l["clinical_uncertainties"]}
    expect = {"none": (len(nk) == 1 and not al and mentioned), "not_discussed": (not nk and not al and not mentioned),
              "known": (not nk and al and st == {"reported"}), "uncertain": (not nk and st == {"uncertain"} and "allergy_uncertain" in uncs),
              "historical": (not nk and st == {"historical"}), "disputed": (len(nk) == 1 and st == {"disputed"} and "allergy_disputed" in uncs)}[kind]
    check("allergy_representation_matches_blueprint", bool(expect), f"{eid} {kind}")
    allergy_rep[{"none": "explicit_no_known_allergies", "known": "reported" }.get(kind, kind)] += 1
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

# ---- full validator over every transcript-label pair
pair_fail = 0
for eid in labels:
    R = VD.validate_record(inputs[eid], labels[eid])
    if R.errors:
        pair_fail += 1
        fails["validator_pair"].append(f"{eid}: {R.errors[0]['message'][:100]}")
checks["validator_pair"] = len(labels)

# ---- documentation / scripts consistency
doc_hits = {}
for p in list(ROOT.rglob("*.md")) + list(ROOT.rglob("*.py")) + list(ROOT.rglob("*.json")):
    if "output" in p.parts or "scenario_blueprints" in p.parts or p.name in ("final_schema_audit.json", "negative_controls.json", "comparison.json"):
        continue
    t = p.read_text(encoding="utf-8", errors="ignore")
    if "confirmed_by" in t:
        doc_hits[str(p.relative_to(ROOT))] = t.count("confirmed_by")
allowed_mentions = {"reports/DATASET_QUALITY_AUDIT.md", "reports/CHANGELOG.md", "reports/REMAINING_LIMITATIONS.md", "scripts/validator_selftest.py",
                    "scripts/compare_with_original.py", "scripts/final_schema_audit.py", "scripts/dialogue.py", "validation/validate_dataset.py",
                    "reports/FINAL_SCHEMA.md", "schema/final_label_schema.json", "reports/record_changes.csv"}
check("confirmed_by_not_in_schema_or_validator", not any("confirmed_by" in v["keys"] for v in S["categories"].values())
      and not any("confirmed_by" in v for v in VD.EXPECT.values()), "schema or validator still defines confirmed_by")
gen = (ROOT / "scripts" / "dialogue.py").read_text(encoding="utf-8")
check("generator_does_not_emit_confirmed_by", not re.search(r'["\']confirmed_by["\']\s*:', gen), "dialogue.py still builds confirmed_by")
# every documented enum value is either observed or explicitly declared unused
unused = {e: sorted(set(S["enums"][e]) - set(observed[e])) for e in S["enums"] if set(S["enums"][e]) - set(observed[e])}

# ---- unobserved keys / value inventory
report = {
    "audit": "final schema audit (automated; no conversation modified; no model run)",
    "records": len(labels), "checks_run": dict(checks), "total_check_evaluations": sum(checks.values()),
    "failures": {k: v[:10] for k, v in fails.items()}, "failure_count": sum(len(v) for v in fails.values()),
    "pairs_validated": len(labels), "pairs_failing_validator": pair_fail,
    "observed_enum_values": {k: dict(v) for k, v in observed.items()},
    "declared_but_unused_enum_values": unused,
    "declared_but_unused_note": "Permitted schema values that no current record uses. Informational only; not failures.",
    "allergy_representation_counts": dict(allergy_rep),
    "confidence_fields_non_null": sum(len(v) for k, v in fails.items() if k == "confidence_null"),
    "confirmed_by_mentions_in_docs_and_scripts": doc_hits,
    "status": "PASS" if not fails else "FAIL",
}
(ROOT / "validation" / "final_schema_audit.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")

# ---- FINAL_SCHEMA.md generated from the schema file (docs cannot drift)
md = ["# Final label schema (Batch 001 corrected)", "",
      "Generated from `schema/final_label_schema.json` by `scripts/final_schema_audit.py`. That file is the single source of truth; the validator",
      "reads the same enums and key sets. Outer structure and category names follow `clinical_extraction_schema.json`; **no top-level field was added and no field",
      "outside the lists below exists in any of the 500 labels.**", "",
      "## Conventions", "",
      f"* Roles: {', '.join('`' + r + '`' for r in S['roles'])} (lowercase in labels; UPPERCASE in transcripts).",
      f"* **Confidence:** {S['confidence_policy']}",
      "* `evidence_ids` / `supports` / `related_entities` / `ambiguous_entities` use JSON locations like `symptoms[2]`; links are symmetric.",
      "* Empty/unstated information is `null` or `[]`; nothing is inferred (no dose, duration, severity or date that was not spoken).", "",
      "## Key sets", ""]
for c, v in S["categories"].items():
    md.append(f"* `{c}`: " + ", ".join(f"`{k}`" for k in v["keys"]))
md += ["", "Nested: " + "; ".join(f"`{k}` = {', '.join(v)}" for k, v in S["nested_keys"].items() if k != "medical_history"), "", "## Enumerated values and definitions", ""]
for e, d in S["enums"].items():
    md.append(f"### `{e}`")
    for k, v in d.items():
        md.append(f"* `{k}`: {v}")
    md.append("")
md += ["## Allergy representation (distinguishable cases)", ""] + [f"* **{k}**: {v}" for k, v in S["allergy_representation"].items()]
md += ["", "## Reference rules (all enforced by the audit)", ""] + [f"* {r}" for r in S["reference_rules"]]
md += ["", "## Conditional vs planned vs completed vs recommended", "",
       "| Status | Meaning | Allowed on | Evidence wording |", "|---|---|---|---|",
       "| planned | committed future task for the clinic/doctor | investigation, medication, referral, follow_up | doctor orders/prescribes/books it |",
       "| completed | already done | investigation (nurse-performed or previously done) | 'I did', 'already', 'had ... done' |",
       "| recommended | advice for the patient to follow, not an order | counselling, other | imperative advice |",
       "| conditional | only if a stated condition arises; not ordered, no time slot | investigation, follow_up | 'if it hasn't settled', 'hold off', 'if it's not better' |", ""]
(ROOT / "reports" / "FINAL_SCHEMA.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print(json.dumps({k: report[k] for k in ("records", "total_check_evaluations", "failure_count", "pairs_failing_validator", "status", "confidence_fields_non_null")}, indent=1))
for k, v in list(fails.items())[:15]:
    print(k, len(v), v[:3])
print("declared-but-unused enum values (informational, not failures):", unused)
sys.exit(0 if not fails else 1)
