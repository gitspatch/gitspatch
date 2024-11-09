import httpx
import pytest


@pytest.mark.asyncio
async def test_index(client: httpx.AsyncClient) -> None:
    response = await client.get("/")
    assert response.status_code == 200
    assert response.text == "Hello, world!"


@pytest.mark.asyncio
@pytest.mark.parametrize("i", range(10))
async def test_create_user(i: int, client: httpx.AsyncClient) -> None:
    response = await client.post("/create_user")
    assert response.status_code == 200
    assert response.text.startswith("User ")
