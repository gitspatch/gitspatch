import dataclasses
import time
from typing import Any

import httpx
from httpx_oauth.oauth2 import OAuth2Token
from jwcrypto import jwk, jwt

from gitspatch.core.request import Request
from gitspatch.core.settings import Settings


@dataclasses.dataclass
class InstalledRepository:
    id: int
    name: str
    owner: str
    installation_id: int

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.name}"

    @property
    def form_value(self) -> str:
        return f"{self.owner}:{self.name}:{self.id}"


class GitHubService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = httpx.AsyncClient(
            base_url="https://api.github.com",
            headers={"Accept": "application/vnd.github.v3+json"},
        )

    async def get_user_installations(self, token: OAuth2Token) -> list[int]:
        response = await self._client.get(
            "/user/installations",
            headers={"Authorization": f"Bearer {token['access_token']}"},
        )
        response.raise_for_status()

        json = response.json()
        return [item["id"] for item in json["installations"]]

    async def get_installation_repositories(
        self, installation_id: int
    ) -> list[InstalledRepository]:
        response = await self._client.post(
            f"/app/installations/{installation_id}/access_tokens",
            headers={"Authorization": f"Bearer {self._get_app_jwt()}"},
        )
        response.raise_for_status()
        json = response.json()
        token = json["token"]

        response = await self._client.get(
            "/installation/repositories",
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
        json = response.json()
        repositories = [
            InstalledRepository(
                id=item["id"],
                name=item["name"],
                owner=item["owner"]["login"],
                installation_id=installation_id,
            )
            for item in json["repositories"]
        ]
        return repositories

    async def get_user_repositories(
        self, token: OAuth2Token
    ) -> list[InstalledRepository]:
        installations = await self.get_user_installations(token)
        repositories = []
        for installation_id in installations:
            repositories.extend(
                await self.get_installation_repositories(installation_id)
            )
        return repositories

    async def get_repository_installation_id(self, owner: str, repository: str) -> int:
        response = await self._client.get(
            f"/repos/{owner}/{repository}/installation",
            headers={"Authorization": f"Bearer {self._get_app_jwt()}"},
        )
        response.raise_for_status()
        json = response.json()
        return json["id"]

    async def get_repository_installation_access_token(
        self, installation_id: int, repository_id: int
    ) -> tuple[str, InstalledRepository]:
        response = await self._client.post(
            f"/app/installations/{installation_id}/access_tokens",
            headers={"Authorization": f"Bearer {self._get_app_jwt()}"},
            json={"repository_ids": [repository_id]},
        )
        response.raise_for_status()

        json = response.json()
        repository = json["repositories"][0]
        return json["token"], InstalledRepository(
            id=repository["id"],
            name=repository["name"],
            owner=repository["owner"]["login"],
            installation_id=installation_id,
        )

    async def create_workflow_dispatch_event(
        self,
        owner: str,
        repository: str,
        workflow_id: str,
        access_token: str,
        inputs: dict[str, Any],
    ) -> tuple[bool, int | None, str | None]:
        try:
            response = await self._client.post(
                f"/repos/{owner}/{repository}/actions/workflows/{workflow_id}/dispatches",
                headers={"Authorization": f"Bearer {access_token}"},
                json={
                    "ref": "main",
                    "inputs": inputs,
                },
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            return False, e.response.status_code, e.response.text
        except httpx.HTTPError:
            return False, None, None
        else:
            return True, response.status_code, response.text

    def _get_app_jwt(self) -> str:
        claims = {
            "iat": int(time.time()) - 60,
            "exp": int(time.time()) + 600,
            "iss": self._settings.github_client_id,
        }
        jwt_token = jwt.JWT(header={"alg": "RS256"}, claims=claims)
        key = jwk.JWK.from_pem(self._settings.github_private_key.encode())
        jwt_token.make_signed_token(key)
        return jwt_token.serialize()


def get_github_service(request: Request) -> GitHubService:
    return GitHubService(settings=request.state.settings)
