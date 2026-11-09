from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import tempfile
from contextlib import asynccontextmanager, suppress
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path, PurePosixPath
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, StreamingResponse

from .pipeline import run_pipeline
from .progress import ProgressManager
from .wakeword import WakeWordService


PROJECT_ROOT = Path(__file__).resolve().parents[2]
UPLOAD_DIR = PROJECT_ROOT / "backend" / "uploads"
MAX_UPLOAD_BYTES = 1024 * 1024 * 1024
FAST_TRANSCRIPTION_MAX_BYTES = 250 * 1024 * 1024 - 1
UPLOAD_CHUNK_BYTES = 1024 * 1024
REQUIRED_AZURE_SETTINGS = (
    "AZURE_STORAGE_ACCOUNT_NAME",
    "AZURE_STORAGE_ACCOUNT_KEY",
    "AZURE_AUDIO_CONTAINER",
    "AZURE_TRANSCRIPT_CONTAINER",
    "AZURE_STORAGE_OUTPUT_CONTAINER",
    "AZURE_STORAGE_SLM_CONTAINER",
    "FOUNDRY_PROJECT_ENDPOINT",
    "FOUNDRY_API_KEY",
    "FOUNDRY_MODEL_DEPLOYMENT_NAME",
)
SPEECH_PROVIDERS = {
    "azure_speech": {
        "label": "Azure Speech",
        "settings": ("AZURE_SPEECH_ENDPOINT", "AZURE_SPEECH_KEY"),
    },
    "foundry_fast": {
        "label": "Foundry Fast Transcription",
        "settings": (
            "AZURE_FOUNDRY_SPEECH_ENDPOINT",
            "AZURE_FOUNDRY_SPEECH_KEY",
        ),
    },
}
LOCAL_RECORDINGS_DIR = PROJECT_ROOT / "offline_recordings"
WAKEWORD_ALLOWED_ORIGINS = {
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://127.0.0.1:8000",
    "http://localhost:8000",
}

load_dotenv(PROJECT_ROOT / ".env")
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("ambient_demo.api")

app = FastAPI(
    title="Ambient Clinical Listening API",
    description="Web adapter for the existing ambient clinical listening pipeline.",
    version="1.0.0",
)
progress_manager = ProgressManager()
pipeline_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="clinical-pipeline")
voice_service = WakeWordService(LOCAL_RECORDINGS_DIR)
wake_clients: set[WebSocket] = set()


async def _broadcast_wake_state(message: dict[str, Any]) -> None:
    disconnected = []
    for client in tuple(wake_clients):
        try:
            await client.send_json(message)
        except Exception:
            logger.exception("Could not send wake-word state to a connected browser")
            disconnected.append(client)
    for client in disconnected:
        wake_clients.discard(client)


@asynccontextmanager
async def lifespan(_: FastAPI):
    loop = asyncio.get_running_loop()

    def schedule_state(message: dict[str, Any]) -> None:
        loop.call_soon_threadsafe(
            lambda: asyncio.create_task(_broadcast_wake_state(message))
        )

    voice_service.add_listener(schedule_state)
    voice_service.start()

    async def publish_meter() -> None:
        while True:
            await asyncio.sleep(0.05)
            state = voice_service.snapshot()
            await _broadcast_wake_state(
                {
                    "type": "meter",
                    "level": state["level"],
                    "elapsed": state["elapsed"],
                    "audio_connected": state["audio_connected"],
                }
            )

    meter_task = asyncio.create_task(publish_meter())
    try:
        yield
    finally:
        meter_task.cancel()
        with suppress(asyncio.CancelledError):
            await meter_task
        voice_service.remove_listener(schedule_state)
        voice_service.shutdown()
        wake_clients.clear()


app.router.lifespan_context = lifespan


@app.get("/api/health")
def health() -> dict[str, Any]:
    missing = [name for name in REQUIRED_AZURE_SETTINGS if not os.getenv(name, "").strip()]
    speech_providers = {
        provider: {
            "label": details["label"],
            "configured": all(os.getenv(name, "").strip() for name in details["settings"]),
        }
        for provider, details in SPEECH_PROVIDERS.items()
    }
    container_settings = (
        "AZURE_AUDIO_CONTAINER",
        "AZURE_TRANSCRIPT_CONTAINER",
        "AZURE_STORAGE_OUTPUT_CONTAINER",
        "AZURE_STORAGE_SLM_CONTAINER",
    )
    container_values: dict[str, list[str]] = {}
    for name in container_settings:
        value = os.getenv(name, "").strip().casefold()
        if value:
            container_values.setdefault(value, []).append(name)
    duplicates = [
        names for names in container_values.values() if len(names) > 1
    ]
    common_configuration_valid = not missing and not duplicates
    available_speech_provider = any(
        provider["configured"] for provider in speech_providers.values()
    )
    return {
        "status": "ok",
        "azure_configured": common_configuration_valid and available_speech_provider,
        "speech_providers": speech_providers,
        "missing_settings": missing,
        "container_mapping_valid": not duplicates and not missing,
        "configuration_issues": [
            f"{' and '.join(names)} must refer to different Blob containers."
            for names in duplicates
        ],
        "wake_word": voice_service.health(),
    }


