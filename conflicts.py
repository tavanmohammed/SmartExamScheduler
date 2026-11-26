# Student conflict graph


def get_course_students(students):

    course_students = {}

    for student_id, student in students.items():

        for course in student["courses"]:

            course_students.setdefault(
                course,
                set()
            ).add(student_id)

    return course_students


def check_conflict(
    course1,
    course2,
    course_students
):

    students1 = course_students.get(
        course1,
        set()
    )

    students2 = course_students.get(
        course2,
        set()
    )

    return not students1.isdisjoint(students2)


def generate_conflicts(
    exams,
    course_students
):

    conflicts = {
        exam_id: []
        for exam_id in exams
    }

    exam_ids = list(exams)

    for i in range(len(exam_ids)):

        for j in range(i + 1, len(exam_ids)):

            exam1 = exam_ids[i]
            exam2 = exam_ids[j]

            if check_conflict(
                exam1,
                exam2,
                course_students
            ):

                conflicts[exam1].append(exam2)
                conflicts[exam2].append(exam1)

    return conflicts


def conflict_density(conflicts):

    n = len(conflicts)

    if n < 2:
        return 0.0

    edges = sum(
        len(neighbors)
        for neighbors in conflicts.values()
    )

    return edges / (n * (n - 1))


if __name__ == "__main__":

    from university_data import exams, students

    course_students = get_course_students(students)

    conflicts = generate_conflicts(
        exams,
        course_students
    )

    for exam_id, neighbors in conflicts.items():

        print(exam_id, ":", neighbors)