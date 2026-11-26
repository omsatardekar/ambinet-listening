# P02 v3 — prompt design and validation (no inference run yet)

Prompt: `prompt_versions/P02_v3_p01_schema_no_evidence.txt`, sha256 `31C61B484E367B1F4A2D2ACEACDCBEDBF127646962DDAC08C4A2DD7FA9957BBB`. P01 (`P01_schema_guided.txt`) is untouched.

## What changed relative to P01

| P01 | P02 v3 | Why |
|---|---|---|
| Rule 11: every item lists `evidence_ids` pointing to model-written `clinical_evidence` records | Model writes **no** evidence records. `clinical_evidence` is always `[]`; `evidence_ids` hold transcript segment ids (`SEG0007`), copied exactly, only the 1–3 lines that state the fact | evidence is rebuilt by the backend; the evidence blob caused P01's truncations |
| Rule 6 example "no fever, no allergies, no previous surgery" | generic wording (a denied symptom, allergy, habit or past event) | the example leaked into 10–14 of 25 P01 outputs |
| Rule 5 roles | adds "read the role in brackets; `person_1` is not a role and is not always the patient" | 45 of 168 matched pairs wrote a speaker id |
| — | new block "What to extract": one line per section (every symptom with its details; every denial as its own item; question ≠ answer; family history with relation; social history only if discussed; every medicine incl. stopped/planned; possible allergies kept uncertain; every measurement; exam findings only; ROS only if explicit; differential ≠ condition; every test; every action as a separate item, no invented dates; follow-up; uncertainty only if actually present) | completeness and anti-hallucination instructions from the task |
| — | six short invented examples (denials, several symptoms, current + stopped medicine, family + social history, several actions, nurse-read vitals) with "never copy their content" | teach behaviour, not content |
| — | a final section-by-section check ("this check never permits inventing information") | completeness review |
| — | naming guidance: `vital_signs.normalized_name` from eight names, `social_history.category` from six values, `review_of_systems.system` as a body system | P01 outputs were rejected by the strict key for `weight/bmi/pulse` etc. |
| Structure rules | rule on evidence replaced; `clinical_evidence` removed from the list of non-empty arrays | consistent with the above |

**Not changed:** the 20 top-level keys and their order; every nested key and its order; every field name (`evidence_ids`, `reported_by`, `stated_by`, `observed_by`, `requested_by`, `responsible_person`, `related_entities`); the Allowed-values block (byte-identical to P01); `encounter_metadata`, `extraction_status`, `quality_checks`; null / empty conventions; the compact-JSON instruction. Nothing is sparse, renamed or reordered (the v2.2 mistake).

**Disclosure — tuning on development data.** The three naming vocabularies in the last row were read from the gold labels of the 50 development records (the schema itself does not state them). The same 50 records were used before for 0.6B prompt work, so every result here is development-only, not independent validation. It also means this run measures the combined effect of the whole prompt, not each change separately.

## Validation performed (no model, no inference)

| Check | Result |
|---|---|
| Static prompt check `p02_v3/code/verify_prompt_v3.py` (`derived/PROMPT_V3_VERIFICATION.json`) | 15 of 15 pass: placeholders; 20 top-level keys and every nested key path (P01's 185 minus the sub-keys of `clinical_evidence`, which the model no longer writes) identical to P01 in name and order; only `chief_complaint` (evidence placeholder) and `clinical_evidence` differ; `quality_checks` and `encounter_metadata` byte-identical; enums byte-identical; no old leaked phrase; no dev encounter id; no 5-word sequence of any example sentence in any dev transcript; no example-specific clinical term anywhere in the dev transcripts or gold; no BOM/CRLF |
| Unit tests `p02_v3/code/test_v3.py` (`derived/UNIT_TEST_OUTPUT.txt`) | 7 of 7 pass, incl. gold→segment ids→backfill reproduces the gold evidence records for all 50 dev records; invalid ids kept and flagged (none repaired or dropped); model-written evidence reported and replaced; input not mutated; excess references kept (warning only) |
| Evaluator on a perfect model output (`derived/GOLD_ROUNDTRIP_EVALUATOR_CHECK.json`), 50 records, both the raw model form (segment ids, `clinical_evidence` `[]`) and the backfilled record | strict F1 1.000 (1,860 TP, 0 FP, 0 FN) and 3,258 of 3,258 references valid, in both forms |
| Token counts, tokenizer file only (`derived/PROMPT_V3_TOKEN_COUNTS.json`) | calibration exact on all 30 P01 records (0 difference); template 2,087 tokens (P01) → about 3,000 (v3); input median 5,115, max 6,054 tokens |
| P01 baseline | prompt, outputs, ids, model and conversion record byte-identical to the P01 freeze manifest |

## Backend evidence handling

`p02_v3/code/backfill_evidence.py` is a small adapter around the existing Stage 1 `EvidenceResolver` (no second resolver). It validates each id against the transcript, resolves speaker id, role, text and MM:SS times, allocates `EV_001…` in transcript order, fills `clinical_evidence` and `supports`, and rewrites valid segment ids to EV ids. An id that is not a segment id of the transcript is kept as given and flagged. `quality_checks` stays as the model wrote it (it is not scored). The frozen evaluator and matcher are not modified.

## Run settings (frozen, unchanged from the 1.7B P01 run)

Qwen3-1.7B revision `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`, OpenVINO FP16, GPU, greedy, thinking off, `max_new_tokens` 4,096, fresh pipeline per record. Differences from P01: pilot controls from your decisions D1–D3 (RAM gate 8.0 GiB before the first load, retries 0, stop on out-of-memory) and the longer prompt. Freeze manifest `manifests/FREEZE_P02_v3_dev30.json`; ids `manifests/P02_v3_30_IDS.json`.

Early-stop rules (fixed before the run, `p02_v3/code/stop_rules_v3.py`): stop if record 1 does not parse; stop if two of the first three records do not parse; stop if two of the first three parsed records have 16 or more of 18 sections empty. After record 3 nothing stops the run and failures count in the headline score.
