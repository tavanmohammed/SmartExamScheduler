
"""
SMART EXAM SCHEDULER
Controlled AI Algorithm Benchmarking

Purpose:
    Compare seven CSP algorithm configurations
    across multiple dataset sizes, seeds and scenarios.

Dataset sizes:
    small
    medium
    large
    very_large
    extreme

Scenarios:
    normal
    restricted
    impossible
    dense_conflicts

Metrics:
    - Execution time
    - Assignment attempts
    - Backtracks
    - Constraint checks
    - Nodes explored
    - Values pruned
    - Success rate
    - Timeout rate
    - Schedule validity

Outputs:
    benchmark_results.csv
    benchmark_summary.csv

All algorithms receive the same scheduling instance
for each size, seed and scenario.

Teaching Assistants are not included.
"""

import argparse
import csv
import random
import statistics

from collections import defaultdict
from pathlib import Path

from dataset_generator import (
    PRESETS,
    generate_dataset,
)

from algorithm_selector import (
    ALGORITHMS,
    run_algorithm,
)

from conflicts import conflict_density
from validator import validate_schedule


# ============================================================
# VALID SCENARIOS
# ============================================================

SCENARIOS = (
    "normal",
    "restricted",
    "impossible",
    "dense_conflicts",
)


# ============================================================
# RUN CONTROLLED BENCHMARKS
# ============================================================

def run_benchmarks(
    sizes,
    seeds,
    scenarios,
    timeout=10,
):
    """
    Run each algorithm on the same generated
    university scheduling instances.

    Fairness controls:
        - Fixed dataset seeds
        - Same input for all algorithms
        - Same timeout for all algorithms
        - Independent schedule validation
        - Deterministic shuffled execution order

    Returns:
        List of detailed benchmark result rows.
    """

    if not sizes:
        raise ValueError(
            "At least one dataset size is required."
        )

    if not seeds:
        raise ValueError(
            "At least one seed is required."
        )

    if not scenarios:
        raise ValueError(
            "At least one scenario is required."
        )

    if timeout < 0:
        raise ValueError(
            "Timeout cannot be negative."
        )

    rows = []

    # --------------------------------------------------------
    # 1. ITERATE OVER DATASET CONFIGURATIONS
    # --------------------------------------------------------

    for size in sizes:

        for seed in seeds:

            for scenario in scenarios:

                print("\n" + "=" * 70)

                print(
                    f"DATASET: {size} | "
                    f"SEED: {seed} | "
                    f"SCENARIO: {scenario}"
                )

                print("=" * 70)

                # --------------------------------------------
                # 2. GENERATE DATASET
                # --------------------------------------------

                data, conflicts, witness = (
                    generate_dataset(
                        size,
                        seed,
                        scenario,
                    )
                )

                # --------------------------------------------
                # 3. VALIDATE KNOWN-FEASIBLE WITNESS
                # --------------------------------------------

                if scenario != "impossible":

                    witness_validation = validate_schedule(
                        data["exams"],
                        data["rooms"],
                        data["time_slots"],
                        data["students"],
                        witness,
                        data["professors"],
                    )

                    if not witness_validation["valid"]:

                        raise RuntimeError(
                            "Generated dataset's witness "
                            "is invalid:\n"
                            + "\n".join(
                                str(error)
                                for error in
                                witness_validation["errors"]
                            )
                        )

                # --------------------------------------------
                # 4. CALCULATE DATASET FEATURES
                # --------------------------------------------

                n_exams = len(
                    data["exams"]
                )

                n_students = len(
                    data["students"]
                )

                n_rooms = len(
                    data["rooms"]
                )

                n_slots = len(
                    data["time_slots"]
                )

                n_professors = len(
                    data["professors"]
                )

                n_days = len({
                    slot["day"]
                    for slot in data["time_slots"]
                })

                density = conflict_density(
                    conflicts
                )

                total_registrations = sum(
                    len(student.get("courses", []))
                    for student in data["students"].values()
                )

                print(
                    f"Examinations: {n_exams}"
                )

                print(
                    f"Students: {n_students}"
                )

                print(
                    f"Professors: {n_professors}"
                )

                print(
                    f"Rooms: {n_rooms}"
                )

                print(
                    f"Time slots: {n_slots}"
                )

                print(
                    f"Student conflict density: "
                    f"{density:.3f}"
                )

                # --------------------------------------------
                # 5. SHUFFLE ALGORITHM ORDER
                # --------------------------------------------

                order = list(
                    ALGORITHMS
                )

                # Deterministically shuffle algorithm
                # order to reduce order-related bias.

                order_rng = random.Random(
                    f"{size}:{seed}:{scenario}"
                )

                order_rng.shuffle(
                    order
                )

                # --------------------------------------------
                # 6. RUN ALL SEVEN ALGORITHMS
                # --------------------------------------------

                for algorithm in order:

                    print(
                        f"\nRunning: {algorithm}"
                    )

                    result = run_algorithm(
                        algorithm,
                        data,
                        conflicts,
                        timeout_seconds=timeout,
                    )

                    # ----------------------------------------
                    # 7. VALIDATE SUCCESSFUL TIMETABLES
                    # ----------------------------------------

                    valid = False

                    if result["success"]:

                        validation = validate_schedule(
                            data["exams"],
                            data["rooms"],
                            data["time_slots"],
                            data["students"],
                            result["schedule"],
                            data["professors"],
                        )

                        valid = validation["valid"]

                        if not valid:

                            raise RuntimeError(
                                "Invalid timetable generated "
                                f"by {algorithm}:\n"
                                + "\n".join(
                                    str(error)
                                    for error in
                                    validation["errors"]
                                )
                            )

                    # ----------------------------------------
                    # 8. RECORD PERFORMANCE METRICS
                    # ----------------------------------------

                    execution_time = result.get(
                        "execution_time"
                    )

                    time_ms = (
                        execution_time * 1000
                        if execution_time is not None
                        else None
                    )

                    row = {
                        "size": size,

                        "seed": seed,

                        "scenario": scenario,

                        "algorithm": algorithm,

                        "exams": n_exams,

                        "students": n_students,

                        "rooms": n_rooms,

                        "time_slots": n_slots,

                        "days": n_days,

                        "professors": n_professors,

                        "course_registrations":
                            total_registrations,

                        "conflict_density": density,

                        "status": result.get(
                            "status",
                            "UNKNOWN",
                        ),

                        "success": bool(
                            result["success"]
                        ),

                        "valid": valid,

                        "execution_time_ms": time_ms,

                        "assignments_attempted":
                            result.get(
                                "assignments_attempted"
                            ),

                        "backtracks":
                            result.get(
                                "backtracks"
                            ),

                        "constraint_checks":
                            result.get(
                                "constraint_checks"
                            ),

                        "nodes_explored":
                            result.get(
                                "nodes_explored"
                            ),

                        "values_pruned":
                            result.get(
                                "values_pruned"
                            ),

                        "total_domain_values":
                            result.get(
                                "total_domain_values"
                            ),

                        "domain_generation_time_ms": (
                            result.get(
                                "domain_generation_time"
                            ) * 1000
                            if result.get(
                                "domain_generation_time"
                            ) is not None
                            else None
                        ),

                        "search_time_ms": (
                            result.get(
                                "search_time"
                            ) * 1000
                            if result.get(
                                "search_time"
                            ) is not None
                            else None
                        ),
                    }

                    rows.append(
                        row
                    )

                    # ----------------------------------------
                    # 9. DISPLAY RESULT
                    # ----------------------------------------

                    formatted_time = (
                        f"{time_ms:.3f} ms"
                        if time_ms is not None
                        else "N/A"
                    )

                    print(
                        f"Status: {row['status']} | "
                        f"Valid: {valid} | "
                        f"Time: {formatted_time}"
                    )

    return rows


