# Batch 002 author guide (read fully before writing)

You hand-write synthetic clinical consultations (dialogue + ground-truth annotation) for a small-model extraction dataset. Quality, realism and
**honest, evidence-grounded labels** matter more than speed. A deterministic compiler turns your draft into the exact input/label JSON files and
runs the project's real validator. You never write timestamps, EV ids or `supports` lists; you write dialogue and annotation.

## Workflow (per encounter)
1. Read your plan entry (`plan/scenario_plan.json`, entries given to you by id). It fixes the situation, the speakers and *what information exists*.
2. Write `drafts/draft_<id>.json` (format below). Invent concrete details yourself (age, names of drugs/doses, etc.) - but only what the plan allows.
3. Run `cd /Users/shubhamsahu/ambinet-listening/dataset_v2_batch_001_corrected/batch_002_generation && python3 -B compile_draft.py drafts/draft_<id>.json`
   It prints PASS or the list of problems. Fix **the draft** until PASS (it then writes `staging/output/inputs|labels`). Never edit the validator, the schema or other files.
4. Do not stop at PASS: re-read the dialogue as a clinician would. Does the label contain anything the speakers did not say? Is anything said that is clinically
   important but missing from the label? Fix it.
Only write inside `drafts/`. Do not open other agents' drafts, `staging/`, or any Batch 001 encounter file. Study `examples/example_sparse_headache_draft.json` for the exact format.

## Draft format
```
{"encounter_id": "00501",
 "speakers": {"person_1": "PATIENT", "person_2": "DOCTOR", "person_3": "NURSE"},   # uppercase roles; ids person_N; one id per person
 "turns": [{"s": "person_1", "t": "text"}, {"s": "person_2", "t": "text", "pause": 18}],   # "pause": optional extra silent seconds BEFORE the turn (exam, vitals, typing)
 "label": {"chief_complaint": {...}, "symptoms": [...], "negative_findings": [...], "medical_history": {"past_medical_history": [], "surgical_history": [], "family_history": [], "social_history": []},
           "medications": [], "allergies": [], "vital_signs": [], "physical_examination": [], "review_of_systems": [], "clinical_conditions": [],
           "clinical_assessment": [], "procedures_and_investigations": [], "clinical_actions": [], "follow_up": [], "clinical_uncertainties": [],
           "quality_checks": {"contradictions_detected": [], "ambiguous_entities": []}}}
```
* Turn numbers are **1-based**. In every entity, `"evidence_ids": [3, 4]` lists the turn numbers that support it (the compiler converts them). Include the question
  turn when the answer only makes sense with it ("No." needs the question that asked about the finding). Every entity needs >= 1 evidence turn.
* Omit any field that is null / [] - the compiler fills `null` (and `[]` for associated_symptoms, aggravating_factors, relieving_factors). Omit `confidence`.
* Field names/enums are exactly those in `../schema/final_label_schema.json` (read it once; it documents every enum value). No new fields, no new enum values.
* Entities appear in the label in the order you list them; `related_entities` use `symptoms[0]`, `allergies[1]`, `negative_findings[2]`, `medications[0]` (0-based list positions).

## Transcript requirements (hard, checked)
* 30-80 turns; total length 300-540 s (the compiler times the turns from word count and stretches natural pauses, but only up to a limit):
  aim for **the plan's target_turns** and an average of >= 11 words per turn. Short "Mm-hm." turns are welcome but do not make everything short.
* Both a DOCTOR and a PATIENT speak. Speaker ids consistent; one role per id. A person who never speaks is not listed. Only the roles the plan lists (plus DOCTOR and PATIENT).
* FAMILY_MEMBER = parent/spouse/adult child/sibling; CAREGIVER = paid or live-in carer / care-home worker; NURSE; CLINICAL_STAFF = receptionist, healthcare assistant, phlebotomist, pharmacist tech.
* Young children are PATIENT; they speak a little ("It hurts here") and the parent answers (reported_by `family_member`). Infants: the patient may only make one or two utterances such as "Mama." or "Waaah" - keep them to a couple of turns.
* An UNKNOWN speaker (only if the plan asks): an utterance whose speaker cannot be identified (role UNKNOWN, e.g. "[from the doorway] It started on Tuesday"). Keep it short.
* The label is for **this** transcript only. No dates are extracted (`encounter_date` is null).

