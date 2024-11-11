from httpx_oauth.oauth2 import OAuth2Token

from gitspatch.core.request import Request
from gitspatch.core.settings import Settings
from gitspatch.models import User
from gitspatch.repositories import UserRepository


class UserService:
    def __init__(self, repository: UserRepository, settings: Settings) -> None:
        self._repository = repository
        self._settings = settings

    async def get_github_token(self, user: User) -> OAuth2Token:
        token = user.github_token
        if token.is_expired():
            oauth_client = self._settings.get_github_oauth_client()
            token = await oauth_client.refresh_token(token["refresh_token"])
            user.github_token = token
            await self._repository.update(user, autoflush=False)
        return token


def get_user_service(request: Request) -> UserService:
    return UserService(
        repository=UserRepository(request.state.session),
        settings=request.state.settings,
    )
