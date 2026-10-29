from fastapi import APIRouter

from app.core.dependencies import CurrentTime, DbSession
from app.lessons import service
from app.lessons.schemas import CancelRequest, LessonRead

router = APIRouter(prefix="/lessons", tags=["lessons"])


@router.post("/{lesson_id}/cancel")
def cancel_lesson(lesson_id: str, data: CancelRequest, db: DbSession, now: CurrentTime) -> LessonRead:
    lesson = service.cancel_lesson(db, lesson_id, data.cancelled_by, data.note, now)
    return LessonRead.from_lesson(lesson)


@router.post("/{lesson_id}/no-show")
def mark_no_show(lesson_id: str, db: DbSession, now: CurrentTime) -> LessonRead:
    lesson = service.mark_no_show(db, lesson_id, now)
    return LessonRead.from_lesson(lesson)
