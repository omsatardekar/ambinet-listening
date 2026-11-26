"""Phase A driver: synthetic-only feasibility gates for S1.1 (see design/PHASE_A_GATES.json, fixed before this script ran).
Reads no project transcript/label/validation/locked-test/Batch 002 file. Builds its own OpenVINO GenAI pipeline per run; project inference code is not modified.
usage: python -B run_phase_a.py   (resumable: finished variants are cached in phase_a/results/)"""
import gc
import hashlib
import json
import sys
import time
from pathlib import Path

import openvino_genai as ovg

HERE = Path(__file__).resolve().parent
EXP7 = HERE.parent
ROOT = EXP7.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(EXP7 / "design"))
sys.path.insert(0, str(EXP7 / "feasibility"))
sys.dont_write_bytecode = True
import synth_gen as SG  # noqa: E402
import structured_feasibility as F  # noqa: E402  (provides validate() for the schema subset)
from direct_inference_baseline.inference.output_parser import parse_response  # noqa: E402  (the project's strict, non-repairing parser; fences/think only)

RES = HERE / "results"
RES.mkdir(exist_ok=True)
MODEL, CACHE, MAX_NEW = F.MODEL, F.CACHE, 2048
SCHEMA = F.SCHEMA
ROLES = ["doctor", "patient", "nurse", "caregiver", "family_member", "clinical_staff", "unknown"]
LAYOUT = {"R1": "Each line of the transcript starts with the speaker label (doctor, patient, nurse, caregiver, family_member, clinical_staff or unknown) followed by a colon, then what was said.",
          "R0": "Each line looks like [SEG0001] person_1 (ROLE) times: text. Ignore the segment ids, the speaker ids (person_N) and the times. The word in brackets (PATIENT, DOCTOR, NURSE ...) is the speaker label; write it in lower case in reported_by."}
PREFIX = '{"chief_complaint":"'
GRAMMARS = {"G1": ("S1_1_output_grammar.ebnf", False), "G2": ("S1_1_output_grammar_G2_cap20.ebnf", False), "G3": ("S1_1_output_grammar_G3_cap20_prefix.ebnf", True)}
PRIMARY = {"symptoms": "name", "negative_findings": "finding", "medical_history": "condition", "surgical_history": "procedure", "family_history": "condition", "social_history": "category",
           "medications": "name", "allergies": "substance", "vital_signs": "name", "physical_examination": "finding", "review_of_systems": "system", "clinical_assessment": "assessment",
           "investigations": "name", "procedures": "name", "clinical_actions": "description", "follow_up": "when"}
JUNK = {"", "none", "null", "n/a", "na", "unknown", "nothing", "-"}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def prompt_for(pname, mode, case):
    t = (EXP7 / "prompts" / f"S1_1_{pname}.txt").read_text(encoding="utf-8")
    return t.replace("{LAYOUT}", LAYOUT[mode]).replace("{TRANSCRIPT}", SG.render(SG.CASES[case][0], mode))


def generate(prompt, grammar_name=None):
    pipe = ovg.LLMPipeline(str(MODEL), "GPU", CACHE_DIR=str(CACHE))
    tok = pipe.get_tokenizer()
    text_in = tok.apply_chat_template([{"role": "user", "content": prompt}], add_generation_prompt=True, extra_context={"enable_thinking": False})
    g = pipe.get_generation_config()
    g.max_new_tokens, g.do_sample, g.apply_chat_template = MAX_NEW, False, False
    prefix = ""
    if grammar_name:
        gfile, prefixed = GRAMMARS[grammar_name]
        g.structured_output_config = ovg.StructuredOutputConfig(grammar=(EXP7 / "design" / gfile).read_text(encoding="utf-8"))
        if prefixed:
            prefix = PREFIX
            text_in += prefix
    t1 = time.perf_counter()
    res = pipe.generate([text_in], g)
    wall = time.perf_counter() - t1
    pm = res.perf_metrics
    n_out, n_in = int(pm.get_num_generated_tokens()), int(pm.get_num_input_tokens())
    out = {"text": prefix + res.texts[0], "gen_s": round(wall, 2), "in_tokens": n_in, "out_tokens": n_out, "cap_hit": n_out >= MAX_NEW}
    del pipe, res
    gc.collect()
    return out


def items(d, k):
    v = d.get(k)
    return [x for x in v if isinstance(x, dict)] if isinstance(v, list) else []


