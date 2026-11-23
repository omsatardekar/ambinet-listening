# P05 final architecture document (frozen configuration; validation NOT yet authorised)

Written for: you, for approval of the freeze, the integrated guard and the validation protocol. **No inference or GPU job has started.** P00-P04, the frozen dataset, labels, schema and evaluator are unmodified. P02's prompt and outputs are unmodified.

## 1. Approved architecture (D1)
1. Qwen3-0.6B (pinned snapshot c1899de2, OpenVINO FP16, GPU, greedy, thinking off, 6144 tokens) performs comprehensive extraction with the **frozen P02 prompt** (sha256 `cf50ce8efe850cda76fe6eadebf45391fa0461a657e52de5783edb31ccdde5d1`).
2. Python retrieves candidate transcript segments for each extracted fact (`p05_retrieval.py`, R_cons v4).
3. Conservative rules accept or reject candidates; 4. the system abstains when evidence is insufficient or ambiguous (reason codes recorded).
5. The existing evidence builder (`evidence_builder.py`) creates the final evidence records and `supports` paths.
6. The frozen schema, evaluator and the extraction outputs are unchanged (asserted per record: `verify_only_evidence_changed`).
P02 stays the extraction baseline. R_cons v4 is the preferred retrieval candidate **provisionally**; its results are development results.

## 2. Distinctions kept separate in every report (D1)
1. **Citation coverage**: cited facts / extracted facts.
2. **Agreement with gold-cited segments when cited**, with the denominator (strictly matched facts that have a gold citation) and matched coverage.
3. **Agreement counting abstentions as misses.**
4. **Semantic correctness from human review** (45-fact feasibility audit; not computed by the evaluator).
5. **Correctness of the underlying extracted fact** (extraction precision/recall/F1; share of cited facts whose fact strictly matches gold).
None of these is clinical accuracy. Gold-segment agreement is a proxy that exists only for matched facts; lexical grounding from the existing evaluator is circular for a retrieval method and is reported with that warning.

