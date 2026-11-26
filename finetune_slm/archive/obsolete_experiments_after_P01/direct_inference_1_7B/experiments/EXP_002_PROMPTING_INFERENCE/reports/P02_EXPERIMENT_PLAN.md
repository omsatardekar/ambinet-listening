# P02 experiment plan v2.1 (Qwen3-1.7B): after the final consistency check; nothing here has been run

**Status: revised plan for approval. Not approved for inference.** **DEVELOPMENT-ONLY.** All records are among the 50 prompt-development ids (used earlier for 0.6B prompt development; generator-derived labels). No use of the consumed validation set, the locked test set or sealed files. Prompt under review: `P02_COMPREHENSIVE_PROMPT_DRAFT.md` **v2.1 (sha256 `e8fab9034acee29d7bc93a5303e657c8b9fd5841d9df9d5e153f6effe9850ed5`, 19,680 characters, 4,170 tokens)**; v2 (`effe5be3…d802`, 3,910 tokens) and v1 are preserved. All changes: `P02_FINAL_REVIEW_CHANGELOG.md`. Evidence base: `P00_P01_RECORD_BY_RECORD_GAP_ANALYSIS.md`, `P00_P01_CLINICAL_EXTRACTION_ROOT_CAUSE_REPORT.md`, `INVALID_JSON_TRUNCATION_AND_RECOVERY_ANALYSIS.md`.

## 0. Decisions needed from you before the pilot (nothing below has been changed)
| # | Decision | Why | My recommendation |
|---|---|---|---|
| D1 | **Available-RAM threshold at start.** The plan text so far said 7 GB. Measured evidence (section 8) shows 7 GB leaves 0.0 to 0.5 GB headroom in the worst observed cases | RAM is the main hardware risk | **Adopt a hard gate of at least 8.0 GB** (needs Chrome and other large apps closed; 7.36 GB is available right now). Keep 7.0 GB only if you accept the documented risk. The value in force until you decide: 7.0 GB |
| D2 | **Out-of-memory retries.** The runner treats an "out of memory" RuntimeError as transient and retries it up to 3 times (2, 4, 8 s) on the same configuration (`ov_client_1_7b.py` lines 80-82; `base_client.generate`; `run_prompt.py` passes `retries=3`) | your earlier rule: stop and report the real error, no repeated retries of an unsupported configuration | **Set `retries=0` for the pilot** so an out-of-memory error is recorded and the run stops with the exact error |
| D3 | **Runner changes** (no generation setting involved): add `--ids` for the frozen eight-id subset; add the RAM gate (the runner currently only *records* available RAM before each call as `system_available_mb_before` and has no gate); apply D2 | the gate in this plan does not exist in code yet | approve a small reviewed change to `run_prompt.py`, hash-frozen like P01's files |

## 1. Objective and hypotheses
Objective: increase the correct clinical information extracted per record from Qwen3-1.7B and stop losing records to the token cap. **The only experimental variable is the prompt text.** Unchanged: model and revision `70d244cc…`, OpenVINO FP16 on the explicit GPU, greedy decoding, thinking disabled, `max_new_tokens=4096`, OpenVINO settings, transcript rendering, evaluator, frozen schema, the single-call architecture.

| # | Hypothesis | Basis | Null |
|---|---|---|---|
| H1 | Explicit per-section coverage rules and the schema's own definitions raise the number of correct facts without lowering precision | outputs stop 40% below the cap; 733 of 1,093 gold facts missed; conventions never given | no gain over P01 on records both complete (tier 2) |
| H2 | A compact template and one-line evidence rules cut output tokens and remove truncation | whitespace is 29-31% of output tokens; every truncation is inside the evidence string | any cap hit, or most outputs still indented |
| H3 | Reading the role from each line fixes speaker lists and attribution | person_1 is the doctor in 9/30 records; P00 0/9, P01 1/6 correct | speakers wrong in the doctor-first records |
| H4 | One evidence record per cited line gives usable evidence | 22/23 and 23/25 outputs had one blob record | evidence collapse persists (then a separate P02-E decision) |
| H5 | Placeholder, route, history and allergy rules remove convention errors | empty strings and `person_N` roles; invented route; placeholder/medication allergies | counts do not fall |

