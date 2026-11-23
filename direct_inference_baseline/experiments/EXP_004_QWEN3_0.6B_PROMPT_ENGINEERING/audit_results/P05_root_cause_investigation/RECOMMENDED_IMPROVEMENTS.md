# Recommended improvement strategy (proposal only; nothing implemented)

Written for: the study owner who must approve any next experiment. All items below need your approval before any code, prompt or run is created. The root-cause evidence is in `ROOT_CAUSE_ANALYSIS.md` and `ROOT_CAUSE_MATRIX.csv` (R01-R22).

## 1. Principles

1. Fix what Python can fix deterministically first: it costs no model time, is auditable, and cannot hallucinate.
2. Give the 0.6B model smaller, narrower tasks than "emit 17 sections in one pass".
3. Stop asking the model for things Python can derive from the transcript (`reported_by`, timestamps, evidence ids, kinship, category).
4. Treat each change as a separate, measured experiment on prompt_dev; report with and without it. Never tune on the consumed validation set.
5. Keep abstention. Where a validator cannot confirm a fact, flag or drop it rather than let it through.

## 2. Environment facts that shape the options (measured or read from this project)

- Installed: OpenVINO and OpenVINO GenAI 2026.4.1; the API exposes `StructuredOutputConfig` (schema or grammar-guided decoding) and `SchedulerConfig` (cache settings). Whether guided decoding works with `LLMPipeline` on the UHD 620 GPU for Qwen3-0.6B was not tested.
- Measured throughput in the P05 validation: decode about 6.5 tokens/s, prefill about 141 tokens/s, 245 s per encounter on average, 4,290 input and 1,426 output tokens on average. Decode dominates (about 220 s of the 245 s).
- Implication: shrinking the output is the cheapest speed-up, and prefill is relatively cheap, so several short prompts can cost less than one long output.

## 3. Proposed stages, in order of value per effort

