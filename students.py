# ==========================================
# SMART EXAM SCHEDULER
# Student Enrollment Data Generator
# ==========================================

import random


def generate_students(exams):

    # Make generated data reproducible
    random.seed(42)

    students = {}

    # Identify every academic program
    programs = set()

    for exam in exams.values():
        for program in exam["programs"]:
            programs.add(program)

    # Create 260 students for each program
    student_id = 1000

    for program in sorted(programs):

        for i in range(260):

            students[str(student_id)] = {
                "program": program,
                "courses": []
            }

            student_id += 1

    # Register students in courses
    for course_code, exam in exams.items():

        required_students = exam["students"]

        # Students from programs associated
        # with this course
        preferred_students = [
            sid
            for sid, student in students.items()
            if student["program"] in exam["programs"]
        ]

        # Students from other programs who
        # might take this course as an elective
        other_students = [
            sid
            for sid, student in students.items()
            if student["program"] not in exam["programs"]
        ]

        # Reserve 10% for cross-program enrollment
        elective_count = int(required_students * 0.10)

        regular_count = required_students - elective_count

        # Randomly select registered students
        selected_regular = random.sample(
            preferred_students,
            regular_count
        )

        selected_electives = random.sample(
            other_students,
            elective_count
        )

        selected_students = (
            selected_regular + selected_electives
        )

        # Add the course to each student's record
        for sid in selected_students:
            students[sid]["courses"].append(course_code)

    return students