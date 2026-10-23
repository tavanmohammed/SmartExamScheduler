# ==========================================
# SMART EXAM SCHEDULER
# Automatic Schedule Validator
# ==========================================


def validate_schedule(exams, rooms, time_slots, students, schedule):

    errors = []

    # ======================================
    # 1. CHECK ALL EXAMS ARE SCHEDULED
    # ======================================

    if set(schedule.keys()) != set(exams.keys()):

        errors.append(
            "Some exams are missing or unknown exams were assigned."
        )

    # ======================================
    # 2. CHECK ROOM CAPACITY
    # ======================================

    for exam_code, assignment in schedule.items():

        # Unknown exams cannot be validated
        if exam_code not in exams:
            continue

        slot_index, room_id = assignment

        # Check classroom exists
        if room_id not in rooms:

            errors.append(
                f"{exam_code}: Unknown classroom {room_id}"
            )

            continue

        # Check time slot exists
        if (
            not isinstance(slot_index, int)
            or not 0 <= slot_index < len(time_slots)
        ):

            errors.append(
                f"{exam_code}: Invalid time slot"
            )

            continue

        # Get examination capacity
        room_capacity = rooms[room_id].get(
            "exam_capacity",
            rooms[room_id]["capacity"]
        )

        exam_students = exams[exam_code]["students"]

        if exam_students > room_capacity:

            errors.append(
                f"{exam_code}: Room {room_id} is too small"
            )

    # ======================================
    # 3. CHECK ROOM COLLISIONS
    # ======================================

    exam_codes = list(schedule.keys())

    for i in range(len(exam_codes)):

        for j in range(i + 1, len(exam_codes)):

            exam1 = exam_codes[i]
            exam2 = exam_codes[j]

            slot1, room1 = schedule[exam1]
            slot2, room2 = schedule[exam2]

            if slot1 == slot2 and room1 == room2:

                errors.append(
                    f"Room conflict: {exam1} and {exam2}"
                )

    # ======================================
    # 4. CHECK STUDENT EXAM CONFLICTS
    # ======================================

    for student_id, information in students.items():

        registered_courses = information["courses"]

        # Store the time slots assigned
        # to this student's exams
        used_slots = {}

        for course in registered_courses:

            if course not in schedule:
                continue

            slot_index, room_id = schedule[course]

            if slot_index in used_slots:

                errors.append(
                    f"Student {student_id} has overlapping "
                    f"exams: {used_slots[slot_index]} and {course}"
                )

            else:

                used_slots[slot_index] = course

    # ======================================
    # 5. RETURN VALIDATION RESULTS
    # ======================================

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }

