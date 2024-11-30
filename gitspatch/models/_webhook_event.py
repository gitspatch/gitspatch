from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from gitspatch.models._timestamp import TimestampMixin

from ._base import Base, get_prefixed_tablename
from ._id import IDModel
from ._webhook import Webhook

if TYPE_CHECKING:
    from ._webhook_event_delivery import WebhookEventDelivery


class WorkflowRunStatus(StrEnum):
    COMPLETED = "completed"
    ACTION_REQUIRED = "action_required"
    CANCELLED = "cancelled"
    FAILURE = "failure"
    NEUTRAL = "neutral"
    SKIPPED = "skipped"
    STALE = "stale"
    SUCCESS = "success"
    TIMED_OUT = "timed_out"
    IN_PROGRESS = "in_progress"
    QUEUED = "queued"
    REQUESTED = "requested"
    WAITING = "waiting"
    PENDING = "pending"


class WebhookEvent(IDModel, TimestampMixin, Base):
    __tablename__ = "webhook_events"
    __idprefix__ = "whe"

    webhook_id: Mapped[str] = mapped_column(
        ForeignKey(get_prefixed_tablename("webhooks.id"), ondelete="cascade"),
        nullable=False,
    )
    webhook: Mapped[Webhook] = relationship("Webhook", lazy="raise")

    workflow_run_id: Mapped[str | None] = mapped_column(String, nullable=True)
    workflow_run_status: Mapped[WorkflowRunStatus | None] = mapped_column(
        String, nullable=True
    )

    deliveries: Mapped[list["WebhookEventDelivery"]] = relationship(
        "WebhookEventDelivery", back_populates="webhook_event"
    )

    payload: Mapped[str | None] = mapped_column(Text, nullable=True)
