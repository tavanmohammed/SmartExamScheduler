# Backtracking + Forward Checking

from solver_core import solve


def forward_checking(
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
        mrv=False,
        fc=True,
        lcv=False,
        professors=professors,

        timeout_seconds=timeout_seconds
    )
