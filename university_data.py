
"""
SMART EXAM SCHEDULER
Sample University Data

Contains:
- Departments and programs
- Courses and examinations
- Students and their course registrations
- Professors and their availability
- Examination rooms
- Examination time slots

No Teaching Assistant information.

Each examination is assigned:
    (time_slot_index, room_id)
"""

from copy import deepcopy


# ============================================================
# DEPARTMENTS AND PROGRAMS
# ============================================================

departments = {
    "Engineering": [
        "Software Engineering",
        "Electrical Engineering",
    ],
    "Science": [
        "Mathematics",
        "Computer Science",
    ],
    "Business": [
        "Commerce",
        "Accounting",
    ],
}


# ============================================================
# EXAMINATION DAYS AND TIME SLOTS
# ============================================================

days = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
]

times = [
    "09:00",
    "13:00",
]

time_slots = [
    {"day": day, "time": start_time}
    for day in days
    for start_time in times
]


# ============================================================
# PROFESSORS
# ============================================================

professors = {
    "P001": {
        "name": "Dr. Ahmed",
        "departments": ["Engineering", "Science"],
        "unavailable_days": ["Monday"],
        "unavailable_slots": [],
        "preferred_days": ["Tuesday", "Wednesday"],
        "preferred_slots": [2, 4],
        "avoid_days": ["Friday"],
    },

    "P002": {
        "name": "Dr. Sara",
        "departments": ["Engineering"],
        "unavailable_days": [],
        "unavailable_slots": [1],
        "preferred_days": ["Monday"],
        "preferred_slots": [0],
        "avoid_days": [],
    },

    "P003": {
        "name": "Dr. David",
        "departments": ["Science"],
        "unavailable_days": ["Wednesday"],
        "unavailable_slots": [],
        "preferred_days": ["Thursday"],
        "preferred_slots": [6],
        "avoid_days": [],
    },

    "P004": {
        "name": "Dr. Maria",
        "departments": ["Business"],
        "unavailable_days": [],
        "unavailable_slots": [],
        "preferred_days": ["Friday"],
        "preferred_slots": [8],
        "avoid_days": [],
    },
}


# ============================================================
# COURSES AND EXAMINATIONS
# ============================================================

exams = {
    "ENG-MATH101": {
        "course_code": "MATH101",
        "name": "Engineering Mathematics",
        "department": "Engineering",
        "programs": [
            "Software Engineering",
            "Electrical Engineering",
        ],
        "professor_id": "P001",
        "students": 3,
        "duration": 180,
        "room_type": "classroom",
    },

    "ENG-SOFE301": {
        "course_code": "SOFE301",
        "name": "Database Systems",
        "department": "Engineering",
        "programs": [
            "Software Engineering",
        ],
        "professor_id": "P002",
        "students": 2,
        "duration": 180,
        "room_type": "classroom",
    },

    "ENG-SOFE302": {
        "course_code": "SOFE302",
        "name": "Algorithms",
        "department": "Engineering",
        "programs": [
            "Software Engineering",
        ],
        "professor_id": "P002",
        "students": 2,
        "duration": 180,
        "room_type": "classroom",
    },

    "SCI-MATH101": {
        "course_code": "MATH101",
        "name": "Science Mathematics",
        "department": "Science",
        "programs": [
            "Mathematics",
            "Computer Science",
        ],
        "professor_id": "P001",
        "students": 2,
        "duration": 180,
        "room_type": "classroom",
    },

    "SCI-CSCI301": {
        "course_code": "CSCI301",
        "name": "Artificial Intelligence",
        "department": "Science",
        "programs": [
            "Computer Science",
        ],
        "professor_id": "P003",
        "students": 2,
        "duration": 180,
        "room_type": "laboratory",
    },

    "BUS-BUSI101": {
        "course_code": "BUSI101",
        "name": "Business Mathematics",
        "department": "Business",
        "programs": [
            "Commerce",
        ],
        "professor_id": "P004",
        "students": 2,
        "duration": 180,
        "room_type": "classroom",
    },

    "BUS-BUSI201": {
        "course_code": "BUSI201",
        "name": "Financial Accounting",
        "department": "Business",
        "programs": [
            "Commerce",
            "Accounting",
        ],
        "professor_id": "P004",
        "students": 2,
        "duration": 180,
        "room_type": "classroom",
    },
}


# ============================================================
# STUDENTS AND COURSE REGISTRATIONS
# ============================================================

students = {
    "S001": {
        "department": "Engineering",
        "program": "Software Engineering",
        "courses": [
            "ENG-MATH101",
            "ENG-SOFE301",
            "ENG-SOFE302",
        ],
    },

    "S002": {
        "department": "Engineering",
        "program": "Software Engineering",
        "courses": [
            "ENG-MATH101",
            "ENG-SOFE301",
            "SCI-CSCI301",
        ],
    },

    "S003": {
        "department": "Engineering",
        "program": "Electrical Engineering",
        "courses": [
            "ENG-MATH101",
            "ENG-SOFE302",
        ],
    },

    "S004": {
        "department": "Science",
        "program": "Computer Science",
        "courses": [
            "SCI-MATH101",
            "SCI-CSCI301",
        ],
    },

    "S005": {
        "department": "Science",
        "program": "Mathematics",
        "courses": [
            "SCI-MATH101",
        ],
    },

    "S006": {
        "department": "Business",
        "program": "Commerce",
        "courses": [
            "BUS-BUSI101",
            "BUS-BUSI201",
        ],
    },

    "S007": {
        "department": "Business",
        "program": "Accounting",
        "courses": [
            "BUS-BUSI101",
            "BUS-BUSI201",
        ],
    },
}


# ============================================================
# EXAMINATION ROOMS
# ============================================================

rooms = {
    "ROOM_A": {
        "capacity": 100,
        "exam_capacity": 70,
        "room_type": "classroom",
        "unavailable_slots": [],
    },

    "ROOM_B": {
        "capacity": 150,
        "exam_capacity": 100,
        "room_type": "classroom",
        "unavailable_slots": [0],
    },

    "ROOM_C": {
        "capacity": 200,
        "exam_capacity": 150,
        "room_type": "classroom",
        "unavailable_slots": [],
    },

    "LAB_A": {
        "capacity": 60,
        "exam_capacity": 40,
        "room_type": "laboratory",
        "unavailable_slots": [1],
    },
}


# ============================================================
# GET UNIVERSITY DATA
# ============================================================

def get_university_data():
    """
    Return independent copies of all university data.

    Prevents scheduling algorithms from accidentally
    modifying the original sample dataset.
    """

    return deepcopy({
        "departments": departments,
        "exams": exams,
        "rooms": rooms,
        "time_slots": time_slots,
        "students": students,
        "professors": professors,
    })


# ============================================================
# DISPLAY SAMPLE DATA SUMMARY
# ============================================================

if __name__ == "__main__":

    university = get_university_data()

    print("SMART EXAM SCHEDULER")
    print("----------------------------")

    print(
        "Departments:",
        len(university["departments"])
    )

    print(
        "Programs:",
        sum(
            len(programs)
            for programs
            in university["departments"].values()
        )
    )

    print(
        "Professors:",
        len(university["professors"])
    )

    print(
        "Exams:",
        len(university["exams"])
    )

    print(
        "Students:",
        len(university["students"])
    )

    print(
        "Rooms:",
        len(university["rooms"])
    )

    print(
        "Time Slots:",
        len(university["time_slots"])
    )

    print(
        "Course Registrations:",
        sum(
            len(student["courses"])
            for student in university["students"].values()
        )
    )
