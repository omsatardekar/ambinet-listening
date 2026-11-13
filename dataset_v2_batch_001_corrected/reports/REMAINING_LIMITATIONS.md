# Remaining limitations (be conservative when interpreting model results)

1. **Not clinically reviewed.** All clinical content (profiles, pairings, doses, plans, vitals, assessments) was authored from general
   knowledge. Some pairings are only loosely plausible (for example a metformin-only patient with hypoglycaemic episodes). The prioritised
   list in `human_review_required.csv` is an automated triage, not a review.
2. **Still template-composed language.** Phrase pools are wider and sub-sampled per encounter, and filler is gone, but ~27% of segments are
   texts shared by >=5% of encounters (routine history questions and short answers). A model can learn this scaffolding. Real clinic
   speech has far more irregular structure.
3. **Original facts were re-sampled**, not carried over (see audit, "How the correction was done"). Only ID, specialty, complexity and (for
   413 records) the profile are preserved.
4. **Transcript imperfection is synthetic and restrained**: case/punctuation loss, repeated words, spoken contractions. There are no
   acoustic or recognition errors on medical terms, no overlapping speech, no speaker-attribution mistakes beyond the 26 deliberately
   unattributable utterances. These are not real ASR outputs.
5. **Duration is partly silence.** About 10% of recording time (mean 39 s per encounter) is silent documentation/examination pause. Mean
   duration is 6.4 min (range 5.0-8.9); some simple encounters are only just over 5 minutes. 8 encounters have 32-34 or 71-72 segments.
6. **Profile coverage:** 108 profiles, each reused up to 6 times; rare diseases and paediatric/obstetric detail are absent. Age is
   a latent blueprint variable (it conditions history); it is never spoken, so it is not extractable.
7. **Label conventions you may want to change:** counselling/safety-net advice is a `clinical_actions` entry with status `recommended`;
   planned prescriptions are `medications` with status `planned`; the doctor's "that's already on your record" line is the evidence for
   `clinical_conditions`; `severity: "unknown"` is the allergy default; the description text of counselling actions is a summary and is
   not lexically verified against the advice.
8. **Neutral talk is unlabelled** (a few remarks such as "my family kept telling me to get it checked"), and patient age/sex are not in the schema.
9. **Automated validation is heuristic.** Lexical grounding proves a value is literally present in cited evidence, not that it is
   clinically right. The category check only covers symptom names seen in the authored profiles. Dose-disagreement detection works
   at sentence level and can miss unusual phrasings. The "historical labelled current" rule is a pattern check.
10. **Confidence fields are null by design**; do not include them in accuracy calculations.
11. **Evaluation integrity:** this is still a locked evaluation set. Do not use it, the blueprints, or paraphrases for fine-tuning data.
