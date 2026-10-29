from collections.abc import Iterator
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Engine, Enum, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.types import TypeDecorator

from app.core.config import TIMEZONE, get_settings


class Base(DeclarativeBase):
    pass


class LocalDateTime(TypeDecorator):
    """A moment stored as local time (Asia/Ho_Chi_Minh) and read back with its offset."""

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("A moment needs a time zone")
        return value.astimezone(TIMEZONE).replace(tzinfo=None)

    def process_result_value(self, value: datetime | None, dialect) -> datetime | None:
        return None if value is None else value.replace(tzinfo=TIMEZONE)


def enum_column(enum_class: type[StrEnum]) -> Enum:
    """Store the enum values as text. The database rejects any other value."""
    return Enum(
        enum_class,
        native_enum=False,
        create_constraint=True,
        name=enum_class.__name__.lower(),
        length=20,
        values_callable=lambda members: [member.value for member in members],
    )


def create_tables(engine: Engine) -> None:
    # Import every model so that Base knows all the tables.
    import app.lessons.model  # noqa: F401
    import app.rooms.model  # noqa: F401
    import app.students.model  # noqa: F401
    import app.tutors.model  # noqa: F401

    Base.metadata.create_all(engine)


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
