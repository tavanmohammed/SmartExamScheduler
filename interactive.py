
"""
SMART EXAM SCHEDULER
Interactive Command-Line Scheduling Interface

Features:
    - Sample university data
    - Generated experimental datasets
    - University JSON file import
    - Manual JSON input
    - Seven CSP algorithm configurations
    - Automatic algorithm selection
    - Independent timetable validation
    - Algorithm performance metrics
    - Student and professor scheduling constraints

Assignment format:
    exam_id -> (slot_index, room_id)

No Teaching Assistant dependencies.
"""

import json
import math

from pathlib import Path

from university_data import get_university_data

from dataset_generator import (
    PRESETS,
    generate_dataset,
)

from conflicts import (
    get_course_students,
    generate_conflicts,
)

from algorithm_selector import (
    ALGORITHMS,
    run_algorithm,
)

from validator import validate_schedule

from schemas import UniversityData


# ============================================================
# DISPLAY EXAMINATION TIMETABLE
# ============================================================

def display_schedule(data, schedule):
    """
    Display a scheduled examination timetable.

    Columns:
        - Examination
        - Day
        - Time
        - Room
        - Professor

    Each assignment is:
        (slot_index, room_id)
    """

    print("\nEXAMINATION TIMETABLE")
    print("=" * 110)

    if not schedule:
        print("No examinations to display.")
        return

    print(
        f"{'Examination':<22}"
        f"{'Day':<15}"
        f"{'Time':<15}"
        f"{'Room':<15}"
        f"{'Professor':<30}"
    )

    print("-" * 110)

    ordered = sorted(
        schedule.items(),
        key=lambda item: (
            item[1][0],
            item[0],
        ),
    )

    for exam_id, assignment in ordered:

        if (
            not isinstance(assignment, (list, tuple))
            or len(assignment) != 2
        ):
            raise ValueError(
                f"Invalid assignment for {exam_id}. "
                "Expected (slot_index, room_id)."
            )

        slot, room = assignment

        time_slot = data["time_slots"][slot]

        exam = data["exams"][exam_id]

        professor_id = exam.get(
            "professor_id"
        )

        professor_info = data.get(
            "professors", {}
        ).get(
            professor_id, {}
        )

        professor_name = professor_info.get(
            "name",
            professor_id or "Not assigned",
        )

        day = str(
            time_slot.get("day", "N/A")
        )

        exam_time = str(
            time_slot.get("time", "N/A")
        )

        print(
            f"{str(exam_id):<22}"
            f"{day:<15}"
            f"{exam_time:<15}"
            f"{str(room):<15}"
            f"{str(professor_name):<30}"
        )

    print("=" * 110)

    print(
        f"Total scheduled examinations: "
        f"{len(schedule)}"
    )


# ============================================================
# DISPLAY UNIVERSITY INFORMATION
# ============================================================

def display_university_summary(data):
    """
    Display statistics about the selected
    university scheduling problem.
    """

    print("\nUNIVERSITY DATA SUMMARY")
    print("-" * 50)

    print(
        "Examinations:",
        len(data["exams"]),
    )

    print(
        "Students:",
        len(data["students"]),
    )

    print(
        "Professors:",
        len(data.get("professors", {})),
    )

    print(
        "Rooms:",
        len(data["rooms"]),
    )

    print(
        "Time slots:",
        len(data["time_slots"]),
    )

    print(
        "Departments:",
        len(data.get("departments", {})),
    )

    days = {
        slot["day"]
        for slot in data["time_slots"]
    }

    print(
        "Examination days:",
        len(days),
    )


# ============================================================
# INPUT METHOD SELECTION
# ============================================================