## 3. Frozen configuration and hashes (D4 items 1-6)
Freeze manifest: `P05_FREEZE_MANIFEST.json`, **SHA-256 `e383d3a352a6e431bc74c49c8c409d15a6e02831b05ee73e47aec472fd56fae0`** (files set read-only; the runner re-checks every hash at start-up and aborts on any difference).
| Component | SHA-256 |
|---|---|
| **R_cons v4 source** `experiments/p05_retrieval.py` | `49a581ae81a8a277d4b3005f44572355f8eadf4e1b803682d06f040c545a1815` |
| **R_cons v4 configuration** `experiments/p05_config.json` (every constant, lexicon and rule switch; the runner re-derives it from the live module and aborts if it differs) | `96beb989f50f7d68f14ceca35b409e26bc9ad41a6600d4febab2fa11d07df6bf` |
| **P02 prompt** `prompts/P02_comprehensive_extraction.txt` | `cf50ce8efe850cda76fe6eadebf45391fa0461a657e52de5783edb31ccdde5d1` |
| **Evidence builder** `experiments/evidence_builder.py` | `ffd6189e3d93c482c0621c090932167e388e19bd0cca3c568a5df2ced1858525` |
| Pipeline (stages 2-4) `experiments/p05_pipeline.py` | `9eccd1c9c8fc453fbb5be87233c5007238f5e272f927a5012255adf1d40f2902` |
| **Evaluator (combined hash of the 11 files below)** | `7558837a15b0d0b3dc043c3193fd2b197943d8d48ab10fbb43986ec2815126e2` |
| Schema: root `clinical_extraction_schema.json` | `00a9a1d2102d9e23507c53237cd5747c0d1f0a7a2aba07b2863d0aa2b8c6abba` |
| Schema: final label schema | `1c4b7e7d27c022ee40869256378155cb99d98b0664144f2cb0e081a367cf19db` |
| Validation gates `experiments/P05_validation_gates.json` | `693b32e65b53198c3c18f7a9f85578707c843a926a82e06ea04b90792ee49e2a` |
**Evaluator files** (unchanged; compared byte for byte with the EXP_001 code snapshot):
| File | SHA-256 (prefix) | identical to EXP_001 snapshot |
|---|---|---|
| `config/settings.py` | `b19bc940aa5048d2...` | True |
| `evaluation/__init__.py` | `e3b0c44298fc1c14...` | True |
| `evaluation/attribute_metrics.py` | `c26c6bfc4630d432...` | True |
| `evaluation/clinical_metrics.py` | `d57f870e9e1b7628...` | True |
| `evaluation/dataset_split.py` | `489186f8fc33a58b...` | True |
| `evaluation/entity_matching.py` | `8f7f59bc66db7a43...` | True |
| `evaluation/evaluation_runner.py` | `114d09b10897c364...` | True |
| `evaluation/evidence_evaluator.py` | `381eee0061569592...` | True |
| `evaluation/schema_validator.py` | `34ec069f4442e2ac...` | True |
| `inference/inference_runner.py` | `7f6d8d1029fe3bbd...` | True |
| `inference/output_parser.py` | `418d70bd84af6f91...` | True |
**All frozen files**
| File | SHA-256 |
|---|---|
| `dev_safeguards/dev_checksums.sha256` | `8c309ad58d2f5844d13e69da755ec33ca723f2166b72a720335d886729cd8d96` |
| `dev_safeguards/dev_manifest.csv` | `591de9bd0abcfce1f029f6e79c837a9101a04bc8bd2069db5a72cbfa83c9d3b4` |
| `experiments/P05_validation_gates.json` | `693b32e65b53198c3c18f7a9f85578707c843a926a82e06ea04b90792ee49e2a` |
| `experiments/audit_sampler.py` | `d361f0e0df901084e07769cc8b9a770d84cb7a3ec3f538e38121b71dc4cc5292` |
| `experiments/audit_score.py` | `6f6b9fb057572a39382c790cbade780d40a93fb48e0f3f820dd83f5423ba5a22` |
| `experiments/common.py` | `0f99f453a2d12999f56d841627c58a86eb490a06fbf589f705283e1595ffe966` |
| `experiments/dev_guard.py` | `93560eb2c96609ab7d563fcbf66a02ceb680ad904406ce99a024ed4673f3b6ab` |
| `experiments/evaluate_p05.py` | `55a7aafc1581d9e01156b53ba768a39cd8295d920a1add07b6ea3d7d22635454` |
| `experiments/evidence_builder.py` | `ffd6189e3d93c482c0621c090932167e388e19bd0cca3c568a5df2ced1858525` |
| `experiments/make_p05_config.py` | `59b95573d940a480fb756a27330b8b4722e3855c25bb52f5eb3d31c534d5ac60` |
| `experiments/ov_client.py` | `b6442dc0d488db5483b2b964383abb282225b9083fe890bcf1146887ee4f1256` |
| `experiments/p05_config.json` | `96beb989f50f7d68f14ceca35b409e26bc9ad41a6600d4febab2fa11d07df6bf` |
| `experiments/p05_eval_lib.py` | `97d9001f3e4f48022d1788d37b91e21af4411e288db1770cb66ca7bf858a3a17` |
| `experiments/p05_pipeline.py` | `9eccd1c9c8fc453fbb5be87233c5007238f5e272f927a5012255adf1d40f2902` |
| `experiments/p05_retrieval.py` | `49a581ae81a8a277d4b3005f44572355f8eadf4e1b803682d06f040c545a1815` |
| `experiments/record_authorization.py` | `2ee57581c009d44c8505073e8db67110e8823350cb6a6df4e0c70c0aeb8122f1` |
| `experiments/run_p05_validation.py` | `304b7d79e3b81aea627a7d4e8d145078d5664c563e0a2a85f65c35fe932ee8eb` |
| `experiments/split_v1.json` | `b23fccfba02085ca9df42ed7edb8fe10a90f9086a40c31b7162dd8329b87cf94` |
| `experiments/test_dev_guard.py` | `63d4fbfb48e7b9e5c184921987d8843087d6aebc6ed4d062301207d5eb22dd3b` |
| `experiments/test_evidence_builder.py` | `9fa86d8d294964f1b52d83336847e7411ce25a3e11109170b562a7f2e12dda51` |
| `experiments/test_strict_spy.py` | `4f7c19c9ba734d993f0217b955f32b8563340f87653c4edb83f7a532bb58076c` |
| `prompts/P02_comprehensive_extraction.txt` | `cf50ce8efe850cda76fe6eadebf45391fa0461a657e52de5783edb31ccdde5d1` |
**Final-schema mapping (frozen):** exactly as in `reports/07_P04_architecture_and_design_v2.md` section 6 (the mapping code is `evidence_builder.py`, hashed above): `item.evidence_ids` = EV ids in segment order; one `clinical_evidence` record per distinct cited segment with exact transcript text, speaker id, lower-case role, floor-second MM:SS times and `supports` paths (`section[index]`, `medical_history.sub[index]`, `chief_complaint`); an abstained fact keeps `evidence_ids: []`. All other fields pass through untouched. Round trip on the 100 development gold labels: 3,516/3,516 evidence records reproduced exactly.
**Model/runtime pinned (checked at start-up):** Qwen/Qwen3-0.6B revision c1899de289a04d12100db370d81485cdf75e47ca; OpenVINO FP16 files compared with the EXP_002 conversion record (hashes in the manifest); settings compared with the P02 run manifest.

