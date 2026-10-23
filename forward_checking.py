# ==========================================
# SMART EXAM SCHEDULER
# Backtracking + Forward Checking
# ==========================================

import time


def forward_checking(exams, rooms, time_slots, conflicts):

    schedule = {}

    assignments_attempted = 0
    backtracks = 0

    start_time = time.perf_counter()

    exam_list = list(exams.keys())

    # ======================================
    # CREATE INITIAL DOMAINS
    # ======================================

    domains = {}

    for exam_code in exams:

        domains[exam_code] = []

        for slot_index in range(len(time_slots)):

            for room_id in rooms:

                # Get usable examination capacity
                exam_capacity = rooms[room_id].get(
                    "exam_capacity",
                    rooms[room_id]["capacity"]
                )

                # Only use rooms with enough seats
                if exams[exam_code]["students"] <= exam_capacity:

                    domains[exam_code].append(
                        (slot_index, room_id)
                    )


    # ======================================
    # CHECK TWO EXAM ASSIGNMENTS
    # ======================================

    def compatible(exam1, value1, exam2, value2):

        slot1, room1 = value1
        slot2, room2 = value2

        # Different times cannot overlap
        if slot1 != slot2:
            return True

        # Same room at the same time
        if room1 == room2:
            return False

        # Students registered in both exams
        if exam2 in conflicts[exam1]:
            return False

        return True

    # ======================================
    # RECURSIVE BACKTRACKING
    # ======================================

    def backtrack(index, current_domains):

        nonlocal assignments_attempted
        nonlocal backtracks

        # All exams have been scheduled
        if index == len(exam_list):
            return True

        exam_code = exam_list[index]

        # Try remaining possible assignments
        for value in current_domains[exam_code]:

            assignments_attempted += 1

            # Check against assigned exams
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

            # Temporarily assign the exam
            schedule[exam_code] = value

            # Copy the remaining domains
            new_domains = {
                exam: list(values)
                for exam, values in current_domains.items()
            }

            # ==================================
            # FORWARD CHECKING
            # ==================================

            future_valid = True

            for future_exam in exam_list[index + 1:]:

                # Remove values that conflict
                # with the current assignment
                new_domains[future_exam] = [

                    future_value

                    for future_value
                    in new_domains[future_exam]

                    if compatible(
                        exam_code,
                        value,
                        future_exam,
                        future_value
                    )
                ]

                # DOMAIN WIPEOUT:
                # No possible values remain
                if len(new_domains[future_exam]) == 0:

                    future_valid = False
                    break

            # Continue only if future
            # exams still have options
            if future_valid:

                if backtrack(index + 1, new_domains):
                    return True

            # Undo the current assignment
            del schedule[exam_code]

            backtracks += 1

        return False

    # ======================================
    # RUN THE ALGORITHM
    # ======================================

    success = backtrack(0, domains)

    execution_time = time.perf_counter() - start_time

    return {
        "success": success,
        "schedule": schedule if success else {},
        "execution_time": execution_time,
        "assignments_attempted": assignments_attempted,
        "backtracks": backtracks
    }
