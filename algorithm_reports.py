
import copy
import csv
import io
import json
import logging
import math
import re
import time
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from algorithm_selector import ALGORITHMS, run_algorithm
from conflicts import generate_conflicts, get_course_students
from validator import validate_schedule

router = APIRouter(tags=["Algorithm Comparison"])

ROOT = Path(__file__).resolve().parent
REPORT_DIR = ROOT / "uploaded_reports"
logger = logging.getLogger(__name__)

COLUMNS = [
    "Algorithm",
    "Status",
    "Valid",
    "Exams Scheduled",
    "Solver Time (s)",
    "Total Run Time (s)",
    "Assignments Attempted",
    "Backtracks",
    "Constraint Checks",
    "Nodes Explored",
    "Values Pruned",
    "Details",
]


def save_algorithm_comparison(
    job_id: str,
    data: dict,
    selected_result: dict,
    timeout_seconds: float = 30,
) -> dict:

    if not (
        math.isfinite(timeout_seconds)
        and 0 < timeout_seconds <= 300
    ):
        raise ValueError(
            "Comparison timeout must be between 0 and 300 seconds"
        )

    if not re.fullmatch(r"[0-9a-f]{32}", job_id):
        raise ValueError("Invalid job ID")

    records = []

    for name in ALGORITHMS:
        started = time.perf_counter()
        result = None
        note = ""

        try:
            if selected_result.get("algorithm") == name:
                result = selected_result
                note = "Selected timetable run (reused)"
            else:
                independent_data = copy.deepcopy(data)

                conflicts = generate_conflicts(
                    independent_data["exams"],
                    get_course_students(
                        independent_data["students"]
                    ),
                )

                result = run_algorithm(
                    name,
                    independent_data,
                    conflicts,
                    timeout_seconds=timeout_seconds,
                )

            schedule = result.get("schedule") or {}
            status = str(
                result.get("status") or "UNKNOWN"
            )
            valid = False

            if result.get("success"):
                validation = validate_schedule(
                    data["exams"],
                    data["rooms"],
                    data["time_slots"],
                    data["students"],
                    schedule,
                    data["professors"],
                )

                valid = bool(validation.get("valid"))

                if not valid:
                    status = "INVALID"
                    note = "; ".join(
                        str(error)
                        for error in validation.get("errors", [])
                    )[:800]
            else:
                note = str(
                    result.get("message")
                    or result.get("error")
                    or status
                )[:800]

            total_time = time.perf_counter() - started

            if result is selected_result:
                total_time = result.get(
                    "execution_time", total_time
                )

            records.append({
                "algorithm": name,
                "status": status,
                "valid": valid,
                "exams_scheduled": len(schedule),
                "solver_time_seconds": result.get(
                    "execution_time"
                ),
                "total_run_seconds": round(total_time, 4),
                "assignments_attempted": result.get(
                    "assignments_attempted"
                ),
                "backtracks": result.get("backtracks"),
                "constraint_checks": result.get(
                    "constraint_checks"
                ),
                "nodes_explored": result.get(
                    "nodes_explored"
                ),
                "values_pruned": result.get(
                    "values_pruned"
                ),
                "details": note,
            })

        except Exception as error:
            logger.exception(
                "Algorithm %s failed", name
            )

            records.append({
                "algorithm": name,
                "status": "ERROR",
                "valid": False,
                "exams_scheduled": 0,
                "solver_time_seconds": None,
                "total_run_seconds": round(
                    time.perf_counter() - started, 4
                ),
                "assignments_attempted": None,
                "backtracks": None,
                "constraint_checks": None,
                "nodes_explored": None,
                "values_pruned": None,
                "details": str(error)[:800],
            })

    report = {
        "job_id": job_id,
        "selected_algorithm": selected_result.get(
            "algorithm"
        ),
        "selected_status": selected_result.get(
            "status"
        ),
        "exam_count": len(data["exams"]),
        "student_count": len(data["students"]),
        "room_count": len(data["rooms"]),
        "benchmark_timeout_seconds": timeout_seconds,
        "algorithm_count": len(records),
        "passed": sum(
            record["valid"] for record in records
        ),
        "results": records,
    }

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    report_path = REPORT_DIR / f"{job_id}.json"

    report_path.write_text(
        json.dumps(report, indent=2, allow_nan=False),
        encoding="utf-8",
    )

    return report


def load_report(job_id: str) -> dict:
    if not re.fullmatch(r"[0-9a-f]{32}", job_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid job ID",
        )

    path = REPORT_DIR / f"{job_id}.json"

    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail="Algorithm comparison not found",
        )

    return json.loads(
        path.read_text(encoding="utf-8")
    )


def safe_excel_value(value):
    if value is None:
        return ""

    if isinstance(value, str) and value.startswith(
        ("=", "+", "-", "@", "\t", "\r")
    ):
        return "'" + value

    return value


def comparison_rows(report):
    keys = [
        "algorithm",
        "status",
        "valid",
        "exams_scheduled",
        "solver_time_seconds",
        "total_run_seconds",
        "assignments_attempted",
        "backtracks",
        "constraint_checks",
        "nodes_explored",
        "values_pruned",
        "details",
    ]

    for result in report["results"]:
        yield [
            safe_excel_value(result.get(key))
            for key in keys
        ]


@router.get(
    "/schedule/download/{job_id}/algorithms"
)
def download_algorithm_excel(job_id: str):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill
    from openpyxl.utils import get_column_letter

    report = load_report(job_id)

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Algorithm Comparison"

    sheet.append(COLUMNS)

    for row in comparison_rows(report):
        sheet.append(row)

    for cell in sheet[1]:
        cell.font = Font(
            bold=True,
            color="FFFFFF",
        )
        cell.fill = PatternFill(
            fill_type="solid",
            fgColor="17365D",
        )

    widths = [
        40, 15, 12, 20,
        20, 20, 22, 15,
        20, 18, 16, 48,
    ]

    for index, width in enumerate(widths, start=1):
        letter = get_column_letter(index)
        sheet.column_dimensions[letter].width = width

    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions

    summary = workbook.create_sheet("Summary")

    summary_data = [
        ("Job ID", report["job_id"]),
        (
            "Selected Algorithm",
            report["selected_algorithm"],
        ),
        (
            "Selected Status",
            report["selected_status"],
        ),
        ("Exams", report["exam_count"]),
        ("Students", report["student_count"]),
        ("Rooms", report["room_count"]),
        (
            "Algorithms Compared",
            report["algorithm_count"],
        ),
        ("Valid Results", report["passed"]),
        (
            "Timeout Per Algorithm",
            report["benchmark_timeout_seconds"],
        ),
    ]

    for item in summary_data:
        summary.append([
            safe_excel_value(value)
            for value in item
        ])

    summary.column_dimensions["A"].width = 35
    summary.column_dimensions["B"].width = 45

    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)

    filename = (
        f"Algorithm_Comparison_{job_id[:8]}.xlsx"
    )

    return StreamingResponse(
        buffer,
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition":
                f'attachment; filename="{filename}"'
        },
    )


@router.get(
    "/schedule/download/{job_id}/algorithms/csv"
)
def download_algorithm_csv(job_id: str):
    report = load_report(job_id)

    output = io.StringIO(newline="")
    writer = csv.writer(output)

    writer.writerow(COLUMNS)

    for row in comparison_rows(report):
        writer.writerow(row)

    filename = (
        f"Algorithm_Comparison_{job_id[:8]}.csv"
    )

    return StreamingResponse(
        iter([output.getvalue().encode("utf-8-sig")]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition":
                f'attachment; filename="{filename}"'
        },
    )
