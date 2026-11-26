# ==========================================
# SMART EXAM SCHEDULER
# Rescheduling Automated Tests
# ==========================================

import unittest

from rescheduling import repair_schedule
from validator import validate_schedule


class TestRescheduling(unittest.TestCase):

    def setUp(self):

        self.exams = {

            "ENG-MATH": {

                "students": 30,

                "professor_id": "P1"
            },

            "SCI-MATH": {

                "students": 40,

                "professor_id": "P1"
            },

            "PHYS": {

                "students": 50,

                "professor_id": "P2"
            }
        }

        self.rooms = {

            "ROOM_A": {

                "capacity": 100
            },

            "ROOM_B": {

                "capacity": 100
            }
        }

        self.slots = [

            {
                "day": "Monday",
                "time": "9 AM"
            },

            {
                "day": "Tuesday",
                "time": "9 AM"
            },

            {
                "day": "Wednesday",
                "time": "9 AM"
            },

            {
                "day": "Thursday",
                "time": "9 AM"
            }
        ]

        self.conflicts = {

            exam: []

            for exam in self.exams
        }

        self.original_schedule = {

            "ENG-MATH": (0, "ROOM_A"),

            "SCI-MATH": (1, "ROOM_A"),

            "PHYS": (2, "ROOM_B")
        }

    # ======================================
    # TEST NO DISRUPTION
    # ======================================

    def test_no_changes(self):

        result = repair_schedule(

            self.exams,

            self.rooms,

            self.slots,

            self.conflicts,

            self.original_schedule
        )

        self.assertTrue(result["success"])

        self.assertTrue(result["optimal"])

        self.assertEqual(
            result["moved_exams"],
            0
        )

        self.assertEqual(
            result["schedule"],
            self.original_schedule
        )

    # ======================================
    # TEST PROFESSOR CANCELLATION
    # ======================================

    def test_professor_unavailable(self):

        professors = {

            "P1": {

                "unavailable_days": [
                    "Monday"
                ]
            }
        }

        result = repair_schedule(

            self.exams,

            self.rooms,

            self.slots,

            self.conflicts,

            self.original_schedule,

            professors=professors
        )

        self.assertTrue(result["success"])

        self.assertTrue(result["optimal"])

        # Only one exam should move
        self.assertEqual(
            result["moved_exams"],
            1
        )

        self.assertEqual(
            result["preserved_exams"],
            2
        )

        validation = validate_schedule(

            self.exams,

            self.rooms,

            self.slots,

            {},

            result["schedule"],

            professors
        )

        self.assertTrue(validation["valid"])

    # ======================================
    # TEST ROOM CLOSURE
    # ======================================

    def test_room_closure(self):

        self.rooms["ROOM_A"][
            "unavailable_slots"
        ] = [0]

        result = repair_schedule(

            self.exams,

            self.rooms,

            self.slots,

            self.conflicts,

            self.original_schedule
        )

        self.assertTrue(result["success"])

        self.assertTrue(result["optimal"])

        self.assertEqual(
            result["moved_exams"],
            1
        )

        self.assertNotEqual(

            result["schedule"]["ENG-MATH"],

            (0, "ROOM_A")
        )

    # ======================================
    # TEST IMPOSSIBLE REPAIR
    # ======================================

    def test_impossible_repair(self):

        professors = {

            "P1": {

                "unavailable_days": [

                    "Monday",

                    "Tuesday",

                    "Wednesday",

                    "Thursday"
                ]
            }
        }

        result = repair_schedule(

            self.exams,

            self.rooms,

            self.slots,

            self.conflicts,

            self.original_schedule,

            professors=professors
        )

        self.assertFalse(result["success"])

        self.assertEqual(
            result["status"],
            "UNSAT"
        )

    # ======================================
    # TEST TIMEOUT
    # ======================================

    def test_timeout(self):

        result = repair_schedule(

            self.exams,

            self.rooms,

            self.slots,

            self.conflicts,

            self.original_schedule,

            timeout_seconds=0
        )

        self.assertEqual(

            result["status"],

            "TIMEOUT"
        )


if __name__ == "__main__":

    unittest.main()