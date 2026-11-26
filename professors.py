# Professor generation

import random


def generate_professors(
    exams,
    time_slots,
    seed=42
):

    rng = random.Random(seed)

    professors = {}

    days = list(dict.fromkeys(
        slot["day"]
        for slot in time_slots
    ))

    for exam in exams.values():

        professor_id = exam["professor_id"]

        if professor_id not in professors:

            preferred_days = rng.sample(
                days,
                min(2, len(days))
            )

            preferred_slots = [
                index
                for index, slot in enumerate(time_slots)
                if slot["day"] in preferred_days
            ]

            other_days = [
                day
                for day in days
                if day not in preferred_days
            ]

            avoid_days = (
                [rng.choice(other_days)]
                if other_days else []
            )

            professors[professor_id] = {
                "name": f"Professor {professor_id}",
                "departments": [],
                "unavailable_days": [],
                "unavailable_slots": [],
                "preferred_days": preferred_days,
                "preferred_slots": preferred_slots,
                "avoid_days": avoid_days
            }

        department = exam.get(
            "department",
            "General"
        )

        departments = professors[
            professor_id
        ]["departments"]

        if department not in departments:

            departments.append(department)

    return professors