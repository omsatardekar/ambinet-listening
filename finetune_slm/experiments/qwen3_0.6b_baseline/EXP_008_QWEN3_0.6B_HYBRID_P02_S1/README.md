# EXP_008: Qwen3-0.6B hybrid prompt (full P02 schema + S1.1 discipline, no example facts)

Status: COMPLETE. Prompt frozen (`config/H1_FREEZE.json`); main run on the 30 shared encounters finished 30/30 parsed, 0 failed, 0 token-cap hits (`outputs/H1_main30/run_summary.json`); scored with the gpt-5.4 judge. Prompting only, no fine-tuning.

## Goal (owner's request)
The mentor chose Qwen3-0.6B for the final track. This last prompting experiment combines:
- the **full, normal P02 JSON** (all sections and keys, SEG evidence ids, `clinical_evidence` = `[]`), not the simplified S1.1 format;
- the **discipline that made S1.1 B1 the best 0.6B run**: write only what is said, a doctor's question is not a fact, one item per fact;
- **no worked examples with literal values.** The 1.7B P02 prompt contained 14 invented example facts (eyelid twitch, hip pain, 138/86, muscle strain, sinus scan, shoulder advice, an aunt's gallstones ...). A 1.7B model copied them into real outputs (seen on encounters 00037 and 03). H1 has none, and the runner refuses to start if any of those words appear in the prompt;
- an explicit rule that an empty list `[]` is correct when nothing is stated.
The same 30 encounters as the 1.7B P01/P02 runs are used so the result can be compared with the same LLM judge.

## Setup (unchanged from the earlier 0.6B experiments)
Qwen3-0.6B (revision c1899de2...), OpenVINO FP16 IR from EXP_002, Intel GPU, greedy decoding, thinking off, a fresh pipeline per encounter, `max_new_tokens` 6144 (the longest earlier 0.6B full-schema output was 2,674 tokens). Dataset `dataset_v2_batch_001_corrected`; inputs only (labels are never opened by the runner, see `file_access_audit.json`). The existing inference runner, parser and schema validator are imported read-only. Nothing in EXP_001 to EXP_007 or the 1.7B track was modified.
Runner: `scripts/run_h1.py`. Diagnostics: `scripts/check_outputs.py`. Memory guard: a generation does not start below 3.5 GiB available RAM (the 0.6B runs peak at about 3.1 GB; the 8 GiB gate belongs to the 1.7B P02 runs).

## How the prompt was built (and what failed)
All prompt work used 3 spare development ids (00288, 00289, 00291) that are NOT among the 30 evaluated ids.
| attempt | result on spare ids |
|---|---|
| v1 full instructions, "use the fewest lines" for evidence | truncated at 6,144 tokens: 20+ SEG ids listed per item |
| v2 `<angle-bracket>` template (B1 style, full keys) | invalid JSON after 5,327 tokens |
| v3 "[] is correct, delete the blank item" emphasis | parsed, but echoed the blank skeleton (7 junk items, nothing extracted) |
| v4 coverage-first wording, blank skeleton head | parsed, but every field blank |
| v5 placeholders only in the head fields | chief complaint filled, every list blank |
| runner sanity check | the original EXP_004 P02 prompt through this runner reproduced the stored output exactly (same text, 1,301 tokens), so the collapses were caused by the prompts, not the setup |
| v6a/b/c/d: start from the proven EXP_004 P02 prompt, remove its literal examples, add faithfulness bullets, switch to SEG evidence | all parsed; compared below |

Finding: a 0.6B model copies a blank JSON skeleton unless the first fields hold `"<text>"`-style placeholders; long rule lists lower recall; it cannot cite segments (it leaves `evidence_ids` empty).

## Prompt selection on the 3 spare ids (gpt-5.4 judge, lenient judge-F1; n=3, so only directional)
| prompt | precision | recall | judge-F1 | hallucination | critical-flag rate |
|---|---|---|---|---|---|
| EXP_004 P02 (reference) | 0.641 | 0.239 | 0.348 | 0.154 | 0.179 |
| S1.1 B1 (reference) | 0.710 | 0.257 | 0.377 | 0.220 | 0.140 |
| v6b (chosen) | 0.600 | 0.147 | 0.236 | 0.233 | 0.133 |
| v6c | 0.541 | 0.183 | 0.274 | 0.216 | 0.189 |
| v6d | 0.456 | 0.206 | 0.284 | 0.311 | 0.222 |
**v6b** was frozen: highest precision and lowest critical-flag rate of the hybrids, and it avoids v6d's degenerate speaker list. No hybrid beat the earlier prompts on this selection data; v6b was chosen because the owner's priority is minimal hallucination with partial recall acceptable, not because it won.

## Known weaknesses seen in the spare-id outputs
- `evidence_ids` are empty (the model does not cite segments); `clinical_evidence` is `[]` as designed.
- `primary_speakers.speaker_id` is sometimes `"1"` or `"0"` instead of `person_N`; a few roles are written in capitals.
- Wrong items still occur (for example a symptom also listed as a negative finding).

## Files
- `prompts/H1_hybrid_prompt.txt` (frozen; sha256 in `config/H1_FREEZE.json`), `prompts/superseded/` (failed designs kept for the record), `prompts/H1_v6*.txt` (selection candidates), `prompts/SANITY_EXP004_P02_copy.txt` (runner check only).
- `outputs/H1_main30/` raw, parsed and failed predictions, `performance.json`, `run_summary.json`; `outputs/H1_*smoke3` and `outputs/_failed_smoke_attempts/NOTES.txt` (prompt-selection runs).
- Judge results: `judge_eval/` (see its REPORT.md and METHODOLOGY.md).

## Results (30 shared encounters, gpt-5.4 judge, lenient judge-F1; Judge-F1 is not clinical accuracy)
Run quality: 30/30 parsed on the first attempt, finish reason `stop` for all, longest output 2,577 of 6,144 tokens, median 1,167 tokens, median 225 s per encounter on the Intel GPU, no leftover `<placeholders>`, no invented segment ids, no label file opened.
| run | judge-F1 [95% CI] | precision | recall | hallucination | critical-flag rate | parsed of 30 |
|---|---|---|---|---|---|---|
| **H1 (this experiment)** | **0.352 [0.313, 0.390]** | 0.568 | 0.255 | 0.262 | 0.120 | **30** |
| S1.1 B1 (best earlier 0.6B) | 0.395 [0.343, 0.444] | 0.650 | 0.284 | 0.280 | 0.119 | 27 |
| P02 (EXP_004) | 0.318 [0.263, 0.364] | 0.577 | 0.220 | 0.241 | 0.136 | 30 |
| P01 (EXP_004) | 0.291 [0.234, 0.341] | 0.557 | 0.197 | 0.249 | 0.114 | 30 |
| EXP_003 direct | 0.193 [0.152, 0.230] | 0.589 | 0.115 | 0.167 | 0.107 | 29 |
| 1.7B P02 (frozen, for reference) | 0.536 [0.484, 0.573] | 0.666 | 0.448 | 0.231 | 0.101 | 28 |
Paired differences (same encounters, 95% CI): H1 vs S1.1 B1 -0.043 [-0.096, +0.020] (tie); H1 vs EXP_004 P02 +0.034 [-0.015, +0.083] (tie); H1 vs P01 +0.061 [-0.004, +0.133] (borderline); H1 vs EXP_003 +0.159 [+0.110, +0.207] (better); H1 vs 1.7B P02 -0.184 [-0.232, -0.126] (worse).

What it achieved:
- The full normal P02 JSON with 100% first-attempt parse (S1.1 B1 parsed 27/30, S1 24/30, B2 17/30).
- No copying of example facts. The old 1.7B P02 prompt's invented examples (hip pain, 138/86, rest the shoulder, gallstones, sinus scan ...) appear in 28 of 28 outputs of the frozen 1.7B P02 run (106 hits) and in 0 of 30 H1 outputs (also 0 in the earlier 0.6B prompts, which never contained those examples).
What it did not achieve:
- It does not beat the best earlier 0.6B prompt (S1.1 B1) and its hallucination rate (0.262) is not lower than the earlier prompts'. The hybrid design removed copying from the prompt, but the 0.6B model still invents items on its own.
Weakest sections (precision/recall, lenient): negative_findings 0.32/0.14 (30 items written for 168 expected, most wrong), review_of_systems 0.14/0.08, follow_up 0.44/0.35, clinical_actions 0.61/0.16, social_history 0.93/0.09 (rarely written), clinical_uncertainties never written (0 of 25).
Format problems: roles written as person_1/person_2/person_3 in 141 places despite the rule; `evidence_ids` always empty (the model does not cite segments); `speaker_id` sometimes "1".
Sections it fills even when it should often be empty: negative_findings and clinical_assessment in all 30 encounters, symptoms 30/30, vital_signs 24/30. The "write [] when nothing is stated" rule helped only partly.
