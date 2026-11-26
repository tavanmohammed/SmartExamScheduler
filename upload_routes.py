

import json
import math
import logging

from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    BackgroundTasks,
    File,
    Form,
    HTTPException,
    UploadFile,
)


from pydantic import ValidationError

from algorithm_selector import ALGORITHMS, run_algorithm
from conflicts import generate_conflicts, get_course_students
from schemas import UniversityData
from validator import validate_schedule
from university_file_importer import import_university_file
from exam_time_slots import generate_time_slots
from comparison_jobs import queue_comparison, run_comparison_job

# ============================================================
# ROUTER AND LOGGING
# ============================================================


router = APIRouter(
    tags=["Upload University Data"]
)

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent

UPLOAD_DIR = BASE_DIR / "uploaded_data"
RESULT_DIR = BASE_DIR / "uploaded_results"

MAX_FILE_SIZE = 10 * 1024 * 1024


# ============================================================
# UPLOAD AND GENERATE SCHEDULE
# ============================================================







@router.post("/schedule/upload")
async def upload_and_schedule(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    algorithm: str = Form("Auto"),
    timeout_seconds: float = Form(30),

    # Automatically benchmark all seven algorithms
    compare_algorithms: bool = Form(True),
    compare_timeout_seconds: float = Form(30),


    # Examination period
    start_date: str = Form("2026-12-07"),
    end_date: str = Form("2026-12-18"),

    # Daily examination hours
    start_time: str = Form("09:00"),
    end_time: str = Form("18:00"),

    # Days allowed for examinations
    include_saturday: bool = Form(False),
    include_sunday: bool = Form(False),

    # Dates to exclude, separated by commas
    excluded_dates: str = Form(""),
):

 

    # ========================================================
    # STEP 1 - VALIDATE ALGORITHM
    # ========================================================

    allowed_algorithms = set(ALGORITHMS) | {"Auto"}

    if algorithm not in allowed_algorithms:

        raise HTTPException(
            status_code=400,
            detail=(
                f"Unknown scheduling algorithm: {algorithm}"
            ),
        )

    # ========================================================
    # STEP 2 - VALIDATE TIMEOUT
    # ========================================================

    if (
        not math.isfinite(timeout_seconds)
        or not 0 <= timeout_seconds <= 300
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Timeout must be between "
                "0 and 300 seconds."
            ),
        )

    # ========================================================
    # STEP 3 - READ UPLOADED FILE
    # ========================================================

    filename = file.filename or ""

    logger.info(
        "Received university upload: %s",
        filename
    )

    try:

        contents = await file.read(
            MAX_FILE_SIZE + 1
        )

    finally:

        await file.close()

    if len(contents) > MAX_FILE_SIZE:

        raise HTTPException(
            status_code=413,
            detail=(
                "Uploaded file exceeds "
                "the maximum size of 10 MB."
            ),
        )

    # ========================================================
    # STEP 4 - IMPORT UNIVERSITY DATA
    # ========================================================

    try:
        raw_data = import_university_file(filename, contents)
        university = UniversityData.model_validate(raw_data)
        data = university.model_dump(mode="json")
    except (ValueError, ValidationError) as error:
        logger.warning("University upload validation failed: %s", error)
        raise HTTPException(
            status_code=422,
            detail=f"Invalid university data: {error}",
        ) from error

    # The imported schema may omit duration_minutes, so preserve the
    # original spreadsheet duration before passing data to the solver.
    for exam_id, exam in data["exams"].items():
        original = raw_data["exams"].get(exam_id, {})
        duration = original.get("duration_minutes")
        if duration in (None, ""):
            duration = exam.get("duration_minutes")
        if duration in (None, ""):
            duration = 180
        try:
            duration = int(duration)
        except (ValueError, TypeError) as error:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid duration for {exam_id}: {duration!r}",
            ) from error
        if duration <= 0:
            raise HTTPException(
                status_code=422,
                detail=f"Duration must be positive for {exam_id}",
            )
        exam["duration_minutes"] = duration

    # Generated slots replace reference slots in the uploaded file.
    # Do not reinterpret old slot-index restrictions as new indices.
    for kind in ("exams", "rooms", "professors"):
        for record_id, record in data[kind].items():
            if record.get("unavailable_slots") or record.get("available_slots") is not None:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"{kind} {record_id} has slot-index restrictions from "
                        "the uploaded file. Remove or convert these to "
                        "unavailable_days/unavailable_dates before generating new slots."
                    ),
                )

    try:
        data["time_slots"] = generate_time_slots(
            start_date=start_date,
            end_date=end_date,
            start_time=start_time,
            end_time=end_time,
            include_saturday=include_saturday,
            include_sunday=include_sunday,
            excluded_dates=excluded_dates,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    # ========================================================
    # STEP 5 - SUMMARIZE UNIVERSITY DATA
    # ========================================================

    summary = {
        "departments": len(
            data["departments"]
        ),

        "programs": sum(
            len(programs)
            for programs in data["departments"].values()
        ),

        "examinations": len(
            data["exams"]
        ),

        "students": len(
            data["students"]
        ),

        "rooms": len(
            data["rooms"]
        ),

        "professors": len(
            data["professors"]
        ),

        "time_slots": len(
            data["time_slots"]
        ),

        "course_registrations": sum(
            len(student["courses"])
            for student in data["students"].values()
        ),
    }

    logger.info(
        "University dataset: %s",
        summary
    )

    # ========================================================
    # STEP 6 - BUILD STUDENT CONFLICT GRAPH
    # ========================================================

    course_students = get_course_students(
        data["students"]
    )

    conflicts = generate_conflicts(
        data["exams"],
        course_students,
    )

    conflict_pairs = sum(
        len(neighbors)
        for neighbors in conflicts.values()
    ) // 2

    summary["student_conflict_pairs"] = (
        conflict_pairs
    )

    logger.info(
        "Generated %d student conflict pairs",
        conflict_pairs
    )

    # ========================================================
    # STEP 7 - RUN CSP ALGORITHM
    # ========================================================

    logger.info(
        "Running algorithm %s with timeout %.1fs",
        algorithm,
        timeout_seconds
    )

    result = run_algorithm(
        algorithm,
        data,
        conflicts,
        timeout_seconds=timeout_seconds,
    )

    # ========================================================
    # STEP 8 - VALIDATE GENERATED TIMETABLE
    # ========================================================

    if result["success"]:

        validation = validate_schedule(
            data["exams"],
            data["rooms"],
            data["time_slots"],
            data["students"],
            result["schedule"],
            data["professors"],
        )

        result["validation"] = validation

        if not validation["valid"]:

            logger.error(
                "Generated timetable failed validation: %s",
                validation["errors"]
            )

            # Do not treat an invalid schedule as successful.
            raise HTTPException(
                status_code=500,
                detail={
                    "message": (
                        "Generated timetable failed "
                        "independent validation."
                    ),
                    "errors": validation["errors"],
                },
            )

    else:

        result["validation"] = None

    # ========================================================
    # STEP 9 - GENERATE UNIQUE JOB ID
    # ========================================================

    job_id = uuid4().hex

    UPLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    RESULT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    input_path = (
        UPLOAD_DIR / f"{job_id}.json"
    )

    output_path = (
        RESULT_DIR / f"{job_id}.json"
    )

    # ========================================================
    # STEP 10 - SAVE INPUT AND RESULT
    # ========================================================

    input_path.write_text(
        json.dumps(
            data,
            indent=4
        ),
        encoding="utf-8"
    )

    output_path.write_text(
        json.dumps(
            result,
            indent=4
        ),
        encoding="utf-8"
    )

    logger.info(
        "Scheduling result saved: %s",
        output_path
    )

    # ========================================================
    # STEP 11 - LOG FINAL PERFORMANCE
    # ========================================================

    logger.info(
        "Scheduling finished | status=%s | "
        "success=%s | execution=%.3fs | "
        "assignments=%s | backtracks=%s",
        result.get("status"),
        result.get("success"),
        result.get("execution_time", 0),
        result.get("assignments_attempted"),
        result.get("backtracks"),
    )

    # Readable result alongside the raw exam -> [slot, room] assignments.
    timetable = []
    if result["success"]:
        from datetime import datetime, timedelta
        for exam_id, (slot_index, room_id) in result["schedule"].items():
            exam = data["exams"][exam_id]
            slot = data["time_slots"][slot_index]
            day = slot.get("date") or slot["day"]
            start = datetime.fromisoformat(f"{day}T{slot['start_time']}")
            finish = start + timedelta(minutes=exam["duration_minutes"])
            timetable.append({
                "exam_id": exam_id,
                "course_id": exam.get("course_code", ""),
                "professor_id": exam.get("professor_id", ""),
                "date": day,
                "weekday": start.strftime("%A"),
                "start_time": start.strftime("%H:%M"),
                "end_time": finish.strftime("%H:%M"),
                "room_id": room_id,
            })
        timetable.sort(key=lambda row: (row["date"], row["start_time"], row["exam_id"]))



    # ========================================================
    # STEP 12 - QUEUE ALGORITHM COMPARISON AFTER HTTP RESPONSE
    # ========================================================

    comparison_status = "NOT_REQUESTED"
    if compare_algorithms:
        if (
            not math.isfinite(compare_timeout_seconds)
            or not 0 < compare_timeout_seconds <= 300
        ):
            raise HTTPException(
                status_code=422,
                detail="Comparison timeout must be between 0 and 300 seconds.",
            )

        # FastAPI runs this task after returning the timetable response.
        queue_comparison(job_id)
        background_tasks.add_task(
            run_comparison_job,
            job_id,
            data,
            result,
            compare_timeout_seconds,
        )
        comparison_status = "PENDING"
        logger.info("Queued seven-algorithm comparison for job %s", job_id)

    # ========================================================
    # STEP 13 - RETURN TIMETABLE IMMEDIATELY
    # ========================================================

    return {
        "message": "University file processed.",
        "job_id": job_id,
        "input_file": input_path.name,
        "output_file": output_path.name,
        "input_summary": summary,
        "result": result,
        "timetable": timetable,
        "download_excel": f"/schedule/download/{job_id}" if timetable else None,
        "download_csv": f"/schedule/download/{job_id}/csv" if timetable else None,
        "algorithm_comparison": None,
        "comparison_error": None,
        "comparison_status": comparison_status,
        "comparison_status_url": (
            f"/schedule/comparison-status/{job_id}" if compare_algorithms else None
        ),
        "download_algorithms_excel": None,
        "download_algorithms_csv": None,
    }
