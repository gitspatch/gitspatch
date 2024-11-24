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

    repository_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    workflow_id: Mapped[str] = mapped_column(String, nullable=False)
    installation_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    owner: Mapped[str] = mapped_column(String, nullable=False)
    repository_name: Mapped[str] = mapped_column(String, nullable=False)

    token: Mapped[str] = mapped_column(String, nullable=False, index=True, unique=True)

    @property
    def repository_full_name(self) -> str:
        return f"{self.owner}/{self.repository_name}"

    @property
    def repository_url(self) -> str:
        return f"https://github.com/{self.repository_full_name}"

    @property
    def workflow_url(self) -> str:
        return f"{self.repository_url}/actions/workflows/{self.workflow_id}"
