"""In-memory pipeline status tracking.

Thread-safe status store for tracking pipeline progress. Works perfectly for
a single-server deployment where the background task and API run in the same process.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Literal


StepName = Literal[
    "queued",
    "lighthouse",
    "builtwith",
    "screenshots",
    "scoring",
    "ai_interpretation",
    "analyst_seeding",
    "complete",
    "error",
]


@dataclass
class PipelineRun:
    project_id: str
    current_step: StepName = "queued"
    progress: int = 0
    error_message: str | None = None
    started_at: float = field(default_factory=time.time)
    completed_at: float | None = None
    step_times: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        if self.current_step == "complete":
            status = "complete"
        elif self.current_step == "error":
            status = "error"
        else:
            status = "running"

        return {
            "project_id": self.project_id,
            "status": status,
            "current_step": self.current_step,
            "progress": self.progress,
            "error_message": self.error_message,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "step_times": self.step_times,
        }


# Thread-safe store
_lock = threading.Lock()
_runs: dict[str, PipelineRun] = {}


def create_run(project_id: str) -> PipelineRun:
    """Create a new pipeline run (or reset an existing one)."""
    with _lock:
        run = PipelineRun(project_id=project_id)
        _runs[project_id] = run
        return run


def update_step(project_id: str, step: StepName, progress: int) -> None:
    """Update the current step and progress for a pipeline run."""
    with _lock:
        run = _runs.get(project_id)
        if run:
            # Record time for previous step
            if run.current_step != "queued":
                run.step_times[run.current_step] = round(time.time() - run.started_at, 1)
            run.current_step = step
            run.progress = min(progress, 100)


def complete_run(project_id: str) -> None:
    """Mark a pipeline run as complete."""
    with _lock:
        run = _runs.get(project_id)
        if run:
            run.current_step = "complete"
            run.progress = 100
            run.completed_at = time.time()
            run.step_times["complete"] = round(run.completed_at - run.started_at, 1)


def fail_run(project_id: str, error_message: str) -> None:
    """Mark a pipeline run as failed."""
    with _lock:
        run = _runs.get(project_id)
        if run:
            run.current_step = "error"
            run.error_message = error_message
            run.completed_at = time.time()


def get_run(project_id: str) -> dict | None:
    """Get the current status of a pipeline run."""
    with _lock:
        run = _runs.get(project_id)
        return run.to_dict() if run else None
