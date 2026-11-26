# Compare regular scheduling with optimization

from university_data import get_university_data

from conflicts import (
    get_course_students,
    generate_conflicts
)

from algorithm_selector import run_algorithm

from preference_optimizer import optimize_preferences

from preferences import evaluate_preferences


data = get_university_data()

conflicts = generate_conflicts(
    data["exams"],
    get_course_students(data["students"])
)

baseline = run_algorithm(
    "MRV + Forward Checking",
    data,
    conflicts
)

optimized = optimize_preferences(
    data["exams"],
    data["rooms"],
    data["time_slots"],
    conflicts,
    professors=data["professors"],
    teaching_assistants=data[
        "teaching_assistants"
    ]
)

if baseline["success"]:

    baseline_preferences = evaluate_preferences(
        baseline["schedule"],
        data["exams"],
        data["time_slots"],
        data["professors"],
        data["teaching_assistants"]
    )

    print(
        "Original penalty:",
        baseline_preferences["total_penalty"]
    )

    print(
        "Original satisfaction:",
        baseline_preferences["satisfaction_rate"]
    )

if optimized["success"]:

    print(
        "Optimized penalty:",
        optimized["total_penalty"]
    )

    print(
        "Optimized satisfaction:",
        optimized["preference_results"][
            "satisfaction_rate"
        ]
    )

print(
    "Optimization status:",
    optimized["status"]
)