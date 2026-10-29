from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.lessons.model import ChangeKind, Lesson, LessonChange, LessonStatus

VIETNAM = timezone(timedelta(hours=7))
# L018 is booked on 2026-03-06 at 09:00. The default time of the tests is 07:00 on that day.
BOOKED = "L018"


def change_count(db, lesson_id: str) -> int:
    return db.scalar(select(func.count()).select_from(LessonChange).where(LessonChange.lesson_id == lesson_id))


def status_of(db, lesson_id: str) -> LessonStatus:
    return db.scalar(select(Lesson.status).where(Lesson.id == lesson_id))


def test_a_family_cancellation_returns_the_lesson_with_its_change(client):
    response = client.post(f"/lessons/{BOOKED}/cancel", json={"cancelled_by": "family", "note": "family called"})

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == BOOKED
    assert body["status"] == "cancelled"
    assert body["change"] == {
        "kind": "cancelled",
        "changed_at": "2026-03-06T07:00:00+07:00",
        "cancelled_by": "family",
        "note": "family called",
        "late": True,
    }


def test_a_cancellation_writes_the_status_and_one_change(client, db):
    client.post(f"/lessons/{BOOKED}/cancel", json={"cancelled_by": "tutor"})

    assert status_of(db, BOOKED) is LessonStatus.CANCELLED
    assert change_count(db, BOOKED) == 1


def test_a_cancellation_after_the_cutoff_shows_on_the_schedule(client):
    client.post(f"/lessons/{BOOKED}/cancel", json={"cancelled_by": "centre", "note": "room closed"})

    lessons = client.get("/schedule/2026-03-06").json()["lessons"]
    cancelled = next(lesson for lesson in lessons if lesson["id"] == BOOKED)

    assert cancelled["change"]["note"] == "room closed"


def test_a_tutor_cancellation_is_not_late(client):
    body = client.post(f"/lessons/{BOOKED}/cancel", json={"cancelled_by": "tutor"}).json()

    assert body["change"]["late"] is None


def test_a_lesson_can_be_cancelled_after_it_started(client, set_now):
    set_now(datetime(2026, 3, 6, 10, 0, tzinfo=VIETNAM))

    assert client.post(f"/lessons/{BOOKED}/cancel", json={"cancelled_by": "family"}).status_code == 200


def test_a_lesson_cannot_be_cancelled_twice(client, db):
    client.post(f"/lessons/{BOOKED}/cancel", json={"cancelled_by": "family"})

    response = client.post(f"/lessons/{BOOKED}/cancel", json={"cancelled_by": "family"})

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "not_booked"
    assert change_count(db, BOOKED) == 1


def test_a_cancelled_or_no_show_lesson_cannot_be_cancelled(client):
    for lesson_id in ("L017", "L015"):
        response = client.post(f"/lessons/{lesson_id}/cancel", json={"cancelled_by": "family"})

        assert response.status_code == 409
        assert response.json()["error"]["code"] == "not_booked"


def test_the_database_blocks_a_second_closing_change(client, db):
    # A broken row: a closing change exists, but the lesson still says booked.
    db.add(LessonChange(lesson_id=BOOKED, kind=ChangeKind.NO_SHOW, changed_at=datetime(2026, 3, 6, tzinfo=VIETNAM)))
    db.commit()

    response = client.post(f"/lessons/{BOOKED}/cancel", json={"cancelled_by": "family"})

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "not_booked"
    assert status_of(db, BOOKED) is LessonStatus.BOOKED
    assert change_count(db, BOOKED) == 1


def test_an_unknown_lesson_returns_404(client):
    response = client.post("/lessons/L999/cancel", json={"cancelled_by": "family"})

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "lesson_not_found"


def test_a_bad_request_returns_422_and_writes_nothing(client, db):
    bodies = [{}, {"cancelled_by": "neighbour"}]

    for body in bodies:
        response = client.post(f"/lessons/{BOOKED}/cancel", json=body)

        assert response.status_code == 422
        assert response.json()["error"]["code"] == "invalid_request"
    assert status_of(db, BOOKED) is LessonStatus.BOOKED
    assert change_count(db, BOOKED) == 0
