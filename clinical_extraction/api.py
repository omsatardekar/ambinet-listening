"""Separate extraction API (FastAPI router). Registered by one line in backend/app/main.py; it does not touch the pipeline or wake-word routes.

POST /api/extraction/start                      {"run_id": "..."} or {"encounter_id": "02"}  -> 202 {job_id, status_url, events_url, result_url, evidence_url}
GET  /api/extraction/health
GET  /api/extraction/{job_id}/status
GET  /api/extraction/{job_id}/events            server-sent events (same pattern as /api/pipeline/{id}/events)
GET  /api/extraction/{job_id}/result            raw P02 JSON + execution metadata (kept separate)
GET  /api/extraction/{job_id}/evidence          all model-cited segments; ?path=symptoms[0] for one fact
"""
from __future__ import annotations

import asyncio
import json
from typing import Any, Callable

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse

from .blob_source import SourceError
from .config import DRAFT_NOTICE, TERMINAL_STATES
from .evidence import evidence_for_path
from .service import ExtractionService



def _public(job: dict) -> dict[str, Any]:
    keys = ("job_id", "encounter_ref", "run_id", "encounter_id", "status", "stage_message", "created_at", "started_at", "finished_at", "warnings", "error", "source", "saved_to")
    return {k: job.get(k) for k in keys}


def build_router(service: ExtractionService) -> APIRouter:
    router = APIRouter(prefix="/api/extraction", tags=["clinical-extraction"])

    def job_or_404(job_id: str) -> dict:
        job = service.store.load(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Extraction job not found.")
        return job

    @router.get("/health")
    def health() -> dict[str, Any]:
        return service.health()

    @router.post("/start", status_code=202)
    async def start(request: Request) -> dict[str, Any]:
        try:
            body = await request.json()
        except ValueError:
            body = {}
        if not isinstance(body, dict):
            body = {}
        try:
            job = service.submit(encounter_ref=(str(body["encounter_id"]) if body.get("encounter_id") not in (None, "") else None), run_id=body.get("run_id"))
        except SourceError as exc:
            raise HTTPException(status_code=422, detail=exc.message) from exc
        jid = job["job_id"]
        base = f"/api/extraction/{jid}"
        return {"job_id": jid, "status": job["status"], "status_url": f"{base}/status", "events_url": f"{base}/events", "result_url": f"{base}/result",
                "evidence_url": f"{base}/evidence", "notice": DRAFT_NOTICE}

    @router.get("/{job_id}/status")
    def status(job_id: str) -> dict[str, Any]:
        job = _public(job_or_404(job_id))
        job["notice"] = DRAFT_NOTICE
        return job

    @router.get("/{job_id}/events")
    async def events(job_id: str, request: Request) -> StreamingResponse:
        job_or_404(job_id)
        try:
            sequence = max(0, int(request.headers.get("last-event-id", "0")))
        except ValueError:
            sequence = 0

        async def stream():
            nonlocal sequence
            while not await request.is_disconnected():
                job = service.store.load(job_id)
                if job is None:
                    return
                new = [e for e in job["events"] if e["sequence"] > sequence]
                for event in new:
                    sequence = event["sequence"]
                    yield f"id: {sequence}\ndata: {json.dumps({**event, 'run_status': job['status']}, ensure_ascii=False)}\n\n"
                if job["status"] in TERMINAL_STATES and not new:
                    return
                if not new:
                    yield ": keepalive\n\n"
                await asyncio.sleep(2)

        return StreamingResponse(stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"})

    @router.get("/{job_id}/result")
    def result(job_id: str) -> dict[str, Any]:
        job = job_or_404(job_id)
        if job["status"] == "failed":
            raise HTTPException(status_code=409, detail=(job.get("error") or {}).get("message") or "The extraction failed.")
        if job["status"] not in ("completed", "completed_with_warnings"):
            raise HTTPException(status_code=409, detail="The extraction is not finished.")
        return {"notice": DRAFT_NOTICE, "job": _public(job), "extraction": service.store.read(job_id, "extraction_raw.json"), "metadata": service.store.read(job_id, "metadata.json")}

    @router.get("/{job_id}/evidence")
    def evidence(job_id: str, path: str | None = None) -> dict[str, Any]:
        job = job_or_404(job_id)
        if job["status"] not in ("completed", "completed_with_warnings"):
            raise HTTPException(status_code=409, detail="The extraction is not finished.")
        derived = service.store.read(job_id, "evidence.json")
        if path is None:
            return derived
        one = evidence_for_path(derived, path)
        if one is None:
            raise HTTPException(status_code=404, detail="No extracted fact has that path.")
        return one

    return router


def register_extraction_routes(app: FastAPI, run_result: Callable[[str], dict | None] | None = None) -> ExtractionService:
    """The only integration point. `run_result` is the existing ProgressManager.result (read-only lookup of a completed run's final transcript)."""
    service = ExtractionService(run_lookup=run_result)
    app.include_router(build_router(service))
    return service
