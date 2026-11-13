"""Unit tests for S0.2 (synthetic data). usage: python -B test_s0_2.py"""
import copy, sys
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import s0_2_fill_nullable as F
fails = []
def check(n, c):
    print(("PASS " if c else "FAIL ") + n)
    if not c: fails.append(n)
base = {"medications": [{"name": "x", "dose": "5 mg", "route": ""}], "symptoms": [{"name": "h", "severity": "mild", "evidence_ids": []}], "follow_up": [{"type": "consultation", "status": "planned"}],
        "medical_history": {"past_medical_history": [{"condition": "c"}], "surgical_history": [], "family_history": [], "social_history": []}, "encounter_metadata": {"primary_speakers": [{"speaker_id": "p1", "role": "doctor"}]}}
orig = copy.deepcopy(base)
out, log = F.fill(base, "T")
m = out["medications"][0]
check("input never modified", base == orig)
check("missing nullable keys added as null", m["generic_name"] is None and m["frequency"] is None and m["confidence"] is None and out["follow_up"][0]["normalized_datetime"] is None)
check("existing non-null and empty-string values untouched", m["dose"] == "5 mg" and m["route"] == "" and out["symptoms"][0]["severity"] == "mild")
check("list/object-typed fields are never filled", "evidence_ids" not in out["follow_up"][0] and "duration" not in out["symptoms"][0] and "associated_symptoms" not in out["symptoms"][0])
check("history and metadata nullable keys filled", out["medical_history"]["past_medical_history"][0]["duration"] is None and out["encounter_metadata"]["encounter_date"] is None and out["encounter_metadata"]["primary_speakers"][0]["role_confidence"] is None)
check("every addition is logged with its path", all(r["rule"] == "S0.2_fill_nullable_field" and r["original"] == "<key absent>" for r in log) and any(r["path"] == "medications[0].generic_name" for r in log))
out2, log2 = F.fill(out, "T")
check("idempotent: second pass changes nothing", out2 == out and not log2)
check("non-dict containers and unknown sections are ignored", F.fill({"follow_up": {"type": "x"}, "clinical_assessment": None}, "T")[0] == {"follow_up": {"type": "x"}, "clinical_assessment": None})
t = open(Path(__file__).resolve().parents[2] / "EXP_004_QWEN3_0.6B_PROMPT_ENGINEERING/prompts/P02_comprehensive_extraction.txt", encoding="utf-8").read()
check("nullable table agrees with the model template (default null)", F.verify_against_template(t) == [])
print(f"{len(fails)} failed" if fails else "all passed"); sys.exit(1 if fails else 0)
