# 02. The datasets: what they contain, how they were made, and their weaknesses

All data is synthetic. No real patient data, no real recording, and no clinician review is involved anywhere in this document.

## 1. Overview

| Data | Size | Made by | Used for | Folder |
|---|---|---|---|---|
| **Round-1 corpus** (Batches 1 to 9) | 4,200 encounters | templates, hand-written drafts, scenario profiles | training (2,856), validation (250), locked test (973), reserve (121) | `data/round1_synthetic/` |
| **Natural round-2 data** | 529 written, 304 accepted | a language model (writer) + a different model (checker) | round 2 training (263 accepted) and held-out validation (41) | `data/round2_natural/` |
| **Round-3 data** | 112 strict-accepted natural + 300 replayed | subset of the round-2 data | round 3 training | `data/round2_natural/run3/` |
| **20 hand-written scenarios** | 20 consultations of about 11 minutes | written by hand | realism test only, never trained on | `scenarios/` (repository root), model inputs in `data/module3_eval_inputs/` |
| **30-encounter baseline subset** | 30 (inside Test A) | from Batch 1 | the only set that has a before-and-after against the old H1 model | listed in `data/round1_synthetic/manifest.csv` (`exp008_eval_id`) |

Every encounter has a **transcript** (turns with speaker ids and roles) and a **full structured label**. The label format is defined in `data/round1_synthetic/schema/final_label_schema.json`.

## 2. The round-1 corpus (4,200 encounters)

| Batch | Encounters | How it was made |
|---|---|---|
| 1 | 500 | template generator; its own README says "evaluation use only", so it is **never trained on** |
| 2 | 500 | template generator, second profile set |
| 3 | 500 | 107 hand-authored encounters plus 393 drafts from a colleague, validated and compiled with a scenario description language; **the only human-written dialogue** |
| 4, 5, 6, 7, 8 | 500 each (2,500) | template generator with new scenario profiles: best, middle and worst cases side by side, different specialties |
| 9 | 200 | deliberately non-obvious cases: atypical presentations, mimics, medicine-induced problems, quiet red flags |
| **Total** | **4,200** | |

**What "template-driven" means for us.** In Batches 1, 2 and 4 to 9 the dialogue is assembled by a program from scenario profiles (a condition, a set of symptoms, medicines, vital signs, plan items) with different patient names and wording. The language is correct and consistent but regular: doctors ask in a similar order, patients answer cleanly, corrections and interruptions are rare. This is useful for teaching format and rules, but it is **not what real speech sounds like**. It is the main reason the round-1 score on template test data (0.933) is higher than on natural hand-written speech.

**Labels.** Every label was validated automatically: the cited evidence text exists in the cited turns, enum values are legal, speaker attribution is consistent, and duplicates against earlier batches were removed. Batch 3 labels were validated by the same rules. **No label was reviewed by a clinician.**

### 2.1 What the model sees and writes
| | First idea | What was trained |
|---|---|---|
| Prompt | the H1 prompt, 2,359 tokens | a short prompt of **313 tokens** (`prompt/short_prompt.txt`) |
| Transcript line | `[SEG0001] person_1 (DOCTOR) 0.70-5.72s: text` | `[SEG0001] person_1 (DOCTOR): text` (timestamps removed) |
| Model output | full JSON with every key | **compact JSON**: empty and null fields are left out, at most two evidence ids per item, `clinical_evidence` omitted |
| What the project receives | full JSON | full JSON: `expand()` restores every key in the original order |

Why: the T4 GPU is slow (about 500 tokens per second), so every token that carries no clinical information costs training time and money. Removing timestamps saved **692 tokens per example (18%)**: the median example went from about 3,800 to 3,115 tokens. The start and end seconds carry no clinical meaning (labels cite segment ids, not times); they stay in the pipeline and the front end, but the model never sees them, so the scoring file must format lines exactly as in training. The compact form is **lossless**: `expand(compact(label)) == label` was checked on all 4,200 labels (`codec/roundtrip_report.json`).

### 2.2 The split
| Split | Encounters | Purpose |
|---|---|---|
| **Train** | 2,856 (3,484 lines with 628 rare cases repeated once) | the model learns from these; `train_oversampled.jsonl` |
| **Validation** | 250 = 190 "seen" + 60 "unseen" | choose the checkpoint, never trained on |
| **Test A (benchmark)** | 500 = all of Batch 1 | final score, comparable with every earlier experiment |
| **Test B (curated)** | 473 | final score on new, harder, more natural cases |
| Reserve | 121 | unused; leftovers of held-out scenario groups |

Training contributions by batch: batch 2 = 344, batch 3 = 419, batch 4 = 414, batch 5 = 385, batch 6 = 371, batch 7 = 418, batch 8 = 413, batch 9 = 92.

