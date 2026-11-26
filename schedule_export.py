"""Download validated Smart Exam Scheduler results as an Excel or CSV timetable.

Installation: put this file next to api.py, then include its router in api.py.
Reads the upload API's existing uploaded_data/<job_id>.json and
uploaded_results/<job_id>.json. It does not rerun the scheduling algorithm.
"""

import csv
import io
import json
import re
from datetime import date, datetime, time, timedelta
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

router = APIRouter(tags=["Download Timetable"])
ROOT = Path(__file__).resolve().parent
INPUT_DIR = ROOT / "uploaded_data"
RESULT_DIR = ROOT / "uploaded_results"

HEADERS = (
    "Exam ID", "Course ID", "Exam Name", "Department", "Professor ID",
    "Date", "Day", "Start Time", "End Time", "Duration (minutes)",
    "Room ID", "Enrolled Students",
)


def _safe_text(value):
    """Avoid executable spreadsheet formulas from user-provided text."""
    if value is None:
        return ""
    if isinstance(value, str) and value.startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + value
    return value


def _load_saved(job_id):
    if not re.fullmatch(r"[0-9a-f]{32}", job_id):
        raise HTTPException(status_code=400, detail="Invalid job ID")

    input_file = INPUT_DIR / f"{job_id}.json"
    result_file = RESULT_DIR / f"{job_id}.json"
    if not input_file.is_file() or not result_file.is_file():
        raise HTTPException(status_code=404, detail="Saved schedule not found")

    try:
        data = json.loads(input_file.read_text(encoding="utf-8"))
        result = json.loads(result_file.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=500, detail="Cannot read saved timetable") from exc

    if not result.get("success") or not (result.get("validation") or {}).get("valid"):
        raise HTTPException(status_code=409, detail="Only successfully validated timetables can be downloaded")

    return data, result


def _parse_clock(value):
    if isinstance(value, datetime):
        return value.time()
    if isinstance(value, time):
        return value
    return time.fromisoformat(str(value).strip())


def _build_rows(data, result):
    """Reconstruct readable timetable from stored inputs and solver output."""
    exams = data["exams"]
    slots = data["time_slots"]
    rows = []
    assignments = result["schedule"]

    if len(assignments) != len(exams) or set(assignments) != set(exams):
        raise ValueError("Saved schedule does not include exactly all exams")

    for exam_id, assignment in assignments.items():
        if not isinstance(assignment, (tuple, list)) or len(assignment) != 2:
            raise ValueError(f"Invalid saved assignment for {exam_id}")
        slot_index, room_id = assignment
        if type(slot_index) is not int or not 0 <= slot_index < len(slots):
            raise ValueError(f"Invalid saved slot for {exam_id}")
        exam = exams[exam_id]
        slot = slots[slot_index]
        day_value = slot.get("date") or slot.get("day")
        exam_day = date.fromisoformat(str(day_value)[:10])
        start_dt = datetime.combine(exam_day, _parse_clock(slot["start_time"]))
        duration = int(exam.get("duration_minutes", 180))
        if duration <= 0:
            raise ValueError(f"Invalid exam duration for {exam_id}")
        end_dt = start_dt + timedelta(minutes=duration)
        if end_dt.date() != start_dt.date():
            raise ValueError(f"Exam extends to the next day: {exam_id}")
        if slot.get("end_time") not in (None, ""):
            slot_end = datetime.combine(exam_day, _parse_clock(slot["end_time"]))
            if end_dt > slot_end:
                raise ValueError(f"Exam exceeds its assigned time slot: {exam_id}")
        rows.append([
            _safe_text(exam_id),
            _safe_text(exam.get("course_code", exam.get("course_id", ""))),
            _safe_text(exam.get("name", exam.get("exam_name", ""))),
            _safe_text(exam.get("department", "")),
            _safe_text(exam.get("professor_id", "")),
            exam_day.isoformat(),
            exam_day.strftime("%A"),
            start_dt.strftime("%H:%M"),
            end_dt.strftime("%H:%M"),
            duration,
            _safe_text(room_id),
            exam.get("students", exam.get("enrollment", "")),
        ])

    rows.sort(key=lambda row: (row[5], row[7], row[10], row[0]))
    return rows


def _get_rows(job_id):
    data, result = _load_saved(job_id)
    try:
        return _build_rows(data, result), result
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        raise HTTPException(status_code=500, detail=f"Saved schedule data is invalid: {exc}") from exc


def _xlsx_bytes(rows, result):
    workbook = Workbook()
    ws = workbook.active
    ws.title = "Exam Timetable"
    ws.append(HEADERS)
    for row in rows:
        ws.append(row)

    navy = "17365D"
    for cell in ws[1]:
        cell.fill = PatternFill(fill_type="solid", fgColor=navy)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.alignment = Alignment(vertical="center", wrap_text=True)
    ws.row_dimensions[1].height = 30
    for index, width in enumerate((15, 16, 32, 22, 18, 16, 16, 15, 15, 20, 17, 19), 1):
        ws.column_dimensions[get_column_letter(index)].width = width
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions

    summary = workbook.create_sheet("Summary")
    summary.append(["Smart Exam Scheduler — Validated Result"])
    summary.append(["Exams Scheduled", len(rows)])
    summary.append(["Status", result.get("status", "SOLVED")])
    summary.append(["Algorithm", result.get("algorithm", "")])
    summary.append(["Execution Time (seconds)", result.get("execution_time", "")])
    summary.append(["Validation", "PASSED"])
    summary.column_dimensions["A"].width = 30
    summary.column_dimensions["B"].width = 35
    summary["A1"].font = Font(bold=True, color=navy, size=14)

    output = io.BytesIO()
    workbook.save(output)
    output.seek(0)
    return output


@router.get("/schedule/download/{job_id}")
def download_excel(job_id: str):
    """Download a saved, validated timetable as an Excel workbook."""
    rows, result = _get_rows(job_id)
    return StreamingResponse(
        _xlsx_bytes(rows, result),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="Exam_Timetable_{job_id[:8]}.xlsx"'},
    )


@router.get("/schedule/download/{job_id}/csv")
def download_csv(job_id: str):
    """Download the same saved timetable as CSV."""
    rows, _ = _get_rows(job_id)
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(HEADERS)
    writer.writerows(rows)
    return StreamingResponse(
        iter([output.getvalue().encode("utf-8-sig")]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="Exam_Timetable_{job_id[:8]}.csv"'},
    )
