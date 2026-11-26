
# ============================================================
# SMART EXAM SCHEDULER - API INPUT VALIDATION
# ============================================================
#
# Supports:
# - Students and course registrations
# - Departments and programs
# - Professors and their availability
# - Examinations
# - Rooms and their availability
# - Scheduling and rescheduling requests
# - Dataset generation
# - Preference optimization
#
# Teaching Assistants have been removed.
#
# Assignment format:
#     exam_id: (slot_index, room_id)
# ============================================================

from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    StrictStr,
    model_validator,
)


# ============================================================
# SUPPORTED AI ALGORITHMS
# ============================================================

AlgorithmName = Literal[
    "Auto",
    "Basic Backtracking",
    "MRV",
    "Forward Checking",
    "MRV + Forward Checking",
    "MRV + FC + LCV",
    "MRV + FC + Degree",
    "MRV + FC + Degree + Adaptive LCV",
]


DatasetSize = Literal[
    "small",
    "medium",
    "large",
    "very_large",
    "extreme",
]


DatasetScenario = Literal[
    "normal",
    "restricted",
    "dense_conflicts",
    "impossible",
]


# ============================================================
# UNIVERSITY PROBLEM VALIDATION
# ============================================================

def validate_problem(data):

    exams = data["exams"]
    rooms = data["rooms"]
    students = data["students"]
    slots = data["time_slots"]

    professors = data.get("professors", {})
    departments = data.get("departments", {})

    # --------------------------------------------------------
    # BASIC DATA VALIDATION
    # --------------------------------------------------------

    if not exams:
        raise ValueError(
            "At least one examination is required"
        )

    if not rooms:
        raise ValueError(
            "At least one examination room is required"
        )

    if not slots:
        raise ValueError(
            "At least one time slot is required"
        )

    # --------------------------------------------------------
    # RESOURCE IDENTIFIERS
    # --------------------------------------------------------

    for group_name, records in [
        ("examination", exams),
        ("room", rooms),
        ("student", students),
        ("professor", professors),
    ]:

        for record_id in records:

            if (
                not isinstance(record_id, str)
                or not record_id.strip()
            ):

                raise ValueError(
                    f"Invalid {group_name} ID"
                )

    # --------------------------------------------------------
    # DEPARTMENTS AND PROGRAMS
    # --------------------------------------------------------

    if not isinstance(departments, dict):
        raise ValueError(
            "Departments must be a dictionary"
        )

    for department, programs in departments.items():

        if (
            not isinstance(department, str)
            or not department.strip()
        ):
            raise ValueError(
                "Invalid department name"
            )

        if not isinstance(programs, list):
            raise ValueError(
                f"Invalid programs for {department}"
            )

        if any(
            not isinstance(program, str)
            or not program.strip()
            for program in programs
        ):
            raise ValueError(
                f"Invalid program in {department}"
            )

    # ========================================================
    # TIME SLOT VALIDATION
    # ========================================================

    daily_times = {}

    for index, slot in enumerate(slots):

        day = slot.get("day")
        time_value = slot.get("time")

        if (
            not isinstance(day, str)
            or not day.strip()
        ):
            raise ValueError(
                f"Invalid examination day: slot {index}"
            )

        if not isinstance(time_value, str):
            raise ValueError(
                f"Invalid time format: slot {index}"
            )

        try:

            hour, minute = map(
                int,
                time_value.split(":")
            )

        except (ValueError, AttributeError) as exc:

            raise ValueError(
                f"Invalid time format: slot {index}"
            ) from exc

        if not (
            0 <= hour < 24
            and 0 <= minute < 60
        ):
            raise ValueError(
                f"Invalid time: slot {index}"
            )

        start = hour * 60 + minute

        # Maximum supported examination duration.
        end = start + 180

        if end > 1440:
            raise ValueError(
                "Examination extends beyond the day"
            )

        # Prevent overlapping time slots on a day.
        for other_start in daily_times.get(day, []):

            if (
                start < other_start + 180
                and other_start < end
            ):
                raise ValueError(
                    f"Time slots overlap on {day}"
                )

        daily_times.setdefault(
            day, []
        ).append(start)

    # ========================================================
    # AVAILABILITY AND PREFERENCE REFERENCES
    # ========================================================

    for records in [
        exams,
        rooms,
        professors,
    ]:

        for record_id, record in records.items():

            for field in [
                "available_slots",
                "unavailable_slots",
                "preferred_slots",
            ]:

                if field == "available_slots":
                    values = record.get(field)

                    if values is None:
                        continue
                else:
                    values = record.get(field, [])

                if not isinstance(values, list):
                    raise ValueError(
                        f"Invalid {field}: {record_id}"
                    )

                if any(
                    type(slot) is not int
                    or not 0 <= slot < len(slots)
                    for slot in values
                ):
                    raise ValueError(
                        f"Invalid slot in "
                        f"{field}: {record_id}"
                    )

            for field in [
                "unavailable_days",
                "preferred_days",
                "avoid_days",
            ]:

                values = record.get(field, [])

                if not isinstance(values, list):
                    raise ValueError(
                        f"Invalid {field}: {record_id}"
                    )

                if any(
                    not isinstance(day, str)
                    or day not in daily_times
                    for day in values
                ):
                    raise ValueError(
                        f"Unknown day in "
                        f"{field}: {record_id}"
                    )

    # ========================================================
    # STUDENT ENROLLMENT VALIDATION
    # ========================================================

    enrollment = {
        exam_id: 0
        for exam_id in exams
    }

    for student_id, student in students.items():

        courses = student.get("courses")

        if not isinstance(courses, list):
            raise ValueError(
                f"Invalid courses: {student_id}"
            )

        if any(
            not isinstance(course, str)
            or not course.strip()
            for course in courses
        ):
            raise ValueError(
                f"Invalid course ID: {student_id}"
            )

        if len(courses) != len(set(courses)):
            raise ValueError(
                f"Duplicate courses: {student_id}"
            )

        # Validate optional academic-year information.
        year = student.get("year")

        if year is not None and (
            type(year) is not int
            or not 1 <= year <= 4
        ):
            raise ValueError(
                f"Invalid academic year: {student_id}"
            )

        for course in courses:

            if course not in exams:
                raise ValueError(
                    f"Unknown exam {course}: {student_id}"
                )

            enrollment[course] += 1

    # ========================================================
    # EXAMINATION VALIDATION
    # ========================================================

    for exam_id, exam in exams.items():

        count = exam.get("students")

        if (
            type(count) is not int
            or count < 0
        ):
            raise ValueError(
                f"Invalid enrollment: {exam_id}"
            )

        if count != enrollment[exam_id]:
            raise ValueError(
                f"Enrollment mismatch: {exam_id}. "
                f"Expected {enrollment[exam_id]}, "
                f"received {count}"
            )

        # ----------------------------------------------------
        # PROFESSOR ASSIGNMENT
        # ----------------------------------------------------

        professor_id = exam.get("professor_id")

        if (
            not isinstance(professor_id, str)
            or professor_id not in professors
        ):
            raise ValueError(
                f"Unknown professor: {exam_id}"
            )

        # ----------------------------------------------------
        # EXAMINATION DURATION
        # ----------------------------------------------------

        duration = exam.get("duration", 180)

        if (
            type(duration) is not int
            or not 1 <= duration <= 180
        ):
            raise ValueError(
                f"Invalid exam duration: {exam_id}"
            )

        # ----------------------------------------------------
        # DEPARTMENT
        # ----------------------------------------------------

        department = exam.get("department")

        if (
            not isinstance(department, str)
            or not department.strip()
        ):
            raise ValueError(
                f"Invalid department: {exam_id}"
            )

        # ----------------------------------------------------
        # PROGRAMS
        # ----------------------------------------------------

        programs = exam.get("programs", [])

        if (
            not isinstance(programs, list)
            or any(
                not isinstance(program, str)
                or not program.strip()
                for program in programs
            )
        ):
            raise ValueError(
                f"Invalid programs: {exam_id}"
            )

        # ----------------------------------------------------
        # ROOM TYPE
        # ----------------------------------------------------

        room_type = exam.get("room_type")

        if room_type is not None:

            if (
                not isinstance(room_type, str)
                or not room_type.strip()
            ):
                raise ValueError(
                    f"Invalid room type: {exam_id}"
                )

    # ========================================================
    # ROOM VALIDATION
    # ========================================================

    for room_id, room in rooms.items():

        capacity = room.get(
            "exam_capacity",
            room.get("capacity")
        )

        if (
            type(capacity) is not int
            or capacity < 0
        ):
            raise ValueError(
                f"Invalid room capacity: {room_id}"
            )

        physical = room.get(
            "capacity",
            capacity
        )

        if (
            type(physical) is not int
            or physical < capacity
        ):
            raise ValueError(
                f"Invalid physical capacity: {room_id}"
            )

        room_type = room.get("room_type")

        if room_type is not None:

            if (
                not isinstance(room_type, str)
                or not room_type.strip()
            ):
                raise ValueError(
                    f"Invalid room type: {room_id}"
                )

    return data


