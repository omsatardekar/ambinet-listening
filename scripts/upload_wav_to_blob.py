
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient, ContentSettings
from azure.core.exceptions import AzureError

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
ACCOUNT_KEY = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
CONTAINER_NAME = os.getenv("AZURE_AUDIO_CONTAINER")

# Folder containing all generated encounter folders
AUDIO_ROOT = Path("output/clinical_audio_dataset")

# --------------------------------------------------
# VALIDATE CONFIGURATION
# --------------------------------------------------

if not ACCOUNT_NAME or not ACCOUNT_KEY or not CONTAINER_NAME:
    raise ValueError(
        "Missing Azure configuration. Check your .env file."
    )

if not AUDIO_ROOT.exists():
    raise FileNotFoundError(
        f"Audio directory not found: {AUDIO_ROOT.resolve()}"
    )

# --------------------------------------------------
# CONNECT TO AZURE BLOB STORAGE USING ACCESS KEY
# --------------------------------------------------

connection_string = (
    f"DefaultEndpointsProtocol=https;"
    f"AccountName={ACCOUNT_NAME};"
    f"AccountKey={ACCOUNT_KEY};"
    f"EndpointSuffix=core.windows.net"
)

blob_service_client = BlobServiceClient.from_connection_string(
    connection_string
)

container_client = blob_service_client.get_container_client(
    CONTAINER_NAME
)

# --------------------------------------------------
# FIND WAV FILES
# --------------------------------------------------

wav_files = list(AUDIO_ROOT.rglob("*.wav"))

if not wav_files:
    raise FileNotFoundError(
        f"No WAV recordings found inside {AUDIO_ROOT.resolve()}"
    )

# Sort by encounter number, e.g. encounter_001, encounter_002
def encounter_number(path):
    match = re.search(r"encounter_(\d+)", str(path))
    return int(match.group(1)) if match else 999999

wav_files.sort(key=encounter_number)

print(f"\nFound {len(wav_files)} WAV recordings.")
print(f"Target container: {CONTAINER_NAME}\n")

# --------------------------------------------------
# UPLOAD RECORDINGS DIRECTLY TO CONTAINER ROOT
# --------------------------------------------------

successful_uploads = []
failed_uploads = []

for index, wav_path in enumerate(wav_files, start=1):

    # Names: 01audio.wav, 02audio.wav ... 50audio.wav
    blob_name = f"{index:02d}audio.wav"

    try:
        blob_client = container_client.get_blob_client(blob_name)

        print(f"[{index}/{len(wav_files)}] Uploading {wav_path.name}")

        with open(wav_path, "rb") as audio_file:
            blob_client.upload_blob(
                audio_file,
                overwrite=True,
                content_settings=ContentSettings(
                    content_type="audio/wav"
                )
            )

        successful_uploads.append(blob_name)
        print(f"SUCCESS: {blob_name}\n")

    except (AzureError, OSError) as error:
        failed_uploads.append((blob_name, str(error)))
        print(f"FAILED: {blob_name}")
        print(f"Reason: {error}\n")

# --------------------------------------------------
# FINAL REPORT
# --------------------------------------------------

print("\n" + "=" * 55)
print("AZURE BLOB UPLOAD REPORT")
print("=" * 55)

print(f"Total WAV files found : {len(wav_files)}")
print(f"Successfully uploaded: {len(successful_uploads)}")
print(f"Failed uploads       : {len(failed_uploads)}")

if failed_uploads:
    print("\nFailed recordings:")
    for name, reason in failed_uploads:
        print(f"- {name}: {reason}")

print("\nUpload process completed.")
