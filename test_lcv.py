# ==========================================
# SMART EXAM SCHEDULER
# LCV Automated Tests
# ==========================================

import unittest

from mrv_forward_checking import mrv_forward_checking
from mrv_fc_lcv import mrv_fc_lcv
from validator import validate_schedule


class TestLCV(unittest.TestCase):

    def setUp(self):

        self.exams = {

            "MATH": {
                "students": 30,
                "available_slots": [0, 1]
            },

            "PHYS": {
                "students": 30,
                "available_slots": [0, 2]
            },

            "CHEM": {
                "students": 30,
                "available_slots": [0, 2]
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

    # ======================================
    # TEST VALID LCV SCHEDULE
    # ======================================

    def test_valid_schedule(self):

        result = mrv_fc_lcv(

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

    # ======================================
    # TEST LCV VALUE ORDERING
    # ======================================

    def test_value_selection(self):

        result = mrv_fc_lcv(

            self.exams,

            self.rooms,

            self.slots,

            self.conflicts
        )

        # LCV should choose Tuesday for MATH
        # because it preserves more options

        self.assertEqual(

            result["schedule"]["MATH"],

            (1, "ROOM_A")
        )

        self.assertEqual(

            result["backtracks"],

            0
        )

    # ======================================
    # COMPARE SEARCH EFFORT
    # ======================================

    def test_search_effort(self):

        original = mrv_forward_checking(

            self.exams,

            self.rooms,

            self.slots,

            self.conflicts
        )

        enhanced = mrv_fc_lcv(

            self.exams,

            self.rooms,

            self.slots,

            self.conflicts
        )

        self.assertTrue(original["success"])

        self.assertTrue(enhanced["success"])

        self.assertLess(

            enhanced["assignments_attempted"],

            original["assignments_attempted"]
        )

    # ======================================
    # TEST TIMEOUT
    # ======================================

    def test_timeout(self):

        result = mrv_fc_lcv(

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


if __name__ == "__main__":

    unittest.main()