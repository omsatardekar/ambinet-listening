"""Creates the Phase B arm prompts and configs STRICTLY from manifests/PHASE_A_AMENDED_DECISION.json (Amendment 001 applied to the Phase A evidence); no other choice is made here.
usage: python -B make_arm_configs.py   (run once, after Phase A, before the freeze)"""
import json
from pathlib import Path

EXP7 = Path(__file__).resolve().parents[1]
res = json.loads((EXP7 / "manifests" / "PHASE_A_AMENDED_DECISION.json").read_text(encoding="utf-8"))
dec = res["decision"]
pname = res["prompt_selected"]
ids = json.loads((EXP7.parent / "EXP_006_S1_SIMPLIFIED_EXTRACTION" / "config" / "S1_CONFIG.json").read_text(encoding="utf-8"))["ids"]
LAYOUT = {"R1": "Each line of the transcript starts with the speaker label (doctor, patient, nurse, caregiver, family_member, clinical_staff or unknown) followed by a colon, then what was said.",
          "R0": "Each line looks like [SEG0001] person_1 (ROLE) times: text. Ignore the segment ids, the speaker ids (person_N) and the times. The word in brackets (PATIENT, DOCTOR, NURSE ...) is the speaker label; write it in lower case in reported_by."}
GRAM = {"G1": ("S1_1_output_grammar.ebnf", ""), "G2": ("S1_1_output_grammar_G2_cap20.ebnf", ""), "G3": ("S1_1_output_grammar_G3_cap20_prefix.ebnf", '{"chief_complaint":"')}
ARMS = {"B1": ("R0", None, "B1_B2"), "B2": ("R1", None, "B1_B2"), "B3": ("R1", dec.get("B3_variant"), "B3")}
(EXP7 / "prompts" / "arm").mkdir(exist_ok=True)
(EXP7 / "config").mkdir(exist_ok=True)
tmpl = (EXP7 / "prompts" / f"S1_1_{pname}.txt").read_text(encoding="utf-8")
for arm, (render, gvar, key) in ARMS.items():
    if dec.get(key) != "run":
        print(arm, "not permitted by the Phase A gates; no files created")
        continue
    (EXP7 / "prompts" / "arm" / f"S1_1_{arm}_PROMPT.txt").write_text(tmpl.replace("{LAYOUT}", LAYOUT[render]), encoding="utf-8", newline="\n")
    cfg = {"experiment": "EXP_007_S1_1_SIMPLIFIED_EXTRACTION", "arm": arm, "run_id": f"S1_1_{arm}_dev50", "ids": ids, "ids_source": "EXP_006/config/S1_CONFIG.json (P02 prompt-dev ids)",
           "model_id": "Qwen/Qwen3-0.6B", "model_revision": "c1899de289a04d12100db370d81485cdf75e47ca", "runtime": "openvino_genai.LLMPipeline, FP16 IR (EXP_002), fresh pipeline per encounter", "device": "GPU",
           "generation": {"do_sample": False, "enable_thinking": False}, "max_new_tokens": 2048, "max_new_tokens_note": "approved reduction from 6144 (S1.0 longest output 1121 tokens); token-cap hits are recorded separately",
           "prompt_choice": pname, "prompt_file": f"prompts/arm/S1_1_{arm}_PROMPT.txt", "rendering": render,
           "rendering_description": "R0 = existing renderer unchanged" if render == "R0" else "R1 = 'role: text' per line, no segment ids/speaker ids/times; sidecar keeps the mapping",
           "grammar": None if not gvar else {"variant": gvar, "file": GRAM[gvar][0], "answer_prefix": GRAM[gvar][1]},
           "differences_from_P02": ["prompt", "output structure (no current_conditions)", "max_new_tokens 2048"] + (["R1 rendering"] if render == "R1" else []) + (["constrained decoding"] if gvar else []),
           "comparison": "P02 primary (stored outputs, reproduced 153/522/1707); S1.0 secondary (stored adapted outputs)"}
    (EXP7 / "config" / f"S1_1_{arm}_CONFIG.json").write_text(json.dumps(cfg, indent=1), encoding="utf-8")
    print(arm, "created:", render, gvar or "unconstrained")
