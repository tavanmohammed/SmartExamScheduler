# ==========================================
# SMART EXAM SCHEDULER
# Automated CSP Constraint Tests
# ==========================================

import unittest

from backtracking import basic_backtracking
from mrv import mrv_backtracking
from forward_checking import forward_checking
from mrv_forward_checking import mrv_forward_checking

from validator import validate_schedule

from dataset_generator import generate_dataset


SOLVERS = [

    basic_backtracking,

    mrv_backtracking,

    forward_checking,

    mrv_forward_checking
]


class TestConstraints(unittest.TestCase):

    def setUp(self):

        self.exams = {

            "ENG-MATH": {

                "students": 30,

                "professor_id": "P1"
            },

            "SCI-MATH": {

                "students": 80,

                "professor_id": "P1"
            }
        }

        self.rooms = {

            "large": {
                "exam_capacity": 100
            },

            "small": {
                "capacity": 40
            }
        }

        self.slots = [

            {
                "day": "Monday",
                "time": "09:00"
            },

            {
                "day": "Monday",
                "time": "13:00"
            },

            {
                "day": "Tuesday",
                "time": "09:00"
            }
        ]

        self.conflicts = {
            exam: []
            for exam in self.exams
        }

    # ======================================
    # TEST PROFESSOR DAILY LIMIT
    # ======================================

    def test_professor_day(self):

        for solver in SOLVERS:

            result = solver(
                self.exams,
                self.rooms,
                self.slots,
                self.conflicts
            )

            self.assertTrue(result["success"])

            validation = validate_schedule(
                self.exams,
                self.rooms,
                self.slots,
                {},
                result["schedule"]
            )

            self.assertTrue(validation["valid"])

            self.assertEqual(
                result["assignments_attempted"],
                len(self.exams) + result["backtracks"]
            )

    # ======================================
    # TEST IMPOSSIBLE PROBLEM
    # ======================================

    def test_unsat(self):

        for solver in SOLVERS:

            result = solver(
                self.exams,
                self.rooms,
                self.slots[:2],
                self.conflicts
            )

            self.assertEqual(
                result["status"],
                "UNSAT"
            )

    # ======================================
    # TEST PROFESSOR AVAILABILITY
    # ======================================

    def test_availability(self):

        professors = {

            "P1": {

                "unavailable_days": [
                    "Tuesday"
                ]
            }
        }

        for solver in SOLVERS:

            result = solver(
                self.exams,
                self.rooms,
                self.slots,
                self.conflicts,
                professors
            )

            self.assertEqual(
                result["status"],
                "UNSAT"
            )

    # ======================================
    # TEST BACKTRACKING
    # ======================================

    def test_backtrack(self):

        self.exams["SCI-MATH"]["professor_id"] = "P2"

        for solver in SOLVERS:

            result = solver(
                self.exams,
                self.rooms,
                self.slots[:1],
                self.conflicts
            )

            self.assertTrue(result["success"])

            self.assertEqual(
                result["schedule"]["ENG-MATH"],
                (0, "small")
            )

            self.assertEqual(
                result["assignments_attempted"],
                2 + result["backtracks"]
            )

    # ======================================
    # TEST TIMEOUT
    # ======================================

    def test_timeout(self):

        for solver in SOLVERS:

            result = solver(
                self.exams,
                self.rooms,
                self.slots,
                self.conflicts,
                timeout_seconds=0
            )

            self.assertEqual(
                result["status"],
                "TIMEOUT"
            )

    # ======================================
    # TEST GENERATED DATASETS
    # ======================================

    def test_witness(self):

        sizes = [

            "small",
            "medium",
            "large",
            "very_large",
            "extreme"
        ]

        for size in sizes:

            exams, rooms, slots, students, conflicts, witness = (
                generate_dataset(size)
            )

            validation = validate_schedule(
                exams,
                rooms,
                slots,
                students,
                witness
            )

            self.assertTrue(validation["valid"])

    # ======================================
    # TEST INVALID SCHEDULE
    # ======================================

    def test_invalid_schedule(self):

        invalid_schedule = {

            "ENG-MATH": (0, "small"),

            "SCI-MATH": (1, "large")
        }

        validation = validate_schedule(
            self.exams,
            self.rooms,
            self.slots,
            {},
            invalid_schedule
        )

        self.assertFalse(validation["valid"])


if __name__ == "__main__":

    unittest.main()