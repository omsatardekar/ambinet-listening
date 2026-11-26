# Folder moves (2026-11-25)

Everything was moved, not copied or deleted. Old path (relative to the repository root; `..` = the folder above it) -> new path.

| old | new |
|---|---|
| `dataset_v2` | `finetune_slm/data/round1_synthetic` |
| `dataset_natural` | `finetune_slm/data/round2_natural` |
| `test_results/module3_recordings.jsonl` | `finetune_slm/data/module3_eval_inputs/module3_recordings.jsonl` |
| `test_results/module3_windows.jsonl` | `finetune_slm/data/module3_eval_inputs/module3_windows.jsonl` |
| `test_results/module3_windows_index.json` | `finetune_slm/data/module3_eval_inputs/module3_windows_index.json` |
| `model_qwen3_0.6b` | `finetune_slm/models/base_qwen3_0.6b` |
| `../backup_checkpoint_step400` | `finetune_slm/models/adapters/round1_step400` |
| `../backup_run2_step100` | `finetune_slm/models/adapters/round2_step100` |
| `../backup_run2_step156` | `finetune_slm/models/adapters/round2_step156` |
| `../backup_run3_step20` | `finetune_slm/models/adapters/round3_step20` |
| `../backup_run3_step50` | `finetune_slm/models/adapters/round3_step50` |
| `../merged_step400` | `finetune_slm/models/merged_hf/round1_step400` |
| `../merged_step156` | `finetune_slm/models/merged_hf/round2_step156` |
| `finetune_scripts/train_lora.py` | `finetune_slm/scripts/to_gpu_vm/train_lora.py` |
| `finetune_scripts/generate_check.py` | `finetune_slm/scripts/to_gpu_vm/generate_check.py` |
| `finetune_scripts/generate_vllm.py` | `finetune_slm/scripts/to_gpu_vm/generate_vllm.py` |
| `finetune_scripts/merge_adapter.py` | `finetune_slm/scripts/to_gpu_vm/merge_adapter.py` |
| `finetune_scripts/generate_baseline_h1.py` | `finetune_slm/scripts/to_gpu_vm/generate_baseline_h1.py` |
| `finetune_scripts/README_RUN.md` | `finetune_slm/scripts/to_gpu_vm/README_RUN.md` |
| `finetune_scripts/build_module3_eval.py` | `finetune_slm/scripts/local/build_module3_eval.py` |
| `finetune_scripts/build_window_eval.py` | `finetune_slm/scripts/local/build_window_eval.py` |
| `finetune_scripts/merge_window_outputs.py` | `finetune_slm/scripts/local/merge_window_outputs.py` |
| `finetune_scripts/natural_gen` | `finetune_slm/scripts/local/natural_gen` |
| `finetune_scripts/json_guard.py` | `finetune_slm/scripts/shared/json_guard.py` |
| `finetune_scripts/chunking.py` | `finetune_slm/scripts/shared/chunking.py` |
| `judge_eval` | `finetune_slm/evaluation/judge_eval` |
| `test_results/test_step400.log` | `finetune_slm/runs/round1_step400/test_step400.log` |
| `test_results/test_step400_outputs` | `finetune_slm/runs/round1_step400/test_step400_outputs` |
| `test_results/m3.log` | `finetune_slm/runs/round1_step400/m3.log` |
| `test_results/m3_outputs` | `finetune_slm/runs/round1_step400/m3_outputs` |
| `test_results/judge_all.log` | `finetune_slm/runs/round1_step400/judge_all.log` |
| `test_results/judge_all2.log` | `finetune_slm/runs/round1_step400/judge_all2.log` |
| `test_results/judge_all3.log` | `finetune_slm/runs/round1_step400/judge_all3.log` |
| `test_results/judge_all4.log` | `finetune_slm/runs/round1_step400/judge_all4.log` |
| `test_results/judge_ov30.log` | `finetune_slm/runs/round1_step400/judge_ov30.log` |
| `test_results/ov_cpu` | `finetune_slm/runs/round1_step400/ov_cpu` |
| `test_results/ov_cpu.log` | `finetune_slm/runs/round1_step400/ov_cpu.log` |
| `test_results/guard_00045.json` | `finetune_slm/runs/round1_step400/guard_00045.json` |
| `test_results/guard_00045_3_model_full.json` | `finetune_slm/runs/round1_step400/guard_00045_3_model_full.json` |
| `test_results/guard_00270.json` | `finetune_slm/runs/round1_step400/guard_00270.json` |
| `test_results/guard_00270_3_model_full.json` | `finetune_slm/runs/round1_step400/guard_00270_3_model_full.json` |
| `test_results/guard_00421.json` | `finetune_slm/runs/round1_step400/guard_00421.json` |
| `test_results/guard_00421_3_model_full.json` | `finetune_slm/runs/round1_step400/guard_00421_3_model_full.json` |
| `test_results/guard_00424_3_model_full.json` | `finetune_slm/runs/round1_step400/guard_00424_3_model_full.json` |
| `test_results/guard_00485_3_model_full.json` | `finetune_slm/runs/round1_step400/guard_00485_3_model_full.json` |
| `test_results/guard_01125_3_model_full.json` | `finetune_slm/runs/round1_step400/guard_01125_3_model_full.json` |
| `test_results/m3_baseline` | `finetune_slm/runs/baseline_h1/m3_baseline` |
| `test_results/m3_baseline.log` | `finetune_slm/runs/baseline_h1/m3_baseline.log` |
| `test_results/m3_run2_step100` | `finetune_slm/runs/round2_natural_and_windows/m3_run2_step100` |
| `test_results/m3_run2_step100.log` | `finetune_slm/runs/round2_natural_and_windows/m3_run2_step100.log` |
| `test_results/m3_run2_step100_guard` | `finetune_slm/runs/round2_natural_and_windows/m3_run2_step100_guard` |
| `test_results/m3_run2_step156` | `finetune_slm/runs/round2_natural_and_windows/m3_run2_step156` |
| `test_results/m3_run2_step156.log` | `finetune_slm/runs/round2_natural_and_windows/m3_run2_step156.log` |
| `test_results/m3_run2_step156_guard` | `finetune_slm/runs/round2_natural_and_windows/m3_run2_step156_guard` |
| `test_results/judge_r2_100.log` | `finetune_slm/runs/round2_natural_and_windows/judge_r2_100.log` |
| `test_results/judge_r2_100g.log` | `finetune_slm/runs/round2_natural_and_windows/judge_r2_100g.log` |
| `test_results/judge_r2_156.log` | `finetune_slm/runs/round2_natural_and_windows/judge_r2_156.log` |
| `test_results/judge_r2_156g.log` | `finetune_slm/runs/round2_natural_and_windows/judge_r2_156g.log` |
| `test_results/m3_win_step156` | `finetune_slm/runs/round2_natural_and_windows/m3_win_step156` |
| `test_results/m3_win_step156_merged` | `finetune_slm/runs/round2_natural_and_windows/m3_win_step156_merged` |
| `test_results/m3_win_step400` | `finetune_slm/runs/round2_natural_and_windows/m3_win_step400` |
| `test_results/m3_win_step400_merged` | `finetune_slm/runs/round2_natural_and_windows/m3_win_step400_merged` |
| `test_results/judge_win_156.log` | `finetune_slm/runs/round2_natural_and_windows/judge_win_156.log` |
| `test_results/judge_win_400.log` | `finetune_slm/runs/round2_natural_and_windows/judge_win_400.log` |
| `test_results/ov_cpu_m3` | `finetune_slm/runs/round2_natural_and_windows/ov_cpu_m3` |
| `test_results/ov_cpu_m3.log` | `finetune_slm/runs/round2_natural_and_windows/ov_cpu_m3.log` |
| `test_results/m3_win_r3_step20` | `finetune_slm/runs/round3_strict_labels/m3_win_r3_step20` |
| `test_results/m3_win_r3_step20_merged` | `finetune_slm/runs/round3_strict_labels/m3_win_r3_step20_merged` |
| `test_results/m3_win_r3_step50` | `finetune_slm/runs/round3_strict_labels/m3_win_r3_step50` |
| `test_results/m3_win_r3_step50_merged` | `finetune_slm/runs/round3_strict_labels/m3_win_r3_step50_merged` |
| `test_results/judge_win_r3_20.log` | `finetune_slm/runs/round3_strict_labels/judge_win_r3_20.log` |
| `test_results/judge_win_r3_50.log` | `finetune_slm/runs/round3_strict_labels/judge_win_r3_50.log` |
| `test_results/natgen_main.log` | `finetune_slm/runs/natural_data_generation/natgen_main.log` |
| `test_results/natgen_main2.log` | `finetune_slm/runs/natural_data_generation/natgen_main2.log` |
| `test_results/natgen_main3.log` | `finetune_slm/runs/natural_data_generation/natgen_main3.log` |
| `test_results/natgen_pilot.log` | `finetune_slm/runs/natural_data_generation/natgen_pilot.log` |
| `test_results/natverify.log` | `finetune_slm/runs/natural_data_generation/natverify.log` |
| `test_results/verify_loop.sh` | `finetune_slm/runs/natural_data_generation/verify_loop.sh` |
| `test_results/verify_loop2.sh` | `finetune_slm/runs/natural_data_generation/verify_loop2.sh` |
| `test_results/STOP_VERIFY` | `finetune_slm/runs/natural_data_generation/STOP_VERIFY` |
| `test_results/m3_outputs.tgz` | `finetune_slm/archive/transfer_tarballs/m3_outputs.tgz` |
| `test_results/test_step400_outputs.tgz` | `finetune_slm/archive/transfer_tarballs/test_step400_outputs.tgz` |
| `test_results/m3_baseline.tgz` | `finetune_slm/archive/transfer_tarballs/m3_baseline.tgz` |
| `../ov_step400_fp16` | `finetune_slm/deployment/step400_round1/model_files` |
| `../ov_step156_fp16` | `finetune_slm/deployment/step156_round2/model_files` |
| `azure_ml_ft/score_single_file_step400.py` | `finetune_slm/deployment/step400_round1/score_single_file_step400.py` |
| `azure_ml_ft/score_single_file_step156.py` | `finetune_slm/deployment/step156_round2/score_single_file_step156.py` |
| `azure_ml_ft/build_single_file_score.py` | `finetune_slm/deployment/source/build_single_file_score.py` |
| `azure_ml_ft/score.py` | `finetune_slm/deployment/source/score.py` |
| `azure_ml_ft/selftest_score.py` | `finetune_slm/deployment/source/selftest_score.py` |
| `azure_ml_ft/local_ov_test.py` | `finetune_slm/deployment/source/local_ov_test.py` |
| `azure_ml_ft/local_ov_m3.py` | `finetune_slm/deployment/source/local_ov_m3.py` |
| `azure_ml_ft/sample_request.json` | `finetune_slm/deployment/source/sample_request.json` |
| `azure_ml_ft/code_bundle` | `finetune_slm/deployment/source/code_bundle` |
| `azure_ml_h1` | `finetune_slm/deployment/h1_baseline` |
| `docs/FINETUNING_TRAINING_REPORT.md` | `finetune_slm/docs/FINETUNING_TRAINING_REPORT.md` |
| `docs/MODULE3_FINETUNING_FOCUS.md` | `finetune_slm/docs/MODULE3_FINETUNING_FOCUS.md` |
| `direct_inference_baseline/experiments/EXP_008_QWEN3_0.6B_HYBRID_P02_S1` | `finetune_slm/experiments/qwen3_0.6b_baseline/EXP_008_QWEN3_0.6B_HYBRID_P02_S1` |
| `direct_inference_baseline/experiments/EXP_002_QWEN3_0.6B_GPU_DIRECT` | `finetune_slm/experiments/qwen3_0.6b_baseline/EXP_002_QWEN3_0.6B_GPU_DIRECT` |
| `direct_inference_baseline/experiments/EXP_001_QWEN3_0.6B_CPU_BASELINE` | `finetune_slm/experiments/qwen3_0.6b_baseline/earlier_experiments/EXP_001_QWEN3_0.6B_CPU_BASELINE` |
| `direct_inference_baseline/experiments/EXP_003_QWEN3_0.6B_OPENVINO_GPU_DIRECT` | `finetune_slm/experiments/qwen3_0.6b_baseline/earlier_experiments/EXP_003_QWEN3_0.6B_OPENVINO_GPU_DIRECT` |
| `direct_inference_baseline/experiments/EXP_004_QWEN3_0.6B_PROMPT_ENGINEERING` | `finetune_slm/experiments/qwen3_0.6b_baseline/earlier_experiments/EXP_004_QWEN3_0.6B_PROMPT_ENGINEERING` |
| `direct_inference_baseline/experiments/EXP_005_S0_DETERMINISTIC_REPAIR` | `finetune_slm/experiments/qwen3_0.6b_baseline/earlier_experiments/EXP_005_S0_DETERMINISTIC_REPAIR` |
| `direct_inference_baseline/experiments/EXP_006_S1_SIMPLIFIED_EXTRACTION` | `finetune_slm/experiments/qwen3_0.6b_baseline/earlier_experiments/EXP_006_S1_SIMPLIFIED_EXTRACTION` |
| `direct_inference_baseline/experiments/EXP_007_S1_1_SIMPLIFIED_EXTRACTION` | `finetune_slm/experiments/qwen3_0.6b_baseline/earlier_experiments/EXP_007_S1_1_SIMPLIFIED_EXTRACTION` |
| `direct_inference_baseline/experiments/kernel.errors.txt` | `finetune_slm/experiments/qwen3_0.6b_baseline/earlier_experiments/kernel.errors.txt` |
| `direct_inference_1_7B` | `finetune_slm/experiments/qwen3_1.7b_track` |
| `dataset` | `finetune_slm/archive/dataset` |
| `dataset_v2_batch_001` | `finetune_slm/archive/dataset_v2_batch_001` |
| `dataset_v2_batch_001_corrected` | `finetune_slm/archive/dataset_v2_batch_001_corrected` |
| `dataset.zip` | `finetune_slm/archive/dataset.zip` |
| `dataset_v2.tar` | `finetune_slm/archive/dataset_v2.tar` |


