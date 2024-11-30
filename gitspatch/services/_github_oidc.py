import contextvars
import json

import httpx
from jwcrypto.common import JWException
from jwcrypto.jwk import JWKSet
from jwcrypto.jwt import JWT

from gitspatch.core.redis import Redis
from gitspatch.core.request import Request
from gitspatch.core.settings import Settings
from gitspatch.exceptions import GitspatchError

_GITHUB_OIDC_JKWS_URL = "https://token.actions.githubusercontent.com/.well-known/jwks"


class GitHubOIDCServiceError(GitspatchError):
    pass


class InvalidIDTokenError(GitHubOIDCServiceError):
    def __init__(self, jwexception: JWException) -> None:
        message = "Invalid or expired ID token"
        self.jwexception = jwexception
        super().__init__(message)


class AlreadyUsedIDTokenError(GitHubOIDCServiceError):
    def __init__(self, jti: str) -> None:
        self.jti = jti
        message = f"ID token {jti} has already been used"
        super().__init__(message)


_jwkset: contextvars.ContextVar[JWKSet | None] = contextvars.ContextVar(
    "github_oidc_jwkset", default=None
)


class GitHubOIDCService:
    def __init__(self, settings: Settings, redis: Redis) -> None:
        self._settings = settings
        self._redis = redis

    async def verify_id_token(self, id_token: str) -> tuple[int, str]:
        jwkset = await self._get_jwkset()
        try:
            validated_id_token = JWT(
                jwt=id_token,
                key=jwkset,
                check_claims={
                    "nbf": None,
                    "exp": None,
                    "jti": None,
                    "iss": "https://token.actions.githubusercontent.com",
                    "aud": self._settings.github_oidc_id_token_audience,
                },
            )
        except JWException as e:
            print("jwexception", e)
            raise InvalidIDTokenError(e) from e

        claims = json.loads(validated_id_token.claims)

        nonce_jti_key = f"github_oidc_nonce:{claims['jti']}"
        if await self._redis.get(nonce_jti_key) is not None:
            print("AlreadyUsedIDTokenError")
            raise AlreadyUsedIDTokenError(claims["jti"])
        await self._redis.setex(nonce_jti_key, claims["exp"] + 60, "1")

        repository_id = int(claims.get("repository_id"))
        run_id = claims.get("run_id")

        return repository_id, run_id

    async def _get_jwkset(self) -> JWKSet:
        jwkset_value = _jwkset.get()
        if jwkset_value is None:
            async with httpx.AsyncClient() as client:
                response = await client.get(_GITHUB_OIDC_JKWS_URL)
                response.raise_for_status()
                jwkset_value = JWKSet.from_json(response.text)
                _jwkset.set(jwkset_value)
        return jwkset_value


def get_github_oidc_service(request: Request) -> GitHubOIDCService:
    return GitHubOIDCService(settings=request.state.settings, redis=request.state.redis)
