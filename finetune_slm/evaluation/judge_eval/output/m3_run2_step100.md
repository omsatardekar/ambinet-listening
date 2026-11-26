# Realism check: fine-tuned step 400 on the 20 hand-written Module 3 scenarios

Clean dialogue text as input (no ASR errors), trained line format. No label file: recall is against the scenario `design` block (floor-style), precision is against the transcript. Same judge and frozen prompts as the test-set evaluation. Synthetic data only.

| encounters | precision | recall vs design | hallucination | critical |
|---|---|---|---|---|
| 20 | 0.722 | 0.207 | 0.204 | 0.085 |

## Per encounter

| encounter | predicted facts | precision | recall vs design | hallucination | critical |
|---|---|---|---|---|---|
| m3_01_foot_sore_bus_driver | 54 | 0.713 | 0.714 | 0.185 | 0.093 |
| m3_02_low_mood_wife_answers | 53 | 0.613 | 0.429 | 0.321 | 0.113 |
| m3_03_heart_tablets_bruising_carer | 0 | n/a | 0.000 | n/a | n/a |
| m3_04_hair_thinning_terse | 0 | n/a | 0.000 | n/a | n/a |
| m3_05_swollen_ankles_cant_lie_flat_ed | 0 | n/a | 0.000 | n/a | n/a |
| m3_06_hip_groin_pain_grandmother | 41 | 0.744 | 0.786 | 0.171 | 0.073 |
| m3_07_hearing_a_voice_at_night | 38 | 0.671 | 0.650 | 0.263 | 0.105 |
| m3_08_toddler_vaccination_runny_nose | 0 | n/a | 0.000 | n/a | n/a |
| m3_09_dizzy_on_standing_plumber | 0 | n/a | 0.000 | n/a | n/a |
| m3_10_high_calcium_found_by_chance | 0 | n/a | 0.000 | n/a | n/a |
| m3_11_rectal_bleeding_embarrassed | 35 | 0.800 | 0.455 | 0.114 | 0.086 |
| m3_12_cracked_hands_carer_and_pharmacy_tech | 0 | n/a | 0.000 | n/a | n/a |
| m3_13_forgetting_and_getting_lost | 0 | n/a | 0.000 | n/a | n/a |
| m3_14_fever_after_travel | 0 | n/a | 0.000 | n/a | n/a |
| m3_15_irregular_periods_night_sweats | 49 | 0.816 | 0.792 | 0.143 | 0.041 |
| m3_16_kitchen_knife_cut_hand | 0 | n/a | 0.000 | n/a | n/a |
| m3_17_burning_upper_stomach_after_meals | 0 | n/a | 0.000 | n/a | n/a |
| m3_18_hoarse_voice_primary_teacher | 0 | n/a | 0.000 | n/a | n/a |
| m3_19_prediabetes_what_happens_now | 0 | n/a | 0.000 | n/a | n/a |
| m3_20_diabetes_screening_symptom_diary | 0 | n/a | 0.000 | n/a | n/a |

## Facts the judge did not find supported by the transcript (95)

