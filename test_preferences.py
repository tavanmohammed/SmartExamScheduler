# ==========================================
# SMART EXAM SCHEDULER
# Professor Preference Tests
# ==========================================

import unittest

from preferences import (
    assignment_penalty,
    evaluate_preferences
)

from preference_optimizer import optimize_preferences

from validator import validate_schedule


class TestPreferences(unittest.TestCase):

    def setUp(self):

        self.exams = {

            "ENG-MATH": {

                "students": 30,

                "professor_id": "P1"
            },

            "SCI-MATH": {

                "students": 40,

                "professor_id": "P1"
            }
        }

        self.rooms = {

            "ROOM_A": {

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
            }
        ]

        self.conflicts = {

            exam: []

            for exam in self.exams
        }

        self.professors = {

            "P1": {

                "preferred_days": [

                    "Monday",

                    "Wednesday"
                ],

                "preferred_slots": [0, 2],

                "avoid_days": ["Tuesday"]
            }
        }

    # ======================================
    # TEST PENALTY CALCULATION
    # ======================================

    def test_penalty(self):

        penalty = assignment_penalty(

            "ENG-MATH",

            (1, "ROOM_A"),

            self.exams,

            self.slots,

            self.professors
        )

        # Tuesday violates all three preferences
        # 5 + 3 + 10 = 18

        self.assertEqual(penalty, 18)

    # ======================================
    # TEST OPTIMAL PREFERENCES
    # ======================================

    def test_optimal_preferences(self):

        result = optimize_preferences(

            self.exams,

            self.rooms,

            self.slots,

            self.conflicts,

            self.professors
        )

        self.assertTrue(result["success"])

        self.assertTrue(result["optimal"])

        self.assertEqual(

            result["total_penalty"],

            0
        )

        self.assertEqual(

            result["preference_results"][
                "satisfaction_rate"
            ],

            100
        )

        validation = validate_schedule(

            self.exams,

            self.rooms,

            self.slots,

            {},

            result["schedule"],

            self.professors
        )

        self.assertTrue(validation["valid"])

    # ======================================
    # HARD CONSTRAINTS OVERRIDE PREFERENCES
    # ======================================

    def test_hard_constraint_priority(self):

        self.professors["P1"][
            "unavailable_days"
        ] = ["Monday"]

        result = optimize_preferences(

            self.exams,

            self.rooms,

            self.slots,

            self.conflicts,

            self.professors
        )

        self.assertTrue(result["success"])

        self.assertTrue(result["optimal"])

        self.assertEqual(

            result["total_penalty"],

            18
        )

        for slot, room in result["schedule"].values():

            self.assertNotEqual(slot, 0)

        validation = validate_schedule(

            self.exams,

            self.rooms,

            self.slots,

            {},

            result["schedule"],

            self.professors
        )

        self.assertTrue(validation["valid"])

    # ======================================
    # TEST UNSAT
    # ======================================

    def test_unsat(self):

        self.professors["P1"][
            "unavailable_days"
        ] = ["Monday", "Tuesday"]

        result = optimize_preferences(

            self.exams,

            self.rooms,

            self.slots,

            self.conflicts,

            self.professors
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

        result = optimize_preferences(

            self.exams,

            self.rooms,

            self.slots,

            self.conflicts,

            self.professors,

            timeout_seconds=0
        )

        self.assertEqual(

            result["status"],

            "TIMEOUT"
        )

    # ======================================
    # TEST NO PREFERENCES
    # ======================================

    def test_no_preferences(self):

        result = optimize_preferences(

            self.exams,

            self.rooms,

            self.slots,

            self.conflicts,

            {}
        )

        self.assertTrue(result["success"])

        self.assertEqual(

            result["total_penalty"],

            0
        )

        self.assertIsNone(

            result["preference_results"][
                "satisfaction_rate"
            ]
        )


if __name__ == "__main__":

    unittest.main()