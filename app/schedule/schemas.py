from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel

from app.lessons.schemas import LessonRead


class ScheduleState(StrEnum):
    DRAFT = "draft"
    FINAL = "final"


class ScheduleRead(BaseModel):
    date: date
    state: ScheduleState
    cutoff: datetime
    lessons: list[LessonRead]
