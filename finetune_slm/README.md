# finetune_slm: Module 3 fine-tuning of Qwen3-0.6B (clinical information extraction)

Everything about training, evaluating and deploying the fine-tuned extraction model is in this folder. The application code (backend, frontend, `clinical_extraction/`) stays outside; it only reads the two things it needs from here (the H1 prompt and the OpenVINO runtime under `experiments/qwen3_0.6b/`).

**Start with the reading guide:** [`docs/00_INDEX.md`](docs/00_INDEX.md) (eleven short reports: project and Module 3, datasets, models and earlier experiments, training rounds 1 to 6, the LLM judge and the final selection, the live tests). **Chronological working report:** [`docs/FINETUNING_TRAINING_REPORT.md`](docs/FINETUNING_TRAINING_REPORT.md). **Where every file used to be:** [`docs/FOLDER_MOVES.md`](docs/FOLDER_MOVES.md).

## What was done, in one table

| Step | What | Result (20 hand-written scenarios unless noted) |
|---|---|---|
| Baseline | Qwen3-0.6B with the hand-engineered H1 prompt (no training) | precision 0.515, recall 0.272, hallucination 0.325, critical 0.159 |
| Round 1 | LoRA on 2,856 synthetic encounters, short prompt, compact output; checkpoint step 400 | 973-encounter locked test: judge F1 0.933. 20 scenarios: precision 0.762, recall 0.558, hallucination 0.168, critical 0.048 |
| Round 2 | continued from step 400 on 263 natural-speech encounters + 600 replayed; checkpoint step 156 | needs the guard and windows; on windows: precision 0.710, recall 0.675, hallucination 0.213, critical 0.054 |
| Round 3 | cleaner labels (112) from step 156 | precision fell (0.683 / 0.664): **not used** |
| Round 4 | targeted synthetic data from the live-test mistakes (250 + 350 replay) from step 400; checkpoint step 114 | on windows: precision 0.691, recall 0.651, hallucination 0.237, critical 0.070; on full text only 10 of 20 outputs finished: **not used, step 400 stays** (`docs/07_TRAINING_ROUND4.md`) |
| Round 6 | round-5 step 220 + 50 steps with counselling lists capped at 4; on windows: precision 0.621, recall 0.614, hallucination 0.303, critical 0.078; 12 of 44 windows did not finish: **not used, step 400 stays** (`docs/09_TRAINING_ROUND6.md`) |
| Round 5 | cleaned natural + round-1 data (2,668 lines) trained once from the base model, 220 steps; on windows: precision 0.639, recall 0.621, hallucination 0.288, critical 0.080; 16 of 44 windows did not finish: **not used, step 400 stays** (`docs/08_TRAINING_ROUND5.md`) |

Honest reading: round 2 gives a more complete record (about 52 facts per consultation against 30) at the price of lower precision. Round 1 (step 400) is the more precise model. Both are packaged for deployment; **step 400 is the recommended and deployed one** (see `docs/10_LLM_JUDGE_AND_FINAL_SELECTION.md`, sections 4 and 5). Limits: 20 scenarios, one judge model, labels of the training data are model-written (not clinician reviewed), recall is measured against a short list of designed facts (a floor).

## Folder map

