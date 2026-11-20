# P02 v2.2 proposal: compact extraction with backend evidence resolution

Status: **proposal only. Nothing in this document is implemented, frozen or approved.** No model inference was run to write it. No existing file was modified. Development-only: labels are generator-derived.

Written for: the project owner, to decide whether and how to build v2.2.

Two corrections to the task wording, both from the run files: the model is **Qwen3-1.7B** (revision `70d244cc…`, OpenVINO FP16), not 0.6B, and decoding ran on the **Intel UHD 620 GPU** (`device: GPU` in `run_settings_P02_v2_1_pilot8.json`), not on the CPU. Speeds of about 2.5 tokens/s are real either way.

Method note. Sizes in tokens are **estimates**: characters divided by 3.04, the ratio observed in one truncated output (12,460 characters = 4,096 tokens). Counts, comparisons and mappings below are exact, computed from the files.

---

## 1. P02 v2.1 diagnosis

### What happened
| Record | Result | Output tokens | Generation time | Finish reason |
|---|---|---:|---:|---|
| 00168 | parsed | 3,789 | 1,597 s | stop |
| 00204 | failed, truncated | 4,096 | 1,803 s | length |
| 00037 | failed, truncated | 4,096 | 1,759 s | length |

After record 3 the watcher found 2 of 3 records at the cap and terminated the runner, as approved. Records 00092, 00152, 00157, 00042, 00165 never ran. The evaluation was not run.

### Resource failure or output-length failure
**Output length.** There was no out-of-memory event and no `OOM_STOP` file. Free RAM before each load was 8.37, 8.91 and 9.19 GB (decimal MB reading); the lowest free RAM during generation was 2.87, 2.97 and 3.30 GB; the process peaked at 5.6–5.7 GB. Decode speed was 2.5–2.6 tokens/s. The records stopped because 4,096 tokens were generated, which at that speed is about 30 minutes per record.

### Where the tokens went (raw outputs)
| Record | Characters before `clinical_evidence` | Characters in `clinical_evidence` | Share of output that is evidence | Notes |
|---|---:|---:|---:|---|
| 00168 | 4,290 | 8,459 | 66% | 36 evidence records for 37 transcript lines |
| 00204 | 3,470 | 8,958 (cut off) | 72% | 37 evidence records started; timestamps written as `"353.69-359.74"` |
| 00037 | 10,928 | 1,532 (cut off) | 12% | the cap hit at the very start of the evidence list |

The two records differ, and this matters for the design:

* **00204 and 00168** are dominated by the evidence list. Without it they would have needed about 1,100 (00204) and 1,400 (00168) tokens.
* **00037** is not evidence-dominated. Its fact sections alone were about 10.9k characters (about 3.6k tokens) before the evidence list began. Causes visible in the raw text: indented, multi-line formatting (971 whitespace characters, 9%), **229 evidence ids across 37 arrays** (up to 18 ids in one array, about 2,900 characters), and every null and empty field written out. Removing the evidence list alone would likely have let it finish only just under the cap (estimated about 3.6k tokens, with `quality_checks` still to come). Evidence removal is necessary, not sufficient.

### A structural limit independent of the model
Gold labels of the 50 frozen dev records, compact JSON, estimated tokens:

| Form | Median | Maximum |
|---|---:|---:|
| Full gold, including `clinical_evidence` | 5,899 | 8,331 |
| Gold without `clinical_evidence` | 2,922 | 4,130 |
| Gold without `clinical_evidence`, null/empty keys omitted | 2,402 | 3,384 |

So **a perfect full-schema answer exceeds the 4,096 cap for more than half of the records** (median 5.9k). Even without evidence, the largest records sit at the cap. Any design that keeps all null and empty keys will remain fragile at 4,096 tokens, regardless of the prompt.

### What three records can and cannot show
Can show: v2.1 as written cannot meet gate G1 (at most 1 cap hit in 8); the evidence list is the main token consumer in two of three records; evidence references in the model output are broken (section 2); extraction recall was low on the one parsed record.

