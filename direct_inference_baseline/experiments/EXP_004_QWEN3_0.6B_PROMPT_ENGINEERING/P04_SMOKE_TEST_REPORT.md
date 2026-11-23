# P04 smoke-test report (5 records) - FOR REVIEW. A smoke test is a feasibility check; it does not show that P04 works or that evidence is semantically correct.

Run `P04_smoke_5`; prompt `prompts/P04_integrated_segment_evidence.txt` sha256 `e05c8beaf82380bdd9581acd07fc77940a363346eb003d44295364683c5aaf55` (verified before and after inference: True).
Ids: 00035, 00037, 00040, 00215, 00248 (all prompt_dev, none in validation or the locked test set). Start 2026-11-13T02:16:02+05:30, end 2026-11-13T02:49:38+05:30, wall 2016.3 s.
Pre-flight: all 10 checks passed = True (prompt hash, ids/splits, OpenVINO FP16 model files vs the EXP_002 conversion record, settings identical to the P02 and P03 run manifests, 6144-token cap, Qwen3-0.6B rev c1899de2, OpenVINO GenAI GPU, greedy, thinking off). File-access audit: 0 label/blueprint files opened, 400 locked-test transcripts were read ONLY to compute their SHA-256 in the existing runner's frozen-dataset verification (see section 6); 0 were used for prompting, parsing or evaluation.

## 1. Gates (smoke criteria S1-S6)
| Gate | Result | Detail |
|---|---|---|
| S1_all_parse_build_validator | **FAIL** | {"parsed": "4/5", "builder_ok": "4/5", "evidence_field_violations_in_final": 0} |
| S2_valid_refs | **FAIL** | {"facts_with_valid_ref": "33/40 (82.5%)", "emitted_ids_valid": "150/150 (100.0%)", "exact_only_share": "100.0%"} |
| S3_records_ge_5_in_at_least_4_of_5 | **FAIL** | {"records_per_encounter": {"00035": 33, "00037": null, "00040": 28, "00215": 5, "00248": 4}, "encounters_with_ge_5": 3} |
| S5_not_collapsed | **FAIL** | {"p04_items": 40, "p02_items_same_ids": 82, "ratio": 0.488, "mean_output_tokens_all_5_records": 2080.8} |
| S6_builder_integrity | **PASS** | {"identical_except_evidence_fields": "4/4", "invalid_or_missing_refs_reported_separately": true, "records_the_builder_processed": 4, "not_applicable": ["00037"], "label_files_opened_during_inference": 0, "locked_test_transcripts_opened_only_for_checksum_by_existing_runner": 400, "locked_test_transcripts_used_for_prompting_parsing_or_evaluation": 0} |

S4 is report-only (section 5). Passing S1-S3, S5 and S6 means the pipeline is feasible and structurally sound; it says nothing about whether the cited segments genuinely support the facts (section 5 and 6).

## 2. Per-encounter summary
| Item | 00035 | 00037 | 00040 | 00215 | 00248 |
|---|---|---|---|---|---|
| JSON parse result (status / finish) | parsed / stop | failed / stop | parsed / stop | parsed / stop | parsed / stop |
| Schema compliant (final) | False | None | False | False | False |
| Schema violations (final), by kind | {"missing_field": 16, "enum_violation": 9, "wrong_type": 2} | null | {"missing_field": 16, "wrong_type": 2} | {"missing_field": 18, "enum_violation": 8, "wrong_type": 2} | {"enum_violation": 7, "missing_field": 6, "wrong_type": 2} |
| Evidence-field violations in final | 0 | None | 0 | 0 | 0 |
| Extracted facts | 13 | None | 9 | 11 | 7 |
| Facts with >=1 valid reference | 11 | None | 6 | 9 | 7 |
| Facts with no reference | 2 | None | 3 | 2 | 0 |
| Refs exact / spelling-normalised / invalid / duplicate-removed | 83 / 0 / 0 / 0 | None / None / None / None | 51 / 0 / 0 / 0 | 9 / 0 / 0 / 0 | 7 / 0 / 0 / 0 |
| Invalid-ref examples | [] | None | [] | [] | [] |
| Items with missing / mistyped source_segments | 2 / 0 | None / None | 3 / 0 | 2 / 0 | 0 / 0 |
| Evidence records created | 33 | None | 28 | 5 | 4 |
| Segments in transcript | 39 | 56 | 58 | 46 | 39 |
| Ids per item (n ids: n items) | {"1": 7, "33": 2, "0": 2, "5": 2} | null | {"1": 1, "5": 3, "0": 3, "13": 1, "22": 1} | {"1": 9, "0": 2} | {"1": 7} |
| Citations / in first two segments | 83 / 3 | None / None | 51 / 4 | 9 / 3 | 7 / 1 |
| Citation position (index 0..5+) | {"1": 3, "2": 2, "4": 2, "5": 76} | null | {"0": 4, "2": 3, "4": 3, "5": 41} | {"1": 3, "5": 6} | {"1": 1, "5": 6} |
| Items auto-flagged questionable (lexical/greeting/question-only) | 8 | None | 6 | 5 | 3 |
| Items questionable incl. manual review | 8 | None | 6 | 5 | 3 |
| Records: text exact / speaker / role / start / end vs transcript | 33/33/33/33/33 of 33 | None/None/None/None/None of None | 28/28/28/28/28 of 28 | 5/5/5/5/5 of 5 | 4/4/4/4/4 of 4 |
| Supports: entries / to existing item / reciprocal; item ids listed in supports | 83/83/83; 83 of 83 | None/None/None; None of None | 51/51/51; 51 of 51 | 9/9/9; 9 of 9 | 7/7/7; 7 of 7 |
| Records with empty supports | 0 | None | 0 | 0 | 0 |
| Builder integrity (only evidence fields changed) | True | None | True | True | True |
| Model wrote own evidence_ids items / clinical_evidence records (ignored) | 0 / 0 | None / None | 0 / 0 | 0 / 0 | 0 / 0 |
| Completion tokens / prompt tokens | 1750 / 4132 | 5365 / 4872 | 1281 / 4930 | 1110 / 4396 | 898 / 4135 |
| Latency s / tokens per s | 307.484 / 5.69 | 1080.943 / 4.96 | 242.439 / 5.28 | 196.646 / 5.64 | 160.278 / 5.6 |
| Extraction TP/FP/FN (strict) | 4/9/20 | 0/0/40 | 0/9/46 | 3/8/23 | 2/5/25 |
| Precision / recall / F1 | 0.308/0.167/0.216 | 0.000/0.000/0.000 | 0.000/0.000/0.000 | 0.273/0.115/0.162 | 0.286/0.074/0.118 |

## 3. Comparison with P02 on exactly the same five ids (P02 = existing 50-record outputs, same model and settings)
| | P04 smoke | P02 |
|---|---|---|
| Strict TP / FP / FN (pooled) | 9 / 31 / 154 | 20 / 62 / 143 |
| Micro precision / recall / F1 | 0.225 / 0.055 / 0.089 | 0.244 / 0.123 / 0.163 |
| Items extracted | 40 | 82 |
| Schema violations total (final / as written by the model) | 88 | 140 |
| Fully schema-compliant records | 0 | 0 |
| Mean completion tokens | 2080.8 | 1540 |
| Mean latency s | 397.6 | 263.0 |
| Evidence records per encounter | 33, None, 28, 5, 4 | 1, 1, 1, 1, 1 (one template record in every P02 output) |

Per encounter (P04 TP/FP/FN vs P02): 00035: 4/9/20 vs 4/11/20; 00037: 0/0/40 vs 2/15/38; 00040: 0/9/46 vs 8/15/38; 00215: 3/8/23 vs 3/9/23; 00248: 2/5/25 vs 3/12/24

Five records are too few to say whether extraction was preserved; they only show whether it collapsed. The 50-record gates are the real test.

## 4. Gold-segment agreement (provisional V5 reference 73.9%) - denominators first

* Extracted facts: 40; strictly matched to a gold item and carrying a gold citation (the denominator): **9** (22.5% of extracted facts). Hit-any: 6/9 = 0.6667; set precision 0.6, set recall 0.4615.
* This applies only to the matched items, which is a small and favourable subset; it is **not overall clinical evidence accuracy** and says nothing about the facts that do not match a gold item. With so few matched items it cannot be compared with 73.9% in a meaningful way. Arm R's 88.9% is likewise a matched-items figure.

## 5. Citation inspection (S4: report and inspect; no positional rejection)

Segment-position distribution of all citations (index 0 = SEG0001; 5 = index 5 or later): {0: 4, 1: 7, 2: 5, 4: 5, 5: 129}. Automatic flags (counts): {"opening/greeting segment": 11, "no lexical overlap": 22, "question-only citation": 7, "no reference": 7}.
Flags are heuristics: 'no lexical overlap' can be legitimate when the item uses a standard term that was not spoken; 'opening/greeting segment' = cited segment among the first two and either no overlap or <= 8 words. They are not verdicts. The full item-by-item table (item, cited segment text, flags, gold-match, manual review if present) follows.

