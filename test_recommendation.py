from dataset_generator import generate_dataset
from algorithm_selector import select_algorithm


for size in ["small", "medium", "large"]:

    for scenario in [
        "normal",
        "restricted",
        "dense_conflicts",
        "impossible"
    ]:

        data, conflicts, witness = generate_dataset(
            size,
            45,
            scenario
        )

        result = select_algorithm(
            data,
            conflicts
        )

        print("\n" + "=" * 60)

        print("Dataset:", size)

        print("Scenario:", scenario)

        print(
            "Recommended algorithm:",
            result["algorithm"]
        )

        print(
            "Complexity:",
            result["complexity"]
        )

        print(
            "Complexity score:",
            result["complexity_score"]
        )

        print(
            "Reason:",
            result["reason"]
        )

        print(
            "Warning:",
            result["warning"]
        )