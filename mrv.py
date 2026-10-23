# ==========================================
# SMART EXAM SCHEDULER
# Backtracking + MRV Heuristic
# ==========================================

import time


def mrv_backtracking(exams, rooms, time_slots, conflicts):

    # Store exam assignments
    schedule = {}

    # Performance counters
    assignments_attempted = 0
    backtracks = 0

    # Start timer
    start_time = time.perf_counter()

    # ======================================
    # CHECK ASSIGNMENT VALIDITY
    # ======================================

    def is_valid(exam_code, slot_index, room_id):

        # Constraint 1: Room capacity
        exam_students = exams[exam_code]["students"]
        room_capacity = rooms[room_id]["exam_capacity"]

        if exam_students > room_capacity:
            return False

        for scheduled_exam, assignment in schedule.items():

            scheduled_slot, scheduled_room = assignment

            if slot_index == scheduled_slot:

                # Constraint 2: Room collision
                if room_id == scheduled_room:
                    return False

                # Constraint 3: Student conflicts
                if scheduled_exam in conflicts[exam_code]:
                    return False

        return True

    # ======================================
    # FIND REMAINING VALID VALUES
    # ======================================

    def get_valid_values(exam_code):

        valid_values = []

        for slot_index in range(len(time_slots)):

            for room_id in rooms:

                if is_valid(exam_code, slot_index, room_id):

                    valid_values.append(
                        (slot_index, room_id)
                    )

        return valid_values

    # ======================================
    # MRV HEURISTIC
    # ======================================

    def select_mrv_exam():

        selected_exam = None
        minimum_values = float("inf")
        selected_domain = []

        for exam_code in exams:

            # Skip already scheduled exams
            if exam_code in schedule:
                continue

            # Find remaining valid assignments
            valid_values = get_valid_values(exam_code)

            number_of_values = len(valid_values)

            # Select the most restricted exam
            if number_of_values < minimum_values:

                minimum_values = number_of_values
                selected_exam = exam_code
                selected_domain = valid_values

        return selected_exam, selected_domain

    # ======================================
    # RECURSIVE BACKTRACKING WITH MRV
    # ======================================

    def backtrack():

        nonlocal assignments_attempted
        nonlocal backtracks

        # BASE CASE:
        # All exams have been scheduled
        if len(schedule) == len(exams):
            return True

        # Select exam using MRV
        exam_code, valid_values = select_mrv_exam()

        # No possible assignment:
        # This branch cannot produce a solution
        if len(valid_values) == 0:
            return False

        # Try remaining valid assignments
        for slot_index, room_id in valid_values:

            assignments_attempted += 1

            # Assign exam
            schedule[exam_code] = (
                slot_index,
                room_id
            )

            # Recursively schedule remaining exams
            if backtrack():
                return True

            # Undo assignment
            del schedule[exam_code]

            backtracks += 1

        return False

    # Run algorithm
    success = backtrack()

    # Stop timer
    execution_time = time.perf_counter() - start_time

    return {
        "success": success,
        "schedule": schedule if success else {},
        "execution_time": execution_time,
        "assignments_attempted": assignments_attempted,
        "backtracks": backtracks
    }