| id | item | cited segment(s) | flags | gold | manual |
|---|---|---|---|---|---|
| 00035 | chief_complaint : severe | SEG0002 person_2/DOCTOR: You're fine, sit down. So, what brings you in? | no lexical overlap, opening/greeting segment, question-only citation | - | wrong: value 'severe' is not a complaint; cites the doctor's question (SEG0002) instead of the patient's answer SEG0003 |
| 00035 | symptoms[0] : severe | SEG0002 person_2/DOCTOR: You're fine, sit down. So, what brings you in?<br>SEG0003 person_1/PATIENT: Yeah, it's a slight slur in my speech. I don't know what's causing it. I didn't want to make a fuss, you know.<br>SEG0005 person_1/PATIENT: For ten days, I'd say.<br>SEG0007 person_1/PATIENT: I'd say severe.<br>SEG0008 person_2/DOCTOR: Any palpitations, chest pain or confusion at all?<br>SEG0009 person_1/PATIENT: I haven't had palpitations, chest pain or confusion, no.<br>SEG0010 person_2/DOCTOR: Okay, is your mobility otherwise okay?<br>SEG0011 person_1/PATIENT: I move fine otherwise.<br>SEG0013 person_1/PATIENT: No, uh, none that I know of.<br>SEG0014 person_2/DOCTOR: Are there any allergies on your record that I should check?<br>SEG0015 person_1/PATIENT: No, no allergies to anything.<br>SEG0017 person_1/PATIENT: Just a lump removed from my back, years ago.<br>SEG0019 person_1/PATIENT: It's just me and my wife at home now.<br>SEG0020 person_2/DOCTOR: Tell me about your work.<br>SEG0021 person_1/PATIENT: I'm a software engineer, so I'm at a screen all day.<br>SEG0022 person_2/DOCTOR: Any relatives with health problems I should be aware of?<br>SEG0023 person_1/PATIENT: Uh, you know, my father had a heart attack.<br>SEG0024 person_2/DOCTOR: Let's go through your medication. What are you taking?<br>SEG0025 person_1/PATIENT: It's aspirin, 75 milligrams, once a day.<br>SEG0026 person_2/DOCTOR: Let me measure a few things.<br>SEG0027 person_2/DOCTOR: Hold still for me...<br>SEG0028 person_2/DOCTOR: Okay: heart rate 79, temp 36.7 degrees, pressure 167 over 90. And oxygen saturation is 96 percent.<br>SEG0029 person_1/PATIENT: Is that normal?<br>SEG0030 person_2/DOCTOR: That's fine, we'll come to it.<br>SEG0031 person_2/DOCTOR: Let me tell you where I've got to. It points towards a possible mini-stroke, which we need to investigate urgently.<br>SEG0032 person_1/PATIENT: I've been thinking the worst, uh, to be honest. Is it bad?<br>SEG0033 person_2/DOCTOR: I can't promise yet, but most people with a possible mini-stroke, which we need to investigate urgently do well once it's treated <br>SEG0034 person_1/PATIENT: So, that's what happened, yes.<br>SEG0035 person_2/DOCTOR: I'd like to arrange an ECG for possible stroke. I'd rather check than guess, and this is the quickest way to know more. Don't driv<br>SEG0036 person_1/PATIENT: Okay.<br>SEG0037 person_2/DOCTOR: Alright, take care, and call us if anything changes.<br>SEG0038 person_1/PATIENT: Thanks so much, doctor.<br>SEG0039 person_2/DOCTOR: All the best. | no lexical overlap, opening/greeting segment | - | wrong: item 'severe' is not a symptom; 33 of 39 segments cited, not minimal |
| 00035 | negative_findings[0] : severe | SEG0002 person_2/DOCTOR: You're fine, sit down. So, what brings you in?<br>SEG0003 person_1/PATIENT: Yeah, it's a slight slur in my speech. I don't know what's causing it. I didn't want to make a fuss, you know.<br>SEG0005 person_1/PATIENT: For ten days, I'd say.<br>SEG0007 person_1/PATIENT: I'd say severe.<br>SEG0008 person_2/DOCTOR: Any palpitations, chest pain or confusion at all?<br>SEG0009 person_1/PATIENT: I haven't had palpitations, chest pain or confusion, no.<br>SEG0010 person_2/DOCTOR: Okay, is your mobility otherwise okay?<br>SEG0011 person_1/PATIENT: I move fine otherwise.<br>SEG0013 person_1/PATIENT: No, uh, none that I know of.<br>SEG0014 person_2/DOCTOR: Are there any allergies on your record that I should check?<br>SEG0015 person_1/PATIENT: No, no allergies to anything.<br>SEG0017 person_1/PATIENT: Just a lump removed from my back, years ago.<br>SEG0019 person_1/PATIENT: It's just me and my wife at home now.<br>SEG0020 person_2/DOCTOR: Tell me about your work.<br>SEG0021 person_1/PATIENT: I'm a software engineer, so I'm at a screen all day.<br>SEG0022 person_2/DOCTOR: Any relatives with health problems I should be aware of?<br>SEG0023 person_1/PATIENT: Uh, you know, my father had a heart attack.<br>SEG0024 person_2/DOCTOR: Let's go through your medication. What are you taking?<br>SEG0025 person_1/PATIENT: It's aspirin, 75 milligrams, once a day.<br>SEG0026 person_2/DOCTOR: Let me measure a few things.<br>SEG0027 person_2/DOCTOR: Hold still for me...<br>SEG0028 person_2/DOCTOR: Okay: heart rate 79, temp 36.7 degrees, pressure 167 over 90. And oxygen saturation is 96 percent.<br>SEG0029 person_1/PATIENT: Is that normal?<br>SEG0030 person_2/DOCTOR: That's fine, we'll come to it.<br>SEG0031 person_2/DOCTOR: Let me tell you where I've got to. It points towards a possible mini-stroke, which we need to investigate urgently.<br>SEG0032 person_1/PATIENT: I've been thinking the worst, uh, to be honest. Is it bad?<br>SEG0033 person_2/DOCTOR: I can't promise yet, but most people with a possible mini-stroke, which we need to investigate urgently do well once it's treated <br>SEG0034 person_1/PATIENT: So, that's what happened, yes.<br>SEG0035 person_2/DOCTOR: I'd like to arrange an ECG for possible stroke. I'd rather check than guess, and this is the quickest way to know more. Don't driv<br>SEG0036 person_1/PATIENT: Okay.<br>SEG0037 person_2/DOCTOR: Alright, take care, and call us if anything changes.<br>SEG0038 person_1/PATIENT: Thanks so much, doctor.<br>SEG0039 person_2/DOCTOR: All the best. | no lexical overlap, opening/greeting segment | - | wrong: item is not a denied finding; same 33 ids |
| 00035 | medications[0] : aspirin | - | no reference | TP miss | - |
| 00035 | allergies[0] : none | - | no reference | - | - |
| 00035 | vital_signs[0] : heart rate | SEG0028 person_2/DOCTOR: Okay: heart rate 79, temp 36.7 degrees, pressure 167 over 90. And oxygen saturation is 96 percent. | - | TP hit | ok: SEG0028 states the heart rate |
| 00035 | vital_signs[1] : temperature | SEG0028 person_2/DOCTOR: Okay: heart rate 79, temp 36.7 degrees, pressure 167 over 90. And oxygen saturation is 96 percent. | - | - | ok: SEG0028 states the temperature |
| 00035 | vital_signs[2] : blood pressure | SEG0028 person_2/DOCTOR: Okay: heart rate 79, temp 36.7 degrees, pressure 167 over 90. And oxygen saturation is 96 percent. | - | TP hit | ok: SEG0028 states the blood pressure |
| 00035 | physical_examination[0] : severe | SEG0028 person_2/DOCTOR: Okay: heart rate 79, temp 36.7 degrees, pressure 167 over 90. And oxygen saturation is 96 percent. | no lexical overlap | - | wrong: item 'severe' is not an examination finding; vitals line does not state it |
| 00035 | review_of_systems[0] : cardiovascular | SEG0028 person_2/DOCTOR: Okay: heart rate 79, temp 36.7 degrees, pressure 167 over 90. And oxygen saturation is 96 percent. | no lexical overlap | - | questionable: vitals line does not state a cardiovascular review |
| 00035 | clinical_conditions[0] : severe | SEG0028 person_2/DOCTOR: Okay: heart rate 79, temp 36.7 degrees, pressure 167 over 90. And oxygen saturation is 96 percent. | no lexical overlap | - | wrong: item 'severe' is not a condition; vitals line |
| 00035 | procedures_and_investigations[0] : ECG | SEG0035 person_2/DOCTOR: I'd like to arrange an ECG for possible stroke. I'd rather check than guess, and this is the quickest way to know more. Don't driv<br>SEG0036 person_1/PATIENT: Okay.<br>SEG0037 person_2/DOCTOR: Alright, take care, and call us if anything changes.<br>SEG0038 person_1/PATIENT: Thanks so much, doctor.<br>SEG0039 person_2/DOCTOR: All the best. | no lexical overlap | TP hit | questionable: SEG0035 states the ECG; SEG0036 ('Okay.'), SEG0037 (farewell) and later ids add nothing |
| 00035 | clinical_actions[0] : consultation|arrange electrocardiogram for possible stroke | SEG0035 person_2/DOCTOR: I'd like to arrange an ECG for possible stroke. I'd rather check than guess, and this is the quickest way to know more. Don't driv<br>SEG0036 person_1/PATIENT: Okay.<br>SEG0037 person_2/DOCTOR: Alright, take care, and call us if anything changes.<br>SEG0038 person_1/PATIENT: Thanks so much, doctor.<br>SEG0039 person_2/DOCTOR: All the best. | no lexical overlap | - | questionable: same five ids; only SEG0035 states the plan |
| 00040 | chief_complaint : twitching in fingers | SEG0001 person_1/PATIENT: Good afternoon, doctor, the receptionist said you'd see me now. | no lexical overlap, opening/greeting segment | - | wrong: cites the greeting SEG0001; the complaint is in SEG0003 ('tingling in my fingers'); value says 'twitching' |
| 00040 | symptoms[0] : twitching in fingers | SEG0001 person_1/PATIENT: Good afternoon, doctor, the receptionist said you'd see me now.<br>SEG0003 person_1/PATIENT: So the thing is, I've got tingling in my fingers.<br>SEG0005 person_1/PATIENT: It's been five days now.<br>SEG0007 person_1/PATIENT: Yes, about the same, six months. With ache in the wrist, I'd say moderate. It's a couple of times a week. Oh, and numbness in the <br>SEG0009 person_1/PATIENT: Honestly, once or twice a day. I've been waking up at night with pins and needles too, you know, since Monday. | no lexical overlap, opening/greeting segment | - | questionable: SEG0003 and SEG0005 are relevant; SEG0001 is a greeting; item says 'twitching' while the patient says 'tingling' |
| 00040 | negative_findings[0] : twitching in fingers | SEG0001 person_1/PATIENT: Good afternoon, doctor, the receptionist said you'd see me now.<br>SEG0003 person_1/PATIENT: So the thing is, I've got tingling in my fingers.<br>SEG0005 person_1/PATIENT: It's been five days now.<br>SEG0007 person_1/PATIENT: Yes, about the same, six months. With ache in the wrist, I'd say moderate. It's a couple of times a week. Oh, and numbness in the <br>SEG0009 person_1/PATIENT: Honestly, once or twice a day. I've been waking up at night with pins and needles too, you know, since Monday. | no lexical overlap, opening/greeting segment | - | wrong: a symptom placed in negative_findings; cites the symptom lines |
| 00040 | medications[0] : thyroxine | - | no reference | - | - |
| 00040 | allergies[0] : antibiotic | - | no reference | - | - |
| 00040 | vital_signs[0] : temperature | SEG0046 person_2/DOCTOR: Okay: temperature 36.7, BP is 123 over 70. And heart rate 64, SpO2 97 percent on room air.<br>SEG0047 person_2/DOCTOR: Let's do the physical part now.<br>SEG0048 person_1/PATIENT: Fine.<br>SEG0049 person_2/DOCTOR: Take your time, no rush.<br>SEG0050 person_2/DOCTOR: Bending the wrist for a minute brings on the numbness.<br>SEG0051 person_2/DOCTOR: Let me look at this properly.<br>SEG0052 person_2/DOCTOR: Tapping over the wrist reproduces the tingling.<br>SEG0053 person_2/DOCTOR: That's all I need, thank you. Right, here's what I'm thinking. The most likely explanation is carpal tunnel syndrome. I can't rule<br>SEG0054 person_2/DOCTOR: See me again after the results are back.<br>SEG0055 person_1/PATIENT: Alright, I'll put it in my diary.<br>SEG0056 person_2/DOCTOR: Okay, I think we're finished. Is everything clear?<br>SEG0057 person_1/PATIENT: One thing: no, actually that's all. Thanks.<br>SEG0058 person_2/DOCTOR: See you then. | no lexical overlap | - | questionable: SEG0046 states the temperature; 12 further consecutive ids (exam chatter) are not needed |
| 00040 | physical_examination[0] : twitching in fingers | SEG0001 person_1/PATIENT: Good afternoon, doctor, the receptionist said you'd see me now.<br>SEG0003 person_1/PATIENT: So the thing is, I've got tingling in my fingers.<br>SEG0005 person_1/PATIENT: It's been five days now.<br>SEG0007 person_1/PATIENT: Yes, about the same, six months. With ache in the wrist, I'd say moderate. It's a couple of times a week. Oh, and numbness in the <br>SEG0009 person_1/PATIENT: Honestly, once or twice a day. I've been waking up at night with pins and needles too, you know, since Monday. | no lexical overlap, opening/greeting segment | - | wrong: a patient-reported symptom, not an examination finding; cites patient lines |
| 00040 | review_of_systems[0] : musculoskeletal | - | no reference | - | - |
| 00040 | clinical_conditions[0] : underactive thyroid | SEG0029 person_1/PATIENT: I have an underactive thyroid, for about ten years.<br>SEG0031 person_1/PATIENT: I've got diabetes.<br>SEG0033 person_1/PATIENT: I've got high cholesterol.<br>SEG0035 person_1/PATIENT: No headache or weakness in the legs, none of it.<br>SEG0037 person_1/PATIENT: No neck pain, trouble walking or bladder problems, none of it.<br>SEG0039 person_1/PATIENT: No. No swelling in the joints.<br>SEG0040 person_2/DOCTOR: How about your heart, any problems like that?<br>SEG0041 person_1/PATIENT: Nothing like that.<br>SEG0043 person_1/PATIENT: Okay, so no problems with breathing.<br>SEG0045 person_2/DOCTOR: Rest your hand here...<br>SEG0047 person_2/DOCTOR: Let's do the physical part now.<br>SEG0048 person_1/PATIENT: Fine.<br>SEG0049 person_2/DOCTOR: Take your time, no rush.<br>SEG0050 person_2/DOCTOR: Bending the wrist for a minute brings on the numbness.<br>SEG0051 person_2/DOCTOR: Let me look at this properly.<br>SEG0052 person_2/DOCTOR: Tapping over the wrist reproduces the tingling.<br>SEG0053 person_2/DOCTOR: That's all I need, thank you. Right, here's what I'm thinking. The most likely explanation is carpal tunnel syndrome. I can't rule<br>SEG0054 person_2/DOCTOR: See me again after the results are back.<br>SEG0055 person_1/PATIENT: Alright, I'll put it in my diary.<br>SEG0056 person_2/DOCTOR: Okay, I think we're finished. Is everything clear?<br>SEG0057 person_1/PATIENT: One thing: no, actually that's all. Thanks.<br>SEG0058 person_2/DOCTOR: See you then. | no lexical overlap | - | questionable: SEG0029 states the thyroid condition; 21 further ids are the patient's other conditions |
| 00215 | chief_complaint : severe headaches | SEG0002 person_2/DOCTOR: Of course, put it down anywhere. So, how can I help? | no lexical overlap, opening/greeting segment, question-only citation | - | wrong: cites the doctor's question line only; the complaint is stated in the patient's answer (SEG0003) |
| 00215 | symptoms[0] : headaches | SEG0002 person_2/DOCTOR: Of course, put it down anywhere. So, how can I help? | no lexical overlap, opening/greeting segment, question-only citation | - | wrong: cites the doctor's question line only; the complaint is stated in the patient's answer (SEG0003) |
| 00215 | negative_findings[0] : no fever | SEG0002 person_2/DOCTOR: Of course, put it down anywhere. So, how can I help? | no lexical overlap, opening/greeting segment, question-only citation | - | wrong: 'no fever' is not stated in the cited question SEG0002 |
| 00215 | medications[0] : Amlodipine | - | no reference | TP miss | - |
| 00215 | allergies[0] : ibuprofen | - | no reference | TP miss | - |
| 00215 | vital_signs[0] : pulse | SEG0030 person_2/DOCTOR: Okay: pulse 89, temperature 36.8, BP is 152 over 97. | - | - | ok: SEG0030 states the pulse |
| 00215 | vital_signs[1] : temperature | SEG0030 person_2/DOCTOR: Okay: pulse 89, temperature 36.8, BP is 152 over 97. | - | - | ok: SEG0030 states the temperature |
| 00215 | vital_signs[2] : blood pressure | SEG0030 person_2/DOCTOR: Okay: pulse 89, temperature 36.8, BP is 152 over 97. | - | TP hit | ok: SEG0030 states the BP |
| 00215 | physical_examination[0] : mild pitting swelling at both ankles | SEG0026 person_2/DOCTOR: Any muscle or joint problems besides this? | no lexical overlap, question-only citation | - | wrong: cites a question about joint problems (SEG0026), not an examination finding |
| 00215 | review_of_systems[0] : cardiovascular | SEG0033 person_2/DOCTOR: If you're comfortable, I'll examine you now. | no lexical overlap | - | wrong: cites 'I will examine you now' (SEG0033); not a review of systems |
| 00215 | clinical_conditions[0] : high blood pressure | SEG0013 person_1/PATIENT: Um, I have high blood pressure, for nearly five years. | - | - | ok: SEG0013: patient states high blood pressure |
| 00248 | chief_complaint : mild | SEG0002 person_2/DOCTOR: Right on time. Sit, please. How can I help? | no lexical overlap, opening/greeting segment, question-only citation | - | wrong: value 'mild' is not a complaint; cites the doctor's question SEG0002 (complaint in SEG0003) |
| 00248 | symptoms[0] : acid reflux | SEG0019 person_1/PATIENT: I have acid reflux, for nearly five years. | - | - | ok: SEG0019: patient states acid reflux |
| 00248 | negative_findings[0] : no fever | SEG0028 person_2/DOCTOR: Okay: pulse is 71 beats a minute, blood pressure 127 over 82, temperature is 36.6 degrees. | no lexical overlap | - | questionable: temperature reading only indirectly supports 'no fever' |
| 00248 | allergies[0] : pollen | SEG0024 person_2/DOCTOR: Are there any allergies on your record that I should check? | no lexical overlap, question-only citation | TP hit | wrong: cites the doctor's question SEG0024 only; the patient's answer (SEG0025) is the evidence (the gold also cites the question, so it counts as a gold hit) |
| 00248 | vital_signs[0] : pulse | SEG0028 person_2/DOCTOR: Okay: pulse is 71 beats a minute, blood pressure 127 over 82, temperature is 36.6 degrees. | - | - | ok: SEG0028 |
| 00248 | vital_signs[1] : blood pressure | SEG0028 person_2/DOCTOR: Okay: pulse is 71 beats a minute, blood pressure 127 over 82, temperature is 36.6 degrees. | - | TP hit | ok: SEG0028 |
| 00248 | vital_signs[2] : temperature | SEG0028 person_2/DOCTOR: Okay: pulse is 71 beats a minute, blood pressure 127 over 82, temperature is 36.6 degrees. | - | - | ok: SEG0028 |

