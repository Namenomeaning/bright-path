from datetime import date

import pytest
from pydantic import ValidationError

from app.core.config import Settings, Weekday

MONDAY = date(2026, 3, 9)
SUNDAY = date(2026, 3, 8)
TUESDAY = date(2026, 3, 10)


def test_monday_is_closed_by_default():
    settings = Settings()

    assert settings.is_closed(MONDAY)
    assert not settings.is_closed(SUNDAY)


def test_closed_weekdays_can_hold_more_than_one(monkeypatch):
    monkeypatch.setenv("BRIGHT_PATH_CLOSED_WEEKDAYS", '["monday", "sunday"]')

    settings = Settings()

    assert settings.closed_weekdays == [Weekday.MONDAY, Weekday.SUNDAY]
    assert settings.is_closed(MONDAY)
    assert settings.is_closed(SUNDAY)
    assert not settings.is_closed(TUESDAY)


def test_an_unknown_weekday_name_fails_at_startup(monkeypatch):
    monkeypatch.setenv("BRIGHT_PATH_CLOSED_WEEKDAYS", '["funday"]')

    with pytest.raises(ValidationError):
        Settings()
