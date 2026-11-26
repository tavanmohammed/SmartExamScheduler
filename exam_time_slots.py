
from datetime import date, datetime, timedelta


def generate_time_slots(
    start_date,
    end_date,
    start_time,
    end_time,
    include_saturday=False,
    include_sunday=False,
    excluded_dates="",
    slot_minutes=180,
):
    first = date.fromisoformat(start_date)
    last = date.fromisoformat(end_date)

    if first > last:
        raise ValueError("Start date must be before end date.")

    if slot_minutes <= 0:
        raise ValueError("Slot duration must be positive.")

    opening = datetime.strptime(start_time, "%H:%M").time()
    closing = datetime.strptime(end_time, "%H:%M").time()

    if opening >= closing:
        raise ValueError("Start time must be before end time.")

    excluded = {
        date.fromisoformat(item.strip())
        for item in excluded_dates.split(",")
        if item.strip()
    }

    slots = []
    current_date = first

    while current_date <= last:
        weekday = current_date.weekday()

        allowed = (
            current_date not in excluded
            and (weekday != 5 or include_saturday)
            and (weekday != 6 or include_sunday)
        )

        if allowed:
            current = datetime.combine(current_date, opening)
            closing_dt = datetime.combine(current_date, closing)

            while current + timedelta(minutes=slot_minutes) <= closing_dt:
                finish = current + timedelta(minutes=slot_minutes)

                slots.append({
                    "day": current_date.isoformat(),
                    "date": current_date.isoformat(),
                    "start_time": current.strftime("%H:%M"),
                    "end_time": finish.strftime("%H:%M"),
                })

                current = finish

        current_date += timedelta(days=1)

    if not slots:
        raise ValueError("No available examination slots.")

    return slots