## 2026-11-26: the root folder `direct_inference_baseline/` moved into `finetune_slm/direct_inference_baseline/`
It is the code package of the H1 pipeline (config, inference, evaluation, prompts, tests) and is imported by the app (`clinical_extraction/h1_worker.py`, `inference_worker.py`). The package name is unchanged; the two workers add `finetune_slm/` to the import path. `config/settings.py` now finds the project root as the folder that holds `clinical_extraction_schema.json` (the repository root, or the root of the Azure scoring bundle) and finds the frozen dataset in `finetune_slm/archive/`. The two scoring-file builders copy the package from the new place; the bundle layout is unchanged. The step-400 scoring file already deployed to Azure was not rebuilt (a rebuild differs only in `settings.py`).


## 2026-11-26: `office_transfer_package/` (and `office_transfer_package.zip`) renamed and archived
Now `finetune_slm/archive/office_laptop_transfer_snapshot_2026-11-16/` and `office_laptop_transfer_snapshot_2026-11-16.zip` (not in Git: 3.3 GB folder and 2.5 GB zip). It is a snapshot made on 2026-11-16 to move the Qwen3-1.7B P02 stage to another laptop (its own `README_TRANSFER.md`, `MANIFEST_SHA256.txt` and `Verify-Package.ps1` are untouched, so the old verification still works inside the folder). A comparison by name, size and SHA-256 found that almost everything in it exists elsewhere in the repository: the dataset (1,005 of 1,005 files), `direct_inference_1_7B` (262 of 262), `direct_inference_baseline` (21 of 21), the schema, the script and 10 of the 11 model files. Only its `setup/` (Windows OpenVINO setup guide), 15 files of `azure_ml/` (the 1.7B hosting yaml files and README), 9 older versions of `clinical_extraction/` files and the package's own README, manifest and verification script exist nowhere else.

