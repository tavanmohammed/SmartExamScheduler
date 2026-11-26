import json

from dataset_generator import generate_dataset
from algorithm_selector import run_algorithm
from validator import validate_schedule


# Generate university input data
data, conflicts, witness = generate_dataset(
    "medium",
    42,
    "normal"
)


# Save the actual input
with open("demo_input.json", "w") as file:

    json.dump(data, file, indent=4)


# Run the AI scheduling algorithm
result = run_algorithm(
    "MRV + FC + Degree",
    data,
    conflicts,
    timeout_seconds=10
)


# Validate the generated timetable
if result["success"]:

    result["validation"] = validate_schedule(
        data["exams"],
        data["rooms"],
        data["time_slots"],
        data["students"],
        result["schedule"],
        data["professors"],
        data["teaching_assistants"]
    )

else:

    result["validation"] = None


# Save the actual output
with open("demo_output.json", "w") as file:

    json.dump(result, file, indent=4)


print("\n========== INPUT ==========")

print("Examinations:", len(data["exams"]))
print("Students:", len(data["students"]))
print("Rooms:", len(data["rooms"]))
print("Professors:", len(data["professors"]))
print("TAs:", len(data["teaching_assistants"]))
print("Time slots:", len(data["time_slots"]))


print("\n========== OUTPUT ==========")

print("Algorithm:", result["algorithm"])
print("Status:", result["status"])

if result["success"]:

    print("Validation:", result["validation"])

    for exam_id, assignment in result["schedule"].items():

        slot, room, tas = assignment

        print(
            exam_id,
            data["time_slots"][slot]["day"],
            data["time_slots"][slot]["time"],
            room,
            data["exams"][exam_id]["professor_id"],
            tas
        )

else:

    print("No schedule generated.")


print("\nInput saved to demo_input.json")
print("Output saved to demo_output.json")