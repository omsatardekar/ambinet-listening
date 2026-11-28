# Fine-tuning Qwen3-0.6B for clinical extraction: what we did and why

Status: training run 1 is finished (654 steps). Checkpoint selection, the baseline comparison and the locked test run are still to do (section 11 lists what is measured and what is not).

## 1. Goal
The Module 3 extractor reads a consultation transcript and writes a structured JSON (symptoms, negatives, medicines, allergies, vitals, examination, assessment, plan, follow-up, uncertainties, and so on). With the base Qwen3-0.6B and only a long prompt, the model missed items, invented items and broke rules (failure classes F1 to F32 in `docs/MODULE3_FINETUNING_FOCUS.md`; baseline item F1 0.352 and invented-item rate 0.262 on 30 encounters). Fine-tuning teaches the model the task directly, so the prompt can be short and the behaviour (use only what is said, leave empty things empty, flag real doubts) is learned and not only requested.

## 2. The data we built
| Batch | Encounters | How it was made |
|---|---|---|
| 1 | 500 | template generator; its README says evaluation use only |
| 2 | 500 | template generator, second profile set |
| 3 | 500 | 107 hand-authored encounters plus 393 drafts from a colleague, validated and compiled |
| 4, 5, 6, 7, 8 | 500 each (2,500) | template generator with new scenario profiles: best, middle and worst cases side by side, different specialties |
| 9 | 200 | deliberately non-obvious cases (atypical presentations, mimics, medicine-induced problems, quiet red flags) |
| **Total** | **4,200** | every encounter has a transcript and a full structured label |

Labels were validated automatically (evidence text exists in the cited turns, enums, speaker attribution, duplicates against earlier batches). **They were not reviewed by a clinician.** Batches 1, 2 and 4 to 9 use template dialogue; only Batch 3 is human-written.

## 3. What the model sees and writes (and why we changed it)
| | First idea | What we trained |
|---|---|---|
| Prompt | the frozen H1 prompt, 2,359 tokens | a short prompt, **313 tokens** (`dataset_v2/prompt/short_prompt.txt`) |
| Transcript line | `[SEG0001] person_1 (DOCTOR) 0.70-5.72s: text` | `[SEG0001] person_1 (DOCTOR): text` |
| Model output | the full JSON with every key | a **compact JSON** (fields that are empty, `null` or `[]`, are left out; at most two evidence ids; `clinical_evidence` omitted) |
| Project receives | full JSON | full JSON: `expand()` restores every key in the original order, so nothing changes for the project |

Why:
* **Time and cost.** The T4 GPU is the only one we can get, and it is slow (about 500 tokens per second). Every token costs training time and money, so we cut tokens that carry no clinical information.
* **Timestamps removed.** The start and end seconds on each line carry no clinical meaning (the labels cite segment ids, not times). Removing them saved **692 tokens per example (18%)**. Median example length went from about 3,800 to **3,115 tokens** (maximum 5,412). The original timestamps stay in the pipeline and the frontend; only the text given to the model omits them, so at deployment the scoring file must format lines exactly as in training.
* **Short prompt.** The rules the model needs are now learned from 2,856 examples, so only a compact reminder is needed.
* **Compact output is lossless.** `expand(compact(label)) == label` was verified on all 4,200 labels (`codec/roundtrip_report.json`). The model writes fewer tokens (median answer about 1,600 tokens) and the full structure is restored afterwards.

## 4. The split (train, validation, test)
| Split | Encounters | Purpose |
|---|---|---|
| **Train** | 2,856 (3,484 lines with rare cases repeated once) | the model learns from these |
| **Validation** | 250: **190 seen** + **60 unseen** | pick the checkpoint and decide when to stop; never trained on |
| **Test A (benchmark)** | 500 = all of Batch 1 | final score; same set as every earlier experiment, so before-and-after is fair |
| **Test B (curated)** | 473 | final score on new, harder, more natural cases |
| Reserve | 121 | unused; leftovers of held-out scenario groups, kept out of training to avoid leaks |
| **Total** | **4,200** | |

Why these splits, in plain words:
* **Train / validation / test.** Train is what the model learns from. Validation is used during training to see whether the model really learns or just memorises, and to choose a checkpoint. Test is a final exam used **once**, at the end, so the reported number is honest.
* **Not a random split.** Many encounters come from the same clinical scenario with different patient names and wording. A random split would put near-twins in train and test and inflate the score. We hold out **whole scenario groups**. Measured word 5-gram overlap of test with training: median 0.06, maximum 0.115 (Test B).
* **Seen versus unseen validation.** *Seen* = new encounters from scenario groups that are in training (checks normal learning). *Unseen* = encounters from scenario groups completely held out of training (checks whether the model generalises, which is what we really care about). The gap between the two curves is the overfitting signal.
* **Test B is chosen, not random:** harder cases (more uncertainties, more speakers, unidentified voices), the 102 non-obvious Batch 9 cases, worst, middle and best cases from every specialty, and the 60 hand-written Batch 3 conversations. Uncertainty is present in 48% of Test B against 35% of training.
* **Lock.** `test/TEST_LOCK.json` stores the test ids and SHA-256 hashes (re-hashed on 2026-11-22 after the timestamp change). No test id is in train or validation.
* **Rare cases repeated once** in training (628 extra lines): no vitals 236, no social history 208, unnamed medicine 97, disputed allergy 94, unidentified speaker 90, no negative findings 75, conflicting statement 68, no history at all 49. Reason: the model must learn to leave sections empty and to flag real doubts, and these cases are rare.

