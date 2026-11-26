# 01. The project and Module 3 (clinical extraction)

Read this first. It explains what we are building, what Module 3 does, why it is a small model, what was wrong with it before fine-tuning, and the words used in the other documents.

## 1. The project in one paragraph
**Ambient Clinical Listening** records a doctor-patient consultation, writes a speaker-aware transcript, extracts the clinical facts into a structured record with a small language model, and prepares a SOAP note with an agent. The whole pipeline (capture, transcript, extraction, SOAP note) is in this repository, together with every dataset, experiment and evaluation that led to the extraction model. All data used for training and testing is **synthetic** (no real patient data was used).

| Module | What it does | Where |
|---|---|---|
| 1 | hands-free recording ("Hey Asha"), upload of WAV recordings | `backend/`, `frontend/` |
| 2 | speech to text, speaker separation, speaker roles (doctor, patient, nurse, ...), output `final_transcript.json` and `slm_input.json` | `backend/`, `scripts/`, Azure AI Foundry |
| **3** | **clinical extraction: transcript in, structured JSON out. This is the model we fine-tuned** | `clinical_extraction/`, `finetune_slm/` |
| 4 | SOAP note written by a Foundry prompt agent, from the Module 3 output only | `soap_generation/` |

Module 4 reads only the Module 3 output (a decision of the project owner, 2026-11-20), so **the quality of the SOAP note is bounded by the completeness and correctness of the extraction**. That is why Module 3 is the part we fine-tuned.

## 2. What Module 3 receives and returns
**Input.** One consultation as a list of segments. Each segment has a segment id (`SEG0001`), a speaker id (`person_1`), a role (`DOCTOR`, `PATIENT`, `NURSE`, `CAREGIVER`, `FAMILY_MEMBER`, `CLINICAL_STAFF`, `UNKNOWN`), the text, and (from the front end) start and end seconds. The model sees one line per segment:

```
[SEG0001] person_1 (DOCTOR): Good morning, what brings you in today?
[SEG0002] person_2 (PATIENT): My foot has a sore that will not heal.
```

**Output.** One JSON object with these sections (each item names who said it and cites the segment ids that support it): chief complaint, symptoms, negative findings (things denied), medical history (past, surgical, family, social), medications (name, dose, route, frequency, status such as current or stopped), allergies, vital signs, physical examination, review of systems, clinical assessment (provisional or differential, only if the doctor said one), procedures and investigations, clinical actions (the plan), follow-up, clinical uncertainties (real doubts or disagreements between speakers), and quality checks. The exact definition is `data/round1_synthetic/schema/final_label_schema.json`.

**Rules the model must follow** (they are in the 313-token prompt and were taught by the training data): use only what is said; leave a section empty when nothing was said; a denied finding is a negative finding and never a symptom; a doctor's question is not a fact; a medicine the patient takes is not an allergy; a stopped medicine is not current; keep both statements when speakers disagree and describe the doubt.

## 3. Why a small model (Qwen3-0.6B)
* The Module 3 model is hosted as an **Azure ML endpoint on CPU** (OpenVINO, FP16); the application only knows the endpoint URL and key, so a better model can be swapped in without changing the application.
* The project mentor chose **Qwen3-0.6B** for the final track (recorded in `experiments/qwen3_0.6b/EXP_008.../README.md`). Measured reasons in our own logs: the 0.6B model peaks at about 3.1 GB of memory, while the 1.7B runs needed an 8 GiB memory gate and a 30-encounter run took about 8 to 9 hours on the same machine (document 03).
* The price of a small model is that it makes more mistakes than a large one when only prompted. Fine-tuning is how we close that gap (next section).

## 4. Why we fine-tuned: what the prompted model did wrong
The starting point (**H1**) was Qwen3-0.6B with a long hand-engineered prompt (2,359 tokens), no training. On 30 encounters judged by an LLM judge: **judge-F1 0.352, hallucination rate 0.262, critical-error rate 0.120** (document 07).

