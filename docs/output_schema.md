# Final transcript output schema (conceptual)

```json
{
  "schema_version": "1.0",
  "encounter_id": "02",
  "source_blob": "02transcript.json",
  "source_speech_job_id": "...",
  "processed_at_utc": "...",
  "processing_status": "NEEDS_REVIEW",
  "processing_notice": "LLM text/context reconstruction only; not acoustic speaker verification or clinician approval.",
  "speaker_registry": [
    {
      "canonical_speaker_id": "person_1",
      "role": "PATIENT",
      "role_confidence": 0.95,
      "attribution_status": "PROVISIONAL",
      "original_azure_speaker_ids": ["speaker_1", "speaker_3"],
      "evidence": ["Reports own symptoms and history throughout the encounter"],
      "conflicting_evidence": [],
      "review_required": false
    }
  ],
  "utterances": [
    {
      "utterance_id": "U0001",
      "start_seconds": 0.64,
      "end_seconds": 2.68,
      "duration_seconds": 2.04,
      "canonical_speaker_id": "person_1",
      "role": "PATIENT",
      "text": "I brought the packet/notes with me.",
      "source_segment_indices": [0],
      "original_azure_speaker_ids": ["speaker_1"],
      "attribution_confidence": 0.95,
      "attribution_status": "PROVISIONAL",
      "reconstruction_type": "NORMALIZED",
      "notes": []
    }
  ],
  "review_flags": [],
  "reconstruction_notes": [],
  "foundry_response_id": "...",
  "model_deployment": "..."
}
```

The sample values are illustrative, not a prediction of actual model performance. The output is a transcript-processing artifact and must not be treated as clinician-approved documentation.