## 5. Method: LoRA (and why not the alternatives)
* **Supervised fine-tuning (SFT):** the training example is a chat: the user turn is the short prompt plus the transcript, the assistant turn is the compact JSON. The Qwen3 chat template is used with thinking off (an empty think block is added to the assistant turn, exactly as at inference).
* **Loss on the answer only.** The prompt and transcript tokens are masked, so the model is not rewarded for copying the input. At each answer token it is asked to predict the next token and is penalised by how little probability it gave the correct one (cross-entropy). It learns the wording and style of the labels this way. Semantic matching ("morning stiffness" versus "stiffness in the morning") is not part of training; it is part of evaluation.
* **LoRA (Low-Rank Adaptation).** The 0.6B base weights are frozen. Next to each chosen weight matrix we add two small trainable matrices A and B (rank r); the layer's output becomes `W x + (alpha / r) * B A x`. Only A and B are trained. Benefits: far less memory, and the base knowledge is not overwritten (less forgetting). The result is a small adapter file that can be merged into the base model before deployment.
* **Why not full fine-tuning:** it needs gradients and optimizer states for every parameter and risks forgetting; on a 16 GB T4 it is slower and riskier. **Why not QLoRA:** it quantises the base to 4 bits to save memory; the 0.6B model already fits in 16 GB, so quantisation would only add noise and slow the T4 down. With a model this small, LoRA at a high rank gives close to full-fine-tuning quality.

## 6. Hyper-parameters used (run 1)
| Setting | Value | Note |
|---|---|---|
| Base model | Qwen3-0.6B (28 layers, hidden 1024, 16 attention heads, 8 key-value heads, MLP 3072) | frozen |
| LoRA rank r | **64** | capacity of the adapter |
| LoRA alpha | **128** (scale alpha / r = 2) | |
| LoRA dropout | 0.05 | |
| LoRA targets | q, k, v, o, gate, up, down projections in all 28 layers (196 matrices) | attention and MLP |
| Trainable parameters | **40,370,176** (about 7% of the model) | per layer: 655,360 attention + 786,432 MLP |
| Optimizer | AdamW (betas 0.9 / 0.999, weight decay 0) | |
| Learning rate | **1e-4**, 19 warm-up steps (3%), then cosine decay to 1e-5 | |
| Gradient clipping | 1.0 | |
| **Micro-batch size** | **1 example** per forward and backward pass | memory limit of the T4 with 3,000-token sequences |
| **Gradient accumulation** | **16** | gradients of 16 examples are added before one weight update |
| **Effective batch size** | **16 examples per optimizer step** (about 51,000 tokens) | one "step" in the logs |
| Steps per epoch | 218 (3,484 / 16, rounded up) | |
| **Epochs** | **3** | 3 x 218 = **654 optimizer steps** |
| Examples processed | 654 x 16 = 10,464 (3.0 passes over 3,484) | roughly 33 million tokens |
| Maximum sequence length | 5,632 tokens | longest example is 5,412; none skipped |
| Precision | base weights fp16, LoRA weights fp32, fp16 autocast with a gradient scaler | the T4 has no bf16 |
| Memory savers | gradient checkpointing, only the answer positions get logits, SDPA attention | peak GPU 8.4 GiB of about 15 |
| Validation | every 50 steps on a fixed sample of 60 (30 seen + 30 unseen) | |
| Checkpoints | every 50 steps and at the end | |
| Seed | 20261127 | |

"654 steps" and "batch size": the total is 654 updates; each update uses a batch of 16 examples, fed one at a time and accumulated. So the model saw 654 x 16 = 10,464 example-passes, which is the 3,484 training lines three times.

## 7. Hardware, speed, time, cost
* One Azure VM `vm-qwen3-finetune-t4` (resource group `GEN-AI-BATCH6-TRAINING-RG`), NVIDIA T4 (`NC4as_T4_v3`), Ubuntu 22.04, data on the OS disk (`/data/finetune`), run inside `tmux`.
* The T4 is compute-bound and power-capped; software tweaks gave no gain, so we reduced tokens instead (timestamps).
* Run 1: **1,102 minutes (18.4 hours)**, about 503 tokens per second, no skipped example, no non-finite loss. At about Rs 58 per hour the compute cost is roughly Rs 1,070.

## 8. What happened during training
* Training loss: 1.02 at step 1, 0.24 at step 20, 0.15 at step 30, and about 0.003 to 0.01 near the end. Early drops are mostly the model learning the output format.
* Validation loss (per answer token):

| Step | Seen | Unseen |
|---|---|---|
| 50 | 0.0883 | 0.0872 |
| 100 | 0.0491 | 0.0492 |
| 150 | 0.0380 | 0.0389 |
| 200 | 0.0310 | 0.0353 |
| 250 | 0.0269 | 0.0339 |
| 300 | 0.0252 | 0.0342 |
| 350 | 0.0222 | 0.0326 |
| **400** | 0.0208 | **0.0322 (lowest)** |
| 450 | 0.0214 | 0.0358 |
| 500 | 0.0206 | 0.0353 |
| 550 | 0.0210 | 0.0353 |
| 600 | 0.0208 | 0.0351 |
| 650 | 0.0211 | 0.0361 |
| 654 (final) | 0.0211 | 0.0360 |

Reading it: both curves fall together until about step 250, so the model generalises. After step 400 the unseen loss no longer improves while training loss keeps falling, which is mild overfitting. The last third of the run added nothing for new scenarios. The differences are small and are measured on only 30 unseen examples, so loss alone does not choose the checkpoint; generated output does (section 9).

## 9. Checkpoints
Saved in `/data/finetune/runs/run1/` as `checkpoint_step50`, `100`, `150`, `200`, `250`, `300`, `350`, `400`, `450`, `500`, `550`, `600`, `650` and `654` (14 adapters), plus `train_log.txt` and `state.pt` (for resuming). Each is a LoRA adapter (40 million fp32 parameters, about 160 MB).

