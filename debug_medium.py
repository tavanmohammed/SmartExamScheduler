from dataset_generator import generate_dataset
from constraints import Constraints
import time


data, conflicts, witness = generate_dataset(
    "medium",
    42,
    "normal"
)

rules = Constraints(
    data["exams"],
    data["rooms"],
    data["time_slots"],
    conflicts,
    data["professors"],
    data["teaching_assistants"]
)

print("\nMEDIUM DATASET ANALYSIS")
print("=" * 60)

print("Exams:", len(data["exams"]))
print("Students:", len(data["students"]))
print("Rooms:", len(data["rooms"]))
print("Time slots:", len(data["time_slots"]))
print("Professors:", len(data["professors"]))
print("TAs:", len(data["teaching_assistants"]))

total_values = 0
start = time.perf_counter()

for exam_id, exam in data["exams"].items():

    exam_start = time.perf_counter()

    domain = rules.domain(exam_id)

    elapsed = time.perf_counter() - exam_start

    total_values += len(domain)

    print(
        exam_id,
        "| Students:", exam["students"],
        "| Required TAs:", exam["required_tas"],
        "| Domain:", len(domain),
        "| Time:", round(elapsed * 1000, 3), "ms",
        flush=True
    )

print("\nTotal domain values:", total_values)

print(
    "Domain generation time:",
    round(time.perf_counter() - start, 3),
    "seconds"
)
