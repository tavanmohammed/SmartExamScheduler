# ==========================================
# SMART EXAM SCHEDULER
# ==========================================

from students import generate_students
from conflicts import get_course_students, generate_conflicts
from backtracking import basic_backtracking
from mrv import mrv_backtracking
from forward_checking import forward_checking
from mrv_forward_checking import mrv_forward_checking
from validator import validate_schedule
# ==========================================
# 1. UNIVERSITY EXAMS
# ==========================================

exams = {

    # ENGINEERING

    "ENG101": {
        "name": "Engineering Mathematics",
        "faculty": "Engineering",
        "programs": [
            "Software Engineering",
            "Electrical Engineering"
        ],
        "students": 100,
        "duration": 180
    },

    "SOFE301": {
        "name": "Database Systems",
        "faculty": "Engineering",
        "programs": ["Software Engineering"],
        "students": 60,
        "duration": 180
    },

    "SOFE302": {
        "name": "Design and Analysis of Algorithms",
        "faculty": "Engineering",
        "programs": ["Software Engineering"],
        "students": 70,
        "duration": 180
    },

    "ELEE301": {
        "name": "Circuit Analysis",
        "faculty": "Engineering",
        "programs": ["Electrical Engineering"],
        "students": 80,
        "duration": 180
    },

    # SCIENCE

    "MATH101": {
        "name": "Calculus for Science",
        "faculty": "Science",
        "programs": [
            "Mathematics",
            "Computer Science"
        ],
        "students": 90,
        "duration": 180
    },

    "CSCI301": {
        "name": "Artificial Intelligence",
        "faculty": "Science",
        "programs": ["Computer Science"],
        "students": 60,
        "duration": 180
    },

    # BUSINESS

    "BUSI101": {
        "name": "Business Mathematics",
        "faculty": "Business",
        "programs": ["Commerce"],
        "students": 100,
        "duration": 180
    },

    "BUSI201": {
        "name": "Financial Accounting",
        "faculty": "Business",
        "programs": ["Commerce"],
        "students": 80,
        "duration": 180
    }
}


# ==========================================
# 2. CLASSROOMS
# ==========================================

rooms = {

    "ROOM_A": {
        "capacity": 100,
        "exam_capacity": 70
    },

    "ROOM_B": {
        "capacity": 150,
        "exam_capacity": 100
    },

    "ROOM_C": {
        "capacity": 200,
        "exam_capacity": 150
    },

    "EXAM_HALL": {
        "capacity": 250,
        "exam_capacity": 180
    }
}


# ==========================================
# 3. EXAM TIME SLOTS
# ==========================================

days = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday"

]

times = [
    "9:00 AM",
    "1:00 PM"
]

time_slots = []

for day in days:
    for time in times:

        time_slots.append({
            "day": day,
            "time": time
        })


# ==========================================
# 4. GENERATE STUDENT ENROLLMENT
# ==========================================

students = generate_students(exams)

course_students = get_course_students(students)

exam_conflicts = generate_conflicts(
    exams,
    course_students
)


# ==========================================
# 5. DISPLAY UNIVERSITY INFORMATION
# ==========================================

print("\n====================================")
print("       SMART EXAM SCHEDULER")
print("====================================")

print("\nTotal Exams:", len(exams))
print("Total Classrooms:", len(rooms))
print("Total Time Slots:", len(time_slots))

print("\nEXAM CONFLICTS")

for exam, conflicting_exams in exam_conflicts.items():

    print(exam, ":", conflicting_exams)


# ==========================================
# 6. RUN BASIC BACKTRACKING
# ==========================================

result = basic_backtracking(
    exams,
    rooms,
    time_slots,
    exam_conflicts
)


# ==========================================
# 7. DISPLAY EXAM SCHEDULE
# ==========================================

print("\n====================================")
print("       GENERATED EXAM SCHEDULE")
print("====================================")

if result["success"]:

    for exam_code, assignment in result["schedule"].items():

        slot_index, room_id = assignment

        slot = time_slots[slot_index]

        print(
            f"{exam_code} | "
            f"{slot['day']} | "
            f"{slot['time']} | "
            f"{room_id}"
        )

else:

    print("No valid schedule found.")


# ==========================================
# 8. PERFORMANCE RESULTS
# ==========================================

print("\n====================================")
print("       PERFORMANCE RESULTS")
print("====================================")