Cannot show: a failure rate for the eight, a parse rate for the 50, any improvement or regression against P00/P01, or whether the clinical omissions are typical. One parsed record and two truncated ones carry no statistical weight. Nothing here was evaluated with the frozen evaluator.

---

## 2. Actual versus expected JSON, encounter 00168

### 2.1 Which "expected" file
The pilot read `dataset_v2_batch_001_corrected` (`direct_inference_baseline/config/settings.py:17`, and the run manifest). The older untracked folder `dataset_v2_batch_001` also has an `encounter_00168`, but it is **a different encounter**:

| | corrected (used by the run) | old `dataset_v2_batch_001` |
|---|---|---|
| Segments | 37 | 62 |
| Speakers | person_1 NURSE (3), person_2 DOCTOR (18), person_3 PATIENT (16) | person_1 PATIENT (27), person_2 DOCTOR (34), person_3 CLINICAL_STAFF (1) |
| First line | "All set here, doctor. Chart's updated…" | "Excuse me, doctor, should I sit here?" |
| Gold `primary_speakers` | person_1 nurse, person_2 doctor, person_3 patient | person_1 patient, person_2 doctor, person_3 clinical_staff |

All 500 input files in the two folders differ byte for byte (0 identical), and the labels of 00168 differ in 59 places. **If speaker or timestamp differences were seen against the old folder, the cause is the comparison, not the model.** I did not investigate why the two datasets differ beyond this. The pilot input, the corrected gold and the corrected transcript are mutually consistent: all 30 gold evidence records map to exactly one transcript line by text, speaker and `mm:ss` start and end (and 1,772 of 1,772 across the 50 dev ids).

### 2.2 Field by field (corrected gold against the actual parsed output)
| Section | Gold | Actual | Finding |
|---|---|---|---|
| `encounter_metadata.primary_speakers` | 3 (nurse, doctor, patient) | 2 (person_1 nurse, person_2 doctor) | patient (person_3) missing. The transcript supplies all three. |
| `chief_complaint` | feeling faint, reported by `patient`, 1 evidence id | "faintness", reported_by `"person_3"`, **16 evidence ids** | role replaced by speaker id; 16 ids include the closing "Thanks so much, doctor." (SEG0037). |
| `symptoms` | 3: faint (mild; worse standing in the sun; since last night), headache (about 2 weeks), nausea (**resolved**) | 1: faintness, onset kept | headache and resolved nausea missing; severity `mild` and aggravating factor missing; 16 ids. |
| `negative_findings` | 7: fainting, chest pain, no urine, vomiting, confusion, fever, allergies | **0** | all seven explicit denials missed (SEG0011, SEG0013, SEG0017). |
| `medical_history` | hypertension, knee arthritis (5 years), gallbladder removed 2016; alcohol never, lives alone, night-shift warehouse | hypertension, arthritis (no duration), gallbladder 2016; **smoking "none"**, alcohol none, "warehouse" | duration missing; "lives alone" missing; **smoking was never discussed** in the transcript, so `smoking: none` is an unsupported claim. |
| `medications` | ramipril (**dose null**, discrepancy), paracetamol 650 mg, **ORS 1 sachet, 3 times a day, 2 days, planned** | ramipril **5 milligrams**, paracetamol 650 milligrams | ORS missing. Ramipril dose chosen as 5 mg. Routes `oral` and ramipril indication `hypertension` were added although not stated (gold null for both). |
| `allergies` | [] (and "No known allergies" in negatives) | [] | consistent. |
| `vital_signs` | BP "100/62", HR 93, RR 19 (numbers), reported by **nurse** | all three values correct, but numbers written as strings ("93"), unit "beats per minute" (gold "bpm"), name "Heart rate (for pulse)", reported_by `"person_2"` | values correct; attribution wrong (the nurse is person_1, SEG0030). |
| `physical_examination` | [] | "normal breathing", observed by person_2 | gold stores this as `review_of_systems` respiratory negative; model also misattributed it. |
| `review_of_systems` | respiratory negative | [] | missed. |
| `clinical_conditions` | arthritis (existing) | [] | missed. |
| `clinical_assessment` | heat exhaustion with some dehydration (provisional); electrolyte imbalance (differential) | first only, `basis`: "listening to the whole story" | differential missed; `basis` copied from the doctor's phrase. |
| `procedures_and_investigations` | blood salts / serum electrolytes, planned | blood salts, planned | matched. |
| `clinical_actions` | 6 (investigation, ORS, avoid midday sun, bring prescription, seek urgent care if confused or not sweating, follow-up in three days) | 1, type `follow_up`, description "order blood salts, for dehydration", time_reference **"2023-10-01"** | 5 of 6 missing; the date was **invented**. |
| `follow_up` | consultation, "in three days", cited SEG0034 | consultation, time_reference and normalized_datetime **"2023-10-01"**, cited SEG0031 | invented date; the phrase "in three days" lost. |
| `clinical_uncertainties` | medication_discrepancy: ramipril patient 5 mg, nurse 10 mg, unresolved | [] | the nurse's 10 mg (SEG0027) ignored; the model silently kept the patient's 5 mg. |
| `quality_checks` | present | **key absent** | the output has 19 of 20 top-level keys although it finished normally. |

