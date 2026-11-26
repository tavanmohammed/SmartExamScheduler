
"""
Smart Exam Scheduler
Controlled Experimental Dataset Generator

Generates:
- Examinations
- Students and registrations
- Departments and programs
- Professors
- Rooms
- Time slots
- Student conflict graph

Scenarios:
- normal
- restricted
- dense_conflicts
- impossible

Teaching Assistant scheduling has been removed.
"""

import random

from conflicts import (
    get_course_students,
    generate_conflicts,
)

from professors import generate_professors


# ============================================================
# DATASET CONFIGURATIONS
# ============================================================

# (exams, students, rooms, time slots)

PRESETS = {
    "small": (10, 500, 5, 10),
    "medium": (30, 1500, 10, 15),
    "large": (60, 3000, 15, 20),
    "very_large": (100, 5000, 20, 30),
    "extreme": (200, 10000, 30, 42),
}


# ============================================================
# UNIVERSITY PROGRAMS
# ============================================================

PROGRAMS = {
    "Engineering": [
        "Software Engineering",
        "Electrical Engineering",
        "Mechanical Engineering",
    ],
    "Science": [
        "Mathematics",
        "Computer Science",
        "Physics",
    ],
    "Business": [
        "Commerce",
        "Accounting",
        "Finance",
    ],
}

ACADEMIC_YEARS = [1, 2, 3, 4]


# ============================================================
# MAIN DATASET GENERATOR
# ============================================================

