from datetime import datetime, timedelta, timezone

from sqlalchemy import update

from app.lessons.model import CancelledBy, ChangeKind, Lesson, LessonChange, LessonStatus

VIETNAM = timezone(timedelta(hours=7))


def ids(body: dict) -> list[str]:
    return [lesson["id"] for lesson in body["lessons"]]


def cancel_in_db(db, lesson_id: str, changed_at: datetime, cancelled_by=None) -> None:
    db.execute(update(Lesson).where(Lesson.id == lesson_id).values(status=LessonStatus.CANCELLED))
    db.add(LessonChange(lesson_id=lesson_id, kind=ChangeKind.CANCELLED, changed_at=changed_at, cancelled_by=cancelled_by))
    db.commit()


def test_a_final_schedule_marks_the_changes_after_the_cutoff(client):
    body = client.get("/schedule/2026-03-05").json()

    assert body["state"] == "final"
    assert body["cutoff"] == "2026-03-04T16:00:00+07:00"
    assert ids(body) == ["L013", "L014", "L015", "L016", "L017"]
    changes = {lesson["id"]: lesson["change"] for lesson in body["lessons"]}
    assert changes["L013"] is None
    assert changes["L015"]["kind"] == "no_show"


def test_a_cancelled_lesson_has_the_shape_of_the_contract(client):
    lessons = client.get("/schedule/2026-03-05").json()["lessons"]
    cancelled = next(lesson for lesson in lessons if lesson["id"] == "L017")

    assert cancelled == {
        "id": "L017",
        "start_time": "16:00",
        "end_time": "17:00",
        "tutor": {"id": "T3", "name": "Le Thu"},
        "room": "R3",
        "students": [{"id": 4, "name": "Do Van Kien"}],
        "status": "cancelled",
        "change": {
            "kind": "cancelled",
            "changed_at": "2026-03-05T14:40:00+07:00",
            "cancelled_by": None,
            "note": "tutor sick",
            "late": None,
        },
    }


def test_the_cutoff_of_tuesday_skips_the_closed_monday(client):
    body = client.get("/schedule/2026-03-03").json()

    assert body["cutoff"] == "2026-03-01T16:00:00+07:00"
    assert "L005" in ids(body)
    assert next(lesson for lesson in body["lessons"] if lesson["id"] == "L005")["change"]["kind"] == "cancelled"


def test_the_exam_pair_shows_once_and_the_conflict_shows_twice(client):
    body = client.get("/schedule/2026-03-04").json()

    assert ids(body).count("L009") == 1
    assert "L010" not in ids(body)
    pair = next(lesson for lesson in body["lessons"] if lesson["id"] == "L009")
    assert [student["name"] for student in pair["students"]] == ["Tran Bao Long", "Nguyen Thi Ha"]
    assert {"L007", "L008"} <= set(ids(body))


def test_a_closed_day_can_still_be_requested(client):
    assert ids(client.get("/schedule/2026-03-09").json()) == ["L032"]


def test_the_lessons_are_sorted_by_start_time(client):
    starts = [lesson["start_time"] for lesson in client.get("/schedule/2026-03-06").json()["lessons"]]

    assert starts == sorted(starts)


def test_a_schedule_is_a_draft_before_its_cutoff(client, set_now):
    set_now(datetime(2026, 3, 4, 10, 0, tzinfo=VIETNAM))

    assert client.get("/schedule/2026-03-05").json()["state"] == "draft"


def test_the_tutor_filter_returns_one_tutor(client):
    body = client.get("/schedule/2026-03-05", params={"tutor_id": "T3"}).json()

    assert ids(body) == ["L014", "L017"]


def test_an_unknown_tutor_returns_404(client):
    response = client.get("/schedule/2026-03-05", params={"tutor_id": "T9"})

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "tutor_not_found"


def test_a_bad_date_returns_422(client):
    response = client.get("/schedule/not-a-date")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"


def test_a_cancellation_before_the_cutoff_leaves_the_schedule(client, db):
    cancel_in_db(db, "L013", datetime(2026, 3, 4, 15, 59, tzinfo=VIETNAM))

    assert "L013" not in ids(client.get("/schedule/2026-03-05").json())


def test_a_cancellation_after_the_cutoff_stays_on_the_schedule(client, db):
    cancel_in_db(db, "L013", datetime(2026, 3, 4, 16, 1, tzinfo=VIETNAM))

    assert "L013" in ids(client.get("/schedule/2026-03-05").json())


def test_a_family_cancellation_within_4_hours_is_late(client, db):
    # L018 starts on 2026-03-06 at 09:00.
    cancel_in_db(db, "L018", datetime(2026, 3, 6, 5, 0, tzinfo=VIETNAM), CancelledBy.FAMILY)

    lesson = next(item for item in client.get("/schedule/2026-03-06").json()["lessons"] if item["id"] == "L018")

    assert lesson["change"]["late"] is True


def test_a_family_cancellation_over_4_hours_before_is_not_late(client, db):
    cancel_in_db(db, "L018", datetime(2026, 3, 6, 4, 59, tzinfo=VIETNAM), CancelledBy.FAMILY)

    lesson = next(item for item in client.get("/schedule/2026-03-06").json()["lessons"] if item["id"] == "L018")

    assert lesson["change"]["late"] is False


def test_a_tutor_cancellation_is_never_late(client, db):
    cancel_in_db(db, "L018", datetime(2026, 3, 6, 8, 0, tzinfo=VIETNAM), CancelledBy.TUTOR)

    lesson = next(item for item in client.get("/schedule/2026-03-06").json()["lessons"] if item["id"] == "L018")

    assert lesson["change"]["late"] is None
