"""Analysis of invalid / truncated outputs and token budgets for P00 and P01 (30 shared ids).  NO inference; only saved raw outputs, the tokenizer files of the pinned snapshot and the frozen evaluator.
Diagnostic structural-closure test: for each failed output, cut at the last complete element boundary and close the open containers (no content is added); then validate and score
with the strict evaluator.  Closed outputs are DIAGNOSTICS ONLY: they are flagged incomplete and are never counted as complete results.
usage: python -B -s analyse_truncation_tokens.py"""
import collections
import json
import re
import statistics as st
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
TRACK = HERE.parents[3]
sys.path.insert(0, str(TRACK / "scripts"))
import common_1_7b as C  # noqa: E402

sys.path.insert(0, str(C.EXP6 / "s1"))
import evaluate_s1 as E  # noqa: E402
from direct_inference_baseline.evaluation import evaluation_runner as ER, schema_validator as SV  # noqa: E402
from direct_inference_baseline.evaluation.entity_matching import CATEGORIES, entity_list, match_category, prf  # noqa: E402
from transformers import AutoTokenizer  # noqa: E402

E1, E2 = TRACK / "experiments" / "EXP_001_DIRECT_INFERENCE", TRACK / "experiments" / "EXP_002_PROMPTING_INFERENCE"
RUN = {"P00": (E1, "P00_direct_dev50", TRACK / "prompts" / "P00_direct_inference_prompt.txt"), "P01": (E2, "P01_schema_guided_dev50", E2 / "prompt_versions" / "P01_schema_guided.txt")}
OUT = E2 / "evaluations" / "p00_p01_audit"
IDS = json.loads((TRACK / "manifests" / "FROZEN_50_PROMPT_DEV_IDS.json").read_text(encoding="utf-8"))["ids"][:30]
man = {k: json.loads((e / "evaluations" / r / "run_manifest.json").read_text(encoding="utf-8-sig"))["records"] for k, (e, r, _) in RUN.items()}
tokz = AutoTokenizer.from_pretrained(str(C.HF_CACHE / "models--Qwen--Qwen3-1.7B" / "snapshots" / C.REVISION), local_files_only=True)


def ntok(t):
    return len(tokz(t, add_special_tokens=False)["input_ids"])


KEYS = ["encounter_id", "extraction_status", "encounter_metadata", "chief_complaint", "symptoms", "negative_findings", "medical_history", "medications", "allergies", "vital_signs", "physical_examination",
        "review_of_systems", "clinical_conditions", "clinical_assessment", "procedures_and_investigations", "clinical_actions", "follow_up", "clinical_uncertainties", "clinical_evidence", "quality_checks"]


def sections(text):
    """split raw text at the top-level keys (first occurrence of each key at 2-space indent or as a compact key after the opening brace/comma)"""
    pos = []
    for k in KEYS:
        m = re.search(r'(?:\n  |[{,]\s*)"%s"\s*:' % re.escape(k), text)
        if m:
            pos.append((m.start(), k))
    pos.sort()
    out = {}
    for n, (p, k) in enumerate(pos):
        q = pos[n + 1][0] if n + 1 < len(pos) else len(text)
        out[k] = text[p:q]
    return out


def strip_wrappers(t):
    t = t.strip()
    t = re.sub(r"^```(?:json)?\s*", "", t)
    return t


def close_structurally(text):
    """cut at the last complete element boundary and close open containers; returns (obj|None, info)"""
    t = strip_wrappers(text)
    stack, in_str, esc = [], False, False
    snaps = []
    for n, ch in enumerate(t):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch in "{[":
            stack.append(ch)
        elif ch in "}]":
            if not stack:
                break
            stack.pop()
            snaps.append((n + 1, "".join(stack)))
    info = {"state_at_cut": {"inside_string": in_str, "open_containers": len(stack)}}
    for end, stk in reversed(snaps):
        cand = t[:end] + "".join("}" if c == "{" else "]" for c in reversed(stk))
        try:
            obj = json.loads(cand)
        except Exception:  # noqa: BLE001
            continue
        info.update(chars_kept=end, chars_discarded=len(t) - end, closers_added="".join("}" if c == "{" else "]" for c in reversed(stk)), discarded_tail=t[end:][:160])
        return obj, info
    return None, info


