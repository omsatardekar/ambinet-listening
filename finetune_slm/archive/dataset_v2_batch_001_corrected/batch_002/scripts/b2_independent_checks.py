"""Batch 002 additional, independently implemented label/transcript/blueprint checks (they do not call the generator code; they only share the read-only
Batch 001 validator for the schema/evidence base numbers). Every check reports numerator/denominator and the failing encounter ids.
These are AUTOMATED checks, not clinician review.   usage: python -B b2_independent_checks.py"""
import collections
import json
import math
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
B2 = HERE.parent
PARENT = B2.parent
sys.path.insert(0, str(PARENT / "validation"))
sys.path.insert(0, str(PARENT / "scripts"))
sys.path.insert(0, str(HERE))
import blueprint as _BP  # noqa: E402,F401  (unmodified Batch 001 module)
import b2_profiles_1, b2_profiles_2, b2_profiles_3, b2_pools  # noqa: E402,F401
b2_pools.apply()   # the Batch 001 validator derives its symptom-category table from the registered profiles: Batch 002 profiles must be registered first
import validate_dataset as VD  # noqa: E402  (read-only reuse)

IN = {p.stem[10:]: json.loads(p.read_text(encoding="utf-8")) for p in sorted((B2 / "output/inputs").glob("encounter_*.json"))}
LB = {p.stem[10:]: json.loads(p.read_text(encoding="utf-8")) for p in sorted((B2 / "output/labels").glob("encounter_*.json"))}
BP = {p.stem[10:]: json.loads(p.read_text(encoding="utf-8")) for p in sorted((B2 / "scenario_blueprints").glob("blueprint_*.json"))}
SECTIONS = ["symptoms", "negative_findings", "medical_history.past_medical_history", "medical_history.surgical_history", "medical_history.family_history", "medical_history.social_history",
            "medications", "allergies", "vital_signs", "physical_examination", "review_of_systems", "clinical_conditions", "clinical_assessment", "procedures_and_investigations",
            "clinical_actions", "follow_up", "clinical_uncertainties"]
NEG = {"no", "not", "none", "never", "nothing", "nope", "neither", "nor", "without", "denies", "haven't", "hasn't", "didn't", "don't", "doesn't", "isn't", "wasn't", "cannot", "can't", "nil"}
SMALLTALK = {"hello", "hi", "hey", "morning", "afternoon", "evening", "thanks", "thank", "welcome", "bye", "goodbye", "sit", "seat"}
R = {}


def rec(name, ok, eid="", note=""):
    d = R.setdefault(name, {"checked": 0, "passed": 0, "failing_ids": [], "notes": []})
    d["checked"] += 1
    if ok:
        d["passed"] += 1
    else:
        if eid and eid not in d["failing_ids"]:
            d["failing_ids"].append(eid)
        if note and len(d["notes"]) < 8:
            d["notes"].append(f"{eid}: {note}")


def sect(lab, path):
    o = lab
    for part in path.split("."):
        o = o[part]
    return o


def toks(t):
    return re.findall(r"[a-z0-9']+", t.lower().replace("’", "'"))


def stems(text):
    return [w[:5] for w in toks(text) if len(w) >= 4 and w not in {"with", "that", "this", "have", "from", "your", "pain"} or w == "pain"]


def pure_question(t):
    """a segment that is only a question (no statement sentence before the final question)"""
    t = t.strip()
    return t.endswith("?") and len(t.split()) <= 14 and not re.search(r"[.!]\s+\S", t)   # long unpunctuated turns that merely end in a question are statements


AFFIRM = {"yes", "yeah", "yep", "correct", "sure", "definitely", "mm", "absolutely", "indeed", "right", "exactly", "uh", "um"}


def mmss(x):
    return f"{int(x) // 60:02d}:{int(x) % 60:02d}"


