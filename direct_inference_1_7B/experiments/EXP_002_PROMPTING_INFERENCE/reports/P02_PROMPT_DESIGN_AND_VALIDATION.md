# P02 — prompt design and validation (strengthened prompt, reviewed before any full run)

Active prompt: `direct_inference_1_7B/experiments/EXP_002_PROMPTING_INFERENCE/prompt_versions/P02_p01_schema_no_evidence.txt`
SHA-256 `F6D5202F26D97C2D73C9D00ADBCA050BC7114AD8B0272749EEFF8D0757DE09B0`. The run pipeline (`scripts/run_prompt.py`) loads this file: the runner's own `build_prompt` returns a template identical to the file and renders the transcript lines without leftover placeholders (checked without loading a model). **The 30-record evaluation has not been run on this prompt.**

## What happened first
A 30-record run with the previous P02 prompt (SHA `31C61B48…57BBB`) was started and stopped after you asked for the prompt to be strengthened first. One record finished (00035: parsed, 1,352 tokens, 621 s) and one was in progress. All artifacts of that aborted run are preserved in `archive/obsolete_experiments_after_P01/_aborted_P02_run_first_prompt/`; nothing from it is in the active P02 folders.

Observed weaknesses of that one output (checked against the transcript; not a score): a symptom described as lasting ten days was written as temporality `past`; blood pressure was written as `167` and lost the `/90`; "severe" was missed; the follow-up was written as "in two weeks" where the doctor said "after the results are back"; several instructions (do not drive, bring someone, come back urgently) were missed; the ECG was typed `imaging`; the clinical_actions item lacked the `evidence_ids` key. The new prompt has a rule for each.

## Unchanged (verified)
The 20 top-level keys and their order, every nested key and its order, all field names, the Allowed-values block (enums), the output template (including `clinical_evidence: []`, `evidence_ids` placeholders, `quality_checks`) — the output-format block is **byte-identical** to the previous P02 prompt, and the key paths and enums are identical to P01. Not changed: P01, the dataset and gold, the 30-id list (byte-identical), the strict matcher, the evaluator, model settings, the evidence resolver / backfill code, the runner.

## Changes by extraction area
| Area | Strengthened rule (summary) |
|---|---|
| Temporality (new section) | Uses only the schema values. Still present for any duration → status present / temporality current ("a duration is not an end"); gone during this illness → resolved / resolved; separate earlier episode → resolved / past; comes and goes → present / current with the rhythm in `frequency`; decide from what is said about now, not from the clinician's tense or from being mentioned in the consultation; unclear → best-supported value, certainty uncertain, a clinical_uncertainties item, never an invented start or end |
| Symptoms | each distinct symptom its own item; name near the patient's words, standard normalized name; severity only when described; duration as `{"value": number, "unit", "normalized"}`; onset / frequency as spoken; details combined from several lines; nothing from a doctor's question unless confirmed |
| Negative findings | each denial separate (also inside long sentences); cue words (no, denies, without, never had, not experiencing); the known-absence phrases (no known allergies, no previous surgery, no known chronic conditions, no regular medication, never diagnosed with X); never from a question, never from an unmentioned item, never from a resolved symptom |
| History | patient / family / surgical / social kept apart; family history = condition + relation, never the patient's own; social categories and statuses; never assume smoking, alcohol, work or living situation |
| Medications / allergies | status rules (the doctor naming a drug ≠ currently_used); dose with units as said; route only when stated; indication never from usual use; adherence and unnamed-medicine uncertainties; allergies only when reported; "no known allergies" is a negative finding |
| Vital signs | whole value (blood pressure with both numbers as one string), units per vital sign, measured not planned, attributed to whoever read it out, closed normalized names |
| Assessment / conditions | provisional vs differential vs existing condition; no confirmation from suspicion; no diagnosis from symptoms alone; no duplicate concepts |
| Investigations | type guide (laboratory / imaging / cardiac / other), planned vs completed vs conditional, indication = the reason the doctor gives, no timestamps as clinical times |
| Actions / follow-up | every instruction separate; counselling = recommended + patient; orders = planned + doctor / clinical_staff; "if X" = conditional; `time_reference` null or `{"value","normalized_date"}`; follow-up stays dependent on results; each visit also yields a follow_up action |
| Examination / ROS | observed findings only, observed_by the clinician; no invented normals; no system normal from one denial |
| Speaker | role from the bracket on each line; `person_1` is not always the patient; attribute to who said or measured it; unknown when unclear |
| Evidence | segment ids only, smallest set that shows the exact value (negation, timing, dose, speaker), no filler, no whole conversation, no reuse for unrelated facts, no invented ids; `clinical_evidence` stays `[]`; every item keeps every template key |
| Examples | 14 short invented patterns covering ongoing-with-duration, resolved, intermittent, earlier episode / historical diagnosis, denials, missing stays missing, incomplete medication, compound vitals, suspected vs confirmed, planned investigation, several instructions, results-dependent follow-up, reported vs observed, family vs patient |
| Closing | completeness check and one short anti-hallucination section |

