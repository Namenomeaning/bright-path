from collections.abc import Iterator

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


def make_engine(path: str) -> Engine:
    engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, _record) -> None:
        dbapi_connection.execute("PRAGMA foreign_keys = ON")

    return engine


engine = make_engine(get_settings().db)
SessionLocal = sessionmaker(engine, expire_on_commit=False, autoflush=False)


def get_db() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session
