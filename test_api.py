# Automated FastAPI integration tests

import unittest

from fastapi.testclient import TestClient

from api import app
from algorithm_selector import ALGORITHMS


client = TestClient(app)


class TestAPI(unittest.TestCase):

    def setUp(self):

        response = client.get(
            "/university/sample"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.data = response.json()

    # ======================================
    # HELPER METHODS
    # ======================================

    def generate_schedule(self):

        response = client.post(
            "/schedule",

            json={
                "data": self.data,
                "algorithm": "Auto",
                "timeout_seconds": 10
            }
        )

        self.assertEqual(
            response.status_code,
            200,
            response.text
        )

        result = response.json()

        self.assertTrue(result["success"])

        self.assertTrue(
            result["validation"]["valid"]
        )

        return result["schedule"]

    # ======================================
    # 1. HEALTH CHECK
    # ======================================

    def test_health_check(self):

        response = client.get("/")

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertEqual(
            response.json()["status"],
            "running"
        )

    # ======================================
    # 2. AVAILABLE ALGORITHMS
    # ======================================

    def test_algorithms(self):

        response = client.get(
            "/algorithms"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        algorithms = response.json()[
            "algorithms"
        ]

        self.assertEqual(
            set(algorithms),
            set(ALGORITHMS) | {"Auto"}
        )

        self.assertEqual(
            len(algorithms),
            8
        )

    # ======================================
    # 3. SAMPLE UNIVERSITY
    # ======================================

    def test_sample_data(self):

        self.assertEqual(
            len(self.data["exams"]),
            7
        )

        self.assertEqual(
            len(self.data["teaching_assistants"]),
            12
        )

        self.assertIn(
            "professors",
            self.data
        )

    # ======================================
    # 4. DATASET GENERATION
    # ======================================

    def test_generate_dataset(self):

        for scenario in [
            "normal",
            "restricted",
            "dense_conflicts",
            "impossible"
        ]:

            with self.subTest(scenario=scenario):

                response = client.post(
                    "/datasets/generate",

                    json={
                        "size": "small",
                        "seed": 42,
                        "scenario": scenario
                    }
                )

                self.assertEqual(
                    response.status_code,
                    200,
                    response.text
                )

                result = response.json()

                self.assertEqual(
                    len(result["data"]["exams"]),
                    10
                )

                self.assertEqual(
                    result["scenario"],
                    scenario
                )

                self.assertNotIn(
                    "witness",
                    result
                )

    # ======================================
    # 5. INVALID DATASET SIZE
    # ======================================

    def test_invalid_dataset_size(self):

        response = client.post(
            "/datasets/generate",

            json={
                "size": "invalid",
                "seed": 42,
                "scenario": "normal"
            }
        )

        self.assertEqual(
            response.status_code,
            422
        )

    # ======================================
    # 6. INVALID DATASET SCENARIO
    # ======================================

    def test_invalid_dataset_scenario(self):

        response = client.post(
            "/datasets/generate",

            json={
                "size": "small",
                "seed": 42,
                "scenario": "unknown"
            }
        )

        self.assertEqual(
            response.status_code,
            422
        )

    # ======================================
    # 7. AUTOMATIC SAMPLE SCHEDULING
    # ======================================

    def test_sample_auto_schedule(self):

        response = client.post(
            "/schedule/sample"
        )

        self.assertEqual(
            response.status_code,
            200,
            response.text
        )

        result = response.json()

        self.assertTrue(result["success"])

        self.assertEqual(
            result["status"],
            "SOLVED"
        )

        self.assertTrue(
            result["validation"]["valid"]
        )

        self.assertIsNotNone(
            result["recommendation"]
        )

        self.assertEqual(
            len(result["schedule"]),
            7
        )

    # ======================================
    # 8. MANUAL ALGORITHM SELECTION
    # ======================================

    def test_manual_schedule(self):

        response = client.post(
            "/schedule",

            json={
                "data": self.data,

                "algorithm": "MRV + FC + Degree",

                "timeout_seconds": 10
            }
        )

        self.assertEqual(
            response.status_code,
            200,
            response.text
        )

        result = response.json()

        self.assertTrue(result["success"])

        self.assertEqual(
            result["algorithm"],
            "MRV + FC + Degree"
        )

        self.assertTrue(
            result["validation"]["valid"]
        )

    # ======================================
    # 9. INVALID ALGORITHM IN REQUEST BODY
    # ======================================

    def test_invalid_algorithm(self):

        response = client.post(
            "/schedule",

            json={
                "data": self.data,
                "algorithm": "Invalid Algorithm",
                "timeout_seconds": 10
            }
        )

        self.assertEqual(
            response.status_code,
            422
        )

    # ======================================
    # 10. INVALID SAMPLE ALGORITHM
    # ======================================

    def test_invalid_sample_algorithm(self):

        response = client.post(
            "/schedule/sample",

            params={
                "algorithm": "Invalid Algorithm"
            }
        )

        self.assertEqual(
            response.status_code,
            422
        )

    # ======================================
    # 11. INVALID TIMEOUT
    # ======================================

    def test_invalid_timeout(self):

        for timeout in [-1, 301]:

            with self.subTest(timeout=timeout):

                response = client.post(
                    "/schedule/sample",

                    params={
                        "timeout_seconds": timeout
                    }
                )

                self.assertEqual(
                    response.status_code,
                    422
                )

    # ======================================
    # 12. INVALID UNIVERSITY ENROLLMENT
    # ======================================

    def test_invalid_enrollment(self):

        self.data["exams"]["ENG-MATH101"][
            "students"
        ] = 999

        response = client.post(
            "/schedule",

            json={
                "data": self.data,
                "algorithm": "Auto"
            }
        )

        self.assertEqual(
            response.status_code,
            422
        )

    # ======================================
    # 13. ALGORITHM COMPARISON
    # ======================================

    def test_compare_algorithms(self):

        response = client.post(
            "/compare",

            json={
                "data": self.data,
                "timeout_seconds": 10
            }
        )

        self.assertEqual(
            response.status_code,
            200,
            response.text
        )

        results = response.json()[
            "results"
        ]

        self.assertEqual(
            len(results),
            7
        )

        self.assertEqual(
            {
                result["algorithm"]
                for result in results
            },
            set(ALGORITHMS)
        )

        for result in results:

            self.assertEqual(
                result["status"],
                "SOLVED"
            )

            self.assertTrue(
                result["validation"]["valid"]
            )

    # ======================================
    # 14. INTELLIGENT RECOMMENDATION
    # ======================================

    def test_recommendation(self):

        response = client.post(
            "/recommend",

            json={
                "data": self.data
            }
        )

        self.assertEqual(
            response.status_code,
            200,
            response.text
        )

        result = response.json()

        self.assertIn(
            result["algorithm"],
            ALGORITHMS
        )

        self.assertIn(
            "complexity",
            result
        )

        self.assertIn(
            "complexity_score",
            result
        )

        self.assertIn(
            "features",
            result
        )

        self.assertTrue(
            result["reason"]
        )

    # ======================================
    # 15. REPAIR UNCHANGED SCHEDULE
    # ======================================

    def test_repair_unchanged(self):

        original = self.generate_schedule()

        response = client.post(
            "/schedule/repair",

            json={
                "data": self.data,

                "original_schedule": original,

                "timeout_seconds": 10
            }
        )

        self.assertEqual(
            response.status_code,
            200,
            response.text
        )

        result = response.json()

        self.assertTrue(result["success"])

        self.assertEqual(
            result["status"],
            "OPTIMAL"
        )

        self.assertEqual(
            result["changed_exams"],
            0
        )

        self.assertTrue(
            result["validation"]["valid"]
        )

    # ======================================
    # 16. REPAIR AFTER ROOM CLOSURE
    # ======================================

    def test_repair_room_closure(self):

        original = self.generate_schedule()

        slot, room, tas = original[
            "ENG-MATH101"
        ]

        self.data["rooms"][room].setdefault(
            "unavailable_slots", []
        ).append(slot)

        response = client.post(
            "/schedule/repair",

            json={
                "data": self.data,

                "original_schedule": original,

                "timeout_seconds": 10
            }
        )

        self.assertEqual(
            response.status_code,
            200,
            response.text
        )

        result = response.json()

        self.assertTrue(result["success"])

        self.assertGreaterEqual(
            result["changed_exams"],
            1
        )

        self.assertTrue(
            result["validation"]["valid"]
        )

    # ======================================
    # 17. PREFERENCE OPTIMIZATION
    # ======================================

    def test_preference_optimization(self):

        response = client.post(
            "/schedule/optimize",

            json={
                "data": self.data,

                "weights": {},

                "timeout_seconds": 30
            }
        )

        self.assertEqual(
            response.status_code,
            200,
            response.text
        )

        result = response.json()

        self.assertTrue(result["success"])

        self.assertTrue(
            result["validation"]["valid"]
        )

        self.assertIn(
            result["status"],
            ["OPTIMAL", "FEASIBLE"]
        )

        self.assertIn(
            "total_penalty",
            result
        )

    # ======================================
    # 18. INVALID PREFERENCE WEIGHTS
    # ======================================

    def test_invalid_preference_weight(self):

        response = client.post(
            "/schedule/optimize",

            json={
                "data": self.data,

                "weights": {
                    "preferred_day": -5
                }
            }
        )

        self.assertEqual(
            response.status_code,
            422
        )

    # ======================================
    # 19. UNSAT AND TIMEOUT HANDLING
    # ======================================

    def test_failure_statuses(self):

        # Test timeout.
        response = client.post(
            "/schedule",

            json={
                "data": self.data,

                "algorithm": "MRV + FC + Degree",

                "timeout_seconds": 0
            }
        )

        self.assertEqual(
            response.status_code,
            200
        )

        result = response.json()

        self.assertFalse(result["success"])

        self.assertEqual(
            result["status"],
            "TIMEOUT"
        )

        self.assertIsNone(
            result["validation"]
        )

        # Test an impossible scheduling problem.
        self.data["exams"]["ENG-MATH101"][
            "available_slots"
        ] = []

        response = client.post(
            "/schedule",

            json={
                "data": self.data,

                "algorithm": "MRV + FC + Degree",

                "timeout_seconds": 10
            }
        )

        self.assertEqual(
            response.status_code,
            200
        )

        result = response.json()

        self.assertFalse(result["success"])

        self.assertEqual(
            result["status"],
            "UNSAT"
        )

        self.assertIsNone(
            result["validation"]
        )

    # ======================================
    # 20. REACT FRONTEND CORS
    # ======================================

    def test_cors(self):

        response = client.options(
            "/schedule",

            headers={
                "Origin": "http://localhost:5173",

                "Access-Control-Request-Method": (
                    "POST"
                ),

                "Access-Control-Request-Headers": (
                    "content-type"
                )
            }
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertEqual(
            response.headers.get(
                "access-control-allow-origin"
            ),

            "http://localhost:5173"
        )


if __name__ == "__main__":

    unittest.main()