Selection rule (validation only, never the test set): compare step 400 and step 654 (and others if close) by generating all 60 unseen-validation encounters (greedy decoding, thinking off) and scoring valid JSON, item-level F1 and the failure-class checks. If they are close, prefer step 400 (lower unseen loss, less overfitting risk). Result: **to be filled in**.

## 10. Example of what the model learned (step 100 only, one validation encounter)
Right: full structure, all 8 vital signs, both medicines with dose, frequency and route, plan items with the correct status, no invented allergy. Wrong: it did not record the denied allergy or the social history, invented a duration ("1 week" where the doctor said "long term"), put the severity on the wrong symptom, and added body sites and a test name that were not said. These are the rare and subtle behaviours that later steps are meant to fix; the same encounter will be re-run on later checkpoints as a visible before-and-after.

## 11. Measured versus not yet measured
Measured: dataset counts and split, token counts, round-trip of the compact format, training and validation loss, speed, memory, time.
Not yet measured: item-level F1 and failure-class checks of any fine-tuned checkpoint, the baseline on the same sets, the locked test result, and the deployed endpoint behaviour. Do not quote accuracy numbers for the fine-tuned model until those are run.

## 12. Known limits (say these to external reviewers)
* Synthetic data; labels are validated by program and not by clinicians. Most dialogue is template-based.
* Some labels contain normalised names not literally in the transcript (for example a named blood-test panel when the doctor only said "blood tests"); this teaches the model to guess and is being audited.
* Validation uses 60 unseen examples, so small differences are noise.
* A final check on realistic recordings (the 20 scripted test recordings) and later approved real data is separate from this split.

## 13. Next steps
1. Choose the checkpoint on validation (section 9).
2. Run the frozen-prompt baseline and the chosen checkpoint on Test A and Test B once, with the failure-class checks.
3. Merge the adapter, convert to OpenVINO FP16, build the scoring file (short prompt, same line format without timestamps, `expand()`), add it as a new deployment on the existing endpoint; the endpoint URL and key stay the same.

## 14. Where things are
* Data and split: `dataset_v2/` (`README.md`, `SPLIT_PLAN.md`, `TRAINING_AND_DEPLOYMENT_PLAN.md`, `manifest.csv`, `test/TEST_LOCK.json`).
* Training code: `finetune_scripts/train_lora.py`, `generate_check.py`, `README_RUN.md`.
* Base model: `model_qwen3_0.6b/`.
* On the VM: `/data/finetune/runs/run1/` (checkpoints and `train_log.txt`).

---

# Update after training (2026-11-23)

Sections 1 to 14 above were written when training had just finished. Everything below happened afterwards. Where it differs from the earlier text (for example section 9 "Result: to be filled in"), this part is the current state.

## 15. Training finished
* The run completed all **654 steps in 1,102 minutes (18.4 hours)** at about 503 tokens per second, with no skipped example and no non-finite loss. Final validation loss: seen 0.0211, unseen 0.0360. Lowest unseen validation loss: **0.0322 at step 400** (full table in section 8).
* The 14 checkpoints (steps 50, 100, ... 650, 654) are in `/data/finetune/runs/run1/`.

## 16. Choosing the checkpoint: generated output on the unseen validation set
Loss alone does not tell us how good the extraction is, so we compared checkpoints by what the model actually writes. The model generated an answer for each of the **60 unseen-scenario validation encounters** (greedy decoding, thinking off, up to 4,096 new tokens) with no correct answer given, and the output was scored against the correct label. The score is a rough item-level F1: each item (a symptom, medicine, vital sign and so on, identified by its section and main text) is matched against the reference. It is the same scorer for every checkpoint.

| Checkpoint | Valid JSON | Ended normally | Mean item F1 |
|---|---|---|---|
| Step 400 | 60 / 60 | 60 / 60 | 0.903 |
| Step 654 (last) | 60 / 60 | 60 / 60 | 0.908 |

Per-encounter comparison: step 654 better on 20 encounters, step 400 better on 14, equal on 26. The difference is small and not statistically meaningful with 60 examples.

**Decision.** We used the rule written down before the comparison: when two checkpoints are tied on generated output, take the one with the lower unseen validation loss and less overfitting risk. That is **step 400**. The choice was made on validation only; the test set played no part in it, and it is now fixed so that the test result stays a clean final exam.

Notes for reviewers: both checkpoints write valid, schema-expandable JSON in every case and always stop by themselves, so the output format is learned. The F1 above is a rough exact-match score against synthetic labels on validation data. It must **not** be compared with the earlier baseline figure of 0.352, which came from a different scorer (an LLM judge on 30 encounters). The fair comparison is the baseline run through the same scorer on the same sets (section 20).

## 17. Evaluation tooling added
`finetune_scripts/generate_check.py` was extended with: `--split` (evaluate only one part of a file, for example `validation_unseen`), `--sort` (group encounters of similar length in a batch), and `--save` (write the transcript, the raw compact output, the expanded full JSON and the correct full label for every encounter, so later scoring does not need generation again). `finetune_scripts/generate_vllm.py` was added as an alternative generator (section 18).

## 18. Generation speed on the T4 (a finding, not a failure)
Generating is slow on this GPU: **about 50 tokens per second in total, about 40 seconds per encounter** (an answer is about 1,900 tokens).