rows, tokens_rows = [], []
spy = C.G.StrictAccessSpy(allow_validation=False)
prompt_tok = {}
for k, (e, r, pp) in RUN.items():
    tpl = pp.read_text(encoding="utf-8")
    prompt_tok[k] = {"template_tokens_without_transcript": ntok(tpl.replace("{TRANSCRIPT}", "").replace("{ENCOUNTER_ID}", "00000")), "template_chars": len(tpl)}
trans_tok = {}
with spy:
    for i in IDS:
        tr = json.loads((C.S.INPUT_DIR / f"encounter_{i}.json").read_text(encoding="utf-8"))
        text = "\n".join(f"[{s['segment_id']}] {s['speaker_id']} ({s['role']}) {s['start_seconds']:.2f}-{s['end_seconds']:.2f}s: {s['text']}" for s in tr["segments"])
        trans_tok[i] = {"transcript_tokens": ntok(text), "segments": len(tr["segments"]), "transcript_chars": len(text)}
    gold = {i: ER.load_gold(i) for i in IDS}

failures = {}
repaired = {k: {} for k in RUN}
for k, (e, r, pp) in RUN.items():
    for i in IDS:
        raw = json.loads((e / "outputs" / "raw" / r / f"encounter_{i}.json").read_text(encoding="utf-8"))
        t = raw["response_text"]
        rec = man[k][i]
        secs = sections(t)
        st_ = {s: ntok(x) for s, x in secs.items()}
        total = ntok(t)
        tokens_rows.append({"run": k, "id": i, "status": rec["status"], "completion_tokens_reported": rec.get("completion_tokens"), "tokens_retokenised": total, "section_tokens": st_,
                            "prompt_tokens": rec.get("prompt_tokens"), "latency_s": rec.get("latency_seconds")})
        if rec["status"] == "failed":
            obj, info = close_structurally(t)
            last = [s for s in KEYS if s in secs][-1] if secs else None
            lines = [x for x in t.split("\n") if x.strip()]
            tail = t[-400:]
            rep = {"id": i, "run": k, "finish_reason": rec.get("finish_reason"), "failure_type": rec.get("failure_type"), "completion_tokens": rec.get("completion_tokens"), "parse_note": (rec.get("parse_notes") or [None])[0],
                   "last_section_started": last, "sections_started": [s for s in KEYS if s in secs], "chars": len(t), "tail_300_chars": t[-300:],
                   "repeated_line_share": round(1 - len(set(lines)) / max(1, len(lines)), 3), "evidence_tokens": st_.get("clinical_evidence", 0), "closure": info, "closure_ok": obj is not None}
            if obj is not None:
                v = SV.validate(obj)
                present = [s for s in KEYS if s in obj]
                rep["closure_missing_top_level_keys"] = [s for s in KEYS if s not in obj]
                rep["closure_all_clinical_sections_present"] = all(s in obj for s in KEYS[:18])
                rep["closure_schema_violation_kinds"] = dict(collections.Counter(x["kind"] for x in v.violations))
                repaired[k][i] = obj
            failures.setdefault(k, []).append(rep)
(OUT / "TRUNCATION_ANALYSIS.json").write_text(json.dumps({"failures": failures, "prompt_tokens": prompt_tok, "transcript_tokens": trans_tok}, indent=1, ensure_ascii=False), encoding="utf-8")
(OUT / "TOKEN_BREAKDOWN.json").write_text(json.dumps(tokens_rows, indent=1), encoding="utf-8")

# ---- diagnostic scoring: strict micro with structurally closed outputs substituted for failed records (NOT a headline; incomplete outputs)
def parsed_of(k, i):
    e, r, _ = RUN[k]
    p = e / "outputs" / "parsed" / r / f"encounter_{i}.json"
    if p.exists():
        d = json.loads(p.read_text(encoding="utf-8"))
        return d.get("parsed", d) if isinstance(d, dict) and "parsed" in d else d
    return None