def load_university_data():
    """
    Allow users to choose how university
    scheduling data is provided.

    Returns:
        University data dictionary.
    """

    print("\nSMART EXAM SCHEDULER")
    print("=" * 55)

    print("SELECT UNIVERSITY DATA SOURCE")
    print("-" * 55)

    print("1. Use sample university data")
    print("2. Generate experimental dataset")
    print("3. Import university JSON file")
    print("4. Enter university JSON manually")

    choice = input(
        "\nChoose input method (1-4): "
    ).strip()

    # --------------------------------------------------------
    # OPTION 1: SAMPLE UNIVERSITY
    # --------------------------------------------------------

    if choice == "1":

        data = get_university_data()

        print(
            "\nSample university data loaded."
        )

    # --------------------------------------------------------
    # OPTION 2: GENERATED DATASET
    # --------------------------------------------------------

    elif choice == "2":

        print("\nAVAILABLE DATASET SIZES")

        sizes = list(PRESETS)

        for index, size in enumerate(sizes, 1):
            print(
                f"{index}. {size}"
            )

        size = input(
            "\nDataset size [small]: "
        ).strip() or "small"

        if size not in PRESETS:
            raise ValueError(
                f"Invalid dataset size: {size}"
            )

        seed = int(
            input(
                "Random seed [42]: "
            ).strip() or "42"
        )

        scenarios = (
            "normal",
            "restricted",
            "dense_conflicts",
            "impossible",
        )

        print("\nAVAILABLE SCENARIOS")

        for scenario in scenarios:
            print("-", scenario)

        scenario = input(
            "\nScenario [normal]: "
        ).strip() or "normal"

        if scenario not in scenarios:
            raise ValueError(
                f"Invalid scenario: {scenario}"
            )

        data, _, _ = generate_dataset(
            size,
            seed,
            scenario,
        )

        print(
            "\nExperimental dataset generated."
        )

    # --------------------------------------------------------
    # OPTION 3: IMPORT JSON FILE
    # --------------------------------------------------------

    elif choice == "3":

        filename = input(
            "\nUniversity JSON file path: "
        ).strip().strip('"')

        if not filename:
            raise ValueError(
                "A JSON file path is required."
            )

        path = Path(filename)

        if not path.is_file():
            raise FileNotFoundError(
                f"File not found: {filename}"
            )

        if path.suffix.lower() != ".json":
            raise ValueError(
                "Only JSON files are supported "
                "by this input option."
            )

        with path.open(
            "r",
            encoding="utf-8-sig",
        ) as file:

            data = json.load(file)

        print(
            "\nUniversity JSON file imported."
        )

    # --------------------------------------------------------
    # OPTION 4: MANUAL JSON ENTRY
    # --------------------------------------------------------

    elif choice == "4":

        print(
            "\nEnter your complete university "
            "data as JSON."
        )

        print(
            "Press Enter on an empty line "
            "when finished."
        )

        lines = []

        while True:

            line = input()

            if not line.strip():
                break

            lines.append(line)

        if not lines:
            raise ValueError(
                "University JSON input cannot be empty."
            )

        data = json.loads(
            "\n".join(lines)
        )

    else:

        raise ValueError(
            "Invalid input method. Choose 1-4."
        )

    # ========================================================
    # VALIDATE UNIVERSITY INPUT
    # ========================================================

    validated_data = (
        UniversityData.model_validate(data)
    )

    return validated_data.model_dump()


# ============================================================
# SELECT SCHEDULING ALGORITHM
# ============================================================

def select_scheduling_algorithm():
    """
    Display all seven CSP algorithm configurations
    plus automatic algorithm selection.
    """

    algorithms = list(ALGORITHMS) + ["Auto"]

    print("\nAVAILABLE AI ALGORITHMS")
    print("=" * 60)

    for index, algorithm in enumerate(
        algorithms,
        start=1,
    ):

        print(
            f"{index}. {algorithm}"
        )

    choice = int(
        input(
            "\nSelect algorithm number: "
        ).strip()
    )

    if not 1 <= choice <= len(algorithms):
        raise ValueError(
            "Invalid algorithm selection."
        )

    return algorithms[choice - 1]


# ============================================================
# DISPLAY PERFORMANCE METRICS
# ============================================================

