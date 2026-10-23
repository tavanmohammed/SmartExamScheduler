# ==========================================
# SMART EXAM SCHEDULER
# Backtracking Test
# ==========================================

from backtracking import basic_backtracking


# ==========================================
# DEFINE TWO EXAMS
# ==========================================

test_exams = {

    "MATH101": {
        "name": "Mathematics",
        "students": 30
    },

    "PHYS101": {
        "name": "Engineering Physics",
        "students": 80
    }
}


# ==========================================
# DEFINE CLASSROOMS
# ==========================================

test_rooms = {

    "LARGE_HALL": {
        "capacity": 100
    },

    "SMALL_ROOM": {
        "capacity": 40
    }
}


# ==========================================
# DEFINE AVAILABLE TIME
# ==========================================

test_time_slots = [
    {
        "day": "Monday",
        "time": "9:00 AM"
    }
]


# ==========================================
# DEFINE STUDENT CONFLICTS
# ==========================================

test_conflicts = {

    "MATH101": [],
    "PHYS101": []

}


# ==========================================
# RUN BACKTRACKING
# ==========================================

result = basic_backtracking(
    test_exams,
    test_rooms,
    test_time_slots,
    test_conflicts
)


# ==========================================
# DISPLAY RESULTS
# ==========================================

print("\n===================================")
print("     BACKTRACKING TEST")
print("===================================")

if result["success"]:

    print("\nValid Schedule Found!\n")

    for exam, assignment in result["schedule"].items():

        slot_index, room_id = assignment

        slot = test_time_slots[slot_index]

        print(
            f"{exam} | "
            f"{slot['day']} | "
            f"{slot['time']} | "
            f"{room_id}"
        )

else:

    print("No valid schedule found.")


# ==========================================
# PERFORMANCE METRICS
# ==========================================

print("\n===================================")
print("PERFORMANCE RESULTS")
print("===================================")

print(
    "Assignments Attempted:",
    result["assignments_attempted"]
)

print(
    "Backtracking Operations:",
    result["backtracks"]
)

print(
    "Execution Time:",
    round(result["execution_time"], 6),
    "seconds"
)

print(
    "Solution Found:",
    result["success"]
)