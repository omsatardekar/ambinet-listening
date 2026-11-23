# Option B: profile-disjoint holdout and development (NOT EXECUTED)

Retained as a separately documented strategy by owner decision. Whole scenario profiles are held out (seed 20261116, round-robin over specialties). Ids: `option_B_profile_disjoint_ids.json`.

## IMPORTANT DISCLOSURE: this is NOT a clean generalisation test

- **52% of the holdout's long segments (>=5 words) occur verbatim in the training set** (measured: 51.5%). The overlap comes from the shared dialogue engine's routine questions, answers and acknowledgements, not from clinical content; it is nearly as high as in Option A (56%).
- Holding out profiles removes scenario overlap only. The sampled medicines, histories, allergy patterns, speaker patterns and the whole conversational scaffold are still shared with training. The same generator, the same author and the same pools produced all records, so a model can still exploit shared structure.
- The holdout covers only 6 of the 12 specialties and 6 of the 60 profiles; sizes are approximate (51 / 51 / 398). A good score would indicate robustness to unseen profiles of the same generator, not robustness to real clinical conversations.

## Measured separation

| | Development | Holdout |
|---|---:|---:|
| Records | 51 | 51 |
| Profiles shared with training | 0 records | 0 records |
| Distinct profiles | 6 | 6 |
| Max 5-gram Jaccard to training | 0.074 | 0.075 |
| Verbatim long-segment share in training | 54.6% | 51.5% |

## Composition

- Holdout profiles: b2_diabetic_foot_ulcer, b2_palpitations_paroxysmal, b2_rectal_bleeding_haemorrhoids, b2_shingles_early, b2_sudden_hearing_loss, b2_unintentional_weight_loss
- Development profiles: b2_acne_scarring_isotretinoin_review, b2_acute_otitis_externa, b2_constipation_adult, b2_hypoglycaemia_episodes, b2_nocturnal_leg_cramps, b2_stable_angina_exertional
- Holdout specialties {'Cardiology': 9, 'Dermatology': 8, 'ENT / Ophthalmology': 6, 'Endocrinology': 9, 'Gastroenterology': 9, 'General Medicine / Primary Care': 10}; tiers {'Hard': 15, 'Medium': 19, 'Simple': 17}
- Development specialties {'Cardiology': 9, 'Dermatology': 8, 'ENT / Ophthalmology': 6, 'Endocrinology': 9, 'Gastroenterology': 9, 'General Medicine / Primary Care': 10}; tiers {'Hard': 11, 'Medium': 30, 'Simple': 10}
- Training specialties {'Cardiology': 27, 'Dermatology': 24, 'ENT / Ophthalmology': 18, 'Endocrinology': 27, 'Gastroenterology': 27, 'General Medicine / Primary Care': 30, 'Gynaecology': 40, 'Infectious Diseases': 40, 'Musculoskeletal / Orthopaedics': 40, 'Neurology': 45, 'Respiratory Medicine': 45, 'Urgent Care / Other': 35}; tiers {'Hard': 99, 'Medium': 176, 'Simple': 123}

Not stratified by specialty or difficulty. Flagged training candidates stay in training with their flags. A genuinely clean generalisation test needs data from a different generator or real recordings; Batch 003 planning addresses part of this (see `BATCH_003_PLANNING.md`).