def micro(k, use_repair):
    t = collections.Counter()
    per = {}
    for i in IDS:
        p = parsed_of(k, i)
        src = "parsed" if p is not None else None
        if p is None and use_repair and i in repaired[k]:
            p, src = repaired[k][i], "structurally_closed(incomplete)"
        c = collections.Counter()
        for cat in CATEGORIES:
            m = match_category(entity_list(gold[i], cat), entity_list(p or {}, cat), cat)
            c["tp"] += m["tp"]; c["fp"] += m["fp"]; c["fn"] += m["fn"]
        t.update(c)
        per[i] = src
    return {**prf(t["tp"], t["fp"], t["fn"]), "tp": t["tp"], "fp": t["fp"], "fn": t["fn"]}


diag = {k: {"as_scored_failed_equals_zero": micro(k, False), "diagnostic_with_structural_closure": micro(k, True)} for k in RUN}
# micro on the records whose closure was used only
(OUT / "CLOSURE_DIAGNOSTIC_SCORES.json").write_text(json.dumps({"note": "DIAGNOSTIC ONLY. Structurally closed outputs are incomplete (evidence tail and/or quality_checks missing) and are not part of any headline.", **diag}, indent=1), encoding="utf-8")

# ---- aggregates
def agg(k):
    rs = [r for r in tokens_rows if r["run"] == k]
    out = {}
    for sec in ("encounter_metadata", "chief_complaint", "symptoms", "negative_findings", "medical_history", "medications", "allergies", "vital_signs", "physical_examination", "review_of_systems",
                "clinical_conditions", "clinical_assessment", "procedures_and_investigations", "clinical_actions", "follow_up", "clinical_uncertainties", "clinical_evidence", "quality_checks"):
        v = [r["section_tokens"].get(sec, 0) for r in rs if r["status"] == "parsed"]
        out[sec] = round(st.mean(v), 1) if v else 0
    parsed = [r for r in rs if r["status"] == "parsed"]
    tot = st.mean(r["tokens_retokenised"] for r in parsed)
    out["_mean_total_tokens_parsed"] = round(tot, 1)
    out["_evidence_share_of_output_parsed"] = round(out["clinical_evidence"] / tot, 3)
    return out


summary = {"prompt_tokens": prompt_tok, "transcript_tokens_mean": round(st.mean(v["transcript_tokens"] for v in trans_tok.values()), 0), "transcript_tokens_max": max(v["transcript_tokens"] for v in trans_tok.values()),
           "section_token_means_parsed_outputs": {k: agg(k) for k in RUN}, "closure_diagnostic": diag,
           "failed_summary": {k: [{x: f[x] for x in ("id", "finish_reason", "completion_tokens", "last_section_started", "evidence_tokens", "closure_ok", "closure_all_clinical_sections_present", "closure_missing_top_level_keys")} for f in failures.get(k, [])] for k in RUN}}
# what-if arithmetic: tokens if evidence section were absent (analysis only)
what = {}
for k in RUN:
    rs = [r for r in tokens_rows if r["run"] == k and r["status"] == "parsed"]
    non_ev = [r["tokens_retokenised"] - r["section_tokens"].get("clinical_evidence", 0) for r in rs]
    what[k] = {"mean_tokens_parsed": round(st.mean(r["tokens_retokenised"] for r in rs)), "mean_tokens_without_evidence_section": round(st.mean(non_ev)), "max_without_evidence": max(non_ev)}
summary["what_if_no_evidence_section_arithmetic"] = what
# for failed outputs: how many tokens did non-evidence content use (cap 4096)
fe = {}
for k in RUN:
    fe[k] = [{"id": r["id"], "tokens_total": r["tokens_retokenised"], "evidence_tokens_emitted_before_cut": r["section_tokens"].get("clinical_evidence", 0), "non_evidence_tokens": r["tokens_retokenised"] - r["section_tokens"].get("clinical_evidence", 0)}
             for r in tokens_rows if r["run"] == k and r["status"] == "failed"]
summary["failed_outputs_token_split"] = fe
(OUT / "TRUNCATION_TOKEN_SUMMARY.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
print(json.dumps({"prompt_tokens": prompt_tok, "transcript_tokens_mean": summary["transcript_tokens_mean"], "diag": diag, "what_if": what}, indent=1))
print(json.dumps(summary["section_token_means_parsed_outputs"], indent=0)[:1800])
