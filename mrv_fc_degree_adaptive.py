from solver_core import solve


def mrv_fc_degree_adaptive(
    exams,
    rooms,
    time_slots,
    conflicts,
    professors=None,
    timeout_seconds=None,

):

    return solve(
        exams,
        rooms,
        time_slots,
        conflicts,
        mrv=True,
        fc=True,
        degree=True,
        adaptive_lcv=True,
        professors=professors,

        timeout_seconds=timeout_seconds
    )