## Natural language (the point of this batch)
Real consults are uneven. Vary: who speaks first; whether the doctor asks open or closed questions; interruptions; hesitations ("um", "well, actually"); self-corrections
("Left... no, sorry, right"); trailing off; patients describing symptoms in everyday words ("my legs feel heavy by evening"); doctors using plain words; tangents that
produce **no** label entity; side remarks; reassurance; the doctor not asking about everything. Follow the plan's style hints. Do **not** use a fixed checklist order,
do not give every doctor the same closing line, do not reuse phrasing from the example or between your own encounters (no "Anything unclear?" ending, no identical vitals sentence).
Dialect hint in the plan is a flavour (spelling of words like diarrhoea/diarrhea, vocabulary like tummy/stomach), keep it consistent and never a caricature.
Chatter that is not extracted is *required* in sparse encounters: ask, explain, reassure, discuss lifestyle, clarify - that is how a 5-minute minimal visit reaches 35+ turns.

## What the plan means
`entity_targets` say how much information exists in the conversation. Treat 0 / "none" / "not_discussed" as **hard**: nothing about that topic is said at all.
Other numbers are targets (+-1 is fine if the conversation demands it; if you deviate, deviate toward natural, not toward more).
* medications `none`: no medicine is named as taken/prescribed (a doctor saying "I won't prescribe anything" is fine). `existingN`: N medicines the patient currently takes; `plannedN`: N the doctor starts now.
* allergies: `not_discussed` = the letters "allerg" appear nowhere in the transcript (also not "allergic", not "hay fever allergy"); `explicit_none` = doctor asks, patient says none -> negative_findings "Allergies"; `reported` etc. see below.
* vital_signs: `none` = no numbers measured/read aloud; `few` = 1-3 values; `full` = 4-6. `vitals_read_aloud_by` says who reads them (nurse -> nurse turns, reported_by "nurse").
* investigations N = procedures_and_investigations entries (tests ordered, completed, or conditional); follow_up `planned` / `conditional` / `none`.
* clinical_assessment `none`: the doctor never states what they think it is (a clinician who says "let's do bloods first and see" has not stated an assessment). `provisional` = "looks like / most likely X"; `differential` = "can't rule out X yet"; `both`.
* `special_features`: see recipes below; each listed feature must be in the label; features not listed must not occur.
Never invent beyond what is said; never turn silence into a negation (not asking about allergies/medicines means nothing is extracted for them).

