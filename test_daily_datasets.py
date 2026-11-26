import unittest

from dataset_generator import generate_dataset
from validator import validate_schedule


class TestDailyDatasets(unittest.TestCase):

    def test_feasible_witnesses(self):

        for size in [

            "small",
            "medium",
            "large"

        ]:

            for seed in [42, 43, 44]:

                for scenario in [

                    "normal",
                    "restricted",
                    "dense_conflicts"

                ]:

                    with self.subTest(

                        size=size,

                        seed=seed,

                        scenario=scenario

                    ):

                        data, conflicts, witness = (
                            generate_dataset(

                                size,

                                seed,

                                scenario

                            )
                        )

                        result = validate_schedule(

                            data["exams"],

                            data["rooms"],

                            data["time_slots"],

                            data["students"],

                            witness,

                            data["professors"],

                            data["teaching_assistants"]

                        )

                        self.assertTrue(

                            result["valid"],

                            result["errors"]

                        )

    def test_student_academic_years(self):

        data, conflicts, witness = (
            generate_dataset("small", 42)
        )

        for student in data["students"].values():

            self.assertIn(

                student["year"],

                [1, 2, 3, 4]

            )

    def test_no_student_multiple_exams_per_day(self):

        data, conflicts, witness = (
            generate_dataset("medium", 42)
        )

        for student in data["students"].values():

            days = []

            for exam_id in student["courses"]:

                slot, room, tas = witness[exam_id]

                day = data["time_slots"][slot]["day"]

                days.append(day)

            self.assertEqual(

                len(days),

                len(set(days))

            )


if __name__ == "__main__":

    unittest.main()