# =====================================================
# SMART EXAM SCHEDULER
# AI-Based University Exam Scheduling System
# =====================================================

from backtracking import basic_backtracking
from mrv import mrv_backtracking
from forward_checking import forward_checking
from mrv_forward_checking import mrv_forward_checking


# =====================================================
# INPUT HELPER FUNCTIONS
# =====================================================

def get_positive_integer(message):

    while True:
        try:
            value = int(input(message))

            if value > 0:
                return value

            print("Please enter a positive number.")

        except ValueError:
            print("Invalid input. Please enter a whole number.")


def get_text(message):

    while True:
        value = input(message).strip()

        if value:
            return value

        print("This field cannot be empty.")


# =====================================================
# DISPLAY SCHEDULE
# =====================================================

def display_schedule(schedule, time_slots):

    print(
        f"\n{'Course':<15}"
        f"{'Day':<18}"
        f"{'Time':<15}"
        f"{'Classroom':<15}"
    )

    print("-" * 63)

    sorted_schedule = sorted(
        schedule.items(),
        key=lambda item: item[1][0]
    )

    for course_code, assignment in sorted_schedule:

        slot_index, room_id = assignment

        slot = time_slots[slot_index]

        print(
            f"{course_code:<15}"
            f"{slot['day']:<18}"
            f"{slot['time']:<15}"
            f"{room_id:<15}"
        )


# =====================================================
# VALIDATE SCHEDULE
# =====================================================

def validate_schedule(
    exams,
    rooms,
    time_slots,
    conflicts,
    schedule
):

    # Check all exams are scheduled
    if set(schedule.keys()) != set(exams.keys()):
        return False

    # Check individual assignments
    for exam_code, assignment in schedule.items():

        slot_index, room_id = assignment

        # Check time slot
        if not isinstance(slot_index, int):
            return False

        if not 0 <= slot_index < len(time_slots):
            return False

        # Check classroom
        if room_id not in rooms:
            return False

        # Check examination capacity
        exam_capacity = rooms[room_id]["exam_capacity"]

        if exams[exam_code]["students"] > exam_capacity:
            return False

    # Check conflicts between pairs of exams
    exam_codes = list(schedule.keys())

    for i in range(len(exam_codes)):

        for j in range(i + 1, len(exam_codes)):

            exam1 = exam_codes[i]
            exam2 = exam_codes[j]

            slot1, room1 = schedule[exam1]
            slot2, room2 = schedule[exam2]

            if slot1 == slot2:

                # Room collision
                if room1 == room2:
                    return False

                # Student-group collision
                if exam2 in conflicts[exam1]:
                    return False

    return True


# =====================================================
# WELCOME SCREEN
# =====================================================

print("\n================================================")
print("              SMART EXAM SCHEDULER")
print("================================================")

print("AI-Based University Exam Scheduling System")

print("\nThis system uses four CSP algorithms:")
print("1. Basic Backtracking")
print("2. Minimum Remaining Values (MRV)")
print("3. Forward Checking")
print("4. MRV + Forward Checking")

print("\nThe system will:")
print("- Accept university examination information")
print("- Detect scheduling conflicts")
print("- Run all four AI algorithms")
print("- Validate generated schedules")
print("- Compare algorithm performance")
print("- Display a valid examination timetable")


# =====================================================
# STEP 1: ENTER EXAMS
# =====================================================

exams = {}

print("\n================================================")
print("                 ENTER EXAMS")
print("================================================")

number_of_exams = get_positive_integer(
    "\nNumber of Exams: "
)

for i in range(number_of_exams):

    print(f"\n------------ EXAM {i + 1} ------------")

    while True:

        course_code = get_text(
            "Course Code: "
        ).upper()

        if course_code not in exams:
            break

        print("This course code already exists.")

    course_name = get_text(
        "Course Name: "
    )

    number_of_students = get_positive_integer(
        "Number of Students: "
    )


    exams[course_code] = {
        "name": course_name,
        "students": number_of_students
        
    }


# =====================================================
# STEP 2: ENTER CLASSROOMS
# =====================================================

rooms = {}

print("\n================================================")
print("               ENTER CLASSROOMS")
print("================================================")

number_of_rooms = get_positive_integer(
    "\nNumber of Available Classrooms: "
)

for i in range(number_of_rooms):

    print(f"\n------------ ROOM {i + 1} ------------")

    while True:

        room_id = get_text(
            "Classroom Name: "
        ).upper()

        if room_id not in rooms:
            break

        print("This classroom already exists.")

    physical_capacity = get_positive_integer(
        "Physical Room Capacity: "
    )

    while True:

        exam_capacity = get_positive_integer(
            "Usable Exam Capacity: "
        )

        if exam_capacity <= physical_capacity:
            break

        print(
            "Exam capacity cannot exceed physical capacity."
        )

    rooms[room_id] = {
        "capacity": physical_capacity,
        "exam_capacity": exam_capacity
    }


# =====================================================
# STEP 3: ENTER AVAILABLE EXAM TIMES
# =====================================================

print("\n================================================")
print("            EXAMINATION AVAILABILITY")
print("================================================")

days = []
times = []
time_slots = []