# ============================================================
# SUMMARIZE BENCHMARK RESULTS
# ============================================================

def summarize(rows):
    """
    Aggregate results by:
        - Dataset size
        - Scenario
        - Algorithm

    Reports:
        - Number of runs
        - Valid solutions
        - Success rate
        - Timeout count
        - UNSAT count
        - Median execution time for solved runs
        - Median assignment attempts
        - Median backtracks
        - Median constraint checks
        - Median nodes explored
        - Median values pruned
    """

    groups = defaultdict(
        list
    )

    for row in rows:

        key = (
            row["size"],
            row["scenario"],
            row["algorithm"],
        )

        groups[key].append(
            row
        )

    summary = []

    for key, group in sorted(
        groups.items()
    ):

        size, scenario, algorithm = key

        solved = [
            row
            for row in group
            if row["valid"]
        ]

        # ----------------------------------------------------
        # MEDIAN HELPER
        # ----------------------------------------------------

        def median_solved(metric):

            values = [
                row[metric]
                for row in solved
                if row.get(metric) is not None
            ]

            if not values:
                return None

            return statistics.median(
                values
            )

        # ----------------------------------------------------
        # CALCULATE SUCCESS RATE
        # ----------------------------------------------------

        run_count = len(
            group
        )

        valid_count = len(
            solved
        )

        success_rate = (
            100 * valid_count / run_count
            if run_count
            else 0.0
        )

        # ----------------------------------------------------
        # CALCULATE TOTAL EXECUTION TIMES
        # ----------------------------------------------------

        all_times = [
            row["execution_time_ms"]
            for row in group
            if row.get(
                "execution_time_ms"
            ) is not None
        ]

        median_all_time = (
            statistics.median(all_times)
            if all_times
            else None
        )

        # ----------------------------------------------------
        # BUILD SUMMARY ROW
        # ----------------------------------------------------

        summary.append({
            "size": size,

            "scenario": scenario,

            "algorithm": algorithm,

            "runs": run_count,

            "valid_solutions": valid_count,

            "success_rate": success_rate,

            "timeouts": sum(
                row["status"] == "TIMEOUT"
                for row in group
            ),

            "unsat": sum(
                row["status"] == "UNSAT"
                for row in group
            ),

            "median_solved_time_ms":
                median_solved(
                    "execution_time_ms"
                ),

            "median_all_time_ms":
                median_all_time,

            "median_assignments":
                median_solved(
                    "assignments_attempted"
                ),

            "median_backtracks":
                median_solved(
                    "backtracks"
                ),

            "median_constraint_checks":
                median_solved(
                    "constraint_checks"
                ),

            "median_nodes":
                median_solved(
                    "nodes_explored"
                ),

            "median_values_pruned":
                median_solved(
                    "values_pruned"
                ),

            "median_domain_values":
                median_solved(
                    "total_domain_values"
                ),
        })

    return summary