| Test | Result |
|---|---|
| Hugging Face generate, batch 6, 60 encounters | about 40 minutes (the two result files were written 40 minutes apart); 114k new tokens, about 47 tokens per second |
| Hugging Face generate, batch 12 with length sorting, 12 encounters | 7 min 53 s, about 50 tokens per second; valid 12/12, F1 0.875 (only 12 examples) |
| vLLM (paged attention, LoRA), 6 encounters | 231 s, **50 tokens per second**; valid 6/6, ended normally 6/6, F1 0.841 (only 6 examples, not comparable) |
| vLLM, 24 encounters at once (probe) | after 4 min 44 s only 2 of 24 were finished, estimated 44 more minutes, about 2 minutes per encounter. This is **slower** per encounter than with 6, so the probe was stopped |

Diagnosis. The GPU was checked while generating: SM clock 1,560 MHz against a 1,590 MHz maximum, power 66 W against the 70 W limit (the "software power cap" flag is normal for a T4 under load), 71 degrees C with no thermal slowdown, no other process on the GPU, and the 4-core CPU 97% idle. So the GPU is working at full speed and nothing is misconfigured. Two different engines give the same 50 tokens per second, and more concurrent sequences make it slower, not faster. Our best explanation (not proven) is that, with transcripts of about 3,000 tokens, the cost is dominated by the attention cache, which grows with sequences times context length. Faster hardware (A10, A100) would fix this, but is not available to us.

Consequence: one pass of the locked test set (973 encounters) takes about **11 hours** per model. We accept this and run it in the background, because the GPU is only needed for generation. The scorer and the deployment package are built in the meantime. Because every raw output is saved, the final scorer can be improved without generating again.

Operational lesson: stopping a vLLM script with `pkill` left its engine process alive, holding 13.4 GB of GPU memory, and the next job failed with "CUDA out of memory". The leftover process had to be killed by its process id. Long jobs must also be started inside `tmux`, never directly in the SSH window.

## 19. The locked test run (started 2026-11-23)
* Command: `generate_check.py --adapter runs/run1/checkpoint_step400 --data dataset_v2/test/test.jsonl --n 973 --batch 6 --sort --save runs/test_step400_outputs`, output log `runs/test_step400.log`, run inside `tmux` session `test`.
* Data: the 973 locked test encounters (Test A: 500 from Batch 1; Test B: 473 curated). Checkpoint: step 400 (section 16). This is the single, final test run for the fine-tuned model; no setting is changed after seeing its result.
* Expected duration: about 11 hours. Progress is read from the number of finished records in the log. Status when this section was written: running.

## 20. What is still to do
1. Write the **final scorer** with the failure-class checks (section 4 of `TRAINING_AND_DEPLOYMENT_PLAN.md`: invented allergy, invented vital sign or assessment, symptom also listed as negative, medicine values not in the transcript, stopped medicine recorded as current, unrecorded conflict, and so on), and score the saved test outputs.
2. Run the **baseline** (same base model, no fine-tuning, frozen H1 prompt) through the same scorer on the same test encounters, so that baseline and fine-tuned are compared like for like. Because the baseline prompt is long and its answers are longer, it will take longer than the fine-tuned run; a representative subset (for example the 30 EXP_008 encounters and a stratified sample of Test B) may be used, and this must be stated in the report.
3. **Deployment:** merge the step 400 adapter into the base model, convert to OpenVINO FP16, build a single scoring file that builds the short prompt with the transcript lines in the trained format (no timestamps), runs the model, calls `expand()` and returns the full JSON, and add it as a new deployment on the existing endpoint. A test must confirm that the scoring file's prompt is identical to the dataset's prompt, byte for byte. The endpoint URL and key stay the same.

## 21. Measured and not yet measured (current)
Measured: everything in section 11, plus generated-output validity and rough F1 of steps 400 and 654 on the 60 unseen validation encounters, and generation speed on the T4.
Not yet measured: the test-set result of the fine-tuned model, the baseline on the same scorer, the failure-class check counts, and the deployed endpoint behaviour. Do not quote accuracy numbers for the test set until section 19 has finished and section 20 is done.

---

# Results on the locked test set (added 2026-11-24)

Sections 19 to 21 above were written while the test run was in progress. This part holds the results; where it differs, this part is current.

## 22. How the test outputs were scored
* **Generation:** the step 400 checkpoint generated an answer for each of the **973 locked test encounters** (Test A: 500, Test B: 473), greedy decoding, thinking off. Every output was saved.
* **Scorer:** the project's existing judge evaluation (`judge_eval/`, described in `judge_eval/METHODOLOGY.md`), unchanged: the model output and the reference label are broken into atomic facts, and a judge model (gpt-5.4 in Azure AI Foundry) with frozen prompts decides (a) whether each fact the model wrote is supported by the transcript (precision, hallucination, critical errors) and (b) whether each reference fact was captured (recall). The new driver is `judge_eval/ft_judge.py` (it reuses the same prompts and metric code; transcripts and labels come from `dataset_v2/test/raw_inputs` and `raw_labels`, verified identical to the files the earlier runs used). All judge results are in `judge_eval/results/JUDGE/ft_step400_test/`; the full tables are in `judge_eval/output/ft_ft_step400_test.md` and `.json`.
* **Invalid outputs** (the model wrote broken JSON) are judged with **zero predictions**, so all their reference facts count as missed. Nothing is dropped.
* "Judge-F1" is agreement under one judge model's reading of one rubric. It is not clinical accuracy, and the labels are synthetic and not clinician reviewed.

## 23. Before and after (the same 30 encounters, the same judge, the same rubric)
The frozen-prompt baseline (EXP_008 H1: base Qwen3-0.6B with the long prompt) exists only for 30 encounters, which are inside Test A. These are the only encounters with a direct before and after.

