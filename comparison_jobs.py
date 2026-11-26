"""Non-blocking FastAPI background benchmark jobs for Smart Exam Scheduler.

Run all seven algorithms after the scheduling HTTP response is sent.
Uses local JSON status files: appropriate for a single-process classroom demo.
"""

import json
import logging
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from algorithm_reports import save_algorithm_comparison

logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent
STATUS_DIR = BASE_DIR / "uploaded_reports" / "status"
STATUS_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter(tags=["Algorithm Comparison Status"])


def _status_path(job_id: str) -> Path:
    if not job_id or not all(c in "0123456789abcdef" for c in job_id.lower()) or len(job_id) != 32:
        raise ValueError("Invalid job ID")
    return STATUS_DIR / f"{job_id}.json"


def _write_status(job_id: str, status: str, **fields) -> None:
    path = _status_path(job_id)
    payload = {
        "job_id": job_id,
        "status": status,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        **fields,
    }
    temp_path = path.with_name(f"{path.stem}.{uuid4().hex}.tmp")
    try:
        temp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        os.replace(temp_path, path)
    finally:
        temp_path.unlink(missing_ok=True)


def queue_comparison(job_id: str, algorithm_count: int = 7) -> None:
    """Create a visible PENDING status before sending the scheduling response."""
    _write_status(
        job_id,
        "PENDING",
        completed_algorithms=0,
        total_algorithms=algorithm_count,
        download_algorithms_excel=None,
        download_algorithms_csv=None,
    )


def run_comparison_job(job_id: str, data: dict, selected_result: dict, timeout_seconds: float = 30) -> None:
    """FastAPI BackgroundTasks calls this *sync* function in a worker thread."""
    try:
        if not math.isfinite(timeout_seconds) or not (0 < timeout_seconds <= 300):
            raise ValueError("Comparison timeout must be between 0 and 300 seconds")
        _write_status(job_id, "PROCESSING", completed_algorithms=0, total_algorithms=7)
        report = save_algorithm_comparison(
            job_id=job_id,
            data=data,
            selected_result=selected_result,
            timeout_seconds=timeout_seconds,
        )
        count = len(report.get("results", []))
        if count != 7:
            raise RuntimeError(f"Expected 7 algorithm results, got {count}")
        _write_status(
            job_id,
            "COMPLETED",
            completed_algorithms=count,
            total_algorithms=7,
            passed=report.get("passed"),
            download_algorithms_excel=f"/schedule/download/{job_id}/algorithms",
            download_algorithms_csv=f"/schedule/download/{job_id}/algorithms/csv",
        )
    except Exception as exc:
        logger.exception("Algorithm comparison job failed for %s", job_id)
        _write_status(
            job_id,
            "FAILED",
            completed_algorithms=0,
            total_algorithms=7,
            error=str(exc),
        )


@router.get("/schedule/comparison-status/{job_id}")
def comparison_status(job_id: str):
    try:
        path = _status_path(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Comparison job not found")
    return json.loads(path.read_text(encoding="utf-8"))
