from datetime import date, datetime, timedelta, timezone

from app.core.config import Settings, Weekday
from app.schedule.schemas import ScheduleState
from app.schedule.service import cutoff_of, state_of

VIETNAM = timezone(timedelta(hours=7))
MONDAY_CLOSED = Settings(closed_weekdays=[Weekday.MONDAY])


def at_16(year: int, month: int, day: int) -> datetime:
    return datetime(year, month, day, 16, 0, tzinfo=VIETNAM)


def test_the_cutoff_is_16_00_the_day_before():
    assert cutoff_of(date(2026, 3, 4), MONDAY_CLOSED) == at_16(2026, 3, 3)


def test_the_cutoff_of_sunday_is_saturday():
    assert cutoff_of(date(2026, 3, 8), MONDAY_CLOSED) == at_16(2026, 3, 7)


def test_the_cutoff_of_tuesday_skips_the_closed_monday():
    assert cutoff_of(date(2026, 3, 3), MONDAY_CLOSED) == at_16(2026, 3, 1)


def test_the_cutoff_of_a_closed_monday_is_sunday():
    assert cutoff_of(date(2026, 3, 9), MONDAY_CLOSED) == at_16(2026, 3, 8)


def test_the_cutoff_skips_every_closed_day():
    settings = Settings(closed_weekdays=[Weekday.SUNDAY, Weekday.MONDAY])

    assert cutoff_of(date(2026, 3, 10), settings) == at_16(2026, 3, 7)


def test_a_schedule_is_final_from_the_cutoff():
    cutoff = at_16(2026, 3, 4)

    assert state_of(cutoff, cutoff - timedelta(minutes=1)) is ScheduleState.DRAFT
    assert state_of(cutoff, cutoff) is ScheduleState.FINAL
