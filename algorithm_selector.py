


from collections import Counter

from backtracking import basic_backtracking
from mrv import mrv_backtracking
from forward_checking import forward_checking
from mrv_forward_checking import mrv_forward_checking
from mrv_fc_lcv import mrv_fc_lcv
from mrv_fc_degree import mrv_fc_degree
from mrv_fc_degree_adaptive import mrv_fc_degree_adaptive

from conflicts import conflict_density
from constraints import Constraints


# ============================================================
# AVAILABLE AI ALGORITHMS
# ============================================================

ALGORITHMS = {
    "Basic Backtracking": basic_backtracking,

    "MRV": mrv_backtracking,

    "Forward Checking": forward_checking,

    "MRV + Forward Checking": mrv_forward_checking,

    "MRV + FC + LCV": mrv_fc_lcv,

    "MRV + FC + Degree": mrv_fc_degree,

    "MRV + FC + Degree + Adaptive LCV":
        mrv_fc_degree_adaptive,
}


# ============================================================
# PROBLEM FEATURE EXTRACTION
# ============================================================

def extract_features(data, conflicts):
    """
    Extract features of a university scheduling problem.

    Features measure:
    - Dataset size
    - Student conflict density
    - Room and time-slot pressure
    - Resource availability restrictions
    - Professor workload
    - Scheduling domain restrictions
    """

    exams = data["exams"]
    rooms = data["rooms"]
    time_slots = data["time_slots"]
    students = data.get("students", {})
    professors = data.get("professors", {})

    n_exams = len(exams)
    n_rooms = len(rooms)
    n_slots = len(time_slots)
    n_students = len(students)
    n_professors = len(professors)

    # --------------------------------------------------------
    # STUDENT CONFLICT DENSITY
    # --------------------------------------------------------

    density = conflict_density(conflicts)

    # --------------------------------------------------------
    # ROOM / SLOT RESOURCE UTILIZATION
    # --------------------------------------------------------

    total_positions = n_rooms * n_slots

    utilization = (
        n_exams / total_positions
        if total_positions
        else 1.0
    )

    # --------------------------------------------------------
    # AVAILABILITY RESTRICTIONS
    # --------------------------------------------------------

    records = [
        record
        for group in (
            exams,
            rooms,
            professors,
        )
        for record in group.values()
    ]

    restricted_count = sum(
        bool(
            record.get("unavailable_slots")
            or record.get("unavailable_days")
            or record.get("available_slots") is not None
        )
        for record in records
    )

    restriction_ratio = (
        restricted_count / len(records)
        if records
        else 0.0
    )

    restricted_resources = restricted_count > 0

    # --------------------------------------------------------
    # PROFESSOR WORKLOAD
    # --------------------------------------------------------

    days = {
        slot["day"]
        for slot in time_slots
    }

    n_days = len(days)

    professor_exam_counts = Counter(
        exam.get("professor_id")
        for exam in exams.values()
        if exam.get("professor_id") is not None
    )

    max_professor_exams = max(
        professor_exam_counts.values(),
        default=0
    )

    average_professor_exams = (
        n_exams / n_professors
        if n_professors
        else 0.0
    )

    professor_utilization = (
        n_exams / (n_professors * n_days)
        if n_professors and n_days
        else 1.0
    )

    # One examination per professor per day.
    professor_capacity_pressure = (
        max_professor_exams / n_days
        if n_days
        else 1.0
    )

    # --------------------------------------------------------
    # EXAMINATION DOMAIN ANALYSIS
    # --------------------------------------------------------

    # Generate only valid (slot, room) pairs.
    # This accounts for:
    # - Room capacity
    # - Room type
    # - Exam availability
    # - Room availability
    # - Professor availability

    rules = Constraints(
        exams,
        rooms,
        time_slots,
        conflicts,
        professors,
    )

    domain_sizes = [
        len(rules.domain(exam_id))
        for exam_id in exams
    ]

    total_domain_values = sum(domain_sizes)

    average_domain_size = (
        total_domain_values / n_exams
        if n_exams
        else 0.0
    )

    minimum_domain_size = min(
        domain_sizes,
        default=0
    )

    maximum_domain_size = max(
        domain_sizes,
        default=0
    )

    # Relative to every possible room/slot pair.
    domain_availability_ratio = (
        average_domain_size / total_positions
        if total_positions
        else 0.0
    )

    domain_restriction_ratio = (
        max(0.0, 1.0 - domain_availability_ratio)
        if total_positions
        else 1.0
    )

    empty_domains = sum(
        size == 0
        for size in domain_sizes
    )

    # --------------------------------------------------------
    # STUDENT COURSE REGISTRATIONS
    # --------------------------------------------------------

    total_registrations = sum(
        len(student.get("courses", []))
        for student in students.values()
    )

    average_courses_per_student = (
        total_registrations / n_students
        if n_students
        else 0.0
    )

    # --------------------------------------------------------
    # RETURN FEATURES
    # --------------------------------------------------------

    return {
        "exams": n_exams,

        "students": n_students,

        "rooms": n_rooms,

        "time_slots": n_slots,

        "days": n_days,

        "professors": n_professors,

        "conflict_density": density,

        "resource_utilization": utilization,

        "restricted_resources": restricted_resources,

        "restricted_resource_count": restricted_count,

        "restriction_ratio": restriction_ratio,

        "professor_utilization": professor_utilization,

        "professor_capacity_pressure":
            professor_capacity_pressure,

        "max_professor_exams": max_professor_exams,

        "average_professor_exams":
            average_professor_exams,

        "total_domain_values": total_domain_values,

        "average_domain_size": average_domain_size,

        "minimum_domain_size": minimum_domain_size,

        "maximum_domain_size": maximum_domain_size,

        "domain_availability_ratio":
            domain_availability_ratio,

        "domain_restriction_ratio":
            domain_restriction_ratio,

        "empty_domains": empty_domains,

        "total_registrations": total_registrations,

        "average_courses_per_student":
            average_courses_per_student,
    }