**Why not a random split.** Many encounters come from the same scenario with different names and wording. A random split would put near-twins in training and test and inflate the score. We hold out **whole scenario groups**: measured word 5-gram overlap of Test B with training has median 0.06 and maximum 0.115 (benchmark: median 0.04, maximum 0.094). `test/TEST_LOCK.json` stores the locked test ids and file hashes (dated 2026-11-22); no test id is in training or validation.

**Seen versus unseen validation.** Seen = new encounters from scenario groups that are in training (normal learning). Unseen = scenario groups completely absent from training (does the model generalise). The gap between the two loss curves is the overfitting signal.

**Test B is chosen, not random:** 102 encounters from 15 of the 28 Batch-9 scenarios; about 78 worst-case (emergency), 95 middle and 38 best-case encounters from Batches 4 to 8, at least one group from each of 12 specialties; 100 from Batch 2; and the **60 hand-written Batch-3 conversations**. Within each held-out group we kept up to 10 encounters, the ones with the most difficulty (more uncertainties, 4 or more speakers, an unidentified voice, more allergies, medicines and negatives). Encounters with a documented uncertainty: 48% in Test B against 35% in training.

**Rare cases repeated once** (628 extra lines): no vital signs 236, no social history 208, unnamed medicine 97, disputed allergy 94, unidentified speaker 90, no negative findings 75, conflicting statement 68, no history at all 49. Reason: the model must learn to leave sections empty and to flag real doubts, and these cases are rare.

### 2.3 Coverage of the failure classes (training set, from `coverage_audit.json`)
Allergy never mentioned and none recorded 18% (508 encounters); explicit "no allergies" 46%; allergy uncertain, disputed or historical 14% (412); discontinued medicines 9% (267); medicines without a stated dose 34%; no vital signs 8% (236); no assessment stated 9% (269); no follow-up arranged 23% (648); no investigations 23% (652); an unidentified speaker 3% (90); caregiver or family speaking 28%; nurse or clinical staff speaking 30%; any recorded uncertainty 35%.

### 2.4 Sizes
Median example (prompt + transcript + answer) is 3,115 tokens, maximum 5,412; by parts, the round-1 training examples have a median **prompt of 1,497 tokens and answer of 1,620 tokens**. One pass over `train.jsonl` is about 9.0 million tokens.

## 3. The natural round-2 data (why and how)

**Why.** After round 1 the model was far better than the baseline but clearly worse on natural hand-written speech (precision 0.762 against 0.945 on the template test set). The remaining errors were spoken corrections (a stopped or swapped medicine recorded as current), denials recorded as findings, a relative's medicine attributed to the patient, spoken-number and unit slips, and sections invented from nothing said. Round 2 adds data that contains exactly these.

**How it was made** (`scripts/local/natural_gen/`):
1. **Blueprints** (`blueprints.py`): 28 real-life visit families (for example exertional chest tightness, child fever with two disagreeing parents, elderly polypharmacy with a carer, diabetes with insulin confusion, ACE-inhibitor cough, recurrent UTI, early-pregnancy bleeding, gout flare, memory concerns with a spouse, post-operative wound check, repeat-prescription review with a pharmacy technician). Each family states what really exists in the visit and where the traps are. Each encounter combines a family with a random setting: 8 patient styles (chatty, terse, anxious, dismissive, formal, tired, over-explaining, uncertain), 5 doctor styles (brisk, warm, thinks aloud, distracted by the computer, summarises back), 6 English flavours (Indian, British, American, Irish, Australian, South African), 9 combinations of extra speakers (nurse, family member, carer, clinical staff), a difficulty (medium or hard), a target length, and several of **18 natural-speech features** (self-correction, spoken numbers, denial then admission, third-party medicine, stopped or never-taken medicine, tangents and small talk, interruptions and trailing off, colloquial drug names, the doctor thinking aloud, a hedged plan, disputed numbers, vague dates, a relative speaking for the patient, a recalled test result, an ambiguous answer, a doctor who misses topics, a patient answering a different question, a doctor who changes their mind).
2. **Writer.** A language model (grok-4.7, the `JUDGE2` deployment) wrote the conversation and the label together in one call, with evidence given as turn numbers. The generator converts it to the exact training format (person ids by first appearance, `[SEG0001]` lines) and the label is checked with the project's schema validator and then compacted.
3. **Independent verifier.** A **different** model (gpt-5.4, the `JUDGE` deployment) checked every label: (a) the frozen precision prompt (is each label fact supported by the transcript?) and (b) an omission prompt (which important spoken things are missing, and which of those are critical).
4. **One repair round.** A rejected label was returned to the writer with the findings (transcript unchanged) and checked again. The first verdict is kept as `initial_verify`.
5. **Acceptance rule** (`is_accepted`): no contradicted fact and no critical error; before the repair round at most 2 unsupported or partial facts and no critical omission; after it at most 3 such facts and at most 1 critical omission.

