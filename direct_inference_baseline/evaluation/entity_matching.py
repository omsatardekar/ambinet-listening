"""Normalisation and entity matching.

STRICT matching (headline): an entity is the normalised PRIMARY KEY of its category (table below). Gold and predicted entities are
matched as multisets: TP = sum over keys of min(gold_count, pred_count); FP = predicted - TP; FN = gold - TP. A wrong attribute
never turns a matched entity into an FN/FP (attributes are scored separately, see attribute_metrics.py).

FUZZY matching (reported separately, never mixed into strict numbers): after strict matching, remaining unmatched gold and predicted
entities of the same category (and same action_type for actions) are paired greedily, one-to-one, when
token-set Jaccard >= 0.75 or difflib ratio >= 0.85. Fuzzy TP = strict TP + these pairs.

Normalisation (norm_text): Unicode NFKC; lowercase; British->American spelling (oe->e, aem->em, haem->hem, rrhoea->rrhea);
unit words -> symbols (milligram(s)/mgs -> mg; microgram(s)/mcg/ug -> mcg; gram(s) -> g; millilitre(s) -> ml; percent -> %;
kilogram(s)/kilo(s) -> kg; centimetre(s) -> cm; degrees celsius -> c; beats per/a minute -> bpm); approved abbreviations expanded
(ecg/ekg, bp, spo2, cbc/fbc, mri, copd, gerd, uti); punctuation removed except digits . / %; whitespace collapsed; leading articles
removed. No stemming, no plural folding, no synonym mapping."""
from __future__ import annotations

import difflib
import re
import unicodedata
from collections import Counter, defaultdict

UNITS = [(r"\b(milligrams?|milligrammes?|mgs?)\b", "mg"), (r"\b(micrograms?|mcg|µg|ug)\b", "mcg"), (r"\bgrams?\b", "g"),
         (r"\b(millilit(?:re|er)s?|mls?)\b", "ml"), (r"\bpercent\b", "%"), (r"\b(kilograms?|kilos?|kgs?)\b", "kg"),
         (r"\b(centimet(?:re|er)s?|cms?)\b", "cm"), (r"(degrees?\s*(celsius|c)\b|°\s*c\b)", "c"), (r"\b(beats (per|a) minute|bpm)\b", "bpm")]
ABBR = {"ecg": "electrocardiogram", "ekg": "electrocardiogram", "bp": "blood pressure", "spo2": "oxygen saturation", "cbc": "complete blood count",
        "fbc": "complete blood count", "mri": "magnetic resonance imaging", "copd": "chronic obstructive pulmonary disease",
        "gerd": "gastro esophageal reflux disease", "uti": "urinary tract infection"}
SPELL = [(r"oesoph", "esoph"), (r"oedema", "edema"), (r"aemia", "emia"), (r"haem", "hem"), (r"rrhoea", "rrhea"), (r"anaesth", "anesth"),
         (r"paed", "ped"), (r"gastro-?oesophageal", "gastro esophageal")]
STOP = {"a", "an", "the", "of", "and", "or", "in", "on", "to", "with", "for", "is", "at", "by", "my", "your", "any", "some"}


def norm_text(s) -> str:
    if s is None:
        return ""
    s = unicodedata.normalize("NFKC", str(s)).lower()
    for a, b in SPELL:
        s = re.sub(a, b, s)
    for a, b in UNITS:
        s = re.sub(a, b, s)
    s = re.sub(r"[^a-z0-9./%\s]", " ", s)
    s = re.sub(r"(?<![0-9])\.|\.(?![0-9])", " ", s)           # keep decimal points only
    toks = [ABBR.get(t, t) for t in s.split()]
    out = " ".join(toks)
    out = re.sub(r"^(a|an|the)\s+", "", out)
    return re.sub(r"\s+", " ", out).strip()


def content_tokens(s: str) -> list[str]:
    return [t for t in norm_text(s).split() if t not in STOP and len(t) > 2]


# category -> function(entity) -> primary key (None if unusable)
def _first(e, *names):
    for n in names:
        if e.get(n) not in (None, ""):
            return e[n]
    return None


