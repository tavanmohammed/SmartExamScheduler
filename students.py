# Synthetic student enrollment generator

import random


def generate_students(
    exams,
    students_per_program=260,
    elective_rate=0.10,
    seed=42
):

    if students_per_program < 0:
        raise ValueError("Invalid student population")

    if not 0 <= elective_rate <= 1:
        raise ValueError("Elective rate must be between 0 and 1")

    rng = random.Random(seed)

    students = {}

    programs = {
        program
        for exam in exams.values()
        for program in exam["programs"]
    }

    student_id = 1000

    # Create students for every academic program.
    for program in sorted(programs):

        for _ in range(students_per_program):

            students[str(student_id)] = {
                "program": program,
                "courses": []
            }

            student_id += 1

    # Register students in examinations.
    for exam_id, exam in exams.items():

        required = exam["students"]

        if not 0 <= required <= len(students):
            raise ValueError(
                f"Invalid enrollment for {exam_id}"
            )

        preferred = [
            sid
            for sid, student in students.items()
            if student["program"] in exam["programs"]
        ]

        others = [
            sid
            for sid, student in students.items()
            if student["program"] not in exam["programs"]
        ]

        elective_count = min(
            int(required * elective_rate),
            len(others)
        )

        regular_count = min(
            required - elective_count,
            len(preferred)
        )

        selected = rng.sample(
            preferred,
            regular_count
        )

        selected += rng.sample(
            others,
            elective_count
        )

        remaining = required - len(selected)

        if remaining:

            selected_set = set(selected)

            available = [
                sid
                for sid in students
                if sid not in selected_set
            ]

            selected += rng.sample(
                available,
                remaining
            )

        for sid in selected:

            students[sid]["courses"].append(exam_id)

    return students


if __name__ == "__main__":

    from university_data import exams

    students = generate_students(
        exams,
        students_per_program=10
    )

    print("Total students:", len(students))