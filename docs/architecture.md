# Architecture

```text
AZURE_AUDIO_CONTAINER
  └── NNaudio.wav
        │
        ├── Azure Speech (asynchronous batch) ─────┐
        └── Foundry Fast Transcription (synchronous)┤
                                                    ▼
                                      AZURE_TRANSCRIPT_CONTAINER
                                        └── NNtranscript.json
                                              │
                                              ▼
                                      Foundry conversation reconstruction
                                              │
                                              └── AZURE_STORAGE_OUTPUT_CONTAINER
                                                    └── NNreconstruction.json (raw model response)
                                                          │
                                                          ▼
                                                  Local structural validation
                                                    - JSON and allowed role/status checks
                                                    - source-segment coverage
                                                    - timestamp reconstruction from source bounds
                                                    - omitted-segment preservation
                                                          │
                                                          └── AZURE_STORAGE_OUTPUT_CONTAINER
                                                                └── NNfinal_transcript.json
                                                                      │
                                                                      ▼
                                                              SLM input preparation
                                                                └── AZURE_STORAGE_SLM_CONTAINER
                                                                      ├── NNslm_input.json
                                                                      └── NNslm_input.manifest.json
```

The four containers are configured with `AZURE_AUDIO_CONTAINER`, `AZURE_TRANSCRIPT_CONTAINER`, `AZURE_STORAGE_OUTPUT_CONTAINER`, and `AZURE_STORAGE_SLM_CONTAINER`. They must be distinct and already exist in the storage account.

The web app lets the operator select one transcription provider per recording. Azure Speech uses the existing asynchronous batch workflow; Foundry Fast Transcription sends the uploaded WAV directly to the synchronous transcription API with diarization enabled. Both branches normalize into the same Speech transcript format and use the same reconstruction agent, validation, and compact SLM conversion. The validated LLM output follows `docs/output_schema.md` and is saved as `NNfinal_transcript.json` in `AZURE_STORAGE_OUTPUT_CONTAINER`; `NNslm_input.json` and its review manifest are saved in `AZURE_STORAGE_SLM_CONTAINER`. Provider choice is recorded on the audio Blob so the same recording can be evaluated through both providers without reusing the other provider's result. The Fast Transcription API has a strict under-250 MB audio limit; the Azure Speech path retains the web app's 1 GB upload limit.

The SLM preparation script reads the validated `NNfinal_transcript.json` from `AZURE_STORAGE_OUTPUT_CONTAINER` and writes the compact SLM input plus its review manifest into `AZURE_STORAGE_SLM_CONTAINER`. It does not modify the validated final transcript.

## Deliberate design boundaries

- One encounter per model request. Never combine separate patients/recordings in a single prompt.
- One Foundry agent definition reused across all encounters.
- Azure speaker IDs are evidence metadata only, not canonical identities.
- Canonical IDs are local to one encounter; there is no cross-recording identity matching.
- The agent sees text, not audio. It cannot acoustically validate identity or overlap.
- Speech diarization clusters voices; it does not identify a participant's profession. Doctor/nurse/other-staff roles are inferred from the conversation text and remain provisional when the evidence is insufficient.
- The raw Speech transcript remains unchanged. The final JSON links back to its source by blob name and source segment indices.
- The two Speech providers are alternatives, not sequential stages. Only one provider is called for a given run.
- Raw model output and validated transcript are stored separately.
- The pipeline is restartable: completed outputs are reused; incomplete prior runs are not automatically resubmitted.
