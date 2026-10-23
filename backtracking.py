# ==========================================
# SMART EXAM SCHEDULER
# Basic Backtracking CSP Algorithm
# ==========================================

import time


def basic_backtracking(exams, rooms, time_slots, conflicts):

    # Store the final exam assignments
    schedule = {}

    # Performance measurements
    assignments_attempted = 0
    backtracks = 0

    # List of exams to schedule
    exam_list = list(exams.keys())

    # Start execution timer
    start_time = time.perf_counter()

    # ======================================
    # CHECK IF AN ASSIGNMENT IS VALID
    # ======================================

    def is_valid(exam_code, slot_index, room_id):

        # Constraint 1: Classroom capacity
        exam_students = exams[exam_code]["students"]
        room_capacity = rooms[room_id].get(
        "exam_capacity",
        rooms[room_id]["capacity"]
)

        if exam_students > room_capacity:
            return False

        # Check already scheduled exams
        for scheduled_exam, assignment in schedule.items():

            scheduled_slot, scheduled_room = assignment

            # Constraint 2: Room cannot host
            # two exams at the same time
            if slot_index == scheduled_slot:

                if room_id == scheduled_room:
                    return False

                # Constraint 3: Students cannot
                # have overlapping exams
                if scheduled_exam in conflicts[exam_code]:
                    return False

        return True

    # ======================================
    # RECURSIVE BACKTRACKING ALGORITHM
    # ======================================

    def backtrack(index):

        nonlocal assignments_attempted
        nonlocal backtracks

        # BASE CASE:
        # All exams have been scheduled
        if index == len(exam_list):
            return True

        # Select the next exam
        exam_code = exam_list[index]

        # Try every available time slot
        for slot_index in range(len(time_slots)):

            # Try every classroom
            for room_id in rooms:

                assignments_attempted += 1

                # Check scheduling constraints
                if is_valid(exam_code, slot_index, room_id):

                    # Assign the exam
                    schedule[exam_code] = (
                        slot_index,
                        room_id
                    )

                    # Recursively schedule
                    # the next exam
                    if backtrack(index + 1):
                        return True

                    # BACKTRACK:
                    # Undo the previous assignment
                    del schedule[exam_code]

                    backtracks += 1

        # No valid assignment found
        return False

    # Start the backtracking search
    success = backtrack(0)

    # Stop execution timer
    end_time = time.perf_counter()

    execution_time = end_time - start_time

    # Return the results
    return {
        "success": success,
        "schedule": schedule if success else {},
        "execution_time": execution_time,
        "assignments_attempted": assignments_attempted,
        "backtracks": backtracks
    }