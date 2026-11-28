# 11. Live tests (m3_14, m3_15, encounter 58) and what to say at the depo

Written for: the presenter. All findings come from real runs through the app on synthetic scripted conversations. No clinician has reviewed them.

## What the three runs showed

| Run | What worked | What went wrong in the extraction | Did "Before you sign" catch it? |
|---|---|---|---|
| m3_14 (fever) | most symptoms, plan, tests | flipped negation, duplicate test, smoking status, invented plan items | most |
| m3_15 (periods) | symptoms, history | repeated symptoms ("flushes" / "the flushes"), sentence-like symptom names | partly (backend now merges/flags) |
| encounter 58 (voice) | allergies, smoking, history, referral, advice, medicine | reason for visit was a joke ("she wouldn't have come at all"), invented "conflict", idioms as symptoms, exam listed as "planned", medicine spelled "Omprazole" | yes: chief complaint, onset, exam, medicine spelling, invented conflict |

## Backend safeguards (clinical_extraction/postprocess.py, no model involved)
1. Contradicted negative removed ("No asthma" next to asthma in history).
2. Duplicate test merged.
3. Repeated symptom merged ("flushes" / "the flushes").
4. Symptom written as a sentence from speech is flagged (including "I can't hear myself think").
5. Reason for visit written as a sentence/remark is flagged.
6. Medicine name close to a known drug but not equal ("Omprazole" -> omeprazole) is flagged. Nothing is rewritten.

Rules 1-3 change the data and list the change; rules 4-6 only warn the clinician.

## Safety checks against the cited conversation (clinical_extraction/safety_checks.py)
Added after the m3_01 run (encounter 19), where the extraction recorded a penicillin allergy although the patient said "No. Never. I have taken penicillin and everything", planned amoxicillin-clavulanate in the same note, and gave a blood pressure (100/60) that was not said (109/77). They run after evidence resolution, change nothing, and appear as warnings; the details are saved as `safety_checks.json` in the job folder.
1. Allergy denied in its own cited passage ("never", "no reaction", "have taken it"; a passage that also names a rash, hives, swelling etc. is not flagged).
2. Recorded allergy and a current or planned medicine of the same drug family (penicillin, cephalosporin, sulfonamide, NSAID, macrolide, fluoroquinolone, tetracycline, opioid). Stopped medicines are ignored.
3. A vital sign whose number is not in the segments cited for it (spoken numbers are read as digits).
Limits: the drug families are a short hand-made list; the checks can raise a false alarm and never fix anything; they were tested on the one real run above plus synthetic cases, not on the 20 scenarios.

## What to say
- "The model reads a consultation and lists symptoms, history, medicines and plan, each linked to the words that were said."
- "On our 20 natural test conversations about 76% of the written facts were supported and about 17% were not; it captured about 56% of the facts we designed into them. On the template-style locked test the unsupported rate was 2.4%. No clinician has reviewed these numbers."
- "It still makes mistakes (we saw about 5 per consultation), so every note is a draft. The note ends with a 'Before you sign' list that points the clinician at the items to check, and in our three live runs it caught most of them."
- "Every item cites the quote it came from, so a clinician can verify it in seconds."

## What NOT to say
- Not "93% accurate" or "70% accurate". 0.933 is a judge score on synthetic template-style data.
- Not "100% linked means 100% correct". The "19 of 19 items linked" bar only means every item has a source quote; wrong items can still have one.
- Not "the model understands the conversation". It makes extraction errors a clinician must check.

## Open
- A targeted fine-tuning round on these mistakes (round 4, document 07) did not beat step 400 (more unsupported facts), so these mistakes are handled by the backend rules above, not by the model.
- Check that `SOAP_INCLUDE_TRANSCRIPT=0` on every test laptop. In the encounter 58 run the note held facts that the extraction panel did not show (exam, "frog in my throat", whistle, microphone), so either the transcript was reaching the writer or the panel shows only part of the extraction. This was not confirmed.
- The drug list is a short hand-made list of common medicines, not a pharmacy database.