# ============================================================
# PROBLEM COMPLEXITY CLASSIFICATION
# ============================================================

def classify_complexity(features):
    """
    Estimate scheduling difficulty using a
    rule-based complexity scoring system.

    This is a heuristic classification,
    not a proof of computational complexity.
    """

    score = 0

    n_exams = features["exams"]

    # --------------------------------------------------------
    # 1. PROBLEM SIZE
    # --------------------------------------------------------

    if n_exams > 30:
        score += 4

    elif n_exams > 15:
        score += 2

    # --------------------------------------------------------
    # 2. STUDENT CONFLICT DENSITY
    # --------------------------------------------------------

    density = features["conflict_density"]

    if density >= 0.5:
        score += 3

    elif density >= 0.25:
        score += 2

    elif density >= 0.1:
        score += 1

    # --------------------------------------------------------
    # 3. ROOM / SLOT UTILIZATION
    # --------------------------------------------------------

    utilization = features[
        "resource_utilization"
    ]

    if utilization >= 0.7:
        score += 3

    elif utilization >= 0.4:
        score += 1

    # --------------------------------------------------------
    # 4. RESOURCE AVAILABILITY RESTRICTIONS
    # --------------------------------------------------------

    restriction_ratio = features[
        "restriction_ratio"
    ]

    if restriction_ratio >= 0.5:
        score += 3

    elif features["restricted_resources"]:
        score += 1

    # --------------------------------------------------------
    # 5. PROFESSOR PRESSURE
    # --------------------------------------------------------

    professor_pressure = max(
        features["professor_utilization"],
        features["professor_capacity_pressure"],
    )

    if professor_pressure >= 0.8:
        score += 2

    elif professor_pressure >= 0.5:
        score += 1

    # --------------------------------------------------------
    # 6. DOMAIN RESTRICTIONS
    # --------------------------------------------------------

    domain_pressure = features[
        "domain_restriction_ratio"
    ]

    if features["empty_domains"] > 0:
        score += 4

    elif domain_pressure >= 0.75:
        score += 3

    elif domain_pressure >= 0.5:
        score += 1

    # --------------------------------------------------------
    # 7. CLASSIFY COMPLEXITY
    # --------------------------------------------------------

    if score <= 1:
        level = "LOW"

    elif score <= 4:
        level = "MEDIUM"

    elif score <= 8:
        level = "HIGH"

    else:
        level = "VERY_HIGH"

    return {
        "score": score,
        "level": level,
    }


