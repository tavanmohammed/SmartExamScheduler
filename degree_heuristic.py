# Degree Heuristic for CSP variable selection


def select_mrv_degree(
    remaining,
    domains,
    conflicts
):

    remaining_set = set(remaining)

    def priority(exam):

        domain_size = len(domains[exam])

        degree = len(
            set(conflicts.get(exam, []))
            & remaining_set
            - {exam}
        )

        return domain_size, -degree

    return min(
        remaining,
        key=priority
    )