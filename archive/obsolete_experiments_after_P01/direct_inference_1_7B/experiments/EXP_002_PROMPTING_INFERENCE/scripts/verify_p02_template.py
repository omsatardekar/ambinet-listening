"""Programmatic verification of a P02 draft prompt's OUTPUT TEMPLATE and ALLOWED-VALUES block against the frozen schema
(dataset_v2_batch_001_corrected/schema/final_label_schema.json) and the conventions observed in the authorised gold labels (evaluations/p02_review/GOLD_CONVENTIONS.json).
No labels are read here (the gold conventions file was produced earlier through the dataset guard); no inference.  The frozen schema is never modified.
usage: python -B -s verify_p02_template.py <prompt.txt> <out_tag>   -> evaluations/p02_review/TEMPLATE_VERIFICATION_<out_tag>.json (+ .md)"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
TRACK = HERE.parents[3]
ROOT = TRACK.parent
SCHEMA = json.loads((ROOT / "dataset_v2_batch_001_corrected" / "schema" / "final_label_schema.json").read_text(encoding="utf-8"))
REV = TRACK / "experiments" / "EXP_002_PROMPTING_INFERENCE" / "evaluations" / "p02_review"
GOLD = json.loads((REV / "GOLD_CONVENTIONS.json").read_text(encoding="utf-8"))
TYPES = GOLD["all_field_types"]
prompt_path, tag = Path(sys.argv[1]), sys.argv[2]
P = prompt_path.read_text(encoding="utf-8")
issues, notes, checks = [], [], []


def ok(name, cond, detail=""):
    checks.append({"check": name, "pass": bool(cond), "detail": detail})
    if not cond:
        issues.append(f"{name}: {detail}")


# ---------------------------------------------------------------- 1. template parses, keys and order
a = P.index('{"encounter_id"')
b = P.index("\n\nTranscript")
tpl_text = P[a:b]
try:
    T = json.loads(tpl_text)
    ok("template_parses_as_json", True)
except Exception as e:  # noqa: BLE001
    ok("template_parses_as_json", False, str(e))
    print(json.dumps(issues, indent=1))
    sys.exit(1)
ok("top_level_keys_equal_schema_and_order", list(T.keys()) == SCHEMA["top_level_keys"], f"template={list(T.keys())}")
for cat, spec in SCHEMA["categories"].items():
    x = T
    for part in cat.split("."):
        x = x[part]
    if cat == "chief_complaint":
        ok("chief_complaint_is_object", isinstance(x, dict))
        item = x
    else:
        ok(f"{cat}_is_list_with_one_template_item", isinstance(x, list) and len(x) == 1)
        item = x[0]
    ok(f"{cat}_keys_equal_schema_in_order", list(item.keys()) == spec["keys"], f"template={list(item.keys())} schema={spec['keys']}")
nk = SCHEMA["nested_keys"]
ok("encounter_metadata_keys", list(T["encounter_metadata"].keys()) == nk["encounter_metadata"])
ok("primary_speakers_keys", list(T["encounter_metadata"]["primary_speakers"][0].keys()) == nk["primary_speakers"])
ok("quality_checks_keys", list(T["quality_checks"].keys()) == nk["quality_checks"])
ok("clinical_evidence_keys", list(T["clinical_evidence"][0].keys()) == nk["clinical_evidence"])
ok("medical_history_keys", list(T["medical_history"].keys()) == nk["medical_history"])
dur = T["symptoms"][0]["duration"]
ok("symptom_duration_is_null_or_object_with_schema_keys", dur is None or list(dur.keys()) == nk["duration"], f"template duration={dur}")
for _path, _item in (("medications", T["medications"][0]), ("past_medical_history", T["medical_history"]["past_medical_history"][0])):
    ok(f"{_path}_duration_is_null_or_schema_object", _item["duration"] is None or list(_item["duration"].keys()) == nk["duration"])
ok("prompt_describes_duration_object_keys", all(k in P for k in ('"value"', '"unit"', '"normalized"')) and "duration" in P)
ok("prompt_describes_action_time_reference_object", '"normalized_date"' in P and "time_reference" in P, "clinical_actions.time_reference is null or {value, normalized_date}")

# ---------------------------------------------------------------- 2. placeholder types and nullability against the observed gold fields
rows = []


def norm_path(path):
    return re.sub(r"\[\d+\]", "[]", path)


def walk(o, path):
    if isinstance(o, dict):
        for k, v in o.items():
            p = f"{path}.{k}" if path else k
            if isinstance(v, dict):
                rows.append((p, "object", v))
                walk(v, p)
            elif isinstance(v, list):
                rows.append((p, "list", v))
                for x in v:
                    if isinstance(x, dict):
                        walk(x, p + "[]")
            else:
                rows.append((p, "leaf", v))


walk(T, "")
verdicts = []
for p, kind, v in rows:
    g = TYPES.get(p)
    if kind != "leaf":
        want = "object" if kind == "object" else "list"
        if g is not None and want not in g:
            verdicts.append((p, "MISMATCH", f"template {want}, gold {dict(g)}"))
        continue
    if g is None:
        verdicts.append((p, "UNVERIFIABLE", "no gold instance in the 50 dev labels"))
        continue
    gset = set(g)
    if v == "":
        if "null" in gset:
            verdicts.append((p, "NOTE", f"template shows a required-text placeholder but gold is nullable here {dict(g)}"))
        elif not (gset <= {"string", "int", "float"} and gset):
            verdicts.append((p, "MISMATCH", f"template string placeholder, gold {dict(g)}"))
        else:
            verdicts.append((p, "OK", "required text (gold never null, never empty)" + (" ; gold also numeric" if gset & {"int", "float"} else "")))
    elif v is None:
        verdicts.append((p, "OK", "nullable in gold") if "null" in gset else (p, "MISMATCH", f"template shows null but gold is never null {dict(g)}"))
    elif isinstance(v, bool):
        verdicts.append((p, "OK" if "bool" in gset else "MISMATCH", f"bool; gold {dict(g)}"))
    elif isinstance(v, str):
        # constant value placeholder
        vals = GOLD["enum_like_values_used"].get(p)
        if vals is not None and set(map(str, vals)) <= {v}:
            verdicts.append((p, "OK", f"constant '{v}' = only value in gold"))
        elif vals is not None and v in map(str, vals):
            verdicts.append((p, "NOTE", f"template constant '{v}' but gold also uses {list(vals)}"))
        elif v.startswith("<") or re.fullmatch(r"EV_\d+|MM:SS", v) or p in ("encounter_id", "encounter_metadata.language"):
            verdicts.append((p, "OK", "instance placeholder / identifier"))
        else:
            verdicts.append((p, "NOTE", f"constant '{v}', gold values {dict(vals) if vals else dict(g)}"))
    else:
        verdicts.append((p, "NOTE", f"{type(v).__name__} {v!r}, gold {dict(g)}"))
DEVIATIONS = {"medical_history.surgical_history[].timeframe": "gold always states a timeframe (27/27), but the frozen schema does not forbid null and a surgery without a stated timeframe must not be dropped or invented; template keeps null",
              "physical_examination[].body_site": "gold always states a body site (80/80), but the frozen schema does not forbid null and a finding without a stated site must not be invented; template keeps null"}
verdicts = [(p, "DOCUMENTED_DEVIATION", DEVIATIONS[p]) if (p in DEVIATIONS and k == "MISMATCH") else (p, k, d) for p, k, d in verdicts]
mism = [x for x in verdicts if x[1] == "MISMATCH"]
deviations = [x for x in verdicts if x[1] == "DOCUMENTED_DEVIATION"]
notes_v = [x for x in verdicts if x[1] in ("NOTE", "UNVERIFIABLE")]
for p, _, d in mism:
    issues.append(f"type/nullability: {p}: {d}")

# ---------------------------------------------------------------- 3. allowed-values block vs schema enums
blk = P[P.index("Allowed values"):]
blk = blk[: blk.index("\n\n")]
parsed = {}
for line in blk.split("\n")[1:]:
    if not line.startswith("- "):
        continue
    segs = [s.strip() for s in line[2:].split(" ; ")]
    first = segs[0]
    key, vals = first.split(": ", 1)
    prefix = key.rsplit(".", 1)[0] if "." in key else key
    entries = [(key, vals)]
    for s in segs[1:]:
        f, v = s.split(": ", 1)
        entries.append((f"{prefix}.{f}", v))
    for k, v in entries:
        v = re.sub(r"\([^)]*\)", "", v)
        v = v.replace(" or null", "").replace("(use other when none fits)", "")
        parsed[k] = {x.strip().strip('"') for x in v.split("|") if x.strip()}
schema_enums = {k: set(v.keys()) for k, v in SCHEMA["enums"].items()}
enum_report = []
for k, vs in schema_enums.items():
    if k in ("extraction_status", "encounter_metadata.encounter_type"):
        ok(f"constant_{k}_in_template", k == "extraction_status" and T["extraction_status"] in vs or k == "encounter_metadata.encounter_type" and T["encounter_metadata"]["encounter_type"] in vs)
        continue
    pv = parsed.get(k)
    same = pv == vs
    enum_report.append({"enum": k, "schema": sorted(vs), "prompt": sorted(pv) if pv is not None else None, "equal": same})
    ok(f"allowed_values_equal_schema:{k}", same, f"schema={sorted(vs)} prompt={sorted(pv) if pv is not None else 'MISSING'}")
extra = sorted(set(parsed) - set(schema_enums))
notes.append(f"enum lines in the prompt that have no entry in final_label_schema.enums: {extra} (their value sets are checked against the gold labels below)")
for k in extra:
    gv = GOLD["enum_like_values_used"].get(k.replace(".", "[].", 1) if k.count(".") == 1 else k)
    notes.append(f"{k}: prompt {sorted(parsed[k])}; gold values used {sorted(map(str, gv)) if gv else 'n/a'}")
roles = SCHEMA["roles"]
ok("roles_listed_exactly_as_schema", ", ".join(roles) in P, f"schema roles: {roles}")
ok("route_enum_is_only_oral", schema_enums.get("medications.route") == {"oral"} and parsed.get("medications.route") == {"oral"}, f"schema={schema_enums.get('medications.route')} prompt={parsed.get('medications.route')}")
ok("pmh_status_only_ongoing", schema_enums.get("medical_history.past_medical_history.status") == {"ongoing"})
ok("review_of_systems_status_only_negative", schema_enums.get("review_of_systems.status") == {"negative"})
ok("allergy_severity_only_unknown", schema_enums.get("allergies.severity") == {"unknown"})

# ---------------------------------------------------------------- 4. evidence and supports conventions
ev = GOLD["evidence"]
ok("gold_evidence_all_exact_single_lines", ev["text_is_exact_single_segment"] == ev["records"], f"{ev['text_is_exact_single_segment']}/{ev['records']}")
ok("gold_timestamps_MM:SS_all", ev["timestamp_format_MM:SS_ok"] == ev["records"])
ok("gold_timestamps_equal_floor_of_line_times_almost_all", ev["start_floor_ok"] >= 0.99 * ev["records"], f"start {ev['start_floor_ok']}/{ev['records']}, end {ev['end_floor_ok']}/{ev['records']} (4 exceptions each, rounding of times that end exactly on a second boundary)")
ok("gold_supports_never_empty", ev["has_empty_supports"] == 0)
ok("gold_references_symmetric_in_all_labels", ev["records_with_symmetric_references"] == ev["labels"], f"{ev['records_with_symmetric_references']}/{ev['labels']}")
for needle in ("MM:SS", "rounded down", "EV_001", "supports"):
    ok(f"prompt_mentions:{needle}", needle in P)
ex_paths = re.findall(r'"((?:symptoms|negative_findings|medications|medical_history\.[a-z_]+)\[\d+\]|chief_complaint)"', P)
ok("supports_path_examples_use_valid_syntax", all(re.fullmatch(r"(chief_complaint|[a-z_]+\[\d+\]|medical_history\.(past_medical_history|surgical_history|family_history|social_history)\[\d+\])", x) for x in ex_paths), str(ex_paths))
ok("prompt_states_empty_string_is_never_valid", bool(re.search(r"empty string is never a valid value", P)))
ok("gold_has_no_empty_string_anywhere", not GOLD["fields_with_empty_strings"], str(GOLD["fields_with_empty_strings"]))
ok("template_has_only_the_two_runner_placeholders", P.count("{TRANSCRIPT}") == 1 and P.count("{ENCOUNTER_ID}") == 1 and len(re.findall(r"\{[A-Z_]{3,}\}", P)) == 2)


# ---------------------------------------------------------------- 5. whole-draft static consistency (instructions vs frozen schema)
instr = P[: P.index("Output format (replace")]
rules_a = instr.index("Extraction rules")
vocab = set(SCHEMA["top_level_keys"]) | set(SCHEMA["roles"])
for spec in SCHEMA["categories"].values():
    vocab |= set(spec["keys"])
for lst in SCHEMA["nested_keys"].values():
    vocab |= set(lst)
for k, vv in SCHEMA["enums"].items():
    vocab |= set(vv.keys()) | set(k.replace(".", " ").split()) | {k.split(".")[-1]}
vocab |= set(SCHEMA["categories"].keys()) | {c.split(".")[-1] for c in SCHEMA["categories"]}
vocab |= {"person_1", "EV_001", "EV_002"}  # explicit examples used in the prompt
ids_in_prompt = sorted(set(re.findall(r"[A-Za-z]+(?:_[A-Za-z0-9]+)+", instr)) - {"person_1"})
unknown = [t for t in ids_in_prompt if t not in vocab and t not in {x.lower() for x in vocab}]
ok("every_snake_case_identifier_in_the_instructions_is_a_schema_key_or_enum_value", not unknown, f"unknown identifiers: {unknown}")
# enum value written after a field word in prose must be an allowed value of a field with that name somewhere in the schema
field_vals = {}
for k, vv in SCHEMA["enums"].items():
    field_vals.setdefault(k.split(".")[-1], set()).update(vv.keys())
bad = []
for m in re.finditer(r"(status|certainty|temporality|route|resolution_status|severity|allergy_type|action_type|type)\s+(?:is\s+|=\s*)?\"?([a-z_]+)\"?", instr[rules_a:]):
    f, v = m.group(1), m.group(2)
    if f in field_vals and v not in field_vals[f] and v not in {"is", "of", "the", "and", "or", "only", "for", "when", "as", "in", "a", "an", "to", "that", "also", "one", "if", "from"}:
        bad.append((f, v))
ok("enum_values_written_after_field_words_in_the_rules_are_allowed_values", not bad, f"{bad}")
# fields in the template that carry "" must be explained or be an enum/text field named in the prompt
ph = [p for p, kind, v in rows if kind == "leaf" and v == ""]
unexplained = sorted({p.split(".")[-1] for p in ph if p.split(".")[-1] not in instr})
notes.append(f"template fields shown as \"\" whose field name is never mentioned in the instructions (self-explanatory text/enum fields): {unexplained}")
ok("no_field_in_the_template_is_shown_as_empty_string_where_gold_allows_null", not [x for x in verdicts if x[1] == "NOTE" and "required-text placeholder but gold is nullable" in x[2]], str([x[0] for x in verdicts if x[1] == "NOTE" and "required-text placeholder but gold is nullable" in x[2]]))
ok("vital_signs_value_placeholder_is_not_an_empty_string", T["vital_signs"][0]["value"] != "" and T["vital_signs"][0]["value"] is not None, f"template value={T['vital_signs'][0]['value']!r}")
ok("prompt_says_vital_value_is_required_number_or_systolic_diastolic_text", "vital_signs.value is required" in P and "<systolic>/<diastolic>" in P)
ok("no_instruction_states_a_speaker_count", not re.search(r"2 to 4|two to four", P))
ok("prompt_ties_route_oral_to_that_medicine", "that medicine is taken by mouth or orally" in P)
for t in ("related_entities", "resolution_status", "contradictions_detected", "ambiguous_entities", "conflicting_statement uncertainty"):
    ok(f"prompt_instructs:{t}", t in instr)
claims_file = REV / "PROMPT_CLAIMS_VS_GOLD.json"
if claims_file.exists():
    cj = json.loads(claims_file.read_text(encoding="utf-8"))
    ok("all_label_convention_claims_hold_on_the_50_dev_gold_labels", not cj["failed"], f"{len(cj['claims'])} claims, not exact: {cj['failed']}")

result = {"prompt": str(prompt_path), "prompt_sha256": __import__("hashlib").sha256(prompt_path.read_bytes()).hexdigest(), "checks_total": len(checks), "checks_failed": len(issues), "issues": issues, "type_nullability_mismatches": mism,
          "type_nullability_notes": notes_v, "documented_deviations": deviations, "enum_report": enum_report, "notes": notes, "checks": checks, "field_verdicts_ok": sum(1 for x in verdicts if x[1] == "OK"), "field_verdicts_total": len(verdicts)}
(REV / f"TEMPLATE_VERIFICATION_{tag}.json").write_text(json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"checks {len(checks)} failed {len(issues)}; field verdicts OK {result['field_verdicts_ok']}/{result['field_verdicts_total']}; documented deviations {len(deviations)}")
for i in issues:
    print(" ISSUE", i[:260])
for n in notes_v[:40]:
    print(" NOTE", str(n)[:200])
for n in notes:
    print(" INFO", n[:300])