# ============================================================
# INTELLIGENT ALGORITHM RECOMMENDATION
# ============================================================

def select_algorithm(data, conflicts):
    """
    Recommend a CSP algorithm configuration based
    on the characteristics of the university dataset.
    """

    features = extract_features(
        data,
        conflicts,
    )

    complexity = classify_complexity(
        features
    )

    level = complexity["level"]

    warning = None

    # --------------------------------------------------------
    # EASY PROBLEM
    # --------------------------------------------------------

    if (
        features["conflict_density"] < 0.10
        and features["resource_utilization"] < 0.40
        and features["restriction_ratio"] < 0.10
        and features["empty_domains"] == 0
        and features["professor_capacity_pressure"] <= 1.0
    ):

        algorithm = "Basic Backtracking"

        reason = (
            "This scheduling instance has low student-conflict "
            "density, low resource pressure, and few availability "
            "restrictions. Basic Backtracking is recommended "
            "to avoid unnecessary heuristic overhead."
        )

    # --------------------------------------------------------
    # MODERATE OR COMPLEX PROBLEM
    # --------------------------------------------------------

    else:

        algorithm = "MRV + FC + Degree"

        reason = (
            "This scheduling problem benefits from "
            "Minimum Remaining Values, Forward "
            "Checking, and Degree-based tie-breaking. "
            "MRV selects constrained examinations "
            "first, Forward Checking removes "
            "incompatible assignments, and Degree "
            "helps break ties."
        )

    # --------------------------------------------------------
    # WARN ABOUT UNSAT OR DIFFICULT PROBLEMS
    # --------------------------------------------------------

    if features["empty_domains"] > 0:

        warning = (
            "At least one examination has no valid "
            "room and time-slot assignment. "
            "The current problem is unsatisfiable "
            "unless its restrictions are changed."
        )

    elif (
        features["professor_capacity_pressure"] > 1
    ):

        warning = (
            "At least one professor is assigned "
            "more examinations than there are "
            "available examination days. The "
            "current daily professor limit makes "
            "this problem unsatisfiable."
        )

    elif (
        level in ("HIGH", "VERY_HIGH")
        or features["exams"] > 15
    ):

        warning = (
            "This scheduling instance may require "
            "substantial search time. A solution "
            "is not guaranteed within the timeout."
        )

    return {
        "algorithm": algorithm,

        "reason": reason,

        "complexity": level,

        "complexity_score": complexity["score"],

        "warning": warning,

        "features": features,
    }


# ============================================================
# EXECUTE SELECTED ALGORITHM
# ============================================================

def run_algorithm(
    algorithm,
    data,
    conflicts,
    timeout_seconds=30,
):
    """
    Execute one of the seven CSP configurations,
    or automatically recommend and execute one.
    """

    recommendation = None

    # --------------------------------------------------------
    # AUTOMATIC ALGORITHM SELECTION
    # --------------------------------------------------------

    if algorithm == "Auto":

        recommendation = select_algorithm(
            data,
            conflicts,
        )

        algorithm = recommendation["algorithm"]

    # --------------------------------------------------------
    # VALIDATE ALGORITHM
    # --------------------------------------------------------

    if algorithm not in ALGORITHMS:

        raise ValueError(
            f"Unknown scheduling algorithm: {algorithm}"
        )

    # --------------------------------------------------------
    # RUN CSP SOLVER
    # --------------------------------------------------------

    result = ALGORITHMS[algorithm](
        data["exams"],
        data["rooms"],
        data["time_slots"],
        conflicts,
        professors=data.get("professors", {}),
        timeout_seconds=timeout_seconds,
    )

    # --------------------------------------------------------
    # ADD ALGORITHM METADATA
    # --------------------------------------------------------

    result["algorithm"] = algorithm

    result["recommendation"] = recommendation

    return result
