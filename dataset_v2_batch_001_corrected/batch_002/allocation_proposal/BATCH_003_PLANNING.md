# Batch 003: planning notes (FUTURE; nothing is generated)

Approved by the owner for planning only. No Batch 003 file, id range or seed is reserved or used yet. Targets below are proposals; each is measured with the same scripts as Batch 002 so the gain (or its absence) is visible.

## Why (measured in Batch 002)
- 60 profiles, each used 6-10 times (Batch 001: 108, up to 6); look-alike drug names co-occur in only 3.4% of encounters.
- Routine scaffolding: about 57% of long segments occur in another Batch 002 encounter; 28% of all segments belong to texts that occur in >=5% of encounters; 10.9% of Batch 002 long segments occur verbatim in the 100 Batch 001 development transcripts (after replacing the wording of the routine pools).
- A stratified holdout shares scenario profiles and about 56% of its long segments with training; a profile-disjoint holdout still shares about 52%.

## 1. Profile diversity
- Target >= 150 scenario profiles (>= 12 per specialty), each used at most 3-4 times in 500 encounters (Batch 002: 6-10).
- Compose scenarios instead of hand-writing every one: separate a presenting complaint, a comorbidity set, a medicine set and a social context so that the same complaint appears with genuinely different backgrounds; keep the exclusion rules (age, sex, pregnancy, drug cautions) and add coverage of multi-morbidity, polypharmacy (>=5 medicines), look-alike drug pairs on purpose (target >= 15% of encounters), paediatric-guardian and elderly-with-carer encounters, mental-health presentations, chronic-disease reviews without a new complaint, telephone-style short contacts.
- Reserve a share of profiles (for example 20%) for evaluation only from the start (profile-disjoint by design).
- Clinical review: have a clinician or pharmacist read every profile definition once (plans, doses, cautions); record the outcome in the manifest.

## 2. Dialogue-engine variation (without editing Batch 001 scripts)
- Implement a new Batch 003 dialogue module that subclasses or wraps the existing `Enc` (as the Batch 002 wrappers do) and is versioned in the Batch 003 folder.
- Replace the fixed section order (history -> medicines -> allergies -> vitals -> exam -> plan) by several discourse plans: patient-led storytelling, doctor-led checklist, revisit of an earlier topic, interruption by a nurse mid-topic, the plan discussed before the last examination step, medicines raised during the complaint rather than in a block.
- Multi-fact utterances and cross-turn references ("the same tablet as before", "no, the other one"), self-corrections, partially answered questions answered later, tag questions, fragments.
- Several speakers contributing to one fact in non-adjacent turns.

## 3. Sentence structure and language
- Per-fact surface realisations drawn from a much larger pool (target >= 10 realisations per fact type), with syntactic variety (passive, relative clauses, fronted time expressions, hedges, negation scopes such as "not the left one, the right").
- Fix known artefacts: gerund clauses used as nouns ("I did have being unsteady"), duplicated phrasing in prescriptions, intensity words clashing with severity.
- Optional human-written seed phrases reviewed by a person, to reduce purely generator-authored language.

## 4. Reduced repeated scaffolding: measurable targets
| Measure | Batch 001 / 002 | Batch 003 target |
|---|---|---|
| Share of segments in texts that occur in >=5% of encounters | 26.6% / 28.1% | <= 10% |
| Long segments verbatim in another encounter of the same batch | not measured / 57% | <= 25% |
| Long segments verbatim in earlier batches' development records | - / 10.9% | <= 5% |
| Distinct opening sentences per 500 | 171 / 201 | >= 350 |
| Max encounters per profile | 6 / 10 | <= 4 |
| Look-alike drug pairs in one encounter | - / 3.4% | >= 15% |

## 5. Quality gates (reuse plus additions)
- Reuse the Batch 001 validator, the final schema audit and the Batch 002 independent checks unchanged; add the Batch 002 gates (latent age, planned-vs-conditional wording, duplicate generic medicine) and new ones for the Batch 002 flag classes (verb-form artefacts, NSAID cautions, same-class medicines).
- Human review sample (for example 5% plus all flagged) before any use for training; keep the statement that labels are generator-derived unless a person has verified them.

## 6. Data-integrity rules
- New id range and seed; own folder `dataset_v2_batch_001_corrected/batch_003/` (or a sibling dataset root if the owner prefers); no overwrite; manifest with hashes; locked Batch 001 records never opened; similarity checks only against development records.
- Allocation (training / development / holdout) decided before generation for the reserved evaluation profiles; evaluation records never used for prompt tuning.
- Schema changes (for example `measured_by`) need separate approval and a new schema version; Batch 003 uses the frozen schema unless approved otherwise.

## 7. Suggested sequence (all subject to approval)
1. Approve targets and the schema position. 2. Write and review profiles and discourse plans (no generation). 3. Pilot 50 encounters, measure against section 4. 4. Adjust, then generate 500. 5. Validate, report, propose allocation. No model run on the data in any step.
