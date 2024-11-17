from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from gitspatch.models._timestamp import TimestampMixin

from ._base import Base, get_prefixed_tablename
from ._id import IDModel
from ._webhook import Webhook


class WebhookEvent(IDModel, TimestampMixin, Base):
    __tablename__ = "webhook_events"
    __idprefix__ = "whe"

    webhook_id: Mapped[str] = mapped_column(
        ForeignKey(get_prefixed_tablename("webhooks.id"), ondelete="cascade"),
        nullable=False,
    )
    webhook: Mapped[Webhook] = relationship("Webhook", lazy="raise")

    payload: Mapped[str | None] = mapped_column(Text, nullable=True)
