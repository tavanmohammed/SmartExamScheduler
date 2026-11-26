
"""
SMART EXAM SCHEDULER
Manual University Data Entry

Create university scheduling datasets using
a terminal-based interface.

Features:
    - Departments and academic programs
    - Examination time slots
    - Examination rooms
    - Professors and availability
    - Professor scheduling preferences
    - Examinations
    - Students and course registrations
    - Automatic enrollment calculation
    - Pydantic input validation
    - AI timetable generation
    - Independent timetable validation
    - JSON export

Assignment format:
    exam_id -> (slot_index, room_id)

No Teaching Assistant dependencies.
"""

import json
from pathlib import Path

from schemas import UniversityData

from conflicts import (
    get_course_students,
    generate_conflicts,
)

from algorithm_selector import run_algorithm
from validator import validate_schedule
from interactive import display_schedule


BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = BASE_DIR / "custom_university.json"
OUTPUT_FILE = BASE_DIR / "custom_schedule.json"


# ============================================================
# INPUT HELPERS
# ============================================================

def ask(message, default=None):

    while True:

        suffix = (
            f" [{default}]"
            if default is not None
            else ""
        )

        value = input(
            f"{message}{suffix}: "
        ).strip()

        if value:
            return value

        if default is not None:
            return str(default)

        print("This field is required.")


def number(message, minimum=1, default=None):

    while True:

        try:

            value = int(
                ask(message, default)
            )

            if value >= minimum:
                return value

        except ValueError:
            pass

        print(
            f"Enter a whole number >= {minimum}."
        )


def choose(message, options):

    options = list(options)

    if not options:
        raise ValueError(
            "No available options."
        )

    print(
        "Available:",
        ", ".join(str(option) for option in options),
    )

    while True:

        value = ask(message)

        if value in options:
            return value

        print("Invalid selection.")


def choose_multiple(message, options):

    options = set(options)

    if not options:
        raise ValueError(
            "No available options."
        )

    print(
        "Available:",
        ", ".join(sorted(options)),
    )

    while True:

        value = ask(
            message + " (comma-separated IDs)"
        )

        selected = list(
            dict.fromkeys(
                item.strip()
                for item in value.split(",")
                if item.strip()
            )
        )

        if (
            selected
            and set(selected).issubset(options)
        ):
            return selected

        print(
            "Select one or more valid IDs."
        )


def optional_multiple(message, options):
    """
    Allow optional comma-separated selections.

    Press Enter to select none.
    """

    options = set(options)

    if not options:
        return []

    print(
        "Available:",
        ", ".join(sorted(options)),
    )

    while True:

        value = input(
            f"{message} (comma-separated, Enter for none): "
        ).strip()

        if not value:
            return []

        selected = list(
            dict.fromkeys(
                item.strip()
                for item in value.split(",")
                if item.strip()
            )
        )

        if set(selected).issubset(options):
            return selected

        print("Invalid selection.")


def unique_id(message, existing):

    while True:

        value = ask(message)

        if value not in existing:
            return value

        print(
            "This ID already exists."
        )


def select_slots(message, time_slots):
    """
    Select zero or more time-slot indices.
    """

    slot_options = [
        str(index)
        for index in range(len(time_slots))
    ]

    print("\nAvailable time slots:")

    for index, slot in enumerate(time_slots):

        print(
            f"{index}: "
            f"{slot['day']} "
            f"{slot['time']}"
        )

    selected = optional_multiple(
        message,
        slot_options,
    )

    return [
        int(index)
        for index in selected
    ]


# ============================================================
# CREATE UNIVERSITY DATA
# ============================================================