## 4. The four post-hoc retrieval revisions (all made on prompt_dev; none tested on held-out data)
| Version | Change | Why |
|---|---|---|
| v1 | as first written and fixed before results (steps: specificity, question->answer, speaker class, polarity, kinship, vital value, ambiguity) | pre-registered |
| v2 (post-hoc) | polarity made item-aware: facts that are themselves absences (status absent/negative/never/none, or a negation word in their wording) outside negative findings get no polarity constraint | v1's polarity rule cost 5.5 points of coverage on gold facts in sections that legitimately hold negatives (social history, examination, assessment, review of systems) |
| v3 (post-hoc) | negative findings need a negation cue next to their anchor (or a negative short reply), not anywhere in the segment | the review sample showed a symptom filed as a negative finding passing because of a neighbouring clause |
| v4 (post-hoc) | the preceding question is added to a short reply (<= 10 words) that cannot be read without it | the sample showed a bare 'No, none of that at all.' cited without its question |
Results of each version are in `p05_diagnostics/p05_ladder_results.json` (v1-v4 rows) and `reports/09_P05_architecture_and_diagnostics.md`. Parameter sensitivity (TAU 0.5/0.6/0.7, short reply 10/25 words) changed hit-when-cited by < 0.4 points and coverage by < 3.7 points; parameters stay at their a-priori values. **No further tuning on the validation subset.**

## 5. Known limitations and residual error rates (development results; prompt_dev, 50 records)
* Agreement on the 153 P02 facts that strictly match a gold item: cited 93.5%; hit when cited 98.6%; hit with abstentions as misses 92.2% (R_simple 88.9%). On 1,860 gold facts used as queries: cited 79.4%, hit when cited 99.2%.
* Coverage on all 679 P02 facts: 72.6% cited; abstained 186 (27.4%); reasons {"ok": 493, "no_candidate": 50, "speaker_class_mismatch": 45, "ambiguous_many_equal_matches": 33, "value_not_in_evidence": 1, "polarity_conflict": 38, "no_anchor_words": 13, "kinship_conflict": 6}.
* Residual detector flags among cited facts: greeting-like 2.1% and polarity 1.4% (matched P02 facts); 0.4% and 0.2% (gold facts); question-only, SEG0001, kinship and speaker-class cases 0%.
* Only 143 of 493 cited facts strictly match a gold fact: P02's extraction precision is 22.7%, so most cited facts are not confirmed by the labels; citing a fact is not evidence that the fact is right.
* Qualitative read of 36 cited items (mine, not independent): 30 appropriate, 3 questionable, 3 wrong; the errors are mostly spurious extracted items that received a plausible citation, one negation-window slip, and one context question that did not concern its item.
* Lexically unreachable categories (review of systems 20%, clinical uncertainties 16%, clinical actions 37% reachable): D2 - they abstain; an empty reference is preferred to a wrong one. No semantic matcher is part of P05.
* Other known failures: lexical collisions (a follow-up "in three days" cited to a medication duration), repeated mentions (the retriever may cite the later summary where gold cites the history exchange), unspoken standard terms, neighbouring-clause negation, context questions not checked for relevance, single-segment bias (set recall 60.0% on gold facts), facts in object-typed sections skipped by the structure walk.
* The rules were calibrated and revised on prompt_dev; the numbers will probably fall on new data.
