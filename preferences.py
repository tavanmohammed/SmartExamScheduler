
"""
SMART EXAM SCHEDULER
Professor Preference Evaluation

Soft constraints:
    1. Preferred examination days
    2. Preferred examination time slots
    3. Days professors prefer to avoid

Hard constraints are enforced separately by
the CSP solver and independent validator.

Lower penalty = better preference satisfaction.

Assignment format:
    exam_id -> (slot_index, room_id)
"""


# ============================================================
# DEFAULT SOFT-CONSTRAINT WEIGHTS
# ============================================================

DEFAULT_WEIGHTS = {
    "preferred_day": 5,
    "preferred_slot": 3,
    "avoid_day": 10,
}


# ============================================================
# NORMALIZE ASSIGNMENTS
# ============================================================

def normalize_assignment(value):
    """
    Accept a two-value schedule assignment:

        (slot_index, room_id)
        [slot_index, room_id]

    Return a normalized tuple.
    """

    if not isinstance(value, (list, tuple)):
        raise ValueError(
            "Assignment must be a list or tuple."
        )

    if len(value) != 2:
        raise ValueError(
            "Assignment must contain exactly "
            "two values: slot and room."
        )

    slot, room = value

    if type(slot) is not int:
        raise ValueError(
            "Slot must be an integer."
        )

    if not isinstance(room, str) or not room:
        raise ValueError(
            "Room must be a nonempty string."
        )

    return slot, room


# ============================================================
# CALCULATE PENALTY FOR ONE EXAMINATION
# ============================================================

def assignment_penalty(
    exam_id,
    value,
    exams,
    time_slots,
    professors,
    weights=None,
):
    """
    Calculate preference penalty for an exam.

    A penalty is applied when:
        - The professor's preferred day is missed.
        - The professor's preferred slot is missed.
        - The exam is placed on an avoided day.

    Returns:
        Nonnegative numerical penalty.
    """

    weights = {
        **DEFAULT_WEIGHTS,
        **(weights or {}),
    }

    slot, room = normalize_assignment(value)

    if not 0 <= slot < len(time_slots):
        raise ValueError(
            f"Invalid slot index: {slot}"
        )

    day = time_slots[slot]["day"]

    professor_id = exams[
        exam_id
    ].get("professor_id")

    professor = professors.get(
        professor_id,
        {},
    )

    preferred_days = professor.get(
        "preferred_days",
        [],
    )

    preferred_slots = professor.get(
        "preferred_slots",
        [],
    )

    avoid_days = professor.get(
        "avoid_days",
        [],
    )

    penalty = 0

    # --------------------------------------------------------
    # PREFERRED DAY
    # --------------------------------------------------------

    if (
        preferred_days
        and day not in preferred_days
    ):
        penalty += weights["preferred_day"]

    # --------------------------------------------------------
    # PREFERRED TIME SLOT
    # --------------------------------------------------------

    if (
        preferred_slots
        and slot not in preferred_slots
    ):
        penalty += weights["preferred_slot"]

    # --------------------------------------------------------
    # AVOIDED DAY
    # --------------------------------------------------------

    if day in avoid_days:
        penalty += weights["avoid_day"]

    return penalty


# ============================================================
# EVALUATE COMPLETE TIMETABLE PREFERENCES
# ============================================================

def evaluate_preferences(
    schedule,
    exams,
    time_slots,
    professors,
    weights=None,
):
    """
    Evaluate professor preference satisfaction
    across an examination timetable.

    Returns:
        total_penalty
        satisfied_exams
        exams_with_preferences
        satisfaction_rate
        details

    Satisfaction is measured per exam with
    at least one professor preference.
    """

    weights = {
        **DEFAULT_WEIGHTS,
        **(weights or {}),
    }

    details = []

    total_penalty = 0

    satisfied_exams = 0
    exams_with_preferences = 0

    for exam_id, value in schedule.items():

        slot, room = normalize_assignment(value)

        professor_id = exams[
            exam_id
        ].get("professor_id")

        professor = professors.get(
            professor_id,
            {},
        )

        # ----------------------------------------------------
        # DETERMINE WHETHER PREFERENCES EXIST
        # ----------------------------------------------------

        preferred_days = professor.get(
            "preferred_days",
            [],
        )

        preferred_slots = professor.get(
            "preferred_slots",
            [],
        )

        avoid_days = professor.get(
            "avoid_days",
            [],
        )

        has_preferences = bool(
            preferred_days
            or preferred_slots
            or avoid_days
        )

        # ----------------------------------------------------
        # CALCULATE EXAM PENALTY
        # ----------------------------------------------------

        penalty = assignment_penalty(
            exam_id,
            (slot, room),
            exams,
            time_slots,
            professors,
            weights=weights,
        )

        total_penalty += penalty

        # ----------------------------------------------------
        # CALCULATE SATISFACTION
        # ----------------------------------------------------

        if has_preferences:

            exams_with_preferences += 1

            if penalty == 0:
                satisfied_exams += 1

        # ----------------------------------------------------
        # STORE EXAMINATION DETAILS
        # ----------------------------------------------------

        details.append({
            "exam": exam_id,
            "professor_id": professor_id,
            "slot": slot,
            "room": room,
            "penalty": penalty,
            "has_preferences": has_preferences,
        })

    # --------------------------------------------------------
    # CALCULATE SATISFACTION RATE
    # --------------------------------------------------------

    satisfaction_rate = (
        100 * satisfied_exams / exams_with_preferences
        if exams_with_preferences
        else None
    )

    return {
        "total_penalty": total_penalty,

        "satisfied_exams": satisfied_exams,

        "exams_with_preferences":
            exams_with_preferences,

        "satisfaction_rate": satisfaction_rate,

        "details": details,
    }


# ============================================================
# OPTIONAL DIRECT TEST
# ============================================================

if __name__ == "__main__":

    from university_data import get_university_data

    from conflicts import (
        get_course_students,
        generate_conflicts,
    )

    from algorithm_selector import run_algorithm

    data = get_university_data()

    conflicts = generate_conflicts(
        data["exams"],
        get_course_students(
            data["students"]
        ),
    )

    result = run_algorithm(
        "MRV + FC + Degree",
        data,
        conflicts,
        timeout_seconds=30,
    )

    if not result["success"]:

        print(
            "Could not generate a valid timetable."
        )

    else:

        evaluation = evaluate_preferences(
            result["schedule"],
            data["exams"],
            data["time_slots"],
            data["professors"],
        )

        print("\nPROFESSOR PREFERENCE EVALUATION")
        print("--------------------------------")

        print(
            "Total penalty:",
            evaluation["total_penalty"],
        )

        print(
            "Satisfied examinations:",
            evaluation["satisfied_exams"],
        )

        print(
            "Examinations with preferences:",
            evaluation["exams_with_preferences"],
        )

        print(
            "Satisfaction rate:",
            evaluation["satisfaction_rate"],
        )

        print("\nExamination details:")

        for detail in evaluation["details"]:
            print(detail)
