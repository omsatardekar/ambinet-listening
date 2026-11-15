"""Record-by-record audit of Qwen3-1.7B P00 vs P01 on the 30 shared development ids: transcript -> gold label -> P00 output -> P01 output.
READ-ONLY with respect to every protected artefact; writes only new files under EXP_002_PROMPTING_INFERENCE/evaluations/p00_p01_audit/ .
Labels are read only for the 30 authorised prompt-development ids, through the dataset guard (StrictAccessSpy).  DEVELOPMENT-ONLY analysis.
usage: python -B -s audit_p00_p01.py"""
import collections
import difflib
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
TRACK = HERE.parents[3]
sys.path.insert(0, str(TRACK / "scripts"))
import common_1_7b as C  # noqa: E402

sys.path.insert(0, str(C.EXP6 / "s1"))
import evaluate_s1 as E  # noqa: E402
from direct_inference_baseline.evaluation import evaluation_runner as ER, evidence_evaluator as EE, attribute_metrics as AM  # noqa: E402
from direct_inference_baseline.evaluation.entity_matching import CATEGORIES, KEYS, entity_list, match_category, norm_text  # noqa: E402

E1, E2 = TRACK / "experiments" / "EXP_001_DIRECT_INFERENCE", TRACK / "experiments" / "EXP_002_PROMPTING_INFERENCE"
RUN = {"P00": (E1, "P00_direct_dev50"), "P01": (E2, "P01_schema_guided_dev50")}
OUT = E2 / "evaluations" / "p00_p01_audit"
OUT.mkdir(parents=True, exist_ok=True)
frozen_ids = json.loads((TRACK / "manifests" / "FROZEN_50_PROMPT_DEV_IDS.json").read_text(encoding="utf-8"))["ids"]
man = {k: json.loads((e / "evaluations" / r / "run_manifest.json").read_text(encoding="utf-8-sig"))["records"] for k, (e, r) in RUN.items()}
IDS = [i for i in frozen_ids if i in man["P01"]]
assert len(IDS) == 30 and IDS == frozen_ids[:30], "the 30 ids must be the first 30 frozen ids"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


# ------------------------------------------------------------------ helpers
def nn(v):  # non-null
    if v is None or v == "" or v == [] or v == {}:
        return False
    if isinstance(v, dict):
        return any(nn(x) for x in v.values())
    return True


def seg_norm(t):
    return re.sub(r"\s+", " ", str(t)).strip().lower()


def safe_dur(g, p):
    try:
        return AM.same_duration(g, p)
    except Exception:  # noqa: BLE001
        return False


def num(v):
    try:
        return float(re.findall(r"-?\d+(?:\.\d+)?", str(v))[0])
    except Exception:  # noqa: BLE001
        return None


def cmp_attr(a, g, p):
    if a in ("dose", "severity"):
        try:
            return AM.same_value(g, p)
        except Exception:  # noqa: BLE001
            return norm_text(g) == norm_text(p)
    if a == "duration":
        return safe_dur(g, p)
    if a == "value":
        return num(g) is not None and num(g) == num(p)
    return norm_text(g) == norm_text(p)


CHECK = {
    "chief_complaint": ["reported_by"], "symptoms": ["status", "temporality", "certainty", "severity", "duration", "frequency", "reported_by"],
    "negative_findings": ["temporality", "reported_by"], "medical_history.past_medical_history": ["status", "reported_by"], "medical_history.surgical_history": ["reported_by"],
    "medical_history.family_history": ["relation", "reported_by"], "medical_history.social_history": ["status", "reported_by"],
    "medications": ["dose", "route", "frequency", "status", "reported_by"], "allergies": ["reaction", "status", "reported_by"], "vital_signs": ["value", "unit", "reported_by"],
    "physical_examination": ["status", "observed_by"], "review_of_systems": ["status", "reported_by"], "clinical_conditions": ["status", "reported_by"],
    "clinical_assessment": ["certainty", "stated_by"], "procedures_and_investigations": ["status", "type"], "clinical_actions": ["status", "responsible_person"],
    "follow_up": ["status", "time_reference"], "clinical_uncertainties": ["resolution_status"]}
ATTRIB = {"reported_by", "observed_by", "stated_by", "responsible_person", "relation"}
STATUS = {"status", "temporality", "certainty", "resolution_status"}
SHORT = {"medical_history.past_medical_history": "past medical history", "medical_history.surgical_history": "surgical history", "medical_history.family_history": "family history",
         "medical_history.social_history": "social history", "procedures_and_investigations": "investigations/procedures"}
PLACEHOLDER = {"none", "no known allergies", "nil", "unknown", "n/a", "no allergies", "nkda", ""}


def label(c):
    return SHORT.get(c, c.replace("_", " "))


def tok(s):
    return [w for w in re.findall(r"[a-z0-9]+", str(s).lower()) if len(w) > 3]


