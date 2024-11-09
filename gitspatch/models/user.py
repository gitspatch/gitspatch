from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base
from .id import IDModel


class User(IDModel, Base):
    __tablename__ = "user"
    __idprefix__ = "usr"

    email: Mapped[str] = mapped_column(String, nullable=False)