### S0. Deterministic repair and validation layer on Stage-1 JSON (no model change)
Addresses R01, R05, R08, R09, R10, R11, R12, R13, R14, R16, R17. Each rule is a small, logged function:
- Wrap object into list for `clinical_assessment` and `follow_up` (recovers 20 and 14 records' content).
- Map enums and lower-case roles; log every substitution.
- Drop placeholder entries (negative finding "absent", assessment "provisional", allergy "none").
- Drop an allergy that is also a medication unless a transcript segment states an allergic reaction.
- Null datetime fields unless the transcript contains a date or time expression.
- Derive `reported_by` and `observed_by` from the role of the cited segment (in P05 the citation exists anyway).
- Flag (not repair) a negative finding that has a positive counterpart in the same record.
- Drop follow-up and action items that come from exam talk (let me / I'll / tell me if); allow follow-up only with a return-visit phrase.
Expected effect: removes most format and fabrication errors; does not fix wrong drugs, wrong doses, missing prescriptions or inverted negatives that survive the checks. Risk: a repair can hide a model error, so report with and without S0 and keep every substitution in a log. Cost: small code, no extra inference time.
Caveat: the lexicons (return-visit phrases, exam phrases) must come from general clinical language, not from reading validation items, otherwise they overfit this synthetic template.

### S1. Shrink the Stage-1 task and output (prompt and schema change; still one pass)
Addresses R21, R17, R13. Remove `evidence_ids`, `clinical_evidence`, `quality_checks`, `confidence` and empty-field boilerplate from the output (385 of 540 entity evidence lists were empty and P05 discards them anyway); remove timestamps from the input; keep plain fields verbatim and drop "normalize to medical terms" from the model task; state allergies as a section that stays empty when not discussed. Expected effect (to be measured): fewer output tokens and less schema copying. Cost: prompt rewrite; test on prompt_dev only.

### S2. Segmented extraction for the highest-risk sections (model task decomposition)
Addresses R02, R03, R04, R06, R07. Python selects the relevant transcript windows by general trigger phrases (for example a doctor question about medicines or allergies and the patient reply; doctor sentences with prescribing verbs; yes/no screening questions) and the model fills a small schema per window:
- Medications: one drug per window; dose, route and frequency only from that window; patient-stated versus doctor-prescribed as two tasks.
- Allergies: only from a window with an allergy question; "none" is never an allergy item.
- Negative findings: one question-answer window at a time; output only if the answer contains a denial cue.
- Prescription detector: every doctor sentence with a prescribing verb must yield an entry or an explicit flag (addresses 14 of 20 missed prescriptions).
Feasibility estimate (from the measured rates, not measured for this design): a window of about 150 input tokens costs about 1 s prefill and 60 output tokens cost about 9 s, so 10-20 windows per encounter would take roughly 100-200 s, comparable to today's 245 s and with far smaller outputs. Prefix or cache reuse could help but is untested.
Risk: windowing rules tuned to templated synthetic dialogue may not generalise; keep rules generic and test on held-out data.

### S3. Constrained decoding (only after S1)
Use `StructuredOutputConfig` with a JSON schema so lists stay lists, enums stay valid and extra keys are impossible. This does not make facts true; it removes R12 and R13 structurally. Needs a quick compatibility test (GPU, Qwen3-0.6B, speed overhead) before any commitment.

### S4. Retrieval improvements (Stage 2 only; needs a new frozen version)
Addresses R18, R19, R20: split doctor turns into sentences before pairing a question with its answer; prefer the earliest patient statement when equal matches tie for symptoms; add a curated lay-medical term map (hypertension and high blood pressure) built from a general terminology source, not from validation items; anchor mis-sectioned items by cross-field matching; require context gates (allergy question present, return-visit phrase present). Re-measure coverage and the false-citation rate on prompt_dev.

### S5. Not recommended now
- A second LLM pass that "checks" the first with the same 0.6B model: low reliability, doubles decode time.
- Fine-tuning or a larger model: out of the stated scope; revisit only if S0-S4 plateau. A larger model (for example a 1.7B in INT4) is a separate capacity-versus-memory question for this iGPU.
- Raising `max_new_tokens`: outputs were not truncated.

## 4. Suggested order and decision gates

| Step | Change | Proof it works | Stop condition |
|---|---|---|---|
| 1 | S0 layer, applied to the stored P02 outputs (no inference) | Error counts of R01, R05, R08-R13 on prompt_dev and the audit items; log of substitutions | If a repair removes true facts, narrow the rule |
| 2 | S1 on prompt_dev (50 records, about 3 h) | Output tokens, shape errors, placeholder rate, strict extraction F1 versus P02 on the same ids | No gain, revert |
| 3 | S2 for medications and allergies only | Missed prescriptions, dose errors, allergy placeholders | Slower than 250 s per encounter or no gain |
| 4 | S3 | Format errors reach zero | Speed or compatibility problem |
| 5 | S4 | Coverage and false-citation rate | Abstention misses not reduced |

## 5. Measurement hygiene (a decision for you)

- The validation set (50 ids) is consumed for development decisions: it was read for this investigation and for the audit. Use prompt_dev for the changes above, and treat any new validation as exploratory.
- A fresh confirmatory set is needed before any claim. The only unused records are the 400 locked-test records, which must not be used for development. Options: (a) keep the lock and accept that later claims are only development-level; (b) ask whoever owns the dataset for additional unseen encounters; (c) explicitly decide to spend a small, pre-registered part of the locked test later. I recommend (b) or (a) until you decide.
- Define the new primary measures before any run: missed-prescription rate, medication-in-allergy rate, polarity-inversion rate, fabricated-datetime rate, `reported_by` agreement with the citing segment role, container-shape error rate, abstention-miss rate.

## 6. Open questions for you

1. Approve S0 first (no inference, run on stored outputs and prompt_dev only)?
2. Should `reported_by` be re-defined as "who said the cited segment" for negatives and vitals?
3. Which option for a fresh confirmatory set (section 5)?

No code, prompt, model run or frozen artifact has been changed. This is not a clinical validation of any approach.