# ------------------------------------------------------------------ reconciliation + data load
spy = C.G.StrictAccessSpy(allow_validation=False)
rec = {}
recon = []
with spy:
    for i in IDS:
        tp = C.S.INPUT_DIR / f"encounter_{i}.json"
        lp = C.S.LABEL_DIR / f"encounter_{i}.json"
        tr, gold = load(tp), ER.load_gold(i)
        row = {"id": i, "in_frozen_50": i in frozen_ids, "transcript_file": tp.name, "transcript_id_inside": tr["encounter_id"], "transcript_segments": len(tr["segments"]), "transcript_sha16": sha(tp),
               "label_file": lp.name, "label_id_inside": gold["encounter_id"], "label_sha16": sha(lp)}
        preds = {}
        for k, (e, r) in RUN.items():
            rp = e / "outputs" / "raw" / r / f"encounter_{i}.json"
            raw = load(rp) if rp.exists() else None
            pp = e / "outputs" / "parsed" / r / f"encounter_{i}.json"
            fp = e / "outputs" / "failed" / r / f"encounter_{i}.json"
            parsed = None
            if pp.exists():
                parsed = load(pp)
                parsed = parsed.get("parsed", parsed) if isinstance(parsed, dict) and "parsed" in parsed else parsed
            row[k] = {"raw_present": raw is not None, "raw_id_inside": raw and raw.get("encounter_id"), "raw_sha16": rp.exists() and sha(rp), "parsed_present": pp.exists(), "parsed_id_inside": parsed and parsed.get("encounter_id"),
                      "failed_present": fp.exists(), "manifest_status": man[k][i]["status"], "finish_reason": man[k][i].get("finish_reason"), "completion_tokens": man[k][i].get("completion_tokens")}
            preds[k] = parsed
        row["matched_ok"] = (row["transcript_id_inside"] == i == row["label_id_inside"] and all(row[k]["raw_id_inside"] == i and ((row[k]["parsed_id_inside"] == i) if row[k]["parsed_present"] else row[k]["failed_present"]) and
                             (row[k]["parsed_present"] != row[k]["failed_present"]) for k in RUN))
        recon.append(row)
        rec[i] = {"tr": tr, "gold": gold, "pred": preds}
dups = [i for i, n in collections.Counter(IDS).items() if n > 1]
extra_p01 = sorted(set(p.stem[10:] for p in (E2 / "outputs" / "raw" / RUN["P01"][1]).glob("encounter_*.json")) - set(IDS))
(OUT / "RECONCILIATION.json").write_text(json.dumps({"ids": IDS, "duplicates": dups, "unexpected_p01_files": extra_p01, "rows": recon}, indent=1), encoding="utf-8")
assert all(r["matched_ok"] for r in recon), [r["id"] for r in recon if not r["matched_ok"]]


# ------------------------------------------------------------------ classification
def evidence_text_map(tr):
    return {seg_norm(s["text"]): s for s in tr["segments"]}


RAWF = ("name", "finding", "condition", "procedure", "substance", "value", "description", "assessment", "system", "normalized_name", "normalized_finding", "normalized_condition",
        "normalized_procedure", "normalized_substance", "normalized_value", "normalized_assessment")


def fact_tokens(g):
    out = set()
    for f in RAWF:
        v = g.get(f)
        if isinstance(v, str):
            out |= {w[:5] for w in tok(v)}
    return out


def gold_segments(g_ent, gold, tr):
    """cited gold evidence segments, best-scoring first: score = overlap with the gold fact's own wording (raw + normalised text fields)"""
    evs = {e["evidence_id"]: e for e in gold.get("clinical_evidence", [])}
    segmap = evidence_text_map(tr)
    ft = fact_tokens(g_ent)
    cands = []
    for eid in g_ent.get("evidence_ids", []) or []:
        e = evs.get(eid)
        if not e:
            continue
        s = segmap.get(seg_norm(e["transcript_text"]))
        score = len(ft & {w[:5] for w in tok(e["transcript_text"])})
        cands.append((score, -len(e["transcript_text"]), s, e))
    cands.sort(key=lambda x: (-x[0], -x[1]))
    return cands


def gold_excerpt(g_ent, gold, tr, key):
    cands = gold_segments(g_ent, gold, tr)
    if not cands:
        return None
    _, _, s, e = cands[0]
    return {"segment_id": s["segment_id"] if s else None, "speaker": f"{e['speaker_id']} {e['speaker_role']}", "text": e["transcript_text"]}


def linked_extra(g_ent, gold, tr, extras):
    """an unmatched prediction whose words lie inside the transcript segment(s) that best express the gold fact = same fact, different wording (terminology / surface form)"""
    cands = gold_segments(g_ent, gold, tr)
    if not cands or cands[0][0] <= 0:
        return None
    best = [c for c in cands if c[0] == cands[0][0]]
    text = " ".join(c[3]["transcript_text"] for c in best).lower()
    for x in extras:
        ts = tok(x["pred_key"] or "")
        if ts and all(w[:5] in text for w in ts) and len(ts) <= 8 and ({w[:5] for w in ts} & fact_tokens(g_ent)):
            return x
    return None


