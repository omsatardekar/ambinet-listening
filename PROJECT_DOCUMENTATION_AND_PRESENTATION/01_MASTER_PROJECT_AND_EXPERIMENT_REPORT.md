# 01 — Master project and experiment report

All results here are **development-only**: the gold labels are generator-derived (synthetic encounters, not human-verified, not clinical validation), and the 50 "prompt-dev" records were used to design prompts. Nothing here is independent validation. F1 is **not accuracy** (see `supporting/metric_definitions.md`).

Paths are relative to the repository root (`ambient_clinical_speech_transcription/`). `[1.7B]` = `direct_inference_1_7B/`, `[0.6B]` = `direct_inference_baseline/`, `[EXP2]` = `direct_inference_1_7B/experiments/EXP_002_PROMPTING_INFERENCE/`.

---

## 0. Read this first: three things that will confuse you if nobody warns you

1. **"P00 / P01 / P02" are not the same thing for the two models.** The 0.6B prompt study (EXP_004) already used the names P00–P05. The 1.7B track later re-used "P00/P01/P02" for *different* prompts. In this document: **0.6B-P0x** and **1.7B-P0x** are always written with the model prefix.
2. **"Direct inference" is not a one-line prompt.** The direct prompt (= 1.7B P00 = 0.6B P00, byte-identical, sha256 `78c5ab95…f604`) already contains the full 20-key JSON schema, allowed values and nine rules. "Minimal" here means "no extra guidance beyond schema + basic rules". Verified by `cmp` of `[1.7B]/prompts/P00_direct_inference_prompt.txt` and `[0.6B]/prompts/direct_extraction_prompt.txt`.
3. **"P02 v2.1" is not the P02 that was evaluated.** The v2.1 draft (model-written evidence, 4,164-token template) was only piloted on 3 records and stopped by its own early-stop rule (2 of 3 outputs hit the 4,096 cap). It is archived. The **evaluated 1.7B P02** is the later "strengthened P02" (sha256 `F6D5202F…09B0`, no model-written evidence). Sources: `[EXP2]/reports/P02_EXPERIMENT_PLAN.md`, `P02_PROMPT_DESIGN_AND_VALIDATION.md`, archived v2.1 under `archive/obsolete_experiments_after_P01/`.

---

## 1. Project and task in one paragraph

Ambient Clinical Listening records a doctor–patient consultation, transcribes it with speaker labels, and a small language model must turn the transcript into one structured JSON object (`clinical_extraction_schema.json`, 20 top-level keys: chief complaint, symptoms, negative findings, medical history, medications, allergies, vitals, examination, review of systems, conditions, assessment, investigations, actions, follow-up, uncertainties, evidence, quality checks, …). This documentation covers the **extraction stage with Qwen3 small models, run locally** on an i7-8665U laptop (15.8 GB RAM, Intel UHD 620 integrated GPU) — prompting only, **no fine-tuning has been done**.

Dataset: `dataset_v2_batch_001_corrected/` — Batch 001 = 500 synthetic encounters, frozen; split (`[0.6B]/evaluation/dataset_split.py`, seed 20260301) = 100 development / 400 locked test (locked test never used). The 100 dev were split again (seed 20260401) into 50 "prompt_dev" and 50 "validation" (`[0.6B]/experiments/…EXP_004…/experiments/split_v1.json`). Batch 002 (500 more synthetic encounters, ids 20001–20500) exists but is **not allocated** to train/dev/test and has had no inference.

---

## 2. Chronological journey

