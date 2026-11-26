"""Isolated technical feasibility test: OpenVINO GenAI structured decoding and role-labelled rendering, on SYNTHETIC hand-written transcripts only.
Reads no project transcript, label, validation or locked-test file. Builds its own pipeline; the project inference runtime is not imported or modified.
usage: python -B structured_feasibility.py smoke | run   (cwd anywhere; results -> feasibility/results/)"""
import gc
import json
import sys
import time
from pathlib import Path

import openvino_genai as ovg
import psutil

HERE = Path(__file__).resolve().parent
EXP7 = HERE.parent
MODEL = EXP7.parent / "EXP_002_QWEN3_0.6B_GPU_DIRECT" / "models" / "Qwen3-0.6B-ov-fp16"
CACHE = EXP7 / "ov_cache"
SCHEMA = json.loads((EXP7 / "design" / "S1_1_output_schema.json").read_text(encoding="utf-8"))
RES = HERE / "results"
RES.mkdir(exist_ok=True)

# (speaker_id, ROLE, start, text) -- invented consultations, no relation to project data
CASES = {
 "syn1": [("person_1", "PATIENT", 1.0, "Hello doctor."), ("person_2", "DOCTOR", 4.2, "Hello, come in. What brings you in today?"),
          ("person_1", "PATIENT", 9.0, "I have had a sore throat and a dry cough for three days."), ("person_2", "DOCTOR", 16.5, "Any fever or trouble breathing?"),
          ("person_1", "PATIENT", 21.0, "No fever. No trouble breathing."), ("person_2", "DOCTOR", 26.0, "Do you take any regular medicines?"),
          ("person_1", "PATIENT", 30.1, "Yes, amlodipine five milligrams once a day for my blood pressure."), ("person_2", "DOCTOR", 37.0, "Any allergies to medicines?"),
          ("person_1", "PATIENT", 41.0, "Yes, penicillin gives me a rash."), ("person_3", "NURSE", 47.0, "Your temperature is 36.8 and your pulse is 78."),
          ("person_2", "DOCTOR", 55.0, "It looks like a viral throat infection. I will prescribe paracetamol five hundred milligrams when needed. Come back in one week if it is not better.")],
 "syn2": [("person_2", "DOCTOR", 2.0, "Good morning. What is the problem?"), ("person_1", "PATIENT", 6.0, "My right knee has been swollen since I fell last week."),
          ("person_2", "DOCTOR", 13.0, "Do you smoke or drink?"), ("person_1", "PATIENT", 17.0, "I never smoked. I have a drink at weekends."),
          ("person_2", "DOCTOR", 24.0, "Any past operations?"), ("person_1", "PATIENT", 27.0, "I had my appendix out as a child."),
          ("person_2", "DOCTOR", 33.0, "Let us get an x-ray of the knee. Take ibuprofen four hundred milligrams three times a day with food."),
          ("person_1", "PATIENT", 42.0, "I do not have any allergies.")],
 "syn3": [("person_1", "PATIENT", 1.5, "Hi, I am here for my cholesterol check."), ("person_2", "DOCTOR", 5.0, "Are you still taking atorvastatin?"),
          ("person_1", "PATIENT", 9.0, "I stopped it last month because of muscle pain, and now I take nothing."), ("person_2", "DOCTOR", 16.0, "Does anyone in your family have heart disease?"),
          ("person_1", "PATIENT", 20.0, "My father had a heart attack at sixty."), ("person_2", "DOCTOR", 27.0, "I would like a blood test for your lipids. Let us review in two weeks.")],
}

HEAD = ("You are a clinical information extraction system. Read the outpatient consultation below and extract the clinical facts the speakers state. "
        "Return ONE JSON object and nothing else.\n\n")
RULES = ("Rules\n- Extract only what is stated. Never invent medicines, doses, allergies, symptoms, diagnoses, findings, vital signs, tests, plans or dates. Use an empty list when nothing was stated.\n"
         "- A doctor's question is not a fact; use the answer.\n- One item per fact, no repeats. Keep names short, lower case, in the speaker's words.\n"
         "- Negative findings: name the thing that is absent without 'no' or 'not'. A symptom is never in both symptoms and negative_findings.\n"
         "- Medicines: one item per medicine with only its own dose, route and frequency. status current = taken now, stopped = was taken but stopped, new = started in this visit.\n"
         "- allergy_status: reported, none_stated (patient clearly said no allergies), unknown, or not_asked. A medicine the patient takes is not an allergy.\n"
         "- Never write dates or clock times unless said. follow_up 'when' is the words said.\n\n"
         "Fields\n- chief_complaint: the patient's own main reason for coming, as a short phrase (the patient's answer, not the doctor's question).\n"
         "- symptoms (name, status present/resolved, duration), negative_findings, medical_history, surgical_history, family_history (condition, relation), social_history, medications, allergies, "
         "vital_signs, physical_examination, review_of_systems, clinical_assessment (provisional or differential), investigations, procedures, clinical_actions, follow_up.\n"
         "- reported_by: the speaker label of the line where the fact was said.\n\n")


