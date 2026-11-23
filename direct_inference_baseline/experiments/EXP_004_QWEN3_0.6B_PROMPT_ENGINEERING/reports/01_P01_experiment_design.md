# P01 experiment design - schema-focused prompt (FOR APPROVAL; nothing has been run)

## 1. Hypothesis
Most schema failures are caused by a small number of repeatable, instruction-fixable habits (see `00_error_analysis_and_split.md` section 3): sections emitted as objects instead of arrays,
upper-case or id-valued role fields, missing `confidence: null`, null `certainty`, out-of-enum `status`/`category`/`route`, missing `primary_speakers` / `supports`.
Stating these rules explicitly should cut schema violations substantially **without** changing what is extracted. P01 changes structure rules only; it is not expected to change recall.
It may even reduce recall if a longer prompt distracts the 0.6B model; that is what the test checks.

## 2. What P01 changes (and what it must not change)
P01 = P00 + a short **"Structure rules"** block (about 12 lines) inserted after "Rules", plus small edits to the output template for consistency. The task wording, the extraction rules,
the allowed-values lists and the template's keys stay as in P00. The diff against P00 is saved with the prompt (`prompts/P01_schema_focused.diff`), and the exact P01 text will be shown to you for review, hashed and frozen before any run.

Planned rules (wording is illustrative, final text is frozen and hashed before running):
1. Every section whose template value starts with `[` is a JSON array, including `clinical_assessment`, `physical_examination`, `follow_up`; use `[]` when nothing is stated. Never output an object for these sections.
2. Role fields (`reported_by`, `observed_by`, `stated_by`, `speaker_role`, `role`) use only: doctor, patient, nurse, caregiver, family_member, clinical_staff, unknown, **in lower case**. The transcript prints roles in capitals (PATIENT, DOCTOR): convert them to lower case. Never put a speaker id (person_1) or an empty string in a role field.
3. Every item that has a `confidence` field includes it, with the value `null`; same for `role_confidence`.
4. `certainty` is never null: use certain, uncertain or disputed. `severity` is null unless stated. `medications.route` is `oral` or null (allowed set in the frozen schema).
5. `encounter_metadata.primary_speakers` lists every speaker of the transcript once (speaker_id exactly as printed, role in lower case, `role_confidence` null).
6. Each `clinical_evidence` record has all keys including `supports`; `speaker_id` is copied from the transcript line that contains the text.
7. Always output every top-level key of the template, in the template order.
8. Enum fields use only the listed values; if none fits, use null where the template allows null.
Nothing about clinical content, terminology, completeness, negation or evidence quality is added (those are P02-P05).

## 3. Controlled conditions (identical to EXP_003)
Model Qwen3-0.6B rev c1899de2..., OpenVINO FP16 from EXP_002, GPU (UHD 620), fresh pipeline per encounter, greedy (do_sample false), enable_thinking false, max_new_tokens 6144, same `inference_runner`, `output_parser`, `schema_validator`, evaluator and the frozen schema. Only the prompt text differs. The evaluator, schema, labels and dataset are untouched; labels are opened only by the evaluator after generation, with the same file-access audit as EXP_003.
Runner: a new script in `EXP_004/experiments/` that imports the unmodified module and the EXP_003 OpenVINO client (copied, not edited); outputs go to `outputs/P01_schema_focused/` (raw, parsed, failed) and `evaluation/P01_schema_focused/`. Nothing in EXP_001-003 is written.

## 4. Encounters
* Development run: the **50 `prompt_dev` ids** (`experiments/split_v1.json`), identical for every prompt version.
* P00 reference: the existing EXP_003 outputs for the same 50 ids (prompt sha256 78c5ab95...; same model, settings, hardware). To confirm the GPU runs are reproducible, I would first re-run P00 on 3 prompt_dev encounters (about 8 min) and compare the raw outputs byte for byte; if they differ, the paired comparison carries run-to-run noise and I will report it.
* Validation ids are **not** run for P01 unless it passes the keep rule below (conserves GPU time and keeps the validation half clean).