# ---------------------------------------------------------------- 1 files, ids, parse
ids = sorted(IN)
rec("files_inputs_500", len(IN) == 500)
rec("files_labels_500", len(LB) == 500)
rec("files_blueprints_500", len(BP) == 500)
rec("ids_match_across_inputs_labels_blueprints", set(IN) == set(LB) == set(BP))
rec("ids_unique_and_in_range_20001_20500", len(set(ids)) == len(ids) and all(20001 <= int(i) <= 20500 for i in ids))
rec("ids_disjoint_from_batch_001_00001_00500", all(int(i) > 500 for i in ids))
for i in ids:
    inp, lab, bp = IN[i], LB[i], BP[i]
    rec("encounter_id_inside_files_equals_filename", inp["encounter_id"] == i and lab["encounter_id"] == i and f"{bp['idx']:05d}" == i, i)
    segs = inp["segments"]
    byid = {s["segment_id"]: s for s in segs}
    # ---------------------------------------------------------- 2 evidence records resolve to real segments
    evs = {e["evidence_id"]: e for e in lab["clinical_evidence"]}
    seg_of_ev = {}
    for e in lab["clinical_evidence"]:
        cand = [k for k, s in enumerate(segs) if s["speaker_id"] == e["speaker_id"] and s["text"] == e["transcript_text"] and s["role"].lower() == e["speaker_role"]
                and mmss(s["start_seconds"]) == e["start_timestamp"]]
        rec("evidence_record_matches_real_transcript_segment", len(cand) >= 1, i, e["evidence_id"])
        seg_of_ev[e["evidence_id"]] = cand[0] if cand else None
    # entities
    ents = []
    for path in SECTIONS:
        for k, x in enumerate(sect(lab, path)):
            ents.append((path, k, x))
    ents.append(("chief_complaint", 0, lab["chief_complaint"]))
    for path, k, x in ents:
        loc = f"{path}[{k}]" if path != "chief_complaint" else path
        eids = x.get("evidence_ids") or []
        rec("entity_evidence_ids_resolve", all(t in evs for t in eids) and len(eids) > 0, i, loc)
        for t in eids:
            if t in evs:
                rec("evidence_supports_symmetric", loc in evs[t]["supports"], i, f"{loc}<->{t}")
    # ---------------------------------------------------------- 3 semantic evidence quality
    def ev_segs(x):
        return [(segs[seg_of_ev[t]], t) for t in (x.get("evidence_ids") or []) if t in seg_of_ev and seg_of_ev[t] is not None]

    patient_origin = [("symptoms", "reported_by"), ("negative_findings", "reported_by"), ("medical_history.past_medical_history", "reported_by"), ("medical_history.surgical_history", "reported_by"),
                      ("medical_history.family_history", "reported_by"), ("medications", "reported_by"), ("allergies", "reported_by")]
    for path, who in patient_origin:
        for k, x in enumerate(sect(lab, path)):
            es = ev_segs(x)
            nonq = [s for s, _ in es if not pure_question(s["text"])]
            rec("patient_origin_fact_has_non_question_evidence", len(nonq) > 0, i, f"{path}[{k}]")
            # speaker consistency: reported_by is the role of a cited non-question segment (clinician-confirmation facts may be cited through the doctor's confirming turn)
            roles = {s["role"].lower() for s in nonq}
            rec("reported_by_equals_role_of_a_cited_non_question_segment", x[who] in roles, i, f"{path}[{k}] {x[who]} vs {sorted(roles)}")
            # no greeting / small talk as the only evidence
            only_small = all(len(toks(s["text"])) <= 8 and (set(toks(s["text"])) & SMALLTALK) for s, _ in es) if es else False
            rec("evidence_not_greeting_only", not only_small, i, f"{path}[{k}]")
    for k, x in enumerate(lab["negative_findings"]):
        nonq = [s for s, _ in ev_segs(x) if not pure_question(s["text"])]
        has_neg = any((set(toks(s["text"])) & NEG) or any(w.endswith("n't") for w in toks(s["text"])) for s in nonq)
        rec("negative_finding_evidence_contains_negation_cue", has_neg, i, f"negative_findings[{k}] {x['finding']}")
    for k, x in enumerate(lab["symptoms"]):
        if x["status"] == "present" and x["temporality"] == "current":
            st = stems(x["name"])
            es_ = ev_segs(x)
            ok = False
            for s, _ in es_:
                tk = toks(s["text"])
                hit = [p for p, w in enumerate(tk) if any(w.startswith(q) for q in st)]
                if not hit:
                    continue
                if not pure_question(s["text"]):
                    own = set(toks(x["name"]))   # a negation word that belongs to the symptom phrase itself ("not opening my bowels") is not a negation of it
                    for sent in re.split(r"[.;!?]", s["text"]):   # negation must be in the same sentence as the symptom words
                        stk = toks(sent)
                        sh = [p for p, w in enumerate(stk) if any(w.startswith(q) for q in st)]
                        if sh and any(not ((set(stk[max(0, p - 4):p]) & NEG) - own) for p in sh):   # at least one un-negated mention
                            ok = True
                else:   # a question naming the symptom is supported when the next cited segment is an affirmative reply
                    pos = segs.index(s)
                    nxt = [t for t, _ in es_ if segs.index(t) == pos + 1]
                    if nxt:
                        nt = toks(nxt[0]["text"])
                        if (set(nt[:6]) & AFFIRM) and not (set(nt[:3]) & NEG):
                            ok = True
            rec("present_symptom_supported_by_statement_or_affirmed_question", ok, i, f"symptoms[{k}] {x['name']}")
    # medications: dose placement and consistency
    names = []
    for k, x in enumerate(lab["medications"]):
        names.append((x["normalized_name"] or x["name"]).lower())
        if x["dose"]:
            num = re.match(r"[\d.]+", x["dose"]).group(0)
            es = ev_segs(x)
            ix = [seg_of_ev[t] for _, t in es]
            name_idx = [n for n, s in enumerate(segs) if (x["name"] or "").lower()[:6] in s["text"].lower() or (x["generic_name"] or "").lower()[:6] in s["text"].lower()]
            dose_in = [n for n in ix if num in re.findall(r"[\d.]+", segs[n]["text"])]
            near = any(abs(d - m) <= 2 and d >= m or d == m for d in dose_in for m in name_idx if m in ix or True)
            rec("medication_dose_number_in_cited_evidence", len(dose_in) > 0, i, f"medications[{k}] {x['name']} {x['dose']}")
            rec("medication_dose_within_two_segments_after_drug_name", near, i, f"medications[{k}] {x['name']} {x['dose']}")
    dup = [n for n, c in collections.Counter(names).items() if c > 1]
    rec("no_duplicate_medication_entries", not dup, i, str(dup))
    stat = collections.defaultdict(set)
    for x in lab["medications"]:
        stat[(x["generic_name"] or x["name"]).lower()].add(x["status"])
    rec("no_drug_both_currently_used_and_planned_or_discontinued", all(not ({"currently_used"} & s and (s - {"currently_used"})) for s in stat.values()), i, str({k: v for k, v in stat.items() if len(v) > 1}))
    # allergies
    medset = {(x["name"] or "").lower() for x in lab["medications"]} | {(x["generic_name"] or "").lower() for x in lab["medications"]}
    for k, x in enumerate(lab["allergies"]):
        rec("allergy_not_placeholder", str(x["substance"]).lower() not in {"none", "no", "nil", "unknown", "n/a", ""}, i, f"allergies[{k}]")
        rec("allergy_substance_in_cited_evidence", any(x["substance"].lower()[:6] in s["text"].lower() or x["normalized_substance"].lower()[:6] in s["text"].lower() for s, _ in ev_segs(x)), i, f"allergies[{k}] {x['substance']}")
        rec("allergy_substance_not_a_current_medication_name", x["status"] in ("historical", "disputed") or x["substance"].lower() not in medset and x["normalized_substance"].lower() not in medset, i, f"allergies[{k}] {x['substance']}")
    txt_all = " ".join(s["text"].lower() for s in segs)
    has_nka = any(n["normalized_name"] == "No known allergies" for n in lab["negative_findings"])
    kind = bp["allergies"]["kind"]
    expect_state = {"none": "explicit_no_known_allergies", "not_discussed": "not_discussed", "known": "reported", "historical": "reported", "uncertain": "reported", "disputed": "disputed"}.get(kind)
    got = ("explicit_no_known_allergies" if has_nka and not lab["allergies"] else "not_discussed" if (not lab["allergies"] and not has_nka and "allerg" not in txt_all) else
           "disputed" if any(a["status"] == "disputed" for a in lab["allergies"]) else "reported" if lab["allergies"] else "other")
    rec("allergy_representation_matches_blueprint_and_schema", got == expect_state, i, f"blueprint {kind} -> expected {expect_state}, label shows {got}")
    rec("allergy_status_values_valid", all(a["status"] in ("reported", "uncertain", "historical", "disputed") for a in lab["allergies"]), i)
    # datetimes
    blob = json.dumps(lab)
    rec("no_iso_date_or_datetime_in_label", not re.search(r"\d{4}-\d{2}-\d{2}|T\d{2}:\d{2}", blob), i)
    rec("follow_up_normalized_datetime_null", all(f["normalized_datetime"] is None for f in lab["follow_up"]), i)
    for k, x in enumerate(lab["procedures_and_investigations"]):
        sd = x["scheduled_datetime"]
        rec("scheduled_datetime_null_or_literally_spoken", sd is None or all(part.lower() in txt_all for part in re.split(r"\s+at\s+", sd)), i, f"procedures[{k}] {sd}")
    # temporality vs blueprint
    n_disp = sum(1 for s in lab["symptoms"] if s["certainty"] == "disputed")
    n_res_bp = sum(1 for s in bp["syms"] if s["status"] == "resolved" or s.get("role") == "previous")
    n_res_lb = sum(1 for s in lab["symptoms"] if s["temporality"] in ("resolved", "past"))
    rec("symptom_count_and_temporality_match_blueprint_allowing_one_disputed_symptom_per_dispute", n_res_bp == n_res_lb and len(lab["symptoms"]) == len(bp["syms"]) + n_disp, i, f"bp resolved {n_res_bp} total {len(bp['syms'])}; label {n_res_lb} total {len(lab['symptoms'])} disputed {n_disp}")
    # blueprint consistency of other sections
    rec("family_history_count_matches_blueprint", len(lab["medical_history"]["family_history"]) == len(bp["fam"]), i)
    rec("surgical_history_count_matches_blueprint", len(lab["medical_history"]["surgical_history"]) == len(bp["surg"]), i)
    n_med_lb = sum(1 for m in lab["medications"] if m["status"] in ("currently_used", "discontinued"))
    rec("current_and_discontinued_medication_count_matches_blueprint", n_med_lb == len(bp["meds"]), i, f"bp {len(bp['meds'])} label {n_med_lb}")
    rec("planned_medication_count_matches_blueprint_rx", sum(1 for m in lab["medications"] if m["status"] == "planned") == len(bp["rx"]), i)
    # contradictions / duplicates inside the label
    present = {s["normalized_name"].lower() for s in lab["symptoms"] if s["status"] == "present" and s["temporality"] == "current" and s["certainty"] != "disputed"}
    negs = {n["normalized_name"].lower() for n in lab["negative_findings"]}
    rec("no_negative_finding_contradicting_an_undisputed_current_present_symptom", not (present & negs), i, str(present & negs))
    for path in SECTIONS[:-1]:
        keyf = {"symptoms": "normalized_name", "negative_findings": "normalized_name", "medical_history.past_medical_history": "normalized_condition", "medical_history.surgical_history": "normalized_procedure",
                "medical_history.family_history": None, "medical_history.social_history": "description", "allergies": "normalized_substance", "vital_signs": "normalized_name", "clinical_conditions": "normalized_name",
                "procedures_and_investigations": "normalized_name", "physical_examination": "normalized_finding"}.get(path)
        if keyf:
            keys = [str(x[keyf]).lower() + ("|" + str(x["temporality"]) if path == "symptoms" else "") for x in sect(lab, path)]
            rec("no_duplicate_entities_within_section_symptoms_keyed_with_temporality", len(keys) == len(set(keys)), i, f"{path}: {[k for k, c in collections.Counter(keys).items() if c > 1]}")
    fam = [(x["normalized_condition"], x["relation"]) for x in lab["medical_history"]["family_history"]]
    rec("no_duplicate_family_history", len(fam) == len(set(fam)), i)

