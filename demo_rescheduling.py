# Demonstrate intelligent schedule repair

from university_data import get_university_data

from conflicts import (
    get_course_students,
    generate_conflicts
)

from algorithm_selector import run_algorithm

from rescheduling import repair_schedule

from validator import validate_schedule


data = get_university_data()

conflicts = generate_conflicts(
    data["exams"],
    get_course_students(data["students"])
)

original = run_algorithm(
    "MRV + Forward Checking",
    data,
    conflicts
)

if original["success"]:

    schedule = original["schedule"]

    exam_id = "ENG-MATH101"

    slot, room, tas = schedule[exam_id]

    # Simulate a room cancellation.
    data["rooms"][room].setdefault(
        "unavailable_slots", []
    ).append(slot)

    repaired = repair_schedule(
        data["exams"],
        data["rooms"],
        data["time_slots"],
        conflicts,
        schedule,
        professors=data["professors"],
        teaching_assistants=data[
            "teaching_assistants"
        ]
    )

    print("Status:", repaired["status"])

    print(
        "Changed exams:",
        repaired["changed_exams"]
    )

    print(
        "Moved exams:",
        repaired["moved_exams"]
    )

    print(
        "Preserved exams:",
        repaired["preserved_exams"]
    )

    for change in repaired["changes"]:

        print(change)

    if repaired["success"]:

        print(
            validate_schedule(
                data["exams"],
                data["rooms"],
                data["time_slots"],
                data["students"],
                repaired["schedule"],
                data["professors"],
                data["teaching_assistants"]
            )
        )