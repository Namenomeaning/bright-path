from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.lessons.exceptions import LessonNotFound, LessonNotStarted, NotBooked
from app.lessons.model import CancelledBy, ChangeKind, Lesson, LessonChange, LessonStatus


def get_lesson(db: Session, lesson_id: str) -> Lesson:
    query = (
        select(Lesson)
        .where(Lesson.id == lesson_id)
        .options(selectinload(Lesson.tutor), selectinload(Lesson.students), selectinload(Lesson.changes))
    )
    lesson = db.scalars(query).one_or_none()
    if lesson is None:
        raise LessonNotFound()
    return lesson


def cancel_lesson(db: Session, lesson_id: str, cancelled_by: CancelledBy, note: str | None, now: datetime) -> Lesson:
    """Cancel a booked lesson at any time. The lesson keeps its row, and a change row records the cancellation."""
    lesson = get_lesson(db, lesson_id)
    if lesson.status is not LessonStatus.BOOKED:
        raise NotBooked()

    lesson.status = LessonStatus.CANCELLED
    lesson.changes.append(LessonChange(kind=ChangeKind.CANCELLED, changed_at=now, cancelled_by=cancelled_by, note=note))
    return commit_change(db, lesson)


def mark_no_show(db: Session, lesson_id: str, now: datetime) -> Lesson:
    """Mark a booked lesson as a no-show. It is allowed only from the start of the lesson."""
    lesson = get_lesson(db, lesson_id)
    if lesson.status is not LessonStatus.BOOKED:
        raise NotBooked()
    if now < lesson.starts_at:
        raise LessonNotStarted()

    lesson.status = LessonStatus.NO_SHOW
    lesson.changes.append(LessonChange(kind=ChangeKind.NO_SHOW, changed_at=now))
    return commit_change(db, lesson)


def commit_change(db: Session, lesson: Lesson) -> Lesson:
    """Write the status and the change row together, or write nothing."""
    try:
        db.commit()
    except IntegrityError:
        # The database allows one cancellation or no-show for each lesson.
        db.rollback()
        raise NotBooked() from None
    return lesson
