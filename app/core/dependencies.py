from datetime import datetime
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.db import get_db


def get_current_time() -> datetime:
    return get_settings().now


AppSettings = Annotated[Settings, Depends(get_settings)]
DbSession = Annotated[Session, Depends(get_db)]
CurrentTime = Annotated[datetime, Depends(get_current_time)]
