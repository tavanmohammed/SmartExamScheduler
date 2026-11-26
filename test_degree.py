from dataset_generator import generate_dataset
from algorithm_selector import run_algorithm
from validator import validate_schedule


data, conflicts, witness = generate_dataset(
    "medium",
    42,
    "normal"
)

result = run_algorithm(
    "MRV + FC + Degree",
    data,
    conflicts,
    10
)

print("\nDEGREE HEURISTIC RESULTS")
print("=" * 50)

for key, value in result.items():

    if key != "schedule":

        print(f"{key}: {value}")

if result["success"]:

    validation = validate_schedule(
        data["exams"],
        data["rooms"],
        data["time_slots"],
        data["students"],
        result["schedule"],
        data["professors"],
        data["teaching_assistants"]
    )

    print("\nValidation:", validation)