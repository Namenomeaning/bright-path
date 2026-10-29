"""Load the front-desk export into the database. Run it again to reset the database.

    uv run python -m scripts.seed
"""

import csv
from datetime import date, datetime, time
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import TIMEZONE, get_settings
from app.core.db import Base, create_tables, make_engine
from app.lessons.model import ChangeKind, Lesson, LessonChange, LessonStatus, LessonStudent
from app.rooms.model import Room
from app.students.model import Student
from app.tutors.model import Tutor

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ROOM_IDS = [f"R{number}" for number in range(1, 7)]
EXAM_PAIR_NOTE = "exam pair - half price"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def load_seed(db: Session, data_dir: Path = DATA_DIR) -> None:
    """Fill empty tables. Every export row loads as it is, including the rows that break a rule."""
    rows = read_csv(data_dir / "lessons_export.csv")

    for tutor in read_csv(data_dir / "tutors.csv"):
        db.add(Tutor(id=tutor["tutor_id"], name=tutor["tutor_name"], subject=tutor["subject"], phone=tutor["phone"]))
    for room_id in ROOM_IDS:
        db.add(Room(id=room_id, name=room_id))

    students: dict[str, Student] = {}
    for row in rows:
        if row["student"] not in students:
            students[row["student"]] = Student(name=row["student"])
            db.add(students[row["student"]])
    db.flush()

    for group in group_exam_pairs(rows):
        add_lesson(db, group, students)
    db.commit()


def group_exam_pairs(rows: list[dict[str, str]]) -> list[list[dict[str, str]]]:
    """One group for each lesson. An exam pair is two rows with the same tutor, room and start."""
    groups: dict[tuple, list[dict[str, str]]] = {}
    for row in rows:
        key = (row["date"], row["start_time"], row["tutor_id"], row["room"], EXAM_PAIR_NOTE)
        is_pair_row = row["note"] == EXAM_PAIR_NOTE
        groups.setdefault(key if is_pair_row else (row["lesson_id"],), []).append(row)
    return list(groups.values())


def add_lesson(db: Session, group: list[dict[str, str]], students: dict[str, Student]) -> None:
    row = group[0]
    status = LessonStatus(row["status"])
    start = datetime.combine(date.fromisoformat(row["date"]), time.fromisoformat(row["start_time"]), TIMEZONE)

    db.add(
        Lesson(
            id=row["lesson_id"],
            date=start.date(),
            start_time=start.time(),
            duration_min=int(row["duration_min"]),
            tutor_id=row["tutor_id"],
            room_id=row["room"],
            capacity=len(group),
            status=status,
            # The note of a cancelled row goes to its change row.
            note=None if status is LessonStatus.CANCELLED else row["note"] or None,
        )
    )
    db.flush()
    for member in group:
        db.add(LessonStudent(lesson_id=row["lesson_id"], student_id=students[member["student"]].id))

    if status is LessonStatus.CANCELLED:
        db.add(
            LessonChange(
                lesson_id=row["lesson_id"],
                kind=ChangeKind.CANCELLED,
                changed_at=datetime.fromisoformat(row["cancelled_at"]),
                note=row["note"] or None,
            )
        )
    elif status is LessonStatus.NO_SHOW:
        # The export has no time for a no-show. The lesson start is the earliest Mai can mark one.
        db.add(LessonChange(lesson_id=row["lesson_id"], kind=ChangeKind.NO_SHOW, changed_at=start))


def main() -> None:
    engine = make_engine(get_settings().db)
    Base.metadata.drop_all(engine)
    create_tables(engine)
    with Session(engine) as db:
        load_seed(db)
        lessons = db.query(Lesson).count()
        students = db.query(Student).count()
        changes = db.query(LessonChange).count()
    print(f"Loaded {lessons} lessons, {students} students and {changes} changes into {get_settings().db}")


if __name__ == "__main__":
    main()
