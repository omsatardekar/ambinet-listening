# P02 v2.2 pilot: failure investigation and recovery proposal

Investigation only. No code, prompt, schema, dataset, gold label or earlier experiment file was modified; no inference was run. This file is new. All raw/parsed/failed outputs and logs of the pilot are untouched (`outputs/*/P02_v2_2_pilot6/`, `logs/*P02_v2_2_pilot6*`).
Written for: the project owner, to decide the next experiment.

**State of the pilot.** All six records ran to the end (the runner was still on record 6 when you stopped me; it finished at 10:51). Result: **3 parsed (00168, 00152, 00157), 3 failed `invalid_json` (00204, 00037, 00092)**. No stop rule fired. That is a gap in the rules I wrote: they watched for token-cap hits, which never happened, and had nothing for invalid JSON or empty sections.

## 1. Why three outputs failed JSON parsing (actual evidence)

All five analysed outputs have `finish_reason: "stop"`, `attempts: 1`; there is no `OOM_STOP` file, no traceback, exit code 0. The model ended each answer by itself (it emitted its end-of-text token). The only "errors" in the stdout log are PowerShell's wrapper text around normal INFO lines. RAM never fell below 1.77 GB available. So: **not truncation, not a runtime problem.**

Token counts are low (136–1,037, cap 4,096) because the model **stopped early**: either it wrote almost nothing, or it finished a malformed answer after a few hundred tokens. The cap was never close. Per-record time (184–536 s) is mostly prefill of a 4.8–5.6k-token input (123–183 s) plus 2.3–2.9 tokens/s decoding.

The parser (`output_parser.parse_response`) is the same strict `json.loads` used for P00/P01/v2.1: it removes a `<think>` block or a markdown fence and nothing else, so it correctly rejects the three outputs. It was not changed.

| Record | Parser error | What the raw output is |
|---|---|---|
| 00204 (537 tokens, 1,975 chars) | `Expecting ',' delimiter at char 1975` (line 6) | **Unterminated object.** The answer ends with `…"status":"present","by":"doctor","refs":["SEG0037"]}]` after `physical_examination` and **has no closing `}`**; the position of the error is the end of the text. The model also never wrote `medications`, `clinical_uncertainties`, `clinical_actions`, `procedures_and_investigations`, `clinical_assessment`, `follow_up` or `chief_complaint`. |
| 00037 (1,037 tokens, 3,606 chars) | `Extra data at char 287` (line 3) | **Many separate JSON objects, one per section**, separated by blank lines: `{"negative_findings":[…]}` `\n\n` `{"medications":[…]}` `\n\n` `{"clinical_uncertainties":[…]}` … 14 objects. The first object ends at char 285; everything after is "extra data". |
| 00092 (750 tokens, 2,751 chars) | `Extra data at char 197` (line 3) | The same pattern, plus defects inside: `{"medical_history":{"social_history":[…]}` is **missing a closing brace**, `{"allergies":{}}`, `{"physical_examination":{}}` etc. are objects instead of lists, and the answer ends with a nonsense object `{"medical_history":{"surgical_history":{},"family_history":{},"social_history":{},"medical_history":{}}}`. |

The two that parsed are not good either:

* 00168 (177 tokens): `{"negative_findings":[],"medications":[],"clinical_uncertainties":[],"clinical_actions":[],"procedures_and_investigations":[],"clinical_assessment":[],"follow_up":[],"chief_complaint":{…"faint"…},"symptoms":[],"medical_history":{"social_history":[…2 items…]},"allergies":[],"vital_signs":[],…}`: **16 of 18 sections empty.**
* 00152 (136 tokens): the same shape, **17 of 18 empty**, with `"social_history"` written twice inside `medical_history`.

