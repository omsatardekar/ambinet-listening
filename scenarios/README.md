# Module 3 recording scenarios (20)

Hand-written, natural consultations (about 11 minutes of speech each) for `scripts/ambient_tts.py`. They are not the templated Module-2 scripts.

* **Sources of the situations (reference only, the wording is new):** 10 from `dataset_v2_batch_001_corrected/batch_002` (blueprints 20029-20351: uncertain doses, stopped medicines, disputed allergies, forgotten drug names, conflicting durations, an unidentified speaker) and 10 from the `batch_002_generation` plan (sparse designs: allergies, vitals, history or follow-up deliberately never mentioned). None of them is an evaluated or spare id of EXP_008.
* **Variety:** who starts (patient, doctor, carer, family member, doctor checking the name, patient apologising for being late), accents (GB, US, IN, AU, CA), hesitant/terse/chatty/anxious/stoic patients, 2 to 5 speakers, roles DOCTOR, PATIENT, NURSE, CAREGIVER, FAMILY_MEMBER, CLINICAL_STAFF, UNKNOWN.
* **Each `scenario.json` has a `design` block** that says what was put in on purpose: what is partial, uncertain or absent, and the facts that are present. That is the key for judging an extraction (there is no label file for these).

```
scenarios/_authoring/NN_name.txt     the hand-written source (JSON header, three dashes, dialogue)  <- edit these
scenarios/encounter_m3_NN_name/      generated: scenario.json + dialogue.txt                        <- do not edit
python scripts/build_module3_scenarios.py        recompile (checks speakers, bracketed stage directions, "must_not_mention" words, length >= 10.8 min estimated)
```

The compiler adds spoken-language texture on top of the written text, deterministically per scenario: about 9 short overlapping listener responses ("Mm-hm.", "Right."), about 9 "um/uh" starts in non-doctor answers, 3 in the doctor's, and a few quiet/muffled turns written by hand. `--no-enrich` turns the first part off.

## Generate audio
```powershell
python scripts/ambient_tts.py generate --dry-run            # characters and minutes, no Azure call
python scripts/ambient_tts.py generate                      # the next 10 scenarios without audio -> output/<scenario>/audio.wav
python scripts/ambient_tts.py generate                      # run again: the following 10 (dataset_manifest.json is merged)
python scripts/ambient_tts.py generate --scenario-voices    # ignore VOICE_* in .env: use the voices and accents in each scenario.json
python scripts/ambient_tts.py generate --only m3_07         # redo one;  --all = everything;  --next 5 = other batch size
python scripts/ambient_tts.py validate --out output --expected 20
```
About 85,000 characters are sent to the speech service per batch of 10 (cached per sentence and voice in `.tts_cache`).

**Voices:** the `VOICE_<ROLE>` lines in `.env` override the scenario voices for every encounter (one doctor voice, one patient voice, ...). Use `--scenario-voices` or remove those lines for variety and accents; patients also support `VOICE_PATIENT_M` / `VOICE_PATIENT_F`. Two people in one encounter never share a voice.

**Known limits:** a young child (scenario 08) is voiced by an adult voice; timing of the real audio is only estimated from the measured 2.53 words per second of the earlier Module-2 recordings, so check the actual durations after the first run (`dataset_manifest.json`).