def classify(cat, gold, pred, tr, failed):
    """returns (gold_rows, extra_rows)"""
    g_ents = entity_list(gold, cat)
    p_ents = entity_list(pred or {}, cat)
    m = match_category(g_ents, p_ents, cat, fuzzy=True)
    pair_by_g = {id(g): p for g, p in m["pairs"]}
    fuzzy_by_g = {id(g): p for g, p in m["fuzzy_pairs"]}
    used_fuzzy_p = {id(p) for _, p in m["fuzzy_pairs"]}
    rows = []
    for g in g_ents:
        key = KEYS[cat](g)
        ex = gold_excerpt(g, gold, tr, key)
        r = {"cat": cat, "gold_key": key, "excerpt": ex, "gold_attrs": {a: g.get(a) for a in CHECK[cat] if nn(g.get(a))}}
        if failed:
            r.update(cls="MISSED", detail=["no usable output (invalid/truncated JSON)"], pred_key=None)
        elif id(g) in pair_by_g:
            p = pair_by_g[id(g)]
            issues, cls = [], "CORRECT"
            for a in CHECK[cat]:
                gv, pv = g.get(a), p.get(a)
                if nn(gv):
                    if not nn(pv) or not cmp_attr(a, gv, pv):
                        tag = "WRONG_ATTRIBUTION" if a in ATTRIB else "WRONG_STATUS" if a in STATUS else "PARTIAL"
                        note = f"{a}: gold={json.dumps(gv, ensure_ascii=False)[:40]} pred={json.dumps(pv, ensure_ascii=False)[:40]}"
                        if a in ATTRIB and isinstance(pv, str) and re.match(r"person_\d", pv):
                            note += " (speaker id written instead of role)"
                        issues.append((tag, note))
                elif nn(pv) and a in ("dose", "route", "frequency") and cat == "medications":
                    issues.append(("UNSUPPORTED", f"{a}: not in gold, pred={json.dumps(pv, ensure_ascii=False)[:40]}"))
            if issues:
                order = ["WRONG_STATUS", "WRONG_ATTRIBUTION", "PARTIAL", "UNSUPPORTED"]
                cls = sorted(issues, key=lambda x: order.index(x[0]))[0][0]
            r.update(cls=cls, detail=[n for _, n in issues], pred_key=KEYS[cat](p), tags=sorted({t for t, _ in issues}))
        elif id(g) in fuzzy_by_g:
            p = fuzzy_by_g[id(g)]
            r.update(cls="WRONG_NORMALIZATION", detail=[f"same fact, different form: pred '{KEYS[cat](p)}'"], pred_key=KEYS[cat](p))
        else:
            r.update(cls="MISSED", detail=[], pred_key=None)
        rows.append(r)
    extras = []
    if not failed:
        text = " ".join(s["text"] for s in tr["segments"]).lower()
        other_gold = {}
        for c2 in CATEGORIES:
            if c2 != cat:
                for g2 in entity_list(gold, c2):
                    other_gold.setdefault(norm_text(KEYS[c2](g2)), c2)
        med_names = {norm_text(KEYS["medications"](x)) for x in entity_list(pred or {}, "medications")} if cat == "allergies" else set()
        for k, p in m["fp_entities"]:
            if id(p) in used_fuzzy_p:
                continue
            toks = tok(KEYS[cat](p) or "")
            sup = bool(toks) and all(w[:5] in text for w in toks)
            flag = "EXTRA_SUPPORTED_BY_TRANSCRIPT" if sup else "UNSUPPORTED"
            note = []
            if cat == "allergies" and k in PLACEHOLDER:
                flag, note = "INCORRECT", ["placeholder written as an allergy entry (gold has no allergy)"]
            elif cat == "allergies" and k in med_names:
                flag, note = "INCORRECT", ["a medication from the medication list written as an allergy"]
            elif k in other_gold:
                flag, note = "INCORRECT", [f"gold has this fact in category '{label(other_gold[k])}'"]
            extras.append({"cat": cat, "pred_key": k, "cls": flag, "detail": note})
    if not failed:
        for r, g in zip(rows, g_ents):
            if r["cls"] == "MISSED":
                x = linked_extra(g, gold, tr, [e for e in extras if not e.get("used")])
                if x:
                    x["used"] = True
                    r.update(cls="WRONG_NORMALIZATION", detail=[f"present in the output under different wording: pred '{x['pred_key']}' (linked through the transcript segment the gold fact cites)"], pred_key=x["pred_key"], linked=True)
        extras = [e for e in extras if not e.get("used")]
    return rows, extras


facts, extras_all = [], []
per_rec = {}
for i in IDS:
    d = rec[i]
    per_rec[i] = {"gold_rows": {}, "extra_rows": {}}
    for k in RUN:
        failed = d["pred"][k] is None
        for cat in CATEGORIES:
            rows, ex = classify(cat, d["gold"], d["pred"][k], d["tr"], failed)
            per_rec[i]["gold_rows"].setdefault(cat, {})[k] = rows
            per_rec[i]["extra_rows"].setdefault(cat, {})[k] = ex
# flatten facts (both systems aligned by gold position: rows lists have same gold order)
for i in IDS:
    for cat in CATEGORIES:
        r0, r1 = per_rec[i]["gold_rows"][cat]["P00"], per_rec[i]["gold_rows"][cat]["P01"]
        for a, b in zip(r0, r1):
            facts.append({"id": i, "cat": cat, "gold_key": a["gold_key"], "segment": (a["excerpt"] or {}).get("segment_id"), "P00": a["cls"], "P00_detail": a["detail"], "P01": b["cls"], "P01_detail": b["detail"]})
        for k in RUN:
            for x in per_rec[i]["extra_rows"][cat][k]:
                extras_all.append({"id": i, "system": k, **x})
(OUT / "AUDIT_GOLD_FACTS.jsonl").write_text("\n".join(json.dumps(f, ensure_ascii=False) for f in facts), encoding="utf-8")
(OUT / "AUDIT_EXTRA_PREDICTIONS.jsonl").write_text("\n".join(json.dumps(f, ensure_ascii=False) for f in extras_all), encoding="utf-8")

