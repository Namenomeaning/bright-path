from collections.abc import Iterator

import pytest
from sqlalchemy.orm import Session, sessionmaker

from app.core.db import create_tables, make_engine


@pytest.fixture
def db(tmp_path) -> Iterator[Session]:
    engine = make_engine(str(tmp_path / "test.db"))
    create_tables(engine)
    with sessionmaker(engine, expire_on_commit=False, autoflush=False)() as session:
        yield session
    engine.dispose()