# ============================================================
# UNIVERSITY DATA MODEL
# ============================================================

class UniversityData(BaseModel):

    model_config = ConfigDict(extra="ignore")

    departments: dict = Field(
        default_factory=dict
    )

    exams: dict[str, dict]

    rooms: dict[str, dict]

    time_slots: list[dict]

    students: dict[str, dict]

    professors: dict[str, dict]

    @model_validator(mode="after")
    def check_problem(self):

        validate_problem(
            self.model_dump()
        )

        return self


# ============================================================
# GENERATE SCHEDULE REQUEST
# ============================================================

class ScheduleRequest(BaseModel):

    data: UniversityData

    algorithm: AlgorithmName = "Auto"

    timeout_seconds: float = Field(
        default=30,
        ge=0,
        le=300,
        allow_inf_nan=False
    )


# ============================================================
# COMPARE ALGORITHMS REQUEST
# ============================================================

class CompareRequest(BaseModel):

    data: UniversityData

    timeout_seconds: float = Field(
        default=10,
        ge=0,
        le=60,
        allow_inf_nan=False
    )


# ============================================================
# DATASET GENERATION REQUEST
# ============================================================

class DatasetRequest(BaseModel):

    size: DatasetSize = "small"

    seed: int = 42

    scenario: DatasetScenario = "normal"


