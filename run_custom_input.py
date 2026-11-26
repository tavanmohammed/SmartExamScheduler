import json

from schemas import UniversityData
from conflicts import get_course_students, generate_conflicts
from algorithm_selector import run_algorithm
from validator import validate_schedule


INPUT_FILE = "custom_university.json"
OUTPUT_FILE = "custom_schedule.json"


def main():

    # 1. Load manually entered university data.
    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    # 2. Validate input structure.
    UniversityData.model_validate(data)

    # 3. Build student conflict graph.
    course_students = get_course_students(
        data["students"]
    )

    conflicts = generate_conflicts(
        data["exams"],
        course_students
    )

    # 4. Run the AI.
    result = run_algorithm(
        "Auto",
        data,
        conflicts,
        timeout_seconds=30
    )

    # 5. Independently validate the result.
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

        result["validation"] = validation

    else:

        result["validation"] = None

    # 6. Save output.
    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(result, file, indent=4)

    print("\n========== RESULTS ==========")
    print("Status:", result["status"])
    print("Algorithm:", result.get("algorithm"))
    print("Validation:", result["validation"])

    if result["success"]:

        print("\nGenerated examination timetable:\n")

        for exam_id, assignment in sorted(
            result["schedule"].items()
        ):

            slot, room, tas = assignment

            day = data["time_slots"][slot]["day"]
            time = data["time_slots"][slot]["time"]

            print(
                f"{exam_id}: {day} {time} | "
                f"Room: {room} | TAs: {', '.join(tas)}"
            )

    print(f"\nResults saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()