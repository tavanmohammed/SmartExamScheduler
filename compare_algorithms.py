# ==========================================
# SMART EXAM SCHEDULER
# Basic Backtracking vs MRV
# ==========================================

from backtracking import basic_backtracking
from mrv import mrv_backtracking
from forward_checking import forward_checking
from mrv_forward_checking import mrv_forward_checking

# Two exams with different room requirements
exams = {

    "MATH101": {
        "name": "Mathematics",
        "students": 30
    },

    "PHYS101": {
        "name": "Engineering Physics",
        "students": 80
    }
}


# Available rooms
rooms = {

    "LARGE_HALL": {
        "capacity": 100
    },

    "SMALL_ROOM": {
        "capacity": 40
    }
}


# Only one time slot
time_slots = [
    {
        "day": "Monday",
        "time": "9:00 AM"
    }
]


# No shared students
conflicts = {
    "MATH101": [],
    "PHYS101": []
}


# ==========================================
# RUN BASIC BACKTRACKING
# ==========================================

basic_result = basic_backtracking(
    exams,
    rooms,
    time_slots,
    conflicts
)


# ==========================================
# RUN MRV
# ==========================================

mrv_result = mrv_backtracking(
    exams,
    rooms,
    time_slots,
    conflicts
)


# ==========================================
# DISPLAY COMPARISON
# ==========================================

print("\n====================================")
print(" SMART EXAM SCHEDULER")
print(" BASIC BACKTRACKING VS MRV")
print("====================================")

print("\nBASIC BACKTRACKING")

print(
    "Assignments Attempted:",
    basic_result["assignments_attempted"]
)

print(
    "Backtracks:",
    basic_result["backtracks"]
)

print(
    "Execution Time:",
    round(basic_result["execution_time"], 6)
)

print(
    "Solution Found:",
    basic_result["success"]
)


print("\nMRV BACKTRACKING")

print(
    "Assignments Attempted:",
    mrv_result["assignments_attempted"]
)

print(
    "Backtracks:",
    mrv_result["backtracks"]
)

print(
    "Execution Time:",
    round(mrv_result["execution_time"], 6)
)

print(
    "Solution Found:",
    mrv_result["success"]
)

# ==========================================
# RUN FORWARD CHECKING
# ==========================================

fc_result = forward_checking(
    exams,
    rooms,
    time_slots,
    conflicts
)


print("\nFORWARD CHECKING")

print(
    "Assignments Attempted:",
    fc_result["assignments_attempted"]
)

print(
    "Backtracks:",
    fc_result["backtracks"]
)

print(
    "Execution Time:",
    round(fc_result["execution_time"], 6)
)

print(
    "Solution Found:",
    fc_result["success"]
)


# Display generated schedule
if fc_result["success"]:

    print("\nGenerated Schedule:")

    for exam, assignment in fc_result["schedule"].items():

        slot_index, room_id = assignment

        print(
            exam,
            "->",
            time_slots[slot_index]["day"],
            time_slots[slot_index]["time"],
            room_id
        )

# ==========================================
# RUN MRV + FORWARD CHECKING
# ==========================================

combined_result = mrv_forward_checking(
    exams,
    rooms,
    time_slots,
    conflicts
)


print("\n====================================")
print("MRV + FORWARD CHECKING")
print("====================================")

print(
    "Assignments Attempted:",
    combined_result["assignments_attempted"]
)

print(
    "Backtracks:",
    combined_result["backtracks"]
)

print(
    "Execution Time:",
    round(combined_result["execution_time"], 6)
)

print(
    "Solution Found:",
    combined_result["success"]
)


if combined_result["success"]:

    print("\nGenerated Schedule:")

    for exam, assignment in combined_result["schedule"].items():

        slot_index, room_id = assignment

        slot = time_slots[slot_index]

        print(
            f"{exam} | "
            f"{slot['day']} | "
            f"{slot['time']} | "
            f"{room_id}"
        )

        