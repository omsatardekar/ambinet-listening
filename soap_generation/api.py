"""SOAP API (FastAPI router). Registered by one line in backend/app/main.py; it does not touch any other route.

POST /api/soap/start              {"run_id": "..."} or {"encounter_id": "02"}   -> 202 {job_id, status_url, events_url, result_url}
GET  /api/soap/health
GET  /api/soap/{job_id}/status
GET  /api/soap/{job_id}/events    server-sent events
GET  /api/soap/{job_id}/result    {note, review, markdown, job}
"""
from __future__ import annotations

import asyncio
import json
from typing import Any, Callable

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse

from clinical_extraction.blob_source import SourceError

from .config import NOTICE, TERMINAL_STATES
from .service import SoapService


def _public(job: dict) -> dict[str, Any]:
    keys = ("job_id", "encounter_ref", "run_id", "encounter_id", "status", "stage_message", "created_at", "started_at", "finished_at", "warnings", "error", "saved_to")
    return {k: job.get(k) for k in keys}


def build_router(service: SoapService) -> APIRouter:
    router = APIRouter(prefix="/api/soap", tags=["soap-note"])

    def job_or_404(job_id: str) -> dict:
        job = service.store.load(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="SOAP job not found.")
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
        body = body if isinstance(body, dict) else {}
        try:
            job = service.submit(encounter_ref=(str(body["encounter_id"]) if body.get("encounter_id") not in (None, "") else None), run_id=body.get("run_id"))
        except SourceError as exc:
            raise HTTPException(status_code=422, detail=exc.message) from exc
        base = f"/api/soap/{job['job_id']}"
        return {"job_id": job["job_id"], "status": job["status"], "status_url": f"{base}/status", "events_url": f"{base}/events", "result_url": f"{base}/result", "notice": NOTICE}

    @router.get("/{job_id}/status")
    def status(job_id: str) -> dict[str, Any]:
        return {**_public(job_or_404(job_id)), "notice": NOTICE}

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
            raise HTTPException(status_code=409, detail=(job.get("error") or {}).get("message") or "The note could not be completed.")
        if job["status"] not in ("completed", "completed_with_warnings"):
            raise HTTPException(status_code=409, detail="The note is not finished.")
        return {"notice": NOTICE, "job": _public(job), "note": service.store.read(job_id, "note.json"),
                "review": {"data_quality_flags": [], "system_checks": (service.store.read(job_id, "review.json") or {}).get("system_checks", [])},   # internal rule messages stay on the server
                "markdown": (service.store.dir(job_id) / "note.md").read_text(encoding="utf-8")}

    return router


def register_soap_routes(app: FastAPI, run_result: Callable[[str], dict | None] | None = None) -> SoapService:
    """The only integration point (one line in backend/app/main.py)."""
    service = SoapService(run_lookup=run_result)
    app.include_router(build_router(service))
    return service