## Size
| Prompt | Template tokens (tokenizer file only) | Median input for the 30 records |
|---|---|---|
| P01 | 2,087 | 4,127 (measured by the P01 run; counter reproduces all 30 exactly) |
| previous P02 | 2,982 | 5,116 |
| **P02 now** | **4,645** | **6,685** (max 7,623) |

The increase (+1,663 over the previous P02, +2,558 over P01) is the temporality block, the per-section rules and the 14 patterns. Expected cost: about 3 minutes of prefill per record at the measured 29–40 tokens/s, i.e. a few extra minutes per record; no existing instruction was removed. A longer prompt can also lower a 1.7B model's compliance: this is a risk the evaluation has to show, not something the review can rule out.

## Validation (no model loaded, no inference)
| Check | Result |
|---|---|
| Static prompt validation `p02/code/verify_prompt.py` (`derived/PROMPT_VERIFICATION.json`) | 37 of 37: placeholders; 20 keys and every nested key path/order identical to P01 apart from the evidence sub-keys; output-format block and Allowed-values block byte-identical to the previous P02; enums identical to P01; 14 numbered patterns; required rule texts present; no old leaked P01 phrase; no dev encounter id; no 5-word run of any quoted example in any dev transcript; none of 19 example-specific terms (and no blood-pressure-like number) occurs in the 50 dev transcripts or gold |
| Unit tests `p02/code/test_p02.py` | 7 of 7 (backfill; gold round trip on 50 records) |
| Prompt-only synthetic review `p02/code/prompt_review_synthetic.py` (`derived/PROMPT_SYNTHETIC_REVIEW.json`) | an invented consultation; an output written by the rules passes shape / enum / temporality / speaker / evidence / vital-sign / follow-up checks and the backfill adapter with zero hard flags; 10 deliberately wrong variants (ongoing written as past, resolved written as current, truncated blood pressure, nurse measurement attributed to the patient, invented segment id, model-written EV records, denial from a question, result-dependent follow-up turned into weeks, invalid temporality value, dropped key, whole conversation cited) are each caught; every rule family is present in the prompt text. This checks consistency of the prompt and the checks, **not** model behaviour |
| Pipeline loads the active prompt | runner template == file; pre-flight passes under a throwaway run id (its files archived); 0.6B tree identical to its inventory |
| Integrity | P00 + P01 (318 files) and dataset / schema / matcher (3,096 files): 0 missing, 0 changed (SHA-256); 30-id manifest byte-identical |

## Disclosures and remaining weaknesses
- **Tuned on development data.** The naming and format conventions (vital-sign names and units, social-history categories and statuses, review-of-systems systems, blood-pressure string, duration object, `time_reference` object, known-absence negative findings, one follow_up action per follow-up) were read from the gold of the 50 dev records and the frozen schema enums. No transcript text or expected answer is in the prompt (verified), but results remain development-only.
- **The schema has no "unknown" temporality.** The prompt cannot express unknown timing except by best-supported value + uncertain certainty + a clinical_uncertainties item.
- **Intermittent and historical symptoms** have no dedicated value; they map to present/current with a frequency, or resolved/past.
- **Strict keys for clinical_actions and follow_up contain free text**, so correct actions can still score near zero; the fuzzy diagnostic and counts are reported separately.
- **Not proven by this review:** whether a 1.7B model follows 14 patterns and many rules, whether the longer prompt increases truncation, and whether the evidence ids it writes are correct. These need the evaluation.
- **Evidence:** `clinical_evidence` stays `[]` by design and is not a prompt failure; linking is left to the backend as you said.

## Before any run
`FREEZE_P02.json` and `configs/P02_CONFIG.json` do not exist yet; the pre-flight creates them from this prompt. If the prompt is edited again they must be regenerated before launch. The RAM gate (six readings, final ≥ 8.0 GiB) applies at launch.