## 2. Traceability: prompt change -> observed failure -> measure
| P02 v2.1 change | Observed failure (30-record audit unless stated) | Measure in the pilot |
|---|---|---|
| Line-by-line coverage; one item per distinct fact; symptoms list (multiple symptoms per sentence, later mentions, accompanying symptoms, resolved earlier episodes, corrections) | 12 of 91 gold symptoms matched; one symptom per record | symptoms matched by key and fully correct (G5b) |
| Negatives: one item per item asked, any denial wording, none from silence, no copied examples | 4 of 168 negatives matched by key, none fully correct; stock negatives written 34 times, 11 absent from the transcript | fully-correct negatives (G5a); unsupported negatives |
| ROS four-case rule (schema has only `negative`) | 0 of 40 ROS matched; 17 unsupported ROS entries (systems not asked) | ROS matched; ROS entries unsupported (G6) |
| PMH only for present conditions; resolved episodes -> symptoms | PMH status is `ongoing` only; resolved episodes live in symptoms in gold | PMH-as-ongoing audit (G6) |
| Medication status/route/dose/frequency/duration kept apart; route only if "by mouth" said | 14 of 17 planned missed; invented `oral` in 17 of 37 matched items (P01); `once a day` in `dose` | planned-medication recall (G5d); invented-route count (G6) |
| Allergy five-case rule | 21 incorrect allergy entries (placeholders, medications); 22/30 status errors | placeholder/medication-as-allergy count (G5e, G6) |
| Reporter / observer / stated-by / responsible-person / no subject field | 12 genuine doctor->patient role confusions; relatives' facts | speaker and attribution checks (G2) |
| Every speaker id, role from the line | 13/23 and 8/25 records omit a speaker; person_1 assumed patient; 42 `person_N` roles | speakers (G2) |
| Placeholder rule, shapes of duration/time_reference/value, full enum list | empty strings and enum violations (212 in P01); social-history status/category missing from P00/P01 | empty-string count, schema violations (G2) |
| `vital_signs.value` required, placeholder not an empty string; number or blood-pressure text | v2 contradiction (template `""` vs rule); gold 219 of 219 never empty, numbers except blood-pressure text | empty-string count; vital-sign value validity (G2) |
| Uncertainty relationships (`related_entities`, `resolution_status`, per-type conventions), exact `contradictions_detected` / `ambiguous_entities`, conditional actions only for investigations and return visits | schema reference rules; gold 44 of 44 uncertainties follow them; v2 stated contradictions loosely | schema violations, uncertainty extras (G2, G6) |
| Quality-check flag rules | flags copied from the template in 100% of outputs (negation false with negatives in 18 of 18 P01 records) | flag consistency (G2) |
| Actions: read the whole plan, one item per instruction | 1 of 165 actions matched; 1.7 vs gold 5.5 per record | actions matched (G5c) |
| Uncertainty closed list | 17 `date_uncertain` fillers (gold 3) | uncertainty extras |
| Compact template | indented output in 30/30 | compact compliance, tokens (G1) |
| Evidence rules (one record per cited line, copy one line, at most 2 lines per fact, no greetings, ids must exist, supports reciprocal) | single blob record; empty `supports` in 53 of 54 evidence records | the five evidence measures (section 5) |

Not changed on purpose: P00's working rules, the 18 categories, the canonical key set and order (programmatically verified: 108 static checks, 0 failed, plus 31 label-convention claims verified on the 50 dev gold labels), the transcript rendering and every generation setting.

## 3. Pilot records (unchanged: eight of the 30, same ids as P00 and P01)
`00168, 00204, 00037, 00092, 00152, 00157, 00042, 00165`; run order as listed (the two records that both baselines truncated first, for an early completion signal).

| ID | Transcript tokens | Speakers (person_1) | P00 / P01 | Why included |
|---|---:|---|---|---|
| 00168 | 1,719 | 3 (patient), nurse | fail / fail | truncated by both; 3 speakers incl. nurse |
| 00204 | 1,772 | 3 (patient) | fail / fail | truncated by both |
| 00037 | 2,428 | 3 (**doctor**), patient, caregiver | ok / fail | P01 lost it; caregiver |
| 00092 | 2,166 | 2 (**doctor**) | ok / fail | P01 lost it |
| 00152 | 1,619 | 2 (**doctor**) | ok / ok | shortest; 8 gold negatives |
| 00157 | 1,627 | 2 (**doctor**) | ok / ok | vitals, fluticasone, allergy placeholder |
| 00042 | 1,941 | 2 (patient) | ok / ok | negatives, social history, actions, planned drug |
| 00165 | 1,774 | 3 (patient), nurse | ok / ok | nurse speaker, vitals |

