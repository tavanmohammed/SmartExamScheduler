
"""
SMART EXAM SCHEDULER
University File Importer - No Teaching Assistants

Supported formats:
    Excel (.xlsx)
    CSV files inside ZIP (.zip)
    JSON (.json)

Required university tables:
    1. Students
    2. Registrations
    3. Exams
    4. Rooms
    5. Professors
    6. Time_Slots
"""

import csv
import io
import json
import zipfile

from collections import Counter, defaultdict
from datetime import datetime, time
from pathlib import PurePosixPath

# ============================================================
# REQUIRED WORKSHEETS / CSV FILES
# ============================================================

SHEETS = (
    "students",
    "registrations",
    "exams",
    "rooms",
    "professors",
    "time_slots",
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def items(value):
    """Read semicolon-separated values into a list."""

    if value is None:
        return []

    return [
        item.strip()
        for item in str(value).split(";")
        if item.strip()
    ]


def int_value(value, label, default=None):
    """Convert numeric spreadsheet values to integers."""

    if value is None or str(value).strip() == "":

        if default is not None:
            return default

        raise ValueError(
            f"Missing required value: {label}"
        )

    try:
        number = float(value)

        if not number.is_integer():
            raise ValueError()

        return int(number)

    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(
            f"{label} must be an integer: {value!r}"
        ) from exc


def require(row, field, sheet):
    """Return a required cell or raise a useful error."""

    value = row.get(field)

    if value is None or not str(value).strip():
        raise ValueError(
            f"{sheet}: missing required field {field}"
        )

    return str(value).strip()


def slot_time(value):
    """Convert Excel time cells into HH:MM strings."""

    if isinstance(value, (datetime, time)):
        return value.strftime("%H:%M")

    value = str(value or "").strip()

    if not value:
        raise ValueError("Missing start_time")

    return value


def int_list(value, label):
    """Read semicolon-separated slot indexes."""

    return [
        int_value(item, label)
        for item in items(value)
    ]


def clean_old_ta_fields(data):
    """
    Remove legacy TA information from older JSON data.

    Does not change student registrations,
    professor assignments, rooms or time slots.
    """

    if not isinstance(data, dict):
        raise ValueError(
            "University data must be a JSON object"
        )

    data.pop("teaching_assistants", None)

    exams = data.get("exams", {})

    if isinstance(exams, dict):
        for exam in exams.values():
            if isinstance(exam, dict):
                exam.pop("required_tas", None)

    return data


# ============================================================
# 1. EXCEL FILE READER
# ============================================================

def read_excel(content):
    """Read six required worksheets from an Excel file."""

    from openpyxl import load_workbook

    try:
        workbook = load_workbook(
            io.BytesIO(content),
            read_only=True,
            data_only=True,
        )

    except Exception as exc:
        raise ValueError(
            f"Cannot read Excel workbook: {exc}"
        ) from exc

    try:
        lookup = {
            name.strip().lower(): name
            for name in workbook.sheetnames
        }

        missing = set(SHEETS) - set(lookup)

        if missing:
            raise ValueError(
                "Missing required Excel worksheets: "
                + ", ".join(sorted(missing))
            )

        tables = {}

        for sheet_name in SHEETS:

            worksheet = workbook[lookup[sheet_name]]

            rows = worksheet.iter_rows(
                values_only=True
            )

            headers = next(rows, None)

            if not headers:
                raise ValueError(
                    f"{sheet_name}: missing header row"
                )

            headers = [
                str(header).strip().lower()
                if header is not None
                else ""
                for header in headers
            ]

            if (
                not all(headers)
                or len(headers) != len(set(headers))
            ):
                raise ValueError(
                    f"{sheet_name}: invalid column headers"
                )

            tables[sheet_name] = []

            for values in rows:

                if not any(
                    value is not None
                    and str(value).strip()
                    for value in values
                ):
                    continue

                tables[sheet_name].append(
                    dict(zip(headers, values))
                )

        return tables

    finally:
        workbook.close()


# ============================================================
# 2. CSV ZIP READER
# ============================================================

def read_csv_zip(content):
    """
    Read a ZIP containing six CSV files:

        students.csv
        registrations.csv
        exams.csv
        rooms.csv
        professors.csv
        time_slots.csv
    """

    try:
        archive = zipfile.ZipFile(
            io.BytesIO(content)
        )

    except (zipfile.BadZipFile, OSError) as exc:
        raise ValueError(
            "Invalid ZIP file"
        ) from exc

    with archive:

        if len(archive.infolist()) > 50:
            raise ValueError(
                "ZIP contains too many files"
            )

        names = {}

        required_files = {
            f"{sheet}.csv"
            for sheet in SHEETS
        }

        for info in archive.infolist():

            if info.is_dir():
                continue

            filename = PurePosixPath(
                info.filename.replace("\\", "/")
            ).name.lower()

            if filename not in required_files:
                continue

            if filename in names:
                raise ValueError(
                    f"Duplicate CSV file: {filename}"
                )

            names[filename] = info

        missing = required_files - set(names)

        if missing:
            raise ValueError(
                "Missing CSV files: "
                + ", ".join(sorted(missing))
            )

        total_size = sum(
            info.file_size
            for info in names.values()
        )

        if total_size > 30 * 1024 * 1024:
            raise ValueError(
                "Uncompressed CSV data exceeds 30 MB"
            )

        tables = {}

        for sheet in SHEETS:

            raw = archive.read(
                names[f"{sheet}.csv"]
            )

            try:
                text_data = raw.decode("utf-8-sig")

            except UnicodeDecodeError as exc:
                raise ValueError(
                    f"{sheet}.csv must use UTF-8"
                ) from exc

            reader = csv.DictReader(
                io.StringIO(text_data)
            )

            if not reader.fieldnames:
                raise ValueError(
                    f"{sheet}.csv has no headers"
                )

            headers = [
                str(header).strip().lower()
                if header is not None
                else ""
                for header in reader.fieldnames
            ]

            if (
                not all(headers)
                or len(headers) != len(set(headers))
            ):
                raise ValueError(
                    f"Invalid headers in {sheet}.csv"
                )

            reader.fieldnames = headers
            tables[sheet] = []

            for row in reader:

                if None in row:
                    raise ValueError(
                        f"Too many columns in {sheet}.csv"
                    )

                if any(
                    value is not None
                    and str(value).strip()
                    for value in row.values()
                ):
                    tables[sheet].append(row)

        return tables


# ============================================================
# 3. CONVERT TABLES INTO UNIVERSITY CSP DATA
# ============================================================

def convert_tables(tables):
    """
    Convert Excel / CSV tables into the
    standard university scheduling structure.

    Teaching Assistants are excluded.
    """

    students = {}
    registrations = defaultdict(list)

    exams = {}
    rooms = {}
    professors = {}
    departments = defaultdict(set)

    enrollment_counts = Counter()

    # ========================================================
    # STUDENTS
    # ========================================================

    for row in tables["students"]:

        student_id = require(
            row,
            "student_id",
            "Students"
        )

        if student_id in students:
            raise ValueError(
                f"Duplicate student ID: {student_id}"
            )

        department = require(
            row,
            "department",
            "Students"
        )

        program = require(
            row,
            "program",
            "Students"
        )

        year = int_value(
            row.get("academic_year"),
            "academic_year"
        )

        if not 1 <= year <= 4:
            raise ValueError(
                f"Invalid academic year: {student_id}"
            )

        departments[department].add(program)

        students[student_id] = {
            "department": department,
            "program": program,
            "year": year,
            "courses": [],
        }

    # ========================================================
    # STUDENT COURSE REGISTRATIONS
    # ========================================================

    for row in tables["registrations"]:

        student_id = require(
            row,
            "student_id",
            "Registrations"
        )

        exam_id = require(
            row,
            "exam_id",
            "Registrations"
        )

        if student_id not in students:
            raise ValueError(
                f"Unknown student in registration: "
                f"{student_id}"
            )

        if exam_id in students[student_id]["courses"]:
            raise ValueError(
                f"Duplicate registration: "
                f"{student_id} / {exam_id}"
            )

        students[student_id]["courses"].append(
            exam_id
        )

        enrollment_counts[exam_id] += 1

    # ========================================================
    # EXAMINATIONS / COURSES
    # ========================================================

    for row in tables["exams"]:

        exam_id = require(
            row,
            "exam_id",
            "Exams"
        )

        if exam_id in exams:
            raise ValueError(
                f"Duplicate exam ID: {exam_id}"
            )

        department = require(
            row,
            "department",
            "Exams"
        )

        programs = items(
            row.get("programs")
        )

        if not programs:
            raise ValueError(
                f"{exam_id}: missing programs"
            )

        departments[department].update(
            programs
        )

        enrollment = enrollment_counts[exam_id]

        declared = int_value(
            row.get("enrollment"),
            "enrollment",
            enrollment
        )

        if declared != enrollment:
            raise ValueError(
                f"{exam_id}: enrollment mismatch. "
                f"Declared {declared}, "
                f"registered {enrollment}"
            )

        exams[exam_id] = {
            "course_code": require(
                row,
                "course_code",
                "Exams"
            ),

            "name": require(
                row,
                "exam_name",
                "Exams"
            ),

            "department": department,

            "programs": programs,

            "professor_id": require(
                row,
                "professor_id",
                "Exams"
            ),

            "students": enrollment,

            "duration": int_value(
                row.get("duration_minutes"),
                "duration_minutes",
                180
            ),

            "room_type": str(
                row.get("room_type")
                or "classroom"
            ).strip(),
        }

    # ========================================================
    # VALIDATE REGISTERED COURSES
    # ========================================================

    for student_id, student in students.items():

        unknown = (
            set(student["courses"]) - set(exams)
        )

        if unknown:
            raise ValueError(
                f"Student {student_id} registered "
                f"in unknown courses: {sorted(unknown)}"
            )

    # ========================================================
    # ROOMS
    # ========================================================

    for row in tables["rooms"]:

        room_id = require(
            row,
            "room_id",
            "Rooms"
        )

        if room_id in rooms:
            raise ValueError(
                f"Duplicate room: {room_id}"
            )

        exam_capacity = int_value(
            row.get("exam_capacity"),
            "exam_capacity"
        )

        physical_capacity = int_value(
            row.get("capacity"),
            "capacity",
            exam_capacity
        )

        rooms[room_id] = {
            "capacity": physical_capacity,

            "exam_capacity": exam_capacity,

            "room_type": str(
                row.get("room_type")
                or "classroom"
            ).strip(),

            "unavailable_slots": int_list(
                row.get("unavailable_slots"),
                "room unavailable slot"
            ),

            "unavailable_days": items(
                row.get("unavailable_days")
            ),
        }

    # ========================================================
    # PROFESSORS
    # ========================================================

    for row in tables["professors"]:

        professor_id = require(
            row,
            "professor_id",
            "Professors"
        )

        if professor_id in professors:
            raise ValueError(
                f"Duplicate professor ID: {professor_id}"
            )

        professors[professor_id] = {
            "name": str(
                row.get("name")
                or professor_id
            ).strip(),

            "unavailable_days": items(
                row.get("unavailable_days")
            ),

            "unavailable_slots": int_list(
                row.get("unavailable_slots"),
                "professor unavailable slot"
            ),
        }

    # ========================================================
    # VALIDATE COURSE PROFESSOR REFERENCES
    # ========================================================

    for exam_id, exam in exams.items():

        professor_id = exam["professor_id"]

        if professor_id not in professors:
            raise ValueError(
                f"Exam {exam_id} references "
                f"unknown professor {professor_id}"
            )

    # ========================================================
    # EXAMINATION TIME SLOTS
    # ========================================================

    indexed_slots = {}

    for row in tables["time_slots"]:

        index = int_value(
            row.get("slot_index"),
            "slot_index"
        )

        if index in indexed_slots:
            raise ValueError(
                f"Duplicate slot index: {index}"
            )

        indexed_slots[index] = {
            "day": require(
                row,
                "day",
                "Time_Slots"
            ),

            "time": slot_time(
                row.get("start_time")
            ),
        }

    expected = list(
        range(len(indexed_slots))
    )

    if sorted(indexed_slots) != expected:
        raise ValueError(
            "Slot indexes must start at 0 "
            "and have no gaps"
        )

    time_slots = [
        indexed_slots[index]
        for index in expected
    ]

    # ========================================================
    # FINAL CSP UNIVERSITY DATA
    # ========================================================

    return {
        "departments": {
            department: sorted(programs)
            for department, programs
            in departments.items()
        },

        "exams": exams,

        "rooms": rooms,

        "time_slots": time_slots,

        "students": students,

        "professors": professors,
    }


# ============================================================
# 4. MAIN FILE IMPORT FUNCTION
# ============================================================

def import_university_file(filename, content):
    """
    Automatically detect the uploaded format
    and return validated-style university data.

    Full structural validation is performed by
    UniversityData in schemas.py.
    """

    filename = (filename or "").lower()

    # --------------------------------------------------------
    # JSON
    # --------------------------------------------------------

    if filename.endswith(".json"):

        try:
            data = json.loads(
                content.decode("utf-8-sig")
            )

        except (
            ValueError,
            UnicodeDecodeError
        ) as exc:

            raise ValueError(
                f"Invalid JSON: {exc}"
            ) from exc

        return clean_old_ta_fields(data)

    # --------------------------------------------------------
    # EXCEL
    # --------------------------------------------------------

    if filename.endswith(".xlsx"):

        tables = read_excel(content)

        return convert_tables(tables)

    # --------------------------------------------------------
    # CSV ZIP
    # --------------------------------------------------------

    if filename.endswith(".zip"):

        tables = read_csv_zip(content)

        return convert_tables(tables)

    # --------------------------------------------------------
    # SINGLE CSV
    # --------------------------------------------------------

    if filename.endswith(".csv"):

        raise ValueError(
            "A single CSV contains only one table. "
            "Upload a ZIP containing six CSV files."
        )

    raise ValueError(
        "Unsupported file format. "
        "Use .xlsx, .json or .zip."
    )
