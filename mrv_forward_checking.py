# ==========================================
# SMART EXAM SCHEDULER
# MRV + Forward Checking
# ==========================================

import time


def mrv_forward_checking(exams, rooms, time_slots, conflicts):

    schedule = {}

    assignments_attempted = 0
    backtracks = 0

    start_time = time.perf_counter()

        # CREATE INITIAL DOMAINS

    domains = {}

    for exam_code in exams:

        domains[exam_code] = []

        for slot_index in range(len(time_slots)):

            for room_id in rooms:

                exam_capacity = rooms[room_id].get(
                    "exam_capacity",
                    rooms[room_id]["capacity"]
                )

                if exams[exam_code]["students"] <= exam_capacity:

                    domains[exam_code].append(
                        (slot_index, room_id)
                    )
    # ======================================
    # CHECK ASSIGNMENT COMPATIBILITY
    # ======================================

    def compatible(exam1, value1, exam2, value2):

        slot1, room1 = value1
        slot2, room2 = value2

        # Different time slots
        if slot1 != slot2:
            return True

        # Same classroom and time
        if room1 == room2:
            return False

        # Shared students
        if exam2 in conflicts[exam1]:
            return False

        return True

    # ======================================
    # MRV: SELECT MOST RESTRICTED EXAM
    # ======================================

    def select_mrv(current_domains):

        unassigned = [
            exam
            for exam in exams
            if exam not in schedule
        ]

        selected_exam = min(
            unassigned,
            key=lambda exam: len(current_domains[exam])
        )

        return selected_exam

    # ======================================
    # RECURSIVE SEARCH
    # ======================================

    def backtrack(current_domains):

        nonlocal assignments_attempted
        nonlocal backtracks

        # Base case: All exams scheduled
        if len(schedule) == len(exams):
            return True

        # Select an exam using MRV
        exam_code = select_mrv(current_domains)

        # No possible assignment
        if len(current_domains[exam_code]) == 0:
            return False

        # Try remaining domain values
        for value in current_domains[exam_code]:

            assignments_attempted += 1

            # Check consistency with
            # already assigned exams
            valid = True

            for other_exam, other_value in schedule.items():

                if not compatible(
                    exam_code,
                    value,
                    other_exam,
                    other_value
                ):
                    valid = False
                    break

            if not valid:
                continue

            # Assign the exam
            schedule[exam_code] = value

            # Copy remaining domains
            new_domains = {
                exam: list(values)
                for exam, values in current_domains.items()
            }

            # ==================================
            # FORWARD CHECKING
            # ==================================

            future_valid = True

            for future_exam in exams:

                if future_exam in schedule:
                    continue

                new_domains[future_exam] = [

                    future_value

                    for future_value in new_domains[future_exam]

                    if compatible(
                        exam_code,
                        value,
                        future_exam,
                        future_value
                    )
                ]

                # Domain wipeout
                if len(new_domains[future_exam]) == 0:

                    future_valid = False
                    break

            # Continue recursive search
            if future_valid:

                if backtrack(new_domains):
                    return True

            # Undo assignment
            del schedule[exam_code]

            backtracks += 1

        return False

    # ======================================
    # EXECUTE SEARCH
    # ======================================

    success = backtrack(domains)

    execution_time = time.perf_counter() - start_time

    return {
        "success": success,
        "schedule": schedule if success else {},
        "execution_time": execution_time,
        "assignments_attempted": assignments_attempted,
        "backtracks": backtracks
    }