## Grounding rules (each is checked lexically against the evidence turns you cite)
Values that are free text must appear **literally** (case-insensitive) in the cited turns; normalized_* fields are your standard-term version and are not checked, but must mean the same.
| section | literal in evidence | notes |
|---|---|---|
| chief_complaint.value | exact phrase | reported_by role must be a speaker of cited turns |
| symptoms | `name` (exact phrase said, "your"/"I" swapped is ok); `duration` as "2 weeks"/"two weeks" (value, unit); `onset` phrase; `frequency` phrase; `severity` the word mild/moderate/severe (or "7/10" with "seven out of ten" spoken); each aggravating/relieving factor phrase | category from: ENT, cardiovascular, constitutional, dermatological, endocrine, gastrointestinal, genitourinary, musculoskeletal, neurological, ophthalmological, other, psychiatric, respiratory. status present->temporality current; resolved symptom: status resolved + temporality resolved ("gone", "settled" spoken) or past (previous separate episode). certainty certain/uncertain/disputed |
| negative_findings | `finding` phrase (as spoken in the question or answer) + a negation word (no, not, none, nothing, never, haven't, don't, nope) in the cited turns | status "absent", assertion "negative", temporality current/past. Cite question + answer turns. Never list something denied that is also a present symptom. A patient who says "no" to a list denies *each* item the doctor listed; the validator expects one entity per item |
| medical_history.past_medical_history | `condition` phrase; duration literal; | status "ongoing" only |
| surgical_history | `procedure` AND `timeframe` phrases | always give a spoken timeframe ("about ten years ago", "in 2019", "as a child") |
| family_history | `relation` AND `condition` phrases | e.g. relation "mother", condition "breast cancer" |
| social_history | `details` phrase; for smoking/alcohol the words smok/cigarette/drink/alcohol/beer | category smoking/alcohol/occupation/exercise/diet/living; status current/former/never/none/retired |
| medications | `name` phrase (what was said, e.g. "the water tablet" / "metformin"); `dose` e.g. "500 mg" (number + unit word mg/milligrams); `frequency` phrase; `indication` phrase; duration | generic_name/normalized_name = proper name; route only "oral" or omit; status currently_used / discontinued / planned. `planned` needs a clinical_actions entry (medication, planned, doctor) sharing the evidence. Do not state a dose/frequency/indication that was not said |
| allergies | `substance` phrase; `reaction` phrase if given | allergy_type medication/food/environmental; severity always "unknown"; status reported/uncertain/historical/disputed; reaction null if not said; the transcript must contain "allerg" |
| vital_signs | every number in `value` (BP as "128/76": both numbers) | name e.g. Blood pressure, Heart rate, Temperature, Oxygen saturation, Respiratory rate, Weight, Height, BMI (if weight+height+BMI all present, BMI must match); unit as spoken (mmHg, bpm, %, °C, breaths/min, kg, cm) |
| physical_examination | `finding` phrase | observed_by doctor/nurse; status present (observed) or absent (stated not present) |
| review_of_systems | a denial word (no, nothing, normal, fine) in evidence | system e.g. respiratory; status "negative"; used only when the doctor asks at system level ("any trouble with your breathing?") |
| clinical_conditions | `name` phrase; the condition must also be in past_medical_history (same normalized_condition) | status "existing"; use when the patient reports a known condition and the doctor acknowledges it |
| clinical_assessment | `assessment` phrase from the **doctor** | certainty provisional|differential only; never a confirmed diagnosis |
| procedures_and_investigations | `name` phrase; scheduled_datetime parts if given | type laboratory/imaging/cardiac/other; status planned (needs a plan word: "arrange", "order", "book", "I'd like", "we'll do", "let's get"...), completed (needs "did"/"already"/"had"), conditional (needs "if"/"might"/"consider"/"hold off"/"not now"); requested_by doctor needs clinician evidence |
| clinical_actions | description is free text (e.g. "Arrange Chest X-ray"); `time_reference` {value, normalized_date: null} if a time was said | action_type investigation/medication/counselling/referral/follow_up/other; status planned/completed/recommended/conditional; responsible_person doctor/patient/nurse/clinical_staff. Investigation actions share evidence with a procedures entry; conditional only for investigation or follow_up; completed needs did/already/had wording; referral needs refer/see/seen/letter/send. Advice to the patient = counselling, recommended, responsible patient |
| follow_up | `time_reference` phrase | type consultation; status planned (stated unconditionally) or conditional ("if it's not better in three days"); each follow_up needs a matching clinical_actions follow_up entry with the same evidence and time_reference value |
Other rules: `reported_by`/`observed_by`/`stated_by` must be a role that actually speaks in the cited turns. A planned item cannot be supported only by a question.
A planned medication must not be in the allergy family of a reported allergy (penicillin: amoxicillin..., aspirin/ibuprofen: NSAIDs, sulfa, codeine). If `explicit_none`/`reported`... allergies appear, the transcript must contain "allerg".
Medicine names must be unique per label (a drug that is both taken and changed is one entry with the status that fits best).

## Additional conventions enforced by the project's schema audit (run after you finish; follow them now)
* clinical_actions `completed`: only `investigation` actions with responsible_person `nurse` (e.g. the nurse already did an ECG / swab before the doctor came in). Something the patient says was done elsewhere = a procedures entry with status `completed` and **no** action.
* `recommended` actions: only action_type `counselling` or `other`, responsible_person `patient`. Anything the clinic orders/starts/books/refers = `planned`; clinic-side responsible person is `doctor`, or `clinical_staff` when reception/staff books it.
* Every `planned` procedure needs a `planned` investigation action sharing an evidence turn; every `conditional` procedure needs a `conditional` investigation action sharing evidence, with `requested_by: "doctor"` and no scheduled_datetime. `completed` procedures need did/already/had wording in their evidence.
* follow_up: status `conditional` **iff** the time_reference starts with "if " (copy the spoken words, e.g. "if it's not better in three days"); a planned one is an unconditional time ("in two weeks", "next Tuesday"). Each follow_up has a twin clinical_actions entry: action_type follow_up, description "Follow-up consultation", same status, responsible doctor, time_reference {value: same string, normalized_date: null}, same evidence.
* A `planned` action's evidence must not contain hedged wording ("hold off", "not now", "we might do if...") about the same item - that would be `conditional`.
* Planned medication = medications entry status planned (reported_by doctor) + clinical_actions {action_type medication, status planned, responsible doctor, description e.g. "Start Amoxicillin 500 mg three times a day"} with shared evidence.
* Allergy entries: `reaction` is null when status is uncertain or disputed. Allergy kinds allowed together: none-discussed / explicit none (negative finding only) / reported / uncertain / historical / disputed.
* uncertainty `related_entities` target types: allergy_uncertain->allergies; allergy_disputed->negative_findings+allergies; medication_discrepancy, uncertain_dose, adherence_uncertain, incomplete_medication_name->medications; date_uncertain, duration_disagreement, unknown_speaker->symptoms; conflicting_statement->symptoms (+negative_findings).
* disputed symptoms must be reported_by caregiver/family_member and have a conflicting_statement uncertainty; negative_findings and symptoms must not both claim the same thing as present/absent unless disputed.

