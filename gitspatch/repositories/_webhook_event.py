from gitspatch.models import WebhookEvent

from ._base import Repository


class WebhookEventRepository(Repository[WebhookEvent]):
    model = WebhookEvent
