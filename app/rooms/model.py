from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Room(Base):
    __tablename__ = "room"

    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]