KEYS = {
    "chief_complaint": lambda e: _first(e, "normalized_value", "value"),
    "symptoms": lambda e: _first(e, "normalized_name", "name"),
    "negative_findings": lambda e: _first(e, "normalized_name", "finding"),
    "medical_history.past_medical_history": lambda e: _first(e, "normalized_condition", "condition"),
    "medical_history.surgical_history": lambda e: _first(e, "normalized_procedure", "procedure"),
    "medical_history.family_history": lambda e: _first(e, "normalized_condition", "condition"),
    "medical_history.social_history": lambda e: e.get("category"),
    "medications": lambda e: _first(e, "normalized_name", "name"),
    "allergies": lambda e: _first(e, "normalized_substance", "substance"),
    "vital_signs": lambda e: _first(e, "normalized_name", "name"),
    "physical_examination": lambda e: _first(e, "normalized_finding", "finding"),
    "review_of_systems": lambda e: e.get("system"),
    "clinical_conditions": lambda e: _first(e, "normalized_name", "name"),
    "clinical_assessment": lambda e: _first(e, "normalized_assessment", "assessment"),
    "procedures_and_investigations": lambda e: _first(e, "normalized_name", "name"),
    "clinical_actions": lambda e: f"{norm_text(e.get('action_type'))}|{norm_text(e.get('description'))}" if e.get("description") else None,
    "follow_up": lambda e: f"{norm_text(e.get('type'))}|{norm_text(e.get('time_reference'))}",
    "clinical_uncertainties": lambda e: e.get("type"),
}
CATEGORIES = list(KEYS)


def entity_list(label_or_pred: dict, cat: str) -> list[dict]:
    """Entities of one category; malformed containers/items are skipped (the schema validator reports them)."""
    if cat == "chief_complaint":
        cc = label_or_pred.get("chief_complaint")
        return [cc] if isinstance(cc, dict) and KEYS[cat](cc) else []
    obj = label_or_pred
    try:
        for part in cat.split("."):
            obj = obj[part]
    except (KeyError, TypeError):
        return []
    return [e for e in obj if isinstance(e, dict)] if isinstance(obj, list) else []


def keyed(ents: list[dict], cat: str):
    out = []
    for e in ents:
        k = KEYS[cat](e)
        if k not in (None, ""):
            out.append((norm_text(k) if cat not in ("clinical_actions", "follow_up") else k, e))
    return out


def match_category(gold: list[dict], pred: list[dict], cat: str, fuzzy: bool = False):
    """Returns dict(tp, fp, fn, pairs=[(gold_entity, pred_entity)], fp_entities, fn_entities, fuzzy_pairs)."""
    g, p = keyed(gold, cat), keyed(pred, cat)
    gb, pb = defaultdict(list), defaultdict(list)
    for k, e in g:
        gb[k].append(e)
    for k, e in p:
        pb[k].append(e)
    pairs, fn_e, fp_e = [], [], []
    for k in set(gb) | set(pb):
        n = min(len(gb[k]), len(pb[k]))
        pairs += list(zip(gb[k][:n], pb[k][:n]))
        fn_e += [(k, e) for e in gb[k][n:]]
        fp_e += [(k, e) for e in pb[k][n:]]
    res = {"tp": len(pairs), "fp": len(fp_e), "fn": len(fn_e), "pairs": pairs, "fp_entities": fp_e, "fn_entities": fn_e, "fuzzy_pairs": []}
    if fuzzy:
        used_p = set()
        for gk, ge in fn_e:
            best, bi = 0.0, None
            for i, (pk, pe) in enumerate(fp_e):
                if i in used_p:
                    continue
                if cat == "clinical_actions" and gk.split("|")[0] != pk.split("|")[0]:
                    continue
                gt, pt = set(gk.split()), set(pk.split())
                jac = len(gt & pt) / len(gt | pt) if gt | pt else 0
                rat = difflib.SequenceMatcher(None, gk, pk).ratio()
                score = max(jac if jac >= 0.75 else 0, rat if rat >= 0.85 else 0)
                if score > best:
                    best, bi = score, i
            if bi is not None:
                used_p.add(bi)
                res["fuzzy_pairs"].append((ge, fp_e[bi][1]))
    return res


def prf(tp: int, fp: int, fn: int) -> dict:
    """Precision/recall/F1 with UNDEFINED (None) instead of silent 0/1 when a denominator is zero."""
    p = tp / (tp + fp) if tp + fp else None
    r = tp / (tp + fn) if tp + fn else None
    f = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None
    return {"tp": tp, "fp": fp, "fn": fn, "precision": p, "recall": r, "f1": f}


def micro_macro(per_cat: dict[str, dict]) -> dict:
    tp = sum(c["tp"] for c in per_cat.values())
    fp = sum(c["fp"] for c in per_cat.values())
    fn = sum(c["fn"] for c in per_cat.values())
    micro = prf(tp, fp, fn)
    defined = {k: c["f1"] for k, c in per_cat.items() if c["f1"] is not None}
    pr = [c["precision"] for c in per_cat.values() if c["precision"] is not None]
    rc = [c["recall"] for c in per_cat.values() if c["recall"] is not None]
    macro = {"precision": sum(pr) / len(pr) if pr else None, "recall": sum(rc) / len(rc) if rc else None,
             "f1": sum(defined.values()) / len(defined) if defined else None, "categories_averaged": sorted(defined),
             "categories_excluded_undefined": sorted(set(per_cat) - set(defined))}
    return {"micro": micro, "macro": macro}