# ============================================================
# EXPORT CSV RESULTS
# ============================================================

def save_csv(filename, rows):
    """
    Export a list of dictionaries to a CSV file.
    """

    if not rows:
        print(
            f"No rows to save: {filename}"
        )
        return

    path = Path(
        filename
    )

    # Create output directory if necessary.
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=list(rows[0]),
        )

        writer.writeheader()

        writer.writerows(
            rows
        )


# ============================================================
# DISPLAY BENCHMARK SUMMARY
# ============================================================

def print_summary(summary):
    """
    Print a compact summary table.
    """

    print("\nAI ALGORITHM BENCHMARK SUMMARY")
    print("=" * 115)

    print(
        f"{'Size':<12}"
        f"{'Scenario':<18}"
        f"{'Algorithm':<37}"
        f"{'Success %':>12}"
        f"{'Median ms':>12}"
        f"{'Timeouts':>10}"
        f"{'Runs':>8}"
    )

    print("-" * 115)

    for row in summary:

        median_time = row[
            "median_solved_time_ms"
        ]

        formatted_time = (
            f"{median_time:.3f}"
            if median_time is not None
            else "N/A"
        )

        print(
            f"{row['size']:<12}"
            f"{row['scenario']:<18}"
            f"{row['algorithm']:<37}"
            f"{row['success_rate']:>12.1f}"
            f"{formatted_time:>12}"
            f"{row['timeouts']:>10}"
            f"{row['runs']:>8}"
        )

    print("=" * 115)


# ============================================================
# COMMAND-LINE INTERFACE
# ============================================================

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description=(
            "Run controlled Smart Exam Scheduler "
            "algorithm benchmarks."
        )
    )

    parser.add_argument(
        "--sizes",
        nargs="+",
        choices=list(PRESETS),
        default=[
            "small",
            "medium",
        ],
    )

    parser.add_argument(
        "--seeds",
        nargs="+",
        type=int,
        default=[
            42,
            43,
            44,
        ],
    )

    parser.add_argument(
        "--scenarios",
        nargs="+",
        choices=SCENARIOS,
        default=[
            "normal",
            "restricted",
        ],
    )

    parser.add_argument(
        "--timeout",
        type=float,
        default=10,
    )

    parser.add_argument(
        "--output",
        type=str,
        default="benchmark",
    )

    args = parser.parse_args()

    # --------------------------------------------------------
    # RUN EXPERIMENTS
    # --------------------------------------------------------

    results = run_benchmarks(
        args.sizes,
        args.seeds,
        args.scenarios,
        args.timeout,
    )

    summary = summarize(
        results
    )

    # --------------------------------------------------------
    # EXPORT RESULTS
    # --------------------------------------------------------

    results_file = (
        f"{args.output}_results.csv"
    )

    summary_file = (
        f"{args.output}_summary.csv"
    )

    save_csv(
        results_file,
        results,
    )

    save_csv(
        summary_file,
        summary,
    )

    print_summary(
        summary
    )

    print(
        "\nBenchmark completed successfully."
    )

    print(
        "Detailed results:",
        results_file,
    )

    print(
        "Summary results:",
        summary_file,
    )
