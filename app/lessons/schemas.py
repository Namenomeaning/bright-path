from datetime import datetime, timedelta

from pydantic import BaseModel

from app.lessons.model import CancelledBy, ChangeKind, Lesson, LessonChange, LessonStatus
from app.students.schemas import StudentRead
from app.tutors.schemas import TutorRead

# A family cancellation this close to the start is late. The centre charges for it.
LATE_CANCELLATION_WINDOW = timedelta(hours=4)


class ChangeRead(BaseModel):
    kind: ChangeKind
    changed_at: datetime
    cancelled_by: CancelledBy | None
    note: str | None
    # Only a family cancellation can be late. Any other change is null.
    late: bool | None

    @classmethod
    def from_change(cls, change: LessonChange, lesson: Lesson) -> "ChangeRead":
        is_family_cancellation = change.kind is ChangeKind.CANCELLED and change.cancelled_by is CancelledBy.FAMILY
        late = lesson.starts_at - change.changed_at <= LATE_CANCELLATION_WINDOW if is_family_cancellation else None
        return cls(
            kind=change.kind,
            changed_at=change.changed_at,
            cancelled_by=change.cancelled_by,
            note=change.note,
            late=late,
        )


class LessonRead(BaseModel):
    id: str
    start_time: str
    end_time: str
    tutor: TutorRead
    room: str
    students: list[StudentRead]
    status: LessonStatus
    change: ChangeRead | None

    @classmethod
    def from_lesson(cls, lesson: Lesson) -> "LessonRead":
        closing = closing_change(lesson)
        return cls(
            id=lesson.id,
            start_time=lesson.starts_at.strftime("%H:%M"),
            end_time=lesson.ends_at.strftime("%H:%M"),
            tutor=TutorRead.model_validate(lesson.tutor),
            room=lesson.room_id,
            students=sorted(
                (StudentRead.model_validate(student) for student in lesson.students),
                key=lambda student: student.id,
            ),
            status=lesson.status,
            change=ChangeRead.from_change(closing, lesson) if closing else None,
        )


def closing_change(lesson: Lesson) -> LessonChange | None:
    """The cancellation or no-show of a lesson. A move does not close a lesson."""
    for change in lesson.changes:
        if change.kind in (ChangeKind.CANCELLED, ChangeKind.NO_SHOW):
            return change
    return None
