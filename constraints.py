"""Scheduling constraints for the Smart Exam Scheduler.

Assignment format: exam_id -> (slot_index, room_id).
Time slots require an ISO calendar date in ``date`` or ``day`` and a
``start_time`` (HH:MM). If ``end_time`` is present it is the slot limit.

Performance: memoizes immutable exam/slot calculations for each Constraints
instance. Recreate the Constraints object if the input dataset changes.
"""

from datetime import date, datetime, time, timedelta


def room_capacity(room):
    return room.get("exam_capacity", room.get("capacity", 0))


def exam_date(slot, time_slots):
    """Retrieve a real calendar date, not a weekday name like 'Monday'."""
    record = time_slots[slot]
    value = record.get("date") or record.get("day")
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError) as error:
        raise ValueError(
            f"Slot {slot} needs an ISO date (YYYY-MM-DD), got {value!r}"
        ) from error


def parse_clock(value):
    if isinstance(value, datetime):
        return value.time()
    if isinstance(value, time):
        return value
    if isinstance(value, str):
        try:
            return time.fromisoformat(value.strip())
        except ValueError as error:
            raise ValueError(f"Invalid time {value!r}; expected HH:MM") from error
    raise ValueError(f"Invalid time value: {value!r}")


def exam_interval(exam_id, slot, exams, time_slots):
    """Return (start, end) for an exam, or None if it doesn't fit the slot."""
    record = time_slots[slot]
    start = datetime.combine(exam_date(slot, time_slots), parse_clock(record["start_time"]))
    duration = int(exams[exam_id].get("duration_minutes", 180))
    if duration <= 0:
        return None
    end = start + timedelta(minutes=duration)
    if end.date() != start.date():
        return None
    if record.get("end_time") not in (None, ""):
        slot_end = datetime.combine(start.date(), parse_clock(record["end_time"]))
        if end > slot_end:
            return None
    return start, end


def times_overlap(interval1, interval2):
    start1, end1 = interval1
    start2, end2 = interval2
    return start1 < end2 and start2 < end1


def available(record, slot, time_slots):
    """Respect slot, weekday, and specific-date restrictions."""
    record = record or {}
    slot_record = time_slots[slot]
    calendar_day = exam_date(slot, time_slots)
    weekday = calendar_day.strftime("%A")
    day_value = slot_record.get("day")
    if slot in record.get("unavailable_slots", []):
        return False
    blocked_days = record.get("unavailable_days", [])
    if weekday in blocked_days or day_value in blocked_days or calendar_day.isoformat() in blocked_days:
        return False
    if calendar_day.isoformat() in record.get("unavailable_dates", []):
        return False
    allowed_slots = record.get("available_slots")
    if allowed_slots is not None and slot not in allowed_slots:
        return False
    return True


def normalize_assignment(value):
    if not isinstance(value, (tuple, list)) or len(value) != 2:
        raise ValueError("Assignment must be (slot_index, room_id)")
    return value[0], value[1]


