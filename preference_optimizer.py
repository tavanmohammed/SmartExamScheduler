
"""
SMART EXAM SCHEDULER
Weighted CSP Preference Optimization

Algorithm:
    MRV + Forward Checking + Branch and Bound

Objective:
    Minimize professor preference penalties
    while satisfying all hard scheduling constraints.

Soft constraints:
    - Preferred examination days
    - Preferred examination time slots
    - Days professors want to avoid

Hard constraints:
    - Student daily examination conflicts
    - Professor availability
    - Professor one-exam-per-day restriction
    - Room capacity and type
    - Room availability
    - Examination availability
    - Room double-booking prevention

Assignment format:
    exam_id -> (slot_index, room_id)

No Teaching Assistant dependencies.
"""

from solver_core import solve

from preferences import (
    DEFAULT_WEIGHTS,
    assignment_penalty,
    evaluate_preferences,
)


# ============================================================
# WEIGHTED CSP PREFERENCE OPTIMIZATION
# ============================================================

def optimize_preferences(
    exams,
    rooms,
    time_slots,
    conflicts,
    professors=None,
    weights=None,
    timeout_seconds=30,
):
    """
    Find a valid schedule with minimum total
    professor preference penalty.

    Uses the shared CSP solver with a weighted
    objective function.

    Returns:
        Solver result with additional fields:
            preference_results
            total_penalty

    An OPTIMAL result means the solver has proven
    that no lower-cost valid schedule exists.
    """

    # --------------------------------------------------------
    # 1. NORMALIZE INPUTS
    # --------------------------------------------------------

    professors = professors or {}

    weights = {
        **DEFAULT_WEIGHTS,
        **(weights or {}),
    }

    # --------------------------------------------------------
    # 2. VALIDATE PREFERENCE WEIGHTS
    # --------------------------------------------------------

    if any(
        type(weight) is not int or weight < 0
        for weight in weights.values()
    ):
        raise ValueError(
            "Preference weights must be "
            "nonnegative integers."
        )

    # --------------------------------------------------------
    # 3. DEFINE WEIGHTED OBJECTIVE FUNCTION
    # --------------------------------------------------------

    def cost(exam_id, value):
        """
        Calculate the preference penalty associated
        with assigning an examination to a specific
        time slot and room.

        Lower cost indicates higher satisfaction.
        """

        return assignment_penalty(
            exam_id,
            value,
            exams,
            time_slots,
            professors,
            weights=weights,
        )

    # --------------------------------------------------------
    # 4. RUN CSP BRANCH-AND-BOUND OPTIMIZATION
    # --------------------------------------------------------

    result = solve(
        exams,
        rooms,
        time_slots,
        conflicts,
        mrv=True,
        fc=True,
        professors=professors,
        timeout_seconds=timeout_seconds,
        cost_function=cost,
    )

    # --------------------------------------------------------
    # 5. EVALUATE OPTIMIZED SCHEDULE
    # --------------------------------------------------------

    if result["success"]:

        preference_results = evaluate_preferences(
            result["schedule"],
            exams,
            time_slots,
            professors,
            weights=weights,
        )

        result["preference_results"] = (
            preference_results
        )

        # The independent preference calculation
        # provides a consistency check on the
        # solver's reported objective cost.

        result["total_penalty"] = (
            preference_results["total_penalty"]
        )

        if (
            result.get("total_cost") is not None
            and result["total_cost"]
            != result["total_penalty"]
        ):
            raise RuntimeError(
                "Optimization cost does not match "
                "the independently evaluated "
                "preference penalty."
            )

    else:

        result["preference_results"] = None

        result["total_penalty"] = None

    return result


# ============================================================
# OPTIONAL DIRECT TEST
# ============================================================

if __name__ == "__main__":

    from university_data import get_university_data

    from conflicts import (
        get_course_students,
        generate_conflicts,
    )

    from validator import validate_schedule
    from algorithm_selector import run_algorithm

    # --------------------------------------------------------
    # LOAD UNIVERSITY DATA
    # --------------------------------------------------------

    data = get_university_data()

    conflicts = generate_conflicts(
        data["exams"],
        get_course_students(
            data["students"]
        ),
    )

    # --------------------------------------------------------
    # GENERATE BASELINE SCHEDULE
    # --------------------------------------------------------

    baseline = run_algorithm(
        "MRV + FC + Degree",
        data,
        conflicts,
        timeout_seconds=30,
    )

    if not baseline["success"]:

        print(
            "Could not generate baseline schedule."
        )

    else:

        baseline_preferences = evaluate_preferences(
            baseline["schedule"],
            data["exams"],
            data["time_slots"],
            data["professors"],
        )

        print("\nBASELINE SCHEDULE")
        print("----------------------------")

        print(
            "Baseline preference penalty:",
            baseline_preferences["total_penalty"],
        )

        # ----------------------------------------------------
        # OPTIMIZE PREFERENCES
        # ----------------------------------------------------

        optimized = optimize_preferences(
            data["exams"],
            data["rooms"],
            data["time_slots"],
            conflicts,
            professors=data["professors"],
            timeout_seconds=30,
        )

        print("\nOPTIMIZED SCHEDULE")
        print("----------------------------")

        print(
            "Status:",
            optimized["status"],
        )

        print(
            "Success:",
            optimized["success"],
        )

        print(
            "Total preference penalty:",
            optimized["total_penalty"],
        )

        if optimized["success"]:

            validation = validate_schedule(
                data["exams"],
                data["rooms"],
                data["time_slots"],
                data["students"],
                optimized["schedule"],
                data["professors"],
            )

            print(
                "Valid schedule:",
                validation["valid"],
            )

            print(
                "Satisfaction rate:",
                optimized["preference_results"][
                    "satisfaction_rate"
                ],
            )

            print(
                "Penalty improvement:",
                baseline_preferences["total_penalty"]
                - optimized["total_penalty"],
            )

            print("\nProfessor preference details:")

            for detail in optimized[
                "preference_results"
            ]["details"]:

                print(detail)
