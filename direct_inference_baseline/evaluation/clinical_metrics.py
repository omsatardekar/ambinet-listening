"""Clinical-specific metrics (per encounter raw counters; aggregated by evaluation_runner).

Vital Sign Accuracy: over GOLD vital signs; a vital is correct when the model emits a vital with the same normalised name whose
  value and unit are equal after normalisation. Also reports name-found rate (value/unit ignored).
Speaker Attribution Accuracy: over strictly matched entities with a role field (reported_by / observed_by / stated_by). EXCLUDED
  (and counted): records whose gold quality_checks.speaker_attribution_available is false (contain an UNKNOWN speaker), gold entities
  whose own evidence includes an UNKNOWN-role segment, and gold roles equal to 'unknown'. Denominator is reported.
Negation: for each gold negative finding -> correct (present in negative_findings), polarity_flip (emitted as a PRESENT symptom
  instead) or missing. For each gold present symptom -> polarity_flip if emitted only as a negative finding.
Temporality: matched symptoms and negative findings, gold temporality vs predicted (labels use current / past / resolved; future
  intentions are represented by action status instead)."""
from __future__ import annotations

from collections import Counter

from .attribute_metrics import same_value
from .entity_matching import entity_list, keyed, norm_text

ROLE_FIELD = {"symptoms": "reported_by", "negative_findings": "reported_by", "medications": "reported_by", "allergies": "reported_by",
              "vital_signs": "reported_by", "physical_examination": "observed_by", "review_of_systems": "reported_by",
              "clinical_conditions": "reported_by", "clinical_assessment": "stated_by", "chief_complaint": "reported_by",
              "medical_history.past_medical_history": "reported_by", "medical_history.surgical_history": "reported_by",
              "medical_history.family_history": "reported_by", "medical_history.social_history": "reported_by"}


def vital_signs(gold: dict, pred: dict) -> Counter:
    c = Counter()
    pv = {}
    for e in entity_list(pred, "vital_signs"):
        k = norm_text(e.get("normalized_name") or e.get("name"))
        pv.setdefault(k, []).append(e)
    for g in entity_list(gold, "vital_signs"):
        c["gold_vitals"] += 1
        k = norm_text(g.get("normalized_name") or g.get("name"))
        cands = pv.get(k, [])
        if cands:
            c["name_found"] += 1
            p = cands.pop(0)
            if same_value(g.get("value"), p.get("value")) and norm_text(g.get("unit")) == norm_text(p.get("unit")):
                c["correct"] += 1
    return c


def speaker_attribution(gold: dict, pairs_by_cat: dict) -> Counter:
    c = Counter()
    if gold["quality_checks"].get("speaker_attribution_available") is False:
        c["records_excluded_unknown_speaker"] += 1
        c["entities_excluded_record"] += sum(len(v) for k, v in pairs_by_cat.items() if k in ROLE_FIELD)
        return c
    ev_role = {r["evidence_id"]: r["speaker_role"] for r in gold["clinical_evidence"]}
    for cat, pairs in pairs_by_cat.items():
        f = ROLE_FIELD.get(cat)
        if not f:
            continue
        for g, p in pairs:
            roles = {ev_role.get(i) for i in g.get("evidence_ids", [])}
            if g.get(f) in (None, "unknown") or "unknown" in roles:
                c["entities_excluded_unknown_or_unreliable"] += 1
                continue
            c["evaluated"] += 1
            ok = str(p.get(f)).lower() == str(g[f]).lower()
            c["correct"] += ok
            c[f"gold_role_{g[f]}"] += 1
            c[f"gold_role_{g[f]}_correct"] += ok
    return c


def negation(gold: dict, pred: dict) -> Counter:
    c = Counter()
    pneg = Counter(k for k, _ in keyed(entity_list(pred, "negative_findings"), "negative_findings"))
    ppos = Counter(k for k, _ in keyed(entity_list(pred, "symptoms"), "symptoms") if True)
    pos_present = Counter(k for k, e in keyed(entity_list(pred, "symptoms"), "symptoms") if e.get("status", "present") != "resolved")
    for k, _ in keyed(entity_list(gold, "negative_findings"), "negative_findings"):
        c["gold_negatives"] += 1
        if pneg[k] > 0:
            pneg[k] -= 1
            c["correct"] += 1
        elif pos_present[k] > 0:
            c["polarity_flip_negative_reported_as_present"] += 1
        else:
            c["missing"] += 1
    gold_pos = Counter(k for k, e in keyed(entity_list(gold, "symptoms"), "symptoms") if e.get("status") == "present" and e.get("certainty") != "disputed")
    pneg2 = Counter(k for k, _ in keyed(entity_list(pred, "negative_findings"), "negative_findings"))
    for k, n in gold_pos.items():
        c["gold_present_symptoms"] += n
        if pneg2[k] > 0 and pos_present[k] == 0:
            c["polarity_flip_present_reported_as_negative"] += n
    return c
