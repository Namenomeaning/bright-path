from datetime import date, datetime
from enum import StrEnum
from functools import lru_cache
from zoneinfo import ZoneInfo

from pydantic_settings import BaseSettings, SettingsConfigDict

TIMEZONE = ZoneInfo("Asia/Ho_Chi_Minh")


class Weekday(StrEnum):
    # The order matches date.weekday(): Monday is 0.
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"

    @property
    def number(self) -> int:
        return list(Weekday).index(self)


class Settings(BaseSettings):
    """Read from environment variables with the BRIGHT_PATH_ prefix."""

    model_config = SettingsConfigDict(env_prefix="BRIGHT_PATH_")

    # The tool reads the current time from here, so a demo is repeatable.
    now: datetime = datetime(2026, 3, 6, 7, 0, tzinfo=TIMEZONE)
    db: str = "bright_path.db"
    # Weekdays when the centre does not teach. Only the cut-off reads this.
    closed_weekdays: list[Weekday] = [Weekday.MONDAY]

    def is_closed(self, day: date) -> bool:
        return day.weekday() in {weekday.number for weekday in self.closed_weekdays}


@lru_cache
def get_settings() -> Settings:
    return Settings()
