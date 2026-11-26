# Batch 002 allocation PROPOSAL (not executed)

Status: proposal only, awaiting owner approval. Nothing reads or enforces this split; no Batch 002 data file was modified (they are read-only and their checksums still verify). Seed 20261115; reproduce with `python -B scripts/b2_allocation_proposal.py`. Files: `allocation_proposal.csv` (id, split, specialty, tier, complexity, profile, quality flags, needs_review), `allocation_proposal.json` (all id lists, cell counts, measurements).

> **Update (owner decision):** Option A and Option B are both retained as separately documented strategies and neither is executed: see `OPTION_A_stratified.md` and `OPTION_B_profile_disjoint.md` (Option B discloses its 52% verbatim segment overlap and is not a clean generalisation test). The 41 flagged training candidates are retained with their flags: see `FLAGGED_TRAINING_CANDIDATES_REVIEW.md`. Batch 003 is for planning only: `BATCH_003_PLANNING.md`.

## Method

Stratified by specialty x difficulty tier (36 cells: 12 specialties x Simple/Medium/Hard). Within each cell ids are sorted and shuffled with `random.Random(20261115)`; development and holdout quotas per cell come from cumulative error diffusion (`round(50 x cumulative_n / 500)`), so the totals are exactly 400 / 50 / 50 and every cell is close to 80/10/10. Generator complexity (moderate / complex / challenging) is reported but is not a stratification key.

## Resulting counts

| Specialty | Training candidates | Development | Internal holdout |
|---|---:|---:|---:|
| General Medicine / Primary Care | 38 | 6 | 6 |
| Cardiology | 37 | 4 | 4 |
| Respiratory Medicine | 37 | 4 | 4 |
| Gastroenterology | 37 | 4 | 4 |
| Endocrinology | 37 | 4 | 4 |
| Neurology | 37 | 4 | 4 |
| Musculoskeletal / Orthopaedics | 32 | 4 | 4 |
| Dermatology | 32 | 4 | 4 |
| Gynaecology | 32 | 4 | 4 |
| ENT / Ophthalmology | 22 | 4 | 4 |
| Infectious Diseases | 32 | 4 | 4 |
| Urgent Care / Other | 27 | 4 | 4 |
| **Total** | **400** | **50** | **50** |

| Tier | Training | Development | Holdout |
|---|---:|---:|---:|
| Simple | 118 | 16 | 16 |
| Medium | 179 | 23 | 23 |
| Hard | 103 | 11 | 11 |

| Generator complexity | Training | Development | Holdout |
|---|---:|---:|---:|
| simple | 118 | 16 | 16 |
| moderate | 179 | 23 | 23 |
| complex | 60 | 8 | 7 |
| challenging | 43 | 3 | 4 |

With 36 cells and 50 records each, 3 cells have no development record and 3 have no holdout record (small cells); every specialty has at least 4 records in each of development and holdout.

## Leakage and similarity (measured on the proposal)

| | Development | Internal holdout |
|---|---:|---:|
| Max 5-gram Jaccard to any training candidate | 0.111 | 0.104 |
| Share of segments (>=5 words) verbatim in training candidates | 56% | 56% |
| Records whose scenario profile also occurs in training | 50/50 | 50/50 |
| Distinct profiles | 35 | 36 |