number_of_days = get_positive_integer(
    "\nNumber of Examination Days: "
)

for i in range(number_of_days):

    while True:

        day = get_text(
            f"Enter Day {i + 1}: "
        )

        if day.upper() not in [d.upper() for d in days]:
            days.append(day)
            break

        print("This day has already been entered.")


number_of_times = get_positive_integer(
    "\nNumber of Exam Times Per Day: "
)

for i in range(number_of_times):

    while True:

        exam_time = get_text(
            f"Enter Time {i + 1}: "
        )

        if exam_time.upper() not in [t.upper() for t in times]:
            times.append(exam_time)
            break

        print("This time has already been entered.")


for day in days:

    for exam_time in times:

        time_slots.append({
            "day": day,
            "time": exam_time
        })


# =====================================================
# STEP 4: DETECT EXAM CONFLICTS
# =====================================================

conflicts = {
    exam_code: []
    for exam_code in exams
}

total_conflicts = 0

# =====================================================
# STEP 5: DISPLAY INPUT SUMMARY
# =====================================================

print("\n================================================")
print("                 INPUT SUMMARY")
print("================================================")

print("Total Exams:", len(exams))
print("Total Classrooms:", len(rooms))
print("Total Available Time Slots:", len(time_slots))

print("\nDetected Student-Group Conflicts:")

total_conflicts = 0

for exam_code, conflicting_exams in conflicts.items():

    print(
        f"{exam_code}: {conflicting_exams}"
    )

    total_conflicts += len(conflicting_exams)

# Each pair was counted twice
total_conflicts = total_conflicts // 2

print("\nTotal Conflicting Exam Pairs:", total_conflicts)


# =====================================================
# STEP 6: DEFINE ALL FOUR ALGORITHMS
# =====================================================

algorithms = {
    "Basic Backtracking": basic_backtracking,
    "MRV": mrv_backtracking,
    "Forward Checking": forward_checking,
    "MRV + Forward Checking": mrv_forward_checking
}


# =====================================================
# STEP 7: RUN ALL FOUR ALGORITHMS
# =====================================================

print("\n================================================")
print("              RUNNING AI ALGORITHMS")
print("================================================")

results = {}

for algorithm_name, algorithm_function in algorithms.items():

    print("\nRunning:", algorithm_name)

    result = algorithm_function(
        exams,
        rooms,
        time_slots,
        conflicts
    )

    # Verify each generated schedule
    if result["success"]:

        valid = validate_schedule(
            exams,
            rooms,
            time_slots,
            conflicts,
            result["schedule"]
        )

    else:

        valid = False

    result["valid"] = valid

    results[algorithm_name] = result

    print("Completed.")
    print("Solution Found:", result["success"])
    print("Schedule Valid:", result["valid"])


# =====================================================
# STEP 8: ALGORITHM PERFORMANCE COMPARISON
# =====================================================

print("\n================================================")
print("           AI PERFORMANCE COMPARISON")
print("================================================")

print(
    f"\n{'Algorithm':<26}"
    f"{'Time (ms)':<12}"
    f"{'Attempts':<12}"
    f"{'Backtracks':<12}"
    f"{'Valid':<8}"
)

print("-" * 70)

for algorithm_name, result in results.items():

    execution_ms = result["execution_time"] * 1000

    print(
        f"{algorithm_name:<26}"
        f"{execution_ms:<12.4f}"
        f"{result['assignments_attempted']:<12}"
        f"{result['backtracks']:<12}"
        f"{str(result['valid']):<8}"
    )


# =====================================================
# STEP 9: DISPLAY FINAL EXAM TIMETABLE
# =====================================================

print("\n================================================")
print("             FINAL EXAM TIMETABLE")
print("================================================")

preferred_algorithm = "MRV + Forward Checking"

selected_result = results[preferred_algorithm]

# If the preferred result is invalid,
# find another valid result
if not selected_result["valid"]:

    selected_result = None

    for algorithm_name, result in results.items():

        if result["valid"]:

            preferred_algorithm = algorithm_name
            selected_result = result
            break


if selected_result is not None:

    print("\nSchedule Generated Using:", preferred_algorithm)

    display_schedule(
        selected_result["schedule"],
        time_slots
    )

    print("\nSCHEDULE STATUS: SUCCESS")
    print("VALIDATION: PASSED")

else:

    print("\nNO VALID SCHEDULE FOUND")

    print(
        "The scheduling constraints could not "
        "be satisfied with the available resources."
    )


# =====================================================
# STEP 10: OPTIONAL INDIVIDUAL SCHEDULES
# =====================================================

show_all = input(
    "\nDisplay the schedule from each algorithm? (yes/no): "
).strip().lower()

if show_all in ["yes", "y"]:

    for algorithm_name, result in results.items():

        print("\n================================================")
        print("ALGORITHM:", algorithm_name)
        print("================================================")

        if result["valid"]:

            display_schedule(
                result["schedule"],
                time_slots
            )

        else:

            print("No validated schedule available.")


# =====================================================
# FINISH
# =====================================================

print("\n================================================")
print("           SMART EXAM SCHEDULER")
print("                  FINISHED")
print("================================================")