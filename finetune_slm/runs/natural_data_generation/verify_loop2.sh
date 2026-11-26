#!/bin/bash
cd /d/ambient_clinical_speech_transcription/ambient_clinical_speech_transcription
while true; do
  JUDGE_TIMEOUT_SECONDS=900 python -u -m finetune_scripts.natural_gen.verify_natural --raw dataset_natural/raw --workers 24 >> test_results/natverify.log 2>&1
  if [ -f test_results/STOP_VERIFY ]; then break; fi
  sleep 120
done