# ------------------------------------------------------------------ speaker audit
speaker = {}
for i in IDS:
    d = rec[i]
    tr_sp = {(s["speaker_id"], s["role"].lower()) for s in d["tr"]["segments"]}
    gold_sp = {(s["speaker_id"], s["role"]) for s in d["gold"]["encounter_metadata"]["primary_speakers"]}
    row = {"transcript_speakers": sorted(tr_sp), "gold_primary_speakers": sorted(gold_sp)}
    for k in RUN:
        p = d["pred"][k]
        if p is None:
            row[k] = None
            continue
        ps = [(s.get("speaker_id"), s.get("role")) for s in (p.get("encounter_metadata") or {}).get("primary_speakers", []) if isinstance(s, dict)]
        exact = [s for s in ps if s in tr_sp]
        ids_ok = {s[0] for s in ps} & {s[0] for s in tr_sp}
        wrong_role = [s for s in ps if s[0] in {t[0] for t in tr_sp} and s not in tr_sp]
        row[k] = {"predicted": ps, "n_transcript_speakers": len(tr_sp), "n_pred_speakers": len(ps), "exact_id_and_role": len(exact), "missing_speakers": sorted(tr_sp - set(ps)), "wrong_role": wrong_role,
                  "invented_ids": [s for s in ps if s[0] not in {t[0] for t in tr_sp}], "all_speakers_correct": set(ps) == tr_sp}
    speaker[i] = row
(OUT / "SPEAKER_AUDIT.json").write_text(json.dumps(speaker, indent=1, default=str), encoding="utf-8")

# ------------------------------------------------------------------ evidence audit
def ev_audit(i, k):
    d = rec[i]
    p = d["pred"][k]
    if p is None:
        return None
    segs = d["tr"]["segments"]
    segmap = evidence_text_map(d["tr"])
    evs = [e for e in (p.get("clinical_evidence") or []) if isinstance(e, dict)]
    by_id = {e.get("evidence_id"): e for e in evs}
    out = collections.Counter()
    out["evidence_records"] = len(evs)
    seg_of = {}
    for e in evs:
        t = seg_norm(e.get("transcript_text", ""))
        s = segmap.get(t)
        if s:
            out["ev_exact_single_segment"] += 1
            seg_of[e.get("evidence_id")] = s
            if e.get("speaker_id") != s["speaker_id"]:
                out["ev_wrong_speaker_id"] += 1
            if str(e.get("speaker_role", "")).lower() != s["role"].lower():
                out["ev_wrong_or_empty_speaker_role"] += 1
        else:
            contained = sum(seg_norm(s2["text"]) in t for s2 in segs)
            if contained >= 2:
                out["ev_multi_segment_or_whole_transcript_dump"] += 1
            elif t and max(difflib.SequenceMatcher(None, t, seg_norm(s2["text"])).ratio() for s2 in segs) >= 0.85:
                out["ev_near_copy_not_exact"] += 1
            else:
                out["ev_text_not_in_transcript"] += 1
        if not e.get("supports"):
            out["ev_empty_supports"] += 1
    intro_ids = {s["segment_id"] for s in segs[:2]}
    for cat in CATEGORIES:
        for n, ent in enumerate(entity_list(p, cat)):
            path = "chief_complaint" if cat == "chief_complaint" else f"{cat}[{n}]"
            out["facts_checked"] += 1
            ids = [x for x in (ent.get("evidence_ids") or []) if isinstance(x, str)]
            if not ids:
                out["fact_no_evidence_ids"] += 1
                continue
            cited = [by_id[x] for x in ids if x in by_id]
            if len(cited) < len(ids):
                out["fact_dangling_evidence_id"] += 1
            if not cited:
                continue
            key = KEYS[cat](ent) or ""
            txt = " ".join(str(c.get("transcript_text", "")) for c in cited)
            if not EE.lexical_support(key, txt, False):
                out["fact_not_mentioned_in_cited_text"] += 1
                if any(seg_of.get(c.get("evidence_id"), {}).get("segment_id") in intro_ids for c in cited):
                    out["fact_cites_intro_segment_unrelated"] += 1
            if not any(path in (c.get("supports") or []) for c in cited):
                out["fact_path_missing_from_supports"] += 1
            if EE.lexical_support(key, txt, False) and any(path in (c.get("supports") or []) for c in cited):
                out["fact_evidence_ok"] += 1
    return dict(out)


evid = {i: {k: ev_audit(i, k) for k in RUN} for i in IDS}
(OUT / "EVIDENCE_AUDIT.json").write_text(json.dumps(evid, indent=1), encoding="utf-8")

# ------------------------------------------------------------------ aggregates
agg = {k: collections.defaultdict(collections.Counter) for k in RUN}
both_parsed = [i for i in IDS if rec[i]["pred"]["P00"] is not None and rec[i]["pred"]["P01"] is not None]
groups = {"all30": IDS, "both_parsed20": both_parsed}
summary = {"ids": IDS, "both_parsed": both_parsed, "classes": {}, "extra": {}}
for gname, gids in groups.items():
    summary["classes"][gname] = {}
    for k in RUN:
        c = collections.defaultdict(collections.Counter)
        for f in facts:
            if f["id"] in gids:
                c[f["cat"]][f[k]] += 1
        summary["classes"][gname][k] = {cat: dict(v) for cat, v in c.items()}
    summary["extra"][gname] = {}
    for k in RUN:
        c = collections.defaultdict(collections.Counter)
        for x in extras_all:
            if x["id"] in gids and x["system"] == k:
                c[x["cat"]][x["cls"]] += 1
        summary["extra"][gname][k] = {cat: dict(v) for cat, v in c.items()}
