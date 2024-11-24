from sqlalchemy import Boolean, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from gitspatch.models._timestamp import TimestampMixin

from ._base import Base, get_prefixed_tablename
from ._id import IDModel
from ._webhook_event import WebhookEvent


class WebhookEventDelivery(IDModel, TimestampMixin, Base):
    __tablename__ = "webhook_event_deliveries"
    __idprefix__ = "whd"

    webhook_event_id: Mapped[str] = mapped_column(
        ForeignKey(get_prefixed_tablename("webhook_events.id"), ondelete="cascade"),
        nullable=False,
    )
    webhook_event: Mapped[WebhookEvent] = relationship(
        "WebhookEvent", lazy="joined", back_populates="deliveries"
    )

    attempt: Mapped[int] = mapped_column(Integer, nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_body: Mapped[str | None] = mapped_column(Text, nullable=True)
