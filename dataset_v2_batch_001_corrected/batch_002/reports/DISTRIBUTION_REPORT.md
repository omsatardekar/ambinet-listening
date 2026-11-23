# Batch 002 distribution report

All numbers are measured from the generated files (validation/distribution.json). Planned quotas are in scripts/generate_batch_002.py.

## Specialty (planned = actual)

| Specialty | Encounters | Simple | Medium | Hard |
|---|---:|---:|---:|---:|
| General Medicine / Primary Care | 50 | 13 | 23 | 14 |
| Cardiology | 45 | 13 | 20 | 12 |
| Respiratory Medicine | 45 | 14 | 20 | 11 |
| Gastroenterology | 45 | 14 | 20 | 11 |
| Endocrinology and diabetes | 45 | 14 | 20 | 11 |
| Neurology | 45 | 14 | 20 | 11 |
| Orthopaedics / Musculoskeletal | 40 | 12 | 18 | 10 |
| Dermatology | 40 | 12 | 18 | 10 |
| Women's health (Gynaecology) | 40 | 12 | 18 | 10 |
| ENT / Ophthalmology | 30 | 9 | 14 | 7 |
| Infectious Diseases | 40 | 12 | 18 | 10 |
| Urgent Care / Other | 35 | 11 | 16 | 8 |
| **Total** | **500** | **150** | **225** | **125** |

Internal specialty names follow the unmodified Batch 001 generator; 'Gynaecology' is reported as women's health, 'General Medicine / Primary Care' and 'Infectious Diseases' are separate specialties, and 'Urgent Care / Other' collects minor injury, allergy and general urgent presentations. Nephrology/urology is not a separate specialty (urinary infection sits under Infectious Diseases).

## Difficulty tiers

| Tier | Planned | Actual | Generator complexity |
|---|---:|---:|---|
| Simple | 150 | 150 | simple (150) |
| Medium | 225 | 225 | moderate (225) |
| Hard | 125 | 125 | complex (75) + challenging (50) |

The generator's complexity features decide the content (for example a 'moderate' encounter may include a resolved symptom or discontinued medicine; 'complex' and 'challenging' add speaker disagreements, interruptions, unknown speakers, mixed negation).

## Profiles and speakers

- Distinct scenario profiles: 60 (Batch 001: 108); encounters per profile min 6, max 10, mean 8.33 (Batch 001 max 6, mean 4.63).
- Speakers per encounter: {'2': 248, '3': 189, '4': 37, '5': 25, '6': 1}.
- Encounters containing each role: {'DOCTOR': 500, 'FAMILY_MEMBER': 66, 'NURSE': 116, 'PATIENT': 500, 'CAREGIVER': 86, 'UNKNOWN': 21, 'CLINICAL_STAFF': 53}.

## Requested extraction challenges: measured coverage (of 500 encounters)

| Challenge | Encounters |
|---|---:|
| abstention-appropriate: allergy status not assessed in the transcript | 53/500 (10.6%) |
| abstention-appropriate: allergy status uncertain (patient unsure) | 32/500 (6.4%) |
| abstention-appropriate: incomplete or interrupted answers | 48/500 (9.6%) |
| abstention-appropriate: no assessment stated | 46/500 (9.2%) |
| abstention-appropriate: no follow-up stated | 115/500 (23.0%) |
| abstention-appropriate: unattributable utterance (unknown speaker) | 21/500 (4.2%) |
| allergy status: disputed | 23/500 (4.6%) |
| allergy status: historical | 17/500 (3.4%) |
| allergy status: known | 146/500 (29.2%) |
| allergy status: none | 229/500 (45.8%) |
| allergy status: not_discussed | 53/500 (10.6%) |
| allergy status: uncertain | 32/500 (6.4%) |
| allergy: medication statement within three segments of the allergy question | 147/500 (29.4%) |
| assessment: provisional or differential only (nothing confirmed) | 454/500 (90.8%) |
| history: family history present | 213/500 (42.6%) |
| history: past medical history >=2 conditions | 210/500 (42.0%) |
| history: surgical history present | 198/500 (39.6%) |
| medications: >=3 current medicines | 86/500 (17.2%) |
| medications: adherence doubted | 37/500 (7.4%) |
| medications: current + discontinued + planned in the same encounter | 28/500 (5.6%) |
| medications: discontinued (historical) medicine | 55/500 (11.0%) |
| medications: dose disagreement between speakers | 30/500 (6.0%) |
| medications: dose not established (uncertain / name forgotten) | 76/500 (15.2%) |
| medications: look-alike drug names in the same encounter | 17/500 (3.4%) |
| medications: newly prescribed (planned) medicine | 275/500 (55.0%) |
| medications: reported by caregiver or family member | 42/500 (8.4%) |
| medications: two or more different medicines supported by one transcript segment | 231/500 (46.2%) |
| negation: >=4 negative findings | 484/500 (96.8%) |
| negation: disputed finding (patient denies, other speaker reports) | 14/500 (2.8%) |
| negation: patient corrects/qualifies an earlier statement (mixed negation, previous episode, resolved symptom) | 145/500 (29.0%) |
| negation: positive symptom and negated symptom set in the same encounter | 500/500 (100.0%) |
| speakers: caregiver speaks | 86/500 (17.2%) |
| speakers: clinical staff speaks | 53/500 (10.6%) |
| speakers: family member speaks | 68/500 (13.6%) |
| speakers: nurse speaks | 116/500 (23.2%) |
| speakers: two or more speakers contribute to the same fact (conflict / duration disagreement / discrepancy / adherence by other) | 100/500 (20.0%) |
| speakers: unattributed speaker | 21/500 (4.2%) |
| temporality: appointment time spoken by staff (scheduled_datetime holds the spoken words, no invented date) | 50/500 (10.0%) |
| temporality: conditional follow-up or investigation | 98/500 (19.6%) |
| temporality: onset/date uncertain | 43/500 (8.6%) |
| temporality: planned investigation | 423/500 (84.6%) |
| temporality: resolved or previous-episode symptom | 145/500 (29.0%) |

Counts are measured from blueprints, labels and transcripts (see scripts/b2_make_reports.py for the exact rules). Look-alike drug groups used: metformin/metoprolol; lisinopril/losartan; glibenclamide/gliclazide/glimepiride; carbamazepine/carvedilol; prednisolone/prednisone; atorvastatin/rosuvastatin/simvastatin; esomeprazole/lansoprazole/omeprazole/pantoprazole; amiodarone/amlodipine.