# direct P00-vs-P01 fact comparison on both-parsed records
cmp = collections.Counter()
lists = collections.defaultdict(list)
for f in facts:
    a, b = f["P00"], f["P01"]
    if f["id"] in both_parsed:
        key = ("both_correct" if a == b == "CORRECT" else "P01_only_correct" if b == "CORRECT" and a != "CORRECT" else "P00_only_correct" if a == "CORRECT" and b != "CORRECT" else "neither_correct")
        cmp[key] += 1
        if key in ("P01_only_correct", "P00_only_correct"):
            lists[key].append(f"{f['id']} {f['cat']}: {f['gold_key']} (P00 {a}, P01 {b})")
summary["both_parsed_fact_comparison"] = dict(cmp)
summary["both_parsed_fact_lists"] = dict(lists)
summary["speaker_summary"] = {k: {"records_with_usable_output": sum(1 for i in IDS if speaker[i][k]),
                                  "all_speakers_correct": sum(1 for i in IDS if speaker[i][k] and speaker[i][k]["all_speakers_correct"]),
                                  "records_with_missing_speaker": sum(1 for i in IDS if speaker[i][k] and speaker[i][k]["missing_speakers"]),
                                  "records_with_wrong_role": sum(1 for i in IDS if speaker[i][k] and speaker[i][k]["wrong_role"]),
                                  "records_with_invented_speaker": sum(1 for i in IDS if speaker[i][k] and speaker[i][k]["invented_ids"])} for k in RUN}
ev_tot = {k: collections.Counter() for k in RUN}
for i in IDS:
    for k in RUN:
        if evid[i][k]:
            ev_tot[k].update(evid[i][k])
summary["evidence_totals"] = {k: dict(v) for k, v in ev_tot.items()}
# attribution detail on matched facts
attr = {k: collections.Counter() for k in RUN}
for i in IDS:
    for cat in CATEGORIES:
        for k in RUN:
            for r in per_rec[i]["gold_rows"][cat][k]:
                for t in r.get("tags", []):
                    attr[k][t] += 1
                for dd in r.get("detail", []):
                    if "speaker id written instead of role" in dd:
                        attr[k]["person_id_instead_of_role"] += 1
summary["matched_fact_issue_tags"] = {k: dict(v) for k, v in attr.items()}
(OUT / "AUDIT_SUMMARY.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")

# ------------------------------------------------------------------ markdown (record by record)
ABBR = {"CORRECT": "CORRECT", "PARTIAL": "PARTIAL", "MISSED": "MISSED", "WRONG_STATUS": "WRONG_STATUS", "WRONG_ATTRIBUTION": "WRONG_ATTRIB", "WRONG_NORMALIZATION": "WRONG_NORM", "UNSUPPORTED": "UNSUPPORTED", "INCORRECT": "INCORRECT"}


def cell(r):
    s = ABBR[r["cls"]]
    if r["cls"] == "MISSED" and r["detail"]:
        return "NO OUTPUT (record failed)"
    if r["cls"] in ("PARTIAL", "WRONG_STATUS", "WRONG_ATTRIBUTION", "UNSUPPORTED") and r["detail"]:
        return s + ": " + "; ".join(r["detail"])[:150]
    if r["cls"] == "WRONG_NORMALIZATION":
        return s + f" ('{r['pred_key']}')"
    return s


def esc(t):
    return str(t).replace("|", "/").replace("\n", " ")


md = ["# P00 / P01 record-by-record clinical extraction gap analysis (Qwen3-1.7B, 30 development records)", "",
      "**DEVELOPMENT-ONLY.** Labels are generator-derived; the 50 prompt-development records were used earlier for 0.6B prompt development. Not independent or clinical validation.", "",
      "Source of every row: transcript (`dataset_v2_batch_001_corrected/output/inputs`) -> gold label (`.../output/labels`) -> P00 raw/parsed output -> P01 raw/parsed output. Data tables behind this report: "
      "`evaluations/p00_p01_audit/{RECONCILIATION.json, AUDIT_GOLD_FACTS.jsonl, AUDIT_EXTRA_PREDICTIONS.jsonl, SPEAKER_AUDIT.json, EVIDENCE_AUDIT.json, AUDIT_SUMMARY.json}`.", "",
      "Class legend: CORRECT / PARTIAL (matched, a detail differs) / MISSED / INCORRECT / UNSUPPORTED / WRONG_ATTRIB / WRONG_STATUS / WRONG_NORM (same fact, different surface form: the strict matcher scores it a miss + a false positive) / "
      "EVIDENCE_ERROR (section 'Evidence') / N/A (category absent in gold and prediction). `NO OUTPUT` = the record's JSON was truncated/invalid, so nothing was extracted.", "",
      "## 1. Reconciliation (Phase 1)", "",
      f"Frozen ids = first 30 of `FROZEN_50_PROMPT_DEV_IDS.json` (`{IDS[0]}` .. `{IDS[-1]}`, not sequential). Duplicate ids: {dups or 'none'}. Unexpected extra P01 files: {extra_p01 or 'none'}. "
      "Every file's inner `encounter_id` was checked against the id (not just the filename). P00 files for the other 20 frozen ids exist but were not used.", "",
      "| ID | Segs | Transcript id | Gold id | P00 raw/parsed id | P00 status | P01 raw/parsed id | P01 status | Matched |", "|---|---:|---|---|---|---|---|---|---|"]
