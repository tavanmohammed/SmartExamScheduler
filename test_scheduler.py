
"""
SMART EXAM SCHEDULER
Automated Correctness Tests - No Teaching Assistants

Tests:
- Student examination conflicts
- All seven AI algorithm configurations
- Room capacity and room type
- Professor daily limits and availability
- Examination and room availability
- Forward Checking
- MRV and Degree heuristics
- LCV and Adaptive LCV
- Impossible scheduling problems
- Timeouts
- Independent schedule validation
- Synthetic dataset generation
- Data reproducibility
- Input validation
- Automatic algorithm selection

Assignment format:
    exam_id -> (slot_index, room_id)
"""

import unittest

from university_data import get_university_data

from conflicts import (
    get_course_students,
    generate_conflicts,
)

from algorithm_selector import (
    ALGORITHMS,
    run_algorithm,
    select_algorithm,
)

from validator import validate_schedule
from dataset_generator import generate_dataset
from constraints import Constraints
from schemas import UniversityData
from degree_heuristic import select_mrv_degree
from adaptive_lcv import order_adaptive_lcv_values
from lcv import order_lcv_values


class TestScheduler(unittest.TestCase):

    # ========================================================
    # SETUP
    # ========================================================

    def setUp(self):

        self.data = get_university_data()

        self.conflicts = generate_conflicts(
            self.data["exams"],
            get_course_students(
                self.data["students"]
            ),
        )

    # ========================================================
    # HELPER METHODS
    # ========================================================

    def rules(self):

        return Constraints(
            self.data["exams"],
            self.data["rooms"],
            self.data["time_slots"],
            self.conflicts,
            self.data["professors"],
        )

    def validate(self, schedule):

        return validate_schedule(
            self.data["exams"],
            self.data["rooms"],
            self.data["time_slots"],
            self.data["students"],
            schedule,
            self.data["professors"],
        )

    def solve(
        self,
        algorithm="MRV + Forward Checking",
        timeout_seconds=10,
    ):

        return run_algorithm(
            algorithm,
            self.data,
            self.conflicts,
            timeout_seconds=timeout_seconds,
        )

    def valid_schedule(self):

        result = self.solve()

        self.assertTrue(
            result["success"],
            result.get("status"),
        )

        validation = self.validate(
            result["schedule"]
        )

        self.assertTrue(
            validation["valid"],
            validation["errors"],
        )

        return result["schedule"].copy()

    # ========================================================
    # 1. STUDENT CONFLICT GRAPH
    # ========================================================

    def test_student_conflicts(self):

        self.assertIn(
            "ENG-SOFE301",
            self.conflicts["ENG-MATH101"],
        )

        self.assertIn(
            "ENG-MATH101",
            self.conflicts["ENG-SOFE301"],
        )

        self.assertNotIn(
            "BUS-BUSI101",
            self.conflicts["ENG-MATH101"],
        )

    # ========================================================
    # 2. ALL SEVEN ALGORITHMS
    # ========================================================

    def test_all_algorithms(self):

        self.assertEqual(
            len(ALGORITHMS),
            7,
        )

        for algorithm in ALGORITHMS:

            with self.subTest(
                algorithm=algorithm
            ):

                result = self.solve(algorithm)

                self.assertTrue(
                    result["success"],
                    (
                        algorithm,
                        result.get("status"),
                    ),
                )

                validation = self.validate(
                    result["schedule"]
                )

                self.assertTrue(
                    validation["valid"],
                    validation["errors"],
                )

    # ========================================================
    # 3. TWO-VALUE ASSIGNMENT FORMAT
    # ========================================================

    def test_assignment_format(self):

        schedule = self.valid_schedule()

        for exam_id, assignment in (
            schedule.items()
        ):

            with self.subTest(exam=exam_id):

                self.assertEqual(
                    len(assignment),
                    2,
                )

                slot, room_id = assignment

                self.assertIs(
                    type(slot),
                    int,
                )

                self.assertIn(
                    room_id,
                    self.data["rooms"],
                )

    # ========================================================
    # 4. DOMAIN GENERATION
    # ========================================================

    def test_domain_generation(self):

        rules = self.rules()

        for exam_id in self.data["exams"]:

            domain = rules.domain(exam_id)

            self.assertTrue(
                domain,
                exam_id,
            )

            for value in domain:

                self.assertEqual(
                    len(value),
                    2,
                )

                self.assertTrue(
                    rules.unary_valid(
                        exam_id,
                        value,
                    )
                )

    # ========================================================
    # 5. ROOM CAPACITY
    # ========================================================

    def test_room_capacity(self):

        exam_id = "ENG-MATH101"

        value = (
            2,
            "ROOM_A",
        )

        self.assertTrue(
            self.rules().unary_valid(
                exam_id,
                value,
            )
        )

        self.data["rooms"]["ROOM_A"][
            "exam_capacity"
        ] = 1

        self.assertFalse(
            self.rules().unary_valid(
                exam_id,
                value,
            )
        )

    # ========================================================
    # 6. PROFESSOR DAILY LIMIT
    # ========================================================

    def test_professor_same_day(self):

        rules = self.rules()

        exam1 = "ENG-MATH101"
        exam2 = "SCI-MATH101"

        value1 = (
            2,
            "ROOM_A",
        )

        value2 = (
            3,
            "ROOM_B",
        )

        self.assertTrue(
            rules.unary_valid(
                exam1,
                value1,
            )
        )

        self.assertTrue(
            rules.unary_valid(
                exam2,
                value2,
            )
        )

        self.assertFalse(
            rules.compatible(
                exam1,
                value1,
                exam2,
                value2,
            )
        )

    # ========================================================
    # 7. PROFESSOR DIFFERENT DAYS
    # ========================================================

    def test_professor_different_days(self):

        rules = self.rules()

        self.assertTrue(
            rules.compatible(
                "ENG-MATH101",
                (2, "ROOM_A"),
                "SCI-MATH101",
                (4, "ROOM_B"),
            )
        )

    # ========================================================
    # 8. STUDENT SAME-DAY CONFLICT
    # ========================================================

    def test_student_same_day_conflict(self):

        rules = self.rules()

        exam1 = "ENG-MATH101"
        exam2 = "ENG-SOFE301"

        self.assertIn(
            exam2,
            self.conflicts[exam1],
        )

        self.assertEqual(
            self.data["time_slots"][2]["day"],
            self.data["time_slots"][3]["day"],
        )

        self.assertFalse(
            rules.compatible(
                exam1,
                (2, "ROOM_A"),
                exam2,
                (3, "ROOM_B"),
            )
        )

    # ========================================================
    # 9. STUDENT DIFFERENT DAYS
    # ========================================================

    def test_student_different_days(self):

        rules = self.rules()

        self.assertTrue(
            rules.compatible(
                "ENG-MATH101",
                (2, "ROOM_A"),
                "ENG-SOFE301",
                (4, "ROOM_B"),
            )
        )

    # ========================================================
    # 10. ROOM DOUBLE-BOOKING
    # ========================================================

    def test_room_double_booking(self):

        rules = self.rules()

        # Independent examinations, but same room/slot.
        self.assertFalse(
            rules.compatible(
                "ENG-SOFE301",
                (2, "ROOM_A"),
                "BUS-BUSI101",
                (2, "ROOM_A"),
            )
        )

        # Different rooms in the same slot are allowed
        # when there is no other conflict.
        self.assertTrue(
            rules.compatible(
                "ENG-SOFE301",
                (2, "ROOM_A"),
                "BUS-BUSI101",
                (2, "ROOM_B"),
            )
        )

    # ========================================================
    # 11. ROOM AVAILABILITY
    # ========================================================

    def test_room_availability(self):

        exam_id = "ENG-MATH101"
        value = (2, "ROOM_A")

        self.assertTrue(
            self.rules().unary_valid(
                exam_id,
                value,
            )
        )

        self.data["rooms"]["ROOM_A"][
            "unavailable_slots"
        ] = [2]

        self.assertFalse(
            self.rules().unary_valid(
                exam_id,
                value,
            )
        )

    # ========================================================
    # 12. PROFESSOR AVAILABILITY
    # ========================================================

    def test_professor_availability(self):

        exam_id = "ENG-MATH101"
        value = (2, "ROOM_A")

        self.assertTrue(
            self.rules().unary_valid(
                exam_id,
                value,
            )
        )

        professor_id = self.data[
            "exams"
        ][exam_id]["professor_id"]

        self.data["professors"][
            professor_id
        ]["unavailable_slots"] = [2]

        self.assertFalse(
            self.rules().unary_valid(
                exam_id,
                value,
            )
        )

    # ========================================================
    # 13. EXAMINATION AVAILABILITY
    # ========================================================

    def test_exam_availability(self):

        exam_id = "ENG-MATH101"

        self.data["exams"][exam_id][
            "available_slots"
        ] = [4]

        rules = self.rules()

        domain = rules.domain(exam_id)

        self.assertTrue(domain)

        self.assertTrue(
            all(
                slot == 4
                for slot, room in domain
            )
        )

    # ========================================================
    # 14. ROOM TYPE
    # ========================================================

    def test_room_type(self):

        rules = self.rules()

        self.assertTrue(
            rules.unary_valid(
                "SCI-CSCI301",
                (2, "LAB_A"),
            )
        )

        self.assertFalse(
            rules.unary_valid(
                "SCI-CSCI301",
                (2, "ROOM_A"),
            )
        )

    # ========================================================
    # 15. INVALID ASSIGNMENT STRUCTURE
    # ========================================================

    def test_invalid_assignment_structure(self):

        rules = self.rules()

        self.assertFalse(
            rules.unary_valid(
                "ENG-MATH101",
                (2, "ROOM_A", "EXTRA"),
            )
        )

        self.assertFalse(
            rules.unary_valid(
                "ENG-MATH101",
                (2,),
            )
        )

    # ========================================================
    # 16. EMPTY DOMAIN FAILURE
    # ========================================================

    def test_impossible_schedule(self):

        self.data["exams"]["ENG-MATH101"][
            "available_slots"
        ] = []

        for algorithm in ALGORITHMS:

            with self.subTest(
                algorithm=algorithm
            ):

                result = self.solve(algorithm)

                self.assertFalse(
                    result["success"]
                )

                self.assertEqual(
                    result["status"],
                    "UNSAT",
                )

                self.assertEqual(
                    result["assignments_attempted"],
                    0,
                )

    # ========================================================
    # 17. NONEMPTY DOMAIN FAILURE
    # ========================================================

    def test_search_failure(self):

        for exam_id in [
            "ENG-MATH101",
            "SCI-MATH101",
        ]:

            self.data["exams"][exam_id][
                "available_slots"
            ] = [2]

        rules = self.rules()

        self.assertTrue(
            rules.domain("ENG-MATH101")
        )

        self.assertTrue(
            rules.domain("SCI-MATH101")
        )

        result = self.solve()

        self.assertEqual(
            result["status"],
            "UNSAT",
        )

        self.assertGreater(
            result["nodes_explored"],
            0,
        )

    # ========================================================
    # 18. TIMEOUT HANDLING
    # ========================================================

    def test_timeout(self):

        result = self.solve(
            timeout_seconds=0
        )

        self.assertEqual(
            result["status"],
            "TIMEOUT",
        )

        self.assertFalse(
            result["success"]
        )

    # ========================================================
    # 19. MISSING EXAM VALIDATION
    # ========================================================

    def test_missing_exam(self):

        schedule = self.valid_schedule()

        schedule.pop(
            "ENG-MATH101"
        )

        validation = self.validate(
            schedule
        )

        self.assertFalse(
            validation["valid"]
        )

        self.assertIn(
            "Missing examination: ENG-MATH101",
            validation["errors"],
        )

    # ========================================================
    # 20. VALIDATOR: BAD ASSIGNMENT STRUCTURE
    # ========================================================

    def test_validator_malformed_assignment(self):

        schedule = self.valid_schedule()

        schedule["ENG-MATH101"] = (
            2,
            "ROOM_A",
            "EXTRA",
        )

        validation = self.validate(
            schedule
        )

        self.assertFalse(
            validation["valid"]
        )

        self.assertTrue(
            any(
                "Invalid assignment structure" in error
                for error in validation["errors"]
            )
        )

    # ========================================================
    # 21. VALIDATOR: MISSING PROFESSOR
    # ========================================================

    def test_validator_missing_professor(self):

        schedule = self.valid_schedule()

        self.data["exams"]["ENG-MATH101"][
            "professor_id"
        ] = None

        validation = self.validate(
            schedule
        )

        self.assertFalse(
            validation["valid"]
        )

        self.assertTrue(
            any(
                "Missing professor" in error
                for error in validation["errors"]
            )
        )

    # ========================================================
    # 22. VALIDATOR: STUDENT DAILY CONFLICT
    # ========================================================

    def test_validator_student_daily_conflict(self):

        schedule = self.valid_schedule()

        schedule["ENG-MATH101"] = (
            2,
            "ROOM_A",
        )

        schedule["ENG-SOFE301"] = (
            3,
            "ROOM_B",
        )

        validation = self.validate(
            schedule
        )

        self.assertFalse(
            validation["valid"]
        )

        self.assertTrue(
            any(
                "Student daily conflict" in error
                for error in validation["errors"]
            )
        )

    # ========================================================
    # 23. FORWARD CHECKING INCREMENTAL CONSISTENCY
    # ========================================================

    def test_incremental_consistency(self):

        rules = self.rules()

        assigned_exam = "ENG-MATH101"

        assigned_value = (
            2,
            "ROOM_A",
        )

        partial = {
            assigned_exam: assigned_value
        }

        for exam_id in self.data["exams"]:

            if exam_id == assigned_exam:
                continue

            for value in rules.domain(exam_id):

                standard = rules.consistent(
                    exam_id,
                    value,
                    partial,
                )

                incremental = (
                    rules.incremental_consistent(
                        exam_id,
                        value,
                        assigned_exam,
                        assigned_value,
                    )
                )

                self.assertEqual(
                    standard,
                    incremental,
                )

    # ========================================================
    # 24. DEGREE HEURISTIC TIE-BREAKING
    # ========================================================

    def test_degree_heuristic(self):

        remaining = ["A", "B", "C"]

        domains = {
            "A": [1, 2],
            "B": [1, 2],
            "C": [1, 2, 3],
        }

        conflicts = {
            "A": ["B"],
            "B": ["A", "C"],
            "C": ["B"],
        }

        selected = select_mrv_degree(
            remaining,
            domains,
            conflicts,
        )

        self.assertEqual(
            selected,
            "B",
        )

        # MRV takes priority over degree.
        domains["A"] = [1]

        self.assertEqual(
            select_mrv_degree(
                remaining,
                domains,
                conflicts,
            ),
            "A",
        )

    # ========================================================
    # 25. STANDARD LCV ORDERING
    # ========================================================

    def test_lcv_ordering(self):

        rules = self.rules()

        exam_id = "ENG-MATH101"
        other = "ENG-SOFE301"

        candidates = rules.domain(
            exam_id
        )[:3]

        domains = {
            other: rules.domain(other)[:10]
        }

        ordered = order_lcv_values(
            exam_id,
            candidates,
            [other],
            domains,
            rules,
            {},
            lambda: None,
        )

        self.assertEqual(
            set(ordered),
            set(candidates),
        )

        self.assertEqual(
            len(ordered),
            len(candidates),
        )

    # ========================================================
    # 26. ADAPTIVE LCV FALLBACK
    # ========================================================

    def test_adaptive_lcv_fallback(self):

        candidates = [
            (0, "R1"),
            (1, "R1"),
        ]

        domains = {
            "B": list(range(100))
        }

        result = order_adaptive_lcv_values(
            "A",
            candidates,
            ["B"],
            domains,
            None,
            {},
            lambda: None,
            max_comparisons=1,
        )

        self.assertEqual(
            result,
            candidates,
        )

    # ========================================================
    # 27. ADAPTIVE LCV EXACT ORDERING
    # ========================================================

    def test_adaptive_lcv_exact(self):

        rules = self.rules()

        exam_id = "ENG-MATH101"
        other = "ENG-SOFE301"

        candidates = rules.domain(
            exam_id
        )[:3]

        domains = {
            other: rules.domain(other)[:10]
        }

        expected = order_lcv_values(
            exam_id,
            candidates,
            [other],
            domains,
            rules,
            {},
            lambda: None,
        )

        actual = order_adaptive_lcv_values(
            exam_id,
            candidates,
            [other],
            domains,
            rules,
            {},
            lambda: None,
            max_comparisons=100000,
        )

        self.assertEqual(
            expected,
            actual,
        )

    # ========================================================
    # 28. GENERATED DATASETS
    # ========================================================

    def test_generated_dataset(self):

        for scenario in [
            "normal",
            "restricted",
            "dense_conflicts",
        ]:

            with self.subTest(
                scenario=scenario
            ):

                data, conflicts, witness = (
                    generate_dataset(
                        "small",
                        42,
                        scenario,
                    )
                )

                self.assertEqual(
                    len(data["exams"]),
                    10,
                )

                self.assertEqual(
                    len(data["students"]),
                    500,
                )

                self.assertEqual(
                    len(witness),
                    len(data["exams"]),
                )

                UniversityData.model_validate(
                    data
                )

                validation = validate_schedule(
                    data["exams"],
                    data["rooms"],
                    data["time_slots"],
                    data["students"],
                    witness,
                    data["professors"],
                )

                self.assertTrue(
                    validation["valid"],
                    validation["errors"],
                )

    # ========================================================
    # 29. DATASET REPRODUCIBILITY
    # ========================================================

    def test_reproducibility(self):

        first = generate_dataset(
            "small",
            42,
        )

        second = generate_dataset(
            "small",
            42,
        )

        self.assertEqual(
            first,
            second,
        )

    # ========================================================
    # 30. IMPOSSIBLE DATASET
    # ========================================================

    def test_generated_impossible_dataset(self):

        data, conflicts, witness = (
            generate_dataset(
                "small",
                42,
                "impossible",
            )
        )

        rules = Constraints(
            data["exams"],
            data["rooms"],
            data["time_slots"],
            conflicts,
            data["professors"],
        )

        first_exam = next(
            iter(data["exams"])
        )

        self.assertEqual(
            rules.domain(first_exam),
            [],
        )

    # ========================================================
    # 31. VALID UNIVERSITY INPUT
    # ========================================================

    def test_valid_input(self):

        validated = (
            UniversityData.model_validate(
                self.data
            )
        )

        self.assertEqual(
            len(validated.exams),
            7,
        )

        self.assertEqual(
            len(validated.professors),
            4,
        )

    # ========================================================
    # 32. INVALID ENROLLMENT
    # ========================================================

    def test_invalid_enrollment(self):

        self.data["exams"]["ENG-MATH101"][
            "students"
        ] = 100

        with self.assertRaises(
            ValueError
        ):

            UniversityData.model_validate(
                self.data
            )

    # ========================================================
    # 33. AUTOMATIC ALGORITHM RECOMMENDATION
    # ========================================================

    def test_algorithm_recommendation(self):

        result = select_algorithm(
            self.data,
            self.conflicts,
        )

        self.assertIn(
            result["algorithm"],
            ALGORITHMS,
        )

        self.assertIn(
            result["complexity"],
            [
                "LOW",
                "MEDIUM",
                "HIGH",
                "VERY_HIGH",
            ],
        )

        self.assertTrue(
            result["reason"]
        )

    # ========================================================
    # 34. AUTOMATIC ALGORITHM EXECUTION
    # ========================================================

    def test_auto_execution(self):

        result = self.solve("Auto")

        self.assertTrue(
            result["success"]
        )

        self.assertIsNotNone(
            result["recommendation"]
        )

        self.assertEqual(
            result["algorithm"],
            result["recommendation"]["algorithm"],
        )

        validation = self.validate(
            result["schedule"]
        )

        self.assertTrue(
            validation["valid"],
            validation["errors"],
        )

    # ========================================================
    # 35. SOLVER PERFORMANCE METRICS
    # ========================================================

    def test_performance_metrics(self):

        result = self.solve()

        self.assertTrue(
            result["success"]
        )

        for metric in [
            "execution_time",
            "assignments_attempted",
            "backtracks",
            "constraint_checks",
            "nodes_explored",
            "values_pruned",
            "domain_generation_time",
            "search_time",
            "total_domain_values",
        ]:

            self.assertIn(
                metric,
                result,
            )

        self.assertGreater(
            result["total_domain_values"],
            0,
        )


# ============================================================
# RUN AUTOMATED TESTS
# ============================================================

if __name__ == "__main__":

    unittest.main(
        verbosity=2
    )
