from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from gitspatch.models._timestamp import TimestampMixin

from ._base import Base, get_prefixed_tablename
from ._id import IDModel
from ._user import User


class Webhook(IDModel, TimestampMixin, Base):
    __tablename__ = "webhooks"
    __idprefix__ = "whk"

    user_id: Mapped[str] = mapped_column(
        ForeignKey(get_prefixed_tablename("users.id"), ondelete="cascade"),
        nullable=False,
    )
    user: Mapped[User] = relationship("User", lazy="raise")

    github_repository_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    github_workflow_id: Mapped[str] = mapped_column(String, nullable=False)
    github_installation_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    token: Mapped[str] = mapped_column(String, nullable=False, index=True, unique=True)