Section counts, gold against actual: symptoms 3/1, negative findings 7/0, ROS 1/0, conditions 1/0, assessments 2/1, actions 6/1, uncertainties 1/0.

### 2.3 Evidence
* The model wrote **36 evidence records**, one for almost every transcript line (SEG0006 is missing). The gold has 30, skipping greetings and filler. 66% of the output characters are evidence.
* **References are broken inside the model's own output.** Facts cite transcript ids (`SEG0003` and so on: 48 ids, 18 distinct, all real) but the evidence records are named `EV_001…EV_036`, and each record's `supports` holds a `SEG` id where the gold uses field paths such as `symptoms[0]`. **None** of the 48 fact references names an existing evidence record. The prompt (rule at line 61, which I read only in part) tells the model to number evidence records `EV_001, EV_002…`; the facts cite segment ids instead.
* **Timestamps in the evidence block are invented.** All 36 start times and 35 of 36 end times differ from the transcript (SEG0006 runs 44.50–50.01 s; the model wrote an evidence record for SEG0007 with 00:12–00:13). The speaker was correct in all 36; the text differs in 2 of 36.
* Over-citation: the chief complaint and the symptom each cite 16 lines (including the final thanks), and the "faintness" symptom is attached to the doctor's closing remarks.

### 2.4 Speaker and timestamp audit
| Check | Result |
|---|---|
| Did gold and pilot use the same transcript? | **Yes for the corrected folder** (the run read it; gold evidence maps 30/30). The old folder is a different encounter (2.1). |
| Is the speaker table in the input? | **Yes**: the model is given `[SEG0030] person_1 (NURSE) 239.04-244.87s: …`. Roles were not hidden, so the misattribution is a model error. |
| `person_1/2/3` mapping | transcript: nurse, doctor, patient. Model `primary_speakers`: nurse, doctor (patient absent). Gold `primary_speakers` equals the transcript's speaker table in 50 of 50 dev records. |
| Patient facts attributed to the patient | the model wrote the patient's speaker id `person_3` instead of the role `patient` (schema roles are `patient`, `doctor`, `nurse`…). A role-based scorer would fail it although the speaker is right. |
| Nurse facts attributed to the nurse | **No**: the vital signs (SEG0030, person_1) were attributed to person_2, the doctor. |
| Doctor facts attributed to the doctor | `stated_by`, `requested_by` use person_2 (correct speaker) but again as an id, not the role. |
| Segment ids against the transcript | all 48 fact references and all 36 evidence `supports` are real ids; no invented ids. |
| Timestamps | evidence timestamps wrong (2.3); fact-level dates invented ("2023-10-01"). |

