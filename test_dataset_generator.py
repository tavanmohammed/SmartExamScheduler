import unittest
from dataset_generator import generate_dataset, PRESETS

class DatasetTests(unittest.TestCase):
    def test_all_presets(self):
        for size, (n,pop,r,d,sessions) in PRESETS.items():
            with self.subTest(size=size):
                exams,rooms,slots,students,conflicts,witness = generate_dataset(size)
                self.assertEqual((len(exams),len(students),len(rooms),len(slots)),(n,pop,r,d*sessions))
                self.assertEqual(set(exams),set(witness))
                self.assertEqual(len(set(witness.values())),n)
                professor_days = set()
                enrollment = dict.fromkeys(exams,0)
                for e,(s,r) in witness.items():
                    self.assertLessEqual(exams[e]['students'],rooms[r]['exam_capacity'])
                    key = (exams[e]['professor_id'],slots[s]['day'])
                    self.assertNotIn(key,professor_days); professor_days.add(key)
                for student in students.values():
                    courses = student['courses']
                    self.assertEqual(len({witness[e][0] for e in courses}),len(courses))
                    for e in courses:
                        enrollment[e]+=1
                        self.assertTrue(set(courses)-{e} <= set(conflicts[e]))
                self.assertEqual(enrollment,{e:v['students'] for e,v in exams.items()})
    def test_reproducibility(self):
        self.assertEqual(generate_dataset('medium',42),generate_dataset('medium',42))

if __name__ == '__main__': unittest.main()
