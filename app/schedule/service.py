from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import TIMEZONE, Settings
from app.lessons.model import Lesson, LessonStatus
from app.lessons.schemas import LessonRead, closing_change
from app.schedule.schemas import ScheduleRead, ScheduleState
from app.tutors.service import get_tutor

CUTOFF_TIME = time(16, 0)


def cutoff_of(day: date, settings: Settings) -> datetime:
    """The schedule of a day is final at 16:00 on the previous open day."""
    previous = day - timedelta(days=1)
    for _ in range(7):
        if not settings.is_closed(previous):
            break
        previous -= timedelta(days=1)
    return datetime.combine(previous, CUTOFF_TIME, TIMEZONE)


def state_of(cutoff: datetime, now: datetime) -> ScheduleState:
    return ScheduleState.FINAL if now >= cutoff else ScheduleState.DRAFT


def get_schedule(db: Session, day: date, now: datetime, settings: Settings, tutor_id: str | None = None) -> ScheduleRead:
    """The lessons of one day. A lesson cancelled before the cut-off is left out: the tutor never saw it."""
    if tutor_id is not None:
        get_tutor(db, tutor_id)

    query = (
        select(Lesson)
        .where(Lesson.date == day)
        .options(selectinload(Lesson.tutor), selectinload(Lesson.students), selectinload(Lesson.changes))
        .order_by(Lesson.start_time, Lesson.id)
    )
    if tutor_id is not None:
        query = query.where(Lesson.tutor_id == tutor_id)

    cutoff = cutoff_of(day, settings)
    lessons = [lesson for lesson in db.scalars(query) if is_listed(lesson, cutoff)]
    return ScheduleRead(
        date=day,
        state=state_of(cutoff, now),
        cutoff=cutoff,
        lessons=[LessonRead.from_lesson(lesson) for lesson in lessons],
    )


def is_listed(lesson: Lesson, cutoff: datetime) -> bool:
    if lesson.status is not LessonStatus.CANCELLED:
        return True
    cancellation = closing_change(lesson)
    return cancellation is not None and cancellation.changed_at > cutoff
