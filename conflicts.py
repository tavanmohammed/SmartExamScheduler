# ==========================================
# SMART EXAM SCHEDULER
# Exam Conflict Detection
# ==========================================


def get_course_students(students):

    course_students = {}

    for student_id, information in students.items():

        for course in information["courses"]:

            if course not in course_students:
                course_students[course] = set()

            course_students[course].add(student_id)

    return course_students


# ==========================================
# CHECK WHETHER TWO EXAMS CONFLICT
# ==========================================

def check_conflict(course1, course2, course_students):

    students1 = course_students.get(course1, set())

    students2 = course_students.get(course2, set())

    common_students = students1.intersection(students2)

    if len(common_students) > 0:
        return True

    return False


# ==========================================
# GENERATE ALL EXAM CONFLICTS
# ==========================================

def generate_conflicts(exams, course_students):

    conflicts = {}

    course_codes = list(exams.keys())

    for course in course_codes:
        conflicts[course] = []

    for i in range(len(course_codes)):

        for j in range(i + 1, len(course_codes)):

            course1 = course_codes[i]
            course2 = course_codes[j]

            if check_conflict(
                course1,
                course2,
                course_students
            ):

                conflicts[course1].append(course2)

                conflicts[course2].append(course1)

    return conflicts