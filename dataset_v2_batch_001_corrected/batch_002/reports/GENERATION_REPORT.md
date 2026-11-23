# Batch 002 generation report

Generated 2026-11-13 with master seed 20261114; ids 20001-20500; 500 of 500 planned encounters written, 0 unresolved.

## Method

1. The unmodified Batch 001 pipeline is reused: scenario blueprint (facts fixed first) -> multi-speaker dialogue -> label derived from the same turns -> independent validator. Imported modules: blueprint, dialogue, dialogue_pools, content_core, validate_dataset.
2. New content (this folder only): 60 new clinical profiles (5 per specialty, b2_profiles_*.py); look-alike drug options added to existing chronic-condition medication lists; new surgical, family-history, allergy and social-history wording replacing the Batch 001 phrasing; replacement wording for the placeholder-free routine question/answer pools (b2_pools.py, b2_pools_replace.py). All applied in memory; no Batch 001 file was edited.
3. New plan: specialty quotas x difficulty tiers (30/45/25), new seed, ids 20001-20500 (disjoint from Batch 001's 00001-00500).
4. Acceptance: each candidate passes the Batch 001 record validator, a latent-age plausibility gate, a planned-vs-conditional wording gate (re-implementation of one rule of the Batch 001 final audit), a duplicate-generic-medicine gate (the same drug under a generic and a brand name) and a clinical-identity uniqueness gate; otherwise it is regenerated from the same slot with a new attempt (as in Batch 001). Nothing is silently dropped: every failed attempt is in validation/quality_log.txt.

## Attempts

- Records accepted at first attempt: 349; needing 1 or more regenerations: 151; maximum attempt index used: 18.
- Total failed attempts: 414; by check: {'duration': 214, 'age_profile_plausibility': 170, 'evidence_lexical': 22, 'segment_count': 24, 'action_status': 4, 'allergy_consistency': 7, 'planned_not_conditional_text': 1, 'duplicate_clinical_identity': 5, 'duplicate_generic_medicine': 1}.
- 'duration' and 'segment_count' failures are the generator's own length targets (5-9 minutes, 30-80 segments); 'age_profile_plausibility' enforces the latent-age ranges for age-specific profiles.

## Iterations before the final run (disclosure)

Two earlier complete generation runs were produced and deleted by me before the final run because review of samples found problems in my new content: look-alike claims in assessment text that did not follow the sampled medicines, early-pregnancy encounters that could draw contra-indicated chronic medicines, NSAID prescriptions without common cautions, non-symptoms listed as symptoms (past sunburn, analgesic use, an old fracture, an insect bite last week), contradictory intensity wording ('light bleeding' rated severe), single-dose prescriptions with duplicate wording, a dose written as '200/6 micrograms' that could not be matched in the transcript, and one patient listed on paracetamol 650 mg and on the brand Dolo (the same drug twice; the unmodified Batch 001 blueprint de-duplicates only on the spoken name, so Batch 001 may contain the same pattern; this was not checked because it would require opening locked-test labels). A third run was repeated after replacing the routine question wording and after a pool change broke the allergy and regular-medication evidence wording (fixed by keeping the required words). The record set in this folder is the last complete run; the earlier outputs were not kept (they were my own intermediate files).

## Characteristics

- Mean duration 366.23 s (range 300.05-536.16); mean 45.05 segments (range 32-71).
- Allergy representation (Batch 001 schema): 229 explicit 'no known allergies', 146 known, 53 not discussed, 32 uncertain, 23 disputed, 17 historical.

## Comparison with Batch 001 (same measuring script, `audit_metrics.py`)

| Measure | Batch 002 | Batch 001 |
|---|---:|---:|
| distinct profiles | 60 | 108 |
| max encounters per profile | 10 | 6 |
| share of segments whose text occurs in >=5% of encounters | 0.2867 | 0.2657 |
| distinct opening sentences | 164 | 171 |
| most common opening: share | 0.042 | 0.026 |
| distinct closing sentences | 92 | 107 |
| most common closing: share | 0.096 | 0.078 |
| mean segments | 45.1 | 47.6 |
| mean duration (s) | 366.2 | 382.2 |

- Novelty (against the 100 Batch 001 DEVELOPMENT records only): max 5-gram Jaccard 0.074; 0 pairs >= 0.45; 10.9% of Batch 002 segments (>=5 words) appear verbatim in those 100 transcripts; profile keys in common: 0; surgery/family surface phrases in common: 0.
- 57.8% of Batch 002 segments (>=5 words) also occur in another Batch 002 encounter (routine questions and answers), similar to Batch 001's template scaffolding.
- The 400 locked-test records were not opened, so similarity to them is not measured; disjointness rests on construction (no Batch 001 profile registered, replaced phrasing, new ids and seed).

## What did NOT improve (honest)

- Scenario diversity is lower than Batch 001 (60 profiles vs 108; each used 6-10 times). Clinical content is new, but the same profile repeated with different sampled symptoms, medicines and histories.
- Conversation naturalness is bounded by the unmodified dialogue engine: the turn structure is still largely alternating question-answer with the same repertoire of mechanisms (interruptions, conflicts, unknown speaker). Wording of routine questions is new, but template scaffolding is not removed. Real irregular speech, overlapping speech, recognition errors and deeper multi-turn clinical reasoning are not produced.
- Hard encounters add the generator's existing complications; they are not free-form clinical complexity.

## Files

output/inputs, output/labels (500 + 500), scenario_blueprints (500), output/manifest.csv, output/stats.json, output/CHECKSUMS.sha256, manifest/batch_002_manifest.json, validation/*, reports/*.
