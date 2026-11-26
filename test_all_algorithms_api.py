"""Run every algorithm registered by algorithm_selector.py via the local manual API.

Install: no extra dependencies. Run from SmartExamScheduler project directory:
    python test_all_algorithms_api.py

Keep manual_schedule_example.json in the project directory (or pass a path).
"""
import copy
import csv
import json
import sys
import time
from collections import defaultdict
from datetime import date
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
API = "http://127.0.0.1:8000/schedule/manual"


def load_algorithms():
    try:
        from algorithm_selector import ALGORITHMS
    except ImportError as exc:
        raise RuntimeError("Run this script from your SmartExamScheduler folder next to algorithm_selector.py") from exc
    names = list(ALGORITHMS.keys()) if isinstance(ALGORITHMS, dict) else list(ALGORITHMS)
    names = [name for name in names if isinstance(name, str) and name != "Auto"]
    if not names:
        raise RuntimeError("No algorithms found in algorithm_selector.ALGORITHMS")
    return names


def call_api(payload):
    request = Request(API, data=json.dumps(payload).encode("utf-8"),
                      headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(request, timeout=float(payload.get("timeout_seconds", 30)) + 30) as response:
            return json.load(response)
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1400]
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"Cannot connect to {API}: {exc.reason}. Start uvicorn first.") from exc


def inspect_timetable(payload, response):
    errors = []
    if not response.get("success") or response.get("status") != "SOLVED":
        errors.append(f"Schedule not solved: status={response.get('status')}")
        return errors
    validation = response.get("validation") or {}
    if validation.get("valid") is not True:
        errors.append(f"Backend validation failed: {validation.get('errors')}")
    rows = response.get("timetable") or []
    expected = set(payload["exams"])
    actual = [row.get("exam_id") for row in rows]
    if len(actual) != len(expected) or set(actual) != expected:
        errors.append(f"Expected {len(expected)} distinct exams, received {len(actual)} entries with IDs {set(actual)}")
    if len(actual) != len(set(actual)):
        errors.append("Duplicate exam IDs in timetable")
    by_exam = {row["exam_id"]: row for row in rows if row.get("exam_id")}
    period = payload["period"]
    excluded = {d.strip() for d in period.get("excluded_dates", "").split(",") if d.strip()}
    for row in rows:
        eid = row["exam_id"]
        day = row["date"]
        if not period["start_date"] <= day <= period["end_date"] or day in excluded:
            errors.append(f"{eid}: date {day} is outside the allowed exam period")
        weekday = date.fromisoformat(day).weekday()
        if weekday == 5 and not period.get("include_saturday", False):
            errors.append(f"{eid}: illegally scheduled Saturday")
        if weekday == 6 and not period.get("include_sunday", False):
            errors.append(f"{eid}: illegally scheduled Sunday")
        if not period["start_time"] <= row["start_time"] < row["end_time"] <= period["end_time"]:
            errors.append(f"{eid}: exam time outside working hours")
        if eid in payload["exams"] and row.get("professor_id") != payload["exams"][eid].get("professor_id"):
            errors.append(f"{eid}: wrong professor")
        if row.get("room_id") not in payload["rooms"]:
            errors.append(f"{eid}: unknown room {row.get('room_id')}")
    # Critical rule: students can have only one exam per calendar day.
    for sid, student in payload["students"].items():
        days = defaultdict(list)
        for eid in student.get("courses", []):
            if eid in by_exam:
                days[by_exam[eid]["date"]].append(eid)
        for day, eids in days.items():
            if len(eids) > 1:
                errors.append(f"Student {sid}: {len(eids)} exams on {day}: {eids}")
    # Professors may supervise multiple exams in a day, but never at overlapping times.
    for resource in ("professor_id", "room_id"):
        grouped = defaultdict(list)
        for row in rows:
            grouped[(row[resource], row["date"])].append(row)
        for (resource_id, day), entries in grouped.items():
            entries.sort(key=lambda r: r["start_time"])
            for a, b in zip(entries, entries[1:]):
                if a["end_time"] > b["start_time"]:
                    errors.append(f"{resource} {resource_id}: overlap on {day} ({a['exam_id']}, {b['exam_id']})")
    # Room capacity is based on registered students in each exam.
    for row in rows:
        eid = row["exam_id"]
        room = payload["rooms"].get(row.get("room_id"), {})
        capacity = room.get("exam_capacity", room.get("capacity", 0))
        enrollment = sum(eid in s.get("courses", []) for s in payload["students"].values())
        if capacity < enrollment:
            errors.append(f"{eid}: enrollment {enrollment} exceeds room capacity {capacity}")
    return errors


def main():
    example = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "manual_schedule_example.json"
    if not example.is_file():
        print(f"Missing sample JSON: {example}\nPlace manual_schedule_example.json beside this script.")
        return 2
    with example.open(encoding="utf-8") as handle:
        base = json.load(handle)
    try:
        algorithms = load_algorithms()
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        return 2
    print(f"Testing {len(algorithms)} registered algorithms through {API}")
    print("Algorithms: " + ", ".join(algorithms))
    records = []
    for name in algorithms:
        payload = copy.deepcopy(base)
        payload["algorithm"] = name
        start = time.perf_counter()
        try:
            response = call_api(payload)
            errors = inspect_timetable(payload, response)
            passed = not errors
            detail = "PASS" if passed else "FAIL: " + " | ".join(errors)
            records.append({"algorithm": name, "passed": passed,
                            "seconds": round(time.perf_counter()-start, 3),
                            "scheduled": len(response.get("timetable") or []),
                            "status": response.get("status", ""),
                            "job_id": response.get("job_id", ""), "details": detail})
        except Exception as exc:
            records.append({"algorithm": name, "passed": False,
                            "seconds": round(time.perf_counter()-start, 3),
                            "scheduled": 0, "status": "ERROR", "job_id": "", "details": str(exc)})
        record = records[-1]
        print(f"{'PASS' if record['passed'] else 'FAIL'} | {name} | {record['seconds']:.3f}s | "
              f"{record['scheduled']} exams | {record['details'][:250]}")
    report = ROOT / "algorithm_test_results.csv"
    with report.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["algorithm", "passed", "seconds", "scheduled", "status", "job_id", "details"])
        writer.writeheader()
        writer.writerows(records)
    passes = sum(row["passed"] for row in records)
    print(f"\nRESULT: {passes}/{len(records)} passed. Report: {report}")
    return 0 if passes == len(records) else 1


if __name__ == "__main__":
    sys.exit(main())