**The subset was reviewed for a concrete methodological error and is kept.** The one selection effect is real and handled by design: the subset contains the records the baselines truncated, so as-scored baselines are depressed (2 of 8 failures for P00, 4 of 8 for P01) and a prompt that merely completes those records would look better under strict as-scored scoring alone. That is exactly why tier 2 (paired parsed-output comparison) is a required gate, and why tier 1 is never used as the only evidence. Results from the pilot are indicative of the gates only and are not a basis for general claims (8 records, 280 gold facts, hand-chosen for failure modes).

## 4. The three evaluation tiers (definitions)
| Tier | Name | Definition | Role |
|---|---|---|---|
| 1 | **Normal strict evaluation** | the unchanged strict canonical evaluator on all 8 pilot ids; failed or truncated records contribute zero predictions; recovered outputs are not used | **PRIMARY result and headline.** Used for gates G4, G5 |
| 2 | **Parsed-output paired comparison** | strict micro P/R/F1 (and fully-correct counts from the audit) only on the records for which both P02 and the comparator (P01, and separately P00) produced a parsed, valid JSON object | extraction-only evidence, not a headline. Gate G4b. The paired set is determined after the run; thresholds are deltas against the comparator on those same ids |
| 3 | **Structural-recovery diagnostic** | failed outputs closed structurally (cut at the last complete element, close containers, add nothing) and scored; labelled INCOMPLETE; status `incomplete_recovered`, never `completed` | **diagnostic only**: shown in a separate table with the missing keys listed; **no gate is evaluated on tier 3 and no record counts as completed because of it** |

Every report states the tier on each number. Reports never merge tier 3 into tier 1.

## 5. Evidence measurement (not assumed: the pilot measures it)
Script `scripts/p02_gate_metrics.py` (read-only analysis; computes the same measures for P00, P01 and, after approval, P02). References below are computed on the exact eight pilot ids from the saved P00 and P01 outputs (`evaluations/p02_review/PILOT_GATE_REFERENCES.json`, `pilot_ids` stored in the file).

