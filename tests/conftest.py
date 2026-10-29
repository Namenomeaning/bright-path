from collections.abc import Iterator
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.core.db import create_tables, get_db, make_engine
from app.core.dependencies import get_current_time
from app.main import create_app
from scripts.seed import load_seed

VIETNAM = timezone(timedelta(hours=7))
# The default time of the demo: Friday 2026-03-06 at 07:00.
DEFAULT_NOW = datetime(2026, 3, 6, 7, 0, tzinfo=VIETNAM)


@pytest.fixture
def db(tmp_path) -> Iterator[Session]:
    engine = make_engine(str(tmp_path / "test.db"))
    create_tables(engine)
    with sessionmaker(engine, expire_on_commit=False, autoflush=False)() as session:
        yield session
    engine.dispose()


@pytest.fixture
def client(db: Session) -> Iterator[TestClient]:
    """An API client on the seeded database. Change the time with set_now."""
    load_seed(db)
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_time] = lambda: DEFAULT_NOW
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def set_now(client: TestClient):
    def set_now(moment: datetime) -> None:
        client.app.dependency_overrides[get_current_time] = lambda: moment

    return set_now
