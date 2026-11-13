# Batch 002 ground-truth quality report

**Not clinician verified.** Labels are produced by the generator from the same turns that create the transcript (facts are attached when the turn is written), then checked by a separate validator and by independently written checks. They are not independently annotated by humans and were not derived from any model prediction.

## Checks performed (numerators/denominators)

| # | Required check | Result |
|---|---|---|
| 1 | Label refers to the correct encounter | 500/500 encounter ids match file names; ids unique and in range: 1/1 |
| 2 | Every evidence segment exists | 16638/16638 evidence records match a transcript segment on speaker, text, role and start time |
| 3 | Every evidence segment supports its fact | lexical grounding 23533/23533; patient-origin facts with a non-question supporting segment 6551/6551; negative findings with a negation cue in the cited answer 2767/2767; present symptoms with a non-negated statement or affirmed question 1156/1156; no greeting-only evidence 6551/6551 |
| 4 | Speaker attribution | `reported_by` equals the role of a cited non-question segment 6551/6551 |
| 5 | Polarity preserved | negative findings with negation cue 2767/2767; no negative finding contradicting an undisputed present symptom 500/500 |
| 6 | Medication identity and dose | dose number present in cited evidence 808/808; dose within two segments after the drug name 808/808; no duplicate medicine entries 500/500; no drug both current and planned/discontinued 500/500 |
| 7 | Allergy status | representation matches blueprint and schema 500/500; no placeholder allergy 230/230; allergy substance in cited evidence 230/230; no allergy that is a current medicine 230/230 |
| 8 | Historical vs current | symptom count and temporality match blueprint (allowing the disputed symptom) 500/500 |
| 9 | No unsupported datetime | no ISO date/time in any label 500/500; follow-up normalized_datetime null 500/500; scheduled_datetime null or literally spoken 715/715 |
| 10 | No duplicate or contradictory labels | no duplicate entities within sections 5000/5000; no duplicate family history 500/500 |

## Remaining limits

- A passing check means the label is consistent with the transcript and the generating blueprint; it does not show that the medicine/dose/assessment pairing is clinically sensible. Profile content, doses and plans were authored from general knowledge by an AI, then constrained only by simple exclusions (no teratogenic chronic drugs in early pregnancy profiles, no NSAID prescription profile with common NSAID cautions, age ranges).
- Known template artefacts remain: for example an expression such as 'I did have being unsteady at one point' (verb-form of a resolved symptom) and short repeated acknowledgements.
- `reported_by` follows the Batch 001 convention (role of the speaker of the cited turn; clinician confirmations of history are cited through the confirming turn). Under the owner's definition (the speaker who verbally supplied the information) this holds in the independent check above; the schema has no `subject` field and `observed_by` is used for examination findings.
- Confidence fields are null by design. Do not use Batch 002 for evaluation and training at the same time without a recorded allocation; no allocation has been made.
