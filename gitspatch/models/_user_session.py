from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from gitspatch.models._timestamp import TimestampMixin

from ._base import Base, get_prefixed_tablename
from ._id import IDModel
from ._user import User


class UserSession(IDModel, TimestampMixin, Base):
    __tablename__ = "user_sessions"
    __idprefix__ = "ses"

    user_id: Mapped[str] = mapped_column(
        ForeignKey(get_prefixed_tablename("users.id"), ondelete="cascade"),
        nullable=False,
    )
    user: Mapped[User] = relationship("User", lazy="joined")

    token: Mapped[str] = mapped_column(String, nullable=False, index=True, unique=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