print("Execution Time:", round(result["execution_time"], 6))
print("Assignments Attempted:", result["assignments_attempted"])
print("Backtracking Operations:", result["backtracks"])
print("Solution Found:", result["success"])

# ==========================================
# COMPARE ALL FOUR AI ALGORITHMS
# ==========================================

print("\n====================================")
print("       AI ALGORITHM COMPARISON")
print("====================================")


# 1. BASIC BACKTRACKING

basic_result = basic_backtracking(
    exams,
    rooms,
    time_slots,
    exam_conflicts
)


# 2. MRV

mrv_result = mrv_backtracking(
    exams,
    rooms,
    time_slots,
    exam_conflicts
)


# 3. FORWARD CHECKING

fc_result = forward_checking(
    exams,
    rooms,
    time_slots,
    exam_conflicts
)


# 4. MRV + FORWARD CHECKING

combined_result = mrv_forward_checking(
    exams,
    rooms,
    time_slots,
    exam_conflicts
)


# ==========================================
# DISPLAY RESULTS
# ==========================================

results = {
    "Basic Backtracking": basic_result,
    "MRV": mrv_result,
    "Forward Checking": fc_result,
    "MRV + Forward Checking": combined_result
}


for algorithm, result in results.items():

    print("\nAlgorithm:", algorithm)

    print(
        "Execution Time:",
        round(result["execution_time"], 6),
        "seconds"
    )

    print(
        "Assignments Attempted:",
        result["assignments_attempted"]
    )

    print(
        "Backtracks:",
        result["backtracks"]
    )

    print(
        "Solution Found:",
        result["success"]
    )

    print("------------------------------------")

# ==========================================
# AUTOMATIC SCHEDULE VALIDATION
# ==========================================

print("\n====================================")
print("       SCHEDULE VALIDATION")
print("====================================")


for algorithm, result in results.items():

    print("\nAlgorithm:", algorithm)

    # An unsolved problem has no complete
    # schedule to validate
    if not result["success"]:

        print("No schedule found.")
        continue

    validation = validate_schedule(
        exams,
        rooms,
        time_slots,
        students,
        result["schedule"]
    )

    if validation["valid"]:

        print("VALID SCHEDULE")

        print("All scheduling constraints satisfied!")

    else:

        print("INVALID SCHEDULE")

        for error in validation["errors"]:
            print(" -", error)

    print("------------------------------------")

    # ==========================================
# EXPERIMENT 1
# EFFECT OF AVAILABLE TIME SLOTS
# ==========================================

print("\n====================================")
print("EXPERIMENT 1: TIME SLOT AVAILABILITY")
print("====================================")


# Define different exam periods
experiment_days = [
    ["Monday", "Tuesday", "Wednesday", "Thursday"],

    ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],

    ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
]


# Define all algorithms
algorithms = {
    "Basic Backtracking": basic_backtracking,
    "MRV": mrv_backtracking,
    "Forward Checking": forward_checking,
    "MRV + Forward Checking": mrv_forward_checking
}


# Run experiments
for test_number, days_list in enumerate(experiment_days, start=1):

    # Generate time slots
    experiment_slots = []

    for day in days_list:

        for exam_time in ["9:00 AM", "1:00 PM"]:

            experiment_slots.append({
                "day": day,
                "time": exam_time
            })

    print("\n------------------------------------")
    print("TEST CASE:", test_number)
    print("Number of Exams:", len(exams))
    print("Number of Rooms:", len(rooms))
    print("Number of Time Slots:", len(experiment_slots))
    print("------------------------------------")

    # Test all four algorithms
    for algorithm_name, algorithm_function in algorithms.items():

        experiment_result = algorithm_function(
            exams,
            rooms,
            experiment_slots,
            exam_conflicts
        )

        # Independently check each solution
        if experiment_result["success"]:

            validation = validate_schedule(
                exams,
                rooms,
                experiment_slots,
                students,
                experiment_result["schedule"]
            )

            if not validation["valid"]:
                print(
                    "ERROR: Invalid schedule from",
                    algorithm_name
                )
                print(validation["errors"])
                continue

        print("\nAlgorithm:", algorithm_name)

        print(
            "Execution Time:",
            round(experiment_result["execution_time"], 6)
        )

        print(
            "Assignments:",
            experiment_result["assignments_attempted"]
        )

        print(
            "Backtracks:",
            experiment_result["backtracks"]
        )

        print(
            "Solution Found:",
            experiment_result["success"]
        )