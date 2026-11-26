
"""
SMART EXAM SCHEDULER
AI Algorithm Performance Comparison

Compares all seven CSP algorithm configurations
using the same university dataset.

Metrics:
    - Execution time
    - Assignment attempts
    - Backtracks
    - Constraint checks
    - Nodes explored
    - Values pruned
    - Schedule validity
    - Solver status

All successful schedules are validated independently.

Assignment format:
    exam_id -> (slot_index, room_id)

No Teaching Assistant dependencies.
"""

from university_data import get_university_data

from conflicts import (
    get_course_students,
    generate_conflicts,
)

from algorithm_selector import (
    ALGORITHMS,
    run_algorithm,
)

from validator import validate_schedule


# ============================================================
# COMPARE ALL SEVEN AI ALGORITHMS
# ============================================================

def compare_algorithms(
    data,
    timeout_seconds=10,
):
    """
    Run each algorithm on the same university dataset.

    Every algorithm receives:
        - Identical examinations
        - Identical rooms
        - Identical time slots
        - Identical student conflict graph
        - Identical professor constraints
        - Identical timeout

    Returns:
        List of solver results with validation data.
    """

    # --------------------------------------------------------
    # 1. BUILD STUDENT CONFLICT GRAPH
    # --------------------------------------------------------

    course_students = get_course_students(
        data["students"]
    )

    conflicts = generate_conflicts(
        data["exams"],
        course_students,
    )

    # --------------------------------------------------------
    # 2. RUN EVERY ALGORITHM
    # --------------------------------------------------------

    results = []

    for algorithm in ALGORITHMS:

        result = run_algorithm(
            algorithm,
            data,
            conflicts,
            timeout_seconds=timeout_seconds,
        )

        # ----------------------------------------------------
        # 3. INDEPENDENT SCHEDULE VALIDATION
        # ----------------------------------------------------

        if result["success"]:

            validation = validate_schedule(
                data["exams"],
                data["rooms"],
                data["time_slots"],
                data["students"],
                result["schedule"],
                data.get("professors", {}),
            )

        else:

            validation = None

        result["validation"] = validation

        # Prevent treating an invalid timetable
        # as a successful comparison result.
        if (
            result["success"]
            and not validation["valid"]
        ):

            result["valid_schedule"] = False

        else:

            result["valid_schedule"] = (
                validation["valid"]
                if validation is not None
                else None
            )

        results.append(result)

    return results


# ============================================================
# FORMAT METRICS
# ============================================================

def format_metric(value, decimals=3):
    """
    Format a numeric metric safely.
    """

    if value is None:
        return "N/A"

    if isinstance(value, float):
        return f"{value:.{decimals}f}"

    return str(value)


# ============================================================
# PRINT PERFORMANCE COMPARISON
# ============================================================

def print_comparison(results):
    """
    Print a readable comparison table.
    """

    print("\nSMART EXAM SCHEDULER")
    print("AI ALGORITHM PERFORMANCE COMPARISON")
    print("=" * 125)

    print(
        f"{'Algorithm':<37}"
        f"{'Time(ms)':>11}"
        f"{'Attempts':>11}"
        f"{'Backtracks':>12}"
        f"{'Checks':>12}"
        f"{'Nodes':>10}"
        f"{'Pruned':>10}"
        f"{'Valid':>9}"
        f"{'Status':>13}"
    )

    print("-" * 125)

    for result in results:

        execution_time = result.get(
            "execution_time"
        )

        time_ms = (
            execution_time * 1000
            if execution_time is not None
            else None
        )

        validation = result.get(
            "validation"
        )

        valid = (
            "YES"
            if validation is not None
            and validation["valid"]
            else (
                "NO"
                if validation is not None
                else "N/A"
            )
        )

        print(
            f"{result['algorithm']:<37}"
            f"{format_metric(time_ms):>11}"
            f"{format_metric(result.get('assignments_attempted')):>11}"
            f"{format_metric(result.get('backtracks')):>12}"
            f"{format_metric(result.get('constraint_checks')):>12}"
            f"{format_metric(result.get('nodes_explored')):>10}"
            f"{format_metric(result.get('values_pruned')):>10}"
            f"{valid:>9}"
            f"{result.get('status', 'UNKNOWN'):>13}"
        )

    print("=" * 125)


# ============================================================
# OPTIONAL DIRECT TEST
# ============================================================

if __name__ == "__main__":

    data = get_university_data()

    print("\nUniversity Dataset")
    print("----------------------------")

    print(
        "Examinations:",
        len(data["exams"])
    )

    print(
        "Students:",
        len(data["students"])
    )

    print(
        "Professors:",
        len(data["professors"])
    )

    print(
        "Rooms:",
        len(data["rooms"])
    )

    print(
        "Time slots:",
        len(data["time_slots"])
    )

    results = compare_algorithms(
        data,
        timeout_seconds=10,
    )

    print_comparison(results)

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    successful = sum(
        result["success"]
        for result in results
    )

    valid = sum(
        result.get("valid_schedule") is True
        for result in results
    )

    print(
        "\nSuccessful algorithms:",
        f"{successful}/{len(results)}"
    )

    print(
        "Independently validated schedules:",
        f"{valid}/{len(results)}"
    )