| # | Experiment | Model | What it was | Status |
|---|---|---|---|---|
| 1 | **0.6B EXP_001** CPU baseline | Qwen3-0.6B, HF Transformers, CPU FP32 | Direct prompt, 5 dev encounters (smoke test) | Completed (5 records only) |
| 2 | **0.6B EXP_002** | same weights → OpenVINO FP16 | Environment, device check, model conversion to OpenVINO IR, GPU feasibility, long-context test | Completed (infrastructure, no quality study) |
| 3 | **0.6B EXP_003** | Qwen3-0.6B OpenVINO FP16, iGPU | Same direct prompt, 5 → 100 dev encounters | Completed |
| 4 | **0.6B EXP_004** prompt engineering | same | 0.6B-P01 (structure rules), P02 (coverage rules), P03 (evidence), P04 (segment-id evidence), P05 (P02 + retrieval-based evidence), validation run of P05 | P01, P02 completed (50 ids); P03 **partial (35 of 50)**; P04 **smoke test only (5 ids)**; P05 validation completed (50 validation ids) |
| 5 | **0.6B EXP_005** S0 | none (no model) | Deterministic *repair* of stored outputs (nulls/enums) | Completed; structural only, **not an extraction gain** |
| 6 | **0.6B EXP_006** S1 | Qwen3-0.6B | Simplified compact schema, no evidence | Completed (50 ids) |
| 7 | **0.6B EXP_007** S1.1 | Qwen3-0.6B, cap 2048 | Phase A synthetic gates failed; Phase B arms B1/B2 run on 50 ids; neither accepted | Completed, **not accepted** |
| 8 | **1.7B setup** | Qwen3-1.7B rev `70d244cc…` | Download verified, converted to OpenVINO FP16, 7 smoke-test attempts to prove GPU use | Completed |
| 9 | **1.7B P00** (EXP_001_DIRECT_INFERENCE) | Qwen3-1.7B | Direct prompt on 50 dev ids | Completed (50) |
| 10 | **1.7B P01** (EXP_002) | Qwen3-1.7B | P00 + "structure rules" | **Partial: stopped by the owner at 30 of 50** |
| 11 | **1.7B P02 v2.1 / v2.2 pilots** | Qwen3-1.7B | Earlier improved-prompt drafts | **Aborted pilots** (3 and 6 records), archived, not results |
| 12 | **1.7B P02** (strengthened) | Qwen3-1.7B | P01 schema, no model-written evidence, extraction guide | Completed on the same 30 ids |
| — | Fine-tuning / LoRA | — | — | **Planned only. Not started.** |

Why the order: we first needed a working local pipeline (CPU → OpenVINO GPU, 3.7× faster on the same 5 records). Then, with the weakest possible *prompt-side* change, we asked whether instructions could lift a 0.6B model (small gains, mostly formatting/coverage). Then the same direct prompt was tried on a 4× bigger model (1.7B) to see how much was a **capacity** problem. Prompting then continued on 1.7B (P01, P02). Because scores remained low, the next step is fine-tuning (`04_…`).

---

## 3. What each experiment means (verified against the prompt files)

### 3.1 Direct inference (= P00)
**What the model gets** (`[1.7B]/prompts/P00_direct_inference_prompt.txt`, sha256 `78c5ab95…f604`): a role line ("You are a clinical information extraction system…"), return-only-JSON, **nine rules** (extract only what is stated, speaker role words, keep denials in negative_findings, temporality/certainty, disagreements → uncertainties, no diagnosis from possibility, action statuses, evidence_ids/clinical_evidence records, confidence null), an **Allowed values** block (enums), the **full output template**, then the transcript lines `[SEG0001] person_1 (DOCTOR) 0.80-3.28s: text`. No examples, no extraction checklists.
**Expectation / why baseline:** to measure what the model can do with only the schema and rules, so every later change is attributable. Greedy decoding, thinking off, one fresh pipeline per record.
**Results:** 0.6B: micro F1 0.0474 on the 50 prompt-dev ids and 0.049 on 100 dev encounters (EXP_003). 1.7B: 0.1528 on the 50 prompt-dev ids; 15 of 50 outputs hit the 4,096-token cap and were unparseable.

### 3.2 0.6B-P01 "schema-focused" (EXP_004)
Verified in `PROMPT_CHANGELOG.md`: P00 + one **Structure rules** block (7 rules, +352 tokens) before "Output format"; nothing else changed. Motivation: 0/94 outputs were schema-compliant; `clinical_assessment` written as an object in 94/94; roles as `DOCTOR`/`person_N`. Outcome: valid JSON 48 → 50 and micro F1 0.047 → 0.095, **but total schema violations rose 444 → 658 → REJECTED under the pre-registered rule.**

### 3.3 0.6B-P02 "comprehensive" (EXP_004)
P00 + one **Coverage rules** block (`prompts/P02_comprehensive_extraction.diff`): read the whole transcript, extract every item in every section, one item per finding, per-section lists (symptoms, negatives, history, meds, vitals, exam, ROS, conditions, assessment, investigations, actions, follow-up), and a terminology rule for normalised fields. Motivation: recall was 2.7%. Outcome: micro F1 0.047 → 0.121 (recall 0.026 → 0.082), schema violations 444 → 1,064; accepted **at development stage only** (8/8 pre-registered criteria). Its extraction was later re-run unchanged as part of the P05 validation (50 validation ids): micro F1 0.121, i.e. similar, not better.

### 3.4 0.6B-P03/P04/P05 (evidence work)
P03 (evidence-grounded) partial 35/50, rejected as designed (0% strict grounding). P04 (segment-id evidence) smoke test on 5 ids: 4/5 parsed, rejected. P05 = P02 extraction + **retrieval-based evidence built outside the model** (deterministic builder); validation run on 50 validation ids: 50/50 parsed, extraction F1 0.121 (TP 149, FP 553, FN 1612), 15/15 frozen gates passed, citation coverage 74.5%. Human review of evidence correctness: **pending (not done)**. Source: `[0.6B]/experiments/EXP_004…/reports/14_P05_validation_report.md`. This is where the idea "model extracts, backend attaches evidence" comes from.

