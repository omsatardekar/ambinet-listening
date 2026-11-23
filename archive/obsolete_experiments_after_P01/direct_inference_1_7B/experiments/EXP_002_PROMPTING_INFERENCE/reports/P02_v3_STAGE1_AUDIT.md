# P02 v3 — Stage 1 audit of P01 (before any change)

Date 2026-11-15. Development-only: the 50 frozen prompt-development ids were used for 0.6B prompt work before, and the labels are generator-derived. No inference was run for this audit. Every number below is recomputed from the files in this repository (P01 parsed/failed/raw outputs, corrected dataset `dataset_v2_batch_001_corrected`, the frozen entity matcher) and is stored in `p02_v3/derived/P01_30_ANALYSIS.json`.

## 0. Evaluation set and methodology

- **Evaluation ids:** the 30 records P01 completed = the first 30 of `FROZEN_50_PROMPT_DEV_IDS.json` (verified equal to the id set of `outputs/raw/P01_schema_guided_dev50`). Frozen as `manifests/P02_v3_30_IDS.json`.
- **Dataset:** `dataset_v2_batch_001_corrected` (the older `dataset_v2_batch_001` is a different encounter set and is not used).
- **Official metric:** the frozen strict entity matcher (`direct_inference_baseline/evaluation/entity_matching.py`). Per category a fact is keyed by one normalised field (symptoms: `normalized_name`; negative_findings: `normalized_name`; medications: `normalized_name`; vital_signs: `normalized_name`; social_history: `category`; review_of_systems: `system`; clinical_uncertainties: `type`; clinical_actions: `action_type|description`; follow_up: `type|time_reference`; …). A prediction is a true positive only when its normalised key equals a gold key. A paraphrase is therefore one miss **and** one false positive.
- **Headline (tier 1):** all 30 records, a failed record scores zero predictions. Tier 2 = parsed records only (reported next to it, never instead).
- These are precision / recall / F1 over matched facts. **They are not accuracy.**
- The matcher also has a built-in fuzzy mode. It is not the official metric; it is reported below only as a clearly labelled completeness diagnostic.

## 1–2. What P01 extracts, and recall by category (30 records, tier 1)

| Overall | Precision | Recall | F1 | TP / FP / FN |
|---|---|---|---|---|
| P01, all 30 (25 parsed) | 0.283 | 0.156 | 0.201 | 170 / 431 / 923 |
| P01, parsed only (25) | 0.283 | 0.189 | 0.226 | 170 / 431 / 731 |

Validity: 25 of 30 parsed; 5 failed (4 token-cap truncations at 4,096, 1 invalid JSON). Median 2,590 output tokens; 9.1 h total; median 1,047 s per record.

| Category | Gold | Pred | TP | P | R | F1 | Band |
|---|---|---|---|---|---|---|---|
| medications | 72 | 44 | 37 | .84 | .51 | .64 | good |
| clinical_assessment | 48 | 25 | 17 | .68 | .35 | .47 | moderate |
| vital_signs | 129 | 91 | 51 | .56 | .40 | .46 | moderate |
| procedures_and_investigations | 49 | 38 | 15 | .39 | .31 | .34 | moderate |
| family_history | 17 | 20 | 6 | .30 | .35 | .32 | moderate |
| social_history | 88 | 29 | 13 | .45 | .15 | .22 | poor |
| symptoms | 91 | 36 | 12 | .33 | .13 | .19 | poor |
| allergies | 13 | 21 | 3 | .14 | .23 | .18 | poor |
| past_medical_history | 50 | 33 | 6 | .18 | .12 | .14 | poor |
| surgical_history | 16 | 22 | 2 | .09 | .13 | .11 | poor |
| chief_complaint | 30 | 25 | 2 | .08 | .07 | .07 | poor |
| follow_up | 26 | 23 | 1 | .04 | .04 | .04 | poor |
| negative_findings | 168 | 40 | 4 | .10 | .02 | .04 | poor |
| clinical_actions | 165 | 42 | 1 | .02 | .01 | .01 | poor |
| physical_examination | 46 | 39 | 0 | 0 | 0 | 0 | zero |
| review_of_systems | 40 | 21 | 0 | 0 | 0 | 0 | zero |
| clinical_conditions | 20 | 29 | 0 | 0 | 0 | 0 | zero |
| clinical_uncertainties | 25 | 23 | 0 | 0 | 0 | 0 | zero |

## 3. Partial extraction (the model does extract, but incompletely)

The model is not extracting nothing. The count ratio (predicted / gold facts) shows where it stops early:

