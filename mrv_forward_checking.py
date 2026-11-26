# Backtracking + MRV + Forward Checking

from solver_core import solve


def mrv_forward_checking(
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
        lcv=False,
        professors=professors,

        timeout_seconds=timeout_seconds
    )