- m3_01_foot_sore_bus_driver [partially_supported] medical_history.past_medical_history: diabetes (status=ongoing, duration=many years, since her daughter was in school, reported_by=patient) — Diabetes for many years since daughter was in school; transcript says his daughter, not her.
- m3_01_foot_sore_bus_driver [partially_supported] symptoms: foot blister (category=dermatological, status=present, duration=approximately 1 to 2 weeks, temporality=current, body_site=right foot, under the skin near the toes, reported_by=patient, certainty=certain) — Right foot blister under front near toes supported; duration 1-2 weeks not stated.
- m3_01_foot_sore_bus_driver [partially_supported] symptoms: numbness (category=neurological, status=present, duration=approximately 1 to 2 weeks, temporality=current, body_site=both feet, aggravating_factors=sitting wrongly, reported_by=patient, certainty=certain) — Both feet numb/tingly for about a week supported; sitting wrongly was descriptive, not aggravating factor.
- m3_01_foot_sore_bus_driver [unsupported] symptoms: feeling unwell (category=constitutional, status=present, temporality=current, reported_by=patient, certainty=certain) — Feeling unwell is only given as return precaution, not reported present.
- m3_01_foot_sore_bus_driver [unsupported] symptoms: feeling shivering (category=constitutional, status=present, temporality=current, reported_by=patient, certainty=certain) — Shivering was asked/used in safety advice, not reported present.
- m3_01_foot_sore_bus_driver [unsupported] symptoms: feeling unwell (category=constitutional, status=resolved, temporality=resolved, reported_by=patient, certainty=certain) — No resolved feeling-unwell symptom stated.
- m3_01_foot_sore_bus_driver [unsupported] symptoms: feeling unwell (category=constitutional, status=resolved, temporality=resolved, reported_by=patient, certainty=certain) — No resolved feeling-unwell symptom stated.
- m3_01_foot_sore_bus_driver [unsupported] symptoms: feeling unwell (category=constitutional, status=resolved, temporality=resolved, reported_by=patient, certainty=certain) — No resolved feeling-unwell symptom stated.
- m3_01_foot_sore_bus_driver [contradicted, CRITICAL] negative_findings: high blood pressure (status=absent, assertion=negative, reported_by=patient, temporality=current) — Patient has high blood pressure and takes telmisartan.
- m3_01_foot_sore_bus_driver [contradicted, CRITICAL] negative_findings: high cholesterol (status=absent, assertion=negative, reported_by=patient, temporality=current) — Patient has high cholesterol and takes rosuvastatin.
- m3_01_foot_sore_bus_driver [contradicted, CRITICAL] negative_findings: high blood pressure (status=absent, assertion=negative, reported_by=patient, temporality=past) — Patient reports high blood pressure for nearly five years.
- m3_01_foot_sore_bus_driver [contradicted, CRITICAL] negative_findings: high blood pressure (status=absent, assertion=negative, reported_by=patient, temporality=past) — Patient reports high blood pressure for nearly five years.
- m3_01_foot_sore_bus_driver [partially_supported] medications: metformin (dose=500 mg, frequency=twice a day, indication=diabetes, status=currently_used, reported_by=patient) — Patient reports metformin 500 mg twice daily, but doctor says correct dose is unresolved.
- m3_01_foot_sore_bus_driver [partially_supported] medications: Ayurvedic powder (dose=1 tablet, frequency=in the morning, indication=stomach, status=currently_used, reported_by=patient) — Ayurvedic powder in morning for stomach supported; dose '1 tablet' is wrong/not stated.
- m3_01_foot_sore_bus_driver [partially_supported, CRITICAL] medications: amoxicillin with clavulanic acid (dose=625 mg, frequency=three times a day for seven days, indication=diabetes, status=planned, reported_by=doctor) — Drug, dose, frequency, duration planned; indication is foot infection, not diabetes.
- m3_01_foot_sore_bus_driver [partially_supported] vital_signs: temperature (value=38.1, unit=C, reported_by=nurse) — Nurse recorded temperature 38.3 C, not 38.1 C.
- m3_01_foot_sore_bus_driver [partially_supported] vital_signs: blood pressure (value=108/66, unit=mmHg, reported_by=nurse) — Nurse recorded blood pressure 109/77, not 108/66.
- m3_01_foot_sore_bus_driver [partially_supported] procedures_and_investigations: blood tests (type=laboratory, status=planned, requested_by=doctor, indication=infection and kidney function) — Blood tests planned for infection, sugar, and kidneys; sugar omitted from fact.
- m3_01_foot_sore_bus_driver [partially_supported] clinical_actions: Arrange blood tests for infection and kidney function (action_type=investigation, status=planned, responsible_person=doctor) — Doctor plans blood tests for infection and kidneys, also sugar not mentioned in fact.
- m3_01_foot_sore_bus_driver [contradicted] clinical_actions: Talk to the foot clinic about proper insoles (action_type=counselling, status=recommended, responsible_person=patient) — Doctor said 'we'll talk to the foot clinic,' not instructed patient counselling.
- m3_01_foot_sore_bus_driver [partially_supported] clinical_uncertainties: Metformin is prescribed once a day, but the patient says she takes one tablet always, and the clinic list says one thousand milligrams twice a day, so the correct dose is not yet established. (type=adherence_uncertain, related_entities=medications[0], resolution_status=unresolved) — Dose uncertainty supported, but fact incorrectly says she/prescribed once daily; transcript says he takes one tablet, clinic lists 1000 mg twice daily.
- m3_02_low_mood_wife_answers [partially_supported] medical_history.past_medical_history: depression (status=ongoing, duration=approximately 5 years, reported_by=patient) — Depression mentioned, but not ongoing and not stated as approximately 5 years.
- m3_02_low_mood_wife_answers [unsupported] medical_history.social_history: alcohol (description=A can of tea with tea sometimes, not much, status=current, reported_by=patient) — Transcript says a can with tea, not 'a can of tea with tea'.
- m3_02_low_mood_wife_answers [partially_supported] medical_history.social_history: exercise (description=Little activity, mostly staying in, status=none, reported_by=patient) — Patient says he mostly stays in, but exercise is not explicitly discussed and status 'none' is overstated.
- m3_02_low_mood_wife_answers [unsupported] symptoms: headache (category=neurological, status=present, duration=approximately 3 to 4 weeks, temporality=current, reported_by=patient, certainty=certain) — Patient mentions using headache as an excuse, not having headaches.
- m3_02_low_mood_wife_answers [unsupported] symptoms: chest tightness (category=cardiovascular, status=resolved, duration=approximately 3 to 4 weeks, temporality=resolved, reported_by=patient, certainty=certain) — Chest tightness was in the spring, not for approximately 3 to 4 weeks.
- m3_02_low_mood_wife_answers [unsupported] symptoms: sleepiness (category=neurological, status=present, frequency=not much, mostly staying in, temporality=current, reported_by=patient, certainty=certain) — Patient describes low energy, not sleepiness; stated frequency text is unrelated.
- m3_02_low_mood_wife_answers [contradicted, CRITICAL] symptoms: weight loss (category=constitutional, status=resolved, temporality=resolved, reported_by=family_member, certainty=certain) — Family member says he has not lost weight.
- m3_02_low_mood_wife_answers [unsupported] symptoms: headache (category=neurological, status=resolved, duration=approximately 3 to 4 weeks, temporality=resolved, reported_by=patient, certainty=certain) — No resolved headache symptom reported; headache was only an excuse.
- m3_02_low_mood_wife_answers [unsupported] symptoms: sleepiness (category=neurological, status=present, frequency=not much, mostly staying in, temporality=current, reported_by=patient, certainty=certain) — No sleepiness reported; frequency/details are unrelated to sleepiness.
- m3_02_low_mood_wife_answers [contradicted, CRITICAL] symptoms: weight loss (category=constitutional, status=resolved, temporality=resolved, reported_by=family_member, certainty=certain) — Family member says he has not lost weight.
- m3_02_low_mood_wife_answers [partially_supported, CRITICAL] negative_findings: Allergies (status=absent, assertion=negative, reported_by=patient, temporality=current) — Patient denies allergies, but possible diclofenac reaction is recorded as uncertain.
- m3_02_low_mood_wife_answers [partially_supported, CRITICAL] medications: atorvastatin (dose=20 mg, frequency=at night, indication=cholesterol, status=currently_used, reported_by=patient) — Atorvastatin at night for cholesterol supported, but dose uncertain: patient says 20 or maybe 40.
- m3_02_low_mood_wife_answers [partially_supported, CRITICAL] medications: sertraline (duration=approximately 3 years, indication=depression, status=discontinued, reported_by=patient) — Sertraline was stopped, but duration about 3 years and indication depression were not stated.
- m3_02_low_mood_wife_answers [partially_supported, CRITICAL] allergies: diclofenac (allergy_type=medication, reaction=rash all over the arms, severity=unknown, status=reported, reported_by=family_member) — Family reports rash after diclofenac, but doctor records it as possible/uncertain, not confirmed reported allergy.
- m3_02_low_mood_wife_answers [partially_supported] vital_signs: blood pressure (value=120/79, unit=mmHg, reported_by=doctor) — Doctor states blood pressure 124/79, not 120/79.
- m3_02_low_mood_wife_answers [unsupported] physical_examination: restful sitting (body_site=sitting, status=present, observed_by=doctor) — Restful sitting was asked about, not observed as a physical exam finding.
- m3_02_low_mood_wife_answers [unsupported] physical_examination: lying there full of thoughts (body_site=lying, status=present, observed_by=doctor) — This is a symptom report during sleep history, not a physical examination finding.
- m3_02_low_mood_wife_answers [unsupported] clinical_actions: Ask not to sit in a toilet at work for ten minutes every morning (action_type=counselling, status=recommended, responsible_person=patient) — Doctor expressed concern about toilet-sitting, but did not instruct patient not to do it.
- m3_02_low_mood_wife_answers [unsupported] clinical_actions: Come with the questionnaire and the blood form (action_type=counselling, status=recommended, responsible_person=patient) — No instruction to come with questionnaire and blood form was stated.
- m3_02_low_mood_wife_answers [unsupported] clinical_actions: Two sets of ears are better than one (action_type=counselling, status=recommended, responsible_person=patient) — Doctor says two sets of ears are better than one about wife attending, not counselling the patient directly.
- m3_02_low_mood_wife_answers [unsupported] clinical_uncertainties: The patient says the tiredness began about three weeks ago and that the wife said it was before the leaves, but the wife said it was before the leaves and the patient said it was about three weeks ago. (type=date_uncertain, related_entities=symptoms[0], resolution_status=partially_resolved) — Before-the-leaves comment concerned allotment attendance, not tiredness onset.
- m3_02_low_mood_wife_answers [unsupported] clinical_uncertainties: The patient says the tiredness began about three weeks ago and that the wife said it was before the leaves, but the wife said it was before the leaves and the patient said it was about three weeks ago. (type=date_uncertain, related_entities=symptoms[0], resolution_status=partially_resolved) — Before-the-leaves comment concerned allotment attendance, not tiredness onset.
- m3_02_low_mood_wife_answers [unsupported] clinical_uncertainties: The patient says the tiredness began about three weeks ago and that the wife said it was before the leaves, but the wife said it was before the leaves and the patient said it was about three weeks ago. (type=date_uncertain, related_entities=symptoms[0], resolution_status=partially_resolved) — Before-the-leaves comment concerned allotment attendance, not tiredness onset.
- m3_02_low_mood_wife_answers [unsupported] clinical_uncertainties: A confirming remark about the tiredness was made, but the speaker is unknown. (type=unknown_speaker, related_entities=symptoms[0], resolution_status=unresolved) — No unknown speaker made a confirming remark about tiredness.
- m3_06_hip_groin_pain_grandmother [partially_supported] medical_history.past_medical_history: arthritis in my knees (status=ongoing, duration=wear and tear, reported_by=patient) — Knee arthritis is supported; 'duration=wear and tear' is wrong because wear and tear describes type, not duration.
- m3_06_hip_groin_pain_grandmother [partially_supported] medical_history.social_history: living (description=Lives with her mother, who is 91, and her grandchildren, most days, and the two little ones, who live with her mother's work at home., status=current, details=Lives with her mother, who is 91, and her grandchildren, most days, and the two little ones, who live with her mother's work at home., reported_by=patient) — Lives with 91-year-old mother and looks after grandchildren most days; wording about grandchildren living there/mother's work is wrong.
- m3_06_hip_groin_pain_grandmother [partially_supported] symptoms: groin pain (category=musculoskeletal, status=present, duration=approximately 6 months to 1 year, frequency=not all the time, worse after sitting, onset=since the winter, temporality=current, body_site=groin, aggravating_factors=getting up after sitting, relieving_factors=getting up after sitting, reported_by=patient, certainty=certain) — Groin pain details supported except relieving_factors is wrong; getting up after sitting aggravates, not relieves.
- m3_06_hip_groin_pain_grandmother [partially_supported] symptoms: hip stiffness (category=musculoskeletal, status=present, duration=a few minutes after sitting, temporality=current, body_site=hip, aggravating_factors=after sitting, relieving_factors=putting shoes on, reported_by=patient, certainty=certain) — Hip stiffness after sitting for a few minutes is supported; 'putting shoes on' is difficulty, not a relieving factor.
- m3_06_hip_groin_pain_grandmother [contradicted, CRITICAL] negative_findings: back pain (status=absent, assertion=negative, reported_by=patient, temporality=current) — Patient reports some back ache, so back pain is not absent.
- m3_06_hip_groin_pain_grandmother [partially_supported] negative_findings: pins and needles (status=absent, assertion=negative, reported_by=patient, temporality=current) — Pins and needles were asked about but not explicitly answered.
- m3_06_hip_groin_pain_grandmother [contradicted, CRITICAL] medications: naproxen (generic_name=paracetamol, dose=50 mg, frequency=when needed, status=currently_used, reported_by=patient) — Naproxen is rejected; paracetamol is advised later, not current naproxen 50 mg.
- m3_06_hip_groin_pain_grandmother [contradicted, CRITICAL] medications: leviteracetam (status=discontinued, reported_by=patient) — Levetiracetam is listed as current medication, not discontinued.
- m3_06_hip_groin_pain_grandmother [partially_supported] vital_signs: blood pressure (value=18/77, unit=mmHg, reported_by=nurse) — Blood pressure was 118/77, not 18/77.
- m3_06_hip_groin_pain_grandmother [contradicted] physical_examination: left hip pain much further than the right (body_site=left hip, status=present, observed_by=doctor) — Doctor says left hip goes much further; pain is on the right, not left.
- m3_06_hip_groin_pain_grandmother [partially_supported] clinical_actions: Keep moving and do not carry extra weight (action_type=counselling, status=recommended, responsible_person=patient) — This advice was given to Sharon, not the patient.
- m3_06_hip_groin_pain_grandmother [unsupported] clinical_actions: Bend the hip up, then roll it in and out, as far as it will go, and tell the patient when it hurts (action_type=counselling, status=recommended, responsible_person=patient) — This was an examination instruction by doctor, not counselling or recommendation.
- m3_06_hip_groin_pain_grandmother [unsupported] clinical_actions: Sit up whenever ready, and keep moving and do not carry extra weight (action_type=counselling, status=recommended, responsible_person=patient) — Combines exam instruction with advice; no such counselling action stated.
- m3_06_hip_groin_pain_grandmother [unsupported] clinical_uncertainties: A confirming remark about the hip pain was made by the unknown speaker. (type=unknown_speaker, related_entities=symptoms[0], resolution_status=unresolved) — No unknown speaker made a confirming remark about hip pain.
- m3_07_hearing_a_voice_at_night [partially_supported] chief_complaint: A woman's voice at night (reported_by=patient) — Voice at night is supported; gender is uncertain, not clearly a woman's voice.
- m3_07_hearing_a_voice_at_night [partially_supported] medical_history.past_medical_history: Depression (status=ongoing, duration=approximately 11 years ago, reported_by=patient) — Depression 11 years ago is supported, but status is past, not ongoing.
- m3_07_hearing_a_voice_at_night [partially_supported] symptoms: voice (category=neurological, status=present, duration=approximately 7 to 8 times a month, frequency=at night, temporality=current, reported_by=patient, certainty=certain) — Occurs seven or eight times this month, not per month.
- m3_07_hearing_a_voice_at_night [contradicted, CRITICAL] symptoms: feeling someone touching you (category=neurological, status=present, temporality=current, reported_by=patient, certainty=certain) — Patient denies feeling someone touching her.
- m3_07_hearing_a_voice_at_night [contradicted, CRITICAL] symptoms: smelling something (category=other, status=present, temporality=current, reported_by=patient, certainty=certain) — Patient denies smelling something.
- m3_07_hearing_a_voice_at_night [unsupported] negative_findings: Harm to himself (status=absent, assertion=negative, reported_by=patient, temporality=current) — Fact says 'himself'; transcript concerns patient denying harm to herself.
- m3_07_hearing_a_voice_at_night [unsupported] negative_findings: Harming himself (status=absent, assertion=negative, reported_by=patient, temporality=current) — Fact says 'himself'; transcript concerns patient denying harm to herself.
- m3_07_hearing_a_voice_at_night [unsupported] negative_findings: Harming himself (status=absent, assertion=negative, reported_by=patient, temporality=current) — Fact says 'himself'; transcript concerns patient denying harm to herself.
- m3_07_hearing_a_voice_at_night [partially_supported, CRITICAL] medications: sertraline (dose=100 mg, frequency=once a day, indication=sleep, status=currently_used, reported_by=nurse) — Sertraline current once daily is supported; dose is unresolved, and indication sleep is not stated; not reported by nurse.
- m3_07_hearing_a_voice_at_night [partially_supported, CRITICAL] medications: levothyroxine (dose=75 mg, frequency=once a day, duration=forever, status=currently_used, reported_by=nurse) — Drug, 75 dose, once daily, current supported; dose unit should be mcg not mg, and patient stated 'forever,' not nurse.
- m3_07_hearing_a_voice_at_night [unsupported] vital_signs: temperature (value=37.5, unit=C, reported_by=patient) — No temperature value of 37.5 C stated; doctor says not feverish and no temperature.
- m3_07_hearing_a_voice_at_night [unsupported] physical_examination: Follow my finger (body_site=hand, status=present, observed_by=doctor) — Doctor says 'Follow my finger' as instruction, not a present physical finding at hand.
- m3_07_hearing_a_voice_at_night [contradicted] review_of_systems: psychiatric (status=negative, reported_by=patient) — Psychiatric ROS is not negative; patient reports low mood.
- m3_07_hearing_a_voice_at_night [unsupported] clinical_actions: Ring the crisis line if thoughts about harming himself, the voice starts telling you to do things, or if the voice starts in the day (action_type=counselling, status=recommended, responsible_person=patient) — Fact says 'harming himself'; transcript instructs patient about harming herself.
- m3_07_hearing_a_voice_at_night [unsupported] clinical_uncertainties: The patient says he takes a hundred milligrams of sertraline, but the pharmacy record says 50 mg, and the nurse is not sure whether he took two of the 50 mg tablets or the 100 mg tablets. (type=uncertain_dose, related_entities=medications[0], resolution_status=unresolved) — Uses wrong sex and misstates uncertainty; issue is patient vs pharmacy 100 vs 50, possible two 50s.
- m3_11_rectal_bleeding_embarrassed [partially_supported] medical_history.past_medical_history: breathlessness on the stairs (status=ongoing, duration=nearly 8 years, reported_by=patient) — Breathlessness on stairs is stated, but nearly eight years refers to heart failure, not breathlessness.
- m3_11_rectal_bleeding_embarrassed [unsupported] medical_history.social_history: occupation (description=Works as a daughter, status=current, details=my daughter works, reported_by=patient) — Transcript says daughter works; it does not state patient's occupation.
- m3_11_rectal_bleeding_embarrassed [partially_supported] medical_history.social_history: exercise (description=Lifting and bending, status=current, details=a lot of lifting, though, and a lot of bending, reported_by=patient) — Lifting and bending are discussed, but doctor states it; patient only agrees.
- m3_11_rectal_bleeding_embarrassed [partially_supported] symptoms: bright red blood on the toilet (category=gastrointestinal, status=present, duration=approximately 10 to 2 weeks, frequency=streaks or a few drops, temporality=current, reported_by=patient, certainty=certain) — Bright red blood and duration supported, but it's on paper/outside, not 'on the toilet'.
- m3_11_rectal_bleeding_embarrassed [contradicted, CRITICAL] symptoms: black stools (category=gastrointestinal, status=present, temporality=current, reported_by=patient, certainty=certain) — Patient denies black stools; dark stools were only when taking iron, not black tarry stools.
- m3_11_rectal_bleeding_embarrassed [partially_supported] symptoms: light-headedness (category=neurological, status=present, duration=mornings, temporality=current, reported_by=patient, certainty=certain) — Patient reports being a little light-headed in the mornings, but says it is not new.
- m3_11_rectal_bleeding_embarrassed [contradicted, CRITICAL] negative_findings: Dizzy (status=absent, assertion=negative, reported_by=patient, temporality=current) — Patient reports a little dizziness/light-headedness in the mornings.
- m3_11_rectal_bleeding_embarrassed [contradicted] negative_findings: Weight loss (status=absent, assertion=negative, reported_by=patient, temporality=current) — Patient reports losing a couple of kilos this year.
- m3_11_rectal_bleeding_embarrassed [partially_supported, CRITICAL] medications: iron tablets (generic_name=iron, frequency=once a day, indication=water, status=currently_used, reported_by=patient) — Iron tablets once daily and current use supported, but indication 'water' is wrong.
- m3_11_rectal_bleeding_embarrassed [partially_supported] clinical_assessment: Possible rectal bleeding, rectal lump, and weight loss (certainty=provisional, basis=Rectal bleeding, rectal lump, and weight loss, stated_by=doctor) — Doctor cites bleeding and weight/blood count concerns, but does not explicitly assess a rectal lump and weight loss as a combined diagnosis.
- m3_15_irregular_periods_night_sweats [partially_supported] medical_history.social_history: alcohol (description=A glass of wine at the weekend, status=current, reported_by=patient) — Alcohol use supported, but transcript says a glass, perhaps two, at the weekend.
- m3_15_irregular_periods_night_sweats [partially_supported] symptoms: Flushes (category=genitourinary, status=present, frequency=in meetings, temporality=current, reported_by=patient, certainty=certain) — Flushes supported, but 'in meetings' is context, not stated frequency.
- m3_15_irregular_periods_night_sweats [contradicted, CRITICAL] symptoms: Crying in meetings (category=psychiatric, status=present, temporality=current, reported_by=patient, certainty=certain) — Patient cried afterwards in the car park, not in meetings.
- m3_15_irregular_periods_night_sweats [contradicted] symptoms: Back to sleep (category=neurological, status=present, temporality=current, reported_by=patient, certainty=certain) — Patient says she gets back to sleep eventually, not as a symptom/problem present.
- m3_15_irregular_periods_night_sweats [unsupported] negative_findings: Changes to the nipples (status=absent, assertion=negative, reported_by=patient, temporality=current) — No patient denial or doctor finding about nipple changes.
- m3_15_irregular_periods_night_sweats [partially_supported] negative_findings: Palpitations (status=absent, assertion=negative, reported_by=patient, temporality=current) — Mostly denied, but patient reports occasional thump at night with hot flush.
- m3_15_irregular_periods_night_sweats [unsupported] negative_findings: Thyroid problems (status=absent, assertion=negative, reported_by=patient, temporality=current) — No thyroid problem denial; thyroid was examined and testing planned.
- m3_15_irregular_periods_night_sweats [partially_supported] clinical_assessment: Perimenopause (certainty=provisional, basis=Irregular periods, night sweats, mood changes, and a thin bone scan, stated_by=doctor) — Perimenopause provisional assessment supported, but basis mentions flushes, not thin bone scan.
- m3_15_irregular_periods_night_sweats [contradicted, CRITICAL] clinical_actions: Start hormone replacement (action_type=medication, status=planned, responsible_person=doctor) — Doctor explicitly says she does not want to start hormone replacement today.
- m3_15_irregular_periods_night_sweats [unsupported] clinical_actions: Take alendronic acid on an empty stomach with water and stay upright for half an hour (action_type=counselling, status=recommended, responsible_person=patient) — This was patient describing current alendronate instructions, not new counselling given.
- m3_15_irregular_periods_night_sweats [unsupported] clinical_actions: Dana may be right about hormone replacement, especially for osteoporosis (action_type=counselling, status=recommended, responsible_person=patient) — Dana said concern about cancer; doctor did not say Dana may be right about HRT.