**Cause.** The failures are caused by the **v2.2 prompt design, not by the generation settings or the parser** (same settings, runner and parser as P01, which produced 25 of 30 parsed). Specific evidence:
1. The prompt says "ONE JSON object … one top-level key per line", and its worked example writes one key per line. In 00037 and 00092 the model **closed the object at the end of every line** and started a new one (JSON-lines style). The instruction was ambiguous for a 1.7B model.
2. The prompt says "never write `[]`; leave out a section with no facts", yet 00168/00152 are almost all `[]`. The model did the opposite of the rule, which shows it was not following the long list of omission rules.
3. **The worked example leaked into the answers.** 00168 contains the example fact verbatim: `{"category":"smoking","description":"Does not use tobacco","status":"never","by":"patient","refs":["SEG0008","SEG0009"]}` (smoking was never discussed in 00168, and SEG0008/9 are other lines). 00037 contains the example's two vital signs verbatim (`Heart rate 74 bpm`, `Blood pressure 118/76`, `refs ["SEG0010"]`; gold has **no** vitals for 00037). Whole-fact exact matches: 00168 one, 00037 two.
4. The model also invented references: `"SEG009"` (twice, 00037) is not a segment id.

I cannot prove which of these made 00204 stop before the last braces and skip seven sections; what is observable is that the prompt changed three things at once (key names, section order, omission rules), and the outputs are broken in exactly those three ways.

## 2. P01 against v2.2 against gold (same ids)

**Comparable metrics (strict entity matcher, as scored, failed output = zero).** P01 outputs are truncated at the 4,096 cap for four of the six pilot ids (00168, 00204, 00037, 00092), so P01 is not a clean baseline on these ids either.

| On the 6 pilot ids | parsed | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| P01, as scored | 2 of 6 | 0.308 | 0.019 | 0.037 |
| v2.2, as scored | 3 of 6 | 0.500 | 0.034 | 0.064 |
| P01, structurally closed (diagnostic, not a pass/fail result) | 6 of 6 | 0.224 | 0.136 | 0.169 |
| v2.2, malformed outputs merged/closed by me for analysis only (diagnostic) | 6 of 6 | 0.333 | 0.107 | 0.162 |

(The diagnostic rows close P01's truncated JSON and concatenate v2.2's separate objects; they show what the model *wrote*, not a score of the pilot. Official scoring stays "failed".)

**Do not read P01 as "60% accurate".** The evaluator gives, for **all 30 P01 records** (as scored): precision 0.283, recall 0.156, **F1 0.201** (25 parsed; parsed-only F1 0.226). P00 on the same 30: F1 0.161. The nearest figures to 60% are *category recalls*: P01 parsed-only recall is **0.61 for medications**, 0.46 vital signs, 0.45 clinical assessment, 0.46 family history, and **≈0 for negative findings (0.03), physical examination, review of systems, clinical conditions, clinical actions (0.01), follow-up and uncertainties**. So P01 works for named items (medicines, vitals, diagnoses) and fails for exactly the categories that need reasoning about the whole transcript.