| | Before: frozen H1 prompt, base model | After: fine-tuned, step 400, short prompt |
|---|---|---|
| Judge-F1 (lenient) | 0.352 [0.313, 0.390] | **0.939** [0.927, 0.951] |
| Judge-F1 (strict) | 0.239 [0.200, 0.277] | **0.903** [0.886, 0.920] |
| Precision | 0.568 | 0.956 |
| Recall | 0.255 | 0.923 |
| Hallucination rate (facts not supported or contradicted) | 0.262 | **0.014** |
| Critical-error rate (dangerous errors such as a wrong medicine, dose, allergy, or a flipped negation) | 0.120 | **0.005** |
| Valid JSON | 30 / 30 | 30 / 30 |

Brackets are 95% bootstrap confidence intervals over the 30 encounters. Prompt length also fell from 2,359 to 313 tokens.

## 24. The fine-tuned model on the whole locked test set
| Subset | Encounters | Precision | Recall | Judge-F1 (lenient) | Judge-F1 (strict) | Hallucination | Critical | Valid JSON as generated |
|---|---|---|---|---|---|---|---|---|
| Test A (Batch 1 benchmark) | 500 | 0.949 | 0.917 | 0.933 | 0.898 | 0.022 | 0.007 | 495 / 500 |
| Test B (curated) | 473 | 0.939 | 0.925 | 0.932 | 0.896 | 0.026 | 0.009 | 472 / 473 |
| **All** | **973** | **0.945** | **0.921** | **0.933** | **0.897** | **0.024** | **0.008** | **967 / 973 (99.4%)** |

Test B by source batch (judge-F1 lenient, recall): batch_002 0.943 (0.935); batch_003 **0.866 (0.826)**; batch_004 0.943; batch_005 0.940; batch_006 0.939; batch_007 0.920; batch_008 0.948; batch_009 (non-obvious cases) 0.938. **Batch 3, the hand-written natural dialogue, is the lowest** (recall 0.826, hallucination 0.042).

Per section (recall / precision): vital signs 0.986 / 0.997; allergies 0.982 / 0.981; past history 0.984 / 0.985; conditions 0.982 / 1.0; follow-up 0.971 / 0.983; review of systems 0.973 / 0.981; assessment 0.964 / 0.989; negative findings 0.952 / 0.983; medications 0.945 / 0.928; social history 0.932 / 0.965; procedures and investigations 0.914 / 0.976; symptoms 0.841 / 0.872; **clinical actions 0.836 / 0.858; physical examination 0.763 / 0.892; clinical uncertainties 0.774 / 0.752** (the weakest sections).

## 25. Failures to report
* **6 invalid outputs of 973 (0.6%)**: ids 00424, 00485, 00045, 01125, 00270, 00421 (five in Test A, one in Test B). All stopped normally (none hit the token limit). Inspection of four of them: three break in the same place, after the description of a `clinical_uncertainties` item, where the model starts a new key and closes the object without writing the three remaining required fields (`...taken.","},{`); one writes the next object's fields inside the `related_entities` list. All involve encounters with a conflict or doubt between speakers. Our proposed criterion "100% valid JSON" is therefore **not met as generated** (99.4%). The planned safeguard in the scoring file is: parse, then a deterministic repair of the stray-key pattern, then one regeneration, then return `extraction_status` failed with clinician review required. The repaired rate will be reported separately from the as-generated rate.
* **Weakest content:** uncertainties (recall 0.77, precision 0.75), physical examination (recall 0.76), clinical actions (0.84) and symptoms (0.84).

## 26. How to read these numbers (limits)
* **Most test encounters come from the same template families as the training data.** The test is scenario-disjoint (no scenario group of Test B appears in training, and the measured word-overlap with training is low), but the wording style is similar, so these scores show the model has learned the task and the format very well. They do **not** by themselves show performance on real, messy speech.
* **The natural hand-written conversations score lower** (Batch 3: 0.866 against 0.93 to 0.95 for the template batches). That is the more realistic indication, and it is why the separate check on the 20 hand-written recordings (below) matters.
* **A baseline exists for only 30 encounters.** Test B and the rest of Test A have no baseline, so the claim "improvement over the baseline" rests on the 30; the other 943 only show the fine-tuned level.
* One judge model and one rubric; an agreement check with a second judge (JUDGE2) has not been run on these.
* Labels are synthetic and not reviewed by clinicians.

## 27. Realism check on the 20 hand-written scenarios (in progress)
The 20 scenarios in `scenarios/` are hand-written, natural consultations (3 to 5 speakers, hesitant and terse patients, a carer or family member speaking, deliberately partial or absent facts) never used in training. They are converted to the trained input format by `finetune_scripts/build_module3_eval.py` (the clean dialogue text, no timestamps, 3,700 to 4,450 tokens each). They have no label file; the `design` block of each `scenario.json` lists what was put in on purpose and what is absent, and is the key for judging. Limitation: this uses the clean dialogue text, not an ASR transcript of the audio, so speech recognition errors are not included. Status: generation prepared; results to be added.

## 28. Still to do
1. Realism check results (section 27).
2. The safeguard for invalid JSON in the scoring file, tested on the six failures.
3. Deployment: the merged step 400 model (saved on the VM as `/data/finetune/merged_step400`), OpenVINO FP16 conversion, the single scoring file (short prompt, trained line format, `expand()`, safeguard), a byte-for-byte prompt test, a new deployment on the existing endpoint, and the same 30 encounters run through the deployed endpoint to confirm it matches the offline result.
4. Optional: a baseline on a sample of Test B, a short-prompt ablation on the base model, and a second-judge agreement check.

## 29. Realism check results: before and after on natural speech (added 2026-11-23)
The same 20 hand-written scenarios, the same judge and the same frozen judge prompts, were run through both models. Baseline = the untouched Qwen3-0.6B with the frozen H1 hybrid prompt (EXP_008), greedy, thinking off, max_new_tokens 6144, the model writing the full structure itself. After = fine-tuned step 400 with the short prompt and the compact codec. Both models saw identical transcript text (trained line format, no timestamps).

