
"""
SMART EXAM SCHEDULER
Main Command-Line Application

Features:
    1. Generate a sample examination schedule
    2. Interactive scheduling
    3. Compare seven AI algorithms
    4. Optimize professor preferences
    5. Automatic algorithm selection
    6. Minimum-disruption timetable repair
    7. Exit

Assignment format:
    exam_id -> (slot_index, room_id)

No Teaching Assistant dependencies.
"""

from copy import deepcopy

from university_data import get_university_data

from conflicts import (
    get_course_students,
    generate_conflicts,
)

from algorithm_selector import (
    run_algorithm,
    select_algorithm,
)

from compare_algorithms import compare_algorithms

from preference_optimizer import optimize_preferences

from rescheduling import repair_schedule

from interactive import (
    interactive_scheduler,
    display_schedule,
)

from validator import validate_schedule


# ============================================================
# HELPERS
# ============================================================

def build_conflicts(data):
    """Generate student examination conflicts."""

    return generate_conflicts(
        data["exams"],
        get_course_students(data["students"]),
    )


def validate_result(data, result):
    """Independently validate a successful timetable."""

    if not result["success"]:
        print("No timetable was generated.")
        return False

    validation = validate_schedule(
        data["exams"],
        data["rooms"],
        data["time_slots"],
        data["students"],
        result["schedule"],
        data.get("professors", {}),
    )

    print(
        "Schedule valid:",
        validation["valid"],
    )

    if not validation["valid"]:
        print("Validation errors:")

        for error in validation["errors"]:
            print(" -", error)

    return validation["valid"]


def show_metrics(result):
    """Display basic algorithm performance metrics."""

    print("\nALGORITHM METRICS")
    print("-" * 45)

    print(
        "Algorithm:",
        result.get("algorithm", "N/A"),
    )

    print(
        "Status:",
        result["status"],
    )

    print(
        "Execution time:",
        f"{result.get('execution_time', 0) * 1000:.3f} ms",
    )

    print(
        "Assignment attempts:",
        result.get("assignments_attempted", 0),
    )

    print(
        "Backtracks:",
        result.get("backtracks", 0),
    )

    print(
        "Constraint checks:",
        result.get("constraint_checks", 0),
    )

    print(
        "Nodes explored:",
        result.get("nodes_explored", 0),
    )

    print(
        "Values pruned:",
        result.get("values_pruned", 0),
    )


# ============================================================
# OPTION 1: GENERATE SAMPLE SCHEDULE
# ============================================================

def generate_sample_schedule():

    data = get_university_data()
    conflicts = build_conflicts(data)

    result = run_algorithm(
        "MRV + Forward Checking",
        data,
        conflicts,
        timeout_seconds=30,
    )

    show_metrics(result)

    if validate_result(data, result):
        display_schedule(
            data,
            result["schedule"],
        )


# ============================================================
# OPTION 3: COMPARE AI ALGORITHMS
# ============================================================

def compare_sample_algorithms():

    data = get_university_data()

    results = compare_algorithms(
        data,
        timeout_seconds=10,
    )

    print("\nAI ALGORITHM COMPARISON")
    print("=" * 85)

    print(
        f"{'Algorithm':<38}"
        f"{'Time(ms)':>12}"
        f"{'Attempts':>12}"
        f"{'Backtracks':>12}"
        f"{'Valid':>10}"
    )

    print("-" * 85)

    for result in results:

        execution_time = (
            result.get("execution_time", 0) * 1000
        )

        valid = result.get("valid_schedule")

        print(
            f"{result['algorithm']:<38}"
            f"{execution_time:>12.3f}"
            f"{result.get('assignments_attempted', 0):>12}"
            f"{result.get('backtracks', 0):>12}"
            f"{str(valid):>10}"
        )


# ============================================================
# OPTION 4: OPTIMIZE PROFESSOR PREFERENCES
# ============================================================

def optimize_sample_preferences():

    data = get_university_data()
    conflicts = build_conflicts(data)

    result = optimize_preferences(
        data["exams"],
        data["rooms"],
        data["time_slots"],
        conflicts,
        professors=data.get("professors", {}),
        timeout_seconds=30,
    )

    show_metrics(result)

    if validate_result(data, result):

        display_schedule(
            data,
            result["schedule"],
        )

        preferences = result[
            "preference_results"
        ]

        print("\nPROFESSOR PREFERENCES")
        print("-" * 45)

        print(
            "Total penalty:",
            result["total_penalty"],
        )

        satisfaction = preferences[
            "satisfaction_rate"
        ]

        print(
            "Satisfaction rate:",
            (
                f"{satisfaction:.2f}%"
                if satisfaction is not None
                else "N/A"
            ),
        )

        print(
            "Examinations satisfying preferences:",
            preferences["satisfied_exams"],
        )

        print(
            "Examinations with preferences:",
            preferences["exams_with_preferences"],
        )