# ============================================================
# INTELLIGENT RESCHEDULING REQUEST
# ============================================================

class RepairRequest(BaseModel):

    data: UniversityData

    # New format: (slot_index, room_id)
    original_schedule: dict[
        str,
        tuple[
            StrictInt,
            StrictStr
        ]
    ]

    timeout_seconds: float = Field(
        default=30,
        ge=0,
        le=300,
        allow_inf_nan=False
    )

    @model_validator(mode="after")
    def check_original_schedule(self):

        expected_exams = set(
            self.data.exams
        )

        scheduled_exams = set(
            self.original_schedule
        )

        missing = expected_exams - scheduled_exams
        unknown = scheduled_exams - expected_exams

        if missing:
            raise ValueError(
                "Original schedule is missing exams: "
                f"{sorted(missing)}"
            )

        if unknown:
            raise ValueError(
                "Original schedule contains unknown exams: "
                f"{sorted(unknown)}"
            )

        for exam_id, assignment in (
            self.original_schedule.items()
        ):

            slot, room = assignment

            if not (
                0 <= slot < len(self.data.time_slots)
            ):
                raise ValueError(
                    f"Invalid original slot: {exam_id}"
                )

            if not room.strip():
                raise ValueError(
                    f"Invalid original room: {exam_id}"
                )

            if room not in self.data.rooms:
                raise ValueError(
                    f"Unknown original room: {exam_id}"
                )

        return self


# ============================================================
# PREFERENCE OPTIMIZATION REQUEST
# ============================================================

class PreferenceRequest(BaseModel):

    data: UniversityData

    weights: dict[str, StrictInt] = Field(
        default_factory=dict
    )

    timeout_seconds: float = Field(
        default=30,
        ge=0,
        le=300,
        allow_inf_nan=False
    )

    @model_validator(mode="after")
    def check_weights(self):

        for preference, weight in self.weights.items():

            if not preference.strip():
                raise ValueError(
                    "Invalid preference name"
                )

            if weight < 0:
                raise ValueError(
                    "Preference weight must be "
                    f"nonnegative: {preference}"
                )

        return self
