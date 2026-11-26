
"""
Least Constraining Value (LCV) heuristic.

Ranks candidate exam assignments according to
how many legal values they eliminate from
the remaining examination domains.

Assignment format:
    (slot_index, room_id)

No Teaching Assistant dependencies.
"""


def order_lcv_values(
    exam_id,
    candidates,
    remaining,
    domains,
    rules,
    schedule,
    check_time=lambda: None,
):
    """
    Return candidate values from least constraining
    to most constraining.

    A lower score means fewer remaining domain
    values would be eliminated.
    """

    scores = []

    for value in candidates:

        check_time()

        eliminated = 0

        for other_exam in remaining:

            for other_value in domains[other_exam]:

                check_time()

                if not rules.compatible(
                    exam_id,
                    value,
                    other_exam,
                    other_value,
                ):
                    eliminated += 1

        scores.append(
            (eliminated, value)
        )

    # Python's stable sort preserves original domain
    # order when scores are equal.
    scores.sort(key=lambda item: item[0])

    return [
        value
        for _, value in scores
    ]