**On the pilot ids, gold facts by version (matched by the evaluator's key, so a paraphrase counts as a miss):**

* *Found by P01, missed by v2.2:* 00168 headache and nausea (symptoms), ramipril, blood pressure and respiratory rate, fever denial; 00204 chief complaint "itching", amlodipine, exercise, plaque psoriasis assessment, "no previous surgery"; 00092 oxygen saturation; 00152 stress urinary incontinence assessment; 00037 eczema history and the conflicting-statement uncertainty; 00157 sneezing.
* *Found by v2.2, missed by P01:* 00168 occupation; 00092 chief complaint "sweating", HbA1c; 00037 smoking, "early inflammatory arthritis"; 00157 exercise and two vitals; 00204 heart rate.
* *Missed by both:* 00168 six of seven negatives (chest pain, vomiting, confusion, no urine, no known allergies, syncope), ORS, paracetamol, all six actions, the ramipril discrepancy, the follow-up in three days; 00152 all eight negatives, all eight vitals, the bladder diary, the follow-up in six weeks; 00092 seven negatives, vitals other than SpO2, fasting glucose; 00037 six negatives, arthralgia/rash symptoms by gold name, dengue/chikungunya labs by gold name.
* *Invented or wrong in v2.2:* 00168 smoking "none" (example copy); 00037 two vitals (example copy), allergy "telmisartan, reaction none", a `medication_discrepancy` about telmisartan, "swollen painful wrists" and "blotchy rash" written as **negative findings**; 00157 "sneezing fits" written as a negative finding and as a *resolved* symptom; 00204 "itching" as a negative finding, an allergy reaction written as `"I'm allergic to sulfa drugs"`, vital values written as strings with units (`"36.4°C"`, `"98%"`).
* *Invented or wrong in P01:* `no fever`, `no allergies`, `no previous surgery` negatives in 00204 and 00037 (the example text of the P01 prompt, line 6, leaked), `lifestyle` social history, family history `unknown`, six vital rows in 00092 with names such as `pressure`, `bmi`, three `date uncertain` items in 00092.
* *Partial / wrong attributes:* both versions get the right concept with the wrong key in many cases (`high blood pressure` for gold `hypertension`, `glycomet` for `metformin`, `fever and joint pains` for `fever with arthralgia`); the strict matcher scores these as a miss and an extra. This lowers every version's score and is independent of format.
* *Do prompt order and instructions make the model skip sections?* In v2.2 the sections placed **first** (negatives, medications, uncertainties, actions, procedures, assessment, follow-up) are empty or absent in 00168, 00152 and 00204, while the sections placed later (chief complaint, social history, vitals) are filled. P01 fills the same sections more often because it writes them in the template's natural order with the placeholders in front of it. This is consistent with an order effect, but five records cannot prove it.

**v2.2 pilot, other measured facts:** 14 facts in the 3 parsed outputs, all 16 references valid (no invented id in the parsed ones; `SEG009` only in the failed 00037), 0 excessive references, entity matches 7 of 206 gold facts, the only gold medication discrepancy missed, `by` written for every fact, 0 flags. Defaults applied in 00157 only (eight), so the "explicit non-default status" rule was exercised once. Lexical indicators: 1 habit not in transcript (the example's smoking), 1 negation-without-cue (the misfiled symptom).

## 3. What the original requirement was, and what v2.2 changed

**Unchanged by requirement (P01 prompt + the full schema `clinical_extraction_schema.json` / frozen `final_label_schema.json`):** all 20 top-level keys in the schema order; `encounter_metadata` with `primary_speakers`; every category and nested list (`medical_history.{past_medical_history,surgical_history,family_history,social_history}`); every field name (`reported_by`, `observed_by`, `stated_by`, `requested_by`, `responsible_person`, `related_entities`, `evidence_ids`…); the enums; nested `duration` / `time_reference` shapes; `confidence: null`; arrays for all list sections; compact JSON.

**What should change (and only this):** the model stops producing `clinical_evidence` records (transcript text, speaker, timestamps, `supports`) because the backend rebuilds them. Facts still need *some* pointer, so `evidence_ids` stays but holds segment ids.

**What v2.2 changed beyond that (and I should not have):** renamed fields (`refs`, `by`, `responsible`, `related`), merged four speaker field names into `by`, dropped `encounter_metadata`, `extraction_status`, `quality_checks`, reordered the sections, made every key optional/sparse with defaults, replaced the template with a key-list description and a worked example, and added many new omission rules. The pilot shows the 1.7B model cannot follow that much new instruction. Your reading is right: v2.2 drifted from the objective.

## 4. Diagnosis and recovery proposal

1. **Why nearly empty sections:** the model was given a new, sparse, reordered format with a long list of rules and a full worked example; it produced `[]` for the first sections, copied the example facts, and treated the task as format compliance. Observed, not proven: the empty sections are the ones placed first.
2. **Why three JSON failures:** (a) 00204: answer ended without the closing `}` after skipping seven sections; (b) 00037/00092: one object per section (ambiguous "one key per line" wording plus the example layout). Both are format-following failures of the new prompt; settings and parser unchanged.
3. **What worked better in P01:** a complete template with every key present in schema order and placeholders, "output every top-level key in template order", arrays-never-objects rule, lower-case role rule, compact layout rule. Result: 25 of 30 parsed; medicines, vitals, assessments recovered at 0.45–0.61 recall (parsed-only). P01's failures are the 4–5 truncations caused by the evidence blob, and weak recall of negatives/actions.
4. **Instructions to retain from P01 (verbatim):** the Rules block lines 4–10 and 12 (with the line-6 example text neutralised: it leaked as three false negatives), the Allowed-values block, the Structure rules 28–33, 35–36, and the full Output-format template with all 20 keys in order.
5. **Minimum change to remove evidence overhead (proposed "P01-NE", P01 minus evidence):**
   * keep the P01 template and order unchanged; **delete only** the `clinical_evidence` records: leave the key with `[]` (the template line becomes `"clinical_evidence": []`);
   * in every item keep the key `evidence_ids`, but write that it holds **segment ids copied from the line prefixes** (`["SEG0007"]`), 1–2 per item, replacing P01 rule line 11 and Structure rule line 34;
   * change nothing else: same field names, `reported_by`, enums, defaults written out as in P01, `quality_checks` as in P01 (about 60 tokens; whether to keep it is your earlier decision to exclude it from evaluation; I would keep it in the output and not score it).
6. **Backend attaches evidence:** (a) validate each `evidence_ids` entry against the transcript's segment ids (invalid ones flagged, kept); (b) rebuild `clinical_evidence` with the existing, tested resolver/materialiser logic (exact text, speaker, role, `MM:SS`), renumber to `EV_nnn` and rewrite `evidence_ids` and `supports`; (c) no clinical field is touched. The Stage 1 resolver and evaluator already support this (`evaluate_v22.py --format full` treats segment-id `evidence_ids` as references); the only new code is a small adapter from "full structure with segment ids" to the full record.
7. **Next experiment (needs your approval):** P01-NE on the **same six ids** against P01 (and against the P02 v2.1/v2.2 pilot numbers above), same model/settings/cap, early stop after record 1 if it fails to parse or exceeds 2,500 tokens, and a stop if two of the first three fail to parse for any reason (the rule v2.2 lacked). Pass criteria set before the run: ≥ 5 of 6 parse; no record above 3,300 tokens; entity recall not below P01's structurally-closed 0.136 on these ids; no copied example text; reference validity reported. Expected cost: about 15 minutes per record (estimate: P01 median 2,590 tokens, of which the evidence records are the bulk).

**What this will not fix:** the strict matcher compares normalised terms, so even a perfect format leaves recall low (P01 on 30 records: 0.156). Accuracy of negatives, actions and conditions is a separate prompt problem to address after the format is stable. Changing P01's line-6 example text is a second, separate single-variable change I would run as its own comparison, not inside the first.

## 5. Files read
`outputs/raw|parsed|failed/P02_v2_2_pilot6/*`, `logs/inference_P02_v2_2_pilot6.log`, `logs/performance_P02_v2_2_pilot6.json`, `logs/P02_v2_2_pilot6_stdout_stderr.log`, `logs/P02_v2_2_pilot6_STOP_RULE_*`, `evaluations/P02_v2_2_pilot6/run_manifest.json`, `direct_inference_baseline/inference/output_parser.py`, `prompt_versions/P01_schema_guided.txt`, `P02_comprehensive_v2_2.txt`, `clinical_extraction_schema.json`, `final_label_schema.json`, the P00/P01 output folders, the corrected inputs and labels of the 50 dev ids (read-only). Analysis scripts: session scratchpad only.