| Measure | Definition | P00 (6 parsed) | P01 (4 parsed) |
|---|---|---:|---:|
| Evidence records per encounter | records in `clinical_evidence` per completed output (mean) | 1.0 | 1.0 |
| Exact transcript lines | share of evidence records whose text equals one transcript line | 0% (0/6) | 25% (1/4) |
| Whole-transcript or multi-line blobs | records containing 2 or more lines | 2 | 1 |
| Facts with valid evidence ids | facts whose ids all resolve to an existing record | 80% (90/112) | 98% (62/63) |
| Facts with relevant cited text | facts whose cited text mentions the fact (the evaluator's lexical test) | 27% | 8% |
| Correct `supports` paths | citation pairs where the fact's path is in the record's `supports`; and `supports` paths that resolve to an entity citing the record | 0%; n/a (all empty) | 0%; n/a |

"Valid ids" alone is misleading (P01 scores 98% because every fact cites the one blob record that exists), so it is always reported together with relevance and `supports` correctness.

## 6. Gates (pre-registered; evaluated on the pilot; thresholds computed on the exact eight ids)
Reference values are computed from saved outputs by `scripts/p02_gate_metrics.py` and `scripts/pilot_reference_metrics.py` on `00168, 00204, 00037, 00092, 00152, 00157, 00042, 00165` (the scripts assert these eight ids).

**Reference values, exact eight ids (gold facts 280)**
| | P00 | P01 |
|---|---|---|
| Parsed / failed / cap hits | 6 / 2 / 2 | 4 / 4 / 4 |
| **Tier 1** strict micro P / R / F1 (TP/FP/FN) | 0.179 / 0.071 / 0.102 (20/92/260) | 0.270 / 0.061 / 0.099 (17/46/263) |
| **Tier 2** on its own parsed ids | ids 00037 00092 00152 00157 00042 00165: P 0.179, R 0.094, F1 0.123 | ids 00152 00157 00042 00165: P 0.270, R 0.128, F1 0.173 |
| Tier 2 on the 4 ids both parsed | P 0.254, R 0.120, F1 0.163 | P 0.270, R 0.128, F1 0.173 |
| Tier 3 diagnostic (INCOMPLETE, context only) | P 0.212, R 0.121, F1 0.155 | P 0.234, R 0.146, F1 0.180 |
| Mean output tokens of completed records | 2,030 | 1,667 |
| Empty-string values / `person_N` written as role | 27 / 28 | 2 / 0 |
| All speakers correct (completed records) | 1 of 6 | 3 of 4 |
| Quality flags consistent: negation / review | 4 of 6 / 2 of 6 | 3 of 4 / 2 of 4 |
| Schema violations per parsed record (missing `confidence` per record) | 19.2 (9.2) | 4.5 (2.5) |
| Fully-correct negatives / symptoms matched / actions matched | 0 / 2 / 0 | 0 / 2 / 0 |
| Planned medications matched (gold 5) | 0 | 1 |
| Invented route / incorrect allergy entries | 3 / 3 | 4 / 3 |
| Unsupported review-of-systems entries | 1 of 2 | 1 of 2 |
Gold on the eight ids: 51 negatives, 23 symptoms, 39 actions, 16 medications (5 planned), 3 allergies, 36 vital signs, 10 ROS, 12 physical examination, 25 social history.

| Gate | Criterion on the 8 pilot ids | Reference and reason for the threshold |
|---|---|---|
| **G1 completion and layout** | at least 7 of 8 parse; at most 1 cap hit; at least 7 of 8 completed outputs contain no indentation (no `\n` followed by spaces); no completed output above 3,700 tokens; mean tokens reported | P00 2/8 and P01 4/8 failed; P00 and P01 are indented in 100% of outputs. Cap hits must be rare (P01 rate 13% over 30; here 4/8 by selection). Mean tokens are only reported because P02 extracts more items, which lengthens output |
| **G2 format and schema** (tier 1 data) | empty-string values at most 2 in total; `person_N` as role at most 2 in total; all speakers correct in at least 7 of 8 (including the four doctor-first records 00152, 00157, 00037, 00092); quality flags consistent in at least 7 of 8 (negation, review); schema violations at most 9 per parsed record, missing `confidence` at most 3 per record, no missing top-level key | empty strings: P01 had 2 on 4 records, so at most 2 is the P01 level; `person_N`: P01 0 here, P00 28; speakers: P01 3/4; flags: P01 3/4 and 2/4; violations: 2 x P01's 4.5 allows for longer outputs; `confidence`: P01 2.5 per record |
| **G4 (tier 1, PRIMARY extraction gate)** | strict micro F1 at least 0.152 and recall at least 0.121 and precision at least 0.150 on all 8 | F1: best baseline as scored 0.102 + 0.05; recall: 0.071 + 0.05; precision: not more than 0.03 below the lower baseline 0.179. Baselines are depressed by failed records, so G4 alone is not sufficient |
| **G4b (tier 2, paired parsed-output)** | on the records parsed by both P02 and P01: P02 micro F1 at least P01 + 0.03 and recall at least P01 + 0.03; the same against P00 on the records parsed by both P02 and P00; fully-correct facts (audit) not below the comparator | Formula pre-registered; ids known after the run. If P02 parses all 8: vs P01 (4 ids) F1 >= 0.203, R >= 0.158; vs P00 (6 ids) F1 >= 0.153, R >= 0.124. The 0.03 margin is 2.5 times the extraction-only difference actually observed between P00 and P01 on 20 shared records (0.012) |
| **G5 targeted (need 3 of 5; tier 1 counts on all 8)** | (a) at least 10 fully-correct negative findings; (b) symptoms matched by key at least 5; (c) clinical actions matched by key at least 3; (d) planned medications matched at least 3 of 5; (e) 0 placeholder or medication-as-allergy entries | references 0 / 2 of 23 / 0 of 39 / 0-1 of 5 / 3 entries; thresholds are 20% of the 51 gold negatives, 2.5 times the symptom baseline, and the first non-zero values for actions and planned drugs |
| **G6 convention checks** (audit counts, completed outputs) | invented route = 0; placeholder or medication-as-allergy = 0; review-of-systems entries for systems not asked at most 1; 0 positive findings written as review-of-systems or `ongoing` for a resolved condition (manual audit of the transcripts' resolved items) | references: invented route 3 / 4, incorrect allergy 3 / 3, unsupported ROS 1 of 2 |
| **G3 evidence** (reported; **does not block the extraction outcome**; drives the separate P02-E decision) | mean evidence records per completed encounter at least 10; at least 70% exact single lines; 0 blobs; at least 95% of facts with valid ids and at least 40% with relevant cited text; at least 50% of citation pairs with correct `supports` and at least 70% of `supports` paths resolving reciprocally | references: 1.0 / 0-25% / 1-2 blobs / 80-98% valid but 8-27% relevant / 0% supports. Gold has about 35 evidence records per encounter (1,772 over 50 labels), all exact lines |
| Tier 3 | no gate | reported separately, INCOMPLETE, with missing keys; never counted as completed |

**Outcomes.** *Extraction outcome:* PASS if G1, G2, G4, G4b and G6 pass and at least three of five G5 items pass; PARTIAL if one or two of those groups fail (one targeted revision, one variable, may be proposed); FAIL otherwise. *Evidence outcome (separate):* PASS if G3 passes. **Evidence collapse trigger:** mean records per encounter below 3, or exact-line share below 30%, or whole-transcript blobs in two or more records: then I will recommend a separate decision on P02-E (evidence and schema constants moved out of the model's output and built deterministically). P02-E is not implemented and is not part of this plan. Stage B (the remaining 22 records) starts only if the pilot passes and you approve it separately.

**Stop rules during the pilot:** after the first three records stop and report if two or more hit the cap; stop on any memory error and report the exact error (without retries if D2 is approved) with no silent change of device, precision or settings. Evidence collapse alone does not stop the run (extraction data is still being collected).

## 7. Fair comparison procedure
- Same ids, same evaluator (`evaluate_run.py --subset-from-run`), same strict definitions, same transcript rendering; P02 outputs scored as they come.
- Report tier 1 first, tier 2 second, tier 3 last and separately, for P00, P01 and P02.
- Run the same audit code (`audit_p00_p01.py`, extended with a P02 column) so fully-correct / present-in-some-form / missed counts per category are directly comparable.
- Paired per-record table; on Stage B a paired bootstrap over records for the micro-F1 difference.
- Every result labelled development-only.

## 8. Runtime and memory (measured P00/P01 behaviour; estimates for P02)
**Hardware.** 15.81 GB RAM, Intel UHD 620 GPU that uses shared system RAM, Windows pagefile 8.6 GB (1.5 GB in use now). The model weights (3.44 GB FP16), the GPU working memory and the KV cache all count against system RAM, so only system-wide available memory is a valid measure.

**Where the measurement is taken today.** `ov_client_1_7b.py` reads `psutil.virtual_memory().available` **immediately before each `LLMPipeline(...)` is created** (after the previous record's pipeline was deleted and garbage-collected; stored as `system_available_mb_before`) and samples system-wide available RAM every 0.5 s during load and generation. **It is recorded only; no code compares it to a threshold.** The 7 GB gate in v2 of this plan was a proposal, not an existing check.

**What the 80 P00/P01 calls show (from `performance_*.json`)**
| | P00 (50 calls) | P01 (30 calls) |
|---|---|---|
| Available before each call (MB): min / median / max | 8,282 / 8,610 / 9,123 | 6,662 / 8,852 / 9,332 |
| **First call (cold start: kernel compile, load 42-44 s): drop** (available before minus lowest available during) | 6,811 MB (8,305 -> 1,494) | **6,608 MB (6,662 -> 54)** |
| Warm calls (load about 7 s): drop median / p90 / max | 5,227 / 5,694 / 6,049 MB | 5,361 / 5,662 / 6,334 MB |
| Lowest available during any call | 1,494 MB | **54 MB** (first call, started at 6.7 GB) |
| Peak system used | 14,701 MB | 16,141 MB (of about 16,190 MB) |

The drop grows only weakly with tokens (about 0.06-0.10 MB per input+output token), so P02's roughly +2,080 input tokens vs P01 add about 0.1-0.2 GB (KV alone: +227 MB).

**Is 7 GB achievable and sufficient?** *Achievable:* yes, right now (7.36 GB available with this session, VS Code and Chrome open; the last preflight read 7.48 GB). *Sufficient:* no margin. Expected lowest available RAM = available at start - drop - about 0.2 GB for P02's longer prompt:

| Available at start | Warm median | Warm worst observed | Cold start (cache not reusable) |
|---|---:|---:|---:|
| 7.0 GB | 1.4 GB | 0.5 GB | **about 0.0 GB** (P01 reached 54 MB from 6.7 GB) |
| **8.0 GB** | 2.4 GB | 1.5 GB | 1.0 GB |
| 8.6 GB (median seen before calls) | 3.0 GB | 2.1 GB | 1.6 GB |

The pilot should run warm: the P01 compile cache (`EXP_002_PROMPTING_INFERENCE/ov_cache`, 185 files) exists and is used by the same runner, but a cache miss would make the first record cold. When free RAM reaches 0 Windows pages to disk (P01 survived 54 MB, slowly); a real out-of-memory error is the failure to avoid.

**What the gate means if adopted.** *When:* one reading by me immediately before launch (read-only, no model loaded, apps closed), repeated inside the runner at the same point where `system_available_mb_before` is taken for the first record (later records are logged, not gated, because the pipeline freed between records returns its memory). *If not met:* the run does not start and no model is loaded; I report the available GB and the largest processes by name and memory, ask you to close them, and re-measure. **I will not lower the threshold or work around it.** *During the run:* the lowest available RAM is logged for every record; a dip alone does not stop the run (P01 completed at 54 MB); an actual out-of-memory error stops the run and is reported verbatim (with D2, without retries).

**Timing.** P02 v2.1 prompt = 4,170 tokens; input about 6,070 tokens for the pilot's average transcript (1,870 tokens) = about 160 s prefill (+55 s vs P01). Per pilot record: about 13.5-17 min if the output is compact (1,700-2,300 tokens), about 18 min if the model still indents (2,450 tokens), about 28 min at the cap. **Pilot total about 1.8-2.3 hours** (indented case about 2.4 h; every record at the cap 3.7 h). Stage B (22 records, after separate approval) about 5-6.5 h. No setting is changed to save time; prefix caching, structured decoding and a larger cap are not proposed.

## 9. Acceptance of P02 after Stage B (only if the pilot passes and you approve Stage B)
Accept as the new best 1.7B prompt only if, on the 30 shared ids: (1) tier-1 strict micro F1 at least P01 + 0.03 with a paired bootstrap interval that excludes 0; (2) tier-2 extraction-only difference at least +0.03; (3) truncated outputs at most 2 of 30 and invalid JSON at most 3 of 30; (4) no G1, G2, G6 regression; no category with 3 or more P01 matches falling to 0; (5) unsupported claims and incorrect allergy entries not above P01. Otherwise reject and record the measured reason. P03/P04 are recommended only if the P02 error analysis shows a remaining category-level opportunity.

## 10. Implementation steps after approval (none done)
1. You approve (or edit) the v2 text. I copy it to `prompt_versions/`, record the hash and freeze it with the same immutable manifest as P01.
2. After D1-D3: a reviewed change to `run_prompt.py` adding `--ids` (existing defaults unchanged), the RAM gate at the agreed threshold and `retries=0` for the pilot; freeze the eight-id file and the changed script hashes before inference; pre-flight as before (0.6B tree identical, frozen files unchanged).
3. Run the pilot; evaluate tiers 1-3 and the evidence/format measures with the unchanged evaluator; rerun the audit; write the gate report.
4. Stop and wait for review. No further stage without a decision.

## 11. What this plan does not do
It does not change the model, revision, device, precision, decoding, thinking setting, token limit or OpenVINO settings; it does not touch the validation set, the locked test set or sealed files; it does not modify P00, P01, any 0.6B artifact, the evaluator, the datasets or the frozen schema; it does not implement P02-E or any architectural change; it does not run P03/P04; it does not fine-tune; it does not start Stage B.
