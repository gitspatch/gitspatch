from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from gitspatch.models._timestamp import TimestampMixin

from ._base import Base
from ._id import IDModel


class User(IDModel, TimestampMixin, Base):
    __tablename__ = "user"
    __idprefix__ = "usr"

    email: Mapped[str] = mapped_column(String, nullable=False)
    github_account_id: Mapped[str] = mapped_column(String, nullable=False)
