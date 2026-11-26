
"""Manual JSON input -> validated AI exam timetable."""

import json
import math
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field, ValidationError

from algorithm_selector import ALGORITHMS, run_algorithm
from conflicts import generate_conflicts, get_course_students
from exam_time_slots import generate_time_slots
from schemas import UniversityData
from validator import validate_schedule
from comparison_jobs import queue_comparison, run_comparison_job


router = APIRouter(tags=["Manual University Input"])
ROOT = Path(__file__).resolve().parent


class ExamPeriod(BaseModel):
    start_date: str = "2026-12-07"
    end_date: str = "2026-12-18"
    start_time: str = "09:00"
    end_time: str = "18:00"
    include_saturday: bool = False
    include_sunday: bool = False
    excluded_dates: str = ""
    slot_minutes: int = Field(default=180, ge=15, le=720)


class ManualRequest(BaseModel):
    departments: dict[str, list[str]]
    students: dict[str, dict]
    exams: dict[str, dict]
    professors: dict[str, dict]
    rooms: dict[str, dict]

    period: ExamPeriod = Field(default_factory=ExamPeriod)

    algorithm: str = "Auto"
    timeout_seconds: float = Field(default=30, gt=0, le=300)

    # Run all seven algorithms automatically
    compare_algorithms: bool = True
    compare_timeout_seconds: float = Field(
        default=30,
        gt=0,
        le=300,
    )


