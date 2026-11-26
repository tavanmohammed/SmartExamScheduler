import json
from collections import defaultdict

with open("demo_input.json") as file:
    data = json.load(file)

with open("demo_output.json") as file:
    result = json.load(file)

if not result["success"]:
    raise SystemExit("No solved schedule to verify.")

schedule = result["schedule"]
violations = []
total_registrations = 0

for student_id, student in data["students"].items():

    exams_by_day = defaultdict(list)

    for exam_id in student["courses"]:

        slot_index = schedule[exam_id][0]
        day = data["time_slots"][slot_index]["day"]

        exams_by_day[day].append(exam_id)
        total_registrations += 1

    for day, exams in exams_by_day.items():

        if len(exams) > 1:
            violations.append(
                (student_id, day, exams)
            )

print("Students checked:", len(data["students"]))
print("Exam registrations checked:", total_registrations)
print("Daily exam violations:", len(violations))

if violations:
    print("Violations:", violations[:10])
else:
    print("PASS: No student has more than one exam per day.")