```
finetune_slm/
  data/
    round1_synthetic/        the training data of round 1: train / validation / locked test (973), the short prompt, the codec (compact <-> full JSON), the schema
    round2_natural/          the natural-speech data written by a second model and checked by a third: raw/ (all 529), run2/ and run3/ (training and validation files), pilot/
    module3_eval_inputs/     the 20 hand-written scenarios turned into model inputs (module3_recordings.jsonl), and cut into windows (module3_windows*.jsonl)
  models/                    (large, not in Git)
    base_qwen3_0.6b/         the base model
    adapters/                the trained LoRA checkpoints: round1_step400, round2_step100/156, round3_step20/50
    merged_hf/               adapter merged into the base model (Hugging Face format): round1_step400, round2_step156
  scripts/
    to_gpu_vm/               the scripts copied TO the GPU VM: train_lora.py, generate_check.py, generate_vllm.py, merge_adapter.py, generate_baseline_h1.py (+ README_RUN.md)
    local/                   run on the laptop: natural_gen/ (write + verify + build round-2 data), build_module3_eval.py, build_window_eval.py, merge_window_outputs.py
    shared/                  json_guard.py (repairs invalid model JSON), chunking.py (windows for long consultations); both are also packed into the deployed scoring file
  runs/                      what came BACK from the GPU VM and the local test results, one folder per round
    baseline_h1/ round1_step400/ round2_natural_and_windows/ round3_strict_labels/ natural_data_generation/
  evaluation/judge_eval/     the LLM-as-judge (precision and recall passes), its prompts, cache, results and the per-run markdown reports in output/
  deployment/
    step400_round1/          model_files/ (the 11 OpenVINO files) + score_single_file_step400.py
    step156_round2/          model_files/ (the 11 OpenVINO files) + score_single_file_step156.py
    source/                  score.py, the builder of the single scoring file, the offline self-test, local tests of the real OpenVINO model
    h1_baseline/             the previous (H1) hosting package, kept for rollback
  direct_inference_baseline/ the inference / configuration / evaluation code of the H1 pipeline; the app imports it (its workers add finetune_slm/ to the import path)
  experiments/
    qwen3_0.6b/     EXP_008 (the H1 hybrid prompt used by the app) and EXP_002 (OpenVINO runtime and converted model used by the app) at the top level; earlier/ holds EXP_001, 003 to 007
    qwen3_1.7b_track/        the Qwen3-1.7B track (EXP_001 direct inference, EXP_002 prompting)
  docs/                      the training report, the failure-class analysis, FOLDER_MOVES.md
  archive/                   superseded and duplicate material (nothing was deleted): the first dataset, the two batch folders, zip/tar copies, transfer tarballs
```

## What goes to the GPU VM and what comes back

| To the VM (`/data/finetune`) | From the VM |
|---|---|
| `scripts/to_gpu_vm/*` | `runs/*/` outputs of `generate_check.py --save` (transcript, raw output, expanded JSON, label per encounter) and their logs |
| `data/round1_synthetic/` (`data/`, `codec/`, `test/`, `prompt/`) | trained adapters, copied to `models/adapters/` |
| `data/round2_natural/run2` (and `run3`) training and validation files | the training log (`train_log.txt`, `runs/run*.log`) |
| `data/module3_eval_inputs/module3_recordings.jsonl` and `module3_windows.jsonl` | |
| the base model (`models/base_qwen3_0.6b`) | |

## Typical commands (repository root, laptop)

```
# data
python -m finetune_slm.scripts.local.natural_gen.generate_natural --n 50 --first-id 30001 --out finetune_slm/data/round2_natural/raw --workers 6
python -m finetune_slm.scripts.local.natural_gen.verify_natural --raw finetune_slm/data/round2_natural/raw --workers 24
python -m finetune_slm.scripts.local.natural_gen.build_run2_dataset --raw finetune_slm/data/round2_natural/raw --out finetune_slm/data/round2_natural/run2 --replay 600
# windows for long consultations, then merge the model outputs and judge
python finetune_slm/scripts/local/build_window_eval.py --in finetune_slm/data/module3_eval_inputs/module3_recordings.jsonl --out finetune_slm/data/module3_eval_inputs/module3_windows.jsonl
python finetune_slm/scripts/local/merge_window_outputs.py --windows <folder from the VM> --index finetune_slm/data/module3_eval_inputs/module3_windows_index.json --out <merged folder>
python -m finetune_slm.evaluation.judge_eval.m3_judge --outputs <merged folder> --run-id <name> --data finetune_slm/data/module3_eval_inputs/module3_recordings.jsonl
# deployment package (offline self-test, no model needed)
python finetune_slm/deployment/source/build_single_file_score.py --name step156 --label "..." --weights-sha <sha256 of openvino_model.bin>
python finetune_slm/deployment/source/selftest_score.py
```

## Deploying a model to Azure ML (same endpoint, URL and key)

1. Register the 11 files of `deployment/step400_round1/model_files/` (or `step156_round2/`) as a model asset.
2. Add a deployment to the endpoint `qwen3-p02-extraction`: scoring script = `score_single_file_step400.py` (or `..._step156.py`), environment `qwen3-ov-py312-scoring:1`.
3. Test in Azure ML Studio, then move traffic. Keep the H1 deployment for rollback.
Each scoring file pins the SHA-256 of its own model and refuses to start with other weights. It cuts long consultations into windows (step 400: 14,000 characters, 10 shared segments, so the 20 test scenarios are one pass; step 156: 7,000 and 4), repairs invalid JSON, and marks repaired or partial results for clinician review.

## Not in Git

`models/` (adapters, merged and base models), the OpenVINO model files, caches and the zip/tar archives are listed in the repository `.gitignore`. The 11 model files of each deployment are the upload to Azure ML.