## 5b. Findings and interpretation (written after reading every item and all five outputs)

**Smoke-test outcome against the approved gates: S1 FAIL, S2 FAIL, S3 FAIL, S5 FAIL, S6 PASS (for the 4 records the builder processed). S4 is report-only.** On this evidence P04 as approved is not ready for a 50-record run, and I recommend against starting one without a redesign. This is five records and one run, so the failure modes below matter more than any percentage.

**What worked**
* The pipeline is mechanically sound. The builder processed all four parsed outputs, changed nothing except evidence fields (4/4), created records that match the transcript exactly (text, speaker, role, floor-second timestamps) and consistent `supports` paths (all entries reciprocal), with 0 evidence-field schema violations in the final JSON. This is guaranteed by construction and is not evidence of semantic correctness.
* Every emitted segment id was valid (150/150; no placeholder `<segment id>` copied, no non-existent id, no spelling variants).
* Vital-sign facts were cited to the correct line in all four encounters (9 of the 11 items I judged clearly appropriate; the other two are a condition in 00215 and a symptom in 00248).

**What failed**
1. **Invalid JSON and runaway output (00037, S1).** The model wrote 23 `source_segments` lists, several of 25-37 ids (e.g. `SEG0001...SEG0015` runs), producing 5,365 output tokens, 1,081 s (3.5x the P02 latency for that record) and invalid JSON (missing comma at character 5,818). The record yields no extraction and no evidence. Latency overall: mean 398 s vs 263 s for P02 on the same ids.
2. **Over-citation of long id runs.** In 00035 two items cite 33 of 39 segments each; in 00040 an item cites 22 and another 13 ids; procedures/actions in 00035 cite five consecutive segments including "Okay." and a farewell line. The prompt asked for the minimum number of segments and "several only when genuinely required"; the model did not follow that. These inflate the evidence-record counts (33 and 28 records) without improving grounding, which is exactly the confusion you warned about: records-per-encounter (33, 28, 5, 4) says nothing about correctly grounded facts, and S3 passes in 00035/00040 only because of those runs.
3. **The chief complaint cites the doctor's question (3 of 4 records).** In 00035, 00215 and 00248 it cites SEG0002 (a question such as "how can I help?"), and in 00040 the greeting SEG0001; the complaint is stated in SEG0003 in each. The prompt said a question alone is never proof; the model did not apply it. In 00248 the allergy also cites only the doctor's question (SEG0024), not the patient's answer. Per your guidance I count these as semantically wrong even where the gold also cites the question segment (00248 allergy counts as a "gold hit" but I marked it wrong).
4. **Extraction coverage collapsed relative to P02.** Items: 40 vs 82 on the same five ids (0.49; on the four records the builder processed, 40 vs 65 = 0.62, still below the 70% gate). Strict TP/FP/FN pooled: 9/31/154 vs 20/62/143; micro recall 0.055 vs 0.123 and F1 0.089 vs 0.163. 00040 found 0 true positives (P02: 8) and 00037 failed (P02: 2). The model produced about one item per section (typically one symptom, one negative finding, three vitals) instead of the P02-style comprehensive lists. Whether the P02 gains are "preserved" cannot be answered by 5 records, but this is the opposite of preserved.
5. **Spurious fill-in items.** The template now shows a non-empty `source_segments` placeholder in every section, and the model emitted an item in nearly every section even when nothing supported it: in 00035 the key "severe" appears as a symptom, a "negative finding", a physical-examination finding and a condition; in 00040 and 00215 a symptom is repeated as a "negative finding" or "physical examination"; medications/allergies appear with no reference at all (7 facts have no reference: aspirin, "none", thyroxine, antibiotic, musculoskeletal ROS, amlodipine, ibuprofen). I did not test whether the non-empty placeholders cause this; it is consistent with the earlier observation that the model copies what the template pre-fills.
6. **Not fixed from earlier prompts:** `clinical_assessment` and `follow_up` are again emitted as objects in all four parsed outputs (wrong_type); schema compliance 0/4 (88 violations in 4 records vs 140 in 5 P02 records; not comparable because 00037 is missing). The builder does not touch these by design.

**My segment-by-segment reading of the 33 facts that carry references (manual, not independent; full item table in section 5):** 11 appropriate (vital signs x9, a condition, a symptom), 7 questionable (right line plus many unnecessary ids, or indirect support), 15 wrong (spurious items, a question-only or greeting citation, or a line that does not state the fact). Counting the 7 facts with no reference, only **11 of 40 extracted facts (27.5%)** have a clearly appropriate citation. This reading is mine; it should be checked by you or a reviewer.
**Gold-segment agreement (V5):** denominator = 9 strictly matched facts that carry a gold citation (22.5% of the 40 extracted facts): hit-any 6/9 = 66.7%, set precision 60%, set recall 46%. Nine items cannot be compared with the 73.9% provisional threshold, and neither this figure nor Arm R's 88.9% is overall clinical evidence accuracy.

**Auto flags (heuristic):** facts flagged by the lexical/greeting/question-only heuristics: 8, 6, 5 and 3 for 00035, 00040, 00215 and 00248 (22 of the 33 referenced facts). My manual count of questionable plus wrong is also 22 (7 + 15); the two counts coincide per encounter, though I did not verify that the individual items are identical. Citations in the first two segments: 11 of 150, but the 150 are dominated by the long runs. The four chief-complaint citations (00035, 00040, 00215, 00248) all point to a doctor's question or a greeting. Details per encounter are in section 2.

**Comparison with Arm R (offline retrieval, 50 records):** on matched items retrieval hit 81-89%; Qwen 6/9 here. The sample is too small to rank them, but nothing here suggests the model's ids are better than code retrieval, and the failure modes (long runs, question lines, junk items) are ones retrieval does not have.

**Candidate directions (not started; for your decision):** (a) keep the builder but verify or replace the model's ids in code (for example keep a cited segment only if it lexically supports the item; prefer the answer line over a question line; cap or reject long runs deterministically); (b) the model proposes only a segment id for the few facts where it is reliable, with retrieval for the rest; (c) revert the template to empty `source_segments` placeholders as in P00/P02 and test whether the spurious fill-in items disappear (a template-only change, cheap to test on these five ids); (d) fall back to code retrieval (Arm R) for evidence and keep the P02 prompt for extraction. I recommend (a) or (d), with (c) as a quick diagnostic, but I have not started any of them.

**Integrity disclosure (applies to every run since EXP_003, not only this one).** The existing inference runner calls `verify_frozen_dataset(inputs_only=True)`, which re-computes the SHA-256 of all 500 frozen input transcripts, including the 400 locked-test transcripts, at the start of every run. I measured this directly (`evaluation/frozen_dataset_hash_access_audit.json`): 500 transcripts opened for hashing, 400 of them locked-test inputs, 0 label files. The bytes are read to verify checksums; the content is not parsed, rendered, used in any prompt, analysed or evaluated, and no locked-test label has ever been opened. My earlier statements that the locked test set was "untouched" are true for labels and for any use of the data, but strictly the test transcripts were read for checksum verification on every run. The pre-flight check in this run's report (ids not in the test set) concerns ids processed, not files hashed. I cannot change this behaviour without modifying the existing module, which you have prohibited.


## 6. Limitations of this report
Five encounters; one run; evidence-record counts are not a measure of correctly grounded facts; structural checks (records, speakers, timestamps, supports) are correct by construction when the references are valid; manual verdicts (if present) are my reading, not independent.

## 7. Complete intermediate model JSON and final built JSON (all five records)

### 00035 - intermediate model JSON (what Qwen produced, parsed; before evidence building)
```json
{
 "encounter_id": "00035",
 "extraction_status": "completed",
 "encounter_metadata": {
  "encounter_date": null,
  "encounter_type": "outpatient_consultation",
  "language": "en",
  "primary_speakers": [
   {
    "speaker_id": "SEG0002",
    "role": "DOCTOR",
    "role_confidence": null
   }
  ]
 },
 "chief_complaint": {
  "value": "severe",
  "normalized_value": "severe",
  "reported_by": "doctor",
  "source_segments": [
   "SEG0002"
  ]
 },
 "symptoms": [
  {
   "name": "severe",
   "normalized_name": "severe",
   "category": "cardiovascular",
   "status": "resolved",
   "duration": null,
   "frequency": null,
   "onset": null,
   "temporality": "current",
   "body_site": "cardiovascular",
   "associated_symptoms": [],
   "aggravating_factors": [],
   "relieving_factors": [],
   "reported_by": "doctor",
   "certainty": "uncertain",
   "source_segments": [
    "SEG0002",
    "SEG0003",
    "SEG0005",
    "SEG0007",
    "SEG0008",
    "SEG0009",
    "SEG0010",
    "SEG0011",
    "SEG0013",
    "SEG0014",
    "SEG0015",
    "SEG0017",
    "SEG0019",
    "SEG0020",
    "SEG0021",
    "SEG0022",
    "SEG0023",
    "SEG0024",
    "SEG0025",
    "SEG0026",
    "SEG0027",
    "SEG0028",
    "SEG0029",
    "SEG0030",
    "SEG0031",
    "SEG0032",
    "SEG0033",
    "SEG0034",
    "SEG0035",
    "SEG0036",
    "SEG0037",
    "SEG0038",
    "SEG0039"
   ]
  }
 ],
 "negative_findings": [
  {
   "finding": "severe",
   "normalized_name": "severe",
   "status": "absent",
   "assertion": "negative",
   "reported_by": "doctor",
   "temporality": "current",
   "source_segments": [
    "SEG0002",
    "SEG0003",
    "SEG0005",
    "SEG0007",
    "SEG0008",
    "SEG0009",
    "SEG0010",
    "SEG0011",
    "SEG0013",
    "SEG0014",
    "SEG0015",
    "SEG0017",
    "SEG0019",
    "SEG0020",
    "SEG0021",
    "SEG0022",
    "SEG0023",
    "SEG0024",
    "SEG0025",
    "SEG0026",
    "SEG0027",
    "SEG0028",
    "SEG0029",
    "SEG0030",
    "SEG0031",
    "SEG0032",
    "SEG0033",
    "SEG0034",
    "SEG0035",
    "SEG0036",
    "SEG0037",
    "SEG0038",
    "SEG0039"
   ]
  }
 ],
 "medical_history": {
  "past_medical_history": [],
  "surgical_history": [],
  "family_history": [],
  "social_history": []
 },
 "medications": [
  {
   "name": "aspirin",
   "normalized_name": "aspirin",
   "generic_name": "aspirin",
   "dose": "75 milligrams",
   "route": "oral",
   "frequency": "once a day",
   "status": "currently_used"
  }
 ],
 "allergies": [
  {
   "substance": "none",
   "normalized_substance": "none",
   "allergy_type": "none",
   "reaction": "none",
   "severity": "unknown",
   "status": "reported",
   "reported_by": "none"
  }
 ],
 "vital_signs": [
  {
   "name": "heart rate",
   "normalized_name": "heart rate",
   "value": "79",
   "unit": "beats per minute",
   "reported_by": "none",
   "source_segments": [
    "SEG0028"
   ]
  },
  {
   "name": "temperature",
   "normalized_name": "temperature",
   "value": "36.7",
   "unit": "degrees Celsius",
   "reported_by": "none",
   "source_segments": [
    "SEG0028"
   ]
  },
  {
   "name": "blood pressure",
   "normalized_name": "blood pressure",
   "value": "167 over 90",
   "unit": "mmHg",
   "reported_by": "none",
   "source_segments": [
    "SEG0028"
   ]
  }
 ],
 "physical_examination": [
  {
   "finding": "severe",
   "normalized_finding": "severe",
   "body_site": "cardiovascular",
   "status": "present",
   "observed_by": "none",
   "source_segments": [
    "SEG0028"
   ]
  }
 ],
 "review_of_systems": [
  {
   "system": "cardiovascular",
   "status": "negative",
   "details": "severe",
   "reported_by": "none",
   "source_segments": [
    "SEG0028"
   ]
  }
 ],
 "clinical_conditions": [
  {
   "name": "severe",
   "normalized_name": "severe",
   "status": "existing",
   "duration": null,
   "reported_by": "none",
   "source_segments": [
    "SEG0028"
   ]
  }
 ],
 "clinical_assessment": {
  "assessment": "provisional",
  "normalized_assessment": "provisional",
  "certainty": "provisional",
  "basis": "doctor",
  "stated_by": "doctor",
  "source_segments": [
   "SEG0028"
  ]
 },
 "procedures_and_investigations": [
  {
   "name": "ECG",
   "normalized_name": "ECG",
   "type": "laboratory",
   "status": "planned",
   "requested_by": "none",
   "indication": "stroke",
   "scheduled_datetime": null,
   "source_segments": [
    "SEG0035",
    "SEG0036",
    "SEG0037",
    "SEG0038",
    "SEG0039"
   ]
  }
 ],
 "clinical_actions": [
  {
   "action_type": "consultation",
   "description": "arrange ECG for possible stroke",
   "status": "completed",
   "responsible_person": "doctor",
   "time_reference": "none",
   "source_segments": [
    "SEG0035",
    "SEG0036",
    "SEG0037",
    "SEG0038",
    "SEG0039"
   ]
  }
 ],
 "follow_up": {
  "type": "consultation",
  "normalized_datetime": null,
  "status": "conditional"
 },
 "clinical_uncertainties": [],
 "quality_checks": {
  "negation_detected": false,
  "temporality_detected": false,
  "speaker_attribution_available": true,
  "unsupported_clinical_claims": [],
  "contradictions_detected": [],
  "ambiguous_entities": [],
  "requires_clinician_review": false
 }
}
```

