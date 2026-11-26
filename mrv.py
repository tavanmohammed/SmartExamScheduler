# Backtracking + Minimum Remaining Values

from solver_core import solve


def mrv_backtracking(
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
        fc=False,
        lcv=False,
        professors=professors,

        timeout_seconds=timeout_seconds
    )