def score_case(case, out):
    exp = SG.CASES[case][1]
    r = {"case": case, "cap_hit": out["cap_hit"], "out_tokens": out["out_tokens"], "in_tokens": out["in_tokens"], "gen_s": out["gen_s"]}
    pr = parse_response(out["text"], "length" if out["cap_hit"] else "stop")
    r["parse_status"] = pr.status
    r["valid_json"] = pr.status == "ok"
    r["truncated"] = pr.status == "truncated"
    if not r["valid_json"]:
        return r
    d = pr.data
    errs = F.validate(d, SCHEMA, "$")
    r["schema_ok"] = not errs
    r["schema_error_count"] = len(errs)
    cc = str(d.get("chief_complaint", "")) if isinstance(d.get("chief_complaint", ""), str) else ""
    r["chief_ok"] = any(w.lower() in cc.lower() for w in exp["chief_keywords"])
    allempty = all(not items(d, k) for k in PRIMARY)
    r["empty_collapse"] = len(cc.strip()) < 4 or not any(c.isalnum() for c in cc) or allempty
    loops = []
    for k, f in PRIMARY.items():
        names = [str(x.get(f, "")).strip().lower() for x in items(d, k)]
        if len(names) >= 3 and (max(names.count(n) for n in set(names)) >= 3 or sum(n in JUNK for n in names) >= 3):
            loops.append(k)
    r["repetition_loop_sections"] = loops
    names_m = [(str(x.get("name", "")).lower(), str(x.get("reported_by", "")).lower(), str(x.get("status", ""))) for x in items(d, "medications")]
    em = exp["meds"]
    found = [(n, role) for n, st, role in em if any(n in nm for nm, rb, s in names_m)]
    r["meds_expected"], r["meds_found"] = len(em), len(found)
    r["meds_role_ok"] = sum(1 for n, st, role in em if any(n in nm and rb == role for nm, rb, s in names_m))
    r["allergy_status_ok"] = d.get("allergy_status") == exp["allergy_status"]
    vit = [(str(x.get("name", "")).lower(), str(x.get("reported_by", "")).lower()) for x in items(d, "vital_signs")]
    r["vitals_expected"], r["vitals_found"] = 3, sum(1 for n, role in exp["vitals"] if any(n == vn for vn, vr in vit))
    r["vitals_role_ok"] = sum(1 for n, role in exp["vitals"] if any(n == vn and vr == role for vn, vr in vit))
    sy = " | ".join(str(x.get("name", "")).lower() for x in items(d, "symptoms"))
    ng = " | ".join(str(x.get("finding", "")).lower() for x in items(d, "negative_findings"))
    iv = " | ".join(str(x.get("name", "")).lower() for x in items(d, "investigations") + items(d, "procedures"))
    fu = " | ".join(str(x.get("when", "")).lower() for x in items(d, "follow_up"))
    r["symptoms_expected"], r["symptoms_found"] = len(exp["symptoms"]), sum(1 for s in exp["symptoms"] if any(w in sy for w in s.split()[:1] + s.split()[-1:]))
    r["neg_expected"], r["neg_found"] = len(exp["negatives"]), sum(1 for n in exp["negatives"] if n in ng)
    r["inv_found"] = int(exp["investigations"][0] in iv)
    r["followup_found"] = int(exp["follow_up"] in fu)
    vals = [str(x.get("reported_by", "")) for k in PRIMARY for x in items(d, k) if "reported_by" in x]
    r["reported_by_total"], r["reported_by_outside_vocab"] = len(vals), sum(1 for v in vals if v not in ROLES)
    r["items_total"] = sum(len(items(d, k)) for k in PRIMARY)
    r["placeholder_values"] = sum(1 for k in PRIMARY for x in items(d, k) for v in x.values() if isinstance(v, str) and (v.startswith("<") and v.endswith(">")))
    return r


def run_variant(name, pname, mode, grammar):
    f = RES / f"{name}.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    rows, texts = [], {}
    for case in SG.CASES:
        o = generate(prompt_for(pname, mode, case), grammar)
        rows.append(score_case(case, o))
        texts[case] = o["text"]
        print(name, case, {k: rows[-1].get(k) for k in ("valid_json", "schema_ok", "cap_hit", "out_tokens", "gen_s", "empty_collapse", "chief_ok")}, flush=True)
    summary = summarize(rows)
    data = {"variant": name, "prompt": pname, "render": mode, "grammar": grammar, "rows": rows, "summary": summary, "texts": texts}
    f.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    return data


def summarize(rows):
    n = len(rows)
    ok = [r for r in rows if r["valid_json"]]
    s = {"n": n, "valid_json": len(ok), "schema_ok": sum(1 for r in ok if r.get("schema_ok")), "cap_hits": sum(r["cap_hit"] for r in rows), "truncated": sum(r["truncated"] for r in rows),
         "empty_collapse": sum(1 for r in ok if r["empty_collapse"]), "loops": sum(1 for r in ok if r["repetition_loop_sections"]),
         "chief_ok": sum(1 for r in ok if r["chief_ok"]), "allergy_status_ok": sum(1 for r in ok if r["allergy_status_ok"]),
         "out_tokens_mean": round(sum(r["out_tokens"] for r in rows) / n, 1), "gen_s_mean": round(sum(r["gen_s"] for r in rows) / n, 1)}
    s["meds_recall"] = round(sum(r["meds_found"] for r in ok) / max(1, sum(r["meds_expected"] for r in ok)), 3)
    matched = sum(r["meds_found"] for r in ok) + sum(r["vitals_found"] for r in ok)
    right = sum(r["meds_role_ok"] for r in ok) + sum(r["vitals_role_ok"] for r in ok)
    s["role_correct_of_matched"] = round(right / matched, 3) if matched else None
    s["reported_by_outside_vocab"] = sum(r["reported_by_outside_vocab"] for r in ok)
    s["placeholder_values"] = sum(r["placeholder_values"] for r in ok)
    for k, e, f in (("symptoms", "symptoms_expected", "symptoms_found"), ("negative_findings", "neg_expected", "neg_found"), ("vital_signs", "vitals_expected", "vitals_found")):
        s[f"recall_{k}"] = round(sum(r[f] for r in ok) / max(1, sum(r[e] for r in ok)), 3)
    s["recall_investigations"] = round(sum(r["inv_found"] for r in ok) / max(1, len(ok)), 3)
    s["recall_follow_up"] = round(sum(r["followup_found"] for r in ok) / max(1, len(ok)), 3)
    s["recall_medications"] = s["meds_recall"]
    return s


