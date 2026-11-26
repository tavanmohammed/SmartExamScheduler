from typing import Annotated
from fastapi import (FastAPI, HTTPException, Query, )
from algorithm_reports import router as algorithm_report_router
from fastapi.middleware.cors import CORSMiddleware
from upload_routes import router as upload_router
from schedule_export import router as export_router
from schemas import (
    AlgorithmName,
    UniversityData,
    ScheduleRequest,
    CompareRequest,
    DatasetRequest,
    RepairRequest,
    PreferenceRequest,
)
from university_data import get_university_data
from dataset_generator import generate_dataset
from conflicts import (
    get_course_students,
    generate_conflicts,
)
from algorithm_selector import (
    ALGORITHMS,
    run_algorithm,
    select_algorithm,
)
from pathlib import Path
from validator import validate_schedule
from compare_algorithms import compare_algorithms
from rescheduling import repair_schedule
from preference_optimizer import optimize_preferences
from schedule_export import router as export_router
from manual_schedule_routes import router as manual_router
from comparison_jobs import router as comparison_jobs_router
from fastapi.staticfiles import StaticFiles

# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Smart Exam Scheduler API",
    description=(
        "An intelligent constraint-based university "
        "examination scheduling system supporting "
        "seven AI configurations, automatic algorithm "
        "selection, schedule repair, and preference "
        "optimization."
    ),
    version="1.1.0",
)

app.include_router(upload_router)
app.include_router(export_router)
app.include_router(manual_router)
# ============================================================
# FRONTEND CORS CONFIGURATION
# ============================================================

