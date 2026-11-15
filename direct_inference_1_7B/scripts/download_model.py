import os,sys,json,time
os.environ["HF_HUB_DISABLE_TELEMETRY"]="1"
from huggingface_hub import snapshot_download
t=time.time()
p=snapshot_download("Qwen/Qwen3-1.7B",revision="70d244cc86ccca08cf5af4e1e306ecf908b1ad5e",cache_dir=r"D:\ambient_clinical_speech_transcription\ambient_clinical_speech_transcription\direct_inference_1_7B\models\hf_cache",allow_patterns=["*.json","*.safetensors","merges.txt","vocab.json","LICENSE"],force_download=False)
print("SNAPSHOT",p,round(time.time()-t),"s")

