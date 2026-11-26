# Fine-tuning, evaluation and deployment plan (Qwen3-0.6B on one T4)

## 1. What the training data teaches
* Task: transcript in, complete structured extraction out. Short prompt, compact output, evidence segment ids, and empty means empty.
* Coverage of the failure classes seen in live runs (`docs/MODULE3_FINETUNING_FOCUS.md`), measured in `coverage_audit.json`. In training: allergy never mentioned and none recorded 18% (508 encounters); explicit "no allergies" 46%; allergy uncertain, disputed or historical 14% (412); discontinued medicines 9% (267); medicines without a stated dose 34%; no vital signs 8% (236); no assessment stated 9% (269); no follow-up arranged 23% (648); no investigations 23% (652); an unidentified speaker 3% (90); caregiver or family speaking 28%; nurse or clinical staff speaking 30%; any recorded uncertainty 35% (conflicting statements 68, disputed allergy 94, unnamed medicine 97).
* Rare or absence cases are repeated once in `train_oversampled.jsonl` (no vital signs 236, no social history 208, unnamed medicine 97, disputed allergy 94, unidentified speaker 90, no negative findings 75, conflicting statement 68, no history at all 49). Reason: the model must learn to leave sections empty and to flag real doubts instead of filling or inventing.
* Known gaps that data alone cannot fix: a doctor's question mistaken for a fact, a person's name filed as family history, garbled free text, and wrong units. They are covered by the prompt rules and measured by the checks in section 4.

## 2. Training recipe (single T4, 16 GB)
* Method: LoRA, rank 64 (try 128 if validation stalls), alpha twice the rank, dropout 0.05, all attention and MLP projections. No quantisation.
* Precision: the T4 has no bf16. Keep the base weights in fp32 (2.4 GB) and compute in fp16 autocast with a gradient scaler; LoRA weights in fp32. Watch for NaN loss.
* Loss on assistant tokens only; maximum length 5,632 tokens; batch size 1 per step with gradient accumulation 16; gradient checkpointing on; SDPA attention.
* Learning rate 1e-4, cosine decay, 3% warm-up, up to 3 epochs on `train_oversampled.jsonl` (about 11.1 million tokens per pass; the pilot measured 455 tokens/s on the T4, so about 6.8 hours per pass; stop early when the unseen-scenario validation loss stops improving).
* Checkpoint every 100 steps and at each epoch end. Validate each epoch on `validation.jsonl` (loss on the seen and unseen parts separately) and by generating about 60 validation encounters with the checks below. Pick the checkpoint by the unseen-scenario result.
* Pilot first: 30 steps and 5 generations to confirm memory, speed, valid JSON and `expand()`.
* Run inside `tmux`; never copy a `.env` file to the VM.

## 3. Evaluation protocol (test touched once, at the end)
Generate with greedy decoding and thinking off, with at least 4,096 new tokens, then `expand()` and validate against the schema. Report on Test A, Test B and the Test B subsets, next to the baseline.

## 4. Success criteria (proposed, to be agreed before the test run)
* 100% valid JSON and schema-valid after `expand()` on both tests.
* Item-level F1 clearly above the frozen-prompt baseline on Test A (baseline judge-F1 0.352 on 30 encounters; the owner's target range is 0.60 to 0.65), with recall improved and precision not falling.
* Failure-class checks, counted per encounter and reported for baseline and fine-tuned model:
  * an allergy entry with no allergy cue in the transcript (F3, F23);
  * a vital sign, assessment or follow-up whose words or numbers do not occur in the transcript (F17, F23, F24);
  * a symptom that is also a negative finding (F1);
  * one phrase as the main text in three or more sections (F2);
  * a medication value not found in the transcript (F16, F17);
  * wrong units (F18);
  * a stopped medicine recorded as current (F6);
  * a conflict in the dialogue with no uncertainty recorded (F7, F31);
  * a self-harm or chest-pain question asked with no finding recorded (F8).
  The invented-item (hallucination) rate must fall below the baseline's 0.262.
* Absence benchmark: the share of deliberately absent categories correctly left empty (`scenarios/` design blocks).

## 5. Deployment (keeps the project unchanged)
The project calls an Azure ML endpoint (submit, status, result) hosting the model as OpenVINO FP16 on CPU. For the fine-tuned model:
1. Merge the chosen LoRA into the base weights, save in Hugging Face format, and convert to OpenVINO FP16 with the existing conversion step (the same 11 files as today).
2. Build a new single scoring file (the `azure_ml_h1` pattern) that (a) builds the **short prompt** from `prompt/short_prompt.txt`, (b) calls the model, (c) runs `codec.expand()`, and (d) returns the **full-structure JSON** exactly as now. It pins the new weights hash and prompt hash.
3. Register the 11 model files as a new asset version, add a deployment to the existing endpoint with the new scoring file, and switch traffic. The endpoint URL and key stay the same, so `.env` and the application do not change.
4. Test with `sample_request.json` and a few test encounters before switching traffic. Keep the old deployment until the new one is confirmed.