for r in recon:
    def st(k):
        x = r[k]
        return f"{x['raw_id_inside']}/{x['parsed_id_inside'] or 'failed-file'}", f"{x['manifest_status']}" + (f" ({x['finish_reason']}, {x['completion_tokens']} tok)" if x["manifest_status"] == "failed" else "")
    a, b = st("P00"), st("P01")
    md.append(f"| {r['id']} | {r['transcript_segments']} | {r['transcript_id_inside']} | {r['label_id_inside']} | {a[0]} | {a[1]} | {b[0]} | {b[1]} | {'YES' if r['matched_ok'] else '**NO**'} |")
md += ["", f"All 30 records: transcript, label, P00 output and P01 output are present, correctly matched by inner encounter id, and exactly one of parsed/failed exists per output. Missing: none. Mismatched: none. Inaccessible: none.", "",
       "Both-parsed (20): " + ", ".join(both_parsed) + ".  Recovered by P01 (P00 failed): " + ", ".join(i for i in IDS if rec[i]['pred']['P00'] is None and rec[i]['pred']['P01'] is not None)
       + ".  Lost by P01: " + ", ".join(i for i in IDS if rec[i]['pred']['P00'] is not None and rec[i]['pred']['P01'] is None) + ".  Failed in both: " + ", ".join(i for i in IDS if rec[i]['pred']['P00'] is None and rec[i]['pred']['P01'] is None) + ".", ""]

ORDER = ["CORRECT", "PARTIAL", "WRONG_NORMALIZATION", "WRONG_STATUS", "WRONG_ATTRIBUTION", "UNSUPPORTED", "MISSED"]
SH = {"CORRECT": "OK", "PARTIAL": "PART", "WRONG_NORMALIZATION": "NORM", "WRONG_STATUS": "STAT", "WRONG_ATTRIBUTION": "ATTR", "UNSUPPORTED": "UNSUP", "MISSED": "MISS"}


def agg_table(gname):
    out = ["| Category | Gold facts | P00: " + " / ".join(SH[o] for o in ORDER) + " | P01: " + " / ".join(SH[o] for o in ORDER) + " |", "|---|---:|---|---|"]
    tot = {k: collections.Counter() for k in RUN}
    for cat in CATEGORIES:
        a = summary["classes"][gname]["P00"].get(cat, {})
        b = summary["classes"][gname]["P01"].get(cat, {})
        n = sum(a.values())
        if n == 0 and not summary["extra"][gname]["P00"].get(cat) and not summary["extra"][gname]["P01"].get(cat):
            continue
        tot["P00"].update(a)
        tot["P01"].update(b)
        out.append(f"| {label(cat)} | {n} | " + " / ".join(str(a.get(o, 0)) for o in ORDER) + " | " + " / ".join(str(b.get(o, 0)) for o in ORDER) + " |")
    n = sum(tot["P00"].values())
    out.append(f"| **TOTAL** | {n} | " + " / ".join(str(tot["P00"].get(o, 0)) for o in ORDER) + " | " + " / ".join(str(tot["P01"].get(o, 0)) for o in ORDER) + " |")
    return out


def _f3(x):
    return f"{x.get('EXTRA_SUPPORTED_BY_TRANSCRIPT', 0)} / {x.get('UNSUPPORTED', 0)} / {x.get('INCORRECT', 0)}"


def extra_table(gname):
    out = ["| Category | P00 extra: supported-by-transcript / UNSUPPORTED / INCORRECT | P01 extra: supported / UNSUPPORTED / INCORRECT |", "|---|---|---|"]
    tot = {k: collections.Counter() for k in RUN}
    for cat in CATEGORIES:
        a = summary["extra"][gname]["P00"].get(cat, {})
        b = summary["extra"][gname]["P01"].get(cat, {})
        if not a and not b:
            continue
        tot["P00"].update(a)
        tot["P01"].update(b)
        out.append(f"| {label(cat)} | {_f3(a)} | {_f3(b)} |")
    out.append(f"| **TOTAL** | {_f3(tot['P00'])} | {_f3(tot['P01'])} |")
    return out


