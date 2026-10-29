from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.lessons.model import ChangeKind, Lesson, LessonChange, LessonStatus
from app.rooms.model import Room
from app.students.model import Student
from app.tutors.model import Tutor
from scripts.seed import load_seed

VIETNAM = timezone(timedelta(hours=7))


@pytest.fixture
def seeded(db: Session) -> Session:
    load_seed(db)
    return db


def lesson(db: Session, lesson_id: str) -> Lesson | None:
    query = select(Lesson).where(Lesson.id == lesson_id).options(selectinload(Lesson.students), selectinload(Lesson.changes))
    return db.scalars(query).one_or_none()


def test_the_export_loads_in_full(seeded):
    assert len(seeded.scalars(select(Tutor)).all()) == 3
    assert len(seeded.scalars(select(Room)).all()) == 6
    assert len(seeded.scalars(select(Student)).all()) == 6
    assert len(seeded.scalars(select(Lesson)).all()) == 33
    assert len(seeded.scalars(select(LessonChange)).all()) == 3


def test_students_are_numbered_in_order_of_first_appearance(seeded):
    names = [student.name for student in seeded.scalars(select(Student).order_by(Student.id))]

    assert names[:4] == ["Le Minh Chau", "Tran Bao Long", "Nguyen Thi Ha", "Do Van Kien"]


def test_the_exam_pair_is_one_lesson_with_two_students(seeded):
    pair = lesson(seeded, "L009")

    assert lesson(seeded, "L010") is None
    assert pair.capacity == 2
    assert {student.name for student in pair.students} == {"Tran Bao Long", "Nguyen Thi Ha"}
    assert pair.note == "exam pair - half price"


def test_a_normal_lesson_has_one_student(seeded):
    normal = lesson(seeded, "L001")

    assert normal.capacity == 1
    assert [student.name for student in normal.students] == ["Le Minh Chau"]


def test_a_cancelled_row_becomes_a_change_with_its_note(seeded):
    sick = lesson(seeded, "L017")
    (change,) = sick.changes

    assert sick.status is LessonStatus.CANCELLED
    assert sick.note is None
    assert change.kind is ChangeKind.CANCELLED
    assert change.changed_at == datetime(2026, 3, 5, 14, 40, tzinfo=VIETNAM)
    assert change.note == "tutor sick"
    assert change.cancelled_by is None


def test_the_no_show_change_uses_the_lesson_start(seeded):
    missed = lesson(seeded, "L015")
    (change,) = missed.changes

    assert missed.status is LessonStatus.NO_SHOW
    assert change.kind is ChangeKind.NO_SHOW
    assert change.changed_at == datetime(2026, 3, 5, 13, 0, tzinfo=VIETNAM)


def test_the_export_notes_are_kept(seeded):
    assert lesson(seeded, "L008").note == "added by phone; family confirmed"
    assert lesson(seeded, "L032").note == "moved from Sunday at the family's request"


def test_the_real_conflicts_load_as_they_are(seeded):
    same_student = [lesson(seeded, "L007"), lesson(seeded, "L008")]
    same_tutor = [lesson(seeded, "L033"), lesson(seeded, "L034")]

    assert all(row.status is LessonStatus.BOOKED for row in same_student + same_tutor)
    assert {row.students[0].name for row in same_student} == {"Le Minh Chau"}
    assert {row.tutor_id for row in same_tutor} == {"T1"}
    assert {row.room_id for row in same_tutor} == {"R1", "R2"}