## Allergy representations (pick the one in the plan)
* explicit_none: `negative_findings` {finding:"Allergies", normalized_name:"No known allergies", status absent, assertion negative}; allergies [] ; the doctor/patient said "allerg...".
* reported: allergies {substance, normalized_substance, allergy_type, reaction (if said), severity "unknown", status "reported"}. reported_unknown_reaction: patient says they react but cannot recall what -> reaction omitted.
* historical: past reaction (e.g. in childhood), substance avoided since -> status "historical".
* uncertain: possible allergy, cannot name substance/reaction -> status "uncertain" + `allergy_uncertain` uncertainty (related allergies[i]).
* disputed: patient denies (negative_findings "Allergies" by patient), caregiver/family recalls a possible reaction (allergies entry status "disputed", reported_by the third party, reaction omitted) + `allergy_disputed` uncertainty related to BOTH (negative_findings[i], allergies[j]) + one line in quality_checks.contradictions_detected.

## Special-feature recipes (clinical_uncertainties; each has `type`, `description` (one sentence, plain), `related_entities`, `resolution_status`, `evidence_ids`)
* date_uncertain: a speaker cannot say when a symptom started ("might have been last month or the month before"). Symptom: certainty "uncertain", no duration/onset. related symptoms[i], unresolved.
* uncertain_dose: speaker gives dose tentatively ("maybe 20 mg?"). Medication dose = as stated. related medications[i], unresolved.
* adherence_uncertain: frequency given but someone says doses are missed / unsure it is taken as prescribed. Keep BOTH statements in the dialogue (patient "every day"; carer "he skips the evening one"). related medications[i], unresolved. Do not decide who is right.
* incomplete_medication_name: speaker cannot name the medicine ("the small white heart tablet"). Medication name = that description; generic_name & normalized_name omitted (null). related medications[i].
* allergy_uncertain / allergy_disputed: see above.
* duration_disagreement: two speakers give different durations for the same symptom ("two weeks" vs "three weeks"). Symptom: duration {"value": null, "unit": "weeks", "normalized": "approximately 2 to 3 weeks"} (both numbers spoken), certainty "uncertain"... use "certain" only if the speakers resolve it; resolution_status "partially_resolved" (doctor summarises the range aloud); one line in contradictions_detected. related symptoms[i].
* conflicting_statement: patient denies a symptom, caregiver/family reports it. negative_findings entry (patient, the denial) + symptoms entry (certainty "disputed", reported_by the third party, status present, temporality current) ; related [negative_findings[i], symptoms[j]]; unresolved; one line in contradictions_detected.
* medication_discrepancy: two sources give different doses for the same current medicine (patient 75 mg vs nurse/carer 150 mg). Medication dose **null**, status currently_used; related medications[i]; unresolved; one line in contradictions_detected. (The prescribed-frequency stays recorded if said.)
* unknown_speaker: an utterance by an unidentified voice (role UNKNOWN) about a symptom; related symptoms[i], unresolved. Then quality `speaker_attribution_available` is false automatically.
`contradictions_detected` gets **exactly one line** for each of: conflicting_statement, medication_discrepancy, allergy_disputed, duration_disagreement (e.g. "Patient denies fever; caregiver reports fever (unresolved)."). `ambiguous_entities` = list of locations like `medications[1]` for unknown_speaker / incomplete_medication_name items (may be empty otherwise).
Features not in the plan do not appear; do not add uncertainty entries "just in case". If a speaker is merely unsure about something that is not in the list, keep it in the dialogue and do not label it.

## Clinical sense
Doses, drug names, vital-sign values and tests must be plausible. Doctors state assessments only when the plan allows. Don't have the doctor diagnose from thin air. Names of people are optional; if used, make them diverse and not shared across your encounters.
BP systolic - diastolic >= 20; HR 35-190; temperature 34.5-42; SpO2 80-100; RR 8-40.