def create_university_data():

    print("\n" + "=" * 55)
    print("CREATE CUSTOM UNIVERSITY DATA")
    print("=" * 55)

    departments = {}
    exams = {}
    rooms = {}
    students = {}
    professors = {}
    time_slots = []

    # ========================================================
    # 1. DEPARTMENTS AND PROGRAMS
    # ========================================================

    print("\n--- DEPARTMENTS AND PROGRAMS ---")

    total_departments = number(
        "Number of departments"
    )

    for i in range(total_departments):

        print(f"\nDepartment {i + 1}")

        department_id = unique_id(
            "Department name/ID",
            departments,
        )

        while True:

            programs = list(
                dict.fromkeys(
                    program.strip()
                    for program in ask(
                        "Programs (comma-separated)"
                    ).split(",")
                    if program.strip()
                )
            )

            if programs:
                break

            print(
                "Enter at least one program."
            )

        departments[department_id] = programs

    # ========================================================
    # 2. EXAMINATION TIME SLOTS
    # ========================================================

    print("\n--- EXAMINATION TIME SLOTS ---")
    print(
        "Enter non-overlapping examination periods."
    )

    total_slots = number(
        "Number of examination time slots"
    )

    for index in range(total_slots):

        print(f"\nTime slot {index}")

        day = ask(
            "Examination day"
        )

        start_time = ask(
            "Start time (HH:MM)",
            "09:00",
        )

        time_slots.append({
            "day": day,
            "time": start_time,
        })

    # ========================================================
    # 3. EXAMINATION ROOMS
    # ========================================================

    print("\n--- EXAMINATION ROOMS ---")

    total_rooms = number(
        "Number of rooms"
    )

    for i in range(total_rooms):

        print(f"\nRoom {i + 1}")

        room_id = unique_id(
            "Room ID",
            rooms,
        )

        capacity = number(
            "Examination seating capacity"
        )

        room_type = ask(
            "Room type",
            "classroom",
        )

        unavailable_slots = select_slots(
            "Unavailable room slots",
            time_slots,
        )

        rooms[room_id] = {
            "capacity": capacity,
            "exam_capacity": capacity,
            "room_type": room_type,
            "unavailable_slots": unavailable_slots,
        }

    # ========================================================
    # 4. PROFESSORS
    # ========================================================

    print("\n--- PROFESSORS ---")

    total_professors = number(
        "Number of professors"
    )

    days = sorted({
        slot["day"]
        for slot in time_slots
    })

    for i in range(total_professors):

        print(f"\nProfessor {i + 1}")

        professor_id = unique_id(
            "Professor ID",
            professors,
        )

        professor_name = ask(
            "Professor name"
        )

        unavailable_days = optional_multiple(
            "Unavailable days",
            days,
        )

        unavailable_slots = select_slots(
            "Unavailable professor slots",
            time_slots,
        )

        preferred_days = optional_multiple(
            "Preferred examination days",
            days,
        )

        preferred_slots = select_slots(
            "Preferred examination slots",
            time_slots,
        )

        avoid_days = optional_multiple(
            "Days professor prefers to avoid",
            days,
        )

        professors[professor_id] = {
            "name": professor_name,
            "unavailable_days": unavailable_days,
            "unavailable_slots": unavailable_slots,
            "preferred_days": preferred_days,
            "preferred_slots": preferred_slots,
            "avoid_days": avoid_days,
        }

    # ========================================================
    # 5. EXAMINATIONS
    # ========================================================

    print("\n--- EXAMINATIONS ---")

    total_exams = number(
        "Number of examinations"
    )

    for i in range(total_exams):

        print(f"\nExamination {i + 1}")

        exam_id = unique_id(
            "Examination ID",
            exams,
        )

        exam_name = ask(
            "Examination name"
        )

        department = choose(
            "Department",
            departments,
        )

        programs = choose_multiple(
            "Programs taking this examination",
            departments[department],
        )

        professor_id = choose(
            "Professor ID",
            professors,
        )

        room_type = ask(
            "Required room type",
            "classroom",
        )

        duration = number(
            "Examination duration (minutes)",
            default=180,
        )

        exams[exam_id] = {
            "course_code": exam_id,
            "name": exam_name,
            "department": department,
            "programs": programs,
            "professor_id": professor_id,
            "students": 0,
            "duration": duration,
            "room_type": room_type,
        }

    # ========================================================
    # 6. STUDENTS AND COURSE REGISTRATIONS
    # ========================================================

    print("\n--- STUDENTS ---")

    total_students = number(
        "Number of students"
    )

    for i in range(total_students):

        print(f"\nStudent {i + 1}")

        student_id = unique_id(
            "Student ID",
            students,
        )

        department = choose(
            "Department",
            departments,
        )

        program = choose(
            "Program",
            departments[department],
        )

        while True:

            year = number(
                "Academic year (1-4)"
            )

            if year <= 4:
                break

            print(
                "Academic year must be 1, 2, 3 or 4."
            )

        courses = choose_multiple(
            "Registered examination IDs",
            exams,
        )

        students[student_id] = {
            "department": department,
            "program": program,
            "year": year,
            "courses": courses,
        }

    # ========================================================
    # 7. CALCULATE EXAMINATION ENROLLMENT
    # ========================================================

    print("\n--- EXAMINATION ENROLLMENT ---")

    for exam_id, exam in exams.items():

        enrollment = sum(
            exam_id in student["courses"]
            for student in students.values()
        )

        if enrollment == 0:

            raise ValueError(
                f"{exam_id} has no registered students."
            )

        exam["students"] = enrollment

        print(
            f"{exam_id}: {enrollment} students"
        )

    # ========================================================
    # 8. COMPLETE UNIVERSITY DATASET
    # ========================================================

    data = {
        "departments": departments,
        "exams": exams,
        "rooms": rooms,
        "time_slots": time_slots,
        "students": students,
        "professors": professors,
    }

    return UniversityData.model_validate(
        data
    ).model_dump()


# ============================================================
# SAVE / LOAD DATA
# ============================================================

def save_json(filename, data):

    path = Path(filename)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            data,
            file,
            indent=4,
        )

    print(
        f"\nSaved: {path.name}"
    )