| Natural speech, 20 encounters | Precision | Recall vs design | Hallucination | Critical | Valid JSON |
|---|---|---|---|---|---|
| Before (base model, H1 prompt) | 0.515 | 0.272 | 0.325 | 0.159 | 19 / 20 |
| **After (fine-tuned step 400)** | **0.762** | **0.558** | **0.168** | **0.048** | **20 / 20** |

Note on the baseline numbers: the one invalid baseline output (m3_11) counts as zero predicted facts and zero recall, so it lowers recall but not precision (precision is computed over the 19 valid outputs). Recall against the `design` block is a floor-style number: the design block is a short human summary, not an exhaustive label.

Differences from the original baseline run, which affect how far these numbers can be compared with the earlier 30-encounter result: the baseline here ran as PyTorch fp16 on an NVIDIA T4, not OpenVINO FP16 on an Intel GPU; the input is clean dialogue text, not ASR output; and there is no label file.

## 30. The honest summary
* **Template-style test set (973 encounters):** judge-F1 0.933 (precision 0.945, recall 0.921), hallucination 0.024.
* **On the 30 encounters with a baseline** the improvement is large (section 23).
* **On natural hand-written speech** the fine-tuned model is far better than the baseline (precision 0.52 to 0.76, hallucination 0.33 to 0.17, critical 0.16 to 0.05, recall 0.27 to 0.56) but clearly below its template-set level (precision 0.76 against 0.945, hallucination 0.17 against 0.024). The remaining errors are mostly spoken corrections (a stopped or swapped medicine recorded as current), denials recorded as findings, a relative's medicine attributed to the patient, spoken-number and unit slips, and sections invented from nothing said.
* Therefore the 0.93 figure must be quoted as the template-style result only. The next training round should add natural-style data (corrections, spoken numbers, denials, third-party medicines).

## 31. Safeguard for invalid JSON (built and tested offline, 2026-11-24)
`finetune_scripts/json_guard.py` repairs the malformed patterns seen in the six invalid outputs: a key opened and closed by the next brackets (`,"}`), a list not closed before the next key, and a quote mix-up inside a string, plus closing brackets when the output stops early. Each repair is listed and sets `needs_review`.
* **Result on the six invalid outputs of the locked test run: 6 of 6 now parse.** Applied to the 967 outputs that were already valid, it changed **none** of them.
* For four of the six, the model had skipped the three required fields of the last uncertainty items; after the repair those fields are empty (the codec fills their defaults). The repaired content has **not** been judged for accuracy; only validity is claimed.
* If a record still cannot be parsed: one regeneration with light sampling (greedy decoding would repeat the same text), then `extraction_status: failed` with clinician review required. A truncated output (token limit) is never repaired.
* The final as-generated validity (99.4%) and the validity after the guard (100% on these 973, with 6 flagged for review) are reported separately.

## 32. Deployment package and conversion check (2026-11-24)
* The merged step-400 model was converted to OpenVINO FP16 with the same recipe as the baseline (no quantisation); the same 11 files as before; `openvino_model.bin` SHA-256 `627d2b16...c84e` is pinned in the scoring file.
* `azure_ml_ft/score_single_file.py` (same submit/status/result protocol, same endpoint URL and key): builds the trained prompt (short prompt, lines `[SEG0001] person_1 (DOCTOR): text`, no timestamps), runs the model, applies the guard, `expand()`, the existing schema validator and the evidence resolver, and adds `extraction_status`, `needs_review` and `guard_notes` to the metadata. Offline self-test: prompt identical to the dataset prompt for all 973 test encounters; 967 stored outputs pass unchanged; the 6 invalid ones are repaired; garbage fails after one regeneration.
* **Real OpenVINO FP16 model on CPU, through the scoring pipeline, on the 30 baseline encounters:** 30/30 valid JSON; 22/30 outputs identical to the PyTorch text, the other 8 differ after some point in a long greedy generation (floating-point differences between runtimes) with the same number of facts (0 to 2 differing items each). Judged with the same judge: **judge-F1 (lenient) 0.940 against 0.939 for the PyTorch outputs** on the same 30 (precision 0.957, recall 0.924, hallucination 0.014, critical 0.005). The conversion does not change accuracy at this level of measurement.
* Speed on the laptop CPU (not the Azure VM): median 351 s per encounter, minimum 149 s, maximum 842 s. The Azure CPU VM speed is still unmeasured.