**Counts.** 529 consultations were written (267 hard, 262 medium; 95 with two speakers, 219 with three, 211 with four, 4 with five). **304 were accepted** (263 for training, 41 in four **held-out families** that are never trained on: heavy periods with anaemia, gout flare, memory concerns with a spouse, asthma flare with inhaler). 225 were rejected or unverified.

**Lengths.** Natural examples are much longer than round-1 examples: median prompt **2,320 tokens** (round 1: 1,497) and median answer **2,449 tokens** (round 1: 1,620); median total 4,795 tokens, maximum 7,823. Because the T4 cannot train on sequences longer than about 6,144 tokens, **37 of the 263 natural training examples were dropped for length** in round 2 (226 natural examples were trained on, plus 600 replayed round-1 examples).

## 4. The round-3 data
A stricter subset of the accepted natural data: at most 1 unsupported fact and no critical omission. That leaves **112 training examples** (and 15 held-out), plus **300 replayed** round-1 examples = 412 lines; after the length limit, about 397 were trained on (97 natural). Details in document 06.

## 5. The 20 hand-written scenarios
Natural consultations (3 to 5 speakers, hesitant and terse patients, a carer or family member speaking, deliberately partial or absent facts), written for the application's test-recording feature and **never used in training or checkpoint selection**. Each `scenario.json` has a `design` block listing what was put in on purpose, what is partial, and what is deliberately absent. They have no label file; the design block is the key for recall. Converted to model inputs by `scripts/local/build_module3_eval.py` (clean dialogue text, no timestamps, 3,700 to 4,450 tokens each). Limitation: this is the clean dialogue text, not an ASR transcript, so speech-recognition errors are not included.

## 6. Drawbacks and risks (say these to external reviewers)
1. **Template-driven round-1 dialogue** (all batches except Batch 3, which is about 85% of the training lines): regular wording and order, clean answers. Scores on it overstate performance on real speech.
2. **Labels are not clinician reviewed.** Round-1 labels are program-written and automatically validated; round-2 labels are model-written and model-verified.
3. **Circularity in round 2.** The writer, the verifier and the evaluation judge are all language models. The writer (grok-4.7) and the verifier (gpt-5.4) are different families on purpose, but a shared blind spot could survive all three. The 20 hand-written scenarios and Test B stay untouched as held-out checks for this reason.
4. **Label conventions.** Some labels contain normalised names that are not literally in the transcript (for example a named blood-test panel when the doctor said "blood tests"); this can teach the model to guess. It has not been fully audited.
5. **Length gap.** Natural examples are about twice as long as round-1 examples and a share of them could not be trained on (T4 memory). The model has seen few consultations as long as real ones.
6. **Few held-out natural families** (4 families, 41 encounters), so natural validation loss is a noisy signal.
7. **No ASR errors.** Training and test text is clean dialogue; real input comes from speech recognition.
8. **Only English**, with six accent flavours written by a language model.
9. **Rare cases** are repeated once in training; repeated examples can slightly raise memorisation of those cases.
10. **Only 30 encounters have a baseline** (before and after); the other 943 test encounters show only the fine-tuned level.

## 7. Questions an external reviewer may ask
**Is the test set clean?** Yes by construction: scenario groups of Test B and of the unseen validation part are absent from training, Test A is all of Batch 1 (never trained on), and the lock file records the ids and hashes. The test was run once for the chosen checkpoint; no setting was changed after seeing its result.

**Why 4,200 and not more?** The corpus was planned as batches of 500 (the project owner's target was a corpus of about 4,000 encounters). We did not run a data-size experiment, so we cannot say how performance would change with more or less data. What we can say is that the unseen-scenario validation loss stopped improving after step 400 (document 04), and that the weak point was realism of the language, not the number of examples (round 2).

**Why synthetic?** Real recordings need company approval before use for training or testing (an open decision of the project owner). Everything here was designed so a later approved real set can be added.

**Why were timestamps removed?** They carry no clinical meaning, labels cite segment ids not times, and they cost 692 tokens per example. The original timestamps remain in the pipeline.

**Why a compact output?** To save tokens and time without changing what the project receives; the round trip is proven lossless on all 4,200 labels.

**Why were rare cases repeated?** The model must learn that "nothing said" means an empty section and that a disputed fact is flagged, and these cases are rare.

**Was the same data used to choose the model and to test it?** No. Validation chose the checkpoint; the 973 test encounters were scored once; the 20 scenarios were never trained on.