### 00035 - final built JSON (after the evidence builder; validator-checked)
```json
{
 "encounter_id": "00035",
 "extraction_status": "completed",
 "encounter_metadata": {
  "encounter_date": null,
  "encounter_type": "outpatient_consultation",
  "language": "en",
  "primary_speakers": [
   {
    "speaker_id": "SEG0002",
    "role": "DOCTOR",
    "role_confidence": null
   }
  ]
 },
 "chief_complaint": {
  "value": "severe",
  "normalized_value": "severe",
  "reported_by": "doctor",
  "evidence_ids": [
   "EV_001"
  ]
 },
 "symptoms": [
  {
   "name": "severe",
   "normalized_name": "severe",
   "category": "cardiovascular",
   "status": "resolved",
   "duration": null,
   "frequency": null,
   "onset": null,
   "temporality": "current",
   "body_site": "cardiovascular",
   "associated_symptoms": [],
   "aggravating_factors": [],
   "relieving_factors": [],
   "reported_by": "doctor",
   "certainty": "uncertain",
   "evidence_ids": [
    "EV_001",
    "EV_002",
    "EV_003",
    "EV_004",
    "EV_005",
    "EV_006",
    "EV_007",
    "EV_008",
    "EV_009",
    "EV_010",
    "EV_011",
    "EV_012",
    "EV_013",
    "EV_014",
    "EV_015",
    "EV_016",
    "EV_017",
    "EV_018",
    "EV_019",
    "EV_020",
    "EV_021",
    "EV_022",
    "EV_023",
    "EV_024",
    "EV_025",
    "EV_026",
    "EV_027",
    "EV_028",
    "EV_029",
    "EV_030",
    "EV_031",
    "EV_032",
    "EV_033"
   ]
  }
 ],
 "negative_findings": [
  {
   "finding": "severe",
   "normalized_name": "severe",
   "status": "absent",
   "assertion": "negative",
   "reported_by": "doctor",
   "temporality": "current",
   "evidence_ids": [
    "EV_001",
    "EV_002",
    "EV_003",
    "EV_004",
    "EV_005",
    "EV_006",
    "EV_007",
    "EV_008",
    "EV_009",
    "EV_010",
    "EV_011",
    "EV_012",
    "EV_013",
    "EV_014",
    "EV_015",
    "EV_016",
    "EV_017",
    "EV_018",
    "EV_019",
    "EV_020",
    "EV_021",
    "EV_022",
    "EV_023",
    "EV_024",
    "EV_025",
    "EV_026",
    "EV_027",
    "EV_028",
    "EV_029",
    "EV_030",
    "EV_031",
    "EV_032",
    "EV_033"
   ]
  }
 ],
 "medical_history": {
  "past_medical_history": [],
  "surgical_history": [],
  "family_history": [],
  "social_history": []
 },
 "medications": [
  {
   "name": "aspirin",
   "normalized_name": "aspirin",
   "generic_name": "aspirin",
   "dose": "75 milligrams",
   "route": "oral",
   "frequency": "once a day",
   "status": "currently_used",
   "evidence_ids": []
  }
 ],
 "allergies": [
  {
   "substance": "none",
   "normalized_substance": "none",
   "allergy_type": "none",
   "reaction": "none",
   "severity": "unknown",
   "status": "reported",
   "reported_by": "none",
   "evidence_ids": []
  }
 ],
 "vital_signs": [
  {
   "name": "heart rate",
   "normalized_name": "heart rate",
   "value": "79",
   "unit": "beats per minute",
   "reported_by": "none",
   "evidence_ids": [
    "EV_022"
   ]
  },
  {
   "name": "temperature",
   "normalized_name": "temperature",
   "value": "36.7",
   "unit": "degrees Celsius",
   "reported_by": "none",
   "evidence_ids": [
    "EV_022"
   ]
  },
  {
   "name": "blood pressure",
   "normalized_name": "blood pressure",
   "value": "167 over 90",
   "unit": "mmHg",
   "reported_by": "none",
   "evidence_ids": [
    "EV_022"
   ]
  }
 ],
 "physical_examination": [
  {
   "finding": "severe",
   "normalized_finding": "severe",
   "body_site": "cardiovascular",
   "status": "present",
   "observed_by": "none",
   "evidence_ids": [
    "EV_022"
   ]
  }
 ],
 "review_of_systems": [
  {
   "system": "cardiovascular",
   "status": "negative",
   "details": "severe",
   "reported_by": "none",
   "evidence_ids": [
    "EV_022"
   ]
  }
 ],
 "clinical_conditions": [
  {
   "name": "severe",
   "normalized_name": "severe",
   "status": "existing",
   "duration": null,
   "reported_by": "none",
   "evidence_ids": [
    "EV_022"
   ]
  }
 ],
 "clinical_assessment": {
  "assessment": "provisional",
  "normalized_assessment": "provisional",
  "certainty": "provisional",
  "basis": "doctor",
  "stated_by": "doctor",
  "source_segments": [
   "SEG0028"
  ]
 },
 "procedures_and_investigations": [
  {
   "name": "ECG",
   "normalized_name": "ECG",
   "type": "laboratory",
   "status": "planned",
   "requested_by": "none",
   "indication": "stroke",
   "scheduled_datetime": null,
   "evidence_ids": [
    "EV_029",
    "EV_030",
    "EV_031",
    "EV_032",
    "EV_033"
   ]
  }
 ],
 "clinical_actions": [
  {
   "action_type": "consultation",
   "description": "arrange ECG for possible stroke",
   "status": "completed",
   "responsible_person": "doctor",
   "time_reference": "none",
   "evidence_ids": [
    "EV_029",
    "EV_030",
    "EV_031",
    "EV_032",
    "EV_033"
   ]
  }
 ],
 "follow_up": {
  "type": "consultation",
  "normalized_datetime": null,
  "status": "conditional"
 },
 "clinical_uncertainties": [],
 "clinical_evidence": [
  {
   "evidence_id": "EV_001",
   "speaker_id": "person_2",
   "speaker_role": "doctor",
   "transcript_text": "You're fine, sit down. So, what brings you in?",
   "start_timestamp": "00:07",
   "end_timestamp": "00:11",
   "supports": [
    "chief_complaint",
    "symptoms[0]",
    "negative_findings[0]"
   ]
  },
  {
   "evidence_id": "EV_002",
   "speaker_id": "person_1",
   "speaker_role": "patient",
   "transcript_text": "Yeah, it's a slight slur in my speech. I don't know what's causing it. I didn't want to make a fuss, you know.",
   "start_timestamp": "00:15",
   "end_timestamp": "00:26",
   "supports": [
    "symptoms[0]",
    "negative_findings[0]"
   ]
  },
  {
   "evidence_id": "EV_003",
   "speaker_id": "person_1",
   "speaker_role": "patient",
   "transcript_text": "For ten days, I'd say.",
   "start_timestamp": "00:30",
   "end_timestamp": "00:33",
   "supports": [
    "symptoms[0]",
    "negative_findings[0]"
   ]
  },
  {
   "evidence_id": "EV_004",
   "speaker_id": "person_1",
   "speaker_role": "patient",
   "transcript_text": "I'd say severe.",
   "start_timestamp": "00:42",
   "end_timestamp": "00:44",
   "supports": [
    "symptoms[0]",
    "negative_findings[0]"
   ]
  },
  {
   "evidence_id": "EV_005",
   "speaker_id": "person_2",
   "speaker_role": "doctor",
   "transcript_text": "Any palpitations, chest pain or confusion at all?",
   "start_timestamp": "01:00",
   "end_timestamp": "01:03",
   "supports": [
    "symptoms[0]",
    "negative_findings[0]"
   ]
  },
  {
   "evidence_id": "EV_006",
   "speaker_id": "person_1",
   "speaker_role": "patient",
   "transcript_text": "I haven't had palpitations, chest pain or confusion, no.",
   "start_timestamp": "01:06",
   "end_timestamp": "01:11",
   "supports": [
    "symptoms[0]",
    "negative_findings[0]"
   ]
  },
  {
   "evidence_id": "EV_007",
   "speaker_id": "person_2",
   "speaker_role": "doctor",
   "transcript_text": "Okay, is your mobility otherwise okay?",
   "start_timestamp": "01:13",
   "end_timestamp": "01:16",
   "supports": [
    "symptoms[0]",
    "negative_findings[0]"
   ]
  },
  {
   "evidence_id": "EV_008",
   "speaker_id": "person_1",
   "speaker_role": "patient",
   "transcript_text": "I move fine otherwise.",
   "start_timestamp": "01:18",
   "end_timestamp": "01:20",
   "supports": [
    "symptoms[0]",
    "negative_findings[0]"
   ]
  },
  {
   "evidence_id": "EV_009",
   "speaker_id": "person_1",
   "speaker_role": "patient",
   "transcript_text": "No, uh, none that I know of.",
   "start_timestamp": "01:36",
   "end_timestamp": "01:40",
   "supports": [
    "symptoms[0]",
    "negative_findings[0]"
   ]
  },
  {
   "evidence_id": "EV_010",
   "speaker_id": "person_2",
   "speaker_role": "doctor",
   "transcript_text": "Are there any allergies on your record that I should check?",
   "start_timestamp": "01:41",
   "end_timestamp": "01:45",
   "supports": [
    "symptoms[0]",
    "negative_findings[0]"
   ]
  },
  {
   "evidence_id": "EV_011",
   "speaker_id": "person_1",
   "speaker_role": "patient",
   "transcript_text": "No, no allergies to anything.",
   "start_timestamp": "01:47",
   "end_timestamp": "01:49",
   "supports": [
    "symptoms[0]",
    "negative_findings[0]"
   ]
  },
  {
   "evidence_id": "EV_012",
   "speaker_id": "person_1",
   "speaker_role": "patient",
   "transcript_text": "Just a lump removed from my back, years ago.",
   "start_timestamp": "01:54",
   "end_timestamp": "01:59",
   "supports": [
    "symptoms[0]",
    "negative_findings[0]"
   ]
  },
  {
   "evidence_id": "EV_013",
   "speaker_id": "person_1",
   "speaker_role": "patient",
   "transcript_text": "It's just me and my wife at home now.",
   "start_timestamp": "02:03",
   "end_timestamp": "02:07",
   "supports": [
    "symptoms[0]",
    "negative_findings[0]"
   ]
  },
  {
   "evidence_id": "EV_014",
   "speaker_id": "person_2",
   "speaker_role": "doctor",
   "transcript_text": "Tell me about your work.",
   "start_timestamp": "02:09",
   "end_timestamp": "02:12",
   "supports": [
    "symptoms[0]",
    "negative_findings[0]"
   ]
  },
  {
   "evidence_id": "EV_015",
   "speaker_id": "person_1",
   "speaker_role": "patient",
   "transcript_text": "I'm a software engineer, so I'm at a screen all day.",
   "start_timestamp": "02:13",
   "end_timestamp": "02:18",
   "supports": [
    "symptoms[0]",
    "negative_findings[0]"
   ]
  },
  {
   "evidence_id": "EV_016",
   "speaker_id": "person_2",
   "speaker_role": "doctor",
   "transcript_text": "Any relatives with health problems I should be aware of?",
   "start_timestamp": "02:23",
   "end_timestamp": "02:27",
   "supports": [
    "symptoms[0]",
    "negative_findings[0]"
   ]
  },
  {
   "evidence_id": "EV_017",
   "speaker_id": "person_1",
   "speaker_role": "patient",
   "transcript_text": "Uh, you know, my father had a heart attack.",
   "start_timestamp": "02:28",
   "end_timestamp": "02:34",
   "supports": [
    "symptoms[0]",
    "negative_findings[0]"
   ]
  },
  {
   "evidence_id": "EV_018",
   "speaker_id": "person_2",
   "speaker_role": "doctor",
   "transcript_text": "Let's go through your medication. What are you taking?",
   "start_timestamp": "02:35",
   "end_timestamp": "02:39",
   "supports": [
    "symptoms[0]",
    "negative_findings[0]"
   ]
  },
  {
   "evidence_id": "EV_019",
   "speaker_id": "person_1",
   "speaker_role": "patient",
   "transcript_text": "It's aspirin, 75 milligrams, once a day.",
   "start_timestamp": "02:40",
   "end_timestamp": "02:43",
   "supports": [
    "symptoms[0]",
    "negative_findings[0]"
   ]
  },
  {
   "evidence_id": "EV_020",
   "speaker_id": "person_2",
   "speaker_role": "doctor",
   "transcript_text": "Let me measure a few things.",
   "start_timestamp": "02:58",
   "end_timestamp": "03:00",
   "supports": [
    "symptoms[0]",
    "negative_findings[0]"
   ]
  },
  {
   "evidence_id": "EV_021",
   "speaker_id": "person_2",
   "speaker_role": "doctor",
   "transcript_text": "Hold still for me...",
   "start_timestamp": "03:10",
   "end_timestamp": "03:12",
   "supports": [
    "symptoms[0]",
    "negative_findings[0]"
   ]
  },
  {
   "evidence_id": "EV_022",
   "speaker_id": "person_2",
   "speaker_role": "doctor",
   "transcript_text": "Okay: heart rate 79, temp 36.7 degrees, pressure 167 over 90. And oxygen saturation is 96 percent.",
   "start_timestamp": "03:29",
   "end_timestamp": "03:37",
   "supports": [
    "symptoms[0]",
    "negative_findings[0]",
    "vital_signs[0]",
    "vital_signs[1]",
    "vital_signs[2]",
    "physical_examination[0]",
    "review_of_systems[0]",
    "clinical_conditions[0]"
   ]
  },
  {
   "evidence_id": "EV_023",
   "speaker_id": "person_1",
   "speaker_role": "patient",
   "transcript_text": "Is that normal?",
   "start_timestamp": "03:38",
   "end_timestamp": "03:40",
   "supports": [
    "symptoms[0]",
    "negative_findings[0]"
   ]
  },
  {
   "evidence_id": "EV_024",
   "speaker_id": "person_2",
   "speaker_role": "doctor",
   "transcript_text": "That's fine, we'll come to it.",
   "start_timestamp": "03:41",
   "end_timestamp": "03:43",
   "supports": [
    "symptoms[0]",
    "negative_findings[0]"
   ]
  },
  {
   "evidence_id": "EV_025",
   "speaker_id": "person_2",
   "speaker_role": "doctor",
   "transcript_text": "Let me tell you where I've got to. It points towards a possible mini-stroke, which we need to investigate urgently.",
   "start_timestamp": "03:57",
   "end_timestamp": "04:06",
   "supports": [
    "symptoms[0]",
    "negative_findings[0]"
   ]
  },
  {
   "evidence_id": "EV_026",
   "speaker_id": "person_1",
   "speaker_role": "patient",
   "transcript_text": "I've been thinking the worst, uh, to be honest. Is it bad?",
   "start_timestamp": "04:08",
   "end_timestamp": "04:15",
   "supports": [
    "symptoms[0]",
    "negative_findings[0]"
   ]
  },
  {
   "evidence_id": "EV_027",
   "speaker_id": "person_2",
   "speaker_role": "doctor",
   "transcript_text": "I can't promise yet, but most people with a possible mini-stroke, which we need to investigate urgently do well once it's treated properly. Just to be sure I understood. You've had a slight slur in your speech for ten days, severe, and no palpitations or chest pain.",
   "start_timestamp": "04:16",
   "end_timestamp": "04:38",
   "supports": [
    "symptoms[0]",
    "negative_findings[0]"
   ]
  },
  {
   "evidence_id": "EV_028",
   "speaker_id": "person_1",
   "speaker_role": "patient",
   "transcript_text": "So, that's what happened, yes.",
   "start_timestamp": "04:39",
   "end_timestamp": "04:42",
   "supports": [
    "symptoms[0]",
    "negative_findings[0]"
   ]
  },
  {
   "evidence_id": "EV_029",
   "speaker_id": "person_2",
   "speaker_role": "doctor",
   "transcript_text": "I'd like to arrange an ECG for possible stroke. I'd rather check than guess, and this is the quickest way to know more. Don't drive for now, and bring someone with you to the next visit. If the numbness, weakness or speech problem returns, that's the point to come in urgently. We'll catch up after the results are back.",
   "start_timestamp": "04:43",
   "end_timestamp": "05:09",
   "supports": [
    "symptoms[0]",
    "negative_findings[0]",
    "procedures_and_investigations[0]",
    "clinical_actions[0]"
   ]
  },
  {
   "evidence_id": "EV_030",
   "speaker_id": "person_1",
   "speaker_role": "patient",
   "transcript_text": "Okay.",
   "start_timestamp": "05:10",
   "end_timestamp": "05:10",
   "supports": [
    "symptoms[0]",
    "negative_findings[0]",
    "procedures_and_investigations[0]",
    "clinical_actions[0]"
   ]
  },
  {
   "evidence_id": "EV_031",
   "speaker_id": "person_2",
   "speaker_role": "doctor",
   "transcript_text": "Alright, take care, and call us if anything changes.",
   "start_timestamp": "05:12",
   "end_timestamp": "05:16",
   "supports": [
    "symptoms[0]",
    "negative_findings[0]",
    "procedures_and_investigations[0]",
    "clinical_actions[0]"
   ]
  },
  {
   "evidence_id": "EV_032",
   "speaker_id": "person_1",
   "speaker_role": "patient",
   "transcript_text": "Thanks so much, doctor.",
   "start_timestamp": "05:17",
   "end_timestamp": "05:19",
   "supports": [
    "symptoms[0]",
    "negative_findings[0]",
    "procedures_and_investigations[0]",
    "clinical_actions[0]"
   ]
  },
  {
   "evidence_id": "EV_033",
   "speaker_id": "person_2",
   "speaker_role": "doctor",
   "transcript_text": "All the best.",
   "start_timestamp": "05:20",
   "end_timestamp": "05:21",
   "supports": [
    "symptoms[0]",
    "negative_findings[0]",
    "procedures_and_investigations[0]",
    "clinical_actions[0]"
   ]
  }
 ],
 "quality_checks": {
  "negation_detected": false,
  "temporality_detected": false,
  "speaker_attribution_available": true,
  "unsupported_clinical_claims": [],
  "contradictions_detected": [],
  "ambiguous_entities": [],
  "requires_clinician_review": false
 }
}
```