# ---------------------------------------------------------------- 4 existing Batch 001 validator, run on Batch 002 (read-only reuse)
rep, dup, evid = VD.run(B2, write=False, expected=500)
base = {"validator_pass_count": rep["pass_count"], "validator_fail_count": rep["fail_count"], "validator_error_groups": rep["error_groups"], "validator_errors_by_check": rep["errors_by_check"],
        "evidence_lexical_facts_checked": evid["facts_checked"], "evidence_lexical_facts_grounded": evid["facts_grounded"], "evidence_alignment_status": evid["alignment_status"],
        "duplicates": {k: dup[k] for k in ("exact_duplicate_conversations", "max_pairwise_5gram_jaccard", "opening_sentence_unique", "opening_sentence_max_share", "first_two_turn_pairs_unique",
                                           "symptom_combinations_unique", "scenario_fingerprint_duplicates(profile+symptoms+meds+assessment)", "duplicate_count")},
        "near_duplicate_pairs": len(dup["near_duplicate_pairs_jaccard_ge_0.45"])}
out = {"disclaimer": "AUTOMATED checks only; no clinician reviewed any record.", "base_validator": base, "independent_checks": {}}
for name, d in R.items():
    out["independent_checks"][name] = {"numerator_passed": d["passed"], "denominator_checked": d["checked"], "failed": d["checked"] - d["passed"], "failing_encounters": len(d["failing_ids"]),
                                      "failing_ids_sample": d["failing_ids"][:15], "notes": d["notes"]}
(B2 / "validation" / "independent_checks.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
w = max(len(k) for k in out["independent_checks"])
for k, v in out["independent_checks"].items():
    print(f"{k:<{w}}  {v['numerator_passed']}/{v['denominator_checked']}  failed={v['failed']}  enc={v['failing_encounters']}")
print(json.dumps(base["duplicates"]), "near-dup:", base["near_duplicate_pairs"], "| validator", base["validator_pass_count"], "/", 500)