app.include_router(algorithm_report_router)
app.include_router(comparison_jobs_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"

app.mount(
    "/ui",
    StaticFiles(directory=str(FRONTEND_DIR), html=True),
    name="frontend"
)



# ============================================================
# HELPER: BUILD STUDENT CONFLICT GRAPH
# ============================================================

def build_conflicts(data):
    """
    Detect examinations sharing enrolled students.

    Students may take at most one exam per day.
    """

    course_students = get_course_students(
        data["students"]
    )

    return generate_conflicts(
        data["exams"],
        course_students,
    )


# ============================================================
# HELPER: INDEPENDENT SCHEDULE VALIDATION
# ============================================================

def validate_result(data, result):
    """
    Validate successful schedules independently
    from the CSP solver.
    """

    if not result["success"]:

        result["validation"] = None
        return result

    validation = validate_schedule(
        data["exams"],
        data["rooms"],
        data["time_slots"],
        data["students"],
        result["schedule"],
        data["professors"],
    )

    result["validation"] = validation

    if not validation["valid"]:

        raise HTTPException(
            status_code=500,
            detail={
                "message": (
                    "Generated schedule failed "
                    "independent validation."
                ),
                "errors": validation["errors"],
            },
        )

    return result


# ============================================================
# HELPER: EXECUTE SCHEDULING ALGORITHM
# ============================================================

def execute_schedule(
    data,
    algorithm,
    timeout_seconds,
):
    """Run the selected CSP algorithm."""

    conflicts = build_conflicts(data)

    try:

        result = run_algorithm(
            algorithm,
            data,
            conflicts,
            timeout_seconds=timeout_seconds,
        )

        return validate_result(
            data,
            result,
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error


# ============================================================
# 1. HEALTH CHECK
# ============================================================

@app.get(
    "/",
    tags=["System"],
)
def home():

    return {
        "message": "Smart Exam Scheduler API",
        "status": "running",
        "version": "1.1.0",
        "algorithm_count": len(ALGORITHMS),
    }


# ============================================================
# 2. AVAILABLE AI ALGORITHMS
# ============================================================

@app.get(
    "/algorithms",
    tags=["System"],
)
def get_algorithms():

    return {
        "algorithms": list(ALGORITHMS) + ["Auto"]
    }


# ============================================================
# 3. SAMPLE UNIVERSITY DATA
# ============================================================

@app.get(
    "/university/sample",
    tags=["University Data"],
)
def sample_data():

    return get_university_data()


# ============================================================
# 4. GENERATE EXPERIMENTAL DATASET
# ============================================================

@app.post(
    "/datasets/generate",
    tags=["University Data"],
)
def generate(request: DatasetRequest):

    try:

        data, conflicts, witness = generate_dataset(
            request.size,
            request.seed,
            request.scenario,
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except RuntimeError as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Dataset generation failed: "
                + str(error)
            ),
        ) from error

    # Validate the generated university data.
    UniversityData.model_validate(data)

    # The witness is deliberately hidden from the
    # algorithm and the API response.
    return {
        "data": data,
        "conflicts": conflicts,
        "size": request.size,
        "seed": request.seed,
        "scenario": request.scenario,
    }


# ============================================================
# 5. GENERATE EXAMINATION SCHEDULE
# ============================================================

@app.post(
    "/schedule",
    tags=["Scheduling"],
)
def schedule(request: ScheduleRequest):

    data = request.data.model_dump()

    return execute_schedule(
        data,
        request.algorithm,
        request.timeout_seconds,
    )


# ============================================================
# 6. GENERATE SAMPLE SCHEDULE
# ============================================================

@app.post(
    "/schedule/sample",
    tags=["Scheduling"],
)
def schedule_sample(
    algorithm: AlgorithmName = "Auto",
    timeout_seconds: Annotated[
        float,
        Query(
            ge=0,
            le=300,
            allow_inf_nan=False,
        ),
    ] = 30,
):

    data = get_university_data()

    return execute_schedule(
        data,
        algorithm,
        timeout_seconds,
    )


# ============================================================
# 7. COMPARE ALL AI ALGORITHMS
# ============================================================

@app.post(
    "/compare",
    tags=["AI Evaluation"],
)
def compare(request: CompareRequest):

    data = request.data.model_dump()

    results = compare_algorithms(
        data,
        request.timeout_seconds,
    )

    for result in results:

        if not result["success"]:
            continue

        # If the result includes its timetable,
        # validate it independently.
        if result.get("schedule") is not None:

            validate_result(
                data,
                result,
            )

        else:

            # Comparison functions may omit the
            # timetable and return only metrics.
            validation = result.get(
                "validation"
            )

            if (
                validation is None
                or not validation["valid"]
            ):

                raise HTTPException(
                    status_code=500,
                    detail=(
                        "Comparison result is missing "
                        "successful schedule validation."
                    ),
                )

    return {
        "results": results
    }


# ============================================================
# 8. INTELLIGENT ALGORITHM RECOMMENDATION
# ============================================================

@app.post(
    "/recommend",
    tags=["AI Evaluation"],
)
def recommend(request: ScheduleRequest):

    data = request.data.model_dump()

    conflicts = build_conflicts(data)

    return select_algorithm(
        data,
        conflicts,
    )


# ============================================================
# 9. INTELLIGENT SCHEDULE REPAIR
# ============================================================

@app.post(
    "/schedule/repair",
    tags=["Schedule Optimization"],
)
def repair(request: RepairRequest):

    data = request.data.model_dump()

    conflicts = build_conflicts(data)

    try:

        result = repair_schedule(
            data["exams"],
            data["rooms"],
            data["time_slots"],
            conflicts,
            request.original_schedule,
            professors=data["professors"],
            timeout_seconds=request.timeout_seconds,
        )

        return validate_result(
            data,
            result,
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error


# ============================================================
# 10. PREFERENCE OPTIMIZATION
# ============================================================

@app.post(
    "/schedule/optimize",
    tags=["Schedule Optimization"],
)
def optimize(request: PreferenceRequest):

    data = request.data.model_dump()

    conflicts = build_conflicts(data)

    try:

        result = optimize_preferences(
            data["exams"],
            data["rooms"],
            data["time_slots"],
            conflicts,
            professors=data["professors"],
            weights=request.weights,
            timeout_seconds=request.timeout_seconds,
        )

        return validate_result(
            data,
            result,
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error
