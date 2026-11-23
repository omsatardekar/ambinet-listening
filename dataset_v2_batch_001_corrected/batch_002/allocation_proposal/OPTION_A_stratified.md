# Option A: stratified allocation (NOT EXECUTED)

Retained as a separately documented strategy by owner decision. Seed 20261115; stratified by specialty x tier (36 cells); exact 400 training candidates / 50 development / 50 internal holdout. Ids: `option_A_stratified_ids.json` and column `proposed_split` of `allocation_proposal.csv`.

## What it is good for

- Monitoring in-distribution extraction quality on new samples of scenarios the model has trained on; balanced specialty and difficulty coverage (every specialty at least 4 development and 4 holdout records).

## What it cannot show

- Generalisation to unseen scenarios: 50/50 holdout records share their scenario profile with training records, and 56% of the holdout's long segments occur verbatim in training. Max 5-gram Jaccard to any training record 0.104 (development 0.111).
- Any result on this holdout is an in-distribution result on generator-derived labels, not clinical validation.

## Composition

- Development specialties {'Cardiology': 4, 'Dermatology': 4, 'ENT / Ophthalmology': 4, 'Endocrinology': 4, 'Gastroenterology': 4, 'General Medicine / Primary Care': 6, 'Gynaecology': 4, 'Infectious Diseases': 4, 'Musculoskeletal / Orthopaedics': 4, 'Neurology': 4, 'Respiratory Medicine': 4, 'Urgent Care / Other': 4}; tiers {'Hard': 11, 'Medium': 23, 'Simple': 16}
- Holdout specialties {'Cardiology': 4, 'Dermatology': 4, 'ENT / Ophthalmology': 4, 'Endocrinology': 4, 'Gastroenterology': 4, 'General Medicine / Primary Care': 6, 'Gynaecology': 4, 'Infectious Diseases': 4, 'Musculoskeletal / Orthopaedics': 4, 'Neurology': 4, 'Respiratory Medicine': 4, 'Urgent Care / Other': 4}; tiers {'Hard': 11, 'Medium': 23, 'Simple': 16}
- Training specialties {'Cardiology': 37, 'Dermatology': 32, 'ENT / Ophthalmology': 22, 'Endocrinology': 37, 'Gastroenterology': 37, 'General Medicine / Primary Care': 38, 'Gynaecology': 32, 'Infectious Diseases': 32, 'Musculoskeletal / Orthopaedics': 32, 'Neurology': 37, 'Respiratory Medicine': 37, 'Urgent Care / Other': 27}; tiers {'Hard': 103, 'Medium': 179, 'Simple': 118}

The 41 flagged training candidates stay in the training candidates with their flags (see `FLAGGED_TRAINING_CANDIDATES_REVIEW.md`). The 50 holdout records must not be used for training or prompt tuning.