## 33. Round 2: natural-speech data, training and result (added 2026-11-24)
**Data.** 529 new consultations were written by a second model (grok-4.7) from 2,000+ blueprint combinations designed to be unlike the round-1 templates (hesitant, interrupted, partial, family members speaking). Every label was checked by a different model (gpt-5.4: frozen precision prompt plus an omission check); a rejected label got one repair round and a re-check. 304 were accepted (263 for training, 41 in four held-out families that are never trained on); 225 were rejected or unchecked. The labels are model-written and model-verified, **not clinician-reviewed**. Training file: 263 natural + 600 replayed round-1 examples; after dropping examples longer than the 6,144-token training limit (a memory limit of the T4), 826 examples were used.
**Training.** Continued from the step-400 adapter, lr 5e-5, 156 optimizer steps (about 5.3 h). The first attempt ran out of GPU memory at step 25 (fragmentation after the validation pass); it was resumed from the step-25 checkpoint with `expandable_segments` and `--max_len 6144`.
**Validation loss (fixed validation set):**
| step | seen | unseen | held-out natural |
|---|---|---|---|
| 25 | 0.0254 | 0.0350 | 0.3661 |
| 50 | 0.0247 | 0.0351 | 0.3421 |
| 100 | 0.0236 | 0.0354 | 0.3275 |
| 125 | 0.0248 | 0.0379 | 0.3297 |
| 150 | 0.0242 | 0.0370 | 0.3270 |
| 156 | 0.0243 | 0.0371 | 0.3266 |
The loss fell on the held-out natural families and did not rise on round-1 data, so by loss alone round 2 looked successful.
**Generation on the 20 hand-written scenarios (greedy, 4,096 new tokens), judged with the same judge and prompts as before:** the loss did not predict the real behaviour. Many outputs never finished: the model repeated one list item until the token limit (valid JSON: step 100 6/20, step 156 11/20; step 400 20/20). Scores when invalid outputs count as empty: step 100 precision 0.722 / recall 0.207; step 156 0.729 / 0.345.
**With the extended JSON guard (section 34), all 20 outputs of both checkpoints become valid:**
| model | precision | recall vs design | hallucination | critical |
|---|---|---|---|---|
| base + H1 prompt | 0.515 | 0.272 | 0.325 | 0.159 |
| round 1, step 400 | **0.762** | 0.558 | **0.168** | **0.048** |
| round 2, step 100 + guard | 0.703 | 0.524 | 0.206 | 0.079 |
| round 2, step 156 + guard | 0.717 | **0.580** | 0.205 | 0.071 |
**Conclusion.** Round 2 does not beat step 400. Recall is slightly higher for step 156 (+0.02, within the noise of 20 scenarios), but precision is lower (-0.045), hallucination and critical-error rates are higher, and 9 of 20 outputs needed a repetition repair. The step-400 model remains the best candidate. The cause of the loops is not proven; the likely contributors are the longer outputs (the natural labels are about 60% longer than round-1 labels: mean 9.9k vs 6.2k characters) and greedy decoding. The labels were checked for repeated list items and the cause is not simple duplication in the data. Caveats: 20 scenarios, one judge, labels of the natural data are model-written.

## 34. JSON guard extended (2026-11-24)
Two rules were added to `finetune_scripts/json_guard.py`, learned from the round-2 outputs: R7 (a key written as the value of the previous key, e.g. `"duration":"reported_by":"patient"`; the empty field stays absent) and R6 (repetition loop: exact copies of an earlier flat item are removed, the unfinished tail is cut, open brackets are closed; the other rules are then applied again). A bug was also fixed: an error at the very end of the text raised an exception instead of being handled. Checks: 987 outputs that were already valid (973 test + 20 scenarios minus invalid ones, step 400) are returned unchanged (0 altered); all 20 round-2 outputs of both checkpoints now parse. Limitation: R6 removes identical items anywhere in the output, so a genuine repeat in another section would also be dropped, and the content after the loop point is lost (the output stops at the loop). Repaired records are flagged for review.

## 35. Windowed extraction and round 3 (added 2026-11-25)
**Why windows.** The 20 hand-written scenarios have 3,700-4,450 input tokens; the natural training examples are about 2,000 tokens, and training examples longer than 6,144 tokens (prompt + answer) were skipped because of T4 memory (about 40 natural examples). Real consultations can be longer still. `finetune_scripts/chunking.py` cuts a transcript into windows of at most 7,000 characters (about 1,800 tokens) with 4 shared segments, sends each window with local ids SEG0001.. (the trained format) and merges the results: list items identical apart from evidence ids are united (this also removes overlap repeats), `related_entities` pointers are renumbered, evidence ids are mapped back to the original segment ids. Test: merging a full output with a copy of itself returns it unchanged. The 20 scenarios give 44 windows.
**Results on the 20 scenarios (same judge and frozen prompts; recall is against the short `design` list, so it is a floor):**
| model | input | valid | precision | recall | halluc. | critical | facts/scenario |
|---|---|---|---|---|---|---|---|
| base + H1 prompt | full | 19/20 | 0.515 | 0.272 | 0.325 | 0.159 | |
| round 1, step 400 | full | 20/20 | 0.762 | 0.558 | 0.168 | 0.048 | 30 |
| round 1, step 400 | windows | 20/20 | 0.730 | 0.562 | 0.206 | 0.050 | |
| round 2, step 156 | windows | 20/20 | 0.710 | 0.675 | 0.213 | 0.054 | 52 |
| round 3, step 20 | windows | 20/20 | 0.683 | 0.681 | 0.234 | 0.059 | 52 |
| round 3, step 50 | windows | 41/44 windows valid* | 0.664 | 0.640 | 0.255 | 0.060 | 51 |
*3 of 44 windows could not be repaired by the guard; those scenarios were merged from their other windows.
Paired comparison, round 2 step 156 on windows against step 400 on full text: recall +0.112 (better in 15 of 20 scenarios, worse in 3); precision -0.038 (better in 7, worse in 13). Windowing alone costs step 400 about 0.03 precision, so most of the precision gap to step 400 comes from windowing (a window does not see the rest of the visit), not from the model.
**Round 3** (continued from the round-2 step-156 adapter, lr 2e-5, 2 epochs, 50 steps, 104 minutes; data: 112 natural labels that pass a stricter check (at most 1 unsupported fact, no critical omission) + 300 replayed round-1 examples). Pre-set bar: precision >= 0.74 and recall >= 0.65 on windows. **Not met**: precision fell (0.683, 0.664) and hallucination rose. The cleaner labels did not improve precision; the round-1 validation loss also drifted up slightly (seen 0.0243 -> 0.0259, unseen 0.0371 -> 0.0391). Round 3 is not used.
**Conclusion.** Training on natural-speech data raises recall on natural consultations (+0.11) and makes the output more complete (52 vs 30 facts), at the price of lower precision (-0.04 with windows, hallucination 0.168 -> 0.213 against step 400 on full text) and the loss of the loop-free behaviour on long inputs, which windowing and the guard repair. Critical-error rates are similar (0.048 vs 0.054). Combined precision/recall figure (harmonic mean): step 400 full text 0.644, round 2 step 156 windows 0.692. Caveats: 20 scenarios, one judge, recall against a short design list, natural-data labels model-written and not clinician reviewed, one training run per round. The choice between the two models is a trade-off (completeness vs unsupported facts), not a clear win.

