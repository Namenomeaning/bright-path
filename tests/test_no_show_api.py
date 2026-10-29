from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.lessons.model import Lesson, LessonChange, LessonStatus

VIETNAM = timezone(timedelta(hours=7))
# L018 is booked on 2026-03-06 at 09:00. The default time of the tests is 07:00 on that day.
BOOKED = "L018"
AFTER_START = datetime(2026, 3, 6, 10, 0, tzinfo=VIETNAM)


def change_count(db, lesson_id: str) -> int:
    return db.scalar(select(func.count()).select_from(LessonChange).where(LessonChange.lesson_id == lesson_id))


def status_of(db, lesson_id: str) -> LessonStatus:
    return db.scalar(select(Lesson.status).where(Lesson.id == lesson_id))


def test_a_no_show_after_the_start_returns_the_lesson_with_its_change(client, set_now):
    set_now(AFTER_START)

    response = client.post(f"/lessons/{BOOKED}/no-show")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "no_show"
    assert body["change"] == {
        "kind": "no_show",
        "changed_at": "2026-03-06T10:00:00+07:00",
        "cancelled_by": None,
        "note": None,
        "late": None,
    }


def test_a_no_show_writes_the_status_and_one_change(client, set_now, db):
    set_now(AFTER_START)

    client.post(f"/lessons/{BOOKED}/no-show")

    assert status_of(db, BOOKED) is LessonStatus.NO_SHOW
    assert change_count(db, BOOKED) == 1


def test_a_no_show_is_allowed_at_the_exact_start(client, set_now):
    set_now(datetime(2026, 3, 6, 9, 0, tzinfo=VIETNAM))

    assert client.post(f"/lessons/{BOOKED}/no-show").status_code == 200


def test_a_no_show_before_the_start_is_rejected_and_writes_nothing(client, db):
    response = client.post(f"/lessons/{BOOKED}/no-show")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "lesson_not_started"
    assert status_of(db, BOOKED) is LessonStatus.BOOKED
    assert change_count(db, BOOKED) == 0


def test_a_cancelled_lesson_is_not_booked_even_before_its_start(client):
    client.post(f"/lessons/{BOOKED}/cancel", json={"cancelled_by": "family"})

    response = client.post(f"/lessons/{BOOKED}/no-show")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "not_booked"


def test_a_no_show_lesson_cannot_be_cancelled_or_marked_again(client, set_now):
    set_now(AFTER_START)
    client.post(f"/lessons/{BOOKED}/no-show")

    again = client.post(f"/lessons/{BOOKED}/no-show")
    cancel = client.post(f"/lessons/{BOOKED}/cancel", json={"cancelled_by": "family"})

    assert [again.status_code, cancel.status_code] == [409, 409]


def test_an_unknown_lesson_returns_404(client):
    response = client.post("/lessons/L999/no-show")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "lesson_not_found"