@app.get("/api/wake/state")
def wake_state() -> dict[str, Any]:
    return voice_service.snapshot()


@app.post("/api/wake/recording/start")
def wake_start_recording() -> dict[str, Any]:
    try:
        started = voice_service.start_recording("button")
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if not started:
        raise HTTPException(status_code=409, detail="A recording is already in progress.")
    return voice_service.snapshot()


@app.post("/api/wake/recording/stop")
def wake_stop_recording() -> dict[str, Any]:
    if voice_service.stop_recording("button") is None:
        raise HTTPException(status_code=409, detail="No recording is in progress.")
    return voice_service.snapshot()


@app.get("/api/wake/recordings/{session_id}/audio")
def local_recording_audio(session_id: str) -> FileResponse:
    path = voice_service.audio_path(session_id)
    if path is None:
        raise HTTPException(status_code=404, detail="Local recording not found.")
    return FileResponse(path, media_type="audio/wav")


@app.websocket("/api/wake/ws")
async def wake_state_stream(websocket: WebSocket) -> None:
    if not _is_allowed_wake_origin(websocket.headers.get("origin")):
        await websocket.close(code=1008)
        return
    await websocket.accept()
    wake_clients.add(websocket)
    buffered_audio = bytearray()
    try:
        await websocket.send_json(voice_service.snapshot())
        while True:
            message = await websocket.receive()
            if message["type"] == "websocket.disconnect":
                break
            audio = message.get("bytes")
            if audio is None:
                continue
            if len(audio) > 65536:
                await websocket.close(code=1009, reason="Audio chunk is too large.")
                break
            buffered_audio.extend(audio)
            frame_bytes = 512 * 2
            while len(buffered_audio) >= frame_bytes:
                voice_service.accept_audio(bytes(buffered_audio[:frame_bytes]))
                del buffered_audio[:frame_bytes]
    except WebSocketDisconnect:
        pass
    except ValueError:
        logger.exception("Browser sent an invalid microphone frame")
        await websocket.close(code=1003, reason="Invalid microphone audio.")
    finally:
        wake_clients.discard(websocket)


def _is_allowed_wake_origin(origin: str | None) -> bool:
    return origin is None or origin in WAKEWORD_ALLOWED_ORIGINS


@app.post("/api/pipeline/start", status_code=202)
async def start_pipeline(
    file: UploadFile = File(...),
    speech_provider: str = Form(default="azure_speech"),
) -> dict[str, Any]:
    filename = _safe_filename(file.filename)
    if Path(filename).suffix.lower() != ".wav":
        raise HTTPException(status_code=415, detail="Only WAV recordings are supported.")
    if speech_provider not in SPEECH_PROVIDERS:
        raise HTTPException(status_code=422, detail="Select a supported transcription service.")
    configuration = health()
    if not configuration["azure_configured"]:
        raise HTTPException(
            status_code=503,
            detail="Processing is temporarily unavailable. Please ask your administrator to check the workspace setup.",
        )
    if not configuration["speech_providers"][speech_provider]["configured"]:
        raise HTTPException(
            status_code=503,
            detail=f"{SPEECH_PROVIDERS[speech_provider]['label']} is not configured for this workspace.",
        )

    upload_path: Path | None = None
    try:
        max_bytes = (
            FAST_TRANSCRIPTION_MAX_BYTES
            if speech_provider == "foundry_fast"
            else MAX_UPLOAD_BYTES
        )
        upload_path, fingerprint = await _save_upload(file, max_bytes=max_bytes)
        run_fingerprint = hashlib.sha256(
            f"{speech_provider}\0{fingerprint}".encode("utf-8")
        ).hexdigest()
        run_id, duplicate = progress_manager.create(filename, run_fingerprint)
        if duplicate:
            _remove_upload(upload_path)
        else:
            future = pipeline_executor.submit(
                run_pipeline,
                run_id,
                filename,
                fingerprint,
                upload_path,
                progress_manager,
                speech_provider,
            )
            future.add_done_callback(_log_unexpected_worker_error)
        status = progress_manager.status(run_id)
        if status is None:
            raise RuntimeError("Pipeline run state was not created.")
        return {
            "run_id": run_id,
            "filename": filename,
            "speech_provider": speech_provider,
            "duplicate": duplicate,
            "status": status["status"],
            "events_url": f"/api/pipeline/{run_id}/events",
            "status_url": f"/api/pipeline/{run_id}/status",
            "result_url": f"/api/pipeline/{run_id}/result",
        }
    except HTTPException:
        if upload_path is not None:
            _remove_upload(upload_path)
        raise
    except OSError as exc:
        if upload_path is not None:
            _remove_upload(upload_path)
        logger.error("Could not receive audio upload (%s)", type(exc).__name__)
        raise HTTPException(status_code=500, detail="The recording could not be received.") from exc
    finally:
        await file.close()