## 36. Folder layout (2026-11-25)
All fine-tuning material was moved (not copied, nothing deleted) into `finetune_slm/` (data, models and adapters, scripts that go to the GPU VM, local scripts, runs and results per round, the judge evaluation, the two deployable models with their scoring files, the earlier experiments including the Qwen3-1.7B track, the documents, an archive of superseded duplicates). The map is `finetune_slm/README.md` and the list of old and new paths is `finetune_slm/docs/FOLDER_MOVES.md`. Paths named in sections 1 to 35 are the paths at the time of writing. After the move the scripts were re-run on their stored inputs and gave identical output (module 3 inputs, windows, the round-2 training file, the merged window outputs), the offline self-test of the scoring file passes (967 valid outputs unchanged, 6 repaired), the 11 judge tests and the 43 `clinical_extraction` tests pass, and the app's OpenVINO environment (now under `finetune_slm/experiments/qwen3_0.6b_baseline/EXP_002_QWEN3_0.6B_GPU_DIRECT/`) still imports OpenVINO.
Real OpenVINO FP16 model (round 2, step 156) on the laptop CPU through the full scoring pipeline with windows, 4 long scenarios: 4 of 4 valid (status ok; one of them flagged for review by the schema validation), 2 or 3 windows each, 413 to 631 seconds per consultation (laptop CPU, not the Azure VM).

## 37. Folder names shortened (2026-11-26)
To keep every path under the Windows limit, `finetune_slm/experiments/qwen3_0.6b_baseline/` became `finetune_slm/experiments/qwen3_0.6b/` and its `earlier_experiments/` became `earlier/`. Older sections of this report (for example section 36) use the previous names. Details in `FOLDER_MOVES.md`.

## 38. Two more backend flags and a live test (2026-11-26)
After the encounter 58 live run, `postprocess.py` got a flag for a reason for visit written as a spoken remark and a flag for a medicine name that is close to, but not, a known drug (nothing rewritten). Details and depo wording: `11_LIVE_TESTS_AND_DEPO_WORDING.md`. 78 backend and SOAP tests pass.

## 39. Three safety checks on cited passages (2026-11-26)
New `clinical_extraction/safety_checks.py` (allergy denied in its own passage, allergy vs medicine of the same family, vital sign not in its passage), warnings only. Described in `11_LIVE_TESTS_AND_DEPO_WORDING.md`. 83 backend and SOAP tests pass.

## 40. Round 4: targeted dataset, not used (2026-11-27)
Built a targeted synthetic dataset from the live-test mistakes of step 400 (480 planned, 250 targeted examples survived the model verifier, the automatic rules and the length limit; 350 round-1 examples replayed) and trained 114 steps from step 400 (lr 3e-5, 3 epochs, 218 minutes). Validation loss fell (unseen 0.056 to 0.036, natural 0.344 to 0.258). Generation: only 10 of 20 whole-conversation outputs ended normally (step 400: 20 of 20); on windows step 114 ended 42 of 44. Judged on windows: precision 0.691, recall 0.651, hallucination 0.237, critical 0.070, against step 400 0.730 / 0.562 / 0.206 / 0.050. The pre-set bar was not met. **Step 400 stays deployed.** Details: `07_TRAINING_ROUND4.md`; data: `finetune_slm/data/round4_targeted/`. Documents 07 and 08 of the index were renumbered to 08 and 09.

## 41. Round 5: cleaned mixed data from the base model, not used (2026-11-28)
Trained once from the base model on 2,668 lines (1,900 round-1 + 384 natural examples of rounds 2 and 4, each twice, with the facts the verifier marked unsupported, partial or contradicted removed: 423 of 13,660 facts) for 220 steps (420 minutes, lr 1e-4). Validation loss was still falling at the end (seen 0.0434, unseen 0.0431, natural 0.2417). Generation: 9 of 20 whole-conversation outputs and 28 of 44 windows ended normally; the guard repaired all the others. Judge on windows: precision 0.639, recall 0.621, hallucination 0.288, critical 0.080, against step 400 0.730 / 0.562 / 0.206 / 0.050. A paired bootstrap over the 20 scenarios put the differences outside the scenario noise for round 5 and for round 4 precision and recall (this corrects the "within noise" remark of document 07). The unfinished outputs end inside the counselling list; natural labels have up to 13 counselling items against at most 4 in round 1 (likely cause, not proven). **Step 400 stays deployed.** Details: `08_TRAINING_ROUND5.md`. The judge and live-test documents are now 09 and 10.

## 42. Round 6: counselling lists capped at 4, continued from round-5 step 220, not used (2026-11-28)
50 steps (128 minutes, lr 3e-5) on 984 lines (384 natural examples with counselling lists capped at 4, 101 examples changed, 176 items removed, plus 600 round-1). Validation loss natural 0.2365 (0.2417 before). Windows: 32 of 44 ended normally (round 5: 28), one unrepairable; judge precision 0.621, recall 0.614, hallucination 0.303, critical 0.078 against step 400 0.730 / 0.562 / 0.206 / 0.050. Bar (42 of 44 and no metric worse by more than 0.01 with a gain of 0.03) not met. Long counselling lists are not the main cause. Step 400 stays. Details: docs/09_TRAINING_ROUND6.md.