## Self-check list before finishing each file
- PASS from the compiler. - Nothing said that is not in the label when it should be (every medication, allergy, vital, history item, assessment, test, follow-up that is spoken).
- Nothing in the label that was not said. - Targets respected (esp. the hard zeros). - Distinct opening, distinct closing, distinct structure from your other encounters.
- Patient speaks like a person, not a form. - No dialogue copied from the example.

## Lessons from the pilot (apply)
* Count turns by looking them up programmatically: build the `turns` list in Python and compute evidence numbers from text snippets (e.g. `idx("three or four coffees")`) rather than counting by hand.
* The negative finding for allergies is exactly `finding: "Allergies"`, `normalized_name: "No known allergies"`. It does NOT count toward the negative_findings target. A conditional follow_up time_reference starts with lowercase "if " ("if you can't keep fluids down for 24 hours"); its twin action has responsible_person "doctor".
* Allergy `severity` is filled with "unknown" automatically.
* Stay under ~510 s total: long `pause` values and 55+ long turns can pass 540 s. Use `pause` sparingly (exam/vitals, 8-20 s).
* Do not name a past operation, stent, dialysis, prior admission etc. in dialogue unless the plan has surgical_history / procedures / history entries for it; refer to it vaguely ("since you came out of hospital") or, when it is spoken, label it. Anything specific and spoken that is a history item (a procedure with a time, a chronic condition, a family illness) must be labelled, so avoid mentioning it if the plan says 0.
* Only use the speakers listed. An opening style that needs an unlisted person: use the nearest sensible alternative.
* When a medication is stated by the patient and its dose is read by a nurse, reported_by is the speaker who states the medicine name or dose in the cited turns (it must be among the cited speakers); with a discrepancy the two sources are different speakers.
* Dose units that the validator understands: mg/milligrams, g/grams, micrograms/mcg, ml, units, sachet. Write digits in the label ("75 mg") and either digits or number words in speech.
* A condition implied by a named drug ("the acid tablet") is labelled only if someone says the condition.
* Timing: speech is timed at ~0.5 s per word plus gaps. Total words should be roughly 650-1000 (about 12 words/turn average). Over ~1000 words risks >540 s; under ~600 words with few turns risks <300 s.
* Symptom category is checked against known names: sleep-related complaints (early waking, insomnia) are `neurological`, not psychiatric, if the validator complains; follow its message.
* A medication `indication` must be spoken in the cited turns (cite the turn where the patient/doctor says what it is for) or be omitted.
* Zero targets are hard: when negative_findings is 0 avoid any "no X"/"not X" denial of a clinical finding in the dialogue (the "Allergies" negative is a separate case).
* Doses: speak doses with DIGITS ("50 milligrams", "2.5 mg"); number words ("fifty milligrams") fail the dose check. Temperature values must be in °C. If a dose change is discussed (20 -> 18 units) only the new planned dose can be a medication entry.
* Many authors share one scratchpad: keep any helper scripts in a private subfolder named after your chunk index.
* Vital-sign numbers must be spoken as digits ("138 over 82", "pulse 72"). Symptom `name` must appear in the cited turns (cite the turn that contains the phrase). A resolved symptom needs "gone"/"settled"/"went away"/"resolved" in a cited turn. Category quirks: flushing/hot flushes - follow the validator message (cardiovascular / genitourinary).
* Prefer MORE short turns over fewer long ones: the plan's target_turns are the goal; ~12 words/turn on average.

* (DSL) shortcuts: "vitals":{"k":"v","by":"nurse","bp":"128/80","hr":68,"temp":36.6,"spo2":98,"rr":16,"wt":84} and "allergy_none":"a1".
* The 'Allergies' negative needs the literal word 'allergies' in a cited turn (question), not 'allergic'.
* (DSL v2 shortcuts) planned/conditional procedures get an automatic investigation action; follow_up entries get an automatic twin action; planned medications get an automatic medication action; "counsel":[["c1","Advise ..."]] makes counselling/recommended/patient actions. Tag the turns with the same keys.
* Say 'gram'/'grams' for g doses (validator needs 'gram' or 'g ').
* Durations/numbers >12 (except 14,15,20,30) must be spoken as digits; completed items need 'did/already/had'.
* Planned follow-up turn must contain a plan cue ('I'd like to see you', 'come back', 'see you in').
