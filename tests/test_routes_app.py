import httpx
import pytest

from ._assertions import assert_unauthenticated_response


@pytest.mark.asyncio
class TestIndex:
    async def test_unauthenticated(self, client: httpx.AsyncClient) -> None:
        response = await client.get("/app/")
        assert_unauthenticated_response(response)

    @pytest.mark.auth
    async def test_authenticated(self, client: httpx.AsyncClient) -> None:
        response = await client.get("/app/")
        assert response.status_code == 200
