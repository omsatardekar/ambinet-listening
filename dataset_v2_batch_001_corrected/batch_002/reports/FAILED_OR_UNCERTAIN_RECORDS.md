# Failed or uncertain records

## Unresolved or failed

None: all 500 slots were written and passed every automated check.

## Records that needed regeneration (not failures; listed for transparency)

151 of 500 records were accepted only after one or more failed attempts. The per-attempt reasons are in validation/quality_log.txt and the accepted attempt index is the `generation_attempt` column of output/manifest.csv.

## Uncertain / not verifiable by automation

- Clinical plausibility of profile content, dose/frequency pairings, plans and referral choices (not clinically reviewed).
- Naturalness and linguistic quality (no linguistic review; template scaffolding remains).
- Similarity to the 400 locked-test Batch 001 records (not measured; the records may not be opened).
- Records flagged by the generator's own uncertainty features (disputed or uncertain allergy, discrepant doses, unknown speaker) are intentional; they are labelled as uncertainties in the labels, not defects.