class Constraints:
    """Reusable CSP constraint checks for one unchanged scheduling dataset."""

    def __init__(self, exams, rooms, time_slots, conflicts, professors=None):
        self.exams = exams
        self.rooms = rooms
        self.time_slots = time_slots
        self.professors = professors or {}
        self.checks = 0
        self.conflicts = {
            exam_id: set(conflicts.get(exam_id, []))
            for exam_id in exams
        }
        for exam_id, neighbors in list(self.conflicts.items()):
            for other in neighbors:
                if other in self.conflicts:
                    self.conflicts[other].add(exam_id)

        # Each Constraints instance owns its own caches. No cross-request state.
        self._slot_meta_cache = {}  # slot -> (date, datetime_start, datetime_limit|None)
        self._interval_cache = {}  # (exam_id, slot) -> interval|None
        self._availability_cache = {}  # (kind, record_id, slot) -> bool
        self._base_cache = {}  # (exam_id, slot, room_id) -> bool
        self._domain_cache = {}  # exam_id -> tuple of assignment pairs
        self._candidate_rooms_cache = {}  # exam_id -> tuple of room ids

    def _slot_meta(self, slot):
        if slot not in self._slot_meta_cache:
            record = self.time_slots[slot]
            day = exam_date(slot, self.time_slots)
            start = datetime.combine(day, parse_clock(record["start_time"]))
            limit = None
            if record.get("end_time") not in (None, ""):
                limit = datetime.combine(day, parse_clock(record["end_time"]))
            self._slot_meta_cache[slot] = (day, start, limit)
        return self._slot_meta_cache[slot]

    def _interval(self, exam_id, slot):
        key = (exam_id, slot)
        if key not in self._interval_cache:
            day, start, limit = self._slot_meta(slot)
            duration = int(self.exams[exam_id].get("duration_minutes", 180))
            interval = None
            if duration > 0:
                end = start + timedelta(minutes=duration)
                if end.date() == day and (limit is None or end <= limit):
                    interval = (start, end)
            self._interval_cache[key] = interval
        return self._interval_cache[key]

    def _available(self, kind, record_id, slot):
        key = (kind, record_id, slot)
        if key not in self._availability_cache:
            if kind == "exam":
                record = self.exams[record_id]
            elif kind == "room":
                record = self.rooms[record_id]
            else:
                record = self.professors.get(record_id, {})
            self._availability_cache[key] = available(record, slot, self.time_slots)
        return self._availability_cache[key]

    def _candidate_rooms(self, exam_id):
        if exam_id not in self._candidate_rooms_cache:
            exam = self.exams[exam_id]
            expected_type = exam.get("room_type")
            self._candidate_rooms_cache[exam_id] = tuple(
                room_id for room_id, room in self.rooms.items()
                if exam["students"] <= room_capacity(room)
                and (not expected_type or expected_type == room.get("room_type"))
            )
        return self._candidate_rooms_cache[exam_id]

    def base_valid(self, exam_id, slot, room_id):
        if exam_id not in self.exams:
            return False
        if type(slot) is not int or not 0 <= slot < len(self.time_slots):
            return False
        if room_id not in self.rooms:
            return False
        key = (exam_id, slot, room_id)
        if key not in self._base_cache:
            exam = self.exams[exam_id]
            professor_id = exam.get("professor_id")
            self._base_cache[key] = (
                self._interval(exam_id, slot) is not None
                and room_id in self._candidate_rooms(exam_id)
                and self._available("exam", exam_id, slot)
                and self._available("room", room_id, slot)
                and self._available("professor", professor_id, slot)
            )
        return self._base_cache[key]

    def unary_valid(self, exam_id, value):
        self.checks += 1
        try:
            slot, room_id = normalize_assignment(value)
        except ValueError:
            return False
        return self.base_valid(exam_id, slot, room_id)

    def compatible(self, exam1, value1, exam2, value2):
        self.checks += 1
        slot1, room1 = normalize_assignment(value1)
        slot2, room2 = normalize_assignment(value2)
        interval1 = self._interval(exam1, slot1)
        interval2 = self._interval(exam2, slot2)
        if interval1 is None or interval2 is None:
            return False

        # A student shared by two exams cannot have both on one calendar date.
        if (exam2 in self.conflicts[exam1] and self._slot_meta(slot1)[0] == self._slot_meta(slot2)[0]
        ):
            return False
       

        # Professors may have multiple exams per day, but never overlapping.
        professor1 = self.exams[exam1].get("professor_id")
        professor2 = self.exams[exam2].get("professor_id")
        shares_professor = professor1 is not None and professor1 == professor2
        shares_room = room1 == room2
        if (shares_professor or shares_room) and times_overlap(interval1, interval2):
            return False
        return True

    def consistent(self, exam_id, value, schedule):
        if not self.unary_valid(exam_id, value):
            return False
        for other_exam, other_value in schedule.items():
            if other_exam == exam_id:
                continue
            if not self.compatible(exam_id, value, other_exam, other_value):
                return False
        return True

    def domain(self, exam_id, check_time=lambda: None):
        """Generate allowed (slot_index, room_id) pairs; cache immutable results."""
        if exam_id not in self.exams:
            return []
        if exam_id not in self._domain_cache:
            exam = self.exams[exam_id]
            professor_id = exam.get("professor_id")
            candidate_rooms = self._candidate_rooms(exam_id)
            values = []
            for slot in range(len(self.time_slots)):
                check_time()
                if self._interval(exam_id, slot) is None:
                    continue
                if not self._available("exam", exam_id, slot):
                    continue
                if not self._available("professor", professor_id, slot):
                    continue
                for room_id in candidate_rooms:
                    check_time()
                    if self._available("room", room_id, slot):
                        values.append((slot, room_id))
            self._domain_cache[exam_id] = tuple(values)
        else:
            check_time()  # Preserve a timeout opportunity on cached reads.
        return list(self._domain_cache[exam_id])  # Isolate mutable solver domains.

    def incremental_consistent(self, exam_id, value, assigned_exam, assigned_value):
        return self.compatible(exam_id, value, assigned_exam, assigned_value)
