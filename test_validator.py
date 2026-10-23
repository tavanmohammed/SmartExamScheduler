from validator import validate_schedule


# Two exams
exams = {
    "MATH": {"students": 60},
    "PHYS": {"students": 50}
}

# One classroom
rooms = {
    "ROOM_A": {
        "capacity": 100,
        "exam_capacity": 70
    }
}

# One time slot
time_slots = [
    {"day": "Monday", "time": "9:00 AM"}
]

# One student registered in both exams
students = {
    "1001": {
        "program": "Engineering",
        "courses": ["MATH", "PHYS"]
    }
}

# Deliberately invalid schedule
schedule = {
    "MATH": (0, "ROOM_A"),
    "PHYS": (0, "ROOM_A")
}

result = validate_schedule(
    exams,
    rooms,
    time_slots,
    students,
    schedule
)

print("Valid:", result["valid"])

for error in result["errors"]:
    print(error)