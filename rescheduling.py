
"""
SMART EXAM SCHEDULER
Minimum-Disruption Timetable Repair

Purpose:
    Repair an existing examination timetable when
    scheduling constraints change.

Examples:
    - A room becomes unavailable.
    - A professor becomes unavailable.
    - An examination changes its allowed time slots.
    - Room availability or capacity changes.

Objective:
    Minimize the total number of examinations
    whose time slot or room assignment changes.

Assignment format:
    exam_id -> (slot_index, room_id)

No Teaching Assistant dependencies.
"""

from solver_core import solve


# ============================================================
# NORMALIZE ASSIGNMENTS
# ============================================================

def normalize_assignment(value):
    """
    Validate and normalize a timetable assignment.

    Accepts:
        (slot_index, room_id)
        [slot_index, room_id]

    Returns:
        (slot_index, room_id)
    """

    if not isinstance(value, (tuple, list)):
        raise ValueError(
            "Schedule assignments must be "
            "(slot_index, room_id) pairs."
        )

    if len(value) != 2:
        raise ValueError(
            "Each schedule assignment must contain "
            "exactly two values: slot and room."
        )

    slot, room = value

    if type(slot) is not int:
        raise ValueError(
            "Schedule slot index must be an integer."
        )

    if not isinstance(room, str) or not room:
        raise ValueError(
            "Schedule room ID must be a nonempty string."
        )

    return slot, room


# ============================================================
# MINIMUM-DISRUPTION REPAIR
# ============================================================

def repair_schedule(
    exams,
    rooms,
    time_slots,
    conflicts,
    original_schedule,
    professors=None,
    timeout_seconds=30,
):
    """
    Repair an existing schedule while minimizing
    the number of changed examinations.

    Parameters:
        exams:
            Dictionary containing examination data.

        rooms:
            Dictionary containing available rooms.

        time_slots:
            List of examination time slots.

        conflicts:
            Student examination conflict graph.

        original_schedule:
            Existing timetable:
                {exam_id: (slot, room)}

        professors:
            Professor information and availability.

        timeout_seconds:
            Maximum solving time.

    Returns:
        Solver result containing:
            - schedule
            - success
            - status
            - changes
            - changed_exams
            - moved_exams
            - preserved_exams
    """

    # --------------------------------------------------------
    # 1. VALIDATE ORIGINAL SCHEDULE
    # --------------------------------------------------------

    if set(original_schedule) != set(exams):

        raise ValueError(
            "Original schedule must contain "
            "every examination exactly once."
        )

    original = {}

    for exam_id, value in original_schedule.items():

        original[exam_id] = normalize_assignment(
            value
        )

    # --------------------------------------------------------
    # 2. DEFINE MINIMUM-DISRUPTION COST
    # --------------------------------------------------------

    def cost(exam_id, value):
        """
        Zero cost if the original assignment is kept.

        Unit cost if either the time slot or
        examination room changes.
        """

        candidate = normalize_assignment(
            value
        )

        return int(
            candidate != original[exam_id]
        )

    # --------------------------------------------------------
    # 3. EXECUTE CSP SOLVER
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
    # 4. IDENTIFY SCHEDULE CHANGES
    # --------------------------------------------------------

    changes = []

    moved_exams = 0

    if result["success"]:

        for exam_id, new_value in (
            result["schedule"].items()
        ):

            old_assignment = original[
                exam_id
            ]

            new_assignment = normalize_assignment(
                new_value
            )

            if old_assignment != new_assignment:

                # A moved examination is one whose
                # time slot changes.
                if (
                    old_assignment[0]
                    != new_assignment[0]
                ):
                    moved_exams += 1

                changes.append({
                    "exam": exam_id,
                    "old_assignment": old_assignment,
                    "new_assignment": new_assignment,
                })

    # --------------------------------------------------------
    # 5. ADD REPAIR METRICS
    # --------------------------------------------------------

    result["changes"] = changes

    result["changed_exams"] = (
        len(changes)
        if result["success"]
        else None
    )

    result["moved_exams"] = (
        moved_exams
        if result["success"]
        else None
    )

    result["preserved_exams"] = (
        len(exams) - len(changes)
        if result["success"]
        else None
    )

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

    # Load university data.
    data = get_university_data()

    # Build student conflict graph.
    conflicts = generate_conflicts(
        data["exams"],
        get_course_students(
            data["students"]
        ),
    )

    # Generate a valid starting schedule.
    original_result = solve(
        data["exams"],
        data["rooms"],
        data["time_slots"],
        conflicts,
        mrv=True,
        fc=True,
        professors=data["professors"],
        timeout_seconds=30,
    )

    if not original_result["success"]:

        print(
            "Unable to generate the original schedule."
        )

    else:

        original_schedule = (
            original_result["schedule"]
        )

        # Choose the first scheduled examination.
        first_exam = next(
            iter(original_schedule)
        )

        slot, room = normalize_assignment(
            original_schedule[first_exam]
        )

        print(
            "Original assignment:",
            first_exam,
            (slot, room),
        )

        # Simulate a room closure at that time slot.
        data["rooms"][room].setdefault(
            "unavailable_slots",
            [],
        ).append(slot)

        print(
            "Simulated room closure:",
            room,
            "at slot",
            slot,
        )

        # Repair the timetable.
        result = repair_schedule(
            data["exams"],
            data["rooms"],
            data["time_slots"],
            conflicts,
            original_schedule,
            professors=data["professors"],
            timeout_seconds=30,
        )

        print(
            "Repair status:",
            result["status"],
        )

        print(
            "Changed examinations:",
            result["changed_exams"],
        )

        print(
            "Moved examinations:",
            result["moved_exams"],
        )

        print(
            "Preserved examinations:",
            result["preserved_exams"],
        )

        if result["success"]:

            validation = validate_schedule(
                data["exams"],
                data["rooms"],
                data["time_slots"],
                data["students"],
                result["schedule"],
                data["professors"],
            )

            print(
                "Schedule valid:",
                validation["valid"],
            )

            print(
                "Changes:",
                result["changes"],
            )
