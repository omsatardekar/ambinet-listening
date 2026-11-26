#!/bin/bash
cd /d/ambient_clinical_speech_transcription/ambient_clinical_speech_transcription
while true; do
  JUDGE_TIMEOUT_SECONDS=900 python -u -m finetune_scripts.natural_gen.verify_natural --raw dataset_natural/raw --workers 6 >> test_results/natverify.log 2>&1
  n=$(ls dataset_natural/raw | wc -l)
  if [ "$n" -ge 328 ]; then
    JUDGE_TIMEOUT_SECONDS=900 python -u -m finetune_scripts.natural_gen.verify_natural --raw dataset_natural/raw --workers 6 >> test_results/natverify.log 2>&1
    echo ALLDONE >> test_results/natverify.log; break
  fi
  sleep 240
done