@router.post("/schedule/manual")
def schedule_manually(request: ManualRequest, background_tasks: BackgroundTasks):
    """Generate a validated timetable and queue the algorithm comparison."""

    if request.algorithm not in set(ALGORITHMS) | {"Auto"}:
        raise HTTPException(
            status_code=422,
            detail="Unknown algorithm",
        )

    if not math.isfinite(request.timeout_seconds):
        raise HTTPException(
            status_code=422,
            detail="Timeout must be finite",
        )

    if not math.isfinite(request.compare_timeout_seconds):
        raise HTTPException(
            status_code=422,
            detail="Comparison timeout must be finite",
        )

    # Prepare university input
    raw = request.model_dump(
        exclude={
            "period",
            "algorithm",
            "timeout_seconds",
            "compare_algorithms",
            "compare_timeout_seconds",
        }
    )

    # Generate examination time slots
    try:
        raw["time_slots"] = generate_time_slots(
            **request.period.model_dump()
        )
    except (ValueError, TypeError) as error:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid examination period: {error}",
        ) from error

    # Count students registered in each examination
    registrations = {
        exam_id: 0
        for exam_id in raw["exams"]
    }

    for sid, student in raw["students"].items():
        registered = student.get("courses", [])

        if (
            not isinstance(registered, list)
            or len(set(registered)) != len(registered)
        ):
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Student {sid}: courses must be "
                    "a list of unique exam IDs"
                ),
            )

        for exam_id in registered:
            if exam_id not in registrations:
                raise HTTPException(
                    status_code=422,
                    detail=f"Student {sid}: unknown exam {exam_id}",
                )

            registrations[exam_id] += 1

    # Validate exams
    for exam_id, exam in raw["exams"].items():
        if exam.get("professor_id") not in raw["professors"]:
            raise HTTPException(
                status_code=422,
                detail=f"Exam {exam_id}: unknown professor",
            )

        count = registrations[exam_id]

        if count == 0:
            raise HTTPException(
                status_code=422,
                detail=f"Exam {exam_id}: no students registered",
            )

        if exam.get("students") not in (None, count):
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Exam {exam_id}: student count differs "
                    f"from registrations ({count})"
                ),
            )

        exam["students"] = count

        duration = exam.get(
            "duration_minutes",
            exam.get("duration", 180),
        )

        try:
            duration = int(duration)
        except (TypeError, ValueError) as error:
            raise HTTPException(
                status_code=422,
                detail=f"Exam {exam_id}: invalid duration",
            ) from error

        if duration <= 0:
            raise HTTPException(
                status_code=422,
                detail=f"Exam {exam_id}: duration must be positive",
            )

        exam["duration"] = duration
        exam["duration_minutes"] = duration
        exam.setdefault("room_type", "classroom")
        exam.setdefault("required_tas", 0)

        for field in ("available_slots", "unavailable_slots"):
            value = exam.get(field)

            if value is not None and (
                field == "available_slots" or value
            ):
                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"Exam {exam_id}: use dates rather "
                        "than slot index restrictions"
                    ),
                )

    # Validate professors and rooms
    for kind in ("professors", "rooms"):
        for rid, record in raw[kind].items():
            if (
                record.get("available_slots") is not None
                or record.get("unavailable_slots")
            ):
                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"{kind} {rid}: use dates instead "
                        "of slot indices"
                    ),
                )

            if kind == "rooms":
                capacity = record.get(
                    "exam_capacity",
                    record.get("capacity"),
                )

                if (
                    not isinstance(capacity, int)
                    or isinstance(capacity, bool)
                    or capacity <= 0
                ):
                    raise HTTPException(
                        status_code=422,
                        detail=(
                            f"Room {rid}: positive integer "
                            "capacity required"
                        ),
                    )

                record["capacity"] = capacity
                record["exam_capacity"] = capacity
                record.setdefault("room_type", "classroom")

    # Validate university data against the schema
    dated_slots = raw["time_slots"]

    raw["time_slots"] = [
        {**slot, "time": slot["start_time"]}
        for slot in dated_slots
    ]

    try:
        university = UniversityData.model_validate(raw)
        data = university.model_dump(mode="json")
    except (ValidationError, ValueError) as error:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid university data: {error}",
        ) from error

    # Restore fields removed by the legacy schema
    for eid, exam in data["exams"].items():
        exam["duration_minutes"] = (
            raw["exams"][eid]["duration_minutes"]
        )

    data["time_slots"] = dated_slots

    # Identify student conflicts
    conflicts = generate_conflicts(
        data["exams"],
        get_course_students(data["students"]),
    )

    # Run the selected AI algorithm
    try:
        result = run_algorithm(
            request.algorithm,
            data,
            conflicts,
            timeout_seconds=request.timeout_seconds,
        )
    except (ValueError, KeyError) as error:
        raise HTTPException(
            status_code=422,
            detail=f"Cannot schedule this dataset: {error}",
        ) from error

    # Build the examination timetable
    timetable = []

    if result.get("success"):
        validation = validate_schedule(
            data["exams"],
            data["rooms"],
            data["time_slots"],
            data["students"],
            result["schedule"],
            data["professors"],
        )

        result["validation"] = validation

        if not validation.get("valid"):
            raise HTTPException(
                status_code=500,
                detail={
                    "message": (
                        "Timetable failed independent validation"
                    ),
                    "errors": validation.get("errors", []),
                },
            )

        for eid, (slot, room) in result["schedule"].items():
            selected_slot = data["time_slots"][slot]

            start = datetime.fromisoformat(
                f'{selected_slot["date"]}T'
                f'{selected_slot["start_time"]}'
            )

            end = start + timedelta(
                minutes=data["exams"][eid]["duration_minutes"]
            )

            timetable.append({
                "exam_id": eid,
                "course_id": data["exams"][eid]["course_code"],
                "professor_id": (
                    data["exams"][eid]["professor_id"]
                ),
                "date": selected_slot["date"],
                "weekday": start.strftime("%A"),
                "start_time": start.strftime("%H:%M"),
                "end_time": end.strftime("%H:%M"),
                "room_id": room,
            })

        timetable.sort(
            key=lambda item: (
                item["date"],
                item["start_time"],
                item["room_id"],
            )
        )

    else:
        result["validation"] = None

    # Save the original university data and AI result
    job_id = uuid4().hex

    for subdir, payload in (
        ("uploaded_data", data),
        ("uploaded_results", result),
    ):
        folder = ROOT / subdir
        folder.mkdir(parents=True, exist_ok=True)

        (folder / f"{job_id}.json").write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )

    # Run the seven-algorithm comparison *after* the HTTP response.
    comparison_status = "NOT_REQUESTED"
    if request.compare_algorithms:
        queue_comparison(job_id)
        background_tasks.add_task(
            run_comparison_job,
            job_id,
            data,
            result,
            request.compare_timeout_seconds,
        )
        comparison_status = "PENDING"

    # Timetable links are ready immediately; comparison links appear
    # at the status endpoint once the background report is complete.
    return {
        "job_id": job_id,
        "success": bool(result.get("success")),
        "status": result.get("status"),
        "algorithm": result.get("algorithm"),
        "validation": result.get("validation"),
        "timetable": timetable,
        "download_excel": f"/schedule/download/{job_id}" if timetable else None,
        "download_csv": f"/schedule/download/{job_id}/csv" if timetable else None,
        "algorithm_comparison": None,
        "comparison_error": None,
        "comparison_status": comparison_status,
        "comparison_status_url": (
            f"/schedule/comparison-status/{job_id}"
            if request.compare_algorithms else None
        ),
        "download_algorithms_excel": None,
        "download_algorithms_csv": None,
        "message": (
            "Schedule generated" if timetable else
            "No complete schedule found within the allowed dates and constraints"
        ),
    }