| Category | pred / gold | fuzzy recall (diagnostic) |
|---|---|---|
| clinical_actions | 0.26 (42 of 165) | 0.04 |
| negative_findings | 0.24 (40 of 168) | 0.05 |
| social_history | 0.33 (29 of 88) | 0.15 |
| symptoms | 0.40 (36 of 91) | 0.14 |
| clinical_assessment | 0.52 | 0.38 |
| medications | 0.61 | 0.51 |

Examples (strict matcher; the 5 failed records contribute only misses): in record 00060 vital_signs 4 of 8 gold matched, with 4 extra; in 00069 3 of 7, with 4 extra. For symptoms, gold has 91 items but P01 wrote 36: **under-extraction is the main gap** for symptoms, negatives, social history and actions.

**Part of the vital-signs gap is naming, not missing information.** In 00060, 00069, 00141, 00266 and 00042 P01 wrote `weight`, `height`, `bmi`, `temperature`, `pulse`; the gold normalised names are `body weight`, `body height`, `body mass index`, `body temperature`, `heart rate`. The strict key rejects these as miss + extra. The gold vocabulary is closed: eight vital-sign names, six social-history categories (living, occupation, smoking, alcohol, exercise, diet), seven review-of-systems systems (computed from the 50 dev gold records). The P01 prompt names none of these.

**clinical_actions and follow_up cannot score under the strict key.** Their key contains the free-text description / time reference. Recall near 0 is partly the matcher, not only the model. This is why the fuzzy diagnostic exists, and why action quality has to be judged on counts and examples as well.

## 4. False positives and unsupported claims

- `no allergies` appears in 14 of the 25 parsed P01 outputs, `no fever` in 13, `no previous surgery` in 10. These are the words of P01 prompt rule 6 (an earlier root-cause report established that they leak). Examples: allergies list `no allergies` (2) and surgical history `no operations` (4).
- Over-prediction relative to gold: clinical_conditions (29 vs 20), allergies (21 vs 13), surgical_history (22 vs 16), family_history (20 vs 17). All with low precision.
- Examples of extra items: "possible mini-stroke", "Underactive thyroid", "diabetes" written as clinical_conditions; examination findings and symptoms placed in physical_examination ("Numbness in the thumb and first two fingers").
- References: 424 of 424 fact references were valid in the P01 evidence block (`evidence_reference_validity`); no invented evidence ids were found. Lexical unsupported-claim indicators are in the JSON.

## 5. Speaker attribution

Only facts the matcher paired with a gold fact can be compared (168 pairs):

| Outcome | Pairs |
|---|---|
| correct role | 101 (60%) |
| speaker id written instead of a role (`person_1`, `person_3`) | 45 (27%) |
| wrong role | 13 (8%) |
| missing | 9 (5%) |

- The prompt already says never to write a speaker id, so 45 violations are model-side.
- The wrong roles are mostly vital signs and medications that the gold attributes to the doctor, written as `patient` (00035, 00042).
- Procedures' `requested_by` was missing in 9 of 15 pairs.
- clinical_assessment is correct in 17 of 17.

## 6. Negative findings

Missed on a very large scale: 4 of 168 gold items matched, 40 predicted (ratio 0.24). The one rule P01 gives (rule 6) carries an example that leaks into outputs, and nothing tells the model to extract every denial in a long sentence.

## 7. Cause of errors (observed vs. not proven)

| Symptom | Likely source | Evidence |
|---|---|---|
| leaked `no fever / no allergies / no previous surgery` | prompt instruction (example inside rule 6) | phrases in 13–14 of 25 outputs |
| vitals `weight/bmi/pulse/temperature`; social/ROS keys | prompt (no naming convention) + strict key | name pairs above; closed gold vocabularies |
| speaker ids written as roles | model limitation (rule exists) | 45 of 168 pairs |
| under-extraction of symptoms, negatives, social, actions | prompt gives no completeness instruction; also model limitation | count ratios 0.24–0.40 |
| actions / follow-up near 0 | evaluation key (free text) | key definition |
| 5 failed records | output formatting: the evidence block is one blob that dominates the output | 4 truncations at 4,096; median 2,590 tokens |

The last row follows the earlier P00/P01 analyses (evidence block share of output). Whether removing the evidence block removes those failures is **not yet measured**: it is the point of this experiment.

## 8. Baseline preserved

P01 prompt, outputs, ids, conversion record and model files are byte-identical to the P01 freeze manifest. Two scripts differ from that manifest: `scripts/run_prompt.py` (the approved D3 pilot-controls change; the old script is archived) and `scripts/evaluate_run.py` (last written 2026-11-14 20:48, after the P01 freeze at 12:03, in an earlier session). P01 numbers were therefore recomputed with the independent v2.2 evaluator and reproduce the documented values (P .283, R .156, F1 .201).
