from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Tutor(Base):
    __tablename__ = "tutor"

    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]
    subject: Mapped[str]
    phone: Mapped[str]
