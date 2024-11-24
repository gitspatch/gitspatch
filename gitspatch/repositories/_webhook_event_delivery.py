from gitspatch.models import WebhookEventDelivery

from ._base import Repository


class WebhookEventDeliveryRepository(Repository[WebhookEventDelivery]):
    model = WebhookEventDelivery
