
import math
import time

from collections import Counter, defaultdict
from functools import lru_cache

from constraints import Constraints, exam_date, exam_interval, times_overlap
from adaptive_lcv import order_adaptive_lcv_values
from degree_heuristic import select_mrv_degree


class SearchTimeout(Exception):
    """Raised when the search deadline is reached."""
    pass


# ============================================================
# SHARED CSP SOLVER
# ============================================================

def solve(
    exams,
    rooms,
    time_slots,
    conflicts,
    *,
    mrv=False,
    fc=False,
    lcv=False,
    professors=None,
    timeout_seconds=None,
    cost_function=None,
    degree=False,
    adaptive_lcv=False,
):

    # ========================================================
    # 1. VALIDATE SETTINGS
    # ========================================================

    if lcv and not fc:
        raise ValueError(
            "LCV requires Forward Checking."
        )

    if adaptive_lcv and not fc:
        raise ValueError(
            "Adaptive LCV requires Forward Checking."
        )

    if degree and not mrv:
        raise ValueError(
            "Degree heuristic requires MRV."
        )

    if lcv and adaptive_lcv:
        raise ValueError(
            "Standard LCV and Adaptive LCV cannot "
            "both be enabled."
        )

    if timeout_seconds is not None:

        if (
            isinstance(timeout_seconds, bool)
            or not isinstance(
                timeout_seconds,
                (int, float),
            )
            or not math.isfinite(timeout_seconds)
            or timeout_seconds < 0
        ):
            raise ValueError(
                "Invalid timeout."
            )

    # ========================================================
    # 2. TIMER
    # ========================================================

    start = time.perf_counter()

    deadline = (
        None
        if timeout_seconds is None
        else start + timeout_seconds
    )

    def check_time():

        if (
            deadline is not None
            and time.perf_counter() >= deadline
        ):
            raise SearchTimeout()

    # ========================================================
    # 3. CONSTRAINT ENGINE
    # ========================================================

    rules = Constraints(
        exams,
        rooms,
        time_slots,
        conflicts,
        professors,
    )

    schedule = {}

    best_schedule = None
    best_cost = float("inf")

    optimizing = cost_function is not None

    # Cached, immutable calendar information used by the standard LCV scorer.
    # Cache scope is one solver invocation, never shared across uploaded jobs.
    @lru_cache(maxsize=None)
    def cached_day(slot):
        return exam_date(slot, time_slots)

    @lru_cache(maxsize=None)
    def cached_interval(exam_id, slot):
        return exam_interval(exam_id, slot, exams, time_slots)

    def fast_exact_lcv(exam_id, candidates, remaining_exams, domains, check_time):
        """Order values by EXACT number of future domain values eliminated.

        Aggregate alternatives by time slot and room first; unlike an O(V *
        all_future_values) scan, this evaluates each distinct time slot pair.
        It uses the same three binary constraints as Constraints.compatible:
        student exams cannot share a date; professors and rooms cannot overlap.
        Unary restrictions have already been applied in the input domains.
        """
        if len(candidates) <= 1 or not remaining_exams:
            return candidates

        selected_slots = list(dict.fromkeys(slot for slot, _ in candidates))
        slot_penalty = Counter()
        room_penalty = defaultdict(Counter)
        selected_prof = exams[exam_id].get("professor_id")
        student_neighbors = rules.conflicts[exam_id]
        selected_intervals = {
            slot: cached_interval(exam_id, slot) for slot in selected_slots
        }

        for other_exam in remaining_exams:
            check_time()
            domain = domains[other_exam]
            if not domain:
                continue
            grouped = defaultdict(Counter)
            for other_slot, room_id in domain:
                grouped[other_slot][room_id] += 1
            shares_students = other_exam in student_neighbors
            other_prof = exams[other_exam].get("professor_id")
            shares_prof = (selected_prof is not None and
                           selected_prof == other_prof)

            for selected_slot in selected_slots:
                check_time()
                selected_date = cached_day(selected_slot)
                selected_interval = selected_intervals[selected_slot]
                if selected_interval is None:
                    continue
                for other_slot, room_counts in grouped.items():
                    # Order matters: count each eliminated future choice ONCE.
                    if shares_students and selected_date == cached_day(other_slot):
                        slot_penalty[selected_slot] += sum(room_counts.values())
                        continue
                    other_interval = cached_interval(other_exam, other_slot)
                    if other_interval is None or not times_overlap(
                        selected_interval, other_interval
                    ):
                        continue
                    if shares_prof:
                        slot_penalty[selected_slot] += sum(room_counts.values())
                    else:
                        room_penalty[selected_slot].update(room_counts)

        # Stable order retains input ordering for equally constraining choices.
        return sorted(
            candidates,
            key=lambda v: slot_penalty[v[0]] + room_penalty[v[0]][v[1]],
        )

    # ========================================================
    # 4. PERFORMANCE METRICS
    # ========================================================

    assignments_attempted = 0
    backtracks = 0
    nodes_explored = 0
    values_pruned = 0
    branches_pruned = 0

    initialization_time = 0.0
    domain_generation_time = 0.0
    search_time = 0.0

    domains_generated = 0
    total_domain_values = 0

    slowest_exam = None
    slowest_domain_time = 0.0
    current_domain_exam = None

    domain_start = None
    search_start = None

    costs = {}

    adaptive_lcv_calls = 0
    standard_lcv_calls = 0

    # ========================================================
    # 5. RECURSIVE BACKTRACKING SEARCH
    # ========================================================

    def search(
        remaining,
        domains,
        current_cost=0,
    ):

        nonlocal assignments_attempted
        nonlocal backtracks
        nonlocal nodes_explored
        nonlocal values_pruned
        nonlocal branches_pruned

        nonlocal best_schedule
        nonlocal best_cost

        nonlocal adaptive_lcv_calls
        nonlocal standard_lcv_calls

        check_time()

        nodes_explored += 1

        # ----------------------------------------------------
        # COMPLETE ASSIGNMENT
        # ----------------------------------------------------

        if not remaining:

            if (
                best_schedule is None
                or current_cost < best_cost
            ):

                best_schedule = schedule.copy()
                best_cost = current_cost

            # A zero-cost solution is globally optimal
            # when every assignment cost is nonnegative.
            return (
                not optimizing
                or best_cost == 0
            )

        # ====================================================
        # 6. BRANCH AND BOUND
        # ====================================================

        if optimizing:

            lower_bound = current_cost

            for exam_id in remaining:

                check_time()

                if not domains[exam_id]:
                    return False

                minimum_cost = min(
                    costs[exam_id][value]
                    for value in domains[exam_id]
                )

                lower_bound += minimum_cost

            if lower_bound >= best_cost:

                branches_pruned += 1
                return False

        # ====================================================
        # 7. VARIABLE SELECTION
        # ====================================================

        if mrv:

            if fc:

                if degree:

                    # MRV with Degree tie-breaking.
                    exam_id = select_mrv_degree(
                        remaining,
                        domains,
                        rules.conflicts,
                    )

                else:

                    # Minimum Remaining Values.
                    exam_id = min(
                        remaining,
                        key=lambda exam: len(
                            domains[exam]
                        ),
                    )

                candidates = domains[exam_id]

            else:

                # MRV without FC: derive legal-domain sizes from the current
                # schedule using indexed constraints, rather than comparing
                # every candidate against every assigned examination.
                occupied_rooms = defaultdict(list)
                occupied_professors = defaultdict(list)
                for assigned_exam, (assigned_slot, assigned_room) in schedule.items():
                    interval = cached_interval(assigned_exam, assigned_slot)
                    occupied_rooms[assigned_room].append(interval)
                    assigned_prof = exams[assigned_exam].get("professor_id")
                    if assigned_prof is not None:
                        occupied_professors[assigned_prof].append(interval)

                legal_domains = {}
                for candidate_exam in remaining:
                    check_time()
                    professor_id = exams[candidate_exam].get("professor_id")
                    blocked_days = {
                        cached_day(assigned_slot)
                        for assigned_exam, (assigned_slot, _) in schedule.items()
                        if assigned_exam in rules.conflicts[candidate_exam]
                    }
                    professor_busy = occupied_professors.get(professor_id, ())
                    legal_values = []
                    for slot, room_id in domains[candidate_exam]:
                        check_time()
                        # Candidate domains were unary-filtered by domain().
                        # Record an indexed binary consistency evaluation.
                        rules.checks += 1
                        if cached_day(slot) in blocked_days:
                            continue
                        interval = cached_interval(candidate_exam, slot)
                        if interval is None:
                            continue
                        if any(times_overlap(interval, used) for used in professor_busy):
                            continue
                        if any(times_overlap(interval, used)
                               for used in occupied_rooms.get(room_id, ())):
                            continue
                        legal_values.append((slot, room_id))
                    legal_domains[candidate_exam] = legal_values

                exam_id = min(
                    remaining,
                    key=lambda exam: len(
                        legal_domains[exam]
                    ),
                )

                candidates = legal_domains[exam_id]

        else:

            # Basic variable selection:
            # Choose the first remaining exam.

            exam_id = remaining[0]
            candidates = domains[exam_id]

        rest = [
            other_exam
            for other_exam in remaining
            if other_exam != exam_id
        ]

        # ====================================================
        # 8. VALUE ORDERING
        # ====================================================

        # ----------------------------------------------------
        # ADAPTIVE LCV
        # ----------------------------------------------------

        if adaptive_lcv:

            check_time()

            adaptive_lcv_calls += 1

            candidates = order_adaptive_lcv_values(
                exam_id,
                candidates,
                rest,
                domains,
                rules,
                schedule,
                check_time,
            )

        # ----------------------------------------------------
        # STANDARD LCV
        # ----------------------------------------------------

        elif lcv:

            check_time()

            standard_lcv_calls += 1

            candidates = fast_exact_lcv(
                exam_id,
                candidates,
                rest,
                domains,
                check_time,
            )

        # ----------------------------------------------------
        # BRANCH-AND-BOUND COST ORDERING
        # ----------------------------------------------------

        if optimizing:

            # Sort primarily by preference/repair cost.
            # Python's stable sort retains the ordering
            # produced by LCV for equal-cost values.

            candidates = sorted(
                candidates,
                key=lambda value: costs[exam_id][value],
            )

        # ====================================================
        # 9. TRY CANDIDATE ASSIGNMENTS
        # ====================================================

        for value in candidates:

            check_time()

            if not rules.consistent(
                exam_id,
                value,
                schedule,
            ):

                continue

            next_cost = current_cost

            if optimizing:

                next_cost += costs[exam_id][value]

                if next_cost >= best_cost:

                    branches_pruned += 1
                    continue

            assignments_attempted += 1

            schedule[exam_id] = value

            try:

                next_domains = domains
                failed = False

                # ============================================
                # 10. FORWARD CHECKING
                # ============================================

                if fc:

                    next_domains = {}

                    for other_exam in rest:

                        filtered = []

                        for other_value in (
                            domains[other_exam]
                        ):

                            check_time()

                            # Check the candidate against
                            # the most recent assignment.
                            #
                            # Previously assigned exams
                            # were already checked by
                            # earlier propagation steps.

                            if rules.incremental_consistent(
                                other_exam,
                                other_value,
                                exam_id,
                                value,
                            ):

                                filtered.append(
                                    other_value
                                )

                            else:

                                values_pruned += 1

                        next_domains[other_exam] = (
                            filtered
                        )

                        # Domain wipeout: no legal
                        # assignment remains for an exam.

                        if not filtered:

                            failed = True
                            break

                # ============================================
                # 11. RECURSIVE SEARCH
                # ============================================

                if not failed:

                    stop = search(
                        rest,
                        next_domains,
                        next_cost,
                    )

                    if stop:
                        return True

            finally:

                del schedule[exam_id]

            backtracks += 1

        return False

    # ========================================================
    # 12. INITIAL DOMAIN GENERATION
    # ========================================================

    status = "UNSAT"

    try:

        check_time()

        initialization_time = (
            time.perf_counter() - start
        )

        domains = {}

        domain_start = time.perf_counter()

        for exam_id in exams:

            check_time()

            current_domain_exam = exam_id

            exam_start = time.perf_counter()

            # Each domain contains valid:
            #     (slot_index, room_id)
            #
            # Unary constraints are applied here.

            domains[exam_id] = rules.domain(
                exam_id,
                check_time,
            )

            elapsed = (
                time.perf_counter() - exam_start
            )

            domains_generated += 1

            total_domain_values += len(
                domains[exam_id]
            )

            if elapsed > slowest_domain_time:

                slowest_domain_time = elapsed
                slowest_exam = exam_id

            print(
                f"[DOMAIN] {exam_id}: "
                f"{len(domains[exam_id]):,} values "
                f"in {elapsed:.3f}s",
                flush=True,
            )

            if not domains[exam_id]:
                break

        domain_generation_time = (
            time.perf_counter() - domain_start
        )

        domains_valid = (
            len(domains) == len(exams)
            and all(domains.values())
        )

        # ====================================================
        # 13. OPTIMIZATION COST PRECOMPUTATION
        # ====================================================

        if domains_valid:

            if optimizing:

                for exam_id, domain in domains.items():

                    costs[exam_id] = {}

                    for value in domain:

                        check_time()

                        cost = cost_function(
                            exam_id,
                            value,
                        )

                        if (
                            isinstance(cost, bool)
                            or not isinstance(
                                cost,
                                (int, float),
                            )
                            or not math.isfinite(cost)
                            or cost < 0
                        ):

                            raise ValueError(
                                "Optimization costs must "
                                "be finite and nonnegative."
                            )

                        costs[exam_id][value] = cost

            # =================================================
            # 14. START RECURSIVE SEARCH
            # =================================================

            search_start = time.perf_counter()

            search(
                list(exams),
                domains,
            )

            search_time = (
                time.perf_counter() - search_start
            )

        # ====================================================
        # 15. DETERMINE FINAL STATUS
        # ====================================================

        if best_schedule is not None:

            status = (
                "OPTIMAL"
                if optimizing
                else "SOLVED"
            )

    # ========================================================
    # 16. TIMEOUT HANDLING
    # ========================================================

    except SearchTimeout:

        now = time.perf_counter()

        if search_start is not None:

            search_time = (
                now - search_start
            )

        elif domain_start is not None:

            domain_generation_time = (
                now - domain_start
            )

        status = (
            "FEASIBLE"
            if best_schedule is not None
            else "TIMEOUT"
        )

    # ========================================================
    # 17. PERFORMANCE RESULTS
    # ========================================================

    execution_time = (
        time.perf_counter() - start
    )

    return {
        "success": best_schedule is not None,

        "status": status,

        "optimal": status == "OPTIMAL",

        "schedule": (
            best_schedule
            if best_schedule is not None
            else {}
        ),

        "total_cost": (
            best_cost
            if optimizing and best_schedule is not None
            else None
        ),

        "execution_time": execution_time,

        "assignments_attempted":
            assignments_attempted,

        "backtracks": backtracks,

        "constraint_checks": rules.checks,

        "nodes_explored": nodes_explored,

        "values_pruned": values_pruned,

        "branches_pruned": branches_pruned,

        "initialization_time":
            initialization_time,

        "domain_generation_time":
            domain_generation_time,

        "search_time": search_time,

        "domains_generated":
            domains_generated,

        "total_domain_values":
            total_domain_values,

        "slowest_domain_exam":
            slowest_exam,

        "slowest_domain_time":
            slowest_domain_time,

        "current_domain_exam":
            current_domain_exam,

        # ----------------------------------------
        # VALUE-ORDERING DIAGNOSTICS
        # ----------------------------------------

        "standard_lcv_calls":
            standard_lcv_calls,

        "adaptive_lcv_calls":
            adaptive_lcv_calls,
    }