### 3.5 0.6B S0, S1, S1.1
S0: pure repair of stored outputs (adds `null` for absent nullable fields): violations 1,064 → 346 with **identical TP/FP/FN** — not an extraction improvement (`EXP_005…/reports/S0_2_EVALUATION_REPORT.md`). S1: compact schema (20 compact keys, no evidence/confidence): F1 0.1207 → 0.1192 (no change), precision 0.227 → 0.279, output tokens −54%, but 13/50 outputs invalid JSON, speaker accuracy 0.088. S1.1: B1 F1 0.1610 but only 45/50 valid JSON; B2 speaker accuracy 0.953 but 31/50 valid; **neither accepted**. These changed the *output contract* and were not carried to 1.7B.

### 3.6 1.7B P00 → P01 → P02
**P00:** the direct prompt above.
**P01** (`[1.7B]/prompts/P01_schema_guided.txt`, sha256 `b51121cd…3ad8`): P00 + the same "Structure rules" idea as 0.6B-P01, **plus two extra lines** (compact JSON layout; symptoms.category must be an allowed value). Verified with `diff`: the only differences from P00 are the 11-line block. Motivation: reduce malformed/oversized output and enum errors. **Outcome (30 records):** valid JSON 23 → 25, truncations 7 → 4, F1 0.161 → 0.201 — but ~¾ of the gain was "more records finished", only ~¼ real extraction change; schema violations went *up* (504 → 614), `person_N` still written as role, 0 records fully schema-compliant, indentation ignored. Source: `[EXP2]/reports/P01_VS_P00_30RECORD_EVALUATION_REPORT.md`.
**P02** (`[EXP2]/prompt_versions/P02_p01_schema_no_evidence.txt`, sha256 `F6D5202F…09B0`, 4,645 template tokens vs P01's 2,087): keeps P01's template/enums/keys byte-for-byte, removes model-written evidence, and adds:
- **Core rules:** role from the bracket on each line; `person_1` is not always the patient; a doctor's question is not a finding; `clinical_evidence` is always `[]`; `evidence_ids` = segment ids (SEG0007) copied exactly.
- **Temporality block:** still present for any duration → present/current; gone during this illness → resolved/resolved; separate earlier episode → resolved/past; comes-and-goes → present/current + frequency.
- **Per-section "What to extract" rules:** symptoms (each separate), negatives (each denial separate, cue words), history (patient/family/surgical/social separate), medications (status rules; doctor-named ≠ currently used), allergies ("no known allergies" = negative finding), vitals (whole value, blood pressure as `"167/90"`, closed normalised names), exam, ROS, conditions vs assessment, investigations (type guide), actions (each instruction separate), follow-up (results-dependent stays as said), uncertainties.
- **14 invented example patterns** (verified absent from dev transcripts), a completeness check, an anti-hallucination paragraph.
Motivation: the P01 audit (`[EXP2]/reports/P02_STAGE1_AUDIT.md`) showed negatives, actions, exam and ROS near zero, speaker ids written as roles, and evidence blobs causing truncation. Source for the design: `P02_PROMPT_DESIGN_AND_VALIDATION.md`.

### 3.7 Progression in one line
Minimal instruction (schema + rules) → structure rules (format) → coverage rules (completeness; 0.6B) → comprehensive clinical extraction prompt with temporality, per-section rules and examples (1.7B P02). Each stage was introduced because the previous run showed a specific failure (§3.2–3.6); see "what we learned" in §8.

---

## 4. Evaluation set-up (so you can defend the numbers)

- **Evaluator:** frozen `[0.6B]/evaluation/entity_matching.py` (strict normalised-primary-key multiset matching), `evaluation_runner.py`, `attribute_metrics.py`, `clinical_metrics.py`, `evidence_evaluator.py`, `schema_validator.py`. Hashes recorded in `[1.7B]/manifests/FREEZE_P00_direct_dev50.json`. **18 evaluated categories** (chief_complaint, symptoms, negative_findings, 4 medical_history sub-categories, medications, allergies, vital_signs, physical_examination, review_of_systems, clinical_conditions, clinical_assessment, procedures_and_investigations, clinical_actions, follow_up, clinical_uncertainties).
- **Failed records count as zero predictions** (tier 1 / headline). A parsed-only view is shown next to it, never instead.
- The 1.7B comparison below uses the **same 30 ids** for P00, P01, P02 and the 0.6B systems (ids `00035 … 00266`, `[1.7B]/manifests/P02_30_IDS.json`, sha256 `224DF723…FA1`).
- **Check I performed for this document:** for P02 I recomputed micro P/R/F1 from the per-category TP/FP/FN in `[EXP2]/p02/derived/P02_ANALYSIS.json` (234/490/859 → P 0.3232, R 0.2141, F1 0.2576) and for every system the per-category gold counts (TP+FN) are identical across systems (sum 1,093). These match the reports.

---

## 5. Complete comparison

Different experiments use different record sets. **Only the five rows in table 5A are like-for-like.**

### 5A. Same 30 records (strict, tier 1: all 30 records, failures = zero predictions)

| System | TP | FP | FN | Micro P | Micro R | Micro F1 | Macro F1 | Valid JSON | Failed |
|---|---|---|---|---|---|---|---|---|---|
| 0.6B P00 (direct) | 27 | 97 | 1066 | 0.218 | 0.025 | 0.044 | 0.043 | 29/30 | 1 (invalid JSON) |
| 0.6B "P02" coverage (EXP_004) | 91 | 312 | 1002 | 0.226 | 0.083 | 0.122 | 0.128 | 30/30 | 0 |
| 1.7B P00 | 128 | 369 | 965 | 0.258 | 0.117 | 0.161 | 0.154 | 23/30 | 7 (all truncated) |
| 1.7B P01 | 170 | 431 | 923 | 0.283 | 0.156 | 0.201 | 0.180 | 25/30 | 5 (4 truncated, 1 invalid JSON) |
| **1.7B P02** | **234** | **490** | **859** | **0.323** | **0.214** | **0.258** | **0.209** | 28/30 | 2 (both truncated: `00060`, `00206`) |

Sources: 0.6B and 1.7B P00/P01 → `[EXP2]/evaluations/P01_schema_guided_dev50/subset30/METRICS.json`; P02 → `[EXP2]/p02/derived/P02_ANALYSIS.json` and `[EXP2]/reports/P02_VS_P01_METRICS.md`. Macro F1 = mean of the 18 category F1s (undefined precision excluded in the evaluator).

Parsed-only (tier 2): 1.7B P01 P 0.283 / R 0.189 / F1 0.226 (25 records); P02 P 0.323 / R 0.234 / F1 0.271 (28 records). Parsed-only sets differ in size, so they are not directly comparable either.

### 5B. Other record sets (not comparable with 5A)

| Experiment | Model | Records | Micro P / R / F1 | TP/FP/FN | Valid JSON | Notes |
|---|---|---|---|---|---|---|
| EXP_001 direct, CPU | 0.6B | 5 | 0.111 / 0.018 / 0.030 | 3/24/168 | 5/5 | schema compliance 0/5; 634 s/record |
| EXP_003 direct, GPU | 0.6B | 5 | 0.111 / 0.018 / 0.030 | 3/24/168 | 5/5 | identical to EXP_001 on the same 5; 173 s/record |
| EXP_003 direct, GPU | 0.6B | 100 dev | 0.257 / 0.027 / 0.049 | 98/284/3523 | 94/100 | 6 invalid JSON, 0 truncated |
| 0.6B P00 | 0.6B | 50 prompt_dev | 0.237 / 0.026 / 0.0474 | 49/158/1811 | 48/50 | |
| 0.6B P01 (REJECTED) | 0.6B | 50 prompt_dev | 0.242 / 0.059 / 0.095 | 110/345/1750 | 50/50 | violations 658 |
| 0.6B P02 coverage | 0.6B | 50 prompt_dev | 0.227 / 0.082 / 0.1207 | 153/522/1707 | 50/50 | dev-stage KEEP only |
| 0.6B P05 (P02 + external evidence) | 0.6B | 50 **validation** | 0.212 / 0.085 / 0.121 | 149/553/1612 | 50/50 | different record set; evidence human review pending |
| 0.6B S1 | 0.6B | 50 prompt_dev | 0.279 / 0.076 / 0.1192 | 141/364/1719 | 37/50 | compact schema |
| 0.6B S1.1 B1 / B2 (cap 2048) | 0.6B | 50 prompt_dev | B1 0.268/0.115/0.1610; B2 0.272/0.097/0.1427 | not recorded here | 45/50; 31/50 | neither accepted |
| 1.7B P00 | 1.7B | 50 prompt_dev | 0.271 / 0.106 / 0.1528 | 198/533/1662 | 35/50 | 15 truncated; 15.9 h |
| 1.7B P01 | 1.7B | 30 (of 50) | see 5A | | | stopped by owner; 50-record result does not exist |
| 1.7B P02 | 1.7B | 30 | see 5A | | | |
| 0.6B P03 | 0.6B | 35 partial | 0.225 / 0.031 / 0.055 | 40/138/1243 | 33/35 | not final |
| 0.6B P04 smoke | 0.6B | 5 | 0.225 / 0.055 / 0.089 | 9/31/154 | 4/5 | smoke only |

Sources: `[0.6B]/experiments/EXP_003…/final_dev100_report.md`, `EXP_004…/PROMPT_COMPARISON.md`, `…/14_P05_validation_report.md`, `EXP_006…/reports/S1_EXPERIMENT_REPORT.md`, `EXP_007…/reports/S1_1_PHASE_B_DECISION_REPORT.md`, `[1.7B]/experiments/EXP_001_DIRECT_INFERENCE/reports/P00_direct_dev50_EVALUATION.md`.

### 5C. Run settings, runtime, hardware

| Run | Device | Precision | max_new_tokens | Decoding | Runtime | Latency / record |
|---|---|---|---|---|---|---|
| 0.6B EXP_001 | CPU i7-8665U, HF Transformers | FP32 (BF16 weights upcast) | 6144 | greedy, thinking off | 5 × 634 s mean | 634 s |
| 0.6B EXP_003/004/006 | Intel UHD 620 iGPU, OpenVINO GenAI | FP16 IR | 6144 | greedy, thinking off | 100 records ≈ 4.3 h (154 s × 100, computed); P05 validation 3.47 h | 90–245 s |
| 0.6B EXP_007 | same | FP16 | **2048** | greedy | not summarised here | B1 90 s, B2 78 s |
| 1.7B P00 | iGPU, OpenVINO GenAI | FP16 IR | **4096** | greedy, thinking off | 57,118 s = 15.9 h (50 records) | mean 1,134 s |
| 1.7B P01 | same | FP16 | 4096 | same | 9.12 h inference sum (30 records) | mean 1,094 s, median 1,047 s |
| 1.7B P02 | same | FP16 | 4096 | same | 33,314 s = 9.25 h (30 records) | median ≈ 1,028 s |

Token budgets differ between the 0.6B (6,144) and the 1.7B (4,096) tracks — a disclosed difference. Temperature, top-p and top-k were **not applied** (greedy; recorded in `ov_client_1_7b.py::describe`).

### 5D. Input/output sizes and memory (1.7B)
| | P00 | P01 | P02 |
|---|---|---|---|
| Median input tokens | not in the table I verified | 4,126.5 | 6,684.5 |
| Median / max output tokens | – | 2,590 / 4,096 | 2,284 / 4,096 |
| Peak process RSS (max) | 7,091 MB (peak working set, P00 report) | 6,957 MB | 5,857 MB |
| Lowest system available RAM | not compared | 54 MB | 2,015 MB |
Source: `[EXP2]/reports/P02_VS_P01_METRICS.md`, `[1.7B]/experiments/EXP_001…/reports/P00_direct_dev50_EVALUATION.md`. RSS and "available RAM" are different measures; they are not directly comparable between rows or with the "peak system memory 16,141 MB" in the P01 report (system-wide used memory).

---

## 6. Category-wise performance (same 30 records)

Format: **TP/FP/FN (precision / recall / F1)** under strict matching; "gold" = number of gold facts in those 30 records. "–" = undefined (no predictions). Generated from the raw evaluation JSON (P00/P01/0.6B: `subset30/CATEGORY_METRICS.json`; P02: `P02_ANALYSIS.json`).

| Category | gold | 0.6B-P00(direct) TP/FP/FN (P / R / F1) | 0.6B-EXP004-P02(coverage) TP/FP/FN (P / R / F1) | 1.7B-P00 TP/FP/FN (P / R / F1) | 1.7B-P01 TP/FP/FN (P / R / F1) | 1.7B-P02 TP/FP/FN (P / R / F1) |
|---|---|---|---|---|---|---|
| chief_complaint | 30 | 1/28/29 (0.034 / 0.033 / 0.034) | 6/24/24 (0.200 / 0.200 / 0.200) | 3/20/27 (0.130 / 0.100 / 0.113) | 2/23/28 (0.080 / 0.067 / 0.073) | 4/24/26 (0.143 / 0.133 / 0.138) |
| symptoms | 91 | 5/35/86 (0.125 / 0.055 / 0.076) | 5/27/86 (0.156 / 0.055 / 0.081) | 8/25/83 (0.242 / 0.088 / 0.129) | 12/24/79 (0.333 / 0.132 / 0.189) | 10/30/81 (0.250 / 0.110 / 0.153) |
| negative_findings | 168 | 0/5/168 (0.000 / 0.000 / 0.000) | 0/30/168 (0.000 / 0.000 / 0.000) | 2/22/166 (0.083 / 0.012 / 0.021) | 4/36/164 (0.100 / 0.024 / 0.038) | 1/50/167 (0.020 / 0.006 / 0.009) |
| medical_history.past_medical_history | 50 | 0/3/50 (0.000 / 0.000 / 0.000) | 1/12/49 (0.077 / 0.020 / 0.032) | 5/24/45 (0.172 / 0.100 / 0.127) | 6/27/44 (0.182 / 0.120 / 0.145) | 6/33/44 (0.154 / 0.120 / 0.135) |
| medical_history.surgical_history | 16 | 1/5/15 (0.167 / 0.062 / 0.091) | 2/11/14 (0.154 / 0.125 / 0.138) | 2/18/14 (0.100 / 0.125 / 0.111) | 2/20/14 (0.091 / 0.125 / 0.105) | 2/18/14 (0.100 / 0.125 / 0.111) |
| medical_history.family_history | 17 | 0/1/17 (0.000 / 0.000 / 0.000) | 4/6/13 (0.400 / 0.235 / 0.296) | 5/9/12 (0.357 / 0.294 / 0.323) | 6/14/11 (0.300 / 0.353 / 0.324) | 5/22/12 (0.185 / 0.294 / 0.227) |
| medical_history.social_history | 88 | 0/1/88 (0.000 / 0.000 / 0.000) | 0/10/88 (0.000 / 0.000 / 0.000) | 4/11/84 (0.267 / 0.045 / 0.078) | 13/16/75 (0.448 / 0.148 / 0.222) | 24/2/64 (0.923 / 0.273 / 0.421) |
| medications | 72 | 17/2/55 (0.895 / 0.236 / 0.374) | 28/4/44 (0.875 / 0.389 / 0.538) | 30/8/42 (0.789 / 0.417 / 0.545) | 37/7/35 (0.841 / 0.514 / 0.638) | 42/9/30 (0.824 / 0.583 / 0.683) |
| allergies | 13 | 2/7/11 (0.222 / 0.154 / 0.182) | 4/16/9 (0.200 / 0.308 / 0.242) | 3/15/10 (0.167 / 0.231 / 0.194) | 3/18/10 (0.143 / 0.231 / 0.176) | 4/25/9 (0.138 / 0.308 / 0.190) |
| vital_signs | 129 | 1/2/128 (0.333 / 0.008 / 0.015) | 24/28/105 (0.462 / 0.186 / 0.265) | 39/31/90 (0.557 / 0.302 / 0.392) | 51/40/78 (0.560 / 0.395 / 0.464) | 99/20/30 (0.832 / 0.767 / 0.798) |
| physical_examination | 46 | 0/5/46 (0.000 / 0.000 / 0.000) | 0/38/46 (0.000 / 0.000 / 0.000) | 0/28/46 (0.000 / 0.000 / 0.000) | 0/39/46 (0.000 / 0.000 / 0.000) | 0/36/46 (0.000 / 0.000 / 0.000) |
| review_of_systems | 40 | 0/0/40 (– / 0.000 / 0.000) | 3/22/37 (0.120 / 0.075 / 0.092) | 0/16/40 (0.000 / 0.000 / 0.000) | 0/21/40 (0.000 / 0.000 / 0.000) | 0/27/40 (0.000 / 0.000 / 0.000) |
| clinical_conditions | 20 | 0/1/20 (0.000 / 0.000 / 0.000) | 0/26/20 (0.000 / 0.000 / 0.000) | 0/25/20 (0.000 / 0.000 / 0.000) | 0/29/20 (0.000 / 0.000 / 0.000) | 0/29/20 (0.000 / 0.000 / 0.000) |
| clinical_assessment | 48 | 0/0/48 (– / 0.000 / 0.000) | 6/8/42 (0.429 / 0.125 / 0.194) | 15/8/33 (0.652 / 0.312 / 0.423) | 17/8/31 (0.680 / 0.354 / 0.466) | 20/19/28 (0.513 / 0.417 / 0.460) |
| procedures_and_investigations | 49 | 0/1/49 (0.000 / 0.000 / 0.000) | 8/15/41 (0.348 / 0.163 / 0.222) | 11/23/38 (0.324 / 0.224 / 0.265) | 15/23/34 (0.395 / 0.306 / 0.345) | 13/26/36 (0.333 / 0.265 / 0.295) |
| clinical_actions | 165 | 0/1/165 (0.000 / 0.000 / 0.000) | 0/23/165 (0.000 / 0.000 / 0.000) | 0/37/165 (0.000 / 0.000 / 0.000) | 1/41/164 (0.024 / 0.006 / 0.010) | 0/68/165 (0.000 / 0.000 / 0.000) |
| follow_up | 26 | 0/0/26 (– / 0.000 / 0.000) | 0/12/26 (0.000 / 0.000 / 0.000) | 1/19/25 (0.050 / 0.038 / 0.043) | 1/22/25 (0.043 / 0.038 / 0.041) | 2/26/24 (0.071 / 0.077 / 0.074) |
| clinical_uncertainties | 25 | 0/0/25 (– / 0.000 / 0.000) | 0/0/25 (– / 0.000 / 0.000) | 0/30/25 (0.000 / 0.000 / 0.000) | 0/23/25 (0.000 / 0.000 / 0.000) | 2/26/23 (0.071 / 0.080 / 0.075) |

**Categories that exist in the schema but are not scored as entity categories:** `clinical_evidence` and `quality_checks` are not in the 18 entity categories; speaker attribution and evidence grounding are separate metrics (§7). "Clinical observations" is not a schema category — physical examination findings and clinical assessment are the closest, and they are reported above. I did not invent any other category.

---

## 7. Speaker attribution and evidence (separate from entity F1)

| Metric | 1.7B P00 (30) | 1.7B P01 (30) | 1.7B P02 (30) |
|---|---|---|---|
| Speaker attribution | accuracy 0.603 (70/116) | accuracy 0.674 (97/144) | 207 correct of 230 matched facts (see note) |
| Speaker id written where a role belongs | – | 45 (on 168 matched pairs) | 0 |
| Evidence references | P00 grounding strict 0.006 | strict grounding 0.018, partial 0.180 (601 predicted) | 1,240 segment ids; 1,223 valid (98.6%); 17 invalid |
| Facts without evidence ids | – | – | 123 |
| Evidence records built by backend backfill | – | – | 487 (model's original output untouched) |

**Caution on speaker numbers:** the P01 evaluator figure (97/144 = 0.674) uses the evaluator's definition (excludes records with unknown speakers/unreliable roles); the "101 of 168" for P01 and "207 of 230" for P02 come from my analysis script `p02/code/analyse_run.py` on *matched facts* with a different denominator. They are not the same metric and must not be mixed in one sentence. The 0.6B systems' speaker accuracy on the same 30: P00 0.333 (8/24), coverage prompt 0.377.
**Caution on evidence:** "valid" evidence ids (a segment id that exists in the transcript) does not mean the evidence supports the fact. P01's evidence block had 424/424 *existing* references but only 1.8% strict grounding. P02's 98.6% is "id exists", not "id is correct for the fact". Whether P02's ids are the *right* segments was **not measured**.

---

## 8. Detailed 1.7B P01 vs P02 (verified)

| Metric | P01 | P02 | Verified? |
|---|---:|---:|---|
| Precision | 0.283 | 0.323 | yes (recomputed from per-category TP/FP) |
| Recall | 0.156 | 0.214 | yes |
| F1 | 0.201 | 0.258 | yes |
| TP / FP / FN | 170 / 431 / 923 | 234 / 490 / 859 | yes |
| Parsed / failed | 25 / 5 | 28 / 2 | yes (`outputs/parsed/P02` 28 files, `failed/P02` 2 files) |
| Parsed-only F1 | 0.226 | 0.271 | per report |
| Runtime | 9.12 h | 9.25 h (wall 33,314 s) | yes (`logs/P02_STOP_RULE_RESULT.json`) |

P02 failed `00060` and `00206`, both `truncated` at 4,096 tokens (log lines in `inference_P02.log`). P01 failed 5 (4 truncated, 1 invalid JSON).

**What improved (F1, P01 → P02):** vital signs 0.464 → 0.798 (TP 51 → 99), social history 0.222 → 0.421 (TP 13 → 24), medications 0.638 → 0.683 (TP 37 → 42), chief complaint 0.073 → 0.138, clinical assessment 0.466 → 0.460 (TP 17 → 20, precision down), follow-up 0.041 → 0.074, uncertainties 0 → 0.075.
**What got worse or stayed flat:** negative findings (4 correct → 1 correct; 51 predicted), clinical actions (1 → 0 correct; 68 predicted vs 165 gold), symptoms 12 → 10 TP, procedures 15 → 13 TP, family history precision 0.300 → 0.185; the fuzzy follow-up recall fell 0.269 → 0.077.
**Still zero:** physical examination, review of systems, clinical conditions.
**Plain-language reading:** the longer, rule-heavy prompt made the model copy the right *kind* of facts for measurements, social history and medicines and fixed the "person_1 as a role" slip, but did not help it find denials, instructions or examination findings. About 79% of gold facts are still missed (859/1,093 = 78.6%).

**Limitations (must be said out loud):**
1. Vital-sign names, social-history categories and statuses, ROS system names, the blood-pressure string and the duration object were taken from the **dev gold conventions** — part of the vitals/social gain is terminology matching, not new medical understanding.
2. One greedy run on 30 records: no repeats, no confidence intervals. Differences of a few TP in small categories are noise.
3. Strict matching on free-text keys (`clinical_actions`: `action_type|description`; `follow_up`: `type|time_reference`) scores a correct paraphrase as miss + false positive, so actions/follow-up under-state semantic correctness. The fuzzy diagnostic is a non-official view.
4. 352 of P01's 431 FPs were transcript-supported (P01 report §7): precision is *under*-stated; this was not recomputed for P02.
5. The same 30 ids were used to design P02 (the dev data), so this is not independent validation.

---

## 9. Overall extraction performance: what the numbers mean

| Quantity | Meaning here | Available? |
|---|---|---|
| Micro P/R/F1 | all TP/FP/FN pooled across 18 categories and all records (large categories dominate) | yes, all runs |
| Macro F1 | mean of the 18 category F1s | yes, recomputed for P02 = 0.2095 |
| JSON validity | output parses as JSON | yes |
| Schema compliance | zero violations against the frozen schema | yes for 0.6B runs and 1.7B P00/P01 (0 compliant records everywhere); **not measured for P02** |
| Record-level success rate | parsed / attempted | yes (28/30 = 93.3%) |
| Exact/strict fact matching | normalised primary-key equality | yes — this is the headline |

Four different qualities, never to be merged: **extraction quality** (P/R/F1), **output-format quality** (validity, schema), **evidence-grounding quality**, **record-completion reliability** (failures/truncation).

**"Accuracy" is not available.** Record-level or field-level accuracy was never computed, because the evaluator is a fact-set matcher (no true negatives, variable number of facts per record). Do not quote a percentage as "accuracy". See `04_…` §6 and `supporting/metric_definitions.md`.

---

## 10. What we learned (honest)
1. Capacity matters: with the *same* prompt, 1.7B scores about 3× the F1 of 0.6B (0.161 vs 0.044 on the same 30; 0.153 vs 0.047 on 50) — but loses reliability (15/50 truncated vs 0/50).
2. Prompt rules move *surface conventions* easily (vitals, social, speaker role) and *reasoning-heavy* categories hardly at all (negatives, actions, exam, ROS, conditions).
3. A big share of earlier "gains" was completion/format, not extraction (P01: ~¾ of the TP gain).
4. Output budget is a real constraint: 2 of 30 P02 records still hit 4,096 tokens.
5. Strict matching + a frozen schema with free-text keys caps what any prompt can score in actions/follow-up.
6. Prompts are near their limit for this model; the proposed next step is fine-tuning (`04_…`). Fine-tuning may or may not lift these categories; it is not guaranteed.

---

## 11. Inconsistencies and gaps found in existing material
- Name collision of P00–P05 between 0.6B and 1.7B (see §0).
- `[0.6B]/experiments/EXP_004…/README.md` still says "Status: SETUP ONLY. No inference has been run", although P01–P05 were run (stale README).
- `manifests/P02_30_IDS.json` `purpose` text still says "P02 v3" (left to keep the bytes identical).
- The user-facing description "P02 v2.1" does not match the evaluated prompt (see §0.3).
- Token budget differs: 0.6B 6,144 (EXP_007: 2,048) vs 1.7B 4,096.
- The P01 30-record report compares against "0.6B P02" which is the 0.6B dev-stage KEEP prompt (not validated).
- 1.7B P01 was stopped at 30/50 and its own end-of-run audit file was not written (disclosed in the P01 report); `scripts/evaluate_run.py` hash differs from the P01 freeze because a subset option was added afterwards.
- No record-level 1.7B P00 numbers exist with *input* tokens in the table I verified for P01/P02 comparison (P00 mean input 3,791 tokens in the 50-record report).
- "Peak memory" is reported with different definitions in different reports (system used, process RSS, working set).
- Not found: a written statement of *why* the project chose Qwen3-0.6B or *why* it moved to 1.7B beyond what is quoted in `02_…`.

---

## 12. Added metric: overall fact-level accuracy (same 30 records, strict, failures = zero predictions)
Fact-level accuracy = TP / (TP + FP + FN) (definition in `supporting/metric_definitions.md`). It is not F1 and not record-level accuracy.

| System | TP | FP | FN | Fact-level accuracy |
|---|---|---|---|---|
| 0.6B P00 | 27 | 97 | 1066 | 2.3% |
| 0.6B coverage prompt | 91 | 312 | 1002 | 6.5% |
| 1.7B P00 | 128 | 369 | 965 | 8.8% |
| 1.7B P01 | 170 | 431 | 923 | 11.2% |
| **1.7B P02** | **234** | **490** | **859** | **14.8%** |

Other experiments (different record sets, not comparable) are in the CSV column `fact_level_accuracy_tp_over_tp_fp_fn`: 0.6B direct 100 dev 2.5%; 0.6B P01 5.0%, P02 coverage 6.4% (50 dev); P05 validation 6.4%; S1 6.3%; 1.7B P00 50 ids 8.3%. Meaning: of every 100 facts that are either expected or output, about 15 are correct for P02.