def load_university_data():

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            "No custom university dataset found. "
            "Choose option 1 first."
        )

    with INPUT_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:

        data = json.load(file)

    return UniversityData.model_validate(
        data
    ).model_dump()


# ============================================================
# VALIDATE UNIVERSITY INPUT
# ============================================================

def validate_input(data):

    validated = UniversityData.model_validate(
        data
    )

    print(
        "\nUniversity input validation: PASSED"
    )

    return validated.model_dump()


# ============================================================
# GENERATE AI TIMETABLE
# ============================================================

def generate_schedule(data):

    data = validate_input(data)

    print("\n" + "=" * 55)
    print("AI EXAMINATION SCHEDULING")
    print("=" * 55)

    # --------------------------------------------------------
    # BUILD STUDENT CONFLICT GRAPH
    # --------------------------------------------------------

    course_students = get_course_students(
        data["students"]
    )

    conflicts = generate_conflicts(
        data["exams"],
        course_students,
    )

    # --------------------------------------------------------
    # EXECUTE SCHEDULING ALGORITHM
    # --------------------------------------------------------

    algorithm = "MRV + FC + Degree"

    print(
        "\nAlgorithm:",
        algorithm,
    )

    result = run_algorithm(
        algorithm,
        data,
        conflicts,
        timeout_seconds=30,
    )

    # --------------------------------------------------------
    # INDEPENDENT TIMETABLE VALIDATION
    # --------------------------------------------------------

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

    else:

        result["validation"] = None

    # --------------------------------------------------------
    # SAVE SCHEDULING RESULT
    # --------------------------------------------------------

    save_json(
        OUTPUT_FILE,
        result,
    )

    # --------------------------------------------------------
    # DISPLAY RESULTS
    # --------------------------------------------------------

    print("\n" + "=" * 55)
    print("AI SCHEDULING RESULTS")
    print("=" * 55)

    print(
        "Status:",
        result["status"],
    )

    print(
        "Algorithm:",
        result.get("algorithm", algorithm),
    )

    print(
        "Execution time:",
        f"{result['execution_time'] * 1000:.3f} ms",
    )

    print(
        "Assignment attempts:",
        result.get("assignments_attempted"),
    )

    print(
        "Backtracks:",
        result.get("backtracks"),
    )

    print(
        "Constraint checks:",
        result.get("constraint_checks"),
    )

    print(
        "Nodes explored:",
        result.get("nodes_explored"),
    )

    # --------------------------------------------------------
    # CHECK SCHEDULING SUCCESS
    # --------------------------------------------------------

    if not result["success"]:

        print(
            "\nNo complete timetable was generated."
        )

        print(
            "Check examination days, student conflicts, "
            "room capacities, room availability, "
            "and professor availability."
        )

        return result

    if not result["validation"]["valid"]:

        print(
            "\nGenerated timetable failed validation."
        )

        for error in result["validation"]["errors"]:
            print("-", error)

        return result

    # --------------------------------------------------------
    # SHOW VALID TIMETABLE
    # --------------------------------------------------------

    print(
        "\nVALID EXAMINATION TIMETABLE"
    )

    display_schedule(
        data,
        result["schedule"],
    )

    return result


# ============================================================
# DISPLAY UNIVERSITY SUMMARY
# ============================================================

def show_summary():

    data = load_university_data()

    print("\n" + "=" * 55)
    print("UNIVERSITY DATA SUMMARY")
    print("=" * 55)

    for key in (
        "departments",
        "exams",
        "rooms",
        "time_slots",
        "students",
        "professors",
    ):

        print(
            f"{key}: {len(data[key])}"
        )

    total_registrations = sum(
        len(student["courses"])
        for student in data["students"].values()
    )

    print(
        "Total course registrations:",
        total_registrations,
    )


# ============================================================
# MAIN MENU
# ============================================================

def main():

    while True:

        print("\n" + "=" * 55)
        print("SMART EXAM SCHEDULER")
        print("MANUAL UNIVERSITY INPUT")
        print("=" * 55)

        print("1. Create custom university data")
        print("2. Validate saved university data")
        print("3. Generate AI timetable")
        print("4. View university data summary")
        print("0. Exit")

        choice = input(
            "\nEnter your choice: "
        ).strip()

        try:

            if choice == "1":

                data = create_university_data()

                validate_input(data)

                save_json(
                    INPUT_FILE,
                    data,
                )

            elif choice == "2":

                data = load_university_data()

                validate_input(data)

            elif choice == "3":

                data = load_university_data()

                generate_schedule(data)

            elif choice == "4":

                show_summary()

            elif choice == "0":

                print(
                    "\nExiting Smart Exam Scheduler."
                )

                break

            else:

                print(
                    "\nInvalid option. Try again."
                )

        except (
            ValueError,
            KeyError,
            TypeError,
            OSError,
        ) as error:

            print(
                f"\nError: {error}"
            )

        except KeyboardInterrupt:

            print(
                "\nOperation cancelled."
            )


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