## 5. Metrics and pre-registered decision rule
Recorded per version (all from the existing evaluator): valid/invalid/truncated counts, schema compliance, violation counts by kind and by pattern, required-field completeness, TP/FP/FN, micro and macro P/R/F1, category F1, vital accuracy, speaker attribution, evidence grounding, unsupported claims, latency, tokens, tokens/s, plus paired per-encounter differences against P00 on the same ids (mean difference with a bootstrap 95% interval; n=50 is small, so I will say when a difference is within noise).

Keep P01 as a strategy if **all** hold on prompt_dev:
* schema violations (total) fall by at least 30% versus P00 and wrong_type violations fall by at least 80%;
* valid-JSON count is not worse by more than 2 encounters (malformed JSON must not increase);
* micro F1 is not lower than P00 by more than 0.005 absolute and no category with F1 above 0.1 in P00 loses more than 0.05;
* mean output tokens do not collapse (an emptier output can look "compliant"; completeness and F1 guard against that).
Reject if the first or second condition fails; "keep with changes" is possible only for a documented, targeted wording fix, run as a new version P01b on prompt_dev.
Compliance gaming check: I will report the number of empty sections per output so that "more compliant because less content" is visible.

## 6. Cost and schedule
Prompt is about 700 tokens longer than P00 (about 4,470 input tokens instead of 3,770): expected prefill +5 s, so about 160 s per encounter, 50 encounters about **2.3 h** GPU, plus about 8 min for the reproducibility check. The runner is resumable; progress is logged per encounter. An optional interim look at partial results is possible as before.

## 7. Safeguards
* The prompt text is written and hashed before any run; no prompt edits during a run; every version stored under `prompts/` and never overwritten.
* Leakage check (scripted, before running): no string from the development labels (entity names and normalised values) may appear in the prompt except enum words from the frozen schema. Examples inside prompts use generic wording only.
* Error inspection for tuning uses `prompt_dev` encounters only (validation was already seen in aggregate; see the caveat in the analysis).
* If GPU init fails I stop and report; no silent CPU fallback.

## 8. Plan for later versions (hypotheses linked to the observed errors; none assumed to work)
| Version | Targets | Observed evidence |
|---|---|---|
| P02 comprehensive extraction | recall; standard clinical terms in `normalized_*` fields; fill every section the transcript supports (vitals, negatives, actions, follow-up, assessment, social history) | recall 2.7%; 4 entities per encounter vs about 36 gold; 276 supported FPs mostly terminology mismatches |
| P03 evidence-grounded | one evidence record per cited line, correct `speaker_id`, `evidence_ids` on every item | 94 evidence records for 94 encounters, 242/382 entities without ids, 45 wrong speaker ids |
| P04 negation and temporality | denied findings to `negative_findings`; current/past/resolved/uncertain | 0/543 gold negatives reproduced; 88/94 outputs have none |
| P05 speaker attribution | role from the transcript line speaker, no invented roles, unknown when unclear | 51% attribution; capital-letter and id-valued roles |
| P06 combined | only the strategies that show measured gains on prompt_dev and are confirmed on validation | decided by results |
Each later prompt starts from P00 or from the already-validated prompt only if you approve that choice; the default is to test each strategy against P00 independently first, then combine the winners (P06) and re-test.
Rough GPU budget at 2.3 h per 50 encounters: P01-P05 on prompt_dev about 12 h; P06 on prompt_dev and the validation runs for P00 reference reuse (EXP_003) plus about 3 finalists about 7 h; total roughly 20 h, spread over several sessions.

## 9. Decisions I need from you
1. Approve the 50/50 split (or ask for a different ratio).
2. Approve validation only for finalists (P01 and others only if they pass their keep rule), instead of validating every version.
3. Approve the P00 reproducibility re-run on 3 prompt_dev encounters.
4. Approve the keep/reject thresholds above (or change them).