def gate_C(s):
    c = {"valid_json_10_of_10": s["valid_json"] == s["n"], "schema_ok_ge_9": s["schema_ok"] >= 9, "no_cap_or_truncation": s["cap_hits"] == 0 and s["truncated"] == 0,
         "no_empty_collapse": s["empty_collapse"] == 0, "no_repetition_loops": s["loops"] == 0, "chief_ok_ge_7": s["chief_ok"] >= 7, "meds_recall_ge_0.60": s["meds_recall"] >= 0.60,
         "allergy_status_ge_7": s["allergy_status_ok"] >= 7, "roles_correct_ge_0.90": (s["role_correct_of_matched"] or 0) >= 0.90, "no_role_outside_vocab": s["reported_by_outside_vocab"] == 0}
    for k in ("symptoms", "negative_findings", "medications", "vital_signs", "investigations", "follow_up"):
        c[f"no_collapse_{k}_recall_gt_0.20"] = s[f"recall_{k}"] > 0.20
    return c


if __name__ == "__main__":
    t0 = time.time()
    froz = {str(p.relative_to(EXP7)): sha(p) for p in [EXP7 / "design" / "PHASE_A_GATES.json", EXP7 / "prompts" / "S1_1_P1.txt", EXP7 / "prompts" / "S1_1_P2.txt", EXP7 / "design" / "S1_1_output_schema.json",
                                                         EXP7 / "design" / "S1_1_output_grammar.ebnf", EXP7 / "design" / "S1_1_output_grammar_G2_cap20.ebnf",
                                                         EXP7 / "design" / "S1_1_output_grammar_G3_cap20_prefix.ebnf", HERE / "synth_gen.py", Path(__file__)]}
    (EXP7 / "manifests" / "PHASE_A_FREEZE.json").write_text(json.dumps({"files": froz, "note": "hashed before Phase A inference"}, indent=1), encoding="utf-8")
    print("openvino_genai", ovg.__version__, flush=True)
    result = {"started": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "frozen_sha256": froz}
    # stage 1: prompt selection (unconstrained, R1)
    u = {p: run_variant(f"U_{p}_R1", p, "R1", None) for p in ("P1", "P2")}
    sel = sorted(("P1", "P2"), key=lambda p: (-u[p]["summary"]["valid_json"], -(u[p]["summary"]["meds_recall"] + u[p]["summary"]["recall_symptoms"]), p != "P1"))[0]
    result["prompt_selected"] = sel
    result["prompt_stage"] = {p: u[p]["summary"] for p in u}
    # gate P
    u0 = run_variant(f"U_{sel}_R0", sel, "R0", None)
    sP1, sP0 = u[sel]["summary"], u0["summary"]
    gp = {"valid_json_R1_ge_7": sP1["valid_json"] >= 7, "valid_json_R0_ge_7": sP0["valid_json"] >= 7, "cap_hits_R1_le_1": sP1["cap_hits"] <= 1, "cap_hits_R0_le_1": sP0["cap_hits"] <= 1}
    result["gate_P"] = {"criteria": gp, "passed": all(gp.values()), "R1": sP1, "R0": sP0}
    # gate C
    result["gate_C"] = {"variants": {}, "passed": False, "selected_variant": None}
    if result["gate_P"]["passed"] or True:      # constrained variants are still measured so that the failure is characterised; arms are decided by the rules in PHASE_A_GATES.json
        for gname in ("G1", "G2", "G3"):
            v = run_variant(f"C_{sel}_R1_{gname}", sel, "R1", gname)
            cr = gate_C(v["summary"])
            result["gate_C"]["variants"][gname] = {"summary": v["summary"], "criteria": cr, "passed": all(cr.values())}
            if all(cr.values()):
                result["gate_C"].update(passed=True, selected_variant=gname)
                break
    result["decision"] = {"B1_B2": "run" if result["gate_P"]["passed"] else "do not run", "B3": "run" if (result["gate_P"]["passed"] and result["gate_C"]["passed"]) else "do not run",
                          "B3_variant": result["gate_C"]["selected_variant"]}
    result["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    result["elapsed_minutes"] = round((time.time() - t0) / 60, 1)
    (EXP7 / "manifests" / "PHASE_A_RESULT.json").write_text(json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result["decision"]), json.dumps(result["prompt_stage"]), flush=True)
