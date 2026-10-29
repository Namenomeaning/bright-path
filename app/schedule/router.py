from datetime import date

from fastapi import APIRouter

from app.core.dependencies import AppSettings, CurrentTime, DbSession
from app.schedule import service
from app.schedule.schemas import ScheduleRead

router = APIRouter(prefix="/schedule", tags=["schedule"])


@router.get("/{day}")
def get_schedule(
    day: date, db: DbSession, now: CurrentTime, settings: AppSettings, tutor_id: str | None = None
) -> ScheduleRead:
    return service.get_schedule(db, day, now, settings, tutor_id)
