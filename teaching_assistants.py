# Teaching assistant generation

import random


def calculate_required_tas(
    student_count,
    students_per_ta=30
):

    # Validate the input.
    if student_count < 0 or students_per_ta <= 0:
        raise ValueError("Invalid staffing parameters")

    # Calculate the number of TAs based on enrollment.
    required_tas = (
        student_count + students_per_ta - 1
    ) // students_per_ta

    # Every examination requires at least two TAs.
    return max(2, required_tas)

def generate_teaching_assistants(
    exams,
    time_slots,
    witness,
    seed=42
):

    rng = random.Random(seed)

    assistants = {}

    workloads = {}
    occupied = {}

    next_id = 1

    # Construct qualified TA resources around
    # a known-feasible experimental timetable.

    for exam_id, exam in exams.items():

        slot, room = witness[exam_id][:2]

        day = time_slots[slot]["day"]

        department = exam.get(
            "department",
            "General"
        )

        assigned = []

        required = exam.get("required_tas", 0)

        for _ in range(required):

            candidates = [
                ta_id
                for ta_id, ta in assistants.items()
                if department in ta["departments"]
                and ta_id not in assigned
                and slot not in occupied[ta_id]
                and workloads[ta_id].get(day, 0) < 2
            ]

            if candidates:

                ta_id = rng.choice(candidates)

            else:

                ta_id = f"TA{next_id:03d}"

                next_id += 1

                assistants[ta_id] = {
                    "name": f"Teaching Assistant {ta_id}",
                    "departments": [department],
                    "qualified_courses": [],
                    "unavailable_days": [],
                    "unavailable_slots": [],
                    "preferred_slots": [],
                    "max_exams_per_day": 2
                }

                workloads[ta_id] = {}
                occupied[ta_id] = set()

            assistants[ta_id][
                "qualified_courses"
            ].append(exam_id)

            occupied[ta_id].add(slot)

            workloads[ta_id][day] = (
                workloads[ta_id].get(day, 0) + 1
            )

            assigned.append(ta_id)

        witness[exam_id] = (
            slot,
            room,
            tuple(sorted(assigned))
        )

    # Add a small number of alternative qualifications.
    for ta in assistants.values():

        alternatives = [
            exam_id
            for exam_id, exam in exams.items()
            if exam["department"] in ta["departments"]
            and exam_id not in ta["qualified_courses"]
        ]

        ta["qualified_courses"].extend(
            rng.sample(
                alternatives,
                min(2, len(alternatives))
            )
        )

    return assistants