def generate_dataset(
    size="small",
    seed=42,
    scenario="normal",
):

    # --------------------------------------------------------
    # VALIDATE SETTINGS
    # --------------------------------------------------------

    if size not in PRESETS:
        raise ValueError("Unknown dataset size")

    if scenario not in {
        "normal",
        "restricted",
        "dense_conflicts",
        "impossible",
    }:
        raise ValueError("Unknown scenario")

    rng = random.Random(seed)

    n_exams, n_students, n_rooms, n_slots = (
        PRESETS[size]
    )

    exams = {}
    rooms = {}
    students = {}
    time_slots = []

    # A known-feasible schedule is constructed first.
    # It is used only to generate the dataset.
    # It is not given to the CSP solver.

    witness = {}

    # ========================================================
    # 1. GENERATE TIME SLOTS
    # ========================================================

    for index in range(n_slots):

        time_slots.append({
            "day": f"Day {index // 2 + 1}",
            "time": (
                "09:00"
                if index % 2 == 0
                else "13:00"
            ),
        })

    all_days = list(dict.fromkeys(
        slot["day"]
        for slot in time_slots
    ))

    # ========================================================
    # 2. GENERATE ROOMS
    # ========================================================

    for i in range(n_rooms):

        capacity = rng.randint(80, 250)

        rooms[f"ROOM_{i + 1:03d}"] = {
            "capacity": capacity + 30,
            "exam_capacity": capacity,
            "room_type": "classroom",
            "unavailable_slots": [],
        }

    # ========================================================
    # 3. GENERATE STUDENT POPULATION
    # ========================================================

    department_names = list(PROGRAMS)

    for i in range(n_students):

        department = rng.choice(
            department_names
        )

        program = rng.choice(
            PROGRAMS[department]
        )

        year = rng.choice(
            ACADEMIC_YEARS
        )

        students[f"S{i + 1:05d}"] = {
            "department": department,
            "program": program,
            "year": year,
            "courses": [],
        }

    # ========================================================
    # 4. ACTIVE STUDENT POOL
    # ========================================================

    student_ids = list(students)

    active_students = student_ids

    # Fewer active students create more
    # shared registrations and conflicts.

    if scenario == "dense_conflicts":

        active_students = rng.sample(
            student_ids,
            max(1, n_students // 2),
        )

    # ========================================================
    # 5. AVAILABLE ROOM / SLOT POSITIONS
    # ========================================================

    available_positions = [
        (slot, room_id)
        for slot in range(n_slots)
        for room_id in rooms
    ]

    rng.shuffle(available_positions)

    # Tracks the days on which each
    # professor has an exam.

    professor_days = {}

    # ========================================================
    # 6. STUDENT DAILY EXAM TRACKING
    # ========================================================

    occupied_students = {
        day: set()
        for day in all_days
    }

    # ========================================================
    # 7. GENERATE EXAMINATIONS
    # ========================================================

    for i in range(n_exams):

        exam_id = f"EXAM_{i + 1:03d}"

        department = rng.choice(
            department_names
        )

        program = rng.choice(
            PROGRAMS[department]
        )

        academic_year = rng.choice(
            ACADEMIC_YEARS
        )

        selected_position = None

        # ----------------------------------------------------
        # FIND A FEASIBLE ROOM AND SLOT
        # ----------------------------------------------------

        for index, position in enumerate(
            available_positions
        ):

            slot, room_id = position

            day = time_slots[slot]["day"]

            available_students = [
                sid
                for sid in active_students
                if sid not in occupied_students[day]
            ]

            if len(available_students) >= 25:

                selected_position = (
                    index,
                    slot,
                    room_id,
                    available_students,
                )

                break

        if selected_position is None:
            raise RuntimeError(
                "Unable to construct feasible dataset "
                "under the student daily exam limit."
            )

        (
            index,
            slot,
            room_id,
            available_students,
        ) = selected_position

        available_positions.pop(index)

        day = time_slots[slot]["day"]

        # ====================================================
        # 8. ASSIGN PROFESSOR
        # ====================================================

        # A professor may supervise at most
        # one examination per day.

        eligible_professors = [
            professor_id
            for professor_id, assigned_days
            in professor_days.items()
            if day not in assigned_days
        ]

        if (
            eligible_professors
            and rng.random() < 0.7
        ):
            professor_id = rng.choice(
                eligible_professors
            )

        else:

            professor_id = (
                f"P{len(professor_days) + 1:03d}"
            )

            professor_days[professor_id] = set()

        professor_days[professor_id].add(day)

        # ====================================================
        # 9. GENERATE COURSE ENROLLMENT
        # ====================================================

        max_enrollment = min(
            rooms[room_id]["exam_capacity"],
            len(available_students),
            100,
        )

        enrollment = rng.randint(
            min(25, max_enrollment),
            max_enrollment,
        )

        # Prefer students from the selected
        # program and academic year.

        preferred_students = [
            sid
            for sid in available_students
            if students[sid]["program"] == program
            and students[sid]["year"] == academic_year
        ]

        preferred_set = set(
            preferred_students
        )

        other_students = [
            sid
            for sid in available_students
            if sid not in preferred_set
        ]

        rng.shuffle(preferred_students)
        rng.shuffle(other_students)

        selected_students = (
            preferred_students[:enrollment]
        )

        remaining_enrollment = (
            enrollment - len(selected_students)
        )

        if remaining_enrollment > 0:

            selected_students.extend(
                other_students[:remaining_enrollment]
            )

        # ====================================================
        # 10. REGISTER STUDENTS
        # ====================================================

        for sid in selected_students:

            students[sid]["courses"].append(
                exam_id
            )

            # This student may not take another
            # exam on this day in the witness.

            occupied_students[day].add(sid)

        # ====================================================
        # 11. SAVE EXAMINATION
        # ====================================================

        exams[exam_id] = {
            "course_code": (
                f"COURSE_{i + 1:03d}"
            ),

            "name": (
                f"University Exam {i + 1}"
            ),

            "department": department,

            "programs": PROGRAMS[department],

            "primary_program": program,

            "year": academic_year,

            "professor_id": professor_id,

            "students": enrollment,

            "duration": 180,

            "room_type": "classroom",
        }

        # Two-value assignment.
        witness[exam_id] = (
            slot,
            room_id,
        )

    # ========================================================
    # 12. GENERATE PROFESSOR RECORDS
    # ========================================================

    professors = generate_professors(
        exams,
        time_slots,
        seed,
    )

    # Ensure every professor is available at
    # their assigned witness examination.
    #
    # This matters because the witness is used
    # to establish initial dataset feasibility.

    for exam_id, assignment in witness.items():

        slot, _ = assignment
        professor_id = exams[exam_id]["professor_id"]

        professor = professors[professor_id]
        day = time_slots[slot]["day"]

        professor["unavailable_days"] = [
            unavailable_day
            for unavailable_day in professor.get(
                "unavailable_days", []
            )
            if unavailable_day != day
        ]

        professor["unavailable_slots"] = [
            unavailable_slot
            for unavailable_slot in professor.get(
                "unavailable_slots", []
            )
            if unavailable_slot != slot
        ]

        if professor.get("available_slots") is not None:

            allowed = set(
                professor["available_slots"]
            )

            allowed.add(slot)

            professor["available_slots"] = sorted(
                allowed
            )

    # ========================================================
    # 13. RESTRICTED SCENARIO
    # ========================================================

    if scenario == "restricted":

        used_room_slots = {
            room_id: set()
            for room_id in rooms
        }

        used_professor_days = {
            professor_id: set()
            for professor_id in professors
        }

        for exam_id, assignment in witness.items():

            # Two-value assignment:
            slot, room_id = assignment

            professor_id = exams[
                exam_id
            ]["professor_id"]

            used_room_slots[room_id].add(
                slot
            )

            used_professor_days[
                professor_id
            ].add(
                time_slots[slot]["day"]
            )

            # Restrict exam availability,
            # but preserve its witness slot.

            exams[exam_id]["unavailable_slots"] = [
                other_slot
                for other_slot in range(n_slots)
                if other_slot != slot
                and rng.random() < 0.5
            ]

        # ----------------------------------------------------
        # RESTRICT ROOM AVAILABILITY
        # ----------------------------------------------------

        for room_id, room in rooms.items():

            room["unavailable_slots"] = [
                slot
                for slot in range(n_slots)
                if slot not in used_room_slots[room_id]
                and rng.random() < 0.5
            ]

        # ----------------------------------------------------
        # RESTRICT PROFESSOR AVAILABILITY
        # ----------------------------------------------------

        for professor_id, professor in (
            professors.items()
        ):

            professor["unavailable_days"] = [
                day
                for day in all_days
                if day not in used_professor_days[
                    professor_id
                ]
                and rng.random() < 0.5
            ]

    # ========================================================
    # 14. IMPOSSIBLE SCENARIO
    # ========================================================

    elif scenario == "impossible":

        first_exam = next(
            iter(exams)
        )

        # Force the first exam to have
        # an empty scheduling domain.

        exams[first_exam]["available_slots"] = []

    # ========================================================
    # 15. BUILD STUDENT CONFLICT GRAPH
    # ========================================================

    course_students = get_course_students(
        students
    )

    conflicts = generate_conflicts(
        exams,
        course_students,
    )

    # ========================================================
    # 16. RETURN UNIVERSITY DATA
    # ========================================================

    data = {
        "departments": PROGRAMS,
        "exams": exams,
        "rooms": rooms,
        "time_slots": time_slots,
        "students": students,
        "professors": professors,
    }

    return data, conflicts, witness