Nothing was corrected silently; these are observed differences.

---

## 3. Proposed v2.2 output design

### 3.1 Principle
The transcript is the source of truth. The model outputs **facts with references**; deterministic backend code turns references into evidence. Traceability stays a feature; only its implementation moves out of the model.

### 3.2 What the model emits
1. **No `clinical_evidence` key** (the backend builds it, see 3.4). The frozen full schema and evaluator require it, so v2.2 uses a **new, separate compact schema**; the frozen schema is not edited.
2. **`evidence_ids` becomes `refs`**: transcript segment ids, **1–2 per fact** (gold median 2, mean 1.75, maximum 13). The model copies ids from the line prefixes it was given; no EV renumbering.
3. **No speaker, role or timestamp text per fact**: the backend derives them (3.3).
4. **Sparse emission**: omit keys whose value is null, empty or the schema constant. The backend restores them. Measured: about 18% of non-evidence characters.
5. Compact JSON on one line per section (no indentation).
6. No `quality_checks` or `encounter_metadata` from the model; both are derivable (3.3).

Sketch of one record, in the model's output:
```json
{"chief_complaint":{"value":"feeling faint","refs":["SEG0003"]},
 "symptoms":[{"name":"feeling faint","status":"present","severity":"mild","onset":"since last night","aggravating_factors":["standing in the sun"],"refs":["SEG0005","SEG0007"]},
             {"name":"nausea","status":"resolved","refs":["SEG0009"]}],
 "negative_findings":[{"finding":"chest pain","refs":["SEG0011"]}],
 "medications":[{"name":"ramipril","frequency":"every morning","status":"currently_used","refs":["SEG0026"]}],
 "clinical_uncertainties":[{"type":"medication_discrepancy","description":"ramipril: patient states 5 mg; nurse states 10 mg","related":"medications[0]","refs":["SEG0026","SEG0027"]}]}
```

### 3.3 What the backend derives deterministically (measured on the 50 dev gold files)
| Derived field | Rule | Measured agreement with gold |
|---|---|---|
| `encounter_metadata.primary_speakers` | transcript speaker table | 50 of 50 records |
| `reported_by` | role of the speaker of a cited segment | 1,254 of 1,254 |
| `stated_by` | same | 89 of 89 |
| `observed_by` | same | 80 of 80 |
| `requested_by` | same | 79 of 81 |
| `responsible_person` | **not derivable** (the person who must act, often not the speaker) | 163 of 266, so the model keeps emitting it |
| `clinical_evidence` | one record per cited segment | see 3.4 |
| `quality_checks` | flags from the facts (negation present, uncertainties present, and so on) | not measured; to be defined |

The speaker misattribution in 2.2 therefore disappears for all fields except `responsible_person`, **provided the model cites the right segment**.

### 3.4 Backend evidence resolver
Input: the fact's `refs` and the original transcript file. For each ref: look up `segment_id`; return `text`, `speaker_id`, `role`, `start_seconds`, `end_seconds`. Output on demand (clinician clicks a fact) or when materialising the full schema, in which case it creates `clinical_evidence` as `EV_001…` records using the same convention as the gold (one record per cited segment, `mm:ss` from the floor of the seconds, `supports` listing field paths).