@app.get("/api/pipeline/{run_id}/events")
async def pipeline_events(run_id: str, request: Request) -> StreamingResponse:
    if progress_manager.status(run_id) is None:
        raise HTTPException(status_code=404, detail="Pipeline run not found.")

    last_event_id = request.headers.get("last-event-id", "0")
    try:
        sequence = max(0, int(last_event_id))
    except ValueError:
        sequence = 0

    async def stream():
        nonlocal sequence
        while not await request.is_disconnected():
            try:
                events, terminal = progress_manager.events_after(run_id, sequence)
            except KeyError:
                return
            for event in events:
                sequence = event["sequence"]
                yield f"id: {sequence}\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"
            if terminal and not events:
                return
            if not events:
                yield ": keepalive\n\n"
            await asyncio.sleep(10)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/pipeline/{run_id}/status")
def pipeline_status(run_id: str) -> dict[str, Any]:
    status = progress_manager.status(run_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Pipeline run not found.")
    return status


@app.get("/api/pipeline/{run_id}/result")
def pipeline_result(run_id: str) -> dict[str, Any]:
    status = progress_manager.status(run_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Pipeline run not found.")
    if status["status"] == "failed":
        raise HTTPException(status_code=409, detail=status["error"])
    result = progress_manager.result(run_id)
    if result is None:
        raise HTTPException(status_code=409, detail="The final transcript is not ready.")
    return result


async def _save_upload(
    file: UploadFile,
    max_bytes: int = MAX_UPLOAD_BYTES,
) -> tuple[Path, str]:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(
        prefix="incoming_",
        suffix=".wav",
        dir=UPLOAD_DIR,
    )
    path = Path(temp_name)
    digest = hashlib.sha256()
    size = 0
    header = bytearray()

    try:
        with os.fdopen(descriptor, "wb") as target:
            while chunk := await file.read(UPLOAD_CHUNK_BYTES):
                size += len(chunk)
                if size > max_bytes:
                    if max_bytes == FAST_TRANSCRIPTION_MAX_BYTES:
                        detail = (
                            "Foundry Fast Transcription supports audio files smaller "
                            "than 250 MB."
                        )
                    else:
                        detail = "The WAV recording exceeds the 1 GB upload limit."
                    raise HTTPException(
                        status_code=413,
                        detail=detail,
                    )
                if len(header) < 12:
                    header.extend(chunk[: 12 - len(header)])
                digest.update(chunk)
                target.write(chunk)
        if size == 0:
            raise HTTPException(status_code=400, detail="The selected recording is empty.")
        if (
            len(header) < 12
            or bytes(header[:4]) not in {b"RIFF", b"RF64", b"BW64"}
            or bytes(header[8:12]) != b"WAVE"
        ):
            raise HTTPException(
                status_code=415,
                detail="The selected file is not a valid WAV recording.",
            )
        return path, digest.hexdigest()
    except Exception:
        _remove_upload(path)
        raise


def _safe_filename(value: str | None) -> str:
    filename = PurePosixPath((value or "recording.wav").replace("\\", "/")).name
    filename = filename.strip().replace("\x00", "")
    return filename[:160] or "recording.wav"


def _remove_upload(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError as exc:
        logger.error("Could not remove temporary WAV upload (%s)", type(exc).__name__)


def _log_unexpected_worker_error(future: Future[Any]) -> None:
    if future.cancelled():
        return
    error = future.exception()
    if error is not None:
        logger.error("Pipeline worker exited unexpectedly (%s)", type(error).__name__)
