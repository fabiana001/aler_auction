"""Pipeline manager – singleton that tracks and controls pipeline step execution."""

from __future__ import annotations

import asyncio
import logging
import re
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path("/Users/fabianalanotte/git/aler_auction")
MAX_LOG_LINES = 500

PIPELINE_STEPS: dict[str, dict[str, str]] = {
    "wayback_discovery": {
        "name": "Wayback Discovery",
        "script": "run_wayback_discovery.py",
        "icon": "globe",
        "emoji": "🌐",
    },
    "url_extraction": {
        "name": "URL Extraction",
        "script": "run_url_extraction.py",
        "icon": "link",
        "emoji": "🔗",
    },
    "detail_fetching": {
        "name": "Detail Fetching",
        "script": "run_detail_fetching.py",
        "icon": "download",
        "emoji": "📥",
    },
    "data_extraction": {
        "name": "Data Extraction",
        "script": "run_data_extraction.py",
        "icon": "file-text",
        "emoji": "📄",
    },
    "pdf_extraction": {
        "name": "PDF Extraction",
        "script": "run_pdf_extraction.py",
        "icon": "file",
        "emoji": "📑",
    },
    "historical_extraction": {
        "name": "Historical Extraction",
        "script": "run_historical_extraction.py",
        "icon": "clock",
        "emoji": "⏳",
    },
    "dataset_integration": {
        "name": "Dataset Integration",
        "script": "run_dataset_integration.py",
        "icon": "database",
        "emoji": "🗄️",
    },
    "geocoding": {
        "name": "Geocoding",
        "script": "run_geocoding.py",
        "icon": "map-pin",
        "emoji": "📍",
    },
    "price_analysis": {
        "name": "Price Analysis",
        "script": "run_price_analysis.py",
        "icon": "bar-chart",
        "emoji": "📊",
    },
}

_STEP_ORDER = list(PIPELINE_STEPS.keys())


class _StepState:
    """Mutable state for a single pipeline step."""

    def __init__(self, step_id: str, meta: dict[str, str]):
        self.step_id = step_id
        self.name: str = meta["name"]
        self.script: str = meta["script"]
        self.icon: str = meta["icon"]
        self.emoji: str = meta["emoji"]
        self.status: str = "idle"
        self.pid: int | None = None
        self.started_at: str | None = None
        self.finished_at: str | None = None
        self.logs: deque[str] = deque(maxlen=MAX_LOG_LINES)
        self.summary: dict[str, Any] = {}
        self._process: asyncio.subprocess.Process | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "name": self.name,
            "script": self.script,
            "icon": self.icon,
            "emoji": self.emoji,
            "status": self.status,
            "pid": self.pid,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "logs": list(self.logs),
            "summary": self.summary,
        }


class PipelineManager:
    """Singleton that manages pipeline step execution."""

    def __init__(self) -> None:
        self._steps: dict[str, _StepState] = {
            sid: _StepState(sid, meta) for sid, meta in PIPELINE_STEPS.items()
        }
        self._running_task: asyncio.Task | None = None
        self._last_error: str | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_status(self) -> dict[str, Any]:
        return {
            "steps": [s.to_dict() for s in self._steps.values()],
            "running": self._running_task is not None and not self._running_task.done(),
            "last_error": self._last_error,
        }

    async def run_step(self, step_id: str) -> None:
        """Run a single pipeline step."""
        step = self._steps[step_id]
        await self._execute_step(step)

    async def run_all(self, from_step: str | None = None) -> None:
        """Run all pipeline steps sequentially, optionally starting from *from_step*."""
        start_idx = 0
        if from_step is not None:
            if from_step not in self._steps:
                raise ValueError(f"Unknown step: {from_step}")
            start_idx = _STEP_ORDER.index(from_step)

        self._last_error = None

        for sid in _STEP_ORDER[start_idx:]:
            step = self._steps[sid]
            await self._execute_step(step)
            if step.status == "error":
                self._last_error = f"Step '{step.name}' failed"
                break

    async def stop_step(self, step_id: str) -> None:
        """Kill a running step."""
        step = self._steps[step_id]
        if step._process is not None and step._process.returncode is None:
            step._process.kill()
            await step._process.wait()
        step.status = "idle"
        step._process = None
        step.finished_at = datetime.now(timezone.utc).isoformat()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _execute_step(self, step: _StepState) -> None:
        """Launch the script for *step* and capture output."""
        step.status = "running"
        step.started_at = datetime.now(timezone.utc).isoformat()
        step.finished_at = None
        step.logs.clear()
        step.summary = {}
        step.pid = None

        cmd = f"uv run python scripts/{step.script}"
        logger.info("Starting step %s: %s", step.step_id, cmd)

        try:
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=str(PROJECT_ROOT),
            )
            step._process = proc
            step.pid = proc.pid

            assert proc.stdout is not None
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                decoded = line.decode(errors="replace").rstrip()
                step.logs.append(decoded)

            await proc.wait()

            if proc.returncode == 0:
                step.status = "done"
            else:
                step.status = "error"
                step.logs.append(f"[exit code {proc.returncode}]")

            step.summary = self._parse_summary(step.step_id, list(step.logs))

        except Exception as exc:
            logger.exception("Error running step %s", step.step_id)
            step.status = "error"
            step.logs.append(f"[exception: {exc}]")
        finally:
            step.finished_at = datetime.now(timezone.utc).isoformat()
            step._process = None

    @staticmethod
    def _parse_summary(step_id: str, log_lines: list[str]) -> dict[str, Any]:
        """Extract useful metrics from the last lines of output."""
        summary: dict[str, Any] = {}
        # Scan last 100 lines for known patterns
        tail = log_lines[-100:] if len(log_lines) > 100 else log_lines

        patterns = [
            (r"Found\s+(\d+)\s+snapshots", "snapshots_found"),
            (r"Extracted\s+(\d+)\s+records", "records_extracted"),
            (r"Total records:\s*(\d+)", "total_records"),
            (r"(\d+)\s+aste", "auction_count"),
            (r"Successfully\s+saved\s+(\d+)", "saved_count"),
            (r"Data\s+saved\s+to", "data_saved"),
            (r"(\d+)\s+pages?", "pages_count"),
            (r"Processed\s+(\d+)\s+items", "items_processed"),
            (r"(\d+)\s+locations?\s+geocoded", "geocoded_count"),
            (r"Generated\s+(\d+)\s+price", "price_records"),
        ]

        for line in reversed(tail):
            for regex, key in patterns:
                m = re.search(regex, line, re.IGNORECASE)
                if m:
                    val = m.group(1)
                    # Try int conversion
                    try:
                        summary[key] = int(val)
                    except ValueError:
                        summary[key] = val
                    break  # one match per line

        return summary