Rules the resolver enforces and reports (never silently repairs):
* ref not in the transcript → flagged `invalid_reference`, fact kept, shown as unsupported;
* ref count above a limit (proposed 3) → flagged `over_cited`;
* the same segment cited by more than N facts → informational;
* optional lexical support check (does the cited line mention the fact's key words), reusing the idea in `evidence_evaluator.py`, labelled as lexical only.

The resolver gives no clinical correctness guarantee; a valid reference does not prove the claim.

### 3.5 Risks of this design
* Models can still cite the wrong line. Valid-but-wrong references are not detectable without a support check or human review.
* Dropping the model-written evidence changes the contract of the frozen evaluator and the schema, so v2.2 results are **not directly comparable** to P00/P01/P02 v2.1 evidence scores; only entity metrics are.
* `refs` copied from the line prefix is a lighter task than evidence records, but the 1.7B model has already shown it over-cites (16 ids); the "1–2" limit must be tested, not assumed.

---

## 4. Clinical extraction improvements

These are analysed separately from evidence. The omissions in 2.2 are not caused by the token budget: 00168 stopped normally at 3,789 tokens and still missed seven negatives and five actions.

### 4.1 Likely causes (from the outputs; not all tested)
1. **Budget spent early on evidence**, so the model's own output is dominated by a list it must also keep consistent. Likely contributes to shallow sections but cannot explain the empty `negative_findings` on a finished record.
2. **Denials are not framed as facts.** SEG0011 "I haven't had fainting or chest pain, no" is a denial; the model produced an empty list. P00/P01 showed the same pattern in the earlier audit (negatives near zero).
3. **A 4,170-token prompt for a 1.7B model.** The section checklists may be too long for it to apply item by item.
4. **Output-order effect.** Sections are generated in a fixed order; late sections (actions, uncertainties, quality checks) arrive after the model has spent most of its budget; in 00168 `quality_checks` is absent although the record finished normally.
5. **Speaker semantics left to the model** (`reported_by` etc.).
6. **Template fields filled by pattern**: the invented route, indication, smoking and 2023 date are values the model completes from the template shape. The prompt asks for null when absent but the template shows value-shaped slots.

### 4.2 Prompt improvements for v2.2 (to be verified one at a time on the three diagnosed records)
* Remove all evidence text from the prompt; state: "cite 1–2 segment ids per fact, exactly as written in brackets; never write transcript text, names, times or speaker roles".
* Per-section short rule plus one worked mini-example per hard case (negation, resolved symptom, planned medication, discrepancy), using **invented non-clinical filler**, not the 'no fever, no allergies, no previous surgery' text that leaked in P00/P01.
* Negation: "Write a negative finding only when a speaker explicitly denies it ('no', 'haven't had', 'never'). A symptom not mentioned is not a negative finding. Do not write smoking, alcohol, or any habit that was not asked and answered."
* Resolved symptoms: "'went away' or 'has gone' → status `resolved`, same section as symptoms."
* Planned medication: "a medicine the doctor starts or prescribes now → `status: planned`, dose and frequency as spoken."
* Contradictions: "If two speakers give different values for the same item, set the value to null and add a `medication_discrepancy` (or the relevant type) uncertainty that names both values. Never choose one." Add: "A chart value stated by the nurse counts as a second source."
* Do not invent values: "date, route, indication, basis are copied from the transcript or left out. Never write a calendar date unless it was spoken."
* Order sections so that the highest-risk ones (negatives, medications, uncertainties, actions) come **first**, and drop `quality_checks`, `encounter_metadata`.

### 4.3 Schema improvements (new compact schema, frozen schema untouched)
* `refs` instead of `evidence_ids`; no `clinical_evidence`.
* Sparse emission with documented defaults.
* Roles from a closed enum (`patient`, `doctor`, `nurse`, …) derived by the backend, not model free text.
* Types for values (numbers as numbers) documented and checked by a new validator (the frozen schema has no types).
* Contradiction as a first-class field: `value_conflict: {source_a, source_b}` could replace prose, to be decided with the owner.

### 4.4 Training-data improvements
The track is limited to prompting; no fine-tuning is proposed here. For a possible later stage:
* A converter can produce a v2.2 gold from the existing gold: `evidence_ids` EV → segment ids is exact (1,772 of 1,772 mapped), speaker-derived fields can be dropped (measured above), evidence list dropped, null keys dropped. This yields compact targets with no manual work.
* Few-shot examples for the prompt can be built from dev records **outside** the 8 pilot ids and with invented text where a record would otherwise leak into evaluation.
* Gold conventions to document and re-verify before use: `responsible_person`, negative-finding scope, `reported_by`.

---

## 5. Evaluation plan

All frozen-evaluator behaviour stays as is. v2.2 adds a **new evaluator script** that materialises a full schema record from the compact output and reports separately.

| Measure | Definition |
|---|---|
| JSON validity | parsed, closed JSON; finish reason `stop`; also reported as the share of records truncated |
| Clinical entity P/R/F1 | the existing strict canonical multiset matching on the materialised record, 18 categories, failed output = zero predictions, headline = all records (tier 1); parsed-only paired comparison (tier 2) |
| Negative findings | P/R/F1 of the `negative_findings` category, plus the count of negatives produced where gold has none |
| Medication extraction | P/R/F1 of the `medications` category; planned medications recall separately |
| Discrepancy handling | for each gold `medication_discrepancy` / `conflicting_statement`: uncertainty present, both values named, **dose left null** (a chosen dose counts as an error) |
| Evidence-reference validity | share of `refs` that exist in the transcript; share of facts with 1–3 refs; share of refs whose segment speaker matches the gold speaker |
| Evidence correctness against gold | overlap of a fact's refs with gold segments for that fact (using the 1,772/1,772 mapping) |
| Unsupported-claim rate | share of predicted facts whose cited segments do not contain the value lexically, plus a count of values that appear in no segment (dates, routes, habits); computed as in `evidence_evaluator.py`, labelled lexical |
| Output tokens | per record, and the number of records above 3,300 and at 4,096 |
| Generation time | per record, prefill and decode separately |

---

## 6. Proposed v2.2 pilot (for approval; not started)

### Objective
Show, cheaply, that the compact design (a) finishes inside the cap, (b) produces valid references, and (c) is not clinically worse than v2.1 on the three diagnosed records. Not to estimate F1.

### Records
**Six**: the three diagnosed records (00168, 00204, 00037), so the change is tested where it failed, plus the next three of the already approved pilot order (00092, 00152, 00157), so no new record is selected. All are authorised dev ids. With about 3 minutes of prefill and 1.3–3.4k output tokens at about 2.5 tokens/s, each record should take roughly 12–25 minutes (estimate), about 1.5–2.5 hours for six, against the 30 minutes per record at the cap in v2.1.

### Run controls (carried over)
Same model, revision, GPU, greedy, thinking off, `max_new_tokens` 4,096, retries 0, RAM gate 8.0 GiB, stop on OOM, frozen prompt, schema and files with hashes.

### Proposed gates (to be fixed before the run; thresholds are judgment, not derived from v2.1)
| # | Gate | Threshold |
|---|---|---|
| H1 | all six finish with `stop` | 6 of 6, none above 3,300 output tokens |
| H2 | JSON valid and materialisable | 6 of 6 |
| H3 | invented segment ids | 0 |
| H4 | facts with 1–3 refs | at least 90% |
| H5 | invented values on 00168 (smoking, 2023 date, routes) | 0 |
| H6 | 00168: negatives recalled | at least 4 of 7; ORS planned medication present |
| H7 | 00168: ramipril discrepancy | uncertainty present and dose null |
| H8 | entity micro-recall on the six, tier 1 | not below the v2.1/P01 reference computed on the same six ids |

H8 needs P00/P01/v2.1 references recomputed for the six (v2.1 has only 3 records, two failed). Only the 00168 comparison is meaningful for P02 v2.1.

### Early-stop rule
The v2.1 rule (stop if 2 of 3 hit the cap) was built for an evidence-heavy design. The v2.2 objective is compactness, so stop when:
* record 1 (00168) exceeds 2,500 output tokens, or does not parse, or invents a segment id (it should need about 1,300–2,000); or
* any two records of the first three reach the cap, or any one reaches the cap while another exceeds 3,300 tokens.
Stopping after record 1 costs at most about 20 minutes, rather than 30 minutes at the cap. No other record is retried.

---

## 7. Implementation sequence (future; nothing below is done)

### A. Prompt and schema changes
| File | Change |
|---|---|
| `prompt_versions/P02_comprehensive_v2_2.txt` (new) and `prompt_versions/drafts/` | new prompt as in section 4.2 |
| `schemas/` or `manifests/` new `compact_output_schema_v2_2.json` | compact schema, defaults, enums, types |
| `reports/P02_v2_2_PROMPT_DRAFT.md` (new) | draft, template-vs-schema verification (reuse `verify_p02_template.py` idea) |

### B. Backend evidence resolver
| File | Change |
|---|---|
| new `evidence_resolver.py` | segment lookup, materialise `clinical_evidence`, derive roles and `primary_speakers`, flag invalid or over-cited refs |
| new unit tests | refs, invalid id, role derivation (1,254/1,254 rule), `mm:ss` convention |
| later, outside this repository's evaluation: the API/frontend call that returns a segment for a clicked fact | not part of the pilot |

### C. Code changes
| File | Change |
|---|---|
| `scripts/run_prompt.py` | none expected: `--prompt` and `--ids` already exist. A materialisation step would be separate. |
| new `scripts/materialise_v2_2.py` | compact output → full record |
| new `scripts/evaluate_v2_2.py` | measures in section 5; the frozen `evaluate_run.py` and 0.6B code stay unmodified |

### D. Dataset changes
| File | Change |
|---|---|
| none to existing datasets or labels | the old `dataset_v2_batch_001` and `..._corrected` are untouched |
| new derived gold (compact targets, SEG-mapped) in a new folder | from `make_v22_gold.py`, read-only on the corrected dataset |

### Dependencies and risks
* The corrected dataset has to stay frozen; v2.2 depends on its segment ids (the mapping is exact today).
* Gold uses `mm:ss` floors; the resolver must follow the same convention.
* The decision on whether `quality_checks` is derived or generated needs an owner decision.
* A new evaluator is a new measurement instrument: validate it first against the gold (gold must score 1.0, and the three v2.1 outputs should reproduce the measurements above).
* The unsupported-claim measure is lexical only.
* Running even six records costs 1.5–2.5 hours; only the early-stop rule limits waste.
* No fine-tuning and no change to the 4,096-token cap are proposed.

---

## 8. Files inspected (read-only)
Run files: `logs/P02_v2_1_pilot8_EARLY_STOP_RULE_CHECK.json`, `logs/inference_P02_v2_1_pilot8.log`, `logs/performance_P02_v2_1_pilot8.json`, `logs/P02_v2_1_pilot8_stdout_stderr_attempt2.log`, `logs/run_exit_codes.txt`, `logs/run_settings_P02_v2_1_pilot8.json`, `outputs/raw|parsed|failed/P02_v2_1_pilot8/*` (00168, 00204, 00037), `prompt_versions/P02_comprehensive_v2_1.txt` (evidence rules and template lines).
Data: `dataset_v2_batch_001_corrected/output/inputs|labels/encounter_00168.json`, `dataset_v2_batch_001/output/inputs|labels/encounter_00168.json`, input and label files of the 50 frozen dev ids in the corrected dataset (sizes, mappings, speaker rules), `manifests/FROZEN_50_PROMPT_DEV_IDS.json`.
Code (read only): `direct_inference_baseline/inference/inference_runner.py` (`render_transcript`), `config/settings.py`, `evaluation/schema_validator.py`, `evidence_evaluator.py`, `clinical_metrics.py` (grep), `direct_inference_1_7B/scripts/common_1_7b.py`, `run_prompt.py` (grep).
Not inspected: the content of the 00204 and 00037 facts against their gold (only structure and size), the `final_label_schema.json` beyond what earlier work recorded, the project report and architecture diagram.
Analysis scripts used (read-only, in the session scratchpad): `cmp168.py`, `cmp168b.py`–`cmp168g.py`.
