
"""
SMART EXAM SCHEDULER
Adaptive Least Constraining Value (Adaptive LCV)

Purpose:
    Balance LCV effectiveness against computational cost.

Strategy:
    1. Estimate the cost of exact LCV ordering.
    2. Apply exact LCV when the estimated work is affordable.
    3. Preserve original candidate order when the
       estimated comparison count is too large.

Assignment format:
    (time_slot_index, room_id)

No Teaching Assistant dependencies.
"""

from lcv import order_lcv_values


DEFAULT_MAX_COMPARISONS = 100_000


def order_adaptive_lcv_values(
    exam,
    candidates,
    remaining,
    domains,
    rules,
    schedule,
    check_time,
    max_comparisons=DEFAULT_MAX_COMPARISONS,
):
    """
    Adaptively order values using LCV.

    Parameters:
        exam:
            Examination being assigned.

        candidates:
            Candidate (slot, room) values.

        remaining:
            Unassigned examinations.

        domains:
            Remaining examination domains.

        rules:
            Constraint engine.

        schedule:
            Current partial timetable.

        check_time:
            Callback for timeout enforcement.

        max_comparisons:
            Maximum estimated constraint comparisons
            allowed before skipping exact LCV.

    Returns:
        Ordered candidate values.
    """

    if (
        type(max_comparisons) is not int
        or max_comparisons < 0
    ):
        raise ValueError(
            "max_comparisons must be "
            "a nonnegative integer."
        )

    check_time()

    # --------------------------------------------------------
    # ESTIMATE EXACT LCV COMPUTATIONAL COST
    # --------------------------------------------------------

    candidate_count = len(
        candidates
    )

    if candidate_count <= 1:
        return candidates

    estimated_comparisons = 0

    for other_exam in remaining:

        check_time()

        estimated_comparisons += (
            candidate_count
            * len(domains[other_exam])
        )

        # ----------------------------------------------------
        # ADAPTIVE FALLBACK
        # ----------------------------------------------------

        if estimated_comparisons > max_comparisons:

            # Preserve the original domain order.
            # No expensive LCV scoring is performed.

            return candidates

    # --------------------------------------------------------
    # EXACT LEAST CONSTRAINING VALUE
    # --------------------------------------------------------

    return order_lcv_values(
        exam,
        candidates,
        remaining,
        domains,
        rules,
        schedule,
        check_time,
    )
