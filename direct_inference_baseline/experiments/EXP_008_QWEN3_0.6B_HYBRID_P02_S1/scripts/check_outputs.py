"""Label-free diagnostics for an EXP_008 run (reads the run's own outputs and the TRANSCRIPT inputs only; never opens labels).

    python check_outputs.py <run_id>

Reports: parse / schema status and token use per encounter, finish reasons, how many answers contain leftover <placeholders>, items whose text appears in the
PROMPT but not in the transcript (copying from the prompt), invalid role values, cited segment ids that do not exist, and how many sections are empty.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

EXP8 = Path(__file__).resolve().parents[1]
ROOT = EXP8.parents[2]
INPUTS = ROOT / "dataset_v2_batch_001_corrected" / "output" / "inputs"
ROLES = {"doctor", "patient", "nurse", "caregiver", "family_member", "clinical_staff", "unknown"}
LISTS = ["symptoms", "negative_findings", "medications", "allergies", "vital_signs", "physical_examination", "review_of_systems", "clinical_conditions",
         "clinical_assessment", "procedures_and_investigations", "clinical_actions", "follow_up", "clinical_uncertainties"]
HISTORY = ["past_medical_history", "surgical_history", "family_history", "social_history"]
ROLE_KEYS = {"reported_by", "observed_by", "stated_by", "requested_by", "role", "responsible_person"}


def walk(node, path=""):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from walk(v, f"{path}.{k}" if path else k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk(v, f"{path}[{i}]")
    else:
        yield path, node


def main(run_id: str) -> int:
    base = EXP8 / "outputs" / run_id
    manifest_candidates = list(base.glob("**/manifest*.json")) + list((EXP8 / "evaluation").glob(f"**/{run_id}*/run_manifest.json"))
    prompt_text = (EXP8 / "prompts" / json.loads((base / "run_settings.json").read_text(encoding="utf-8"))["prompt_file"].replace("\\", "/").split("/")[-1]).read_text(encoding="utf-8").lower()
    parsed_dir = base / "parsed_predictions" / run_id
    failed_dir = base / "failed_predictions" / run_id
    raw_dir = base / "raw_predictions" / run_id
    report = {"run_id": run_id, "attempted": len(list(raw_dir.glob("*.json"))), "parsed": len(list(parsed_dir.glob("*.json"))), "failed": len(list(failed_dir.glob("*.json")))}
    per, finish, tokens, copies, placeholders, bad_roles, bad_segs = [], Counter(), [], [], [], [], []
    empty_sections, filled_sections, items = Counter(), Counter(), []
    for raw in sorted(raw_dir.glob("*.json")):
        eid = raw.stem.replace("encounter_", "")
        r = json.loads(raw.read_text(encoding="utf-8"))
        g = r.get("generation", {})
        finish[g.get("finish_reason")] += 1
        tokens.append(g.get("completion_tokens") or 0)
        transcript = json.loads((INPUTS / f"encounter_{eid}.json").read_text(encoding="utf-8"))
        t_text = " ".join(s["text"] for s in transcript["segments"]).lower()
        seg_ids = {s["segment_id"] for s in transcript["segments"]}
        if re.search(r"<[a-z][^<>]{2,40}>", r.get("response_text", "")):
            placeholders.append(eid)
        pf = parsed_dir / f"encounter_{eid}.json"
        row = {"encounter": eid, "parsed": pf.exists(), "finish": g.get("finish_reason"), "completion_tokens": g.get("completion_tokens"), "prompt_tokens": g.get("prompt_tokens"),
               "latency_s": round(g.get("latency_seconds") or 0)}
        if pf.exists():
            doc = json.loads(pf.read_text(encoding="utf-8"))
            n = 0
            for sec in LISTS + HISTORY:
                v = (doc.get("medical_history") or {}).get(sec) if sec in HISTORY else doc.get(sec)
                (filled_sections if v else empty_sections)[sec] += 1
                n += len(v) if isinstance(v, list) else 0
            row["items"] = n
            for path, val in walk(doc):
                leaf = path.split(".")[-1].split("[")[0]
                if leaf in ROLE_KEYS and isinstance(val, str) and val not in ROLES:
                    bad_roles.append((eid, path, val))
                if leaf == "evidence_ids" or path.endswith("]") and "evidence_ids" in path:
                    if isinstance(val, str) and val not in seg_ids:
                        bad_segs.append((eid, path, val))
                if isinstance(val, str) and len(val) >= 5 and leaf in ("name", "finding", "condition", "description", "assessment", "substance", "procedure", "value") and not path.startswith("encounter"):
                    v = val.strip().lower()
                    if v in prompt_text and v not in t_text:
                        copies.append((eid, path, val))
        per.append(row)
    report.update(finish_reasons=dict(finish), completion_tokens={"max": max(tokens or [0]), "median": sorted(tokens)[len(tokens) // 2] if tokens else 0},
                  answers_with_leftover_placeholders=placeholders, text_copied_from_prompt_not_in_transcript=copies, invalid_role_values=bad_roles[:40],
                  invalid_role_value_count=len(bad_roles), cited_segment_ids_that_do_not_exist=bad_segs[:40], nonexistent_segment_count=len(bad_segs),
                  sections_empty=dict(empty_sections), sections_filled=dict(filled_sections), per_encounter=per)
    out = EXP8 / "evaluation" / f"check_{run_id}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "per_encounter"}, indent=1)[:3500])
    for r in per:
        print(r)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