def display_metrics(result):
    """
    Display the solver's recorded metrics.
    """

    print("\nAI PERFORMANCE METRICS")
    print("=" * 55)

    print(
        "Algorithm:",
        result.get("algorithm", "N/A"),
    )

    print(
        "Status:",
        result.get("status", "UNKNOWN"),
    )

    print(
        "Success:",
        result.get("success", False),
    )

    execution_time = result.get(
        "execution_time",
        0,
    )

    print(
        "Execution time:",
        f"{execution_time * 1000:.3f} ms",
    )

    metrics = {
        "Assignment attempts":
            "assignments_attempted",

        "Backtracks":
            "backtracks",

        "Constraint checks":
            "constraint_checks",

        "Nodes explored":
            "nodes_explored",

        "Values pruned":
            "values_pruned",

        "Branches pruned":
            "branches_pruned",

        "Total domain values":
            "total_domain_values",

        "Adaptive LCV calls":
            "adaptive_lcv_calls",

        "Standard LCV calls":
            "standard_lcv_calls",
    }

    for label, key in metrics.items():

        if key in result:

            print(
                f"{label}:",
                result[key],
            )


# ============================================================
# INTERACTIVE SCHEDULER
# ============================================================

def interactive_scheduler():
    """
    Complete interactive university scheduling flow.

    1. Select university data source.
    2. Validate university input.
    3. Generate student conflict graph.
    4. Select scheduling algorithm.
    5. Run AI scheduler.
    6. Independently validate timetable.
    7. Display results and performance metrics.
    """

    # --------------------------------------------------------
    # 1. LOAD UNIVERSITY DATA
    # --------------------------------------------------------

    data = load_university_data()

    display_university_summary(
        data
    )

    # --------------------------------------------------------
    # 2. GENERATE STUDENT CONFLICT GRAPH
    # --------------------------------------------------------

    conflicts = generate_conflicts(
        data["exams"],
        get_course_students(
            data["students"]
        ),
    )

    # --------------------------------------------------------
    # 3. CHOOSE AI ALGORITHM
    # --------------------------------------------------------

    algorithm = select_scheduling_algorithm()

    # --------------------------------------------------------
    # 4. CHOOSE TIMEOUT
    # --------------------------------------------------------

    timeout = float(
        input(
            "\nTimeout seconds [30]: "
        ).strip() or "30"
    )

    if (
        not math.isfinite(timeout)
        or timeout < 0
    ):
        raise ValueError(
            "Timeout must be a finite, "
            "nonnegative number."
        )

    # --------------------------------------------------------
    # 5. RUN AI SCHEDULER
    # --------------------------------------------------------

    print("\nGENERATING EXAMINATION TIMETABLE")
    print("=" * 55)

    print(
        "Selected algorithm:",
        algorithm,
    )

    result = run_algorithm(
        algorithm,
        data,
        conflicts,
        timeout_seconds=timeout,
    )

    # --------------------------------------------------------
    # 6. INDEPENDENT VALIDATION
    # --------------------------------------------------------

    if result["success"]:

        validation = validate_schedule(
            data["exams"],
            data["rooms"],
            data["time_slots"],
            data["students"],
            result["schedule"],
            data.get("professors", {}),
        )

        print(
            "\nSchedule valid:",
            validation["valid"],
        )

        if validation["valid"]:

            display_schedule(
                data,
                result["schedule"],
            )

        else:

            print(
                "\nSCHEDULE VALIDATION FAILED"
            )

            for error in validation["errors"]:
                print(" -", error)

    else:

        print(
            "\nNo valid timetable was generated."
        )

        print(
            "Solver status:",
            result["status"],
        )

        if result["status"] == "TIMEOUT":

            print(
                "The algorithm reached its time limit. "
                "This does not prove that the problem "
                "has no solution."
            )

        elif result["status"] == "UNSAT":

            print(
                "The solver determined that the "
                "constraints cannot all be satisfied."
            )

    # --------------------------------------------------------
    # 7. PERFORMANCE METRICS
    # --------------------------------------------------------

    display_metrics(
        result
    )

    return result


# ============================================================
# RUN DIRECTLY
# ============================================================

if __name__ == "__main__":

    try:
        interactive_scheduler()

    except (
        ValueError,
        TypeError,
        KeyError,
        OSError,
        json.JSONDecodeError,
    ) as error:

        print(
            "\nError:",
            error,
        )

    except KeyboardInterrupt:

        print(
            "\nScheduling cancelled."
        )