## 2026-11-26: more root clean-up
* `archive/obsolete_experiments_after_P01/` (223 files, the discarded P02 attempts of the 1.7B track) is now `finetune_slm/archive/obsolete_experiments_after_P01/`. The path in `p02/code/verify_prompt.py` was adjusted (`parents[3]`).
* `_recovered_archives/` (two partial `.zip.recovered` files of the dataset and the voice models) is now `finetune_slm/archive/_recovered_archives/`.
* `kernel.errors.txt` (an OpenVINO GPU-compiler error log) is now `finetune_slm/experiments/qwen3_1.7b_track/kernel.errors.txt`.
* The empty folder `AppData/` was removed (it held no files).

## 2026-11-26: two folder names shortened (Windows 260-character path limit)
A clone into `C:\Users\...\Desktop\OMKAR\ambinet-listening` failed to check out the longest files (220 characters; 100 of them were over the limit once the clone prefix was added). Renamed:
* `finetune_slm/experiments/qwen3_0.6b_baseline/` -> `finetune_slm/experiments/qwen3_0.6b/`
* `.../earlier_experiments/` -> `.../earlier/` (so `finetune_slm/experiments/qwen3_0.6b/earlier/EXP_001, 003 to 007`)
The longest path in the repository is now 199 characters, which fits a clone location of up to about 60 characters. Wherever this document or an older report says `qwen3_0.6b_baseline` or `earlier_experiments`, read the new names. Code, tests and live documents were updated; experiment files and the numbered report sections 1 to 36 keep their original wording.
