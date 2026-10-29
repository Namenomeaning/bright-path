"""The database rejects bad rows. These tests use plain SQL, so the ORM cannot hide a missing rule."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.lessons.model import LessonChange

LESSON = {
    "id": "L001", "date": "2026-03-03", "start_time": "09:00:00", "duration_min": 60,
    "tutor_id": "T1", "room_id": "R1", "capacity": 1, "status": "booked",
}


@pytest.fixture
def base(db: Session) -> Session:
    db.execute(text("INSERT INTO tutor VALUES ('T1', 'Ngoc Anh', 'Maths', '090xxx1122')"))
    db.execute(text("INSERT INTO room VALUES ('R1', 'R1')"))
    db.execute(text("INSERT INTO student VALUES (1, 'Le Minh Chau')"))
    db.commit()
    return db


def add_lesson(db: Session, **overrides) -> None:
    row = {**LESSON, **overrides}
    db.execute(
        text(
            "INSERT INTO lesson (id, date, start_time, duration_min, tutor_id, room_id, capacity, status) "
            "VALUES (:id, :date, :start_time, :duration_min, :tutor_id, :room_id, :capacity, :status)"
        ),
        row,
    )


def add_change(db: Session, kind: str, cancelled_by: str | None = None, lesson_id: str = "L001") -> None:
    db.execute(
        text(
            "INSERT INTO lesson_change (lesson_id, kind, changed_at, cancelled_by) "
            "VALUES (:lesson_id, :kind, '2026-03-03 08:15:00', :cancelled_by)"
        ),
        {"lesson_id": lesson_id, "kind": kind, "cancelled_by": cancelled_by},
    )


def test_a_valid_lesson_is_accepted(base):
    add_lesson(base)
    base.commit()


@pytest.mark.parametrize(
    "override",
    [
        {"duration_min": 45},
        {"capacity": 0},
        {"status": "maybe"},
        {"tutor_id": "T9"},
        {"room_id": "R9"},
    ],
    ids=["duration", "capacity", "status", "unknown tutor", "unknown room"],
)
def test_a_bad_lesson_is_rejected(base, override):
    with pytest.raises(IntegrityError):
        add_lesson(base, **override)


def test_a_change_needs_a_known_kind(base):
    add_lesson(base)

    with pytest.raises(IntegrityError):
        add_change(base, "deleted")


def test_cancelled_by_needs_a_known_value(base):
    add_lesson(base)

    with pytest.raises(IntegrityError):
        add_change(base, "cancelled", cancelled_by="neighbour")


def test_cancelled_by_is_only_for_a_cancellation(base):
    add_lesson(base)

    with pytest.raises(IntegrityError):
        add_change(base, "no_show", cancelled_by="family")


def test_a_lesson_closes_once(base):
    add_lesson(base)
    add_change(base, "cancelled", cancelled_by="family")

    with pytest.raises(IntegrityError):
        add_change(base, "no_show")


def test_a_lesson_can_move_after_it_closes(base):
    add_lesson(base)
    add_change(base, "cancelled", cancelled_by="family")
    add_change(base, "moved")
    add_change(base, "moved")
    base.commit()


def test_a_student_joins_a_lesson_once(base):
    add_lesson(base)
    base.execute(text("INSERT INTO lesson_student VALUES ('L001', 1)"))

    with pytest.raises(IntegrityError):
        base.execute(text("INSERT INTO lesson_student VALUES ('L001', 1)"))


def test_changed_at_keeps_its_offset(base):
    add_lesson(base)
    moment = datetime(2026, 3, 3, 8, 15, tzinfo=timezone(timedelta(hours=7)))
    base.add(LessonChange(lesson_id="L001", kind="cancelled", changed_at=moment))
    base.commit()

    saved = base.scalars(select(LessonChange)).one()

    assert saved.changed_at == moment
    assert saved.changed_at.utcoffset() == timedelta(hours=7)
