# Basic Backtracking

from solver_core import solve


def basic_backtracking(
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
        fc=False,
        lcv=False,
        professors=professors,

        timeout_seconds=timeout_seconds
    )