ev = summary["evidence_totals"]
n_one = {k: sum(1 for i in IDS if evid[i][k] and evid[i][k]["evidence_records"] == 1) for k in RUN}
n_par = {k: sum(1 for i in IDS if evid[i][k]) for k in RUN}
sps = summary["speaker_summary"]
md += ["## 1b. Method, definitions and limits of this audit", "",
       "- **Unit of audit:** every gold fact (1,093 across the 30 records, the same total the strict evaluator uses: TP+FN) and every extra predicted fact, per category, per prompt. Row-level data: `AUDIT_GOLD_FACTS.jsonl`, `AUDIT_EXTRA_PREDICTIONS.jsonl`.",
       "- **Classification** (priority for a matched fact with several issues: WRONG_STATUS > WRONG_ATTRIB > PARTIAL > UNSUPPORTED):",
       "  - CORRECT = the strict matcher links the gold and predicted fact and every checked attribute agrees (status, temporality, certainty, severity, duration, frequency, dose, route, value/unit, reported_by/observed_by/stated_by, relation ...).",
       "  - PARTIAL = matched, but a detail (dose, route, frequency, duration, severity, reaction, value, unit, time, type) differs. WRONG_STATUS / WRONG_ATTRIB = matched, but a status-like or speaker-like attribute is wrong (including a speaker id such as `person_1` written instead of a role). UNSUPPORTED (on a matched fact) = a detail was added that gold does not have (here: an invented `route`).",
       "  - WRONG_NORM = the fact is present in the output but in a form the strict matcher cannot link. Two sub-cases: (a) the evaluator's own fuzzy matcher links it; (b) **audit heuristic, not part of the evaluator**: an unmatched prediction in the same category whose words lie inside the transcript segment that best expresses the gold fact and that shares a word with the gold fact's own wording (for example gold 'Polydipsia' vs predicted 'constant thirst'). Heuristic (b) can over- or under-link; it is used only for this audit and never for the headline metrics.",
       "  - MISSED = no usable prediction for the fact. Records whose JSON failed are shown as NO OUTPUT and counted as MISSED.",
       "  - Extras (no gold counterpart): INCORRECT = recognisably wrong (a placeholder or a medication written as an allergy, or the fact exists in gold under another category); UNSUPPORTED = its content words do not appear in the transcript; 'supported by transcript' = present in the transcript but not in gold (extra but true, or a paraphrase the matcher cannot link).",
       "  - EVIDENCE_ERROR is reported in the per-record Evidence lines and in the evidence table below, not per fact.",
       "- **Not asserted:** the audit judges only against the gold label and the transcript text; gold labels are generator-derived, not human-verified.", ""]
md += ["## 1c. Aggregate class counts", "", "### Records completed by BOTH prompts (20 records): extraction on identical, parsed outputs", ""] + agg_table("both_parsed20")
md += ["", "(OK correct, PART partial, NORM wrong normalisation / surface form, STAT wrong status, ATTR wrong attribution, UNSUP matched fact with an unsupported added detail, MISS missed.)", "",
       "### All 30 records (failed outputs count as MISSED, as in the headline scoring)", ""] + agg_table("all30")
md += ["", "### Extra predictions with no gold counterpart (all 30 records)", ""] + extra_table("all30")
cmpd = summary["both_parsed_fact_comparison"]
md += ["", "### Facts that differ between P00 and P01 on the 20 records both completed (CORRECT in one prompt only)", "",
       f"Counts: both correct {cmpd.get('both_correct')}, P01 only {cmpd.get('P01_only_correct')}, P00 only {cmpd.get('P00_only_correct')}, neither {cmpd.get('neither_correct')}.", "", "P01 only:"]
md += [f"- {x}" for x in summary["both_parsed_fact_lists"].get("P01_only_correct", [])] + ["", "P00 only:"] + [f"- {x}" for x in summary["both_parsed_fact_lists"].get("P00_only_correct", [])]
md += ["", "### Speakers (A), 30 records", "", "| | P00 | P01 |", "|---|---:|---:|",
       f"| Records with usable output | {sps['P00']['records_with_usable_output']} | {sps['P01']['records_with_usable_output']} |",
       f"| All transcript speakers listed with the correct role | {sps['P00']['all_speakers_correct']} | {sps['P01']['all_speakers_correct']} |",
       f"| Records with at least one speaker missing | {sps['P00']['records_with_missing_speaker']} | {sps['P01']['records_with_missing_speaker']} |",
       f"| Records with a wrong role / an invented speaker | {sps['P00']['records_with_wrong_role']} / {sps['P00']['records_with_invented_speaker']} | {sps['P01']['records_with_wrong_role']} / {sps['P01']['records_with_invented_speaker']} |",
       "", f"Matched-fact issue tags: P00 {summary['matched_fact_issue_tags']['P00']}; P01 {summary['matched_fact_issue_tags']['P01']}.", "",
       "### Evidence (L), parsed outputs", "", "| | P00 | P01 |", "|---|---:|---:|",
       f"| Parsed outputs | {n_par['P00']} | {n_par['P01']} |",
       f"| Outputs whose `clinical_evidence` holds exactly ONE record (every fact cites it) | {n_one['P00']} | {n_one['P01']} |",
       f"| Evidence records in total | {ev['P00'].get('evidence_records')} | {ev['P01'].get('evidence_records')} |",
       f"| ...that are an exact single transcript segment | {ev['P00'].get('ev_exact_single_segment', 0)} | {ev['P01'].get('ev_exact_single_segment', 0)} |",
       f"| ...that are multi-segment / whole-transcript dumps | {ev['P00'].get('ev_multi_segment_or_whole_transcript_dump', 0)} | {ev['P01'].get('ev_multi_segment_or_whole_transcript_dump', 0)} |",
       f"| ...with empty `supports` | {ev['P00'].get('ev_empty_supports', 0)} | {ev['P01'].get('ev_empty_supports', 0)} |",
       f"| Facts checked | {ev['P00'].get('facts_checked')} | {ev['P01'].get('facts_checked')} |",
       f"| Facts with NO evidence id at all | {ev['P00'].get('fact_no_evidence_ids', 0)} | {ev['P01'].get('fact_no_evidence_ids', 0)} |",
       f"| Facts whose cited text does not mention the fact | {ev['P00'].get('fact_not_mentioned_in_cited_text', 0)} | {ev['P01'].get('fact_not_mentioned_in_cited_text', 0)} |",
       f"| ...of which cite the greeting / intro segment (first two segments) | {ev['P00'].get('fact_cites_intro_segment_unrelated', 0)} | {ev['P01'].get('fact_cites_intro_segment_unrelated', 0)} |",
       f"| Facts whose path is missing from the cited record's `supports` | {ev['P00'].get('fact_path_missing_from_supports', 0)} | {ev['P01'].get('fact_path_missing_from_supports', 0)} |",
       f"| Facts with usable evidence (text mentions the fact AND path in `supports`) | {ev['P00'].get('fact_evidence_ok', 0)} | {ev['P01'].get('fact_evidence_ok', 0)} |", ""]
