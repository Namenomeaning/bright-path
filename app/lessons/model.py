from datetime import date, datetime, time
from enum import StrEnum

from sqlalchemy import CheckConstraint, ForeignKey, Index, JSON, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, LocalDateTime, enum_column
from app.rooms.model import Room
from app.students.model import Student
from app.tutors.model import Tutor


class LessonStatus(StrEnum):
    BOOKED = "booked"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class ChangeKind(StrEnum):
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    MOVED = "moved"


class CancelledBy(StrEnum):
    FAMILY = "family"
    TUTOR = "tutor"
    CENTRE = "centre"


class Lesson(Base):
    """One lesson in one slot. It holds the current state only. History is in LessonChange."""

    __tablename__ = "lesson"
    __table_args__ = (
        CheckConstraint("duration_min IN (60, 90)", name="lesson_duration"),
        CheckConstraint("capacity >= 1", name="lesson_capacity"),
        Index("ix_lesson_date_tutor", "date", "tutor_id"),
    )

    id: Mapped[str] = mapped_column(primary_key=True)
    date: Mapped[date]
    start_time: Mapped[time]
    duration_min: Mapped[int]
    tutor_id: Mapped[str] = mapped_column(ForeignKey("tutor.id"))
    room_id: Mapped[str] = mapped_column(ForeignKey("room.id"))
    capacity: Mapped[int] = mapped_column(default=1)
    status: Mapped[LessonStatus] = mapped_column(enum_column(LessonStatus), default=LessonStatus.BOOKED)
    note: Mapped[str | None] = mapped_column(Text)

    tutor: Mapped[Tutor] = relationship(lazy="raise")
    room: Mapped[Room] = relationship(lazy="raise")
    students: Mapped[list[Student]] = relationship(secondary="lesson_student", lazy="raise")
    changes: Mapped[list["LessonChange"]] = relationship(
        order_by="LessonChange.changed_at, LessonChange.id", lazy="raise"
    )


class LessonStudent(Base):
    """A student in a lesson. An exam pair is one lesson with two rows."""

    __tablename__ = "lesson_student"

    lesson_id: Mapped[str] = mapped_column(ForeignKey("lesson.id"), primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("student.id"), primary_key=True)


class LessonChange(Base):
    """An append-only log. The code never updates or deletes a row."""

    __tablename__ = "lesson_change"
    __table_args__ = (
        CheckConstraint("cancelled_by IS NULL OR kind = 'cancelled'", name="change_cancelled_by_kind"),
        # A lesson can be cancelled or marked no-show once. A move can repeat.
        Index(
            "uq_lesson_change_closing",
            "lesson_id",
            unique=True,
            sqlite_where=text("kind IN ('cancelled', 'no_show')"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    lesson_id: Mapped[str] = mapped_column(ForeignKey("lesson.id"))
    kind: Mapped[ChangeKind] = mapped_column(enum_column(ChangeKind))
    changed_at: Mapped[datetime] = mapped_column(LocalDateTime)
    cancelled_by: Mapped[CancelledBy | None] = mapped_column(enum_column(CancelledBy))
    note: Mapped[str | None] = mapped_column(Text)
    # For a move: the old date, start_time, tutor_id and room_id.
    old_values: Mapped[dict | None] = mapped_column(JSON)