# ============================================================
# OPTION 5: AUTOMATIC ALGORITHM SELECTION
# ============================================================

def generate_auto_schedule():

    data = get_university_data()
    conflicts = build_conflicts(data)

    recommendation = select_algorithm(
        data,
        conflicts,
    )

    print("\nAUTOMATIC AI RECOMMENDATION")
    print("-" * 45)

    print(
        "Recommended algorithm:",
        recommendation["algorithm"],
    )

    print(
        "Reason:",
        recommendation["reason"],
    )

    print(
        "Problem complexity:",
        recommendation["complexity"],
    )

    if recommendation.get("warning"):
        print(
            "Warning:",
            recommendation["warning"],
        )

    result = run_algorithm(
        "Auto",
        data,
        conflicts,
        timeout_seconds=30,
    )

    show_metrics(result)

    if validate_result(data, result):
        display_schedule(
            data,
            result["schedule"],
        )


# ============================================================
# OPTION 6: MINIMUM-DISRUPTION REPAIR
# ============================================================

def demonstrate_schedule_repair():

    # Use a copy so the sample dataset is not
    # permanently modified during the demonstration.

    data = deepcopy(
        get_university_data()
    )

    conflicts = build_conflicts(data)

    original_result = run_algorithm(
        "MRV + FC + Degree",
        data,
        conflicts,
        timeout_seconds=30,
    )

    if not original_result["success"]:
        print(
            "Unable to generate an original timetable."
        )
        return

    original_schedule = (
        original_result["schedule"]
    )

    print("\nORIGINAL TIMETABLE")
    print("-" * 45)

    if not validate_result(
        data,
        original_result,
    ):
        return

    display_schedule(
        data,
        original_schedule,
    )

    # --------------------------------------------------------
    # SIMULATE AN UNEXPECTED ROOM CLOSURE
    # --------------------------------------------------------

    if not original_schedule:
        print("No exams available for repair.")
        return

    exam_id = next(
        iter(original_schedule)
    )

    slot, room = original_schedule[exam_id]

    data["rooms"][room].setdefault(
        "unavailable_slots",
        [],
    )

    if slot not in data["rooms"][room][
        "unavailable_slots"
    ]:

        data["rooms"][room][
            "unavailable_slots"
        ].append(slot)

    print("\nSIMULATED DISRUPTION")
    print("-" * 45)

    print(
        "Room:",
        room,
    )

    print(
        "Unavailable slot:",
        slot,
    )

    print(
        "Affected exam:",
        exam_id,
    )

    # --------------------------------------------------------
    # REPAIR THE SCHEDULE
    # --------------------------------------------------------

    result = repair_schedule(
        data["exams"],
        data["rooms"],
        data["time_slots"],
        conflicts,
        original_schedule,
        professors=data.get("professors", {}),
        timeout_seconds=30,
    )

    show_metrics(result)

    if validate_result(data, result):

        print("\nREPAIRED TIMETABLE")
        print("-" * 45)

        display_schedule(
            data,
            result["schedule"],
        )

        print("\nREPAIR RESULTS")
        print("-" * 45)

        print(
            "Changed examinations:",
            result["changed_exams"],
        )

        print(
            "Moved examinations:",
            result["moved_exams"],
        )

        print(
            "Preserved examinations:",
            result["preserved_exams"],
        )

        print("\nCHANGES:")

        for change in result["changes"]:

            print(
                change["exam"],
                ":",
                change["old_assignment"],
                "->",
                change["new_assignment"],
            )


# ============================================================
# MAIN MENU
# ============================================================

def main():

    while True:

        print("\n" + "=" * 55)
        print("SMART EXAM SCHEDULER")
        print("=" * 55)

        print("1. Generate sample schedule")
        print("2. Interactive scheduling")
        print("3. Compare AI algorithms")
        print("4. Optimize professor preferences")
        print("5. Automatic algorithm selection")
        print("6. Minimum-disruption timetable repair")
        print("7. Exit")

        choice = input(
            "\nSelect an option (1-7): "
        ).strip()

        try:

            if choice == "1":
                generate_sample_schedule()

            elif choice == "2":
                interactive_scheduler()

            elif choice == "3":
                compare_sample_algorithms()

            elif choice == "4":
                optimize_sample_preferences()

            elif choice == "5":
                generate_auto_schedule()

            elif choice == "6":
                demonstrate_schedule_repair()

            elif choice == "7":

                print(
                    "\nExiting Smart Exam Scheduler."
                )

                break

            else:

                print(
                    "Invalid option. Choose 1-7."
                )

        except (
            ValueError,
            OSError,
            KeyError,
            TypeError,
        ) as error:

            print(
                "\nError:",
                error,
            )

        except KeyboardInterrupt:

            print(
                "\nOperation cancelled."
            )


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