md += ["## 2. Record-by-record audit", ""]
for i in IDS:
    d = rec[i]
    s = speaker[i]
    st0 = "parsed" if d["pred"]["P00"] else "FAILED"
    st1 = "parsed" if d["pred"]["P01"] else "FAILED"
    md += [f"### Record {i}   (P00: {st0}, P01: {st1})", ""]
    ts = ", ".join(f"{a} {b}" for a, b in s["transcript_speakers"])
    md.append(f"**Speakers (A).** Transcript: {ts}. Gold primary speakers: {', '.join(f'{a} {b}' for a, b in s['gold_primary_speakers'])}.")
    for k in RUN:
        x = s[k]
        if x is None:
            md.append(f"- {k}: no usable output.")
        else:
            md.append(f"- {k}: predicted {x['predicted']}; all speakers+roles correct: {x['all_speakers_correct']}; missing {x['missing_speakers'] or 'none'}; wrong role {x['wrong_role'] or 'none'}; invented ids {x['invented_ids'] or 'none'}.")
    # chief complaint
    cc = per_rec[i]["gold_rows"]["chief_complaint"]
    g_cc = d["gold"].get("chief_complaint") or {}
    md.append("")
    md.append(f"**Chief complaint (B).** Gold: '{g_cc.get('value')}' / normalized '{g_cc.get('normalized_value')}' (reported by {g_cc.get('reported_by')}).")
    for k in RUN:
        p = d["pred"][k]
        pc = (p or {}).get("chief_complaint") or {}
        r0 = cc[k][0] if cc[k] else None
        md.append(f"- {k}: " + ("no usable output." if p is None else f"'{pc.get('value')}' / normalized '{pc.get('normalized_value')}' (reported_by {pc.get('reported_by')}) -> {cell(r0) if r0 else 'n/a'}"))
    md.append("")
    na = []
    for cat in CATEGORIES:
        if cat == "chief_complaint":
            continue
        g0 = per_rec[i]["gold_rows"][cat]["P00"]
        e0, e1 = per_rec[i]["extra_rows"][cat]["P00"], per_rec[i]["extra_rows"][cat]["P01"]
        if not g0 and not e0 and not e1:
            na.append(label(cat))
            continue
        g1 = per_rec[i]["gold_rows"][cat]["P01"]
        md += [f"**{label(cat)}**", "", "| Gold fact | Transcript evidence (segment) | P00 | P01 |", "|---|---|---|---|"]
        for a, b in zip(g0, g1):
            ex = a["excerpt"]
            exs = f"{ex['segment_id']} {ex['speaker']}: \"{esc(ex['text'])[:90]}\"" if ex and ex["segment_id"] else (f"\"{esc(ex['text'])[:90]}\"" if ex else "-")
            attrs = ", ".join(f"{k_}={esc(json.dumps(v, ensure_ascii=False))[:25]}" for k_, v in list(a["gold_attrs"].items())[:3])
            md.append(f"| {esc(a['gold_key'])} ({esc(attrs)}) | {exs} | {esc(cell(a))} | {esc(cell(b))} |")
        for k, e in (("P00", e0), ("P01", e1)):
            if e:
                md.append(f"| *(extra {k})* | " + "; ".join(f"{esc(x['pred_key'])} [{x['cls']}{' - ' + x['detail'][0] if x['detail'] else ''}]" for x in e[:8]) + (f" (+{len(e) - 8} more)" if len(e) > 8 else "") + " | | |")
        md.append("")
    if not d["gold"]["encounter_metadata"]:
        pass
    md.append("**Not applicable (no gold fact and no prediction):** " + (", ".join(na) if na else "none") + ".")
    md.append("")
    md.append("**Evidence (L).**")
    for k in RUN:
        x = evid[i][k]
        if x is None:
            md.append(f"- {k}: no usable output.")
        else:
            bad = {a: b for a, b in x.items() if a.startswith(("ev_wrong", "ev_multi", "ev_text", "ev_near", "ev_empty", "fact_no", "fact_dangling", "fact_not", "fact_cites", "fact_path"))}
            md.append(f"- {k}: {x['evidence_records']} evidence records; {x.get('ev_exact_single_segment', 0)} are an exact single transcript segment; {x['facts_checked']} facts checked, {x.get('fact_evidence_ok', 0)} with usable evidence (cited text mentions the fact and the `supports` path lists it). Problems: {bad or 'none'}.")
    md.append("")
(OUT.parent.parent / "reports" / "P00_P01_RECORD_BY_RECORD_GAP_ANALYSIS.md").write_text("\n".join(md), encoding="utf-8")
print("records", len(IDS), "facts", len(facts), "extras", len(extras_all))
print(json.dumps(summary["both_parsed_fact_comparison"]), json.dumps(summary["speaker_summary"]))