def render(case, mode):
    if mode == "R0":   # original format, ids and times visible
        return "\n".join(f"[SEG{i + 1:04d}] {sp} ({role}) {t:.2f}-{t + 3:.2f}s: {txt}" for i, (sp, role, t, txt) in enumerate(case))
    return "\n".join(f"{role.lower()}: {txt}" for sp, role, t, txt in case)   # R1: role word is the label, no ids, no times


def build_prompt(case, mode):
    lay = ("Each line looks like [SEG0001] person_1 (ROLE) times: text. Ignore ids and times. reported_by is the ROLE in brackets (patient, doctor, nurse...), never person_N.\n\n" if mode == "R0"
           else "Each line starts with the speaker label (doctor, patient, nurse, ...) and a colon. reported_by is that label.\n\n")
    return HEAD + lay + RULES + "Transcript\n" + render(case, mode) + "\n\nJSON:"


def run_one(prompt, constrained, max_new, device="GPU"):
    proc = psutil.Process()
    t0 = time.perf_counter()
    pipe = ovg.LLMPipeline(str(MODEL), device, CACHE_DIR=str(CACHE))
    load_s = time.perf_counter() - t0
    tok = pipe.get_tokenizer()
    text_in = tok.apply_chat_template([{"role": "user", "content": prompt}], add_generation_prompt=True, extra_context={"enable_thinking": False})
    g = pipe.get_generation_config()
    g.max_new_tokens, g.do_sample, g.apply_chat_template = max_new, False, False
    if constrained:
        g.structured_output_config = ovg.StructuredOutputConfig(json_schema=json.dumps(SCHEMA))
    t1 = time.perf_counter()
    res = pipe.generate([text_in], g)
    wall = time.perf_counter() - t1
    pm = res.perf_metrics
    out = {"text": res.texts[0], "load_s": round(load_s, 2), "gen_s": round(wall, 2), "in_tokens": int(pm.get_num_input_tokens()), "out_tokens": int(pm.get_num_generated_tokens()),
           "peak_mb": round(getattr(proc.memory_info(), "peak_wset", 0) / 2**20)}
    del pipe, res
    gc.collect()
    return out


def validate(v, sc, path):
    """Minimal validator for the schema subset used (type, enum, required, minLength, additionalProperties, items); the jsonschema package is not installed in the project env."""
    e = []
    t = sc.get("type")
    if t == "object":
        if not isinstance(v, dict):
            return [f"{path}: not an object"]
        for k in sc.get("required", []):
            if k not in v:
                e.append(f"{path}: missing {k}")
        for k, x in v.items():
            if k in sc["properties"]:
                e += validate(x, sc["properties"][k], f"{path}.{k}")
            elif sc.get("additionalProperties") is False:
                e.append(f"{path}: unexpected {k}")
    elif t == "array":
        if not isinstance(v, list):
            return [f"{path}: not a list"]
        for i, x in enumerate(v):
            e += validate(x, sc["items"], f"{path}[{i}]")
    elif t == "string":
        if not isinstance(v, str):
            return [f"{path}: not a string"]
        if "enum" in sc and v not in sc["enum"]:
            e.append(f"{path}: '{v}' not in enum")
        if len(v) < sc.get("minLength", 0):
            e.append(f"{path}: shorter than minLength")
    return e


def check(text):
    r = {"valid_json": False, "schema_ok": None, "reported_by_values": [], "chief_complaint": None, "n_items": 0}
    try:
        d = json.loads(text)
    except Exception as e:
        r["error"] = str(e)[:80]
        return r
    r["valid_json"] = isinstance(d, dict)
    if not isinstance(d, dict):
        return r
    errs = validate(d, SCHEMA, "$")
    r["schema_ok"] = not errs
    if errs:
        r["schema_errors"] = errs[:5]
        r["schema_error_count"] = len(errs)
    r["chief_complaint"] = d.get("chief_complaint")
    vals = []
    for k, v in d.items():
        if isinstance(v, list):
            for it in v:
                if isinstance(it, dict):
                    r["n_items"] += 1
                    if "reported_by" in it:
                        vals.append(str(it["reported_by"]))
    r["reported_by_values"] = sorted(set(vals))
    r["reported_by_blank_or_person"] = sum(1 for x in vals if x == "" or x.startswith("person"))
    return r


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "smoke"
    print("openvino_genai", ovg.__version__, flush=True)
    jobs = [("syn1", "R1", True, 400)] if mode == "smoke" else [(c, m, k, 1500) for c in CASES for m in ("R0", "R1") for k in (False, True)]
    log = []
    for case, m, k, mx in jobs:
        try:
            o = run_one(build_prompt(CASES[case], m), k, mx)
            r = check(o["text"])
            row = {"case": case, "render": m, "constrained": k, **{x: o[x] for x in ("load_s", "gen_s", "in_tokens", "out_tokens", "peak_mb")}, **r, "text": o["text"]}
        except Exception as e:  # record, do not hide
            row = {"case": case, "render": m, "constrained": k, "exception": f"{type(e).__name__}: {str(e)[:300]}"}
        log.append(row)
        print({x: row.get(x) for x in ("case", "render", "constrained", "gen_s", "out_tokens", "valid_json", "schema_ok", "reported_by_values", "chief_complaint", "exception")}, flush=True)
        (RES / f"{mode}.json").write_text(json.dumps(log, indent=1, ensure_ascii=False), encoding="utf-8")