## Design facts or doubts the output did not convey fully (198)

- m3_01_foot_sore_bus_driver [partially_found] denies confusion, calf pain, pain at rest, chest pain, vomiting — Chest pain and vomiting present; calf pain/rest pain mismatched, confusion missing.
- m3_01_foot_sore_bus_driver [partially_found] type 2 diabetes, high blood pressure, high cholesterol — Diabetes found, but hypertension and hypercholesterolemia recorded incorrectly as absent.
- m3_01_foot_sore_bus_driver [partially_found] temperature 38.3, pulse 88, BP 109/77, weight 52 kg — Pulse and weight match; temperature and BP values differ.
- m3_01_foot_sore_bus_driver [partially_found] weak ankle pulses, 2 cm ulcer ball of right foot with redness — Weak ankle pulses and right foot ulcer with redness found; 2 cm size and ball location missing.
- m3_01_foot_sore_bus_driver [missing] The record should show this doubt or gap, not a confident fact: how long the foot sore has been there is never stated — Predicted facts state sore duration 1 to 2 weeks instead of leaving it unstated.
- m3_01_foot_sore_bus_driver [missing] The record should show this doubt or gap, not a confident fact: doctor never asks about family history (the patient mentions a brother heart attack and a cousin only in passing) — No predicted uncertainty about absent family history discussion.
- m3_02_low_mood_wife_answers [partially_found] no energy and losing interest, about three weeks — Low energy present for ~3-4 weeks, but losing interest/anhedonia is not captured.
- m3_02_low_mood_wife_answers [partially_found] tight chest when stressed, now gone — Resolved chest tightness captured, but trigger 'when stressed' is missing.
- m3_02_low_mood_wife_answers [partially_found] denies chest pain, thoughts of harming himself, weight loss, panic attacks, hearing voices — Chest pain, self-harm thoughts, panic attacks, hearing voices covered; weight loss wrongly recorded as resolved, not denied.
- m3_02_low_mood_wife_answers [partially_found] anxiety for about five years, earlier depression — Anxiety for ~5 years captured, but depression incorrectly marked ongoing instead of earlier/past.
- m3_02_low_mood_wife_answers [partially_found] atorvastatin, sertraline stopped — Atorvastatin and stopped sertraline captured, but atorvastatin dose stated confidently despite patient uncertainty.
- m3_02_low_mood_wife_answers [partially_found] heart rate 75, oxygen 98, BP 124/79 — Heart rate 75 and oxygen 98 match; blood pressure is 120/79, not 124/79.
- m3_02_low_mood_wife_answers [missing] tearful when talking about work — No tearfulness or emotion when discussing work documented.
- m3_02_low_mood_wife_answers [missing] The record should show this doubt or gap, not a confident fact: atorvastatin dose: patient thinks twenty, not sure — Atorvastatin dose uncertainty absent; dose recorded as confident 20 mg.
- m3_02_low_mood_wife_answers [partially_found] The record should show this doubt or gap, not a confident fact: sertraline was stopped by the patient on his own, dose never stated, month uncertain — Sertraline discontinuation captured, but self-stopped and dose/month uncertainty are missing.
- m3_02_low_mood_wife_answers [missing] The record should show this doubt or gap, not a confident fact: allergy disputed: wife says diclofenac gave him a rash, he says it was a heat rash — Disputed diclofenac allergy not shown; allergy recorded confidently from wife only.
- m3_02_low_mood_wife_answers [partially_found] The record should show this doubt or gap, not a confident fact: an unidentified voice from the doorway interrupts twice and is never identified — Unknown speaker uncertainty captured, but not that it interrupted twice from the doorway.
- m3_02_low_mood_wife_answers [missing] The record should show this doubt or gap, not a confident fact: doctor states no diagnosis — No explicit uncertainty or statement that doctor made no diagnosis.
- m3_03_heart_tablets_bruising_carer [missing] chest tightness on the stairs for nearly five years, unchanged — no output
- m3_03_heart_tablets_bruising_carer [missing] indigestion after tablets for about a year — no output
- m3_03_heart_tablets_bruising_carer [missing] tired, easy bruising for three weeks — no output
- m3_03_heart_tablets_bruising_carer [missing] denies breathlessness, blood in urine, fainting, palpitations, black stools — no output
- m3_03_heart_tablets_bruising_carer [missing] heart disease, high cholesterol, diabetes — no output
- m3_03_heart_tablets_bruising_carer [missing] metoprolol 50 twice a day, simvastatin 20 at night, glimepiride, aspirin, clopidogrel — no output
- m3_03_heart_tablets_bruising_carer [missing] allergy to plasters and to tramadol, reactions not known — no output
- m3_03_heart_tablets_bruising_carer [missing] smokes about eight a day, stopped heavy drinking four years ago, grandmother had dementia — no output
- m3_03_heart_tablets_bruising_carer [missing] BP 119/74, resp rate 18, temp 36.7, pulse 66, oxygen 98 — no output
- m3_03_heart_tablets_bruising_carer [missing] normal heart sounds, clear chest, small bruises on forearms — no output
- m3_03_heart_tablets_bruising_carer [missing] plan: pantoprazole 40 before breakfast, blood count, ECG, return if black stools or bleeding that will not stop — no output
- m3_03_heart_tablets_bruising_carer [missing] The record should show this doubt or gap, not a confident fact: whether the patient takes the aspirin every day is unclear (carer fills the pill box, patient sometimes pushes the white one aside) — no output
- m3_03_heart_tablets_bruising_carer [missing] The record should show this doubt or gap, not a confident fact: reactions to plasters and tramadol are not remembered — no output
- m3_03_heart_tablets_bruising_carer [missing] The record should show this doubt or gap, not a confident fact: the clopidogrel strength is not stated by anyone — no output
- m3_04_hair_thinning_terse [missing] hair thinning for about six months — no output
- m3_04_hair_thinning_terse [missing] more hair coming out in the shower and on the brush — no output
- m3_04_hair_thinning_terse [missing] one blood test (iron stores and thyroid) is arranged — no output
- m3_04_hair_thinning_terse [missing] one treatment is started: minoxidil foam, twice a day — no output
- m3_05_swollen_ankles_cant_lie_flat_ed [missing] swollen ankles and breathless lying flat, sleeping in the recliner, woke gasping once — no output
- m3_05_swollen_ankles_cant_lie_flat_ed [missing] no chest pain — no output
- m3_05_swollen_ankles_cant_lie_flat_ed [missing] heart attack some years ago, knee replacement — no output
- m3_05_swollen_ankles_cant_lie_flat_ed [missing] lisinopril and a small yellow tablet for fluid — no output
- m3_05_swollen_ankles_cant_lie_flat_ed [missing] lives alone, aide visits daily — no output
- m3_05_swollen_ankles_cant_lie_flat_ed [missing] BP 148/92, pulse 102, resp 24, oxygen 91 on room air, temp 36.9, weight 94 kg — no output
- m3_05_swollen_ankles_cant_lie_flat_ed [missing] swollen legs to the knees, crackles at both lung bases — no output
- m3_05_swollen_ankles_cant_lie_flat_ed [missing] ECG, chest X-ray, blood tests — no output
- m3_05_swollen_ankles_cant_lie_flat_ed [missing] admit if oxygen does not improve — no output
- m3_05_swollen_ankles_cant_lie_flat_ed [missing] The record should show this doubt or gap, not a confident fact: duration: patient says since Tuesday, aide says the ankles have been puffy for over a week — no output
- m3_05_swollen_ankles_cant_lie_flat_ed [missing] The record should show this doubt or gap, not a confident fact: patient cannot name his water tablet, describes it — no output
- m3_05_swollen_ankles_cant_lie_flat_ed [missing] The record should show this doubt or gap, not a confident fact: allergies are never discussed — no output
- m3_05_swollen_ankles_cant_lie_flat_ed [missing] The record should show this doubt or gap, not a confident fact: diagnosis is only provisional, disposition is conditional on results — no output
- m3_06_hip_groin_pain_grandmother [missing] earlier groin pain settled — No predicted fact states an earlier groin pain episode that settled.
- m3_06_hip_groin_pain_grandmother [partially_found] hydrochlorothiazide, an anti-inflammatory, an epilepsy tablet — Hydrochlorothiazide and anti-inflammatory present; epilepsy tablet recorded as discontinued, not current.
- m3_06_hip_groin_pain_grandmother [partially_found] BP 118/77, pulse 82, oxygen 97, resp 15, temp 36.8 — All vitals present, but blood pressure value is wrong: 18/77 vs 118/77.
- m3_06_hip_groin_pain_grandmother [missing] The record should show this doubt or gap, not a confident fact: an earlier episode of groin pain two years ago that settled — No uncertainty or fact about a groin pain episode two years ago that settled.
- m3_07_hearing_a_voice_at_night [partially_found] hears a voice calling her name at night, in bed, several times in recent weeks, frightened — Night voice present, but missing calling her name, being in bed, frightened; frequency conflicts with vague recent weeks.
- m3_07_hearing_a_voice_at_night [partially_found] no thoughts of harming herself, no voice in the daytime — No self-harm thoughts found; no daytime voice only implied in safety advice, not documented as current negative finding.
- m3_07_hearing_a_voice_at_night [partially_found] depression in the past — Depression documented, but status wrongly marked ongoing instead of past.
- m3_07_hearing_a_voice_at_night [partially_found] sertraline (dose disputed) and levothyroxine — Both medicines present, but levothyroxine dose wrong and sertraline dose recorded confidently despite unresolved dispute.
- m3_07_hearing_a_voice_at_night [missing] The record should show this doubt or gap, not a confident fact: how many nights it has happened is vague ("a few times, maybe more") — No uncertainty about number of nights; instead gives confident 7 to 8 times a month.
- m3_07_hearing_a_voice_at_night [partially_found] The record should show this doubt or gap, not a confident fact: what the voice says is only partly remembered — Voice content partly represented as a woman's voice/name, but uncertainty about exactly what was said is absent.
- m3_08_toddler_vaccination_runny_nose [missing] routine vaccinations due — no output
- m3_08_toddler_vaccination_runny_nose [missing] runny nose for three days, no fever, no cough — no output
- m3_08_toddler_vaccination_runny_nose [missing] reaction to egg as a baby (hives and swollen lip), now eats baked egg without trouble — no output
- m3_08_toddler_vaccination_runny_nose [missing] no regular medicines — no output
- m3_08_toddler_vaccination_runny_nose [missing] bronchiolitis admission as a baby — no output
- m3_08_toddler_vaccination_runny_nose [missing] plan: temperature 37.1, MMR and the four-in-one booster given, 15 minutes observation, paracetamol if sore — no output
- m3_08_toddler_vaccination_runny_nose [missing] The record should show this doubt or gap, not a confident fact: the decision to vaccinate depends on the temperature the nurse takes during the visit — no output
- m3_08_toddler_vaccination_runny_nose [missing] The record should show this doubt or gap, not a confident fact: what exactly happened with the egg is only partly remembered (rash and lip swelling, once, at about one year) — no output
- m3_08_toddler_vaccination_runny_nose [missing] The record should show this doubt or gap, not a confident fact: the child's weight is not measured — no output
- m3_09_dizzy_on_standing_plumber [missing] dizzy when she stands up, nearly blacked out once, weak for about a week — no output
- m3_09_dizzy_on_standing_plumber [missing] no vomiting, fainting, black stools, slurred speech, chest pain, palpitations — no output
- m3_09_dizzy_on_standing_plumber [missing] high blood pressure about a year, anxiety — no output
- m3_09_dizzy_on_standing_plumber [missing] hydrochlorothiazide (not named), escitalopram stopped, propranolol — no output
- m3_09_dizzy_on_standing_plumber [missing] hernia operation last spring, father has Parkinson's, plumber, a glass of wine with dinner — no output
- m3_09_dizzy_on_standing_plumber [missing] lying then standing BP, pulse 107, resp 19, temp 36.4, oxygen 98 — no output
- m3_09_dizzy_on_standing_plumber [missing] plan: ECG, repeat lying and standing pressure, bloods; review after the results — no output
- m3_09_dizzy_on_standing_plumber [missing] The record should show this doubt or gap, not a confident fact: duration: she says since Monday, he says about two weeks — no output
- m3_09_dizzy_on_standing_plumber [missing] The record should show this doubt or gap, not a confident fact: one tablet is identified only as the round yellow one for her pressure — no output
- m3_09_dizzy_on_standing_plumber [missing] The record should show this doubt or gap, not a confident fact: she stopped the escitalopram without being sure when, and takes the propranolol only when she remembers — no output
- m3_09_dizzy_on_standing_plumber [missing] The record should show this doubt or gap, not a confident fact: allergy: a reaction to some antibiotic as a child, name unknown — no output
- m3_10_high_calcium_found_by_chance [missing] very thirsty and passing a lot of water, tired, constipated, vague aches — no output
- m3_10_high_calcium_found_by_chance [missing] no confusion, no vomiting — no output
- m3_10_high_calcium_found_by_chance [missing] arthritis in the hands — no output
- m3_10_high_calcium_found_by_chance [missing] one calcium and vitamin D supplement (dose disputed) — no output
- m3_10_high_calcium_found_by_chance [missing] no allergies — no output
- m3_10_high_calcium_found_by_chance [missing] retired school cook — no output
- m3_10_high_calcium_found_by_chance [missing] temperature 36.7, BP 134/80, pulse 74 — no output
- m3_10_high_calcium_found_by_chance [missing] tender in the belly on deep press, otherwise normal — no output
- m3_10_high_calcium_found_by_chance [missing] The record should show this doubt or gap, not a confident fact: the dose of her calcium or vitamin D supplement is given differently by the patient and by her son — no output
- m3_10_high_calcium_found_by_chance [missing] The record should show this doubt or gap, not a confident fact: she cannot say when she last drank enough or how often she passes water — no output
- m3_10_high_calcium_found_by_chance [missing] The record should show this doubt or gap, not a confident fact: the doctor never names a diagnosis, orders no new test beyond what is already done, and arranges no follow-up — no output
- m3_11_rectal_bleeding_embarrassed [partially_found] a lump near the back passage, discomfort when sitting for about a week, bright red blood on the paper — Lump, sitting discomfort, bright red bleeding found; bleeding recorded as toilet, not specifically on paper.
- m3_11_rectal_bleeding_embarrassed [missing] constipation now resolved — No predicted fact states constipation resolved.
- m3_11_rectal_bleeding_embarrassed [partially_found] no black stools, severe pain, dizziness, fever, weight loss, change in bowel habit — Negatives for black stools, severe pain, dizziness, fever, weight loss found; change in bowel habit missing.
- m3_11_rectal_bleeding_embarrassed [partially_found] low blood count for years, heart failure — Heart failure found; longstanding low blood count missing.
- m3_11_rectal_bleeding_embarrassed [partially_found] iron tablets and spironolactone 25 — Iron tablets and spironolactone 25 found; iron tablet specifics uncertain/inaccurate.
- m3_11_rectal_bleeding_embarrassed [partially_found] plan: blood count Thursday at 10, a camera test of the bowel, review in four weeks, return if bleeding heavier or faint — CBC Thursday morning, bowel camera test, four-week review, return if heavier bleeding/faint found; 10 o'clock missing.
- m3_11_rectal_bleeding_embarrassed [missing] The record should show this doubt or gap, not a confident fact: the patient cannot name her iron tablets or her water tablet — No uncertainty that patient cannot name iron or water tablets.
- m3_11_rectal_bleeding_embarrassed [partially_found] The record should show this doubt or gap, not a confident fact: the doctor never states a diagnosis: he says he does not want to guess and offers possibilities in passing only — Provisional assessment shown, but still states possible diagnoses rather than explicitly avoiding diagnosis.
- m3_11_rectal_bleeding_embarrassed [missing] The record should show this doubt or gap, not a confident fact: no examination is done today, the patient asks to wait — No fact indicates examination deferred today at patient request.
- m3_12_cracked_hands_carer_and_pharmacy_tech [missing] red, cracked hands, blisters between fingers, drier skin that has settled — no output
- m3_12_cracked_hands_carer_and_pharmacy_tech [missing] denies a new soap or cream, oozing, fever, joint pain, rash elsewhere, nail changes — no output
- m3_12_cracked_hands_carer_and_pharmacy_tech [missing] eczema, acid reflux — no output
- m3_12_cracked_hands_carer_and_pharmacy_tech [missing] hydrocortisone cream, simvastatin, furosemide — no output
- m3_12_cracked_hands_carer_and_pharmacy_tech [missing] tonsils out as a teenager, son has asthma, brother has epilepsy — no output
- m3_12_cracked_hands_carer_and_pharmacy_tech [missing] smokes about eight a day, fast food at lunch — no output
- m3_12_cracked_hands_carer_and_pharmacy_tech [missing] allergy to grass pollen (sneezing) — no output
- m3_12_cracked_hands_carer_and_pharmacy_tech [missing] red, dry, cracked skin in the finger creases, no weeping — no output
- m3_12_cracked_hands_carer_and_pharmacy_tech [missing] plan: patch test on a Wednesday at 10, review in three weeks — no output
- m3_12_cracked_hands_carer_and_pharmacy_tech [missing] The record should show this doubt or gap, not a confident fact: how long the hands have been bad: she says since the spring, the carer says since Christmas, the pharmacy technician remembers a visit in August — no output
- m3_12_cracked_hands_carer_and_pharmacy_tech [missing] The record should show this doubt or gap, not a confident fact: she cannot name the cream that helped; she describes it as the white one in the tube with a blue lid — no output
- m3_12_cracked_hands_carer_and_pharmacy_tech [missing] The record should show this doubt or gap, not a confident fact: she stopped one cream herself and is not sure when — no output
- m3_12_cracked_hands_carer_and_pharmacy_tech [missing] The record should show this doubt or gap, not a confident fact: an unidentified woman's voice interrupts from the corridor and is never identified — no output
- m3_12_cracked_hands_carer_and_pharmacy_tech [missing] The record should show this doubt or gap, not a confident fact: which of her two tablets is for cholesterol and which for fluid is muddled — no output
- m3_13_forgetting_and_getting_lost [missing] forgetting recent things, getting lost on roads he knows for about three months — no output
- m3_13_forgetting_and_getting_lost [missing] low mood for about two years — no output
- m3_13_forgetting_and_getting_lost [missing] denies falls, headaches, hallucinations, weakness on one side, bladder problems — no output
- m3_13_forgetting_and_getting_lost [missing] high cholesterol for nearly five years, diabetes — no output
- m3_13_forgetting_and_getting_lost [missing] simvastatin 20 at night, glibenclamide 5 before breakfast — no output
- m3_13_forgetting_and_getting_lost [missing] bunion operation six years ago — no output
- m3_13_forgetting_and_getting_lost [missing] son has asthma — no output
- m3_13_forgetting_and_getting_lost [missing] retired from the post office two years ago, walks the dog every morning — no output
- m3_13_forgetting_and_getting_lost [missing] temp 36.6, pulse 66, resp 14, oxygen 98, BP 116/79 — no output
- m3_13_forgetting_and_getting_lost [missing] memory test a little low — no output
- m3_13_forgetting_and_getting_lost [missing] plan: bloods (thyroid, B12), CT head, review in six weeks, return if suddenly confused — no output
- m3_13_forgetting_and_getting_lost [missing] The record should show this doubt or gap, not a confident fact: antibiotic allergy: he thinks a doctor wrote something on his card once, no name, no reaction — no output
- m3_13_forgetting_and_getting_lost [missing] The record should show this doubt or gap, not a confident fact: an earlier bout of forgetfulness after flu a few years ago that cleared up — no output
- m3_13_forgetting_and_getting_lost [missing] The record should show this doubt or gap, not a confident fact: he came alone and drove, which the doctor picks up — no output
- m3_13_forgetting_and_getting_lost [missing] The record should show this doubt or gap, not a confident fact: the memory test score is only a little low, nothing is diagnosed — no output
- m3_14_fever_after_travel [missing] fever with shaking chills for three days, headache for a week, sweating a lot — no output
- m3_14_fever_after_travel [missing] no diarrhoea, rash, neck stiffness, cough — no output
- m3_14_fever_after_travel [missing] asthma for nearly five years — no output
- m3_14_fever_after_travel [missing] Foracort inhaler twice a day, Dolo 650 — no output
- m3_14_fever_after_travel [missing] no allergies — no output
- m3_14_fever_after_travel [missing] smokes about half a pack a day, stopped heavy drinking four years ago, grandmother had dementia — no output
- m3_14_fever_after_travel [missing] BP 108/78, oxygen 97, pulse 105, temp 39.2 — no output
- m3_14_fever_after_travel [missing] spleen tip just palpable, chest clear — no output
- m3_14_fever_after_travel [missing] plan: malaria test and blood film, blood cultures, fluids, return at once if confused or cannot keep fluids down — no output
- m3_14_fever_after_travel [missing] The record should show this doubt or gap, not a confident fact: paracetamol: she cannot say how many Dolo she has taken in 24 hours ('four, maybe five, maybe six') — no output
- m3_14_fever_after_travel [missing] The record should show this doubt or gap, not a confident fact: she does not remember the name of the malaria tablets the clinic offered before the trip, only that they were not collected — no output
- m3_14_fever_after_travel [missing] The record should show this doubt or gap, not a confident fact: diagnosis is uncertain (malaria first, dengue possible) — no output
- m3_15_irregular_periods_night_sweats [partially_found] caesarean for her second baby nine years ago — Caesarean nine years ago captured, but not that it was for her second baby.
- m3_15_irregular_periods_night_sweats [partially_found] plan: bloods (thyroid, blood count), bone density scan, review once results are in — Thyroid test, bone density scan, and review captured; blood count is missing.
- m3_15_irregular_periods_night_sweats [missing] The record should show this doubt or gap, not a confident fact: she is not sure what she takes for her bones beyond 'the weekly one' — No uncertainty recorded about bone medication beyond the weekly one.
- m3_15_irregular_periods_night_sweats [partially_found] The record should show this doubt or gap, not a confident fact: no firm diagnosis: perimenopause is likely but anaemia needs ruling out — Perimenopause is provisional and thyroid considered, but anaemia needing exclusion is not captured.
- m3_16_kitchen_knife_cut_hand [missing] cut across the left palm with a kitchen knife about two hours ago while cutting a squash, bleeding controlled — no output
- m3_16_kitchen_knife_cut_hand [missing] no numbness, can bend and straighten all fingers, no fever — no output
- m3_16_kitchen_knife_cut_hand [missing] diabetes diet-controlled, asthma, high cholesterol — no output
- m3_16_kitchen_knife_cut_hand [missing] daily inhaler — no output
- m3_16_kitchen_knife_cut_hand [missing] appendix removed as a teenager — no output
- m3_16_kitchen_knife_cut_hand [missing] no allergies — no output
- m3_16_kitchen_knife_cut_hand [missing] pulse 84, BP 132/84, temp 36.8 — no output
- m3_16_kitchen_knife_cut_hand [missing] tetanus last done about six years ago — no output
- m3_16_kitchen_knife_cut_hand [missing] wound cleaned by the technician, closed with 5 stitches — no output
- m3_16_kitchen_knife_cut_hand [missing] return if red, swollen, leaking pus, fever; stitches out in ten days — no output
- m3_16_kitchen_knife_cut_hand [missing] The record should show this doubt or gap, not a confident fact: the doctor never states a diagnosis — no output
- m3_16_kitchen_knife_cut_hand [missing] The record should show this doubt or gap, not a confident fact: follow-up is conditional on how the wound looks — no output
- m3_16_kitchen_knife_cut_hand [missing] The record should show this doubt or gap, not a confident fact: the exact minutes since the injury are given roughly — no output
- m3_17_burning_upper_stomach_after_meals [missing] burning pain in the upper stomach after meals, worse with spicy food and lying down — no output
- m3_17_burning_upper_stomach_after_meals [missing] some waking at night, a sour taste — no output
- m3_17_burning_upper_stomach_after_meals [missing] no vomiting blood, black stools, trouble swallowing, weight loss — no output
- m3_17_burning_upper_stomach_after_meals [missing] high blood pressure and a previous ulcer — no output
- m3_17_burning_upper_stomach_after_meals [missing] amlodipine and an over-the-counter antacid — no output
- m3_17_burning_upper_stomach_after_meals [missing] gallbladder out years ago — no output
- m3_17_burning_upper_stomach_after_meals [missing] father had stomach problems and mother had thyroid trouble — no output
- m3_17_burning_upper_stomach_after_meals [missing] works nights as a delivery driver, smokes about ten a day, two or three pints at weekends — no output
- m3_17_burning_upper_stomach_after_meals [missing] pulse and blood pressure taken, weight taken — no output
- m3_17_burning_upper_stomach_after_meals [missing] plan: breath test for the stomach bug, bloods taken by the phlebotomist, camera test of the stomach if it persists, lifestyle advice — no output
- m3_17_burning_upper_stomach_after_meals [missing] The record should show this doubt or gap, not a confident fact: what he takes for it ('the pink stuff') is described, not named — no output
- m3_17_burning_upper_stomach_after_meals [missing] The record should show this doubt or gap, not a confident fact: how long it has gone on: 'since the Jubilee' is his reference point — no output
- m3_17_burning_upper_stomach_after_meals [missing] The record should show this doubt or gap, not a confident fact: the nurse measures only a few values — no output
- m3_18_hoarse_voice_primary_teacher [missing] hoarse voice for months, worse by the end of the week and the end of the day, voice tires — no output
- m3_18_hoarse_voice_primary_teacher [missing] no pain on swallowing — no output
- m3_18_hoarse_voice_primary_teacher [missing] acid reflux — no output
- m3_18_hoarse_voice_primary_teacher [missing] omeprazole 20 in the morning — no output
- m3_18_hoarse_voice_primary_teacher [missing] primary school teacher for twenty-seven years, does playground duty, has never smoked, sings in a choir — no output
- m3_18_hoarse_voice_primary_teacher [missing] neck and throat examined, no lumps — no output
- m3_18_hoarse_voice_primary_teacher [missing] plan: camera look at the voice box at the ENT clinic, assessment with a speech therapist, voice care advice — no output
- m3_18_hoarse_voice_primary_teacher [missing] The record should show this doubt or gap, not a confident fact: how long: she says since the spring, her husband says before Easter — no output
- m3_18_hoarse_voice_primary_teacher [missing] The record should show this doubt or gap, not a confident fact: the doctor says what it may be (strain, reflux) but is open that a camera look is needed to be sure — no output
- m3_19_prediabetes_what_happens_now [missing] blood sugar result in the pre-diabetes range, found on a routine check — no output
- m3_19_prediabetes_what_happens_now [missing] tired and thirstier than usual — no output
- m3_19_prediabetes_what_happens_now [missing] denies blurred vision and passing lots of water — no output
- m3_19_prediabetes_what_happens_now [missing] denies chest pain — no output
- m3_19_prediabetes_what_happens_now [missing] weight 94 kg, BP 128/82 — no output
- m3_19_prediabetes_what_happens_now [missing] plan: food and activity changes, repeat blood test in six months — no output
- m3_19_prediabetes_what_happens_now [missing] The record should show this doubt or gap, not a confident fact: tiredness: he says a month, his wife says since the winter — no output
- m3_19_prediabetes_what_happens_now [missing] The record should show this doubt or gap, not a confident fact: the doctor calls it 'in the pre-diabetes range' and a 'warning', not a firm diagnosis, until the repeat test — no output
- m3_20_diabetes_screening_symptom_diary [missing] tingling in the toes at night and blurred vision when reading in the evening (diary entries) — no output
- m3_20_diabetes_screening_symptom_diary [missing] no weight loss — no output
- m3_20_diabetes_screening_symptom_diary [missing] underactive thyroid for twelve years — no output
- m3_20_diabetes_screening_symptom_diary [missing] amlodipine 5, levothyroxine 50 micrograms, a calcium supplement — no output
- m3_20_diabetes_screening_symptom_diary [missing] cataract operation on the right eye — no output
- m3_20_diabetes_screening_symptom_diary [missing] retired bank manager — no output
- m3_20_diabetes_screening_symptom_diary [missing] BP 138/84, pulse 72, weight 71 kg — no output
- m3_20_diabetes_screening_symptom_diary [missing] feet pulses felt, sensation to light touch normal, heart and chest normal — no output
- m3_20_diabetes_screening_symptom_diary [missing] plan: fasting blood sugar and HbA1c, review in two weeks with results — no output
- m3_20_diabetes_screening_symptom_diary [missing] The record should show this doubt or gap, not a confident fact: allergy: a reaction (itching) after an operation, the drug is either an antibiotic or a painkiller, she cannot say which, no name and no clear reaction details — no output
- m3_20_diabetes_screening_symptom_diary [missing] The record should show this doubt or gap, not a confident fact: the home help adds details the patient leaves out and corrects one time — no output