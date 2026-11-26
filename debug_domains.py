from university_data import get_university_data

from conflicts import (
    get_course_students,
    generate_conflicts
)

from constraints import Constraints


data = get_university_data()

conflicts = generate_conflicts(
    data["exams"],
    get_course_students(data["students"])
)

rules = Constraints(
    data["exams"],
    data["rooms"],
    data["time_slots"],
    conflicts,
    data["professors"],
    data["teaching_assistants"]
)

print("\nEXAM DOMAIN ANALYSIS")
print("=" * 60)

for exam_id, exam in data["exams"].items():

    domain = rules.domain(exam_id)

    qualified_tas = [
        ta_id
        for ta_id, ta in data["teaching_assistants"].items()
        if exam_id in ta["qualified_courses"]
        and exam["department"] in ta["departments"]
    ]

    print("\nExam:", exam_id)

    print("Required TAs:", exam["required_tas"])

    print("Qualified TAs:", qualified_tas)

    print("Number of qualified TAs:", len(qualified_tas))

    print("Domain size:", len(domain))

    if not domain:

        print("ERROR: No valid assignments available")

    else:

        print("STATUS: Valid domain")

        