### 00037 - intermediate model JSON (what Qwen produced, parsed; before evidence building)
```json
{
 "RAW_MODEL_OUTPUT_NOT_PARSED": "```json\n{\n  \"encounter_id\": \"00037\",\n  \"extraction_status\": \"completed\",\n  \"encounter_metadata\": {\n    \"encounter_date\": null,\n    \"encounter_type\": \"outpatient_consultation\",\n    \"language\": \"en\",\n    \"primary_speakers\": [\n      {\n        \"speaker_id\": \"SEG0001\",\n        \"role\": \"doctor\",\n        \"role_confidence\": null\n      },\n      {\n        \"speaker_id\": \"SEG0019\",\n        \"role\": \"doctor\",\n        \"role_confidence\": null\n      },\n      {\n        \"speaker_id\": \"SEG0020\",\n        \"role\": \"doctor\",\n        \"role_confidence\": null\n      },\n      {\n        \"speaker_id\": \"SEG0021\",\n        \"role\": \"caregiver\",\n        \"role_confidence\": null\n      },\n      {\n        \"speaker_id\": \"SEG0023\",\n        \"role\": \"caregiver\",\n        \"role_confidence\": null\n      },\n      {\n        \"speaker_id\": \"SEG0024\",\n        \"role\": \"patient\",\n        \"role_confidence\": null\n      },\n      {\n        \"speaker_id\": \"SEG0025\",\n        \"role\": \"patient\",\n        \"role_confidence\": null\n      },\n      {\n        \"speaker_id\": \"SEG0027\",\n        \"role\": \"patient\",\n        \"role_confidence\": null\n      },\n      {\n        \"speaker_id\": \"SEG0028\",\n        \"role\": \"patient\",\n        \"role_confidence\": null\n      },\n      {\n        \"speaker_id\": \"SEG0030\",\n        \"role\": \"patient\",\n        \"role_confidence\": null\n      },\n      {\n        \"speaker_id\": \"SEG0033\",\n        \"role\": \"patient\",\n        \"role_confidence\": null\n      },\n      {\n        \"speaker_id\": \"SEG0034\",\n        \"role\": \"patient\",\n        \"role_confidence\": null\n      },\n      {\n        \"speaker_id\": \"SEG0035\",\n        \"role\": \"patient\",\n        \"role_confidence\": null\n      },\n      {\n        \"speaker_id\": \"SEG0036\",\n        \"role\": \"patient\",\n        \"role_confidence\": null\n      },\n      {\n        \"speaker_id\": \"SEG0037\",\n        \"role\": \"patient\",\n        \"role_confidence\": null\n      }\n    ]\n  },\n  \"chief_complaint\": {\n    \"value\": \"fever and joint pains\",\n    \"normalized_value\": \"fever and joint pains\",\n    \"reported_by\": \"doctor\",\n    \"source_segments\": [\"SEG0001\", \"SEG0002\", \"SEG0003\", \"SEG0004\", \"SEG0005\", \"SEG0006\", \"SEG0007\", \"SEG0008\", \"SEG0009\", \"SEG0010\", \"SEG0011\", \"SEG0012\", \"SEG0013\", \"SEG0014\", \"SEG0015\", \"SEG0016\", \"SEG0017\", \"SEG0018\", \"SEG0019\", \"SEG0020\", \"SEG0021\", \"SEG0022\", \"SEG0023\", \"SEG0024\", \"SEG0025\", \"SEG0026\", \"SEG0027\", \"SEG0028\", \"SEG0029\", \"SEG0030\", \"SEG0031\", \"SEG0032\", \"SEG0033\", \"SEG0034\", \"SEG0035\", \"SEG0036\", \"SEG0037\"]\n  },\n  \"symptoms\": [\n    {\n      \"name\": \"fever and joint pains\",\n      \"normalized_name\": \"fever and joint pains\",\n      \"category\": \"cardiovascular\",\n      \"status\": \"present\",\n      \"severity\": \"mild\",\n      \"duration\": null,\n      \"frequency\": null,\n      \"onset\": null,\n      \"temporality\": \"current\",\n      \"body_site\": \"system\",\n      \"associated_symptoms\": [],\n      \"aggravating_factors\": [],\n      \"relieving_factors\": [],\n      \"reported_by\": \"doctor\",\n      \"certainty\": \"present\",\n      \"source_segments\": [\"SEG0001\", \"SEG0002\", \"SEG0003\", \"SEG0004\", \"SEG0005\", \"SEG0006\", \"SEG0007\", \"SEG0008\", \"SEG0009\", \"SEG0010\", \"SEG0011\", \"SEG0012\", \"SEG0013\", \"SEG0014\", \"SEG0015\", \"SEG0016\", \"SEG0017\", \"SEG0018\", \"SEG0019\", \"SEG0020\", \"SEG0021\", \"SEG0022\", \"SEG0023\", \"SEG0024\", \"SEG0025\", \"SEG0026\", \"SEG0027\", \"SEG0028\", \"SEG0029\", \"SEG0030\", \"SEG0031\", \"SEG0032\", \"SEG0033\", \"SEG0034\", \"SEG0035\", \"SEG0036\", \"SEG0037\"]\n    }\n  ],\n  \"negative_findings\": [\n    {\n      \"finding\": \"fever and joint pains\",\n      \"normalized_name\": \"fever and joint pains\",\n      \"status\": \"absent\",\n      \"assertion\": \"negative\",\n      \"reported_by\": \"doctor\",\n      \"temporality\": \"current\",\n      \"source_segments\": [\"SEG0001\", \"SEG0002\", \"SEG0003\", \"SEG0004\", \"SEG0005\", \"SEG0006\", \"SEG0007\", \"SEG0008\", \"SEG0009\", \"SEG0010\", \"SEG0011\", \"SEG0012\", \"SEG0013\", \"SEG0014\", \"SEG0015\", \"SEG0016\", \"SEG0017\", \"SEG0018\", \"SEG0019\", \"SEG0020\", \"SEG0021\", \"SEG0022\", \"SEG0023\", \"SEG0024\", \"SEG0025\", \"SEG0026\", \"SEG0027\", \"SEG0028\", \"SEG0029\", \"SEG0030\", \"SEG0031\", \"SEG0032\", \"SEG0033\", \"SEG0034\", \"SEG0035\", \"SEG0036\", \"SEG0037\"]\n    }\n  ],\n  \"medical_history\": {\n    \"past_medical_history\": [\n      {\n        \"condition\": \"high blood pressure\",\n        \"normalized_condition\": \"high blood pressure\",\n        \"status\": \"ongoing\",\n        \"duration\": null,\n        \"reported_by\": \"doctor\",\n        \"source_segments\": [\"SEG0013\", \"SEG0014\", \"SEG0015\", \"SEG0016\", \"SEG0017\", \"SEG0018\", \"SEG0019\", \"SEG0020\", \"SEG0021\", \"SEG0022\", \"SEG0023\", \"SEG0024\", \"SEG0025\", \"SEG0026\", \"SEG0027\", \"SEG0028\", \"SEG0029\", \"SEG0030\", \"SEG0031\", \"SEG0032\", \"SEG0033\", \"SEG0034\", \"SEG0035\", \"SEG0036\", \"SEG0037\"]\n      },\n      {\n        \"procedure\": \"stent\",\n        \"normalized_procedure\": \"stent\",\n        \"timeframe\": null,\n        \"reported_by\": \"caregiver\",\n        \"source_segments\": [\"SEG0017\", \"SEG0020\", \"SEG0021\", \"SEG0022\", \"SEG0023\", \"SEG0024\", \"SEG0025\", \"SEG0026\", \"SEG0027\", \"SEG0028\", \"SEG0029\", \"SEG0030\", \"SEG0031\", \"SEG0032\", \"SEG0033\", \"SEG0034\", \"SEG0035\", \"SEG0036\", \"SEG0037\"]\n      },\n      {\n        \"family_history\": {\n          \"condition\": \"thyroid problems\",\n          \"relation\": \"family\",\n          \"reported_by\": \"doctor\",\n          \"source_segments\": [\"SEG0015\", \"SEG0016\", \"SEG0017\", \"SEG0018\", \"SEG0019\", \"SEG0020\", \"SEG0021\", \"SEG0022\", \"SEG0023\", \"SEG0024\", \"SEG0025\", \"SEG0026\", \"SEG0027\", \"SEG0028\", \"SEG0029\", \"SEG0030\", \"SEG0031\", \"SEG0032\", \"SEG0033\", \"SEG0034\", \"SEG0035\", \"SEG0036\", \"SEG0037\"]\n        }\n      },\n      {\n        \"social_history\": {\n          \"category\": \"lifestyle\",\n          \"description\": \"smoking\",\n          \"status\": \"ongoing\",\n          \"details\": null,\n          \"reported_by\": \"caregiver\",\n          \"source_segments\": [\"SEG0027\", \"SEG0028\", \"SEG0030\", \"SEG0031\", \"SEG0032\", \"SEG0033\", \"SEG0034\", \"SEG0035\", \"SEG0036\", \"SEG0037\"]\n        }\n      }\n    },\n    \"surgical_history\": [\n      {\n        \"procedure\": \"stent\",\n        \"normalized_procedure\": \"stent\",\n        \"timeframe\": null,\n        \"reported_by\": \"caregiver\",\n   "
}
```

### 00040 - intermediate model JSON (what Qwen produced, parsed; before evidence building)
```json
{
 "encounter_id": "00040",
 "extraction_status": "completed",
 "encounter_metadata": {
  "encounter_date": null,
  "encounter_type": "outpatient_consultation",
  "language": "en"
 },
 "chief_complaint": {
  "value": "twitching in fingers",
  "normalized_value": "twitching in fingers",
  "reported_by": "patient",
  "source_segments": [
   "SEG0001"
  ]
 },
 "symptoms": [
  {
   "name": "twitching in fingers",
   "normalized_name": "twitching in fingers",
   "category": "musculoskeletal",
   "status": "present",
   "certainty": "uncertain",
   "duration": null,
   "frequency": null,
   "onset": null,
   "temporality": "current",
   "body_site": "fingers",
   "associated_symptoms": [],
   "aggravating_factors": [],
   "relieving_factors": [],
   "reported_by": "patient",
   "source_segments": [
    "SEG0001",
    "SEG0003",
    "SEG0005",
    "SEG0007",
    "SEG0009"
   ]
  }
 ],
 "negative_findings": [
  {
   "finding": "twitching in fingers",
   "normalized_name": "twitching in fingers",
   "status": "absent",
   "assertion": "negative",
   "reported_by": "patient",
   "temporality": "current",
   "source_segments": [
    "SEG0001",
    "SEG0003",
    "SEG0005",
    "SEG0007",
    "SEG0009"
   ]
  }
 ],
 "medical_history": {
  "past_medical_history": [],
  "surgical_history": [],
  "family_history": [],
  "social_history": []
 },
 "medications": [
  {
   "name": "thyroxine",
   "normalized_name": "thyroxine",
   "status": "currently_used",
   "route": "oral",
   "dose": "75 micrograms",
   "frequency": "every morning"
  }
 ],
 "allergies": [
  {
   "substance": "antibiotic",
   "normalized_substance": "antibiotic",
   "allergy_type": "medication",
   "reaction": "years ago",
   "status": "reported",
   "reported_by": "patient"
  }
 ],
 "vital_signs": [
  {
   "name": "temperature",
   "normalized_name": "temperature",
   "value": "36.7",
   "unit": "°C",
   "reported_by": "doctor",
   "source_segments": [
    "SEG0046",
    "SEG0047",
    "SEG0048",
    "SEG0049",
    "SEG0050",
    "SEG0051",
    "SEG0052",
    "SEG0053",
    "SEG0054",
    "SEG0055",
    "SEG0056",
    "SEG0057",
    "SEG0058"
   ]
  }
 ],
 "physical_examination": [
  {
   "finding": "twitching in fingers",
   "normalized_finding": "twitching in fingers",
   "body_site": "fingers",
   "status": "present",
   "observed_by": "doctor",
   "source_segments": [
    "SEG0001",
    "SEG0003",
    "SEG0005",
    "SEG0007",
    "SEG0009"
   ]
  }
 ],
 "review_of_systems": [
  {
   "system": "musculoskeletal",
   "status": "negative",
   "details": "twitching in fingers"
  }
 ],
 "clinical_conditions": [
  {
   "name": "underactive thyroid",
   "normalized_name": "underactive thyroid",
   "status": "existing",
   "duration": "10 years",
   "reported_by": "patient",
   "source_segments": [
    "SEG0029",
    "SEG0031",
    "SEG0033",
    "SEG0035",
    "SEG0037",
    "SEG0039",
    "SEG0040",
    "SEG0041",
    "SEG0043",
    "SEG0045",
    "SEG0047",
    "SEG0048",
    "SEG0049",
    "SEG0050",
    "SEG0051",
    "SEG0052",
    "SEG0053",
    "SEG0054",
    "SEG0055",
    "SEG0056",
    "SEG0057",
    "SEG0058"
   ]
  }
 ],
 "clinical_assessment": {
  "assessment": "carpal tunnel syndrome",
  "normalized_assessment": "carpal tunnel syndrome",
  "certainty": "differential",
  "basis": "physical examination",
  "stated_by": "doctor",
  "source_segments": [
   "SEG0053",
   "SEG0055",
   "SEG0057",
   "SEG0058"
  ]
 },
 "procedures_and_investigations": [],
 "clinical_actions": [],
 "follow_up": {
  "type": "consultation",
  "time_reference": null
 },
 "clinical_uncertainties": [],
 "quality_checks": {
  "negation_detected": false,
  "temporality_detected": false,
  "speaker_attribution_available": true,
  "unsupported_clinical_claims": [],
  "contradictions_detected": [],
  "ambiguous_entities": [],
  "requires_clinician_review": false
 }
}
```

### 00040 - final built JSON (after the evidence builder; validator-checked)
```json
{
 "encounter_id": "00040",
 "extraction_status": "completed",
 "encounter_metadata": {
  "encounter_date": null,
  "encounter_type": "outpatient_consultation",
  "language": "en"
 },
 "chief_complaint": {
  "value": "twitching in fingers",
  "normalized_value": "twitching in fingers",
  "reported_by": "patient",
  "evidence_ids": [
   "EV_001"
  ]
 },
 "symptoms": [
  {
   "name": "twitching in fingers",
   "normalized_name": "twitching in fingers",
   "category": "musculoskeletal",
   "status": "present",
   "certainty": "uncertain",
   "duration": null,
   "frequency": null,
   "onset": null,
   "temporality": "current",
   "body_site": "fingers",
   "associated_symptoms": [],
   "aggravating_factors": [],
   "relieving_factors": [],
   "reported_by": "patient",
   "evidence_ids": [
    "EV_001",
    "EV_002",
    "EV_003",
    "EV_004",
    "EV_005"
   ]
  }
 ],
 "negative_findings": [
  {
   "finding": "twitching in fingers",
   "normalized_name": "twitching in fingers",
   "status": "absent",
   "assertion": "negative",
   "reported_by": "patient",
   "temporality": "current",
   "evidence_ids": [
    "EV_001",
    "EV_002",
    "EV_003",
    "EV_004",
    "EV_005"
   ]
  }
 ],
 "medical_history": {
  "past_medical_history": [],
  "surgical_history": [],
  "family_history": [],
  "social_history": []
 },
 "medications": [
  {
   "name": "thyroxine",
   "normalized_name": "thyroxine",
   "status": "currently_used",
   "route": "oral",
   "dose": "75 micrograms",
   "frequency": "every morning",
   "evidence_ids": []
  }
 ],
 "allergies": [
  {
   "substance": "antibiotic",
   "normalized_substance": "antibiotic",
   "allergy_type": "medication",
   "reaction": "years ago",
   "status": "reported",
   "reported_by": "patient",
   "evidence_ids": []
  }
 ],
 "vital_signs": [
  {
   "name": "temperature",
   "normalized_name": "temperature",
   "value": "36.7",
   "unit": "°C",
   "reported_by": "doctor",
   "evidence_ids": [
    "EV_016",
    "EV_017",
    "EV_018",
    "EV_019",
    "EV_020",
    "EV_021",
    "EV_022",
    "EV_023",
    "EV_024",
    "EV_025",
    "EV_026",
    "EV_027",
    "EV_028"
   ]
  }
 ],
 "physical_examination": [
  {
   "finding": "twitching in fingers",
   "normalized_finding": "twitching in fingers",
   "body_site": "fingers",
   "status": "present",
   "observed_by": "doctor",
   "evidence_ids": [
    "EV_001",
    "EV_002",
    "EV_003",
    "EV_004",
    "EV_005"
   ]
  }
 ],
 "review_of_systems": [
  {
   "system": "musculoskeletal",
   "status": "negative",
   "details": "twitching in fingers",
   "evidence_ids": []
  }
 ],
 "clinical_conditions": [
  {
   "name": "underactive thyroid",
   "normalized_name": "underactive thyroid",
   "status": "existing",
   "duration": "10 years",
   "reported_by": "patient",
   "evidence_ids": [
    "EV_006",
    "EV_007",
    "EV_008",
    "EV_009",
    "EV_010",
    "EV_011",
    "EV_012",
    "EV_013",
    "EV_014",
    "EV_015",
    "EV_017",
    "EV_018",
    "EV_019",
    "EV_020",
    "EV_021",
    "EV_022",
    "EV_023",
    "EV_024",
    "EV_025",
    "EV_026",
    "EV_027",
    "EV_028"
   ]
  }
 ],
 "clinical_assessment": {
  "assessment": "carpal tunnel syndrome",
  "normalized_assessment": "carpal tunnel syndrome",
  "certainty": "differential",
  "basis": "physical examination",
  "stated_by": "doctor",
  "source_segments": [
   "SEG0053",
   "SEG0055",
   "SEG0057",
   "SEG0058"
  ]
 },
 "procedures_and_investigations": [],
 "clinical_actions": [],
 "follow_up": {
  "type": "consultation",
  "time_reference": null
 },
 "clinical_uncertainties": [],
 "clinical_evidence": [
  {
   "evidence_id": "EV_001",
   "speaker_id": "person_1",
   "speaker_role": "patient",
   "transcript_text": "Good afternoon, doctor, the receptionist said you'd see me now.",
   "start_timestamp": "00:01",
   "end_timestamp": "00:06",
   "supports": [
    "chief_complaint",
    "symptoms[0]",
    "negative_findings[0]",
    "physical_examination[0]"
   ]
  },
  {
   "evidence_id": "EV_002",
   "speaker_id": "person_1",
   "speaker_role": "patient",
   "transcript_text": "So the thing is, I've got tingling in my fingers.",
   "start_timestamp": "00:14",
   "end_timestamp": "00:18",
   "supports": [
    "symptoms[0]",
    "negative_findings[0]",
    "physical_examination[0]"
   ]
  },
  {
   "evidence_id": "EV_003",
   "speaker_id": "person_1",
   "speaker_role": "patient",
   "transcript_text": "It's been five days now.",
   "start_timestamp": "00:22",
   "end_timestamp": "00:25",
   "supports": [
    "symptoms[0]",
    "negative_findings[0]",
    "physical_examination[0]"
   ]
  },
  {
   "evidence_id": "EV_004",
   "speaker_id": "person_1",
   "speaker_role": "patient",
   "transcript_text": "Yes, about the same, six months. With ache in the wrist, I'd say moderate. It's a couple of times a week. Oh, and numbness in the thumb and first two fingers.",
   "start_timestamp": "00:31",
   "end_timestamp": "00:48",
   "supports": [
    "symptoms[0]",
    "negative_findings[0]",
    "physical_examination[0]"
   ]
  },
  {
   "evidence_id": "EV_005",
   "speaker_id": "person_1",
   "speaker_role": "patient",
   "transcript_text": "Honestly, once or twice a day. I've been waking up at night with pins and needles too, you know, since Monday.",
   "start_timestamp": "00:54",
   "end_timestamp": "01:06",
   "supports": [
    "symptoms[0]",
    "negative_findings[0]",
    "physical_examination[0]"
   ]
  },
  {
   "evidence_id": "EV_006",
   "speaker_id": "person_1",
   "speaker_role": "patient",
   "transcript_text": "I have an underactive thyroid, for about ten years.",
   "start_timestamp": "03:40",
   "end_timestamp": "03:45",
   "supports": [
    "clinical_conditions[0]"
   ]
  },
  {
   "evidence_id": "EV_007",
   "speaker_id": "person_1",
   "speaker_role": "patient",
   "transcript_text": "I've got diabetes.",
   "start_timestamp": "03:51",
   "end_timestamp": "03:52",
   "supports": [
    "clinical_conditions[0]"
   ]
  },
  {
   "evidence_id": "EV_008",
   "speaker_id": "person_1",
   "speaker_role": "patient",
   "transcript_text": "I've got high cholesterol.",
   "start_timestamp": "03:56",
   "end_timestamp": "03:58",
   "supports": [
    "clinical_conditions[0]"
   ]
  },
  {
   "evidence_id": "EV_009",
   "speaker_id": "person_1",
   "speaker_role": "patient",
   "transcript_text": "No headache or weakness in the legs, none of it.",
   "start_timestamp": "04:10",
   "end_timestamp": "04:15",
   "supports": [
    "clinical_conditions[0]"
   ]
  },
  {
   "evidence_id": "EV_010",
   "speaker_id": "person_1",
   "speaker_role": "patient",
   "transcript_text": "No neck pain, trouble walking or bladder problems, none of it.",
   "start_timestamp": "04:23",
   "end_timestamp": "04:29",
   "supports": [
    "clinical_conditions[0]"
   ]
  },
  {
   "evidence_id": "EV_011",
   "speaker_id": "person_1",
   "speaker_role": "patient",
   "transcript_text": "No. No swelling in the joints.",
   "start_timestamp": "04:34",
   "end_timestamp": "04:37",
   "supports": [
    "clinical_conditions[0]"
   ]
  },
  {
   "evidence_id": "EV_012",
   "speaker_id": "person_2",
   "speaker_role": "doctor",
   "transcript_text": "How about your heart, any problems like that?",
   "start_timestamp": "04:38",
   "end_timestamp": "04:41",
   "supports": [
    "clinical_conditions[0]"
   ]
  },
  {
   "evidence_id": "EV_013",
   "speaker_id": "person_1",
   "speaker_role": "patient",
   "transcript_text": "Nothing like that.",
   "start_timestamp": "04:43",
   "end_timestamp": "04:44",
   "supports": [
    "clinical_conditions[0]"
   ]
  },
  {
   "evidence_id": "EV_014",
   "speaker_id": "person_1",
   "speaker_role": "patient",
   "transcript_text": "Okay, so no problems with breathing.",
   "start_timestamp": "04:49",
   "end_timestamp": "04:52",
   "supports": [
    "clinical_conditions[0]"
   ]
  },
  {
   "evidence_id": "EV_015",
   "speaker_id": "person_2",
   "speaker_role": "doctor",
   "transcript_text": "Rest your hand here...",
   "start_timestamp": "05:03",
   "end_timestamp": "05:05",
   "supports": [
    "clinical_conditions[0]"
   ]
  },
  {
   "evidence_id": "EV_016",
   "speaker_id": "person_2",
   "speaker_role": "doctor",
   "transcript_text": "Okay: temperature 36.7, BP is 123 over 70. And heart rate 64, SpO2 97 percent on room air.",
   "start_timestamp": "05:19",
   "end_timestamp": "05:28",
   "supports": [
    "vital_signs[0]"
   ]
  },
  {
   "evidence_id": "EV_017",
   "speaker_id": "person_2",
   "speaker_role": "doctor",
   "transcript_text": "Let's do the physical part now.",
   "start_timestamp": "05:30",
   "end_timestamp": "05:32",
   "supports": [
    "vital_signs[0]",
    "clinical_conditions[0]"
   ]
  },
  {
   "evidence_id": "EV_018",
   "speaker_id": "person_1",
   "speaker_role": "patient",
   "transcript_text": "Fine.",
   "start_timestamp": "05:34",
   "end_timestamp": "05:34",
   "supports": [
    "vital_signs[0]",
    "clinical_conditions[0]"
   ]
  },
  {
   "evidence_id": "EV_019",
   "speaker_id": "person_2",
   "speaker_role": "doctor",
   "transcript_text": "Take your time, no rush.",
   "start_timestamp": "05:36",
   "end_timestamp": "05:39",
   "supports": [
    "vital_signs[0]",
    "clinical_conditions[0]"
   ]
  },
  {
   "evidence_id": "EV_020",
   "speaker_id": "person_2",
   "speaker_role": "doctor",
   "transcript_text": "Bending the wrist for a minute brings on the numbness.",
   "start_timestamp": "05:56",
   "end_timestamp": "06:00",
   "supports": [
    "vital_signs[0]",
    "clinical_conditions[0]"
   ]
  },
  {
   "evidence_id": "EV_021",
   "speaker_id": "person_2",
   "speaker_role": "doctor",
   "transcript_text": "Let me look at this properly.",
   "start_timestamp": "06:02",
   "end_timestamp": "06:04",
   "supports": [
    "vital_signs[0]",
    "clinical_conditions[0]"
   ]
  },
  {
   "evidence_id": "EV_022",
   "speaker_id": "person_2",
   "speaker_role": "doctor",
   "transcript_text": "Tapping over the wrist reproduces the tingling.",
   "start_timestamp": "06:12",
   "end_timestamp": "06:15",
   "supports": [
    "vital_signs[0]",
    "clinical_conditions[0]"
   ]
  },
  {
   "evidence_id": "EV_023",
   "speaker_id": "person_2",
   "speaker_role": "doctor",
   "transcript_text": "That's all I need, thank you. Right, here's what I'm thinking. The most likely explanation is carpal tunnel syndrome. I can't rule out a pinched nerve in the neck yet. I think a blood sugar test makes sense here, for neuropathy screen. I'd like to arrange a nerve conduction study for hand numbness. Take short breaks from typing and keep the wrist straight. Do get help quickly if the symptoms get worse.",
   "start_timestamp": "06:18",
   "end_timestamp": "06:54",
   "supports": [
    "vital_signs[0]",
    "clinical_conditions[0]"
   ]
  },
  {
   "evidence_id": "EV_024",
   "speaker_id": "person_2",
   "speaker_role": "doctor",
   "transcript_text": "See me again after the results are back.",
   "start_timestamp": "06:56",
   "end_timestamp": "07:00",
   "supports": [
    "vital_signs[0]",
    "clinical_conditions[0]"
   ]
  },
  {
   "evidence_id": "EV_025",
   "speaker_id": "person_1",
   "speaker_role": "patient",
   "transcript_text": "Alright, I'll put it in my diary.",
   "start_timestamp": "07:00",
   "end_timestamp": "07:04",
   "supports": [
    "vital_signs[0]",
    "clinical_conditions[0]"
   ]
  },
  {
   "evidence_id": "EV_026",
   "speaker_id": "person_2",
   "speaker_role": "doctor",
   "transcript_text": "Okay, I think we're finished. Is everything clear?",
   "start_timestamp": "07:08",
   "end_timestamp": "07:11",
   "supports": [
    "vital_signs[0]",
    "clinical_conditions[0]"
   ]
  },
  {
   "evidence_id": "EV_027",
   "speaker_id": "person_1",
   "speaker_role": "patient",
   "transcript_text": "One thing: no, actually that's all. Thanks.",
   "start_timestamp": "07:12",
   "end_timestamp": "07:15",
   "supports": [
    "vital_signs[0]",
    "clinical_conditions[0]"
   ]
  },
  {
   "evidence_id": "EV_028",
   "speaker_id": "person_2",
   "speaker_role": "doctor",
   "transcript_text": "See you then.",
   "start_timestamp": "07:17",
   "end_timestamp": "07:18",
   "supports": [
    "vital_signs[0]",
    "clinical_conditions[0]"
   ]
  }
 ],
 "quality_checks": {
  "negation_detected": false,
  "temporality_detected": false,
  "speaker_attribution_available": true,
  "unsupported_clinical_claims": [],
  "contradictions_detected": [],
  "ambiguous_entities": [],
  "requires_clinician_review": false
 }
}
```

### 00215 - intermediate model JSON (what Qwen produced, parsed; before evidence building)
```json
{
 "encounter_id": "00215",
 "extraction_status": "completed",
 "encounter_metadata": {
  "encounter_date": null,
  "encounter_type": "outpatient_consultation",
  "language": "en",
  "primary_speakers": [
   {
    "speaker_id": "SEG0002",
    "role": "DOCTOR",
    "role_confidence": null
   }
  ]
 },
 "chief_complaint": {
  "value": "severe headaches",
  "normalized_value": "severe headaches",
  "reported_by": "doctor",
  "source_segments": [
   "SEG0002"
  ]
 },
 "symptoms": [
  {
   "name": "headaches",
   "normalized_name": "headaches",
   "category": "cardiovascular",
   "status": "present",
   "certainty": "uncertain",
   "duration": null,
   "frequency": null,
   "onset": null,
   "temporality": "current",
   "body_site": null,
   "associated_symptoms": [],
   "aggravating_factors": [],
   "relieving_factors": [],
   "reported_by": "",
   "source_segments": [
    "SEG0002"
   ]
  }
 ],
 "negative_findings": [
  {
   "finding": "no fever",
   "normalized_name": "no fever",
   "status": "absent",
   "assertion": "negative",
   "reported_by": "",
   "temporality": "current",
   "source_segments": [
    "SEG0002"
   ]
  }
 ],
 "medical_history": {
  "past_medical_history": [],
  "surgical_history": [],
  "family_history": [],
  "social_history": []
 },
 "medications": [
  {
   "name": "Amlodipine",
   "normalized_name": "Amlodipine",
   "status": "currently_used",
   "route": "oral",
   "dose": "5 milligrams",
   "frequency": "once a day"
  }
 ],
 "allergies": [
  {
   "substance": "ibuprofen",
   "normalized_substance": "ibuprofen",
   "allergy_type": "medication",
   "reaction": "rash"
  }
 ],
 "vital_signs": [
  {
   "name": "pulse",
   "normalized_name": "pulse",
   "value": "89",
   "unit": "beats per minute",
   "reported_by": "",
   "source_segments": [
    "SEG0030"
   ]
  },
  {
   "name": "temperature",
   "normalized_name": "temperature",
   "value": "36.8",
   "unit": "degrees Celsius",
   "reported_by": "",
   "source_segments": [
    "SEG0030"
   ]
  },
  {
   "name": "blood pressure",
   "normalized_name": "blood pressure",
   "value": "152/97",
   "unit": "mmHg",
   "reported_by": "",
   "source_segments": [
    "SEG0030"
   ]
  }
 ],
 "physical_examination": [
  {
   "finding": "mild pitting swelling at both ankles",
   "normalized_finding": "mild pitting swelling at both ankles",
   "body_site": "both ankles",
   "status": "present",
   "observed_by": "",
   "source_segments": [
    "SEG0026"
   ]
  }
 ],
 "review_of_systems": [
  {
   "system": "cardiovascular",
   "status": "negative",
   "details": "hypertension not well controlled",
   "reported_by": "",
   "source_segments": [
    "SEG0033"
   ]
  }
 ],
 "clinical_conditions": [
  {
   "name": "high blood pressure",
   "normalized_name": "high blood pressure",
   "status": "existing",
   "duration": null,
   "reported_by": "",
   "source_segments": [
    "SEG0013"
   ]
  }
 ],
 "clinical_assessment": {
  "assessment": "I'd like to arrange a lipid profile for cardiovascular risk.",
  "normalized_assessment": "I'd like to arrange a lipid profile for cardiovascular risk.",
  "certainty": "provisional",
  "basis": "the patient's history of hypertension",
  "stated_by": "doctor",
  "source_segments": [
   "SEG0033"
  ]
 },
 "procedures_and_investigations": [],
 "clinical_actions": [],
 "follow_up": {
  "type": "consultation",
  "time_reference": "",
  "normalized_datetime": null
 },
 "clinical_uncertainties": [],
 "quality_checks": {
  "negation_detected": false,
  "temporality_detected": false,
  "speaker_attribution_available": true,
  "unsupported_clinical_claims": [],
  "contradictions_detected": [],
  "ambiguous_entities": [],
  "requires_clinician_review": false
 }
}
```

### 00215 - final built JSON (after the evidence builder; validator-checked)
```json
{
 "encounter_id": "00215",
 "extraction_status": "completed",
 "encounter_metadata": {
  "encounter_date": null,
  "encounter_type": "outpatient_consultation",
  "language": "en",
  "primary_speakers": [
   {
    "speaker_id": "SEG0002",
    "role": "DOCTOR",
    "role_confidence": null
   }
  ]
 },
 "chief_complaint": {
  "value": "severe headaches",
  "normalized_value": "severe headaches",
  "reported_by": "doctor",
  "evidence_ids": [
   "EV_001"
  ]
 },
 "symptoms": [
  {
   "name": "headaches",
   "normalized_name": "headaches",
   "category": "cardiovascular",
   "status": "present",
   "certainty": "uncertain",
   "duration": null,
   "frequency": null,
   "onset": null,
   "temporality": "current",
   "body_site": null,
   "associated_symptoms": [],
   "aggravating_factors": [],
   "relieving_factors": [],
   "reported_by": "",
   "evidence_ids": [
    "EV_001"
   ]
  }
 ],
 "negative_findings": [
  {
   "finding": "no fever",
   "normalized_name": "no fever",
   "status": "absent",
   "assertion": "negative",
   "reported_by": "",
   "temporality": "current",
   "evidence_ids": [
    "EV_001"
   ]
  }
 ],
 "medical_history": {
  "past_medical_history": [],
  "surgical_history": [],
  "family_history": [],
  "social_history": []
 },
 "medications": [
  {
   "name": "Amlodipine",
   "normalized_name": "Amlodipine",
   "status": "currently_used",
   "route": "oral",
   "dose": "5 milligrams",
   "frequency": "once a day",
   "evidence_ids": []
  }
 ],
 "allergies": [
  {
   "substance": "ibuprofen",
   "normalized_substance": "ibuprofen",
   "allergy_type": "medication",
   "reaction": "rash",
   "evidence_ids": []
  }
 ],
 "vital_signs": [
  {
   "name": "pulse",
   "normalized_name": "pulse",
   "value": "89",
   "unit": "beats per minute",
   "reported_by": "",
   "evidence_ids": [
    "EV_004"
   ]
  },
  {
   "name": "temperature",
   "normalized_name": "temperature",
   "value": "36.8",
   "unit": "degrees Celsius",
   "reported_by": "",
   "evidence_ids": [
    "EV_004"
   ]
  },
  {
   "name": "blood pressure",
   "normalized_name": "blood pressure",
   "value": "152/97",
   "unit": "mmHg",
   "reported_by": "",
   "evidence_ids": [
    "EV_004"
   ]
  }
 ],
 "physical_examination": [
  {
   "finding": "mild pitting swelling at both ankles",
   "normalized_finding": "mild pitting swelling at both ankles",
   "body_site": "both ankles",
   "status": "present",
   "observed_by": "",
   "evidence_ids": [
    "EV_003"
   ]
  }
 ],
 "review_of_systems": [
  {
   "system": "cardiovascular",
   "status": "negative",
   "details": "hypertension not well controlled",
   "reported_by": "",
   "evidence_ids": [
    "EV_005"
   ]
  }
 ],
 "clinical_conditions": [
  {
   "name": "high blood pressure",
   "normalized_name": "high blood pressure",
   "status": "existing",
   "duration": null,
   "reported_by": "",
   "evidence_ids": [
    "EV_002"
   ]
  }
 ],
 "clinical_assessment": {
  "assessment": "I'd like to arrange a lipid profile for cardiovascular risk.",
  "normalized_assessment": "I'd like to arrange a lipid profile for cardiovascular risk.",
  "certainty": "provisional",
  "basis": "the patient's history of hypertension",
  "stated_by": "doctor",
  "source_segments": [
   "SEG0033"
  ]
 },
 "procedures_and_investigations": [],
 "clinical_actions": [],
 "follow_up": {
  "type": "consultation",
  "time_reference": "",
  "normalized_datetime": null
 },
 "clinical_uncertainties": [],
 "clinical_evidence": [
  {
   "evidence_id": "EV_001",
   "speaker_id": "person_2",
   "speaker_role": "doctor",
   "transcript_text": "Of course, put it down anywhere. So, how can I help?",
   "start_timestamp": "00:05",
   "end_timestamp": "00:10",
   "supports": [
    "chief_complaint",
    "symptoms[0]",
    "negative_findings[0]"
   ]
  },
  {
   "evidence_id": "EV_002",
   "speaker_id": "person_1",
   "speaker_role": "patient",
   "transcript_text": "Um, I have high blood pressure, for nearly five years.",
   "start_timestamp": "01:38",
   "end_timestamp": "01:44",
   "supports": [
    "clinical_conditions[0]"
   ]
  },
  {
   "evidence_id": "EV_003",
   "speaker_id": "person_2",
   "speaker_role": "doctor",
   "transcript_text": "Any muscle or joint problems besides this?",
   "start_timestamp": "02:49",
   "end_timestamp": "02:52",
   "supports": [
    "physical_examination[0]"
   ]
  },
  {
   "evidence_id": "EV_004",
   "speaker_id": "person_2",
   "speaker_role": "doctor",
   "transcript_text": "Okay: pulse 89, temperature 36.8, BP is 152 over 97.",
   "start_timestamp": "03:30",
   "end_timestamp": "03:34",
   "supports": [
    "vital_signs[0]",
    "vital_signs[1]",
    "vital_signs[2]"
   ]
  },
  {
   "evidence_id": "EV_005",
   "speaker_id": "person_2",
   "speaker_role": "doctor",
   "transcript_text": "If you're comfortable, I'll examine you now.",
   "start_timestamp": "03:46",
   "end_timestamp": "03:49",
   "supports": [
    "review_of_systems[0]"
   ]
  }
 ],
 "quality_checks": {
  "negation_detected": false,
  "temporality_detected": false,
  "speaker_attribution_available": true,
  "unsupported_clinical_claims": [],
  "contradictions_detected": [],
  "ambiguous_entities": [],
  "requires_clinician_review": false
 }
}
```

### 00248 - intermediate model JSON (what Qwen produced, parsed; before evidence building)
```json
{
 "encounter_id": "00248",
 "extraction_status": "completed",
 "encounter_metadata": {
  "encounter_date": null,
  "encounter_type": "outpatient_consultation",
  "language": "en",
  "primary_speakers": [
   {
    "speaker_id": "SEG0002",
    "role": "DOCTOR",
    "role_confidence": null
   }
  ]
 },
 "chief_complaint": {
  "value": "Mild, I'd say",
  "normalized_value": "mild",
  "reported_by": "DOCTOR",
  "source_segments": [
   "SEG0002"
  ]
 },
 "symptoms": [
  {
   "name": "acid reflux",
   "normalized_name": "acid reflux",
   "category": "gastrointestinal",
   "status": "present",
   "severity": "moderate",
   "duration": null,
   "frequency": null,
   "onset": null,
   "temporality": "current",
   "body_site": "gastrointestinal",
   "associated_symptoms": [],
   "aggravating_factors": [],
   "relieving_factors": [],
   "reported_by": "DOCTOR",
   "certainty": "uncertain",
   "source_segments": [
    "SEG0019"
   ]
  }
 ],
 "negative_findings": [
  {
   "finding": "no fever",
   "normalized_name": "no fever",
   "status": "absent",
   "assertion": "negative",
   "reported_by": "DOCTOR",
   "temporality": "current",
   "source_segments": [
    "SEG0028"
   ]
  }
 ],
 "medical_history": {
  "past_medical_history": [],
  "surgical_history": [],
  "family_history": [],
  "social_history": []
 },
 "medications": [],
 "allergies": [
  {
   "substance": "pollen",
   "normalized_substance": "pollen",
   "allergy_type": "environmental",
   "reaction": null,
   "severity": "unknown",
   "status": "reported",
   "reported_by": "DOCTOR",
   "source_segments": [
    "SEG0024"
   ]
  }
 ],
 "vital_signs": [
  {
   "name": "pulse",
   "normalized_name": "pulse",
   "value": "71",
   "unit": "beats per minute",
   "reported_by": "DOCTOR",
   "source_segments": [
    "SEG0028"
   ]
  },
  {
   "name": "blood pressure",
   "normalized_name": "blood pressure",
   "value": "127",
   "unit": "mmHg",
   "reported_by": "DOCTOR",
   "source_segments": [
    "SEG0028"
   ]
  },
  {
   "name": "temperature",
   "normalized_name": "temperature",
   "value": "36.6",
   "unit": "°C",
   "reported_by": "DOCTOR",
   "source_segments": [
    "SEG0028"
   ]
  }
 ],
 "physical_examination": [],
 "review_of_systems": [],
 "clinical_conditions": [],
 "clinical_assessment": {
  "assessment": "stress-related symptoms",
  "normalized_assessment": "stress-related symptoms",
  "certainty": "provisional",
  "basis": "blood tests",
  "stated_by": "DOCTOR",
  "source_segments": [
   "SEG0031"
  ]
 },
 "procedures_and_investigations": [],
 "clinical_actions": [],
 "follow_up": {
  "type": "consultation",
  "time_reference": null,
  "normalized_datetime": null
 },
 "clinical_uncertainties": [],
 "quality_checks": {
  "negation_detected": false,
  "temporality_detected": false,
  "speaker_attribution_available": true,
  "unsupported_clinical_claims": [],
  "contradictions_detected": [],
  "ambiguous_entities": [],
  "requires_clinician_review": false
 }
}
```

### 00248 - final built JSON (after the evidence builder; validator-checked)
```json
{
 "encounter_id": "00248",
 "extraction_status": "completed",
 "encounter_metadata": {
  "encounter_date": null,
  "encounter_type": "outpatient_consultation",
  "language": "en",
  "primary_speakers": [
   {
    "speaker_id": "SEG0002",
    "role": "DOCTOR",
    "role_confidence": null
   }
  ]
 },
 "chief_complaint": {
  "value": "Mild, I'd say",
  "normalized_value": "mild",
  "reported_by": "DOCTOR",
  "evidence_ids": [
   "EV_001"
  ]
 },
 "symptoms": [
  {
   "name": "acid reflux",
   "normalized_name": "acid reflux",
   "category": "gastrointestinal",
   "status": "present",
   "severity": "moderate",
   "duration": null,
   "frequency": null,
   "onset": null,
   "temporality": "current",
   "body_site": "gastrointestinal",
   "associated_symptoms": [],
   "aggravating_factors": [],
   "relieving_factors": [],
   "reported_by": "DOCTOR",
   "certainty": "uncertain",
   "evidence_ids": [
    "EV_002"
   ]
  }
 ],
 "negative_findings": [
  {
   "finding": "no fever",
   "normalized_name": "no fever",
   "status": "absent",
   "assertion": "negative",
   "reported_by": "DOCTOR",
   "temporality": "current",
   "evidence_ids": [
    "EV_004"
   ]
  }
 ],
 "medical_history": {
  "past_medical_history": [],
  "surgical_history": [],
  "family_history": [],
  "social_history": []
 },
 "medications": [],
 "allergies": [
  {
   "substance": "pollen",
   "normalized_substance": "pollen",
   "allergy_type": "environmental",
   "reaction": null,
   "severity": "unknown",
   "status": "reported",
   "reported_by": "DOCTOR",
   "evidence_ids": [
    "EV_003"
   ]
  }
 ],
 "vital_signs": [
  {
   "name": "pulse",
   "normalized_name": "pulse",
   "value": "71",
   "unit": "beats per minute",
   "reported_by": "DOCTOR",
   "evidence_ids": [
    "EV_004"
   ]
  },
  {
   "name": "blood pressure",
   "normalized_name": "blood pressure",
   "value": "127",
   "unit": "mmHg",
   "reported_by": "DOCTOR",
   "evidence_ids": [
    "EV_004"
   ]
  },
  {
   "name": "temperature",
   "normalized_name": "temperature",
   "value": "36.6",
   "unit": "°C",
   "reported_by": "DOCTOR",
   "evidence_ids": [
    "EV_004"
   ]
  }
 ],
 "physical_examination": [],
 "review_of_systems": [],
 "clinical_conditions": [],
 "clinical_assessment": {
  "assessment": "stress-related symptoms",
  "normalized_assessment": "stress-related symptoms",
  "certainty": "provisional",
  "basis": "blood tests",
  "stated_by": "DOCTOR",
  "source_segments": [
   "SEG0031"
  ]
 },
 "procedures_and_investigations": [],
 "clinical_actions": [],
 "follow_up": {
  "type": "consultation",
  "time_reference": null,
  "normalized_datetime": null
 },
 "clinical_uncertainties": [],
 "clinical_evidence": [
  {
   "evidence_id": "EV_001",
   "speaker_id": "person_2",
   "speaker_role": "doctor",
   "transcript_text": "Right on time. Sit, please. How can I help?",
   "start_timestamp": "00:08",
   "end_timestamp": "00:13",
   "supports": [
    "chief_complaint"
   ]
  },
  {
   "evidence_id": "EV_002",
   "speaker_id": "person_1",
   "speaker_role": "patient",
   "transcript_text": "I have acid reflux, for nearly five years.",
   "start_timestamp": "02:13",
   "end_timestamp": "02:17",
   "supports": [
    "symptoms[0]"
   ]
  },
  {
   "evidence_id": "EV_003",
   "speaker_id": "person_2",
   "speaker_role": "doctor",
   "transcript_text": "Are there any allergies on your record that I should check?",
   "start_timestamp": "02:56",
   "end_timestamp": "03:00",
   "supports": [
    "allergies[0]"
   ]
  },
  {
   "evidence_id": "EV_004",
   "speaker_id": "person_2",
   "speaker_role": "doctor",
   "transcript_text": "Okay: pulse is 71 beats a minute, blood pressure 127 over 82, temperature is 36.6 degrees.",
   "start_timestamp": "03:43",
   "end_timestamp": "03:52",
   "supports": [
    "negative_findings[0]",
    "vital_signs[0]",
    "vital_signs[1]",
    "vital_signs[2]"
   ]
  }
 ],
 "quality_checks": {
  "negation_detected": false,
  "temporality_detected": false,
  "speaker_attribution_available": true,
  "unsupported_clinical_claims": [],
  "contradictions_detected": [],
  "ambiguous_entities": [],
  "requires_clinician_review": false
 }
}
```