**Consequence:** with the requested stratification every holdout record shares its scenario profile with at least 3 training records, and about 56% of its long segments occur verbatim in the training set (the same dialogue engine's routine questions). The holdout therefore measures in-distribution extraction on new samples of known scenarios, not generalisation to unseen clinical scenarios, and must not be used to claim generalisation.

## Alternative B for comparison (also not executed): profile-disjoint holdout and development

Whole scenario profiles are held out (seed 20261116, one profile per specialty round-robin): holdout = 6 profiles / 51 records (b2_diabetic_foot_ulcer, b2_palpitations_paroxysmal, b2_rectal_bleeding_haemorrhoids, b2_shingles_early, b2_sudden_hearing_loss, b2_unintentional_weight_loss); development = 6 profiles / 51 records; training = 398 records. Holdout profile overlap with training: 0. Verbatim segment overlap with training is still 52% (shared routine wording), so scaffolding leakage remains in both options. B is not stratified by specialty (the holdout covers 6 of 12 specialties) and sizes are approximate. Id lists: `allocation_proposal.json`, key `alternative_B_profile_disjoint_for_comparison`.

## Label quality inspection before any training approval

Already passed for all 500 records (`reports/VALIDATION_REPORT.md`): Batch 001 validator 500/500, final schema audit 0 failures, 35 independent checks 0 failures. Additional deterministic flags added for this proposal (review prompts, not rejections):

| Flag | All 500 | Training candidates | Development | Holdout |
|---|---:|---:|---:|---:|
| no_assessment_stated_(intentional_abstention_case) | 46 | 40 | 1 | 5 |
| nsaid_with_common_caution_in_history | 13 | 10 | 2 | 1 |
| resolved_symptom_phrase_is_a_gerund_clause | 21 | 16 | 3 | 2 |
| template_artifact_verb_form_in_symptom_phrase | 13 | 13 | 0 | 0 |
| two_current_or_planned_medicines_of_the_same_class | 6 | 5 | 0 | 1 |

**41 of the 400 training candidates carry a review flag** (verb-form artefact in a symptom phrase such as "I did have being unsteady", resolved-symptom wording, NSAID with a caution in the history, two medicines of one class); their ids are the rows with `needs_review_before_training = 1` in the CSV. 'No assessment stated' is an intentional abstention case, not a defect.

Still open for the 400 training candidates before fine-tuning can be approved (not verifiable by automation): clinical plausibility of profile content, doses and plans (AI-authored, never clinician reviewed); label correctness beyond lexical grounding and consistency (labels come from the generator, not independent human annotation, so they are not human-verified or clinically validated); `reported_by` follows the cited speaker, so confirmed history carries the patient as reporter although the doctor's confirming turn is also cited (one role per fact); template scaffolding (about 57% of long segments recur across Batch 002) that a model can memorise; low profile diversity (60 profiles, each used 6-10 times). Suggested additional checks: a person reads a sample of each flagged class plus a random 5%; a profile-level review of the 60 scenario definitions; a near-duplicate check of the final training set against Batch 001 development records only (the 400 locked records may not be opened).

## Development and holdout ids (Option A as requested)

Development (50): 20012, 20015, 20049, 20051, 20053, 20055, 20060, 20063, 20077, 20089, 20116, 20125, 20127, 20130, 20131, 20135, 20139, 20145, 20154, 20156, 20159, 20160, 20173, 20181, 20191, 20192, 20195, 20229, 20233, 20243, 20260, 20268, 20270, 20274, 20288, 20318, 20323, 20327, 20363, 20368, 20376, 20387, 20390, 20411, 20425, 20435, 20463, 20469, 20476, 20482

Internal holdout (50, never for training or prompt tuning): 20009, 20020, 20022, 20030, 20032, 20043, 20076, 20100, 20110, 20118, 20119, 20138, 20140, 20150, 20183, 20185, 20197, 20199, 20210, 20211, 20216, 20225, 20236, 20254, 20258, 20285, 20292, 20301, 20329, 20337, 20346, 20353, 20356, 20358, 20365, 20383, 20388, 20391, 20392, 20394, 20398, 20400, 20405, 20431, 20436, 20440, 20450, 20460, 20483, 20498

Training candidates (400): all other ids; see `allocation_proposal.csv`, column `proposed_split`.

## Decisions needed

1. Option A (stratified as requested, in-distribution holdout), Option B (profile-disjoint holdout/development), or both (A for monitoring, B as the generalisation test)?
2. Flagged training candidates: exclude, regenerate with a new attempt, or keep with the flag?
3. Approve more profiles and dialogue variation in Batch 003 so a future holdout does not overlap scenarios?
