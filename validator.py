"""Independent exam timetable validator.

Student: at most one exam per calendar date.
Professor: multiple same-day exams permitted if times do not overlap.
Room: no overlapping exams in the same room.
The uploaded time slots must contain ISO calendar dates and start times.
"""

from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta


def _date_for(slot):
    raw = slot.get('date', slot.get('day'))
    if isinstance(raw, datetime):
        return raw.date()
    if isinstance(raw, date):
        return raw
    if raw is None:
        raise ValueError('Missing actual exam date (YYYY-MM-DD)')
    try:
        return date.fromisoformat(str(raw).strip()[:10])
    except ValueError as exc:
        raise ValueError(f'Expected calendar date YYYY-MM-DD; received {raw!r}') from exc


def _clock(raw):
    if isinstance(raw, datetime):
        return raw.time()
    if isinstance(raw, time):
        return raw
    if raw is None:
        raise ValueError('Missing start_time')
    value = str(raw).strip()
    try:
        return time.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f'Invalid time {raw!r}; use HH:MM') from exc


def _interval(exam, slot):
    exam_day = _date_for(slot)
    start = datetime.combine(exam_day, _clock(slot.get('start_time')))
    duration = int(exam.get('duration_minutes', 0))
    if duration <= 0:
        raise ValueError('duration_minutes must be positive')
    end = start + timedelta(minutes=duration)
    if end.date() != exam_day:
        raise ValueError('Exam crosses midnight')
    if slot.get('end_time') is not None:
        slot_end = datetime.combine(exam_day, _clock(slot['end_time']))
        if slot_end <= start:
            raise ValueError('Slot end_time must be after start_time')
        if end > slot_end:
            raise ValueError('Exam does not fit within available slot hours')
    return start, end


def _overlap(a, b):
    return a[0] < b[1] and b[0] < a[1]


def _availability_errors(record, slot_index, exam_day, label):
    messages = []
    weekday = exam_day.strftime('%A')
    blocked = {str(v) for v in (record.get('unavailable_days') or [])}
    excluded_dates = {str(v) for v in (record.get('excluded_dates') or [])}
    unavailable = record.get('unavailable_slots') or []
    allowed = record.get('available_slots')
    if slot_index in unavailable or str(slot_index) in unavailable:
        messages.append(f'{label} unavailable at slot {slot_index}')
    if weekday in blocked or exam_day.isoformat() in blocked or exam_day.isoformat() in excluded_dates:
        messages.append(f'{label} unavailable on {exam_day.isoformat()}')
    if allowed is not None and slot_index not in allowed and str(slot_index) not in allowed:
        messages.append(f'{label} not allowed at slot {slot_index}')
    return messages


def validate_schedule(exams, rooms, time_slots, students, schedule, professors=None):
    """Return {'valid': bool, 'errors': list[str]} without using solver constraints."""
    professors = professors or {}
    errors = []
    counts = Counter()
    student_days = set()
    room_assignments = defaultdict(list)
    professor_assignments = defaultdict(list)
    normalized = {}

    # Student enrollment and data integrity.
    for student_id, student in students.items():
        courses = student.get('courses', [])
        if not isinstance(courses, list):
            errors.append(f'Invalid courses for student {student_id}')
            continue
        if len(courses) != len(set(courses)):
            errors.append(f'Duplicate student registrations: {student_id}')
        for exam_id in set(courses):
            if exam_id not in exams:
                errors.append(f'Unknown exam {exam_id} for student {student_id}')
            else:
                counts[exam_id] += 1

    for exam_id, exam in exams.items():
        if exam_id not in schedule:
            errors.append(f'Missing examination: {exam_id}')
        if counts[exam_id] != exam.get('students'):
            errors.append(
                f'Enrollment mismatch: {exam_id}. Expected {exam.get("students")}, '
                f'registered {counts[exam_id]}'
            )
    for exam_id in schedule:
        if exam_id not in exams:
            errors.append(f'Unknown examination: {exam_id}')

    for exam_id, assignment in schedule.items():
        if exam_id not in exams:
            continue
        if not isinstance(assignment, (list, tuple)) or len(assignment) != 2:
            errors.append(f'Invalid assignment structure for {exam_id}: expected [slot, room]')
            continue
        slot_index, room_id = assignment
        if type(slot_index) is not int or not 0 <= slot_index < len(time_slots):
            errors.append(f'Invalid time slot for {exam_id}: {slot_index}')
            continue
        if not isinstance(room_id, str) or room_id not in rooms:
            errors.append(f'Unknown room for {exam_id}: {room_id}')
            continue

        exam = exams[exam_id]
        room = rooms[room_id]
        slot = time_slots[slot_index]
        try:
            exam_day = _date_for(slot)
            interval = _interval(exam, slot)
        except (ValueError, TypeError, OverflowError) as exc:
            errors.append(f'Invalid date/time for {exam_id}: {exc}')
            continue

        normalized[exam_id] = (exam_day, interval)
        capacity = room.get('exam_capacity', room.get('capacity', 0))
        if max(exam.get('students', 0), counts[exam_id]) > capacity:
            errors.append(f'Insufficient room capacity for {exam_id} in {room_id}')
        if exam.get('room_type') and exam['room_type'] != room.get('room_type'):
            errors.append(f'Incorrect room type for {exam_id} in {room_id}')

        errors.extend(_availability_errors(room, slot_index, exam_day, f'Room {room_id}'))
        errors.extend(_availability_errors(exam, slot_index, exam_day, f'Examination {exam_id}'))

        # Check actual interval overlap, even when slot indices differ.
        for other_exam, other_interval in room_assignments[room_id]:
            if _overlap(interval, other_interval):
                errors.append(f'Room overlap: {room_id} between {exam_id} and {other_exam}')
        room_assignments[room_id].append((exam_id, interval))

        professor_id = exam.get('professor_id')
        if not professor_id:
            errors.append(f'Missing professor for {exam_id}')
        elif professor_id not in professors:
            errors.append(f'Unknown professor {professor_id} for {exam_id}')
        else:
            # Same professor may have multiple exams in a day, but not at overlapping hours.
            for other_exam, other_interval in professor_assignments[professor_id]:
                if _overlap(interval, other_interval):
                    errors.append(
                        f'Professor overlap: {professor_id} between {exam_id} and {other_exam}'
                    )
            professor_assignments[professor_id].append((exam_id, interval))
            errors.extend(
                _availability_errors(professors[professor_id], slot_index,
                                     exam_day, f'Professor {professor_id}')
            )

    # One exam per student per actual calendar date (regardless of hours).
    for student_id, student in students.items():
        courses = student.get('courses', [])
        if not isinstance(courses, list):
            continue
        for exam_id in set(courses):
            if exam_id not in normalized:
                continue
            exam_day, _ = normalized[exam_id]
            key = (student_id, exam_day)
            if key in student_days:
                errors.append(
                    f'Student daily conflict: {student_id} has multiple exams on {exam_day}'
                )
            student_days.add(key)

    return {'valid': not errors, 'errors': errors}
