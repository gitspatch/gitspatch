from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from gitspatch.models._timestamp import TimestampMixin

from ._base import Base, get_prefixed_tablename
from ._id import IDModel


class UserSession(IDModel, TimestampMixin, Base):
    __tablename__ = "user_session"
    __idprefix__ = "usr"

    user_id: Mapped[str] = mapped_column(
        ForeignKey(get_prefixed_tablename("user.id"), ondelete="cascade"),
        nullable=False,
    )
    user = relationship("User", lazy="joined")

    token: Mapped[str] = mapped_column(String, nullable=False, index=True, unique=True)