Six live runs on scripted consultations, checked line by line against the dialogue, gave 32 failure classes (`MODULE3_FINETUNING_FOCUS.md`, F1 to F32). The ones that matter most:
* **Invented allergy**: a normal medicine, a supplement or an over-the-counter tablet recorded as an allergy (5 of 6 runs).
* **Wrong polarity**: a present symptom filed as absent, or a stray sentence filed as a denial.
* **One phrase copied into many sections.**
* **A stopped medicine recorded as taken**; disputed or conflicting information recorded as settled.
* **Safety-critical denials dropped** (for example "no thoughts of harming myself").
* **Sections filled although nothing was said** (all five deliberately absent categories filled in the "absence test").
* **Incomplete lists** (1 of 4 vital signs, 1 of 3 medicines) and no evidence ids.
* **A spurious "date" uncertainty in every run**, probably copied from the prompt template (a hypothesis, not tested).

Fine-tuning teaches these behaviours directly instead of asking for them in a long prompt.

## 5. What we did (summary; details in documents 02 to 07)
1. Built a **4,200-encounter synthetic dataset** with full labels, split by scenario so test scenarios never appear in training (document 02).
2. Replaced the 2,359-token prompt with a **313-token prompt**, removed timestamps, and trained the model to write a **compact JSON** that expands losslessly to the full structure (document 02, 04).
3. **Round 1:** LoRA fine-tuning on one NVIDIA T4, 654 steps, 18.4 hours; checkpoint chosen on validation (step 400) (document 04).
4. Locked-test result: judge-F1 **0.933**; on natural hand-written speech it is clearly better than the baseline but lower than on the template data (document 07).
5. **Round 2** with 529 newly written natural-style consultations, and **round 3** with a stricter subset (documents 05, 06). Neither beat round 1 on precision; round 2 raises recall.
6. Added a **JSON repair guard** and **windowed extraction** for long consultations (documents 05, 07).
7. Packaged **two deployable models** for the existing Azure ML endpoint: step 400 (round 1) and step 156 (round 2), each with its 11 model files and its own scoring file (`deployment/`).

## 6. Words used in these documents
| Word | Meaning here |
|---|---|
| Token | a piece of text the model reads or writes (about 0.75 of an English word) |
| SFT | supervised fine-tuning: the model is shown the input and the correct answer and learns to produce the answer |
| LoRA | low-rank adaptation: the base weights are frozen and small extra matrices are trained; the result is a small "adapter" (about 160 MB) |
| Step (optimizer step) | one update of the weights; here each step uses 16 examples (accumulated one at a time) |
| Epoch | one full pass over the training data |
| Loss | how unlikely the correct next word was for the model; lower is better. Measured per answer token |
| Seen / unseen validation | validation examples from scenarios that are in training / scenarios held out of training |
| Greedy decoding | always take the most likely next token (temperature effectively 0); the same input gives the same output |
| Precision | of the facts the model wrote, the share the judge found supported by the transcript |
| Recall | of the facts that should be there, the share the model captured |
| Judge-F1 | harmonic mean of precision and recall under the LLM judge's verdicts. **Not clinical accuracy** |
| Hallucination rate | share of written facts that are unsupported or contradicted |
| Critical-error rate | share of written facts the judge flags as dangerous (a wrong medicine, dose or allergy, or a flipped negation); the flag is noisy, so treat it as an upper estimate |
| Valid JSON | the output can be parsed as JSON |
| Guard | deterministic repair of invalid JSON (document 07) |
| Window | one piece of a long transcript sent to the model on its own (document 05) |
| OpenVINO FP16 | Intel's runtime and the 16-bit number format used for the deployed model; no quantisation |

## 7. Limits to state to any reviewer
* Everything is synthetic. Labels are written by programs or by language models and checked automatically or by a second model. **No clinician reviewed any label.**
* The judge is one model (gpt-5.4) with one rubric; it has not been calibrated against a human (document 07).
* The very high score (0.933) is on a test set that is scenario-disjoint from training but built from the same template families. It shows the task and format are learned; it is not a measure of performance on real speech.
* The 20 hand-written natural scenarios are the more realistic check and they use clean text, not speech-recognition output.

## 8. Where things are
`finetune_slm/README.md` is the folder map. Documents: `01` (this), `02` datasets, `03` models and experiments, `04` round 1, `05` round 2, `06` round 3, `07` judge findings and the final choice. The chronological working report is `FINETUNING_TRAINING_REPORT.md` and the failure-class analysis is `MODULE3_FINETUNING_FOCUS.md`.
