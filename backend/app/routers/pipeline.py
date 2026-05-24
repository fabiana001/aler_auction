"""Pipeline controller router – REST + SSE endpoints."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from sse_starlette.sse import EventSourceResponse

from app.pipeline.manager import PipelineManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


def _get_manager(request: Request) -> PipelineManager:
    return request.app.state.pipeline_manager


# ------------------------------------------------------------------
# REST endpoints
# ------------------------------------------------------------------


@router.get("/status")
def get_status(request: Request) -> dict[str, Any]:
    """Return the status of every pipeline step."""
    return _get_manager(request).get_status()


@router.post("/run")
async def run_pipeline(request: Request, from_step: str | None = None) -> dict[str, Any]:
    """Start the full pipeline (or from a given step) as a background task."""
    manager: PipelineManager = _get_manager(request)

    status = manager.get_status()
    if status["running"]:
        raise HTTPException(status_code=409, detail="Pipeline is already running")

    asyncio.create_task(manager.run_all(from_step=from_step))
    return {"accepted": True, "from_step": from_step}


@router.post("/run/{step_id}")
async def run_single_step(request: Request, step_id: str) -> dict[str, Any]:
    """Start a single pipeline step as a background task."""
    manager: PipelineManager = _get_manager(request)

    if step_id not in manager._steps:
        raise HTTPException(status_code=404, detail=f"Unknown step: {step_id}")

    step = manager._steps[step_id]
    if step.status == "running":
        raise HTTPException(status_code=409, detail=f"Step '{step_id}' is already running")

    asyncio.create_task(manager.run_step(step_id))
    return {"accepted": True}


@router.post("/stop/{step_id}")
async def stop_step(request: Request, step_id: str) -> dict[str, Any]:
    """Stop a running pipeline step."""
    manager: PipelineManager = _get_manager(request)

    if step_id not in manager._steps:
        raise HTTPException(status_code=404, detail=f"Unknown step: {step_id}")

    await manager.stop_step(step_id)
    return {"stopped": True}


# ------------------------------------------------------------------
# SSE endpoint
# ------------------------------------------------------------------


@router.get("/logs/{step_id}")
async def stream_logs(request: Request, step_id: str) -> EventSourceResponse:
    """Stream log lines for *step_id* via Server-Sent Events."""
    manager: PipelineManager = _get_manager(request)

    if step_id not in manager._steps:
        raise HTTPException(status_code=404, detail=f"Unknown step: {step_id}")

    step = manager._steps[step_id]

    async def event_generator():
        # Send existing buffered logs first
        snapshot = list(step.logs)
        for line in snapshot:
            yield {"event": "log", "data": json.dumps({"line": line})}

        # If the step is not running, close after sending buffer
        if step.status != "running":
            yield {"event": "status", "data": json.dumps({"status": step.status})}
            return

        # Tail new lines while the step is running
        last_idx = len(snapshot)
        try:
            while step.status == "running":
                await asyncio.sleep(0.5)
                current = list(step.logs)
                new_lines = current[last_idx:]
                for line in new_lines:
                    yield {"event": "log", "data": json.dumps({"line": line})}
                last_idx = len(current)
        except asyncio.CancelledError:
            pass
        finally:
            yield {"event": "status", "data": json.dumps({"status": step.status})}

    return EventSourceResponse(event_generator())
