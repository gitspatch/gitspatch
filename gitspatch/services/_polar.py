from polar_sdk import (
    CheckoutProductCreatePaymentProcessor,
    Polar,
    WebhookBenefitGrantCreatedPayload,
    WebhookBenefitGrantRevokedPayload,
    WebhookBenefitGrantUpdatedPayload,
)
from polar_sdk.webhooks import WebhoookPayload

from gitspatch.core.request import Request
from gitspatch.core.settings import Settings
from gitspatch.exceptions import GitspatchError
from gitspatch.models import User
from gitspatch.repositories import UserRepository, get_repository


class PolarServiceError(GitspatchError):
    pass


class NoCustomerID(PolarServiceError):
    def __init__(self, user: User) -> None:
        self.user = user
        message = f"User {user.id} has no customer_id"
        super().__init__(message)


class UnknownCustomer(PolarServiceError):
    def __init__(self, event: WebhoookPayload) -> None:
        self.event = event
        message = "Received event from Polar but wasn't able to link it to a user"
        super().__init__(message)


class UnhandledEvent(PolarServiceError):
    def __init__(self, event: WebhoookPayload) -> None:
        self.event = event
        message = "Received event from Polar that wasn't handled"
        super().__init__(message)


class PolarService:
    def __init__(self, user_repository: UserRepository, settings: Settings) -> None:
        self._user_repository = user_repository
        self._settings = settings
        self._client = Polar(
            settings.polar_access_token, server=settings.polar_environment
        )

    async def create_checkout(self, user: User) -> str:
        checkout = await self._client.checkouts.custom.create_async(
            request={
                "payment_processor": CheckoutProductCreatePaymentProcessor.STRIPE,
                "product_id": self._settings.polar_product_id,
                "customer_email": user.email,
                "customer_metadata": {"user_id": user.id},
            }
        )
        return checkout.url

    async def create_customer_portal_session(self, user: User) -> str:
        if user.customer_id is None:
            raise NoCustomerID(user)

        customer_session = await self._client.customer_sessions.create_async(
            request={"customer_id": user.customer_id}
        )

        host = (
            "polar.sh"
            if self._settings.polar_environment == "production"
            else "sandbox.polar.sh"
        )
        url = f"https://{host}/gitspatch/portal?customer_session_token={customer_session.token}"
        return url

    async def handle_event(self, event: WebhoookPayload) -> None:
        if isinstance(event, WebhookBenefitGrantCreatedPayload) or isinstance(
            event, WebhookBenefitGrantUpdatedPayload
        ):
            user = await self._get_user_from_customer_id(event.data.customer_id)
            if user is None:
                raise UnknownCustomer(event)
            if event.data.benefit_id == self._settings.polar_webhooks_benefit_id:
                user.webhooks_benefit_id = event.data.benefit_id
                user.max_webhooks = -1
                await self._user_repository.update(user, autoflush=False)
            return

        if isinstance(event, WebhookBenefitGrantRevokedPayload):
            user = await self._get_user_from_customer_id(event.data.customer_id)
            if user is None:
                raise UnknownCustomer(event)
            if event.data.benefit_id == user.webhooks_benefit_id:
                user.webhooks_benefit_id = None
                user.max_webhooks = 1
                await self._user_repository.update(user, autoflush=False)
            return

        raise UnhandledEvent(event)

    async def _get_user_from_customer_id(self, customer_id: str) -> User | None:
        user = await self._user_repository.get_by_customer_id(customer_id)

        if user is None:
            customer = await self._client.customers.get_async(id=customer_id)
            user_id = customer.metadata.get("user_id")
            if user_id is None:
                return None
            user = await self._user_repository.get_by_id(str(user_id))

        if user is not None:
            user.customer_id = customer_id
            await self._user_repository.update(user, autoflush=False)

        return user


def get_polar_service(request: Request) -> PolarService:
    return PolarService(get_repository(UserRepository, request), request.state.settings)
